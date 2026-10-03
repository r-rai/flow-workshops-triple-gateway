import sys
import httpx
from spikes.spike4_identity.test_spike4 import issue_token

def main():
    print("=== Running Profile w4 Verification Smoke Test ===")
    base_url = "http://127.0.0.1:9080"

    with httpx.Client(timeout=10.0) as client:
        # Gate 1 Replay
        r_ai = client.post(
            f"{base_url}/ai/chat/completions",
            json={"messages": [{"role": "user", "content": "Negotiate settlement for acc-101"}]}
        )
        assert r_ai.status_code == 200
        print("✓ Gate 1 AI Replay OK")

        # Gate 2 MCP tools
        r_tools = client.post(
            f"{base_url}/mcp",
            json={"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
        )
        assert r_tools.status_code == 200
        print("✓ Gate 2 MCP tools discovery OK")

        # Gate 3 API direct authorization
        token = issue_token("auditor-01", audience="novabank-api", scopes=["api:accounts:read"], role="auditor")
        r_acc = client.get(f"{base_url}/api/v1/accounts/acc-101", headers={"Authorization": f"Bearer {token}"})
        assert r_acc.status_code == 200
        print("✓ Gate 3 API token validation OK:", r_acc.json()["name"])

    print("=== Profile w4 Verification Complete: ALL CHECKS PASSED ===")
    return 0

if __name__ == "__main__":
    sys.exit(main())
