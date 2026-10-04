# NovaBank Workshop Platform – Final Audit Remediation Report

**Date**: 2026-10-04  
**Author**: Antigravity Assistant  
**Repository Branch**: `feat/implement-novabank-platform`  
**Reference Audit**: [`docs/audits/2026-10-03-novabank-final-audit.md`](2026-10-03-novabank-final-audit.md) (Reviewed HEAD `c54a269`)  

---

## Executive Summary

This report documents the systematic remediation and verification of all findings identified in the final audit of the NovaBank workshop platform, including the two bypasses uncovered in focused verification (delegated self-approval depth truncation and A2A settlement destination/currency/uniqueness binding). Every fix has been verified with repeatable commands, exit codes, and fresh rehearsal evidence files.

All seven priority areas have been resolved:
1. **Delegated anti-self-approval bypass**: Provenance across RFC 8693 nested `act` claims and repeated exchanges is preserved and parsed recursively; requesters anywhere in the delegation chain are rejected with HTTP 403. Delegation chains exceeding depth 20 are rejected fail-closed with HTTP 400 Bad Request, preventing bypass via depth truncation.
2. **Executable W1 curated contract**: Dedicated `/mcp/curated` route in APISIX backed by `/openapi-curated.json` is live; verified exact 2-tool catalog, successful balance/case reads, and rejection of actual broad operations.
3. **Telemetry packaging and distributed tracing**: Added `setuptools` to eliminate missing `pkg_resources` in Python 3.12-slim; wired OTel in API and adapter; verified correlated distributed traces with parent-child span hierarchy across Gate 2 and Gate 3 boundaries with fail-closed assertions.
4. **W1 startup readiness**: Decoupled backend spec readiness from MCP initialization; warmed MCP gateway and tools to eliminate cache poisoning and HTTP 500 errors on cold switches.
5. **Fail-closed preflight validation**: Strict digest parsing and inspection without `|| true`; failure exit codes propagated to shell; 5 isolated CLI subprocess negative tests verify the real `./scripts/workshop preflight` script.
6. **A2A settlement binding**: Enforced state machine transitions, executor authorization (`payments-agent-executor`), strict destination account matching (`payment.beneficiary == task_input['destination_account']`), currency matching, unique 1:1 payment task association, and validated settlement records against Core Banking database; added PaymentsAgent dispatch path.
7. **Delivery and reporting gaps**: `USE_REPLAY_FIXTURES=false` fails closed without credentials; W3 writers stopped before SQLite storage reset; real SIGKILL used for crash recovery; accurate Linux peak memory reported (~755–995 MB / 720–949 MiB); unverified Windows benchmark transparently accounted for.

---

## Detailed Remediation & Verification Matrix

### 1. Delegated Anti-Self-Approval Provenance Traversal & Depth Guard (HIGH)
- **Defect**:
  1. Token exchange wrapped delegators into nested `act` claims (`{"sub": manager, "act": {"sub": agent}}`), but principal extraction only read the outer `act.sub`. An agent delegating to a manager could approve its own proposal after token exchange.
  2. Silent depth truncation: Earlier traversal stopped iterating at depth 20 (`depth < 20`). Pushing a requester to depth 21 via token exchange caused truncation, flipping authorization from 403 to 200.
- **Changed Code**:
  - `src/core/security.py`:
    - `MAX_DELEGATION_DEPTH = 20`.
    - `extract_delegation_chain(claims)`: Traverses nested `act` claims. If depth exceeds `MAX_DELEGATION_DEPTH`, raises `HTTPException(status_code=400, detail="Delegation chain exceeds maximum permitted depth of 20")`.
    - Added `delegation_chain: List[str]` to `Principal`. Added `act` claim parameter to `create_jwt_token`.
    - Propagates `HTTPException` directly in `get_current_principal`.
  - `src/api/routes/oauth.py`:
    - Validates incoming subject token delegation chain with `extract_delegation_chain(claims)`.
    - Validates resulting `act_claim` with `extract_delegation_chain({"act": act_claim, "delegated_by": delegated_by})`. Any chain pushing beyond depth 20 fails-closed with HTTP 400 Bad Request.
  - `src/services/approvals.py`: `approve_proposal_service` checks:
    `requester_in_chain = (principal.id == prop.requester_id or principal.delegated_by == prop.requester_id or prop.requester_id in principal.delegation_chain)`
    Raises HTTP 403 Forbidden.
- **Verification Command & Exit Code**:
  - `PYTHONPATH=. .venv/bin/python tests/test_api_foundation.py` -> Exit code `0` (12/12 passed, including `test_delegated_anti_self_approval_regression` and `test_delegation_chain_depth_limit_regression`).
  - Segment 7 in `workshops/w4/rehearsal_w4.py` -> Direct delegation: 403; Exchanged delegation: 403; Nested delegation: 403; Repeated exchanges: 403; Static API key: 403; Independent manager: 200.
  - Live API verification: Direct depth 21 token -> HTTP 400; Token exchange pushing to depth 21 -> HTTP 400.

### 2. Executable W1 Curated Contract
- **Defect**: W1 displayed the 2-endpoint contract but served all 23 tools on `/mcp`. Its rejection check only tested an unknown dummy tool name. Broad payment tools remained callable.
- **Changed Code**:
  - `src/api/openapi-curated.json`: Contract with 2 operations: `get_account` (`/api/v1/accounts/{id}`) and `get_case` (`/api/v1/cases/{id}`).
  - `src/api/main.py`: Route `GET /openapi-curated.json`.
  - `docker/apisix/apisix-w1.yaml`: Added route `w1_mcp_curated_route` at `/mcp/curated` pointing to `http://api:8000/openapi-curated.json`.
  - `workshops/w1/client.py`: Added `--curated` flag.
  - `workshops/w1/rehearsal_w1.py`: Segment 3 connects to `/mcp/curated`, verifies exact 2 tools (`['get_account', 'get_case']`), reads account balance and support case, and verifies rejection of `list_payments_api_v1_payments_get` and `delete_customer_account`.
- **Verification Command & Exit Code**:
  - `PYTHONPATH=. .venv/bin/python workshops/w1/rehearsal_w1.py` -> Exit code `0`.
  - Evidence: [`workshops/w1/evidence/rehearsal-evidence.json`](../../workshops/w1/evidence/rehearsal-evidence.json).

### 3. Telemetry Packaging & Distributed Trace Correlation
- **Defect**: Python 3.12-slim dropped `setuptools`, causing `opentelemetry-instrumentation-fastapi` to crash importing `pkg_resources`. The adapter lacked OTel setup. Rehearsal W4 caught exceptions and substituted fabricated service names.
- **Changed Code**:
  - `docker/api/requirements.txt` & `docker/adapter/requirements.txt`: Added `setuptools==70.3.0` and `opentelemetry-instrumentation-fastapi==0.46b0`.
  - `src/adapter/server.py`: Initialized TracerProvider, BatchSpanProcessor, OTLPSpanExporter, and FastAPIInstrumentor. Injected `traceparent` or active context to Gate 3 calls.
  - `workshops/w4/rehearsal_w4.py`: Added authorized MCP call in Segment 4 forwarding to Gate 3. In Segment 9, queries Jaeger: asserts `novabank-api` and `novabank-adapter` exist, queries traces, validates parent-child span hierarchy (`novabank-api` child span linked to `novabank-adapter` parent span), and fails closed if evidence is missing.
- **Verification Command & Exit Code**:
  - `PYTHONPATH=. .venv/bin/python workshops/w4/rehearsal_w4.py` -> Exit code `0`.
  - Recorded trace ID: `d0cb27801fd38ceff6e07300850add7d` with 4 adapter spans and 3 API spans.
  - Evidence: [`workshops/w4/evidence/rehearsal-evidence.json`](../../workshops/w4/evidence/rehearsal-evidence.json).

### 4. W1 Startup Readiness & Zero Flap
- **Defect**: `switch w1` exited 0 while Uvicorn was still booting. Probing `/mcp` caused APISIX plugin `openapi-to-mcp` to fail fetching the OpenAPI spec, caching the failure for 5 seconds and causing `verify w1` to fail with HTTP 500.
- **Changed Code**:
  - `scripts/workshop` `cmd_start`: Decoupled readiness into two stages:
    1. Polls backend API `/api/v1/accounts/acc-101` AND spec `/openapi.json` (and `openapi-curated.json` for W1) until HTTP 200.
    2. Pauses 1s, then warms MCP `initialize`, `tools/list`, and `tools/call` for account read. If W1, also warms `/mcp/curated`.
- **Verification Command & Exit Code**:
  - `./scripts/workshop switch w1 && ./scripts/workshop verify w1` -> Exit code `0` on cold switch with zero errors.

### 5. Fail-Closed Preflight Validation
- **Defect**: Preflight suppressed digest inspection errors with `2>/dev/null || true` and did not fail closed on malformed manifest or inspection errors. Preflight tests in Python exercised copied validation logic rather than the actual CLI.
- **Changed Code**:
  - `scripts/workshop` `cmd_preflight`: Strictly loads manifest, inspects repo digests for each pinned image, records errors, and propagates exit code 1 to bash on failure. Supports `WORKSHOP_MANIFEST_PATH` environment variable for isolated CLI testing.
  - `tests/test_preflight_validation.py`: Tests the actual `./scripts/workshop preflight` executable via `subprocess.run` across 5 isolated scenarios: valid manifest (exit 0), malformed JSON (exit 1), missing `pinned_images` mapping (exit 1), digest mismatch (exit 1), and missing image on daemon (exit 1). Includes direct execution entrypoint `if __name__ == "__main__": sys.exit(pytest.main(["-v", __file__]))`.
- **Verification Command & Exit Code**:
  - `./scripts/workshop preflight` -> Exit code `0`.
  - `PYTHONPATH=. .venv/bin/python tests/test_preflight_validation.py` -> Exit code `0` (5/5 passed).

### 6. A2A Settlement Binding & Executor Authorization
- **Defect**:
  1. Any agent with `api:a2a:tasks` could complete tasks with arbitrary payment IDs, including nonexistent payments or payments from unrelated transactions.
  2. `src/api/routes/a2a.py:219` accepted `payment.account_id == expected_dest` (the debit source), allowing payments to third-party recipients to complete tasks.
  3. No currency validation was performed.
  4. Multiple tasks could bind the exact same payment ID: checking existing bindings and committing completion were separate application-level operations, creating a race condition where concurrent requests both returned HTTP 200 and bound the same payment to two tasks.
- **Changed Code**:
  - `src/models/db_models.py`:
    - Created `PaymentTaskBinding` model mapping to `a2a_payment_bindings` with `payment_id` as primary key and `task_id` unique index, enforcing database-level uniqueness.
    - Added `bound_payment_id = Column(String(64), unique=True, nullable=True, index=True)` to `A2ATask`.
  - `src/api/main.py`: Updated lifespan to ensure `a2a_payment_bindings` table and `bound_payment_id` unique index are created on startup.
  - `src/api/routes/a2a.py`:
    - Enforced state machine transitions: completing a task in a terminal state (`completed`, `failed`, `cancelled`) raises HTTP 400.
    - Enforced executor authorization: completing a `propose_payment` task requires `payments-agent-executor` (or admin); non-executors (including task owner) receive HTTP 403.
    - Strict destination matching: requires `payment.beneficiary == expected_dest` (removed permissive `payment.account_id == expected_dest` check).
    - Currency matching: `payment.currency == expected_currency` (raises HTTP 400 on mismatch).
    - Database uniqueness & atomic claim: inserts `PaymentTaskBinding` record and sets `task.bound_payment_id` within the completion transaction. Commits atomically with `IntegrityError` handler rolling back and raising HTTP 409 Conflict (`"Payment '...' is already bound to task"`). Pre-checks also raise HTTP 409 Conflict.
    - Validated settlement record: queries database for `payment_id`, validates status in `('completed', 'settled')`, validates amount matches task input, and verifies proposal is `consumed`.
  - `src/agents/payments_agent.py`: Added `dispatch_payment_task(task_id)` to query the task, execute the payment, and complete the task with verified settlement.
- **Verification Command & Exit Code**:
  - Direct execution: `.venv/bin/python tests/test_api_foundation.py` -> Exit code `0` (13/13 passed, including `test_a2a_concurrent_settlement_binding_race` verifying statuses `[200, 409]` and database state asserting exactly 1 completed task and 1 payment binding).
  - CLI preflight tests: `.venv/bin/python tests/test_preflight_validation.py` -> Exit code `0` (5/5 passed).
  - Full suite: `PYTHONPATH=. .venv/bin/pytest tests/test_api_foundation.py tests/test_preflight_validation.py` -> Exit code `0` (18/18 passed).
  - Segment 8 in `workshops/w4/rehearsal_w4.py` -> Nonexistent payment: 400; Mismatched payment: 400; Non-executor owner completion: 403; PaymentsAgent dispatch: 200; Re-completion: 400; Concurrent settlement binding race: [200, 409].
  - Live API verification: Duplicate payment reuse -> 409; Wrong destination -> 400; Currency mismatch -> 400.

### 7. Remaining Delivery & Reporting Gaps
- **`USE_REPLAY_FIXTURES=false`**: When set to `false`, `src/adapter/server.py` verifies presence of live credentials (`OPENAI_API_KEY`/`LLM_API_KEY`). If absent, returns explicit HTTP 503 instead of fabricating replay content.
- **W3 LangGraph Simulation**: Documented in `config/manifest.json` and `docs/workshops/delivery-plan.md` that the diagnosis activity uses a deterministic simulation of LangGraph reasoning for zero-cost, reproducible lab execution.
- **W3 Storage Reset & Crash Recovery**: `workshops/w3/rehearsal_w3.py` Segment 1 stops `temporal` and `worker` writers before deleting SQLite storage. Segment 4 terminates the worker container using real `docker kill --signal=SIGKILL novabank-workshops-worker-1`.
- **Built Image Tagging**: Documented in `config/manifest.json` that built images (`api`, `adapter`, `worker`, `temporal`) use semantic tag `1.0.0` with base image `python:3.12-slim` pinned to exact SHA256 digest (`sha256:dddfd7e07f9d15ae4421b4a69eb6ef57b8054044a69a9143ae84ad2c664b9683`).

---

## Protected Service Coexistence & Memory Footprint

### Protected VPS Services Check
All protected services (`caddy`, `portainer`, `uptime-kuma`, `dozzle`) remain untouched and running:
```bash
$ docker ps --format 'table {{.Names}}\t{{.Status}}' | grep -E 'caddy|portainer|uptime-kuma|dozzle'
caddy                           Up 22 hours
portainer                       Up 22 hours
uptime-kuma                     Up 22 hours (healthy)
dozzle                          Up 22 hours
```

### Measured Container Memory (Profile W4 - 9 Services Active)
```
CONTAINER                       MEM USAGE / LIMIT   MEM %
novabank-workshops-kafka-1      295.1 MiB / 512 MiB 57.64%
novabank-workshops-apisix-1     105.8 MiB / 384 MiB 27.55%
novabank-workshops-temporal-1   99.06 MiB / 384 MiB 25.80%
novabank-workshops-api-1        89.61 MiB / 256 MiB 35.00%
novabank-workshops-worker-1     69.68 MiB / 512 MiB 13.61%
novabank-workshops-adapter-1    59.65 MiB / 256 MiB 23.30%
novabank-workshops-postgres-1   17.14 MiB / 384 MiB  4.46%
novabank-workshops-jaeger-1     11.65 MiB / 256 MiB  4.55%
novabank-workshops-opa-1         7.36 MiB / 128 MiB  5.75%
------------------------------------------------------------
Total Working Set:              ~755.05 MiB (0.74 GiB)
Operating Budget:               6.00 GiB VPS Available
```
- Historical sampled peak: ~995 MB / 949 MiB. Current active usage: ~755 MB / 720 MiB.
- Single active profile policy strictly enforced.

---

## Remaining Gaps & Transparent Accounting

1. **Windows 11 / WSL2 5 GB Benchmark**: Unverified on this Linux VPS host (Ubuntu x86_64). Documented in `config/manifest.json`.
2. **LangGraph Multi-Step Reasoning**: Simulated deterministically inside `src/worker/workflows.py` activities to provide reproducible offline execution.
3. **Local Built Images**: Built images are tagged `1.0.0` from local Dockerfiles with pinned base image digests, rather than pulled as pre-built images from an external registry.

