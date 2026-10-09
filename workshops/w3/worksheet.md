# Workshop 3 Worksheet: Architecting the Agentic Enterprise: Middleware, Durable State, and Event-Driven AI

Before running Python commands or the Bash launcher, complete the [workshop Python setup](../../docs/workshops/participant-infra-guide.md#step-23-set-up-python-virtual-environment-for-workshop-clients-verification--tests) from the repository root. Use Bash on Linux/WSL for the launcher; macOS users can run Python clients and direct Docker Compose commands.

Presenter narrative: [The Resolver That Remembered](../../docs/workshops/workshop-3-story.md).

Visual reference: [W3 architecture, resolution, and crash-recovery diagrams](../../docs/workshops/diagrams/w3/README.md)
(editable Mermaid plus SVG/PNG).

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
| **5. Approve and Inspect** | 00:35–00:41 | Send human approval signal; verify settlement payment and idempotency | Workflow CLI / banking API evidence |
| **6. Review & Wrap-up** | 00:41–00:45 | Explain the 24-hour lab timeout and what longer waits require | Rehearsal evidence |

---

## 🛠️ Step-by-Step Instructions

### Step 1: Environment Readiness
Run all commands from the repository root in your Linux/WSL2 terminal. If you
finished W2, explicitly switch profiles: `verify w3` runs checks only and does
not start W3 services.

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

**Verify**: Status reports `Active Workshop Profile: w3`, with `worker`,
`temporal`, and `kafka` running. The smoke test checks incident retrieval,
requests incident remediation, and checks Temporal/Kafka connectivity; it does
not prove the investigation's tool calls
will succeed. Inspect those results in Step 3.

The worker must receive the same `JWT_ISSUER` and `API_AUDIENCE` as the API,
and the same `MCP_AUDIENCE` as the adapter. Current Compose passes these `.env`
settings to the worker, including custom NovaBank settings on older labs.

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

Expected phases are `READING_TICKET` → `REASONING_DIAGNOSIS` →
`WAITING_FOR_APPROVAL`. Both `get_case` and `get_account` in
`proposal.graph_metadata.tool_results` should report `SUCCESS`. Approval and
execution remain `null`. The fixture's duplicate-debit rationale is model text;
the case description and account balance do not establish a duplicate debit.
If the workflow stalls or reports `INVESTIGATION_FAILED`, use Troubleshooting
below before continuing.

### Step 4: Simulate Worker Crash & Duplicate Redelivery
Save the pending proposal before stopping the worker:

```bash
.venv/bin/python workshops/w3/client.py query --case-id case-501 | tee /tmp/w3-before-crash.txt
```

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
docker compose --profile w3 logs --tail=50 worker
```
**Verify**: Workflow state is fully intact in `WAITING_FOR_APPROVAL`. Check that the workflow ID is still `dispute-case-case-501`; after approval,
inspect the settlement evidence to confirm one payment.

Wait for the consumer to restart. Logs should show the duplicate event, reuse
of the existing workflow, and the Kafka offset committed afterward. Compare
the amount and destination with the saved proposal. This stop/start exercise
tests recovery during the approval wait; it does not test a crash during payment
commit or a lost settlement response.

### Step 5: Deliver Human Approval Signal
Deliver the sign-off:
```bash
.venv/bin/python workshops/w3/client.py approve --case-id case-501 --reviewer ops-lead --comments "Approved replay proposal for workshop demonstration"
.venv/bin/python workshops/w3/client.py query --case-id case-501
```
The approval command waits for the result. Expect `COMPLETED`, an approved
decision, and a settlement result containing a payment ID.

**Verify**: The workflow completes, creating exactly ONE payment in the Core Banking API with idempotency key `settle-dispute-case-501`, and marks `case-501` as `resolved`.

### Step 6: Verify the Banking Records

Use this read-only check to verify the business outcome independently of the
workflow result. The payments API requires `api:payments:write` even for its
GET endpoint; this command issues only GET requests.

```bash
docker compose --profile w3 exec -T worker python - <<'PY'
import os
import httpx
from src.core.security import create_jwt_token

token = create_jwt_token(
    subject="system-workflow-engine",
    audience=os.getenv("API_AUDIENCE", "flobank-api"),
    scopes=["api:cases:read", "api:payments:write"],
)
headers = {
    "Authorization": f"Bearer {token}",
    "X-API-Key": os.getenv("GATE3_API_KEY", "gate3-secret-token"),
}
base = os.environ["GATE3_URL"]
with httpx.Client(headers=headers, timeout=10) as client:
    case = client.get(f"{base}/cases/case-501")
    case.raise_for_status()
    payments = client.get(f"{base}/payments")
    payments.raise_for_status()
matches = [
    p for p in payments.json()
    if p.get("idempotency_key") == "settle-dispute-case-501"
]
print("Case status:", case.json()["status"])
print("Settlement payment count:", len(matches))
print("Settlement records:", matches)
assert case.json()["status"] == "resolved"
assert len(matches) == 1
assert matches[0]["amount"] == 75000
assert matches[0]["beneficiary"] == "acc-101"
assert matches[0]["status"] == "completed"
PY
```

Expected: `Case status: resolved`, `Settlement payment count: 1`, and a
completed ₹750 payment from `acc-102` to `acc-101`. Save the query, recovery
logs, and this banking evidence. The lab approval wait has a 24-hour timeout;
longer business processes require an explicit timeout design.

### Step 7: Optional Automated Rehearsal
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

## Available UIs

| Surface | Default local URL | Use in W3 |
|---|---|---|
| Banking application | http://localhost:9080 | Customer-facing banking demo; use CLI commands for this resolver exercise |
| Jaeger | http://localhost:16686 | Inspect exported traces; banking records remain the settlement evidence |
| Temporal UI | http://localhost:8233 | Inspect workflow history, activity inputs/results, signals, and queries |

There is no dedicated `/workshop-3` console. Temporal UI starts with W3 and W4;
port 7233 remains the Temporal API. On WSL2, open the browser URLs from Windows
while Docker is running in your WSL environment. Change the host UI port with
`TEMPORAL_UI_PORT` in `.env` (default 8233). Jaeger's port can be changed with
`JAEGER_UI_PORT`.

### Follow the Resolver in Temporal UI

For an existing W3 lab, update and start only the new UI without resetting data:

```bash
git pull --ff-only origin main
docker compose --profile w3 pull temporal-ui
docker compose --profile w3 up -d temporal-ui
```

1. Open http://localhost:8233 and select the `default` namespace.
2. Open **Workflows** and find `dispute-case-case-501`. If needed, filter with
   `WorkflowId = 'dispute-case-case-501'`.
3. Open its latest run and inspect **History**. Expand activity events to see
   `read_dispute_ticket` and `diagnose_and_propose_resolution`, including inputs,
   results, and any retries. The graph's tool evidence is in the diagnosis result;
   each LangGraph step is not a separate Temporal activity.
4. While approval is pending, Temporal reports the workflow as **Running**.
   Run the `get_status` workflow query in the UI to see the business phase
   `WAITING_FOR_APPROVAL` and the saved proposal. Queries need a running worker;
   recorded history remains available when the worker is stopped.
5. During Step 4, refresh after restarting the worker. Duplicate Kafka delivery
   should reuse the same workflow. Kafka offsets are visible in worker logs,
   not in Temporal history.
6. Approve using Step 5's CLI command. Refresh History to see the
   `human_approval` signal, settlement activity, and workflow completion.
   Continue to Step 6 to verify the payment count in banking records.

The UI is configured for inspection with write actions disabled; use the CLI
for approval and the guarded recovery command for a failed investigation.
Earlier failed runs remain visible after a reset, so select the latest run.
The standalone UI adds a 128 MiB memory limit to the profile.

If the page or workflow list fails to load:

```bash
docker compose --profile w3 ps temporal temporal-ui
docker compose --profile w3 logs --tail=50 temporal-ui temporal
```

`./scripts/workshop verify w3` checks the UI page, default namespace, and
workflow listing through the UI's backend. These checks also detect a UI that
loads HTML but cannot connect to Temporal.

## Troubleshooting

### Temporal port 7233 unreachable; status still says W2

Run `./scripts/workshop switch w3` first. If switching fails, inspect that
error before running verification again. Do not start multiple workshop
profiles together.

### Stuck in READING_TICKET or investigation tool reads denied

Inspect the worker:

```bash
docker compose --profile w3 ps -a worker
docker compose --profile w3 logs --tail=100 worker
docker compose --profile w3 exec -T api python -c 'from src.core.config import settings; print(settings.JWT_ISSUER)'
docker compose --profile w3 exec -T worker python -c 'from src.core.config import settings; print(settings.JWT_ISSUER)'
docker compose --profile w3 exec -T adapter printenv MCP_AUDIENCE
docker compose --profile w3 exec -T worker printenv MCP_AUDIENCE
```

`Invalid issuer` on the ticket GET indicates an issuer mismatch. Gate 2's
`UNAUTHENTICATED_CALLER: Invalid audience` indicates an MCP token audience
mismatch. Older Compose files omitted worker `JWT_ISSUER` and `MCP_AUDIENCE`.
Update the repository and recreate the worker so it receives the settings:

```bash
git pull --ff-only origin main
docker compose --profile w3 up -d --no-deps --force-recreate worker
```

Resolve local Git changes before pulling if Git reports a conflict. Verify
that the issuer pair and audience pair match. A pending ticket-read activity
can take roughly 100 seconds to retry after repeated failures.

### Recover a completed INVESTIGATION_FAILED lab run

An investigation failure completes the Temporal run with a business failure
result. Fixing configuration or sending the event again does not rerun that
completed workflow. After correcting the root cause, the following targeted
reset creates a new run of `dispute-case-case-501` from its first completed
workflow task. It preserves the original run history and banking data, and
reruns the investigation. Use only for this disposable lab's failed
investigation, before any settlement; do not use it to replay an approved case.

```bash
.venv/bin/python - <<'PY'
import asyncio
import uuid
from temporalio.client import Client
from temporalio.api.common.v1 import WorkflowExecution
from temporalio.api.enums.v1 import EventType
from temporalio.api.workflowservice.v1 import ResetWorkflowExecutionRequest

async def main():
    client = await Client.connect("localhost:7233")  # Adjust if TEMPORAL_PORT differs.
    handle = client.get_workflow_handle("dispute-case-case-501")
    description = await handle.describe()
    handle = client.get_workflow_handle(description.id, run_id=description.run_id)
    state = await handle.query("get_status")
    if state["current_phase"] != "INVESTIGATION_FAILED":
        raise RuntimeError("Stopped: workflow is not in INVESTIGATION_FAILED")
    history = await handle.fetch_history()
    checkpoint = next(
        event.event_id for event in history.events
        if event.event_type == EventType.EVENT_TYPE_WORKFLOW_TASK_COMPLETED
    )
    result = await client.workflow_service.reset_workflow_execution(
        ResetWorkflowExecutionRequest(
            namespace=client.namespace,
            workflow_execution=WorkflowExecution(
                workflow_id=description.id, run_id=description.run_id,
            ),
            workflow_task_finish_event_id=checkpoint,
            reason="Retry investigation after fixing worker JWT configuration",
            request_id=str(uuid.uuid4()),
        )
    )
    print("Reset started. New run ID:", result.run_id)

asyncio.run(main())
PY
```

Query again using Step 3. Continue to the recovery exercise only after the
workflow reaches `WAITING_FOR_APPROVAL` with successful tool-read evidence.
