# Flo Bank Agentic AI Workshop Platform

Open-source-first, self-hosted reference platform for four workshops
covering OpenAPI-to-MCP modernization, AI/MCP governance, durable
event-driven agents, and defense-in-depth security.

## Goals

-   One reusable fictional enterprise and platform across all workshops.
-   Designed for 16 GB Windows participant laptops.
-   Normal exercises target roughly 3--5 GB WSL2/Docker headroom.
-   One physical gateway with three logical security boundaries.
-   Progressive Docker Compose profiles; only required services run.
-   Deterministic authorization remains outside the LLM.
-   End-to-end observability for agent and tool execution.

## Architecture

Apache APISIX is the leading unified-gateway candidate: 1. **Gate 1 ---
Inference:** agent-to-LLM. 2. **Gate 2 --- Capability:**
agent-to-MCP/tool. 3. **Gate 3 --- API:** tool-to-enterprise API.

Supporting components: FastAPI, LangGraph, OPA, Keycloak, Kafka,
Temporal, PostgreSQL/SQLite, OpenTelemetry and Jaeger. Workshops 2–4 add
a lightweight MCP adapter for argument policy and downstream identity.
Kafka runs only in Workshop 3; Redis is not required.

## Documentation

Start here for implementation and delivery:

- [Workshop Delivery Plan](docs/workshops/delivery-plan.md)
- [VPS Infrastructure Setup Guide](docs/setup/vps-setup-guide.md)
- [Implementation Agent Handoff and Copyable Prompt](docs/implementation/agent-handoff.md)

Background and architecture:

-   [Problem Statement](docs/01-problem-statement.md)
-   [Solution Overview](docs/02-solution-overview.md)
-   [Implementation Roadmap](docs/03-implementation-roadmap.md)
-   [Reference
    Architecture](docs/architecture/01-reference-architecture.md)
-   [Triple-Gate
    Architecture](docs/architecture/02-triple-gate-architecture.md)
-   [Lean Workshop Runtime](docs/architecture/03-lean-runtime.md)
-   [Architecture
    Decisions](docs/architecture/04-architecture-decisions.md)
-   [Workshop Mapping](docs/workshops/README.md)
-   [Participant Requirements](docs/setup/participant-requirements.md)
-   [Technical POC](docs/poc/README.md)

## Customer dashboard and chatbot demo

Open a Flo Bank sample account, simulate sign-in, and chat with Flo. The responsive
dashboard includes checking and savings balances, recent transactions, a virtual
card, and a scripted banking assistant. Try a balance query, spending summary,
card freeze/unfreeze, transaction dispute, or dispute-status check.

**With Docker Compose (recommended for laptops):**

The main `docker-compose.yml` includes a `demo` profile. From the repository
root, start the Flo Bank dashboard and chatbot with one command:

```bash
docker compose --profile demo up -d --build
```

Open **http://localhost:8000** and use the prefilled sample login:
`maya@flobank.demo` / `flo-demo`.

Docker Desktop or Docker Engine with Compose is all you need. No local Python,
`.env` setup, LLM key, or additional scripts are required for this profile.
The first build downloads the base image and dependencies.

Stop the demo with:

```bash
docker compose stop demo
```

Demo sessions reset when the container stops. If port 8000 is busy, set
`DEMO_HTTP_PORT=8001` in `.env` and open **http://localhost:8001** instead.
The workshop infrastructure remains in the same Compose file under the
existing `w1`–`w4` profiles.

**Standalone (no Docker or LLM key required):**

```bash
python3 -m venv .venv
.venv/bin/pip install -r docker/api/requirements.txt
.venv/bin/uvicorn src.demo.app:app --host 127.0.0.1 --port 8000
```

Open **http://localhost:8000** and use the prefilled sample login:
`maya@flobank.demo` / `flo-demo`.

**With the workshop infrastructure:** the UI is also available at
**http://localhost:9080** (or your configured APISIX port) in every workshop
profile. To build and start Workshop 1 from the same Compose file:

```bash
docker compose --profile w1 up -d --build
```

The gateway uses `ACTIVE_PROFILE` (default `w1`) to select its configuration.
If `.env` exists, ensure this value matches your chosen workshop profile.
Use `demo` for the standalone simulation or a workshop profile for its
infrastructure; each command uses the main Compose file.

The demo uses fictional fixtures and deterministic responses. It does not call
the live LLM, MCP tools, or enterprise ledger. Demo card controls and disputes
are isolated per session; signing out or restarting the process resets them.
Sessions expire after 30 minutes. Run one API process for this in-memory demo.
This is simulated authentication, not a production customer identity system.

Flo Bank is the public brand throughout the UI, APIs, and workshop material.
Existing `novabank` infrastructure identifiers (JWT audiences/issuer, OPA
namespace, image tags, volumes, and database names) remain for compatibility
with existing installations. Historical audit and rehearsal evidence retains
its original branding.

The customer demo tests are `tests/test_demo_bank.py`. An optional Chromium
smoke test covers login, chat, card controls, disputes, responsive widths,
and delayed-response regressions:

```bash
npm install --prefix /tmp/flo-bank-browser playwright
/tmp/flo-bank-browser/node_modules/.bin/playwright install chromium
# With the standalone server running on port 8000:
NODE_PATH=/tmp/flo-bank-browser/node_modules node tests/demo_bank_browser.cjs
```

## Status

The repository includes the workshop runtime and a customer simulation. See
`config/manifest.json` and the workshop evidence for verification of individual
profiles and remaining participant-hardware requirements.

Target: one active profile within a **6 GB total VPS operating budget**,
with local participant labs and limited replay-based VPS fallback.

> Keep deterministic enterprise controls. Add agent-aware controls
> around them.
