import time
import json
import uuid
import hashlib
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from src.models.db_models import Account, PaymentRecord, PaymentProposal, IdempotencyRecord
from src.models.schemas import PaymentExecuteRequest, PaymentExecuteResponse, AccountResponse
from src.core.security import Principal

def canonical_hash(obj: dict) -> str:
    serialized = json.dumps(obj, sort_keys=True)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

def get_account_by_id(db: Session, account_id: str) -> AccountResponse:
    acc = db.query(Account).filter(Account.id == account_id).first()
    if not acc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Account '{account_id}' not found")
    return AccountResponse(
        id=acc.id,
        name=acc.name,
        balance=acc.balance,
        currency=acc.currency,
        status=acc.status,
    )

def execute_payment_service(
    db: Session,
    principal: Principal,
    req: PaymentExecuteRequest,
    idempotency_key: str = None,
) -> PaymentExecuteResponse:
    # 1. Idempotency Check
    payload_dict = {
        "account_id": req.account_id,
        "amount": req.amount,
        "currency": req.currency,
        "beneficiary": req.beneficiary,
    }
    req_hash = canonical_hash(payload_dict)

    if idempotency_key:
        idemp_id = f"{principal.id}:payment:{idempotency_key}"
        cached = db.query(IdempotencyRecord).filter(IdempotencyRecord.id == idemp_id).first()
        if cached:
            if cached.payload_hash != req_hash:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Idempotency key reused with different request payload",
                )
            cached_data = json.loads(cached.response_json)
            cached_data["idempotent_replay"] = True
            return PaymentExecuteResponse(**cached_data)

    # 2. Account Validation
    acc = db.query(Account).filter(Account.id == req.account_id).with_for_update().first()
    if not acc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Account '{req.account_id}' not found")
    if acc.status != "active":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Account is not active")

    # 3. Unsupervised threshold check: Amounts > 100,000 minor units require an approved proposal
    UNSUPERVISED_LIMIT = 100000
    if req.amount > UNSUPERVISED_LIMIT:
        if not req.proposal_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Amount {req.amount} exceeds unsupervised limit ({UNSUPERVISED_LIMIT}). Valid proposal_id required.",
            )
        prop = db.query(PaymentProposal).filter(PaymentProposal.id == req.proposal_id).with_for_update().first()
        if not prop:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment proposal not found")
        if prop.status != "approved":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Proposal is not approved. Current status: '{prop.status}'",
            )
        if prop.expires_at < time.time():
            prop.status = "expired"
            db.commit()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Payment proposal has expired")
        
        # Verify exact argument binding
        if prop.canonical_args_hash != req_hash:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Execution arguments do not match the approved proposal arguments",
            )
        
        # Atomically consume proposal
        prop.status = "consumed"
        prop.consumed_at = time.time()

    # 4. Balance check & debit
    if acc.balance < req.amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient funds: available {acc.balance}, required {req.amount}",
        )

    acc.balance -= req.amount
    acc.updated_at = time.time()

    payment_id = f"pay-{uuid.uuid4().hex[:8]}"
    payment_record = PaymentRecord(
        id=payment_id,
        proposal_id=req.proposal_id,
        account_id=req.account_id,
        amount=req.amount,
        currency=req.currency,
        beneficiary=req.beneficiary,
        status="completed",
        created_at=time.time(),
    )
    db.add(payment_record)

    response_payload = {
        "payment_id": payment_id,
        "status": "COMPLETED",
        "account_id": req.account_id,
        "amount": req.amount,
        "currency": req.currency,
        "beneficiary": req.beneficiary,
        "remaining_balance": acc.balance,
        "idempotent_replay": False,
    }

    # Record idempotency
    if idempotency_key:
        db.add(IdempotencyRecord(
            id=idemp_id,
            principal_id=principal.id,
            action="payment",
            idempotency_key=idempotency_key,
            payload_hash=req_hash,
            response_json=json.dumps(response_payload),
            created_at=time.time(),
        ))

    db.commit()
    return PaymentExecuteResponse(**response_payload)
