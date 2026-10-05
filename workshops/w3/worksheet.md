# Workshop 3 Worksheet: Architecting the Agentic Enterprise: Middleware, Durable State, and Event-Driven AI

Before running Python commands or the Bash launcher, complete the [workshop Python setup](../../docs/workshops/participant-infra-guide.md#step-23-set-up-python-virtual-environment-for-workshop-clients-verification--tests) from the repository root. Use Bash on Linux/WSL for the launcher; macOS users can run Python clients and direct Docker Compose commands.

Presenter narrative: [The Resolver That Remembered](../../docs/workshops/workshop-3-story.md).

**Duration**: 45 Minutes  
**Profile**: `w3`  
**Focus**: Durable workflow execution, event-driven AI with Apache Kafka, Temporal durable execution, and zero-duplicate financial side effects across system crashes.

---

## 🎯 Objectives
1. Understand the state ownership boundary between Event Broker (Kafka), Durable Orchestrator (Temporal), and Reasoning Engine (LangGraph).
2. Establish stable workflow identities (`dispute-case-{case_id}`) and understand offset commit ordering.
3. Observe how AI agent decisions pause durably for human sign-off without holding synchronous connections open.
4. Execute a simulated worker crash and duplicate event redelivery; prove that zero duplicate financial payments occur.
5. Inspect the recovered Temporal event history and business audit trail.

---

## ⏱️ Session Roadmap

| Segment | Timing | Activity | Artifacts |
|---|---|---|---|
| **1. Autonomous Resolver** | 00:00–00:06 | Review the customer’s disputed-charge ticket `case-501` | Dispute API `/cases/case-501` |
| **2. State Ownership** | 00:06–00:13 | Architecture of Kafka (at-least-once) + Temporal (state history) + Idempotency | Architecture diagram |
| **3. End-to-End Demo** | 00:13–00:23 | Emit event to Kafka; worker diagnoses refund and pauses in `WAITING_FOR_APPROVAL` | `workshops/w3/client.py` |
| **4. Guided Recovery Exercise** | 00:23–00:35 | Kill worker container, redeliver duplicate Kafka event, restart worker; observe recovery | Docker stop/start |
| **5. Approve and Inspect** | 00:35–00:41 | Send human approval signal; verify settlement payment and idempotency | Temporal UI / API audit |
| **6. Review & Wrap-up** | 00:41–00:45 | Explain the 24-hour lab timeout and what longer waits require | Rehearsal evidence |

---

## 🛠️ Step-by-Step Instructions

### Step 1: Environment Readiness
Before startup, set `USE_REPLAY_FIXTURES=true` in the repository-root `.env`
for the reproducible ₹750 proposal below. Live inference can produce a different
proposal or an investigation failure. Build current images, then start W3:

```bash
./scripts/workshop pull w3
```

Ensure profile `w3` is active and healthy:
```bash
./scripts/workshop switch w3
./scripts/workshop status
./scripts/workshop verify w3
```

Run the exercise on a fresh local lab. A previous completed `case-501` workflow
is deliberately not started again; resetting bank data alone does not clear
Temporal history. Preserve evidence from earlier runs before using the automated
rehearsal, which resets both bank data and Temporal history.

The CLI defaults to Kafka `localhost:9092` and Temporal `localhost:7233`. If you
changed the Temporal host port, pass `--temporal localhost:<port>` to query and
approval commands. Kafka host-port changes also require matching advertised
listener configuration; changing only `KAFKA_PORT` is insufficient.

### Step 2: Emit Dispute to Kafka
Use the workshop client to emit a customer dispute event to Kafka:
```bash
.venv/bin/python workshops/w3/client.py emit --case-id case-501 --customer-id cust-8801
```

### Step 3: Query Workflow State
Inspect the Temporal workflow state:
```bash
.venv/bin/python workshops/w3/client.py query --case-id case-501
```
Query again while the worker processes the event. Inspect `current_phase` and
`proposal` in the response.

**Verify**: The workflow is paused in `WAITING_FOR_APPROVAL` with proposed compensation `75000` (INR 750.00). This is a replay fixture, not a calculated refund for the ticket's claimed 45000 INR charge. Inspect graph/tool results and keep the model's rationale separate from verified case facts.

### Step 4: Simulate Worker Crash & Duplicate Redelivery
In another terminal, stop the worker:
```bash
docker compose --profile w3 stop worker
```
Now redeliver the exact same dispute event:
```bash
.venv/bin/python workshops/w3/client.py emit --case-id case-501 --customer-id cust-8801
```
Restart the worker:
```bash
docker compose --profile w3 start worker
```
Query the workflow again:
```bash
.venv/bin/python workshops/w3/client.py query --case-id case-501
```
**Verify**: Workflow state is fully intact in `WAITING_FOR_APPROVAL`. Check that the workflow ID is still `dispute-case-case-501`; after approval,
inspect the settlement evidence to confirm one payment.

### Step 5: Deliver Human Approval Signal
Deliver the sign-off:
```bash
.venv/bin/python workshops/w3/client.py approve --case-id case-501 --reviewer ops-lead --comments "Reviewed case evidence and validated proposal"
```
**Verify**: The workflow completes, creating exactly ONE payment in the Core Banking API with idempotency key `settle-dispute-case-501`, and marks `case-501` as `resolved`.

### Step 6: Automated Rehearsal
This technical rehearsal resets seeded banking data, stops Temporal and the
worker, and deletes the local lab Temporal SQLite history. It also runs the
rejection branch for `case-502`. Save earlier evidence first; run only on a
disposable local W3 lab, separate from the manual exercise. It is not a measured
45-minute delivery rehearsal.

Run the automated rehearsal:
```bash
.venv/bin/python workshops/w3/rehearsal_w3.py
```
Check evidence in `workshops/w3/evidence/rehearsal-evidence.json`.
