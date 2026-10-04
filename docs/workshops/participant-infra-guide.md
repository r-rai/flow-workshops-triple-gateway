# Flo Bank Workshop Infrastructure Setup & Teardown Guide

This step-by-step guide is designed for **participants and instructors** to set up, operate, switch between, and cleanly shut down the infrastructure for all Flo Bank workshops and customer demo environments.

---

## 📋 Table of Contents

1. [Hardware & Software Prerequisites](#1-hardware--software-prerequisites)
2. [Initial Environment Setup (One-Time Preparation)](#2-initial-environment-setup-one-time-preparation)
3. [Flo Bank Customer Demo Setup & Teardown](#3-flo-bank-customer-demo-setup--teardown)
   - [Option A: Standalone Simulated Demo (`demo`)](#option-a-standalone-simulated-demo-demo)
   - [Option B: Real API Gateway Enterprise Demo (`demo-enterprise`)](#option-b-real-api-gateway-enterprise-demo-demo-enterprise)
4. [Workshop 1: Core Banking to MCP (`w1`)](#4-workshop-1-core-banking-to-mcp-w1)
5. [Workshop 2: Governance, OPA & Security (`w2`)](#5-workshop-2-governance-opa--security-w2)
6. [Workshop 3: Durability, Temporal & Kafka (`w3`)](#6-workshop-3-durability-temporal--kafka-w3)
7. [Workshop 4: Triple-Gate Architecture & A2A (`w4`)](#7-workshop-4-triple-gate-architecture--a2a-w4)
8. [Switching Between Workshops & Resetting Lab State](#8-switching-between-workshops--resetting-lab-state)
9. [Complete Infrastructure Teardown & Cleanup](#9-complete-infrastructure-teardown--cleanup)
10. [Troubleshooting & FAQs](#10-troubleshooting--faqs)

---

## 1. Hardware & Software Prerequisites

### System Requirements
- **OS**: Windows 11 (with WSL2), macOS (Sonoma/Sequoia), or Linux (Ubuntu 22.04/24.04).
- **RAM**: Minimum 8 GB host RAM (>= 5 GB allocated to Docker / WSL2).
- **Disk**: >= 10 GB free SSD disk space for Docker images, volumes, and build caches.
- **CPU**: 4+ cores recommended.

### Required Software Installed on Host
- **Git** (`git --version` >= 2.30)
- **Docker Desktop** (or Docker Engine on Linux) with **Docker Compose v2** (`docker compose version` >= 2.20)
- **Python 3.12** (recommended for verification scripts and tests)
- **curl** and a modern web browser (Chrome, Edge, Firefox, or Safari)

> [!IMPORTANT]
> **Pre-download before the workshop**: Do not rely on venue or conference Wi-Fi during the live session. Complete Section 2 before arriving at the workshop.

---

## 2. Initial Environment Setup (One-Time Preparation)

### Step 2.1: Clone the Repository
```bash
git clone https://github.com/r-rai/flow-workshops-triple-gateway.git
cd flow-workshops-triple-gateway
git switch main
```

### Step 2.2: Configure Environment Variables
Create your local `.env` configuration file from the sample:
```bash
cp .env.example .env
```

*(Optional)* If you wish to use live LLM inference instead of deterministic fixtures, open `.env` and add your provider key:
```dotenv
MINIMAX_API_KEY="your-minimax-api-key"
```

### Step 2.3: Set Up Python Virtual Environment (For Verification & Tests)
```bash
python3 -m venv .venv
source .venv/bin/activate    # On Windows PowerShell: .venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r docker/api/requirements.txt -r docker/worker/requirements.txt pytest pytest-asyncio
```

### Step 2.4: Pre-Pull Pinned Images & Run Preflight Validation
Download all pinned third-party container images (APISIX, OPA, PostgreSQL, Kafka, Jaeger) in advance:
```bash
docker compose --profile w3 pull --ignore-buildable
./scripts/workshop preflight
```
*Expected Output:* `[OK] Preflight PASSED! Host is ready for workshop execution.`

---

## 3. Flo Bank Customer Demo Setup & Teardown

The Flo Bank customer application serves a modern banking UI with conversational AI assistant **Flo**.

### Option A: Standalone Simulated Demo (`demo`)
Zero-dependency, standalone laptop demo using in-memory session fixtures and Gate 1 AI inference.

1. **Start the Demo:**
   ```bash
   docker compose --profile demo up -d --build
   ```
2. **Access the App:**
   - Open: [http://localhost:8000](http://localhost:8000)
   - Credentials: `maya@flobank.demo` / `flo-demo` (prefilled)
   - Badge: `LIVE AI · MINIMAX-M2.7` (or `SCRIPTED DEMO` if no key is configured).
   - Test actions: Check balances, ask spending questions, freeze/unfreeze debit card, and dispute transaction `tx-1004`.
3. **Shut Down:**
   ```bash
   docker compose --profile demo down
   ```

---

### Option B: Real API Gateway Enterprise Demo (`demo-enterprise`)
Integrates Flo Bank directly with **APISIX Gate 3** (`:9080/api/v1`). Queries live account balances, issues customer JWT tokens, executes card state changes in Core Banking, and creates real support cases in SQLite/Postgres.

1. **Start the Enterprise Demo:**
   ```bash
   docker compose --profile demo-enterprise up -d --build
   ```
2. **Access the App:**
   - Open: [http://localhost:8000](http://localhost:8000) (or via APISIX at [http://localhost:9080](http://localhost:9080))
   - Badge: `LIVE AI · MINIMAX-M2.7 · GATEWAY`
   - Description: `Real model · APISIX Gate 3 Core Banking`
3. **Shut Down:**
   ```bash
   docker compose --profile demo-enterprise down
   ```

---

## 4. Workshop 1: Core Banking to MCP (`w1`)

**Goal:** Transform OpenAPI endpoints into Model Context Protocol (MCP) tool catalogs via APISIX.
- **Containers**: `apisix`, `api`
- **Configured Memory Cap**: ~640 MiB

### Setup & Startup
**Using the Workshop CLI (Recommended on Linux / macOS / WSL2):**
```bash
./scripts/workshop switch w1
```
*Or using native Docker Compose (Cross-platform):*
```bash
# In .env ensure: ACTIVE_PROFILE=w1
docker compose --profile w1 up -d --build
```

### Verification & Interaction
1. **Verify Services:**
   ```bash
   ./scripts/workshop verify w1
   ```
2. **Inspect MCP Tool Endpoints:**
   ```bash
   # Initialize MCP session
   curl -s -X POST http://127.0.0.1:9080/mcp \
     -H "Content-Type: application/json" \
     -H "Accept: application/json, text/event-stream" \
     -d '{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "curl-test", "version": "1.0"}}}'
   ```
3. **Run Participant Lab Script:**
   ```bash
   PYTHONPATH=. .venv/bin/python workshops/w1/client.py
   ```

### Teardown
```bash
./scripts/workshop stop
# Or: docker compose --profile w1 down
```

---

## 5. Workshop 2: Beyond API Governance – Securing AI Agents & MCP (`w2`)

**Goal:** Implement Open Policy Agent (OPA) fine-grained authorization, human approval gates, and Jaeger tracing across Gate 2 and Gate 3.
- **Containers**: `apisix`, `api`, `adapter`, `opa`, `postgres`, `jaeger`
- **Configured Memory Cap**: ~1,664 MiB

### Setup & Startup
```bash
./scripts/workshop switch w2
# Or: docker compose --profile w2 up -d --build
```

### Verification & Interaction
1. **Verify Services:**
   ```bash
   ./scripts/workshop verify w2
   ```
2. **Explore Observability & Governance:**
   - **APISIX Gateway**: [http://localhost:9080](http://localhost:9080)
   - **Jaeger Tracing UI**: [http://localhost:16686](http://localhost:16686) (inspect distributed traces tagged with `traceparent`)
   - **Core API Health**: `curl http://127.0.0.1:9080/healthz`
3. **Run Participant Lab Rehearsal:**
   ```bash
   PYTHONPATH=. .venv/bin/python workshops/w2/rehearsal_w2.py
   ```

### Teardown
```bash
./scripts/workshop stop
# Or: docker compose --profile w2 down
```

---

## 6. Workshop 3: Architecting the Agentic Enterprise (`w3`)

**Goal:** Implement durable workflow execution, human-in-the-loop approval pause/resume, worker crash recovery, and Kafka event streaming using Temporal.
- **Containers**: `apisix`, `api`, `adapter`, `opa`, `postgres`, `jaeger`, `temporal`, `kafka`, `worker`
- **Configured Memory Cap**: ~3,072 MiB

### Setup & Startup
```bash
./scripts/workshop switch w3
# Or: docker compose --profile w3 up -d --build
```

### Verification & Interaction
1. **Verify Services:**
   ```bash
   ./scripts/workshop verify w3
   ```
2. **Execute LangGraph Dispute Resolution Agent:**
   ```bash
   # Offline deterministic replay mode (no API key needed):
   USE_REPLAY_FIXTURES=true PYTHONPATH=. .venv/bin/python -m src.worker.dispute_agent

   # Or live MiniMax-M2.7 reasoning (requires MINIMAX_API_KEY in .env):
   USE_REPLAY_FIXTURES=false PYTHONPATH=. .venv/bin/python -m src.worker.dispute_agent
   ```
3. **Run Workshop 3 Rehearsal Suite:**
   ```bash
   PYTHONPATH=. .venv/bin/python workshops/w3/rehearsal_w3.py
   ```

### Teardown
```bash
./scripts/workshop stop
# Or: docker compose --profile w3 down
```

---

## 7. Workshop 4: Triple-Gate Architecture & A2A Security (`w4`)

**Goal:** Defense-in-depth triple-gate architecture, RFC 8693 token exchange, Agent-to-Agent (A2A) task settlement binding, and anti-tampering guards.
- **Containers**: Same topology as W3 (`apisix`, `api`, `adapter`, `opa`, `postgres`, `jaeger`, `temporal`, `kafka`, `worker`)
- **Configured Memory Cap**: ~3,072 MiB

### Setup & Startup
```bash
./scripts/workshop switch w4
# Or: docker compose --profile w4 up -d --build
```

### Verification & Interaction
1. **Verify Services:**
   ```bash
   ./scripts/workshop verify w4
   ```
2. **Inspect Agent Card Discovery:**
   ```bash
   curl -s http://127.0.0.1:9080/.well-known/agent.json | jq .
   ```
3. **Execute Full A2A Negotiation Rehearsal:**
   ```bash
   PYTHONPATH=. .venv/bin/python workshops/w4/rehearsal_w4.py
   ```

### Teardown
```bash
./scripts/workshop stop
# Or: docker compose --profile w4 down
```

---

## 8. Switching Between Workshops & Resetting Lab State

### Switching Between Profiles
Always run **one workshop profile at a time** to respect memory limits:
```bash
./scripts/workshop switch w1
./scripts/workshop switch w2
./scripts/workshop switch w3
./scripts/workshop switch w4
```
*What `switch` does automatically:*
1. Stops previously active workshop containers.
2. Updates `.active_profile` and `.env`.
3. Starts the target profile's container set.
4. Waits for APISIX upstream cache and backend readiness.
5. Warms up the MCP tool registry.

### Resetting Seed Database State
If an exercise modifies database state or accounts and you wish to return to the clean workshop initial seed (`seed/v1_seed.json`):
```bash
./scripts/workshop reset <w1|w2|w3|w4>
```
*Alternatively, call the API directly:*
```bash
curl -X POST "http://127.0.0.1:9080/api/v1/admin/reset" \
  -H "X-API-Key: gate3-secret-token" \
  -H "X-Confirm-Reset: CONFIRM"
```

---

## 9. Complete Infrastructure Teardown & Cleanup

### Clean Teardown (Preserving Data Volumes)
Stops all containers across all profiles without deleting persistent database volumes:
```bash
./scripts/workshop stop
```
*Or via Docker Compose:*
```bash
docker compose --profile demo --profile demo-enterprise --profile w1 --profile w2 --profile w3 --profile w4 down --remove-orphans
```

### Complete Factory Reset (Purging All Lab Volumes)
To remove all containers, networks, and persistent database volumes (`novabank_api_data`, `novabank_postgres_data`, `novabank_temporal_data`):
```bash
docker compose --profile demo --profile demo-enterprise --profile w1 --profile w2 --profile w3 --profile w4 down -v --remove-orphans
```

### Clean Host Storage
If Docker disk space is constrained after building multiple images:
```bash
docker system prune -f
```

---

## 10. Troubleshooting & FAQs

| Issue / Symptom | Root Cause | Solution |
|---|---|---|
| **Port 9080 already in use** | A previous workshop profile or local proxy is occupying port 9080. | Run `./scripts/workshop stop` or check `ss -ltn '( sport = :9080 )'`. |
| **Port 8000 already in use** | Local service listening on 8000. | In `.env`, set `DEMO_HTTP_PORT=8001`, restart demo, and open [http://localhost:8001](http://localhost:8001). |
| **`HTTP 401 Missing API key`** | Request to Gate 3 omitted required key-auth header. | Include `-H "X-API-Key: gate3-secret-token"` in requests to `:9080/api/v1/*`. |
| **`HTTP 401 Insufficient scope`** | JWT token does not have required permissions. | Ensure JWT was minted with the appropriate scope (e.g. `api:cards:read`, `api:payments:write`). |
| **Model request timeout (504)** | Upstream LLM provider latency or missing API key. | For deterministic lab execution without external latency, set `USE_REPLAY_FIXTURES=true` or `DEMO_CHAT_MODE=scripted`. |
| **Container memory killed (OOM)** | Running multiple workshop profiles simultaneously or host has < 5 GB RAM. | Ensure only one profile is active at a time. Increase Docker Desktop memory allocation in settings. |
| **APISIX 404 Route Not Found** | APISIX loaded the wrong profile YAML configuration. | Verify `.env` has matching `ACTIVE_PROFILE=<profile>` and restart APISIX: `docker compose restart apisix`. |
