# Workshop Series Overview & Architecture Mapping

See the [complete delivery plan](delivery-plan.md) for timed agendas, exercise artifacts, checkpoints, facilitator preparation, and acceptance criteria. For participant hands-on commands, see the [Participant Infrastructure Guide](participant-infra-guide.md).

---

## Flo Bank Customer Dashboard & AI Companion

The interactive Flo Bank customer simulation is available on `main` via Docker Compose:

```bash
# Standalone simulated demo:
docker compose --profile demo up -d --build

# Or enterprise mode connected directly to APISIX Gate 3 Core Banking:
docker compose --profile demo-enterprise up -d --build
```

- Open **http://localhost:8000** (or via APISIX at **http://localhost:9080**) and log in with sample credentials: `maya@flobank.demo` / `flo-demo`.
- **Live AI**: Powered by **MiniMax 2.7 Fast** (`MiniMax-M2.7-highspeed`) through APISIX Gate 1 (`/ai/chat/completions`) with session-scoped tool calling (`get_demo_accounts`, `set_demo_card_state`, `create_demo_dispute`, etc.).
- **Zero-Key Offline Support**: Automatically falls back to deterministic, scripted customer responses if `MINIMAX_API_KEY` is not configured.
- See [participant setup](../setup/participant-requirements.md) for attendee workstation prerequisites.

---

## Topic 1 (W1): Modernizing APIs for AI Agents: From OpenAPI to MCP
- **Duration**: 45 minutes
- **Profile**: `w1`
- **Description**: Most enterprises already have well-documented REST APIs, but AI agents cannot reliably use them without an interface designed for tool discovery, structured invocation, and safe runtime interaction. This session shows how API architects and integration engineers can transform existing OpenAPI-described services into MCP-based, AI-consumable tools, where automation helps, where curation is essential, and how to preserve governance, security, and observability along the way.
- **Practical Walkthrough**: Compares OpenAPI and MCP, demonstrates automatic MCP server generation from an existing API contract, and explains how to refine tool semantics so agents can use them effectively rather than blindly exposing every endpoint as a tool. Attendees will also see how to apply guardrails such as selective exposure, policy controls, and runtime monitoring, which are increasingly important because MCP adoption is moving faster than enterprise governance models built for human-driven API traffic.

---

## Topic 2 (W2): Beyond API Governance: Securing AI Agents, MCP Servers, and Enterprise Integrations
- **Duration**: 45 minutes
- **Profile**: `w2`
- **Description**: As organizations rapidly integrate Large Language Models (LLMs), AI agents, MCP servers, and AI gateways into enterprise ecosystems, traditional API governance models are no longer sufficient. AI systems introduce new challenges including prompt injection attacks, uncontrolled tool access, data leakage, shadow AI adoption, compliance risks, and lack of observability.
- **Practical Walkthrough**: Explores how API and integration teams can extend established governance practices into the age of AI. Through real-world architectural patterns and live demonstrations, attendees learn how to govern AI interactions across APIs, MCP servers, AI gateways, and backend enterprise systems. Showcases practical approaches for implementing policy enforcement (via Open Policy Agent), access control, auditability, observability (via W3C distributed tracing in Jaeger), and responsible AI controls without slowing innovation. Participants leave with a blueprint for building enterprise-grade AI integration platforms that are secure, compliant, and production-ready.

---

## Topic 3 (W3): Architecting the Agentic Enterprise: Middleware, Durable State, and Event-Driven AI
- **Duration**: 45 minutes
- **Profile**: `w3`
- **Description**: The generative AI landscape is rapidly shifting from stateless, synchronous chat applications to autonomous, long-running, multi-agent workflows. However, integrating non-deterministic AI agents into deterministic enterprise infrastructure presents massive architectural challenges regarding state, reliability, and governance.
- **Practical Walkthrough**: Bridges the gap between theoretical multi-agent systems and robust enterprise middleware by treating agents as resilient, event-driven microservices. Through a live architectural demonstration of an "Autonomous System Resolver", attendees see the exact plumbing required to take agents to production: exposing legacy systems to LLMs securely via MCP and API gateways, triggering agentic cognition via Kafka event streams, and managing long-running, multi-week agent processes without state loss using Temporal and LangGraph (supporting live **MiniMax 2.7 Fast** inference or deterministic replay fixtures). Finally, demonstrates how to enforce safety through strict human-in-the-loop (HITL) execution pauses before high-stakes API commits.

---

## Topic 4 (W4): The Day the Agent Broke the Bank: Implementing Triple-Gate Architecture & A2A Security for Autonomous AI Workloads
- **Duration**: 135 minutes (2h 15m)
- **Profile**: `w4`
- **Description**: Traditional API gateways protect systems from fast humans, but they are fundamentally blind to autonomous AI agents. When an enterprise deploys agentic workflows (via frameworks like LangGraph or CrewAI) and exposes internal business APIs as "Tools," standard REST security fails. Prompt injections don't violate network schemas, and non-deterministic agentic reasoning loops routinely bypass traditional rate limits, risking massive financial and data liability.
- **Practical Walkthrough**: Uses a "live incident response" storytelling approach to deconstruct a high-consequence system compromise: *The Day NegotiatorBot Broke the Bank*. Through the lens of a multi-million-dollar automated exploit driven by a subtle prompt injection, participants map out why legacy OAuth and standard API proxies failed to stop the breach. Moving from forensic analysis to modern architecture, attendees learn how to systematically remediate the vulnerability by deploying a production-ready Triple-Gate Architecture across three distinct security perimeters:
  1. **Defending the Inference Boundary (Gate 1 - AI Gateway)**
  2. **Governing Capability Execution (Gate 2 - Tool / MCP Gateway)**
  3. **Securing Micro-Scoped Identity Propagation (Gate 3 - Standard API Gateway)** via OAuth Token Exchange ($RFC\ 8693$)
  Finally, demonstrates how to achieve deep observability across recursive agentic loops using modern OpenTelemetry GenAI span tracing and safely govern autonomous Agent-to-Agent (A2A) interactions in production.

---

## Resource & Profile Rules
- **Run One Profile at a Time**: Always run one active workshop profile at a time to stay strictly within the host memory limits (`./scripts/workshop switch <w1|w2|w3|w4>`).
- **Persistence**: All profiles use pinned image tags and persistent volumes.
- See the [VPS runbook](../setup/vps-setup-guide.md) for hardware limits and host coexistence policies.
