# Workshop 4 Public Incident Room Deployment Report

**Deployment Date:** 2026-10-09  
**Target Environment:** VPS (`vmi3355051` / `13.140.146.58`)  
**Status:** **LIVE & VERIFIED**  

---

## 1. Executive Summary & Access Information

A secure, mobile-friendly, observation-only participant environment for **FLO Workshop 4: “The Day the Agent Broke the Bank”** has been successfully deployed and verified.

Participants can join the Incident Room directly from their smartphones via QR code or direct URL to inspect 11 curated, recorded execution runs without executing attacks, payments, approvals, or mutations.

* **Public URL:** [https://w4.ravirai.in/workshop-4](https://w4.ravirai.in/workshop-4)
* **Root Short Redirect:** [https://w4.ravirai.in/](https://w4.ravirai.in/) (307 redirect to `/workshop-4`)
* **Event Access Code:** `FLO-W4-2026`
* **Access Mode:** Observation Only (`viewer` role, 3-hour session lifetime)
* **Mobile QR Code:** Saved in repository at [`docs/workshops/w4-qr-code.png`](w4-qr-code.png)

```text
█████████████████████████████████████
█████████████████████████████████████
████ ▄▄▄▄▄ ██ ▄   ▀▀▄█▀▄▀█ ▄▄▄▄▄ ████
████ █   █ ███▀▄▀ ▀▀▄▄▀▄▄█ █   █ ████
████ █▄▄▄█ █▀ █▀█  █▄  ▀ █ █▄▄▄█ ████
████▄▄▄▄▄▄▄█▄▀▄█ █ █▄▀ ▀ █▄▄▄▄▄▄▄████
████▄▀▀▄█ ▄█ ▄▀▄▄█▀ █▀▀▄▀ ▀▄█▀██▀████
████▀▀▀ ▄▀▄ █ ▀▀██▀▀▄▄▄ ▀████▄  █████
████▄██ ▄█▄▄▄█▄▄ ██▀▄▄█  ▄▄▄█▄█▄▄████
█████▀▄▄ █▄▄▄  ██▀▀▄ ▀ █▀  ▄▀ ▄ ▄████
████▄ ▄▀█▄▄▀  ▀█▄▄▄ █▄▀█  ▀██▀█▄▀████
████▄█▄ █▀▄▄▀▀▄▄▀ █▀▄  ███▀█▄██  ████
████▄█▄▄▄█▄▄▀▀█ █▀▄████  ▄▄▄ █ ▀▀████
████ ▄▄▄▄▄ █▀██▄▄ ▄▀ █▄█ █▄█ ▀▀ █████
████ █   █ █▀ ▀██▀ ▄ ▄█▀▄▄ ▄ ▀▀▀▄████
████ █▄▄▄█ ███▀▄█ █▀▄▀▀▀▀ █▄ ▄▄▀▄████
████▄▄▄▄▄▄▄█▄█▄██▄██▄▄██▄█▄▄▄██▄█████
█████████████████████████████████████
▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀
```

---

## 2. Infrastructure & Security Architecture

### Traffic Flow
```text
Mobile Phone (QR Code) 
      ↓ HTTPS (TLS 1.3 / Port 443)
Cloudflare Edge Anycast (WAF, Universal SSL, Anti-Scraper)
      ↓ Proxied HTTPS (Zone ravirai.in)
Host Port 443 (Caddy Reverse Proxy Container)
      ↓ Docker Bridge Network "apps" (No exposed host ports!)
Container "flo-w4-incident-room:8000" (FastAPI / Uvicorn)
      ├─ Curated Evidence Database (:ro SQLite mount)
      └─ Ephemeral Session Store (Hashed cookies in private volume)
```

### Key Security Invariants Enforced
1. **Zero Host Port Exposure:**
   The `flo-w4-incident-room` container has **no published ports** (`ports: []`). It connects strictly to the internal Docker bridge network `apps` where Caddy reaches it directly. No port is listening on host IPv4 or IPv6.
2. **Read-Only Curated Evidence:**
   * Evidence database (`data/w4-public-evidence.sqlite`) was generated offline by `scripts/w4_public_evidence.py` from verified rehearsal run `incident-2026-10-05T170259Z.json`.
   * Filesystem permission is `0444`.
   * Docker mount is strictly `:ro`.
   * SQLite URI mode is `mode=ro`.
   * Database SHA-256 hash is verified against the manifest (`2e2cfa3f6603b1e0198c1fd7a63ed7130ce88cee7b94213164efc7e9baefe406`).
3. **Hard Fail-Closed Enforcement on Startup:**
   The service immediately aborts boot if:
   * `W4_OBSERVATION_ONLY != "true"`
   * `W4_ENABLE_VULNERABLE != "false"`
   * `ACTIVE_PROFILE != "w4"`
   * Access code file is missing or empty.
   * Evidence database is missing, empty, or unreadable in `mode=ro`.
4. **All Mutation Endpoints Explicitly Blocked (HTTP 403):**
   * POST `/demo-api/workshop-4/runs` (denied)
   * POST `/demo-api/workshop-4/reviewer-session` (denied)
   * POST `/demo-api/workshop-4/runs/{id}/decision` (denied)
   * POST `/demo-api/workshop-4/runs/{id}/traces` (denied)
   * POST `/demo-api/workshop-4/runs/{id}/reconcile` (denied)
5. **Absent Attack Surface (HTTP 404):**
   No customer banking, chat, admin, Temporal, Kafka, APISIX, or OPA endpoints are mounted or accessible (`/demo-api/chat`, `/demo-api/dashboard`, `/demo-api/banking`, `/api/v1/*`, `/oauth/*`, `/mcp`, `/docs`, `/openapi.json`).
6. **Rate-Limited Authentication:**
   * Access code verified via `secrets.compare_digest`.
   * Client IP rate limited to 5 failed attempts per 60 seconds (HTTP 429).
   * Generates 32-byte cryptographically random token (`secrets.token_urlsafe(32)`).
   * Raw token is never stored in DB (only SHA-256 hash).
   * Cookie is `HttpOnly`, `SameSite=Strict`, `Secure=True`, scoped to root `/`.
7. **Complete Independence of Laptop Presenter Demo:**
   * The public deployment lives in a separate Compose project (`flo-w4-public`) and separate file (`compose.w4-public.yml`).
   * The local laptop presenter instance and existing VPS test containers (`flobank-workshops-...`) were not modified, stopped, or disrupted.

---

## 3. Deviations from Codex Plan

1. **Proxy Connectivity Pattern:**
   * *Codex proposal:* Contemplated host-loopback port binding (`127.0.0.1:<port>:8000`) or a dedicated proxy network.
   * *Actual Implementation:* Caddy is containerized and connects to Docker network `apps`. By placing `flo-w4-incident-room` on `apps` with zero host port mappings, Caddy proxies directly to `http://flo-w4-incident-room:8000`. This completely eliminates exposing any host loopback or external ports.
2. **Dedicated Entrypoint & Assets:**
   * Rather than editing `src/demo/incident.py` and risking regressions on local presentation scripts, we created `src/demo/public_incident.py` alongside `src/demo/static/incident_public.html` and `src/demo/static/incident_public.js`. This guarantees 100% regression freedom for local runs.
3. **Subdomain Resolution:**
   * Configured `w4.ravirai.in` in Cloudflare DNS pointing to VPS IP `13.140.146.58` with Cloudflare proxy enabled.

---

## 4. Verification Results

### A. Python Regression & Public Test Suite
* Command: `PYTHONPATH=. .venv/bin/pytest tests/test_w4_public.py tests/test_w4_public_evidence.py -q`
  * **Result: 8/8 passed.** Verified fail-closed startup, auth requirement, session lifecycle, all 5 mutation blocks returning 403, customer routes returning 404, and evidence projection/sanitization.
* Command: `PYTHONPATH=. .venv/bin/pytest tests/test_w4_incident.py tests/test_w4_verification.py -q`
  * **Result: 35/35 passed.** Confirmed 0 regressions on existing workshop suites.

### B. Live HTTPS Smoke Tests (`https://w4.ravirai.in`)
The following live verification script was executed against the public Cloudflare edge:
```text
1. Unauthenticated access to /workshop-4:
   Status: 200 OK
2. Unauthenticated access to /demo-api/workshop-4/runs:
   Status: 401 Unauthorized
3. Invalid access code login:
   Status: 401 Unauthorized
4. Valid access code login (FLO-W4-2026):
   Status: 200 OK {"status":"authenticated","role":"viewer","expires_in":10800}
5. Authenticated readiness check:
   Status: 200 OK (Recording available: True, Run count: 11)
6. Authenticated runs check:
   Status: 200 OK (11 runs returned)
7. Authenticated run evidence for run-b27f461502750964fef9442e:
   Status: 200 OK
8. Denied mutating routes (All returned HTTP 403 Forbidden):
   POST /demo-api/workshop-4/runs -> 403
   POST /demo-api/workshop-4/reviewer-session -> 403
   POST /demo-api/workshop-4/runs/{id}/decision -> 403
   POST /demo-api/workshop-4/runs/{id}/traces -> 403
   POST /demo-api/workshop-4/runs/{id}/reconcile -> 403
9. Probing absent routes (All returned HTTP 404 Not Found):
   GET /demo-api/chat -> 404
   GET /demo-api/dashboard -> 404
   GET /demo-api/banking -> 404
   GET /api/v1/payments -> 404
   GET /api/v1/admin -> 404
   GET /oauth/token -> 404
   GET /mcp -> 404
   GET /docs -> 404
   GET /openapi.json -> 404
   GET /.env -> 404
   GET /.git/config -> 404
10. Logout and session revocation:
   Logout: 200 OK
   Post-logout runs access: 401 Unauthorized
```

### C. Live Playwright Mobile Viewport Test Suite
Executed headless Chromium over real mobile viewports via `tests/w4_public_browser.cjs`:
* **iPhone SE (320px × 667px):** Passed. Zero horizontal overflow, signin form, workspace, and run switcher responsive.
* **Android Standard (360px × 780px):** Passed.
* **iPhone 14 (390px × 844px):** Passed.
* **Android Large Pixel (412px × 915px):** Passed.
* All touch targets verified with height ≥ 40px.

### D. Evidence Database Immutability Check
```bash
sha256sum data/w4-public-evidence.sqlite
# 2e2cfa3f6603b1e0198c1fd7a63ed7130ce88cee7b94213164efc7e9baefe406
```
Hash before tests: `2e2cfa3f6603b1e0198c1fd7a63ed7130ce88cee7b94213164efc7e9baefe406`  
Hash after entire test barrage: `2e2cfa3f6603b1e0198c1fd7a63ed7130ce88cee7b94213164efc7e9baefe406` (Identical).

### E. Baseline VPS Service Health
All preexisting containers (`caddy`, `portainer`, `uptime-kuma`, `dozzle`, `flobank-workshops-...`) verified running healthy with zero disruption.

---

## 5. Known Limitations

1. **Preloaded Curated Rehearsal (By Design):**
   The public instance serves the 11 verified rehearsal runs recorded from the laptop test suite. It does not mirror the presenter's laptop ledger in real time.
2. **Single Worker / Single Process:**
   The instance runs with 1 Uvicorn worker and 256 MiB RAM limit. It is designed for participant smartphone observation (reading and downloading JSON evidence), not high-concurrency scraping or load testing.
3. **Browser Prediction Storage:**
   Participant notes and predictions are stored in client-side `localStorage` on each phone and are never transmitted to the server.

---

## 6. Rollback Procedure

If the public environment needs to be taken down or rolled back:

### Step 1: Remove Caddy Reverse Proxy Block
1. Edit `/home/sysadmin/apps/caddy/Caddyfile` and remove the `w4.ravirai.in { ... }` block (or restore the backup):
   ```bash
   cp /home/sysadmin/apps/caddy/Caddyfile_backup_* /home/sysadmin/apps/caddy/Caddyfile
   ```
2. Validate and reload Caddy:
   ```bash
   docker exec caddy caddy validate --config /etc/caddy/Caddyfile
   docker exec caddy caddy reload --config /etc/caddy/Caddyfile
   ```

### Step 2: Stop and Remove the Public Container
```bash
docker compose -p flo-w4-public -f /home/sysadmin/projects/flow-workshops-triple-gateway/compose.w4-public.yml down -v
```

### Step 3: Remove DNS Record (Optional)
Using Cloudflare MCP or Cloudflare Dashboard, delete DNS A record for `w4.ravirai.in` on zone `4073980eb3b4d357145857792e5ef588`.

### Step 4: Clean up Access Code Secret
```bash
rm -rf /home/sysadmin/.flo-w4/
```
