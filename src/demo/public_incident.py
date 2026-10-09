"""Dedicated Workshop 4 Public Observation Service.

Provides a secure, mobile-friendly, observation-only Incident Room.
Zero banking, replay, approval, or execution services are exposed.
All evidence is read directly from an immutable SQLite database in read-only mode.
"""
from __future__ import annotations

import collections
import hashlib
import json
import logging
import os
from pathlib import Path
import secrets
import sqlite3
import time
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger("flobank.w4_public")

STATIC_DIR = Path(__file__).parent / "static"

SCENARIOS = {
    "vulnerable_replay": "Replay the isolated ₹90 lakh incident",
    "budget_denial": "Gate 1: exceed inference headroom",
    "prohibited_beneficiary": "Gate 2: prohibited beneficiary",
    "excessive_amount": "Gate 2: excessive amount",
    "permitted_payment": "Gate 2: permitted ₹250 payment",
    "policy_outage": "Gate 2: test a stopped policy service",
    "wrong_audience": "Gate 3: MCP token at the API",
    "insufficient_scope": "Gate 3: read-only payment attempt",
    "scope_escalation": "Gate 3: unauthorized scope exchange",
    "valid_exchange": "Gate 3: permitted scope exchange",
    "legitimate_delegation": "A2A: independently approve ₹1,500 settlement",
}

# Strict startup validation (fail-closed)
def validate_environment():
    obs = os.getenv("W4_OBSERVATION_ONLY", "").strip().lower()
    if obs != "true":
        raise RuntimeError("FATAL: W4_OBSERVATION_ONLY must be explicitly set to 'true'")

    vuln = os.getenv("W4_ENABLE_VULNERABLE", "").strip().lower()
    if vuln != "false":
        raise RuntimeError("FATAL: W4_ENABLE_VULNERABLE must be explicitly set to 'false'")

    profile = os.getenv("ACTIVE_PROFILE", "").strip().lower()
    if profile != "w4":
        raise RuntimeError("FATAL: ACTIVE_PROFILE must be set to 'w4'")

    code_file = os.getenv("W4_ACCESS_CODE_FILE")
    if not code_file or not Path(code_file).is_file():
        raise RuntimeError(f"FATAL: W4_ACCESS_CODE_FILE is missing or invalid: {code_file}")
    with open(code_file, "r", encoding="utf-8") as f:
        code = f.read().strip()
    if not code:
        raise RuntimeError("FATAL: W4_ACCESS_CODE_FILE contains an empty access code")

    ev_db = os.getenv("W4_EVIDENCE_DB", "data/w4-public-evidence.sqlite")
    if not Path(ev_db).is_file():
        raise RuntimeError(f"FATAL: W4_EVIDENCE_DB not found: {ev_db}")

    # Test read-only DB access
    try:
        conn = sqlite3.connect(f"file:{ev_db}?mode=ro", uri=True)
        cur = conn.cursor()
        count = cur.execute("SELECT count(*) FROM runs").fetchone()[0]
        conn.close()
        if count == 0:
            raise RuntimeError("FATAL: W4_EVIDENCE_DB has 0 runs")
    except Exception as e:
        raise RuntimeError(f"FATAL: Failed to query W4_EVIDENCE_DB in read-only mode: {e}")

validate_environment()

# In-memory IP rate limiter for login attempts (5 failures in 60s)
_failed_logins: dict[str, list[float]] = collections.defaultdict(list)

def check_login_rate_limit(client_ip: str):
    now = time.time()
    attempts = [t for t in _failed_logins[client_ip] if now - t < 60]
    _failed_logins[client_ip] = attempts
    if len(attempts) >= 5:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed access attempts. Please wait 60 seconds.",
        )

def record_failed_login(client_ip: str):
    _failed_logins[client_ip].append(time.time())

# Session database helper
def get_session_db_path() -> Path:
    p = Path(os.getenv("W4_SESSION_DB", "data/w4-public-sessions.sqlite"))
    p.parent.mkdir(parents=True, exist_ok=True)
    return p

def init_session_db():
    p = get_session_db_path()
    conn = sqlite3.connect(p)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            hash_id TEXT PRIMARY KEY,
            role TEXT NOT NULL,
            created_at REAL NOT NULL,
            expires_at REAL NOT NULL
        )
    """
    )
    conn.commit()
    conn.close()

init_session_db()

def hash_token(token: str) -> str:
    return hashlib.sha256((token or "").encode("utf-8")).hexdigest()

def create_session() -> tuple[str, float]:
    token = secrets.token_urlsafe(32)
    h = hash_token(token)
    now = time.time()
    expires_at = now + 10800  # 3 hours TTL
    conn = sqlite3.connect(get_session_db_path())
    conn.execute("DELETE FROM sessions WHERE expires_at < ?", (now,))
    conn.execute(
        "INSERT INTO sessions (hash_id, role, created_at, expires_at) VALUES (?, ?, ?, ?)",
        (h, "viewer", now, expires_at),
    )
    conn.commit()
    conn.close()
    return token, expires_at

def verify_session(token: str | None) -> dict | None:
    if not token:
        return None
    h = hash_token(token)
    now = time.time()
    conn = sqlite3.connect(get_session_db_path())
    row = conn.execute(
        "SELECT role, expires_at FROM sessions WHERE hash_id = ?", (h,)
    ).fetchone()
    conn.close()
    if row and row[1] > now:
        return {"role": row[0], "expires_at": row[1]}
    return None

def revoke_session(token: str | None):
    if not token:
        return
    h = hash_token(token)
    conn = sqlite3.connect(get_session_db_path())
    conn.execute("DELETE FROM sessions WHERE hash_id = ?", (h,))
    conn.commit()
    conn.close()

# Evidence DB query helper (strictly read-only)
def get_evidence_conn():
    ev_path = os.getenv("W4_EVIDENCE_DB", "data/w4-public-evidence.sqlite")
    return sqlite3.connect(f"file:{ev_path}?mode=ro", uri=True)

# Pydantic Schemas
class LoginPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    access_code: str = Field(min_length=1, max_length=120)

app = FastAPI(
    title="Flo Bank · Workshop 4 Incident Room (Observation)",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

# Viewer Dependency
async def require_viewer(request: Request) -> dict:
    token = request.cookies.get("flo_demo_session")
    sess = verify_session(token)
    if not sess:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Participant event access code required.",
        )
    return sess

# Security headers middleware
@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    # Enforce request body size limit for login (max 4 KiB)
    if request.url.path == "/demo-api/login" and request.method == "POST":
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > 4096:
            return Response(content="Payload Too Large", status_code=413)

    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; connect-src 'self'; frame-ancestors 'none';"
    )
    return response

# Public Root & Assets
@app.api_route("/", methods=["GET", "HEAD"], include_in_schema=False)
async def index():
    return RedirectResponse(url="/workshop-4", status_code=status.HTTP_307_TEMPORARY_REDIRECT)

@app.api_route("/healthz", methods=["GET", "HEAD"], include_in_schema=False)
async def healthz():
    return {"status": "ok", "mode": "observation", "profile": "w4"}

@app.api_route("/workshop-4", methods=["GET", "HEAD"], include_in_schema=False)
async def incident_public():
    target = STATIC_DIR / "incident_public.html"
    if not target.is_file():
        target = STATIC_DIR / "incident.html"
    return FileResponse(target, headers={"Cache-Control": "no-cache"})

# Safe static assets mount
app.mount("/demo-assets", StaticFiles(directory=STATIC_DIR), name="demo-assets")

# API Router
demo_api = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

@demo_api.post("/login")
async def login(payload: LoginPayload, request: Request, response: Response):
    client_ip = request.client.host if request.client else "unknown"
    check_login_rate_limit(client_ip)

    code_file = os.getenv("W4_ACCESS_CODE_FILE")
    with open(code_file, "r", encoding="utf-8") as f:
        expected = f.read().strip()

    if not secrets.compare_digest(payload.access_code.strip(), expected):
        record_failed_login(client_ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid event access code.",
        )

    token, expires_at = create_session()
    is_https = request.url.scheme == "https" or request.headers.get("x-forwarded-proto") == "https"
    # Secure cookie scoped to root
    response.set_cookie(
        key="flo_demo_session",
        value=token,
        httponly=True,
        samesite="strict",
        secure=is_https,
        max_age=10800,
        path="/",
    )
    return {
        "status": "authenticated",
        "role": "viewer",
        "expires_in": 10800,
        "message": "Welcome to Workshop 4 Incident Room observation.",
    }

@demo_api.post("/logout")
async def logout(request: Request, response: Response):
    token = request.cookies.get("flo_demo_session")
    revoke_session(token)
    response.delete_cookie(key="flo_demo_session", path="/")
    return {"status": "logged_out"}

@demo_api.get("/workshop-4/readiness")
async def readiness(session: dict = Depends(require_viewer)):
    conn = get_evidence_conn()
    cur = conn.cursor()
    count = cur.execute("SELECT count(*) FROM runs").fetchone()[0]
    meta_rows = cur.execute("SELECT key, value FROM metadata").fetchall()
    meta = dict(meta_rows)
    conn.close()

    return {
        "profile": "w4",
        "observation_only": True,
        "single_instance": True,
        "mode": "recorded_observation",
        "scenarios": [{"id": k, "title": v} for k, v in SCENARIOS.items()],
        "recording": {
            "available": True,
            "capture_timestamp": meta.get("timestamp", "2026-10-05T170259Z"),
            "run_count": count,
            "version": meta.get("version", "1.0.0"),
        },
        "reviewer_configured": False,
        "reviewer_authenticated": False,
        "checks": {
            "evidence_db": {"reachable": True},
            "session_store": {"reachable": True},
        },
    }

@demo_api.get("/workshop-4/runs")
async def list_runs(session: dict = Depends(require_viewer)):
    conn = get_evidence_conn()
    cur = conn.cursor()
    rows = cur.execute("SELECT data FROM runs ORDER BY rowid ASC").fetchall()
    conn.close()
    return [json.loads(r[0]) for r in rows]

@demo_api.get("/workshop-4/runs/{run_id}")
async def get_run_detail(run_id: str, response: Response, session: dict = Depends(require_viewer)):
    conn = get_evidence_conn()
    cur = conn.cursor()
    row = cur.execute("SELECT data FROM runs WHERE id = ?", (run_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Run not found in curated evidence.")
    response.headers["Cache-Control"] = "no-store"
    return json.loads(row[0])

@demo_api.get("/workshop-4/runs/{run_id}/evidence")
async def get_run_evidence(run_id: str, response: Response, session: dict = Depends(require_viewer)):
    conn = get_evidence_conn()
    cur = conn.cursor()
    row = cur.execute("SELECT data FROM runs WHERE id = ?", (run_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Run not found in curated evidence.")
    response.headers["Cache-Control"] = "no-store"
    return json.loads(row[0])

# Explicitly Denied Mutating Routes (403 Forbidden)
@demo_api.post("/workshop-4/runs")
async def deny_create_run():
    raise HTTPException(
        status_code=403,
        detail="Run creation is disabled. This is an observation-only instance for participant smartphones.",
    )

@demo_api.post("/workshop-4/reviewer-session")
async def deny_reviewer_login():
    raise HTTPException(
        status_code=403,
        detail="Reviewer role elevation is disabled on the public observation deployment.",
    )

@demo_api.post("/workshop-4/runs/{run_id}/decision")
async def deny_decision(run_id: str):
    raise HTTPException(
        status_code=403,
        detail="Approval and rejection execution are disabled on this observation deployment.",
    )

@demo_api.post("/workshop-4/runs/{run_id}/traces")
async def deny_traces(run_id: str):
    raise HTTPException(
        status_code=403,
        detail="Collector live queries are disabled. Curated span summaries are preloaded in evidence.",
    )

@demo_api.post("/workshop-4/runs/{run_id}/reconcile")
async def deny_reconcile(run_id: str):
    raise HTTPException(
        status_code=403,
        detail="Ledger mutation and reconciliation are disabled on this observation deployment.",
    )

app.mount("/demo-api", demo_api)
