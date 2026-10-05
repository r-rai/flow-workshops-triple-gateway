# Workshop 4 · The Day the Agent Broke the Bank

You are Flo Bank’s response team. NegotiatorBot handles customer cases; PaymentsAgent carries out settlements. A malicious ticket became a payment instruction. The opening loss is **₹90 lakh = 900,000,000 paise**. The incident is a recorded proposal executed against an isolated vulnerable ledger. It does not demonstrate a live model compromise.

Before the session, install dependencies, pull/build images and start your local `w4` instance using the [infrastructure guide](../../docs/workshops/participant-infra-guide.md). Use one instance per pair. Open `http://localhost:9080/workshop-4` and sign in with `maya@flobank.demo` / `flo-demo`. Shared presenter hosting is for observation and recovery, not a multi-tenant lab.

For every exercise: **predict → run → inspect → change → retest**. Predictions stay in your browser. Download server evidence for each result. Integer amounts are paise; divide by 100 for rupees.

| Minutes | One task | Expected evidence |
|---|---|---|
| 0–8 | Vote: identity, model, tool policy or approval? | Your opening prediction |
| 8–20 | Mark where ticket data became authority in NegotiatorBot → PaymentsAgent | Isolated loss of 900,000,000 paise; zero protected-ledger change |
| 20–33 | Predict whether Gate 1 denial stops a direct tool request; compare boundaries | Budget HTTP 429, no inference dispatch; independent Gate 2 result |
| 33–53 | Repair the prepared local policy and test both denied and permitted requests | Prohibited beneficiary denial, amount denial and one ₹250 payment |
| 53–60 | Find the missing audience/scope constraint in a direct API request | HTTP 401 wrong audience and 403 missing scope |
| 60–67 | Break; facilitator restores stalled local labs | Completed checkpoint, readiness results |
| 67–85 | Change the prepared identity request to an entitled scope | Unauthorized exchange 403; permitted exchange 200 and sanitized claims |
| 85–103 | Independently review the exact proposal and predict tampering/retry results | Self approval 403, tampering 400, exact execution and one effect |
| 103–119 | Identify the principal allowed to read, execute, approve and complete | Foreign read 403, unauthorized completion 403, mismatch 400; bound task/payment |
| 119–130 | Explain one denial and prove one legitimate payment | Run → proposal → task → payment → ledger; observed traces or explicit incomplete label |
| 130–135 | Revisit your vote; assign each control an owner | Incident review below |

## Pair exercise: local tool policy

Only your local policy file changes. The initial checkpoint adds `vendor-alpha` to the prohibited list, so the legitimate ₹250 request is denied. The protected transfer ceiling and attacker block remain enforced.

```bash
cp workshops/w4/checkpoints/initial/policy.rego spikes/spike3_opa/policy.rego
docker compose restart opa
```

Run **prohibited beneficiary**, **excessive amount** and **permitted payment** in the console. Predict the three results. Remove only `vendor-alpha` from the prepared prohibited list (or use the completed checkpoint below), restart OPA and retest. Keep `fraud-account-66` prohibited. Evidence comes from the running policy service, not a console switch.

```bash
cp workshops/w4/checkpoints/completed/policy.rego spikes/spike3_opa/policy.rego
docker compose restart opa
```

Expected: the attack requests remain denied; the permitted request creates one 25,000-paise payment. Never retry an uncertain financial request with a new run ID; select the original run and reconcile.

## Pair exercise: local identity request

```bash
.venv/bin/python workshops/w4/exercise_exchange.py initial
```

Inspect `checkpoints/initial/identity.json`: a viewer requests `api:payments:write`. Predict the denial. Change only `requested_scope` to `api:accounts:read`, rerun, then compare with the completed checkpoint:

```bash
.venv/bin/python workshops/w4/exercise_exchange.py completed
```

Use the supplied completed file rather than editing it when you need a checkpoint. Requests mint lab credentials server-side/CLI-side; evidence contains no tokens. In the console, compare **valid exchange**, **wrong audience** and **scope escalation** independently.

## Approval and delegation

Run **legitimate delegation** immediately before review. This creates a 150,000-paise (₹1,500) proposal. Use a separate private window or browser profile for the reviewer; sign in, choose Independent reviewer, and enter the facilitator’s reviewer password. Selecting that view alone grants no authority.

Review all four fields plus the proposal and task IDs. The requester cannot approve, even if a reviewer cookie exists in its own browser. Approve or reject independently. Approval executes the server-owned exact arguments, tests changed arguments and retry, then binds the actual payment to the task. Inspect every boundary result; check the protected balance delta is −150,000 and the payment count delta is 1. Refresh both browsers and compare the evidence.

## Incident review

- What did your original vote miss? Where did untrusted content become authority?
- Explain Gate 1’s responsibility and why a refusal or budget limit cannot authorize or block a separate direct API request.
- Explain one Gate 2 or Gate 3 denial using its actual caller, arguments and response.
- Prove a legitimate settlement with proposal ID, independent reviewer, payment ID, task output and measured ledger delta.
- Assign owners: inference/budgets ______; tool policy ______; identity/exchange ______; approval ______; audit/incident operations ______.
- Before production, identify work for managed identity and key rotation, distributed budget state, availability, audit retention, trace completeness and protocol conformance.

If stalled, timebox to two minutes. Export evidence, select the original run and reconcile. Ask the facilitator for the completed checkpoint; do not invent a successful result when a service or trace is unavailable.
