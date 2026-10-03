from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.models.schemas import IncidentResponse, RemediationRequest, RemediationResponse
from src.services.incidents import get_incident_by_id, remediate_incident_service
from src.core.security import require_scope, Principal

router = APIRouter(prefix="/api/v1/incidents", tags=["Incidents"])

@router.get("/{id}", response_model=IncidentResponse)
def read_incident(
    id: str = Path(..., description="The unique incident identifier"),
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_scope("api:cases:read")),
):
    return get_incident_by_id(db, id)

@router.post("/{id}/remediate", response_model=RemediationResponse)
def remediate_incident(
    req: RemediationRequest,
    id: str = Path(..., description="The unique incident identifier"),
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_scope("api:incidents:write")),
):
    return remediate_incident_service(db, principal, id, req.action)
