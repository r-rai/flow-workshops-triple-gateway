# NovaBank implementation audit — 2026-10-03

The implementation does **not** meet the handoff's “Implementation Complete & Verified” claim. All seven package commits exist, all four profile verification scripts have passing fresh runs after readiness, and several important controls work. However, the unchanged W2 rehearsal fails reproducibly, multiple security invariants fail under direct probes, and measured active memory exceeds 750 MB.

Audited branch: `feat/implement-novabank-platform`. Implementation endpoint: `e8c4678`; current HEAD: `6003764bcacdeaabcb8dfc804e5cdab81f452521`, whose only change is the handoff document. Evidence is in [2026-10-03-novabank-evidence](2026-10-03-novabank-evidence/). These results are an audit of the existing code; no implementation fixes were made.

**Git history and package traceability**

| Package | Commit | Inspected scope |
|---|---|---|
| 1 | `cde4fb2` | Compatibility spikes and report |
| 2 | `eff6cde` | API, models, persistence, seed, adapter, Compose, CLI, tests |
| 3 | `957e19e` | W1 contracts, client, rehearsal, worksheets |
| 4 | `eec932a` | W2 policy checkpoints, rehearsal, worksheets |
| 5 | `ae54353` | Kafka, Temporal, worker, W3 rehearsal and worksheets |
| 6 | `a44dffc` | Agent helpers, A2A routes, W4 rehearsal and worksheets |
| 7 | `e8c4678` | Release manifest and facilitator guide |

The seven commits are consecutive in the expected order above base `2bcc587`, which is also local `main`. The local remote-tracking feature ref equals HEAD; the live remote was not fetched. The working tree was clean before testing. A limited scan of 105 changed historical file versions found no common GitHub/OpenAI/AWS credential formats or private-key headers. This is not a comprehensive secret-scan guarantee. Published synthetic lab keys and a shared JWT signing secret do exist. Only `.env.example` is tracked among environment files. See [history-audit.json](2026-10-03-novabank-evidence/history-audit.json).

**Fresh verification and rehearsal outputs**

Commands were run sequentially with one active profile: `./scripts/workshop switch wN`, a lab reset, `./scripts/workshop verify wN`, and `.venv/bin/python workshops/wN/rehearsal_wN.py`. Rehearsals are compressed automated checks, not measurements of actual 45/135-minute participant sessions.

| Profile | `verify` | Unchanged rehearsal | Fresh saved evidence |
|---|---|---|---|
| W1 | First run: exit 1, MCP initialization HTTP 500. Recheck after API readiness: exit 0. | Exit 0, 1.62 seconds process time. | Yes: `w1-rehearsal-evidence.json`. |
| W2 | Exit 0 on initial and subsequent runs. | Exit 1 twice, 14.07 / 14.73 seconds. Downstream case read returned HTTP 502; assertion at line 60 failed. | No from either unchanged run. |
| W3 | Exit 0. | Exit 0, 35.56 seconds. Worker stop/start, duplicate dispatch, approval, one settlement. | Yes: `w3-rehearsal-evidence.json`. |
| W4 | Exit 0, including final verification after restoring W4. | Exit 0, 1.52 seconds. | Yes: `w4-rehearsal-evidence.json`. |

The original W2 failure leaves the old checked-in evidence in place. A separately labelled audit harness waits for `/api/v1/accounts/acc-101` to return 200 after the rehearsal's internal switch. With that guard, the W2 body passed, saved fresh evidence, and returned `POLICY_TIMEOUT_FAIL_CLOSED` during OPA pause. This harness result **does not** establish that the unchanged W2 runner executes cleanly.

The API foundation suite also returned `9 passed, 2 warnings in 1.69s`. Preflight returned exit 0. Full outputs and exit codes are preserved in [profile-results.json](2026-10-03-novabank-evidence/profile-results.json), [startup-results.json](2026-10-03-novabank-evidence/startup-results.json), the corresponding `.log` files, and [foundation-tests.log](2026-10-03-novabank-evidence/foundation-tests.log).

Representative outputs:

```text
W1 initial: AssertionError: MCP init failed: 500
W1 recheck: Profile w1 Verification Complete: ALL CHECKS PASSED
W2 unchanged: <h1>502 Bad Gateway</h1>; AssertionError at rehearsal_w2.py:60
W2 guarded: POLICY_DENIED ... POLICY_TIMEOUT_FAIL_CLOSED
W3: Workflow state preserved ... Settlement payments ...: 1
W4: Wrong audience HTTP 401; insufficient scope HTTP 403
```

**Security and correctness findings — release blockers**

1. **High: atomic single-use approval consumption fails on the deployed SQLite backend.** `src/services/banking.py:56–92` relies on `with_for_update()`. The live API uses SQLite, whose compiled SQL omits `FOR UPDATE`. In an isolated SQLite database, two synchronized executions of the same approved proposal, using distinct idempotency keys, both succeeded. Two payment records were inserted, while the balance fell only once from 8,500,000 to 8,350,000 minor units: a duplicate execution plus a lost update. The W4 rehearsal checks sequential replay only. Use a transaction/conditional state transition and balance update that are atomic on the supported backend, or deploy PostgreSQL with effective locking; add a concurrent regression test. Evidence: [isolated-probes.json](2026-10-03-novabank-evidence/isolated-probes.json).

2. **High: the W1 static-key admin fallback bypasses W4 anti-self-approval.** `src/core/security.py:48–58` accepts the shared lab key as `w1-lab-operator`, role `admin`, in every profile. Both agent helpers possess this key. A payment agent's self-approval with its Bearer token returned 403; removing that token and sending its existing key approved the same proposal with HTTP 200 as `w1-lab-operator`. The subject/role checks in `src/services/approvals.py:91–105` work only while the agent retains its restricted credential. Restrict the bootstrap fallback to its intended profile and keep privileged approval credentials separate from agent credentials. Evidence: [final-security-probes.json](2026-10-03-novabank-evidence/final-security-probes.json).

3. **High: A2A task mutation is not owner-scoped.** `src/api/routes/a2a.py:83–88` rejects foreign reads, but `complete_a2a_task` at lines 92–104 checks only `api:payments:write`. A foreign payment-scoped agent received 403 on GET, then 200 on POST `/complete`, and overwrote the owner's task output. Task creation also accepted a viewer token with no A2A scope. Apply owner/delegation authorization and required scopes to every task operation, including state transitions. Evidence: [security-probes.json](2026-10-03-novabank-evidence/security-probes.json).

4. **High: lowering payment amount bypasses proposal argument binding and consumption.** `src/services/banking.py:64` runs all proposal validation only when `amount > 100000`. A 150,000-unit approved proposal rejected a tampered 200,000-unit request with 400, but accepted a 1,000-unit request with a changed beneficiary with 200. The payment referenced that proposal, which remained `approved`. Whenever a proposal ID is supplied, validate its exact arguments, status, expiry, and authorization and consume it atomically regardless of the execution amount. Evidence: [security-probes.json](2026-10-03-novabank-evidence/security-probes.json).

5. **High: unexpected OPA decisions fall through to execution.** OPA timeout and unavailable-policy paths deny correctly, but `src/adapter/server.py:196–227` only handles the exact values `deny` and `approval_required`; every other value reaches the downstream branch. A mocked OPA HTTP 200 response with `decision: unexpected` caused a downstream payment POST. This was an isolated transport test, not a live OPA policy change or real debit. Execute only on an explicitly validated `allow` decision; reject null, unknown, malformed, and incomplete policy results. Evidence: [isolated-probes.json](2026-10-03-novabank-evidence/isolated-probes.json).

6. **High: a transient Temporal workflow-start failure can lose a Kafka event.** At `src/worker/kafka_consumer.py:87–93`, failure continues to the next fetched message. The consumer position advances; a later successful message invokes a broad `consumer.commit()`, committing past the failed message. A mocked sequence where offset 10 failed and offset 11 succeeded committed next offset 12, with no workflow for offset 10. Retry the failed message before advancing or seek/pause its partition and commit only safely handled offsets. Evidence: [kafka-offset-probe.json](2026-10-03-novabank-evidence/kafka-offset-probe.json).

7. **High: the private lab boundary is not enforced by published port bindings.** APISIX, Kafka, Temporal, and Jaeger are published on all host interfaces, not `127.0.0.1` (`docker-compose.yml:23–24, 138–139, 158–159, 176–177`). Kafka is PLAINTEXT and the Temporal development server accepted SDK operations without authentication; `human_approval` trusts a caller-provided dictionary (`src/worker/workflow.py:32–34`). Bind presenter/local services to loopback or enforce the intended authenticated private access path. Docker binding exposure is verified; reachability from the public Internet through external firewall rules was not tested.

**Additional implementation and delivery gaps**

8. **Approval-required responses do not persist a proposal.** `src/adapter/server.py:206–224` fabricates a timestamp ID and says “Proposal recorded” without a backend write. GET `/api/v1/approvals/{returned_id}` returned 404. The W2 rehearsal checks the response string only. Persist the proposal through the real approval service and assert durable lookup and unchanged financial state.

9. **Audience separation passes, but live RFC 8693 exchange is absent and identity checks are incomplete.** Wrong-audience API tokens returned 401 and missing payment scope returned 403. However, the adapter locally signs a JWT (`src/adapter/server.py:89–108`) rather than invoking a token-exchange endpoint; `/oauth/token`, advertised by the Agent Card, returned 404. No Keycloak service is packaged. RFC 8693 defines a token-endpoint request/response protocol; local JWT minting alone does not verify that protocol ([RFC 8693 §2](https://www.rfc-editor.org/rfc/rfc8693.html#section-2)). API and adapter JWT decoders omit expected-issuer validation; a signed token with an unrelated issuer was accepted by the API. An MCP token with no `mcp:tools` scope was also allowed to read. Align issuer generation/verification, require relevant claims and scopes, implement live exchange or label the simplification consistently, and remove nonfunctional discovery URLs. Evidence: [security-probes.json](2026-10-03-novabank-evidence/security-probes.json).

10. **Startup readiness is too weak and failure handling overstates success.** `scripts/workshop:180–197` tests MCP `initialize`, which can succeed before the backend is available; it also returns success after readiness timeout. W2 immediately invokes a backend tool after switching. Its second unmodified failure was corroborated by APISIX `connect() failed (111: Connection refused)` to backend port 8000. Wait for every required dependency and a real downstream operation, propagate switch failures, and fail the start command on timeout. W1 passed after a downstream readiness wait; the exact first-run W1 HTTP 500 cause was not captured before its container was replaced, so its mechanism is less certain than W2's.

11. **“All contracts verified” exceeds rehearsal coverage.** W1 discovers 20 broad tools and never loads the curated OpenAPI checkpoint or proves excluded tools uncallable. W4's purported OPA attack lacks `beneficiary` and authentication, so it is rejected by argument validation before OPA. Its concurrency check is sequential; its A2A check exercises reads only. It queries Jaeger service names without asserting a shared trace or required spans; the saved W4 run had `traced_services: null`, and a later query showed only Jaeger and the API. Full trace stitching is not verified by this implementation rehearsal. W3 stops the worker gracefully rather than killing it, and deletes Temporal's database at its initial reset; this is not a server-recovery test. Destructive workflow resets should be explicit and performed safely with the service stopped.

12. **Several delivery-plan capabilities are simplified or missing.** Gate 1 always produces a constructed replay response; it does not consume `USE_REPLAY_FIXTURES` or implement live-provider fallback or inference budgets. W3 diagnosis is ordinary hardcoded Python described as simulating LangGraph; it is a case-dispute settlement rather than the delivery plan's incident-remediation workflow. A2A submission creates an in-memory dictionary entry; no PaymentsAgent dispatch processes it or binds completion to a real approved payment. The task registry disappears on API restart. Rejecting proposals also lacks a role/owner check (`src/services/approvals.py:117–132`): a no-scope viewer rejected another caller's pending proposal with 200. Reconcile the approved scope with delivered behavior before declaring package completion.

**Positive security evidence and its limits**

| Invariant | Audit result |
|---|---|
| Gate 3 loopback / isolation | W1 generated calls and curated adapter calls route through APISIX; invalid-key calls fail. API has no published port; direct adapter-to-backend TCP access failed. However, backend networks have `internal: false`; the worker joins the backend network and directly accesses `api:8000` with HTTP 200. Its activities actually use this direct URL, bypassing APISIX. The broad claim that all tool/workflow API access re-enters Gate 3 is false. |
| OPA fail-closed | Live paused-OPA payment request denied with `POLICY_TIMEOUT_FAIL_CLOSED`; account balance and payment count stayed unchanged. Unexpected decisions fail open in the isolated probe. |
| Audience / API scope | Wrong audience 401; missing payment-write scope 403. Issuer/MCP-scope and exchange-protocol gaps remain. |
| Anti-self-approval | Restricted Bearer self-approval 403; shared-key admin fallback bypass 200. |
| Argument tampering | Above-threshold tamper 400; below-threshold tamper 200. |
| Single-use approval | Sequential consumed-proposal reuse 400; concurrent SQLite execution succeeds twice. |
| Temporal durability | Supplemental live test preserved `WAITING_FOR_APPROVAL` after worker SIGKILL and Temporal server restart with the existing volume. Rejection created no payment. Completed Kafka redelivery retained the original workflow run ID and created no payment. Transient-start offset handling remains defective. |
| A2A isolation | Foreign read 403; foreign completion 200. |

The supplemental Temporal test saved a 29-event history and before/after status. Payment counts were `2 → 2 → 2` through rejection and completed-event redelivery. See [durability-probe.json](2026-10-03-novabank-evidence/durability-probe.json) and [durability-history.json](2026-10-03-novabank-evidence/durability-history.json). This verifies short crash recovery, not multi-week availability. It does not establish atomic business effects under concurrent calls.

The payment listing itself misrepresents idempotency evidence: `src/api/routes/payments.py:59` assigns `settle-dispute-case-501` to every `pay-` payment when its lookup fails. W3's one-payment filter therefore is not a reliable key-to-payment mapping. Return the stored association rather than a fabricated label and verify balances, payment IDs, and idempotency records directly.

**Memory containment and release reproducibility**

Memory is reported in decimal MB; Docker's binary MiB values were converted. These are sampled active working sets from `docker stats`, not container memory caps, full-duration load benchmarks, or total host RAM.

| Measurement | Active memory | `< 750 MB` |
|---|---:|---|
| W1 snapshot, 2 containers | 193.14 MB | Pass at snapshot |
| W2 snapshot, 6 containers | 258.73 MB | Pass at snapshot |
| W3 snapshot, 9 containers | 815.03 MB | **Fail** |
| W4 early snapshot, 9 containers | 740.98 MB | Pass only at that snapshot |
| W4 maximum of 80 samples during audit activity | **951.02 MB / 906.97 MiB** | **Fail** |

At the W4 sampled peak, Kafka alone used about 480.88 MB. The `<750 MB` requirement fails even if interpreted as 750 MiB. Container limits are applied, but there is no aggregate 750 MB limit or memory assertion in verification. Host memory pressure remained below the broader 6 GB operating budget in observed snapshots; available host RAM was approximately 5.3–5.6 GiB during this audit, not the handoff's claimed >6.3 GB free. Some swap was already in use. Sustained load, two fallback runs, and all startup peaks were not benchmarked. See [memory-summary.json](2026-10-03-novabank-evidence/memory-summary.json) and [memory-samples.jsonl](2026-10-03-novabank-evidence/memory-samples.jsonl).

All five installed third-party image repository digests match the manifest. However, Compose uses mutable tags, and `scripts/workshop pull` never uses or validates manifest digests and ignores pull failures. Consequently the manifest does not pin a future installation. Pin actual Compose image references and validate the built-image/dependency coordinates. See [image-digests.json](2026-10-03-novabank-evidence/image-digests.json).

**Existing VPS services**

Before/after Docker inspection confirmed exactly the same container IDs, start times, restart counts, and running states for `caddy`, `portainer`, `uptime-kuma`, and `dozzle`. Uptime Kuma remained healthy. Direct HTTP checks returned Caddy 308, Portainer `/api/status` 200, Uptime Kuma 302 to `/dashboard`, and Dozzle 200. These observations support that the services were unharmed by this audit; they cannot prove their entire prior deployment history. Initial checks through the host's Caddy-facing ports returned 400 and are preserved separately, not counted as successful application checks.

Evidence: [protected-services-before.json](2026-10-03-novabank-evidence/protected-services-before.json), [protected-services-after.json](2026-10-03-novabank-evidence/protected-services-after.json), and [protected-services-direct-http.json](2026-10-03-novabank-evidence/protected-services-direct-http.json).

**Windows 11 / WSL2 benchmark**

The manifest, handoff, facilitator guide, and compatibility report explicitly label the Windows 11 / WSL2 5 GB benchmark **unverified**. None of those references claims that Linux measurements prove the Windows benchmark. That accounting is correct. The approximately 700 MB Linux “peak” quoted in their explanations is inconsistent with this fresh audit and should be updated independently of the still-unverified Windows status. No Windows/WSL2 hardware or participant benchmark was available here.

**Recommended next steps**

Resolve findings 1–7 before using this platform to demonstrate enforced security invariants. Then persist real MCP proposals, correct identity/exchange handling, fix readiness and offset handling, and replace permissive rehearsal assertions with meaningful state and concurrent checks. Make the intended checkpoints executable, connect A2A dispatch to actual execution, and verify correlated traces. Enforce deployment image digests and either meet the 750 MB target or explicitly revise it with measured evidence. Run the outstanding Windows/WSL2 and sustained-session benchmarks before participant delivery.

W4 was restored as the active profile and its final smoke test passed. Rehearsals intentionally reset synthetic lab data, and the W3 runner reset Temporal history. Pre-audit runtime copies are retained at `/tmp/novabank-audit-20261003/runtime-backup`; these are raw live file copies, not a validated restore set. Original tracked rehearsal evidence was restored after copying fresh results into the audit evidence directory. Only new audit artifacts were added to the repository; implementation files and existing services were not changed.
