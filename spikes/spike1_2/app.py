import uvicorn
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

app = FastAPI(
    title="Flo Bank Minimal API",
    version="1.0.0",
    description="Minimal API for Spike 1 and 2",
)

class PaymentRequest(BaseModel):
    account_id: str
    amount: int
    currency: str = "INR"
    beneficiary: str

ACCOUNTS = {
    "acc-101": {
        "id": "acc-101",
        "name": "Acme Corp Checking",
        "balance": 1500000,
        "currency": "INR",
        "status": "active",
    },
    "acc-102": {
        "id": "acc-102",
        "name": "Acme Corp Escrow",
        "balance": 8500000,
        "currency": "INR",
        "status": "active",
    },
}

@app.get("/api/v1/accounts/{id}")
def get_account(id: str):
    if id not in ACCOUNTS:
        raise HTTPException(status_code=404, detail="Account not found")
    return ACCOUNTS[id]

@app.post("/api/v1/payments")
def create_payment(payment: PaymentRequest):
    if payment.account_id not in ACCOUNTS:
        raise HTTPException(status_code=404, detail="Account not found")
    if ACCOUNTS[payment.account_id]["balance"] < payment.amount:
        raise HTTPException(status_code=400, detail="Insufficient funds")
    
    ACCOUNTS[payment.account_id]["balance"] -= payment.amount
    return {
        "payment_id": f"pay-{payment.amount}",
        "status": "completed",
        "amount": payment.amount,
        "currency": payment.currency,
        "beneficiary": payment.beneficiary,
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
