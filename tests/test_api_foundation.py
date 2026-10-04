import os
import sys
from pathlib import Path

# Ensure repo root is on sys.path for direct python execution
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

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
    from src.core.config import settings
    orig_key = settings.API_KEY_SECRET
    settings.API_KEY_SECRET = "gate3-test-key"
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    reset_and_seed_db(db, "seed/v1_seed.json")
    db.close()
    yield
    settings.API_KEY_SECRET = orig_key
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

def test_delegated_anti_self_approval_regression(client, agent_jwt_headers, manager_jwt_headers):
    from src.core.security import create_jwt_token
    from jose import jwt
    from src.core.config import settings

    # 1. Requester creates a high-value proposal
    prop_req = {
        "account_id": "acc-101",
        "amount": 200000,
        "currency": "INR",
        "beneficiary": "merchant-safe-01"
    }
    create_res = client.post("/api/v1/payments/proposals", headers=agent_jwt_headers, json=prop_req)
    assert create_res.status_code == 200
    prop_id = create_res.json()["proposal_id"]
    requester_id = create_res.json()["requester_id"] # "agent-support-01"

    # Direct requester self-approval attempt -> 403
    self_appr = client.post(f"/api/v1/approvals/{prop_id}/approve", headers=agent_jwt_headers)
    assert self_appr.status_code == 403
    assert "Self-approval prohibited" in self_appr.json()["detail"]

    # 2. Direct delegation: manager token with delegated_by = requester -> 403
    direct_delegated_token = create_jwt_token(
        subject="delegated-manager-01",
        audience="novabank-api",
        scopes=["api:payments:write", "api:accounts:read"],
        role="manager",
        delegated_by=requester_id
    )
    direct_res = client.post(
        f"/api/v1/approvals/{prop_id}/approve",
        headers={"Authorization": f"Bearer {direct_delegated_token}"}
    )
    assert direct_res.status_code == 403
    assert "Self-approval prohibited" in direct_res.json()["detail"]

    # 3. Nested delegation: manager token with nested act chain -> 403
    nested_claims = {
        "iss": settings.JWT_ISSUER,
        "sub": "nested-manager-02",
        "aud": "novabank-api",
        "role": "manager",
        "scope": "api:payments:write api:accounts:read",
        "iat": 1700000000,
        "exp": 1900000000,
        "act": {
            "sub": "intermediate-lead",
            "act": {
                "sub": requester_id
            }
        }
    }
    nested_token = jwt.encode(nested_claims, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    nested_res = client.post(
        f"/api/v1/approvals/{prop_id}/approve",
        headers={"Authorization": f"Bearer {nested_token}"}
    )
    assert nested_res.status_code == 403
    assert "Self-approval prohibited" in nested_res.json()["detail"]

    # 4. Token exchange (1st exchange) of delegated token -> 403
    # Use direct_delegated_token as subject_token for exchange
    exchange_res1 = client.post(
        "/oauth/token",
        data={
            "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
            "subject_token": direct_delegated_token,
            "subject_token_type": "urn:ietf:params:oauth:token-type:access_token",
            "audience": "novabank-api",
            "requested_token_type": "urn:ietf:params:oauth:token-type:access_token",
            "scope": "api:payments:write api:accounts:read"
        }
    )
    assert exchange_res1.status_code == 200
    exchanged_token1 = exchange_res1.json()["access_token"]

    exchanged_res1 = client.post(
        f"/api/v1/approvals/{prop_id}/approve",
        headers={"Authorization": f"Bearer {exchanged_token1}"}
    )
    assert exchanged_res1.status_code == 403
    assert "Self-approval prohibited" in exchanged_res1.json()["detail"]

    # 5. Repeated token exchange (2nd exchange) -> 403
    exchange_res2 = client.post(
        "/oauth/token",
        data={
            "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
            "subject_token": exchanged_token1,
            "subject_token_type": "urn:ietf:params:oauth:token-type:access_token",
            "audience": "novabank-api",
            "requested_token_type": "urn:ietf:params:oauth:token-type:access_token",
            "scope": "api:payments:write"
        }
    )
    assert exchange_res2.status_code == 200
    exchanged_token2 = exchange_res2.json()["access_token"]

    exchanged_res2 = client.post(
        f"/api/v1/approvals/{prop_id}/approve",
        headers={"Authorization": f"Bearer {exchanged_token2}"}
    )
    assert exchanged_res2.status_code == 403
    assert "Self-approval prohibited" in exchanged_res2.json()["detail"]

    # 6. Legitimate independent manager approval succeeds -> 200
    clean_manager_token = create_jwt_token(
        subject="manager-priya",
        audience="novabank-api",
        scopes=["api:payments:write", "api:accounts:read"],
        role="manager",
        delegated_by="different-unrelated-agent"
    )
    clean_res = client.post(
        f"/api/v1/approvals/{prop_id}/approve",
        headers={"Authorization": f"Bearer {clean_manager_token}"}
    )
    assert clean_res.status_code == 200
    assert clean_res.json()["status"] == "approved"
    assert clean_res.json()["approver_id"] == "manager-priya"

def test_a2a_settlement_binding_regression(client):
    from src.core.security import create_jwt_token

    # Setup tokens
    negotiator_token = create_jwt_token("negotiator-bot-agent", audience="novabank-api", scopes=["api:a2a:tasks"], role="agent")
    payments_token = create_jwt_token("payments-agent-executor", audience="novabank-api", scopes=["api:payments:write", "api:a2a:tasks"], role="agent")
    foreign_agent_token = create_jwt_token("foreign-agent-99", audience="novabank-api", scopes=["api:payments:write"], role="agent")

    # 1. Negotiator creates task
    task_payload = {
        "task_type": "propose_payment",
        "input": {
            "amount": 50000,
            "destination_account": "acc-101",
            "source_account": "acc-102",
            "case_id": "case-501"
        }
    }
    create_task_res = client.post(
        "/api/v1/a2a/tasks",
        headers={"Authorization": f"Bearer {negotiator_token}"},
        json=task_payload
    )
    assert create_task_res.status_code == 200
    task_id = create_task_res.json()["task_id"]

    # 2. Foreign agent without task ownership / executor rights denied access -> 403
    foreign_get = client.get(
        f"/api/v1/a2a/tasks/{task_id}",
        headers={"Authorization": f"Bearer {foreign_agent_token}"}
    )
    assert foreign_get.status_code == 403

    # Foreign agent denied completion -> 403
    foreign_comp = client.post(
        f"/api/v1/a2a/tasks/{task_id}/complete",
        headers={"Authorization": f"Bearer {foreign_agent_token}"},
        json={"payment_id": "pay-dummy", "status": "SETTLED"}
    )
    assert foreign_comp.status_code == 403

    # 3. Owner without payment executor rights cannot complete propose_payment task -> 403
    owner_comp = client.post(
        f"/api/v1/a2a/tasks/{task_id}/complete",
        headers={"Authorization": f"Bearer {negotiator_token}"},
        json={"payment_id": "pay-dummy", "status": "SETTLED"}
    )
    assert owner_comp.status_code == 403

    # 4. Executor provides nonexistent payment ID -> 400
    nonexistent_comp = client.post(
        f"/api/v1/a2a/tasks/{task_id}/complete",
        headers={"Authorization": f"Bearer {payments_token}"},
        json={"payment_id": "nonexistent-payment-id-1234", "status": "SETTLED"}
    )
    assert nonexistent_comp.status_code == 400
    assert "does not exist in banking ledger" in nonexistent_comp.json()["detail"]

    # 5. Create real payments: one with mismatched amount (75000), one with matching amount (50000)
    pay_mismatch_res = client.post(
        "/api/v1/payments",
        headers={"Authorization": f"Bearer {payments_token}", "Idempotency-Key": "idemp-pay-mismatch"},
        json={"account_id": "acc-102", "beneficiary": "acc-101", "amount": 75000, "currency": "INR"}
    )
    assert pay_mismatch_res.status_code == 200
    mismatch_pay_id = pay_mismatch_res.json()["payment_id"]

    # Executor attempts to attach mismatched payment (75000 vs 50000 expected) -> 400
    mismatch_comp = client.post(
        f"/api/v1/a2a/tasks/{task_id}/complete",
        headers={"Authorization": f"Bearer {payments_token}"},
        json={"payment_id": mismatch_pay_id, "status": "SETTLED"}
    )
    assert mismatch_comp.status_code == 400
    assert "amount mismatch" in mismatch_comp.json()["detail"]

    # 6. Create matching payment (50000 units to acc-101)
    pay_match_res = client.post(
        "/api/v1/payments",
        headers={"Authorization": f"Bearer {payments_token}", "Idempotency-Key": "idemp-pay-match"},
        json={"account_id": "acc-102", "beneficiary": "acc-101", "amount": 50000, "currency": "INR"}
    )
    assert pay_match_res.status_code == 200
    match_pay_id = pay_match_res.json()["payment_id"]

    # 7. Executor successfully binds matching payment to task -> 200
    success_comp = client.post(
        f"/api/v1/a2a/tasks/{task_id}/complete",
        headers={"Authorization": f"Bearer {payments_token}"},
        json={"payment_id": match_pay_id, "status": "SETTLED"}
    )
    assert success_comp.status_code == 200
    task_completed = success_comp.json()
    assert task_completed["status"] == "completed"

    # 8. Attempting to complete already completed task -> 400 (terminal state invariant)
    recomplete = client.post(
        f"/api/v1/a2a/tasks/{task_id}/complete",
        headers={"Authorization": f"Bearer {payments_token}"},
        json={"payment_id": match_pay_id, "status": "SETTLED"}
    )
    assert recomplete.status_code == 400
    assert "terminal state" in recomplete.json()["detail"]

    # 9. Settlement currency mismatch check -> 400
    task_curr_res = client.post(
        "/api/v1/a2a/tasks",
        headers={"Authorization": f"Bearer {negotiator_token}"},
        json={
            "task_type": "propose_payment",
            "input": {
                "amount": 50000,
                "currency": "USD",
                "destination_account": "acc-101",
            }
        }
    )
    assert task_curr_res.status_code == 200
    curr_task_id = task_curr_res.json()["task_id"]

    pay_inr_res = client.post(
        "/api/v1/payments",
        headers={"Authorization": f"Bearer {payments_token}", "Idempotency-Key": "idemp-pay-inr"},
        json={"account_id": "acc-102", "beneficiary": "acc-101", "amount": 50000, "currency": "INR"}
    )
    assert pay_inr_res.status_code == 200
    inr_pay_id = pay_inr_res.json()["payment_id"]

    curr_comp = client.post(
        f"/api/v1/a2a/tasks/{curr_task_id}/complete",
        headers={"Authorization": f"Bearer {payments_token}"},
        json={"payment_id": inr_pay_id, "status": "SETTLED"}
    )
    assert curr_comp.status_code == 400
    assert "currency mismatch" in curr_comp.json()["detail"].lower()

    # 10. Settlement destination mismatch: source account != destination account -> 400
    # Task expects payment to destination acc-102.
    # Payment was sent from acc-102 to acc-101 (beneficiary is acc-101).
    task_dest_res = client.post(
        "/api/v1/a2a/tasks",
        headers={"Authorization": f"Bearer {negotiator_token}"},
        json={
            "task_type": "propose_payment",
            "input": {
                "amount": 50000,
                "destination_account": "acc-102",
            }
        }
    )
    assert task_dest_res.status_code == 200
    dest_task_id = task_dest_res.json()["task_id"]

    dest_comp = client.post(
        f"/api/v1/a2a/tasks/{dest_task_id}/complete",
        headers={"Authorization": f"Bearer {payments_token}"},
        json={"payment_id": inr_pay_id, "status": "SETTLED"}
    )
    assert dest_comp.status_code == 400
    assert "destination mismatch" in dest_comp.json()["detail"].lower()

    # 11. Unique task association: reusing match_pay_id already bound to task_id -> 400
    task_dup_res = client.post(
        "/api/v1/a2a/tasks",
        headers={"Authorization": f"Bearer {negotiator_token}"},
        json={
            "task_type": "propose_payment",
            "input": {
                "amount": 50000,
                "destination_account": "acc-101",
            }
        }
    )
    assert task_dup_res.status_code == 200
    dup_task_id = task_dup_res.json()["task_id"]

    dup_comp = client.post(
        f"/api/v1/a2a/tasks/{dup_task_id}/complete",
        headers={"Authorization": f"Bearer {payments_token}"},
        json={"payment_id": match_pay_id, "status": "SETTLED"}
    )
    assert dup_comp.status_code in (400, 409)
    assert "already bound to task" in dup_comp.json()["detail"]

def test_delegation_chain_depth_limit_regression(client):
    from src.core.security import create_jwt_token

    # Helper to build nested act structure of arbitrary depth
    def make_nested_act(depth: int, innermost_sub: str = "agent-requester"):
        current = {"sub": innermost_sub}
        for d in range(1, depth):
            current = {"sub": f"intermediate-agent-{d}", "act": current}
        return current

    # 1. Depth 20 is the maximum permitted depth
    act_20 = make_nested_act(20, innermost_sub="agent-requester")
    token_depth_20 = create_jwt_token(
        subject="manager-priya",
        audience="novabank-api",
        scopes=["api:accounts:read", "api:payments:write"],
        role="manager",
        act=act_20
    )

    # Calling an endpoint with depth 20 works
    res_20 = client.get("/api/v1/accounts/acc-101", headers={"Authorization": f"Bearer {token_depth_20}"})
    assert res_20.status_code == 200

    # 2. Depth 21 exceeds MAX_DELEGATION_DEPTH -> 400 Bad Request
    act_21 = make_nested_act(21, innermost_sub="agent-requester")
    token_depth_21 = create_jwt_token(
        subject="manager-priya",
        audience="novabank-api",
        scopes=["api:accounts:read", "api:payments:write"],
        role="manager",
        act=act_21
    )

    # Direct presentation of over-depth token fails-closed with 400
    res_21 = client.get("/api/v1/accounts/acc-101", headers={"Authorization": f"Bearer {token_depth_21}"})
    assert res_21.status_code == 400
    assert "exceeds maximum permitted depth of 20" in res_21.json()["detail"]

    # 3. Token exchange with subject_token already at depth 21 fails with 400
    exchange_over = client.post(
        "/oauth/token",
        data={
            "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
            "subject_token": token_depth_21,
            "subject_token_type": "urn:ietf:params:oauth:token-type:access_token",
            "audience": "novabank-api",
            "requested_token_type": "urn:ietf:params:oauth:token-type:access_token",
            "scope": "api:payments:write"
        }
    )
    assert exchange_over.status_code == 400
    assert "exceeds maximum permitted depth of 20" in exchange_over.json()["detail"]

    # 4. Token exchange that would push depth from 20 to 21 fails with 400
    token_mcp_20 = create_jwt_token(
        subject="agent-requester",
        audience="novabank-mcp",
        scopes=["mcp:tools", "tools:call"],
        role="agent",
        act=act_20
    )
    exchange_push = client.post(
        "/oauth/token",
        data={
            "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
            "subject_token": token_mcp_20,
            "subject_token_type": "urn:ietf:params:oauth:token-type:access_token",
            "audience": "novabank-api",
            "requested_token_type": "urn:ietf:params:oauth:token-type:access_token",
            "scope": "api:payments:write"
        }
    )
    assert exchange_push.status_code == 400
    assert "exceeds maximum permitted depth of 20" in exchange_push.json()["detail"]

def test_a2a_concurrent_settlement_binding_race(client):
    import concurrent.futures
    from src.core.security import create_jwt_token
    from src.core.database import SessionLocal
    from src.models.db_models import A2ATask, PaymentTaskBinding

    negotiator_token = create_jwt_token("negotiator-bot-agent", audience="novabank-api", scopes=["api:a2a:tasks"], role="agent")
    payments_token = create_jwt_token("payments-agent-executor", audience="novabank-api", scopes=["api:payments:write", "api:a2a:tasks"], role="agent")

    # 1. Create two separate tasks expecting the same payment parameters
    task1_res = client.post(
        "/api/v1/a2a/tasks",
        headers={"Authorization": f"Bearer {negotiator_token}"},
        json={
            "task_type": "propose_payment",
            "input": {"amount": 50000, "currency": "INR", "destination_account": "acc-101"}
        }
    )
    assert task1_res.status_code == 200
    task1_id = task1_res.json()["task_id"]

    task2_res = client.post(
        "/api/v1/a2a/tasks",
        headers={"Authorization": f"Bearer {negotiator_token}"},
        json={
            "task_type": "propose_payment",
            "input": {"amount": 50000, "currency": "INR", "destination_account": "acc-101"}
        }
    )
    assert task2_res.status_code == 200
    task2_id = task2_res.json()["task_id"]

    # 2. Create single settled payment in backend ledger
    pay_res = client.post(
        "/api/v1/payments",
        headers={"Authorization": f"Bearer {payments_token}", "Idempotency-Key": "idemp-concurrent-settle-race"},
        json={"account_id": "acc-102", "beneficiary": "acc-101", "amount": 50000, "currency": "INR"}
    )
    assert pay_res.status_code == 200
    race_payment_id = pay_res.json()["payment_id"]

    # 3. Concurrently attempt to complete both tasks with the exact same payment_id
    def attempt_complete(target_task_id):
        # Create a fresh TestClient in thread or reuse client
        with TestClient(app) as thread_client:
            return thread_client.post(
                f"/api/v1/a2a/tasks/{target_task_id}/complete",
                headers={"Authorization": f"Bearer {payments_token}"},
                json={"payment_id": race_payment_id, "status": "SETTLED"}
            )

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        f1 = executor.submit(attempt_complete, task1_id)
        f2 = executor.submit(attempt_complete, task2_id)
        res1 = f1.result()
        res2 = f2.result()

    statuses = sorted([res1.status_code, res2.status_code])
    assert statuses == [200, 409], f"Expected exactly one 200 and one 409, got {statuses}"

    # 4. Verify database state: exactly ONE task is completed, and only one binding exists
    db = SessionLocal()
    try:
        completed_tasks = db.query(A2ATask).filter(
            A2ATask.id.in_([task1_id, task2_id]),
            A2ATask.status == "completed"
        ).all()
        assert len(completed_tasks) == 1, f"Expected exactly 1 completed task, found {len(completed_tasks)}"

        bindings = db.query(PaymentTaskBinding).filter(
            PaymentTaskBinding.payment_id == race_payment_id
        ).all()
        assert len(bindings) == 1, f"Expected exactly 1 payment binding, found {len(bindings)}"
        assert bindings[0].task_id == completed_tasks[0].id
    finally:
        db.close()

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", __file__]))
