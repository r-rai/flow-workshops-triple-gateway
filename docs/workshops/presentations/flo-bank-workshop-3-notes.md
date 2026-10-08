# Workshop 3: The resolver that remembered

Architecting the Agentic Enterprise: Middleware, Durable State, and Event-Driven AI

Duration: 45 minutes. Last slide is presenter reference outside the timed agenda.

Expected outcomes in these slides are instructional targets, not fresh execution results.

## 01. The resolver that remembered

**Timing:** 0–6 min

Ask what happens when the customer closes the chat, the reviewer returns tomorrow or the worker crashes. Flo Bank's Autonomous System Resolver is implemented as a customer-dispute resolver. Introduce case-501 and declare live or replay mode.

Sources: [workshop-3-story.md](../../../docs/workshops/workshop-3-story.md), [worksheet.md](../../../workshops/w3/worksheet.md), [answer-key.md](../../../workshops/w3/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md)

## 02. The 45-minute route

**Timing:** 0–6 min

Have terminal queries, worker logs and business evidence open. Use fresh prepared W3 state. A previously completed case-501 workflow is deliberately not started again, and a banking reset alone does not clear Temporal history.

Sources: [workshop-3-story.md](../../../docs/workshops/workshop-3-story.md), [worksheet.md](../../../workshops/w3/worksheet.md), [answer-key.md](../../../workshops/w3/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md)

## 03. The customer leaves. The work continues.

**Timing:** 0–6 min

Do not describe the seeded ticket as a verified duplicate debit. Ask where the case, proposal, approval and payment should live. Collect failure predictions: lost progress, repeated investigation, missing approval or double payment.

Sources: [workshop-3-story.md](../../../docs/workshops/workshop-3-story.md), [worksheet.md](../../../workshops/w3/worksheet.md), [answer-key.md](../../../workshops/w3/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md)

## 04. Declare how the investigation is running

**Timing:** 0–6 min

Set USE_REPLAY_FIXTURES=true before preparing the stack for the deterministic fixture. Live mode may produce different arguments or fail investigation. The fixture's ₹750 is not a calculated refund for the ticket's claimed charge. MiniMax is the documented default; optional participant-provider setup is in the infrastructure/OpenRouter guides.

Sources: [workshop-3-story.md](../../../docs/workshops/workshop-3-story.md), [worksheet.md](../../../workshops/w3/worksheet.md), [answer-key.md](../../../workshops/w3/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md)

## 05. Give every kind of state an owner

**Timing:** 6–13 min

Temporal replays completed activity results. A failed investigation activity may repeat model inference and read tools. This lab does not checkpoint every unfinished LangGraph step.

Sources: [workshop-3-story.md](../../../docs/workshops/workshop-3-story.md), [worksheet.md](../../../workshops/w3/worksheet.md), [answer-key.md](../../../workshops/w3/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md)

## 06. Trace the durable business process

**Timing:** 6–13 min

During investigation, model inference goes through Gate 1 and allowed MCP reads through Gate 2 and Gate 3. The workflow owns the subsequent approval wait and settlement activity. Explain why arbitrary model responses cannot be replayed as deterministic workflow code.

Sources: [workshop-3-story.md](../../../docs/workshops/workshop-3-story.md), [worksheet.md](../../../workshops/w3/worksheet.md), [answer-key.md](../../../workshops/w3/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md)

## 07. Stable identity closes two duplicate windows

**Timing:** 6–13 min

General workflow format: dispute-case-{case_id}. Explain that stable workflow identity and banking idempotency address different failure windows. Do not claim exactly-once event delivery or inference.

Sources: [workshop-3-story.md](../../../docs/workshops/workshop-3-story.md), [worksheet.md](../../../workshops/w3/worksheet.md), [answer-key.md](../../../workshops/w3/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md)

## 08. Investigation has a bounded tool loop

**Timing:** 13–23 min

Allowed initial tools include get_case and get_account. In live mode inspect at least one actual model-selected read. Server rules validate amount, currency and destination and decide whether approval is required; the model cannot grant itself permission.

Sources: [workshop-3-story.md](../../../docs/workshops/workshop-3-story.md), [worksheet.md](../../../workshops/w3/worksheet.md), [answer-key.md](../../../workshops/w3/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md)

## 09. Demo: deliver a case and inspect progress

**Timing:** 13–23 min

Run from the repository root on a prepared stack. The CLI defaults to Kafka localhost:9092 and Temporal localhost:7233. If using live mode, confirm provider and governed-tool evidence rather than promising a fixed proposal.

```bash
.venv/bin/python workshops/w3/client.py emit \
  --case-id case-501 --customer-id cust-8801

.venv/bin/python workshops/w3/client.py query --case-id case-501
```

Sources: [workshop-3-story.md](../../../docs/workshops/workshop-3-story.md), [worksheet.md](../../../workshops/w3/worksheet.md), [answer-key.md](../../../workshops/w3/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md)

## 10. The agent proposes, then the process pauses

**Timing:** 13–23 min

Ask whether the case is resolved yet and what evidence would establish that money moved. W3 resolver review rules are separate from W2's support-agent thresholds. Save this baseline before stopping anything.

Sources: [workshop-3-story.md](../../../docs/workshops/workshop-3-story.md), [worksheet.md](../../../workshops/w3/worksheet.md), [answer-key.md](../../../workshops/w3/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md)

## 11. Exercise: capture the pre-crash checkpoint

**Timing:** 23–35 min

Pairs should predict what survives and what could repeat. Leave Kafka, Temporal and banking persistence running. Stopping the worker alone during the wait is the timed exercise.

Sources: [workshop-3-story.md](../../../docs/workshops/workshop-3-story.md), [worksheet.md](../../../workshops/w3/worksheet.md), [answer-key.md](../../../workshops/w3/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md)

## 12. Demo: stop, redeliver, restart

**Timing:** 23–35 min

Wait for worker readiness after restart. Inspect duplicate-start handling in logs and the workflow history. Confirm the same pending proposal with zero settlement effects. Do not reset the banking or Temporal state during this exercise.

```bash
docker compose --profile w3 stop worker

.venv/bin/python workshops/w3/client.py emit \
  --case-id case-501 --customer-id cust-8801

docker compose --profile w3 start worker
.venv/bin/python workshops/w3/client.py query --case-id case-501
```

Sources: [workshop-3-story.md](../../../docs/workshops/workshop-3-story.md), [worksheet.md](../../../workshops/w3/worksheet.md), [answer-key.md](../../../workshops/w3/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md)

## 13. Recovery preserves recorded progress

**Timing:** 23–35 min

The current exercise stops at the durable approval wait. It does not itself test a response lost after a payment commits. Explain that separate failure window and the role of the stable payment key without claiming it was observed here.

Sources: [workshop-3-story.md](../../../docs/workshops/workshop-3-story.md), [worksheet.md](../../../workshops/w3/worksheet.md), [answer-key.md](../../../workshops/w3/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md)

## 14. Review the recovered proposal, then approve

**Timing:** 35–41 min

Read the actual proposal before sending the decision. The CLI's reviewer label is a lab decision signal; production approval needs authenticated and authorized reviewers bound to the exact proposal. Inspect the resulting payment rather than trusting only the workflow's final text.

```bash
.venv/bin/python workshops/w3/client.py approve \
  --case-id case-501 --reviewer ops-lead \
  --comments "Reviewed case evidence and validated proposal"

.venv/bin/python workshops/w3/client.py query --case-id case-501
```

Sources: [workshop-3-story.md](../../../docs/workshops/workshop-3-story.md), [worksheet.md](../../../workshops/w3/worksheet.md), [answer-key.md](../../../workshops/w3/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md)

## 15. Prove one approved settlement

**Timing:** 35–41 min

Use actual ledger records and the stable key. A separate rejection run should close with no payment. The optional case-502 replay has a missing-account tool error: show that error if used; it is not evidence of a fully successful investigation.

Sources: [workshop-3-story.md](../../../docs/workshops/workshop-3-story.md), [worksheet.md](../../../workshops/w3/worksheet.md), [answer-key.md](../../../workshops/w3/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md)

## 16. Three distinct failure windows

**Timing:** 41–45 min

Ask participants which state owner closes each window. Completed activity results replay from history; unfinished activity work can repeat. A brief crash demonstration does not experimentally prove weeks of availability.

Sources: [workshop-3-story.md](../../../docs/workshops/workshop-3-story.md), [worksheet.md](../../../workshops/w3/worksheet.md), [answer-key.md](../../../workshops/w3/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md)

## 17. From a demo pause to a longer process

**Timing:** 41–45 min

Do not describe the lab as a production multi-agent deployment or claim unfinished LangGraph steps are checkpointed. Invite participants to name a process in their organization that outlasts a request/response session.

Sources: [workshop-3-story.md](../../../docs/workshops/workshop-3-story.md), [worksheet.md](../../../workshops/w3/worksheet.md), [answer-key.md](../../../workshops/w3/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md)

## 18. Progress survives. Authority stays explicit.

**Timing:** 41–45 min

Return to the opening failure predictions. Have pairs explain where the proposal lived during the worker outage and how the bank avoided a duplicate business effect. Bridge to deliberate boundary testing and delegation.

Sources: [workshop-3-story.md](../../../docs/workshops/workshop-3-story.md), [worksheet.md](../../../workshops/w3/worksheet.md), [answer-key.md](../../../workshops/w3/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md)

## 19. Presenter preparation & source guide

**Timing:** Reference / outside timed delivery

Setup: ./scripts/workshop pull w3; ./scripts/workshop switch w3; ./scripts/workshop verify w3. Automated rehearsal: .venv/bin/python workshops/w3/rehearsal_w3.py. It deletes local Temporal SQLite history and resets seeded banking data; never run casually during the manual exercise. Evidence: workshops/w3/evidence/rehearsal-evidence.json. See the worksheet and participant infrastructure guide for complete preparation.

Sources: [workshop-3-story.md](../../../docs/workshops/workshop-3-story.md), [worksheet.md](../../../workshops/w3/worksheet.md), [answer-key.md](../../../workshops/w3/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md)
