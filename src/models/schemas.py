from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

class AccountResponse(BaseModel):
    id: str
    name: str
    balance: int = Field(..., description="Integer minor units (e.g. paise for INR)")
    currency: str
    status: str

class SupportCaseResponse(BaseModel):
    id: str
    customer_id: str
    issue_type: str
    description: str
    priority: str
    status: str

class IncidentResponse(BaseModel):
    id: str
    service_name: str
    severity: str
    status: str
    root_cause: Optional[str] = None
    remediation_action: str

class PaymentProposalRequest(BaseModel):
    account_id: str
    amount: int = Field(..., gt=0, description="Amount in integer minor units")
    currency: str = "INR"
    beneficiary: str

class PaymentProposalResponse(BaseModel):
    proposal_id: str
    requester_id: str
    account_id: str
    amount: int
    currency: str
    beneficiary: str
    status: str
    expires_at: float

class ApprovalActionRequest(BaseModel):
    notes: Optional[str] = None

class ApprovalActionResponse(BaseModel):
    proposal_id: str
    status: str
    approver_id: str
    message: str

class PaymentExecuteRequest(BaseModel):
    account_id: str
    amount: int = Field(..., gt=0)
    currency: str = "INR"
    beneficiary: str
    proposal_id: Optional[str] = Field(None, description="Required if amount exceeds unsupervised policy limit")

class PaymentExecuteResponse(BaseModel):
    payment_id: str
    status: str
    account_id: str
    amount: int
    currency: str
    beneficiary: str
    remaining_balance: int
    idempotent_replay: bool = False

class RemediationRequest(BaseModel):
    action: str
    operator_id: Optional[str] = None

class RemediationResponse(BaseModel):
    remediation_id: str
    incident_id: str
    action: str
    status: str
    result: str

class ResetResponse(BaseModel):
    status: str
    message: str
    seed_version: str
    accounts_seeded: int
    cases_seeded: int
    incidents_seeded: int

class HealthResponse(BaseModel):
    status: str
    version: str
    database: str
