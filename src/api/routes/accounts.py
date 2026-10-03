from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.models.schemas import AccountResponse
from src.services.banking import get_account_by_id
from src.core.security import require_scope, Principal

router = APIRouter(prefix="/api/v1/accounts", tags=["Accounts"])

@router.get("/{id}", response_model=AccountResponse)
def read_account(
    id: str = Path(..., description="The unique account identifier"),
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_scope("api:accounts:read")),
):
    return get_account_by_id(db, id)
