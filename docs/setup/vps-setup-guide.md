# VPS Infrastructure Setup Guide

## Status and operating assumptions

This is an implementation runbook, not evidence of a deployed platform. The application, Compose files, images, and `scripts/workshop` commands described below must still be built. Do not run future commands until their work package is complete.

Read-only inspection on 2026-10-03 found four CPUs, approximately 7.8 GiB RAM, about 60 GB free disk, and existing Caddy, Portainer, Uptime Kuma, and Dozzle containers. These are a snapshot, not reserved resources. Recheck before deployment and retain the requested **6 GB total host operating budget** (conservatively 6,000,000,000 bytes).

Use one active workshop profile, local participant labs, hosted inference, and deterministic replay. No local LLM, Kubernetes, Redis, Elasticsearch, or full metrics/logging stack is required.

## 1. Preflight and coexistence

From the repository root, collect read-only diagnostics:

```bash
git status --short
docker version
docker compose version
docker ps --format '{{.Names}}\t{{.Status}}\t{{.Ports}}'
docker stats --no-stream
docker network ls
docker volume ls
free -m
df -h /
nproc
ss -ltn
```

Inspect Caddy mounts and network membership without dumping environment variables, private configuration, or credentials. Do not print raw Git remote URLs because they may contain embedded credentials.

Record occupied ports, host memory baseline, Docker/Compose versions, and disk capacity in the implementation evidence. Confirm outbound registry and model-provider access without logging keys. Preserve existing services and port ownership, especially Caddy on 80/443.

## 2. Package and pin the runtime

Create a dedicated Compose project named `novabank-workshops`, a base configuration, explicit `w1`–`w4` profiles, and local/VPS overrides. Use standalone declarative APISIX to avoid etcd, subject to compatibility evidence.

Start the native MCP compatibility spike with APISIX 3.19.0; freeze a tested image digest rather than a floating tag. Record exact versions/digests for every image, Python dependency, MCP/A2A protocol, and telemetry convention after testing. Publish or export prebuilt application images with an immutable manifest; the preflight must verify access before workshop day. Never invent registry/image coordinates in instructions.

Provide health/readiness probes, bounded startup timeouts, versioned seed data, and named volumes. Keep model fixtures in the lightweight application image rather than adding another required service. SQLite is embedded, not a container.

### Initial limits

These are proposed container limits, not measured usage or proven minimums. Enforce limits with the selected Compose version and verify their effective values through Docker inspection.

| Component | Limit |
|---|---:|
| APISIX | 384 MiB |
| NovaBank API | 256 MiB |
| MCP adapter | 256 MiB |
| Agent/worker processes combined | 512 MiB |
| OPA | 128 MiB |
| Keycloak | 768 MiB |
| PostgreSQL | 384 MiB |
| Kafka | 768 MiB |
| Temporal development server | 512 MiB |
| OpenTelemetry Collector | 128 MiB |
| Jaeger | 256 MiB |

| Profile | Services | Sum of limits |
|---|---|---:|
| `w1` | APISIX, API/SQLite, agent/client | 1,152 MiB |
| `w2` | W1 plus adapter, OPA, Keycloak, PostgreSQL, Collector, Jaeger; API uses PostgreSQL | 3,072 MiB |
| `w3` | APISIX, API, adapter, worker, OPA, PostgreSQL, Kafka, Temporal, Collector, Jaeger | 3,584 MiB |
| `w4` | W2 plus Temporal; two agents share the combined worker allowance | 3,584 MiB |

In W3 use workshop-issued signed credentials with mounted verification keys and distinct MCP/API audiences. Label this identity simplification; it does not demonstrate live token exchange.

Reserve the rest of the 6 GB budget for existing services, OS, Docker, cache, and transient peaks. Account for host-level usage, not just `docker stats`. Bound JVM heap below its container cap and leave space for native memory. Swap is an emergency buffer; sustained swapping fails rehearsal.

## 3. Network topology and ingress

```text
Presenter SSH tunnel / optional existing Caddy HTTPS
                         |
                       APISIX
             /ai         /mcp          /api/v1
              |            |               |
       Hosted LLM or    MCP adapter      NovaBank API
       replay fixture      |               |
                           OPA         PostgreSQL/SQLite
                            
Adapter -> restricted API-facing token -> APISIX /api/v1
Keycloak: identity (W2/W4)
Kafka: event ingress (W3)
Temporal: durable workflow/approval (W3/W4)
Collector -> Jaeger: traces (W2/W3/W4)
```

Use separate edge, capability/policy, backend, persistence, and workflow networks. Only APISIX and the API join the backend network; the adapter must not be able to reach the API directly. The API may also join a persistence network, but untrusted agents/adapters must not join that network and gain an alternate API path. Use separate persistence networks where necessary for Keycloak or workers. Test reachability, not just network names.

Give APISIX required external egress for hosted inference and identity discovery; keep data networks internal where feasible. Administrative ports are never public.

Default VPS access is loopback publication and SSH tunnels. Allocate free loopback ports during preflight and document the actual selected values. After implementation, supply a concrete command using these values, for example:

```bash
# Replace placeholders with the recorded SSH target and free ports.
ssh -N -L <local-gateway-port>:127.0.0.1:<vps-gateway-port> <ssh-target>
```

Optional public access uses the existing Caddy instance, a configured workshop hostname, valid TLS, and the application's own authentication. Keep OIDC issuer URLs consistent and reachable from the browser and validating containers. Verify discovery, redirects, JWKS, and token issuer matching before enabling access; do not disable issuer checks to fix tunnel routing. Validate Caddy configuration before reloading it.

Do not publicly publish PostgreSQL, Kafka, OPA, Temporal, Jaeger administration, or APISIX administration. Vulnerable checkpoints are presenter-only/local. Shared fallback runs use only secured checkpoints.

## 4. Configuration, credentials, and data

Create `.env.example` with placeholders and configuration descriptions. Ignore actual secret files and set restrictive permissions. Generate workshop-only credentials; never reuse production or existing VPS credentials.

- Participants keep provider keys on their laptops and configure their local inference gateway.
- Presenter live inference uses a presenter-owned credential; VPS fallback uses replay by default.
- W1 uses separate narrow MCP/API lab credentials. W2/W4 use Keycloak audiences and restricted token exchange.
- Redact authorization headers, provider keys, and tokens. Disable prompt/body capture by default.
- Use named volumes for business data, Keycloak's PostgreSQL database, and Temporal's SQLite database.
- Share the PostgreSQL instance where needed, but use separate databases/users for application and identity data.
- Pin seed versions. Profile switching preserves volumes; each profile has a deterministic seed/reset path and never implicitly migrates another workshop's lab state.

Persisted approval records contain trusted requester/approver identity, canonical proposed arguments, expiry, status, and single-use execution association. API transactions enforce ownership, approval, balance rules, and idempotency.

## 5. Operator interface to implement

The implementing agent must provide and document:

```bash
./scripts/workshop preflight
./scripts/workshop pull w1
./scripts/workshop start w1
./scripts/workshop status
./scripts/workshop verify w1
./scripts/workshop switch w2
./scripts/workshop reset w2
./scripts/workshop stop
```

| Command | Required behavior |
|---|---|
| `preflight` | Check dependencies, memory, disk, ports, image availability, config, and optional provider access; redact secrets |
| `pull PROFILE` | Fetch pinned images from the release manifest; fail clearly if unavailable |
| `start PROFILE` | Refuse a different active profile; start dependencies and wait for readiness with a timeout |
| `status` | Show active profile, health, and resource usage |
| `verify PROFILE` | Run deterministic positive/negative smoke checks and return nonzero on failure |
| `switch PROFILE` | Stop current profile before starting the next; preserve volumes; report failed target startup clearly |
| `reset PROFILE` | Show affected workshop resources, require explicit confirmation, restore only that profile's lab data |
| `stop` | Stop only the `novabank-workshops` project without deleting persistent data |

Compose profile activation does not stop prior-profile containers. The wrapper must explicitly implement switching and reject unsafe profile overlap.

## 6. Bounded operation and fallback

Rotate container logs; cap Kafka retention, Jaeger storage, and Collector queues. Set finite agent iterations, tool calls, model output, and execution time. Record selected values in the release configuration and exercise worksheets. Instrument denied paths as well as successful execution without recording raw secrets.

Start with no more than two remote fallback runs. Allocate distinct identities and isolated seeded data per run; enforce ownership on reads, mutations, approvals, and A2A tasks. Queue further users or use presenter demonstration mode. Do not collect participant LLM keys centrally.

Use existing monitoring services for health and resource visibility. Avoid builds, image pulls, or other heavy maintenance during a session.

## 7. Rehearsal, recovery, and release acceptance

For each workshop: start, verify, reset, pre-warm, validate replay/live inference, inspect traces, and run the complete timed exercise. Measure startup and exercise peaks, existing host load, swap activity, and container restarts. Test the heaviest profile with two fallback runs. Repeat participant rehearsal on Windows/WSL2 capped at 5 GB; a Linux-only run does not prove Windows compatibility.

| Failure | Recovery and proof |
|---|---|
| Provider unavailable/quota exhausted | Select labelled replay; policy/API/workflow behavior still runs |
| OPA unavailable | Deny execution; restore OPA and rerun the request |
| Worker crash | Restart worker; persisted workflow resumes without duplicate effect |
| Temporal restart | Reopen persistent database; approval wait remains intact |
| Lab state corrupted | Export evidence, confirm targeted reset, restore seed |
| OOM or sustained swap | Stop workshop project, diagnose profile/baseline, retune and repeat rehearsal; do not call it a pass |

Before release, export redacted example traces, document actual versions, ports, URLs, image coordinates and measured resource results, and replace future-command placeholders with verified instructions. Keep a last-known-good image/config manifest for rollback. Roll back only workshop resources; database-incompatible rollback uses a documented backup restore or confirmed lab reset, never silently deletes data.

## References

- [APISIX OpenAPI-to-MCP](https://apisix.apache.org/docs/apisix/plugins/openapi-to-mcp/): native generation and transport configuration.
- [Keycloak token exchange](https://www.keycloak.org/securing-apps/token-exchange): audience/scope configuration must be verified explicitly.
- [Temporal self-hosting guidance](https://docs.temporal.io/self-hosted-guide): development server is not a production topology.
- [Workshop delivery plan](../workshops/delivery-plan.md) and [agent handoff](../implementation/agent-handoff.md).
