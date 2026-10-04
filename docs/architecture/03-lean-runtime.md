# Lean Workshop Runtime

The current runtime is implemented in the main `docker-compose.yml`. See the
[VPS runbook](../setup/vps-setup-guide.md) for service sets, actual configured
memory limits, ingress, and operator commands. Recorded Linux rehearsals are
available; the Windows/WSL2 participant memory benchmark remains unverified.

The laptop target for full workshop labs is Windows 11, 16 GB RAM, four CPU
cores, and WSL2 capped near 5 GB. The presenter operating budget is 6 GB total,
including existing services and the OS.

| Component | Demo | W1 | W2 | W3 | W4 |
|---|---|---|---|---|---|
| Customer UI and scripted bot | Yes | Yes, via API | Yes, via API | Yes, via API | Yes, via API |
| APISIX standalone | No | Yes | Yes | Yes | Yes |
| Core banking API | No | Yes | Yes | Yes | Yes |
| Curated MCP adapter | No | No | Yes | Yes | Yes |
| OPA | No | No | Yes | Yes | Yes |
| PostgreSQL service | No | No | Yes | Yes | Yes |
| Kafka KRaft | No | No | No | Yes | Yes |
| Temporal dev server with persistent SQLite | No | No | No | Yes | Yes |
| Jaeger | No | No | Yes | Yes | Yes |
| Background worker | No | No | No | Yes | Yes |

The API defaults to SQLite; selecting PostgreSQL requires an explicit
`DATABASE_URL`. Keycloak and a separate OTel Collector are not included in the
current Compose service set. Lab JWTs and restricted token exchange provide the
workshop identity flow; instrumentation exports directly to Jaeger. Redis and
a local LLM are not required.

Summed configured container limits are 256 MiB for `demo`, 640 MiB for W1,
1,664 MiB for W2, and 3,072 MiB for W3/W4. These are caps, not measured usage or
host-capacity guarantees. Leave headroom for Docker, the OS, and other services.

Start the customer simulation with
`docker compose --profile demo up -d --build`; it needs no extra shell scripts
or provider keys. Start a workshop with its matching profile and gateway
`ACTIVE_PROFILE` setting. The optional `scripts/workshop` launcher handles
warm-up and profile switching. Compose profile activation alone does not stop
services from the prior workshop.

The standalone customer bot uses fictional session state and never calls the
enterprise ledger or model provider. Workshop W3 runs a separate bounded
LangGraph investigation inside a Temporal activity, with explicit replay/live
modes and deterministic downstream authorization. The initial presenter
fallback limit is two isolated concurrent runs, pending load testing.
