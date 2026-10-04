# Flo Bank Workshop Series: Master Facilitator & Delivery Guide

## 📌 Executive Overview
This guide provides complete instructions for instructors, facilitators, and operators delivering the 4-workshop enterprise series:
1. **Workshop 1**: The Agentic API Evolution – Turning Core Banking APIs into MCP (45 min)
2. **Workshop 2**: Beyond API Governance – Securing AI Agents & MCP (45 min)
3. **Workshop 3**: Architecting the Agentic Enterprise – Middleware, Durable State, and Event-Driven AI (45 min)
4. **Workshop 4**: The Day the Agent Broke the Bank – Triple-Gate Architecture and A2A Security (135 min)

---

## Customer UI demonstration

Use the same Compose file as the workshop infrastructure:

```bash
docker compose --profile demo up -d --build
```

Open **http://localhost:8000**; the prefilled login is
`maya@flobank.demo` / `flo-demo`. Show a balance query, card freeze/unfreeze,
and a simulated dispute. This scripted Flo bot is separate from the W3
LangGraph investigation agent. In a running workshop profile, the UI is also
available through APISIX at **http://localhost:9080**. No additional UI service
or scripts are needed for that workshop route.

Use `docker compose stop demo` to stop the standalone simulation. Use the
existing launcher below for workshop readiness, verification, and switching.
Current service sets and configured limits are in the
[VPS runbook](../setup/vps-setup-guide.md); the [participant guide](../setup/participant-requirements.md)
contains laptop setup commands.

## ⚙️ VPS Architecture & Resource Protection Policy

### Resource Budget & Coexistence Invariant
- **Host**: Linux VPS (`vmi3355051` / 8 GB RAM total).
- **Hard Limit**: The workshop platform must operate within a strict **6 GB operating memory budget**.
- **Existing Host Services**: Existing services (`caddy`, `portainer`, `uptime-kuma`, `dozzle`) must **never** be stopped, restarted, or altered.
- **Single Profile Policy**: Always run **one active workshop profile at a time**. Never run multiple profiles simultaneously:
  ```bash
  # Correct way to transition profiles
  ./scripts/workshop switch w1
  ./scripts/workshop switch w2
  ./scripts/workshop switch w3
  ./scripts/workshop switch w4
  ```

---

## 🚀 Pre-Session Checklist (Run Before Every Workshop)

1. **Preflight Environment**:
   ```bash
   ./scripts/workshop preflight
   ```
   *Checks Docker/Compose, Python, host memory and disk, gateway port 9080, and pinned image digests.*

2. **Switch to Session Profile**:
   ```bash
   ./scripts/workshop switch <w1|w2|w3|w4>
   ```

3. **Verify Container Health & Smoke Test**:
   ```bash
   ./scripts/workshop status
   ./scripts/workshop verify <w1|w2|w3|w4>
   ```

4. **Verify Offline Replay Provider Fallback (W2–W4)**:
   The platform defaults to `USE_REPLAY_FIXTURES=true`, which serves deterministic model fixtures without provider calls. W1 has no Gate 1 inference route, so skip this check for W1. The customer Flo bot remains scripted in every profile.
   ```bash
   curl -s -X POST http://127.0.0.1:9080/ai/chat/completions \
     -H "Content-Type: application/json" \
     -d '{"messages": [{"role": "user", "content": "What is the balance of acc-101?"}]}'
   ```

5. **Reset Seed Data**:
   ```bash
   FORCE=true ./scripts/workshop reset <w1|w2|w3|w4>
   ```

---

## 🧪 Workshop Verification & Rehearsal Index

| Workshop | Profile | Automated Rehearsal Command | Verification Command | Evidence Location |
|---|---|---|---|---|
| **W1: OpenAPI to MCP** | `w1` | `.venv/bin/python workshops/w1/rehearsal_w1.py` | `./scripts/workshop verify w1` | `workshops/w1/evidence/rehearsal-evidence.json` |
| **W2: Governance** | `w2` | `.venv/bin/python workshops/w2/rehearsal_w2.py` | `./scripts/workshop verify w2` | `workshops/w2/evidence/rehearsal-evidence.json` |
| **W3: Durability** | `w3` | `.venv/bin/python workshops/w3/rehearsal_w3.py` | `./scripts/workshop verify w3` | `workshops/w3/evidence/rehearsal-evidence.json` |
| **W4: Triple-Gate** | `w4` | `.venv/bin/python workshops/w4/rehearsal_w4.py` | `./scripts/workshop verify w4` | `workshops/w4/evidence/rehearsal-evidence.json` |

---

## 🔒 Security Invariants Enforced

1. **Loopback Gate 3 Enforcement**: The core banking backend (`api:8000`) is bound exclusively to internal Docker networks (`novabank-backend`, `novabank-persistence`). External clients must access the API via APISIX Gate 3 (`http://127.0.0.1:9080/api/v1/*`), requiring valid cryptographic authentication (`X-API-Key` and/or RFC 8693 Bearer JWT).
2. **Deterministic Argument Evaluation (Gate 2)**: Open Policy Agent (OPA) strictly evaluates extracted runtime arguments (`account_id`, `destination_account`, `amount`) before tools can be invoked, blocking prohibited beneficiaries (`fraud-account-66`) and enforcing tiered risk approvals.
3. **Fail-Closed Resiliency**: If OPA crashes, times out, or becomes partitioned, the adapter strictly denies execution with `POLICY_TIMEOUT_FAIL_CLOSED`.
4. **Anti-Self-Approval**: Agents are strictly prohibited from approving their own financial proposals (`403 Forbidden`). Only authorized manager principals can approve proposals.
5. **Durable Pause & Zero Duplicate Effects**: Temporal workflows maintain durable history across worker crashes. Settle activities use stable backend idempotency keys (`settle-dispute-{case_id}`) preventing duplicate settlement payments when activities retry.
6. **Owner-Scoped A2A Isolation**: Delegated tasks in the A2A registry are strictly scoped to the calling principal's identity; unauthorized agents attempting to query or hijack tasks are denied with `HTTP 403`.

---

## 📊 Verification Status & Unverified Requirements

### Verified on Host Platform (Linux VPS vmi3355051 / Ubuntu x86_64)
- [x] Package 1: All 7 Compatibility Spikes (APISIX, openapi-to-mcp, OPA, RFC 8693, OTel, Host Memory, A2A/Approval)
- [x] Package 2: API Foundation, SQLite/PostgreSQL persistence, idempotency, seed data, Docker Compose, CLI
- [x] Package 3: Workshop 1 OpenAPI curation, SSE transport unwrapping, participant client, automated rehearsal
- [x] Package 4: Workshop 2 Curated MCP adapter, hardened OPA policy, fail-closed tests, automated rehearsal
- [x] Package 5: Workshop 3 Apache Kafka (KRaft), Temporal dev-server, worker crash recovery, zero duplicate payments
- [x] Package 6: Workshop 4 Triple-Gate defense-in-depth, NegotiatorBot & PaymentsAgent, anti-self-approval, A2A isolation
- [x] Package 7: Release manifest, facilitator guide, offline replay fallback, memory budget containment

### Unverified Requirements (Documented Transparently)
- [ ] **Windows 11 / WSL2 5 GB RAM Participant Benchmark**:
  - **Status**: Unverified on local infrastructure.
  - **Reason**: The host system is a Linux VPS. While total Linux container active memory across 9 microservices peaks at ~951 MB / 907 MiB (comfortably within the 6 GB VPS operating budget), Windows 11 WSL2 introduces virtualization overhead (Vmmem process allocation and dynamic memory reclamation) that cannot be measured on a native Linux kernel. This benchmark must be confirmed during participant onboarding on native Windows 11 hardware.

