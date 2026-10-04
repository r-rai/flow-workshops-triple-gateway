#!/usr/bin/env python3
import sys
import json
import httpx

GATEWAY_URL = "http://127.0.0.1:9080"
MCP_ENDPOINT = f"{GATEWAY_URL}/mcp"
if "--curated" in sys.argv:
    MCP_ENDPOINT = f"{GATEWAY_URL}/mcp/curated"
    sys.argv.remove("--curated")

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

def send_mcp(method: str, params: dict = None, headers: dict = None):
    req_headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }
    if headers:
        req_headers.update(headers)
    
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params or {}
    }
    with httpx.Client(timeout=10.0) as client:
        r = client.post(MCP_ENDPOINT, headers=req_headers, json=payload)
        return r.status_code, parse_sse(r.text)

def main():
    if len(sys.argv) < 2:
        print("Usage: python client.py [--curated] <init|list|call-account [id]|call-unauthorized|call-payment>")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "init":
        print(f"Connecting to APISIX MCP Gateway at {MCP_ENDPOINT}...")
        status, data = send_mcp("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "w1-participant-cli", "version": "1.0"}
        })
        print(f"Status: {status}")
        print(json.dumps(data, indent=2))

    elif cmd == "list":
        print(f"Discovering exposed tools via MCP tools/list...")
        status, data = send_mcp("tools/list")
        print(f"Status: {status}")
        tools = data.get("result", {}).get("tools", [])
        print(f"Discovered {len(tools)} tools:")
        for t in tools:
            print(f"  - {t['name']}: {t.get('description', '')}")

    elif cmd == "call-account":
        acc_id = sys.argv[2] if len(sys.argv) > 2 else "acc-101"
        print(f"Calling account read tool for ID '{acc_id}' with valid Gate 3 key...")
        # Check tool name from list
        status, ldata = send_mcp("tools/list")
        tools = ldata.get("result", {}).get("tools", [])
        tool_name = next((t["name"] for t in tools if "account" in t["name"].lower()), "get_account")

        status, data = send_mcp(
            "tools/call",
            {"name": tool_name, "arguments": {"pathParameters": {"id": acc_id}}},
            headers={"X-API-Key": "gate3-secret-token"}
        )
        print(f"Status: {status}")
        print(json.dumps(data, indent=2))

    elif cmd == "call-unauthorized":
        print("Calling account read tool WITHOUT valid Gate 3 key...")
        status, ldata = send_mcp("tools/list")
        tools = ldata.get("result", {}).get("tools", [])
        tool_name = next((t["name"] for t in tools if "account" in t["name"].lower()), "get_account")

        status, data = send_mcp(
            "tools/call",
            {"name": tool_name, "arguments": {"pathParameters": {"id": "acc-101"}}},
            headers={"X-API-Key": "invalid-secret"}
        )
        print(f"Status: {status}")
        print(json.dumps(data, indent=2))

    elif cmd == "call-payment":
        print("Attempting to call payment tool via MCP...")
        status, ldata = send_mcp("tools/list")
        tools = ldata.get("result", {}).get("tools", [])
        tool_name = next((t["name"] for t in tools if "payment" in t["name"].lower()), "create_payment")

        status, data = send_mcp(
            "tools/call",
            {
                "name": tool_name,
                "arguments": {
                    "requestBody": {
                        "account_id": "acc-101",
                        "amount": 500000,
                        "currency": "INR",
                        "beneficiary": "fraud-account-66"
                    }
                }
            },
            headers={"X-API-Key": "gate3-secret-token"}
        )
        print(f"Status: {status}")
        print(json.dumps(data, indent=2))

    else:
        print(f"Unknown command: {cmd}")

if __name__ == "__main__":
    main()
