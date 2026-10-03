# Workshop 4 Answer Key & Facilitator Guide

## 📋 Verification & Rehearsal
```bash
# Smoke test
./scripts/workshop verify w4

# Automated 135-minute rehearsal simulation
.venv/bin/python workshops/w4/rehearsal_w4.py
```

---

## 🔑 Key Security Invariants & Solutions

### 1. Anti-Self-Approval Implementation
In `src/services/approvals.py`:
```python
if principal.id == prop.requester_id:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Self-approval prohibited: Requester cannot approve their own proposal",
    )
```

### 2. Exact Argument Binding via Canonical Hash
```python
# During proposal creation:
args_hash = canonical_hash({"account_id": req.account_id, "amount": req.amount, ...})
proposal.canonical_args_hash = args_hash

# During execution:
req_hash = canonical_hash({"account_id": req.account_id, "amount": req.amount, ...})
if prop.canonical_args_hash != req_hash:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Execution arguments do not match the approved proposal arguments",
    )
```

### 3. Atomic Single-Use Approval Consumption
```python
# In transaction with FOR UPDATE lock:
if prop.status != "approved":
    raise HTTPException(400, "Proposal is not approved")
prop.status = "consumed"
prop.consumed_at = time.time()
db.commit()
```

### 4. A2A Owner-Scoped Task Access
In `src/api/routes/a2a.py`:
```python
task = A2A_TASKS[task_id]
if principal.id != task["owner_id"] and principal.role != "admin":
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=f"Access denied: caller '{principal.id}' does not own task '{task_id}'"
    )
```

---

## 💡 Facilitator Notes
- Emphasize to participants that **Triple-Gate** is not three copies of the same firewall; it is three conceptually distinct boundaries:
  - **Gate 1 (Semantic)**: Model access, rate limits, and replay fallback.
  - **Gate 2 (Capability)**: Policy engine evaluating tool intent and arguments before external dispatch.
  - **Gate 3 (Cryptographic & Transport)**: API Gateway enforcing RFC 8693 token exchange, audience bounds, downscoped scopes, and loopback isolation.
- Walk participants through the Jaeger UI at `http://<vps-ip>:16686` to show how a single `traceparent` header links all five layers (Client -> Adapter -> OPA -> APISIX -> API).
