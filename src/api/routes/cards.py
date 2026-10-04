from fastapi import APIRouter, Depends, HTTPException, Path, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.models.db_models import CardRecord
from src.core.security import require_scope, Principal

router = APIRouter(prefix="/api/v1/cards", tags=["Cards"])

class CardStateRequest(BaseModel):
    locked: bool

@router.get("/{id}")
def read_card(
    id: str = Path(...),
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_scope("api:cards:read")),
):
    card = db.query(CardRecord).filter(CardRecord.id == id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    return {
        "id": card.id,
        "account_id": card.account_id,
        "customer_id": card.customer_id,
        "last_four": card.last_four,
        "holder_name": card.holder_name,
        "expiry": card.expiry,
        "locked": card.locked,
    }

@router.post("/{id}/state")
def set_card_state(
    payload: CardStateRequest,
    id: str = Path(...),
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_scope("api:cards:write")),
):
    card = db.query(CardRecord).filter(CardRecord.id == id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    card.locked = payload.locked
    db.commit()
    db.refresh(card)
    return {
        "id": card.id,
        "locked": card.locked,
        "status": "frozen" if card.locked else "active",
    }
