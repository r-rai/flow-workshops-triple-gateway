# Architecture Decisions

## ADR-001 --- Unified Gateway

**Decision:** Apache APISIX is the leading candidate for all three
logical boundaries.

**Why:** lower workshop footprint, fewer hops/configuration models, and
a strong teaching model.

**Status:** pending POC.

## ADR-002 --- Open-Source-First

Prefer self-hostable open-source components so attendees can reproduce
the architecture and the workshops remain vendor-neutral.

## ADR-003 --- Progressive Compose Profiles

Never require the complete reference architecture on participant
laptops. Start only the services required for the active exercise.

## ADR-004 --- APISIX Standalone for Participants

Prefer declarative standalone mode to remove etcd.

**Risk:** plugin compatibility and exercise behavior must be validated.

## ADR-005 --- OPA Owns Fine-Grained Policy

Authorization stays deterministic and outside the LLM/agent graph. MCP
JSON-RPC body inspection is a POC requirement.

## ADR-006 --- LangGraph for Agent Orchestration

Chosen for explicit graph/state/tool flow. It is not a security
boundary.

## ADR-007 --- Temporal for Durability

Keep long-running durable business execution separate from agent
reasoning. Use a lightweight dev server for workshops.

## ADR-008 --- Kafka for Events

Use single-node KRaft mode for a recognizable enterprise event model
without ZooKeeper.

## ADR-009 --- Jaeger for Participant Tracing

Use OTel + Jaeger for hands-on distributed tracing; discuss richer
observability stacks as reference architecture.

## ADR-010 --- Real Identity with Fallback

Prefer Keycloak for Workshops 2 and 4 if benchmarked footprint is
acceptable; retain mock/pre-issued JWTs as fallback. Token exchange
remains a POC item.
