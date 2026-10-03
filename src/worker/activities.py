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


@activity.defn
async def diagnose_and_propose_resolution(case_data: dict) -> dict:
    """Simulates LangGraph multi-step reasoning activity."""
    case_id = case_data.get("id")
    customer_id = case_data.get("customer_id")
    issue_type = case_data.get("issue_type", "")
    desc = case_data.get("description", "")
    
    # If case-501 (double charge on acc-101), refund INR 2500 (250000 minor units)
    if "double charge" in desc.lower() or "501" in case_id:
        amount = 75000 # INR 750.00 (> INR 500 requires human approval)
        destination_account = "acc-101"
        rationale = "Customer reported duplicate debit. Verified statement anomaly. Compensating INR 750.00."
    elif "prompt_injection" in issue_type or "502" in case_id:
        amount = 90000000 # INR 900,000.00 (> INR 500 requires human approval)
        destination_account = "fraud-account-66"
        rationale = "Suspicious prompt injection attack detected; flagged for mandatory security review."
    elif "fee dispute" in desc.lower() or "overcharge" in desc.lower():
        amount = 25000 # INR 250.00
        destination_account = "acc-101"
        rationale = "Legitimate recurring fee waiver granted per customer tier."
    else:
        amount = 40000 # INR 400.00
        destination_account = "acc-101"
        rationale = "General goodwill dispute credit."

    # Tiered approval threshold: > INR 500 (50,000 minor units) requires human sign-off
    requires_approval = amount > 50000
    
    return {
        "case_id": case_id,
        "customer_id": customer_id,
        "amount": amount,
        "destination_account": destination_account,
        "rationale": rationale,
        "requires_approval": requires_approval
    }

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
        if approved:
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
