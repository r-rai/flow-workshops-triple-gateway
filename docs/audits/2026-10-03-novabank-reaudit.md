# NovaBank implementation re-audit — 2026-10-03

**Verdict: the requested smoke suites and rehearsals pass, but the claim that all audit findings are resolved is not supported.** Token exchange remains both nonfunctional for ordinary issued tokens and insufficiently authorized for other accepted tokens. Proposal persistence still reports false success on backend failure. A new worker regression breaks rejected settlements. Deployment digest enforcement and several original delivery/rehearsal gaps remain open.

Reviewed branch `feat/implement-novabank-platform`, HEAD `17f0b02a98d6e0d1d3c708ff3f9cc0a4e88e588c`, on the Linux VPS. Fresh logs, probe scripts, JSON results, and memory samples are in [the re-audit evidence directory](2026-10-03-novabank-reaudit-evidence/). Implementation files were not modified.

**Findings requiring follow-up, in priority order**

1. **High — token exchange grants payment scope without validating the caller's entitlement.** In [oauth.py](../../src/api/routes/oauth.py), lines 73–91, `granted_scopes` is read but never used. Requested scopes are filtered against a global vocabulary; there is no role/subject-to-target permission mapping. A synthetic issuer-signed viewer token with only `api:accounts:read` and no `aud` claim received HTTP 200 and an exchanged token containing `api:payments:write`. The same principal's payment-list request changed from **403 before exchange to 200 after exchange**. No live debit was performed. The source token was deliberately signed using the workshop issuer; this does not demonstrate signature forgery or exploitation with an unsigned token. Reject incomplete subject tokens and authorize target audience/scopes using an explicit entitlement mapping. Preserve delegation context rather than replacing it unconditionally. Evidence: [live-readonly-probes.json](2026-10-03-novabank-reaudit-evidence/live-readonly-probes.json).

2. **High — the advertised RFC 8693 exchange does not work for normal workshop tokens.** [oauth.py](../../src/api/routes/oauth.py), lines 41 and 61–66, has two independent defects. Form requests return **500** because the built API image lacks `python-multipart`. JSON requests with an ordinary `novabank-mcp` audience token return **401, `Invalid subject token: Invalid audience`**: `python-jose` validates an existing `aud` claim, but this decoder supplies no expected audience. Both token paths were checked; a repeated request to `/oauth/token` reproduced 401. One intervening request returned 502 after the form exception; it is preserved, not counted as the stable failure. Missing and unsupported `subject_token_type` values were also accepted with 200 for the audience-less test token. RFC 8693 specifies form encoding and requires this parameter ([§2.1](https://www.rfc-editor.org/rfc/rfc8693.html#section-2.1)). Meanwhile [server.py](../../src/adapter/server.py), lines 101–139, silently falls back to local signing when exchange fails, so passing tool calls and W4 rehearsals do not prove exchange. Package the form parser, validate supported input audiences and required fields, enforce exchange authorization, and test the actual exchange path without that fallback. Evidence: [live probes](2026-10-03-novabank-reaudit-evidence/live-readonly-probes.json), [JSON recheck](2026-10-03-novabank-reaudit-evidence/oauth-json-recheck.json), and [API errors](2026-10-03-novabank-reaudit-evidence/api-token-errors.log).

3. **High — rejected W3 settlements raise `NameError`.** [activities.py](../../src/worker/activities.py), line 115, still references `api_url`, although commit `17f0b02` renamed the local variable to `gate3_url`. Calling the rejection activity with `approved=False` reproduced **`NameError: name 'api_url' is not defined`** before a downstream request. A rejected workflow therefore cannot complete this activity normally. The passing W3 runner exercises approval only. Correct the rejection URL and add a rejected-workflow check that verifies final case state and unchanged payments. Evidence: [isolated-probes.json](2026-10-03-novabank-reaudit-evidence/isolated-probes.json).

4. **Medium — failed proposal persistence still fabricates success.** [server.py](../../src/adapter/server.py), lines 254–282, creates real proposals on the healthy path, but fabricates `prop-<timestamp>` if the backend write fails. With an injected backend HTTP 503, the adapter returned `isError: false`, `APPROVAL_REQUIRED`, and **“Proposal recorded.”** No durable proposal existed in that mocked backend. Return an explicit persistence error and require a verified proposal ID before reporting recorded state. Evidence: [isolated probes](2026-10-03-novabank-reaudit-evidence/isolated-probes.json).

5. **Medium — the manifest records digests but does not enforce reproducible deployment.** All five installed third-party repository digests match [manifest.json](../../config/manifest.json). However, [docker-compose.yml](../../docker-compose.yml) still references mutable tags, and [scripts/workshop](../../scripts/workshop) does not validate manifest digests and ignores pull failures. The four built images have tags/Dockerfiles, not pinned digests; their Python requirements use lower bounds. The handoff's claim that all nine image digests are pinned is false. Use immutable deployment references and locked build dependencies, and propagate pull/validation failures. Evidence: `third_party_image_digests` in [live probes](2026-10-03-novabank-reaudit-evidence/live-readonly-probes.json).

6. **Medium — the original rehearsal and delivery-scope findings are only partly addressed.** W1 still exercises the broad 20-tool catalog without loading the curated checkpoint or proving excluded tools uncallable. Gate 1 constructs a replay response; it implements neither live-provider fallback nor inference budgets and does not consume `USE_REPLAY_FIXTURES`. W3 still uses hardcoded diagnosis described as simulating LangGraph, gracefully stops the worker, and deletes Temporal history at setup. A2A tasks now persist, but task submission still does not dispatch a PaymentsAgent or bind completion to an approved payment. W4 checks Jaeger service names, not a common trace with required spans; its fresh evidence contained only `novabank-api`. API logs also contain telemetry export 404s. These remaining parts of original findings 11–12 prevent a blanket “all contracts verified” conclusion. Implement or explicitly narrow these promised capabilities and make the rehearsal assertions prove them.

**Git traceability**

The initial working tree was clean. HEAD and the local `origin/feat/implement-novabank-platform` tracking reference both resolve to `17f0b02`; `main` resolves to `2bcc587`. There are nine branch commits: seven package commits, one handoff documentation commit, and the remediation commit. The package sequence is:

```text
cde4fb2  Package 1: compatibility spikes
eff6cde  Package 2: foundation
957e19e  Package 3: W1
eec932a  Package 4: W2
ae54353  Package 5: W3
a44dffc  Package 6: W4
e8c4678  Package 7: delivery
6003764  Handoff documentation
17f0b02  Audit remediations
```

The eight sampled security/worker source files in running images exactly match their checked-out SHA-256 hashes. No remote fetch was performed; local history cannot prove historical force-push behavior. Evidence: [history.json](2026-10-03-novabank-reaudit-evidence/history.json), [history.log](2026-10-03-novabank-reaudit-evidence/history.log), and `runtime_source_checks` in the live probes.

**Fresh verification outputs**

All commands below ran on their corresponding active profile, with seeded synthetic data. Times are wall-clock command durations, including runner setup; the labelled workshop segments are accelerated checks, not full-length participant sessions.

| Profile | `./scripts/workshop verify <profile>` | `.venv/bin/python workshops/<profile>/rehearsal_<profile>.py` | Fresh logs |
|---|---|---|---|
| W1 | Exit 0; all checks passed; 0.32 s | Exit 0; 0.62 s | [verify](2026-10-03-novabank-reaudit-evidence/w1-verify.log), [rehearsal](2026-10-03-novabank-reaudit-evidence/w1-rehearsal.log) |
| W2 | Exit 0; all checks passed; 0.52 s | Exit 0; 18.10 s | [verify](2026-10-03-novabank-reaudit-evidence/w2-verify.log), [rehearsal](2026-10-03-novabank-reaudit-evidence/w2-rehearsal.log) |
| W3 | Exit 0; all checks passed; 0.32 s | Exit 0; 22.62 s | [verify](2026-10-03-novabank-reaudit-evidence/w3-verify.log), [rehearsal](2026-10-03-novabank-reaudit-evidence/w3-rehearsal.log) |
| W4 | Exit 0; all checks passed; 0.82 s | Exit 0; 2.03 s | [verify](2026-10-03-novabank-reaudit-evidence/w4-verify.log), [rehearsal](2026-10-03-novabank-reaudit-evidence/w4-rehearsal.log) |

Preflight and all four profile switches exited 0. Existing foundation tests reported **9 passed, 2 deprecation warnings** in 1.31 s ([output](2026-10-03-novabank-reaudit-evidence/foundation-tests.log)). Command exit codes and durations are saved in [results.json](2026-10-03-novabank-reaudit-evidence/results.json).

**The twelve handoff remediations, checked individually**

This numbering follows the handoff's remediation summary, which reorganizes the original audit findings.

| # | Remediation | Re-audit result |
|---|---|---|
| 1 | Atomic consumption and balance debit | **Pass.** Live W4 returned `[200, 409]`. Post-run SQLite held one payment, a consumed proposal, and exactly one 150,000-unit debit (`8,500,000 → 8,350,000`). A forced two-reader SQLite race independently returned `[200, 409]`; two separate concurrent 50,000-unit payments both succeeded and deducted 100,000 in total. |
| 2 | Static-key/self-approval rejection | **Pass.** Bearer self-approval and static-key approval both returned 403; an authorized manager approved successfully. |
| 3 | A2A persistence and isolation | **Pass for the specified controls.** Viewer creation, foreign read, and foreign completion returned 403. The fresh delegated task exists in SQLite; an original backed-up task was readable with its owner's token after API restart/restoration. Actual agent dispatch remains absent. |
| 4 | Below-threshold argument binding | **Pass.** Changed amount/beneficiary below threshold returned 400, as did above-threshold tampering. |
| 5 | OPA strict decisions | **Pass.** Only exact `allow` reached the downstream read in isolated probes. `deny`, unexpected strings, null, uppercase `ALLOW`, empty strings, dictionaries, and lists did not. Live paused-OPA calls returned `POLICY_TIMEOUT_FAIL_CLOSED`. |
| 6 | Kafka retries and rewind | **Pass in isolated fault probes.** Transient failure retried offset 10 before committing 11. Ten failed starts sought back to 10, reread it, then safely committed 11/12 after recovery. The stop-after-exhaustion case committed nothing. W3 live redelivery also passed. This is not a live broker/Temporal outage benchmark. |
| 7 | Loopback ports and worker Gate 3 | **Pass.** Runtime ports 9080/16686/7233/9092 all bind to `127.0.0.1`. Worker joins workflow/capability networks only; `api:8000` name resolution failed, while APISIX connection and authenticated Gate 3 account read succeeded. |
| 8 | Real MCP proposals | **Partial.** Fresh W2 verified a durable pending proposal by backend lookup. Failure still produces a fake ID and false recorded-state message, as finding 4 shows. |
| 9 | Live RFC 8693 exchange | **Fail.** Standard form request 500; normal JWT JSON exchange 401; accepted audience-less viewer tokens can gain payment scope. Tool calls hide failure through local signing. |
| 10 | Startup readiness/W2 502 | **Pass for reproduced profile transitions.** CLI checks downstream account access and MCP initialization and exits nonzero on readiness timeout. W2 verify and its independently switching rehearsal passed with no startup 502. A later adapter stop/start produced a transient stale-upstream 502 during restoration; see operational limits below. |
| 11 | Memory accounting | **Pass for sampled containment and corrected historic units.** Historical 951.02 MB/906.97 MiB is independently reproduced from saved samples; fresh maximum was 914.47 MB/872.11 MiB. Neither is a sustained-load maximum. |
| 12 | Image pinning | **Partial.** Five installed digests match; mutable deployment tags and four unpinned built images remain. |

Evidence: [W4 log](2026-10-03-novabank-reaudit-evidence/w4-rehearsal.log), [post-rehearsal SQLite checks](2026-10-03-novabank-reaudit-evidence/post-rehearsal-db-checks.json), [isolated probes](2026-10-03-novabank-reaudit-evidence/isolated-probes.json), and [live probes](2026-10-03-novabank-reaudit-evidence/live-readonly-probes.json).

**Memory, protected services, and Windows accounting**

Seventy fresh Docker samples were recorded across audit activity, profile transitions, and restoration. The sampled maximum across nine containers was **914,470,470 bytes = 914.47 decimal MB = 872.11 MiB**. Recomputing the previous 80 samples gives **951,021,733 bytes = 951.02 MB = 906.97 MiB**, matching the updated manifest. All nine runtime memory limits are applied and total **3 GiB**. Observed workshop usage preserves the 6 GB operating budget. At the fresh peak, host `MemAvailable` was approximately 5.89 decimal GB, so a blanket “>6 GB free” assertion remains unsupported. Existing swap usage was about 80 MiB. These observations do not prove sustained sessions, every startup transient, two fallback runs, or the earlier `<750 MB` target; the previous 951 MB evidence exceeds that target. Evidence: [memory-summary.json](2026-10-03-novabank-reaudit-evidence/memory-summary.json) and [raw samples](2026-10-03-novabank-reaudit-evidence/memory-samples.jsonl).

`caddy`, `portainer`, `uptime-kuma`, and `dozzle` retain identical container IDs, start times, restart counts, running states, and health across the audit. Direct HTTP checks returned **308, 200, 302, and 200**, respectively; Uptime Kuma remains healthy. They were not stopped, restarted, or changed. Evidence: [before](2026-10-03-novabank-reaudit-evidence/protected-before.json), [after](2026-10-03-novabank-reaudit-evidence/protected-after.json), and [HTTP checks](2026-10-03-novabank-reaudit-evidence/protected-direct-http.json).

The manifest, handoff, facilitator guide, and compatibility report explicitly mark the **Windows 11 / WSL2 5 GB RAM benchmark unverified**. That distinction is accurate; this Linux audit supplies no Windows benchmark. Test capped native Windows participant hardware before claiming compatibility. Also reconcile the delivery plan's stale “applications ... not implemented yet” status and the compatibility report's still-future Keycloak packaging statement with the delivered lab issuer.

**Audit state and operational limits**

Fresh rehearsal JSON was copied to this evidence directory; original tracked evidence was restored. Before rehearsal resets, API and Temporal SQLite databases were backed up using SQLite's online backup API. They were restored with writer services stopped, and both returned `integrity_check=ok`. Initial direct access to Docker volume paths failed with a host permission error; restoration was completed using network-disabled Docker helpers mounted only to the workshop volumes. These backups cover SQLite state, not Kafka broker state. Profile switching recreates Kafka, which has no persistent volume.

Automatic approval review initially rejected a wrapper that did not restore databases; the revised restoration-backed run was approved. The exact executed harness is retained as [rehearsal-harness-as-executed.py](2026-10-03-novabank-reaudit-evidence/rehearsal-harness-as-executed.py), including its failed host-path restoration attempt. Do not rerun it without replacing that restoration block with the Docker-volume method. Recovery details are in [database-restoration.json](2026-10-03-novabank-reaudit-evidence/database-restoration.json).

A post-restoration W4 check initially failed at Gate 1 with HTTP 502. Gateway diagnostics showed the cached adapter upstream at `172.23.0.3`, while the restarted adapter had `172.23.0.6`. A later request and full W4 verification succeeded without implementation changes. Preserve this as a dependency-restart recovery gap, separate from the now-passing W2 startup path. Add readiness/failure checks around dependency restarts and verify gateway DNS/upstream refresh. Both the [failed check](2026-10-03-novabank-reaudit-evidence/w4-final-verify-first-attempt.log) and [passing final check](2026-10-03-novabank-reaudit-evidence/w4-final-verify.log) are retained, with [gateway diagnostics](2026-10-03-novabank-reaudit-evidence/gateway-followup.log).

W4 is active at audit completion. Only new audit artifacts were added; no implementation changes, commits, merges, or pushes were performed. Prioritize exchange authorization/protocol fixes and the rejection regression, then eliminate fabricated persistence success, enforce immutable deployment inputs, and close the original delivery/rehearsal coverage gaps before declaring all findings resolved.
