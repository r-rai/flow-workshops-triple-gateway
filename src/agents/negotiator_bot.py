import httpx
from typing import Dict, Any
from src.core.security import create_jwt_token

class NegotiatorBot:
    """
    Customer negotiation agent.
    Authorized to read customer cases and delegate payment tasks to PaymentsAgent,
    but NOT authorized to directly execute payments or approve tasks.
    """
    def __init__(self, base_url: str = "http://127.0.0.1:9080", api_key: str = "gate3-secret-token"):
        self.base_url = base_url
        self.api_key = api_key
        self.agent_id = "negotiator-bot-agent"
        # Restricted scope: only cases and a2a tasks, no payments:write
        self.token = create_jwt_token(
            subject=self.agent_id,
            audience="novabank-api",
            scopes=["api:cases:read", "api:a2a:tasks"],
            role="agent"
        )

    def get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "X-API-Key": self.api_key
        }

    async def discover_payments_agent(self) -> Dict[str, Any]:
        """Discovers PaymentsAgent Agent Card via well-known RFC endpoint."""
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{self.base_url}/.well-known/agent.json", headers=self.get_headers())
            if resp.status_code != 200:
                # Fallback to direct api route
                resp = await client.get(f"{self.base_url}/api/v1/a2a/card", headers=self.get_headers())
            return resp.json()

    async def delegate_payment_task(self, case_id: str, amount: int, destination_account: str) -> Dict[str, Any]:
        """Submits an A2A task delegation to PaymentsAgent."""
        payload = {
            "task_type": "propose_payment",
            "input": {
                "case_id": case_id,
                "amount": amount,
                "destination_account": destination_account,
                "currency": "INR",
                "reason": "Negotiated settlement for customer dispute"
            }
        }
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(f"{self.base_url}/api/v1/a2a/tasks", json=payload, headers=self.get_headers())
            if resp.status_code not in (200, 201):
                raise RuntimeError(f"Failed to delegate task: {resp.status_code} {resp.text}")
            return resp.json()

    async def query_task(self, task_id: str) -> Dict[str, Any]:
        """Queries status of own delegated task."""
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{self.base_url}/api/v1/a2a/tasks/{task_id}", headers=self.get_headers())
            if resp.status_code != 200:
                raise RuntimeError(f"Failed to query task {task_id}: {resp.status_code} {resp.text}")
            return resp.json()
