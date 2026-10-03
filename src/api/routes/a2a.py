import json
import time
import uuid
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Path
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.models.db_models import A2ATask
from src.core.security import get_current_principal, Principal, require_scope

router = APIRouter(prefix="/api/v1/a2a", tags=["A2A"])

AGENT_CARD = {
    "name": "NovaBank PaymentsAgent",
    "description": "Agent-to-Agent interface for compliant payment proposal and execution",
    "url": "http://127.0.0.1:9080/api/v1/a2a",
    "version": "1.0.0",
    "protocolVersion": "0.2.0",
    "skills": [
        {
            "id": "propose_payment",
            "name": "Propose Payment",
            "description": "Submits a payment request for governance evaluation and supervisory approval"
        },
        {
            "id": "query_task_status",
            "name": "Query Task Status",
            "description": "Queries the real-time processing status of a submitted payment task"
        }
    ],
    "authentication": {
        "type": "oauth2",
        "tokenUrl": "http://127.0.0.1:9080/oauth/token"
    }
}

class TaskCreateRequest(BaseModel):
    task_type: str = Field(..., example="propose_payment")
    input: Dict[str, Any]

class TaskResponse(BaseModel):
    task_id: str
    owner_id: str
    owner_role: str
    type: str
    status: str
    input: Dict[str, Any]
    output: Optional[Dict[str, Any]] = None
    created_at: float

@router.get("/card")
def get_agent_card():
    return AGENT_CARD

@router.post("/tasks", response_model=TaskResponse)
def submit_a2a_task(
    req: TaskCreateRequest,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    # Enforce required task creation scope (viewer tokens with no write scope are rejected with 403)
    if not any(s in principal.scopes for s in ("api:payments:write", "api:a2a:tasks")):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient scope. Task creation requires 'api:payments:write' or 'api:a2a:tasks', present: {principal.scopes}"
        )

    task_id = f"task-{uuid.uuid4().hex[:8]}"
    now = time.time()
    task = A2ATask(
        id=task_id,
        owner_id=principal.id,
        owner_role=principal.role,
        task_type=req.task_type,
        status="pending_approval",
        input_json=json.dumps(req.input),
        output_json=None,
        created_at=now,
        updated_at=now,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    return TaskResponse(
        task_id=task.id,
        owner_id=task.owner_id,
        owner_role=task.owner_role,
        type=task.task_type,
        status=task.status,
        input=json.loads(task.input_json),
        output=json.loads(task.output_json) if task.output_json else None,
        created_at=task.created_at,
    )

@router.get("/tasks/{task_id}", response_model=TaskResponse)
def get_a2a_task(
    task_id: str = Path(..., description="Unique A2A task ID"),
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    task = db.query(A2ATask).filter(A2ATask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task '{task_id}' not found")

    # Scope verification
    if not any(s in principal.scopes for s in ("api:accounts:read", "api:payments:write", "api:a2a:tasks")):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient scope to query task status",
        )

    # Owner-scoped task access invariant
    if principal.id != task.owner_id and principal.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied: caller '{principal.id}' does not own task '{task_id}'"
        )

    return TaskResponse(
        task_id=task.id,
        owner_id=task.owner_id,
        owner_role=task.owner_role,
        type=task.task_type,
        status=task.status,
        input=json.loads(task.input_json),
        output=json.loads(task.output_json) if task.output_json else None,
        created_at=task.created_at,
    )

@router.post("/tasks/{task_id}/complete", response_model=TaskResponse)
def complete_a2a_task(
    result_data: Dict[str, Any],
    task_id: str = Path(...),
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_scope("api:payments:write")),
):
    task = db.query(A2ATask).filter(A2ATask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task '{task_id}' not found")
    
    # Owner-scoped completion invariant
    if principal.id != task.owner_id and principal.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied: caller '{principal.id}' does not own task '{task_id}'"
        )

    task.status = "completed"
    task.output_json = json.dumps(result_data)
    task.updated_at = time.time()
    db.commit()
    db.refresh(task)

    return TaskResponse(
        task_id=task.id,
        owner_id=task.owner_id,
        owner_role=task.owner_role,
        type=task.task_type,
        status=task.status,
        input=json.loads(task.input_json),
        output=json.loads(task.output_json) if task.output_json else None,
        created_at=task.created_at,
    )

