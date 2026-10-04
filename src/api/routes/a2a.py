import json
import time
import uuid
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Path
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from src.core.database import get_db
from src.models.db_models import A2ATask, PaymentRecord, PaymentProposal, PaymentTaskBinding
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

    # Owner-scoped or designated executor task access invariant
    if principal.id != task.owner_id and principal.id != "payments-agent-executor" and principal.role != "admin":
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
    principal: Principal = Depends(get_current_principal),
):
    task = db.query(A2ATask).filter(A2ATask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task '{task_id}' not found")

    # 1. State transition validation: cannot complete task in terminal status
    if task.status in ("completed", "failed", "cancelled"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid state transition: Task '{task_id}' is already in terminal state '{task.status}'",
        )

    # 2. Scope check: requires api:payments:write or api:a2a:tasks
    if not any(s in principal.scopes for s in ("api:payments:write", "api:a2a:tasks")):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient scope to complete task",
        )

    # 3. Authorized completion executor check:
    # Payment proposals must be executed and completed by designated payments executor or admin with payments:write
    if task.task_type == "propose_payment":
        if principal.id != "payments-agent-executor" and principal.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: caller '{principal.id}' is not authorized as payment executor for task '{task_id}'",
            )
        if "api:payments:write" not in principal.scopes and principal.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Payment executor requires 'api:payments:write' scope to complete payment task",
            )
    else:
        authorized_actors = {task.owner_id, "payments-agent-executor"}
        if principal.id not in authorized_actors and principal.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: caller '{principal.id}' is not authorized to complete task '{task_id}'",
            )

    # 4. Strict Settlement Binding Validation
    if task.task_type == "propose_payment" or result_data.get("payment_id") or result_data.get("status") in ("SETTLED", "completed"):
        payment_id = result_data.get("payment_id")
        if not payment_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Settlement completion requires a valid 'payment_id'",
            )

        # Validate payment existence in banking ledger
        payment = db.query(PaymentRecord).filter(PaymentRecord.id == payment_id).first()
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Settlement payment '{payment_id}' does not exist in banking ledger",
            )

        # Validate payment status
        if payment.status not in ("completed", "settled"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Payment '{payment_id}' is not settled (status: '{payment.status}')",
            )

        # Validate task input correlation
        try:
            task_input = json.loads(task.input_json)
        except Exception:
            task_input = {}

        # Validate amount
        expected_amount = task_input.get("amount")
        if expected_amount is not None and int(payment.amount) != int(expected_amount):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Settlement amount mismatch: payment '{payment_id}' amount {payment.amount} != task amount {expected_amount}",
            )

        # Validate currency
        expected_currency = task_input.get("currency")
        if expected_currency and payment.currency != expected_currency:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Settlement currency mismatch: payment '{payment_id}' currency '{payment.currency}' != task currency '{expected_currency}'",
            )

        # Validate destination account / beneficiary (strict beneficiary match only)
        expected_dest = task_input.get("destination_account") or task_input.get("beneficiary")
        if expected_dest:
            if payment.beneficiary != expected_dest:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Settlement destination mismatch: payment target '{payment.beneficiary}' does not match task destination '{expected_dest}'",
                )

        # Validate unique task association: prevent reusing the same payment_id across multiple tasks
        existing_binding = db.query(PaymentTaskBinding).filter(PaymentTaskBinding.payment_id == payment_id).first()
        if existing_binding and existing_binding.task_id != task.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Payment '{payment_id}' is already bound to task '{existing_binding.task_id}'",
            )

        existing_tasks = db.query(A2ATask).filter(
            A2ATask.id != task.id,
            A2ATask.status.in_(["completed", "settled"]),
        ).all()
        for t in existing_tasks:
            try:
                t_out = json.loads(t.output_json or "{}")
                if t_out.get("payment_id") == payment_id:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Payment '{payment_id}' is already bound to task '{t.id}'",
                    )
            except (json.JSONDecodeError, TypeError):
                continue

        # Validate proposal / approval association
        if payment.proposal_id:
            prop = db.query(PaymentProposal).filter(PaymentProposal.id == payment.proposal_id).first()
            if not prop or prop.status != "consumed":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Associated payment proposal '{payment.proposal_id}' is not in consumed state",
                )

        # Atomic claim in database
        binding = PaymentTaskBinding(payment_id=payment_id, task_id=task.id, created_at=time.time())
        db.add(binding)
        task.bound_payment_id = payment_id

    task.status = "completed"
    task.output_json = json.dumps(result_data)
    task.updated_at = time.time()

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Payment '{payment_id}' is already bound to another task",
        )
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

