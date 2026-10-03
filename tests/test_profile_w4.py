import sys
import httpx
from src.core.security import create_jwt_token

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
        token = create_jwt_token("auditor-01", audience="novabank-api", scopes=["api:accounts:read"], role="auditor")
        r_acc = client.get(
            f"{base_url}/api/v1/accounts/acc-101",
            headers={"Authorization": f"Bearer {token}", "X-API-Key": "gate3-secret-token"}
        )
        assert r_acc.status_code == 200
        print("✓ Gate 3 API token validation OK:", r_acc.json()["name"])

        # A2A Agent Card discovery
        r_card = client.get(f"{base_url}/.well-known/agent.json")
        assert r_card.status_code == 200, f"Expected 200 from .well-known, got {r_card.status_code}"
        print("✓ A2A Agent Card Discovery OK:", r_card.json()["name"])

    print("=== Profile w4 Verification Complete: ALL CHECKS PASSED ===")
    return 0

if __name__ == "__main__":
    sys.exit(main())
