# Workshop 4: The day the agent broke the bank

Implementing Triple-Gate Architecture & A2A Security for Autonomous AI Workloads

Duration: 150 minutes. Last slide is presenter reference outside the timed agenda.

Expected outcomes in these slides are instructional targets, not fresh execution results.

Delivery: 15-minute gateway primer followed by the 135-minute lab, including its seven-minute break.

## 01. API gateway: govern business requests

**Timing:** Gateway primer / 15 minutes before the lab

Introduce the sequence: API gateways govern business-service traffic; AI gateways manage model traffic; MCP gateways govern tool-facing traffic. These are responsibilities, not necessarily three products. This deck adds a 15-minute primer before the existing 135-minute lab; start the lab clock at the incident opening. Ask which gateways participants already operate. Source: https://apisix.apache.org/learning-center/mcp-protocol-ai-gateway/

Sources: [workshop-4-story.md](../../../docs/workshops/workshop-4-story.md), [worksheet.md](../../../workshops/w4/worksheet.md), [answer-key.md](../../../workshops/w4/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md), [runbook.md](../../../workshops/w4/runbook.md), [incident.py](../../../src/demo/incident.py), [server.py](../../../src/adapter/server.py), [apisix-w4.yaml](../../../docker/apisix/apisix-w4.yaml)

## 02. How an API gateway works

**Timing:** Gateway primer

Walk through an account read and a payment write. A gateway matches a configured route, applies authentication, limits and transformation as configured, then forwards to an upstream. The service still enforces domain rules. In W4, APISIX protects the route while the banking API validates JWT audience/scopes and transaction invariants. Do not imply every rule lives in APISIX. Source: https://apisix.apache.org/docs/apisix/getting-started/

Sources: [workshop-4-story.md](../../../docs/workshops/workshop-4-story.md), [worksheet.md](../../../workshops/w4/worksheet.md), [answer-key.md](../../../workshops/w4/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md), [runbook.md](../../../workshops/w4/runbook.md), [incident.py](../../../src/demo/incident.py), [server.py](../../../src/adapter/server.py), [apisix-w4.yaml](../../../docker/apisix/apisix-w4.yaml)

## 03. API gateway capabilities

**Timing:** Gateway primer

Explain one capability at a time. Access controls decide whether a request reaches a service; reliability controls determine how traffic reaches available upstreams; telemetry explains what happened. W4 uses stable financial keys in the service for one-effect retries. Gateway retries alone do not make payments idempotent. These are configured capabilities, not a claim that every plugin is enabled in this lab. Source: https://apisix.apache.org/docs/apisix/plugins/

Sources: [workshop-4-story.md](../../../docs/workshops/workshop-4-story.md), [worksheet.md](../../../workshops/w4/worksheet.md), [answer-key.md](../../../workshops/w4/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md), [runbook.md](../../../workshops/w4/runbook.md), [incident.py](../../../src/demo/incident.py), [server.py](../../../src/adapter/server.py), [apisix-w4.yaml](../../../docker/apisix/apisix-w4.yaml)

## 04. AI gateway: manage model consumption

**Timing:** Gateway primer

Distinguish general APISIX AI capabilities from the W4 implementation. Model proxying and configured routing can centralize provider access. W4 implements a pre-dispatch token reservation in src/adapter/server.py; do not present it as proof of production distributed budget accounting. A refusal or inference denial cannot authorize an independent payment. Sources: https://apisix.apache.org/docs/apisix/plugins/ai-proxy-multi/ and https://apisix.apache.org/docs/apisix/plugins/ai-rate-limiting/

Sources: [workshop-4-story.md](../../../docs/workshops/workshop-4-story.md), [worksheet.md](../../../workshops/w4/worksheet.md), [answer-key.md](../../../workshops/w4/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md), [runbook.md](../../../workshops/w4/runbook.md), [incident.py](../../../src/demo/incident.py), [server.py](../../../src/adapter/server.py), [apisix-w4.yaml](../../../docker/apisix/apisix-w4.yaml)

## 05. How the AI gateway evaluates a request

**Timing:** Gateway primer

Use a familiar allowance analogy: a small amount already consumed does not mean a huge next request fits. W4 estimates serialized input at roughly four characters per token and caps reserved output at 2048. Its counter and lock are process-local, so multi-worker/distributed state is production work. Do not run the budget-reset endpoint during the incident to manufacture a result.

Sources: [workshop-4-story.md](../../../docs/workshops/workshop-4-story.md), [worksheet.md](../../../workshops/w4/worksheet.md), [answer-key.md](../../../workshops/w4/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md), [runbook.md](../../../workshops/w4/runbook.md), [incident.py](../../../src/demo/incident.py), [server.py](../../../src/adapter/server.py), [apisix-w4.yaml](../../../docker/apisix/apisix-w4.yaml)

## 06. MCP gateway: expose governed capabilities

**Timing:** Gateway primer

Introduce MCP as a protocol for connecting clients to tools and other server capabilities. Focus on tools/list and tools/call for this workshop. MCP does not inherently make every exposed tool safe. APISIX can expose OpenAPI operations as tools; W4 uses the protected adapter/OPA path for argument-aware tool decisions. Sources: https://modelcontextprotocol.io/specification/2025-11-25/server/tools and https://apisix.apache.org/docs/apisix/plugins/openapi-to-mcp/

Sources: [workshop-4-story.md](../../../docs/workshops/workshop-4-story.md), [worksheet.md](../../../workshops/w4/worksheet.md), [answer-key.md](../../../workshops/w4/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md), [runbook.md](../../../workshops/w4/runbook.md), [incident.py](../../../src/demo/incident.py), [server.py](../../../src/adapter/server.py), [apisix-w4.yaml](../../../docker/apisix/apisix-w4.yaml)

## 07. How the MCP gateway handles a payment

**Timing:** Gateway primer

Show the difference between transport success and successful tool execution. The adapter can return an MCP result with isError=true and POLICY_DENIED text under HTTP 200. Identity must come from validated credentials, not a role supplied in the prompt. Explain that approved calls still encounter the banking boundary. Source: https://modelcontextprotocol.io/specification/2025-11-25/server/tools

Sources: [workshop-4-story.md](../../../docs/workshops/workshop-4-story.md), [worksheet.md](../../../workshops/w4/worksheet.md), [answer-key.md](../../../workshops/w4/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md), [runbook.md](../../../workshops/w4/runbook.md), [incident.py](../../../src/demo/incident.py), [server.py](../../../src/adapter/server.py), [apisix-w4.yaml](../../../docker/apisix/apisix-w4.yaml)

## 08. Three gateways, three different decisions

**Timing:** Gateway primer

Ask the audience to classify three requests: an account GET, a model completion, and create_payment via tools/call. Explain why an inference denial says nothing about an independent direct banking call. APISIX hosts the three logical boundaries; adapters and the banking API supply additional checks. Ground the model in the actual W4 routes, rather than claiming three physically isolated gateways.

Sources: [workshop-4-story.md](../../../docs/workshops/workshop-4-story.md), [worksheet.md](../../../workshops/w4/worksheet.md), [answer-key.md](../../../workshops/w4/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md), [runbook.md](../../../workshops/w4/runbook.md), [incident.py](../../../src/demo/incident.py), [server.py](../../../src/adapter/server.py), [apisix-w4.yaml](../../../docker/apisix/apisix-w4.yaml)

## 09. Flo Bank: Triple-Gate architecture

**Timing:** Gateway primer

Follow the top inference lane, then the lower execution lane. Model output returns to the agent backend, which requests tools. Gate 2 asks OPA about identity and actual arguments. Gate 3 includes APISIX routing and banking API JWT validation. Independent review binds exact proposal values; the API manages settlement, stable retry keys and task/payment binding. Jaeger supplies observed traces. The isolated vulnerable ledger is separate from this protected lane. The diagram uses editable PowerPoint shapes.

Sources: [workshop-4-story.md](../../../docs/workshops/workshop-4-story.md), [worksheet.md](../../../workshops/w4/worksheet.md), [answer-key.md](../../../workshops/w4/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md), [runbook.md](../../../workshops/w4/runbook.md), [incident.py](../../../src/demo/incident.py), [server.py](../../../src/adapter/server.py), [apisix-w4.yaml](../../../docker/apisix/apisix-w4.yaml)

## 10. Presenter lab and QR observers

**Timing:** Gateway primer

Explain the two participation modes before people scan. Local pairs can edit policy and identity checkpoints. Phones use the separate observation entrypoint, event access code, and curated runs. The audience code grants viewing only; it is distinct from the local reviewer password. Observer timelines identify the selected recorded run and label original incident context separately.

Sources: [workshop-4-story.md](../../../docs/workshops/workshop-4-story.md), [worksheet.md](../../../workshops/w4/worksheet.md), [answer-key.md](../../../workshops/w4/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md), [runbook.md](../../../workshops/w4/runbook.md), [incident.py](../../../src/demo/incident.py), [server.py](../../../src/adapter/server.py), [apisix-w4.yaml](../../../docker/apisix/apisix-w4.yaml)

## 11. Join the Incident Room

**Timing:** Audience access

Allow the room time to scan. The QR encodes only https://w4.ravirai.in/workshop-4; the event code is entered separately on the page. Verify the displayed expiry against the running observer service before delivery. This audience code is intentionally shown on the event slide, while reviewer and sandbox secrets remain private. The repository deck is reusable without a live code; the separate event deck includes the configured audience code.

Sources: [workshop-4-story.md](../../../docs/workshops/workshop-4-story.md), [worksheet.md](../../../workshops/w4/worksheet.md), [answer-key.md](../../../workshops/w4/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md), [runbook.md](../../../workshops/w4/runbook.md), [incident.py](../../../src/demo/incident.py), [server.py](../../../src/adapter/server.py), [apisix-w4.yaml](../../../docker/apisix/apisix-w4.yaml)

## 12. The day the agent broke the bank

**Timing:** 0–8 min

Open http://localhost:9080/workshop-4?view=presenter. Say: the credentials were valid, the request passed schema validation, and the fictional bank still lost ₹90 lakh. What did we authorize? Withhold the ticket until the next chapter. Declare that the incident is a recorded proposal executed in an isolated local ledger.

Sources: [workshop-4-story.md](../../../docs/workshops/workshop-4-story.md), [worksheet.md](../../../workshops/w4/worksheet.md), [answer-key.md](../../../workshops/w4/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md), [runbook.md](../../../workshops/w4/runbook.md), [incident.py](../../../src/demo/incident.py), [server.py](../../../src/adapter/server.py), [apisix-w4.yaml](../../../docker/apisix/apisix-w4.yaml)

## 13. ₹90 lakh

**Timing:** 0–8 min

Collect predictions: identity, model, tool policy or approval? Record local votes without a polling service. The visible success status and credential validity establish neither transaction legitimacy nor correct delegation. No live model compromise is being asserted.

Sources: [workshop-4-story.md](../../../docs/workshops/workshop-4-story.md), [worksheet.md](../../../workshops/w4/worksheet.md), [answer-key.md](../../../workshops/w4/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md), [runbook.md](../../../workshops/w4/runbook.md), [incident.py](../../../src/demo/incident.py), [server.py](../../../src/adapter/server.py), [apisix-w4.yaml](../../../docker/apisix/apisix-w4.yaml)

## 14. Your assignment: repair and prove the bank still works

**Timing:** 0–8 min

Use one prepared local instance per pair. Shared hosting is observation/fallback only. Give each pair one task and one evidence artifact at a time; keep explanation blocks under seven minutes.

Sources: [workshop-4-story.md](../../../docs/workshops/workshop-4-story.md), [worksheet.md](../../../workshops/w4/worksheet.md), [answer-key.md](../../../workshops/w4/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md), [runbook.md](../../../workshops/w4/runbook.md), [incident.py](../../../src/demo/incident.py), [server.py](../../../src/adapter/server.py), [apisix-w4.yaml](../../../docker/apisix/apisix-w4.yaml)

## 15. The incident-response clock / first half

**Timing:** 0–8 min

Keep the opening tight. The seven-minute break is included in the full 135 minutes. Completed local checkpoints are available for stalled pairs.

Sources: [workshop-4-story.md](../../../docs/workshops/workshop-4-story.md), [worksheet.md](../../../workshops/w4/worksheet.md), [answer-key.md](../../../workshops/w4/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md), [runbook.md](../../../workshops/w4/runbook.md), [incident.py](../../../src/demo/incident.py), [server.py](../../../src/adapter/server.py), [apisix-w4.yaml](../../../docker/apisix/apisix-w4.yaml)

## 16. The incident-response clock / second half

**Timing:** 0–8 min

Create approval proposals immediately before review: they expire after ten minutes. Leave enough time for legitimate settlement and evidence reconstruction. A blocked attack suite alone is insufficient to prove the repaired business path.

Sources: [workshop-4-story.md](../../../docs/workshops/workshop-4-story.md), [worksheet.md](../../../workshops/w4/worksheet.md), [answer-key.md](../../../workshops/w4/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md), [runbook.md](../../../workshops/w4/runbook.md), [incident.py](../../../src/demo/incident.py), [server.py](../../../src/adapter/server.py), [apisix-w4.yaml](../../../docker/apisix/apisix-w4.yaml)

## 17. Follow the money across the handoff

**Timing:** 8–20 min

Reveal the ticket, recorded proposal and handoff. Ask which checks are missing at each boundary. The console replays fixed server-owned scenarios; the prediction/view controls do not enforce policy.

Sources: [workshop-4-story.md](../../../docs/workshops/workshop-4-story.md), [worksheet.md](../../../workshops/w4/worksheet.md), [answer-key.md](../../../workshops/w4/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md), [runbook.md](../../../workshops/w4/runbook.md), [incident.py](../../../src/demo/incident.py), [server.py](../../../src/adapter/server.py), [apisix-w4.yaml](../../../docker/apisix/apisix-w4.yaml)

## 18. Replay one incident; inspect two ledgers

**Timing:** 8–20 min

The isolated sandbox is a presenter-only service with a separate disposable ledger and no protected volumes or provider/banking keys. Starting w4 alone does not enable it; follow the answer-key setup before delivery. Do not expose secrets in slides or exports.

Sources: [workshop-4-story.md](../../../docs/workshops/workshop-4-story.md), [worksheet.md](../../../workshops/w4/worksheet.md), [answer-key.md](../../../workshops/w4/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md), [runbook.md](../../../workshops/w4/runbook.md), [incident.py](../../../src/demo/incident.py), [server.py](../../../src/adapter/server.py), [apisix-w4.yaml](../../../docker/apisix/apisix-w4.yaml)

## 19. The Triple-Gate model

**Timing:** 20–33 min

These are logical responsibilities in the lab, sharing APISIX infrastructure. No single boundary owns every failure. Prompt refusal cannot establish that direct tool or API calls are controlled.

Sources: [workshop-4-story.md](../../../docs/workshops/workshop-4-story.md), [worksheet.md](../../../workshops/w4/worksheet.md), [answer-key.md](../../../workshops/w4/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md), [runbook.md](../../../workshops/w4/runbook.md), [incident.py](../../../src/demo/incident.py), [server.py](../../../src/adapter/server.py), [apisix-w4.yaml](../../../docker/apisix/apisix-w4.yaml)

## 20. Gate 1: stop dispatch when the budget is exhausted

**Timing:** 20–33 min

Show zero dispatch evidence for the budget scenario. Optional live comparison makes one bounded call and executes no tools. Report the actual response, refusal or live_failed outcome without relabelling a recorded result.

Sources: [workshop-4-story.md](../../../docs/workshops/workshop-4-story.md), [worksheet.md](../../../workshops/w4/worksheet.md), [answer-key.md](../../../workshops/w4/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md), [runbook.md](../../../workshops/w4/runbook.md), [incident.py](../../../src/demo/incident.py), [server.py](../../../src/adapter/server.py), [apisix-w4.yaml](../../../docker/apisix/apisix-w4.yaml)

## 21. Why 140 / 100,000 can still produce a denial

**Timing:** 20–33 min

Show GET /ai/budget and the 200 headroom response, then the 429 inference denial. Explain accumulated usage + estimated prompt + reserved output > limit. The workshop constructs a synthetic large prompt from available headroom; the live counter may differ from 140. Inference consumption and the bank account balance are different budgets. Expected protected effect is zero, but that alone does not prove direct payment protection.

Sources: [workshop-4-story.md](../../../docs/workshops/workshop-4-story.md), [worksheet.md](../../../workshops/w4/worksheet.md), [answer-key.md](../../../workshops/w4/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md), [runbook.md](../../../workshops/w4/runbook.md), [incident.py](../../../src/demo/incident.py), [server.py](../../../src/adapter/server.py), [apisix-w4.yaml](../../../docker/apisix/apisix-w4.yaml)

## 22. Gate 2: isolate the reason for denial

**Timing:** 33–53 min

Use the low amount for the prohibited-beneficiary test and a permitted beneficiary for the amount test. Conflating both would hide which rule stopped the request. Interpret the actual MCP decision rather than only the outer transport status.

Sources: [workshop-4-story.md](../../../docs/workshops/workshop-4-story.md), [worksheet.md](../../../workshops/w4/worksheet.md), [answer-key.md](../../../workshops/w4/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md), [runbook.md](../../../workshops/w4/runbook.md), [incident.py](../../../src/demo/incident.py), [server.py](../../../src/adapter/server.py), [apisix-w4.yaml](../../../docker/apisix/apisix-w4.yaml)

## 23. Inspect the actual MCP payment payload

**Timing:** 33–53 min

This is the excessive-amount scenario: 900,000,000 paise equals ₹90 lakh, to the intended permitted vendor. In the server export, events[].arguments stores the JSON request body, not events[].request. Inspect the response reason AMOUNT_EXCEEDS_TRANSFER_CEILING and measured zero effect. The original incident ticket is background context; it does not mean this protected request executed the isolated replay.

```bash
{"jsonrpc":"2.0","id":"<run-id>",
 "method":"tools/call",
 "params":{"name":"create_payment","arguments":{
   "account_id":"acc-101",
   "beneficiary":"vendor-alpha",
   "amount":900000000,"currency":"INR"
 }}}
```

Sources: [workshop-4-story.md](../../../docs/workshops/workshop-4-story.md), [worksheet.md](../../../workshops/w4/worksheet.md), [answer-key.md](../../../workshops/w4/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md), [runbook.md](../../../workshops/w4/runbook.md), [incident.py](../../../src/demo/incident.py), [server.py](../../../src/adapter/server.py), [apisix-w4.yaml](../../../docker/apisix/apisix-w4.yaml)

## 24. Exercise: repair the prepared local policy

**Timing:** 33–53 min

Run prohibited beneficiary, excessive amount and permitted payment before the edit. Remove only vendor-alpha; retain attacker block and transfer ceiling. Repeating the success scenario creates payments; reconcile uncertain responses under the original run ID.

```bash
cp workshops/w4/checkpoints/initial/policy.rego \
  spikes/spike3_opa/policy.rego
docker compose restart opa

# Remove only vendor-alpha from the prepared prohibited list.
# Keep fraud-account-66 blocked, restart OPA, then retest.
```

Sources: [workshop-4-story.md](../../../docs/workshops/workshop-4-story.md), [worksheet.md](../../../workshops/w4/worksheet.md), [answer-key.md](../../../workshops/w4/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md), [runbook.md](../../../workshops/w4/runbook.md), [incident.py](../../../src/demo/incident.py), [server.py](../../../src/adapter/server.py), [apisix-w4.yaml](../../../docker/apisix/apisix-w4.yaml)

## 25. Retest the repair against both attack and business paths

**Timing:** 33–53 min

Collect actual denied and allowed responses, balance deltas and payment count. This is a running-policy change, not a UI toggle. If stalled, allow two minutes before supplying the completed checkpoint.

```bash
# Completed checkpoint if a pair needs recovery:
cp workshops/w4/checkpoints/completed/policy.rego \
  spikes/spike3_opa/policy.rego
docker compose restart opa
```

Sources: [workshop-4-story.md](../../../docs/workshops/workshop-4-story.md), [worksheet.md](../../../workshops/w4/worksheet.md), [answer-key.md](../../../workshops/w4/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md), [runbook.md](../../../workshops/w4/runbook.md), [incident.py](../../../src/demo/incident.py), [server.py](../../../src/adapter/server.py), [apisix-w4.yaml](../../../docker/apisix/apisix-w4.yaml)

## 26. Gate 3: the attacker changes routes

**Timing:** 53–60 min

Ask what would happen if the API accepted every validly signed token regardless of audience. Then inspect the actual responses. A Gate 2 denial does not prove the direct API path is protected; test it independently. The wrong-audience scenario actually performs GET /api/v1/accounts/acc-101 with an MCP-audience token; the insufficient-scope scenario attempts POST /api/v1/payments. Do not describe the first as a payment attempt.

Sources: [workshop-4-story.md](../../../docs/workshops/workshop-4-story.md), [worksheet.md](../../../workshops/w4/worksheet.md), [answer-key.md](../../../workshops/w4/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md), [runbook.md](../../../workshops/w4/runbook.md), [incident.py](../../../src/demo/incident.py), [server.py](../../../src/adapter/server.py), [apisix-w4.yaml](../../../docker/apisix/apisix-w4.yaml)

## 27. Break / checkpoint recovery

**Timing:** 60–67 min

Pause for the scheduled break. Restore completed policy/identity files where needed, restart OPA and refresh readiness. Export interrupted evidence first. Do not reset protected ledger state to hide an uncertain payment result.

Sources: [workshop-4-story.md](../../../docs/workshops/workshop-4-story.md), [worksheet.md](../../../workshops/w4/worksheet.md), [answer-key.md](../../../workshops/w4/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md), [runbook.md](../../../workshops/w4/runbook.md), [incident.py](../../../src/demo/incident.py), [server.py](../../../src/adapter/server.py), [apisix-w4.yaml](../../../docker/apisix/apisix-w4.yaml)

## 28. Identity must narrow at the next boundary

**Timing:** 67–85 min

The lab demonstrates a constrained token-exchange pattern. Show sanitized claims rather than bearer credentials. Managed identity, key rotation and broader protocol conformance remain production work.

Sources: [workshop-4-story.md](../../../docs/workshops/workshop-4-story.md), [worksheet.md](../../../workshops/w4/worksheet.md), [answer-key.md](../../../workshops/w4/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md), [runbook.md](../../../workshops/w4/runbook.md), [incident.py](../../../src/demo/incident.py), [server.py](../../../src/adapter/server.py), [apisix-w4.yaml](../../../docker/apisix/apisix-w4.yaml)

## 29. Exercise: request only an entitled scope

**Timing:** 67–85 min

The full edit path is workshops/w4/checkpoints/initial/identity.json. Change only requested_scope. The CLI writes sanitized timestamped evidence under workshops/w4/evidence. It mints lab credentials locally and does not load .env automatically: export matching JWT settings if the stack overrides defaults, using the answer-key instructions. Before each new session, restore initial/identity.json requested_scope to api:payments:write if a previous exercise left the corrected read scope. Export matching JWT settings from the running API using the runbook when customized.

```bash
.venv/bin/python workshops/w4/exercise_exchange.py initial

# In checkpoints/initial/identity.json, change requested_scope
# from api:payments:write to api:accounts:read, then rerun.

.venv/bin/python workshops/w4/exercise_exchange.py completed
```

Sources: [workshop-4-story.md](../../../docs/workshops/workshop-4-story.md), [worksheet.md](../../../workshops/w4/worksheet.md), [answer-key.md](../../../workshops/w4/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md), [runbook.md](../../../workshops/w4/runbook.md), [incident.py](../../../src/demo/incident.py), [server.py](../../../src/adapter/server.py), [apisix-w4.yaml](../../../docker/apisix/apisix-w4.yaml)

## 30. Explain the identity evidence

**Timing:** 67–85 min

Have each pair explain one denied and one permitted identity request. View selection cannot grant authority. A successful token exchange does not by itself prove a subsequent payment is authorized.

Sources: [workshop-4-story.md](../../../docs/workshops/workshop-4-story.md), [worksheet.md](../../../workshops/w4/worksheet.md), [answer-key.md](../../../workshops/w4/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md), [runbook.md](../../../workshops/w4/runbook.md), [incident.py](../../../src/demo/incident.py), [server.py](../../../src/adapter/server.py), [apisix-w4.yaml](../../../docker/apisix/apisix-w4.yaml)

## 31. Approval attaches to one exact transaction

**Timing:** 85–103 min

Proposals expire after ten minutes. Read the actual proposal and task identifiers. Independent review should approve exact server-owned arguments; changed arguments must fail. W4's password-backed lab reviewer flow is not a claim of production IAM.

Sources: [workshop-4-story.md](../../../docs/workshops/workshop-4-story.md), [worksheet.md](../../../workshops/w4/worksheet.md), [answer-key.md](../../../workshops/w4/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md), [runbook.md](../../../workshops/w4/runbook.md), [incident.py](../../../src/demo/incident.py), [server.py](../../../src/adapter/server.py), [apisix-w4.yaml](../../../docker/apisix/apisix-w4.yaml)

## 32. Retrieve the local reviewer password

**Timing:** 85–103 min

Prepare a private/incognito window or separate profile before creating the proposal. Sign in with maya@flobank.demo / flo-demo, select Independent reviewer, enter the running API password and click Open reviewer session. Another tab shares requester cookies. The password differs from the audience code. If absent, configure it in .env and recreate the API before creating proposals; a restart does not load changed environment. Proposals expire after ten minutes. See workshops/w4/runbook.md section 2.

```bash
docker compose exec -T api printenv W4_REVIEWER_PASSWORD
```

Sources: [workshop-4-story.md](../../../docs/workshops/workshop-4-story.md), [worksheet.md](../../../workshops/w4/worksheet.md), [answer-key.md](../../../workshops/w4/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md), [runbook.md](../../../workshops/w4/runbook.md), [incident.py](../../../src/demo/incident.py), [server.py](../../../src/adapter/server.py), [apisix-w4.yaml](../../../docker/apisix/apisix-w4.yaml)

## 33. Use an independent reviewer session

**Timing:** 85–103 min

The facilitator configures and privately provides the reviewer password to the cofacilitator. The requester cannot approve its own proposal even with a reviewer cookie in its browser. Never paste the password into slides or evidence. Inspect the current proposal immediately before approval.

Sources: [workshop-4-story.md](../../../docs/workshops/workshop-4-story.md), [worksheet.md](../../../workshops/w4/worksheet.md), [answer-key.md](../../../workshops/w4/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md), [runbook.md](../../../workshops/w4/runbook.md), [incident.py](../../../src/demo/incident.py), [server.py](../../../src/adapter/server.py), [apisix-w4.yaml](../../../docker/apisix/apisix-w4.yaml)

## 34. Attempt self approval and transaction tampering

**Timing:** 85–103 min

The console approval path executes the server-owned exact arguments, tests tampering and retry, and binds the payment to the task. Use the actual evidence order shown by the run; these rows describe the controls, not a manual command sequence.

Sources: [workshop-4-story.md](../../../docs/workshops/workshop-4-story.md), [worksheet.md](../../../workshops/w4/worksheet.md), [answer-key.md](../../../workshops/w4/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md), [runbook.md](../../../workshops/w4/runbook.md), [incident.py](../../../src/demo/incident.py), [server.py](../../../src/adapter/server.py), [apisix-w4.yaml](../../../docker/apisix/apisix-w4.yaml)

## 35. One effect survives a retry

**Timing:** 85–103 min

Use Reconcile uncertain result after a lost response or process restart. Proposal status and keyed payments determine the result. Never invent a fresh run or financial key to retry an uncertain payment. If the API cannot be read, keep the result unresolved.

Sources: [workshop-4-story.md](../../../docs/workshops/workshop-4-story.md), [worksheet.md](../../../workshops/w4/worksheet.md), [answer-key.md](../../../workshops/w4/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md), [runbook.md](../../../workshops/w4/runbook.md), [incident.py](../../../src/demo/incident.py), [server.py](../../../src/adapter/server.py), [apisix-w4.yaml](../../../docker/apisix/apisix-w4.yaml)

## 36. A second agent creates a second boundary

**Timing:** 103–119 min

The repository implements selected A2A controls; this is not a demonstration of complete A2A protocol conformance. Have pairs identify which principal may perform each operation before running the scenarios. Inspect the same completed delegation run; do not create another ₹1,500 settlement for this chapter. Foreign access and unauthorized completion tests occur before review; mismatch binding occurs after settlement.

Sources: [workshop-4-story.md](../../../docs/workshops/workshop-4-story.md), [worksheet.md](../../../workshops/w4/worksheet.md), [answer-key.md](../../../workshops/w4/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md), [runbook.md](../../../workshops/w4/runbook.md), [incident.py](../../../src/demo/incident.py), [server.py](../../../src/adapter/server.py), [apisix-w4.yaml](../../../docker/apisix/apisix-w4.yaml)

## 37. Test access to the delegated task

**Timing:** 103–119 min

Only task owner/designated executor can access the relevant task. Binding checks source, amount, currency, destination and optional proposal. Explain which principal made each tested request using sanitized evidence.

Sources: [workshop-4-story.md](../../../docs/workshops/workshop-4-story.md), [worksheet.md](../../../workshops/w4/worksheet.md), [answer-key.md](../../../workshops/w4/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md), [runbook.md](../../../workshops/w4/runbook.md), [incident.py](../../../src/demo/incident.py), [server.py](../../../src/adapter/server.py), [apisix-w4.yaml](../../../docker/apisix/apisix-w4.yaml)

## 38. Bind completion to a business fact

**Timing:** 103–119 min

Inspect task, proposal and payment records side by side. The final legitimate path is delegate → propose → independently approve → execute exact arguments → bind the actual payment to the task.

Sources: [workshop-4-story.md](../../../docs/workshops/workshop-4-story.md), [worksheet.md](../../../workshops/w4/worksheet.md), [answer-key.md](../../../workshops/w4/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md), [runbook.md](../../../workshops/w4/runbook.md), [incident.py](../../../src/demo/incident.py), [server.py](../../../src/adapter/server.py), [apisix-w4.yaml](../../../docker/apisix/apisix-w4.yaml)

## 39. Prove the repaired system in both directions

**Timing:** 119–130 min

Run the attack suite and legitimate path on prepared state, or inspect the collected chapter evidence if time is short. The table lists expected outcomes, not fresh measurements. Do not conflate the separate ₹250 policy exercise with the ₹1,500 delegation payment.

Sources: [workshop-4-story.md](../../../docs/workshops/workshop-4-story.md), [worksheet.md](../../../workshops/w4/worksheet.md), [answer-key.md](../../../workshops/w4/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md), [runbook.md](../../../workshops/w4/runbook.md), [incident.py](../../../src/demo/incident.py), [server.py](../../../src/adapter/server.py), [apisix-w4.yaml](../../../docker/apisix/apisix-w4.yaml)

## 40. Reconstruct the incident from familiar records

**Timing:** 119–130 min

Evidence sheet: workshops/w4/incident-evidence.md. Save sanitized caller, audience/scopes, arguments and boundary responses as well as business IDs. Null ledger observations are unresolved, not zero. A generated trace ID alone is not collector evidence. Aggregate deltas need an isolated run without concurrent external mutations.

Sources: [workshop-4-story.md](../../../docs/workshops/workshop-4-story.md), [worksheet.md](../../../workshops/w4/worksheet.md), [answer-key.md](../../../workshops/w4/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md), [runbook.md](../../../workshops/w4/runbook.md), [incident.py](../../../src/demo/incident.py), [server.py](../../../src/adapter/server.py), [apisix-w4.yaml](../../../docker/apisix/apisix-w4.yaml)

## 41. Incident review: what did your first vote miss?

**Timing:** 130–135 min

Revisit initial votes. Identify work for key rotation, distributed budget state, availability, audit retention, trace completeness and protocol conformance. Technical rehearsal evidence does not establish a completed 135-minute human delivery rehearsal or production readiness.

Sources: [workshop-4-story.md](../../../docs/workshops/workshop-4-story.md), [worksheet.md](../../../workshops/w4/worksheet.md), [answer-key.md](../../../workshops/w4/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md), [runbook.md](../../../workshops/w4/runbook.md), [incident.py](../../../src/demo/incident.py), [server.py](../../../src/adapter/server.py), [apisix-w4.yaml](../../../docker/apisix/apisix-w4.yaml)

## 42. Restore useful work under explicit authority

**Timing:** 130–135 min

Close the four-workshop arc. Ask participants to name one control they would add to an existing agent integration and the evidence they would require to show it works.

Sources: [workshop-4-story.md](../../../docs/workshops/workshop-4-story.md), [worksheet.md](../../../workshops/w4/worksheet.md), [answer-key.md](../../../workshops/w4/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md), [runbook.md](../../../workshops/w4/runbook.md), [incident.py](../../../src/demo/incident.py), [server.py](../../../src/adapter/server.py), [apisix-w4.yaml](../../../docker/apisix/apisix-w4.yaml)

## 43. Presenter preparation & source guide

**Timing:** Reference / outside timed delivery

Do setup outside the timed workshop. See workshops/w4/answer-key.md for W4_REVIEWER_PASSWORD, W4_ENABLE_VULNERABLE, W4_SANDBOX_KEY, observation-only hosting and presenter sandbox startup. Do not put actual values in this deck. Technical runner: .venv/bin/python workshops/w4/rehearsal_w4.py --vulnerable --outage, only on the appropriately prepared stack. It creates fictional records and does not reset data. Human timing record: workshops/w4/delivery-rehearsal.md. Downloads/builds and profile switching happen before attendees arrive. Use workshops/w4/runbook.md for persisted setup, password retrieval and recovery. The --live runner repeats the full suite with an additional live comparison; use the standalone console scenario for only one bounded review.

Sources: [workshop-4-story.md](../../../docs/workshops/workshop-4-story.md), [worksheet.md](../../../workshops/w4/worksheet.md), [answer-key.md](../../../workshops/w4/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md), [runbook.md](../../../workshops/w4/runbook.md), [incident.py](../../../src/demo/incident.py), [server.py](../../../src/adapter/server.py), [apisix-w4.yaml](../../../docker/apisix/apisix-w4.yaml)
