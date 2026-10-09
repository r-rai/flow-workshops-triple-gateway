# Workshop 4 · Mobile Participant Companion
## “The Day the Agent Broke the Bank” — Observation Guide

Welcome to the **Flo Bank Incident Room** on your mobile device.

You are accessing an observation-only view of 11 curated, recorded execution runs. You do not need to run Docker or Python on your phone; your role is to investigate the evidence, inspect security boundaries, and answer the workshop questions.

---

### Access Details
* **Public URL:** `https://w4.ravirai.in/workshop-4`
* **Access Code:** Check the presenter slide (e.g. `FLO-W4-2026`)
* **Role:** Participant Observer (`viewer`)

---

### Investigation Checklist across Scenarios

#### 1. Follow the Money: The ₹90 Lakh Loss
* **Scenario:** `vulnerable_replay`
* **Question:** Where did untrusted data become authority?
* **Look for:** The untrusted ticket description, NegotiatorBot’s handoff to PaymentsAgent, and the isolated ledger balance delta (-900,000,000 paise).
* **Observation:** Notice that the protected ledger remained completely unchanged (0 paise delta) because the vulnerable exploit occurred in an isolated sandbox.

#### 2. Contain the Reasoning Loop (Gate 1)
* **Scenario:** `budget_denial`
* **Question:** Does an inference budget denial stop direct tool requests?
* **Look for:** Gate 1 HTTP 429 response, headroom exhaustion, and the boundary map showing Gate 1 denied.

#### 3. Control the Capability (Gate 2)
* **Scenarios:** `prohibited_beneficiary`, `excessive_amount`, `permitted_payment`, `policy_outage`
* **Question:** How does OPA tool policy enforce argument controls?
* **Look for:**
  * Beneficiary check denying `fraud-account-66`.
  * Amount check denying `900,000,000 paise`.
  * Legitimate request allowing `25,000 paise` (₹250).
  * Stopped policy service causing fail-closed denial with `POLICY_` error.

#### 4. The Attacker Changes Routes (Gate 3)
* **Scenarios:** `wrong_audience`, `insufficient_scope`, `scope_escalation`, `valid_exchange`
* **Question:** What stops an agent from bypassing tool policies and calling the banking API directly?
* **Look for:**
  * MCP audience token presented to API returning HTTP 401.
  * Read-only token attempting payment write returning HTTP 403.
  * Unauthorized scope exchange returning HTTP 403.
  * Valid token exchange returning HTTP 200 with sanitized delegation claims.

#### 5. Approval & Second Trust Boundary (A2A & Approvals)
* **Scenario:** `legitimate_delegation`
* **Question:** Who independently approves the settlement, and how is it bound to the task?
* **Look for:**
  * Self-approval by `payments-agent-executor` rejected.
  * Independent reviewer required.
  * Idempotent retry proving exactly one financial effect.
  * A2A task output bound to the exact `payment_id`.

---

### Summary Findings
* **Paise vs. Rupees:** All API amounts are integer paise (divide by 100).
* **Identities vs. Permissions:** Valid identity tokens are necessary, but insufficient without audience, scope, delegation, and policy gates.
