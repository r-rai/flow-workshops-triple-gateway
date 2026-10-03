from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.models.schemas import PaymentProposalResponse, ApprovalActionResponse, ApprovalActionRequest
from src.services.approvals import get_proposal_service, approve_proposal_service, reject_proposal_service
from src.core.security import get_current_principal, Principal

router = APIRouter(prefix="/api/v1/approvals", tags=["Approvals"])

@router.get("/{id}", response_model=PaymentProposalResponse)
def get_approval(
    id: str = Path(..., description="The unique proposal/approval identifier"),
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    return get_proposal_service(db, id)

@router.post("/{id}/approve", response_model=ApprovalActionResponse)
def approve_proposal(
    id: str = Path(..., description="The unique proposal/approval identifier"),
    req: ApprovalActionRequest = None,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    return approve_proposal_service(db, principal, id)

@router.post("/{id}/reject", response_model=ApprovalActionResponse)
def reject_proposal(
    id: str = Path(..., description="The unique proposal/approval identifier"),
    req: ApprovalActionRequest = None,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    return reject_proposal_service(db, principal, id)
