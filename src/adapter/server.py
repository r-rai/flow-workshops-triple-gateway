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
                issuer=ISSUER,
            )
            scopes = claims.get("scope", "").split()
            if "mcp:tools" not in scopes:
                return {
                    "id": claims.get("sub", "unknown"),
                    "role": "unauthenticated",
                    "scopes": scopes,
                    "error": "Missing 'mcp:tools' scope in bearer token",
                }
            return {
                "id": claims.get("sub", "unknown"),
                "role": claims.get("role", "viewer"),
                "scopes": scopes,
                "raw_token": token,
            }
        except Exception as e:
            return {"id": "anonymous", "role": "unauthenticated", "error": str(e)}

    # Check X-API-Key for lab fallback
    api_key = req.headers.get("X-API-Key")
    if api_key == GATE3_KEY:
        return {"id": "lab-support-agent", "role": "support_agent", "scopes": ["mcp:tools"]}

    return {"id": "anonymous", "role": "anonymous", "scopes": []}

def evaluate_opa_policy(principal: Dict[str, Any], tool_name: str, arguments: Dict[str, Any]) -> Tuple[str, str]:
    if principal.get("role") in ("unauthenticated", "anonymous"):
        err_detail = principal.get("error", "Missing valid credentials")
        return "deny", f"UNAUTHENTICATED_CALLER: {err_detail}"


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
    """Performs RFC 8693 token exchange via API for bearer tokens without silent fallback."""
    raw_token = principal.get("raw_token")
    if raw_token:
        scope = "api:accounts:read api:cases:read"
        if tool_name == "create_payment":
            scope = "api:accounts:read api:cases:read api:payments:write"
        elif tool_name == "remediate_incident":
            scope = "api:accounts:read api:cases:read api:incidents:write"

        exchange_payload = {
            "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
            "subject_token": raw_token,
            "subject_token_type": "urn:ietf:params:oauth:token-type:access_token",
            "audience": API_AUDIENCE,
            "scope": scope,
        }

        with httpx.Client(timeout=3.0) as client:
            resp = client.post(
                f"{GATE3_URL}/oauth/token",
                headers={
                    "X-API-Key": GATE3_KEY,
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data=exchange_payload,
            )
            if resp.status_code == 200:
                return resp.json()["access_token"]
            else:
                raise HTTPException(
                    status_code=resp.status_code,
                    detail=f"RFC 8693 token exchange failed (HTTP {resp.status_code}): {resp.text}"
                )

    # Fallback only for authenticated static lab API key principals (non-bearer)
    if principal.get("role") == "support_agent":
        now = int(time.time())
        scopes = ["api:accounts:read", "api:cases:read"]
        payload = {
            "iss": ISSUER,
            "sub": principal.get("id", "lab-support-agent"),
            "aud": API_AUDIENCE,
            "exp": now + 600,
            "iat": now,
            "scope": " ".join(scopes),
            "role": "support_agent",
            "act": {"sub": "lab-static-key"},
        }
        return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Caller lacks valid bearer token for RFC 8693 token exchange",
    )

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
        principal = extract_principal_from_request(req)
        if principal.get("role") == "unauthenticated":
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32000, "message": "Unauthorized: Invalid MCP bearer token or missing 'mcp:tools' scope"}
            }, status_code=403)
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

        elif decision == "approval_required":
            # Persist proposal through the real approval service
            api_token = get_exchanged_api_token(principal, tool_name)
            headers = {
                "Authorization": f"Bearer {api_token}",
                "X-API-Key": GATE3_KEY,
                "Content-Type": "application/json",
            }
            prop_id = None
            persist_err = None
            try:
                with httpx.Client(timeout=5.0) as client:
                    proposal_payload = {
                        "account_id": norm_args.get("account_id", "acc-101"),
                        "amount": norm_args.get("amount", 0),
                        "currency": norm_args.get("currency", "INR"),
                        "beneficiary": norm_args.get("beneficiary", ""),
                    }
                    p_res = client.post(f"{GATE3_URL}/payments/proposals", headers=headers, json=proposal_payload)
                    if p_res.status_code in (200, 201):
                        prop_id = p_res.json().get("proposal_id")
                    else:
                        persist_err = f"Backend banking service returned HTTP {p_res.status_code}: {p_res.text}"
            except Exception as e:
                persist_err = f"Backend banking service communication failure: {str(e)}"

            if not prop_id:
                # Return explicit persistence failure - never fabricate proposal IDs or report recorded status
                return JSONResponse({
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "isError": True,
                        "content": [{
                            "type": "text",
                            "text": json.dumps({
                                "error": "PROPOSAL_PERSISTENCE_FAILED",
                                "status": "ERROR",
                                "reason": reason,
                                "detail": persist_err or "Proposal could not be recorded in backend banking service.",
                                "message": "Payment requires supervisory approval, but the proposal could not be durably recorded in the banking ledger. No financial mutation occurred."
                            }, indent=2)
                        }]
                    }
                })

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

        elif decision == "allow":
            # 3. Decision == "allow": Re-enter Gate 3 with downstream API token
            api_token = get_exchanged_api_token(principal, tool_name)
            headers = {
                "Authorization": f"Bearer {api_token}",
                "X-API-Key": GATE3_KEY,
                "Content-Type": "application/json",
            }
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
            except Exception as e:
                return JSONResponse({
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {"isError": True, "content": [{"type": "text", "text": f"Downstream service unavailable: {str(e)}"}]}
                })

            if res.status_code >= 400:
                return JSONResponse({
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {"isError": True, "content": [{"type": "text", "text": f"Downstream API error ({res.status_code}): {res.text}"}]}
                })

            return JSONResponse({
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {"isError": False, "content": [{"type": "text", "text": json.dumps(res.json(), indent=2)}]}
            })

        else:
            # Strict fail closed: unknown, null, or malformed decisions are rejected
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "isError": True,
                    "content": [{"type": "text", "text": f"POLICY_DENIED: Execution rejected by Gate 2 policy. Decision: '{decision}'. Reason: {reason}"}]
                }
            })

    return JSONResponse({"jsonrpc": "2.0", "id": msg_id, "error": {"code": -32601, "message": "Method not found"}})


_accumulated_tokens = 0
INFERENCE_BUDGET_TOKENS = int(os.getenv("INFERENCE_BUDGET_TOKENS", "10000"))

@app.post("/ai/chat/completions")
async def ai_chat_completions(req: Request):
    """
    Gate 1 Mock/Replay LLM provider.
    Evaluates inference budget and returns deterministic responses marked [REPLAY]
    when USE_REPLAY_FIXTURES is true or live keys are absent.
    """
    global _accumulated_tokens
    body = await req.json()
    messages = body.get("messages", [])
    last_msg = messages[-1]["content"] if messages else ""

    tokens_requested = 35
    if _accumulated_tokens + tokens_requested > INFERENCE_BUDGET_TOKENS:
        return JSONResponse({
            "error": {
                "message": f"Inference budget exceeded ({_accumulated_tokens}/{INFERENCE_BUDGET_TOKENS} tokens)",
                "type": "budget_exceeded_error",
                "code": 429
            }
        }, status_code=429)

    _accumulated_tokens += tokens_requested

    use_replay = os.getenv("USE_REPLAY_FIXTURES", "true").lower() in ("true", "1", "yes")
    model_name = "novabank-replay-fixture" if use_replay else "gpt-4o-mini"
    content = f"[REPLAY] Simulated reasoning complete for input: '{last_msg[:80]}'. Tool proposed: get_account"
    return JSONResponse({
        "id": f"chatcmpl-replay-{int(time.time())}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model_name,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 15,
            "completion_tokens": 20,
            "total_tokens": tokens_requested,
            "accumulated_budget_tokens": _accumulated_tokens,
            "budget_limit": INFERENCE_BUDGET_TOKENS
        }
    })
