# Workshop 2 — Beyond API Governance

Before running Python commands or the Bash launcher, complete the [workshop Python setup](../../docs/workshops/participant-infra-guide.md#step-23-set-up-python-virtual-environment-for-workshop-clients-verification--tests) from the repository root. Use Bash on Linux/WSL for the launcher; macOS users can run Python clients and direct Docker Compose commands.

**Securing AI Agents, MCP Servers, and Enterprise Integrations**

**Duration:** 45 minutes · **Profile:** `w2` · **Experience:** Flo Bank Governance Studio

## Start the lab

From the repository root, with Docker and the workshop Python environment ready:

```bash
./scripts/workshop pull w2
./scripts/workshop switch w2
./scripts/workshop verify w2
```

Open **http://localhost:9080/workshop-2**. Sign in with the prefilled fictional
credentials `maya@flobank.demo` / `flo-demo`. The customer dashboard also links to
**Governance Studio** when W2 is active. Use one presenter at a time: scenarios
share the seeded `acc-101` ledger. The ₹250 success demo creates a real record in
that fictional ledger; pending proposals do not debit it.

For a fresh checkout without another profile running, the equivalent startup is:

```bash
ACTIVE_PROFILE=w2 docker compose --profile w2 up -d --build
```

Use the workshop switch command when changing profiles. Installation and image
downloads happen before the timed session. See the [participant infrastructure
guide](../../docs/workshops/participant-infra-guide.md) for Windows/WSL setup.

## The 45-minute story

| Minutes | Presenter action | Participant evidence |
|---|---|---|
| 0–5 | Open the support case via **Replay the unsafe proposal** | Identify case text as untrusted input and inspect the prohibited beneficiary |
| 5–12 | Follow the three boundary cards | Identify who owns inference access, tool policy, and banking rules |
| 12–22 | Compare the recorded attack with **Ask Flo to review the case** | Distinguish a model refusal from a policy denial; inspect arguments and signed role |
| 22–34 | Run payment, approval, ceiling and viewer scenarios | Record decision, reason, balance delta and new-payment count |
| 34–41 | Presenter pauses OPA; rerun the small payment | Verify a timeout denial and zero observed financial effects; inspect trace/evidence |
| 41–45 | Open the enterprise blueprint panels | Assign control owners; discuss data protection, shadow AI and audit retention |

## Exercise 1 — An instruction is not authority

Click **Replay the unsafe proposal**. The console reads `case-502` through MCP,
then submits a fixed synthetic `create_payment` request for **900,000 paise =
₹9,000**, beneficiary `fraud-account-66`. The ticket's text itself asks for
900000 INR; the recorded request deliberately uses the original lab fixture's
minor-unit amount. Do not treat it as a faithful live interpretation of that text.

Expect `PROHIBITED_BENEFICIARY`, balance change ₹0 and zero new payments. The
recorded proposal bypasses model inference but traverses real policy and API
services. It proves execution control for this request, not prompt-injection
prevention or successful compromise of a live model.

**Optional live comparison:** select **Ask Flo to review the case**. It reads the
same case and makes one hosted-model call through Gate 1, capped at 2,048 output
tokens. A configured provider key is required in the adapter environment. Only
case ID and description are sent; credentials and ledger snapshots are excluded.
It validates at most one payment tool proposal before passing it to MCP. A model
refusal is displayed as **No tool proposed**. Provider failures are visible;
there is no silent recorded fallback. The live call can incur provider charges.

Record: did the model request an action, did Gate 2 evaluate a payment, and did
the bank actually create a payment? These are three different questions.

## Exercise 2 — Identity and arguments change the outcome

Run the following buttons and download each result.

| Button | Role / request | Expected result | Balance / payment delta |
|---|---|---|---|
| Pay ₹250 to a vendor | `support_agent`, 25,000 paise, `vendor-alpha` | Payment executed | −₹250 / +1 |
| Request a ₹5,000 payment | `support_agent`, 500,000 paise, `vendor-beta` | `APPROVAL_REQUIRED`, persisted `pending` proposal | ₹0 / 0 |
| Attempt a ₹15,000 payment | `support_agent`, 1,500,000 paise | `AMOUNT_EXCEEDS_TRANSFER_CEILING` | ₹0 / 0 |
| Try the same payment as a viewer | Signed `viewer`, 25,000 paise | `NO_MATCHING_RULE` | ₹0 / 0 |

The active policy is [spikes/spike3_opa/policy.rego](../../spikes/spike3_opa/policy.rego).
For a support agent and a permitted beneficiary: **≤100,000 paise (₹1,000) allows**;
**100,001–1,000,000 paise requires approval**; **above 1,000,000 paise denies**.
The browser selects fixed scenarios. It cannot choose an admin identity, arbitrary
account, tool, approval ID or gateway URL. The shared lab login is a convenience,
not a production identity provider. Do not deploy this console as public banking.

**Guided policy discussion:** locate `input.principal.role`,
`input.arguments.amount` and `input.arguments.beneficiary`. Predict what removing
`support_agent` from both low-risk allow rules would do. The policy has separate
`decision` and `reason` rules; change both consistently if experimenting locally.
Work on a private copy and evaluate it offline before changing a running policy.
The initial broad checkpoint is a deliberately insecure teaching artifact; do
not install it on the shared presenter stack.

A pending approval is stored by Core Banking. This console does not approve or
settle it; the durable approval/resume workflow belongs to Workshops 3–4.

## Exercise 3 — Policy failure stops execution

On the presenter machine, pause only OPA:

```bash
docker compose pause opa
```

Click **Pay ₹250 to a vendor**. Expect `POLICY_TIMEOUT_FAIL_CLOSED`, zero new
payments and an unchanged balance. Do not use the case-review buttons while OPA
is paused: the initial case read also requires policy and will fail first.
Restore OPA immediately:

```bash
docker compose unpause opa
```

For an automated rehearsal with restoration in a `finally` block:

```bash
.venv/bin/python workshops/w2/rehearsal_console.py --outage
# Optional, with one live provider call as well:
.venv/bin/python workshops/w2/rehearsal_console.py --outage --live
```

The script uses the current W2 stack; it does not switch profiles or reset data.
It saves timestamped JSON in `workshops/w2/evidence/`. If a request loses its
response after execution, inspect the ledger before retrying: console payment
requests currently do not carry idempotency keys.

## Evidence and takeaways

Expand **Boundary responses** to compare submitted arguments with actual service
results. **Trace correlation** gives a trace ID for Jaeger at
http://localhost:16686. Verify that spans were exported before calling a trace
complete. Snapshot reads use a separate observer identity; their spans are not
proof that a denied payment reached the banking API. Downloaded evidence includes
fictional case content and business identifiers, but no issued tokens or private
model reasoning. Treat future real-world audit exports according to data policy.

The blueprint panels cover approved AI inventory, data minimization, provider
controls, review, audit and operations. The lab demonstrates selected controls;
it does not implement enterprise DLP, shadow-AI discovery, full MCP OAuth discovery,
production IAM, tamper-proof audit storage, or compliance certification.

## Reset for the next session

Sign out clears the browser session, not the shared bank ledger. After saving any
needed lab evidence, reset only the fictional workshop data:

```bash
./scripts/workshop reset w2 --yes
```

Complete a [participant evidence worksheet](#exercise-2--identity-and-arguments-change-the-outcome)
with each decision, its reason, the signed role and the observed financial effect.
