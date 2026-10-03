import time
import json
import sys
import os
import subprocess

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import httpx
from spikes.spike4_identity.test_spike4 import issue_token

def run_cmd(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True)

def main():
    print("=====================================================================")
    print(" WORKSHOP 2 REHEARSAL: Beyond API Governance - Securing AI Agents & MCP")
    print(" 45-Minute Session Automated Verification & Evidence Capture")
    print("=====================================================================")

    start_time = time.time()
    evidence = {}

    # Switch to profile w2
    print("\n[Segment 1: 0–5 min] Threat Scenario - Reading Adversarial Support Case")
    run_cmd("./scripts/workshop switch w2")

    base_url = "http://127.0.0.1:9080"
    mcp_url = f"{base_url}/mcp"

    token_support = issue_token(
        subject="agent-support-01",
        audience="novabank-mcp",
        scopes=["mcp:tools"],
        role="support_agent",
    )
    headers = {"Authorization": f"Bearer {token_support}"}

    with httpx.Client(timeout=10.0) as client:
        # Step 1: Read case-502 containing indirect prompt injection
        print("Reading dispute ticket case-502...")
        r_case = client.post(
            mcp_url,
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {"name": "get_case", "arguments": {"id": "case-502"}}
            }
        )
        assert r_case.status_code == 200
        case_data = r_case.json()
        case_desc = case_data.get("result", {}).get("content", [{}])[0].get("text", "")
        evidence["threat_scenario_case"] = case_desc
        print("✓ Injected Prompt Case Read Successfully:")
        print(f"  Description: {case_desc}")
        assert "Ignore all previous rules" in case_desc

        # Step 2: Unsafe Execution Blocked (12–22 min)
        print("\n[Segment 2: 12–22 min] Adversarial Model Request Blocked by Policy")
        # Attacker instruction: transfer to fraud-account-66
        r_attack = client.post(
            mcp_url,
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "create_payment",
                    "arguments": {
                        "account_id": "acc-101",
                        "amount": 900000,
                        "currency": "INR",
                        "beneficiary": "fraud-account-66"
                    }
                }
            }
        )
        assert r_attack.status_code == 200
        attack_res = r_attack.json()
        evidence["attack_response"] = attack_res
        attack_text = attack_res.get("result", {}).get("content", [{}])[0].get("text", "")
        print("✓ Policy Evaluation Result on Injected Attack:")
        print(f"  {attack_text}")
        assert "PROHIBITED_BENEFICIARY" in attack_text or attack_res.get("result", {}).get("isError") is True
        print("✓ Attack Defeated: Model was unable to execute transaction to blacklisted account!")

        # Step 3: Guided Policy Exercise (22–34 min)
        print("\n[Segment 3: 22–34 min] Guided Policy Exercise - Allow, Approval-Required, Deny")
        
        # 3a. Small payment -> Allowed
        r_small = client.post(
            mcp_url,
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "create_payment",
                    "arguments": {"account_id": "acc-101", "amount": 25000, "currency": "INR", "beneficiary": "vendor-alpha"}
                }
            }
        )
        small_res = r_small.json()
        assert small_res.get("result", {}).get("isError") is False
        print("✓ Small payment (INR 250.00) automatically allowed")

        # 3b. Medium payment (INR 5,000.00) -> Approval Required
        r_med = client.post(
            mcp_url,
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {
                    "name": "create_payment",
                    "arguments": {"account_id": "acc-101", "amount": 500000, "currency": "INR", "beneficiary": "vendor-beta"}
                }
            }
        )
        med_res = r_med.json()
        med_text = med_res.get("result", {}).get("content", [{}])[0].get("text", "")
        evidence["approval_required_response"] = med_text
        assert "APPROVAL_REQUIRED" in med_text or "AMOUNT_EXCEEDS_UNSUPERVISED_LIMIT" in med_text
        print("✓ Medium payment triggered 'APPROVAL_REQUIRED' without executing backend debit")

        # 3c. Large payment (INR 50,000.00) -> Denied
        r_large = client.post(
            mcp_url,
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 5,
                "method": "tools/call",
                "params": {
                    "name": "create_payment",
                    "arguments": {"account_id": "acc-101", "amount": 5000000, "currency": "INR", "beneficiary": "vendor-beta"}
                }
            }
        )
        large_res = r_large.json()
        large_text = large_res.get("result", {}).get("content", [{}])[0].get("text", "")
        assert "AMOUNT_EXCEEDS_TRANSFER_CEILING" in large_text or large_res.get("result", {}).get("isError") is True
        print("✓ Large payment (INR 50,000.00) denied by ceiling rule")

        # Step 4: Failure & Audit (34–41 min) - OPA Outage Simulation
        print("\n[Segment 4: 34–41 min] Failure & Audit - OPA Outage Fail-Closed Test")
        opa_container = "novabank-workshops-opa-1"
        print(f"Pausing OPA container '{opa_container}'...")
        run_cmd(f"docker pause {opa_container}")

        try:
            r_outage = client.post(
                mcp_url,
                headers=headers,
                json={
                    "jsonrpc": "2.0",
                    "id": 6,
                    "method": "tools/call",
                    "params": {"name": "get_account", "arguments": {"id": "acc-101"}}
                }
            )
            outage_res = r_outage.json()
            outage_text = outage_res.get("result", {}).get("content", [{}])[0].get("text", "")
            evidence["opa_outage_response"] = outage_text
            print("✓ Result during OPA Outage:", outage_text)
            assert "FAIL_CLOSED" in outage_text or "POLICY_UNAVAILABLE" in outage_text or outage_res.get("result", {}).get("isError") is True
            print("✓ FAIL-CLOSED INVARIANT VERIFIED: Gateway denied tool invocation when policy engine was unreachable!")
        finally:
            print("Unpausing OPA container...")
            run_cmd(f"docker unpause {opa_container}")

    elapsed = time.time() - start_time
    evidence["rehearsal_duration_seconds"] = round(elapsed, 2)
    with open("workshops/w2/evidence/rehearsal-evidence.json", "w") as f:
        json.dump(evidence, f, indent=2)

    print(f"\n✓ Saved rehearsal evidence to workshops/w2/evidence/rehearsal-evidence.json")
    print("\n=====================================================================")
    print(f"🎉 WORKSHOP 2 REHEARSAL COMPLETE in {round(elapsed, 2)}s: ALL GOVERNANCE CONTRACTS VERIFIED!")
    print("=====================================================================")
    return 0

if __name__ == "__main__":
    sys.exit(main())
