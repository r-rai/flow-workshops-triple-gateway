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
            audience="novabank-api",
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
