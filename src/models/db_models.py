import time
from sqlalchemy import Column, String, Integer, BigInteger, Text, Boolean, Float
from src.core.database import Base

class Account(Base):
    __tablename__ = "accounts"

    id = Column(String(64), primary_key=True, index=True)
    name = Column(String(128), nullable=False)
    balance = Column(BigInteger, nullable=False) # integer minor units
    currency = Column(String(8), nullable=False, default="INR")
    status = Column(String(32), nullable=False, default="active")
    updated_at = Column(Float, default=time.time, onupdate=time.time)

class SupportCase(Base):
    __tablename__ = "support_cases"

    id = Column(String(64), primary_key=True, index=True)
    customer_id = Column(String(64), nullable=False, index=True)
    issue_type = Column(String(64), nullable=False)
    description = Column(Text, nullable=False)
    priority = Column(String(32), nullable=False, default="medium")
    status = Column(String(32), nullable=False, default="open")
    updated_at = Column(Float, default=time.time, onupdate=time.time)

class Incident(Base):
    __tablename__ = "incidents"

    id = Column(String(64), primary_key=True, index=True)
    service_name = Column(String(128), nullable=False)
    severity = Column(String(32), nullable=False)
    status = Column(String(32), nullable=False, default="triggered")
    root_cause = Column(Text, nullable=True)
    remediation_action = Column(String(128), nullable=False)
    updated_at = Column(Float, default=time.time, onupdate=time.time)

class PaymentProposal(Base):
    __tablename__ = "payment_proposals"

    id = Column(String(64), primary_key=True, index=True)
    requester_id = Column(String(128), nullable=False)
    account_id = Column(String(64), nullable=False)
    amount = Column(BigInteger, nullable=False)
    currency = Column(String(8), nullable=False, default="INR")
    beneficiary = Column(String(128), nullable=False)
    canonical_args_hash = Column(String(64), nullable=False, index=True)
    status = Column(String(32), nullable=False, default="pending") # pending, approved, rejected, expired, consumed
    approver_id = Column(String(128), nullable=True)
    expires_at = Column(Float, nullable=False)
    created_at = Column(Float, default=time.time)
    consumed_at = Column(Float, nullable=True)

class PaymentRecord(Base):
    __tablename__ = "payment_records"

    id = Column(String(64), primary_key=True, index=True)
    proposal_id = Column(String(64), nullable=True, index=True)
    account_id = Column(String(64), nullable=False, index=True)
    amount = Column(BigInteger, nullable=False)
    currency = Column(String(8), nullable=False)
    beneficiary = Column(String(128), nullable=False)
    idempotency_key = Column(String(128), nullable=True, index=True)
    status = Column(String(32), nullable=False, default="completed")
    created_at = Column(Float, default=time.time)

class RemediationRecord(Base):
    __tablename__ = "remediation_records"

    id = Column(String(64), primary_key=True, index=True)
    incident_id = Column(String(64), nullable=False, index=True)
    action = Column(String(128), nullable=False)
    operator_id = Column(String(128), nullable=False)
    executed_at = Column(Float, default=time.time)
    result = Column(String(64), nullable=False, default="SUCCESS")

class IdempotencyRecord(Base):
    __tablename__ = "idempotency_records"

    id = Column(String(128), primary_key=True) # {principal_id}:{action}:{key}
    principal_id = Column(String(128), nullable=False)
    action = Column(String(64), nullable=False)
    idempotency_key = Column(String(128), nullable=False)
    payload_hash = Column(String(64), nullable=False)
    response_json = Column(Text, nullable=False)
    created_at = Column(Float, default=time.time)

class A2ATask(Base):
    __tablename__ = "a2a_tasks"

    id = Column(String(64), primary_key=True, index=True)
    owner_id = Column(String(128), nullable=False, index=True)
    owner_role = Column(String(64), nullable=False)
    task_type = Column(String(64), nullable=False)
    status = Column(String(32), nullable=False, default="pending_approval")
    input_json = Column(Text, nullable=False)
    output_json = Column(Text, nullable=True)
    created_at = Column(Float, default=time.time)
    updated_at = Column(Float, default=time.time, onupdate=time.time)
