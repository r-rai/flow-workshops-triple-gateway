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
Temporal, PostgreSQL/SQLite, Redis, OpenTelemetry and Jaeger.

## Documentation

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

**Architecture v1.0 candidate.** APISIX-specific behavior around
standalone MCP generation, loopback routing, body-aware OPA policy,
token propagation and trace propagation must be validated before being
treated as guaranteed.

> Keep deterministic enterprise controls. Add agent-aware controls
> around them.
