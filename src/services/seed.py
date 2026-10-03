import os
import json
import time
from sqlalchemy.orm import Session
from src.core.database import Base, engine
from src.models.db_models import Account, SupportCase, Incident, PaymentProposal, PaymentRecord, RemediationRecord, IdempotencyRecord
from src.core.config import settings

def reset_and_seed_db(db: Session, seed_file: str = None) -> dict:
    if seed_file is None:
        seed_file = settings.SEED_FILE_PATH

    # Recreate tables
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    # Read seed file
    if not os.path.exists(seed_file):
        # Fallback to local relative
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
        seed_file = os.path.join(base_dir, "seed/v1_seed.json")

    with open(seed_file, "r") as f:
        data = json.load(f)

    # Insert Accounts
    for acc in data.get("accounts", []):
        db.add(Account(
            id=acc["id"],
            name=acc["name"],
            balance=acc["balance"],
            currency=acc.get("currency", "INR"),
            status=acc.get("status", "active"),
            updated_at=time.time(),
        ))

    # Insert Support Cases
    for case in data.get("cases", []):
        db.add(SupportCase(
            id=case["id"],
            customer_id=case["customer_id"],
            issue_type=case["issue_type"],
            description=case["description"],
            priority=case.get("priority", "medium"),
            status=case.get("status", "open"),
            updated_at=time.time(),
        ))

    # Insert Incidents
    for inc in data.get("incidents", []):
        db.add(Incident(
            id=inc["id"],
            service_name=inc["service_name"],
            severity=inc["severity"],
            status=inc.get("status", "triggered"),
            root_cause=inc.get("root_cause"),
            remediation_action=inc["remediation_action"],
            updated_at=time.time(),
        ))

    db.commit()

    return {
        "status": "success",
        "message": "Database successfully reset and seeded",
        "seed_version": data.get("version", "1.0.0"),
        "accounts_seeded": len(data.get("accounts", [])),
        "cases_seeded": len(data.get("cases", [])),
        "incidents_seeded": len(data.get("incidents", [])),
    }
