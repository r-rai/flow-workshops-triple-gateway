# Technical POC / Spike Plan

Validate the risky assumptions before building the complete NovaBank
platform.

## Spike 1 --- APISIX Standalone + OpenAPI-to-MCP

Prove standalone APISIX supports the selected plugins and can expose a
minimal FastAPI OpenAPI contract through `tools/list` and `tools/call`.

Minimal API:

``` text
GET /api/v1/accounts/{id}
POST /api/v1/payments
```

## Spike 2 --- Gate 2 -\> Gate 3 Loopback

Prove MCP-generated REST calls re-enter the APISIX API route before
FastAPI. A request through MCP must not bypass Gate 3 policy.

## Spike 3 --- Argument-Aware OPA

Given:

``` json
{
  "method": "tools/call",
  "params": {
    "name": "createPayment",
    "arguments": {"amount": 500000}
  }
}
```

prove policy can use method, tool, nested arguments and identity
context. Define explicitly how an approval-required decision is
represented and enforced.

## Spike 4 --- Identity Propagation

Prove token/context propagation from agent -\> `/mcp` -\> `/api` -\>
FastAPI. Then validate the selected Keycloak delegated/token-exchange
scenario before Workshop 4 is frozen.

## Spike 5 --- Trace Stitching

Prove W3C trace context survives LangGraph -\> inference gate, LangGraph
-\> capability gate, capability -\> API gate, and API gate -\> FastAPI.
Inspect the complete waterfall in Jaeger.

## Spike 6 --- Hardware Benchmark

Test Windows 11 / 16 GB with WSL2 near a 5 GB cap and 4 processors.
Record startup time, idle/active memory, CPU peak, restart behavior and
total WSL footprint for every workshop profile.

Do not publish estimated memory figures as guarantees until this
benchmark is complete.

## Exit Condition

Proceed to the full platform only when the unified-gateway security
invariants and participant hardware envelope are proven.
