# Workshop 1 Facilitator Answer Key & Presenter Cues

**Workshop:** W1 — Modernizing APIs for AI Agents: From OpenAPI to MCP  
**Profile:** `w1`  
**Duration:** 45 minutes

---

## Facilitator Pre-Flight Checklist

Complete the [full Python setup](../../docs/workshops/participant-infra-guide.md#step-23-set-up-python-virtual-environment-for-workshop-clients-verification--tests) before using the launcher. Ask participants to complete the worksheet’s Python client setup before the timed session.

- [ ] Complete shared infrastructure image preparation: `docker compose --profile w3 pull --ignore-buildable`. Global preflight checks the W2–W4 pinned images even for W1.
- [ ] Build/download W1 images: `./scripts/workshop pull w1`.
- [ ] Run `./scripts/workshop preflight` before starting services to check port 9080, memory and pinned images.
- [ ] Pre-warm the profile: `./scripts/workshop switch w1`.
- [ ] Preserve previous evidence and any fictional lab data needed before reset.
- [ ] Reset lab state before attendees begin: `./scripts/workshop reset w1 --yes`.
- [ ] Run `./scripts/workshop verify w1` to verify traversal with the expected fresh seed.
- [ ] Open `/docs`, `/openapi.json`, and the bank page with Developer Tools → Network. Follow the [live API walkthrough](../../docs/workshops/w1-api-walkthrough.md).
- [ ] Confirm enterprise backend mode; W1 scripted chat needs no provider key. Restore any card freeze used during the demo.

---

## Presenter Timeline & Cues

| Timeline | Topic | Talking Points & Presenter Actions |
|---|---|---|
| **0–5 min** | Intro | Welcome attendees, name the topic/outcomes, introduce the Flo Bank story, then tour Swagger and the bank page’s real account requests before asking which tools Flo needs. Support scenario: an agent needs to assist customers with account queries, but exposing existing internal APIs raw to LLMs is dangerous. |
| **5–12 min** | OpenAPI vs MCP | Explain the difference: OpenAPI defines HTTP endpoints, verbs, and schemas. MCP provides runtime tool negotiation (`initialize`), schema discovery (`tools/list`), and execution envelopes (`tools/call`). |
| **12–22 min** | Native Generation Demo | Show APISIX `openapi-to-mcp` plugin generating tools on the fly from `/openapi.json`. Record the current generated count (26 on 2026-10-05), highlighting the danger of exposing `execute_payment` and `reset_database`. |
| **22–32 min** | Invocation and curation | Read the account, then use `client.py --curated init`, `--curated list` and `--curated call-account acc-101`. Show exactly two read tools and the fresh balance (`1,500,000 paise = ₹15,000`). Use the rehearsal for case read and excluded payment-list rejection. |
| **32–40 min** | Gate 3 Denial | Demonstrate `.venv/bin/python workshops/w1/client.py --curated call-unauthorized`. Show that APISIX Gate 3 route `/api/v1/*` enforces `key-auth` and returns 401 Unauthorized. Emphasize: *MCP does not bypass API security*. |
| **40–45 min** | Capability review & Q&A | Ask pairs to explain one removed operation, one description improvement and their actual authorization evidence. |

---

## Worksheet Answers

### Step 2: Broad Tool Catalog
1. **Tool Count:** Discover at runtime; 26 tools were observed on 2026-10-05. The static broad teaching checkpoint may differ from the served API.
2. **Exposed Mutations:** Yes. Both payment creation (`execute_payment_api_v1_payments_post`) and admin reset (`reset_database_api_v1_admin_reset_post`) are discoverable in the broad catalog; execution still requires downstream authorization.
3. **Security Risk:** If a model hallucinates or is prompted by an attacker (indirect prompt injection), an unnecessarily broad catalog can expose high-impact requests to the model. Whether a request executes still depends on authorization and banking rules.

### Step 3: Account Read
- **Account ID:** `acc-101`
- **Fresh-seed balance:** `1500000` (minor units = 15,000.00 INR). Record the actual result if using a previously modified ledger; technical verification expects the fresh seed.
- **Currency:** `INR`

### Step 4: Gate 3 Enforcement
1. **HTTP Status Code:** `401 Unauthorized` (`Invalid API key in request`).
2. **Backend Database Reachability:** The embedded 401 establishes denial of this read. Inspect route configuration and relevant logs to establish where it stopped; the MCP envelope alone does not prove database reachability.
3. **Critical Invariant:** Direct Gate-2-to-backend routing would bypass all API gateway rate-limiting, authentication, logging, and WAF rules. Re-entering Gate 3 preserves the configured API-key boundary. This W1 lab does not prove production IAM, customer isolation, WAF coverage or complete tracing.
