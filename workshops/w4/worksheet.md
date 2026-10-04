# Workshop 4 Worksheet: The Day the Agent Broke the Bank: Implementing Triple-Gate Architecture & A2A Security for Autonomous AI Workloads

**Duration**: 135 Minutes  
**Profile**: `w4`  
**Focus**: Defense-in-depth across three security boundaries, restricted identity, supervisory human-in-the-loop approvals, and secure Agent-to-Agent (A2A) delegation.

---

## 🎯 Objectives
1. Reproduce a multi-step financial exploit against an unconstrained AI agent.
2. Implement and test **Gate 1** (Model Guardrails & Inference Budgets).
3. Implement and test **Gate 2** (OPA Argument-Aware Capability Policies).
4. Implement and test **Gate 3** (APISIX Gateway Cryptographic Enforcement & RFC 8693 Token Exchange).
5. Enforce **Anti-Self-Approval** and exact **Argument Hash Binding** on financial mutations.
6. Build and verify **Agent-to-Agent (A2A)** collaboration between `NegotiatorBot` and `PaymentsAgent` with owner-scoped isolation.
7. Reconstruct the entire exploit and remediation using W3C distributed traces in Jaeger.

---

## ⏱️ Session Roadmap

| Segment | Timing | Activity | Artifacts |
|---|---|---|---|
| **1. Incident Briefing** | 00:00–00:10 | Review the NegotiatorBot incident scenario | Incident briefing doc |
| **2. Reproduce the Exploit** | 00:10–00:25 | Execute prompt injection against vulnerable baseline | Simulated exploit script |
| **3. Gate 1 Controls** | 00:25–00:40 | Provider access and inference budget bounds | Local replay provider |
| **4. Gate 2 Controls** | 00:40–01:00 | Rego argument policies: block prohibited accounts | `policy-hardened.rego` |
| **5. Break** | 01:00–01:05 | Rest and environment sync | Checkpoint sync |
| **6. Gate 3 Controls** | 01:05–01:25 | RFC 8693 token exchange; audience & scope enforcement | APISIX config |
| **7. Approval Engine** | 01:25–01:45 | Anti-self-approval rule; argument tampering rejection | `src/services/approvals.py` |
| **8. A2A Collaboration** | 01:45–02:00 | Agent Card discovery; owner-scoped task access | `src/agents/` |
| **9. Trace Reconstruction** | 02:00–02:10 | Reconstruct incident timeline in Jaeger UI (`:16686`) | Trace waterfall |
| **10. Review & Operations**| 02:10–02:15 | Wrap-up, production separation, residual risks | Rehearsal evidence |

---

## 🛠️ Step-by-Step Instructions

### Step 1: Environment Readiness
Ensure profile `w4` is active and healthy:
```bash
./scripts/workshop switch w4
./scripts/workshop status
./scripts/workshop verify w4
```

### Step 2: Testing Gate 3 Audience Separation
Attempt to call Gate 3 Core Banking API using a token issued for the MCP capability layer (`aud=novabank-mcp`):
```python
# The gateway enforces audience separation:
token = create_jwt_token("attacker", audience="novabank-mcp", scopes=["api:accounts:read"])
# Result: HTTP 401 Unauthorized
```

### Step 3: Verifying Anti-Self-Approval
When `PaymentsAgent` submits a proposal for high-value funds:
```bash
.venv/bin/python -c "
import asyncio
from src.agents.payments_agent import PaymentsAgent
async def main():
    agent = PaymentsAgent()
    p = await agent.submit_proposal('acc-102', 'acc-101', 150000)
    print('Proposal:', p['proposal_id'])
    res = await agent.attempt_self_approval(p['proposal_id'])
    print('Self-approval response:', res['status_code'])
asyncio.run(main())
"
```
**Verify**: Output shows `Self-approval response: 403`. Agents cannot approve their own financial proposals!

### Step 4: Testing Argument Tampering Rejection
If an attacker intercepts an approved proposal `prop-123` and attempts to execute it with a modified transfer amount (e.g. INR 2,000 instead of INR 1,500):
**Verify**: Gate 3 rejects execution with `HTTP 400: Execution arguments do not match the approved proposal arguments`.

### Step 5: Testing A2A Owner-Scoped Isolation
Run `NegotiatorBot` to create a task:
```python
task = await negotiator.delegate_payment_task("case-501", 50000, "acc-101")
```
When an unrelated rogue agent attempts to query `task['task_id']`:
**Verify**: API returns `HTTP 403 Forbidden: caller does not own task`.

### Step 6: Automated Rehearsal
Run the complete automated 135-minute rehearsal:
```bash
.venv/bin/python workshops/w4/rehearsal_w4.py
```
Check evidence in `workshops/w4/evidence/rehearsal-evidence.json`.
