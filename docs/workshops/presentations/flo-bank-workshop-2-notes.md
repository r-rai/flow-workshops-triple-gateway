# Workshop 2: The ticket that tried to give orders

Beyond API Governance: Securing AI Agents, MCP Servers, and Enterprise Integrations

Duration: 45 minutes. Last slide is presenter reference outside the timed agenda.

Expected outcomes in these slides are instructional targets, not fresh execution results.

## 01. The ticket that tried to give orders

**Timing:** 0–5 min

Flo is allowed to read a support ticket. Someone has placed instructions inside it. Ask what decides whether the bank pays if those instructions become a tool call. Use Governance Studio at http://localhost:9080/workshop-2.

Sources: [workshop-2-story.md](../../../docs/workshops/workshop-2-story.md), [worksheet.md](../../../workshops/w2/worksheet.md), [answer-key.md](../../../workshops/w2/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md)

## 02. The 45-minute route

**Timing:** 0–5 min

Use one presenter against the shared seeded ledger. Recorded scenarios need no provider key. Installation and setup are outside this clock. Optional live inference remains bounded and separately labelled.

Sources: [workshop-2-story.md](../../../docs/workshops/workshop-2-story.md), [worksheet.md](../../../workshops/w2/worksheet.md), [answer-key.md](../../../workshops/w2/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md)

## 03. An authorized read can return untrusted text

**Timing:** 0–5 min

Open Replay the unsafe proposal. Identify where data could be mistaken for an instruction. The ticket asks for 900000 INR, while the fixed W2 request is 900,000 paise. Keep those distinct.

Sources: [workshop-2-story.md](../../../docs/workshops/workshop-2-story.md), [worksheet.md](../../../workshops/w2/worksheet.md), [answer-key.md](../../../workshops/w2/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md)

## 04. Replay the unsafe proposal

**Timing:** 0–5 min

The fixture bypasses model inference but exercises the real governance services. A denial proves the submitted request was blocked. It does not establish that a live model was compromised, or that the ticket's rupee amount was interpreted faithfully.

Sources: [workshop-2-story.md](../../../docs/workshops/workshop-2-story.md), [worksheet.md](../../../workshops/w2/worksheet.md), [answer-key.md](../../../workshops/w2/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md)

## 05. Give each gate a precise responsibility

**Timing:** 5–12 min

A recorded proposal skips inference. A denied payment may stop at Gate 2 before reaching the banking API. Avoid narrating a full successful call path when the observed request was stopped earlier.

Sources: [workshop-2-story.md](../../../docs/workshops/workshop-2-story.md), [worksheet.md](../../../workshops/w2/worksheet.md), [answer-key.md](../../../workshops/w2/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md)

## 06. Workshop 2 architecture: proposal to execution

**Timing:** 5–12 min

Read the diagram in two stages. The Governance Studio backend first reads the case through MCP and Gate 3. For live review, it sends minimal case context through Gate 1 to the hosted model and validates at most one returned payment proposal. Recorded replay supplies a fixed proposal without inference. Both payment paths enter Gate 2, where the MCP adapter validates signed identity and arguments and queries OPA. An allowed payment traverses Gate 3 API-key authentication and Core Banking's signed-identity, approval and ledger rules. Approval-required requests can persist a pending proposal with no debit. PostgreSQL holds banking records; exported telemetry is inspected in Jaeger. APISIX implements all three logical gateway routes. Gate 1 enforces inference budgets and output limits; this lab has no dedicated gateway prompt-injection filter. Model instructions treat case text as untrusted. Denied payment calls stop at Gate 2; independent observer reads do not prove that payment reached Core Banking.

Sources: [workshop-2-story.md](../../../docs/workshops/workshop-2-story.md), [worksheet.md](../../../workshops/w2/worksheet.md), [answer-key.md](../../../workshops/w2/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md)

## 07. Model behavior and permission are distinct

**Timing:** 12–22 min

If configured, use Ask Flo to review the case. It makes at most one bounded provider call with minimal case context and validates at most one payment proposal. Accept refusal or provider failure as the observed result. Never silently relabel replay as live.

Sources: [workshop-2-story.md](../../../docs/workshops/workshop-2-story.md), [worksheet.md](../../../workshops/w2/worksheet.md), [answer-key.md](../../../workshops/w2/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md)

## 08. Exercise: predict four business outcomes

**Timing:** 22–34 min

Give pairs a short prediction window. Record the validated signed role, actual amount and beneficiary. The console uses fixed server-owned scenarios; browser selection is not arbitrary identity or tool authority.

Sources: [workshop-2-story.md](../../../docs/workshops/workshop-2-story.md), [worksheet.md](../../../workshops/w2/worksheet.md), [answer-key.md](../../../workshops/w2/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md)

## 09. Compare predictions with actual evidence

**Timing:** 22–34 min

Exact ceiling reason: AMOUNT_EXCEEDS_TRANSFER_CEILING. Review each downloaded result. Repeated successful small-payment scenarios mutate the fictional ledger, so compare per-run effects, not an assumed absolute balance.

Sources: [workshop-2-story.md](../../../docs/workshops/workshop-2-story.md), [worksheet.md](../../../workshops/w2/worksheet.md), [answer-key.md](../../../workshops/w2/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md)

## 10. Policy evaluates the real request

**Timing:** 22–34 min

Show spikes/spike3_opa/policy.rego and the checkpoints linked from the worksheet. Ask what removing support_agent from both the low-risk decision and reason rules would do. Make consistent changes on a private offline copy; do not install the broad teaching checkpoint on the shared presenter stack.

Sources: [workshop-2-story.md](../../../docs/workshops/workshop-2-story.md), [worksheet.md](../../../workshops/w2/worksheet.md), [answer-key.md](../../../workshops/w2/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md)

## 11. Thresholds define the support-agent path

**Timing:** 22–34 min

These are W2 support-agent policy thresholds, not W3 resolver approval rules. Raising an OPA allowance alone does not bypass the banking approval requirement. The W2 console stores pending proposals but does not approve or settle them.

Sources: [workshop-2-story.md](../../../docs/workshops/workshop-2-story.md), [worksheet.md](../../../workshops/w2/worksheet.md), [answer-key.md](../../../workshops/w2/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md)

## 12. A pending proposal has no financial effect

**Timing:** 22–34 min

Ask participants which component owns the persisted approval record. W2 introduces this lightweight state; W3 supplies a durable workflow pause and W4 demonstrates independent exact-transaction review.

Sources: [workshop-2-story.md](../../../docs/workshops/workshop-2-story.md), [worksheet.md](../../../workshops/w2/worksheet.md), [answer-key.md](../../../workshops/w2/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md)

## 13. Demo: policy stops answering

**Timing:** 34–41 min

Use the small-payment button: case-review actions require a governed case read first. The automated outage runner restores OPA in a finally block. A timeout must never become execution permission.

```bash
docker compose pause opa

# In Governance Studio: click Pay ₹250 to a vendor
# Inspect decision, balance and new-payment count

docker compose unpause opa
```

Sources: [workshop-2-story.md](../../../docs/workshops/workshop-2-story.md), [worksheet.md](../../../workshops/w2/worksheet.md), [answer-key.md](../../../workshops/w2/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md)

## 14. Build an evidence chain, not just a screenshot

**Timing:** 34–41 min

Open Jaeger at http://localhost:16686. Observer reads are separate from the denied request. W2 console payment requests currently lack idempotency keys: inspect ledger effects before retrying an ambiguous response.

Sources: [workshop-2-story.md](../../../docs/workshops/workshop-2-story.md), [worksheet.md](../../../workshops/w2/worksheet.md), [answer-key.md](../../../workshops/w2/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md)

## 15. Assign an owner to each governance concern

**Timing:** 41–45 min

The blueprint panels discuss enterprise controls beyond the lab. Do not imply the development stack implements enterprise DLP, shadow-AI discovery, full MCP OAuth discovery, production IAM, immutable audit storage or compliance certification.

Sources: [workshop-2-story.md](../../../docs/workshops/workshop-2-story.md), [worksheet.md](../../../workshops/w2/worksheet.md), [answer-key.md](../../../workshops/w2/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md)

## 16. The ticket can suggest. The platform decides.

**Timing:** 41–45 min

Ask each pair to explain one denial and the pending-proposal result using evidence. Close with the difference between model behavior and enforcement.

Sources: [workshop-2-story.md](../../../docs/workshops/workshop-2-story.md), [worksheet.md](../../../workshops/w2/worksheet.md), [answer-key.md](../../../workshops/w2/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md)

## 17. Presenter preparation & source guide

**Timing:** Reference / outside timed delivery

Use sample login maya@flobank.demo / flo-demo. The rehearsal writes timestamped evidence in workshops/w2/evidence and does not reset or switch profiles. Preserve old evidence before any fictional-ledger reset. For optional live review, see docs/workshops/openrouter-setup.md and provider configuration guidance. No live calls are needed for the recorded exercise.

```bash
./scripts/workshop switch w2
./scripts/workshop verify w2

# Technical rehearsal on the prepared stack:
.venv/bin/python workshops/w2/rehearsal_console.py --outage
```

Sources: [workshop-2-story.md](../../../docs/workshops/workshop-2-story.md), [worksheet.md](../../../workshops/w2/worksheet.md), [answer-key.md](../../../workshops/w2/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md)
