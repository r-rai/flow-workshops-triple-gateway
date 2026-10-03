# Implementation Roadmap

The [agent handoff](implementation/agent-handoff.md) defines ordered work
packages, interface contracts, a copyable prompt, and required evidence.
Status: documentation baseline; runtime implementation is outstanding.

## Phase 0 --- Technical Spikes

Validate APISIX standalone mode, OpenAPI-to-MCP, Gate-2-to-Gate-3
loopback, adapter-based argument policy, audience-separated token exchange, trace propagation
and Windows/WSL memory.

## Phase 1 --- NovaBank API

Build the minimal account, support-case, payment proposal/execution, incident,
approval, and simulated-remediation flows with seed data and transactional
idempotency. Deliver the Compose skeleton and operator interface early.

## Phase 2 --- Workshop 1

Add deliberately imperfect OpenAPI semantics, automatic MCP exposure,
curated alternatives and selective exposure.

## Phase 3 --- Workshop 2

Add OPA policies, Keycloak configuration, identity context,
tool/argument authorization, audit and lightweight tracing.

## Phase 4 --- Workshop 3

Add Kafka events, the Autonomous System Resolver, LangGraph
orchestration, Temporal durability and HITL pause/resume.

## Phase 5 --- Workshop 4

Build NegotiatorBot in vulnerable and remediated states. Demonstrate
inference controls, capability policy, scoped API identity, approval and
end-to-end tracing and a protocol-level A2A exchange with task ownership checks.

## Phase 6 --- Packaging

Provide Docker Compose profiles, `.env.example`, health checks,
setup/validation scripts, pre-built images, troubleshooting and
presenter fallback configuration.

## Phase 7 --- Rehearsal

Test on Windows 11 / 16 GB / WSL2 capped near 5 GB, the presenter VPS, a
clean uncached machine and realistic network conditions.

## Definition of Done

Each workshop starts with one documented command, has a deterministic
fallback, does not require the full stack, can visibly demonstrate
control failure/success and can trace the relevant execution path.

Release requires the [VPS runbook](setup/vps-setup-guide.md) to contain actual
verified versions, commands, endpoints, image coordinates and measurements.
Do not publish future interfaces or estimated memory as verified behavior.
