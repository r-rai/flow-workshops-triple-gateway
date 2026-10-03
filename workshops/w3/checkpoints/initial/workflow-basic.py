# Initial Vulnerable / Naive Checkpoint: In-Memory Workflow
# Anti-patterns:
# 1. State stored in volatile Python memory (lost on crash)
# 2. No stable workflow ID deduplication
# 3. Direct execution of side effects without human approval wait
# 4. No idempotent backend key

import httpx

def handle_dispute_naive(case_id: str, case_data: dict):
    # Directly executes payment without waiting for approval
    amount = 75000
    destination_account = "acc-101"
    
    # Financial mutation happens immediately
    resp = httpx.post("http://localhost:8000/api/v1/payments", json={
        "account_id": "acc-102",
        "beneficiary": destination_account,
        "amount": amount,
        "currency": "INR"
    }, headers={"X-API-Key": "gate3-secret-token"})
    
    # If worker crashes right here, event redelivery from Kafka causes DUPLICATE payment!
    return resp.json()
