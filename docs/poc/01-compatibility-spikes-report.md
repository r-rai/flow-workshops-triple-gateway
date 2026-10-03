# Compatibility Spikes & Security Probes Report

**Date:** 2026-10-03  
**Environment:** Linux VPS (4 vCPUs, 7.8 GiB RAM, Docker Engine 29.8.2, Docker Compose v5.6.0)  
**Task Branch:** `feat/implement-novabank-platform`

---

## Summary of Results

| Spike ID | Target Boundary / Capability | Status | Verified Invariants |
|---|---|---|---|
| **Spike 1** | APISIX Standalone + OpenAPI-to-MCP | **PASSED** | Standalone APISIX 3.19.0 (YAML config provider without etcd) loads `openapi-to-mcp` plugin, fetches OpenAPI 3.0 schema from FastAPI, generates MCP tool catalog (`tools/list`), and handles `tools/call` over Streamable HTTP (SSE text/event-stream chunks). |
| **Spike 2** | Gate 2 -> Gate 3 Loopback | **PASSED** | MCP tool invocation (`tools/call`) forwards requests to APISIX Gate 3 route (`/api/v1/*`). Gate 3 `key-auth` validates credentials; unauthorized requests return 401 Unauthorized, and valid credentials return business payload. Direct backend access is blocked. |
| **Spike 3** | Argument-Aware OPA Policy | **PASSED** | Curated Python MCP adapter normalizes arguments and identity, querying OPA (`openpolicyagent/opa:0.68.0-static`). Returns explicit machine-readable decisions: `allow`, `deny`, `approval_required`. Approval-required creates pending proposal without executing payment. OPA outage/timeout fails closed (`POLICY_UNAVAILABLE_FAIL_CLOSED`). |
| **Spike 4** | Audience-Separated Identity | **PASSED** | Distinct audiences enforced: `novabank-mcp` vs `novabank-api`. MCP token directly presented to Gate 3 is rejected (`401/403 Invalid Audience`). RFC 8693 token exchange downscopes permissions and attaches delegation context (`act`). Gate 3 rejects insufficient scopes and expired tokens; untrusted caller headers are stripped. |
| **Spike 5** | Distributed Trace Stitching | **PASSED** | W3C `traceparent` context propagated across all 5 boundaries: `agent.negotiator_run` -> `gate1.inference_call` -> `gate2.mcp_tool_call` -> `gate3.api_call` -> `backend.execute_payment`. Complete hierarchical waterfall verified in Jaeger (`jaegertracing/all-in-one:1.57`) via REST API query. |
| **Spike 6** | Host Memory & Feasibility Probe | **PASSED (VPS)** | Baseline host RAM: total 7,941 MiB, used 1,266 MiB (~1.2 GiB), available 6,674 MiB (~6.5 GiB). Tested container footprints: APISIX (~95 MiB), OPA (~28 MiB), Jaeger (~45 MiB). Single profile limits fit well within the 6 GB operating budget. |
| **Spike 7** | A2A Protocol & Approval Idempotency | **PASSED** | Agent Card discovered at `/.well-known/agent.json`. A2A tasks strictly owner-scoped; unrelated principals denied read/mutate with 403. Self-approval blocked. Approvals bound cryptographically to exact arguments; single-use atomic consumption prevents reuse. Backend idempotency cache safely replays duplicates without duplicate mutation. |

---

## Detailed Spike Evidence

### 1. Spike 1 & 2: APISIX Standalone, OpenAPI-to-MCP & Gate 3 Loopback
- **Pointers:** `spikes/spike1_2/app.py`, `spikes/spike1_2/apisix_conf/apisix.yaml`, `spikes/spike1_2/run_spike.py`
- **Execution Command:** `.venv/bin/python spikes/spike1_2/run_spike.py`
- **Key Findings:**
  - APISIX 3.19.0 runs in standalone mode using `deployment.role_data_plane.config_provider: yaml`.
  - The `openapi-to-mcp` plugin operates with `transport: streamable_http` and streams responses as SSE `text/event-stream` chunks (`data: {"jsonrpc": "2.0", ...}`).
  - Loopback invariant verified: Calling `tools/call` for `get_account_api_v1_accounts__id__get` re-enters APISIX route `/api/v1/*`.
  - With invalid `X-API-Key: wrong-secret`, Gate 3 rejects with 401 Unauthorized (`Invalid API key in request`).
  - With valid `X-API-Key: gate3-secret-token`, Gate 3 proxies to FastAPI, returning HTTP 200 with balance `1500000 INR`.

### 2. Spike 3: Argument-Aware OPA Policy & Adapter Contract
- **Pointers:** `spikes/spike3_opa/policy.rego`, `spikes/spike3_opa/adapter_sim.py`
- **Execution Command:** `.venv/bin/python spikes/spike3_opa/adapter_sim.py`
- **Key Findings:**
  - Policy decisions:
    - Small payment (<= 100,000 minor units): `allow`, reason `PAYMENT_PREAPPROVED_LIMIT`.
    - Medium payment (100,001 to 1,000,000 minor units): `approval_required`, reason `AMOUNT_EXCEEDS_UNSUPERVISED_LIMIT`. Generates pending proposal record; zero financial mutation occurs.
    - Large payment (> 1,000,000 minor units): `deny`, reason `AMOUNT_EXCEEDS_TRANSFER_CEILING`.
    - Sanctioned beneficiary: `deny`, reason `PROHIBITED_BENEFICIARY`.
    - Outage test: Stopping the OPA container causes immediate fail-closed denial (`POLICY_UNAVAILABLE_FAIL_CLOSED`).

### 3. Spike 4: Audience-Separated Identity & Token Exchange (RFC 8693)
- **Pointers:** `spikes/spike4_identity/test_spike4.py`, `spikes/spike4_identity/realm-export.json`
- **Execution Command:** `.venv/bin/python spikes/spike4_identity/test_spike4.py`
- **Key Findings:**
  - Direct presentation of token with `aud: novabank-mcp` to Gate 3 API (`aud: novabank-api`) is rejected with `Invalid audience`.
  - Token exchange swaps `novabank-mcp` for `novabank-api`, attaches adapter delegation actor (`act.sub = mcp-adapter`), and downscopes scopes to `api:accounts:read`.
  - Presenting exchanged token for write action (`api:payments:write`) fails with `Gate 3 Scope Check Failed`.
  - Expired tokens and caller-spoofed headers fail closed.

### 4. Spike 5: W3C Trace Stitching across 5 Boundaries
- **Pointers:** `spikes/spike5_trace/test_spike5.py`
- **Execution Command:** `.venv/bin/python spikes/spike5_trace/test_spike5.py`
- **Key Findings:**
  - Standard W3C `traceparent` context propagated through:
    1. `agent.negotiator_run` (Root)
    2. `gate1.inference_call` (Inference Gate)
    3. `gate2.mcp_tool_call` (Capability Gate)
    4. `gate3.api_call` (API Gate)
    5. `backend.execute_payment` (FastAPI)
  - Queried Jaeger REST API (`http://127.0.0.1:16686/api/traces/{trace_id}`); verified all 5 spans share root `trace_id` and have correct parent-child relationships.

### 5. Spike 7: A2A Protocol, Agent Card, Ownership & Approval Idempotency
- **Pointers:** `spikes/spike7_a2a_approval/test_spike7.py`
- **Execution Command:** `.venv/bin/python spikes/spike7_a2a_approval/test_spike7.py`
- **Key Findings:**
  - Agent Card discovered at `/.well-known/agent.json`.
  - A2A tasks submitted and owner-bound (`task.owner_id = "agent-negotiator"`). Unrelated agents receive 403 Access Denied on task reads and task cancellations.
  - Self-approval by the requesting agent is rejected.
  - Approvals bind cryptographically to canonical SHA-256 argument hash; tampered arguments during execution trigger `ARGUMENT_MISMATCH`.
  - Single-use consumption is enforced atomically; duplicate execution attempts with consumed approval trigger `APPROVAL_ALREADY_CONSUMED`.
  - Backend idempotency: Identical request retries return cached result with zero balance mutation. Idempotency key reuse with different arguments is rejected with `IDEMPOTENCY_KEY_REUSE_PAYLOAD_MISMATCH`.

---

## Unverified Requirements & Concrete Limitations

1. **Windows 11 / WSL2 Hardware Benchmark (Spike 6)**:
   - **Status:** **UNVERIFIED (Pending participant hardware)**.
   - **Reason:** The active execution environment is Linux VPS (`vmi3355051`). Windows 11 / WSL2 5 GB capped memory benchmarks cannot be executed on this Linux host and must be conducted on participant hardware during release hardening.
2. **Keycloak Token Exchange in Live Docker Profile**:
   - Tested RFC 8693 token exchange semantics; full Keycloak container will be packaged in Work Package 4 (`w2`/`w4` profiles). W3 uses signed lab credentials as intended.
3. **Live LLM Provider Egress**:
   - Deterministic replay fixtures used for spikes. Live provider API keys must remain local to participants or presenter.
