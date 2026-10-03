import os
import json
import time
import httpx
from typing import Dict, Any, Tuple
from fastapi import FastAPI, Request, Response, HTTPException, status
from fastapi.responses import JSONResponse, PlainTextResponse
from jose import jwt, JWTError

OPA_URL = os.getenv("OPA_URL", "http://opa:8181/v1/data/novabank/policy")
GATE3_URL = os.getenv("GATE3_URL", "http://apisix:9080/api/v1")
GATE3_KEY = os.getenv("GATE3_API_KEY", "gate3-secret-token")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "novabank-super-secret-signing-key-for-lab")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ISSUER = os.getenv("JWT_ISSUER", "https://identity.novabank.internal/realms/novabank")
MCP_AUDIENCE = os.getenv("MCP_AUDIENCE", "novabank-mcp")
API_AUDIENCE = os.getenv("API_AUDIENCE", "novabank-api")

app = FastAPI(title="NovaBank Curated MCP Adapter", version="1.0.0")

def normalize_arguments(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    norm = dict(arguments or {})
    if tool_name == "create_payment":
        if "amount" not in norm:
            raise ValueError("Missing required argument 'amount'")
        try:
            norm["amount"] = int(norm["amount"])
        except Exception:
            raise ValueError("Argument 'amount' must be an integer (minor units)")
        if norm["amount"] <= 0:
            raise ValueError("Amount must be positive")
        norm["currency"] = str(norm.get("currency", "INR")).upper()
        if "beneficiary" not in norm:
            raise ValueError("Missing required argument 'beneficiary'")
        norm["beneficiary"] = str(norm["beneficiary"]).strip()
    return norm

def extract_principal_from_request(req: Request) -> Dict[str, Any]:
    auth = req.headers.get("Authorization")
    if auth and auth.startswith("Bearer "):
        token = auth.split("Bearer ", 1)[1].strip()
        try:
            claims = jwt.decode(
                token,
                JWT_SECRET_KEY,
                algorithms=[JWT_ALGORITHM],
                audience=MCP_AUDIENCE,
            )
            return {
                "id": claims.get("sub", "unknown"),
                "role": claims.get("role", "viewer"),
                "scopes": claims.get("scope", "").split(),
            }
        except Exception as e:
            return {"id": "anonymous", "role": "unauthenticated", "error": str(e)}

    # Check X-API-Key for lab W1/W2 fallback
    api_key = req.headers.get("X-API-Key")
    if api_key == GATE3_KEY:
        return {"id": "lab-support-agent", "role": "support_agent", "scopes": ["mcp:tools"]}

    return {"id": "anonymous", "role": "unauthenticated"}

def evaluate_opa_policy(principal: Dict[str, Any], tool_name: str, arguments: Dict[str, Any]) -> Tuple[str, str]:
    if principal.get("role") == "unauthenticated":
        return "deny", "UNAUTHENTICATED_CALLER"

    payload = {
        "input": {
            "principal": principal,
            "tool": tool_name,
            "arguments": arguments,
        }
    }
    try:
        with httpx.Client(timeout=0.6) as client:
            resp = client.post(OPA_URL, json=payload)
            if resp.status_code != 200:
                return "deny", f"OPA_ERROR_{resp.status_code}"
            data = resp.json().get("result", {})
            decision = data.get("decision", "deny")
            reason = data.get("reason", "NO_MATCHING_RULE")
            return decision, reason
    except httpx.TimeoutException:
        return "deny", "POLICY_TIMEOUT_FAIL_CLOSED"
    except Exception as e:
        return "deny", f"POLICY_UNAVAILABLE_FAIL_CLOSED: {type(e).__name__}"

def get_exchanged_api_token(principal: Dict[str, Any], tool_name: str) -> str:
    """Creates a scoped API-audience JWT for downstream Gate 3 traversal."""
    now = int(time.time())
    scopes = ["api:accounts:read", "api:cases:read"]
    if tool_name == "create_payment":
        scopes.append("api:payments:write")
    if tool_name == "remediate_incident":
        scopes.append("api:incidents:write")

    payload = {
        "iss": ISSUER,
        "sub": principal.get("id", "adapter-service"),
        "aud": API_AUDIENCE,
        "exp": now + 600,
        "iat": now,
        "scope": " ".join(scopes),
        "role": principal.get("role", "viewer"),
        "act": {"sub": "mcp-adapter"},
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

CURATED_TOOLS = [
    {
        "name": "get_account",
        "description": "Retrieve verified NovaBank account balance and metadata by account ID.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "id": {"type": "string", "description": "The unique account identifier (e.g. acc-101)"}
            },
            "required": ["id"]
        },
        "annotations": {"readOnlyHint": True}
    },
    {
        "name": "get_case",
        "description": "Read support case details and transaction dispute records.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "id": {"type": "string", "description": "The case ID (e.g. case-501)"}
            },
            "required": ["id"]
        },
        "annotations": {"readOnlyHint": True}
    },
    {
        "name": "create_payment",
        "description": "Propose or execute a compliant enterprise payment. Amounts > 1,000 INR require manager approval.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "account_id": {"type": "string", "description": "Source account ID"},
                "amount": {"type": "integer", "description": "Payment amount in minor units (paise for INR)"},
                "currency": {"type": "string", "default": "INR"},
                "beneficiary": {"type": "string", "description": "Destination account or entity identifier"}
            },
            "required": ["account_id", "amount", "beneficiary"]
        }
    }
]

@app.get("/healthz")
def healthz():
    return {"status": "healthy", "service": "mcp-adapter"}

@app.post("/mcp")
async def handle_mcp(req: Request):
    try:
        body = await req.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON-RPC payload")

    method = body.get("method")
    msg_id = body.get("id")

    if method == "initialize":
        result = {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "novabank-curated-mcp-adapter", "version": "1.0.0"}
        }
        return JSONResponse({"jsonrpc": "2.0", "id": msg_id, "result": result})

    elif method == "tools/list":
        return JSONResponse({"jsonrpc": "2.0", "id": msg_id, "result": {"tools": CURATED_TOOLS}})

    elif method == "tools/call":
        params = body.get("params", {})
        tool_name = params.get("name")
        args = params.get("arguments", {})

        principal = extract_principal_from_request(req)

        # 1. Normalize
        try:
            norm_args = normalize_arguments(tool_name, args)
        except Exception as e:
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {"isError": True, "content": [{"type": "text", "text": f"Argument validation failed: {str(e)}"}]}
            })

        # 2. OPA Policy Evaluation
        decision, reason = evaluate_opa_policy(principal, tool_name, norm_args)

        if decision == "deny":
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "isError": True,
                    "content": [{"type": "text", "text": f"POLICY_DENIED: Execution rejected by Gate 2 policy. Reason: {reason}"}]
                }
            })

        if decision == "approval_required":
            # Record proposal without executing mutation
            prop_id = f"prop-{int(time.time()*1000)}"
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "isError": False,
                    "content": [{
                        "type": "text",
                        "text": json.dumps({
                            "status": "APPROVAL_REQUIRED",
                            "proposal_id": prop_id,
                            "reason": reason,
                            "message": "Payment amount requires supervisory approval. Proposal recorded."
                        }, indent=2)
                    }]
                }
            })

        # 3. Decision == "allow": Re-enter Gate 3 with downstream API token
        api_token = get_exchanged_api_token(principal, tool_name)
        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
        }
        # Propagate W3C traceparent if present
        traceparent = req.headers.get("traceparent")
        if traceparent:
            headers["traceparent"] = traceparent

        try:
            with httpx.Client(timeout=5.0) as client:
                if tool_name == "get_account":
                    acc_id = norm_args.get("id")
                    res = client.get(f"{GATE3_URL}/accounts/{acc_id}", headers=headers)
                elif tool_name == "get_case":
                    case_id = norm_args.get("id")
                    res = client.get(f"{GATE3_URL}/cases/{case_id}", headers=headers)
                elif tool_name == "create_payment":
                    res = client.post(f"{GATE3_URL}/payments", headers=headers, json=norm_args)
                else:
                    return JSONResponse({"jsonrpc": "2.0", "id": msg_id, "error": {"code": -32601, "message": "Method not found"}})

                return JSONResponse({
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "isError": res.status_code >= 400,
                        "content": [{"type": "text", "text": res.text}]
                    }
                })
        except Exception as e:
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "isError": True,
                    "content": [{"type": "text", "text": f"Gate 3 connection failure: {str(e)}"}]
                }
            })

    return JSONResponse({"jsonrpc": "2.0", "id": msg_id, "error": {"code": -32601, "message": "Method not found"}})

@app.post("/ai/chat/completions")
async def ai_chat_completions(req: Request):
    """
    Gate 1 Mock/Replay LLM provider.
    Returns deterministic responses clearly marked [REPLAY].
    """
    body = await req.json()
    messages = body.get("messages", [])
    last_msg = messages[-1]["content"] if messages else ""

    content = f"[REPLAY] Simulated reasoning complete for input: '{last_msg[:80]}'. Tool proposed: get_account"
    return JSONResponse({
        "id": f"chatcmpl-replay-{int(time.time())}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": "novabank-replay-fixture",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": "stop"
            }
        ],
        "usage": {"prompt_tokens": 15, "completion_tokens": 20, "total_tokens": 35}
    })
