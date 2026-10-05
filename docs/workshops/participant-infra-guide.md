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
- **RAM**: Target 16 GB participant host RAM (>= 5 GB allocated to Docker / WSL2).
- **Disk**: >= 10 GB free SSD disk space for Docker images, volumes, and build caches.
- **CPU**: 4+ cores recommended.

### Required Software Installed on Host
- **Git** (`git --version` >= 2.30)
- **Docker Desktop** (or Docker Engine on Linux) with **Docker Compose v2** (`docker compose version` >= 2.20)
- **Python 3.12** with `venv` and pip (required for workshop Python clients, launcher preflight, verification scripts and tests; optional for Docker-only demos)
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

### Step 2.3: Set Up Python Virtual Environment (For Workshop Clients, Verification & Tests)

Run the launcher in Bash on Linux or WSL; it uses Linux utilities such as
`free` and GNU `sed`. Python clients and direct Docker Compose commands can also
run from Bash on macOS. On Windows,
create the environment inside WSL; the launcher and `.venv/bin/python` commands
below use Unix paths. Docker-only customer demos can skip this Python setup.

From the repository root, using Python 3.12:

```bash
python3 --version
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r docker/api/requirements.txt -r docker/worker/requirements.txt pytest pytest-asyncio
.venv/bin/python -c "import httpx, aiokafka, temporalio, jose; print('Workshop client dependencies ready')"
```

The existing requirements include `httpx` for the W1 MCP client and W2/W4 HTTP
scripts, and `aiokafka`/`temporalio` for the W3 client. Installing dependencies
inside Docker does not install them into your host Python. Use `.venv/bin/python`
for worksheet commands; environment activation is unnecessary. W1 participants
who only run `client.py` can use the [minimal W1 setup](../../workshops/w1/worksheet.md#before-the-session-prepare-the-python-client).

If environment creation reports that `ensurepip` is unavailable on Ubuntu/Debian,
install the `python3-venv` package matching your interpreter (for example,
`python3.12-venv` for Python 3.12), then rerun `python3 -m venv .venv`.

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
   - Badge: `LIVE AI · MINIMAX 2.7 FAST` (`MiniMax-M2.7-highspeed`) or `SCRIPTED DEMO` (if no key is configured).
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
   - Badge: `LIVE AI · MINIMAX 2.7 FAST · GATEWAY`
   - Description: `Real model · APISIX Gate 3 Core Banking`
3. **Shut Down:**
   ```bash
   docker compose --profile demo-enterprise down
   ```

---

## 4. Workshop 1: Modernizing APIs for AI Agents: From OpenAPI to MCP (`w1`)

- **Duration**: 45 minutes
- **Topology**: `apisix` (Gate 2 MCP + Gate 3 API), `api` (Core Banking service)
- **Configured Memory Cap**: ~640 MiB
- **Concept & Description**: Most enterprises already have well-documented REST APIs, but AI agents cannot reliably use them without an interface designed for tool discovery, structured invocation, and safe runtime interaction. This session shows how API architects and integration engineers can transform existing OpenAPI-described services into MCP-based, AI-consumable tools, where automation helps, where curation is essential, and how to preserve governance, security, and observability along the way.
- **Practical Walkthrough**:
  1. Compares OpenAPI and MCP protocols.
  2. Demonstrates automatic MCP server generation from an existing API contract.
  3. Refines tool semantics so agents can use them effectively rather than blindly exposing every endpoint as a tool.
  4. Applies guardrails such as selective exposure, policy controls, and runtime monitoring to preserve the enterprise API boundary.

### Step 1: Switch Profile & Start Workshop 1
```bash
./scripts/workshop switch w1
```
*Or using Docker Compose from Bash:*
```bash
export ACTIVE_PROFILE=w1
docker compose --profile w1 up -d --build
```

### Step 2: Verify Infrastructure Health
```bash
./scripts/workshop verify w1
```
*Expected Output:* `[OK] Verification PASSED for profile w1.`

### Step 3: Initialize MCP Session & Inspect Broad Tool Generation
```bash
# Initialize MCP protocol session over Streamable HTTP:
PYTHONPATH=. .venv/bin/python workshops/w1/client.py init

# Discover all generated tools from the uncurated API contract:
PYTHONPATH=. .venv/bin/python workshops/w1/client.py list
```
*Review Questions:*
- Notice how naive OpenAPI-to-MCP generation exposes dangerous administrative (`/admin/reset`) and mutation endpoints (`/payments`) to autonomous LLMs without curation.

### Step 4: Invoke Safe Read Operations & Prove Gate 3 Loopback
```bash
# Invoke read account tool for acc-101 through MCP:
PYTHONPATH=. .venv/bin/python workshops/w1/client.py call-account acc-101

# Prove Gate 3 loopback enforcement (unauthorized request rejected):
PYTHONPATH=. .venv/bin/python workshops/w1/client.py call-unauthorized
```

### Step 5: Verify the Curated Catalog

```bash
.venv/bin/python workshops/w1/client.py --curated init
.venv/bin/python workshops/w1/client.py --curated list
.venv/bin/python workshops/w1/client.py --curated call-account acc-101
.venv/bin/python workshops/w1/client.py --curated call-unauthorized
```

Expect two tools, `get_account` and `get_case`, an authorized read and an embedded
401 for invalid credentials. Follow the [W1 worksheet](../../workshops/w1/worksheet.md)
for checkpoint comparison and fresh-seed rehearsal requirements.

### Step 6: Shut Down Workshop 1
```bash
./scripts/workshop stop
# Or: docker compose --profile w1 down
```

---

## 5. Workshop 2: Beyond API Governance: Securing AI Agents, MCP Servers, and Enterprise Integrations (`w2`)

- **Duration**: 45 minutes
- **Topology**: `apisix`, `api`, `adapter`, `opa`, `postgres`, `jaeger`
- **Configured Memory Cap**: ~1,664 MiB
- **Concept & Description**: As organizations rapidly integrate Large Language Models (LLMs), AI agents, MCP servers, and AI gateways into enterprise ecosystems, traditional API governance models are no longer sufficient. AI systems introduce new challenges including prompt injection attacks, uncontrolled tool access, data leakage, shadow AI adoption, compliance risks, and lack of observability.
- **Practical Walkthrough**: Extends established governance practices into the age of AI. Through real-world architectural patterns and live demonstrations, attendees learn how to govern AI interactions across APIs, MCP servers, AI gateways, and backend enterprise systems. Showcases practical approaches for implementing policy enforcement (via Open Policy Agent), access control, auditability, observability (via W3C distributed tracing in Jaeger), and responsible AI controls without slowing innovation. Participants leave with a blueprint for building enterprise-grade AI integration platforms that are secure, compliant, and production-ready.

### Step 1: Switch Profile & Start Workshop 2
```bash
./scripts/workshop switch w2
```
*Or using Docker Compose from Bash:*
```bash
export ACTIVE_PROFILE=w2
docker compose --profile w2 up -d --build
```

### Step 2: Verify Infrastructure Health
```bash
./scripts/workshop verify w2
```

### Step 3: Inspect Adversarial Support Ticket & Execute Prompt Injection Defense
Open **http://localhost:9080/workshop-2** and use the prefilled sample login. Follow the [W2 worksheet](../../workshops/w2/worksheet.md). The case text contains an indirect prompt injection; the recorded tool request uses 900,000 minor units (₹9,000) to `fraud-account-66`.
```bash
# Rehearse the console against the already-running W2 stack:
.venv/bin/python workshops/w2/rehearsal_console.py --outage
# Add --live to include one real hosted-model case review.
```
*Key Guarantees Verified:*
- **Tiered Risk Evaluation**: For a permitted support-agent beneficiary: up to and including ₹1,000 allowed; above ₹1,000 through ₹10,000 records a pending approval; above ₹10,000 or prohibited beneficiaries denied.
- **Fail-Closed Resiliency**: If OPA crashes, the adapter fails closed, blocking all financial mutations.

### Step 4: Inspect End-to-End Tracing in Jaeger
Open the Jaeger UI at [http://localhost:16686](http://localhost:16686) and search for the console trace ID. Confirm exported spans, then correlate the recorded tool response and banking evidence; a trace ID alone does not prove all hops were captured.

### Step 5: Shut Down Workshop 2
```bash
./scripts/workshop stop
# Or: docker compose --profile w2 down
```

---

## 6. Workshop 3: Architecting the Agentic Enterprise: Middleware, Durable State, and Event-Driven AI (`w3`)

- **Duration**: 45 minutes
- **Topology**: `apisix`, `api`, `adapter`, `opa`, `postgres`, `jaeger`, `temporal`, `kafka`, `worker`
- **Configured Memory Cap**: ~3,072 MiB
- **Concept & Description**: The generative AI landscape is rapidly shifting from stateless, synchronous chat applications to autonomous, long-running, multi-agent workflows. However, integrating non-deterministic AI agents into deterministic enterprise infrastructure presents massive architectural challenges regarding state, reliability, and governance.
- **Practical Walkthrough**: Treats agents as resilient, event-driven microservices. Through a live architectural demonstration of an "Autonomous System Resolver", attendees see the exact plumbing required to take agents to production: exposing legacy systems to LLMs securely via MCP and API gateways, triggering agentic cognition via Kafka event streams, and illustrating durable approval waits using Temporal and LangGraph with live **MiniMax 2.7 Fast** inference or deterministic replay fixtures. The lab timeout is 24 hours; multi-week availability is not measured. Finally, demonstrates how to enforce safety through strict human-in-the-loop (HITL) execution pauses before high-stakes API commits.

### Step 1: Switch Profile & Start Workshop 3
```bash
./scripts/workshop switch w3
```
*Or using Docker Compose from Bash:*
```bash
export ACTIVE_PROFILE=w3
docker compose --profile w3 up -d --build
```

### Step 2: Verify Infrastructure Health
```bash
./scripts/workshop verify w3
```

### Step 3: Trigger Autonomous Resolver via Kafka

Use `USE_REPLAY_FIXTURES=true` in `.env` before starting W3 for the expected
₹750 compensation. Follow the [W3 readiness notes](../../workshops/w3/worksheet.md#step-1-environment-readiness)
for previous completed workflows and client connection settings.

Emit customer dispute `case-501` to the Kafka topic:
```bash
PYTHONPATH=. .venv/bin/python workshops/w3/client.py emit --case-id case-501 --customer-id cust-8801
```

### Step 4: Query Temporal Workflow State & Observe HITL Pause
```bash
PYTHONPATH=. .venv/bin/python workshops/w3/client.py query --case-id case-501
```
*Verify*: The workflow durably pauses in `WAITING_FOR_APPROVAL` with proposed compensation `INR 750.00`.

### Step 5: Test Worker Crash & Duplicate Redelivery Resilience
```bash
# Simulate unexpected worker crash:
docker compose --profile w3 stop worker

# Redeliver duplicate Kafka event:
PYTHONPATH=. .venv/bin/python workshops/w3/client.py emit --case-id case-501 --customer-id cust-8801

# Restart worker and query workflow state:
docker compose --profile w3 start worker
PYTHONPATH=. .venv/bin/python workshops/w3/client.py query --case-id case-501
```
*Verify*: Temporal maintains exact workflow identity and state; the duplicate event reuses the workflow and settlement creates one payment. Failed activities may repeat inference and reads; this exercise does not prove exactly-once execution.

### Step 6: Deliver Human Approval Signal & Verify Settlement
```bash
PYTHONPATH=. .venv/bin/python workshops/w3/client.py approve --case-id case-501 --reviewer ops-lead --comments "Reviewed case evidence and validated proposal"
```
*Verify*: The workflow completes, creating exactly one idempotent compensation payment in Core Banking.

### Step 7: Run Full Workshop 3 Rehearsal Suite

This resets banking data and deletes local Temporal SQLite history. Preserve
evidence first and use a disposable local lab. This is a technical rehearsal,
not a measured 45-minute delivery.

```bash
PYTHONPATH=. .venv/bin/python workshops/w3/rehearsal_w3.py
```

### Step 8: Shut Down Workshop 3
```bash
./scripts/workshop stop
# Or: docker compose --profile w3 down
```

---

## 7. Workshop 4: The Day the Agent Broke the Bank: Implementing Triple-Gate Architecture & A2A Security (`w4`)

- **Duration**: 135 minutes (2h 15m)
- **Topology**: `apisix`, `api`, `adapter`, `opa`, `postgres`, `jaeger`, `temporal`, `kafka`, `worker`
- **Configured Memory Cap**: ~3,072 MiB
- **Exercise**: Use the [W4 worksheet](../../workshops/w4/worksheet.md) for the Incident Room, local policy/identity repairs, independent review and task/payment evidence. The recorded ₹90 lakh incident runs in an isolated presenter ledger; it is not a live model compromise or production certification.

### Step 1: Configure and Start Workshop 4

Follow the [W4 facilitator setup](../../workshops/w4/answer-key.md#setup-and-isolation)
before attendees arrive. Set the independent reviewer password before starting
services. The optional vulnerable replay additionally needs a distinct sandbox
key, `W4_ENABLE_VULNERABLE=true` and the `w4-presenter` service. Plain W4 startup
does not configure these requirements.

### Step 2: Verify Infrastructure Health

```bash
./scripts/workshop status
./scripts/workshop verify w4
```

### Step 3: Open the Incident Room

Open **http://localhost:9080/workshop-4**, sign in with the prefilled sample login,
and check readiness. Follow the worksheet's local policy and identity exercises.
Use a separate browser session for independent review with the configured
reviewer password. Export run evidence before resetting or changing profiles.

### Step 4: Inspect Delegation and Settlement Evidence

Run **legitimate delegation** immediately before independent review. Inspect
self-approval rejection, argument tampering, exact approved execution/retry and
task/payment binding in the console. The [answer key](../../workshops/w4/answer-key.md)
lists expected boundary results and ledger deltas.

### Step 5: Run the Technical Rehearsal

From the setup shell with the same `W4_REVIEWER_PASSWORD`:

```bash
.venv/bin/python workshops/w4/rehearsal_w4.py
# With the configured local presenter sandbox and an OPA outage:
.venv/bin/python workshops/w4/rehearsal_w4.py --vulnerable --outage
```

These commands create fictional payments/proposals and save timestamped JSON in
`workshops/w4/evidence/`. They do not reset the stack or measure 135 minutes of
human delivery. Restore the completed policy checkpoint before rehearsal.

### Step 6: Shut Down Workshop 4
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
# Example for the active W2 lab; substitute w1, w3 or w4 as appropriate.
./scripts/workshop reset w2
```
Bank reset does not clear Temporal history or W4's persisted incident runs.
For W3 repeat delivery, preserve evidence and use the disposable-lab rehearsal
reset described in the worksheet. W4 technical rehearsal does not reset data;
keep existing run evidence and reconcile uncertain outcomes before resetting.
Reset only while the requested profile is active; the launcher resets the
currently reachable API, not a separate database selected by its profile argument.

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
To remove all containers, networks, and persistent database volumes (`flobank_api_data`, `flobank_postgres_data`, `flobank_temporal_data`):
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
| **`ModuleNotFoundError: No module named httpx`** | The host client interpreter lacks its dependency; Docker packages are separate. | Complete Step 2.3 and run `.venv/bin/python workshops/w1/client.py init`. For only the W1 client, install with `.venv/bin/python -m pip install httpx==0.27.0`. |
| **`.venv/bin/python: No such file or directory`** | No virtual environment exists in the current repository. | Run Step 2.3 from the repository root; on Windows use Bash inside WSL. |
| **Port 9080 already in use** | A previous workshop profile or local proxy is occupying port 9080. | Run `./scripts/workshop stop` or check `ss -ltn '( sport = :9080 )'`. |
| **Port 8000 already in use** | Local service listening on 8000. | In `.env`, set `DEMO_HTTP_PORT=8001`, restart demo, and open [http://localhost:8001](http://localhost:8001). |
| **`HTTP 401 Missing API key`** | Request to Gate 3 omitted required key-auth header. | Include `-H "X-API-Key: gate3-secret-token"` in requests to `:9080/api/v1/*`. |
| **`HTTP 401 Insufficient scope`** | JWT token does not have required permissions. | Ensure JWT was minted with the appropriate scope (e.g. `api:cards:read`, `api:payments:write`). |
| **Model request timeout (504)** | Upstream LLM provider latency or missing API key. | For deterministic lab execution without external latency, set `USE_REPLAY_FIXTURES=true` or `DEMO_CHAT_MODE=scripted`. |
| **Container memory killed (OOM)** | Running multiple workshop profiles simultaneously or host has < 5 GB RAM. | Ensure only one profile is active at a time. Increase Docker Desktop memory allocation in settings. |
| **APISIX 404 Route Not Found** | APISIX loaded the wrong profile YAML configuration. | Use `./scripts/workshop switch <profile>` to recreate the container with the matching bind mount; a restart alone retains its old mount. |


W4 delivery now uses the [Incident Room story](workshop-4-story.md) and
[W4 setup/answer key](../../workshops/w4/answer-key.md). Open `/workshop-4` only
under `w4`. The recorded ₹90 lakh incident executes in its separate local
presenter sandbox. Technical rehearsal evidence and measured 135-minute human
delivery acceptance are recorded separately.
