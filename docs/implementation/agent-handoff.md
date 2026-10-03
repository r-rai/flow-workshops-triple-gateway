# Implementation Agent Handoff

## Start here

Status: documentation baseline only. No applications, Compose files, operator commands, or benchmark results have been delivered yet.

Read repository instructions, the [delivery plan](../workshops/delivery-plan.md), [VPS guide](../setup/vps-setup-guide.md), and original [session brief](../workshops/workshot.txt). These plans supersede earlier component/profile suggestions where they differ. Preserve the original session descriptions as the source brief.

The goal is four independently runnable workshops with prebuilt local labs and a presenter VPS constrained to 6 GB total operating memory. Preserve existing Caddy and monitoring services. Do not deploy a full reference stack simultaneously.

## Architecture contracts

### API and tool boundaries

Implement a small FastAPI application for account reads, support-case reads, payment proposal/execution, incident reads, simulated remediation, and approval lifecycle. Use integer minor units and explicit currency for money. Limit initial scope to these flows; a general banking platform is unnecessary.

W1 uses APISIX native OpenAPI-to-MCP generation and separately scoped upstream lab credentials. W2–W4 use a Python MCP adapter for curated tools, normalized argument policy, and downstream identity handling. Both paths must re-enter Gate 3 before reaching FastAPI.

The adapter passes trusted identity, tool name, normalized arguments, and approval context to OPA. Define explicit `allow`, `deny`, and `approval_required` decisions with machine-readable reasons. Missing/invalid policy output or policy timeout denies execution. Approval-required records a proposal and returns a pending result without performing the business action.

Only identity derived from validated credentials is authoritative. Strip/ignore caller-provided identity headers. Tool descriptions, prompts, and agent state are not authorization controls. API ownership and business checks remain authoritative even if an agent bypasses the intended graph.

### Identity

Use Keycloak in W2/W4, with separate MCP/API audiences and configured confidential-client token exchange. Verify issuer, signature, expiry, audience, and required scopes. Configure exchange privileges and optional/default scopes so the requested API credential cannot exceed the intended permission set. Test denial cases; do not assume RFC 8693 automatically narrows privileges.

W3 uses separately issued signed lab credentials for the two boundaries, explicitly labelled as an identity simplification. Do not forward an MCP token directly to the API. Distinguish standard exchange from actor/delegation features that the selected Keycloak release may not support as stable functionality.

### Approval and idempotency

Persist requester/approver, canonical action arguments, expiry, status, and single-use execution association. Reject self-approval, changed arguments, expired approvals, and approval reuse. Enforce approval consumption and business mutation atomically. Bind idempotency to trusted principal and action; reject reuse of a key with different arguments. Approved retries return the original result rather than duplicate payment/remediation.

### Durable state and A2A

Temporal owns workflow progress and approval waits. LangGraph executes bounded reasoning within activities. Keep network/model/tool I/O out of deterministic workflow code. Persist the Temporal development-server database. Use incident identity for workflow deduplication and backend idempotency for retry safety. An in-memory interrupt alone is not a durable approval mechanism.

W4 includes a protocol-level A2A exchange: NegotiatorBot calls PaymentsAgent, discovers an Agent Card, submits a task, and reads task progress. Use a pinned maintained SDK; authenticate requests and authorize task ownership. A task result cannot grant payment permission. An unrelated principal must fail attempts to read, approve, or mutate another principal's task/action. A distinct human principal with the configured approver role and matching tenant/workflow access may review and approve the proposal; this explicit permission does not grant general access to other users' A2A tasks. Test both authorized human approval and unrelated-principal rejection.

### Observability and replay

Propagate trace context across inference, MCP, OPA decisions, Gate 3, and API execution; use appropriate span links for asynchronous Kafka/Temporal boundaries. Record trusted principal, decision reason, workflow/task IDs, and business correlation IDs without raw credentials. Pin the selected GenAI semantic convention version and document custom attributes.

Replay substitutes model responses only. Real policy, identity, API, workflow, and persistence components continue to execute. Label replay visibly in output and traces.

## Ordered work packages

| Package | Dependencies | Deliverables | Exit evidence |
|---|---|---|---|
| 1. Compatibility spikes | None | Minimal APISIX/MCP loopback, adapter/OPA, Keycloak exchange, trace, A2A and memory feasibility probes | Commands, versions, outcomes, and limitations recorded in `docs/poc/` |
| 2. Foundation | Package 1 relevant probes | API, seed data, persistence, idempotency, Compose skeleton, configuration template, operator script | Clean startup, health, reset, stop, and positive/negative API checks |
| 3. Workshop 1 | Package 2 and native MCP proof | Generated/curated contracts, client, refresh procedure, checkpoint worksheets | Complete 45-minute rehearsal and Gate 3 denial evidence |
| 4. Governance / W2 | Packages 2–3 | Adapter, OPA, Keycloak, approval records, audit/tracing, exercise checkpoints | Argument/identity authorization, OPA outage, and approval-required checks |
| 5. Durability / W3 | Packages 2 and 4 | Kafka consumer, Temporal workflow, LangGraph activities, resolver scenario | Worker/server restart, duplicate delivery, and rejection checks |
| 6. Triple-Gate / W4 | Packages 4–5 | Isolated incident checkpoints, durable payment approval, A2A exchange, trace worksheet | Complete attack/remediation flow and 135-minute rehearsal |
| 7. Delivery hardening | Packages 3–6 | Prebuilt image manifest, guides, answer keys, recovery recipes, replay fixtures, measurements | VPS and Windows rehearsals, offline-provider path, two-user fallback check |

Execute in dependency order. Do not build a full platform around an unproven gateway security assumption. Package 1 measures minimal feasibility; complete profile and Windows benchmarks necessarily happen once the profile exists.

If native generation cannot preserve Gate 3 enforcement, document the failed spike and use the adapter for OpenAPI-driven generation as well; preserve W1's learning outcome and update the architecture decision before continuing. Do not bypass Gate 3 to make the demonstration work. If a required product feature is unavailable, report the concrete limitation and adjust the documented implementation rather than claiming equivalence.

## Required interface and packaging

Implement `scripts/workshop` with `preflight`, `pull PROFILE`, `start PROFILE`, `status`, `verify PROFILE`, `switch PROFILE`, `reset PROFILE`, and `stop`, following the [operator contract](../setup/vps-setup-guide.md#5-operator-interface-to-implement).

Ship versioned initial/completed checkpoints per workshop, `.env.example`, local/VPS overrides, readiness checks, named volumes, pinned images, and a release manifest. Keep participant provider credentials local. Reset only workshop-owned resources after explicit confirmation. Never run a system-wide Docker prune.

## Acceptance and reporting

Record verification commands and actual results for:

- MCP initialization/discovery/call, unknown tools, invalid arguments, and catalog refresh.
- Gate 3 traversal for both native and adapter calls; no direct backend reachability from the adapter/agent.
- Wrong audience, insufficient scopes, spoofed identity, malformed policy, and OPA timeout/outage.
- Approval rejection/expiry/self-approval/changed arguments/reuse and idempotent concurrent execution.
- Worker and Temporal restart, event redelivery, and retry-safe business effects.
- A2A unauthorized task access/submission/approval.
- Complete correlated successful/denied traces with secrets redacted.
- All four profile startup and timed exercise measurements; two fallback users; Windows/WSL2 capped at 5 GB.
- Replay with no provider access and preservation of existing VPS services.

Do not claim Windows, capacity, or live-provider validation if the relevant environment is unavailable. Report remaining checks separately from passes. Every work package ends with changed artifacts, fresh verification evidence, limitations, and next dependency. Commit coherent changes; push the task branch without force-pushing or merging automatically.

## Copyable implementation prompt

```text
Implement the NovaBank workshop platform in this repository.

Read AGENTS.md when present and follow the supplied repository instructions,
including CodeGraph-first exploration if .codegraph exists. Then read:
- docs/implementation/agent-handoff.md
- docs/workshops/delivery-plan.md
- docs/setup/vps-setup-guide.md
- docs/poc/README.md

These files contain the agreed scope, architecture, work-package order,
operator interface, workshop agendas, and acceptance criteria.

Start with compatibility spikes and record evidence. Continue through the
dependent implementation packages; do not stop at another plan. Keep the
6 GB total VPS budget, one active profile, existing Caddy/monitoring services,
local participant keys, replay fallback, Gate 3 routing, fail-closed policy,
durable approvals, and backend idempotency. Keep vulnerable scenarios private
and synthetic. Commands documented as future interfaces must be implemented
and verified before describing them as available.

Inspect git status and preserve unrelated changes. Use a task branch for
implementation. Commit only relevant changes and push it to the configured
remote without force-pushing or merging automatically. Never print remote
credentials or secrets. Report the branch, commit hashes, verification
results, actual setup commands, and remaining limitations. If a required
environment is unavailable, complete independent work and identify exactly
which acceptance checks remain unverified.
```
