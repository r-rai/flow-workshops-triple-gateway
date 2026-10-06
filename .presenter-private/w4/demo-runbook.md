# Workshop 4 presenter demo runbook

**The Day the Agent Broke the Bank: Implementing Triple-Gate Architecture & A2A Security for Autonomous AI Workloads** · 135 minutes including a seven-minute break · profile `w4`.

Run commands from the repository root in Bash with the workshop Python environment installed. Present from [Incident Room](http://localhost:9080/workshop-4). Keep the [worksheet](../../workshops/w4/worksheet.md), [answer key](../../workshops/w4/answer-key.md), [incident evidence sheet](../../workshops/w4/incident-evidence.md) and [human delivery record](../../workshops/w4/delivery-rehearsal.md) available.

## Before the room opens

Use one local instance per pair. A shared observation server is for viewing sanitized evidence; it cannot serve independent financial labs. Profile switching stops the workshop stack. Reset only disposable fictional bank data after exporting any evidence you need; bank reset does not clear persisted Incident Room runs or Temporal history. Preserve unresolved runs until reconciled.

Prepare a requester browser and a separate private window/browser profile for the independent reviewer. Use `maya@flobank.demo` / `flo-demo` to sign in to each. Selecting a view alone does not grant reviewer authority.

In a fresh local lab, generate distinct secrets without printing them. Retain this shell for startup and rehearsal; a new password in another shell will not match the running API.

```bash
export W4_REVIEWER_PASSWORD="$(python3 -c 'import secrets; print(secrets.token_urlsafe(24))')"
export W4_SANDBOX_KEY="$(python3 -c 'import secrets; print(secrets.token_urlsafe(24))')"
export W4_ENABLE_VULNERABLE=true
export W4_OBSERVATION_ONLY=false
./scripts/workshop preflight
./scripts/workshop pull w4
docker compose --profile w4 --profile w4-presenter build incident-sandbox
./scripts/workshop switch w4
docker compose --profile w4 --profile w4-presenter up -d incident-sandbox
./scripts/workshop status
./scripts/workshop verify w4
```

Pass the reviewer password privately to the cofacilitator. Keep secrets out of slides, recordings and exports. On shared observation hosting use `W4_OBSERVATION_ONLY=true`, `W4_ENABLE_VULNERABLE=false`, and skip the sandbox. Starting ordinary W4 alone does not enable the opening isolated incident replay.

Use the completed active policy for baseline rehearsal, after preserving any local policy changes:

```bash
mkdir -p .presenter-private/w4/live-evidence
cp spikes/spike3_opa/policy.rego .presenter-private/w4/live-evidence/policy-before.rego
cp workshops/w4/checkpoints/completed/policy.rego spikes/spike3_opa/policy.rego
docker compose restart opa
.venv/bin/python workshops/w4/rehearsal_w4.py --vulnerable --outage
```

This creates fictional payments/proposals and saves timestamped `workshops/w4/evidence/incident-*.json`; it does not reset data. OPA is stopped and restored in `finally`. Inspect the evidence before using it as fallback. Optional `--live` makes one bounded hosted-model comparison; it has no payment capability. Do not turn a recorded response into a live claim.

After rehearsal, export all needed evidence and reconcile uncertain runs. If intended, reset the bank before delivery:

```bash
./scripts/workshop reset w4 --yes
```

Complete verification before the final reset because verification can create payments. Rehearse browser operation, reviewer login, refresh/reconciliation and downloads before presentation. Leave the completed policy active until the pair-repair chapter.

Confirm readiness, projector readability, OPA health and separate reviewer sessions. Inspect `docker stats --no-stream` and container restart/OOM state against the 6 GB workshop budget. The recorded Linux snapshot is not a measured long-session peak. Keep unrelated host services running.

## Timed chapter map

Select **Presenter** view and **Start delivery clock**. Advance the chapter cue at each actual transition; export observed timing at the end. Keep explanation blocks under roughly seven minutes and interleave prediction/inspection. Every scenario follows predict → run → inspect → download.

| Minutes | Scenario/action | Expected proof |
|---|---|---|
| 0–8 | Opening vote; withhold ticket | Prediction: identity, model, tool policy or approval |
| 8–20 | Replay the isolated ₹90 lakh incident | Isolated delta −900,000,000 paise; protected delta 0 |
| 20–33 | Gate 1: exceed inference headroom | 429 before inference dispatch; direct tool result is separate |
| 33–53 | Local policy repair; three Gate 2 scenarios | Beneficiary denied, amount denied, permitted ₹250 executed |
| 53–60 | MCP token at API; read-only payment attempt | 401 audience; 403 scope |
| 60–67 | Break and checkpoint recovery | Seven-minute break; restored local services |
| 67–85 | Local identity repair; scope exchange | Unauthorized 403; permitted 200, sanitized claims |
| 85–103 | Independently approve ₹1,500 settlement | Pending → independent review → exact payment; tampering denied |
| 103–119 | Inspect A2A attacks and bound completion | Foreign read/unauthorized completion 403; mismatch 400; correct binding |
| 119–130 | Reconstruct denied and legitimate paths | Run/proposal/task/payment/ledger and observed spans |
| 130–135 | Revisit vote; assign control owners | Explained denial and one permitted business effect |

## A · Opening and isolated loss · minutes 0–20

Say: “NegotiatorBot handled a case. PaymentsAgent received a settlement instruction. The bank paid ₹90 lakh. Which control would you examine first?” Collect two predictions before revealing the ticket at the next chapter.

Choose **Replay the isolated ₹90 lakh incident**, then **Run scenario**. Inspect the ticket, fixed recorded handoff, sandbox result and both ledgers. Expected isolated loss: **₹90 lakh = 900,000,000 paise**, one isolated payment; protected balance/payment deltas 0/0.

The sandbox has its own disposable ledger, internal network and fixed proposal. This is a recorded proposal executed by an intentionally vulnerable isolated service. It is not a live model compromise or a debit of the protected bank. If sandbox readiness fails, show dated evidence rather than modifying the protected stack to recreate a loss.

## B · Gate 1 and direct execution · minutes 20–33

Run **Gate 1: exceed inference headroom**. Inspect HTTP 429 and no inference dispatch. Ask: “Would this budget decision prevent a separate direct tool request?” Use the Gate 2 evidence to answer; do not infer tool authorization from an inference refusal.

Optional **one bounded live case review** is a separately labelled model observation with no tool execution. Keep refusal and provider failure visible. Skip it if it threatens the chapter boundary.

## C · Gate 2 pair repair · minutes 33–53

On each pair's local instance, install the prepared initial policy:

```bash
cp workshops/w4/checkpoints/initial/policy.rego spikes/spike3_opa/policy.rego
docker compose restart opa
```

Run **Gate 2: prohibited beneficiary**, **Gate 2: excessive amount** and **Gate 2: permitted ₹250 payment**. The initial checkpoint also prohibits `vendor-alpha`, so the legitimate request is denied. Ask pairs to remove only `vendor-alpha`; retain `fraud-account-66` and the transfer ceiling.

Use the completed checkpoint for recovery:

```bash
cp workshops/w4/checkpoints/completed/policy.rego spikes/spike3_opa/policy.rego
docker compose restart opa
```

Retest all three. Expected prohibited beneficiary denial for 25,000 paise, ceiling denial for 900,000,000 paise to a permitted beneficiary, and one permitted 25,000-paise payment. Inspect actual policy response plus ledger deltas; the console does not toggle enforcement.

Optional outage, if already rehearsed: stop OPA, run **Gate 2: test a stopped policy service**, then restore immediately even if the scenario fails:

```bash
docker compose stop opa
# Run the fixed policy-outage scenario in Incident Room.
docker compose start opa
docker compose ps opa
```

Expect fail-closed policy timeout/unavailability and zero protected financial effects. Preserve restoration over extra troubleshooting.

## D · Direct API bypass · minutes 53–60

Run **Gate 3: MCP token at the API**, then **Gate 3: read-only payment attempt**. Show actual audience/scope claims and service responses: wrong audience 401; missing payment scope 403; both protected deltas 0/0.

Say: “A credential valid for the MCP boundary does not grant API payment authority.” Avoid claiming these selected checks establish complete protocol conformance.

## E · Break and local recovery · minutes 60–67

Take the full seven-minute break. Timebox stalled-pair recovery to two minutes each: export evidence, restore completed policy, restart OPA and refresh readiness. Preserve pending or uncertain financial runs for reconciliation rather than replacing them.

Check that both browser sessions remain usable; W4 sessions persist for three hours, while proposals expire after ten minutes. Create the approval proposal after the break, immediately before review.

## F · Scope entitlement exercise · minutes 67–85

```bash
.venv/bin/python workshops/w4/exercise_exchange.py initial
```

Inspect `workshops/w4/checkpoints/initial/identity.json`: a viewer requests `api:payments:write`; expect 403. Change only `requested_scope` to `api:accounts:read`, rerun `initial`, then compare with:

```bash
.venv/bin/python workshops/w4/exercise_exchange.py completed
```

Expect corrected/completed exchange 200. The CLI writes sanitized timestamped evidence. If `.env` changes JWT signing, issuer or audiences, export matching values into this shell; the CLI does not load `.env` automatically. Preserve/restore the initial checkpoint after local edits if preparing another session.

In the console compare **Gate 3: unauthorized scope exchange** and **Gate 3: permitted scope exchange**. Inspect claims without displaying tokens. The browser buttons are fixed scenarios; editing a local checkpoint changes the CLI exercise, not the server-owned scenario definition.

## G · Independent review and exact execution · minutes 85–103

In the requester browser run **A2A: independently approve ₹1,500 settlement** immediately before review. Expected pending proposal, `awaiting_review`, zero financial effect, proposal ID and task ID. Inspect source, beneficiary, currency and amount **150,000 paise**.

In the separate reviewer browser: sign in → choose **Independent reviewer** → enter the configured reviewer password → **Open reviewer session**. Select the same **Server-owned run** by run ID. Review all four payment fields and both identifiers before clicking **Approve exact proposal**. A requester session cannot approve its own run, even if reviewer authority is added to it.

Inspect the resulting events: self approval 403; changed arguments 400; exact execution succeeds; retry reuses the payment. Expected final protected delta **−150,000 paise**, payment-count delta **1**. The server owns the approved arguments and financial key. Refresh both windows, reselect the same run and download evidence. A completed run disables another UI decision; inspect the recorded retry event rather than starting a new settlement to illustrate retry.

An independent rejection is a valid alternate ending but provides no successful payment. Keep one approved synthetic run for the complete business proof.

## H · A2A task ownership and binding · minutes 103–119

Use the approved run from the previous chapter to inspect **Foreign task access** 403, **Unauthorized completion** 403, **Mismatched payment binding** 400, and successful task completion. Identify requester, designated executor and independent reviewer.

Compare `task.output.payment_id` with the actual payment ID, and inspect binding of source, destination, amount, currency and proposal. These attacks are included in the legitimate-delegation scenario; there are no separate UI buttons for each subtest.

If demonstrating a fresh delegation, create it just before review, approve independently and account for its additional ₹1,500 payment. Do not leave a chapter-85 proposal waiting until it expires. This lab implements an A2A subset.

## I · Reconstruct evidence and close · minutes 119–135

Select one denied run and the completed settlement. Reconstruct run → proposal → task → payment → ledger. Expand **Evidence drawer** and **Identity inspector**. Click **Check collector evidence**, then inspect Jaeger. Exported spans establish observed tracing; an ID alone leaves the result `incomplete`.

At minute 130 revisit the opening vote. Ask attendees to explain one denial using caller, arguments and response, then prove one legitimate settlement using IDs and deltas. Assign owners for inference/budget, tool policy, identity/exchange, review and audit/incident operations.

Export observed chapter timing and fill the [human delivery record](../../workshops/w4/delivery-rehearsal.md) with actual break, recovery, projector readability and total duration. Technical rehearsal does not certify 135-minute delivery.

## Recovery, fallback and exit

A stalled pair gets two minutes before a completed checkpoint or saved evidence. If a payment/approval response is lost, select the original **Server-owned run** and **Reconcile uncertain result** when enabled. Inspect proposal status and keyed bank records. Keep an unreadable/unresolved ledger labelled unresolved; do not launch a new run with a new financial key or reset to conceal uncertainty.

Restore OPA after an outage. If reviewer authorization fails, check the password matches the running API and that the browser is separate. If a proposal expires, preserve its evidence and create a new one only after confirming no financial effect. Do not recreate the API to change credentials in the middle of an unresolved payment.

Fallback: [evidence index](../../workshops/w4/evidence/README.md) and [2026-10-05 incident evidence](../../workshops/w4/evidence/incident-2026-10-05T170259Z.json). Announce the original date/mode and inspect actual results. A missing trace remains incomplete; provider failure remains `live_failed`.

If behind, omit optional live comparison and outage, shorten code inspection, and reuse the completed run for A2A evidence. Preserve break, pair repairs, independent review and one settlement proof. Save downloaded evidence and timing locally before logout; logout revokes reviewer authorization. Restore any intended pre-session policy/identity edits on the disposable local lab after all financial runs are settled or explicitly unresolved.
