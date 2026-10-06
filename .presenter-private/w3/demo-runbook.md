# Workshop 3 presenter demo runbook

**Architecting the Agentic Enterprise: Middleware, Durable State, and Event-Driven AI** · 45 minutes · profile `w3`.

Run commands from the repository root in Bash with the workshop Python environment installed. Prepare a terminal, editor and saved evidence. Supporting references: [worksheet](../../workshops/w3/worksheet.md), [answer key](../../workshops/w3/answer-key.md), [story](../../docs/workshops/workshop-3-story.md).

## Before the room opens

Use a disposable W3 lab. Set `USE_REPLAY_FIXTURES=true` in repository-root `.env` before startup for the reproducible 75,000-paise (₹750) proposal. Build and verify before presentation:

```bash
./scripts/workshop preflight
./scripts/workshop pull w3
./scripts/workshop switch w3
./scripts/workshop status
./scripts/workshop verify w3
```

The automated rehearsal below resets bank data, stops Temporal/worker, deletes lab Temporal SQLite history, exercises both approval and rejection, and overwrites `workshops/w3/evidence/rehearsal-evidence.json`. Preserve earlier evidence first. It has fixed default Compose container/volume names; use the repository's default project or inspect those assumptions before running it.

```bash
mkdir -p .presenter-private/w3/live-evidence
cp workshops/w3/evidence/rehearsal-evidence.json .presenter-private/w3/live-evidence/before-rehearsal.json
.venv/bin/python workshops/w3/rehearsal_w3.py
cp workshops/w3/evidence/rehearsal-evidence.json .presenter-private/w3/live-evidence/technical-rehearsal.json
```

That rehearsal completes `case-501`; it does not leave a fresh manual exercise. After preserving results, stop writers and clear only disposable lab workflow history for the manual session. This removes all history in the shared Temporal lab volume, including W4 history. Run only when that loss is intended:

```bash
docker compose --profile w3 stop worker temporal
./scripts/workshop reset w3 --yes
docker compose --profile w3 run --rm --no-deps --entrypoint python temporal -c 'from pathlib import Path; [p.unlink(missing_ok=True) for p in Path("/data").glob("temporal.sqlite*")]'
docker compose --profile w3 start temporal worker
./scripts/workshop status
```

Check worker logs for successful Kafka/Temporal connection. Bank reset alone leaves the old workflow and cannot restart a completed case. Do not delete volumes during the timed demo. The duplicate event experiment later keeps history intact.

CLI defaults are Kafka `localhost:9092` and Temporal `localhost:7233`. For a different Temporal port, add `--temporal localhost:<port>` to query/approval commands. Kafka port changes require matching advertised listener configuration.

Prepare local snapshots using the synthetic lab key. These GET requests are read-only and traverse Gate 3:

```bash
curl --fail --silent --show-error --max-time 10 -H 'X-API-Key: gate3-secret-token' http://127.0.0.1:9080/api/v1/cases/case-501 > .presenter-private/w3/live-evidence/case-before.json
curl --fail --silent --show-error --max-time 10 -H 'X-API-Key: gate3-secret-token' http://127.0.0.1:9080/api/v1/payments > .presenter-private/w3/live-evidence/payments-before.json
```

Verify no existing `settle-dispute-case-501` payment. Inspect the snapshot rather than assuming a fresh seed. Profile verification and earlier demos can create unrelated payments.

## A · Inspect the case · minutes 0–6

Display `case-before.json`: `case-501`, `cust-8801`, status `open`, unapproved-charge claim. Say: “The resolver can investigate and propose. Who owns the state while a reviewer is absent?”

The claimed charge is free text. The replay proposal is ₹750; it is not a computed refund of the claimed 45000 INR charge. Keep the fixture rationale separate from verified facts.

## B · Assign state ownership · minutes 6–13

Show `src/worker/kafka_consumer.py`, `src/worker/workflow.py` and `src/worker/activities.py` in that order. Kafka delivers events at least once. Temporal owns durable history and pending review. LangGraph performs reasoning/tool I/O inside an activity. Core Banking owns payment idempotency.

Point to the stable workflow ID `dispute-case-case-501` and offset commit after successful workflow start or confirmation that it already exists. Ask: “What if we commit before starting the workflow?” Explain the possible event-loss window. This lab's duplicate event uses the same case ID; it does not demonstrate every partition/rebalance failure.

## C · Start and pause · minutes 13–23

```bash
.venv/bin/python workshops/w3/client.py emit --case-id case-501 --customer-id cust-8801
.venv/bin/python workshops/w3/client.py query --case-id case-501
```

Query again while processing; inspect `current_phase` and `proposal`. Expected: `WAITING_FOR_APPROVAL`, amount `75000`, recorded mode/graph/tool results. Save the pending query:

```bash
.venv/bin/python workshops/w3/client.py query --case-id case-501 > .presenter-private/w3/live-evidence/pending-before.txt
```

Say: “The request that started this work has ended. The review wait belongs to the workflow.” Read the payment list again and confirm no settlement under the stable key. “Verified duplicate debit” in the replay rationale is model fixture text; the available account read is not transaction proof.

## D · Worker failure and duplicate event · minutes 23–35

Ask: “Will restart forget the proposal or create a second workflow?” For an actual abrupt worker termination use the Compose service name:

```bash
docker compose --profile w3 kill -s SIGKILL worker
.venv/bin/python workshops/w3/client.py emit --case-id case-501 --customer-id cust-8801
docker compose --profile w3 start worker
.venv/bin/python workshops/w3/client.py query --case-id case-501
```

Wait for worker reconnection, then query again. Expected: same workflow ID, same pending proposal and `WAITING_FOR_APPROVAL`. Inspect `docker compose logs --tail 100 worker` for duplicate-workflow reuse and offset commit. A query while the worker is down can fail because it needs a worker to answer; that alone does not indicate lost history.

The worksheet uses `stop`/`start`, a graceful interruption. Label the method actually used. Keep Temporal and Kafka running in both cases. Inspect history in preparation rather than relying on a Temporal UI: this Compose stack provides the Temporal server without a dedicated UI service.

## E · Approve and inspect one settlement · minutes 35–41

Review the proposal before signalling. The following is fictional lab approval, not evidence that a real refund entitlement was established:

```bash
.venv/bin/python workshops/w3/client.py approve --case-id case-501 --reviewer ops-lead --comments "Approved the synthetic replay proposal for this lab" > .presenter-private/w3/live-evidence/approval-result.txt
curl --fail --silent --show-error --max-time 10 -H 'X-API-Key: gate3-secret-token' http://127.0.0.1:9080/api/v1/payments > .presenter-private/w3/live-evidence/payments-after.json
curl --fail --silent --show-error --max-time 10 -H 'X-API-Key: gate3-secret-token' http://127.0.0.1:9080/api/v1/cases/case-501 > .presenter-private/w3/live-evidence/case-after.json
```

Inspect the approval result and snapshots. Expected case `resolved`, workflow `COMPLETED`, one settlement with key `settle-dispute-case-501`, amount 75,000 paise, source `acc-102`, and the proposal's destination. Compare counts with the before snapshot; unrelated seeded payments do not count as duplicates.

```bash
.venv/bin/python - <<'PY_PAYMENT'
import json
from pathlib import Path
folder = Path('.presenter-private/w3/live-evidence')
before = json.loads((folder / 'payments-before.json').read_text())
after = json.loads((folder / 'payments-after.json').read_text())
assert isinstance(before, list) and isinstance(after, list), 'Inspect unexpected API response shape'
key = 'settle-dispute-case-501'
old = [p for p in before if p.get('idempotency_key') == key]
new = [p for p in after if p.get('idempotency_key') == key]
assert len(old) == 0 and len(new) == 1, (old, new)
assert new[0]['amount'] == 75000, new
print(json.dumps(new[0], indent=2))
print('Observed one new settlement for the case')
PY_PAYMENT
```

Stable workflow identity prevents duplicate starts; stable backend keys protect retried payment effects. The demonstration supports this selected failure path. It does not establish exactly-once delivery for the whole distributed system. Reviewer names in the W3 CLI are supplied labels; W4 demonstrates independent reviewer authorization. `notification_sent` in the result is a lab marker, not evidence of an external message delivery.

## F · Wrap and bridge · minutes 41–45

Ask participants to assign ownership of event delivery, reasoning, pending review and financial effects. The workflow has a 24-hour approval timeout. A longer queue needs a changed timeout and designed expiry handling.

Say: “We preserved a proposal across worker failure and prevented duplicate settlement for this case. Next we will test identity, delegation and exact approvals under attack.” Reserve two minutes for questions.

## Recovery, fallback and exit

At most 60 seconds per failed step. Restore the worker first. If a workflow already completed, keep the actual result visible and use historical evidence; clearing history is preparation work. For `INVESTIGATION_FAILED`, inspect the actual error and do not signal approval as a workaround. If approval hangs or payment status is uncertain, inspect workflow and bank records before further action; do not reset to hide uncertainty.

Fallback: [2026-10-05 replay evidence](../../workshops/w3/evidence/rehearsal-replay-2026-10-05.json), [live example](../../workshops/w3/evidence/rehearsal-live-2026-10-04T090416Z.json), and [dated caveats](../../docs/workshops/rehearsal-2026-10-05.md). Say “This is an earlier recorded run” and retain the original mode/date. Optional case-502 rejection includes an `acc-8802` 404; show that error and zero settlement rather than claiming a successful investigation.

At minute 23 begin recovery; at 35 begin approval; at 41 close. If behind, shorten code browsing and omit the alternate rejection ending. Preserve pending review, restart/redelivery and the payment evidence.

Before delivery sign-off, record date, machine, actual 45-minute spoken duration, before/after workflow ID and proposal, crash method, payment key/count/ID and final case status. Export evidence before resetting for another session.
