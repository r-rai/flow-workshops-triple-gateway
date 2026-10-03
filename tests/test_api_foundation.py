import os
import pytest
from fastapi.testclient import TestClient

# Ensure sqlite for tests
os.environ["DATABASE_URL"] = "sqlite:///./test_novabank.sqlite"
os.environ["GATE3_API_KEY"] = "gate3-test-key"
os.environ["SEED_FILE_PATH"] = "seed/v1_seed.json"

from src.api.main import app
from src.core.database import Base, engine
from src.services.seed import reset_and_seed_db
from src.core.database import SessionLocal
from spikes.spike4_identity.test_spike4 import issue_token

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    reset_and_seed_db(db, "seed/v1_seed.json")
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("./test_novabank.sqlite"):
        try:
            os.remove("./test_novabank.sqlite")
        except Exception:
            pass

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def lab_headers():
    return {"X-API-Key": "gate3-test-key"}

@pytest.fixture
def manager_jwt_headers():
    token = issue_token(
        subject="manager-priya",
        audience="novabank-api",
        scopes=["api:accounts:read", "api:payments:write", "api:cases:read", "api:incidents:write"],
        role="manager",
    )
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def agent_jwt_headers():
    token = issue_token(
        subject="agent-support-01",
        audience="novabank-api",
        scopes=["api:accounts:read", "api:payments:write", "api:cases:read"],
        role="support_agent",
    )
    return {"Authorization": f"Bearer {token}"}

def test_healthz(client):
    res = client.get("/healthz")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"

def test_unauthenticated_rejection(client):
    res = client.get("/api/v1/accounts/acc-101")
    assert res.status_code == 401
    assert "Missing Gate 3 authentication credential" in res.json()["detail"]

def test_account_read_positive(client, lab_headers):
    res = client.get("/api/v1/accounts/acc-101", headers=lab_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == "acc-101"
    assert data["balance"] == 1500000
    assert data["currency"] == "INR"

def test_account_read_not_found(client, lab_headers):
    res = client.get("/api/v1/accounts/acc-nonexistent", headers=lab_headers)
    assert res.status_code == 404

def test_small_payment_auto_allowed(client, agent_jwt_headers):
    initial = client.get("/api/v1/accounts/acc-101", headers=agent_jwt_headers).json()["balance"]
    res = client.post(
        "/api/v1/payments",
        headers={**agent_jwt_headers, "Idempotency-Key": "idemp-test-small-1"},
        json={
            "account_id": "acc-101",
            "amount": 25000,
            "currency": "INR",
            "beneficiary": "vendor-alpha"
        }
    )
    assert res.status_code == 200
    assert res.json()["status"] == "COMPLETED"
    assert res.json()["remaining_balance"] == initial - 25000

    # Test idempotency replay
    replay = client.post(
        "/api/v1/payments",
        headers={**agent_jwt_headers, "Idempotency-Key": "idemp-test-small-1"},
        json={
            "account_id": "acc-101",
            "amount": 25000,
            "currency": "INR",
            "beneficiary": "vendor-alpha"
        }
    )
    assert replay.status_code == 200
    assert replay.json()["idempotent_replay"] is True
    assert replay.json()["remaining_balance"] == initial - 25000

def test_payment_exceeding_threshold_without_proposal_denied(client, agent_jwt_headers):
    res = client.post(
        "/api/v1/payments",
        headers=agent_jwt_headers,
        json={
            "account_id": "acc-101",
            "amount": 500000,
            "currency": "INR",
            "beneficiary": "vendor-beta"
        }
    )
    assert res.status_code == 403
    assert "exceeds unsupervised limit" in res.json()["detail"]

def test_approval_lifecycle_and_tamper_rejection(client, agent_jwt_headers, manager_jwt_headers):
    # 1. Propose payment
    prop_req = {
        "account_id": "acc-101",
        "amount": 500000,
        "currency": "INR",
        "beneficiary": "vendor-beta"
    }
    prop_res = client.post("/api/v1/payments/proposals", headers=agent_jwt_headers, json=prop_req)
    assert prop_res.status_code == 200
    prop_id = prop_res.json()["proposal_id"]

    # 2. Self-approval prohibited
    self_app = client.post(f"/api/v1/approvals/{prop_id}/approve", headers=agent_jwt_headers)
    assert self_app.status_code == 403
    assert "Self-approval prohibited" in self_app.json()["detail"]

    # 3. Manager approval succeeds
    mgr_app = client.post(f"/api/v1/approvals/{prop_id}/approve", headers=manager_jwt_headers)
    assert mgr_app.status_code == 200
    assert mgr_app.json()["status"] == "approved"

    # 4. Tampered arguments execution rejected
    tampered_exec = {**prop_req, "amount": 600000, "proposal_id": prop_id}
    tamper_res = client.post("/api/v1/payments", headers=agent_jwt_headers, json=tampered_exec)
    assert tamper_res.status_code == 400
    assert "Execution arguments do not match" in tamper_res.json()["detail"]

    # 5. Exact arguments execution succeeds
    valid_exec = {**prop_req, "proposal_id": prop_id}
    exec_res = client.post(
        "/api/v1/payments",
        headers={**agent_jwt_headers, "Idempotency-Key": "idemp-approved-1"},
        json=valid_exec
    )
    assert exec_res.status_code == 200
    assert exec_res.json()["status"] == "COMPLETED"

    # 6. Single-use: Reuse of consumed approval rejected
    reuse_res = client.post(
        "/api/v1/payments",
        headers={**agent_jwt_headers, "Idempotency-Key": "idemp-reuse-attempt"},
        json=valid_exec
    )
    assert reuse_res.status_code == 400
    assert "Proposal is not approved" in reuse_res.json()["detail"]

def test_idempotency_key_reuse_different_payload_conflict(client, agent_jwt_headers):
    # Attempt to reuse key 'idemp-test-small-1' with different beneficiary
    diff_res = client.post(
        "/api/v1/payments",
        headers={**agent_jwt_headers, "Idempotency-Key": "idemp-test-small-1"},
        json={
            "account_id": "acc-101",
            "amount": 25000,
            "currency": "INR",
            "beneficiary": "different-beneficiary"
        }
    )
    assert diff_res.status_code == 409
    assert "Idempotency key reused with different request payload" in diff_res.json()["detail"]

def test_support_cases_and_incidents(client, lab_headers):
    cases = client.get("/api/v1/cases", headers=lab_headers).json()
    assert len(cases) >= 2
    assert cases[0]["id"] == "case-501"

    inc = client.get("/api/v1/incidents/inc-901", headers=lab_headers).json()
    assert inc["service_name"] == "payments-gateway-worker"

    rem = client.post(
        "/api/v1/incidents/inc-901/remediate",
        headers=lab_headers,
        json={"action": "restart_service"}
    ).json()
    assert rem["status"] == "resolved"
