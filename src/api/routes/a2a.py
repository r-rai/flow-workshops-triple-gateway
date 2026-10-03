import time
import uuid
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Path
from pydantic import BaseModel, Field
from src.core.security import get_current_principal, Principal, require_scope

router = APIRouter(prefix="/api/v1/a2a", tags=["A2A"])

# In-memory A2A task registry (persistent across requests in API process)
A2A_TASKS: Dict[str, Dict[str, Any]] = {}

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
    principal: Principal = Depends(get_current_principal),
):
    task_id = f"task-{uuid.uuid4().hex[:8]}"
    task_record = {
        "task_id": task_id,
        "owner_id": principal.id,
        "owner_role": principal.role,
        "type": req.task_type,
        "status": "pending_approval",
        "input": req.input,
        "output": None,
        "created_at": time.time(),
    }
    A2A_TASKS[task_id] = task_record
    return task_record

@router.get("/tasks/{task_id}", response_model=TaskResponse)
def get_a2a_task(
    task_id: str = Path(..., description="Unique A2A task ID"),
    principal: Principal = Depends(get_current_principal),
):
    if task_id not in A2A_TASKS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task '{task_id}' not found")

    task = A2A_TASKS[task_id]
    # Owner-scoped task access invariant
    if principal.id != task["owner_id"] and principal.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied: caller '{principal.id}' does not own task '{task_id}'"
        )

    return task

@router.post("/tasks/{task_id}/complete", response_model=TaskResponse)
def complete_a2a_task(
    result_data: Dict[str, Any],
    task_id: str = Path(...),
    principal: Principal = Depends(require_scope("api:payments:write")),
):
    if task_id not in A2A_TASKS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task '{task_id}' not found")
    
    task = A2A_TASKS[task_id]
    task["status"] = "completed"
    task["output"] = result_data
    return task
