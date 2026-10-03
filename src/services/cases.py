from typing import List
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from src.models.db_models import SupportCase
from src.models.schemas import SupportCaseResponse

def get_case_by_id(db: Session, case_id: str) -> SupportCaseResponse:
    c = db.query(SupportCase).filter(SupportCase.id == case_id).first()
    if not c:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Support case '{case_id}' not found")
    return SupportCaseResponse(
        id=c.id,
        customer_id=c.customer_id,
        issue_type=c.issue_type,
        description=c.description,
        priority=c.priority,
        status=c.status,
    )

def list_cases(db: Session, limit: int = 50) -> List[SupportCaseResponse]:
    cases = db.query(SupportCase).limit(limit).all()
    return [
        SupportCaseResponse(
            id=c.id,
            customer_id=c.customer_id,
            issue_type=c.issue_type,
            description=c.description,
            priority=c.priority,
            status=c.status,
        )
        for c in cases
    ]

def update_case(db: Session, case_id: str, updates: dict) -> SupportCaseResponse:
    c = db.query(SupportCase).filter(SupportCase.id == case_id).first()
    if not c:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Support case '{case_id}' not found")
    if "status" in updates:
        c.status = updates["status"]
    db.commit()
    db.refresh(c)
    return SupportCaseResponse(
        id=c.id,
        customer_id=c.customer_id,
        issue_type=c.issue_type,
        description=c.description,
        priority=c.priority,
        status=c.status,
    )
