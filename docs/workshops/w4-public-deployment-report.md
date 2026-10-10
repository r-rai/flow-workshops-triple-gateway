# Workshop 4 Public Incident Room Deployment Report

Updated 2026-10-10T03:22:30+00:00 after owner-requested presentation and container refresh. The original hardening verification below is retained; see the latest refresh section for current deployment details.

## Participant access and schedule

- URL: https://w4.ravirai.in/workshop-4
- Workshop: Saturday 2026-10-10, 10:00–11:30 IST (04:30–06:00 UTC).
- Authenticated-access cutoff: 12:00 IST (06:30 UTC), including the 30-minute grace period.
- At the cutoff, correct-code logins return 403 and existing viewer evidence requests return 401.
- Cutoff is required and validated as a timezone-aware UTC timestamp; invalid configuration fails startup.
- The page/container are not automatically removed or stopped. The owner will shut W4 down manually.
- The rotated access code is kept privately in `/home/sysadmin/.flo-w4/access_code.txt`; it is not published in HTML, JS or this report. The previously disclosed code is rejected.
- Viewers inspect 11 curated rehearsal runs. There is no live synchronization with the presenter's ledger.

## Deployed service and VPS safeguards

Standalone project `flo-w4-public`, service `incident-room`, container `flo-w4-incident-room`.

- Image: `flobank/w4-public:20261009-hardened`.
- Deployed image ID: `sha256:ef541a09d97fe8a96cfd8838de4e5f491529de69291d50c45bb22ca33884fbc5`.
- Dedicated entrypoint: `src.demo.public_incident:app`, one Uvicorn worker.
- User/group: 1000:1000; read-only root filesystem; all capabilities dropped; no-new-privileges; 64-process limit; bounded 8 MiB temporary filesystem.
- CPU: 0.5; memory: 256 MiB; logs: three files of at most 10 MiB each.
- No published host ports. Only Caddy and W4 currently use the `apps` network.
- Forwarded headers trusted only from current Caddy peer 172.21.0.3. If that container's IP changes, update the W4 command and redeploy only W4.
- Curated evidence mounted read-only and opened with SQLite `mode=ro`.
- Private writable session volume; opaque tokens stored only as hashes.
- Active session cap: 250. Cumulative admission cap: 500; successful re-logins count toward this total. Logout frees active capacity but does not reset cumulative admissions.
- Secure/HttpOnly/SameSite=Strict cookies, with expiry bounded by the event cutoff.
- Login bodies limited to 4 KiB before JSON parsing, including chunked uploads. Five-second login-body receive timeout. Non-ASCII invalid codes produce 401 instead of a server error.
- Foreign Origin headers rejected on login/logout; CLI requests without an Origin remain supported.
- All API responses marked no-store. Public static files limited to `incident_public.js`, `incident.css`, and `governance.css`.
- Health checks actually query the recording and session store; unavailable/empty recordings return 503.

The existing W4 session volume was backed up with SQLite's backup API before changing its directory/files to UID/GID 1000 and modes 0700/0600. A newly created replacement volume must likewise be initialized for UID 1000 before startup. Do not delete the volume as part of normal shutdown.

## Observation and evidence

All five Incident Room execution/reviewer/decision/trace/reconciliation POST routes return 403. Banking, approval, policy and administration APIs are absent from this entrypoint. Checks against HTTPS and direct upstream confirmed these denials.

The synthetic budget-exhaustion filler is represented by an explicit 399,864-character summary. Actual HTTP 429 responses, identities, arguments, decision reasons and measured effects remain visible. The legitimate settlement preserves its ₹1,500 delta and exact task/payment binding. Credentials remain redacted. The offline importer now removes nested password/secret/cookie fields and opaque Bearer credentials, with a regression fixture proving useful flow fields survive.

Recording SHA-256: `97398e40f6cf2224f67df6cc068f23919bb463b2cd81401e966fb8be794cbc85`. The recording remained unchanged during deployment and testing.

## Fresh verification

- Public authorization/import tests: 32 passed.
- Presenter/verification/customer regression tests: 53 passed. Final combined run: 85 passed, with two existing dependency deprecation warnings. Public test environment setup no longer contaminates presenter test collection.
- Exact cutoff boundary simulated in an isolated session store: before cutoff, login/read 200; at cutoff, login 403 and an existing viewer 401. Session expiry equals the cutoff when it is less than three hours away.
- Four live Chromium mobile viewports (320/360/390/412px) passed, including a storage-blocked phone, notes clearing, actual JSON download, settlement binding and logout.
- Live HTTPS and direct upstream: Unicode invalid code 401; oversized chunked body 413; foreign Origin 403; correct private code 200; Secure cookie; authenticated reads no-store; revoked cookie 401; mutation routes 403; payment/policy/admin probes 404.
- Bounded live smoke: 20 simultaneous evidence reads, all 200; observed p95 1.425 seconds and maximum 1.49 seconds. This is not a full audience-duration load test.
- All pre-existing running containers retained their IDs, start timestamps and restart counts. Shared Caddyfile hash remained unchanged. W4 is healthy with no OOM/restart events.
- Deployed public Python source hash matches the workspace source.

Limitations: real physical iOS/Android devices and a full classroom load were not available for this verification. Cloudflare still holds previously cached `incident.js` and `app.js`; direct upstream and fresh cache-key requests return 404. Those cached public lab scripts contain no live authority: their API actions are denied. No Cloudflare cache purge was performed.

## Manual shutdown after the workshop

Stop only the public service; preserve session storage and unrelated services:

```bash
docker compose -p flo-w4-public -f /home/sysadmin/projects/flow-workshops-triple-gateway/compose.w4-public.yml stop incident-room
```

To withdraw routing as well, remove only the `w4.ravirai.in` block from `/home/sysadmin/apps/caddy/Caddyfile`, then validate and reload Caddy. Do not copy an old whole Caddyfile over intervening changes.

```bash
docker exec caddy caddy validate --config /etc/caddy/Caddyfile
docker exec caddy caddy reload --config /etc/caddy/Caddyfile
```

If complete project removal is wanted, use `down` without `-v`. Do not prune Docker or remove shared networks. DNS removal is optional and manual.

## W4-only rollback

Previous public image retained as `flobank/w4-public:rollback-e465e20`. Matching previous Compose saved in `/tmp/w4-hardening-review/compose.before.yml`; private session backup is `w4-sessions.pre-hardening.sqlite` inside the W4 session volume. These are local recovery artifacts, not participant assets.

```bash
docker compose -p flo-w4-public -f /tmp/w4-hardening-review/compose.before.yml up -d --no-deps --pull never incident-room
```

This restores only the prior observation container, not the core banking entrypoint or shared proxy configuration. Prefer withdrawing W4 if a security incident is suspected. Retain the local rollback artifacts through the workshop; `/tmp` is not permanent release storage.

## Gateway presentation and container refresh — 2026-10-10

- Built a 43-slide editable Workshop 4 deck: API gateway, AI gateway, MCP gateway,
  Triple-Gate architecture, QR audience access, then the incident-response lab.
  Delivery is a 15-minute gateway primer plus the original 135-minute lab.
- Reusable repository PPTX/PDF contain the audience URL QR and a facilitator-code
  placeholder. The separate event PPTX/PDF include the newly generated audience
  code. No reviewer or sandbox password is embedded in either deck.
- Rotated the private audience-code file and recreated only the local API and
  public observer containers. Existing volumes were retained; other running
  container IDs stayed unchanged.
- Current public image: `flobank/w4-public:20261010-gateway-workshop`.
- Current public image ID: `sha256:860b89f8cf003b884d6b9cc392c9e9bc3507071f484942c93b3400663b6ca2a2`.
- Preserved event cutoff: **2026-10-10 12:00 IST / 06:30 UTC**. The deck's longer
  delivery duration does not automatically extend this event-specific cutoff.
- Live HTTPS verification: new code 200; previous code 401; 11 recordings
  accessible; execution POST 403; logout revokes access; served observer script
  hash matches the current checkout.
- Local `./scripts/workshop verify w4` passed inference, MCP discovery, banking
  identity and A2A agent-card checks.
- Recording SHA-256 remained `97398e40f6cf2224f67df6cc068f23919bb463b2cd81401e966fb8be794cbc85`.
- QR decoding passed for the embedded image and the actual rendered PDF slide.
  Presentation checks passed slide bounds, text fit, notes, source paths, PDF
  page count and package integrity. PDF rendering is independent of PowerPoint;
  inspect the PPTX in the presentation application before delivery.
- Private previous-code backup and keyed event artifacts are under
  `/tmp/flo-w4-event`; copy required delivery artifacts to durable private storage
  before that temporary directory is cleaned. Previous observer image retained
  as `flobank/w4-public:rollback-pre-gateway-workshop`.
