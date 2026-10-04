"""Re-audit probes: temporary SQLite DB and mocked transports; no live debits."""
import asyncio
import concurrent.futures
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
scratch = tempfile.TemporaryDirectory(prefix="novabank-final-concurrency-")
os.environ["DATABASE_URL"] = "sqlite:///" + scratch.name + "/isolated.sqlite"
from fastapi import HTTPException
from fastapi.testclient import TestClient
import httpx
from sqlalchemy import event
from src.core.database import Base, engine, SessionLocal
from src.core.security import Principal
from src.models.db_models import Account, PaymentRecord, PaymentProposal
from src.models.schemas import PaymentProposalRequest, PaymentExecuteRequest
from src.services.seed import reset_and_seed_db
from src.services.approvals import create_proposal_service, approve_proposal_service
from src.services.banking import execute_payment_service
from src.adapter import server
from src.worker import kafka_consumer as kafka
from src.worker.activities import execute_settlement_and_notify

results = {}
agent = Principal("audit-agent", "agent", ["api:payments:write"])
manager = Principal("audit-manager", "manager", ["api:payments:write"])

def reset():
    with SessionLocal() as db:
        reset_and_seed_db(db)

def execute(payload, key):
    with SessionLocal() as db:
        try:
            res = execute_payment_service(db, agent, PaymentExecuteRequest(**payload), key)
            return {"status": 200, "response": res.model_dump()}
        except HTTPException as exc:
            db.rollback()
            return {"status": exc.status_code, "detail": exc.detail}
        except Exception as exc:
            db.rollback()
            return {"status": 500, "error": type(exc).__name__ + ": " + str(exc)}

reset()
payload = {"account_id": "acc-102", "amount": 150000, "currency": "INR", "beneficiary": "acc-101"}
with SessionLocal() as db:
    before = db.get(Account, "acc-102").balance
    prop = create_proposal_service(db, agent, PaymentProposalRequest(**payload)).proposal_id
    approve_proposal_service(db, manager, prop)
barrier = threading.Barrier(2)
def synchronize_proposal(conn, cursor, statement, parameters, context, many):
    if threading.current_thread().name.startswith("race") and statement.lstrip().startswith("SELECT") and "FROM payment_proposals" in statement:
        barrier.wait(timeout=10)
event.listen(engine, "after_cursor_execute", synchronize_proposal)
with concurrent.futures.ThreadPoolExecutor(max_workers=2, thread_name_prefix="race") as pool:
    calls = list(pool.map(lambda i: execute({**payload, "proposal_id": prop}, f"race-{i}"), [1, 2]))
event.remove(engine, "after_cursor_execute", synchronize_proposal)
with SessionLocal() as db:
    results["forced_proposal_race"] = {"calls": calls, "statuses": sorted(c["status"] for c in calls), "payment_count": db.query(PaymentRecord).filter_by(proposal_id=prop).count(), "balance_before": before, "balance_after": db.get(Account, "acc-102").balance, "proposal_status": db.get(PaymentProposal, prop).status}

reset()
with SessionLocal() as db:
    before = db.get(Account, "acc-102").balance
barrier = threading.Barrier(2)
account_threads_seen = set()
def synchronize_account(conn, cursor, statement, parameters, context, many):
    thread_name = threading.current_thread().name
    if thread_name.startswith("debit") and thread_name not in account_threads_seen and statement.lstrip().startswith("SELECT") and "FROM accounts" in statement:
        account_threads_seen.add(thread_name)
        barrier.wait(timeout=10)
event.listen(engine, "after_cursor_execute", synchronize_account)
with concurrent.futures.ThreadPoolExecutor(max_workers=2, thread_name_prefix="debit") as pool:
    calls = list(pool.map(lambda i: execute({**payload, "amount": 50000}, f"debit-{i}"), [1, 2]))
event.remove(engine, "after_cursor_execute", synchronize_account)
with SessionLocal() as db:
    results["independent_debit_race"] = {"statuses": [c["status"] for c in calls], "balance_before": before, "balance_after": db.get(Account, "acc-102").balance, "payment_count": db.query(PaymentRecord).count()}

async def offset_probe(mode):
    stop = asyncio.Event()
    reads, starts, commits, seeks = [], [], [], []
    class Consumer:
        def __init__(self, *args, **kwargs): self.position = 10
        async def start(self): pass
        async def stop(self): pass
        async def getone(self):
            offset = self.position; self.position += 1; reads.append(offset)
            return SimpleNamespace(topic="novabank.disputes", partition=0, offset=offset, value={"case_id": f"case-{offset}"})
        async def commit(self, offsets):
            commits.append({f"{tp.topic}:{tp.partition}": value for tp, value in offsets.items()})
            if any(value == 12 for value in offsets.values()): stop.set()
        def seek(self, tp, offset):
            seeks.append(offset); self.position = offset
            if mode == "shutdown": stop.set()
    class Temporal:
        failures = 0
        async def start_workflow(self, *args, **kwargs):
            starts.append(kwargs["id"])
            if kwargs["id"].endswith("case-10") and self.failures < (10 if mode != "transient" else 1):
                self.failures += 1; raise RuntimeError("Injected Temporal start failure")
            return SimpleNamespace(run_id="isolated-audit")
    temporal = Temporal()
    async def connect(*args, **kwargs): return temporal
    async def no_delay(*args, **kwargs): pass
    with patch.object(kafka, "AIOKafkaConsumer", Consumer), patch.object(kafka.Client, "connect", connect), patch.object(kafka.asyncio, "Event", return_value=stop), patch.object(kafka.asyncio, "sleep", no_delay):
        await kafka.run_consumer()
    return {"mode": mode, "read_offsets": reads, "start_attempts": starts, "commits": commits, "seeks": seeks}
results["kafka_offsets"] = [asyncio.run(offset_probe(mode)) for mode in ["transient", "exhaust_then_recover", "shutdown"]]

assert results["forced_proposal_race"]["statuses"] == [200, 409]
assert results["forced_proposal_race"]["payment_count"] == 1
assert results["forced_proposal_race"]["balance_after"] == before - 150000  # Seeded balance identical in both probes.
assert results["independent_debit_race"]["balance_after"] == before - 100000

Path(__file__).with_suffix(".json").write_text(json.dumps(results, indent=2))
print(json.dumps(results, indent=2))
engine.dispose()
scratch.cleanup()
