import pytest
import json
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import Response
from src.worker.dispute_agent import (
    validate_proposal_node,
    execute_tools_node,
    route_after_model,
    MAX_TOOL_CALLS,
    MAX_ITERATIONS,
    DisputeState
)

@pytest.mark.asyncio
async def test_invalid_model_output_does_not_fabricate_refund():
    """Finding 1: Invalid model output must not trigger fallback heuristic fabricating a refund."""
    state: DisputeState = {
        "case_id": "case-501",
        "case_data": {
            "id": "case-501",
            "customer_id": "cust-8801",
            "description": "Double charge on account.",
            "issue_type": "dispute"
        },
        "messages": [
            {"role": "assistant", "content": "I could not parse anything or decide."}
        ],
        "iterations": 1,
        "tool_calls_count": 0,
        "total_tokens": 100,
        "tool_results": [],
        "proposal": None,
        "error": None,
        "is_complete": False
    }

    res = await validate_proposal_node(state)
    proposal = res.get("proposal", {})
    # Must NOT fabricate a 75000 refund for case-501
    assert proposal.get("amount", 0) == 0, f"Expected amount 0 on invalid model output, got {proposal.get('amount')}"
    # Must explicitly indicate failure
    assert proposal.get("status") == "FAILED" or proposal.get("error") is not None
    assert "error" in proposal or proposal.get("status") == "FAILED"

@pytest.mark.asyncio
async def test_iteration_exhaustion_does_not_fabricate_refund():
    """Finding 1: Iteration exhaustion without valid proposal must result in investigation failure."""
    state: DisputeState = {
        "case_id": "case-501",
        "case_data": {
            "id": "case-501",
            "customer_id": "cust-8801",
            "description": "Double charge on account.",
            "issue_type": "dispute"
        },
        "messages": [
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [{"id": "call-6", "function": {"name": "get_case", "arguments": '{"id":"case-501"}'}}]
            }
        ],
        "iterations": 6,
        "tool_calls_count": 5,
        "total_tokens": 600,
        "tool_results": [{"tool": "get_case", "status": "SUCCESS"}],
        "proposal": None,
        "error": None,
        "is_complete": False
    }

    res = await validate_proposal_node(state)
    proposal = res.get("proposal", {})
    assert proposal.get("amount", 0) == 0, f"Exhaustion must not fabricate refund, got {proposal.get('amount')}"
    assert proposal.get("status") == "FAILED" or proposal.get("error") is not None

@pytest.mark.asyncio
async def test_inconsistent_case_id_and_currency_rejected():
    """Finding 2: Inconsistent case ID and non-INR currency must be rejected, not silently rewritten."""
    state: DisputeState = {
        "case_id": "case-501",
        "case_data": {
            "id": "case-501",
            "customer_id": "cust-8801",
            "description": "Double charge on account.",
            "issue_type": "dispute"
        },
        "messages": [
            {
                "role": "assistant",
                "content": json.dumps({
                    "case_id": "case-999", # foreign case ID
                    "customer_id": "cust-8801",
                    "amount": 25000,
                    "currency": "USD", # foreign currency
                    "destination_account": "acc-101",
                    "rationale": "Refund in USD for wrong case"
                })
            }
        ],
        "iterations": 2,
        "tool_calls_count": 2,
        "total_tokens": 200,
        "tool_results": [{"tool": "get_account", "status": "SUCCESS", "arguments": {"id": "acc-101"}}],
        "proposal": None,
        "error": None,
        "is_complete": False
    }

    res = await validate_proposal_node(state)
    proposal = res.get("proposal", {})
    assert proposal.get("status") == "FAILED" or proposal.get("error") is not None
    assert proposal.get("amount", 0) == 0, "Mismatched case ID or currency must not produce payable proposal"

@pytest.mark.asyncio
async def test_unauthorized_destination_account_rejected():
    """Finding 2: Payment destination must be trusted/associated with customer, not arbitrary recipient."""
    state: DisputeState = {
        "case_id": "case-501",
        "case_data": {
            "id": "case-501",
            "customer_id": "cust-8801",
            "description": "Double charge on account.",
            "issue_type": "dispute"
        },
        "messages": [
            {
                "role": "assistant",
                "content": json.dumps({
                    "case_id": "case-501",
                    "customer_id": "cust-8801",
                    "amount": 25000,
                    "currency": "INR",
                    "destination_account": "unrelated-recipient", # unauthorized recipient
                    "rationale": "Transfer to unknown account"
                })
            }
        ],
        "iterations": 2,
        "tool_calls_count": 2,
        "total_tokens": 200,
        "tool_results": [{"tool": "get_case", "status": "SUCCESS", "arguments": {"id": "case-501"}}],
        "proposal": None,
        "error": None,
        "is_complete": False
    }

    res = await validate_proposal_node(state)
    proposal = res.get("proposal", {})
    assert proposal.get("status") == "FAILED" or proposal.get("error") is not None
    assert proposal.get("amount", 0) == 0

@pytest.mark.asyncio
async def test_payable_proposal_requires_successful_read_evidence():
    """Finding 2: Payable proposal without relevant successful read evidence must fail."""
    state: DisputeState = {
        "case_id": "case-501",
        "case_data": {
            "id": "case-501",
            "customer_id": "cust-8801",
            "description": "Double charge on account.",
            "issue_type": "dispute"
        },
        "messages": [
            {
                "role": "assistant",
                "content": json.dumps({
                    "case_id": "case-501",
                    "customer_id": "cust-8801",
                    "amount": 25000,
                    "currency": "INR",
                    "destination_account": "acc-101",
                    "rationale": "Refund without checking evidence"
                })
            }
        ],
        "iterations": 1,
        "tool_calls_count": 0,
        "total_tokens": 100,
        "tool_results": [], # zero read evidence
        "proposal": None,
        "error": None,
        "is_complete": False
    }

    res = await validate_proposal_node(state)
    proposal = res.get("proposal", {})
    assert proposal.get("status") == "FAILED" or proposal.get("error") is not None
    assert proposal.get("amount", 0) == 0

@pytest.mark.asyncio
async def test_oversized_tool_call_batch_enforces_limit_before_each_call():
    """Finding 4: Single message with 9 tool calls must respect MAX_TOOL_CALLS (8) and not execute 9th."""
    tool_calls = [
        {"id": f"tc-{i}", "type": "function", "function": {"name": "get_account", "arguments": '{"id":"acc-101"}'}}
        for i in range(9)
    ]
    state: DisputeState = {
        "case_id": "case-501",
        "case_data": {"id": "case-501", "customer_id": "cust-8801"},
        "messages": [
            {"role": "assistant", "tool_calls": tool_calls}
        ],
        "iterations": 1,
        "tool_calls_count": 0,
        "total_tokens": 100,
        "tool_results": [],
        "proposal": None,
        "error": None,
        "is_complete": False
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"result": {"content": [{"text": '{"balance": 1500000}'}], "isError": False}}

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        res = await execute_tools_node(state)

        # Total tool calls executed must not exceed MAX_TOOL_CALLS (8)
        assert mock_post.call_count <= MAX_TOOL_CALLS, f"Expected at most {MAX_TOOL_CALLS} calls, got {mock_post.call_count}"
        assert res["tool_calls_count"] <= MAX_TOOL_CALLS or res.get("error") is not None

@pytest.mark.asyncio
async def test_workflow_investigation_failure_does_not_close_or_reject_dispute():
    """Finding 3: Investigation failure must not auto-approve settlement or reject/close dispute case."""
    from src.worker.workflow import DisputeResolutionWorkflow, DisputeInput

    wf = DisputeResolutionWorkflow()
    # Mock activities executed inside workflow
    mock_case = {"id": "case-501", "customer_id": "cust-8801", "status": "open"}
    failed_proposal = {
        "status": "FAILED",
        "case_id": "case-501",
        "customer_id": "cust-8801",
        "amount": 0,
        "destination_account": "none",
        "rationale": "Investigation failed due to Gate 1 HTTP 503",
        "requires_approval": False,
        "error": "Gate 1 AI Gateway returned HTTP 503: Service Unavailable"
    }

    settlement_called = False

    async def fake_execute_activity(activity_fn, *args, **kwargs):
        nonlocal settlement_called
        fn_name = getattr(activity_fn, "__name__", str(activity_fn))
        if "read_dispute_ticket" in fn_name:
            return mock_case
        if "diagnose_and_propose_resolution" in fn_name:
            return failed_proposal
        if "execute_settlement_and_notify" in fn_name:
            settlement_called = True
            return {"case_id": "case-501", "status": "REJECTED"}
        return {}

    with patch("temporalio.workflow.execute_activity", side_effect=fake_execute_activity):
        res = await wf.run(DisputeInput(case_id="case-501"))

        # Settlement activity MUST NOT be called on investigation failure
        assert not settlement_called, "Settlement must NOT be executed when investigation fails!"
        assert wf.current_phase in ("INVESTIGATION_FAILED", "BLOCKED")
        assert res["phase"] in ("INVESTIGATION_FAILED", "BLOCKED")
        assert res["result"]["status"] == "INVESTIGATION_FAILED"

@pytest.mark.asyncio
async def test_concurrent_budget_admission():
    """Finding 4: Concurrent requests must reserve budget atomically, preventing budget overruns."""
    from src.adapter.server import app
    import src.adapter.server as adapter_module
    from httpx import AsyncClient, ASGITransport, Response

    # Configure a 1000-token budget with 900 tokens already used
    adapter_module.INFERENCE_BUDGET_TOKENS = 1000
    adapter_module._accumulated_tokens = 900

    original_post = AsyncClient.post

    async def mock_upstream_post(self, *args, **kwargs):
        # Only intercept upstream provider post calls (e.g. minimax), not ASGI test client requests
        if args and "minimax.io" in str(args[0]):
            await asyncio.sleep(0.05)
            mock_body = {
                "choices": [{"message": {"role": "assistant", "content": "Done"}}],
                "usage": {"total_tokens": 300, "prompt_tokens": 150, "completion_tokens": 150}
            }
            return Response(200, json=mock_body)
        return await original_post(self, *args, **kwargs)

    with patch.dict("os.environ", {"USE_REPLAY_FIXTURES": "false", "MINIMAX_API_KEY": "valid-test-key"}), \
         patch.object(AsyncClient, "post", mock_upstream_post):

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            req_payload = {
                "messages": [{"role": "user", "content": "Investigate dispute"}]
            }
            res1, res2 = await asyncio.gather(
                ac.post("/ai/chat/completions", json=req_payload),
                ac.post("/ai/chat/completions", json=req_payload)
            )

            status_codes = [res1.status_code, res2.status_code]
            # Atomic reservation prevents concurrent over-admission: at least one must be 429!
            assert 429 in status_codes, f"Expected 429 for concurrent budget overrun, got {status_codes}"
            assert 200 in status_codes, f"Expected one successful request, got {status_codes}"

