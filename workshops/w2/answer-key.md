# Workshop 2 — Facilitator guide and answer key

Use the [worksheet](worksheet.md) for the 45-minute schedule, commands and exact
expected outputs. Keep Governance Studio at **http://localhost:9080/workshop-2**
on screen; use terminal commands for startup and the OPA outage only.

## Preflight

1. Complete the [workshop Python setup](../../docs/workshops/participant-infra-guide.md#step-23-set-up-python-virtual-environment-for-workshop-clients-verification--tests). Run `./scripts/workshop pull w2`, `./scripts/workshop switch w2`, then `./scripts/workshop verify w2`.
2. Run `.venv/bin/python workshops/w2/rehearsal_console.py --outage`; add `--live`
   only when provider credentials and the fictional-data transfer are intended.
3. Inspect timestamped console evidence. Reset seeded lab data before delivery
   with `./scripts/workshop reset w2 --yes` after preserving evidence you need.
4. Open Jaeger; inspect an exported trace using a console trace ID. Have a saved
   JSON run available if provider or telemetry services fail during the session.
5. Verify OPA is unpaused. Keep one workshop profile and one presenter active.

## Presenter narrative

**0–5:** “Our support agent can read a ticket. The ticket contains an instruction
from outside the trust boundary. What would authorize the requested payment?”
Run the recorded injection. Explain that fixed model output makes this policy
exercise reproducible; the real MCP, OPA and bank services still execute.

**5–12:** Draw three responsibilities: model/provider access at Gate 1; signed
identity plus actual tool arguments at Gate 2; scoped API identity and business
invariants at Gate 3. The physical gateway is shared in this lab. Show which
requests actually happened in the evidence rather than claiming all gates ran
for every button.

**12–22:** Run the optional live review. Accept a refusal as a valid model result.
Do not weaken its prompt to force a dramatic attack. If it proposes an invalid
call, validation stops it before the MCP payment request. If it proposes a valid
call, external policy decides. Return to the recorded attack to demonstrate a
repeatable denial regardless of model behavior.

**22–34:** Compare the four request/identity buttons. Ask attendees to predict
each result first. Show a persisted proposal ID and `pending` status alongside
zero new payments; a successful MCP envelope alone does not imply payment.

**34–41:** Pause OPA and use the small-payment button. Show timeout denial and
observed zero changes; unpause OPA. Correlate trace ID, request, decision, proposal
and payment records. The observer's account reads still work during the outage.

**41–45:** Use the blueprint panels to ask who owns inventory, approved egress,
data classification, tool policy, high-impact review, evidence retention and
incident response. The lab is a reference implementation, not a compliance claim.

## Answers and implementation boundaries

| Question | Answer |
|---|---|
| Can instructions in a ticket grant a role? | No. The console issues a fixed short-lived lab JWT; the adapter validates it. Text and request headers cannot choose the role used in this demo. |
| Why is the injected proposal denied? | The actual `beneficiary` argument matches `fraud-account-66`, a prohibited beneficiary. Amount is 900,000 minor units (₹9,000) in the recorded fixture. |
| What is the automatic threshold? | Support/teller low-risk payments up to and including 100,000 minor units (₹1,000); 100,001–1,000,000 requires approval. |
| Why does the viewer fail on ₹250? | Its signed role satisfies no payment rule; default decision is `deny`, reason `NO_MATCHING_RULE`. |
| Does approval-required move funds? | It creates a persisted proposal. The console checks the shared account balance and payment count before and after; expected deltas are zero. |
| Does pausing OPA bypass policy? | No. The adapter timeout produces `POLICY_TIMEOUT_FAIL_CLOSED`. An unavailable service can instead produce `POLICY_UNAVAILABLE_FAIL_CLOSED`. |
| Does live refusal prove OPA blocked a payment? | No. The response is explicitly `no_tool_proposed`; only the case-read policy was exercised. |
| Does a trace ID prove end-to-end auditability? | No. Confirm exported spans and durable banking records; define storage retention and access controls separately. |
| Does the demo stop data leakage or shadow AI everywhere? | No. Minimal provider input is shown; enterprise inventory, approved egress and DLP are blueprint extensions. |

## Policy exercise

The active file is `spikes/spike3_opa/policy.rego`; the completed teaching copy is
`workshops/w2/checkpoints/completed/policy-hardened.rego`. Both use
`input.arguments.beneficiary`, not `destination_account`. OPA 0.68 supports the
existing rule syntax; preserve mutually exclusive reason rules when modifying it.
For a payment that is both above the ceiling and blacklisted,
`PROHIBITED_BENEFICIARY` takes precedence, avoiding conflicting complete-rule outputs.

Inspect the existing rules together. Removing `support_agent` from both small
payment decision/reason rules changes its ₹250 result to the default denial.
Merely raising OPA's auto-allow ceiling does not remove Core Banking's independent
100,000-minor-unit approval requirement. This illustrates policy layering.

## Enterprise blueprint and references

Use an inventory with owners and use cases; evaluate risks in context; measure
behavior and failures; manage residual risks throughout operation. This teaching
mapping follows the four NIST AI RMF functions, including its inventory and
monitoring outcomes. It is not a certification checklist.
[NIST AI RMF Core](https://airc.nist.gov/airmf-resources/airmf/5-sec-core/).

Validate intended token audiences at the MCP boundary and use appropriately scoped
downstream credentials. The lab demonstrates audience separation and token
exchange; it does not implement the complete current MCP authorization discovery
flow. The MCP security guidance rejects token passthrough.
[MCP Security Best Practices](https://modelcontextprotocol.io/docs/draft/tutorials/security/security_best_practices).

Before production, replace shared lab identities/secrets, require authenticated
model access, enforce approved egress and tenant/resource authorization, redact
sensitive telemetry, design idempotent execution and durable approvals, and test
failure recovery. Plan legal/compliance requirements for the actual use case and
jurisdiction with the responsible teams.

## Fresh rehearsal notes (2026-10-05)

Both the historical CLI and current Governance Studio outage rehearsals passed.
Use `rehearsal_console.py --outage` for the current story: the CLI runner switches
W2 itself and tests a ₹50,000 ceiling request; the console uses ₹15,000. Both
exceed the ₹10,000 policy ceiling. Compare balance and payment-count deltas,
not absolute balances, because profile verification and permitted scenarios
create payments in the shared fictional ledger. Preserve evidence, then reset
bank data before attendees start. See the [series dry-run report](../../docs/workshops/rehearsal-2026-10-05.md).
