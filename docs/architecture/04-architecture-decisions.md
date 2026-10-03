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

Authorization stays deterministic and outside the LLM/agent graph. A lightweight
MCP adapter sends validated identity and normalized tool arguments to OPA in
W2–W4. Do not assume the stock APISIX OPA plugin supplies the JSON request body.
Missing decisions and policy failures deny execution.

## ADR-006 --- LangGraph for Agent Orchestration

Chosen for explicit graph/state/tool flow. It is not a security
boundary.

## ADR-007 --- Temporal for Durability

Keep long-running durable business execution separate from agent
reasoning. Run LangGraph and external I/O inside activities; Temporal owns
progress and approval waits. Use a development server with persistent SQLite,
and label it as a workshop deployment rather than a production topology.

## ADR-008 --- Kafka for Events

Use single-node KRaft mode for a recognizable enterprise event model
without ZooKeeper, in W3 only. Backend idempotency and stable workflow IDs
handle duplicate delivery; do not claim exactly-once event transport.

## ADR-009 --- Jaeger for Participant Tracing

Use OTel + Jaeger for hands-on distributed tracing; discuss richer
observability stacks as reference architecture.

## ADR-010 --- Real Identity with Fallback

Use Keycloak for W2/W4 with distinct MCP/API audiences and restricted token
exchange. Verify effective scopes; exchange alone does not ensure downscoping.
W1 uses separate narrow lab credentials. W3 uses separately issued signed lab
credentials and explicitly does not demonstrate live exchange. Replay replaces
model responses, not required identity/security components.

## ADR-011 --- Native Generation and Curated Adapter

Start W1 with native APISIX OpenAPI-to-MCP generation, using 3.19.0 as the
initial spike candidate. W2–W4 use a curated Python MCP adapter for argument
policy and identity exchange. Both routes must re-enter Gate 3. If native
routing fails the spike, generate through the adapter and record the decision.

## ADR-012 --- Minimal Profiles and Resource Budget

No required Redis; Kafka only in W3. PostgreSQL supports W2–W4. Run one active
profile within a 6 GB total VPS envelope, preserving existing services. Values
in the [VPS guide](../setup/vps-setup-guide.md) are unverified starting budgets.

## ADR-013 --- Approval and Business Integrity

Persist exact proposed arguments, identities, expiry, and single-use execution
association. The backend atomically enforces approval consumption, ownership,
balance rules, and idempotency. The agent cannot approve its own action.

## ADR-014 --- Actual A2A Security Exercise

W4 includes NegotiatorBot → PaymentsAgent using a pinned A2A SDK/protocol,
Agent Card discovery, authenticated task submission, and owner-scoped task
access. Task delegation never substitutes for business authorization.

See the [implementation handoff](../implementation/agent-handoff.md) for
contracts, ordered packages, and acceptance evidence.
