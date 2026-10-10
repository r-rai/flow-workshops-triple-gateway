"""Gateway primer and current Incident Room delivery guidance for Workshop 4."""

def expand_workshop_four(deck, add):
    original = deck['slides']
    deck['slides'] = []
    deck['duration'] = 150
    deck['sources'] += ['workshops/w4/runbook.md', 'src/demo/incident.py',
                        'src/adapter/server.py', 'docker/apisix/apisix-w4.yaml']
    add(deck, 'API gateway: govern business requests', 'Gateway primer / 15 minutes before the lab', kind='cover',
        lead='API gateway → AI gateway → MCP gateway\nThen investigate and repair Flo Bank.',
        takeaway='15-minute gateway primer + 135-minute incident-response lab',
        notes='Introduce the sequence: API gateways govern business-service traffic; AI gateways manage model traffic; MCP gateways govern tool-facing traffic. These are responsibilities, not necessarily three products. This deck adds a 15-minute primer before the existing 135-minute lab; start the lab clock at the incident opening. Ask which gateways participants already operate. Source: https://apisix.apache.org/learning-center/mcp-protocol-ai-gateway/')
    add(deck, 'How an API gateway works', 'Gateway primer', steps=[
        ('Client', 'Send method, path and credential'),
        ('Gateway', 'Match route; apply configured controls'),
        ('Service', 'Enforce business authorization'),
        ('Response', 'Return result; record telemetry')],
        takeaway='A successful HTTP response establishes delivery, not business legitimacy.',
        notes='Walk through an account read and a payment write. A gateway matches a configured route, applies authentication, limits and transformation as configured, then forwards to an upstream. The service still enforces domain rules. In W4, APISIX protects the route while the banking API validates JWT audience/scopes and transaction invariants. Do not imply every rule lives in APISIX. Source: https://apisix.apache.org/docs/apisix/getting-started/')
    add(deck, 'API gateway capabilities', 'Gateway primer', cards=[
        ('ACCESS', 'Authentication, routing and request-rate controls.'),
        ('RELIABILITY', 'Upstream balancing, timeouts and configured retries.'),
        ('VISIBILITY', 'Request logs, metrics and distributed trace integration.')],
        takeaway='For financial writes, retries require a stable business idempotency key.',
        notes='Explain one capability at a time. Access controls decide whether a request reaches a service; reliability controls determine how traffic reaches available upstreams; telemetry explains what happened. W4 uses stable financial keys in the service for one-effect retries. Gateway retries alone do not make payments idempotent. These are configured capabilities, not a claim that every plugin is enabled in this lab. Source: https://apisix.apache.org/docs/apisix/plugins/')
    add(deck, 'AI gateway: manage model consumption', 'Gateway primer', cards=[
        ('MODEL ACCESS', 'A governed entry point for configured model providers.'),
        ('CONSUMPTION', 'Token limits, output limits and inference allowance.'),
        ('OPERATIONS', 'Configured routing, resilience and model-traffic telemetry.')],
        takeaway='In this lab, an adapter reserves the inference allowance before dispatch.',
        notes='Distinguish general APISIX AI capabilities from the W4 implementation. Model proxying and configured routing can centralize provider access. W4 implements a pre-dispatch token reservation in src/adapter/server.py; do not present it as proof of production distributed budget accounting. A refusal or inference denial cannot authorize an independent payment. Sources: https://apisix.apache.org/docs/apisix/plugins/ai-proxy-multi/ and https://apisix.apache.org/docs/apisix/plugins/ai-rate-limiting/')
    add(deck, 'How the AI gateway evaluates a request', 'Gateway primer', steps=[
        ('Receive', 'Messages + requested output'),
        ('Reserve', 'Estimate input; reserve output'),
        ('Dispatch', 'Call provider only if allowed'),
        ('Reconcile', 'Update allowance using actual usage')],
        takeaway='Reject projected overuse before making the provider call.',
        notes='Use a familiar allowance analogy: a small amount already consumed does not mean a huge next request fits. W4 estimates serialized input at roughly four characters per token and caps reserved output at 2048. Its counter and lock are process-local, so multi-worker/distributed state is production work. Do not run the budget-reset endpoint during the incident to manufacture a result.')
    add(deck, 'MCP gateway: expose governed capabilities', 'Gateway primer', headers=['Concern', 'Interface', 'Enforcement'], rows=[
        ['Discover', 'tools/list returns named tools', 'Expose the intended capability surface'],
        ['Invoke', 'tools/call carries arguments', 'Validate caller, tool and arguments'],
        ['Execute', 'Call a downstream API', 'Preserve downstream authorization']],
        takeaway='Tool discovery is useful; authorization must hold at invocation.',
        notes='Introduce MCP as a protocol for connecting clients to tools and other server capabilities. Focus on tools/list and tools/call for this workshop. MCP does not inherently make every exposed tool safe. APISIX can expose OpenAPI operations as tools; W4 uses the protected adapter/OPA path for argument-aware tool decisions. Sources: https://modelcontextprotocol.io/specification/2025-11-25/server/tools and https://apisix.apache.org/docs/apisix/plugins/openapi-to-mcp/')
    add(deck, 'How the MCP gateway handles a payment', 'Gateway primer', steps=[
        ('Agent', 'Select create_payment'),
        ('MCP boundary', 'Read identity and actual arguments'),
        ('OPA', 'Allow, deny or require approval'),
        ('API boundary', 'Authorize the business operation')],
        takeaway='HTTP 200 may carry a tool error. Read the MCP decision inside the response.',
        notes='Show the difference between transport success and successful tool execution. The adapter can return an MCP result with isError=true and POLICY_DENIED text under HTTP 200. Identity must come from validated credentials, not a role supplied in the prompt. Explain that approved calls still encounter the banking boundary. Source: https://modelcontextprotocol.io/specification/2025-11-25/server/tools')
    add(deck, 'Three gateways, three different decisions', 'Gateway primer', headers=['Boundary', 'Traffic', 'Decision in W4'], rows=[
        ['API / Gate 3', 'HTTP business requests', 'Correct audience, scope and business authority?'],
        ['AI / Gate 1', 'Model inference', 'Does projected usage fit the allowance?'],
        ['MCP / Gate 2', 'Tool discovery and invocation', 'May this caller use this tool with these arguments?']],
        takeaway='A decision at one boundary does not replace checks on another route.',
        notes='Ask the audience to classify three requests: an account GET, a model completion, and create_payment via tools/call. Explain why an inference denial says nothing about an independent direct banking call. APISIX hosts the three logical boundaries; adapters and the banking API supply additional checks. Ground the model in the actual W4 routes, rather than claiming three physically isolated gateways.')
    add(deck, 'Flo Bank: Triple-Gate architecture', 'Gateway primer', kind='w4_architecture',
        takeaway='Agent orchestration connects model output to tools; business authority stays explicit.',
        notes='Follow the top inference lane, then the lower execution lane. Model output returns to the agent backend, which requests tools. Gate 2 asks OPA about identity and actual arguments. Gate 3 includes APISIX routing and banking API JWT validation. Independent review binds exact proposal values; the API manages settlement, stable retry keys and task/payment binding. Jaeger supplies observed traces. The isolated vulnerable ledger is separate from this protected lane. The diagram uses editable PowerPoint shapes.')
    add(deck, 'Presenter lab and QR observers', 'Gateway primer', cards=[
        ('LOCAL PRESENTER', 'Runs fixed scenarios against protected services and a separate replay ledger.'),
        ('QR AUDIENCE', 'Reads curated recorded evidence. No approval or payment execution.'),
        ('SHARED METHOD', 'Predict the decision; inspect caller, arguments, response and effect.')],
        takeaway='The observer recording does not synchronize live with the presenter ledger.',
        notes='Explain the two participation modes before people scan. Local pairs can edit policy and identity checkpoints. Phones use the separate observation entrypoint, event access code, and curated runs. The audience code grants viewing only; it is distinct from the local reviewer password. Observer timelines identify the selected recorded run and label original incident context separately.')
    add(deck, 'Join the Incident Room', 'Audience access', kind='audience_access',
        takeaway='Scan → enter the event code → select a recorded run → inspect the evidence.',
        notes='Allow the room time to scan. The QR encodes only https://w4.ravirai.in/workshop-4; the event code is entered separately on the page. Verify the displayed expiry against the running observer service before delivery. This audience code is intentionally shown on the event slide, while reviewer and sandbox secrets remain private. The repository deck is reusable without a live code; the separate event deck includes the configured audience code.')

    # Existing timed lab follows the primer; keep its chapter clock intact.
    original[0]['kind'] = 'statement'
    original[0]['takeaway'] = 'Start the 135-minute lab clock / Become Flo Bank’s response team'
    deck['slides'] += original

    def before(title, new_slide):
        index = next(i for i, slide in enumerate(deck['slides']) if slide['title'] == title)
        deck['slides'].insert(index, new_slide)

    def extra(title, time, **kwargs):
        add(deck, title, time, **kwargs)
        return deck['slides'].pop()

    before('Gate 2: isolate the reason for denial', extra('Why 140 / 100,000 can still produce a denial', '20–33 min',
        headers=['Budget component', 'Illustrative run', 'Interpretation'], rows=[
            ['Already used', '140 tokens', 'Existing usage is below the limit'],
            ['Remaining headroom', '99,860 tokens', 'Available before the next request'],
            ['Incoming request', 'Oversized prompt + 512 output', 'Projected total exceeds the allowance']],
        takeaway='The error omits incoming estimates. 140 itself did not exceed 100,000.',
        notes='Show GET /ai/budget and the 200 headroom response, then the 429 inference denial. Explain accumulated usage + estimated prompt + reserved output > limit. The workshop constructs a synthetic large prompt from available headroom; the live counter may differ from 140. Inference consumption and the bank account balance are different budgets. Expected protected effect is zero, but that alone does not prove direct payment protection.'))
    before('Exercise: repair the prepared local policy', extra('Inspect the actual MCP payment payload', '33–53 min', kind='request_payload',
        code='{"jsonrpc":"2.0","id":"<run-id>",\n "method":"tools/call",\n "params":{"name":"create_payment","arguments":{\n   "account_id":"acc-101",\n   "beneficiary":"vendor-alpha",\n   "amount":900000000,"currency":"INR"\n }}}',
        takeaway='Evidence drawer → Tool policy event → arguments.params.arguments',
        notes='This is the excessive-amount scenario: 900,000,000 paise equals ₹90 lakh, to the intended permitted vendor. In the server export, events[].arguments stores the JSON request body, not events[].request. Inspect the response reason AMOUNT_EXCEEDS_TRANSFER_CEILING and measured zero effect. The original incident ticket is background context; it does not mean this protected request executed the isolated replay.'))
    before('Use an independent reviewer session', extra('Retrieve the local reviewer password', '85–103 min',
        code='docker compose exec -T api printenv W4_REVIEWER_PASSWORD',
        lead='Run privately on the local lab host. Never project the result.',
        takeaway='Separate browser session + reviewer login + exact proposal review.',
        notes='Prepare a private/incognito window or separate profile before creating the proposal. Sign in with maya@flobank.demo / flo-demo, select Independent reviewer, enter the running API password and click Open reviewer session. Another tab shares requester cookies. The password differs from the audience code. If absent, configure it in .env and recreate the API before creating proposals; a restart does not load changed environment. Proposals expire after ten minutes. See workshops/w4/runbook.md section 2.'))

    for item in deck['slides']:
        if item['title'] == 'Gate 3: the attacker changes routes':
            item['notes'] += ' The wrong-audience scenario actually performs GET /api/v1/accounts/acc-101 with an MCP-audience token; the insufficient-scope scenario attempts POST /api/v1/payments. Do not describe the first as a payment attempt.'
        elif item['title'] == 'Exercise: request only an entitled scope':
            item['notes'] += ' Before each new session, restore initial/identity.json requested_scope to api:payments:write if a previous exercise left the corrected read scope. Export matching JWT settings from the running API using the runbook when customized.'
        elif item['title'] == 'A second agent creates a second boundary':
            item['notes'] += ' Inspect the same completed delegation run; do not create another ₹1,500 settlement for this chapter. Foreign access and unauthorized completion tests occur before review; mismatch binding occurs after settlement.'
        elif item['title'] == 'Presenter preparation & source guide':
            item['notes'] += ' Use workshops/w4/runbook.md for persisted setup, password retrieval and recovery. The --live runner repeats the full suite with an additional live comparison; use the standalone console scenario for only one bounded review.'
