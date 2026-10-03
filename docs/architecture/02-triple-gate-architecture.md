# Triple-Gate Architecture

Triple-Gate Architecture means **three logical enforcement boundaries**,
not three mandatory gateway products.

## Gate 1 --- Inference

`Agent -> APISIX /ai/* -> LLM`

Controls model/provider access, inference quotas, prompt/input controls
and AI telemetry. It does not authorize enterprise actions.

## Gate 2 --- Capability

`Agent -> APISIX /mcp -> MCP Tool`

Controls tool discovery, selective exposure, tool authorization,
argument-aware policy, agent/user context, approval requirements and
audit.

Example policy input:

``` json
{
  "agent": "negotiator-agent",
  "tool": "createPayment",
  "arguments": {"amount": 500000, "currency": "INR"}
}
```

Policy outcomes may conceptually include ALLOW, DENY or
approval-required. How approval-required is technically
represented/enforced must be designed and tested; it is not assumed
native gateway behavior.

## Gate 3 --- API

`Tool -> APISIX /api/v1/* -> Enterprise API`

Controls OAuth/OIDC/JWT validation, API scopes, validation, rate
limiting, backend routing and conventional API telemetry.

## Loopback Invariant

``` text
tools/call -> Gate 2 -> translated REST request -> Gate 3 -> FastAPI
```

Direct Gate-2-to-FastAPI routing would bypass the API boundary.

## Why One Product?

Separate AI, MCP and API gateway products add memory, containers, hops,
configuration models and failure modes. The workshop teaches separation
of **policy concerns**, not product proliferation.

## Defense in Depth

Gate 1 cannot authorize a payment. Gate 2 cannot replace backend
business invariants. Gate 3 cannot understand all prompt/tool-selection
risks. Prompt instructions and agent graphs are not authorization
controls.
