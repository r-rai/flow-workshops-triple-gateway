# Workshop 4: The day the agent broke the bank

Implementing Triple-Gate Architecture & A2A Security for Autonomous AI Workloads

Duration: 135 minutes. Last slide is presenter reference outside the timed agenda.

Expected outcomes in these slides are instructional targets, not fresh execution results.

## 01. The day the agent broke the bank

**Timing:** 0–8 min

Open http://localhost:9080/workshop-4?view=presenter. Say: the credentials were valid, the request passed schema validation, and the fictional bank still lost ₹90 lakh. What did we authorize? Withhold the ticket until the next chapter. Declare that the incident is a recorded proposal executed in an isolated local ledger.

Sources: [workshop-4-story.md](../../../docs/workshops/workshop-4-story.md), [worksheet.md](../../../workshops/w4/worksheet.md), [answer-key.md](../../../workshops/w4/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md)

## 02. ₹90 lakh

**Timing:** 0–8 min

Collect predictions: identity, model, tool policy or approval? Record local votes without a polling service. The visible success status and credential validity establish neither transaction legitimacy nor correct delegation. No live model compromise is being asserted.

Sources: [workshop-4-story.md](../../../docs/workshops/workshop-4-story.md), [worksheet.md](../../../workshops/w4/worksheet.md), [answer-key.md](../../../workshops/w4/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md)

## 03. Your assignment: repair and prove the bank still works

**Timing:** 0–8 min

Use one prepared local instance per pair. Shared hosting is observation/fallback only. Give each pair one task and one evidence artifact at a time; keep explanation blocks under seven minutes.

Sources: [workshop-4-story.md](../../../docs/workshops/workshop-4-story.md), [worksheet.md](../../../workshops/w4/worksheet.md), [answer-key.md](../../../workshops/w4/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md)

## 04. The incident-response clock / first half

**Timing:** 0–8 min

Keep the opening tight. The seven-minute break is included in the full 135 minutes. Completed local checkpoints are available for stalled pairs.

Sources: [workshop-4-story.md](../../../docs/workshops/workshop-4-story.md), [worksheet.md](../../../workshops/w4/worksheet.md), [answer-key.md](../../../workshops/w4/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md)

## 05. The incident-response clock / second half

**Timing:** 0–8 min

Create approval proposals immediately before review: they expire after ten minutes. Leave enough time for legitimate settlement and evidence reconstruction. A blocked attack suite alone is insufficient to prove the repaired business path.

Sources: [workshop-4-story.md](../../../docs/workshops/workshop-4-story.md), [worksheet.md](../../../workshops/w4/worksheet.md), [answer-key.md](../../../workshops/w4/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md)

## 06. Follow the money across the handoff

**Timing:** 8–20 min

Reveal the ticket, recorded proposal and handoff. Ask which checks are missing at each boundary. The console replays fixed server-owned scenarios; the prediction/view controls do not enforce policy.

Sources: [workshop-4-story.md](../../../docs/workshops/workshop-4-story.md), [worksheet.md](../../../workshops/w4/worksheet.md), [answer-key.md](../../../workshops/w4/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md)

## 07. Replay one incident; inspect two ledgers

**Timing:** 8–20 min

The isolated sandbox is a presenter-only service with a separate disposable ledger and no protected volumes or provider/banking keys. Starting w4 alone does not enable it; follow the answer-key setup before delivery. Do not expose secrets in slides or exports.

Sources: [workshop-4-story.md](../../../docs/workshops/workshop-4-story.md), [worksheet.md](../../../workshops/w4/worksheet.md), [answer-key.md](../../../workshops/w4/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md)

## 08. The Triple-Gate model

**Timing:** 20–33 min

These are logical responsibilities in the lab, sharing APISIX infrastructure. No single boundary owns every failure. Prompt refusal cannot establish that direct tool or API calls are controlled.

Sources: [workshop-4-story.md](../../../docs/workshops/workshop-4-story.md), [worksheet.md](../../../workshops/w4/worksheet.md), [answer-key.md](../../../workshops/w4/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md)

## 09. Gate 1: stop dispatch when the budget is exhausted

**Timing:** 20–33 min

Show zero dispatch evidence for the budget scenario. Optional live comparison makes one bounded call and executes no tools. Report the actual response, refusal or live_failed outcome without relabelling a recorded result.

Sources: [workshop-4-story.md](../../../docs/workshops/workshop-4-story.md), [worksheet.md](../../../workshops/w4/worksheet.md), [answer-key.md](../../../workshops/w4/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md)

## 10. Gate 2: isolate the reason for denial

**Timing:** 33–53 min

Use the low amount for the prohibited-beneficiary test and a permitted beneficiary for the amount test. Conflating both would hide which rule stopped the request. Interpret the actual MCP decision rather than only the outer transport status.

Sources: [workshop-4-story.md](../../../docs/workshops/workshop-4-story.md), [worksheet.md](../../../workshops/w4/worksheet.md), [answer-key.md](../../../workshops/w4/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md)

## 11. Exercise: repair the prepared local policy

**Timing:** 33–53 min

Run prohibited beneficiary, excessive amount and permitted payment before the edit. Remove only vendor-alpha; retain attacker block and transfer ceiling. Repeating the success scenario creates payments; reconcile uncertain responses under the original run ID.

```bash
cp workshops/w4/checkpoints/initial/policy.rego \
  spikes/spike3_opa/policy.rego
docker compose restart opa

# Remove only vendor-alpha from the prepared prohibited list.
# Keep fraud-account-66 blocked, restart OPA, then retest.
```

Sources: [workshop-4-story.md](../../../docs/workshops/workshop-4-story.md), [worksheet.md](../../../workshops/w4/worksheet.md), [answer-key.md](../../../workshops/w4/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md)

## 12. Retest the repair against both attack and business paths

**Timing:** 33–53 min

Collect actual denied and allowed responses, balance deltas and payment count. This is a running-policy change, not a UI toggle. If stalled, allow two minutes before supplying the completed checkpoint.

```bash
# Completed checkpoint if a pair needs recovery:
cp workshops/w4/checkpoints/completed/policy.rego \
  spikes/spike3_opa/policy.rego
docker compose restart opa
```

Sources: [workshop-4-story.md](../../../docs/workshops/workshop-4-story.md), [worksheet.md](../../../workshops/w4/worksheet.md), [answer-key.md](../../../workshops/w4/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md)

## 13. Gate 3: the attacker changes routes

**Timing:** 53–60 min

Ask what would happen if the API accepted every validly signed token regardless of audience. Then inspect the actual responses. A Gate 2 denial does not prove the direct API path is protected; test it independently.

Sources: [workshop-4-story.md](../../../docs/workshops/workshop-4-story.md), [worksheet.md](../../../workshops/w4/worksheet.md), [answer-key.md](../../../workshops/w4/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md)

## 14. Break / checkpoint recovery

**Timing:** 60–67 min

Pause for the scheduled break. Restore completed policy/identity files where needed, restart OPA and refresh readiness. Export interrupted evidence first. Do not reset protected ledger state to hide an uncertain payment result.

Sources: [workshop-4-story.md](../../../docs/workshops/workshop-4-story.md), [worksheet.md](../../../workshops/w4/worksheet.md), [answer-key.md](../../../workshops/w4/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md)

## 15. Identity must narrow at the next boundary

**Timing:** 67–85 min

The lab demonstrates a constrained token-exchange pattern. Show sanitized claims rather than bearer credentials. Managed identity, key rotation and broader protocol conformance remain production work.

Sources: [workshop-4-story.md](../../../docs/workshops/workshop-4-story.md), [worksheet.md](../../../workshops/w4/worksheet.md), [answer-key.md](../../../workshops/w4/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md)

## 16. Exercise: request only an entitled scope

**Timing:** 67–85 min

The full edit path is workshops/w4/checkpoints/initial/identity.json. Change only requested_scope. The CLI writes sanitized timestamped evidence under workshops/w4/evidence. It mints lab credentials locally and does not load .env automatically: export matching JWT settings if the stack overrides defaults, using the answer-key instructions.

```bash
.venv/bin/python workshops/w4/exercise_exchange.py initial

# In checkpoints/initial/identity.json, change requested_scope
# from api:payments:write to api:accounts:read, then rerun.

.venv/bin/python workshops/w4/exercise_exchange.py completed
```

Sources: [workshop-4-story.md](../../../docs/workshops/workshop-4-story.md), [worksheet.md](../../../workshops/w4/worksheet.md), [answer-key.md](../../../workshops/w4/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md)

## 17. Explain the identity evidence

**Timing:** 67–85 min

Have each pair explain one denied and one permitted identity request. View selection cannot grant authority. A successful token exchange does not by itself prove a subsequent payment is authorized.

Sources: [workshop-4-story.md](../../../docs/workshops/workshop-4-story.md), [worksheet.md](../../../workshops/w4/worksheet.md), [answer-key.md](../../../workshops/w4/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md)

## 18. Approval attaches to one exact transaction

**Timing:** 85–103 min

Proposals expire after ten minutes. Read the actual proposal and task identifiers. Independent review should approve exact server-owned arguments; changed arguments must fail. W4's password-backed lab reviewer flow is not a claim of production IAM.

Sources: [workshop-4-story.md](../../../docs/workshops/workshop-4-story.md), [worksheet.md](../../../workshops/w4/worksheet.md), [answer-key.md](../../../workshops/w4/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md)

## 19. Use an independent reviewer session

**Timing:** 85–103 min

The facilitator configures and privately provides the reviewer password to the cofacilitator. The requester cannot approve its own proposal even with a reviewer cookie in its browser. Never paste the password into slides or evidence. Inspect the current proposal immediately before approval.

Sources: [workshop-4-story.md](../../../docs/workshops/workshop-4-story.md), [worksheet.md](../../../workshops/w4/worksheet.md), [answer-key.md](../../../workshops/w4/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md)

## 20. Attempt self approval and transaction tampering

**Timing:** 85–103 min

The console approval path executes the server-owned exact arguments, tests tampering and retry, and binds the payment to the task. Use the actual evidence order shown by the run; these rows describe the controls, not a manual command sequence.

Sources: [workshop-4-story.md](../../../docs/workshops/workshop-4-story.md), [worksheet.md](../../../workshops/w4/worksheet.md), [answer-key.md](../../../workshops/w4/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md)

## 21. One effect survives a retry

**Timing:** 85–103 min

Use Reconcile uncertain result after a lost response or process restart. Proposal status and keyed payments determine the result. Never invent a fresh run or financial key to retry an uncertain payment. If the API cannot be read, keep the result unresolved.

Sources: [workshop-4-story.md](../../../docs/workshops/workshop-4-story.md), [worksheet.md](../../../workshops/w4/worksheet.md), [answer-key.md](../../../workshops/w4/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md)

## 22. A second agent creates a second boundary

**Timing:** 103–119 min

The repository implements selected A2A controls; this is not a demonstration of complete A2A protocol conformance. Have pairs identify which principal may perform each operation before running the scenarios.

Sources: [workshop-4-story.md](../../../docs/workshops/workshop-4-story.md), [worksheet.md](../../../workshops/w4/worksheet.md), [answer-key.md](../../../workshops/w4/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md)

## 23. Test access to the delegated task

**Timing:** 103–119 min

Only task owner/designated executor can access the relevant task. Binding checks source, amount, currency, destination and optional proposal. Explain which principal made each tested request using sanitized evidence.

Sources: [workshop-4-story.md](../../../docs/workshops/workshop-4-story.md), [worksheet.md](../../../workshops/w4/worksheet.md), [answer-key.md](../../../workshops/w4/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md)

## 24. Bind completion to a business fact

**Timing:** 103–119 min

Inspect task, proposal and payment records side by side. The final legitimate path is delegate → propose → independently approve → execute exact arguments → bind the actual payment to the task.

Sources: [workshop-4-story.md](../../../docs/workshops/workshop-4-story.md), [worksheet.md](../../../workshops/w4/worksheet.md), [answer-key.md](../../../workshops/w4/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md)

## 25. Prove the repaired system in both directions

**Timing:** 119–130 min

Run the attack suite and legitimate path on prepared state, or inspect the collected chapter evidence if time is short. The table lists expected outcomes, not fresh measurements. Do not conflate the separate ₹250 policy exercise with the ₹1,500 delegation payment.

Sources: [workshop-4-story.md](../../../docs/workshops/workshop-4-story.md), [worksheet.md](../../../workshops/w4/worksheet.md), [answer-key.md](../../../workshops/w4/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md)

## 26. Reconstruct the incident from familiar records

**Timing:** 119–130 min

Evidence sheet: workshops/w4/incident-evidence.md. Save sanitized caller, audience/scopes, arguments and boundary responses as well as business IDs. Null ledger observations are unresolved, not zero. A generated trace ID alone is not collector evidence. Aggregate deltas need an isolated run without concurrent external mutations.

Sources: [workshop-4-story.md](../../../docs/workshops/workshop-4-story.md), [worksheet.md](../../../workshops/w4/worksheet.md), [answer-key.md](../../../workshops/w4/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md)

## 27. Incident review: what did your first vote miss?

**Timing:** 130–135 min

Revisit initial votes. Identify work for key rotation, distributed budget state, availability, audit retention, trace completeness and protocol conformance. Technical rehearsal evidence does not establish a completed 135-minute human delivery rehearsal or production readiness.

Sources: [workshop-4-story.md](../../../docs/workshops/workshop-4-story.md), [worksheet.md](../../../workshops/w4/worksheet.md), [answer-key.md](../../../workshops/w4/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md)

## 28. Restore useful work under explicit authority

**Timing:** 130–135 min

Close the four-workshop arc. Ask participants to name one control they would add to an existing agent integration and the evidence they would require to show it works.

Sources: [workshop-4-story.md](../../../docs/workshops/workshop-4-story.md), [worksheet.md](../../../workshops/w4/worksheet.md), [answer-key.md](../../../workshops/w4/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md)

## 29. Presenter preparation & source guide

**Timing:** Reference / outside timed delivery

Do setup outside the timed workshop. See workshops/w4/answer-key.md for W4_REVIEWER_PASSWORD, W4_ENABLE_VULNERABLE, W4_SANDBOX_KEY, observation-only hosting and presenter sandbox startup. Do not put actual values in this deck. Technical runner: .venv/bin/python workshops/w4/rehearsal_w4.py --vulnerable --outage, only on the appropriately prepared stack. It creates fictional records and does not reset data. Human timing record: workshops/w4/delivery-rehearsal.md. Downloads/builds and profile switching happen before attendees arrive.

Sources: [workshop-4-story.md](../../../docs/workshops/workshop-4-story.md), [worksheet.md](../../../workshops/w4/worksheet.md), [answer-key.md](../../../workshops/w4/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md)
