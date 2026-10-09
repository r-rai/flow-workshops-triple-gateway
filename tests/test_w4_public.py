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

# Import-time validation runs with temporary settings, then restores the process
# environment so collecting public tests cannot disable the presenter suite.
with pytest.MonkeyPatch.context() as setup:
    setup.setenv("W4_OBSERVATION_ONLY", "true")
    setup.setenv("W4_ENABLE_VULNERABLE", "false")
    setup.setenv("ACTIVE_PROFILE", "w4")
    setup.setenv("W4_ACCESS_CODE_FILE", str(code_file))
    setup.setenv("W4_EVIDENCE_DB", "data/w4-public-evidence.sqlite")
    setup.setenv("W4_SESSION_DB", str(Path(tmp_dir.name) / "test_sessions.sqlite"))
    setup.setenv("W4_EVENT_CUTOFF_UTC", "2099-01-01T00:00:00Z")
    from src.demo.public_incident import app, validate_environment


@pytest.fixture
def client(monkeypatch, tmp_path):
    from src.demo import public_incident
    monkeypatch.setenv("W4_OBSERVATION_ONLY", "true")
    monkeypatch.setenv("W4_ENABLE_VULNERABLE", "false")
    monkeypatch.setenv("ACTIVE_PROFILE", "w4")
    monkeypatch.setenv("W4_ACCESS_CODE_FILE", str(code_file))
    monkeypatch.setenv("W4_EVIDENCE_DB", "data/w4-public-evidence.sqlite")
    monkeypatch.setenv("W4_SESSION_DB", str(tmp_path / "sessions.sqlite"))
    monkeypatch.setenv("W4_EVENT_CUTOFF_UTC", "2099-01-01T00:00:00Z")
    public_incident.init_session_db()
    public_incident._failed_logins.clear()
    return TestClient(app, base_url="https://testserver")


def test_fail_closed_validation(client):
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


def test_event_cutoff_rejection(client, monkeypatch):
    # Set cutoff in the past
    monkeypatch.setenv("W4_EVENT_CUTOFF_UTC", "2020-01-01T00:00:00Z")
    r = client.post("/demo-api/login", json={"access_code": ACCESS_CODE})
    assert r.status_code == 403
    assert "concluded" in r.json()["detail"].lower()


def test_budget_denial_filler_cleaned(client):
    # Log in and verify budget denial has no 400k x's
    client.post("/demo-api/login", json={"access_code": ACCESS_CODE})
    r = client.get("/demo-api/workshop-4/runs")
    assert r.status_code == 200
    runs = r.json()
    bd = next(x for x in runs if x["scenario"] == "budget_denial")
    raw_str = str(bd)
    assert raw_str.count("x") < 50
    assert "399,864 filler characters" in raw_str



@pytest.mark.parametrize("streamed", [False, True])
def test_oversized_login_is_rejected_before_creating_session(client, streamed):
    import json
    from src.demo import public_incident
    body = b" " * 5000 + json.dumps({"access_code": ACCESS_CODE}).encode()
    response = client.post("/demo-api/login", content=iter([body[:3000], body[3000:]]) if streamed else body,
                           headers={"Content-Type": "application/json"})
    assert response.status_code == 413
    import sqlite3
    with sqlite3.connect(public_incident.get_session_db_path()) as conn:
        assert conn.execute("SELECT count(*) FROM sessions").fetchone()[0] == 0


def test_unicode_access_code_is_rejected_without_server_error(client):
    response = client.post("/demo-api/login", json={"access_code": "₹-invalid"})
    assert response.status_code == 401


def test_cookie_is_secure_even_for_direct_http_login(client):
    with TestClient(app, base_url="http://testserver") as upstream:
        response = upstream.post("/demo-api/login", json={"access_code": ACCESS_CODE})
        assert response.status_code == 200
        assert "; Secure" in response.headers["set-cookie"]


@pytest.mark.parametrize("path", ["/demo-api/login", "/demo-api/logout"])
def test_cross_origin_session_changes_rejected(client, path):
    response = client.post(path, json={"access_code": ACCESS_CODE},
                           headers={"Origin": "https://untrusted.example"})
    assert response.status_code == 403


def test_authenticated_reads_are_not_cacheable(client):
    client.post("/demo-api/login", json={"access_code": ACCESS_CODE})
    for path in ["/demo-api/workshop-4/runs", "/demo-api/workshop-4/readiness"]:
        response = client.get(path)
        assert response.status_code == 200
        assert response.headers["cache-control"] == "no-store"


@pytest.mark.parametrize("asset", ["index.html", "incident.html", "incident.js", "governance.html", "app.js"])
def test_legacy_assets_not_served(client, asset):
    assert client.get("/demo-assets/" + asset).status_code == 404


def test_health_reports_missing_recording(client, monkeypatch, tmp_path):
    monkeypatch.setenv("W4_EVIDENCE_DB", str(tmp_path / "missing.sqlite"))
    assert client.get("/healthz").status_code == 503


@pytest.mark.parametrize("cutoff", ["", "invalid", "2026-10-10T06:30:00", "NaN"])
def test_invalid_cutoff_fails_closed(client, monkeypatch, cutoff):
    monkeypatch.setenv("W4_EVENT_CUTOFF_UTC", cutoff)
    with pytest.raises(RuntimeError, match="W4_EVENT_CUTOFF_UTC"):
        validate_environment()



def test_epoch_cutoff_still_closes_admissions(client, monkeypatch):
    monkeypatch.setenv("W4_EVENT_CUTOFF_UTC", "1970-01-01T00:00:00Z")
    assert client.post("/demo-api/login", json={"access_code": ACCESS_CODE}).status_code == 403
    assert client.get("/demo-api/workshop-4/runs").status_code == 401


def test_login_limit_accumulates_separate_asgi_chunks(client):
    import asyncio
    from src.demo.public_incident import PublicSessionBoundary
    called = False
    sent = []
    chunks = iter([
        {"type": "http.request", "body": b" " * 3000, "more_body": True},
        {"type": "http.request", "body": b" " * 3000, "more_body": False},
    ])

    async def downstream(scope, receive, send):
        nonlocal called
        called = True

    async def receive():
        return next(chunks)

    async def send(message):
        sent.append(message)

    scope = {"type": "http", "method": "POST", "path": "/demo-api/login", "headers": []}
    asyncio.run(PublicSessionBoundary(downstream)(scope, receive, send))
    assert not called
    assert sent[0]["status"] == 413



def test_cutoff_boundary_closes_an_existing_viewer(client, monkeypatch):
    import sqlite3
    from src.demo import public_incident
    cutoff = public_incident.get_cutoff_timestamp()
    monkeypatch.setattr(public_incident.time, "time", lambda: cutoff - 60)
    assert client.post("/demo-api/login", json={"access_code": ACCESS_CODE}).status_code == 200
    token = client.cookies.get("flo_demo_session")
    assert client.get("/demo-api/workshop-4/runs").status_code == 200
    with sqlite3.connect(public_incident.get_session_db_path()) as conn:
        assert conn.execute("SELECT expires_at FROM sessions").fetchone()[0] == cutoff
    monkeypatch.setattr(public_incident.time, "time", lambda: cutoff)
    assert client.post("/demo-api/login", json={"access_code": ACCESS_CODE}).status_code == 403
    assert client.get("/demo-api/workshop-4/runs", headers={"Cookie": "flo_demo_session=" + token}).status_code == 401


def test_admission_caps_survive_logout(client, monkeypatch):
    from src.demo import public_incident
    monkeypatch.setattr(public_incident, "MAX_ACTIVE_SESSIONS", 1)
    monkeypatch.setattr(public_incident, "MAX_TOTAL_ADMISSIONS", 2)
    assert client.post("/demo-api/login", json={"access_code": ACCESS_CODE}).status_code == 200
    assert client.post("/demo-api/login", json={"access_code": ACCESS_CODE}).status_code == 429
    assert client.post("/demo-api/logout").status_code == 200
    assert client.post("/demo-api/login", json={"access_code": ACCESS_CODE}).status_code == 200
    assert client.post("/demo-api/logout").status_code == 200
    assert client.post("/demo-api/login", json={"access_code": ACCESS_CODE}).status_code == 403
