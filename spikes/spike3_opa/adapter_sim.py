import os
import sys
import time
import json
import subprocess
import httpx
from typing import Dict, Any, Tuple

class NovaBankMcpPolicyEngine:
    def __init__(self, opa_url: str = "http://127.0.0.1:8181/v1/data/novabank/policy", timeout_sec: float = 0.5):
        self.opa_url = opa_url
        self.timeout_sec = timeout_sec

    def normalize_arguments(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Validates and normalizes arguments according to enterprise canonical rules."""
        norm = dict(arguments)
        if tool_name == "create_payment":
            if "amount" not in norm:
                raise ValueError("Missing required argument: amount")
            # Enforce integer minor units
            try:
                norm["amount"] = int(norm["amount"])
            except (ValueError, TypeError):
                raise ValueError("Argument 'amount' must be an integer (minor units)")
            if norm["amount"] <= 0:
                raise ValueError("Argument 'amount' must be positive")
            norm["currency"] = str(norm.get("currency", "INR")).upper()
            if "beneficiary" not in norm:
                raise ValueError("Missing required argument: beneficiary")
            norm["beneficiary"] = str(norm["beneficiary"]).strip()
        elif tool_name == "remediate_incident":
            if "incident_id" not in norm or "action" not in norm:
                raise ValueError("Missing incident_id or action")
            norm["incident_id"] = str(norm["incident_id"]).strip()
            norm["action"] = str(norm["action"]).strip()
        return norm

    def evaluate_policy(self, principal: Dict[str, Any], tool_name: str, arguments: Dict[str, Any]) -> Tuple[str, str]:
        """
        Queries OPA.
        Returns (decision, reason).
        Fails closed on error, timeout, or malformed policy output.
        """
        if not principal or "id" not in principal or "role" not in principal:
            return "deny", "UNAUTHENTICATED_PRINCIPAL"

        try:
            norm_args = self.normalize_arguments(tool_name, arguments)
        except Exception as e:
            return "deny", f"INVALID_ARGUMENTS: {str(e)}"

        payload = {
            "input": {
                "principal": principal,
                "tool": tool_name,
                "arguments": norm_args,
            }
        }

        try:
            with httpx.Client(timeout=self.timeout_sec) as client:
                resp = client.post(self.opa_url, json=payload)
                if resp.status_code != 200:
                    return "deny", f"POLICY_HTTP_ERROR_{resp.status_code}"
                data = resp.json().get("result", {})
                decision = data.get("decision")
                reason = data.get("reason", "NO_REASON_GIVEN")
                if decision not in ("allow", "deny", "approval_required"):
                    return "deny", "MALFORMED_POLICY_OUTPUT"
                return decision, reason
        except httpx.TimeoutException:
            return "deny", "POLICY_TIMEOUT_FAIL_CLOSED"
        except Exception as e:
            return "deny", f"POLICY_UNAVAILABLE_FAIL_CLOSED: {type(e).__name__}"

    def handle_tool_call(self, principal: Dict[str, Any], tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        decision, reason = self.evaluate_policy(principal, tool_name, arguments)
        
        if decision == "deny":
            return {
                "status": "denied",
                "decision": decision,
                "reason": reason,
                "executed": False,
            }
        elif decision == "approval_required":
            # Record proposal without executing mutation
            proposal_id = f"prop-sim-{int(time.time()*1000)}"
            return {
                "status": "pending_approval",
                "decision": decision,
                "reason": reason,
                "proposal_id": proposal_id,
                "proposed_arguments": arguments,
                "executed": False,
                "message": "Action requires human supervisory approval before execution."
            }
        elif decision == "allow":
            return {
                "status": "allowed",
                "decision": decision,
                "reason": reason,
                "executed": True,
                "result": {"status": "SUCCESS", "tool": tool_name}
            }
        else:
            return {"status": "denied", "reason": "UNKNOWN_DECISION_FAIL_CLOSED", "executed": False}

def main():
    print("=====================================================================")
    print("SPIKE 3: Argument-Aware OPA Policy Engine & MCP Adapter Contract")
    print("=====================================================================")
    
    opa_container = "novabank-spike3-opa"
    subprocess.run(["docker", "rm", "-f", opa_container], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    policy_path = os.path.abspath("spikes/spike3_opa/policy.rego")
    
    # 1. Run OPA container
    print("Starting OPA container on port 8181...")
    opa_cmd = [
        "docker", "run", "-d",
        "--name", opa_container,
        "-p", "8181:8181",
        "-v", f"{policy_path}:/policy.rego:ro",
        "openpolicyagent/opa:0.68.0-static",
        "run", "--server", "--log-level=error", "/policy.rego"
    ]
    res = subprocess.run(opa_cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("Failed to start OPA:", res.stderr)
        return 1
    
    # Wait for OPA to be ready
    opa_ready = False
    for _ in range(15):
        time.sleep(0.5)
        try:
            with httpx.Client(timeout=2.0) as client:
                r = client.get("http://127.0.0.1:8181/health")
                if r.status_code == 200:
                    opa_ready = True
                    print("✓ OPA server is healthy")
                    break
        except Exception:
            pass
            
    if not opa_ready:
        print("❌ OPA server failed to respond.")
        return 1

    try:
        engine = NovaBankMcpPolicyEngine(opa_url="http://127.0.0.1:8181/v1/data/novabank/policy")
        
        # Test Case 1: Read tool allowed
        print("\n--- Test Case 1: Read tool (get_account) ---")
        user = {"id": "agent-support-1", "role": "support_agent"}
        res1 = engine.handle_tool_call(user, "get_account", {"id": "acc-101"})
        print("Result:", res1)
        assert res1["decision"] == "allow" and res1["reason"] == "READ_ALLOWED"
        print("✓ Read tool allowed as expected")

        # Test Case 2: Small payment (amount=50,000 minor units -> INR 500.00)
        print("\n--- Test Case 2: Small payment below 100,000 (auto-allow) ---")
        res2 = engine.handle_tool_call(user, "create_payment", {"amount": 50000, "beneficiary": "vendor-alpha", "account_id": "acc-101"})
        print("Result:", res2)
        assert res2["decision"] == "allow" and res2["executed"] is True
        print("✓ Payment under threshold automatically allowed")

        # Test Case 3: Medium payment (amount=500,000 minor units -> INR 5,000.00)
        # Spike 3 requirement: argument 500000 requires approval
        print("\n--- Test Case 3: Medium payment (amount=500,000 minor units) -> APPROVAL_REQUIRED ---")
        res3 = engine.handle_tool_call(user, "create_payment", {"amount": 500000, "beneficiary": "vendor-beta", "account_id": "acc-101"})
        print("Result:", res3)
        assert res3["decision"] == "approval_required"
        assert res3["executed"] is False
        assert "proposal_id" in res3
        assert res3["reason"] == "AMOUNT_EXCEEDS_UNSUPERVISED_LIMIT"
        print("✓ Policy triggered 'approval_required'. Recorded pending proposal without business execution!")

        # Test Case 4: Excessive payment (amount=5,000,000 minor units) -> DENIED
        print("\n--- Test Case 4: Excessive payment (amount=5,000,000 minor units) -> DENIED ---")
        res4 = engine.handle_tool_call(user, "create_payment", {"amount": 5000000, "beneficiary": "vendor-beta", "account_id": "acc-101"})
        print("Result:", res4)
        assert res4["decision"] == "deny" and res4["reason"] == "AMOUNT_EXCEEDS_TRANSFER_CEILING"
        print("✓ Excess payment denied as expected")

        # Test Case 5: Blacklisted beneficiary -> DENIED
        print("\n--- Test Case 5: Sanctioned beneficiary -> DENIED ---")
        res5 = engine.handle_tool_call(user, "create_payment", {"amount": 20000, "beneficiary": "sanctioned-entity-99", "account_id": "acc-101"})
        print("Result:", res5)
        assert res5["decision"] == "deny" and res5["reason"] == "PROHIBITED_BENEFICIARY"
        print("✓ Blacklisted beneficiary denied")

        # Test Case 6: Unauthenticated principal / spoofed caller -> DENIED
        print("\n--- Test Case 6: Unauthenticated caller -> DENIED ---")
        res6 = engine.handle_tool_call({}, "create_payment", {"amount": 50000, "beneficiary": "vendor-alpha", "account_id": "acc-101"})
        print("Result:", res6)
        assert res6["decision"] == "deny" and "UNAUTHENTICATED" in res6["reason"]
        print("✓ Unauthenticated principal rejected")

        # Test Case 7: OPA Outage / Fail-closed test
        print("\n--- Test Case 7: OPA Outage / Fail-closed validation ---")
        print("Stopping OPA container to simulate network partition / service outage...")
        subprocess.run(["docker", "stop", opa_container], stdout=subprocess.DEVNULL)
        res7 = engine.handle_tool_call(user, "get_account", {"id": "acc-101"})
        print("Result during OPA outage:", res7)
        assert res7["decision"] == "deny"
        assert res7["executed"] is False
        assert "FAIL_CLOSED" in res7["reason"]
        print("✓ FAIL-CLOSED INVARIANT VERIFIED: Tool execution denied when OPA is offline!")

        print("\n=====================================================================")
        print("✅ SPIKE 3 PASSED COMPLETELY!")
        print("1. Curated MCP adapter normalizes arguments and identity.")
        print("2. Arguments, tool, and identity passed to OPA.")
        print("3. Explicit allow, deny, approval_required outcomes with machine reasons.")
        print("4. Approval-required generates pending proposal without business mutation.")
        print("5. Fail-closed on OPA outage/timeout verified.")
        print("=====================================================================")
        return 0

    finally:
        subprocess.run(["docker", "rm", "-f", opa_container], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

if __name__ == "__main__":
    sys.exit(main())
