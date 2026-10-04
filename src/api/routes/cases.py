import time
from typing import List, Optional
from fastapi import APIRouter, Depends, Path, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.models.schemas import SupportCaseResponse
from src.models.db_models import SupportCase
from src.services.cases import get_case_by_id, list_cases
from src.core.security import require_scope, Principal

router = APIRouter(prefix="/api/v1/cases", tags=["SupportCases"])

class CreateCaseRequest(BaseModel):
    id: Optional[str] = None
    customer_id: str
    issue_type: str = "disputed_transaction"
    description: str
    priority: str = "medium"

@router.post("", response_model=SupportCaseResponse, status_code=status.HTTP_201_CREATED)
def create_case_endpoint(
    payload: CreateCaseRequest,
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_scope("api:cases:write")),
):
    case_id = payload.id or f"case-{int(time.time()*1000)}"
    new_case = SupportCase(
        id=case_id,
        customer_id=payload.customer_id,
        issue_type=payload.issue_type,
        description=payload.description,
        priority=payload.priority,
        status="open",
        updated_at=time.time(),
    )
    db.add(new_case)
    db.commit()
    db.refresh(new_case)
    return SupportCaseResponse(
        id=new_case.id,
        customer_id=new_case.customer_id,
        issue_type=new_case.issue_type,
        description=new_case.description,
        priority=new_case.priority,
        status=new_case.status,
    )

@router.get("", response_model=List[SupportCaseResponse])
def get_all_cases(
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_scope("api:cases:read")),
):
    return list_cases(db)

@router.get("/{id}", response_model=SupportCaseResponse)
def read_case(
    id: str = Path(..., description="The unique support case identifier"),
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_scope("api:cases:read")),
):
    return get_case_by_id(db, id)

@router.patch("/{id}", response_model=SupportCaseResponse)
def update_case_endpoint(
    updates: dict,
    id: str = Path(..., description="The unique support case identifier"),
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_scope("api:cases:write")),
):
    from src.services.cases import update_case
    return update_case(db, id, updates)

