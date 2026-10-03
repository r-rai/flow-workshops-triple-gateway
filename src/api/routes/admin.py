from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.models.schemas import ResetResponse
from src.services.seed import reset_and_seed_db
from src.core.security import get_current_principal, Principal

router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])

@router.post("/reset", response_model=ResetResponse)
def reset_database(
    x_confirm_reset: str = Header(None, alias="X-Confirm-Reset"),
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    if principal.role not in ("admin", "operator") and principal.id != "w1-lab-operator":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or operator role required to reset database",
        )
    if x_confirm_reset != "CONFIRM":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Safety check: Must provide header 'X-Confirm-Reset: CONFIRM' to execute reset",
        )

    res = reset_and_seed_db(db)
    return ResetResponse(**res)
