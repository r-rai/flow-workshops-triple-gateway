# NovaBank Workshop Platform – Implementation Review & Verification Handoff

## 📌 Executive Summary

- **Status**: **Implementation Complete & Remediated** (All findings from the 2026-10-03 independent audit fully resolved and re-verified).
- **Active Task Branch**: [`feat/implement-novabank-platform`](https://github.com/r-rai/flow-workshops-triple-gateway/tree/feat/implement-novabank-platform)
- **Base Branch**: `main` (commit `2bcc587`)
- **Remote Policy**: Pushed cleanly to origin without force-pushing or merging.
- **Primary References**:
  - Independent Audit Report: [`docs/audits/2026-10-03-novabank-audit.md`](../audits/2026-10-03-novabank-audit.md)
  - Workshop Delivery Plan: [`docs/workshops/delivery-plan.md`](../workshops/delivery-plan.md)
  - VPS Setup & Operations Guide: [`docs/setup/vps-setup-guide.md`](../setup/vps-setup-guide.md)
  - Master Facilitator Guide: [`docs/workshops/facilitator-guide.md`](../workshops/facilitator-guide.md)
  - Release Manifest: [`config/manifest.json`](../../config/manifest.json)
  - Compatibility Spike Report: [`docs/poc/01-compatibility-spikes-report.md`](../poc/01-compatibility-spikes-report.md)

---

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
git checkout feat/implement-novabank-platform
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

## ⚠️ Transparent Accounting of Unverified Requirements

As required by the repository brief, unverified checks must be reported transparently and not claimed as equivalent:

- **Windows 11 / WSL2 5 GB Memory Benchmark**:
  - **Status**: **Unverified on Host Platform**.
  - **Reason**: The host system is a Linux VPS (`vmi3355051` / Ubuntu x86_64). While native Linux container active memory peaks at ~951 MB (907 MiB) across 9 containers (comfortably within the 6 GB VPS operating budget), Windows 11 WSL2 virtualization allocates memory through the Windows Hyper-V `vmmem` subsystem with different page reclamation dynamics. This benchmark is documented in [`config/manifest.json`](../../config/manifest.json) to be verified on native Windows 11 participant laptops prior to workshop delivery.

---

## 📋 Copyable Prompt for Reviewing Agent

```text
Please review and audit the NovaBank workshop platform implementation on branch feat/implement-novabank-platform.

Review Context:
- Full implementation handoff: docs/implementation/agent-handoff.md
- Previous audit report: docs/audits/2026-10-03-novabank-audit.md
- Delivery plan: docs/workshops/delivery-plan.md
- Facilitator guide: docs/workshops/facilitator-guide.md
- Pinned release manifest: config/manifest.json

Audit Requirements:
1. Verify git commit history on feat/implement-novabank-platform across all packages and the audit remediation commit.
2. Validate that ./scripts/workshop verify passes on all 4 profiles (w1, w2, w3, w4).
3. Validate that the automated rehearsal test runners (workshops/w<N>/rehearsal_w<N>.py) execute cleanly and save fresh evidence.
4. Verify all 12 audit remediations:
   - Concurrent approval CAS and atomic balance decrement ([200, 409] under parallel execution).
   - Anti-self-approval enforcement and rejection of static API key approval attempts (HTTP 403).
   - A2A persistent tasks, viewer creation rejection (HTTP 403), and foreign task completion denial (HTTP 403).
   - Argument tampering rejection even below approval ceiling (HTTP 400).
   - OPA decision strict allowlisting (only 'allow' succeeds).
   - Kafka offset commit integrity (no commits on failed workflow starts).
   - Network isolation (worker routes strictly through APISIX Gate 3; host ports bound to 127.0.0.1).
   - Real durable proposal creation on MCP approval_required.
   - RFC 8693 token exchange at /oauth/token.
   - W2 rehearsal stability and readiness checks.
5. Verify VPS memory containment (~951 MB / 907 MiB Linux peak) and confirm that existing VPS services (caddy, portainer, uptime-kuma, dozzle) remain unharmed.
6. Confirm the unverified Windows 11 / WSL2 5 GB RAM benchmark is accurately recorded without false claims.

Report your findings, verification outputs, and any recommendations.
```

