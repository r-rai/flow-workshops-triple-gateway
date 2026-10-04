# Solution Overview

## Flo Bank

All workshops use one fictional enterprise, **Flo Bank**, with
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

W2–W4 add a curated MCP adapter between Gate 2 and Gate 3 for argument-aware
OPA policy and downstream credentials. W1 demonstrates native OpenAPI-to-MCP
generation. Keycloak runs in W2/W4, Kafka in W3, and Temporal in W3/W4.
PostgreSQL and OpenTelemetry/Jaeger support W2–W4. Redis is not required.

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
Agent -> Gate 2 (/mcp) -> native generator or adapter -> Gate 3 -> FastAPI
```

They must not call FastAPI directly. Exact APISIX loopback behavior is a
POC item.

## Two Deployment Views

**Lean Workshop Edition:** only components needed by the active
exercise.

**Reference Enterprise Edition:** complete architecture used for design
discussion and presenter demonstrations.

See the [delivery plan](workshops/delivery-plan.md),
[VPS guide](setup/vps-setup-guide.md), and
[agent handoff](implementation/agent-handoff.md) for the agreed scope.
