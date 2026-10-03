from typing import Optional
from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.models.schemas import (
    PaymentProposalRequest,
    PaymentProposalResponse,
    PaymentExecuteRequest,
    PaymentExecuteResponse,
)
from src.services.approvals import create_proposal_service
from src.services.banking import execute_payment_service
from src.core.security import require_scope, Principal

router = APIRouter(prefix="/api/v1/payments", tags=["Payments"])

@router.post("/proposals", response_model=PaymentProposalResponse)
def propose_payment(
    req: PaymentProposalRequest,
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_scope("api:payments:write")),
):
    return create_proposal_service(db, principal, req)

@router.post("", response_model=PaymentExecuteResponse)
def execute_payment(
    req: PaymentExecuteRequest,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_scope("api:payments:write")),
):
    return execute_payment_service(db, principal, req, idempotency_key=idempotency_key)
