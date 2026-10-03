# Workshop 3 Answer Key & Facilitator Guide

## 📋 Verification & Rehearsal Commands
```bash
# Smoke test
./scripts/workshop verify w3

# Complete 45-minute simulated rehearsal
.venv/bin/python workshops/w3/rehearsal_w3.py
```

---

## 🔑 Architecture Highlights & Code Solutions

### 1. Invariant: Stable Workflow Identity & Duplicate Rejection
```python
# In src/worker/kafka_consumer.py:
workflow_id = f"dispute-case-{case_id}"

try:
    handle = await temporal_client.start_workflow(
        DisputeResolutionWorkflow.run,
        DisputeInput(case_id=case_id),
        id=workflow_id,
        task_queue="dispute-resolution-queue",
        id_reuse_policy=WorkflowIDReusePolicy.REJECT_DUPLICATE
    )
except WorkflowAlreadyStartedError:
    # Safe duplicate delivery handling: reuses the existing in-flight workflow
    pass

# Commit offset ONLY after workflow is acknowledged
await consumer.commit()
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
```python
# In src/worker/activities.py:
idempotency_key = f"settle-dispute-{case_id}"
pay_headers = {
    **headers,
    "Idempotency-Key": idempotency_key
}
pay_resp = await client.post(f"{api_url}/payments", json=payment_body, headers=pay_headers)
```

---

## 💡 Facilitator Notes
- **Why not just rely on Kafka?** Kafka provides at-least-once message delivery, not workflow state management. If an agent crashes midway through a 3-step decision, Kafka can redeliver the event, but without Temporal history and backend idempotency, steps 1 and 2 might execute twice!
- **Activity Separation Rule**: Model/tool I/O and HTTP network calls belong strictly in Temporal Activities, never in workflow definitions. Workflow code must be deterministic so Temporal can replay the event history safely.
- **Enterprise Resilience**: The durable wait demonstrated here operates for seconds in this rehearsal, but in production the exact same code supports 30-day human approval queues with zero server memory held open.
