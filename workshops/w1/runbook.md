# Workshop 1 presenter runbook: Give Flo the Right Tools

**Topic:** Modernizing APIs for AI Agents: From OpenAPI to MCP  
**Duration:** 45 minutes · **Profile:** `w1` · **Audience:** Beginners

Use this runbook with the [deck](../../docs/workshops/presentations/flo-bank-workshop-1.pptx),
[worksheet](worksheet.md), [answer key](answer-key.md), and
[live API/browser walkthrough](../../docs/workshops/w1-api-walkthrough.md).
Expected results are teaching targets, not evidence of a fresh run.

## 1. Prepare before the session

Complete the [full infrastructure and Python setup](../../docs/workshops/participant-infra-guide.md)
before using launcher verification or rehearsal. W1 needs no model provider key.
The CLI and Postman call MCP directly; customer chat is separate and defaults to scripted replies.
Run commands from the repository root in Bash on Linux/WSL.

```bash
docker compose --profile w3 pull --ignore-buildable
./scripts/workshop pull w1
./scripts/workshop preflight
./scripts/workshop switch w1
```

Shared image preparation is included because global preflight checks pinned images
used across the series. Run one workshop profile at a time.
Preserve earlier evidence and fictional data before resetting; reset replaces banking data.

```bash
./scripts/workshop reset w1 --yes
./scripts/workshop status
./scripts/workshop verify w1
.venv/bin/python workshops/w1/rehearsal_w1.py
```

The rehearsal overwrites `workshops/w1/evidence/rehearsal-evidence.json` and expects
`acc-101` to contain `1500000` paise. It verifies technical behavior, not delivery time.

Open these local URLs:

| URL | Purpose |
|---|---|
| `http://127.0.0.1:9080` | Customer page |
| `http://127.0.0.1:9080/docs` | Swagger API documentation |
| `http://127.0.0.1:9080/openapi.json` | Live broad API contract |
| `http://127.0.0.1:9080/mcp` | Broad MCP connection |
| `http://127.0.0.1:9080/mcp/curated` | Curated MCP connection |

Use the configured MCP URLs without trailing slashes. The gateway binds to host
loopback. When Docker runs remotely, forward the port from the presenter laptop:

```bash
ssh -N -L 9080:127.0.0.1:9080 <user>@<workshop-host>
```

## 2. Choose a client

### Direct MCP connection

An MCP-aware client can connect directly to either MCP URL using Streamable HTTP.
It handles initialization and discovery. A normal browser navigation sends GET
and does not provide an interactive tool catalog for this W1 configuration.

For authorized calls, configure a custom HTTP header on the MCP connection:

```text
X-API-Key: gate3-secret-token
```

Do not confuse a tool input form with connection-header configuration. Listing
tools does not require the banking key in this configuration; banking execution does.
If your client has no connection-header control, use the supplied HTTP collection.

### Postman HTTP collection

Import [Flo-Bank-W1-MCP.postman_collection.json](postman/Flo-Bank-W1-MCP.postman_collection.json).
This is an HTTP collection: it exposes the MCP messages explicitly. All requests
use POST with these headers:

```text
Content-Type: application/json
Accept: application/json, text/event-stream
```

Collection variables include `base_url=http://127.0.0.1:9080`,
`api_key=gate3-secret-token`, `account_id=acc-101`, and `case_id=case-501`.
Authorized requests already include `X-API-Key: {{api_key}}` in Headers.
The collection uses No Auth because the lab key is supplied as an explicit header.

Run the requests in numbered order. Broad discovery captures generated account
and payment-list names for later requests; inspect those variables if discovery
fails or the live contract changes. The broad account tool name is not necessarily
`get_account`; that stable name belongs to the curated contract.

| Request | Presenter purpose |
|---|---|
| 01 Initialize | Show protocol/server information |
| 02 Discover tools | Record actual broad count and names |
| 03 Read account | Demonstrate a broad authorized read |
| 04 Initialize curated | Connect to the completed interface |
| 05 Discover curated tools | Verify exactly `get_account` and `get_case` |
| 06 Read account | Demonstrate retained account capability |
| 07 Read support case | Demonstrate retained case capability |
| 08 Invalid API key | Inspect downstream denial |
| 09 Missing API key | Inspect downstream denial |
| 10 Excluded payment-list tool | Demonstrate lookup rejection |

Responses may be JSON or SSE, where JSON follows a `data:` prefix. Discovery
scripts parse both forms. Other responses can be inspected in the response body.

## 3. Opening and existing API: 0–5 minutes, slides 1–4

**Say:** “Flo needs to answer account questions and inspect support cases. The
bank already has these capabilities. Today we will generate tools, choose the
right scope, and preserve the bank's access checks.”

Explain an API as a defined interface through which one program requests an
operation from another. A tool has a name, structured inputs, and a result.
A model may propose a tool call; surrounding software sends the request.

In Swagger, expand `GET /api/v1/accounts/{id}`. Explain GET, path, placeholder,
parameter, operationId, and response schema. A schema describes data structure
and types. Use Try it out with `acc-101` and `gate3-secret-token` in X-API-Key;
leave Authorization empty for this W1 operator example. Documentation is public,
but banking operations require the gateway credential.

Show the customer page using `maya@flobank.demo` / `flo-demo`. Open Developer
Tools → Network → Fetch/XHR before signing in, filter by `banking`, and inspect
an account response. Browser accounts are `demo-checking` and `demo-savings`;
MCP uses `acc-101`. Browser calls go through a session-authenticated
`/demo-api/banking/...` proxy, then Gate 3; credentials stay on the server.
Keep card/dispute mutations optional and restore any card freeze. Transaction
history and spending remain sample activity.

**Ask:** “Which two capabilities does account support need?”
Expected answer: account read and support-case read.

## 4. Contract to tool interface: 5–12 minutes, slides 5–6

Show the account operation in `/openapi.json`. Explain that OpenAPI describes
HTTP operations and MCP provides discovery and structured invocation.

| MCP method | Meaning |
|---|---|
| `initialize` | Introduce the client and receive server information |
| `tools/list` | Discover tool definitions |
| `tools/call` | Invoke a tool with arguments |

Run Postman 01 Initialize or:

```bash
.venv/bin/python workshops/w1/client.py init
```

Point out protocolVersion, capabilities.tools, and serverInfo. The supplied CLI
does not retain a session between commands. Explain JSON-RPC: method names the
action, params supplies inputs, and id correlates request and response.

**Say:** “Generation maps the contract into tools. It cannot infer the support
team's permitted job from all the bank's operations.”

Show the logical path: MCP client → APISIX generated tool (Gate 2) → APISIX API
route (Gate 3) → banking service. These are responsibilities within the same
APISIX service in W1. W1 demonstrates an API-key boundary, not the richer policy
and signed-identity controls in later workshops.

## 5. Broad discovery: 12–22 minutes, slides 7–8

Run Postman 02 Discover tools or:

```bash
.venv/bin/python workshops/w1/client.py list
```

Record the actual count. Locate account/case reads, payment execution, and reset
without invoking mutations. Live discovery can differ from the saved broad checkpoint.

**Say:** “The generator represented the contract it received. The resulting
catalog includes capabilities outside Flo's support job.”

Explain read versus mutation and least privilege. Have pairs retain account/case
reads and remove payment, incident, and administrative operations outside the job.
Even read/list operations can be out of scope or expose sensitive information.
Discovery does not establish execution permission.

## 6. Curation and useful reads: 22–32 minutes, slides 9–12

Compare the [broad checkpoint](checkpoints/initial/openapi-broad.json) with the
[curated checkpoint](checkpoints/completed/openapi-curated.json). Show operationId,
descriptions, input types, and integer minor-unit balance semantics.
The completed checkpoint has no readOnlyHint annotation; descriptions and hints
are not authorization controls.

Run Postman 03, then 04–07. Alternatively:

```bash
.venv/bin/python workshops/w1/client.py call-account acc-101
.venv/bin/python workshops/w1/client.py --curated init
.venv/bin/python workshops/w1/client.py --curated list
.venv/bin/python workshops/w1/client.py --curated call-account acc-101
```

Expect exactly `get_account` and `get_case` in curated discovery. Generated
arguments use `pathParameters.id`. Fresh seed balance is `1500000` paise =
₹15,000, currency INR; record the actual returned balance on a modified ledger.
Postman 07 reads `case-501`; explain description, priority, and status.
The CLI has no call-case command; use Postman or the rehearsal for that read.

**Say:** “Curation is observable: the intended reads remain discoverable and usable.”

### Why the API-key field differs between catalogs

The broad OpenAPI account operation declares Authorization and X-API-Key header
parameters. The curated operation declares only the path ID. Consequently, the
broad tool can expose credential fields in its generated input schema, while
get_account's curated input form only asks for an ID. Inspect live tools/list
schemas to confirm what your client is displaying.

Both W1 routes forward the incoming HTTP X-API-Key header. Supply the credential
at the connection/request level for curated calls; its absence from the tool
schema does not remove Gate 3 authentication. The HTTP collection and CLI use
this connection-header approach for both endpoints.

## 7. Exclusion and authorization: 32–40 minutes, slides 13–14

Run Postman 10 after Broad discovery has captured the actual payment-list tool.
Expect lookup rejection at the curated endpoint. This uses an excluded read/list
operation, not a financial mutation. Do not run the CLI call-payment command or
invoke reset to demonstrate exclusion.

Run Postman 08 and 09. CLI equivalent for the invalid-key check:

```bash
.venv/bin/python workshops/w1/client.py --curated call-unauthorized
```

The CLI sends `invalid-secret`, rather than omitting the header. Expect an embedded
401/authorization denial and no successful account result. Missing-key and
invalid-key messages can differ.

**Say:** “The outer HTTP status describes the exchange with MCP. The embedded
result describes the banking request. An outer 200 does not guarantee banking success.”

Show [the W1 gateway routes](../../docker/apisix/apisix-w1.yaml): generated calls
use gateway base_url, headers forwards the caller's key, and `/api/v1/*` has key-auth.
Inspect relevant logs to substantiate the denial location:

```bash
docker compose --profile w1 logs --tail=100 apisix
curl -i http://127.0.0.1:9080/api/v1/accounts/acc-101
curl -i http://127.0.0.1:9080/api/v1/accounts/acc-101 \
  -H 'X-API-Key: gate3-secret-token'
```

Direct requests should return 401 without a key and 200 with the lab key.
The embedded denial alone does not establish database reachability. W1 does not
prove full customer isolation, production identity management, or complete tracing.

## 8. Configuration tour and live contract updates

| File | Responsibility |
|---|---|
| [docker/apisix/apisix-w1.yaml](../../docker/apisix/apisix-w1.yaml) | MCP routes, contract URLs, request base URL, forwarded key, Gate 3 key-auth |
| [src/api/openapi-curated.json](../../src/api/openapi-curated.json) | Curated contract served from the Docker API image |
| [curated checkpoint](checkpoints/completed/openapi-curated.json) | Completed teaching artifact to compare against the broad contract |
| [src/api/main.py](../../src/api/main.py) | Serves /openapi-curated.json, preferring the src/api copy |
| [docker-compose.yml](../../docker-compose.yml) | Mounts the selected APISIX profile configuration |

APISIX's openapi-to-mcp plugin runs inside the gateway; W1 has no separate MCP
handler for get_account. The operationId becomes its tool name, parameters become
inputs, and HTTP method/path determine the generated request. Tool calls use
base_url plus the substituted operation path. Here that sends the account read
back to Gate 3 at `http://127.0.0.1:9080/api/v1/accounts/acc-101`.

Changing only the checkpoint does not change the contract served by Docker.
For an intentional local experiment, update the served src/api contract and keep
the teaching checkpoint consistent. Then rebuild the API and recreate the gateway
to clear its generated catalog cache:

```bash
ACTIVE_PROFILE=w1 docker compose --profile w1 build api
ACTIVE_PROFILE=w1 docker compose --profile w1 up -d --no-deps --force-recreate api apisix
```

Rerun initialization, discovery, reads, exclusion, and denial checks before claiming
the running catalog changed. Use the prepared completed endpoint during timed delivery.

## 9. Review and close: 40–45 minutes, slides 15–16

Ask pairs to report one removed operation, one clearer description, and their
observed read/exclusion/authorization results. Save response bodies and relevant
route/log evidence. Distinguish expected targets from actual observed results.

**Say:** “Flo now has tools matched to its support job. The banking access check
still applies to tool calls. A case's text can inform an answer, but it cannot
grant execution authority.”

If presenting after W2–W4, connect these foundations to the policy, durable work,
and delegation controls participants have already seen. Otherwise bridge to W2.
After evidence is saved and the lab is no longer needed:

```bash
./scripts/workshop stop
```

## 10. Recovery notes

| Observation | Check/action |
|---|---|
| MCP URL works in an MCP client but not as a browser page | MCP client sends protocol messages; use Swagger for browser documentation |
| Curated input form has no API-key field | Configure X-API-Key as an HTTP connection/request header |
| Curated URL does not match | Use /mcp/curated without a trailing slash |
| Broad read uses wrong tool name | Run 02 Discover tools and inspect broad_account_tool |
| Connection refused | Check workshop status, port 9080, and SSH forwarding if remote |
| Swagger fails to load offline | Use /openapi.json or saved checkpoint; Swagger assets use a CDN |
| Tool count differs | Record live discovery, not a historical fixed count |
| Catalog remains old after editing | Check served src/api contract, rebuild image, recreate gateway, rediscover |
| Account balance differs | Record actual data; reset before the next fresh-seed rehearsal if needed |
| Outer response is 200 on denial | Inspect embedded downstream status and error |
| httpx import fails | Use .venv/bin/python and install worksheet/full setup dependencies |
