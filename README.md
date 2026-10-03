# NovaBank Agentic AI Workshop Platform

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

## Status

**Documentation baseline; runtime not implemented.** The delivery plan and agent
handoff define the agreed implementation scope. Commands in the setup guide
are future interfaces until built and verified. Native MCP generation,
Gate 3 routing, adapter policy, audience-separated identity, trace propagation,
and resource use require recorded compatibility evidence.

Target: one active profile within a **6 GB total VPS operating budget**,
with local participant labs and limited replay-based VPS fallback.

> Keep deterministic enterprise controls. Add agent-aware controls
> around them.
