import time
import uuid
import json
import hashlib
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from src.models.db_models import PaymentProposal
from src.models.schemas import PaymentProposalRequest, PaymentProposalResponse, ApprovalActionResponse
from src.core.security import Principal

def canonical_hash(obj: dict) -> str:
    serialized = json.dumps(obj, sort_keys=True)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

def create_proposal_service(
    db: Session,
    principal: Principal,
    req: PaymentProposalRequest,
    expiry_seconds: int = 600,
) -> PaymentProposalResponse:
    proposal_id = f"prop-{uuid.uuid4().hex[:8]}"
    payload_dict = {
        "account_id": req.account_id,
        "amount": req.amount,
        "currency": req.currency,
        "beneficiary": req.beneficiary,
    }
    args_hash = canonical_hash(payload_dict)
    expires_at = time.time() + expiry_seconds

    proposal = PaymentProposal(
        id=proposal_id,
        requester_id=principal.id,
        account_id=req.account_id,
        amount=req.amount,
        currency=req.currency,
        beneficiary=req.beneficiary,
        canonical_args_hash=args_hash,
        status="pending",
        expires_at=expires_at,
        created_at=time.time(),
    )
    db.add(proposal)
    db.commit()

    return PaymentProposalResponse(
        proposal_id=proposal.id,
        requester_id=proposal.requester_id,
        account_id=proposal.account_id,
        amount=proposal.amount,
        currency=proposal.currency,
        beneficiary=proposal.beneficiary,
        status=proposal.status,
        expires_at=proposal.expires_at,
    )

def get_proposal_service(db: Session, proposal_id: str) -> PaymentProposalResponse:
    prop = db.query(PaymentProposal).filter(PaymentProposal.id == proposal_id).first()
    if not prop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proposal not found")
    return PaymentProposalResponse(
        proposal_id=prop.id,
        requester_id=prop.requester_id,
        account_id=prop.account_id,
        amount=prop.amount,
        currency=prop.currency,
        beneficiary=prop.beneficiary,
        status=prop.status,
        expires_at=prop.expires_at,
    )

def approve_proposal_service(
    db: Session,
    principal: Principal,
    proposal_id: str,
) -> ApprovalActionResponse:
    if getattr(principal, "auth_method", "bearer") != "bearer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Approvals require an authenticated Bearer token. Static lab API keys cannot approve proposals.",
        )

    prop = db.query(PaymentProposal).filter(PaymentProposal.id == proposal_id).first()
    if not prop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proposal not found")

    if prop.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot approve proposal in '{prop.status}' state",
        )
    if prop.expires_at < time.time():
        prop.status = "expired"
        db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Proposal has expired")

    # Anti-Self-Approval Invariant (requester or delegated actor)
    if principal.id == prop.requester_id or getattr(principal, "delegated_by", None) == prop.requester_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Self-approval prohibited: Requester cannot approve their own proposal",
        )

    # Role Invariant
    if principal.role not in ("manager", "admin", "approver"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Unauthorized role '{principal.role}'. Manager or approver role required.",
        )

    # Atomic CAS status transition: status 'pending' -> 'approved'
    approved_count = db.query(PaymentProposal).filter(
        PaymentProposal.id == proposal_id,
        PaymentProposal.status == "pending"
    ).update(
        {
            PaymentProposal.status: "approved",
            PaymentProposal.approver_id: principal.id,
        },
        synchronize_session="fetch"
    )
    if approved_count == 0:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Proposal status changed concurrently",
        )

    db.commit()

    return ApprovalActionResponse(
        proposal_id=prop.id,
        status="approved",
        approver_id=principal.id,
        message="Proposal successfully approved",
    )

def reject_proposal_service(
    db: Session,
    principal: Principal,
    proposal_id: str,
) -> ApprovalActionResponse:
    if getattr(principal, "auth_method", "bearer") != "bearer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Rejections require an authenticated Bearer token. Static lab API keys cannot reject proposals.",
        )

    prop = db.query(PaymentProposal).filter(PaymentProposal.id == proposal_id).first()
    if not prop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proposal not found")

    if prop.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot reject proposal in '{prop.status}' state",
        )

    # Role/Owner Invariant: Requester can cancel/reject their own proposal, or an authorized manager/admin/approver can reject
    if principal.role not in ("manager", "admin", "approver") and principal.id != prop.requester_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Unauthorized role '{principal.role}'. Manager or approver role (or proposal requester) required to reject.",
        )

    # Atomic CAS status transition: status 'pending' -> 'rejected'
    rejected_count = db.query(PaymentProposal).filter(
        PaymentProposal.id == proposal_id,
        PaymentProposal.status == "pending"
    ).update(
        {
            PaymentProposal.status: "rejected",
            PaymentProposal.approver_id: principal.id,
        },
        synchronize_session="fetch"
    )
    if rejected_count == 0:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Proposal status changed concurrently",
        )

    db.commit()

    return ApprovalActionResponse(
        proposal_id=prop.id,
        status="rejected",
        approver_id=principal.id,
        message="Proposal rejected",
    )

