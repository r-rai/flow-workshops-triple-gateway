import os
import httpx
from temporalio import activity
from src.core.security import create_jwt_token

@activity.defn
async def read_dispute_ticket(case_id: str) -> dict:
    gate3_url = os.getenv("GATE3_URL", os.getenv("API_URL", "http://apisix:9080/api/v1"))
    token = create_jwt_token(
        subject="system-workflow-engine",
        audience="novabank-api",
        scopes=["api:accounts:read", "api:cases:read", "api:cases:write", "api:payments:write"]
    )
    headers = {
        "Authorization": f"Bearer {token}",
        "X-API-Key": os.getenv("GATE3_API_KEY", "gate3-secret-token")
    }
    
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(f"{gate3_url}/cases/{case_id}", headers=headers)
        if resp.status_code != 200:
            raise RuntimeError(f"Failed to fetch case {case_id}: {resp.status_code} {resp.text}")
        return resp.json()


from src.worker.dispute_agent import run_dispute_investigation

@activity.defn
async def diagnose_and_propose_resolution(case_data: dict) -> dict:
    """Executes compiled LangGraph multi-step reasoning agent."""
    return await run_dispute_investigation(case_data)


@activity.defn
async def execute_settlement_and_notify(settlement_data: dict) -> dict:
    case_id = settlement_data["case_id"]
    approved = settlement_data.get("approved", False)
    amount = settlement_data["amount"]
    destination_account = settlement_data["destination_account"]
    
    gate3_url = os.getenv("GATE3_URL", os.getenv("API_URL", "http://apisix:9080/api/v1"))
    token = create_jwt_token(
        subject="system-workflow-engine",
        audience="novabank-api",
        scopes=["api:accounts:read", "api:cases:read", "api:cases:write", "api:payments:write"]
    )
    headers = {
        "Authorization": f"Bearer {token}",
        "X-API-Key": os.getenv("GATE3_API_KEY", "gate3-secret-token")
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        if approved and amount > 0:
            # 1. Execute financial settlement with stable idempotency key
            idempotency_key = f"settle-dispute-{case_id}"
            payment_body = {
                "account_id": "acc-102",
                "beneficiary": destination_account,
                "amount": amount,
                "currency": "INR",
            }
            pay_headers = {
                **headers,
                "Idempotency-Key": idempotency_key
            }
            pay_resp = await client.post(f"{gate3_url}/payments", json=payment_body, headers=pay_headers)
            if pay_resp.status_code not in (200, 201):
                raise RuntimeError(f"Payment execution failed: {pay_resp.status_code} {pay_resp.text}")
            payment_record = pay_resp.json()

            # 2. Update case status to resolved
            case_update = {
                "status": "resolved"
            }
            case_resp = await client.patch(f"{gate3_url}/cases/{case_id}", json=case_update, headers=headers)

            
            return {
                "case_id": case_id,
                "status": "RESOLVED",
                "payment": payment_record,
                "notification_sent": True
            }
        else:
            # Rejection branch
            case_update = {
                "status": "closed"
            }
            await client.patch(f"{gate3_url}/cases/{case_id}", json=case_update, headers=headers)
            return {
                "case_id": case_id,
                "status": "REJECTED",
                "notification_sent": True
            }
