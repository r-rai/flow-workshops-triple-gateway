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
- [ ] Run `./scripts/workshop verify w1` to verify traversal.
- [ ] Reset lab state before attendees begin: `./scripts/workshop reset w1 --yes`.

---

## Presenter Timeline & Cues

| Timeline | Topic | Talking Points & Presenter Actions |
|---|---|---|
| **0–5 min** | Intro | Welcome attendees. Introduce fictional Flo Bank support scenario: an agent needs to assist customers with account queries, but exposing existing internal APIs raw to LLMs is dangerous. |
| **5–12 min** | OpenAPI vs MCP | Explain the difference: OpenAPI defines HTTP endpoints, verbs, and schemas. MCP provides runtime tool negotiation (`initialize`), schema discovery (`tools/list`), and execution envelopes (`tools/call`). |
| **12–22 min** | Native Generation Demo | Show APISIX `openapi-to-mcp` plugin generating tools on the fly from `/openapi.json`. Point out the 13 generated tools, highlighting the danger of exposing `execute_payment` and `reset_database`. |
| **22–32 min** | Guided Invocation | Guide participants to run `.venv/bin/python workshops/w1/client.py call-account acc-101`. Show the retrieved balance (`1,500,000 paise = ₹15,000`). |
| **32–40 min** | Gate 3 Denial | Demonstrate `.venv/bin/python workshops/w1/client.py call-unauthorized`. Show that APISIX Gate 3 route `/api/v1/*` enforces `key-auth` and returns 401 Unauthorized. Emphasize: *MCP does not bypass API security*. |
| **40–45 min** | Curation & Q&A | Show `openapi-curated.json`. Discuss why purposeful capability design is essential rather than exposing all swagger endpoints to agents. |

---

## Worksheet Answers

### Step 2: Broad Tool Catalog
1. **Tool Count:** 13 tools generated.
2. **Exposed Mutations:** Yes. Both payment creation (`execute_payment_api_v1_payments_post`) and admin reset (`reset_database_api_v1_admin_reset_post`) are callable.
3. **Security Risk:** If a model hallucinates or is prompted by an attacker (indirect prompt injection), it can trigger financial transactions or wipe database state without human oversight.

### Step 3: Account Read
- **Account ID:** `acc-101`
- **Verified Balance:** `1500000` (minor units = 15,000.00 INR)
- **Currency:** `INR`

### Step 4: Gate 3 Enforcement
1. **HTTP Status Code:** `401 Unauthorized` (`Invalid API key in request`).
2. **Backend Database Reachability:** Zero. The request is terminated at APISIX Gate 3 before reaching the API backend.
3. **Critical Invariant:** Direct Gate-2-to-backend routing would bypass all API gateway rate-limiting, authentication, logging, and WAF rules. Re-entering Gate 3 guarantees full API governance.
