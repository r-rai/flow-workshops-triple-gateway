# Incident evidence sheet

Use server exports; never copy bearer tokens, signing keys or private model reasoning.

| Record | Required correlation |
|---|---|
| Run | Run ID, scenario, recorded/live inference mode, timestamp and observed state |
| Ticket / proposal | Untrusted ticket ID, exact source/beneficiary/currency/paise amount |
| Caller | Sanitized subject, audience, scopes, role and delegation context |
| Boundary | Actual request arguments, HTTP/MCP response, allow/deny/unresolved outcome |
| Approval | Proposal ID, expiry, independent decision; self approval denial |
| Delegation | Owner and designated executor, task ID, foreign access/completion denials |
| Settlement | Payment ID, stable idempotency key, exact proposal ID, task output binding |
| Ledger | Before/after balance and payment count; null observations mean unresolved |
| Trace | Trace ID and collector-observed services, or explicit incomplete status |

Opening incident expectations: 900,000,000 paise loss, one payment in the separate vulnerable ledger, zero protected-ledger effects. Protected attack expectations: no new payment and no debit. Legitimate delegation: one 150,000-paise debit, one payment, task output equals actual payment ID. A small permitted policy exercise creates one 25,000-paise debit.

Explain one denial: caller ______; audience/scopes ______; arguments ______; service response ______; observed ledger delta ______.

Prove one legitimate payment: run ______; proposal ______; independent reviewer ______; task ______; payment ______; one-effect retry ______; before/after ______; trace observed/incomplete ______.

Exports survive refresh and W4 process restart. One instance executes one active demonstration; do not attribute concurrent external lab activity to the run’s aggregate ledger observations. For uncertain responses, reconcile the keyed payment/proposal before retry. An incomplete trace does not invalidate a banking record, but must not be presented as complete distributed evidence.
