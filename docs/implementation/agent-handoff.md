# Flo Bank Workshop Platform – Implementation Review & Verification Handoff

## 📌 Executive Summary

- **Status**: **Implementation Remediated & Fully Re-Verified** (All findings from the initial audit and the 2026-10-03 re-audit fully resolved, hardened, and verified).
- **Current delivery branch**: [`main`](https://github.com/r-rai/flow-workshops-triple-gateway/tree/main). The implementation and demo were merged and pushed at `8dcae8b`.
- **Historical implementation branch**: `feat/implement-novabank-platform`, based on `2bcc587`.
- **Remote policy**: normal commits and pushes; do not force-push shared history.
- **Primary References**:
  - Initial Audit Report: [`docs/audits/2026-10-03-novabank-audit.md`](../audits/2026-10-03-novabank-audit.md)
  - Re-Audit Report: [`docs/audits/2026-10-03-novabank-reaudit.md`](../audits/2026-10-03-novabank-reaudit.md)
  - Workshop Delivery Plan: [`docs/workshops/delivery-plan.md`](../workshops/delivery-plan.md)
  - VPS Setup & Operations Guide: [`docs/setup/vps-setup-guide.md`](../setup/vps-setup-guide.md)
  - Master Facilitator Guide: [`docs/workshops/facilitator-guide.md`](../workshops/facilitator-guide.md)
  - Release Manifest: [`config/manifest.json`](../../config/manifest.json)
  - Compatibility Spike Report: [`docs/poc/01-compatibility-spikes-report.md`](../poc/01-compatibility-spikes-report.md)

---

## Delivered: Real LLM & Dual-Mode Real API Gateway in the Customer Demo

Status: **Delivered and fully verified** on branch `feat/flo-bank-real-llm`.
- Customer Flo bot connects to real hosted inference with **MiniMax 2.7 Fast** (`MiniMax-M2.7-highspeed`) through APISIX Gate 1 (`demo-gateway` -> `demo-inference` or workshop `apisix` -> `adapter`).
- Dual-mode backend architecture:
  - **Simulated Mode (`DEMO_BACKEND_MODE=simulated`, default)**: Standalone single-command Compose execution (`docker compose --profile demo up -d --build`) using in-memory session fixtures with integer minor unit precision (paise).
  - **Enterprise Mode (`DEMO_BACKEND_MODE=enterprise`)**: Real-time integration with APISIX Gate 3 (`:9080/api/v1`), issuing customer JWTs (`sub="cust-maya"`, `aud="flobank-api"`), full distributed trace propagation into Jaeger, and live mutations against Core Banking SQLite/Postgres tables for cards (`/api/v1/cards/card-2048/state`) and support cases (`/api/v1/cases`). Runnable via `docker compose --profile demo-enterprise up -d --build`.
- Dedicated demo fixtures (`demo-checking`, `demo-savings`, `card-2048`) in `seed/v1_seed.json` strictly isolated from workshop rehearsal state (`acc-101`, `case-501`).
- Bounded turn loop (max 4 rounds, 8 tool calls) with staged session mutations committed only on turn completion.
- Rejection of unknown tools, malformed arguments, and foreign transactions.
- Zero silent fallback to scripted/mock when live mode errors or budget is exceeded.
- 66 Python tests passing (including 15 dedicated live LLM tests), Playwright browser smoke test passing, and bounded live verification successfully executed against real MiniMax.
- See the [real API gateway implementation plan](../superpowers/plans/2026-10-04-demo-real-api-gateway-plan.md) and [real LLM plan](demo-real-llm-plan.md).


## Customer demo and current setup

The Flo Bank login, account dashboard, scripted chatbot, and `demo` profile are
included in the original `docker-compose.yml`:

```bash
docker compose --profile demo up -d --build
```

Open **http://localhost:8000** and use `maya@flobank.demo` / `flo-demo`.
The customer simulation is isolated from the enterprise ledger and model
provider. Workshop profiles still serve this UI through APISIX at port 9080.
See [participant setup](../setup/participant-requirements.md) and the
[VPS runbook](../setup/vps-setup-guide.md) for current commands and limits.
The audit/remediation summaries below preserve the historical implementation
record; their counts and timestamps describe the recorded runs.

## 🗂️ Work Package Delivery & Git Traceability

All deliverables have been authored, verified with reproducible automated rehearsal evidence, and committed sequentially:

| Package | Commit | Key Deliverables & Code Changes | Verification Evidence |
|---|---|---|---|
| **Package 1: Compatibility Spikes** | [`cde4fb2`](https://github.com/r-rai/flow-workshops-triple-gateway/commit/cde4fb2) | All 7 spikes verified: APISIX 3.19.0 Standalone, `openapi-to-mcp` SSE stream unwrapping, Gate 3 Loopback, argument-aware OPA, RFC 8693 token exchange, Jaeger W3C tracecontext stitching, memory feasibility, and A2A anti-self-approval. | [`docs/poc/01-compatibility-spikes-report.md`](../poc/01-compatibility-spikes-report.md) |
| **Package 2: API Foundation** | [`eff6cde`](https://github.com/r-rai/flow-workshops-triple-gateway/commit/eff6cde) | Core Banking FastAPI service (`src/api/`), SQLAlchemy models (`src/models/`), integer minor units, SQLite/PostgreSQL persistence, canonical argument hashing, versioned seed data (`seed/v1_seed.json`), Compose skeleton (`docker-compose.yml`), and CLI (`scripts/workshop`). | [`tests/test_api_foundation.py`](../../tests/test_api_foundation.py) (9/9 passed) |
| **Package 3: Workshop 1 (OpenAPI to MCP)** | [`957e19e`](https://github.com/r-rai/flow-workshops-triple-gateway/commit/957e19e) | OpenAPI broad vs curated contracts (`workshops/w1/checkpoints/`), participant CLI (`workshops/w1/client.py`), automated 45-min rehearsal runner, worksheet, and answer key. | [`workshops/w1/evidence/rehearsal-evidence.json`](../../workshops/w1/evidence/rehearsal-evidence.json) |
| **Package 4: Workshop 2 (Governance & OPA)** | [`eec932a`](https://github.com/r-rai/flow-workshops-triple-gateway/commit/eec932a) | Curated Python MCP adapter (`src/adapter/`), declarative Rego policies (allow / approval_required / deny), fail-closed OPA outage test, automated 45-min rehearsal runner, worksheet, and answer key. | [`workshops/w2/evidence/rehearsal-evidence.json`](../../workshops/w2/evidence/rehearsal-evidence.json) |
| **Package 5: Workshop 3 (Durability & Temporal)** | [`ae54353`](https://github.com/r-rai/flow-workshops-triple-gateway/commit/ae54353) | Apache Kafka 3.7.0 (KRaft mode), persistent Temporal dev-server, worker process (`DisputeResolutionWorkflow`), human approval signal pause, worker crash recovery test, backend idempotency (`settle-dispute-case-501`), rehearsal runner, worksheet, and answer key. | [`workshops/w3/evidence/rehearsal-evidence.json`](../../workshops/w3/evidence/rehearsal-evidence.json) |
| **Package 6: Workshop 4 (Triple-Gate & A2A)** | [`a44dffc`](https://github.com/r-rai/flow-workshops-triple-gateway/commit/a44dffc) | Triple-Gate defense-in-depth, `NegotiatorBot` and `PaymentsAgent` (`src/agents/`), Agent Card discovery (`/.well-known/agent.json`), owner-scoped task access isolation (`HTTP 403` on rogue agent), anti-self-approval enforcement, argument tampering rejection, 135-min rehearsal runner, worksheet, and answer key. | [`workshops/w4/evidence/rehearsal-evidence.json`](../../workshops/w4/evidence/rehearsal-evidence.json) |
| **Package 7: Delivery Hardening & Facilitator Guide** | [`e8c4678`](https://github.com/r-rai/flow-workshops-triple-gateway/commit/e8c4678) | Pinned image digests in [`config/manifest.json`](../../config/manifest.json), master [`docs/workshops/facilitator-guide.md`](../workshops/facilitator-guide.md), verified offline replay provider fallback, and documented capacity limits. | All profile smoke tests passed |

---

## 🔍 Instructions for Reviewing Agent

To review and audit the implementation, follow these steps:

### 1. Inspect Git Branch & Commit Hygiene
```bash
git switch main
git log --oneline -n 10
git status -s
```
**Verify**:
- Working tree is clean.
- Commit history shows 7 discrete, well-structured commits matching Packages 1–7.
- No remote credentials or raw API secrets leaked into git history.

### 2. Verify Operational CLI & Profile Switching
```bash
# Preflight environment check
./scripts/workshop preflight

# Check active profile and running containers
./scripts/workshop status

# Switch between workshop profiles
./scripts/workshop switch w1
./scripts/workshop verify w1

./scripts/workshop switch w2
./scripts/workshop verify w2

./scripts/workshop switch w3
./scripts/workshop verify w3

./scripts/workshop switch w4
./scripts/workshop verify w4
```

### 3. Run Automated Rehearsal Suites
Each workshop provides a self-contained, end-to-end automated rehearsal runner simulating the exact attendee session timings, fault injections, and verification contracts:

```bash
# Workshop 1 (45-min simulated rehearsal)
./scripts/workshop switch w1
.venv/bin/python workshops/w1/rehearsal_w1.py

# Workshop 2 (45-min simulated rehearsal with OPA fail-closed test)
./scripts/workshop switch w2
.venv/bin/python workshops/w2/rehearsal_w2.py

# Workshop 3 (45-min simulated rehearsal with worker crash & redelivery)
./scripts/workshop switch w3
.venv/bin/python workshops/w3/rehearsal_w3.py

# Workshop 4 (135-min simulated rehearsal with Triple-Gate & A2A)
./scripts/workshop switch w4
.venv/bin/python workshops/w4/rehearsal_w4.py
```

### 4. Verify Host Memory Budget & Coexistence
Run `docker stats --no-stream` under profile `w4` (the largest profile with 9 microservices):
```bash
docker stats --no-stream $(docker compose ps -q)
```
**Verify**:
- Combined memory usage across all 9 containers operates at **~850–951 MB (907 MiB peak)**, comfortably preserving the **6 GB VPS operating memory budget** (> 6 GB free host RAM).
- Existing host services (`caddy`, `portainer`, `uptime-kuma`, `dozzle`) remain running and completely untouched.

---

## 🛡️ Key Architecture Invariants to Audit

| Invariant | Implementation Mechanism | Audit File / Code Location |
|---|---|---|
| **Loopback Gate 3 Enforced** | `api:8000` is on isolated internal Docker network (`novabank-backend`). External clients, adapter, and background worker must route through APISIX (`:9080/api/v1/*`) requiring cryptographic credentials. Host ports strictly bind to `127.0.0.1`. | [`docker-compose.yml`](../../docker-compose.yml), [`docker/apisix/`](../../docker/apisix/), [`src/worker/activities.py`](../../src/worker/activities.py) |
| **Offline Replay Fallback** | When third-party LLM keys are absent, Gate 1 serves deterministic, recorded completions (`offline-replay`) without network dependencies. | [`src/adapter/server.py`](../../src/adapter/server.py) (`/ai/chat/completions`) |
| **Argument-Aware Policy (Gate 2)** | OPA evaluates extracted arguments (`beneficiary`, `amount`), blocking blacklisted accounts (`fraud-account-66`) and enforcing tiered risk ceilings. Strict allowlisting ensures only `"allow"` proceeds; unexpected values fail closed. | [`spikes/spike3_opa/policy.rego`](../../spikes/spike3_opa/policy.rego), [`src/adapter/server.py`](../../src/adapter/server.py) |
| **Fail-Closed Resiliency** | If OPA crashes, times out, or partitions, the adapter strictly denies execution with `POLICY_TIMEOUT_FAIL_CLOSED`. | [`src/adapter/server.py`](../../src/adapter/server.py) (`call_tool`) |
| **Audience Separation & Downscoping (Gate 3)** | Tokens issued for `novabank-mcp` fail validation on `novabank-api` (HTTP 401). Tokens without `api:payments:write` fail mutation calls (HTTP 403). RFC 8693 token exchange supported at `/oauth/token`. | [`src/core/security.py`](../../src/core/security.py), [`src/api/routes/oauth.py`](../../src/api/routes/oauth.py), [`workshops/w4/rehearsal_w4.py`](../../workshops/w4/rehearsal_w4.py) |
| **Anti-Self-Approval** | Requester agent identity cannot approve its own payment proposal (`HTTP 403 Forbidden`). Only authorized manager principals via Bearer tokens can approve (static API key fallback denied). | [`src/services/approvals.py`](../../src/services/approvals.py#L90-L115) |
| **Argument Hash Binding** | Execution validates canonical argument hash against the proposal record whenever `proposal_id` is supplied, even below approval ceilings. Tampered amounts or beneficiaries fail with `HTTP 400`. | [`src/services/banking.py`](../../src/services/banking.py#L95-L108) |
| **Atomic CAS Consumption & Balance Debit** | Approved proposals transition atomically to `consumed` via SQL CAS (`UPDATE ... WHERE status = 'approved'`). Account debit executes atomically with balance check. Concurrent double-spend attempts return `HTTP 409 Conflict`. | [`src/services/banking.py`](../../src/services/banking.py#L110-L125) |
| **Durable Workflow & Zero Event Loss** | Stable Temporal workflow ID (`dispute-case-{case_id}`) prevents duplicate workflows on Kafka redelivery. Kafka consumer retries with backoff and seeks back on failure, never advancing offsets past unstarted workflows. | [`src/worker/kafka_consumer.py`](../../src/worker/kafka_consumer.py), [`src/worker/workflow.py`](../../src/worker/workflow.py) |
| **A2A Owner-Scoped Isolation & Persistence** | Tasks are durably persisted in SQLite (`A2ATask`). Task submission requires `api:payments:write` or `api:a2a:tasks` scope. Foreign agents attempting to view or complete tasks are strictly denied with `HTTP 403`. | [`src/api/routes/a2a.py`](../../src/api/routes/a2a.py), [`src/models/db_models.py`](../../src/models/db_models.py) |

---

## 🔧 Audit Remediation Summary (2026-10-03 Audit Report)

In response to the independent audit report ([`docs/audits/2026-10-03-novabank-audit.md`](../audits/2026-10-03-novabank-audit.md)), all identified security vulnerabilities, transaction concurrency failures, network isolation gaps, startup readiness issues, and memory discrepancies have been systematically remediated and verified:

1. **Concurrent Approval Consumption & Lost Updates Fixed**:
   - **Root Cause**: SQLite does not support `SELECT ... FOR UPDATE` row locks; concurrent requests read status `approved` simultaneously, creating two payments and lost balance updates.
   - **Remediation**: Implemented atomic SQL CAS in `src/services/banking.py`:
     ```sql
     UPDATE payment_proposals SET status = 'consumed' WHERE id = :id AND status = 'approved'
     ```
     If `rowcount == 0`, immediately raises `HTTP 409 Conflict`. Account balance debits now execute atomically with `UPDATE accounts SET balance = balance - :amount WHERE id = :id AND balance >= :amount AND status = 'active'`.
   - **Verification**: `workshops/w4/rehearsal_w4.py` executes concurrent `asyncio.gather` requests on a single approval, returning `[200, 409]` and strictly 1 debit.

2. **Anti-Self-Approval Bypass via Static API Key Closed**:
   - **Root Cause**: Stripping Bearer token fell back to `X-API-Key` which defaulted to `admin` role without tracking authentication method.
   - **Remediation**: In `src/core/security.py`, `X-API-Key` assigns `role="operator"` and `auth_method="api_key"`. In `src/services/approvals.py`, proposal approval and rejection strictly require `auth_method == "bearer"`, and verify that approver is not the requester or delegating principal.
   - **Verification**: Tested in `rehearsal_w4.py`; static API key approval returns `HTTP 403 Forbidden`.

3. **A2A Ownership Bypass & Scope Enforcement Closed**:
   - **Root Cause**: `complete_a2a_task` (`POST /tasks/{id}/complete`) did not check task ownership, and task creation did not check token scopes. Tasks were in-memory and lost on restart.
   - **Remediation**: In `src/models/db_models.py`, added `A2ATask` model for persistent DB storage. In `src/api/routes/a2a.py`, task creation requires `api:payments:write` or `api:a2a:tasks` scope (returning 403 for viewer tokens), and `complete_a2a_task` enforces owner/admin check, returning `HTTP 403 Forbidden` on foreign agents.
   - **Verification**: Tested in `rehearsal_w4.py`; viewer task creation returns 403, foreign task completion returns 403.

4. **Argument-Binding Bypass Below Approval Threshold Closed**:
   - **Root Cause**: In `execute_payment`, proposal argument hash validation was only performed if `amount >= APPROVAL_THRESHOLD`. Lowering the amount allowed execution with tampered parameters.
   - **Remediation**: In `src/services/banking.py`, proposal lookup and argument hash verification are unconditionally enforced whenever `req.proposal_id` is supplied, regardless of amount.
   - **Verification**: Tested in `rehearsal_w4.py`; tampered amount < threshold returns `HTTP 400 Bad Request`.

5. **Strict Fail-Closed OPA Decision Handling**:
   - **Root Cause**: Unexpected OPA decision values fell through to execution.
   - **Remediation**: In `src/adapter/server.py`, decision handling is strictly allowlisted: only `decision == "allow"` proceeds; all other values, unexpected strings, or unparseable payloads fail closed with `HTTP 403 Forbidden` / tool denial.

6. **Kafka Offset Commit & Event Loss Fixed**:
   - **Root Cause**: Failed Temporal workflow starts could commit Kafka offsets, losing events.
   - **Remediation**: In `src/worker/kafka_consumer.py`, workflow initialization implements a 10-retry loop with exponential backoff. On unrecoverable failure or shutdown, consumer seeks back to the message offset and never commits past unstarted workflows. Offsets are committed explicitly.

7. **Network Isolation & Localhost Port Binding Enforced**:
   - **Root Cause**: Worker had direct access to `novabank-backend` network, bypassing APISIX Gate 3. Services bound to `0.0.0.0`.
   - **Remediation**: In `docker-compose.yml`, host port mappings for `9080`, `16686`, `7233`, and `9092` are bound strictly to `127.0.0.1`. Worker was removed from `novabank-backend` network, and `src/worker/activities.py` routes all banking API calls strictly through APISIX Gate 3 (`http://apisix:9080/api/v1`) using authenticated service credentials.

8. **Persisted Real Proposals on MCP APPROVAL_REQUIRED**:
   - **Root Cause**: MCP adapter generated synthetic unpersisted proposal IDs.
   - **Remediation**: In `src/adapter/server.py`, when OPA yields `approval_required`, adapter calls backend `/payments/proposals` via Gate 3 to persist a durable proposal record with canonical hash, returning a valid UUID and hash to the caller.

9. **Live RFC 8693 Token Exchange Implemented**:
   - **Remediation**: Created `src/api/routes/oauth.py` and mounted at `/oauth/token` and `/api/v1/oauth/token`. Implements standard RFC 8693 token exchange with `grant_type=urn:ietf:params:oauth:grant-type:token-exchange`, returning `access_token`, `issued_token_type`, `token_type`, `expires_in`, and downscoped `scope`.

10. **Startup Readiness & W2 Rehearsal Hardened**:
    - **Remediation**: Updated `./scripts/workshop` with robust polling for APISIX, backend, and MCP endpoints, failing with exit 1 on timeout. Hardened `workshops/w2/rehearsal_w2.py` with downstream readiness checks and persistence validation.

11. **Accurate Memory Benchmark Documentation**:
    - **Documentation**: Linux container active set peak measured across all 9 microservices under load is **~951 MB (907 MiB)**, well within the 6 GB VPS operating budget. The Windows 11 / WSL2 5 GB RAM benchmark is documented as transparently unverified on Linux VPS.

12. **Deployment Digest Pinning in Manifest**:
    - **Documentation**: All 9 container image SHA-256 digests and versions are pinned and verified in [`config/manifest.json`](../../config/manifest.json).

---

## 🔄 Re-Audit Remediation Summary (2026-10-03 Re-Audit Report)

In response to the second independent audit report ([`docs/audits/2026-10-03-novabank-reaudit.md`](../audits/2026-10-03-novabank-reaudit.md)), all remaining findings and hardening gaps were resolved:

1. **RFC 8693 Token Exchange & Protocol Conformance**:
   - **Form URL-Encoded Parsing**: Replaced `request.form()` with standard library `urllib.parse.parse_qs` reading `await request.body()`. Eliminates `python-multipart` runtime requirement and HTTP 500 crashes.
   - **Protocol Field Enforcement**: Enforces required `grant_type="urn:ietf:params:oauth:grant-type:token-exchange"`, `subject_token`, and `subject_token_type="urn:ietf:params:oauth:token-type:access_token"`, rejecting non-compliant requests with `HTTP 400 Bad Request`.
   - **Subject Token Audience & Issuer Validation**: Validates `aud` claim against trusted workshop audiences (`novabank-mcp`, `novabank-api`, `novabank-auth`). Rejects unknown audiences with `HTTP 401 Unauthorized`.
   - **Role Entitlement Scope Enforcement**: Implemented `ROLE_ENTITLED_SCOPES` mapping in `src/api/routes/oauth.py`. Viewers, auditors, and unprivileged agents cannot escalate privileges to `api:payments:write` (returning `HTTP 403 Forbidden`). Only authorized roles (`support_agent`, `teller`, `agent`, `payments_agent`, `manager`, `admin`, `service`) may request mutation scopes.
   - **Delegation Chain Preservation**: Preserves delegation provenance in the exchanged token by populating `act` (actor) and `delegated_by` claims matching the subject token caller.

2. **Adapter Real Token Exchange & Elimination of Local Signing Fallback**:
   - In `src/adapter/server.py` (`get_exchanged_api_token`), the adapter sends standard form-encoded RFC 8693 token exchange requests to Gate 3 (`/oauth/token`) with `subject_token_type="urn:ietf:params:oauth:token-type:access_token"`.
   - Completely eliminated silent fallback to local HMAC signing on exchange failures. If token exchange fails, execution immediately raises an explicit error and fails closed.

3. **Elimination of Fabricated Proposal Success on Write Failures**:
   - In `src/adapter/server.py` (`call_tool`), when OPA evaluates `decision == "approval_required"`, the adapter attempts durable persistence at Gate 3 (`POST /payments/proposals`).
   - If persistence fails (e.g. backend 503, database error, or network partition), the adapter returns `isError: True` with error code `PROPOSAL_PERSISTENCE_FAILED` and descriptive details. It never fabricates synthetic `prop-<timestamp>` IDs or falsely reports "Proposal recorded."

4. **Worker Rejection Activity NameError Fixed**:
   - In `src/worker/activities.py` (line 115), resolved `NameError: name 'api_url' is not defined` by referencing the canonical `gate3_url` variable.
   - Handled `case-502` / prompt injection security review in `diagnose_and_propose_resolution` with high-value threshold (`INR 900,000.00`), requiring human approval.
   - Added automated verification in Segment 6 of `workshops/w3/rehearsal_w3.py`: when the reviewer sends a `REJECT` signal (`approved=False`), the activity executes cleanly, updates the dispute case status to `closed`, and verifies that exactly 0 payment records are created.

5. **Deployment Digest Enforcement & Immutable Builds**:
   - In `docker-compose.yml`, all 5 third-party images are pinned to exact immutable manifest digests:
     - `apache/apisix:3.19.0-debian@sha256:9a7e45dc943fbf10ec916d1232bae4cda9302ae28a4696cfb83c2da01d261141`
     - `openpolicyagent/opa:0.68.0-static@sha256:6a95ee2152d4006732916a8b63106a6e822827952234cc0e783d348ae1ead2cc`
     - `postgres:16-alpine@sha256:721873c34ceb9f8d8fc265984940dc982404c105f19ad51be9fdc5970a6080ea`
     - `jaegertracing/all-in-one:1.57@sha256:8f165334f418ca53691ce358c19b4244226ed35c5d18408c5acf305af2065fb9`
     - `apache/kafka:3.7.0@sha256:41c20d65b0a2180b9deca056d47540771752e69fe9225d5748dd65a25a9675d7`
   - Build dependencies are pinned with exact versions (`==`) across all Docker requirements files (`docker/api/requirements.txt`, `docker/adapter/requirements.txt`, `docker/worker/requirements.txt`, and `docker/temporal/Dockerfile`).
   - In `scripts/workshop`, `cmd_preflight` validates image digests against `config/manifest.json`. `cmd_pull` removed `|| true` so image pull failures fail fast.

6. **Telemetry & Upstream Dynamic DNS Hardening**:
   - In `docker-compose.yml`, configured `OTEL_METRICS_EXPORTER=none` and `OTEL_LOGS_EXPORTER=none` for both `api` and `adapter` services to eliminate metric endpoint 404 noise.
   - In `docker/apisix/config.yaml`, configured Docker's embedded DNS resolver (`127.0.0.11`) with `dns_resolver_valid: 2` to prevent stale upstream IP caching across container recreation.

7. **Rehearsal & Contract Verification Expansion**:
   - **W1 Rehearsal**: Added explicit curated contract inspection (`openapi-curated.json` contains exactly 2 endpoints) and negative testing verifying excluded tools return errors.
   - **W3 Rehearsal**: Added Segment 6 testing dispute rejection workflow (`case-502`), verifying rejection settlement executes without `NameError`, case is marked `closed`, and 0 payments are created.
   - **W4 Rehearsal**: Added automated tests for RFC 8693 form exchange (HTTP 200), viewer scope escalation rejection (HTTP 403), missing token type (HTTP 400), untrusted audience (HTTP 401), A2A task completion binding, and Jaeger distributed trace query.

---

## 🚀 Final Audit Remediation (2026-10-03 Final Audit Review)

In response to the final audit ([`docs/audits/2026-10-03-novabank-final-audit.md`](../audits/2026-10-03-novabank-final-audit.md)), all seven priority areas have been systematically remediated, hardened, and verified with fresh automated rehearsal evidence:

### 1. Delegated Anti-Self-Approval Provenance & Chain Traversal (HIGH)
- **Defect**: Token exchange wrapped the original actor inside a nested `act` claim, but `get_current_principal` inspected only the outer `act.sub`. Delegated manager tokens could bypass anti-self-approval and approve proposals created by their delegator.
- **Remediation**:
  - In [`src/core/security.py`](../../src/core/security.py), implemented recursive delegation chain extractor `extract_delegation_chain(claims)` traversing RFC 8693 nested `act` claims up to depth 20 as well as `delegated_by`. Populated `Principal.delegation_chain`.
  - In [`src/api/routes/oauth.py`](../../src/api/routes/oauth.py), updated RFC 8693 token exchange to preserve provenance across single and repeated exchanges without redundant self-wrapping when subject matches outer actor.
  - In [`src/services/approvals.py`](../../src/services/approvals.py), `approve_proposal_service` verifies:
    ```python
    requester_in_chain = (
        principal.id == prop.requester_id
        or principal.delegated_by == prop.requester_id
        or prop.requester_id in principal.delegation_chain
    )
    if requester_in_chain:
        raise HTTPException(status_code=403, detail="Anti-Self-Approval violation: Requester cannot approve proposal directly or via delegation")
    ```
  - Enforced `MAX_DELEGATION_DEPTH = 20` fail-closed limit in `src/core/security.py` and `src/api/routes/oauth.py`: over-depth chains (> 20) are rejected with HTTP 400 Bad Request, preventing bypasses where token exchange pushes delegators beyond truncation boundaries.
- **Verification**: Added automated regression coverage in [`tests/test_api_foundation.py`](../../tests/test_api_foundation.py) and [`workshops/w4/rehearsal_w4.py`](../../workshops/w4/rehearsal_w4.py) Segment 7 covering direct delegation (403), exchanged delegation (403), nested delegation (403), repeated exchanges (403), over-depth chain direct presentation (400), token exchange depth overflow (400), while allowing independent risk managers (200).

### 2. Executable W1 Curated Contract
- **Defect**: Workshop 1 loaded the 2-endpoint contract for display only, still served the full 23-tool broad catalog, and only checked rejection of an unknown dummy tool name.
- **Remediation**:
  - Created [`src/api/openapi-curated.json`](../../src/api/openapi-curated.json) exposing exactly 2 curated operations (`get_account`, `get_case`).
  - Added `GET /openapi-curated.json` route to Core API [`src/api/main.py`](../../src/api/main.py).
  - Added `/mcp/curated` route in [`docker/apisix/apisix-w1.yaml`](../../docker/apisix/apisix-w1.yaml) targeting `http://api:8000/openapi-curated.json`.
  - Added `--curated` flag to [`workshops/w1/client.py`](../../workshops/w1/client.py).
  - Updated [`workshops/w1/rehearsal_w1.py`](../../workshops/w1/rehearsal_w1.py) Segment 3 to connect to `/mcp/curated`, assert exact 2-tool catalog (`['get_account', 'get_case']`), execute account and case reads, and verify rejection of broad-catalog operations (e.g. `list_payments_api_v1_payments_get`) and unknown tools (`delete_customer_account`).
- **Verification**: Rehearsal W1 verified and recorded in [`workshops/w1/evidence/rehearsal-evidence.json`](../../workshops/w1/evidence/rehearsal-evidence.json).

### 3. Telemetry Packaging & Distributed Trace Correlation
- **Defect**: Python 3.12-slim dropped `setuptools`, causing `opentelemetry-instrumentation-fastapi` to fail importing `pkg_resources`. Adapter lacked instrumentation, and W4 rehearsal fabricated fallback service names without parent-child span verification.
- **Remediation**:
  - Added `setuptools==70.3.0` to both `docker/api/requirements.txt` and `docker/adapter/requirements.txt`. Added `opentelemetry-instrumentation-fastapi==0.46b0` to adapter.
  - In [`src/adapter/server.py`](../../src/adapter/server.py), wired TracerProvider, BatchSpanProcessor, OTLPSpanExporter, and FastAPIInstrumentor. Propagated `traceparent` (and active trace context) to all downstream Gate 3 API calls.
  - In [`workshops/w4/rehearsal_w4.py`](../../workshops/w4/rehearsal_w4.py) Segment 4, executed an authorized MCP call forwarding through adapter to Gate 3 API to produce real cross-service traces.
  - In Segment 9, queried Jaeger API (`:16686`): asserted `novabank-api` and `novabank-adapter` exist, queried traces for `novabank-adapter`, identified correlated trace spanning both services, validated parent-child span hierarchy (child span in `novabank-api` references parent span in `novabank-adapter`), and configured fail-closed assertions if absent.
- **Verification**: Rehearsal W4 verified real distributed trace `c5900339c480664f0a686368048a6fb6` with 4 adapter spans and 3 API spans.

### 4. W1 Startup Readiness & Zero Flap
- **Defect**: Switching to W1 exited 0 while backend API was still initializing; immediate `verify w1` hit APISIX `/mcp` which attempted OpenAPI fetch, failed, and cached the failure for 5s, returning HTTP 500.
- **Remediation**:
  - In [`scripts/workshop`](../../scripts/workshop) `cmd_start`, decoupled backend spec readiness from MCP initialization:
    1. Polls `http://127.0.0.1:9080/api/v1/accounts/acc-101` and `http://127.0.0.1:8000/openapi.json` (and `openapi-curated.json` for W1) until 200 OK.
    2. Pauses 1s for APISIX upstream cache readiness.
    3. Warms MCP `initialize`, `tools/list`, and executes downstream `tools/call` checking for account balance / INR.
    4. If profile is W1, additionally warms `/mcp/curated` `initialize`, `tools/list`, and `tools/call`.
- **Verification**: Verified repeated cold profile switches `./scripts/workshop switch w1 && ./scripts/workshop verify w1` exit 0 on first attempt with zero 500 errors.

### 5. Fail-Closed Preflight Validation
- **Defect**: Preflight suppressed digest inspection errors with `2>/dev/null || true` and did not fail closed on malformed manifest JSON or inspection errors. Preflight unit tests exercised copied logic rather than the CLI script.
- **Remediation**:
  - In [`scripts/workshop`](../../scripts/workshop) `cmd_preflight`, strictly parses `config/manifest.json`, validates each pinned image's `RepoDigests`, records errors, and propagates exit code 1 to bash on any failure. Supports `WORKSHOP_MANIFEST_PATH` for subprocess test isolation.
  - Rewrote [`tests/test_preflight_validation.py`](../../tests/test_preflight_validation.py) to execute the real `./scripts/workshop preflight` executable via `subprocess.run` across 5 negative and positive scenarios. Added direct CLI execution runner (`if __name__ == "__main__": sys.exit(pytest.main(["-v", __file__]))`).
- **Verification**: `./scripts/workshop preflight` passes on host; all 5 CLI subprocess tests pass.

### 6. A2A Settlement Binding & Executor Authorization
- **Defect**:
  1. Any agent with `api:a2a:tasks` could complete tasks with arbitrary payment IDs, including nonexistent payments or payments from unrelated transactions.
  2. Permissive destination check allowed source account match (`payment.account_id == expected_dest`) even when beneficiary did not match.
  3. No currency validation was performed.
  4. Multiple tasks could bind the exact same payment ID: checking existing bindings and committing completion were separate application-level operations, creating a race condition where concurrent requests both returned HTTP 200 and bound the same payment to two tasks.
- **Remediation**:
  - In [`src/models/db_models.py`](../../src/models/db_models.py):
    - Added `PaymentTaskBinding` model mapping to `a2a_payment_bindings` with `payment_id` as primary key and `task_id` unique index, enforcing database-level uniqueness.
    - Added `bound_payment_id = Column(String(64), unique=True, nullable=True, index=True)` to `A2ATask`.
  - In [`src/api/routes/a2a.py`](../../src/api/routes/a2a.py):
    - Enforced state transitions: completing a task in a terminal state (`completed`, `failed`, `cancelled`) raises `HTTP 400 Bad Request`.
    - Enforced executor authorization: completing a `propose_payment` task requires `payments-agent-executor` (or admin with write scope); non-executors (including the task owner) receive `HTTP 403 Forbidden`.
    - Strict destination matching: requires `payment.beneficiary == expected_dest` (no `account_id` fallback).
    - Currency matching: requires `payment.currency == expected_currency` (HTTP 400 on mismatch).
    - Database uniqueness & atomic claim: inserts `PaymentTaskBinding` record and sets `task.bound_payment_id` within the completion transaction. Commits atomically with `IntegrityError` handler rolling back and raising HTTP 409 Conflict (`"Payment '...' is already bound to task"`). Pre-checks also raise HTTP 409 Conflict.
    - Validated settlement record: queries database for `payment_id`, verifies payment status is `completed` or `settled`, verifies amount and beneficiary match task input, and verifies associated proposal is `consumed`.
  - In [`src/agents/payments_agent.py`](../../src/agents/payments_agent.py), implemented `dispatch_payment_task(task_id)` which queries task specifications, executes payment through Core Banking API, and completes task binding the verified settlement record.
- **Verification**: Tested in [`tests/test_api_foundation.py`](../../tests/test_api_foundation.py) and [`workshops/w4/rehearsal_w4.py`](../../workshops/w4/rehearsal_w4.py) Segment 8: nonexistent payment (400), mismatched payment (400), wrong destination (400), wrong currency (400), duplicate payment reuse (409), concurrent settlement race [200, 409], non-executor owner completion (403), payments agent dispatch (200), and terminal state re-completion (400).

### 7. Remaining Delivery Gaps & Reporting Transparency
- **`USE_REPLAY_FIXTURES=false`**:
  - In [`src/adapter/server.py`](../../src/adapter/server.py), when `USE_REPLAY_FIXTURES=false`, checks for live credentials (`OPENAI_API_KEY`/`LLM_API_KEY`). If absent, returns explicit `HTTP 503 Service Unavailable` configuration error instead of fabricating replay content. If configured, executes live upstream chat completion.
- **W3 Real LangGraph Multi-Turn Agent & MiniMax Integration**:
  - **Status**: **Fully Implemented & Remediated**.
  - **Compiled Graph Architecture**: State machine defined in [`src/worker/dispute_agent.py`](../../src/worker/dispute_agent.py) (`DisputeResolutionWorkflow` -> `diagnose_and_propose_resolution`). The exact same compiled graph executes across both live and replay modes.
  - **Dual Mode Support**:
    - **Live Mode (`USE_REPLAY_FIXTURES=false`)**: Egresses via APISIX Gate 1 (`/ai/chat/completions`) to `https://api.minimax.io/v1/chat/completions` using MiniMax 2.7 Fast (`MiniMax-M2.7-highspeed`), executing multi-turn tool calling against allowlisted Gate 2 MCP tools (`get_case`, `get_account`).
    - **Offline Replay Mode (`USE_REPLAY_FIXTURES=true`)**: Gate 1 emits deterministic, multi-turn reasoning and tool-calling fixtures feeding the same compiled graph for zero-cost offline demonstration.
  - **Investigation Failure & Anti-Fabrication Hardening**:
    - Removed heuristic canned proposal fallbacks from live diagnosis. Malformed model outputs, provider errors, and exhausted iterations produce an explicit failure (`status: "FAILED"` / `INVESTIGATION_FAILED`), with zero payable proposal.
    - Provider failures (e.g. Gate 1 HTTP 503, timeouts) preserve the customer dispute case in its original state without mutation, preventing erroneous auto-rejection and keeping the dispute available for bounded retry or explicit presenter restart.
    - Strict structured proposal validation enforces: exact case ID match, customer identity match, currency strictly `INR`, integer minor units within limits, payment destinations restricted to verified/authorized customer accounts, and verified tool read evidence required before any payable proposal.
    - Server-side approval threshold (> INR 400 = 40,000 minor units) and security review flags are strictly computed on the server.
    - Tool-call limits (`MAX_TOOL_CALLS = 8`) are enforced before each individual call.
    - Inference budget uses atomic reservation and reconciliation via `asyncio.Lock`, preventing concurrent over-admission past the configured demo budget (`INFERENCE_BUDGET_TOKENS=100000`).

### 8. Presenter Operations & Mode Switching Runbook

#### A. Starting Live MiniMax Mode
```bash
# 1. Verify that MINIMAX_API_KEY is configured in host .env
grep -q "MINIMAX_API_KEY" .env && echo "MiniMax credential configured"

# 2. Set mode to live provider egress
export USE_REPLAY_FIXTURES=false
export LLM_MODEL=MiniMax-M2.7-highspeed

# 3. Switch or restart workshop profile W3
./scripts/workshop switch w3

# 4. Verify AI Gateway readiness & live mode
curl -s http://127.0.0.1:9080/ai/status | jq .
# Expected output: {"status":"ready","mode":"live","use_replay_fixtures":false,"provider_configured":true,...}
```

#### B. Selecting Offline Replay Mode
```bash
# 1. Set mode to offline deterministic replay fixtures
export USE_REPLAY_FIXTURES=true

# 2. Switch or restart workshop profile W3
./scripts/workshop switch w3

# 3. Verify AI Gateway readiness & replay mode
curl -s http://127.0.0.1:9080/ai/status | jq .
# Expected output: {"status":"ready","mode":"replay","use_replay_fixtures":true,"provider_configured":true,...}
```

#### C. Checking Mode, Readiness, and Inference Headroom
```bash
# Check current AI Gateway mode, budget utilization, and headroom
curl -s http://127.0.0.1:9080/ai/status | jq .

# Reset process-local demo budget (re-authorizes full headroom)
curl -s -X POST http://127.0.0.1:9080/ai/budget/reset | jq .
```

#### D. Recovering / Restarting a Failed Demonstration Without Duplicate Settlement
```bash
# 1. Reset lab database state to pristine seed data (preserves caddy, portainer, uptime-kuma, dozzle)
./scripts/workshop reset w3 -y

# 2. Clean restart of Temporal and worker writers
docker compose --profile w3 restart temporal worker

# 3. Re-emit dispute event via Kafka CLI
PYTHONPATH=. .venv/bin/python -c "import asyncio; from workshops.w3.client import emit_dispute; asyncio.run(emit_dispute('localhost:9092', 'case-501', 'cust-101'))"

# Durability & Settlement Invariants:
# - WorkflowIDReusePolicy.ALLOW_DUPLICATE_FAILED_ONLY allows retrying failed workflow executions.
# - Settlement activity uses database-backed idempotency key 'settle-dispute-{case_id}',
#   guaranteeing strictly zero duplicate payments across redeliveries and worker crashes.
```

- **W3 Writers-Stopped Reset & Real SIGKILL Recovery**:
  - In [`workshops/w3/rehearsal_w3.py`](../../workshops/w3/rehearsal_w3.py), Segment 1 stops `temporal` and `worker` writers before resetting SQLite database to prevent open-handle corruption. Segment 4 upgraded worker crash to real `docker kill --signal=SIGKILL novabank-workshops-worker-1`.
- **Built Image Tagging**:
  - Documented that 4 built images (`api`, `adapter`, `worker`, `temporal`) use semantic tag `1.0.0` with base image `python:3.12-slim` pinned to exact SHA256 digest (`sha256:dddfd7e07f9d15ae4421b4a69eb6ef57b8054044a69a9143ae84ad2c664b9683`) and exact pip package pins.

---

## ⚠️ Transparent Accounting of Unverified Requirements

As required by the repository brief, unverified checks must be reported transparently and not claimed as equivalent:

- **Windows 11 / WSL2 5 GB Memory Benchmark**:
  - **Status**: **Unverified on Host Platform**.
  - **Reason**: The host system is a Linux VPS (`vmi3355051` / Ubuntu x86_64). While native Linux container active memory peaks at ~775–995 MB (740–949 MiB) across 9 containers (comfortably within the 6 GB VPS operating budget), Windows 11 WSL2 virtualization allocates memory through the Windows Hyper-V `vmmem` subsystem with different page reclamation dynamics. This benchmark is documented in [`config/manifest.json`](../../config/manifest.json) to be verified on native Windows 11 participant laptops prior to workshop delivery.

---

## 📋 Copyable Prompt for Reviewing Agent

```text
Please review and audit the Flo Bank workshop platform implementation on branch feat/implement-novabank-platform following remediation of the 2026-10-03 Final Audit.

Review Context:
- Full implementation handoff: docs/implementation/agent-handoff.md
- Final remediation report: docs/audits/2026-10-04-novabank-remediation-report.md
- Initial audit report: docs/audits/2026-10-03-novabank-audit.md
- Re-audit report: docs/audits/2026-10-03-novabank-reaudit.md
- Final audit report: docs/audits/2026-10-03-novabank-final-audit.md
- Pinned release manifest: config/manifest.json

Audit Requirements:
1. Verify git commit history and working tree status on feat/implement-novabank-platform.
2. Validate that ./scripts/workshop preflight passes and negative preflight unit tests pass (tests/test_preflight_validation.py).
3. Validate that ./scripts/workshop switch w1 followed immediately by ./scripts/workshop verify w1 passes with zero HTTP 500 errors.
4. Validate that all 4 workshop rehearsals pass and fresh evidence is captured:
   - W1: workshops/w1/rehearsal_w1.py (executable /mcp/curated contract with 2 tools, account/case reads, broad operation rejection).
   - W2: workshops/w2/rehearsal_w2.py (durable proposal lookup and POLICY_TIMEOUT_FAIL_CLOSED denial).
   - W3: workshops/w3/rehearsal_w3.py (writers-stopped reset, real SIGKILL recovery, approved settlement, and rejection with case-502 closed and 0 payments).
   - W4: workshops/w4/rehearsal_w4.py (RFC 8693 form exchange, delegated anti-self-approval 403 regression suite, argument tampering 400, CAS single-use [200, 409], A2A settlement binding, and correlated distributed traces with parent-child span hierarchy).
5. Verify VPS memory containment (~775–995 MB Linux peak) and confirm protected services (caddy, portainer, uptime-kuma, dozzle) remain running.
6. Verify transparent reporting of the unverified Windows 11 / WSL2 5 GB benchmark and architectural simplifications.
```

