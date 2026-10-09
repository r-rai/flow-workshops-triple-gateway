# Participant Setup

## Flo Bank dashboard and chatbot

For the customer simulation, install Git, Docker Desktop (Windows/macOS) or
Docker Engine with Compose (Linux), and a browser. Start Docker before running
the commands. A local Python installation and model-provider key are not needed.

For a new checkout:

```bash
git clone --branch main https://github.com/r-rai/flow-workshops-triple-gateway.git
cd flow-workshops-triple-gateway
```

For an existing checkout, switch to `main` and pull the latest changes:

```bash
git switch main
git pull --ff-only origin main
```

From the repository root, use the main Compose file:

```bash
docker compose --profile demo up -d --build
```

These commands work in PowerShell, macOS, Linux, and WSL. The first build needs
internet access to download images and dependencies. Open **http://localhost:8000**
and sign in with `maya@flobank.demo` / `flo-demo` (already filled in).

Try a balance query, recent transactions, card freeze/unfreeze, and
`Dispute tx-1004`, followed by a dispute-status query. When configured with
`MINIMAX_API_KEY` in `.env`, the assistant connects to live inference with **MiniMax 2.7 Fast** (`MiniMax-M2.7-highspeed`)
via APISIX Gate 1 (`demo-gateway`); in offline environments, it falls back to
deterministic scripted replies.

For optional live inference with your own OpenRouter key and free models,
follow the [OpenRouter participant setup](../workshops/openrouter-setup.md).
It includes model selection, free-tier limits, and a live verification step.

The demo supports two backend modes:
- **Simulated (`demo`)**: Fictional fixtures, in-memory session isolation.
- **Enterprise (`demo-enterprise`)**: Real-time integration with APISIX Gate 3 (`:9080/api/v1`) using scoped customer JWTs and SQLite/PostgreSQL persistence.

Check status or stop the demo:

```bash
docker compose --profile demo ps
docker compose logs --tail 50 demo
docker compose --profile demo down
```

For complete step-by-step instructions for all workshop profiles (`w1`–`w4`) and teardown procedures, see the [Participant Infrastructure Guide](../workshops/participant-infra-guide.md).

If port 8000 is busy, add `DEMO_HTTP_PORT=8001` to a repository-root `.env` file,
rerun the startup command, and open **http://localhost:8001**. Otherwise `.env`
configuration is optional for the simulated demo.

## Workshop laptop target

The complete workshop labs target Windows 11, 16 GB RAM, four or more CPU cores,
an SSD, Docker Desktop with WSL2, Git, a browser, and an editor. The standalone
customer simulation uses one container with a 256 MiB container memory limit;
this does not include Docker Desktop or operating-system overhead.

For the complete labs, a useful WSL2 test configuration is:

```ini
[wsl2]
memory=5GB
swap=2GB
processors=4
```

Corporate-managed devices may restrict these settings. Changing `.wslconfig`
requires a WSL restart. The Windows/WSL2 memory benchmark remains unverified;
Linux rehearsal evidence does not establish Windows capacity.

The `w1`–`w4` profiles use the same `docker-compose.yml`. For Workshop 1:

```bash
docker compose --profile w1 up -d --build
```

Open **http://localhost:9080** for the sample bank UI through the gateway.
`ACTIVE_PROFILE` selects the gateway configuration and defaults to `w1`.
If `.env` exists, set it to match the chosen workshop profile. Activating a new
Compose profile does not stop previously running workshop services.

The optional `scripts/workshop` launcher handles profile switching, warm-up,
reset, and verification. It runs under Bash (Linux/WSL), and verification uses
the repository's Python virtual environment. It is not needed for the standalone
demo. See the [VPS runbook](vps-setup-guide.md) for workshop operator commands.

## Python workshop clients

Docker-only demos do not need local Python. The W1–W4 Python clients and the
Bash launcher require a host Python environment. Before the session, complete
the [Python setup](../workshops/participant-infra-guide.md#step-23-set-up-python-virtual-environment-for-workshop-clients-verification--tests).
The W1 worksheet also includes a minimal `httpx` installation for its MCP client.
Run client commands with `.venv/bin/python` from the repository root.

## Before the workshop

Build or download the required images before workshop day. Do not depend on
conference Wi-Fi or install dependencies during the timed exercise. For the
operator workflow, `./scripts/workshop pull w1` prepares W1 images. The current
global preflight also requires the pinned third-party images from W2–W4; run
`docker compose --profile w3 pull --ignore-buildable` before
`./scripts/workshop preflight` on a fresh host. This downloads images without
starting services. Prepare the Python environment described in the
[VPS runbook](vps-setup-guide.md) before using the launcher.

The customer bot connects to live hosted inference with **MiniMax 2.7 Fast** (`MiniMax-M2.7-highspeed`) via APISIX
Gate 1 when `MINIMAX_API_KEY` is present, and falls back gracefully to scripted
replies in offline environments. The W3 investigation agent is a separate LangGraph
workflow: replay is the default; live inference requires a participant-owned provider
key in ignored local configuration (`.env`). Never commit keys.

For detailed workshop instructions and clean teardown, see the [Participant Infrastructure Guide](../workshops/participant-infra-guide.md).

If local Docker fails, use presenter demonstration or an explicitly secured,
isolated fallback. The initial limit of two concurrent fallback runs remains an
operating limit pending load testing.

See the [delivery plan](../workshops/delivery-plan.md) for exercise artifacts.
