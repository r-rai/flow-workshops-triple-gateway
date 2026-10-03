import uuid
import time
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from src.models.db_models import Incident, RemediationRecord
from src.models.schemas import IncidentResponse, RemediationResponse
from src.core.security import Principal

def get_incident_by_id(db: Session, incident_id: str) -> IncidentResponse:
    inc = db.query(Incident).filter(Incident.id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Incident '{incident_id}' not found")
    return IncidentResponse(
        id=inc.id,
        service_name=inc.service_name,
        severity=inc.severity,
        status=inc.status,
        root_cause=inc.root_cause,
        remediation_action=inc.remediation_action,
    )

def remediate_incident_service(
    db: Session,
    principal: Principal,
    incident_id: str,
    action: str,
) -> RemediationResponse:
    inc = db.query(Incident).filter(Incident.id == incident_id).with_for_update().first()
    if not inc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Incident '{incident_id}' not found")

    if inc.status == "resolved":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incident is already resolved")

    rem_id = f"rem-{uuid.uuid4().hex[:8]}"
    record = RemediationRecord(
        id=rem_id,
        incident_id=inc.id,
        action=action,
        operator_id=principal.id,
        executed_at=time.time(),
        result="SUCCESS",
    )
    inc.status = "resolved"
    inc.updated_at = time.time()
    db.add(record)
    db.commit()

    return RemediationResponse(
        remediation_id=rem_id,
        incident_id=inc.id,
        action=action,
        status="resolved",
        result="SUCCESS",
    )
