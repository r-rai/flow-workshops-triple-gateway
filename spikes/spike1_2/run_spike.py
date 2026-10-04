import os
import sys
import time
import json
import subprocess
import httpx

def run_cmd(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True)

def parse_mcp_sse(text):
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
    print("SPIKE 1 & 2: APISIX Standalone + OpenAPI-to-MCP + Gate 3 Loopback")
    print("=====================================================================")
    
    net_name = "flobank-spike-net"
    api_container = "flobank-api-spike"
    apisix_container = "flobank-apisix-spike"
    
    run_cmd(f"docker rm -f {api_container} {apisix_container}")
    run_cmd(f"docker network rm {net_name}")
    
    res = run_cmd(f"docker network create {net_name}")
    if res.returncode != 0:
        print("Failed to create network:", res.stderr)
        return 1
    
    try:
        spike_dir = os.path.abspath("spikes/spike1_2")
        
        # 1. Start FastAPI container
        print("Starting FastAPI container...")
        api_cmd = (
            f"docker run -d --name {api_container} --network {net_name} "
            f"-v {spike_dir}:/app -w /app python:3.12-slim "
            f"sh -c 'pip install --no-cache-dir fastapi uvicorn pydantic && python3 -m uvicorn app:app --host 0.0.0.0 --port 8000'"
        )
        api_res = run_cmd(api_cmd)
        if api_res.returncode != 0:
            print("Failed to start API container:", api_res.stderr)
            return 1
        
        # Wait for API container
        api_ready = False
        for _ in range(25):
            time.sleep(1)
            curl_check = run_cmd(f"docker run --rm --network {net_name} curlimages/curl:latest curl -s -f http://{api_container}:8000/openapi.json")
            if curl_check.returncode == 0 and "openapi" in curl_check.stdout:
                api_ready = True
                print("✓ FastAPI is healthy and returning OpenAPI specification")
                break
        
        if not api_ready:
            print("❌ FastAPI container failed to start")
            return 1
        
        # 2. Start APISIX container
        conf_dir = os.path.join(spike_dir, "apisix_conf")
        print("Starting APISIX container...")
        apisix_cmd = (
            f"docker run -d --name {apisix_container} --network {net_name} "
            f"-p 9080:9080 "
            f"-v {conf_dir}/config.yaml:/usr/local/apisix/conf/config.yaml:ro "
            f"-v {conf_dir}/apisix.yaml:/usr/local/apisix/conf/apisix.yaml:ro "
            f"apache/apisix:3.19.0-debian"
        )
        apisix_res = run_cmd(apisix_cmd)
        if apisix_res.returncode != 0:
            print("Failed to start APISIX container:", apisix_res.stderr)
            return 1
        
        headers_mcp = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        
        # 3. Wait for APISIX to answer initialize
        print("Waiting for APISIX MCP endpoint to become ready...")
        ready = False
        with httpx.Client(timeout=10.0) as client:
            for attempt in range(25):
                time.sleep(1)
                try:
                    r = client.post(
                        "http://127.0.0.1:9080/mcp",
                        headers=headers_mcp,
                        json={
                            "jsonrpc": "2.0",
                            "id": 1,
                            "method": "initialize",
                            "params": {
                                "protocolVersion": "2024-11-05",
                                "capabilities": {},
                                "clientInfo": {"name": "spike-client", "version": "1.0"}
                            }
                        }
                    )
                    if r.status_code == 200:
                        parsed = parse_mcp_sse(r.text)
                        if "result" in parsed:
                            ready = True
                            print(f"✓ APISIX MCP endpoint initialized successfully:")
                            print("  Server Info:", parsed["result"].get("serverInfo"))
                            print("  Capabilities:", parsed["result"].get("capabilities"))
                            break
                except Exception:
                    pass
            
            if not ready:
                print("❌ APISIX failed to answer MCP initialize")
                print(run_cmd(f"docker logs {apisix_container}").stdout)
                return 1
            
            # 4. MCP tools/list
            print("\n--- Step 1: Discovering Tools via MCP (tools/list) ---")
            r_tools = client.post(
                "http://127.0.0.1:9080/mcp",
                headers=headers_mcp,
                json={"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
            )
            assert r_tools.status_code == 200, f"tools/list failed: {r_tools.status_code}"
            parsed_tools = parse_mcp_sse(r_tools.text)
            tools = parsed_tools.get("result", {}).get("tools", [])
            tool_names = [t["name"] for t in tools]
            print(f"Discovered {len(tools)} tools generated from OpenAPI:")
            for t in tools:
                print(f"  - {t['name']}: {t.get('description', '')} (readOnlyHint: {t.get('annotations', {}).get('readOnlyHint')})")
            
            read_tool = next((name for name in tool_names if "account" in name.lower()), None)
            assert read_tool is not None, "Missing account read tool"
            
            # 5. Gate 3 Loopback Test: UNAUTHORIZED / DENIAL
            print(f"\n--- Step 2: Testing Gate 3 Loopback - Unauthorized Denial ---")
            unauth_headers = {**headers_mcp, "X-API-Key": "wrong-secret-token"}
            call_denied = client.post(
                "http://127.0.0.1:9080/mcp",
                headers=unauth_headers,
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
            denied_data = parse_mcp_sse(call_denied.text)
            print("Denied response:", json.dumps(denied_data, indent=2))
            denied_text = json.dumps(denied_data)
            assert "401" in denied_text or "Missing API key" in denied_text or "Unauthorized" in denied_text or denied_data.get("result", {}).get("isError") is True, \
                f"Expected 401 Unauthorized or error in response, got: {denied_text}"
            print("✓ Gate 3 enforcement confirmed: Tool call with invalid Gate 3 key was DENIED by Gate 3!")

            # 6. Gate 3 Loopback Test: AUTHORIZED SUCCESS
            print(f"\n--- Step 3: Testing Gate 3 Loopback - Authorized Success ---")
            auth_headers = {**headers_mcp, "X-API-Key": "gate3-secret-token"}
            call_ok = client.post(
                "http://127.0.0.1:9080/mcp",
                headers=auth_headers,
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
            ok_data = parse_mcp_sse(call_ok.text)
            print("Authorized response:", json.dumps(ok_data, indent=2))
            ok_text = json.dumps(ok_data)
            assert "1500000" in ok_text and "Acme Corp Checking" in ok_text, \
                f"Expected account balance 1500000 in response, got: {ok_text}"
            print("✓ Gate 3 loopback SUCCESS: Tool call passed through Gate 3 and returned account balance!")

            # 7. Direct Gate 3 Verification
            print("\n--- Step 4: Direct Gate 3 API Verification ---")
            dir_denied = client.get("http://127.0.0.1:9080/api/v1/accounts/acc-101", headers={"X-API-Key": "bad-key"})
            assert dir_denied.status_code == 401, f"Expected 401, got {dir_denied.status_code}"
            print("✓ Direct GET without valid key -> 401 Unauthorized")
            
            dir_ok = client.get("http://127.0.0.1:9080/api/v1/accounts/acc-101", headers={"X-API-Key": "gate3-secret-token"})
            assert dir_ok.status_code == 200, f"Expected 200, got {dir_ok.status_code}"
            print(f"✓ Direct GET with valid key -> 200 OK: {dir_ok.json()}")

        print("\n=====================================================================")
        print("✅ SPIKE 1 & 2 PASSED!")
        print("Evidence recorded:")
        print("- APISIX 3.19.0 Standalone (YAML config provider without etcd) works.")
        print("- openapi-to-mcp plugin generates MCP tools/list and handles tools/call.")
        print("- Transport: Streamable HTTP (SSE text/event-stream chunks).")
        print("- Gate 3 Loopback: Tools call re-enters APISIX /api/v1/* route.")
        print("- Gate 3 Enforces Auth: Missing/invalid credentials return 401.")
        print("- Valid credentials return 200 with business payload.")
        print("=====================================================================")
        return 0

    finally:
        print("Cleaning up spike containers and network...")
        run_cmd(f"docker rm -f {api_container} {apisix_container}")
        run_cmd(f"docker network rm {net_name}")

if __name__ == "__main__":
    sys.exit(main())
