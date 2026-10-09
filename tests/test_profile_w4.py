import sys
import json
import subprocess
import httpx


def gate3_headers():
    """Mint a read-only lab token using the running API's configuration."""
    program = """
import json
from src.core.config import settings
from src.core.security import create_jwt_token
token = create_jwt_token(
    "auditor-01", audience=settings.API_AUDIENCE,
    scopes=["api:accounts:read"], role="auditor", expires_in_seconds=300,
)
print(json.dumps({"Authorization": "Bearer " + token,
                 "X-API-Key": settings.API_KEY_SECRET}))
"""
    try:
        result = subprocess.run(
            ["docker", "compose", "exec", "-T", "api", "python", "-c", program],
            capture_output=True, text=True, check=True, timeout=15,
        )
        headers = json.loads(result.stdout)
        if not isinstance(headers, dict) or not all(
            isinstance(headers.get(key), str) and headers[key]
            for key in ("Authorization", "X-API-Key")
        ):
            raise ValueError("Missing verification credentials")
        return headers
    except (OSError, subprocess.SubprocessError, ValueError):
        # Docker output can contain credentials; never include it in errors.
        raise RuntimeError(
            "Cannot obtain verification credentials from the API container. "
            "Run './scripts/workshop status' and ensure the w4 API is healthy."
        ) from None

def main():
    print("=== Running Profile w4 Verification Smoke Test ===")
    base_url = "http://127.0.0.1:9080"
    try:
        headers = gate3_headers()
    except RuntimeError as exc:
        print(f"[ERROR] {exc}")
        return 1

    with httpx.Client(timeout=45.0) as client:
        # Gate 1 Replay / Live completions
        r_ai = client.post(
            f"{base_url}/ai/chat/completions",
            json={"messages": [{"role": "user", "content": "Negotiate settlement for acc-101"}]}
        )
        assert r_ai.status_code == 200, f"Gate 1 failed: HTTP {r_ai.status_code}: {r_ai.text[:500]}"
        print("✓ Gate 1 AI Replay / Inference OK")

        # Gate 2 MCP tools
        r_tools = client.post(
            f"{base_url}/mcp",
            json={"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
        )
        assert r_tools.status_code == 200, f"Gate 2 discovery failed: HTTP {r_tools.status_code}: {r_tools.text[:500]}"
        print("✓ Gate 2 MCP tools discovery OK")

        # Gate 3 API direct authorization
        r_acc = client.get(
            f"{base_url}/api/v1/accounts/acc-101",
            headers=headers,
        )
        assert r_acc.status_code == 200, f"Gate 3 account read failed: HTTP {r_acc.status_code}: {r_acc.text[:500]}"
        print("✓ Gate 3 API token validation OK:", r_acc.json()["name"])

        # A2A Agent Card discovery
        r_card = client.get(f"{base_url}/.well-known/agent.json")
        assert r_card.status_code == 200, f"A2A discovery failed: HTTP {r_card.status_code}: {r_card.text[:500]}"
        print("✓ A2A Agent Card Discovery OK:", r_card.json()["name"])

    print("=== Profile w4 Verification Complete: ALL CHECKS PASSED ===")
    return 0

if __name__ == "__main__":
    sys.exit(main())
