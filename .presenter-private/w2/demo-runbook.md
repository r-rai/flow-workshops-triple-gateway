# Workshop 2 presenter demo runbook

**Beyond API Governance: Securing AI Agents, MCP Servers, and Enterprise Integrations** · 45 minutes · profile `w2`.

Run commands from the repository root in Bash with the workshop Python environment installed. Keep [Governance Studio](http://localhost:9080/workshop-2) on screen. Use the [worksheet](../../workshops/w2/worksheet.md), [answer key](../../workshops/w2/answer-key.md) and [story](../../docs/workshops/workshop-2-story.md) for supporting discussion.

## Before the room opens

Use the designated fictional lab with one active workshop profile and one presenter. Switching stops the workshop stack; resetting discards seeded-bank changes. Leave host monitoring and unrelated services alone. Download images and build before the clock starts.

```bash
./scripts/workshop preflight
./scripts/workshop pull w2
./scripts/workshop switch w2
./scripts/workshop status
./scripts/workshop verify w2
.venv/bin/python workshops/w2/rehearsal_console.py --outage
```

The console rehearsal creates one ₹250 payment and a pending proposal, pauses only OPA and attempts restoration in `finally`. It uses the running stack without switching or resetting. Inspect its timestamped `workshops/w2/evidence/console-*.json`, preserve needed evidence, then prepare the bank for delivery:

```bash
./scripts/workshop reset w2 --yes
```

Verification can create payments, so do it before the final reset. Sign in at `/workshop-2` with `maya@flobank.demo` / `flo-demo`. Open a terminal with OPA recovery ready, the active policy `spikes/spike3_opa/policy.rego` in an editor, and [Jaeger](http://localhost:16686). Confirm OPA is running and unpaused. Rehearse the browser buttons as well as the technical runner; reset after those rehearsals if a fresh seed is wanted.

Default delivery uses recorded proposals and actual MCP, OPA and bank services. Optional **Ask Flo to review the case** needs configured provider access in the adapter. Decide before delivery whether to use it; `--live` adds one provider call to the rehearsal and can incur charges. Customer-chat mode and workshop replay mode are separate settings.

## A · The ticket gives orders · minutes 0–5

Say: “Flo may read this ticket. What would authorize a payment requested inside it?” Ask for a prediction, then click **Replay the unsafe proposal**.

Inspect `case-502`, submitted beneficiary `fraud-account-66`, amount **900,000 paise = ₹9,000**, decision `PROHIBITED_BENEFICIARY`, balance delta 0 and payment-count delta 0. Download the result.

The ticket says 900000 INR; the fixed payment request uses a different minor-unit fixture. Name that difference. This is a recorded unsafe proposal evaluated by real services; it does not establish a live model compromise.

## B · Name the boundaries · minutes 5–12

Use the boundary cards: Gate 1 owns inference dispatch and limits; Gate 2 checks signed identity and actual tool arguments; Gate 3 retains scoped API authorization and banking rules. These logical boundaries share gateway infrastructure here.

Ask: “Which boundary received this request?” Expand **Boundary responses**. A recorded proposal skips inference, and a denied payment can stop before the bank. Snapshot reads are separate observer requests.

## C · Optional live comparison · minutes 12–22

If prepared, click **Ask Flo to review the case** once. Inspect mode, model outcome, proposed arguments and the boundaries actually called. It sends only case ID/description and validates at most one payment proposal. Accept **No tool proposed** as a valid refusal. Provider failure remains visible; return explicitly to the recorded scenario.

Without live inference, use this time to inspect the recorded request and ask pairs to distinguish “model proposed”, “policy evaluated” and “bank paid”. A saved live example must carry its original date and mode.

Say: “A refusal describes this model run. Execution authority comes from controls outside the model.”

## D · Four outcomes from one capability · minutes 22–34

Predict → click → inspect → download for each button. Use deltas rather than a memorized absolute balance.

| Button | Expected evidence | Bank balance / payment-count delta |
|---|---|---|
| Pay ₹250 to a vendor | Signed `support_agent`; 25,000 paise to `vendor-alpha`; executed | −25,000 paise / +1 |
| Request a ₹5,000 payment | 500,000 paise; approval required; persisted proposal ID and `pending` | 0 / 0 |
| Attempt a ₹15,000 payment | 1,500,000 paise; `AMOUNT_EXCEEDS_TRANSFER_CEILING` | 0 / 0 |
| Try the same payment as a viewer | Signed `viewer`; `NO_MATCHING_RULE` | 0 / 0 |

The approval reason in console evidence is `AMOUNT_EXCEEDS_UNSUPERVISED_LIMIT`; `APPROVAL_REQUIRED` describes the required action. A successful MCP transport is insufficient to establish payment execution.

Show `input.principal.role`, `input.arguments.amount`, and `input.arguments.beneficiary` in the active policy. For an eligible role and permitted beneficiary, ≤100,000 paise allows; 100,001–1,000,000 requires approval; above 1,000,000 denies. The prohibited-beneficiary rule takes precedence. Core Banking independently requires approval above 100,000 paise.

Optional pair prompt: “What changes if support_agent is removed from both low-risk decision and reason rules?” Inspect an offline copy. Keep the broad insecure checkpoint off the shared stack. W2 stores the pending proposal; W3–W4 show continuation and review.

## E · Policy stops answering · minutes 34–41

Pause only this Compose project's OPA:

```bash
docker compose pause opa
```

Click **Pay ₹250 to a vendor** once. Expect `POLICY_TIMEOUT_FAIL_CLOSED`, balance delta 0, payment-count delta 0. Case-review buttons need a governed read first, so use the payment button for this proof. Restore OPA immediately, even if the request fails:

```bash
docker compose unpause opa
docker compose ps opa
```

Inspect the response and before/after ledger observations. Check exported spans through **Trace correlation** and Jaeger before describing a complete trace. An observer read span does not prove a denied payment reached Core Banking.

## F · Assign owners and bridge · minutes 41–45

Open the blueprint panels. Ask for owners of approved inference access, data minimization, tool policy, independent review, evidence retention and incident response.

Say: “A ticket can influence a proposal, but cannot grant authority. Next, we will make that proposal survive an absent reviewer and a crashed worker.” Reserve two minutes for questions.

## Recovery, fallback and exit

Timebox a failed live step to 60 seconds. Restore OPA before switching to saved evidence. For a lost payment response, inspect the bank ledger before retrying: these W2 console requests lack idempotency keys. Refreshing or signing out does not reset shared bank data.

Use [recorded console verification](../../workshops/w2/evidence/verification-2026-10-04.md) and [2026-10-05 console evidence](../../workshops/w2/evidence/console-2026-10-05T165904Z.json). Say: “This is recorded evidence from an earlier run,” then inspect its actual decisions, effects and trace status. Keep replay/live and historical/current labels visible.

At minute 22 begin the four outcomes; at 34 begin outage; at 41 close. If behind, shorten the optional live discussion and trace browsing. Preserve the permitted payment, pending proposal, denials and outage restoration.

Before delivery sign-off, record date, machine, actual 45-minute spoken duration, each scenario result, pending proposal ID, ledger deltas and OPA restoration. Automated checks do not measure human delivery. Export evidence before any next-session reset.
