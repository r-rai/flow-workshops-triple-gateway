import sys
import json
import httpx

def parse_sse(text):
    for line in text.splitlines():
        if line.startswith("data: "):
            try:
                return json.loads(line[6:].strip())
            except Exception:
                pass
    try:
        return json.loads(text)
    except Exception:
        return {"raw": text}

def main():
    print("=== Running Profile w1 Verification Smoke Test ===")
    headers_mcp = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }
    base_url = "http://127.0.0.1:9080"

    with httpx.Client(timeout=10.0) as client:
        # 1. MCP Initialize
        print("1. Testing MCP Initialize...")
        r_init = client.post(
            f"{base_url}/mcp",
            headers=headers_mcp,
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "test-w1", "version": "1.0"}
                }
            }
        )
        assert r_init.status_code == 200, f"MCP init failed: {r_init.status_code}"
        parsed_init = parse_sse(r_init.text)
        assert "result" in parsed_init, f"Expected result in init, got {parsed_init}"
        print("✓ MCP Initialize passed:", parsed_init["result"]["serverInfo"])

        # 2. MCP Tools List
        print("2. Testing MCP tools/list...")
        r_list = client.post(f"{base_url}/mcp", headers=headers_mcp, json={"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
        assert r_list.status_code == 200
        tools_data = parse_sse(r_list.text)
        tools = tools_data.get("result", {}).get("tools", [])
        tool_names = [t["name"] for t in tools]
        print(f"✓ Discovered {len(tools)} tools: {tool_names}")
        assert any("account" in n.lower() for n in tool_names), "Missing account tool"
        read_tool = next(n for n in tool_names if "account" in n.lower())

        # 3. Gate 3 Loopback - Denial Case
        print("3. Testing Gate 3 Loopback Denial (Invalid key)...")
        r_denied = client.post(
            f"{base_url}/mcp",
            headers={**headers_mcp, "X-API-Key": "invalid-key"},
            json={
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": read_tool,
                    "arguments": {"pathParameters": {"id": "acc-101"}}
                }
            }
        )
        denied_data = parse_sse(r_denied.text)
        denied_str = json.dumps(denied_data)
        assert "401" in denied_str or "Invalid API key" in denied_str or denied_data.get("result", {}).get("isError") is True
        print("✓ Gate 3 Denial passed: Invalid credential was rejected with 401")

        # 4. Gate 3 Loopback - Success Case
        print("4. Testing Gate 3 Loopback Success (Valid key)...")
        r_ok = client.post(
            f"{base_url}/mcp",
            headers={**headers_mcp, "X-API-Key": "gate3-secret-token"},
            json={
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {
                    "name": read_tool,
                    "arguments": {"pathParameters": {"id": "acc-101"}}
                }
            }
        )
        ok_data = parse_sse(r_ok.text)
        ok_str = json.dumps(ok_data)
        assert "1500000" in ok_str and "INR" in ok_str
        print("✓ Gate 3 Success passed: Account balance returned successfully through MCP")

        # 5. Direct Gate 3 API
        print("5. Testing Direct Gate 3 API Route...")
        r_dir_401 = client.get(f"{base_url}/api/v1/accounts/acc-101")
        assert r_dir_401.status_code == 401
        print("✓ Direct call without key rejected with 401")

        r_dir_200 = client.get(f"{base_url}/api/v1/accounts/acc-101", headers={"X-API-Key": "gate3-secret-token"})
        assert r_dir_200.status_code == 200
        print("✓ Direct call with key succeeded with 200:", r_dir_200.json())

    print("=== Profile w1 Verification Complete: ALL CHECKS PASSED ===")
    return 0

if __name__ == "__main__":
    sys.exit(main())
