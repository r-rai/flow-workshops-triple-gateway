# Workshop 1: live API and browser walkthrough

Use this walkthrough after welcoming participants and introducing the Flo Bank
story, before asking which capabilities the support assistant needs. Allow
2–3 minutes for the setup tour. Keep longer card/dispute demonstrations optional
so the MCP exercise still fits its 45-minute slot.

## Prepare the running profile

Complete the [Python and infrastructure setup](participant-infra-guide.md), then
run from the repository root:

```bash
./scripts/workshop pull w1
./scripts/workshop switch w1
```

`pull w1` prepares the current images, including the API application. When
applying local source changes to an already running W1 stack, rebuild and
recreate the API and gateway:

```bash
ACTIVE_PROFILE=w1 docker compose --profile w1 build api
ACTIVE_PROFILE=w1 docker compose --profile w1 up -d --no-deps --force-recreate api apisix
```

Workshop profiles default to `DEMO_BACKEND_MODE=enterprise`. W1 defaults to
scripted chat, so this walkthrough needs no model key. If your `.env` overrides
these defaults, set `DEMO_BACKEND_MODE=enterprise` and `DEMO_CHAT_MODE=scripted`
and recreate the services using the commands above.

Before a fresh-seed technical rehearsal, preserve any evidence and lab data you
need, then run:

```bash
./scripts/workshop reset w1 --yes
./scripts/workshop verify w1
```

Reset replaces the fictional banking data, including persisted demo card/case
changes. W1 verification and the automated rehearsal expect `acc-101` to have
`1500000` paise (₹15,000). A previously used ledger may have a different balance;
a successful account read alone does not satisfy that seed expectation.

## Show the existing API contract

Open these URLs on the Docker host:

| URL | What to show |
|---|---|
| `http://localhost:9080/docs` | Swagger UI with the live API operations |
| `http://localhost:9080/openapi.json` | The live contract consumed by the broad MCP generator |
| `http://localhost:9080` | Flo Bank customer page |

Expand `GET /api/v1/accounts/{id}` in Swagger. Point out the method, path,
`operationId`, account identifier, and response schema. Explain that balances
are integer minor units (paise), then connect the same operation to its generated
MCP tool later in the worksheet.

For **Try it out**, enter `acc-101` and the lab key `gate3-secret-token` in the
`X-API-Key` field. Leave `Authorization` empty for this W1 operator example.
A request without a valid gateway key is rejected with HTTP 401. Documentation
routes are public; banking operations still pass through Gate 3. Do not invoke
payment or administrative mutations during this walkthrough.

Swagger UI loads JavaScript and CSS from a CDN. For a disconnected presentation,
use the JSON contract or the saved
[broad checkpoint](../../workshops/w1/checkpoints/initial/openapi-broad.json).
The saved checkpoint can differ from the running API; use live discovery to
record the actual tool count.

## Show real requests from the bank page

1. Open Developer Tools → **Network** → **Fetch/XHR** before signing in.
2. Sign in with `maya@flobank.demo` / `flo-demo`.
3. Filter by `banking` and inspect the account, card, and case responses.
4. Use **Freeze demo card**, inspect its POST body, then unfreeze the card.
5. Optionally dispute a sample debit charge, inspect the case POST and response,
   then reload to show that the case persists.

| Browser request | Downstream banking request |
|---|---|
| `GET /demo-api/banking/accounts/demo-checking` | `GET /api/v1/accounts/demo-checking` |
| `GET /demo-api/banking/accounts/demo-savings` | `GET /api/v1/accounts/demo-savings` |
| `GET /demo-api/banking/cards/card-2048` | `GET /api/v1/cards/card-2048` |
| `POST /demo-api/banking/cards/card-2048/state` | `POST /api/v1/cards/card-2048/state` |
| `GET /demo-api/banking/cases` | `GET /api/v1/cases`, filtered to the demo customer |
| `POST /demo-api/banking/cases` | Checks existing cases, then creates a case through `POST /api/v1/cases` if needed |

The card POST body contains `{"locked":true}` or `{"locked":false}`. The browser's
case POST contains `{"transaction_id":"tx-1004"}`; the server derives the demo
customer and case description before forwarding the banking request.

Explain the actual request path:

```text
Browser → session-authenticated /demo-api/banking/... proxy
        → APISIX Gate 3 /api/v1/... → banking API → database
```

The browser paths are customer-facing proxy routes, not direct `/api/v1` calls.
The gateway key and scoped customer JWT stay on the server. The proxy limits
requests to the demo accounts, card, and customer cases; it does not expose
payments, admin actions, or arbitrary account IDs. The underlying W1 lab is not
a demonstration of complete production customer authorization.

Scripted balance/card/dispute prompts use these browser routes. In live chat,
model tool calls run on the server; the browser sees `/demo-api/chat` and the
subsequent banking refresh. Mutation controls use the browser banking routes in
both chat modes. Transaction history and spending remain labeled sample
activity, not a live transaction feed. Card changes and case records persist
across reloads and sign-outs in enterprise mode. Standalone simulated mode
keeps its session-local behavior.

Gateway errors remain visible instead of substituting fixture balances. A
browser-request list demonstrates the customer-facing calls; use routing or
gateway logs to substantiate the downstream Gate 3 hop.

## Access from a presenter laptop

Port 9080 binds to the Docker host's loopback interface. If the stack runs on a
remote host, use SSH forwarding from your laptop:

```bash
ssh -N -L 9080:127.0.0.1:9080 <user>@<workshop-host>
```

Open the same `localhost:9080` URLs on the laptop. If local port 9080 is busy,
forward local port 19080 instead and browse to `http://localhost:19080`.

## Transition to the MCP exercise

Say: “We have seen the existing banking APIs and a customer page using them.
Which capabilities does Flo need to answer account questions and inspect support
cases?” Then continue with [MCP initialization and discovery](../../workshops/w1/worksheet.md).
The customer page uses `demo-checking` and `demo-savings`; the MCP account
exercise uses the separate seeded account `acc-101`.

## Verification

With W1 running in enterprise mode and the full Python environment installed:

```bash
.venv/bin/python -m pytest tests/test_demo_banking_proxy.py tests/test_demo_bank.py tests/test_demo_live_llm.py -q
```

For browser verification, install Playwright and its Chromium browser in your
chosen test environment. If Playwright is installed outside the repository,
set `NODE_PATH` to that installation's `node_modules` directory, then run:

```bash
FLO_DEMO_URL=http://127.0.0.1:9080 node tests/demo_bank_gateway_browser.cjs
```

The browser test changes the fictional demo card state and restores it, and
creates or reuses a dispute for `tx-1004`. It checks visible REST requests,
persistence after reload, upstream failure handling, and logout. The existing
`tests/demo_bank_browser.cjs` targets standalone simulated mode. These technical
checks do not measure spoken delivery time.
