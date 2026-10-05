# W4 facilitator answer key

Use the [presenter story](../../docs/workshops/workshop-4-story.md), [participant worksheet](worksheet.md) and [incident evidence sheet](incident-evidence.md). The schedule totals **135 minutes including the seven-minute break**. Keep explanation blocks under seven minutes; use a prediction or evidence inspection between blocks.

## Setup and isolation

Complete the [workshop Python setup](../../docs/workshops/participant-infra-guide.md#step-23-set-up-python-virtual-environment-for-workshop-clients-verification--tests) and run shell commands in Bash on Linux/WSL. Build before attendees arrive. Configure an independent reviewer password locally. Keep it out of exported evidence. For the local presenter only, generate a distinct incident sandbox key and enable the replay:

```bash
export W4_REVIEWER_PASSWORD="$(python3 -c 'import secrets; print(secrets.token_urlsafe(24))')"
export W4_SANDBOX_KEY="$(python3 -c 'import secrets; print(secrets.token_urlsafe(24))')"
export W4_ENABLE_VULNERABLE=true
export W4_OBSERVATION_ONLY=false
./scripts/workshop pull w4
docker compose --profile w4 --profile w4-presenter build incident-sandbox
./scripts/workshop switch w4
docker compose --profile w4 --profile w4-presenter up -d incident-sandbox
```

Pass the reviewer password privately to the cofacilitator; use separate browser sessions. On shared hosting set `W4_OBSERVATION_ONLY=true` and keep `W4_ENABLE_VULNERABLE=false`: authenticated viewers can inspect sanitized presenter runs, but scenario execution, review decisions and financial reconciliation are disabled. The incident service has no public port, no protected volumes, no banking/provider keys, a separate internal network and a disposable ledger. It accepts only a run ID and executes one fixed recorded proposal. Recreating that service resets its ledger; protected runs are stored separately in `/app/data/w4-incident.sqlite`. Run one uvicorn worker per local instance.

## Expected results and explanations

| Test | Expected service result | Business evidence |
|---|---|---|
| Isolated replay | API 200; fixed valid sandbox credential and proposal | −900,000,000 paise only in isolated ledger; protected delta 0 |
| Gate 1 exhausted headroom | 429 before provider dispatch | No payment; budget is a separate boundary |
| Prohibited beneficiary (25,000 paise) | MCP `POLICY_DENIED`, prohibited beneficiary | Delta 0; avoids conflating amount/beneficiary |
| Excessive amount (900,000,000 paise, permitted beneficiary) | MCP ceiling denial | Delta 0 |
| OPA stopped | MCP policy timeout/error fail closed | Delta 0; restore OPA in `finally` |
| MCP token at API | 401 audience validation | Delta 0 |
| Read-only token writes payment | 403 scope validation | Delta 0 |
| Viewer exchanges payment-write scope | 403 entitlement | No exchanged credential exported |
| Permitted exchange | 200 | API audience/read scope shown, token excluded |
| Payment agent self approval | 403 requester/delegation rule | Pending exact proposal, delta 0 |
| Independent review / changed arguments | Approve 200; tampered execute 400 | Approval is attached to source/amount/currency/beneficiary |
| Exact approved execution / retry | 200 / idempotent replay | One payment, −150,000 paise |
| Foreign task read / non-executor completion | 403 / 403 | Only owner/designated executor has task access |
| Payment bound to mismatched task | 400 | Binding checks source, amount, currency, destination and optional proposal |
| Legitimate task completion | 200 | Task output payment ID equals settled ledger payment ID |
| Optional live comparison | Real live answer/refusal, or `live_failed` | No tool execution; never relabel replay as live |
| Trace collector unavailable | `incomplete` | Generated trace ID alone is not span evidence |

The incident has several failed boundaries, not a single “bad model”. Valid credentials authenticate a principal; schema validation establishes request shape. Neither authorizes a beneficiary, amount, self approval or task mutation. Gate 1 manages inference dispatch and budget; Gate 2 checks identity and actual tool arguments; Gate 3 validates downstream audience, scopes and banking invariants. Independent approvals and A2A task binding remain enterprise controls.

## Checkpoint recovery

Allow two minutes per stalled pair. Restore the completed local policy and identity configurations. Restart OPA, then refresh readiness. For pending reviews, finish/reject with the separate reviewer; proposals expire after ten minutes, so create them immediately before review. For lost responses or process restart, select the original server-owned run and use **Reconcile uncertain result**. Proposal status and keyed ledger payments determine recovery. The server never retries a payment with a fresh financial key.

If a run remains unresolved because the API cannot be read, keep it unresolved and show timestamped fallback evidence. Do not reset a protected ledger to conceal uncertainty. Preparation interrupted before any proposal/approval can be retired as `checkpoint_recovered`; export the interruption before starting a fresh demo. Sessions persist for three hours only in W4; logout revokes the persisted session and its reviewer authorization.

The completed checkpoint is a local configuration repair, not a UI enforcement toggle. Restoration must be confirmed with actual service results.

## Rehearsals

Use the same shell as setup so `W4_REVIEWER_PASSWORD` matches the running API.
In a new shell, export the existing configured password; generating a new one
without recreating the API causes reviewer authentication to fail. Restore the
completed policy checkpoint before rehearsal. `--vulnerable` requires the
presenter sandbox setup above. These rehearsals create fictional payments and
proposals on the active stack; they do not reset data. Evidence is written to
`workshops/w4/evidence/incident-<timestamp>.json`.

```bash
.venv/bin/python workshops/w4/rehearsal_w4.py --vulnerable --outage
# Optional hosted-model comparison; sends the fictional ticket only:
.venv/bin/python workshops/w4/rehearsal_w4.py --live
```

The script records a **technical rehearsal**, not 135 minutes of human delivery. It checks the fixed attack suite, independent approval, exact settlement, one effect, refresh/idempotency and trace collection, and restores OPA after outage. Unit tests cover proposal expiry and lost approval/payment responses.

For timed delivery, choose Presenter view and start the delivery clock. Advance chapter cues at actual transitions; export observed timing. Complete [delivery-rehearsal.md](delivery-rehearsal.md) with observed break/recovery/readability and delivery duration. Acceptance stays pending until a real 135-minute rehearsal is recorded. Production claims remain limited to selected lab controls and this repository’s A2A subset.

## Fresh resource and checkpoint findings (2026-10-05)

Initial policy denied `vendor-alpha`; the completed policy permitted one ₹250
payment while both attacker requests remained denied. Initial identity exchange
returned 403; completed exchange returned 200 with the read scope. The original
active policy was restored after the rehearsal.

The W4 resource snapshot measured about 1.06 GiB across workshop containers,
including the sandbox. Kafka used 492.4 MiB of its 512 MiB cap (96.17%); inspect
`docker stats` and OOM/restart state during preparation and longer delivery.
This is a single-point Linux measurement, not a peak-load or Windows benchmark.
See the [series report](../../docs/workshops/rehearsal-2026-10-05.md) for dated evidence.
