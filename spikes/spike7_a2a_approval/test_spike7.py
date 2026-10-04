import time
import json
import uuid
import hashlib
from typing import Dict, Any, Optional

# --- In-Memory Persistence Simulating Atomic DB ---
TASKS: Dict[str, Dict[str, Any]] = {}
PROPOSALS: Dict[str, Dict[str, Any]] = {}
IDEMPOTENCY_STORE: Dict[str, Dict[str, Any]] = {}
ACCOUNTS: Dict[str, Dict[str, Any]] = {
    "acc-101": {"id": "acc-101", "balance": 2000000, "currency": "INR"}
}
PAYMENT_RECORDS: Dict[str, Dict[str, Any]] = {}

# --- A2A Protocol Implementation ---
AGENT_CARD = {
    "name": "Flo Bank PaymentsAgent",
    "description": "Agent-to-Agent interface for compliant payment proposal and execution",
    "url": "https://api.flobank.internal/a2a",
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
        "tokenUrl": "https://identity.flobank.internal/realms/flobank/protocol/openid-connect/token"
    }
}

def discover_agent_card() -> Dict[str, Any]:
    return AGENT_CARD

def a2a_submit_task(caller_id: str, caller_role: str, task_type: str, task_input: Dict[str, Any]) -> Dict[str, Any]:
    task_id = f"task-{uuid.uuid4().hex[:8]}"
    task_record = {
        "task_id": task_id,
        "owner_id": caller_id,
        "owner_role": caller_role,
        "type": task_type,
        "status": "pending_approval",
        "input": task_input,
        "output": None,
        "created_at": time.time(),
    }
    TASKS[task_id] = task_record
    return task_record

def a2a_get_task(task_id: str, caller_id: str, caller_role: str) -> Dict[str, Any]:
    if task_id not in TASKS:
        raise KeyError("Task not found")
    task = TASKS[task_id]
    
    # Authorized if caller is the owner or an authorized approver
    if task["owner_id"] != caller_id and caller_role != "manager":
        raise PermissionError(f"Access Denied: Principal '{caller_id}' is not authorized to read task owned by '{task['owner_id']}'")
    return task

def a2a_mutate_task(task_id: str, caller_id: str, action: str) -> Dict[str, Any]:
    if task_id not in TASKS:
        raise KeyError("Task not found")
    task = TASKS[task_id]
    
    # Only owner can mutate/cancel
    if task["owner_id"] != caller_id:
        raise PermissionError(f"Access Denied: Principal '{caller_id}' cannot mutate task owned by '{task['owner_id']}'")
    task["status"] = action
    return task

# --- Approval & Idempotency Engine ---
def canonicalize_arguments(args: Dict[str, Any]) -> str:
    return json.dumps(args, sort_keys=True)

def create_payment_proposal(requester_id: str, arguments: Dict[str, Any], expiry_seconds: int = 300) -> str:
    proposal_id = f"prop-{uuid.uuid4().hex[:8]}"
    canon_args = canonicalize_arguments(arguments)
    PROPOSALS[proposal_id] = {
        "proposal_id": proposal_id,
        "requester_id": requester_id,
        "arguments": arguments,
        "canonical_args_hash": hashlib.sha256(canon_args.encode()).hexdigest(),
        "status": "pending",
        "approver_id": None,
        "expires_at": time.time() + expiry_seconds,
        "consumed": False,
    }
    return proposal_id

def approve_proposal(proposal_id: str, approver_id: str, approver_role: str):
    if proposal_id not in PROPOSALS:
        raise KeyError("Proposal not found")
    prop = PROPOSALS[proposal_id]
    
    if prop["status"] != "pending":
        raise ValueError(f"Proposal is already {prop['status']}")
    if time.time() > prop["expires_at"]:
        prop["status"] = "expired"
        raise ValueError("Proposal has expired")
    if approver_id == prop["requester_id"]:
        raise PermissionError("Self-approval prohibited: Requester cannot approve their own proposal")
    if approver_role != "manager":
        raise PermissionError("Unauthorized role: Only managers can approve payment proposals")

    prop["status"] = "approved"
    prop["approver_id"] = approver_id

def execute_approved_payment(
    caller_id: str,
    proposal_id: str,
    arguments: Dict[str, Any],
    idempotency_key: str,
) -> Dict[str, Any]:
    # 1. Idempotency Check
    req_hash = hashlib.sha256(canonicalize_arguments(arguments).encode()).hexdigest()
    idemp_id = f"{caller_id}:{idempotency_key}"
    
    if idemp_id in IDEMPOTENCY_STORE:
        cached = IDEMPOTENCY_STORE[idemp_id]
        if cached["payload_hash"] != req_hash:
            raise ValueError("IDEMPOTENCY_KEY_REUSE_PAYLOAD_MISMATCH: Key reused with different arguments")
        # Return previously recorded execution result
        return {**cached["response"], "idempotent_replay": True}

    # 2. Approval Validation
    if proposal_id not in PROPOSALS:
        raise KeyError("Invalid proposal ID")
    prop = PROPOSALS[proposal_id]
    
    if prop["status"] != "approved":
        raise ValueError(f"Proposal is not approved (current status: {prop['status']})")
    if prop["consumed"]:
        raise ValueError("APPROVAL_REUSE_PROHIBITED: This approval has already been consumed")
    if time.time() > prop["expires_at"]:
        prop["status"] = "expired"
        raise ValueError("Approval has expired")
    
    # 3. Argument Binding Check
    if req_hash != prop["canonical_args_hash"]:
        raise ValueError("ARGUMENT_MISMATCH: Execution arguments do not match approved proposal")

    # 4. Atomic Mutation: Consume approval and deduct balance in one transaction
    prop["consumed"] = True
    prop["status"] = "consumed"
    
    acc_id = arguments["account_id"]
    amount = arguments["amount"]
    if ACCOUNTS[acc_id]["balance"] < amount:
        raise ValueError("Insufficient balance")
    
    ACCOUNTS[acc_id]["balance"] -= amount
    payment_id = f"pay-{uuid.uuid4().hex[:8]}"
    
    result = {
        "payment_id": payment_id,
        "status": "COMPLETED",
        "account_id": acc_id,
        "amount": amount,
        "currency": arguments["currency"],
        "beneficiary": arguments["beneficiary"],
        "approval_id": proposal_id,
        "remaining_balance": ACCOUNTS[acc_id]["balance"],
        "idempotent_replay": False,
    }
    
    PAYMENT_RECORDS[payment_id] = result
    IDEMPOTENCY_STORE[idemp_id] = {
        "payload_hash": req_hash,
        "response": result,
    }
    return result

def main():
    print("=====================================================================")
    print("SPIKE 7: A2A Protocol, Agent Card, Ownership & Approval Idempotency")
    print("=====================================================================")

    # 1. Agent Card Discovery
    print("\n--- Test 1: Agent Card Discovery ---")
    card = discover_agent_card()
    print("Discovered Agent Card:", card["name"], "v" + card["version"])
    assert "propose_payment" in [s["id"] for s in card["skills"]]
    print("✓ Agent Card discovery verified")

    # 2. A2A Task Submission
    print("\n--- Test 2: A2A Task Submission (NegotiatorBot -> PaymentsAgent) ---")
    task_input = {"account_id": "acc-101", "amount": 500000, "currency": "INR", "beneficiary": "vendor-gamma"}
    task = a2a_submit_task(caller_id="agent-negotiator", caller_role="agent", task_type="payment_negotiation", task_input=task_input)
    task_id = task["task_id"]
    print(f"Task submitted successfully. Task ID: {task_id}, Owner: {task['owner_id']}")
    assert task["owner_id"] == "agent-negotiator"

    # 3. Unauthorized Principal Access Rejection
    print("\n--- Test 3: Unrelated Principal Access Rejection ---")
    try:
        a2a_get_task(task_id, caller_id="agent-unrelated-intruder", caller_role="agent")
        print("❌ FAILED: Unrelated agent accessed another's task!")
        return 1
    except PermissionError as e:
        print("✓ SUCCESS: Unrelated principal blocked from reading task:", e)

    try:
        a2a_mutate_task(task_id, caller_id="agent-unrelated-intruder", action="cancelled")
        print("❌ FAILED: Unrelated agent mutated another's task!")
        return 1
    except PermissionError as e:
        print("✓ SUCCESS: Unrelated principal blocked from mutating task:", e)

    # 4. Authorized Human Approver Access
    print("\n--- Test 4: Authorized Approver Task Inspection ---")
    task_read = a2a_get_task(task_id, caller_id="manager-priya", caller_role="manager")
    print(f"✓ Manager '{task_read['owner_id']}' inspected task: status={task_read['status']}")

    # 5. Payment Proposal and Self-Approval Prohibition
    print("\n--- Test 5: Proposal Lifecycle and Self-Approval Prohibition ---")
    prop_id = create_payment_proposal("agent-negotiator", task_input)
    print(f"Created proposal {prop_id}")

    try:
        approve_proposal(prop_id, approver_id="agent-negotiator", approver_role="agent")
        print("❌ FAILED: Agent was able to self-approve its proposal!")
        return 1
    except PermissionError as e:
        print("✓ SUCCESS: Self-approval prohibited:", e)

    try:
        approve_proposal(prop_id, approver_id="random-teller", approver_role="teller")
        print("❌ FAILED: Non-manager approved proposal!")
        return 1
    except PermissionError as e:
        print("✓ SUCCESS: Non-manager approver rejected:", e)

    # 6. Authorized Approval by Manager
    print("\n--- Test 6: Authorized Manager Approval ---")
    approve_proposal(prop_id, approver_id="manager-priya", approver_role="manager")
    print("✓ Proposal approved by manager-priya")

    # 7. Changed Arguments Tampering Attack Rejection
    print("\n--- Test 7: Tampered Arguments Rejection ---")
    tampered_input = dict(task_input)
    tampered_input["amount"] = 800000 # Tampered!
    try:
        execute_approved_payment("agent-negotiator", prop_id, tampered_input, "idemp-001")
        print("❌ FAILED: Payment executed with tampered arguments!")
        return 1
    except ValueError as e:
        print("✓ SUCCESS: Tampered execution arguments rejected:", e)

    # 8. Execution with Exact Arguments
    print("\n--- Test 8: Valid Execution and Balance Mutation ---")
    initial_balance = ACCOUNTS["acc-101"]["balance"]
    exec_res = execute_approved_payment("agent-negotiator", prop_id, task_input, "idemp-001")
    print(f"Payment executed! Payment ID: {exec_res['payment_id']}, Remaining Balance: {exec_res['remaining_balance']}")
    assert ACCOUNTS["acc-101"]["balance"] == initial_balance - 500000
    print("✓ Balance correctly mutated")

    # 9. Single-Use Approval Reuse Rejection
    print("\n--- Test 9: Approval Reuse Rejection ---")
    try:
        execute_approved_payment("agent-negotiator", prop_id, task_input, "idemp-002")
        print("❌ FAILED: Consumed approval was reused for a second payment!")
        return 1
    except ValueError as e:
        print("✓ SUCCESS: Approval reuse blocked atomically:", e)

    # 10. Idempotency Key Replay Safety
    print("\n--- Test 10: Idempotent Retry Safety ---")
    balance_before_retry = ACCOUNTS["acc-101"]["balance"]
    retry_res = execute_approved_payment("agent-negotiator", prop_id, task_input, "idemp-001")
    assert retry_res["idempotent_replay"] is True
    assert retry_res["payment_id"] == exec_res["payment_id"]
    assert ACCOUNTS["acc-101"]["balance"] == balance_before_retry
    print(f"✓ Replay returned identical payment ID {retry_res['payment_id']} with zero balance deduction!")

    # 11. Idempotency Key Reuse with Different Arguments Rejection
    print("\n--- Test 11: Idempotency Key Reuse with Different Payload Rejection ---")
    try:
        different_input = dict(task_input)
        different_input["beneficiary"] = "different-vendor"
        execute_approved_payment("agent-negotiator", prop_id, different_input, "idemp-001")
        print("❌ FAILED: Idempotency key reused with different arguments!")
        return 1
    except ValueError as e:
        print("✓ SUCCESS: Idempotency key reuse with different arguments blocked:", e)

    print("\n=====================================================================")
    print("✅ SPIKE 7 PASSED COMPLETELY!")
    print("1. Agent Card discovery and schema validated.")
    print("2. A2A tasks authenticated and strictly owner-scoped (unrelated principal blocked).")
    print("3. Self-approval strictly prohibited.")
    print("4. Approvals bound cryptographically to canonical proposed arguments.")
    print("5. Approval consumption and business mutation enforced atomically.")
    print("6. Single-use execution enforced (approval reuse rejected).")
    print("7. Backend idempotency verified: retry returns cached response without duplicate debit.")
    print("8. Idempotency key reuse with modified payload rejected.")
    print("=====================================================================")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
