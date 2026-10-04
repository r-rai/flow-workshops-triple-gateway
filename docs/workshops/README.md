# Workshop Mapping

See the [complete delivery plan](delivery-plan.md) for timed agendas, exercise
artifacts, checkpoints, facilitator preparation, and acceptance criteria.

## Customer dashboard and chatbot

The customer simulation is available on `main` in the original Compose file:

```bash
docker compose --profile demo up -d --build
```

Open **http://localhost:8000** and use `maya@flobank.demo` / `flo-demo`.
This is a scripted, fictional account simulation; it does not run the workshop
agent or modify enterprise data. The same UI is served through the gateway at
**http://localhost:9080** when a workshop profile is running.
See [participant setup](../setup/participant-requirements.md) for laptop steps.

## W1 --- Modernizing APIs for AI Agents: From OpenAPI to MCP

**45 min.** Existing REST/OpenAPI -\> generated MCP -\> successful
invocation -\> problems with blind exposure -\> curation -\> preserve
API boundary.

Profile: `w1`.

## W2 --- Beyond API Governance

**45 min.** Add OPA, signed lab identity/token exchange, and audit/tracing. Focus on identity,
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

Run one workshop profile at a time. The current W4 Compose profile includes
Kafka alongside its shared worker; Redis is not required. The runtime and
operator commands are implemented. See the [VPS runbook](../setup/vps-setup-guide.md)
for the current service set and profile-switching behavior.
