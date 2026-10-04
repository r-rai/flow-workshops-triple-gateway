# Flo Bank customer demo: real LLM implementation plan

Status: approved direction, implementation pending. Written on 2026-10-04.
This document is the resume context and the implementation handoff for agy.

## Resume context

- Repository: `r-rai/flow-workshops-triple-gateway`; delivery branch: `main`.
- Baseline before this plan: `7c45983`. Agy merged the workshop remediation,
  Flo Bank UI, and demo Compose profile at `8dcae8b`.
- The user wants the customer-facing Flo bot to call a real LLM. Turning on
  live W3 inference alone does not do that today.
- Keep the original `docker-compose.yml` as the user-facing startup file.
  Preserve the simple command `docker compose --profile demo up -d --build`
  and the UI at `http://localhost:8000`.
- Login remains simulated: `maya@flobank.demo` / `flo-demo`. Banking data and
  actions remain fictional and session-scoped even when inference is live.
- Current customer chat is a keyword router in `src/demo/app.py`; it makes
  no model calls. W3 is a separate LangGraph/Temporal investigation agent.
- Existing Gate 1 code in `src/adapter/server.py` forwards OpenAI-compatible
  tool/message requests to MiniMax or serves explicit replay fixtures. It
  already accepts `LLM_PROVIDER_URL`, `LLM_MODEL`, and `MINIMAX_API_KEY`.
- The prior verification passed 49 Python tests, Compose startup/health,
  and `tests/demo_bank_browser.cjs`. That verifies the scripted baseline,
  not this planned live customer chatbot.
- Use Flo Bank identifiers for current infrastructure and preserve historical
  evidence as written. Public branding is Flo Bank. Preserve existing host services
  and any unrelated working-tree changes.

## Outcome and scope

A signed-in user chats naturally with Flo, including follow-up questions.
The server calls the configured model through APISIX Gate 1. The model can
request a small allowlist of tools backed by the user's fictional session.
Tool results supply account balances, transactions, spending, card state,
and dispute records. The dashboard updates after successful simulated actions.

The first release uses the existing configurable MiniMax integration.
Do not require a local LLM or rebuild the W3 workflow. Do not introduce a
second Compose file, additional startup scripts, or real customer authentication.
Real money movement and enterprise-ledger access are outside this feature.

## Read before editing

Use CodeGraph first if the checkout has `.codegraph`; do not create an index.
Read repository instructions and these implementation surfaces:

| Surface | Current files | Planned responsibility |
|---|---|---|
| Demo sessions/API | `src/demo/app.py` | Authenticated chat orchestration, session history, session-scoped state |
| Demo model client | New module under `src/demo/`, such as `llm.py` | Async Gate 1 requests, provider-response handling, bounded tool loop |
| Demo tool functions | New module under `src/demo/`, such as `tools.py` | Validated reads and simulated mutations, reusable by scripted mode |
| UI | `src/demo/static/app.js`, `index.html`, `styles.css` | Live-mode indication, loading/error behavior, returned dashboard state |
| Inference adapter | `src/adapter/server.py` | Reuse provider forwarding and budget controls without breaking W3 |
| Compose/config | `docker-compose.yml`, `.env.example`, existing Dockerfiles | One-command demo topology, backend-only secrets and URLs |
| APISIX | `docker/apisix/config.yaml`, existing route files | Dedicated demo inference routing with a fixed config |
| Contracts/tests | `tests/test_demo_bank.py`, `tests/demo_bank_browser.cjs`, W3/API tests | Live/mock/tool/session failures plus existing regressions |
| Delivery docs | Root README, participant/VPS guides, manifest, agent handoff | Current launch/configuration instructions and honest evidence |

Check the current official provider documentation before changing protocol
handling or model defaults. The existing `MiniMax-M2.7` setting is a baseline,
not a guarantee of account access. Use configured credentials without printing
them; do not search unrelated credential stores or ask for keys in chat.

## 1. Keep one Compose command

Recommended standalone demo topology:

```text
Browser -> demo (/demo-api/chat)
              |
              v
        demo-gateway (APISIX Gate 1)
              |
              v
        demo-inference (existing adapter implementation)
              |
              v
        configured hosted LLM
```

Keep `demo` as the UI/API service in the existing `demo` profile. Add a focused
`demo-gateway` and `demo-inference` to that same profile, reusing existing images
and provider code rather than copying a separate inference implementation.
Give the demo gateway a fixed internal route configuration, for example
`docker/apisix/apisix-demo.yaml`; do not make laptop users remember a separate
`ACTIVE_PROFILE=demo` routing setting. Publish only the UI port. The internal
inference route should expose only the required Gate 1 endpoints, not MCP,
OAuth, enterprise APIs, or budget-reset administration.

The demo backend calls the internal gateway URL. The provider key belongs only
in `demo-inference`; neither the browser nor the demo API needs it. Isolate this
inference process/budget from a concurrently running workshop adapter, and do
not join the standalone demo to enterprise backend/persistence networks.

Retain existing W1–W4 service selections and routes. For the UI mounted in the
core API, support an explicit live configuration pointing to its workshop Gate 1
where available (W2–W4). W1 must remain explicitly scripted unless an inference
route is separately provided; do not imply that W1 already supports Gate 1.

Recommended settings, to finalize during implementation:

- `DEMO_CHAT_MODE=live` as the new customer-demo default. Keep `scripted` as an
  explicitly selected offline alternative for tests and demos without a key.
- `DEMO_AI_GATEWAY_URL` for the server's internal completion endpoint.
- Existing provider key/URL/model settings mapped to the inference service.
- Independent configurable request timeout, history limit, output limit,
  session turn limit, and demo inference budget.

No key is committed to `.env.example`. Configure the key once in ignored `.env`
(or a supported local secret mount), then keep the same Compose startup command.
Readiness must distinguish a running UI from configured, available live chat;
missing credentials should produce a clear setup state rather than a generic
unhealthy-container loop that prevents opening the login page.

## 2. Implement session-scoped real conversation

1. Extract existing fictional banking operations from the keyword dispatcher
   into reusable deterministic functions, preserving scripted behavior.
2. Add bounded conversation history to `DemoSession`, with a per-session lock
   or equivalent serialization. Do not accept authoritative system prompts,
   previous tool results, session identity, or credentials from the browser.
3. Build a server-owned Flo Bank system prompt describing the fictional context,
   permitted tools, current mode, and instruction/data boundaries. Treat customer
   text, merchant labels, and tool data as untrusted content.
4. Call Gate 1 asynchronously with the configured model and allowlisted tools.
   Preserve required assistant/tool-call messages between turns. Keep private
   provider reasoning out of UI replies, logs, and exported evidence.
5. Validate each requested tool name and arguments on the server; execute against
   the authenticated session only. Append actual tool results before continuing
   the model loop. Handle text-only replies and multiple tool calls correctly.
6. Bound each chat turn: initially at most 4 model rounds and 8 tool calls,
   with a configurable overall deadline and completion limit. The adapter's
   accounting must include tool definitions/history and completion reservation;
   charge actual provider usage rather than a canned live token estimate.
7. Stop on tool/protocol/provider errors or exhausted limits. Do not silently
   switch a live request to scripted replies or replay. Prevent automatic retry
   from duplicating a dispute or other simulated action.
8. Revalidate the session after awaited I/O. Logout/expiry must prevent an
   in-flight request from committing history or state after session revocation.
   Clear history, pending work, and state on sign-out/restart as appropriate.

Use a small allowlist, such as `get_demo_accounts`, `get_demo_transactions`,
`get_demo_spending`, `get_demo_card`, `set_demo_card_state`,
`create_demo_dispute`, and `get_demo_disputes`. Currency calculations stay in
integer minor units. Transaction IDs must belong to the session's fixtures;
state changes are deterministic and idempotent. The model cannot supply another
customer identity, invoke arbitrary URLs/functions, or obtain a Gate 3 token.

For mutations followed by a provider failure, avoid an ambiguous partial result:
choose staged session changes committed only after successful turn completion,
or explicitly return the authoritative action result and failed-inference state.
Do not claim an action happened solely because the model says it did. Preserve
simple card controls and dispute actions; no real payment capability is added.

## 3. Preserve the UI and make mode honest

Keep `/demo-api/chat` and the existing `reply` / `dashboard` response contract.
Separate the existing banking-data `mode: simulation` from inference mode, e.g.
`chat_mode: live|scripted`, plus safe model/usage/request metadata where helpful.
“Simulation” must continue to mean fictional bank data, even with live inference.

Expose safe chat status (configured, available, mode, model) without keys or
provider bodies. Replace “SCRIPTED DEMO” and the scripted welcome text only when
live chat is actually selected/configured. A live failure shows a recoverable
message and retains the user's draft. The UI should make clear that real AI
answers are being generated over fictional banking data.

Preserve `textContent` rendering, mobile layouts, pending-message handling,
startup-generation guards, logout behavior, and draft-preservation regressions.
Do not send passwords, cookies, signing keys, or API/provider tokens to the model.
Trim history in a way that keeps tool-call/result pairs valid and session budgets
bounded. Streaming is optional after the non-streaming flow works; it is not a
first-release dependency.

## 4. Verification and acceptance

Write meaningful tests before implementation changes. Default automated tests
must use explicit scripted mode or mock provider responses, never an accidental
paid provider call.

Cover:

- A normal question reaches Gate 1; a balance answer uses actual demo tools.
- A follow-up such as “what about my savings?” retains the correct session context.
- Unknown tools, malformed arguments, and foreign transaction/session identifiers
  are rejected; injected text cannot access enterprise tools or reveal secrets.
- Card freeze/unfreeze and dispute creation update only that session's dashboard;
  retried requests do not duplicate effects.
- Missing key, provider 401/429/5xx, timeout, malformed replies, and exhausted
  budgets produce honest errors without live-to-scripted fallback.
- Concurrent turns, logout during inference, expired sessions, and history
  trimming do not leak data or commit revoked-session changes.
- The browser shows the correct mode, preserves drafts on errors, and still
  passes the existing login/layout/XSS/delayed-response checks.
- W1–W4 configuration and shared inference/API tests still pass.

Run the full Python suite, Compose configuration checks for all profiles, and
the existing/extended browser smoke suite. Use a temporary Compose project/port
for tests instead of changing protected services or resetting workshop data.

After mock/scripted checks pass, perform one bounded live provider smoke test
using an explicitly configured key. Show a real provider response, one
model-selected demo read with its real tool result, and a follow-up turn.
Collect redacted mode/model/request ID/usage/tool-outcome evidence. The user has
requested real LLM integration, so a bounded live verification is in scope once
credentials are configured. If credentials are absent, finish independent work
and state that live verification is pending; do not claim it passed.

Done means the laptop user configures an ignored key, runs the original Compose
command, signs in, and gets genuine model-generated replies grounded in session
fixtures. Update docs, manifest/profile limits, and evidence to reflect the new
three-service demo and explicit offline mode. Retain the fictional-bank warning
and distinguish customer chat from the W3 agent.

## Copyable task for agy or the next chat

```text
Implement docs/implementation/demo-real-llm-plan.md on a fresh feature branch
from current main. The user wants the customer-facing Flo Bank bot to use a
real hosted LLM through APISIX Gate 1, with fictional session-scoped banking
and the same single docker-compose.yml startup command. Read the resume
context and current agent handoff first. Preserve existing workshop controls,
public branding, unrelated changes, and protected host services. Complete
implementation, tests, UI checks, docs, and bounded live verification when an
explicitly configured key is available. Do not label scripted/mock/replay as
live success. Report the final branch, commands, verification evidence, and
any remaining credential-dependent work.
```
