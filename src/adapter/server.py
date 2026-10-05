import os
import json
import time
import asyncio
import re
import httpx
from typing import Dict, Any, Tuple
from fastapi import FastAPI, Request, Response, HTTPException, status
from fastapi.responses import JSONResponse, PlainTextResponse
from jose import jwt, JWTError

OPA_URL = os.getenv("OPA_URL", "http://opa:8181/v1/data/flobank/policy")
GATE3_URL = os.getenv("GATE3_URL", "http://apisix:9080/api/v1")
GATE3_KEY = os.getenv("GATE3_API_KEY", "gate3-secret-token")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "flobank-super-secret-signing-key-for-lab")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ISSUER = os.getenv("JWT_ISSUER", "https://identity.flobank.internal/realms/flobank")
MCP_AUDIENCE = os.getenv("MCP_AUDIENCE", "flobank-mcp")
API_AUDIENCE = os.getenv("API_AUDIENCE", "flobank-api")
ENABLE_TELEMETRY = os.getenv("ENABLE_TELEMETRY", "true").lower() in ("true", "1", "yes")
OTEL_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://jaeger:4318/v1/traces")

app = FastAPI(title="Flo Bank Curated MCP Adapter", version="1.0.0")

if ENABLE_TELEMETRY:
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        res = Resource.create({"service.name": "flobank-adapter"})
        provider = TracerProvider(resource=res)
        exporter = OTLPSpanExporter(endpoint=OTEL_ENDPOINT)
        provider.add_span_processor(BatchSpanProcessor(exporter, schedule_delay_millis=500))
        trace.set_tracer_provider(provider)
        FastAPIInstrumentor.instrument_app(app)
    except Exception as e:
        print(f"Adapter OTel setup skipped or failed: {e}")

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
        "description": "Retrieve verified Flo Bank account balance and metadata by account ID.",
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
            "serverInfo": {"name": "flobank-curated-mcp-adapter", "version": "1.0.0"}
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
            traceparent = req.headers.get("traceparent")
            if traceparent:
                headers["traceparent"] = traceparent
            elif ENABLE_TELEMETRY:
                try:
                    from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
                    TraceContextTextMapPropagator().inject(headers)
                except Exception:
                    pass
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
            elif ENABLE_TELEMETRY:
                try:
                    from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
                    TraceContextTextMapPropagator().inject(headers)
                except Exception:
                    pass

            try:
                with httpx.Client(timeout=5.0) as client:
                    if tool_name == "get_account":
                        acc_id = norm_args.get("id")
                        res = client.get(f"{GATE3_URL}/accounts/{acc_id}", headers=headers)
                    elif tool_name == "get_case":
                        case_id = norm_args.get("id")
                        res = client.get(f"{GATE3_URL}/cases/{case_id}", headers=headers)
                    elif tool_name == "create_payment":
                        if req.headers.get("Idempotency-Key"):
                            headers["Idempotency-Key"] = req.headers["Idempotency-Key"]
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
_budget_lock = asyncio.Lock()
INFERENCE_BUDGET_TOKENS = int(os.getenv("INFERENCE_BUDGET_TOKENS", "100000"))

@app.post("/ai/budget/reset")
async def reset_ai_budget():
    global _accumulated_tokens
    async with _budget_lock:
        _accumulated_tokens = 0
        current = _accumulated_tokens
    return {"status": "ok", "accumulated_tokens": current, "budget_limit": INFERENCE_BUDGET_TOKENS}

@app.get("/ai/status")
@app.get("/ai/budget")
async def get_ai_status():
    use_replay = os.getenv("USE_REPLAY_FIXTURES", "true").lower() in ("true", "1", "yes")
    api_key = os.getenv("MINIMAX_API_KEY") or os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
    provider_ready = bool(api_key and not api_key.startswith("mock-"))
    async with _budget_lock:
        current = _accumulated_tokens
    return {
        "status": "ready",
        "mode": "replay" if use_replay else "live",
        "use_replay_fixtures": use_replay,
        "model": os.getenv("LLM_MODEL", "MiniMax-M2.7-highspeed"),
        "provider_configured": provider_ready if not use_replay else True,
        "accumulated_tokens": current,
        "budget_limit": INFERENCE_BUDGET_TOKENS,
        "headroom_tokens": max(0, INFERENCE_BUDGET_TOKENS - current)
    }

@app.post("/ai/chat/completions")
async def ai_chat_completions(req: Request):
    """
    Gate 1 AI Provider Adapter.
    - Evaluates and tracks inference budget with atomic pre-dispatch reservation and post-call reconciliation.
    - Live Mode (USE_REPLAY_FIXTURES=false): Forwards OpenAI-compatible tool/message payloads
      to upstream LLM provider (e.g. MiniMax) via APISIX Gate 1.
    - Replay Mode (USE_REPLAY_FIXTURES=true): Emits deterministic multi-turn tool-calling
      fixtures compatible with LangGraph dispute agent execution.
    """
    global _accumulated_tokens
    body = await req.json()
    messages = body.get("messages", [])
    tools = body.get("tools")
    has_tools = bool(tools)

    # Atomic token budget reservation before dispatch
    est_prompt = max(15, len(json.dumps({"messages": messages, "tools": tools})) // 4)
    requested_output = body.get("max_tokens", body.get("max_completion_tokens", 2048))
    if type(requested_output) is not int or requested_output <= 0:
        return JSONResponse({"error": {"type": "invalid_max_tokens", "code": 400}}, status_code=400)
    requested_output = min(requested_output, 2048)
    reservation = est_prompt + requested_output

    async with _budget_lock:
        if _accumulated_tokens + reservation > INFERENCE_BUDGET_TOKENS:
            return JSONResponse({
                "error": {
                    "message": f"Inference budget exceeded ({_accumulated_tokens}/{INFERENCE_BUDGET_TOKENS} tokens)",
                    "type": "budget_exceeded_error",
                    "code": 429
                }
            }, status_code=429)
        _accumulated_tokens += reservation

    actual_tokens = 0
    try:
        header_replay = req.headers.get("x-use-replay-fixtures", "").lower()
        if header_replay in ("true", "1", "yes"):
            use_replay = True
        elif header_replay in ("false", "0", "no"):
            use_replay = False
        else:
            use_replay = os.getenv("USE_REPLAY_FIXTURES", "true").lower() in ("true", "1", "yes")
        if not use_replay:
            # Live provider egress path
            api_key = os.getenv("MINIMAX_API_KEY") or os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
            if not api_key or api_key.startswith("mock-"):
                return JSONResponse({
                    "error": {
                        "message": "Live LLM provider credentials not configured on host (MINIMAX_API_KEY, LLM_API_KEY, or OPENAI_API_KEY required when USE_REPLAY_FIXTURES=false). Set USE_REPLAY_FIXTURES=true for offline replay mode.",
                        "type": "provider_configuration_error",
                        "code": 503
                    }
                }, status_code=503)

            provider_url = os.getenv("LLM_PROVIDER_URL", "https://api.minimax.io/v1/chat/completions")
            model = body.get("model") or os.getenv("LLM_MODEL", "MiniMax-M2.7-highspeed")

            payload = {
                "model": model,
                "messages": messages,
            }
            if tools:
                payload["tools"] = tools
            if "tool_choice" in body:
                payload["tool_choice"] = body["tool_choice"]
            payload["max_tokens"] = requested_output
            if "temperature" in body:
                payload["temperature"] = body["temperature"]

            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    res = await client.post(
                        provider_url,
                        headers={
                            "Authorization": f"Bearer {api_key}",
                            "Content-Type": "application/json"
                        },
                        json=payload
                    )
                    try:
                        res_json = res.json()
                    except Exception:
                        return JSONResponse({
                            "error": {
                                "message": f"Upstream LLM provider returned non-JSON response ({res.status_code}): {res.text[:200]}",
                                "type": "provider_error",
                                "code": 502
                            }
                        }, status_code=502)

                    if res.status_code != 200 or "error" in res_json:
                        return JSONResponse(res_json, status_code=res.status_code if res.status_code >= 400 else 502)

                    # Reconcile usage accounting
                    usage = res_json.get("usage", {})
                    actual_tokens = usage.get("total_tokens") or (usage.get("prompt_tokens", 0) + usage.get("completion_tokens", 0)) or reservation
                    usage["accumulated_budget_tokens"] = _accumulated_tokens - reservation + actual_tokens
                    usage["budget_limit"] = INFERENCE_BUDGET_TOKENS
                    res_json["usage"] = usage
                    return JSONResponse(res_json, status_code=200)

            except httpx.TimeoutException:
                return JSONResponse({
                    "error": {
                        "message": "Upstream LLM provider call timed out after 60s",
                        "type": "provider_timeout_error",
                        "code": 504
                    }
                }, status_code=504)
            except Exception as e:
                return JSONResponse({
                    "error": {
                        "message": f"Upstream LLM provider communication error: {str(e)}",
                        "type": "provider_error",
                        "code": 502
                    }
                }, status_code=502)

        # Replay provider path
        if has_tools:
            tool_names = {t.get("function", {}).get("name") for t in tools if isinstance(t, dict)}
            is_demo = any(str(name).startswith("get_demo_") or str(name).startswith("set_demo_") or str(name).startswith("create_demo_") for name in tool_names)

            if is_demo:
                tool_messages = [m for m in messages if m.get("role") == "tool"]
                last_user_msg = ""
                for m in reversed(messages):
                    if m.get("role") == "user" and isinstance(m.get("content"), str):
                        last_user_msg = m.get("content", "").lower()
                        break

                if not tool_messages:
                    actual_tokens = 50
                    call_id = f"call_demo_{int(time.time()*1000)}"
                    if any(w in last_user_msg for w in ["balance", "account", "paise", "money", "how much"]):
                        fn_call = {"name": "get_demo_accounts", "arguments": "{}"}
                    elif any(w in last_user_msg for w in ["freeze", "lock"]):
                        fn_call = {"name": "set_demo_card_state", "arguments": json.dumps({"locked": True})}
                    elif any(w in last_user_msg for w in ["unfreeze", "unlock"]):
                        fn_call = {"name": "set_demo_card_state", "arguments": json.dumps({"locked": False})}
                    elif "card" in last_user_msg:
                        fn_call = {"name": "get_demo_card", "arguments": "{}"}
                    elif any(w in last_user_msg for w in ["dispute", "unrecognized", "fraud", "tx-"]):
                        tx_match = re.search(r'tx-\d+', last_user_msg)
                        target_tx = tx_match.group(0) if tx_match else "tx-1004"
                        fn_call = {"name": "create_demo_dispute", "arguments": json.dumps({"transaction_id": target_tx})}
                    elif any(w in last_user_msg for w in ["spending", "spent", "largest"]):
                        fn_call = {"name": "get_demo_spending", "arguments": "{}"}
                    elif any(w in last_user_msg for w in ["transaction", "recent", "activity", "history", "statement"]):
                        fn_call = {"name": "get_demo_transactions", "arguments": "{}"}
                    else:
                        actual_tokens = 45
                        content = (
                            "Hello Maya! I'm Flo, your banking companion. "
                            "I can help you check your balances, review recent transactions and spending, "
                            "manage debit card controls, or file a dispute on an unrecognized charge. "
                            "What would you like to explore today?"
                        )
                        return JSONResponse({
                            "id": f"chatcmpl-demo-reply-{int(time.time())}",
                            "object": "chat.completion",
                            "created": int(time.time()),
                            "model": "flobank-replay-fixture",
                            "choices": [{
                                "index": 0,
                                "message": {"role": "assistant", "content": content},
                                "finish_reason": "stop"
                            }],
                            "usage": {
                                "prompt_tokens": 40,
                                "completion_tokens": 40,
                                "total_tokens": actual_tokens,
                                "accumulated_budget_tokens": _accumulated_tokens - reservation + actual_tokens,
                                "budget_limit": INFERENCE_BUDGET_TOKENS
                            }
                        })

                    return JSONResponse({
                        "id": f"chatcmpl-demo-tool-{int(time.time())}",
                        "object": "chat.completion",
                        "created": int(time.time()),
                        "model": "flobank-replay-fixture",
                        "choices": [{
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": None,
                                "tool_calls": [{
                                    "id": call_id,
                                    "type": "function",
                                    "function": fn_call
                                }]
                            },
                            "finish_reason": "tool_calls"
                        }],
                        "usage": {
                            "prompt_tokens": 40,
                            "completion_tokens": 40,
                            "total_tokens": actual_tokens,
                            "accumulated_budget_tokens": _accumulated_tokens - reservation + actual_tokens,
                            "budget_limit": INFERENCE_BUDGET_TOKENS
                        }
                    })

                # Round 2: Synthesize assistant response from tool result
                actual_tokens = 70
                last_tool = tool_messages[-1]
                tool_name = last_tool.get("name", "")
                try:
                    tool_data = json.loads(last_tool.get("content", "{}"))
                except Exception:
                    tool_data = {}

                if tool_name == "get_demo_accounts":
                    accs = tool_data.get("accounts", [])
                    if accs:
                        lines = [f"- **{a.get('name', 'Account')}** ({a.get('number', '')}): {a.get('formatted_balance', '₹' + str(a.get('balance_paise', 0)/100))}" for a in accs]
                        total = sum(a.get("balance_paise", 0) for a in accs)
                        content = f"Here are your current balances, Maya:\n\n" + "\n".join(lines) + f"\n\n**Total across accounts:** ₹{total/100:,.2f}"
                    else:
                        content = "Here are your current balances, Maya:\n\n- **Everyday account** (•••• 2048): ₹1,24,850.00\n- **Savings pocket** (•••• 8821): ₹3,50,000.00\n\n**Total across accounts:** ₹4,74,850.00"
                elif tool_name == "set_demo_card_state":
                    locked = tool_data.get("card_locked", True)
                    status_str = "frozen" if locked else "active"
                    content = f"Done! Your debit card ending in **2048** is now **{status_str}**. No charges can be made with this card until you unfreeze it."
                elif tool_name == "get_demo_card":
                    locked = tool_data.get("locked", False)
                    status_str = "frozen" if locked else "active"
                    content = f"Your debit card ending in **2048** is currently **{status_str}**."
                elif tool_name == "create_demo_dispute":
                    case = tool_data.get("case", {})
                    c_id = case.get("id", "DEMO-1001")
                    merchant = case.get("merchant", "Stream+")
                    amt = case.get("formatted_amount", "₹2,499.00")
                    content = f"I've filed simulated dispute **{c_id}** for your {amt} charge at {merchant}. Our disputes team will review the transaction within 2 business days."
                elif tool_name == "get_demo_spending":
                    tot = tool_data.get("formatted_total", "₹5,489.00")
                    cnt = tool_data.get("charge_count", 4)
                    largest = tool_data.get("largest_charge", {})
                    largest_str = f" The largest charge was {largest.get('formatted_amount', '₹2,499.00')} for {largest.get('merchant', 'Stream+')}." if largest else ""
                    content = f"Your total recent spending is {tot} across {cnt} debit charges.{largest_str}"
                elif tool_name == "get_demo_transactions":
                    content = (
                        "Here are your recent transactions, Maya:\n\n"
                        "| Date | Merchant | Category | Amount |\n"
                        "|---|---|---|---|\n"
                        "| 2026-10-03 | Acme Studio | Salary | +₹85,000.00 |\n"
                        "| 2026-10-03 | Blue Tokai | Food & drink | -₹480.00 |\n"
                        "| 2026-10-02 | Fresh Basket | Groceries | -₹1,860.00 |\n"
                        "| 2026-10-01 | Stream+ | Subscription | -₹2,499.00 |\n"
                        "| 2026-09-30 | Metro Transit | Travel | -₹650.00 |"
                    )
                else:
                    content = "I've checked that for you. Is there anything else about your accounts or cards I can assist with?"

                return JSONResponse({
                    "id": f"chatcmpl-demo-finish-{int(time.time())}",
                    "object": "chat.completion",
                    "created": int(time.time()),
                    "model": "flobank-replay-fixture",
                    "choices": [{
                        "index": 0,
                        "message": {"role": "assistant", "content": content},
                        "finish_reason": "stop"
                    }],
                    "usage": {
                        "prompt_tokens": 50,
                        "completion_tokens": 60,
                        "total_tokens": actual_tokens,
                        "accumulated_budget_tokens": _accumulated_tokens - reservation + actual_tokens,
                        "budget_limit": INFERENCE_BUDGET_TOKENS
                    }
                })

            # Inspect tool calling sequence for W3 LangGraph dispute agent
            tool_messages = [m for m in messages if m.get("role") == "tool"]
            prompt_text = " ".join([m.get("content", "") for m in messages if isinstance(m.get("content"), str)])
            case_id = "case-501"
            if "case-502" in prompt_text or "502" in prompt_text:
                case_id = "case-502"
            elif "case-503" in prompt_text or "503" in prompt_text:
                case_id = "case-503"

            called_tools = set()
            for tm in tool_messages:
                tc_id = tm.get("tool_call_id", "")
                if "case" in tc_id:
                    called_tools.add("get_case")
                elif "acc" in tc_id:
                    called_tools.add("get_account")

            # Step 1: Request get_case if not yet called
            if "get_case" not in called_tools:
                actual_tokens = 80
                call_id = f"call_get_case_{int(time.time())}"
                return JSONResponse({
                    "id": f"chatcmpl-replay-tool-{int(time.time())}",
                    "object": "chat.completion",
                    "created": int(time.time()),
                    "model": "flobank-replay-fixture",
                    "choices": [{
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": None,
                            "tool_calls": [{
                                "id": call_id,
                                "type": "function",
                                "function": {
                                    "name": "get_case",
                                    "arguments": json.dumps({"id": case_id})
                                }
                            }]
                        },
                        "finish_reason": "tool_calls"
                    }],
                    "usage": {
                        "prompt_tokens": 40,
                        "completion_tokens": 40,
                        "total_tokens": actual_tokens,
                        "accumulated_budget_tokens": _accumulated_tokens - reservation + actual_tokens,
                        "budget_limit": INFERENCE_BUDGET_TOKENS
                    }
                })

            # Step 2: Request get_account if not yet called
            elif "get_account" not in called_tools:
                actual_tokens = 90
                acc_id = "acc-101"
                if case_id == "case-502":
                    acc_id = "acc-8802"
                call_id = f"call_get_acc_{int(time.time())}"
                return JSONResponse({
                    "id": f"chatcmpl-replay-tool-{int(time.time())}",
                    "object": "chat.completion",
                    "created": int(time.time()),
                    "model": "flobank-replay-fixture",
                    "choices": [{
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": None,
                            "tool_calls": [{
                                "id": call_id,
                                "type": "function",
                                "function": {
                                    "name": "get_account",
                                    "arguments": json.dumps({"id": acc_id})
                                }
                            }]
                        },
                        "finish_reason": "tool_calls"
                    }],
                    "usage": {
                        "prompt_tokens": 50,
                        "completion_tokens": 40,
                        "total_tokens": actual_tokens,
                        "accumulated_budget_tokens": _accumulated_tokens - reservation + actual_tokens,
                        "budget_limit": INFERENCE_BUDGET_TOKENS
                    }
                })

            # Step 3: Synthesis proposal after tools
            actual_tokens = 140
            if case_id == "case-501":
                proposal_dict = {
                    "case_id": "case-501",
                    "customer_id": "cust-8801",
                    "amount": 75000,
                    "currency": "INR",
                    "destination_account": "acc-101",
                    "rationale": "Verified duplicate debit on account acc-101 from case get_case and get_account ledger evidence. Compensating INR 750.00."
                }
            elif case_id == "case-502":
                proposal_dict = {
                    "case_id": "case-502",
                    "customer_id": "cust-8802",
                    "amount": 90000000,
                    "currency": "INR",
                    "destination_account": "fraud-account-66",
                    "rationale": "Suspicious prompt injection attack detected; flagged for mandatory security review."
                }
            else:
                proposal_dict = {
                    "case_id": case_id,
                    "customer_id": "cust-8801",
                    "amount": 40000,
                    "currency": "INR",
                    "destination_account": "acc-101",
                    "rationale": f"General dispute resolution credit for {case_id}."
                }

            return JSONResponse({
                "id": f"chatcmpl-replay-finish-{int(time.time())}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": "flobank-replay-fixture",
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": json.dumps(proposal_dict)
                    },
                    "finish_reason": "stop"
                }],
                "usage": {
                    "prompt_tokens": 80,
                    "completion_tokens": 60,
                    "total_tokens": actual_tokens,
                    "accumulated_budget_tokens": _accumulated_tokens - reservation + actual_tokens,
                    "budget_limit": INFERENCE_BUDGET_TOKENS
                }
            })

        # Standard replay path without tools (backward compatible with existing test cases)
        actual_tokens = 35
        model_name = "flobank-replay-fixture"
        last_msg = messages[-1]["content"] if messages else ""
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
                "total_tokens": actual_tokens,
                "accumulated_budget_tokens": _accumulated_tokens - reservation + actual_tokens,
                "budget_limit": INFERENCE_BUDGET_TOKENS
            }
        })
    finally:
        async with _budget_lock:
            _accumulated_tokens = _accumulated_tokens - reservation + actual_tokens
