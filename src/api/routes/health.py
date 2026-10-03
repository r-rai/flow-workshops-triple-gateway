from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.models.schemas import HealthResponse
from src.core.config import settings

router = APIRouter(tags=["Health"])

@router.get("/healthz", response_model=HealthResponse)
def healthz(db: Session = Depends(get_db)):
    db_status = "connected"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"error: {str(e)}"

    return HealthResponse(
        status="healthy" if db_status == "connected" else "degraded",
        version="1.0.0",
        database=db_status,
    )

@router.get("/readyz", response_model=HealthResponse)
def readyz(db: Session = Depends(get_db)):
    return healthz(db)
