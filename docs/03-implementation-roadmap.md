# Implementation Roadmap

## Phase 0 --- Technical Spikes

Validate APISIX standalone mode, OpenAPI-to-MCP, Gate-2-to-Gate-3
loopback, body-aware OPA policy, token propagation, trace propagation
and Windows/WSL memory.

## Phase 1 --- NovaBank API

Build small deterministic Customer, Account, Transaction, Beneficiary,
Payment, Support and Operations APIs with reproducible seed data.

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
end-to-end tracing.

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
