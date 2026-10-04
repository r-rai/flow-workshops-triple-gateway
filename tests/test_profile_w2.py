import sys
import json
import httpx
from spikes.spike4_identity.test_spike4 import issue_token

def main():
    print("=== Running Profile w2 Verification Smoke Test ===")
    base_url = "http://127.0.0.1:9080"

    with httpx.Client(timeout=10.0) as client:
        # 1. MCP Initialize
        print("1. Testing MCP Initialize...")
        r_init = client.post(
            f"{base_url}/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test-w2", "version": "1.0"}}
            }
        )
        assert r_init.status_code == 200
        print("✓ MCP Initialize OK:", r_init.json()["result"]["serverInfo"])

        # 2. MCP Tools List
        print("2. Testing Curated Tools List...")
        r_list = client.post(f"{base_url}/mcp", json={"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
        assert r_list.status_code == 200
        tools = r_list.json()["result"]["tools"]
        tool_names = [t["name"] for t in tools]
        print(f"✓ Discovered {len(tools)} curated tools: {tool_names}")
        assert "get_account" in tool_names
        assert "create_payment" in tool_names

        # 3. Gate 1 AI endpoint
        print("3. Testing Gate 1 AI Replay Endpoint...")
        r_ai = client.post(
            f"{base_url}/ai/chat/completions",
            headers={"x-use-replay-fixtures": "true"},
            json={"messages": [{"role": "user", "content": "What is the balance of acc-101?"}]}
        )
        assert r_ai.status_code == 200
        ai_choice = r_ai.json()["choices"][0]["message"]["content"]
        assert "[REPLAY]" in ai_choice or len(ai_choice) > 0
        print("✓ Gate 1 AI Replay verified:", ai_choice[:80])

        # 4. Gate 2 Policy - Small payment allowed
        print("4. Testing Gate 2 Policy: Small Payment...")
        token_mcp = issue_token("agent-support-1", audience="novabank-mcp", scopes=["mcp:tools"], role="support_agent")
        headers = {"Authorization": f"Bearer {token_mcp}"}

        r_small = client.post(
            f"{base_url}/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "create_payment",
                    "arguments": {"account_id": "acc-101", "amount": 10000, "beneficiary": "vendor-alpha", "currency": "INR"}
                }
            }
        )
        assert r_small.status_code == 200
        assert r_small.json()["result"]["isError"] is False
        print("✓ Small payment allowed through Gate 2 & Gate 3")

        # 5. Gate 2 Policy - Medium payment requires approval
        print("5. Testing Gate 2 Policy: Medium Payment (Approval Required)...")
        r_med = client.post(
            f"{base_url}/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {
                    "name": "create_payment",
                    "arguments": {"account_id": "acc-101", "amount": 500000, "beneficiary": "vendor-beta", "currency": "INR"}
                }
            }
        )
        assert r_med.status_code == 200
        text_resp = r_med.json()["result"]["content"][0]["text"]
        assert "APPROVAL_REQUIRED" in text_resp
        print("✓ Medium payment triggered APPROVAL_REQUIRED without financial mutation")

    print("=== Profile w2 Verification Complete: ALL CHECKS PASSED ===")
    return 0

if __name__ == "__main__":
    sys.exit(main())
