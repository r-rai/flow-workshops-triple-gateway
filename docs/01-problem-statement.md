# Problem Statement

## Context

Enterprises already protect REST APIs with gateways, OAuth/OIDC, rate
limits, schemas, logging and backend authorization. AI agents introduce
a different consumer: one that can discover capabilities dynamically,
select tools, loop autonomously and act on non-deterministic model
output.

## Problems

### APIs are not automatically good agent tools

An accurate OpenAPI operation can still provide poor semantics for an
agent. Blind one-endpoint-to-one-tool conversion can expose unnecessary
or high-impact capabilities.

### MCP creates a capability-policy problem

At the API boundary a gateway sees `POST /api/v1/payments`. At MCP it
may see `POST /mcp` with a JSON-RPC body containing `tools/call`, a tool
name and arguments. Policy must therefore understand capability
semantics, not only HTTP paths.

### LLM instructions are not authorization

A prompt saying "never transfer more than ₹100,000" is not an
enforcement mechanism. Authorization must remain deterministic,
external, testable and auditable.

### Agents need durable enterprise execution

Agent workflows may start from events, wait for human approval, retry
after failure and run for hours or days. Synchronous chat infrastructure
alone is insufficient.

### Agent actions need deeper observability

Operators need correlation across user → agent → LLM → tool → policy →
API → backend, not only a final API access log.

### Workshop infrastructure must fit participant laptops

Most attendees are expected to use 16 GB Windows laptops with Docker
Desktop/WSL2, browser and IDE already consuming memory. The full
enterprise reference stack cannot be mandatory for every exercise.

## Success Criteria

Participants can: 1. transform OpenAPI-described APIs into MCP tools; 2.
identify where generated tools require curation; 3. enforce
deterministic tool policies; 4. preserve API security behind MCP; 5.
trigger agents from events; 6. demonstrate durable workflows and HITL;
7. trace agent execution end-to-end; 8. run the relevant exercise within
the participant hardware envelope.
