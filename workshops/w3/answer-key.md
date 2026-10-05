# Workshop 3 Answer Key & Facilitator Guide

Complete the [workshop Python setup](../../docs/workshops/participant-infra-guide.md#step-23-set-up-python-virtual-environment-for-workshop-clients-verification--tests)
and follow the [worksheet readiness steps](worksheet.md#step-1-environment-readiness)
first. Preserve evidence before rehearsal; bank reset alone does not remove a
completed Temporal workflow.

## 📋 Verification & Rehearsal Commands
```bash
# Smoke test
./scripts/workshop verify w3

# Technical rehearsal: resets bank data and clears local Temporal history
.venv/bin/python workshops/w3/rehearsal_w3.py
```

---

## 🔑 Architecture Highlights & Code Solutions

### 1. Invariant: Stable Workflow Identity & Duplicate Rejection

The ID format is `dispute-case-{case_id}`: `case-501` therefore becomes
`dispute-case-case-501`. Failed runs may be restarted by redelivery; running or
completed successful runs are recognized without starting another workflow.
This excerpt simplifies the consumer’s retry loop.

```python
# In src/worker/kafka_consumer.py:
workflow_id = f"dispute-case-{case_id}"

try:
    handle = await temporal_client.start_workflow(
        DisputeResolutionWorkflow.run,
        DisputeInput(case_id=case_id),
        id=workflow_id,
        task_queue="dispute-resolution-queue",
        id_reuse_policy=WorkflowIDReusePolicy.ALLOW_DUPLICATE_FAILED_ONLY
    )
except WorkflowAlreadyStartedError:
    # Safe duplicate delivery handling: recognizes the existing workflow
    pass

# Simplified excerpt: tp identifies the consumed topic/partition.
# Commit offset ONLY after workflow is acknowledged
await consumer.commit({tp: msg.offset + 1})
```

### 2. Durable Wait for Human Approval
```python
# In src/worker/workflow.py:
@workflow.defn
class DisputeResolutionWorkflow:
    @workflow.signal
    def human_approval(self, decision: dict):
        self.approval_decision = decision

    @workflow.run
    async def run(self, dispute_input: DisputeInput) -> dict:
        # ... reasoning activity ...
        if self.proposal["requires_approval"]:
            self.current_phase = "WAITING_FOR_APPROVAL"
            await workflow.wait_condition(
                lambda: self.approval_decision is not None,
                timeout=timedelta(hours=24)
            )
```

### 3. Backend Idempotency Binding

`execute_settlement_and_notify` in `src/worker/activities.py` sends the settlement
through APISIX Gate 3 with `Idempotency-Key: settle-dispute-{case_id}`. For
`case-501`, the key is `settle-dispute-case-501`. Payments above 100,000 paise
also pass Core Banking's proposal/approval flow before payment execution.
The worksheet's replay compensation is 75,000 paise (₹750).

---

## 💡 Facilitator Notes
- **Why not just rely on Kafka?** Kafka provides at-least-once message delivery, not workflow state management. If an agent crashes midway through a 3-step decision, Kafka can redeliver the event, but without Temporal history and backend idempotency, steps 1 and 2 might execute twice!
- **Activity Separation Rule**: Model/tool I/O and HTTP network calls belong strictly in Temporal Activities, never in workflow definitions. Workflow code must be deterministic so Temporal can replay the event history safely.
- **Enterprise Resilience**: The workflow waits durably rather than holding an HTTP request open. This implementation sets a 24-hour approval timeout; a 30-day queue requires changing that timeout and defining expiry handling.

## Replay evidence caveats from the 2026-10-05 rehearsal

The `case-501` fixture says “Verified duplicate debit”, but the actual case
reports an unapproved charge and `get_account` returns a balance, not transaction
proof. Present that rationale as recorded model text; it does not establish a
double charge or refund entitlement. The reviewer comments in the automated
runner are also synthetic labels, not additional evidence.

The optional `case-502` rejection fixture requests `acc-8802`, which is absent
from the seed and returns 404. The graph records that tool error and still
returns a fixture proposal for mandatory review. The measured result is a
rejected/closed case with zero payments; it does not prove a fully successful
investigation or approval of that unsafe proposal. Show the error if using this
alternate ending. Replay and live diagnosis must remain clearly labelled.
