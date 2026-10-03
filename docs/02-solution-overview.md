# Solution Overview

## NovaBank

All workshops use one fictional enterprise, **NovaBank**, with
customers, accounts, transactions, beneficiaries, payments, support
cases and operational incidents.

## Core Flow

``` text
Users / MCP Clients
        |
        v
   LangGraph Agent
      /       \
  LLM call   MCP call
     |          |
     +---- Apache APISIX ----+
          |       |       |
        Gate 1  Gate 2  Gate 3
        AI      MCP     REST API
          |       |       |
          v       v       v
        LLM      OPA    FastAPI
```

Optional modules add Keycloak, Kafka, Temporal, PostgreSQL, Redis and
OpenTelemetry/Jaeger.

## Three Logical Boundaries

-   **Inference boundary:** model routing, inference limits,
    prompt/input controls and AI telemetry.
-   **Capability boundary:** tool discovery, selective exposure,
    argument-aware authorization and audit.
-   **API boundary:** OAuth/JWT, API scopes, validation, rate limiting,
    routing and backend protection.

## Critical Invariant

MCP-generated REST calls must pass through Gate 3:

``` text
Agent -> Gate 2 (/mcp) -> Gate 3 (/api/v1/*) -> FastAPI
```

They must not call FastAPI directly. Exact APISIX loopback behavior is a
POC item.

## Two Deployment Views

**Lean Workshop Edition:** only components needed by the active
exercise.

**Reference Enterprise Edition:** complete architecture used for design
discussion and presenter demonstrations.
