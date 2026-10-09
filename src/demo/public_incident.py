"""Dedicated Workshop 4 Public Observation Service.

Provides a secure, mobile-friendly, observation-only Incident Room.
Zero banking, replay, approval, or execution services are exposed.
All evidence is read directly from an immutable SQLite database in read-only mode.
"""
from __future__ import annotations

import asyncio
import collections
import hashlib
import json
import logging
import os
from pathlib import Path
import secrets
import sqlite3
import time
from datetime import datetime, timedelta

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
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

def get_cutoff_timestamp() -> float:
    raw = os.getenv("W4_EVENT_CUTOFF_UTC", "").strip()
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if dt.tzinfo is None or dt.utcoffset() != timedelta(0):
            raise ValueError("UTC timezone required")
        return dt.timestamp()
    except (ValueError, OverflowError) as exc:
        raise RuntimeError("W4_EVENT_CUTOFF_UTC must be an explicit ISO-8601 UTC timestamp") from exc


# Strict startup validation (fail-closed)
def validate_environment():
    get_cutoff_timestamp()
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

MAX_FAILED_LOGINS_PER_MIN = int(os.getenv("W4_MAX_FAILED_LOGINS_PER_MIN", "30"))
_failed_logins: dict[str, list[float]] = collections.defaultdict(list)

def check_login_rate_limit(client_ip: str):
    now = time.time()
    attempts = [t for t in _failed_logins[client_ip] if now - t < 60]
    _failed_logins[client_ip] = attempts
    if len(attempts) >= MAX_FAILED_LOGINS_PER_MIN:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed access attempts from this network. Please wait 60 seconds.",
        )

def record_failed_login(client_ip: str):
    _failed_logins[client_ip].append(time.time())

def reset_failed_logins(client_ip: str):
    _failed_logins.pop(client_ip, None)


MAX_ACTIVE_SESSIONS = int(os.getenv("W4_MAX_ACTIVE_SESSIONS", "250"))
MAX_TOTAL_ADMISSIONS = int(os.getenv("W4_MAX_TOTAL_ADMISSIONS", "500"))

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
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS metrics (
            key TEXT PRIMARY KEY,
            value INTEGER NOT NULL
        )
    """
    )
    conn.execute("INSERT OR IGNORE INTO metrics VALUES ('admissions_count', 0)")
    conn.commit()
    conn.close()

init_session_db()

def hash_token(token: str) -> str:
    return hashlib.sha256((token or "").encode("utf-8")).hexdigest()

def create_session() -> tuple[str, float]:
    cutoff = get_cutoff_timestamp()
    now = time.time()
    if now >= cutoff:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The workshop event has concluded. Observation room admissions are closed.",
        )

    conn = sqlite3.connect(get_session_db_path())
    conn.execute("DELETE FROM sessions WHERE expires_at < ?", (now,))

    # Check total admissions cap
    row = conn.execute("SELECT value FROM metrics WHERE key='admissions_count'").fetchone()
    total_adm = row[0] if row else 0
    if total_adm >= MAX_TOTAL_ADMISSIONS:
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Total workshop admission limit reached for this session.",
        )

    # Check active concurrent sessions cap
    active_count = conn.execute("SELECT count(*) FROM sessions WHERE expires_at > ?", (now,)).fetchone()[0]
    if active_count >= MAX_ACTIVE_SESSIONS:
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Workshop participant capacity reached (maximum concurrent active sessions). Please try again shortly.",
        )

    token = secrets.token_urlsafe(32)
    h = hash_token(token)
    expires_at = now + 10800  # 3 hours TTL
    if expires_at > cutoff:
        expires_at = cutoff

    conn.execute(
        "INSERT INTO sessions (hash_id, role, created_at, expires_at) VALUES (?, ?, ?, ?)",
        (h, "viewer", now, expires_at),
    )
    conn.execute("UPDATE metrics SET value = value + 1 WHERE key='admissions_count'")
    conn.commit()
    conn.close()
    return token, expires_at

def verify_session(token: str | None) -> dict | None:
    if not token:
        return None
    cutoff = get_cutoff_timestamp()
    now = time.time()
    if now >= cutoff:
        return None
    h = hash_token(token)
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

class PublicSessionBoundary:
    """Bound login bytes before JSON parsing, including streamed/chunked bodies."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        path = scope.get("path", "")
        if scope["type"] != "http" or scope["method"] != "POST" or path not in {
            "/demo-api/login", "/demo-api/logout"
        }:
            return await self.app(scope, receive, send)
        headers = dict(scope["headers"])
        origin = headers.get(b"origin")
        expected = os.getenv("W4_PUBLIC_ORIGIN", "https://w4.ravirai.in").encode()
        if origin is not None and origin != expected:
            return await JSONResponse({"detail": "Cross-origin session changes are forbidden."}, status_code=403)(scope, receive, send)
        if path == "/demo-api/logout":
            return await self.app(scope, receive, send)
        length = headers.get(b"content-length")
        if length is not None:
            if not length.isdigit() or len(length) > 10:
                return await JSONResponse({"detail": "Invalid Content-Length."}, status_code=400)(scope, receive, send)
            if int(length) > 4096:
                return await JSONResponse({"detail": "Login body exceeds 4 KiB."}, status_code=413)(scope, receive, send)
        body = bytearray()
        try:
            async with asyncio.timeout(5):
                while True:
                    message = await receive()
                    if message["type"] == "http.disconnect":
                        return
                    chunk = message.get("body", b"")
                    if len(body) + len(chunk) > 4096:
                        return await JSONResponse({"detail": "Login body exceeds 4 KiB."}, status_code=413)(scope, receive, send)
                    body.extend(chunk)
                    if not message.get("more_body", False):
                        break
        except TimeoutError:
            return await JSONResponse({"detail": "Login body timed out."}, status_code=408)(scope, receive, send)
        delivered = False

        async def bounded_receive():
            nonlocal delivered
            if not delivered:
                delivered = True
                return {"type": "http.request", "body": bytes(body), "more_body": False}
            return await receive()

        return await self.app(scope, bounded_receive, send)


app = FastAPI(
    title="Flo Bank · Workshop 4 Incident Room (Observation)",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

app.add_middleware(PublicSessionBoundary)

# Viewer Dependency
async def require_viewer(request: Request) -> dict:
    cutoff = get_cutoff_timestamp()
    if time.time() >= cutoff:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The workshop event has concluded. Observation room sessions are closed.",
        )
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
    response = await call_next(request)
    if request.url.path.startswith("/demo-api/"):
        response.headers["Cache-Control"] = "no-store"
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
    try:
        with get_evidence_conn() as conn:
            if conn.execute("SELECT count(*) FROM runs").fetchone()[0] == 0:
                raise sqlite3.DatabaseError("Empty recording")
            conn.execute("SELECT key, value FROM metadata LIMIT 1").fetchall()
        with sqlite3.connect(f"file:{get_session_db_path()}?mode=ro", uri=True) as conn:
            conn.execute("SELECT count(*) FROM sessions").fetchone()
    except (sqlite3.Error, OSError):
        return JSONResponse({"status": "unavailable", "mode": "observation"}, status_code=503)
    return {"status": "ok", "mode": "observation", "profile": "w4"}

@app.api_route("/workshop-4", methods=["GET", "HEAD"], include_in_schema=False)
async def incident_public():
    target = STATIC_DIR / "incident_public.html"
    if not target.is_file():
        raise HTTPException(503, "Participant page unavailable.")
    return FileResponse(target, headers={"Cache-Control": "no-cache"})

# Safe static assets mount
@app.api_route("/demo-assets/{asset_name}", methods=["GET", "HEAD"], include_in_schema=False)
async def public_asset(asset_name: str):
    if asset_name not in {"incident_public.js", "incident.css", "governance.css"}:
        raise HTTPException(404, "Not found")
    return FileResponse(STATIC_DIR / asset_name, headers={"Cache-Control": "no-cache"})

# API Router
demo_api = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

@demo_api.post("/login")
async def login(payload: LoginPayload, request: Request, response: Response):
    client_ip = request.client.host if request.client else "unknown"
    check_login_rate_limit(client_ip)

    code_file = os.getenv("W4_ACCESS_CODE_FILE")
    with open(code_file, "r", encoding="utf-8") as f:
        expected = f.read().strip()

    if not secrets.compare_digest(payload.access_code.strip().encode("utf-8"), expected.encode("utf-8")):
        record_failed_login(client_ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid event access code.",
        )

    reset_failed_logins(client_ip)
    token, expires_at = create_session()
    # Secure cookie scoped to root
    response.set_cookie(
        key="flo_demo_session",
        value=token,
        httponly=True,
        samesite="strict",
        secure=True,
        max_age=max(0, int(expires_at - time.time())),
        path="/",
    )
    return {
        "status": "authenticated",
        "role": "viewer",
        "expires_in": max(0, int(expires_at - time.time())),
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
