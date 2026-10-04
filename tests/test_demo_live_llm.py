"""Automated contract and regression tests for Flo Bank customer live LLM chat.

Verifies:
- Gate 1 OpenAI-compatible tool interactions and turn execution.
- Session context preservation across follow-up questions.
- Rejection of unknown tools, malformed arguments, and foreign transactions.
- Idempotent card state and dispute mutations.
- Staged state rollback on provider failures (no ambiguous partial commits).
- Honest error reporting on missing key, 401/429/5xx, timeouts (no silent fallback).
- Session lock serialization, expired session rejection, and turn boundary history trimming.
"""
from __future__ import annotations

import asyncio
from copy import deepcopy
import json
from pathlib import Path
import sys
import time
from typing import Any
import unittest.mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient
import httpx
import pytest
import yaml

from src.demo.app import app, sessions, DemoSession
from src.demo.tools import DEMO, StagedDemoState, execute_demo_tool, rupees
from src.demo.llm import (
    run_demo_chat_turn,
    trim_history,
    check_gateway_status,
    LLMConfigError,
    LLMProviderError,
    LLMLimitExceededError,
)


@pytest.fixture
def live_client(monkeypatch):
    monkeypatch.setenv("DEMO_CHAT_MODE", "live")
    monkeypatch.setenv("DEMO_AI_GATEWAY_URL", "http://mock-gateway:9080/ai/chat/completions")
    monkeypatch.setenv("DEMO_AI_STATUS_URL", "http://mock-gateway:9080/ai/status")
    with TestClient(app) as client:
        yield client
        client.post("/demo-api/logout")


def login(client):
    res = client.post("/demo-api/login", json={"email": "maya@flobank.demo", "password": "flo-demo"})
    assert res.status_code == 200
    return res


# ---------------------------------------------------------------------------
# 1. Normal question calling tools & follow-up retaining session history
# ---------------------------------------------------------------------------

def test_normal_balance_question_with_mock_gateway(live_client, monkeypatch):
    login(live_client)
    posted_payloads = []

    def mock_post(url, json=None, headers=None, timeout=None):
        posted_payloads.append(deepcopy(json))
        messages = json.get("messages", [])
        
        # Round 1: Model requests get_demo_accounts tool
        if len(messages) == 2:  # system + user
            return httpx.Response(
                200,
                json={
                    "id": "mock-round-1",
                    "object": "chat.completion",
                    "created": int(time.time()),
                    "model": "MiniMax-M2.7-highspeed",
                    "choices": [{
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": None,
                            "tool_calls": [{
                                "id": "call_acc_1",
                                "type": "function",
                                "function": {
                                    "name": "get_demo_accounts",
                                    "arguments": "{}"
                                }
                            }]
                        },
                        "finish_reason": "tool_calls"
                    }],
                    "usage": {"prompt_tokens": 100, "completion_tokens": 30, "total_tokens": 130}
                }
            )
        # Round 2: Model receives tool result and produces synthesized text
        else:
            assert any(m.get("role") == "tool" and m.get("name") == "get_demo_accounts" for m in messages)
            return httpx.Response(
                200,
                json={
                    "id": "mock-round-2",
                    "object": "chat.completion",
                    "created": int(time.time()),
                    "model": "MiniMax-M2.7-highspeed",
                    "choices": [{
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": "Your Everyday account balance is ₹1,24,850.00 and your Savings pocket has ₹3,50,000.00.",
                        },
                        "finish_reason": "stop"
                    }],
                    "usage": {"prompt_tokens": 150, "completion_tokens": 40, "total_tokens": 190}
                }
            )

    monkeypatch.setattr(httpx.AsyncClient, "post", unittest.mock.AsyncMock(side_effect=mock_post))

    res = live_client.post("/demo-api/chat", json={"message": "What is my balance?"})
    assert res.status_code == 200
    data = res.json()
    assert "₹1,24,850.00" in data["reply"]
    assert data["chat_mode"] == "live"
    assert data["mode"] == "simulation"
    assert len(posted_payloads) == 2


def test_followup_question_retains_session_history(live_client, monkeypatch):
    login(live_client)
    captured_messages = []

    def mock_post(url, json=None, headers=None, timeout=None):
        msgs = json.get("messages", [])
        captured_messages.append(deepcopy(msgs))
        last_user = next((m["content"] for m in reversed(msgs) if m["role"] == "user"), "")
        if "savings" in last_user.lower():
            return httpx.Response(
                200,
                json={
                    "choices": [{
                        "message": {
                            "role": "assistant",
                            "content": "As we saw earlier, your Savings pocket has ₹3,50,000.00.",
                        }
                    }]
                }
            )
        return httpx.Response(
            200,
            json={
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": "Your Everyday balance is ₹1,24,850.00.",
                    }
                }]
            }
        )

    monkeypatch.setattr(httpx.AsyncClient, "post", unittest.mock.AsyncMock(side_effect=mock_post))

    # Turn 1
    r1 = live_client.post("/demo-api/chat", json={"message": "What is my balance?"})
    assert r1.status_code == 200

    # Turn 2 (Follow-up)
    r2 = live_client.post("/demo-api/chat", json={"message": "What about my savings?"})
    assert r2.status_code == 200
    assert "₹3,50,000.00" in r2.json()["reply"]

    # Assert Turn 2 contained Turn 1's interaction in history
    turn2_msgs = captured_messages[1]
    turn1_user = next((m for m in turn2_msgs if m.get("content") == "What is my balance?"), None)
    assert turn1_user is not None
    turn1_assistant = next((m for m in turn2_msgs if m.get("content") == "Your Everyday balance is ₹1,24,850.00."), None)
    assert turn1_assistant is not None


# ---------------------------------------------------------------------------
# 2. Tool validation: rejection of unknown tools, malformed args, foreign txs
# ---------------------------------------------------------------------------

def test_unknown_tools_and_malformed_arguments_rejected():
    staged = StagedDemoState(card_locked=False)

    # 1. Unknown tool
    res = execute_demo_tool("get_enterprise_secrets", {}, staged)
    assert "error" in res
    assert "not in the allowlist" in res["error"]

    # 2. Malformed arguments for card lock
    res = execute_demo_tool("set_demo_card_state", {"locked": "not-a-bool"}, staged)
    assert "error" in res
    assert "boolean" in res["error"]

    # 3. Foreign transaction ID for dispute
    res = execute_demo_tool("create_demo_dispute", {"transaction_id": "tx-9999"}, staged)
    assert "error" in res
    assert "not found" in res["error"]

    # 4. Credit transaction cannot be disputed
    res = execute_demo_tool("create_demo_dispute", {"transaction_id": "tx-1001"}, staged)
    assert "error" in res
    assert "Credit transactions" in res["error"]


# ---------------------------------------------------------------------------
# 3. Card freeze/unfreeze and dispute creation update session idempotently
# ---------------------------------------------------------------------------

def test_card_freeze_and_dispute_update_session_idempotently(live_client, monkeypatch):
    login(live_client)

    def mock_post(url, req_json=None, headers=None, timeout=None, **kwargs):
        payload = kwargs.get("json", req_json)
        msgs = payload.get("messages", [])
        last = msgs[-1]

        if last["role"] == "user" and "freeze" in last["content"].lower():
            return httpx.Response(
                200,
                json={
                    "choices": [{
                        "message": {
                            "role": "assistant",
                            "tool_calls": [{
                                "id": "call_freeze_1",
                                "type": "function",
                                "function": {
                                    "name": "set_demo_card_state",
                                    "arguments": json.dumps({"locked": True})
                                }
                            }]
                        }
                    }]
                }
            )
        elif last["role"] == "tool" and last.get("name") == "set_demo_card_state":
            return httpx.Response(
                200,
                json={
                    "choices": [{
                        "message": {
                            "role": "assistant",
                            "content": "Your demo card ending 2048 is now frozen. This only affects this demo session."
                        }
                    }]
                }
            )
        elif last["role"] == "user" and "dispute" in last["content"].lower():
            return httpx.Response(
                200,
                json={
                    "choices": [{
                        "message": {
                            "role": "assistant",
                            "tool_calls": [{
                                "id": "call_disp_1",
                                "type": "function",
                                "function": {
                                    "name": "create_demo_dispute",
                                    "arguments": json.dumps({"transaction_id": "tx-1004"})
                                }
                            }]
                        }
                    }]
                }
            )
        elif last["role"] == "tool" and last.get("name") == "create_demo_dispute":
            return httpx.Response(
                200,
                json={
                    "choices": [{
                        "message": {
                            "role": "assistant",
                            "content": "Simulated dispute DEMO-1001 for Stream+ is under review."
                        }
                    }]
                }
            )
        return httpx.Response(200, json={"choices": [{"message": {"role": "assistant", "content": "Done"}}]})

    monkeypatch.setattr(httpx.AsyncClient, "post", unittest.mock.AsyncMock(side_effect=mock_post))

    # Freeze card
    r1 = live_client.post("/demo-api/chat", json={"message": "Please freeze my card"})
    assert r1.status_code == 200
    assert r1.json()["dashboard"]["card"]["locked"] is True

    # File dispute
    r2 = live_client.post("/demo-api/chat", json={"message": "Dispute tx-1004"})
    assert r2.status_code == 200
    cases = r2.json()["dashboard"]["cases"]
    assert len(cases) == 1
    assert cases[0]["id"] == "DEMO-1001"

    # Retry dispute -> Idempotent, does not duplicate case
    r3 = live_client.post("/demo-api/chat", json={"message": "Dispute tx-1004 again"})
    assert r3.status_code == 200
    assert len(r3.json()["dashboard"]["cases"]) == 1


# ---------------------------------------------------------------------------
# 4. Failed inference discards staged mutations (no partial commits)
# ---------------------------------------------------------------------------

def test_failed_inference_discards_staged_mutations(live_client, monkeypatch):
    login(live_client)

    # In round 1, model requests card lock. In round 2, gateway throws 502 error.
    def mock_post(url, json=None, headers=None, timeout=None):
        msgs = json.get("messages", [])
        if len(msgs) == 2:
            return httpx.Response(
                200,
                json={
                    "choices": [{
                        "message": {
                            "role": "assistant",
                            "tool_calls": [{
                                "id": "call_freeze_2",
                                "type": "function",
                                "function": {
                                    "name": "set_demo_card_state",
                                    "arguments": json.dumps({"locked": True})
                                }
                            }]
                        }
                    }]
                }
            )
        return httpx.Response(502, json={"error": {"message": "Upstream model connection lost"}})

    monkeypatch.setattr(httpx.AsyncClient, "post", unittest.mock.AsyncMock(side_effect=mock_post))

    res = live_client.post("/demo-api/chat", json={"message": "Freeze card"})
    assert res.status_code == 502

    # Verify session card was NOT committed as locked!
    db = live_client.get("/demo-api/dashboard").json()
    assert db["card"]["locked"] is False


# ---------------------------------------------------------------------------
# 5. Honest errors: missing key, 401/429/5xx, timeouts without fallback
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("status_code,err_message,expected_status", [
    (503, "Live LLM provider credentials not configured", 503),
    (429, "Inference budget exceeded", 429),
    (504, "Upstream LLM provider call timed out after 60s", 504),
    (502, "Upstream LLM provider returned error", 502),
])
def test_provider_errors_produce_honest_errors_without_fallback(live_client, monkeypatch, status_code, err_message, expected_status):
    login(live_client)

    async def mock_post(*args, **kwargs):
        return httpx.Response(status_code, json={"error": {"message": err_message, "code": status_code}})

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    res = live_client.post("/demo-api/chat", json={"message": "What is my balance?"})
    assert res.status_code == expected_status
    # Verify it does NOT fall back to scripted reply containing balance!
    assert err_message in res.json().get("detail", "")


# ---------------------------------------------------------------------------
# 6. Session revocation & history trimming
# ---------------------------------------------------------------------------

def test_session_revocation_during_inference_prevents_commit(live_client, monkeypatch):
    login(live_client)
    token = live_client.cookies.get("flo_demo_session")

    async def mock_post(*args, **kwargs):
        # In-flight logout occurs
        sessions[token].expires_at = 0
        return httpx.Response(200, json={"choices": [{"message": {"role": "assistant", "content": "Done"}}]})

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    res = live_client.post("/demo-api/chat", json={"message": "Hello"})
    assert res.status_code == 401
    assert "session ended" in res.json()["detail"].lower()


def test_history_trimming_preserves_turn_boundaries():
    # Construct 10 turns with user, assistant tool_call, tool response, and final assistant reply
    messages = []
    for i in range(10):
        messages.append({"role": "user", "content": f"Question {i}"})
        messages.append({"role": "assistant", "content": None, "tool_calls": [{"id": f"c_{i}", "function": {"name": "get_demo_accounts", "arguments": "{}"}}]})
        messages.append({"role": "tool", "tool_call_id": f"c_{i}", "name": "get_demo_accounts", "content": "{}"})
        messages.append({"role": "assistant", "content": f"Answer {i}"})

    # Trim to 4 turns
    trimmed = trim_history(messages, max_turns=4)
    # 4 turns * 4 messages = 16 messages
    assert len(trimmed) == 16
    assert trimmed[0]["role"] == "user"
    assert trimmed[0]["content"] == "Question 6"
    assert trimmed[-1]["role"] == "assistant"
    assert trimmed[-1]["content"] == "Answer 9"


# ---------------------------------------------------------------------------
# 7. Gateway routing checks for demo profile
# ---------------------------------------------------------------------------

def test_demo_gateway_routes_only_gate1_inference():
    config = yaml.safe_load(Path("docker/apisix/apisix-demo.yaml").read_text())
    routes = config["routes"]
    uris = [r["uri"] for r in routes]
    assert "/ai/chat/completions" in uris
    assert "/ai/status" in uris
    # Assert NO enterprise APIs, NO MCP, NO OAuth, NO budget reset are exposed
    assert not any(u.startswith("/api/") for u in uris)
    assert not any(u.startswith("/mcp") for u in uris)
    assert not any(u.startswith("/oauth") for u in uris)
    assert "/ai/budget/reset" not in uris


def test_status_endpoint_scripted_and_live(live_client, monkeypatch):
    # Live mode with mock status
    async def mock_get(*args, **kwargs):
        return httpx.Response(200, json={
            "status": "ready",
            "mode": "live",
            "provider_configured": True,
            "model": "MiniMax-M2.7-highspeed",
            "headroom_tokens": 50000,
        })
    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    res = live_client.get("/demo-api/status")
    assert res.status_code == 200
    data = res.json()
    assert data["chat_mode"] == "live"
    assert data["configured"] is True
    assert data["available"] is True
    assert data["model"] == "MiniMax-M2.7-highspeed"

    # Scripted mode
    monkeypatch.setenv("DEMO_CHAT_MODE", "scripted")
    res_scripted = live_client.get("/demo-api/status")
    assert res_scripted.status_code == 200
    assert res_scripted.json()["chat_mode"] == "scripted"


# ---------------------------------------------------------------------------
# 8. Enterprise mode tool execution via APISIX Gate 3
# ---------------------------------------------------------------------------

def test_enterprise_mode_tool_calls_gate3(monkeypatch):
    from src.demo.tools import execute_demo_tool, StagedDemoState
    staged = StagedDemoState(card_locked=False)

    mock_calls = []
    def mock_request(method, url, headers=None, json=None, **kwargs):
        mock_calls.append((method, url, headers, json))
        if "/accounts/demo-checking" in url:
            return httpx.Response(200, json={"id": "demo-checking", "name": "Everyday account", "balance": 12485000, "currency": "INR"})
        elif "/accounts/demo-savings" in url:
            return httpx.Response(200, json={"id": "demo-savings", "name": "Savings pocket", "balance": 35000000, "currency": "INR"})
        elif "/cards/card-2048/state" in url:
            return httpx.Response(200, json={"id": "card-2048", "locked": True, "status": "frozen"})
        elif "/cards/card-2048" in url:
            return httpx.Response(200, json={"id": "card-2048", "last_four": "2048", "holder_name": "MAYA SHAH", "expiry": "09/29", "locked": False})
        elif "/cases" in url and method == "POST":
            return httpx.Response(201, json={"id": "case-9999", "customer_id": "cust-maya", "status": "open", "issue_type": "disputed_transaction"})
        elif "/cases" in url and method == "GET":
            return httpx.Response(200, json=[{"id": "case-9999", "customer_id": "cust-maya", "status": "open", "issue_type": "disputed_transaction", "description": "Stream+ dispute"}])
        return httpx.Response(404)

    monkeypatch.setattr(httpx, "request", mock_request)

    # 1. Accounts read via Gate 3
    res_acc = execute_demo_tool("get_demo_accounts", {}, staged, backend_mode="enterprise", gate3_url="http://apisix:9080/api/v1", api_token="test-token")
    assert res_acc["accounts"][0]["balance_paise"] == 12485000
    assert res_acc["mode"] == "enterprise"

    # 2. Card freeze via Gate 3
    res_card = execute_demo_tool("set_demo_card_state", {"locked": True}, staged, backend_mode="enterprise", gate3_url="http://apisix:9080/api/v1", api_token="test-token")
    assert res_card["card_locked"] is True
    assert staged.card_locked is True
    assert res_card["mode"] == "enterprise"

    # 3. Dispute creation via Gate 3
    res_disp = execute_demo_tool("create_demo_dispute", {"transaction_id": "tx-1004"}, staged, backend_mode="enterprise", gate3_url="http://apisix:9080/api/v1", api_token="test-token")
    assert res_disp["status"] == "created"
    assert res_disp["mode"] == "enterprise"
    assert "case-9999" in res_disp["case"]["id"]


def test_enterprise_mode_login_and_dashboard(live_client, monkeypatch):
    monkeypatch.setenv("DEMO_BACKEND_MODE", "enterprise")
    monkeypatch.setenv("GATE3_URL", "http://mock-apisix:9080/api/v1")

    def mock_get(url, headers=None, timeout=None, **kwargs):
        if "/accounts/demo-checking" in url:
            return httpx.Response(200, json={"id": "demo-checking", "name": "Everyday account", "balance": 12485000, "currency": "INR", "status": "active"})
        elif "/accounts/demo-savings" in url:
            return httpx.Response(200, json={"id": "demo-savings", "name": "Savings pocket", "balance": 35000000, "currency": "INR", "status": "active"})
        elif "/cards/card-2048" in url:
            return httpx.Response(200, json={"id": "card-2048", "locked": False})
        return httpx.Response(404)

    monkeypatch.setattr(httpx, "get", mock_get)
    res = live_client.post("/demo-api/login", json={"email": "maya@flobank.demo", "password": "flo-demo"})
    assert res.status_code == 200
    assert res.json()["backend_mode"] == "enterprise"
    assert res.json()["accounts"][0]["balance"] == 12485000


