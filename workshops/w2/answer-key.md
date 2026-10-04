# Workshop 2 Answer Key & Facilitator Guide

## 📋 Quick Diagnostic & Verification
Run the verification check at any time to validate the environment:
```bash
./scripts/workshop verify w2
```

To run the complete automated 45-minute rehearsal simulation:
```bash
.venv/bin/python workshops/w2/rehearsal_w2.py
```

---

## 🔑 Exercise Solutions & Policy Formulations

### Exercise 1: Defeating Prompt Injections via Gate 2 OPA Policy
In `workshops/w2/checkpoints/initial/policy-broad.rego`, OPA only checks coarse tool names:
```rego
# INSECURE INITIAL CHECKPOINT
package flobank.policy

default allow = false

allow if {
    input.tool != ""
}
```
**Fix (Hardened Rego)** in `workshops/w2/checkpoints/completed/policy-hardened.rego`:
```rego
package flobank.policy

import future.keywords.if
import future.keywords.in

default decision = "deny"
default reason = "NO_MATCHING_POLICY"

decision := "deny" if {
    input.tool == "create_payment"
    input.arguments.destination_account == "fraud-account-66"
}
reason := "PROHIBITED_BENEFICIARY" if {
    input.tool == "create_payment"
    input.arguments.destination_account == "fraud-account-66"
}
```

---

### Exercise 2: Implementing Three-Tier Risk Thresholds

```rego
# Low tier: Allow under INR 500 (50,000 minor units)
decision := "allow" if {
    input.tool == "create_payment"
    input.arguments.destination_account != "fraud-account-66"
    input.arguments.amount <= 50000
}
reason := "LOW_RISK_AUTO_APPROVED" if {
    input.tool == "create_payment"
    input.arguments.destination_account != "fraud-account-66"
    input.arguments.amount <= 50000
}

# Medium tier: Approval Required for INR 500 to INR 10,000
decision := "approval_required" if {
    input.tool == "create_payment"
    input.arguments.destination_account != "fraud-account-66"
    input.arguments.amount > 50000
    input.arguments.amount <= 1000000
}
reason := "REQUIRES_HUMAN_APPROVAL" if {
    input.tool == "create_payment"
    input.arguments.destination_account != "fraud-account-66"
    input.arguments.amount > 50000
    input.arguments.amount <= 1000000
}

# High tier: Deny above INR 10,000
decision := "deny" if {
    input.tool == "create_payment"
    input.arguments.amount > 1000000
}
reason := "TRANSACTION_LIMIT_EXCEEDED" if {
    input.tool == "create_payment"
    input.arguments.amount > 1000000
}
```

---

### Exercise 3: Fail-Closed Resiliency Pattern
In adapter code (`src/adapter/server.py`):
```python
try:
    async with httpx.AsyncClient(timeout=1.0) as client:
        resp = await client.post("http://opa:8181/v1/data/flobank/policy", json=policy_input)
        if resp.status_code == 200:
            result = resp.json().get("result", {})
            return result
        else:
            return {"decision": "deny", "reason": "OPA_ERROR_STATUS"}
except Exception:
    # Crucial Fail-Closed guarantee
    return {"decision": "deny", "reason": "POLICY_TIMEOUT_FAIL_CLOSED"}
```

---

## 💡 Facilitator Tips
- Highlight to participants that Gate 1 (Model Guardrails) alone is probabilistic and insufficient against indirect injections hidden in third-party payloads.
- Gate 2 (OPA) provides deterministic policy checks on actual extracted tool arguments before executing side effects.
- Gate 3 (APISIX Gateway) provides transport and cryptographic enforcement (RFC 8693 token exchange, loopback network isolation, rate limits).
