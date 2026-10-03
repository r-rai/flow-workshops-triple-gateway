from typing import List
from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.models.schemas import SupportCaseResponse
from src.services.cases import get_case_by_id, list_cases
from src.core.security import require_scope, Principal

router = APIRouter(prefix="/api/v1/cases", tags=["SupportCases"])

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
