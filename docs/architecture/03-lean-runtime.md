# Lean Workshop Runtime

Status: planned, not benchmarked. The [VPS guide](../setup/vps-setup-guide.md)
is the source of truth for memory limits, networking, and operator behavior.

Target participant: Windows 11, 16 GB RAM, four CPU cores, WSL2 capped near
5 GB. Target presenter: one active workshop within a 6 GB total host budget.
Neither envelope is a proven capacity claim until rehearsed.

| Component | W1 | W2 | W3 | W4 |
|---|---|---|---|---|
| APISIX standalone | Yes | Yes | Yes | Yes |
| FastAPI | Yes | Yes | Yes | Yes |
| Agent/client or worker | Yes | Yes | Yes | Yes |
| Curated MCP adapter | No | Yes | Yes | Yes |
| SQLite application data | Yes | No | No | No |
| OPA | No | Yes | Yes | Yes |
| Keycloak | No | Yes | No | Yes |
| PostgreSQL | No | Yes | Yes | Yes |
| Kafka KRaft | No | No | Yes | No |
| Temporal development server, persistent SQLite | No | No | Yes | Yes |
| OTel Collector and Jaeger | Optional presenter add-on | Yes | Yes | Yes |

Redis is not required. Database transactions handle idempotency. Kafka is
exclusive to W3. No local LLM or full observability stack is required.
W1 optional tracing is outside its base budget and must be measured if enabled.

Initial summed container limits: W1 1,152 MiB; W2 3,072 MiB; W3/W4 3,584 MiB.
Leave remaining host capacity for the OS, Docker, existing services and peaks.

Use prebuilt images and bounded logs, traces, model calls and JVM memory.
SQLite is embedded. W2/W4 use real identity; W3 uses separately scoped signed
lab credentials with the simplification stated explicitly.

The planned entrypoint is `./scripts/workshop start w1`. Switching must stop
the prior profile; Compose profile activation alone does not do this. The
presenter VPS is a demonstration and limited fallback environment, with an
initial cap of two isolated concurrent fallback runs pending load testing.
