from dataclasses import dataclass
from datetime import timedelta
from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from src.worker.activities import (
        read_dispute_ticket,
        diagnose_and_propose_resolution,
        execute_settlement_and_notify
    )

@dataclass
class DisputeInput:
    case_id: str
    customer_id: str = ""
    override_amount: int = 0

@dataclass
class ApprovalSignal:
    approved: bool
    reviewer: str
    comments: str = ""

@workflow.defn
class DisputeResolutionWorkflow:
    def __init__(self):
        self.approval_decision: dict | None = None
        self.current_phase: str = "INITIALIZED"
        self.proposal: dict | None = None
        self.execution_result: dict | None = None

    @workflow.signal
    def human_approval(self, decision: dict):
        self.approval_decision = decision

    @workflow.query
    def get_status(self) -> dict:
        return {
            "current_phase": self.current_phase,
            "proposal": self.proposal,
            "approval_decision": self.approval_decision,
            "execution_result": self.execution_result
        }

    @workflow.run
    async def run(self, dispute_input: DisputeInput) -> dict:
        self.current_phase = "READING_TICKET"
        case_data = await workflow.execute_activity(
            read_dispute_ticket,
            dispute_input.case_id,
            start_to_close_timeout=timedelta(seconds=15)
        )

        self.current_phase = "REASONING_DIAGNOSIS"
        self.proposal = await workflow.execute_activity(
            diagnose_and_propose_resolution,
            case_data,
            start_to_close_timeout=timedelta(seconds=30)
        )

        # Check if human approval is required
        if self.proposal["requires_approval"]:
            self.current_phase = "WAITING_FOR_APPROVAL"
            # Wait for signal up to 24 hours
            await workflow.wait_condition(
                lambda: self.approval_decision is not None,
                timeout=timedelta(hours=24)
            )

            is_approved = self.approval_decision.get("approved", False)
        else:
            is_approved = True
            self.approval_decision = {
                "approved": True,
                "reviewer": "system-auto-approval",
                "comments": "Below human review threshold (<= INR 500)"
            }

        self.current_phase = "EXECUTING_SETTLEMENT"
        settlement_payload = {
            "case_id": dispute_input.case_id,
            "amount": self.proposal["amount"],
            "destination_account": self.proposal["destination_account"],
            "approved": is_approved,
            "reviewer_comments": self.approval_decision.get("comments", "")
        }

        self.execution_result = await workflow.execute_activity(
            execute_settlement_and_notify,
            settlement_payload,
            start_to_close_timeout=timedelta(seconds=30)
        )

        self.current_phase = "COMPLETED"
        return {
            "case_id": dispute_input.case_id,
            "phase": self.current_phase,
            "proposal": self.proposal,
            "approval": self.approval_decision,
            "result": self.execution_result
        }
