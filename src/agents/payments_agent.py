import os
import httpx
from typing import Dict, Any
from src.core.security import create_jwt_token

class PaymentsAgent:
    """
    Payments specialized execution agent.
    Authorized to propose payments and execute approved proposals.
    Forbidden from approving its own proposals (Anti-Self-Approval invariant).
    """
    def __init__(self, base_url: str = "http://127.0.0.1:9080", api_key: str = "gate3-secret-token"):
        self.base_url = base_url
        self.api_key = api_key
        self.agent_id = "payments-agent-executor"
        self.token = create_jwt_token(
            subject=self.agent_id,
            audience=os.getenv("API_AUDIENCE", "flobank-api"),
            scopes=["api:payments:write", "api:a2a:tasks"],
            role="agent"
        )

    def get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "X-API-Key": self.api_key
        }

    async def submit_proposal(self, account_id: str, beneficiary: str, amount: int, currency: str = "INR") -> Dict[str, Any]:
        """Creates a payment proposal requiring supervisory sign-off."""
        payload = {
            "account_id": account_id,
            "beneficiary": beneficiary,
            "amount": amount,
            "currency": currency,
        }
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(f"{self.base_url}/api/v1/payments/proposals", json=payload, headers=self.get_headers())
            if resp.status_code not in (200, 201):
                raise RuntimeError(f"Proposal submission failed: {resp.status_code} {resp.text}")
            return resp.json()

    async def attempt_self_approval(self, proposal_id: str) -> Dict[str, Any]:
        """Attempts to approve own proposal; MUST fail with 403 Forbidden."""
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(f"{self.base_url}/api/v1/approvals/{proposal_id}/approve", headers=self.get_headers())
            return {"status_code": resp.status_code, "body": resp.text}

    async def execute_approved_payment(self, account_id: str, beneficiary: str, amount: int, proposal_id: str, idempotency_key: str) -> Dict[str, Any]:
        """Executes payment using approved proposal ID."""
        payload = {
            "account_id": account_id,
            "beneficiary": beneficiary,
            "amount": amount,
            "currency": "INR",
            "proposal_id": proposal_id
        }
        headers = {
            **self.get_headers(),
            "Idempotency-Key": idempotency_key
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(f"{self.base_url}/api/v1/payments", json=payload, headers=headers)
            if resp.status_code not in (200, 201):
                raise RuntimeError(f"Payment execution failed: {resp.status_code} {resp.text}")
            return resp.json()

    async def dispatch_payment_task(self, task_id: str, proposal_id: str | None = None) -> Dict[str, Any]:
        """
        Executes an A2A delegated payment task:
        1. Reads task specifications from A2A API.
        2. Executes payment via Core Banking API.
        3. Completes task binding the validated settlement record.
        """
        async with httpx.AsyncClient(timeout=10.0) as client:
            t_res = await client.get(f"{self.base_url}/api/v1/a2a/tasks/{task_id}", headers=self.get_headers())
            if t_res.status_code != 200:
                raise RuntimeError(f"Failed to query task {task_id}: {t_res.status_code} {t_res.text}")
            task = t_res.json()
            task_input = task.get("input", {})

            amount = int(task_input.get("amount", 50000))
            destination = task_input.get("destination_account") or task_input.get("beneficiary") or "acc-101"
            source_acc = task_input.get("source_account") or task_input.get("account_id") or "acc-102"
            case_id = task_input.get("case_id", "case-501")

            idemp_key = f"settle-a2a-{task_id}"
            pay_payload = {
                "account_id": source_acc,
                "beneficiary": destination,
                "amount": amount,
                "currency": task_input.get("currency", "INR")
            }
            # Approval is obtained independently; the executor only references it.
            approved_proposal = proposal_id or task_input.get("proposal_id")
            if approved_proposal:
                pay_payload["proposal_id"] = approved_proposal
            p_res = await client.post(
                f"{self.base_url}/api/v1/payments",
                headers={**self.get_headers(), "Idempotency-Key": idemp_key},
                json=pay_payload
            )
            if p_res.status_code not in (200, 201):
                raise RuntimeError(f"Payment execution failed: {p_res.status_code} {p_res.text}")
            payment_record = p_res.json()

            comp_res = await client.post(
                f"{self.base_url}/api/v1/a2a/tasks/{task_id}/complete",
                headers=self.get_headers(),
                json={
                    "payment_id": payment_record["payment_id"],
                    "status": "SETTLED",
                    "amount": amount,
                    "destination_account": destination,
                    "case_id": case_id
                }
            )
            if comp_res.status_code != 200:
                raise RuntimeError(f"Failed to complete task: {comp_res.status_code} {comp_res.text}")
            return comp_res.json()
