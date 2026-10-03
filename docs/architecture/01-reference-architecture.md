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
                              PostgreSQL / SQLite

Identity: Keycloak
Events: Kafka
Durability/HITL: Temporal
Telemetry: OpenTelemetry -> Jaeger
```

## Responsibilities

-   **APISIX:** traffic enforcement.
-   **FastAPI:** NovaBank enterprise APIs and OpenAPI contracts.
-   **LangGraph:** agent orchestration/state; not authorization.
-   **OPA:** deterministic policy decisions using adapter-supplied trusted identity and arguments.
-   **Keycloak:** identity, OAuth/OIDC, scopes and delegated-identity
    demonstrations.
-   **Kafka:** event distribution.
-   **Temporal:** durable workflows, retries, timers and HITL.
-   **PostgreSQL/SQLite:** application persistence.
-   **MCP adapter:** curated tools, argument policy, and downstream identity in W2–W4.
-   **Idempotency:** backend database transactions; Redis is not required.
-   **OpenTelemetry:** instrumentation/context propagation.
-   **Jaeger:** lean workshop trace storage/query/UI.

A unified gateway does not imply that identity, policy, orchestration,
durability or business invariants belong inside the gateway.

The diagram is a logical reference view. In W2–W4, Gate 2 routes to the MCP
adapter, which consults OPA and re-enters Gate 3; OPA is not an API proxy.
Temporal owns durable progress and executes LangGraph reasoning in activities.
Use the [lean runtime](03-lean-runtime.md) for actual profile composition.
