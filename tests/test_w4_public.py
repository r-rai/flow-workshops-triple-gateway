"""Tests for Workshop 4 Public Observation Service."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Prepare test environment variables before importing app
ACCESS_CODE = "FLO-W4-TEST-CODE"
tmp_dir = tempfile.TemporaryDirectory()
code_file = Path(tmp_dir.name) / "test_access_code.txt"
code_file.write_text(ACCESS_CODE)

os.environ["W4_OBSERVATION_ONLY"] = "true"
os.environ["W4_ENABLE_VULNERABLE"] = "false"
os.environ["ACTIVE_PROFILE"] = "w4"
os.environ["W4_ACCESS_CODE_FILE"] = str(code_file)
os.environ["W4_EVIDENCE_DB"] = "data/w4-public-evidence.sqlite"
os.environ["W4_SESSION_DB"] = str(Path(tmp_dir.name) / "test_sessions.sqlite")

from src.demo.public_incident import app, validate_environment


@pytest.fixture
def client():
    return TestClient(app)


def test_fail_closed_validation():
    # Test that invalid configuration strictly raises RuntimeError
    orig_obs = os.environ["W4_OBSERVATION_ONLY"]
    try:
        os.environ["W4_OBSERVATION_ONLY"] = "false"
        with pytest.raises(RuntimeError, match="W4_OBSERVATION_ONLY"):
            validate_environment()
    finally:
        os.environ["W4_OBSERVATION_ONLY"] = orig_obs

    orig_vuln = os.environ["W4_ENABLE_VULNERABLE"]
    try:
        os.environ["W4_ENABLE_VULNERABLE"] = "true"
        with pytest.raises(RuntimeError, match="W4_ENABLE_VULNERABLE"):
            validate_environment()
    finally:
        os.environ["W4_ENABLE_VULNERABLE"] = orig_vuln


def test_public_routes_unauthenticated(client):
    # Index redirects to /workshop-4
    r = client.get("/", follow_redirects=False)
    assert r.status_code == 307
    assert r.headers["location"] == "/workshop-4"

    # Healthz
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json()["mode"] == "observation"

    # UI is accessible
    r = client.get("/workshop-4")
    assert r.status_code == 200
    assert "Incident Room" in r.text

    # Protected APIs require auth
    assert client.get("/demo-api/workshop-4/runs").status_code == 401
    assert client.get("/demo-api/workshop-4/readiness").status_code == 401
    assert client.get("/demo-api/workshop-4/runs/any-id").status_code == 401


def test_login_and_viewer_lifecycle(client):
    # Invalid access code
    r = client.post("/demo-api/login", json={"access_code": "WRONG_CODE"})
    assert r.status_code == 401

    # Valid access code
    r = client.post("/demo-api/login", json={"access_code": ACCESS_CODE})
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "authenticated"
    assert data["role"] == "viewer"
    assert "flo_demo_session" in client.cookies

    # Read readiness
    r = client.get("/demo-api/workshop-4/readiness")
    assert r.status_code == 200
    readiness = r.json()
    assert readiness["observation_only"] is True
    assert readiness["recording"]["available"] is True
    assert readiness["recording"]["run_count"] == 11

    # Read runs list
    r = client.get("/demo-api/workshop-4/runs")
    assert r.status_code == 200
    runs = r.json()
    assert len(runs) == 11
    scenarios = [x["scenario"] for x in runs]
    assert "vulnerable_replay" in scenarios
    assert "legitimate_delegation" in scenarios

    # Read run detail & evidence
    run_id = runs[0]["run_id"]
    r = client.get(f"/demo-api/workshop-4/runs/{run_id}")
    assert r.status_code == 200
    assert r.json()["run_id"] == run_id

    r = client.get(f"/demo-api/workshop-4/runs/{run_id}/evidence")
    assert r.status_code == 200
    assert r.headers["cache-control"] == "no-store"

    # Logout
    r = client.post("/demo-api/logout")
    assert r.status_code == 200

    # Subsequent access fails
    r = client.get("/demo-api/workshop-4/runs")
    assert r.status_code == 401


def test_all_mutations_forbidden_even_when_authenticated(client):
    # Log in
    client.post("/demo-api/login", json={"access_code": ACCESS_CODE})

    # Run creation forbidden
    r = client.post("/demo-api/workshop-4/runs", json={"scenario": "budget_denial", "request_id": "test-req"})
    assert r.status_code == 403

    # Reviewer elevation forbidden
    r = client.post("/demo-api/workshop-4/reviewer-session", json={"password": "any"})
    assert r.status_code == 403

    # Approval / Decision forbidden
    r = client.post("/demo-api/workshop-4/runs/run-123/decision", json={"decision": "approve"})
    assert r.status_code == 403

    # Traces mutation forbidden
    r = client.post("/demo-api/workshop-4/runs/run-123/traces", json={})
    assert r.status_code == 403

    # Reconcile forbidden
    r = client.post("/demo-api/workshop-4/runs/run-123/reconcile", json={})
    assert r.status_code == 403


def test_absent_customer_and_admin_routes(client):
    client.post("/demo-api/login", json={"access_code": ACCESS_CODE})

    # Customer and admin endpoints must not exist
    for path in [
        "/demo-api/chat",
        "/demo-api/dashboard",
        "/demo-api/banking/card/lock",
        "/api/v1/payments",
        "/api/v1/admin",
        "/oauth/token",
        "/mcp",
        "/docs",
        "/openapi.json",
    ]:
        r = client.get(path)
        assert r.status_code in (404, 405), f"Path {path} returned {r.status_code}"


def test_security_headers_present(client):
    r = client.get("/workshop-4")
    assert r.headers.get("x-content-type-options") == "nosniff"
    assert r.headers.get("x-frame-options") == "DENY"
    assert r.headers.get("referrer-policy") == "no-referrer"
    assert "frame-ancestors 'none'" in r.headers.get("content-security-policy", "")
