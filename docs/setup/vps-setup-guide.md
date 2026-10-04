# VPS Infrastructure Setup Guide

## Current runtime

The runtime, main Compose file, customer dashboard, and workshop launcher are
implemented on `main`. This runbook describes the current configuration; recorded
workshop evidence and remaining requirements are in
[`config/manifest.json`](../../config/manifest.json). The Windows/WSL2 memory
benchmark remains unverified. Keep the presenter deployment within the **6 GB
host operating budget**, including existing services, Docker, and the OS.

Flo Bank is the public brand. Internal `novabank` project, network, volume, issuer,
and audience names remain compatible with existing installations. Historical
audit evidence retains its original branding.

## 1. Customer demo with one Compose command

Docker Engine with Compose is sufficient for the customer simulation:

```bash
docker compose --profile demo up -d --build
```

Open **http://localhost:8000** and use `maya@flobank.demo` / `flo-demo`.
The standalone profile runs a three-service topology (`demo`, `demo-gateway`, `demo-inference`).
When configured with `MINIMAX_API_KEY` in `.env`, Flo connects to live hosted LLM inference
(`MiniMax-M2.7-highspeed` - MiniMax 2.7 Fast) via APISIX Gate 1; otherwise, it falls back gracefully to deterministic scripted replies.
Fictional banking data is session-scoped. Sessions expire after 30 minutes and reset on sign-out or process restart.

For live APISIX Gate 3 integration against real Core Banking SQLite/PostgreSQL data:
```bash
docker compose --profile demo-enterprise up -d --build
```

Check status or stop the demo:

```bash
docker compose --profile demo ps
docker compose logs --tail 50 demo
docker compose --profile demo down
```

For complete step-by-step instructions for all workshop profiles and teardown procedures, see the [Participant Infrastructure Guide](../workshops/participant-infra-guide.md).

The host binding defaults to `127.0.0.1:8000`; change `DEMO_HTTP_PORT` in `.env`
if this port is occupied. For remote access, forward the selected port over SSH:

```bash
ssh -N -L 8000:127.0.0.1:8000 USER@VPS_HOST
```

Replace the SSH target and ports with your own values. Keep existing Caddy,
Portainer, Uptime Kuma, and Dozzle services running; no host proxy changes are
required by this setup.

## 2. Workshop profiles and resources

All profiles use the original `docker-compose.yml`:

| Profile | Compose services | Sum of configured container memory limits |
|---|---|---:|
| `demo` | demo, demo-gateway, demo-inference | 896 MiB |
| `demo-enterprise` | demo, apisix, api, adapter | 1,152 MiB |
| `w1` | apisix, api | 640 MiB |
| `w2` | apisix, api, adapter, opa, postgres, jaeger | 1,664 MiB |
| `w3` | W2 services plus temporal, kafka, worker | 3,072 MiB |
| `w4` | Same container set as W3; A2A exercises use additional clients | 3,072 MiB |

These are configured caps, not measured consumption or host-memory guarantees.
Use `docker stats --no-stream` to measure actual usage and leave headroom for
existing services and transient peaks. The API and demo each have a 256 MiB
limit; APISIX, PostgreSQL, and Temporal each have 384 MiB; adapter and Jaeger
have 256 MiB; OPA has 128 MiB; Kafka and worker each have 512 MiB.

APISIX uses standalone declarative configuration. Keycloak, a separate
OpenTelemetry Collector, Redis, and a local LLM are not Compose services in
this implementation. Workshops use signed lab JWTs, distinct MCP/API audiences,
and an RFC 8693 token-exchange endpoint. Application instrumentation exports
traces directly to Jaeger where configured. The shared W4 worker deployment
includes Kafka even though the A2A exercise itself does not need Kafka events.

The application defaults to embedded SQLite in all profiles. PostgreSQL is
provisioned in W2–W4, but using it for the API requires setting `DATABASE_URL`.
Persistent API, PostgreSQL, and Temporal data use separate named volumes.

For Workshop 1, the direct Compose startup is:

```bash
docker compose --profile w1 up -d --build
```

The UI is available at **http://localhost:9080**, through the gateway. The
`ACTIVE_PROFILE` setting chooses `docker/apisix/apisix-<profile>.yaml` and
defaults to `w1`; match it to the selected profile in `.env` for W2–W4.
Compose activation alone does not stop prior-profile containers. Run one
workshop profile at a time and use the operator launcher for managed switching.

## 3. Preflight and configuration

Before starting a workshop, inspect occupied ports and available resources:

```bash
git status --short
docker version
docker compose version
docker ps --format '{{.Names}}\t{{.Status}}\t{{.Ports}}'
docker stats --no-stream
free -m
df -h /
ss -ltn
```

Keep administrative ports on loopback. Gateway HTTP defaults to 9080, Jaeger UI
to 16686, Kafka to 9092, and Temporal to 7233. Forward only the required ports
over SSH. The core API has no published host port; adapter and worker banking
calls go through APISIX Gate 3, rather than directly to the backend network.

For workshop configuration, copy `.env.example` to the ignored `.env` file and
adjust the chosen profile and ports. Do not print raw Git remote URLs or dump
container environments: they may contain credentials. The sample signing/API
keys are for local labs, and provider keys must stay in ignored configuration.

Replay is the default (`USE_REPLAY_FIXTURES=true`). For live W3 inference, set
`USE_REPLAY_FIXTURES=false`, `MINIMAX_API_KEY`, and the desired provider/model
settings. Recreate affected services after changing environment values. The
worker calls Gate 1 through APISIX; only the adapter needs the provider key.
Live calls consume provider quota. The customer UI's Flo bot remains scripted
in either workshop mode.

## 4. Optional workshop operator launcher

The Bash launcher adds readiness polling, MCP warm-up, smoke verification,
profile switching, and an explicit lab reset. Prepare its Python environment:

```bash
python3.12 -m venv .venv
.venv/bin/pip install -r docker/api/requirements.txt -r docker/worker/requirements.txt
```

Then run the existing operator commands:

```bash
./scripts/workshop pull w1
# Global preflight inspects every pinned third-party image, including W2–W4.
docker compose --profile w3 pull --ignore-buildable
./scripts/workshop preflight
./scripts/workshop start w1
./scripts/workshop status
./scripts/workshop verify w1
./scripts/workshop switch w2
./scripts/workshop reset w2
./scripts/workshop stop
```

`pull PROFILE` builds the application images and pulls the profile's third-party
images. The current global `preflight` checks every pinned third-party image,
so the W3 pull above downloads the full pinned set on a fresh host without
starting any services. `start PROFILE` refuses a conflicting active profile and waits for
backend and MCP readiness. `verify PROFILE` runs its smoke checks. `switch`
stops the workshop project before starting the target; named volumes are
preserved. `reset` restores seeded lab data after confirmation. `stop` leaves
persistent data intact. Run these commands under Linux/WSL with Bash, Python
3.12, Docker/Compose, curl, and the usual Linux resource utilities available.

The launcher targets workshop profiles, not `demo`. Use the direct Compose
commands in section 1 for the customer simulation.

## 5. Verification and recovery

Local automated tests use pytest in the prepared Python environment:

```bash
.venv/bin/pip install pytest pytest-asyncio
.venv/bin/python -m pytest tests -q
```

Customer API/session checks live in `tests/test_demo_bank.py`; the optional
Playwright browser check is `tests/demo_bank_browser.cjs` (see the root README).
Workshop rehearsal runners and recorded evidence are under `workshops/w1`–`w4`.
Live and replay W3 evidence are separate. Saved evidence describes the recorded
run and should not be presented as a fresh verification of every deployment.

| Failure | Recovery and check |
|---|---|
| Demo port occupied | Set a free `DEMO_HTTP_PORT`, recreate demo, open that port |
| Provider unavailable or quota exhausted | Explicitly choose replay and recreate affected services; never label replay as live |
| OPA unavailable | Tool calls fail closed; restore OPA and retry |
| Worker crash | Restart worker; inspect durable workflow and idempotent settlement |
| Temporal restart | Reopen its persistent database and inspect workflow state |
| Lab data needs reset | Retain evidence and run the confirmed workshop reset |
| OOM or sustained swap | Stop the workshop project, inspect host usage, and repeat the capacity check |

Avoid image builds and downloads during a workshop. Capacity for concurrent
fallback runs and the Windows/WSL2 participant benchmark still require separate
measurement. This development topology is not a production deployment recipe.

See the [delivery plan](../workshops/delivery-plan.md),
[facilitator guide](../workshops/facilitator-guide.md), and
[implementation handoff](../implementation/agent-handoff.md).
