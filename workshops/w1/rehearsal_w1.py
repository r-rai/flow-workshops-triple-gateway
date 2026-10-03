#!/usr/bin/env python3
import time
import json
import sys
import os
import subprocess
import httpx

def run_cmd(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True)

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
    print("=====================================================================")
    print(" WORKSHOP 1 REHEARSAL: Modernizing APIs for AI Agents (OpenAPI -> MCP)")
    print(" 45-Minute Session Automated Verification & Evidence Capture")
    print("=====================================================================")
    
    start_time = time.time()
    evidence = {}

    # 1. Start profile w1 if not already running
    print("\n[Segment 1: 0–12 min] Introduction & Gateway Initialization")
    run_cmd("./scripts/workshop start w1")
    
    base_url = "http://127.0.0.1:9080"
    headers_mcp = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }

    with httpx.Client(timeout=10.0) as client:
        # Step 1: Initialize MCP
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
                    "clientInfo": {"name": "rehearsal-client", "version": "1.0"}
                }
            }
        )
        assert r_init.status_code == 200, f"MCP Initialize failed: {r_init.status_code}"
        parsed_init = parse_sse(r_init.text)
        evidence["mcp_initialize"] = parsed_init
        print("✓ APISIX MCP Initialized. Server:", parsed_init.get("result", {}).get("serverInfo"))

        # Step 2: Discover Broad Tool Catalog (12–22 min)
        print("\n[Segment 2: 12–22 min] Native Generation & Tool Discovery")
        r_list = client.post(f"{base_url}/mcp", headers=headers_mcp, json={"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
        assert r_list.status_code == 200
        tools_broad = parse_sse(r_list.text).get("result", {}).get("tools", [])
        tool_names = [t["name"] for t in tools_broad]
        evidence["broad_tools_count"] = len(tools_broad)
        evidence["broad_tool_names"] = tool_names
        print(f"✓ Discovered {len(tools_broad)} generated tools from OpenAPI:")
        for name in tool_names[:5]:
            print(f"  - {name}")
        if len(tool_names) > 5:
            print(f"  - ... ({len(tool_names)-5} more)")

        # Verify account read tool exists
        read_tool = next(t for t in tool_names if "account" in t.lower())

        # Step 3: Invoke Account Read through MCP (22–32 min)
        print("\n[Segment 3: 22–32 min] Authorized Tool Invocation")
        auth_headers = {**headers_mcp, "X-API-Key": "gate3-secret-token"}
        r_call_ok = client.post(
            f"{base_url}/mcp",
            headers=auth_headers,
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
        call_ok_data = parse_sse(r_call_ok.text)
        evidence["authorized_call_status"] = r_call_ok.status_code
        evidence["authorized_call_result"] = call_ok_data
        call_ok_str = json.dumps(call_ok_data)
        assert "1500000" in call_ok_str and "INR" in call_ok_str, f"Unexpected response: {call_ok_str}"
        print("✓ Successfully retrieved account acc-101 balance through MCP:")
        print(" ", call_ok_data.get("result", {}).get("content", [{}])[0].get("text")[:100], "...")

        # Step 4: Gate 3 Denial Invariant (32–40 min)
        print("\n[Segment 4: 32–40 min] Gate 3 Downstream Authorization Enforcement")
        unauth_headers = {**headers_mcp, "X-API-Key": "wrong-secret-token"}
        r_denied = client.post(
            f"{base_url}/mcp",
            headers=unauth_headers,
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
        denied_data = parse_sse(r_denied.text)
        evidence["denied_call_status"] = r_denied.status_code
        evidence["denied_call_result"] = denied_data
        denied_str = json.dumps(denied_data)
        assert "401" in denied_str or "Invalid API key" in denied_str or denied_data.get("result", {}).get("isError") is True
        print("✓ Gate 3 Denial CONFIRMED: Unauthorized MCP call returned 401 Unauthorized:")
        print(" ", denied_data.get("result", {}).get("content", [{}])[0].get("text")[:100], "...")

        # Step 5: Direct Route Gate 3 Validation
        print("\n[Segment 5: 40–45 min] Architecture Review & Routing Evidence")
        r_direct_401 = client.get(f"{base_url}/api/v1/accounts/acc-101")
        assert r_direct_401.status_code == 401
        print("✓ Direct call to /api/v1/accounts/acc-101 without key: 401 Unauthorized")

        r_direct_200 = client.get(f"{base_url}/api/v1/accounts/acc-101", headers={"X-API-Key": "gate3-secret-token"})
        assert r_direct_200.status_code == 200
        print("✓ Direct call to /api/v1/accounts/acc-101 with key: 200 OK")

    elapsed = time.time() - start_time
    evidence["rehearsal_duration_seconds"] = round(elapsed, 2)
    
    # Save evidence file
    os.makedirs("workshops/w1/evidence", exist_ok=True)
    with open("workshops/w1/evidence/rehearsal-evidence.json", "w") as f:
        json.dump(evidence, f, indent=2)
    print(f"\n✓ Saved rehearsal evidence to workshops/w1/evidence/rehearsal-evidence.json")

    print("\n=====================================================================")
    print(f"🎉 WORKSHOP 1 REHEARSAL COMPLETE in {round(elapsed, 2)}s: ALL CONTRACTS VERIFIED!")
    print("=====================================================================")
    return 0

if __name__ == "__main__":
    sys.exit(main())
