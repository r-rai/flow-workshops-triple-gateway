# Reference Architecture

``` text
Users / MCP Clients
        |
        v
+------------------------+
| LangGraph Agent        |
+-----+-------------+----+
      |             |
  inference         MCP
      |             |
      v             v
+-----------------------------------------------+
| Apache APISIX                                 |
| Gate 1: Inference | Gate 2: MCP | Gate 3: API|
+-----+----------------+---------------+---------+
      |                |               |
      v                v               v
 LLM Provider         OPA          NovaBank APIs
                                      |
                              PostgreSQL / Redis

Identity: Keycloak
Events: Kafka
Durability/HITL: Temporal
Telemetry: OpenTelemetry -> Jaeger
```

## Responsibilities

-   **APISIX:** traffic enforcement.
-   **FastAPI:** NovaBank enterprise APIs and OpenAPI contracts.
-   **LangGraph:** agent orchestration/state; not authorization.
-   **OPA:** deterministic policy decisions.
-   **Keycloak:** identity, OAuth/OIDC, scopes and delegated-identity
    demonstrations.
-   **Kafka:** event distribution.
-   **Temporal:** durable workflows, retries, timers and HITL.
-   **PostgreSQL/SQLite:** application persistence.
-   **Redis:** optional transient state/idempotency.
-   **OpenTelemetry:** instrumentation/context propagation.
-   **Jaeger:** lean workshop trace storage/query/UI.

A unified gateway does not imply that identity, policy, orchestration,
durability or business invariants belong inside the gateway.
