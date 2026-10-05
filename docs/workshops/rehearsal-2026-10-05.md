# Workshop story review and technical rehearsal — 2026-10-05

W1–W4 profile smoke checks and technical rehearsals passed on the Linux presenter
host. W2 Governance Studio and W4 Incident Room browser flows also passed.
The run used deterministic replay, real gateway/policy/banking services, and
W3 Kafka/Temporal. No hosted-model calls were made; prior live evidence remains
historical. Automated execution does not certify 45/135-minute human delivery,
room/projector readability, Windows/WSL performance or peak-load capacity.

## Results and reproducible commands

Run from the repository root with the full Python environment and prebuilt
images. Keep one active profile. Save evidence and use disposable fictional lab
data: successful scenarios change the ledger. The W1–W3 runners overwrite their
undated evidence files; this review saved fresh dated copies and retained the
previous committed undated artifacts.

| Workshop | Commands run | Observed result | Fresh evidence |
|---|---|---|---|
| W1 | `switch w1`; `reset w1 --yes`; `verify w1`; `.venv/bin/python workshops/w1/rehearsal_w1.py` | 26 broad tools; exactly two curated tools; account/case reads; excluded payment-list rejection; invalid-key embedded 401; direct API 401/200. Technical runner: 3.00 seconds. | [W1 replay](../../workshops/w1/evidence/rehearsal-replay-2026-10-05.json) |
| W2 | `verify w2`; `.venv/bin/python workshops/w2/rehearsal_w2.py`; `.venv/bin/python workshops/w2/rehearsal_console.py --outage` | Recorded injection denied; ₹250 creates one payment; ₹5,000 creates a pending proposal without debit; ceiling/viewer denied; OPA pause fails closed with zero effects and is restored. CLI runner: 14.01 seconds. | [CLI](../../workshops/w2/evidence/rehearsal-replay-2026-10-05.json), [console](../../workshops/w2/evidence/console-2026-10-05T165904Z.json) |
| W3 | `USE_REPLAY_FIXTURES=true ./scripts/workshop switch w3`; `verify w3`; `.venv/bin/python workshops/w3/rehearsal_w3.py` | Real graph reads; ₹750 proposal waits; worker SIGKILL and duplicate event retain the wait; approved case resolves with one settlement; rejected case closes with zero payments. Runner: 24.78 seconds. | [W3 replay](../../workshops/w3/evidence/rehearsal-replay-2026-10-05.json) |
| W4 | [Facilitator setup](../../workshops/w4/answer-key.md#setup-and-isolation); `verify w4`; `.venv/bin/python workshops/w4/rehearsal_w4.py --vulnerable --outage` | ₹90 lakh loss only in isolated ledger; budget/beneficiary/ceiling/audience/scope attacks denied; OPA stopped and restored; independent review settles one ₹1,500 payment bound to its task; tampering, self approval and task attacks rejected; traces observed. Runner: 4.27 seconds. | [Incident API](../../workshops/w4/evidence/incident-2026-10-05T170259Z.json) |

`switch`, `reset` and `verify` above refer to `./scripts/workshop` commands.
W2's CLI runner switches W2 itself; the console runner uses the active stack.
W3's runner resets banking data and deletes local Temporal SQLite history.
W4 uses temporary independent reviewer and sandbox secrets configured before
startup; secrets are excluded from committed artifacts.

Additional checks:

- W1 participant CLI: curated initialization, discovery and account read passed;
  excluded `create_payment` returned tool-not-found. The newly documented curated
  invalid-key read was also checked directly: outer HTTP 200 contained downstream
  HTTP 401 ([curated denial](../../workshops/w1/evidence/curated-denial-2026-10-05.json)). The automated runner also
  checked exclusion using an actual tool from the broad catalog.
- W2 browser: `NODE_PATH=/tmp/flo-bank-browser/node_modules node tests/w2_console_browser.cjs`.
  Covers fixed scenarios, export, 320–1440 pixel layouts, simulated provider-error
  rendering, dashboard link and logout. The provider-error check is intercepted
  browser traffic, not an actual hosted-provider outage.
- W4 browser: with the same configured reviewer password,
  `NODE_PATH=/tmp/flo-bank-browser/node_modules node tests/w4_incident_browser.cjs`.
  Fixed attacks, isolated replay, refresh, separate reviewer, one bound settlement,
  export and 320–1920 pixel layouts passed. [Export](../../workshops/w4/evidence/incident-browser-2026-10-05T17-03-46-945Z.json),
  [presenter screenshot](../../workshops/w4/evidence/incident-presenter-2026-10-05T17-03-46-945Z.png),
  [mobile screenshot](../../workshops/w4/evidence/incident-mobile-2026-10-05T17-03-46-945Z.png).
- W4 policy exercise: initial checkpoint denied all three test requests;
  completed checkpoint retained both attack denials and permitted one ₹250 payment.
  [Checkpoint results](../../workshops/w4/evidence/checkpoint-rehearsal-2026-10-05.json).
  The original active policy was restored afterward.
- W4 identity exercise: `.venv/bin/python workshops/w4/exercise_exchange.py initial`
  returned 403; `completed` returned 200 with only the read scope.
  [Initial](../../workshops/w4/evidence/identity-initial-2026-10-05T170359Z.json),
  [completed](../../workshops/w4/evidence/identity-completed-2026-10-05T170400Z.json).

## Findings applied to the documentation

| Finding | Delivery correction |
|---|---|
| W1 answer key hard-coded 13 tools; actual catalog contained 26. | Use runtime discovery; distinguish the static teaching contract from the served API. |
| W1 worksheet left curation until minute 40, while the story/rehearsal verifies it during minutes 22–32. | Align worksheet and answer key with the story; add direct `--curated` commands. |
| W1 worksheet claimed a `readOnlyHint` absent from the completed JSON. | Remove the claim; descriptions/hints do not enforce access. |
| W1 rehearsal assumes the seeded 1,500,000-paise balance. | Explicitly switch W1 and reset fictional data before rehearsal; preserve prior evidence. |
| W2 historical CLI ceiling request is ₹50,000; the console story uses ₹15,000. | Prefer the current console rehearsal; both exceed the ₹10,000 ceiling. Compare ledger deltas because verification and permitted scenarios create payments. |
| W3 worksheet claimed a double charge and implied a 30-day implemented wait. | Use disputed-charge wording, neutral review comments and the actual 24-hour timeout. |
| W3 replay rationale claims verified duplicate debit without transaction evidence. | Label it fixture text; the case and account balance do not prove refund entitlement. |
| W3 rejection fixture reads absent account `acc-8802` and records a 404. | Show the tool error; rejection/zero payments passed, but a fully successful investigation was not established. |
| Bank reset leaves Temporal workflows and W4 run records intact. | Clarify reset scope, active-profile requirement and repeat-delivery preparation. |
| APISIX profile mount is chosen at container creation. | Use launcher `switch` to correct a mismatched profile; restarting alone retains the old bind mount. |
| Master guide described customer chat as scripted in every profile. | Separate customer chat configuration from workshop inference replay; explicitly select scripted customer mode for offline delivery. |

## Resource observation and remaining delivery acceptance

The [W4 snapshot](../../workshops/w4/evidence/resources-2026-10-05.json) measured
about 1.06 GiB across ten workshop containers, including the incident sandbox.
The host had 5,219 MiB available. Kafka used 492.4 MiB of its 512 MiB limit
(96.17%): inspect memory and OOM/restart state during longer preparation/delivery.
This is a single-point measurement, not a peak or total operating-budget proof.
The protected Caddy, Portainer, Uptime Kuma and Dozzle services remained running.

The original W2 profile was restored after the rehearsals; the isolated presenter
sandbox was stopped by the switch. Fictional banking data reflects the rehearsals.
Reset it after saving any needed evidence before the next audience session.

[W4 human delivery acceptance](../../workshops/w4/delivery-rehearsal.md) remains
pending actual observed timing, break/recovery and projector checks. The same
separation applies to W1–W3: short technical runners prove selected service
behavior, not spoken duration. Optional live inference, participant hardware and
multi-week durability were not freshly measured in this dry run.
