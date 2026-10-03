# NovaBank Workshop Delivery Plan

Status: approved planning baseline; applications and lab scripts are not implemented yet.
Source session descriptions: [original brief](workshot.txt).

## Delivery model

- Audience: experienced API/integration engineers and architects.
- Participants run prebuilt local labs on 16 GB Windows laptops, with WSL2 capped near 5 GB.
- The presenter VPS runs one workshop at a time within a 6 GB total operating budget.
- Participants bring hosted-model credentials; deterministic replay supports every exercise without a provider.
- Each workshop starts independently from seeded data and an initial checkpoint.
- Installation and image downloads happen before the session. Timed sessions contain short guided exercises.
- The VPS provides presenter demonstrations and at most two concurrent fallback runs initially; this is an operating limit pending testing, not a capacity guarantee.

Use fictional NovaBank accounts, beneficiaries, payments, support cases, and incidents throughout.
Do not claim the development deployment itself is production-ready. Explain which controls and operational components a production deployment would require.

## Workshop 1 — Modernizing APIs for AI Agents: From OpenAPI to MCP

**Duration:** 45 minutes. **Profile:** `w1`.
**Outcome:** generate, curate, and invoke tools while preserving downstream API authorization.

| Minutes | Activity | Presenter cue / participant action |
|---|---|---|
| 0–5 | Introduce NovaBank support agent | Show the account-support request and expected business outcome |
| 5–12 | OpenAPI versus MCP | Compare HTTP operations with initialization, discovery, schemas, and invocation |
| 12–22 | Generate tools from OpenAPI | Demonstrate native APISIX generation and an account read |
| 22–32 | Guided curation exercise | Improve names/descriptions and remove unnecessary operations from the exposed contract |
| 32–40 | Preserve Gate 3 | Invoke through MCP, reject an unauthorized operation, and inspect routing evidence |
| 40–45 | Review and questions | Discuss generation versus purposeful capability design |

**Exercise artifact:** curated contract and saved invocation/denial results.

**Acceptance:** intended tools are discoverable; excluded tools are neither discoverable nor callable; valid reads succeed; downstream authorization failures remain effective through MCP.

**Checkpoints:** broad generated contract → curated contract. Account reads are the primary success path; synthetic payment exposure illustrates excessive capability.

**Facilitator preparation:** pre-warm the generated tool catalog and document how the selected plugin version refreshes its cached OpenAPI document. Verify that the exercise's contract changes actually refresh discovery.

## Workshop 2 — Beyond API Governance: Securing AI Agents, MCP Servers, and Enterprise Integrations

**Duration:** 45 minutes. **Profile:** `w2`.
**Outcome:** enforce identity-aware and argument-aware tool policy independently of model instructions.

| Minutes | Activity | Presenter cue / participant action |
|---|---|---|
| 0–5 | Threat scenario | Read a synthetic support case containing injected instructions |
| 5–12 | Governance responsibilities | Separate identity, capability policy, and backend business rules |
| 12–22 | Unsafe proposal, blocked execution | Show that valid model output is not authorization |
| 22–34 | Guided policy exercise | Modify role, amount, and beneficiary rules; run allow/deny cases |
| 34–41 | Failure and audit | Stop OPA, verify no execution, and inspect decision reasons |
| 41–45 | Review and questions | Map controls to enterprise governance responsibilities |

**Exercise artifact:** OPA policy and reproducible positive/negative requests.

**Acceptance:** policy uses validated identity and actual normalized arguments; missing or unavailable policy fails closed; approval-required creates no payment.

**Checkpoints:** broad synthetic tool policy → restricted policy. Use a lightweight persisted approval record here; the durable pause/resume implementation is introduced in Workshops 3–4.

## Workshop 3 — Architecting the Agentic Enterprise: Middleware, Durable State, and Event-Driven AI

**Duration:** 45 minutes. **Profile:** `w3`.
**Outcome:** recover an event-triggered workflow after failure without duplicate business effects.

| Minutes | Activity | Presenter cue / participant action |
|---|---|---|
| 0–6 | Autonomous System Resolver | Introduce an operational incident and simulated remediation |
| 6–13 | State ownership | Explain Kafka delivery, Temporal progress, and LangGraph reasoning |
| 13–23 | End-to-end demonstration | Incident → diagnosis → human approval wait |
| 23–35 | Guided recovery exercise | Restart the worker and redeliver the same incident |
| 35–41 | Approve and inspect | Resume remediation, examine workflow history and business state |
| 41–45 | Review and questions | Explain how the same durable wait supports longer processes |

**Exercise artifact:** recovered workflow history and exactly one remediation record.

**Acceptance:** approval state survives worker and Temporal server restart; duplicate incident delivery reuses the workflow; activity retries do not duplicate the business action; rejected approval performs no remediation.

**Execution model:** use the incident ID as stable Temporal workflow identity. Commit the Kafka offset only after workflow start is accepted or an existing matching workflow is confirmed. Keep model/tool I/O in activities, never deterministic workflow code. Do not claim exactly-once event delivery: business idempotency prevents duplicate effects.

**Checkpoints:** seeded incident → waiting for approval → worker restarted → remediation complete. A seconds-long demonstration illustrates durable waits; it does not experimentally prove multi-week availability.

## Workshop 4 — The Day the Agent Broke the Bank: Triple-Gate Architecture and A2A Security

**Duration:** 135 minutes. **Profile:** `w4`.
**Outcome:** investigate a synthetic incident and apply three boundaries, restricted identity, durable approval, and A2A task authorization.

| Minutes | Activity | Presenter cue / participant action |
|---|---|---|
| 0–10 | Incident briefing | Introduce NegotiatorBot and the payment scenario |
| 10–25 | Reproduce the unsafe action | Use a private vulnerable checkpoint with synthetic balances |
| 25–40 | Gate 1 | Apply provider access and inference budgets; explain limits of input filters |
| 40–60 | Gate 2 exercise | Restrict tools and enforce argument-aware policy |
| 60–65 | Break | Restore the next prepared checkpoint if needed |
| 65–85 | Gate 3 exercise | Inspect exchanged tokens, audiences, scopes, and denied requests |
| 85–105 | Approval exercise | Pause, approve, resume; reject changed arguments and duplicates |
| 105–120 | A2A demonstration/exercise | NegotiatorBot delegates to PaymentsAgent; reject another principal's task access |
| 120–130 | Incident reconstruction | Correlate traces, policy decisions, approvals, and business audit records |
| 130–135 | Review and questions | Discuss production separation, operations, and residual risks |

**Exercise artifact:** remediated configuration and a short incident evidence worksheet.

**Acceptance:** wrong-audience and insufficient-scope tokens fail; unsafe tool execution fails even when requested by the model; approval binds to exact payment arguments; agent identities cannot self-approve or access another owner's tasks; duplicates do not create duplicate payments.

**Checkpoints:** vulnerable → inference controls → capability controls → API identity → durable approval → secured A2A. Vulnerable checkpoints remain local or presenter-only and are never shared fallback defaults.

## Shared facilitator package

For each workshop deliver initial/completed checkpoints, exact expected outputs, a reset recipe, an exercise worksheet, an answer key, and presenter cues. Provide a visibly labelled recorded-model fixture for each live model interaction; run real policy/API/workflow components around that fixture.

Before each session: select profile, verify readiness, reset seed data, check live inference and replay, pre-warm caches, verify tracing, and record memory headroom. Save representative screenshots/traces as presentation fallback, with secrets removed.

See the [VPS setup guide](../setup/vps-setup-guide.md) and [implementation handoff](../implementation/agent-handoff.md).
