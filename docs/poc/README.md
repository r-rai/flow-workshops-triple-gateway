# Technical POC / Spike Plan

Validate the risky assumptions before building the complete Flo Bank
platform.

See the [agent handoff](../implementation/agent-handoff.md) for contracts and
work-package dependencies. All compatibility spikes (Spikes 1, 2, 3, 4, 5, 7)
have been implemented and verified on the Linux VPS baseline. Full report and
evidence are recorded in [01-compatibility-spikes-report.md](01-compatibility-spikes-report.md).
Hardware benchmark on Windows/WSL2 remains pending participant environment.

## Spike 1 --- APISIX Standalone + OpenAPI-to-MCP

Start with APISIX 3.19.0 and Streamable HTTP. Prove standalone APISIX supports the selected plugins and can expose a
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

prove the curated MCP adapter validates and normalizes arguments, then passes
method, tool, arguments and trusted identity to OPA. Do not assume the stock
APISIX OPA plugin supplies request-body fields. Define explicitly how an approval-required decision is
represented and enforced.

## Spike 4 --- Audience-Separated Identity

Validate the MCP-facing token, exchange for a restricted API-facing token,
and prove Gate 3 rejects wrong audiences or insufficient scopes. Preserve
trusted subject/caller context without token passthrough. Validate Keycloak
client-scope configuration and distinguish standard exchange from preview
actor/delegation behavior before Workshop 4 is frozen.

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

## Spike 7 --- A2A and Approval

Validate a pinned A2A SDK/protocol with Agent Card discovery, authenticated
task submission, and owner-scoped task access. Prove another principal cannot
read or mutate the task. Validate approval binding and retry-safe execution
in the backend.

## Exit Condition

Proceed with dependent implementation only after its security/compatibility
spikes pass. Record minimal memory feasibility first; complete full-profile
and Windows/WSL benchmarks after the profiles exist and before release.
