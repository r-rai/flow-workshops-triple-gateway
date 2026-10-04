# W3 real LangGraph agent with MiniMax — implementation prompt

Status: prepared 2026-10-04; implementation and live verification pending.

Copy the prompt below into the implementing agent's session. Supply the API key separately through an ignored local secret file or environment; do not paste it into this prompt.

```text
Implement the W3 real-agent upgrade in the Flo Bank workshop repository.

Workspace: /home/sysadmin/projects/flow-workshops-triple-gateway
Branch: feat/implement-novabank-platform

Objective
Replace W3's hard-coded diagnosis with an actual compiled LangGraph agent
using MiniMax for live reasoning and tool selection. Demonstrate:
Kafka case event -> Temporal activity -> LangGraph -> MiniMax through Gate 1
-> model-selected MCP read through Gate 2 and Gate 3 -> validated proposal
-> durable human approval -> idempotent settlement or rejection.
Keep an explicit offline replay mode using the SAME graph.
Complete the implementation and verification, not just a plan or scaffold.

Read first
- AGENTS.md instructions; use CodeGraph first if .codegraph exists.
- docs/workshops/delivery-plan.md, especially the W3 MiniMax implementation plan.
- docs/implementation/agent-handoff.md.
- docs/audits/2026-10-04-novabank-remediation-report.md.
- config/manifest.json.
- src/worker/activities.py, src/worker/workflow.py (singular),
  src/worker/main.py, src/worker/kafka_consumer.py.
- src/adapter/server.py, docker/apisix/apisix-w3.yaml,
  docker-compose.yml, docker/worker/requirements.txt, .env.example.
- workshops/w3/rehearsal_w3.py and existing API/preflight tests.

Starting state
The repo already contains extensive uncommitted audit remediation. Preserve
those changes; do not reset, clean, stash, or overwrite unrelated work.
The diagnosed delegation and settlement-binding bypasses have focused
verification, including database-enforced payment/task uniqueness and
concurrent [200, 409] outcomes. Keep those invariants intact.
W3 diagnosis currently uses case-ID/text branches in activities.py; there is
no actual LangGraph runtime in that activity. Temporal orchestration is real.
The shared Gate 1 adapter currently sends only model/messages upstream,
charges a synthetic fixed token amount, and has no useful agent tool-call
replay fixture. W3 currently lacks an inference route. Compose does not yet
wire MiniMax credentials/provider settings. Address these integration gaps.

MiniMax access and secrets
The user has a MiniMax API key. Configure an ignored .env/secret file with
placeholders and exact instructions. Use an existing explicitly configured
MINIMAX_API_KEY without printing its value. If absent, finish all independent
implementation/mock/replay work, then request only the secure configuration
step needed for live verification. Do not ask for the key in chat or search
unrelated credential stores. Do not claim live success without a provider call.
Verify official docs and the user's region/account-supported model:
https://platform.minimax.io/docs/api-reference/text-openai-api
https://platform.minimax.io/docs/guides/text-generation
International base: https://api.minimax.io/v1
Upstream completions URL: https://api.minimax.io/v1/chat/completions
MiniMax-M2.7 is a documented initial candidate; make model/URL configurable
and validate account access rather than assuming subscription entitlements.
Reuse or clearly map LLM_PROVIDER_URL and LLM_MODEL. Keep the provider key
only in the adapter. The worker must call APISIX Gate 1, never MiniMax directly.
Perform a small bounded provider smoke call before expensive rehearsals.

Required behavior
1. Compile and execute a real LangGraph state machine inside the Temporal
   diagnosis activity. Use explicit context/model/tool-validation/tool-execution/
   proposal-validation nodes and conditional edges. Keep all model/tool I/O
   out of deterministic Temporal workflow code. Pin compatible dependencies.
2. Discover the actual MCP catalog, expose allowlisted get_case/get_account
   read tools, and execute model-selected calls through the gateway with valid
   MCP identity, policy enforcement, token exchange, and API audience/scopes.
   Verify W3 OAuth exchange routes. Require at least one real model-selected
   read in live evidence. Diagnosis must have no approval/payment/reset tool
   or arbitrary HTTP execution capability. Validate every tool argument.
3. Extend Gate 1 for supported tools/tool_choice/output-limit fields and
   complete multi-turn assistant/tool-call messages. Preserve provider-required
   reasoning fields internally across turns. Use asynchronous HTTP I/O and
   handle both HTTP errors and provider error payloads. Do not dump private
   reasoning, keys, headers, or bearer tokens into logs, traces, or evidence.
4. Bound inference and tool loops: initially six model calls, eight tool calls,
   a 120-second total activity deadline, 2,048 completion tokens per call, and
   a configurable 16,000-token run budget. Verify supported limit fields and
   reasoning-token accounting. Reserve budget before calls; reconcile actual
   returned usage; cover retries/concurrency. No live fixed 35-token accounting.
   Align HTTP/activity/rehearsal timeouts. Bound retries across activity attempts
   so inference spend does not restart unchecked on every retry. Document any
   process-local accounting limits honestly.
5. Parse and validate a structured final proposal: case ID, amount in integer
   minor units, currency, permitted destination, and concise rationale tied
   to observed tool results. Apply deterministic server rules for beneficiary,
   amount, currency, and approval threshold. Never trust a model-provided
   approval decision. Treat case descriptions as untrusted instructions.
   Malformed output, denied tools, exhaustion, or provider failure cannot settle.
6. Preserve Temporal durable approval/recovery and Kafka stable workflow IDs
   and commit ordering. Bind human approval to exact validated payment arguments;
   use Core API proposal/approval controls when required by banking rules;
   preserve anti-self-approval and stable settlement idempotency. A repeated
   activity may repeat read-only inference; do not claim exactly-once LLM calls.
   Approved execution creates one payment; rejection creates zero payments.
7. USE_REPLAY_FIXTURES=true remains the offline default and feeds provider
   fixtures into the same graph while executing real gateway reads and policy.
   false means live MiniMax: missing credentials, bad credentials, timeout,
   rate limits, and malformed responses fail explicitly; no silent replay fallback.
   Preserve existing Gate 1 replay smoke clients and W1/W2/W4 behavior.
8. Show presenter-friendly mode/provider/model, node transitions, tool calls
   and summarized results, final rationale, approval phase, usage, and timings.
   Export redacted evidence correlated by case/workflow/run/trace identifiers.
   Save live/replay evidence separately and leave historical audit evidence intact.

Verification
- Write meaningful graph/protocol/error/validation tests with provider mocks
  and replay fixtures; ordinary tests must not require paid credentials.
- Test unknown tools, invalid arguments/proposals, prompt-injection case content,
  missing/invalid keys, provider failures, budget exhaustion, and bounded retries.
- Run existing API/preflight suites and direct test entrypoints.
- Run a bounded live MiniMax smoke test and W3 live/replay end-to-end rehearsals.
  Verify real graph execution, at least one model-selected MCP read, and genuine
  provider responses. Assert schemas/invariants, not exact nondeterministic prose.
- Rehearse approval, rejection, duplicate Kafka delivery, real worker SIGKILL
  recovery, one approved payment, and zero rejected payments. Confirm the
  completed diagnosis is reused after approval-wait recovery.
- Rerun W1-W4 verification and relevant shared adapter rehearsals. Keep one
  active profile at a time. Preserve caddy, portainer, uptime-kuma, and dozzle.
  Stay within the 6 GiB VPS budget and existing container limits; measure memory.
- Do not reset workshop databases until the rehearsal requires a documented
  reset. Stop relevant writers before SQLite resets, and verify subprocess exits.
- Check git diff --check, inspect the final diff, and record commands/exit codes.
  Do not commit/push/deploy externally unless separately requested.

Deliverables
Working real-agent implementation; pinned requirements; configuration and
secret setup instructions; live and replay W3 commands; updated plan/facilitator
guide/handoff/manifest; tests; fresh secret-free evidence; concise final report
of changed files, verified outcomes, costs/usage, and any genuinely blocked work.
Do not mark the upgrade implemented merely because documentation is updated.
```
