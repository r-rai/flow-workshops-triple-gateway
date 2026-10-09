# Workshop 4 public Incident Room deployment plan

**Status: proposed; requires owner approval before implementation or deployment.**

Prepared 2026-10-09 for “The Day the Agent Broke the Bank.” This plan is based on inspection of the local checkout of `r-rai/flow-workshops-triple-gateway`, HEAD `09ca591defa62d86c0a89b10651421ebf43e878f`, including existing uncommitted documentation/configuration edits. It does not certify a running VPS. Only this plan was created; no application implementation, container startup, rehearsal, or VPS change was performed.

**Recommendation:** reuse the Incident Room UI, session lifecycle and run/evidence APIs in a dedicated, single-process observation service. Preload a curated recording from the laptop. Run no banking, inference, approval, workflow or vulnerable replay services on the public deployment. Participants investigate recorded evidence on phones; the presenter continues the existing Docker/WSL demonstration locally. Public access requires an event access code that creates a restricted viewer session.

## A. Existing architecture assessment

### Inspected sources and findings

| Source | Relevant behavior |
| --- | --- |
| [Presenter story](workshop-4-story.md), [presenter notes](presentations/flo-bank-workshop-4-notes.md) | 135-minute narrative; recorded ₹90 lakh attack; laptop exercises and independent review; chapter cues are presentation aids. |
| [Participant worksheet](../../workshops/w4/worksheet.md), [answer key](../../workshops/w4/answer-key.md), [evidence sheet](../../workshops/w4/incident-evidence.md) | Current worksheet assumes local Python/Docker/pair labs. Shared hosting is observation/fallback. Evidence must correlate identities, arguments, decisions, ledger effects and task/payment binding. |
| [UI HTML](../../src/demo/static/incident.html), [JS](../../src/demo/static/incident.js), [CSS](../../src/demo/static/incident.css), [shared CSS](../../src/demo/static/governance.css) | Responsive layout, wrapped JSON, predictions in localStorage, run selector and downloads. At widths below 900px Incident Room columns stack. Execution/approval buttons are disabled in observation mode, but administrative-looking panels remain visible. |
| [Incident backend](../../src/demo/incident.py) | SQLite `runs`, `sessions`, `reviewers`; one worker and process lock. Authenticated observation viewers can read all stored runs, including by ID. Three-hour W4 session lifetime. No import/publish mechanism exists. |
| [Customer app](../../src/demo/app.py) | Hardcoded `maya@flobank.demo` / `flo-demo`; maximum 128 in-memory sessions; cookie `flo_demo_session`, HttpOnly, SameSite=Strict, `/demo-api`, Secure only when request scheme is HTTPS. Enterprise session can mint customer JWT with card/case write scopes. |
| [Core API](../../src/api/main.py), [Dockerfile](../../docker/api/Dockerfile), [Compose](../../docker-compose.yml) | API image normally starts the core banking API and mounts the customer app. W4 profile also starts APISIX, adapter, OPA, Postgres, Jaeger, Temporal/UI, Kafka and worker. API uses SQLite by default despite Postgres being present. |
| [W4 gateway](../../docker/apisix/apisix-w4.yaml) | Routes `/demo-api/*`, `/api/v1/*`, `/ai/*`, `/mcp`, `/oauth/*` and discovery. Lab key is hardcoded in gateway consumer configuration. It is unsuitable as the public route policy unchanged. |
| [Tests](../../tests/test_w4_incident.py), [verification tests](../../tests/test_w4_verification.py), [browser view check](../../tests/w4_view_browser.cjs), [browser rehearsal](../../tests/w4_incident_browser.cjs) | Existing observation test checks scenario creation denial. Browser rehearsal executes financial scenarios and must stay local. View regression proves view selection grants no reviewer authority. Additional public-mode tests are required. |
| [Technical runner](../../workshops/w4/rehearsal_w4.py), [evidence inventory](../../workshops/w4/evidence/README.md), [VPS guide](../setup/vps-setup-guide.md) | Runner exports an envelope with `runs`; existing evidence is dated rehearsal material, not fresh VPS proof. VPS guide explicitly describes a development topology. |

The separate opt-in `incident-sandbox` has an internal network, disposable ledger, no public port, no banking/provider keys, and no protected volumes. Preserve it exclusively on the laptop. ₹90 lakh is **900,000,000 paise**; it is a fictional recorded proposal executed against that ledger, never a claim of live model compromise.

### Security gaps relevant to public hosting

1. `W4_OBSERVATION_ONLY=true` guards POST run creation, decision and reconciliation. It does not globally restrict the customer app or core banking routes. Disabling buttons is a usability feature, not authorization.
2. POST `/demo-api/workshop-4/runs/{id}/traces` remains available and queries Jaeger, then saves evidence. Reviewer-session creation also lacks the observation guard. Both must be denied publicly.
3. Existing readiness probes contact banking, inference and MCP services and mint probe credentials. A recording service must report recording availability without these calls.
4. The demo login is publicly known. Enterprise login/restoration can mint write-capable customer credentials. Public-mode sessions must never take that path or return the customer dashboard snapshot.
5. Run list/detail/export return stored JSON. The sanitizer removes selected credential/reasoning keys and JWT-shaped strings, but arbitrary text, nested errors and non-JWT secrets can survive. Observation mode exposes all stored runs, so copying a presenter database would expose unintended material and session/reviewer records.
6. Chapter/ticket visibility is browser-local. Full run responses and downloads already include ticket/events; CSS hiding is not a coordinated or secure reveal.
7. The JS builds a Jaeger URL using public hostname port 16686. Remove that link on the public site; do not expose Jaeger.
8. The base Compose project has fixed network names such as `flobank-edge`; `-p` alone does not isolate explicitly named networks. Image tags such as `flobank/api:1.0.0` also risk collisions. Use a separate Compose file and unique image tag.

## B. Proposed VPS deployment architecture

```text
Phone browser → HTTPS dedicated subdomain → existing VPS reverse proxy
                                             ↓ restricted host/method routes
                              isolated W4 observation container, one worker
                               ├─ existing Incident Room assets
                               ├─ restricted viewer sessions (writable SQLite)
                               └─ curated run recording (read-only SQLite)

Presenter laptop → existing local W4 stack + isolated replay (unchanged)
                  → offline export/review → approved recording artifact
```

Use a proposed `compose.w4-public.yml` **alone**, not as an override merged with the workshop Compose file. Reuse `docker/api/Dockerfile` and dependencies, with a dedicated entrypoint such as `src.demo.public_incident:app` assembling only Incident Room routes and required assets. It must not import/start `src.api.main` or mount the entire customer app. Reuse existing incident read handlers and session helpers through small explicit seams; avoid a broad application restructuring.

Persist only event viewer sessions in a new private volume. Keep the curated evidence database on a separate read-only bind mount, outside the static directory. Because current `store()` creates all tables and commits on every connection, add an observation read connection using SQLite URI `mode=ro`; do not point the existing writable helper at that mount. The runtime has no evidence-write interface. Health checks cover the recording and session store, not nonexistent workshop services.

No APISIX, OPA, adapter, Postgres, Kafka, Temporal, worker, Jaeger or incident-sandbox is required. No provider credentials, banking API key, reviewer password, sandbox key or presenter signing key is supplied. Dependencies may retain unused lab defaults in their modules; ensure public code paths never mint tokens, contact a gateway, or expose those values. Deny unexpected routes in both application and proxy.

For a host reverse proxy, choose a verified free host port and bind `127.0.0.1:<port>:8000`. A containerized proxy cannot reach that host loopback through its own localhost. Antigravity must instead use its established connectivity convention, preferably a dedicated network between proxy and W4 with no host port. Do not attach W4 to a broad shared application/backend network without reviewing lateral reachability. Network names should be project-scoped, consistent with [Docker Compose networking guidance](https://docs.docker.com/compose/how-tos/networking/).

### Capacity and dependencies

Planning estimate for this small service: start with **256 MiB memory, 0.5 CPU, bounded process count and one Uvicorn worker**, subject to measurement; reserve at least 512 MiB available host memory beyond other apps' measured peak. Allow roughly 2–3 GiB disk for image/build layers and 100 MiB for curated evidence/session data, plus capped logs and backup. These are estimates, not measured public capacity. Avoid image builds during the event; build elsewhere if VPS headroom is tight.

The answer key reports about 1.06 GiB for a historical full workshop snapshot and Kafka close to its cap. That measurement does not justify running the full lab on this VPS. Required dependencies are existing Docker/Compose, existing proxy/TLS machinery, DNS control, the built Python image, local SQLite and an approved artifact. No new managed service, identity provider or polling platform is needed.

Confirm expected audience `N`. Require admission capacity of at least `N + 25%` including a simultaneous QR scan burst. Do not merely raise the current 128-session limit: enforce a configurable bounded count across persisted unexpired event sessions, cleanup expiry, rate-limit admission and size evidence responses. One worker remains intentional; load-test before changing it.

## C. Required repository changes (after approval)

| Change | Scope and purpose |
| --- | --- |
| Dedicated public entrypoint | Serve `/workshop-4`, selected assets, login/logout, sanitized readiness and evidence reads. Reuse UI and read/session components. Deny all other paths/methods, even on direct upstream access. Disable docs/OpenAPI and customer dashboard. |
| Public configuration validation | Require exact `W4_OBSERVATION_ONLY=true`, `W4_ENABLE_VULNERABLE=false`, `ACTIVE_PROFILE=w4`, configured access-code secret and valid curated recording. Fail startup if contradictory/missing. Local defaults and presenter entrypoint remain unchanged. |
| Restricted viewer session | Store viewer role, event and expiry; cryptographically random opaque cookie; three-hour lifetime, event close time and server-side revocation. No customer JWT or reviewer role. Public login response contains viewer/event metadata only. Restored sessions must remain viewers. |
| Recording import utility | New offline CLI, e.g. `scripts/w4_public_evidence.py`; accept the runner's `runs` envelope or reviewed run exports. Validate/project allowed fields, sanitize, create a fresh read-only recording DB and manifest with hash, capture time, source revision and record counts. Reject unknown sensitive fields, duplicate IDs and invalid amounts/types. |
| Evidence/readiness seam | Public reads use curated DB only; readiness states “recording available,” capture time, evidence version and observation mode. No live service probing, minted credentials, collector calls or writes. Return safe errors. |
| Observation UI branch | Reuse `incident.html/js/css`; code-only join form without sample credentials; clearly show “Observation only · recorded evidence.” Hide run execution/reviewer/reconcile/collector controls and dashboard navigation. Move run selection into investigation area; keep approval evidence readable. Provide chapter navigation for self-paced investigation. |
| Mobile companion worksheet | Add concise read-only tasks and link from Incident Room. Keep original local-lab worksheet. Answers/key remain facilitator material outside served assets. |
| Standalone Compose and tests | Unique project/image, resource limits, no presenter services, evidence `:ro`, private session volume, non-root UID, read-only root filesystem, tmpfs as needed, drop capabilities, no-new-privileges, capped logs and healthcheck. Add authorization/export/mobile tests below. |

Do not bundle the checkout, `.env`, `/app/data`, facilitator answers, audit directories or evidence inventory as a public static tree. Serve exact required files. Avoid sending the entire collection in the list API if large: return compact summaries and fetch selected run/detail on demand, adapting `reloadRuns()` to fetch detail before rendering. Apply fixed response/record size limits.

## D. Required VPS configuration changes and unresolved facts

Antigravity must resolve these using its VPS knowledge **before any change**:

| Question | Required recorded answer |
| --- | --- |
| Which proxy, version, service owner and deployment mechanism? | Exact configuration location, validation command, safe reload/reconfigure mechanism and backup/restore procedure. No assumption of Nginx, Caddy or Traefik. |
| Is proxy host-based or container-based? | Upstream connection path, trusted peer address, dedicated network feasibility and public port inventory. |
| What domain/subdomain and DNS provider? | Owner-approved FQDN, A/AAAA correctness, TLS issuance/renewal method. No placeholder domain goes live. |
| What else runs here? | Container/project/network/port inventory, baseline app health checks and protected resources. |
| What capacity is actually spare? | CPU, memory/peak/swap, disk, build space and event audience. Reduce scope or decline hosting if safe headroom cannot be shown. |
| What host/firewall/IPv6 protections exist? | Confirm W4 has no externally reachable upstream port on IPv4 or IPv6. Preserve unrelated rules. |
| What secret/log/backup conventions exist? | Restricted code file outside repo, redacted logs, project-specific backups and deletion deadline. |
| Which revision and evidence recording will be used? | Approved commit/image digest, approved export provenance, artifact hash and capture timestamp. |
| What event access policy and duration? | Code distribution, session cap, event close time, post-session availability and retention. |
| Preloaded or progressive evidence? | Default below is preloaded; progressive requires additional explicit approval and verification. |

Add only one dedicated virtual host/router under the existing HTTPS proxy. Use its established certificate automation. HTTP redirects to HTTPS; unknown hosts must not reach W4. Configure method/path allowlist, same-origin policy, small login body cap (e.g. 2 KiB), bounded timeouts/connections, admission throttling and traffic limits tuned to shared NAT attendees. Overly strict per-IP rules can block an entire classroom: load-test the QR burst, then rate-limit failed code attempts separately from ordinary reads.

Set CSP for same-origin scripts/styles/connects and `frame-ancestors 'none'`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer` and appropriate Permissions-Policy. Enable HSTS for this host after verifying TLS, without changing the parent domain's policy. Authenticated API/evidence use `Cache-Control: no-store`; do not cache responses across viewers. Do not log request bodies, cookies or credentials. Do not enable cross-origin CORS.

Forward canonical Host/protocol/client headers; overwrite browser-supplied forwarding headers. Trust proxy headers only from the actual proxy peer/network in Uvicorn. Require Secure cookies in public mode independently of proxy detection. Do not use wildcard trust where unrelated containers can reach upstream. These session controls follow [OWASP session guidance](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html).

## E. Mobile participant experience and evidence timing

QR contains only `https://<approved-subdomain>/workshop-4`, with a short typed URL printed below. Show the access code on the event slide or distribute it in the room; do not put credentials in QR URLs, query parameters or JS. Participants enter the code once and receive their own restricted session.

At the top: fictional ₹90 lakh incident, recorded capture time, observation-only label and a short task. On phones, order content as incident → selected evidence → identities/boundaries → ledger effect → approval/task proof → final review. Keep JSON drawers optional, retain server downloads and explain paise beside rupee totals. Use readable text, at least 44px primary touch targets, focus visibility and no page-wide horizontal scrolling. Predictions stay local and are never sent to the server. Make localStorage failures nonfatal; provide a clear-session action for shared phones.

Mobile tasks reuse the evidence sheet: identify where ticket data became authority; distinguish inference budget from payment permission; compare beneficiary/amount/audience/scope denials; inspect self-approval/tampering results; prove one independently approved ₹1,500 payment bound to its task; name control owners. Participants predict, inspect, compare and explain. Policy editing and command execution remain presenter demonstrations.

**Recommended for tomorrow: preload the complete curated recording.** Present it explicitly as a dated rehearsal, not a synchronized reflection of the laptop's current ledger. Chapter navigation guides investigation; participants can inspect later evidence early. No continuous laptop-to-VPS feed is needed, and full recording remains usable if the laptop demo has trouble.

If a strict progressive reveal is chosen later, use a host-controlled chapter manifest with server-side filtering applied equally to list, detail and download. Unreleased runs/fields must be absent from responses, including guessed IDs. No public presenter toggle or new admin API. Antigravity advances the manifest via its existing operator channel using atomic replacement; optional slow polling/manual refresh reads only published state. Test late joins and cache behavior. This adds operator coordination and is excluded from the recommended first release. Already downloaded evidence cannot be withdrawn.

## F. Authentication and authorization

Reuse opaque cookie sessions and three-hour W4 persistence, with a distinct `viewer` role/event binding in the public entrypoint. Access code verifies against a restricted host secret using constant-time comparison; missing code fails startup, incorrect code returns a generic 401 and throttled attempts return 429. Do not use the documented demo password as public authentication. A shared event code is an admission convenience, not personal identity or permission to perform actions; its leakage exposes only the approved fictional recording.

Require viewer authentication on every run list/detail/export/readiness request. Logout revokes stored session; event closure rejects login and existing sessions. Rotation blocks new admissions; emergency closure revokes all event sessions. Persist no raw session cookie, only its hash. Secure, HttpOnly, SameSite=Strict, host-only cookie scoped to `/demo-api`; no browser JWT, localStorage token or signing secret.

Public route contract (also enforced directly by app):

| Path | Allowed method/access |
| --- | --- |
| `/` | GET/HEAD redirect to `/workshop-4` |
| `/workshop-4` and explicit required assets | GET/HEAD; login shell/static assets only, no incident JSON embedded unauthenticated |
| `/demo-api/login` | POST access code only; bounded schema, no legacy credential bypass |
| `/demo-api/logout` | POST; revoke viewer cookie/session |
| `/demo-api/workshop-4/readiness` | GET authenticated, recording readiness only |
| `/demo-api/workshop-4/runs` | GET authenticated, curated summaries |
| `/demo-api/workshop-4/runs/{id}` and `/{id}/evidence` | GET authenticated, curated detail/export only |
| All other paths/methods | Denied; authenticated mutating Incident Room calls return 403, absent customer/core/admin routes return 404/405; proxy may return its configured 403/404/405 |

Reject cross-origin login/logout requests using canonical Origin checks; support the legitimate same-origin browser flow. A view selector, altered URL or forged `w4_reviewer` cookie must never change authorization. No public payment/approval/policy/token-exchange/live-model capability exists.

## G. Security controls and threat assessment

| Threat | Control and verification |
| --- | --- |
| Participant calls hidden mutation routes | Route/method denial at application and proxy; direct upstream negative tests with a valid viewer cookie. No financial services deployed. |
| Known lab credentials/signing keys | Code-only admission, no legacy login path, no token minting. Never copy laptop `.env`, key or session DB. |
| Secrets/internal details in recording | Allowlisted projection plus sanitizer and human review; drop headers, private reasoning, stack traces, hostnames/IPs/paths/provider metadata. Scan keys and arbitrary strings; JWT regex alone is insufficient. |
| Evidence tampering or misleading claims | Read-only evidence mount, recorded source/hash/time, intact correlation, archived original privately, trace completeness preserved. Never turn null/unresolved effects into zero/success. |
| Prompt injection or XSS in ticket | Ticket is displayed as inert text (`textContent`), never passed to model/tools; retain escaping and CSP. Include hostile HTML/script fixture tests. |
| Availability/session exhaustion | Bounded persisted sessions, expiration cleanup, throttled failed logins, request/response limits, CPU/memory/log limits and tested classroom burst. No live LLM cost. |
| Cross-app access or VPS disruption | Dedicated project/image/network/data, no Docker socket/host mounts/privilege, no workshop launcher against VPS, inventory before/after. Shared proxy is the only intended integration. |
| Stolen viewer session/event code | HTTPS, secure cookies, short event lifetime, no token URLs, closure/revocation, curated-only data. Shared-code attribution remains deliberately limited. |
| Accidental reveal of answer key | Exact static file list; checkout/docs/DB cannot be downloaded; answers stay on presenter machine. |
| SQLite locks/storage failure | Separate immutable recording and writable session DB; one worker, bounded writes, healthchecks, backup and failed-start behavior. |

For import, retain fictional principals and correlation IDs needed for teaching; replace internal issuer/host strings with documented synthetic labels consistently. Remove full account numbers and personal data. Preserve HTTP/MCP outcomes, actual arguments, paise values, exact proposal/task/payment linkage and observed ledger deltas. Include replay, protected denials and a completed legitimate path; exclude pending reviewer sessions, unresolved runs unless pedagogically labeled, raw spans and live-provider transcripts by default. No executable import content; reject malformed/oversized artifacts and use parameterized SQLite inserts.

Residual limits: one VPS/process has no HA, event code can be shared, recordings can be copied after admission, and curated exports demonstrate selected lab controls rather than banking production certification. These are acceptable only for the fictional observation exercise. If security checks cannot finish before tomorrow, use a privately reviewed static worksheet/evidence PDF through an already approved delivery channel and keep all live execution local; do not publish the unmodified lab stack as a shortcut.

## H. Step-by-step instructions for Antigravity (execute only after approval)

1. Resolve D's inventory/questions. Record baseline service health and proxy configuration backup using existing procedures. Record expected audience, FQDN, free port or dedicated proxy network, spare resources and retention deadline. Stop if any shared-resource impact remains uncertain.
2. Implement C in a separate branch/checkout; preserve original Compose and local presenter behavior. Build public image with a unique revision tag. Run authorization/session/import regression tests and existing relevant tests. Do not start vulnerable mode on VPS.
3. Select already recorded evidence or export completed runs from the laptop through its authenticated evidence API. The rehearsal runner itself creates payments: run it only on the local presenter instance if a fresh recording is needed. Do not replay on VPS. Preserve original privately; transfer only reviewed recording through the established secure file-transfer method.
4. Run the proposed importer offline on a preparation machine. Review every exported field/string, provenance and required run correlations. Produce a fresh evidence-only DB, manifest and hash; no sessions/reviewers copied. Create a versioned release directory on VPS following its existing convention.
5. Create restricted access-code file and private session storage with correct non-root ownership. Mount evidence read-only and code as a file; no code in committed config. Set required flags, disable telemetry/live chat, and enforce event close time. Do not reuse presenter secrets.
6. Render standalone Compose config privately, confirm only one `incident-room` service, unique project/network/image/volume, resource limits and desired port binding. Never run `scripts/workshop switch/reset/stop` here; those operate the lab topology.
7. Start W4 alone without adding public proxy route yet. Verify container health, config validation, denied direct upstream routes and artifact hash. Do not print secret-bearing environment/config dumps into reports.
8. Prepare only the new subdomain's proxy route. Apply allowlist, admission/read limits, forwarded-header trust, security/cache headers and TLS. Validate config using the exact existing proxy command. Use its non-disruptive reload/reconfigure procedure; do not restart the whole proxy or alter existing routes.
9. Run J from both operator upstream access and an external mobile network. Verify IPv4/IPv6 port closure, cookie behavior and unrelated application health. Revert on any shared-service regression.
10. Test real Android Chrome and iOS Safari, QR scanning, code entry, investigation and JSON download/share. Run capacity test with synthetic event sessions, revoke them afterward, and confirm clean session state.
11. Record approved release commit/image digest, evidence hash/count, proxy change location, verification outputs without credentials, rollback targets and closure date. Generate QR from final tested HTTPS URL. Presenter dry run compares recording with laptop narrative; no assumption of live mirroring.
12. During the session watch existing VPS metrics plus W4 memory/restarts/errors; keep code private and use manual evidence refresh. After event close admissions/sessions and remove this virtual host or keep approved recording availability only for the agreed interval. Delete session/log/backups according to agreed retention.

### Command templates for the proposed deployment

These templates are for the future implementation; `compose.w4-public.yml`, importer and public tests **do not exist yet**. Antigravity substitutes approved paths/ports/proxy commands and runs only after approval. Never merge with the base Compose file.

```bash
# Read-only inventory; handle outputs privately where they include other service details.
docker compose version
docker ps --format 'table {{.Names}}\t{{.Ports}}\t{{.Status}}'
docker network ls
ss -ltn
free -m
df -h

# From the approved dedicated checkout; host settings/secrets are outside git.
W4_SETTINGS=/approved/private/path/w4-public.env
w4dc() { docker compose --env-file "$W4_SETTINGS" -p flo-w4-public -f compose.w4-public.yml "$@"; }
w4dc config --services             # Exactly incident-room
w4dc config --quiet
w4dc build incident-room           # Or pull the approved prebuilt immutable image
w4dc up -d incident-room
w4dc ps
w4dc exec -T incident-room python -c 'import os; assert os.environ["W4_OBSERVATION_ONLY"] == "true"; assert os.environ["W4_ENABLE_VULNERABLE"] == "false"; assert os.environ["ACTIVE_PROFILE"] == "w4"'
w4dc exec -T incident-room python -c 'import urllib.request; assert urllib.request.urlopen("http://127.0.0.1:8000/healthz").status == 200'
docker stats --no-stream "$(w4dc ps -q incident-room)"
```

Add a private app health route `/healthz` for container checks; deny it at the public proxy. Confirm no credential values in shell tracing/logs. The code secret should be mounted as a file rather than included in the env template.

## I. Rollback procedure

1. If unrelated services degrade or data exposure is suspected, withdraw only the W4 route with the proxy's verified validation/reload procedure. Show presenter-local fallback; revoke event viewer sessions and close admissions.
2. Save sanitized incident diagnostics, recording hash and W4 logs under agreed access/retention. Do not collect passwords/cookies. Preserve the previous image, Compose/settings and recording version before each release.
3. Stop only the public project using `w4dc stop incident-room`. Restore the previous known-safe W4 image/recording/config and session schema-compatible backup if appropriate; otherwise discard viewer sessions and require a new login. Never fall back to the unrestricted core API image entrypoint.
4. For complete removal use `w4dc down` without `-v`; preserve evidence/session backup until retention review. Remove only W4 DNS/proxy entries and project-owned resources. Do not prune Docker, delete shared networks, stop other projects or restore the entire proxy config over intervening unrelated edits. Restore only the W4 diff.
5. Validate/reload proxy, verify existing app baseline health and confirm W4 upstream is unreachable externally. If re-enabling a safe prior release, repeat critical J tests first.

## J. Acceptance criteria and verification commands

**Deployment acceptance is pending.** The following checks must pass with evidence before publishing the QR. Existing historical rehearsal/browser screenshots do not establish public deployment acceptance.

| Criterion | Required evidence |
| --- | --- |
| Public-mode fail closed | Startup fails with observation disabled, vulnerable enabled, missing code or invalid recording. No lab default fallback. |
| Auth required | Anonymous/expired/revoked viewer gets 401 for list/detail/export/readiness; correct code issues a unique restricted cookie; wrong code 401 and repeated failures 429. Demo credentials rejected. |
| Viewer only | Authenticated mutations blocked at proxy and direct app; forged reviewer cookie/view URL cannot grant authority; public session creation/restoration mints no JWT and makes no gateway call. |
| Evidence safe and useful | Curated fields/provenance reviewed, negative secret fixtures removed/rejected, hostile text inert; replay loss and protected zero effects correctly distinguished; one legitimate ₹1,500 payment and task binding intact. |
| Immutable recording | Hash of evidence DB unchanged after all read and denied-mutation checks; no recording write path. Session creation/logout changes only private session state. |
| HTTPS and isolation | Valid TLS and HTTP redirect; Secure/HttpOnly/SameSite cookie; no public upstream/admin/service ports on IPv4/IPv6; exact assets only; no docs/schema/customer endpoints. |
| Mobile usability | 320/360/390/430/768px layouts and real Safari/Chrome; no page overflow; readable identity/ledger/proposal, working download, keyboard/touch navigation and refresh after reopening. |
| Capacity | Test `N + 25%` viewers, including shared-NAT admission burst, for at least 15 minutes with reads/refreshes/downloads. No OOM/restarts/5xx, valid admissions not throttled, p95 evidence reads ≤2s and usable join ≤5s on test mobile connection. Tune limits if measured; record target and actual. |
| Coexistence and rollback | Other apps' baseline checks remain passing; no unacceptable CPU/memory/disk pressure. Demonstrated W4-only rollback and recovery before event. |
| Local presenter preserved | Original local entrypoint/profile/config unchanged; relevant regression suite passes in isolated test environment; local presenter dry run successful. Financial rehearsal checks never target VPS. |

### Test commands after implementation

```bash
# Prepared development environment; public test filenames are proposed deliverables.
.venv/bin/python -m pytest tests/test_w4_incident.py tests/test_w4_verification.py tests/test_demo_bank.py -q
.venv/bin/python -m pytest tests/test_w4_public.py tests/test_w4_public_evidence.py -q
# Proposed observation browser suite: code via protected file, no payments or reviewer login.
W4_URL=https://approved-subdomain.example W4_ACCESS_CODE_FILE=/private/code node tests/w4_public_browser.cjs
```

Public tests must exercise all mutating routes, valid viewer sessions, restoration/logout/event closure, read-only mounts, invalid config/import, oversized input, safe errors and fake secrets in nested/text fields. Include direct app tests; a proxy-only denial is insufficient. Existing `w4_incident_browser.cjs` and `rehearsal_w4.py` execute transactions; do not point them at public hosting. Existing view-browser script assumes legacy login and is not a drop-in public check.

### External HTTP smoke templates

The login payload below is a private JSON file containing the proposed `access_code` field. Keep it and the cookie jar mode 600 in a private operator directory, never a shared artifact/report. Replace the domain. Record status codes and nonsecret headers only.

```bash
W4_BASE=https://approved-subdomain.example
W4_LOGIN_JSON=/private/w4-login.json
W4_COOKIE_JAR=/private/w4-cookies.txt
W4_PUBLIC_RUN_ID=approved-recorded-run-id

curl -sS -o /dev/null -w '%{http_code}\n' "$W4_BASE/workshop-4"     # 200
curl -sS -o /dev/null -w '%{http_code}\n' "$W4_BASE/demo-api/workshop-4/runs" # 401
curl -sS -c "$W4_COOKIE_JAR" -H 'Content-Type: application/json' --data-binary "@$W4_LOGIN_JSON" -o /dev/null -w '%{http_code}\n' "$W4_BASE/demo-api/login" # 200
curl -sS -b "$W4_COOKIE_JAR" "$W4_BASE/demo-api/workshop-4/readiness"
curl -sS -b "$W4_COOKIE_JAR" -o /private/w4-evidence.json "$W4_BASE/demo-api/workshop-4/runs/$W4_PUBLIC_RUN_ID/evidence"

# Valid viewer still cannot mutate; 403/404/405 per route/proxy contract, never 2xx.
for suffix in runs reviewer-session "runs/$W4_PUBLIC_RUN_ID/decision" "runs/$W4_PUBLIC_RUN_ID/reconcile" "runs/$W4_PUBLIC_RUN_ID/traces"; do
  curl -sS -b "$W4_COOKIE_JAR" -H 'Content-Type: application/json' -d '{}' -o /dev/null -w '%{http_code}\n' "$W4_BASE/demo-api/workshop-4/$suffix"
done
for path in /demo-api/chat /demo-api/dashboard /demo-api/banking /api/v1/payments /api/v1/admin /oauth/token /mcp /ai/chat/completions /docs /openapi.json /openapi-curated.json /.env /.git/config /data/w4-incident.sqlite /demo-assets/answer-key.md; do
  curl -sS -b "$W4_COOKIE_JAR" -o /dev/null -w '%{http_code}\n' "$W4_BASE$path"
done
curl -sS -b "$W4_COOKIE_JAR" -X POST -o /dev/null -w '%{http_code}\n' "$W4_BASE/demo-api/logout" # 200
curl -sS -b "$W4_COOKIE_JAR" -o /dev/null -w '%{http_code}\n' "$W4_BASE/demo-api/workshop-4/runs" # 401
```

Automated negative tests must use valid route-specific payloads too, so a 422 validation failure cannot masquerade as authorization. Probe actual customer banking/governance/core routes discovered during implementation, including POST/PUT/PATCH/DELETE, encoded path variants and unexpected methods. Repeat against direct upstream with canonical Host/Origin as needed; only safe deny tests, never connect probes to a running presenter API.

Use `curl -I` on HTTPS assets and an authenticated evidence endpoint to verify headers; inspect cookie attributes privately without publishing cookie values. From an external machine test selected upstream ports on both VPS IP families; only existing intended ports remain open. In the approved release directory run `sha256sum <evidence-db>` before/after the full checks and compare against manifest. Inspect W4 container OOM/restart count and resource limits without dumping environment secrets. Perform the proxy-specific configuration validation and existing applications' actual baseline health commands; Antigravity must insert those commands into its execution record after resolving D.

**Approval requested:** approve the isolated observation service, restricted event-code sessions and preloaded curated evidence approach. Implementation and VPS changes remain pending this approval and Antigravity's recorded answers to the VPS questions above.
