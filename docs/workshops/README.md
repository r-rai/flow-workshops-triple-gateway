# Workshop Mapping

See the [complete delivery plan](delivery-plan.md) for timed agendas, exercise
artifacts, checkpoints, facilitator preparation, and acceptance criteria.

## W1 --- Modernizing APIs for AI Agents: From OpenAPI to MCP

**45 min.** Existing REST/OpenAPI -\> generated MCP -\> successful
invocation -\> problems with blind exposure -\> curation -\> preserve
API boundary.

Profile: `w1`.

## W2 --- Beyond API Governance

**45 min.** Add OPA, Keycloak and audit/tracing. Focus on identity,
tool/argument authorization, selective exposure, prompt/input controls
and deterministic policy.

Profile: `w2`.

## W3 --- Architecting the Agentic Enterprise

**45 min.** Kafka -\> Temporal workflow -\> LangGraph activity -\> MCP/API. Demonstrate
event-triggered agents, durable execution, retries and HITL using an
Autonomous System Resolver.

Profile: `w3`.

## W4 --- The Day the Agent Broke the Bank

**135 min.** NegotiatorBot incident: vulnerable capability exposure -\>
prompt-originated unsafe behavior -\> Gate 1 -\> Gate 2 -\> Gate 3 -\>
restricted token exchange -\> approval -\> secured A2A task exchange -\> forensic trace.

Profile: `w4`.

The fourth workshop should be staged progressively; all services do not
need to be active from minute one.

Run one active profile at a time. W4 does not require Kafka or Redis. Commands
and profiles are planned interfaces until the implementation is delivered.
