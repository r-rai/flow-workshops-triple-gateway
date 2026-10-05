# Workshop 3 Worksheet: Architecting the Agentic Enterprise: Middleware, Durable State, and Event-Driven AI

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
| **1. Autonomous Resolver** | 00:00–00:06 | Review customer double charge dispute ticket `case-501` | Dispute API `/cases/case-501` |
| **2. State Ownership** | 00:06–00:13 | Architecture of Kafka (at-least-once) + Temporal (state history) + Idempotency | Architecture diagram |
| **3. End-to-End Demo** | 00:13–00:23 | Emit event to Kafka; worker diagnoses refund and pauses in `WAITING_FOR_APPROVAL` | `workshops/w3/client.py` |
| **4. Guided Recovery Exercise** | 00:23–00:35 | Kill worker container, redeliver duplicate Kafka event, restart worker; observe recovery | Docker stop/start |
| **5. Approve and Inspect** | 00:35–00:41 | Send human approval signal; verify settlement payment and idempotency | Temporal UI / API audit |
| **6. Review & Wrap-up** | 00:41–00:45 | Explain how durable wait scales from seconds to 30 days without resource exhaustion | Rehearsal evidence |

---

## 🛠️ Step-by-Step Instructions

### Step 1: Environment Readiness
Ensure profile `w3` is active and healthy:
```bash
./scripts/workshop switch w3
./scripts/workshop status
./scripts/workshop verify w3
```

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
**Verify**: The workflow is paused in `WAITING_FOR_APPROVAL` with proposed compensation `75000` (INR 750.00).

### Step 4: Simulate Worker Crash & Duplicate Redelivery
In another terminal, stop the worker:
```bash
docker stop flobank-workshops-worker-1
```
Now redeliver the exact same dispute event:
```bash
.venv/bin/python workshops/w3/client.py emit --case-id case-501 --customer-id cust-8801
```
Restart the worker:
```bash
docker start flobank-workshops-worker-1
```
Query the workflow again:
```bash
.venv/bin/python workshops/w3/client.py query --case-id case-501
```
**Verify**: Workflow state is fully intact in `WAITING_FOR_APPROVAL`. No duplicate execution or duplicate workflow occurred!

### Step 5: Deliver Human Approval Signal
Deliver the sign-off:
```bash
.venv/bin/python workshops/w3/client.py approve --case-id case-501 --reviewer ops-lead --comments "Verified double charge"
```
**Verify**: The workflow completes, creating exactly ONE payment in the Core Banking API with idempotency key `settle-dispute-case-501`, and marks `case-501` as `resolved`.

### Step 6: Automated Rehearsal
Run the complete 45-minute automated rehearsal:
```bash
.venv/bin/python workshops/w3/rehearsal_w3.py
```
Check evidence in `workshops/w3/evidence/rehearsal-evidence.json`.
