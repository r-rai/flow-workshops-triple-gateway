# Workshop 1 private demo runbook

Run commands from the participant repository root. Use an existing virtual environment with the API requirements installed. Examples use `.venv/bin/python`; attendees may use their equivalent activated Python environment. The CLI uses a fixed gateway address, `http://127.0.0.1:9080`.

## Before the room opens

These are operator preparation instructions, not commands run during package authoring. Profile switching stops the workshop Compose stack. Confirm this is your designated lab environment before switching. Reset restores seed data and removes lab changes; use it only when that reset is intended.

```bash
./scripts/workshop preflight
./scripts/workshop switch w1
./scripts/workshop status
./scripts/workshop reset w1 --yes
./scripts/workshop verify w1
```

The existing automated rehearsal also starts W1 and writes tracked historical evidence. To preserve the shared repository’s saved evidence, use the discrete read/denial commands below and save output locally rather than running `workshops/w1/rehearsal_w1.py` blindly.

Prepare three windows: UI at `http://localhost:9080`, terminal at the repo root, editor with broad/curated contracts and `docker/apisix/apisix-w1.yaml`. Verify both catalogs before presenting. Capture current output to an ignored local folder if desired:

```bash
mkdir -p .presenter-private/w1/live-evidence
.venv/bin/python workshops/w1/client.py list > .presenter-private/w1/live-evidence/broad-list.txt
.venv/bin/python workshops/w1/client.py --curated list > .presenter-private/w1/live-evidence/curated-list.txt
```

Those outputs establish discovery only. Rehearse all invocation commands as well. Keep credentials out of exported production evidence; the `gate3-secret-token` below is the repository’s synthetic lab key.

## A · Customer introduction · minutes 2–4

Login: `maya@flobank.demo` / `flo-demo`. Ask “What is my balance?” or simply show the dashboard. Observe and announce the displayed simulation/live mode honestly. Do not start another Compose profile or change provider settings during the timed session.

Fallback: use a prepared dashboard screenshot or describe Maya’s request from slide 1. The UI is a scenario introduction, not evidence of MCP invocation. Do not compare its balance with Acme’s `acc-101` balance.

## B–C · Broad generation and successful account read · minutes 11–17

```bash
.venv/bin/python workshops/w1/client.py init
.venv/bin/python workshops/w1/client.py list
.venv/bin/python workshops/w1/client.py call-account acc-101
```

Point out initialization capabilities, actual tool count, generated account name, and actual account data. The CLI uses substring selection to find an account tool; if the generated catalog changes, inspect its choice before relying on it. For this curated checkpoint there is exactly one account tool.

Expected seeded account: Acme Retail Checking, `acc-101`, balance `1500000` minor units, currency `INR`, status `active`. Show ₹15,000. Do not imply an API read settles a case or changes a balance.

## D · Prepared curated contract · minutes 25–29

Open `workshops/w1/checkpoints/initial/openapi-broad.json` and `workshops/w1/checkpoints/completed/openapi-curated.json`. The broad checkpoint may differ from the currently served `/openapi.json`; use live discovery as the authoritative runtime catalog.

```bash
.venv/bin/python workshops/w1/client.py --curated init
.venv/bin/python workshops/w1/client.py --curated list
```

Expected curated names: `get_account` and `get_case`. The runtime fetches `/openapi-curated.json`, which the API serves from the completed checkpoint. Show that path in the route configuration. The generated account arguments are nested under `pathParameters`, not a flattened `account_id` field.

Use the prepared endpoint for the reveal. Official plugin documentation describes caching of generated tools; do not promise an immediate reload after editing a contract. Confirm reload behavior separately if you later turn this into a contract deployment lab.

## E1 · Successful curated reads · minutes 29–31

```bash
.venv/bin/python workshops/w1/client.py --curated call-account acc-101
```

The CLI has no case subcommand. This snippet reuses its existing request/SSE parser and calls `get_case` explicitly:

```bash
.venv/bin/python - <<'PY_CASE'
import importlib.util
import json
spec = importlib.util.spec_from_file_location('w1client', 'workshops/w1/client.py')
client = importlib.util.module_from_spec(spec)
spec.loader.exec_module(client)
client.MCP_ENDPOINT = client.GATEWAY_URL + '/mcp/curated'
status, result = client.send_mcp(
    'tools/call',
    {'name': 'get_case', 'arguments': {'pathParameters': {'id': 'case-501'}}},
    headers={'X-API-Key': 'gate3-secret-token'},
)
print('MCP transport HTTP status:', status)
print(json.dumps(result, indent=2))
PY_CASE
```

Expected case fixture: `case-501`, customer `cust-8801`, issue type `disputed_transaction`, priority `medium`, status `open`. Its description contains an unstructured amount phrase; do not convert it to a settlement amount. Do not claim a verified relationship to the account or Maya.

## E2 · Excluded-tool rejection · minutes 31–33

Ask for a prediction before running. Use a real tool from the current broad catalog that is absent from the curated catalog. Choose the payment-list read tool to keep this proof free of financial mutations. This snippet discovers the name rather than relying on a remembered name:

```bash
.venv/bin/python - <<'PY_EXCLUDED'
import importlib.util
import json
spec = importlib.util.spec_from_file_location('w1client', 'workshops/w1/client.py')
client = importlib.util.module_from_spec(spec)
spec.loader.exec_module(client)
status, broad = client.send_mcp('tools/list')
if status != 200:
    raise SystemExit('Broad discovery failed; use labelled fallback evidence.')
names = [tool['name'] for tool in broad.get('result', {}).get('tools', [])]
candidates = [name for name in names if 'list_payments' in name.lower() and name.lower().endswith('_get')]
if len(candidates) != 1:
    raise SystemExit('Expected one payment-list read tool; inspect discovery or use fallback.')
name = candidates[0]
client.MCP_ENDPOINT = client.GATEWAY_URL + '/mcp/curated'
status, curated = client.send_mcp('tools/list')
if status != 200 or 'error' in curated or 'result' not in curated:
    raise SystemExit('Curated discovery failed; use labelled fallback evidence.')
curated_names = [tool['name'] for tool in curated['result'].get('tools', [])]
if name in curated_names:
    raise SystemExit('Tool is present in curated catalog; the expected exclusion is missing.')
print('Attempting actual broad tool on curated endpoint:', name)
status, result = client.send_mcp(
    'tools/call', {'name': name, 'arguments': {}},
    headers={'X-API-Key': 'gate3-secret-token'},
)
print('MCP transport HTTP status:', status)
print(json.dumps(result, indent=2))
PY_EXCLUDED
```

Expected recorded behavior: `isError: true` and “Tool … not found.” Inspect the actual response rather than announcing a result before it appears. The proof is local to `/mcp/curated`; `/mcp` remains intentionally broad.

## E3 · API authentication rejection · minutes 33–36

```bash
.venv/bin/python workshops/w1/client.py --curated call-unauthorized
```

This command sends an invalid key, rather than literally omitting it as its console text suggests. Narrate “invalid credential.” The plugin may return HTTP `200` for the MCP response while the text content includes downstream `status: 401` and “Invalid API key in request.” Look inside the result.

Expected outcome is key authentication failure, not a proof of role, account ownership, or argument policy. If it succeeds, stop calling it a denial and use historical evidence to explain the intended boundary; investigate the environment after the session.

## F · Routing and observability · minutes 36–41

Open `docker/apisix/apisix-w1.yaml` and highlight:

- `w1_mcp_curated_route`: `/mcp/curated`, curated OpenAPI source, `base_url: http://127.0.0.1:9080`, forwarded `X-API-Key`.
- `w1_gate3_api`: `/api/v1/*`, `key-auth`, upstream `api:8000`.
- The distinction between public discovery and downstream API authentication in this teaching profile.

Optional direct comparison, only if time remains:

```bash
curl -i --max-time 10 http://127.0.0.1:9080/api/v1/accounts/acc-101
curl -i --max-time 10 -H 'X-API-Key: gate3-secret-token' http://127.0.0.1:9080/api/v1/accounts/acc-101
```

Expect direct HTTP `401`, then `200` with the account data. These calls bypass MCP intentionally to compare API behavior.

Read available container logs without changing the profile:

```bash
docker compose logs --tail 60 apisix api
```

Logs may contain no relevant access records depending on logging configuration. Select and redact a relevant excerpt during rehearsal. Configured backend instrumentation does not guarantee a complete gateway-to-backend trace. W1’s route file contains no gateway tracing plugin. Do not claim that a rejected request never reached the database based solely on an outer status or an absent log line.

## Recovery and completion checklist

If transport fails: check the fixed address and W1 status for at most 60 seconds, then switch to labelled fallback. If discovery is unexpected: report the actual catalog, avoid invoking mutation tools, and use recorded catalog comparison. If reads fail: display the recorded successful read as historical evidence. If logs are unhelpful: explain the configured route and observed responses, then identify the missing correlation.

Before delivery, record the date and machine for a fresh rehearsal; confirm two intended reads, excluded-tool rejection, invalid-key rejection, and the total spoken duration. Keep the reset and profile-switch steps outside the timed session.
