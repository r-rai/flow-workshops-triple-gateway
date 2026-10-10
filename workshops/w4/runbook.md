# Workshop 4 facilitator runbook

Use this runbook to prepare and conduct **The Day the Agent Broke the Bank**.
The session lasts **135 minutes, including a seven-minute break**. For each
exercise, explain the request, collect a prediction, run it, inspect the actual
response and business effect, then state the learning. Expected outcomes below
are targets, not evidence that your current run passed.

Companion material: [participant worksheet](worksheet.md),
[answer key](answer-key.md), [incident evidence sheet](incident-evidence.md),
[presenter story](../../docs/workshops/workshop-4-story.md).

## 1. Prepare the local lab before the session

Run commands from the repository root in Bash on Linux/WSL. Prepare one local
instance per pair. Complete the [infrastructure prerequisites and Python setup](../../docs/workshops/participant-infra-guide.md#2-initial-environment-setup-one-time-preparation)
first. Use replay fixtures for deterministic exercises; these require no model
provider key. macOS users can use Python clients and direct Docker Compose
commands; the Bash launcher expects Linux utilities.

### First-time presenter configuration

Create `.env` only if it does not already exist:

```bash
test -f .env || cp .env.example .env
```

For a new local presenter configuration, generate separate reviewer and sandbox
secrets. This block replaces those W4 settings in `.env`, preserving other
settings. Do not run it to retrieve an existing password or during a pending
review; use the retrieval command in section 2 instead.

```bash
export W4_REVIEWER_PASSWORD="$(python3 -c 'import secrets; print(secrets.token_urlsafe(24))')"
export W4_SANDBOX_KEY="$(python3 -c 'import secrets; print(secrets.token_urlsafe(24))')"
export W4_ENABLE_VULNERABLE=true
export W4_OBSERVATION_ONLY=false

python3 - <<'PY'
import os
import re
from pathlib import Path

path = Path('.env')
text = path.read_text()
for name in ('W4_REVIEWER_PASSWORD', 'W4_SANDBOX_KEY',
             'W4_ENABLE_VULNERABLE', 'W4_OBSERVATION_ONLY'):
    line = f'{name}={os.environ[name]}'
    pattern = rf'^{name}=.*$'
    if re.search(pattern, text, flags=re.MULTILINE):
        text = re.sub(pattern, lambda _: line, text, flags=re.MULTILINE)
    else:
        text = text.rstrip('\n') + '\n' + line + '\n'
path.write_text(text)
print('Saved W4 configuration to local .env; secret values were not printed.')
PY
```

Persistence matters: later API recreation reads Compose settings from the shell
and `.env`. Shell exports override `.env`; keep them consistent. Keep `.env`
local and exclude its values from slides and evidence.

### Build and start

Before changing profiles, download evidence and resolve pending/uncertain runs.
The switch command stops the previous workshop containers and preserves named
volumes; it does not reset the protected ledger.

```bash
./scripts/workshop pull w4
docker compose --profile w4 --profile w4-presenter build incident-sandbox
./scripts/workshop switch w4
docker compose --profile w4 --profile w4-presenter up -d incident-sandbox
./scripts/workshop status
./scripts/workshop verify w4
```

Expected: W4 is active, verification passes, and `incident-sandbox` is running.
Plain W4 startup does not enable the isolated replay. The sandbox has a separate
disposable ledger, no protected volumes, no banking/provider keys, and no public
port. Use one API worker per local instance.

Open `http://localhost:9080/workshop-4?view=presenter`, sign in with
`maya@flobank.demo` / `flo-demo`, and check that API, inference, and tools are
reachable. Choose **Presenter**, then **Start delivery clock** when timed delivery
begins. Chapter selection changes presentation, not enforcement.

### Update an existing local lab

Use existing configured secrets; do not generate new ones for a UI update.

```bash
git pull origin main
docker compose --profile w4 up -d --build --no-deps api
```

Hard-refresh the browser with **Ctrl+Shift+R**. Rebuilding the API serves the
checkout's new UI assets while preserving its data volume. Confirm readiness and
retrieve the running reviewer password again if configuration is uncertain.

## 2. Retrieve the reviewer password and open a separate session

From the local repository root, display the password actually configured in the
running API:

```bash
docker compose exec -T api printenv W4_REVIEWER_PASSWORD
```

Run this in a private terminal and provide the value privately to the
cofacilitator. This is the reviewer password, not the `flo-demo` login password
and not the public observer access code. If it is blank or absent, configure
`W4_REVIEWER_PASSWORD` in local `.env` before creating a proposal, then recreate
only the API:

```bash
docker compose --profile w4 up -d --no-deps --force-recreate api
```

An environment change requires recreation; `docker compose restart api` alone
does not load it. An old shell export can override the edited `.env` value.

1. Open a private/incognito window or separate browser profile. Another tab in
   the requester session shares cookies and is insufficient.
2. Open `http://localhost:9080/workshop-4?view=reviewer`.
3. Sign in with `maya@flobank.demo` / `flo-demo`.
4. Choose **Independent reviewer**, enter the retrieved password, and click
   **Open reviewer session**.
5. Expect **Independent reviewer session opened**. Selecting the view alone
   grants no authority. The requester session still cannot approve itself.

## 3. Know where to inspect a request

Select a scenario, predict its result, then click **Run scenario ↗**. Selecting
the dropdown option alone does not execute it. One local instance permits one
active demonstration at a time.

- **Current run timeline** lists the selected run's recorded events. The pill
  identifies its scenario, inference mode, and run ID.
- **Original incident context: untrusted ticket** describes the opening story.
  It does not establish that the current scenario executed the ₹90 lakh handoff.
- **Boundary map** shows service status and interpreted allow/deny outcome.
- **Identity inspector** shows sanitized callers, audiences, scopes, and roles.
- **Evidence drawer: arguments, responses & ledger** contains top-level
  `arguments` where populated. Within `events`, use `label`, `boundary`,
  `method`, `path`, `identity`, **`arguments`** (the request body), and `response`.
  There is no `events[].request` field. Form-encoded exchange bodies are not
  captured in that JSON-arguments field; inspect exchange identities/responses
  and the CLI evidence's `config` instead.
- **Download server evidence ↓** saves the selected run for later inspection.

For a Gate 2 `Tool policy` event, `arguments.params.arguments` contains the
payment fields inside the JSON-RPC `tools/call` body. HTTP **200 denied** means
the MCP transport succeeded but the tool result rejected the operation.
Null ledger observations are **unresolved**, not zero. A trace ID requires
collector evidence before it establishes an observed distributed trace.

## 4. Opening and isolated replay — 0–20 minutes

**Say:** “The credentials were valid. The request passed schema validation. The
fictional bank still lost ₹90 lakh. What did we authorize?” Collect predictions:
identity, model, tool policy, or approval. Withhold the ticket until chapter two.

Select **8–20 · Follow the money**, then **Replay the isolated ₹90 lakh incident**
and **Run scenario ↗**. This executes a fixed recorded proposal in the sandbox;
it is not a live model compromise.

Expected: `Recorded vulnerable settlement` returns **200 allowed**, the run
completes, and the isolated ledger loses **900,000,000 paise** with one payment.
Protected observations remain **₹0 / 0 payments**. Ask where ticket content
became asserted authority across NegotiatorBot → PaymentsAgent.

**Learning:** authentication and request shape do not authorize the beneficiary,
amount, approval, or delegation. The protected and isolated ledgers are separate.

## 5. Gate 1: inference budget — 20–33 minutes

Select **20–33 · Contain the reasoning loop**, then **Gate 1: exceed inference
headroom** and run it. Predict rejection before model dispatch.

The first request, `GET /ai/budget`, returns **200** with used tokens, limit, and
remaining headroom. The scenario then constructs a large prompt from that
headroom and requests 512 output tokens. The adapter checks:

```text
accumulated usage + estimated prompt + reserved output > budget limit
```

Expected: `Budget-exhausting inference` returns **429 denied**, with no provider
dispatch and no payment. The estimate uses roughly one token per four serialized
characters; it is not an exact model tokenizer calculation.

If the error says `Inference budget exceeded (140/100000 tokens)`, 140 is existing
usage, not the incoming request's size. Remaining headroom is 99,860 tokens; the
deliberately oversized prompt plus output reservation exceeds it. The message
omits those incoming estimates. Do not say 140 itself exceeded 100,000.

**Learning:** Gate 1 limits inference consumption. It does not authorize or block
a separate direct tool/API request. Test those boundaries independently. Optional
live comparison makes one bounded call with no tool execution; report the actual
answer, refusal, or `live_failed` result.

## 6. Gate 2: isolate rules, then repair policy — 33–53 minutes

Select **33–53 · Control the capability**. First test the rules using the completed
policy. Restore it before the baseline tests if an earlier exercise left the
initial policy active:

```bash
cp workshops/w4/checkpoints/completed/policy.rego spikes/spike3_opa/policy.rego
docker compose restart opa
```

Prohibited beneficiary uses **₹250 to `fraud-account-66`**; excessive amount
uses **₹90 lakh to `vendor-alpha`**. Expected reasons are
`PROHIBITED_BENEFICIARY` and `AMOUNT_EXCEEDS_TRANSFER_CEILING`, respectively.
Both should produce **₹0 / 0 payments**. The completed policy's transfer ceiling
is 1,000,000 paise (₹10,000). Inspect actual reasons, not just “denied.”

For the pair repair exercise, load the deliberately restrictive checkpoint:

```bash
cp workshops/w4/checkpoints/initial/policy.rego spikes/spike3_opa/policy.rego
docker compose restart opa
```

Run **prohibited beneficiary**, **excessive amount**, and **permitted ₹250 payment**.
The initial policy also prohibits `vendor-alpha`; the legitimate request should
therefore fail. An excessive-amount request to that blocked vendor may report the
beneficiary reason, so it does not yet isolate the ceiling check.

Remove only `vendor-alpha` from the prohibited list in
`spikes/spike3_opa/policy.rego`; keep `fraud-account-66` blocked and retain the
ceiling. Restart OPA and retest. Completed recovery checkpoint:

```bash
cp workshops/w4/checkpoints/completed/policy.rego spikes/spike3_opa/policy.rego
docker compose restart opa
```

Expected after repair: both attack rules remain enforced, and **Gate 2: permitted
₹250 payment** completes with **−₹250 / 1 payment**. Run that successful scenario
once; fresh successful runs create further payments.

**Learning:** a repair must preserve protective rules and restore legitimate
business work. The policy service enforces the file; a UI selection is not a fix.

Optional facilitator outage test, outside the normal pair repair: stop OPA,
run **Gate 2: test a stopped policy service**, inspect fail-closed timeout/error
and zero payment effect, then restore OPA immediately—even if the test fails.

```bash
docker compose stop opa
# Run the stopped-policy-service scenario in the console and inspect evidence.
docker compose start opa
./scripts/workshop verify w4
```

## 7. Gate 3: direct API identity — 53–60 minutes

Select **53–60 · The attacker changes routes**. Run separately:

| Scenario | Actual test | Expected result | Learning |
|---|---|---|---|
| MCP token at the API | MCP-audience token calls `GET /api/v1/accounts/acc-101` | 401; zero payment effect | A valid signature does not make a token suitable for every service |
| Read-only payment attempt | API-audience read token calls `POST /api/v1/payments` | 403; zero payment effect | Correct audience does not grant payment-write scope |

Inspect caller audience/scopes and each response. The first test is an account
read, not an attempted payment; its zero payment count alone proves no payment
authorization property. The second explicitly tests a payment write.

## 8. Break and checkpoint recovery — 60–67 minutes

Take seven minutes. Give stalled pairs two minutes before supplying completed
checkpoints. Restart OPA and refresh readiness. Export interrupted evidence and
reconcile the original financial run before continuing. Do not reset protected
data to conceal an uncertain settlement.

## 9. Identity exchange exercise — 67–85 minutes

Select **67–85 · Restrict the identity**. The CLI mints a lab token locally and
does not automatically load `.env`. If the stack uses customized JWT settings,
copy its running settings into this shell without printing them:

```bash
for w4_setting in JWT_SECRET_KEY JWT_ALGORITHM JWT_ISSUER API_AUDIENCE MCP_AUDIENCE; do
  export "$w4_setting=$(docker compose exec -T api printenv "$w4_setting")"
done
```

Inspect checkpoint audiences against your configured audiences; adapt those
audience fields only if your lab intentionally uses custom values. The standard
exercise changes only `requested_scope`. Before the first run of each session,
inspect `workshops/w4/checkpoints/initial/identity.json`: if a previous exercise
left `requested_scope` as `api:accounts:read`, restore it to
`api:payments:write` so the initial request tests the intended denial.

```bash
.venv/bin/python workshops/w4/exercise_exchange.py initial
```

Expected: a viewer requesting `api:payments:write` receives **403**. Inspect the
saved timestamped file under `workshops/w4/evidence/`. In
`workshops/w4/checkpoints/initial/identity.json`, change `requested_scope` to
`api:accounts:read`, then rerun the same `initial` command. Expected: **200**, API
audience and read scope in sanitized claims. Compare the supplied reference:

```bash
.venv/bin/python workshops/w4/exercise_exchange.py completed
```

In the console, compare **unauthorized scope exchange** and **permitted scope
exchange** independently. A signing/audience configuration failure is not proof
of the intended entitlement denial.

**Learning:** requesting authority does not create entitlement. Successful token
exchange grants a constrained credential, not automatic payment approval.

## 10. Independent approval and exact execution — 85–103 minutes

Prepare the separate reviewer session using section 2 **before** creating the
proposal. Select **85–103 · Approval attaches to a transaction**.

1. In the requester window, run **A2A: independently approve ₹1,500 settlement**.
   If a pending run already exists, use it instead of creating another.
2. Inspect `Self approval`: expected **403**. Expected run state is **awaiting
   review**, with **₹0 / 0 payments**. Foreign-task access and unauthorized
   completion checks also execute during this preparation.
3. In the reviewer window, **Refresh evidence** and select the matching
   **Server-owned run**. Match run ID, proposal ID, and task ID.
4. Read source `acc-101`, beneficiary `vendor-alpha`, currency `INR`, and amount
   **150,000 paise = ₹1,500**. Check expiry; proposals last ten minutes.
5. Click **Approve exact proposal** once in the reviewer session. The requester
   cannot approve itself, even if its browser has a reviewer cookie.
6. Inspect the resulting events in actual order. Independent approval succeeds;
   `Changed arguments` is rejected with **400**; `Execute exact payment`
   succeeds; `Idempotent retry` returns the same financial effect. The console
   orchestrates these tests; do not manually create replacement payments.
7. Expect final **completed**, **−₹1,500 / 1 payment**, and matching payment ID
   in the payment record and task output. Refresh both sessions to compare.

**Learning:** independent review authorizes one exact transaction; argument
binding rejects changes and stable idempotency preserves one payment on retry.

## 11. A2A task authority and business binding — 103–119 minutes

Select **103–119 · A second trust boundary** and inspect the **same delegation
run**. Do not create another ₹1,500 settlement for this chapter.

| Event | Expected | Explanation |
|---|---|---|
| Foreign task access | 403 | Caller is neither owner nor designated executor |
| Unauthorized completion | 403 | Completion requires the designated executor |
| Mismatched payment binding | 400 | Actual payment does not meet the other task's requirements |
| Bind actual settlement | 200 | Matching settled payment can complete the authorized task |

Read event identities and task IDs. Compare task, proposal, and payment source,
amount, currency, destination, and proposal reference where present. Task output
payment ID must equal the actual settled payment ID. Missing checks remain
unverified; do not infer that an absent event passed.

**Learning:** task ownership, execution, approval, and completion are distinct
authorities. A task completes against a matching business fact, not an agent's
unsupported claim. This lab implements selected A2A controls, not full protocol
conformance.

## 12. Reconstruct evidence and close — 119–135 minutes

Select **119–130 · Prove the repair**. Explain one denial using caller, request
arguments, boundary response/reason, and observed ledger effect. Reconstruct one
legitimate settlement using run → task → proposal → independent approval →
payment → matching task output. Keep the separate ₹250 policy payment out of
the ₹1,500 run's reconciliation.

Expand **Trace references**, click **Check collector evidence**, and inspect
observed services or an explicit **incomplete** status. Download server evidence
for the denial and legitimate settlement. If time permits a fresh technical
suite, account for the additional fictional records it creates; otherwise use
the chapter evidence already collected.

At **130–135 · Incident review**, revisit opening predictions and assign owners
for inference budgets, tool policy, identity/exchange, approval, and audit
operations. Identify production work for managed identities, key rotation,
distributed budget state, availability, audit retention, trace completeness, and
protocol conformance. Complete [delivery-rehearsal.md](delivery-rehearsal.md) with
actual timing and readability; technical results do not certify human delivery.

## 13. Recovery, rehearsal, and shutdown

For an uncertain financial result, select the original run and click
**Reconcile uncertain result**. Proposal status and keyed payment records
determine recovery. Do not retry with a new run or financial key. If API records
cannot be read, keep the result unresolved.

Before technical rehearsal, restore the completed policy and retrieve the
running reviewer password into the rehearsal shell without printing it:

For custom JWT configuration in a new shell, first use section 9's export loop
to match the running API's signing and audience settings.

```bash
export W4_REVIEWER_PASSWORD="$(docker compose exec -T api printenv W4_REVIEWER_PASSWORD)"
cp workshops/w4/checkpoints/completed/policy.rego spikes/spike3_opa/policy.rego
docker compose restart opa
.venv/bin/python workshops/w4/rehearsal_w4.py --vulnerable --outage
```

This creates fictional proposals/payments, restores OPA after the outage test,
and writes timestamped evidence. It does not reset data or measure 135 minutes
of human delivery. To run the full technical suite again with one additional
bounded live comparison:

```bash
.venv/bin/python workshops/w4/rehearsal_w4.py --live
```

`--live` adds the model comparison to the suite; it does not skip the other
scenarios or their financial effects. To make only the bounded comparison, use
**Optional: one bounded live case review** in the console instead.

Download evidence and resolve pending work before stopping the local lab:

```bash
./scripts/workshop stop
```

## 14. QR observers and hosted updates

QR participants use the separate observation page and event access code. They
inspect curated recorded runs; they do not execute scenarios, approve proposals,
or synchronize live with the local presenter's ledger. They do not need the
reviewer password. Use the [mobile companion](mobile-companion.md).

The observer page also labels **Current run timeline** and **Original incident
context**. A repository push or local API rebuild does not update hosted
observers. The hosting operator must rebuild the public image and recreate only
the `incident-room` service in the `flo-w4-public` project, following the
[deployment report](../../docs/workshops/w4-public-deployment-report.md) and
[deployment plan](../../docs/workshops/w4-public-deployment-plan.md). Public
Compose has no build definition: `up --build` alone does not rebuild its image.
Check the event access cutoff for the intended session before deploying; its
configured date is event-specific. Refresh the observer page after deployment.
Do not run the local workshop profile-switch commands against the shared host.
