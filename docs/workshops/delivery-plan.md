# Flo Bank Workshop Delivery Plan

Status: the workshop runtime, W3 LangGraph remediation, and Flo Bank customer demo are implemented on `main`. Separate live/replay W3 rehearsal evidence was recorded on 2026-10-04. The customer chatbot connects to real hosted inference (`MiniMax-M2.7`) via APISIX Gate 1 with allowlisted session tools, supports dual-mode backend execution (standalone simulated vs APISIX Gate 3 real Core Banking), and retains deterministic offline scripted mode for zero-key environments.
Source session descriptions: [original brief](workshot.txt).

## Delivery model

- Audience: experienced API/integration engineers and architects.
- Participants run prebuilt local labs on 16 GB Windows laptops, with WSL2 capped near 5 GB.
- The presenter VPS runs one workshop at a time within a 6 GB total operating budget.
- Participants bring hosted-model credentials; deterministic replay supports every exercise without a provider.
- Each workshop starts independently from seeded data and an initial checkpoint.
- Installation and image downloads happen before the session. Timed sessions contain short guided exercises.
- The VPS provides presenter demonstrations and at most two concurrent fallback runs initially; this is an operating limit pending testing, not a capacity guarantee.

Use fictional Flo Bank accounts, beneficiaries, payments, support cases, and incidents throughout.
Do not claim the development deployment itself is production-ready. Explain which controls and operational components a production deployment would require.

## Workshop 1 — Modernizing APIs for AI Agents: From OpenAPI to MCP

**Duration:** 45 minutes. **Profile:** `w1`.
**Outcome:** generate, curate, and invoke tools while preserving downstream API authorization.

| Minutes | Activity | Presenter cue / participant action |
|---|---|---|
| 0–5 | Introduce Flo Bank support agent | Show the account-support request and expected business outcome |
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
**Outcome:** run a real LangGraph agent with MiniMax to investigate a dispute and propose a resolution, then recover the event-triggered Temporal workflow after failure without duplicate business effects. Keep an explicit offline replay mode for exercises without provider access.

| Minutes | Activity | Presenter cue / participant action |
|---|---|---|
| 0–6 | Flo Bank dispute resolver | Inspect a fictional support case; identify live MiniMax or offline replay mode |
| 6–13 | State ownership | Explain Kafka delivery, Temporal progress, and actual LangGraph execution inside an activity |
| 13–23 | End-to-end demonstration | Case event → model-selected MCP reads → validated proposal → human approval wait |
| 23–35 | Guided recovery exercise | Restart the worker and redeliver the same case event |
| 35–41 | Approve and inspect | Resume settlement; inspect graph steps, tool outcomes, workflow history, and business state |
| 41–45 | Review and questions | Explain how the same durable wait supports longer processes |

**Exercise artifact:** recovered workflow history, graph/tool execution evidence, and exactly one approved settlement payment. A rejected dispute closes with zero payments. Use the existing dispute workflow as the implementation baseline; an additional incident-remediation scenario is outside this upgrade.

**Acceptance:** live mode executes a compiled LangGraph graph, calls MiniMax through Gate 1, and executes at least one model-selected, allowlisted read tool through MCP/Gate 2 and Gate 3. Validated proposals pause when server rules require approval; approval state survives worker and Temporal server restart; duplicate case delivery reuses the workflow; activity retries do not duplicate settlement; rejection creates no payment. Provider failure never produces a replay response labelled as live success.

**Execution model:** use the case ID as stable Temporal workflow identity for the dispute lab. Commit the Kafka offset only after workflow start is accepted or an existing matching workflow is confirmed. Keep model/tool I/O in activities, never deterministic workflow code. Do not claim exactly-once event delivery: business idempotency prevents duplicate effects.

For the existing dispute implementation, the stable workflow ID is `dispute-case-{case_id}`. Temporal owns durable progress, approval, and retry history. LangGraph owns the bounded diagnosis/tool loop within the activity. A failed activity may repeat inference and read tools; completed activity results are replayed by Temporal. Do not claim exactly-once inference or preservation of unfinished graph steps without an explicit checkpoint implementation.

**Checkpoints:** seeded case → graph and MCP reads → validated proposal → waiting for approval → worker restarted → settlement or rejection complete. A seconds-long demonstration illustrates durable waits; it does not experimentally prove multi-week availability.

### W3 real-agent implementation plan — MiniMax (historical scope)

**Historical scope:** the plan below records the original upgrade requirements; current code and recorded verification are in the implementation handoff. Replace the hard-coded diagnosis in `src/worker/activities.py` with actual LangGraph execution using the user's MiniMax API access. Retain the tested Kafka/Temporal recovery behavior, gateway controls, and settlement invariants. The implementation handoff is [the copyable agent prompt](../implementation/w3-minimax-agent-prompt.md).

1. **Provider configuration and routing.** Use MiniMax's OpenAI-compatible protocol behind the existing APISIX Gate 1 endpoint. The international provider base is `https://api.minimax.io/v1`; the full upstream completion URL is `https://api.minimax.io/v1/chat/completions`. Verify the user's key region, account entitlement, and a supported tool-capable model before a bounded smoke call. Keep model and endpoint configurable; `MiniMax-M2.7` is a documented starting candidate, not a claim of account access. Store `MINIMAX_API_KEY` in an ignored local secret file/environment and expose it only to the provider adapter. Add explicit Compose mappings and placeholder configuration; never put the key in the worker, model messages, source, traces, or evidence. Worker inference goes to APISIX, not directly to MiniMax. Add the missing W3 inference route and verify token-exchange routing needed by MCP tools.
2. **Gate 1 protocol and budgets.** The current adapter forwards only `model` and `messages`; extend its validated request handling for tool definitions, tool selection, and supported output limits. Preserve complete assistant/tool-call messages and any provider-required reasoning fields in conversation state, while excluding private reasoning from logs and exported evidence. Use asynchronous provider I/O, explicit timeouts, bounded retries, actual returned usage accounting, and budget reservation before dispatch. Replace the synthetic fixed 35-token charge for live calls. Bound each activity run by six model calls, eight tool calls, a 120-second deadline, and a configurable token budget (initial target: 16,000 total tokens and 2,048 completion tokens per call, including reasoning where the provider counts it). Align provider, activity, workflow, and rehearsal timeouts. Document that retries may repeat billable inference; bounds must include retries, not reset per attempt.
3. **Real graph and tools.** Pin compatible LangGraph/provider dependencies. Compile an explicit state graph: prepare case context → ask model → validate requested tools → execute allowlisted reads → return tool results → ask model again or validate final proposal → finish. Start with `get_case` and `get_account` from the actual MCP catalog. Require at least one real model-selected read in the live demonstration. Reject unknown tools and malformed arguments; do not expose payment execution, approval, reset, or arbitrary HTTP access to the diagnosis graph. A final proposal must contain a schema-validated amount in integer minor units, currency, destination, case identity, and concise evidence-based rationale. Do not determine live proposals through case-ID branches or canned text.
4. **Settlement governance.** Treat case descriptions and model output as untrusted. Resolve permitted accounts/beneficiaries, approval thresholds, amount limits, and currency through server rules, not the model's `requires_approval` flag. The model proposes; Temporal pauses and the authorized executor settles. Keep human approval bound to the validated exact proposal and use the existing Core API approval/proposal mechanism whenever required by banking rules. Agent identities cannot approve themselves. Retain stable payment idempotency keys and prohibit settlement on malformed output, denied tools, provider errors, budget exhaustion, or rejection.
5. **Replay and presenter experience.** Live mode (`USE_REPLAY_FIXTURES=false`) calls MiniMax; replay mode (`true`, default) supplies recorded/synthetic provider message fixtures to the same compiled graph, with real gateway reads and business controls. Label mode, provider/model, graph steps, tool names/results, final rationale, approval phase, usage, and elapsed time. Never silently switch modes. Existing simple Gate 1 replay smoke checks must keep working. Keep evidence for live and replay runs separate and secret-free.
6. **Verification and delivery.** Add meaningful tests for tool-call message round trips, graph routing, argument/output validation, timeouts, provider/configuration errors, budget exhaustion, and malicious case content. Run a bounded live MiniMax smoke test, then W3 live/replay rehearsals including approval, rejection, duplicate delivery, and real worker SIGKILL recovery. Assert workflow/business outcomes rather than exact model prose. Save correlated workflow/graph/gateway evidence. Rerun API/preflight tests and W1–W4 verification because the adapter is shared. Keep one active profile, preserve protected host services and historical audit artifacts, and measure memory headroom. Update the manifest/handoff to distinguish verified live behavior from replay and remaining requirements.

**Completion evidence:** a successful live provider response, a model-selected MCP read with its real result, a validated proposal and human approval boundary, exactly one approved payment despite redelivery/recovery, zero rejected payments, a reproducible replay run using the same graph, and command/exit-code evidence for shared regressions. Recorded [live](../../workshops/w3/evidence/rehearsal-live-2026-10-04T090416Z.json) and [replay](../../workshops/w3/evidence/rehearsal-replay-2026-10-04T085050Z.json) evidence is available. Rehearse again for each delivery environment; saved evidence is not a fresh deployment check.

**Provider references (checked 2026-10-04):** [MiniMax OpenAI-compatible API](https://platform.minimax.io/docs/api-reference/text-openai-api) and [model invocation/configuration](https://platform.minimax.io/docs/guides/text-generation). Recheck model availability and protocol requirements during implementation. Actual LangGraph execution also works offline; paid inference is required only for the live MiniMax demonstration.

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
