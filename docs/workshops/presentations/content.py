"""Editable slide content, aligned to the repository's workshop delivery stories."""

DECKS = []


def deck(number, title, subtitle, duration):
    d = dict(number=number, title=title, subtitle=subtitle, duration=duration, slides=[],
             sources=[f"docs/workshops/workshop-{number}-story.md",
                      f"workshops/w{number}/worksheet.md", f"workshops/w{number}/answer-key.md",
                      "docs/workshops/delivery-plan.md"])
    DECKS.append(d)
    return d


def slide(d, title, time, *, lead="", cards=None, rows=None, headers=None,
          code=None, steps=None, takeaway="", notes="", kind="content"):
    d["slides"].append(dict(title=title, time=time, lead=lead, cards=cards,
                            rows=rows, headers=headers, code=code, steps=steps,
                            takeaway=takeaway, notes=notes, kind=kind))


w1 = deck(1, "Give Flo the right tools", "Modernizing APIs for AI Agents: From OpenAPI to MCP", 45)
slide(w1, w1["title"], "0–5 min", kind="cover", lead=w1["subtitle"],
      takeaway="Generate • Curate • Preserve authorization",
      notes="Open with the support request: Flo needs to read an account and understand a case. Introduce fictional Flo Bank and the audience's role as the integration team. W1 uses the native APISIX openapi-to-mcp plugin; this CLI lab needs no provider key. Prepare the stack before the clock starts.")
slide(w1, "One bank. Four engineering questions.", "0–5 min", cards=[
    ("01 / CAPABILITIES", "Which API operations should an agent discover?"),
    ("02 / AUTHORITY", "Who may execute a tool, with which arguments?"),
    ("03 + 04 / OPERATIONS", "Can work survive failure? Can the boundaries withstand an attack?")],
    takeaway="Today: build a purposeful tool catalog over existing banking APIs.",
    notes="Briefly position W1 within the series. W2 adds execution governance, W3 durable work, and W4 incident response and delegation. Each workshop starts independently from prepared lab data.")
slide(w1, "The 45-minute route", "0–5 min", headers=["Time", "Activity", "Evidence"], rows=[
    ["0–5", "Support request + API tour", "Minimum required capabilities"],
    ["5–12", "OpenAPI and MCP", "Initialization response"],
    ["12–22", "Inspect generated tools", "Broad catalog"],
    ["22–32", "Curate and invoke", "Two tools + successful read"],
    ["32–40", "Preserve Gate 3", "Embedded authorization denial"],
    ["40–45", "Review and questions", "Capability design explanation"]],
    notes="Use these as segment boundaries, not time allocated to every individual slide. Downloads and profile setup are outside the 45-minute session. Open the worksheet for copyable commands.")
slide(w1, "Start with the customer's job", "0–5 min", lead="“What is my account balance, and what is happening with my case?”", cards=[
    ("NEEDED", "Read the account. Read the support case. Return clear identifiers and units."),
    ("EXCESS CAPABILITY", "Payments, incident mutations and database resets exceed this support task."),
    ("LIVE API TOUR", "Open localhost:9080/docs. Inspect an account operation and the browser's network requests.")],
    takeaway="The customer's job defines the tool surface.",
    notes="Show the live method, path, input and response, then connect it to the bank page. Browser demo accounts are demo-checking and demo-savings; the MCP exercise uses acc-101. Documentation access does not authorize banking operations. Keep optional card/dispute mutations out of the timed path.")
slide(w1, "An HTTP contract becomes a tool interface", "5–12 min", headers=["Concern", "OpenAPI", "MCP in this lab"], rows=[
    ["Describe", "HTTP paths, methods, schemas", "Named tools + input schemas"],
    ["Discover", "Read a service contract", "Initialize, then list tools"],
    ["Invoke", "Send an HTTP request", "Call a tool with arguments"],
    ["Govern", "Backend/API controls", "Preserve downstream controls"]],
    takeaway="Generation maps structure; people design capability and intent.",
    notes="Ask what a generator can infer from a contract and what requires business context. Keep the comparison grounded in this lab, rather than presenting an exhaustive protocol comparison.")
slide(w1, "Follow the generated call", "5–12 min", steps=[
    ("MCP client", "Initialize → discover → invoke"),
    ("APISIX / MCP", "Translate the selected tool"),
    ("APISIX / Gate 3", "Validate API credentials"),
    ("Banking API", "Read business data")],
    takeaway="A translated tool call must re-enter the API enforcement path.",
    notes="These are logical stages, not four separate gateway products. W1 demonstrates API-key validation at Gate 3. W2–W4 introduce richer signed identities and scope controls. Show the actual route/log evidence later.")
slide(w1, "Demo: initialize and discover", "12–22 min", code=".venv/bin/python workshops/w1/client.py init\n.venv/bin/python workshops/w1/client.py list",
    lead="Inspect the actual catalog returned by the running gateway.",
    takeaway="Record today's tool count. Find reads, payments and administrative operations.",
    notes="Run from the repository root. The supplied CLI does not retain a session between commands. Locate the generated payment and reset tools without invoking them. The broad tool count depends on the served API contract; do not promise a fixed number.")
slide(w1, "Generated correctly. Scoped too broadly.", "12–22 min", cards=[
    ("READ", "Account and case queries match the support request."),
    ("MOVE MONEY", "A payment mutation changes the consequence of a mistaken tool choice."),
    ("ADMINISTER", "A reset operation belongs to lab administration, outside support work.")],
    takeaway="Pair prompt: retain, remove or rename each capability.",
    notes="Let participants inspect the broad checkpoint at workshops/w1/checkpoints/initial/openapi-broad.json. Existing authorization still applies to broad tools; discovery alone does not prove a call is authorized.")
slide(w1, "Design two tools that explain their job", "22–32 min", cards=[
    ("get_account", "Read one account using its ID. Make balance units and currency explicit."),
    ("get_case", "Read one support case using its ID. Treat returned case text as data."),
    ("EXCLUDE", "Remove unrelated payment and administrative operations from this catalog.")],
    takeaway="Clear semantics guide selection. Server controls enforce access.",
    notes="Compare workshops/w1/checkpoints/completed/openapi-curated.json. Generated inputs use pathParameters.id. The completed checkpoint contains no readOnlyHint annotation. Descriptions or hints alone are not authorization.")
slide(w1, "Exercise: curate the support contract", "22–32 min", steps=[
    ("Inspect", "Compare broad and completed contracts"),
    ("Choose", "Keep account + case reads"),
    ("Explain", "Improve one tool description"),
    ("Verify", "Check the served curated catalog")],
    takeaway="Deliverable: one removed operation, one improved description, discovery evidence.",
    notes="Allocate a short pair discussion within this ten-minute block. Use the prepared completed endpoint for executable comparison. A local file edit does not update the running catalog by itself; check plugin caching/refresh before claiming a live change.")
slide(w1, "Demo: a useful account read", "22–32 min", code=".venv/bin/python workshops/w1/client.py call-account acc-101",
    lead="Fresh seed: 1,500,000 paise = ₹15,000.",
    takeaway="Record account ID, actual balance, and currency from the response.",
    notes="Explain integer minor units: 100 paise equals one rupee. If the ledger has changed, record the returned result rather than asserting the fresh-seed balance. This read demonstrates an actual governed API result.")
slide(w1, "Demo: invoke the curated endpoint", "22–32 min", code=".venv/bin/python workshops/w1/client.py --curated init\n.venv/bin/python workshops/w1/client.py --curated list\n.venv/bin/python workshops/w1/client.py --curated call-account acc-101",
    lead="/mcp/curated exposes exactly get_account and get_case.",
    takeaway="Prove discovery and successful invocation against the running endpoint.",
    notes="The broad endpoint is /mcp. The curated endpoint is preconfigured. Use the W1 rehearsal's case-read and excluded payment-list checks as additional evidence. A rejected removed read/list operation proves exclusion without executing a financial mutation.")
slide(w1, "Exclusion must hold at invocation too", "32–40 min", headers=["Check", "Expected observation"], rows=[
    ["Curated discovery", "Only get_account and get_case"],
    ["Permitted read", "Account/case result returned"],
    ["Excluded tool call", "Tool lookup rejects the operation"],
    ["Missing API credentials", "Gate 3 authorization failure"]],
    takeaway="Catalog design and downstream authorization solve different parts of the problem.",
    notes="The rehearsal invokes an actual broad payment-list tool against the curated endpoint. Do not invoke payment mutations or administrative resets merely to show absence. Evidence for routing is needed to attribute the downstream denial to Gate 3.")
slide(w1, "Demo: the banking boundary still applies", "32–40 min", code=".venv/bin/python workshops/w1/client.py --curated call-unauthorized",
    lead="Inspect the embedded downstream response and gateway routing evidence.",
    takeaway="An outer MCP HTTP success can contain a failed downstream operation.",
    notes="Ask participants to find the embedded HTTP status and confirm that no successful account result was returned. W1 proves the lab's API-key boundary; it does not prove full customer-specific authorization or production identity management.")
slide(w1, "What evidence earns a pass?", "40–45 min", cards=[
    ("PURPOSEFUL", "Two intended tools are discoverable and callable."),
    ("RESTRICTED", "Excluded operations fail tool lookup in the curated catalog."),
    ("GOVERNED", "Authorized reads work; missing downstream credentials still fail.")],
    takeaway="Explain one design choice using a response you observed.",
    notes="Have pairs report their removed operation, clearer description and authorization evidence. Save the contract and invocation/denial output. Ask where the evidence would be insufficient without routing logs.")
slide(w1, "Next: the tool reads an attacker’s instructions", "40–45 min", kind="statement",
    lead="A useful catalog is the beginning. Execution still needs identity and argument policy.",
    takeaway="W2 / The ticket that tried to give orders",
    notes="Close the story: Flo now has tools matched to support work. Invite questions about generation, cache refresh and downstream enforcement. Bridge to a legitimate case read containing malicious instructions.")
slide(w1, "Presenter preparation & source guide", "Reference / outside timed delivery", cards=[
    ("PREPARE", "Use profile w1. Download/build first. Preserve evidence before resetting fictional data."),
    ("OPEN", "localhost:9080/docs\nlocalhost:9080/openapi.json\nW1 worksheet + answer key"),
    ("VERIFY", "Run workshop verify w1 on fresh seed. Pre-warm broad and curated catalogs.")],
    takeaway="Full commands and source paths are in the speaker notes and companion notes file.",
    notes="Preparation commands: ./scripts/workshop switch w1; after preserving evidence, ./scripts/workshop reset w1 --yes; ./scripts/workshop verify w1. Optional technical rehearsal: .venv/bin/python workshops/w1/rehearsal_w1.py. It overwrites workshops/w1/evidence/rehearsal-evidence.json. See docs/workshops/w1-api-walkthrough.md and docs/workshops/participant-infra-guide.md. These decks do not run or reset the labs.")

w2 = deck(2, "The ticket that tried to give orders", "Beyond API Governance: Securing AI Agents, MCP Servers, and Enterprise Integrations", 45)
slide(w2, w2["title"], "0–5 min", kind="cover", lead=w2["subtitle"], takeaway="Identity • Actual arguments • Observable business effects",
    notes="Flo is allowed to read a support ticket. Someone has placed instructions inside it. Ask what decides whether the bank pays if those instructions become a tool call. Use Governance Studio at http://localhost:9080/workshop-2.")
slide(w2, "The 45-minute route", "0–5 min", headers=["Time", "Activity", "Evidence"], rows=[
    ["0–5", "Read the injected ticket", "Unsafe recorded request"], ["5–12", "Assign boundary responsibilities", "Identity / tool / API controls"],
    ["12–22", "Compare proposal and execution", "Actual model + policy outcomes"], ["22–34", "Predict policy decisions", "Four scenario results"],
    ["34–41", "Make policy unavailable", "Fail-closed denial + ledger"], ["41–45", "Review ownership", "Governance responsibilities"]],
    notes="Use one presenter against the shared seeded ledger. Recorded scenarios need no provider key. Installation and setup are outside this clock. Optional live inference remains bounded and separately labelled.")
slide(w2, "An authorized read can return untrusted text", "0–5 min", steps=[
    ("Read case-502", "Legitimate support operation"),
    ("Encounter text", "Ticket asks for a payment"),
    ("Propose a tool", "Arguments need validation"),
    ("Authorize", "External policy decides")],
    takeaway="Ticket content can influence a proposal; it cannot grant payment authority.",
    notes="Open Replay the unsafe proposal. Identify where data could be mistaken for an instruction. The ticket asks for 900000 INR, while the fixed W2 request is 900,000 paise. Keep those distinct.")
slide(w2, "Replay the unsafe proposal", "0–5 min", cards=[
    ("REQUEST", "create_payment\n900,000 paise = ₹9,000\nfraud-account-66"),
    ("DECISION", "PROHIBITED_BENEFICIARY"),
    ("BUSINESS EFFECT", "Expected balance delta: ₹0\nExpected new payments: 0")],
    takeaway="Recorded proposal; actual policy execution. Observe the result in your run.",
    notes="The fixture bypasses model inference but exercises the real governance services. A denial proves the submitted request was blocked. It does not establish that a live model was compromised, or that the ticket's rupee amount was interpreted faithfully.")
slide(w2, "Give each gate a precise responsibility", "5–12 min", cards=[
    ("GATE 1 / INFERENCE", "Control model access and dispatch limits."),
    ("GATE 2 / CAPABILITY", "Evaluate signed identity, tool name and normalized arguments."),
    ("GATE 3 / BANKING", "Enforce scoped API access; retain independent banking and approval rules.")],
    takeaway="The lab shares APISIX infrastructure across these logical boundaries.",
    notes="A recorded proposal skips inference. A denied payment may stop at Gate 2 before reaching the banking API. Avoid narrating a full successful call path when the observed request was stopped earlier.")
slide(w2, "Workshop 2 architecture: proposal to execution", "5–12 min", kind="w2_architecture",
    takeaway="Replay skips Gate 1. Gate 2 checks authority before payment execution.",
    notes="Read the diagram in two stages. The Governance Studio backend first reads the case through MCP and Gate 3. For live review, it sends minimal case context through Gate 1 to the hosted model and validates at most one returned payment proposal. Recorded replay supplies a fixed proposal without inference. Both payment paths enter Gate 2, where the MCP adapter validates signed identity and arguments and queries OPA. An allowed payment traverses Gate 3 API-key authentication and Core Banking's signed-identity, approval and ledger rules. Approval-required requests can persist a pending proposal with no debit. PostgreSQL holds banking records; exported telemetry is inspected in Jaeger. APISIX implements all three logical gateway routes. Gate 1 enforces inference budgets and output limits; this lab has no dedicated gateway prompt-injection filter. Model instructions treat case text as untrusted. Denied payment calls stop at Gate 2; independent observer reads do not prove that payment reached Core Banking.")
slide(w2, "Model behavior and permission are distinct", "12–22 min", headers=["Observed result", "What it establishes"], rows=[
    ["No tool proposed", "This model made no payment proposal on this run"],
    ["Policy denied", "The submitted tool request was blocked"],
    ["Approval required", "A pending proposal exists; no payment yet"],
    ["Payment recorded", "A business effect occurred; inspect the ledger"]],
    takeaway="Ask separately: proposed? authorized? executed?",
    notes="If configured, use Ask Flo to review the case. It makes at most one bounded provider call with minimal case context and validates at most one payment proposal. Accept refusal or provider failure as the observed result. Never silently relabel replay as live.")
slide(w2, "Exercise: predict four business outcomes", "22–34 min", headers=["Caller", "Amount", "Destination", "Your prediction"], rows=[
    ["support_agent", "₹250", "vendor-alpha", "Allow / review / deny?"],
    ["support_agent", "₹5,000", "vendor-beta", "Allow / review / deny?"],
    ["support_agent", "₹15,000", "Permitted vendor", "Allow / review / deny?"],
    ["viewer", "₹250", "Permitted vendor", "Allow / review / deny?"]],
    takeaway="Predict first. Then run each button and download its evidence.",
    notes="Give pairs a short prediction window. Record the validated signed role, actual amount and beneficiary. The console uses fixed server-owned scenarios; browser selection is not arbitrary identity or tool authority.")
slide(w2, "Compare predictions with actual evidence", "22–34 min", headers=["Scenario", "Expected outcome", "Ledger effect"], rows=[
    ["Support / ₹250", "Payment executed", "−₹250; +1 payment"],
    ["Support / ₹5,000", "APPROVAL_REQUIRED", "₹0; pending proposal"],
    ["Support / ₹15,000", "Transfer ceiling denial", "₹0; no payment"],
    ["Viewer / ₹250", "NO_MATCHING_RULE", "₹0; no payment"]],
    takeaway="A persisted pending proposal is a record of work awaiting approval.",
    notes="Exact ceiling reason: AMOUNT_EXCEEDS_TRANSFER_CEILING. Review each downloaded result. Repeated successful small-payment scenarios mutate the fictional ledger, so compare per-run effects, not an assumed absolute balance.")
slide(w2, "Policy evaluates the real request", "22–34 min", cards=[
    ("IDENTITY", "input.principal.role\nUse the validated signed principal."),
    ("AMOUNT", "input.arguments.amount\nUse integer paise from the normalized request."),
    ("DESTINATION", "input.arguments.beneficiary\nKeep prohibited destinations blocked.")],
    takeaway="Do not let ticket text or a model's explanation substitute for policy inputs.",
    notes="Show spikes/spike3_opa/policy.rego and the checkpoints linked from the worksheet. Ask what removing support_agent from both the low-risk decision and reason rules would do. Make consistent changes on a private offline copy; do not install the broad teaching checkpoint on the shared presenter stack.")
slide(w2, "Thresholds define the support-agent path", "22–34 min", headers=["Permitted beneficiary + support role", "Expected policy outcome"], rows=[
    ["Up to 100,000 paise / ₹1,000", "Allow"],
    ["100,001–1,000,000 paise", "Require approval"],
    ["Above 1,000,000 paise / ₹10,000", "Deny: transfer ceiling"],
    ["Prohibited beneficiary", "Deny takes precedence"]],
    takeaway="Core Banking independently requires approval above 100,000 paise.",
    notes="These are W2 support-agent policy thresholds, not W3 resolver approval rules. Raising an OPA allowance alone does not bypass the banking approval requirement. The W2 console stores pending proposals but does not approve or settle them.")
slide(w2, "A pending proposal has no financial effect", "22–34 min", steps=[
    ("Request", "₹5,000 to vendor-beta"), ("Evaluate", "Approval is required"),
    ("Persist", "Record proposal + status"), ("Wait", "No debit, no payment")],
    takeaway="Save the proposal ID and status alongside the before/after ledger.",
    notes="Ask participants which component owns the persisted approval record. W2 introduces this lightweight state; W3 supplies a durable workflow pause and W4 demonstrates independent exact-transaction review.")
slide(w2, "Demo: policy stops answering", "34–41 min", code="docker compose pause opa\n\n# In Governance Studio: click Pay ₹250 to a vendor\n# Inspect decision, balance and new-payment count\n\ndocker compose unpause opa",
    lead="Expected: POLICY_TIMEOUT_FAIL_CLOSED and zero financial effects.",
    takeaway="Restore OPA immediately, including when the demo request fails unexpectedly.",
    notes="Use the small-payment button: case-review actions require a governed case read first. The automated outage runner restores OPA in a finally block. A timeout must never become execution permission.")
slide(w2, "Build an evidence chain, not just a screenshot", "34–41 min", cards=[
    ("REQUEST + DECISION", "Signed role, actual arguments, boundary response and reason."),
    ("BUSINESS RECORDS", "Proposal/payment IDs, before/after balance and new-payment count."),
    ("TRACE", "Correlate the trace ID with exported spans. Label missing spans explicitly.")],
    takeaway="A trace ID alone does not establish a complete distributed trace.",
    notes="Open Jaeger at http://localhost:16686. Observer reads are separate from the denied request. W2 console payment requests currently lack idempotency keys: inspect ledger effects before retrying an ambiguous response.")
slide(w2, "Assign an owner to each governance concern", "41–45 min", headers=["Concern", "Ownership discussion"], rows=[
    ["Approved model access + budgets", "AI platform / platform operations"],
    ["Tool policy + identity", "Integration and security teams"],
    ["Approval + banking rules", "Business operations / service owners"],
    ["Data minimization + retention", "Data governance and audit owners"],
    ["Outages + incident response", "Service operations"]],
    takeaway="Use these as discussion prompts; assign owners in your organization.",
    notes="The blueprint panels discuss enterprise controls beyond the lab. Do not imply the development stack implements enterprise DLP, shadow-AI discovery, full MCP OAuth discovery, production IAM, immutable audit storage or compliance certification.")
slide(w2, "The ticket can suggest. The platform decides.", "41–45 min", kind="statement",
    lead="Prove who asked, which arguments were evaluated, and what the bank changed.",
    takeaway="W3 / Make the proposal survive a closed chat and a crashed worker.",
    notes="Ask each pair to explain one denial and the pending-proposal result using evidence. Close with the difference between model behavior and enforcement.")
slide(w2, "Presenter preparation & source guide", "Reference / outside timed delivery", code="./scripts/workshop switch w2\n./scripts/workshop verify w2\n\n# Technical rehearsal on the prepared stack:\n.venv/bin/python workshops/w2/rehearsal_console.py --outage",
    lead="Open localhost:9080/workshop-2 and localhost:16686 before delivery.",
    takeaway="Use the worksheet for setup, optional live inference and scenario details.",
    notes="Use sample login maya@flobank.demo / flo-demo. The rehearsal writes timestamped evidence in workshops/w2/evidence and does not reset or switch profiles. Preserve old evidence before any fictional-ledger reset. For optional live review, see docs/workshops/openrouter-setup.md and provider configuration guidance. No live calls are needed for the recorded exercise.")

w3 = deck(3, "The resolver that remembered", "Architecting the Agentic Enterprise: Middleware, Durable State, and Event-Driven AI", 45)
slide(w3, w3["title"], "0–6 min", kind="cover", lead=w3["subtitle"], takeaway="Investigate • Pause • Recover • Settle once",
    notes="Ask what happens when the customer closes the chat, the reviewer returns tomorrow or the worker crashes. Flo Bank's Autonomous System Resolver is implemented as a customer-dispute resolver. Introduce case-501 and declare live or replay mode.")
slide(w3, "The 45-minute route", "0–6 min", headers=["Time", "Activity", "Evidence"], rows=[
    ["0–6", "Read the dispute; declare mode", "Case facts and mode"], ["6–13", "Assign state owners", "Workflow + payment identities"],
    ["13–23", "Investigate and pause", "Graph reads + validated proposal"], ["23–35", "Crash and redeliver", "Same pending workflow"],
    ["35–41", "Approve and inspect", "Exactly one settlement"], ["41–45", "Review limits", "Durability responsibilities"]],
    notes="Have terminal queries, worker logs and business evidence open. Use fresh prepared W3 state. A previously completed case-501 workflow is deliberately not started again, and a banking reset alone does not clear Temporal history.")
slide(w3, "The customer leaves. The work continues.", "0–6 min", cards=[
    ("CASE", "case-501 reports a disputed charge. Investigate before deciding entitlement."),
    ("PROPOSAL", "The resolver gathers governed evidence and proposes a resolution."),
    ("OUTCOME", "Approval leads to one settlement; rejection creates no settlement.")],
    takeaway="The business process must outlive both the chat and the worker.",
    notes="Do not describe the seeded ticket as a verified duplicate debit. Ask where the case, proposal, approval and payment should live. Collect failure predictions: lost progress, repeated investigation, missing approval or double payment.")
slide(w3, "Declare how the investigation is running", "0–6 min", cards=[
    ("LIVE", "Compiled LangGraph calls the configured model through Gate 1 and selects allowed reads."),
    ("OFFLINE REPLAY", "Fixtures drive the same graph; governed reads and banking controls still execute."),
    ("HONEST LABELS", "A provider failure remains a failure. Recorded text is not newly verified evidence.")],
    takeaway="Replay case-501 proposes 75,000 paise / ₹750 to acc-101.",
    notes="Set USE_REPLAY_FIXTURES=true before preparing the stack for the deterministic fixture. Live mode may produce different arguments or fail investigation. The fixture's ₹750 is not a calculated refund for the ticket's claimed charge. MiniMax is the documented default; optional participant-provider setup is in the infrastructure/OpenRouter guides.")
slide(w3, "Give every kind of state an owner", "6–13 min", headers=["Component", "Owns", "Recovery role"], rows=[
    ["Kafka", "Case-event delivery", "Redelivery is expected"],
    ["Temporal", "Durable process history", "Progress, approval, activity results"],
    ["LangGraph", "Bounded investigation loop", "Reasoning and tools in an activity"],
    ["Core Banking", "Business records", "Rules and payment idempotency"]],
    takeaway="Event delivery, workflow progress and financial effects need separate controls.",
    notes="Temporal replays completed activity results. A failed investigation activity may repeat model inference and read tools. This lab does not checkpoint every unfinished LangGraph step.")
slide(w3, "Trace the durable business process", "6–13 min", steps=[
    ("Kafka event", "Deliver case identity"), ("Temporal", "Start or reuse workflow"),
    ("Investigation", "LangGraph + governed reads"), ("Approval", "Persist the decision wait"),
    ("Settlement", "Gate 3 + idempotent payment")],
    takeaway="Model calls and network I/O run in activities, outside deterministic workflow code.",
    notes="During investigation, model inference goes through Gate 1 and allowed MCP reads through Gate 2 and Gate 3. The workflow owns the subsequent approval wait and settlement activity. Explain why arbitrary model responses cannot be replayed as deterministic workflow code.")
slide(w3, "Stable identity closes two duplicate windows", "6–13 min", cards=[
    ("BUSINESS CASE", "case-501\nThe source identity stays stable across event redelivery."),
    ("WORKFLOW", "dispute-case-case-501\nA second event reuses the existing business process."),
    ("PAYMENT", "settle-dispute-case-501\nA settlement retry reuses the business effect.")],
    takeaway="Commit the Kafka offset after Temporal accepts or confirms the matching workflow.",
    notes="General workflow format: dispute-case-{case_id}. Explain that stable workflow identity and banking idempotency address different failure windows. Do not claim exactly-once event delivery or inference.")
slide(w3, "Investigation has a bounded tool loop", "13–23 min", steps=[
    ("Prepare", "Case context"), ("Ask model", "Gate 1 inference"),
    ("Validate tools", "Allowlisted read calls"), ("Read evidence", "MCP → Gate 3"),
    ("Validate result", "Exact proposal schema")],
    takeaway="The loop may repeat within its bounds. Diagnosis has no payment or approval tool.",
    notes="Allowed initial tools include get_case and get_account. In live mode inspect at least one actual model-selected read. Server rules validate amount, currency and destination and decide whether approval is required; the model cannot grant itself permission.")
slide(w3, "Demo: deliver a case and inspect progress", "13–23 min", code=".venv/bin/python workshops/w3/client.py emit \\\n  --case-id case-501 --customer-id cust-8801\n\n.venv/bin/python workshops/w3/client.py query --case-id case-501",
    lead="Poll until the investigation reaches its approval wait.",
    takeaway="Inspect graph steps, selected tools, returned evidence and the actual proposal.",
    notes="Run from the repository root on a prepared stack. The CLI defaults to Kafka localhost:9092 and Temporal localhost:7233. If using live mode, confirm provider and governed-tool evidence rather than promising a fixed proposal.")
slide(w3, "The agent proposes, then the process pauses", "13–23 min", cards=[
    ("PHASE", "WAITING_FOR_APPROVAL"),
    ("PROPOSAL", "Replay: ₹750 to acc-101. Record the actual amount and destination."),
    ("LEDGER", "approval_decision: null\nNo settlement payment yet.")],
    takeaway="Server rules control the transition from proposal to business effect.",
    notes="Ask whether the case is resolved yet and what evidence would establish that money moved. W3 resolver review rules are separate from W2's support-agent thresholds. Save this baseline before stopping anything.")
slide(w3, "Exercise: capture the pre-crash checkpoint", "23–35 min", headers=["Capture", "Compare after recovery"], rows=[
    ["Workflow ID", "Same dispute-case-case-501"],
    ["Proposal", "Same amount, currency and destination"],
    ["Current phase", "WAITING_FOR_APPROVAL"],
    ["Approval decision", "Still pending"],
    ["Settlement count", "Still zero"]],
    takeaway="Save the state before the failure so recovery becomes measurable.",
    notes="Pairs should predict what survives and what could repeat. Leave Kafka, Temporal and banking persistence running. Stopping the worker alone during the wait is the timed exercise.")
slide(w3, "Demo: stop, redeliver, restart", "23–35 min", code="docker compose --profile w3 stop worker\n\n.venv/bin/python workshops/w3/client.py emit \\\n  --case-id case-501 --customer-id cust-8801\n\ndocker compose --profile w3 start worker\n.venv/bin/python workshops/w3/client.py query --case-id case-501",
    takeaway="The duplicate event can wait in Kafka while the worker is stopped.",
    notes="Wait for worker readiness after restart. Inspect duplicate-start handling in logs and the workflow history. Confirm the same pending proposal with zero settlement effects. Do not reset the banking or Temporal state during this exercise.")
slide(w3, "Recovery preserves recorded progress", "23–35 min", cards=[
    ("SURVIVES", "Workflow identity, completed activity results, proposal and pending approval."),
    ("MAY REPEAT", "A failed activity's inference and read tools can run again."),
    ("MUST NOT DUPLICATE", "A financial settlement under the stable business idempotency key.")],
    takeaway="Durability does not mean every intermediate computation runs only once.",
    notes="The current exercise stops at the durable approval wait. It does not itself test a response lost after a payment commits. Explain that separate failure window and the role of the stable payment key without claiming it was observed here.")
slide(w3, "Review the recovered proposal, then approve", "35–41 min", code=".venv/bin/python workshops/w3/client.py approve \\\n  --case-id case-501 --reviewer ops-lead \\\n  --comments \"Reviewed case evidence and validated proposal\"\n\n.venv/bin/python workshops/w3/client.py query --case-id case-501",
    takeaway="The approval command waits for the workflow result.",
    notes="Read the actual proposal before sending the decision. The CLI's reviewer label is a lab decision signal; production approval needs authenticated and authorized reviewers bound to the exact proposal. Inspect the resulting payment rather than trusting only the workflow's final text.")
slide(w3, "Prove one approved settlement", "35–41 min", headers=["Evidence", "Expected fresh-run observation"], rows=[
    ["Workflow phase", "COMPLETED"],
    ["Case status", "resolved"],
    ["Settlement key", "settle-dispute-case-501"],
    ["Payment count for that key", "Exactly 1"],
    ["Business amount", "Matches the reviewed proposal"]],
    takeaway="Reconcile workflow history with the actual banking record.",
    notes="Use actual ledger records and the stable key. A separate rejection run should close with no payment. The optional case-502 replay has a missing-account tool error: show that error if used; it is not evidence of a fully successful investigation.")
slide(w3, "Three distinct failure windows", "41–45 min", headers=["Failure", "Control", "Exercise scope"], rows=[
    ["Event delivered twice", "Stable workflow identity", "Observed in redelivery"],
    ["Worker dies during wait", "Temporal durable state", "Observed in restart"],
    ["Payment commits; reply lost", "Stable settlement key", "Separate retry scenario"]],
    takeaway="State the evidence you have for each recovery claim.",
    notes="Ask participants which state owner closes each window. Completed activity results replay from history; unfinished activity work can repeat. A brief crash demonstration does not experimentally prove weeks of availability.")
slide(w3, "From a demo pause to a longer process", "41–45 min", cards=[
    ("LAB", "The approval timeout is 24 hours. The timed demo illustrates a durable wait."),
    ("PRODUCTION DESIGN", "Choose timeout and escalation rules, persistence, availability and recovery procedures."),
    ("NEXT APPLICATIONS", "Incident remediation and procurement can reuse the pattern with their own rules.")],
    takeaway="These extensions require design work beyond the implemented dispute lab.",
    notes="Do not describe the lab as a production multi-agent deployment or claim unfinished LangGraph steps are checkpointed. Invite participants to name a process in their organization that outlasts a request/response session.")
slide(w3, "Progress survives. Authority stays explicit.", "41–45 min", kind="statement",
    lead="Governed investigation + durable approval + idempotent settlement.",
    takeaway="W4 / Test the whole system under an agent attack.",
    notes="Return to the opening failure predictions. Have pairs explain where the proposal lived during the worker outage and how the bank avoided a duplicate business effect. Bridge to deliberate boundary testing and delegation.")
slide(w3, "Presenter preparation & source guide", "Reference / outside timed delivery", cards=[
    ("PREPARE", "Activate w3. Use fresh local workflow state. Declare live/replay mode before the demo."),
    ("OPEN", "Case, workflow query, worker logs, graph/tool evidence and payment records."),
    ("PRESERVE", "Save previous evidence. The automated W3 rehearsal resets bank and Temporal lab state.")],
    takeaway="Use the manual exercise for delivery; reserve destructive rehearsals for disposable labs.",
    notes="Setup: ./scripts/workshop pull w3; ./scripts/workshop switch w3; ./scripts/workshop verify w3. Automated rehearsal: .venv/bin/python workshops/w3/rehearsal_w3.py. It deletes local Temporal SQLite history and resets seeded banking data; never run casually during the manual exercise. Evidence: workshops/w3/evidence/rehearsal-evidence.json. See the worksheet and participant infrastructure guide for complete preparation.")

w4 = deck(4, "The day the agent broke the bank", "Implementing Triple-Gate Architecture & A2A Security for Autonomous AI Workloads", 135)
slide(w4, w4["title"], "0–8 min", kind="cover", lead=w4["subtitle"], takeaway="135 minutes / Become Flo Bank’s response team",
    notes="Open http://localhost:9080/workshop-4?view=presenter. Say: the credentials were valid, the request passed schema validation, and the fictional bank still lost ₹90 lakh. What did we authorize? Withhold the ticket until the next chapter. Declare that the incident is a recorded proposal executed in an isolated local ledger.")
slide(w4, "₹90 lakh", "0–8 min", kind="statement", lead="900,000,000 paise. One payment. API 200. Valid credentials.",
    takeaway="Opening incident: isolated vulnerable ledger; protected-ledger delta stays zero.",
    notes="Collect predictions: identity, model, tool policy or approval? Record local votes without a polling service. The visible success status and credential validity establish neither transaction legitimacy nor correct delegation. No live model compromise is being asserted.")
slide(w4, "Your assignment: repair and prove the bank still works", "0–8 min", cards=[
    ("INVESTIGATE", "Find where untrusted case text became payment authority."),
    ("CONTAIN", "Test inference, tool, identity, approval and delegation boundaries."),
    ("RESTORE", "Block the attacks and prove one legitimate, independently approved settlement.")],
    takeaway="Every chapter: predict → run → inspect → change → retest.",
    notes="Use one prepared local instance per pair. Shared hosting is observation/fallback only. Give each pair one task and one evidence artifact at a time; keep explanation blocks under seven minutes.")
slide(w4, "The incident-response clock / first half", "0–8 min", headers=["Time", "Chapter", "Pair evidence"], rows=[
    ["0–8", "The bank has paid", "Opening prediction"], ["8–20", "Follow the money", "Attack chain + both ledgers"],
    ["20–33", "Contain inference", "Budget denial vs tool policy"], ["33–53", "Control capabilities", "Policy repair + ₹250 payment"],
    ["53–60", "Try the direct API", "Audience / scope denials"], ["60–67", "Break + checkpoint recovery", "Ready local lab"]],
    notes="Keep the opening tight. The seven-minute break is included in the full 135 minutes. Completed local checkpoints are available for stalled pairs.")
slide(w4, "The incident-response clock / second half", "0–8 min", headers=["Time", "Chapter", "Pair evidence"], rows=[
    ["67–85", "Restrict identity", "Entitled token exchange"], ["85–103", "Approve the transaction", "Independent review + one effect"],
    ["103–119", "Secure delegation", "Task access + payment binding"], ["119–130", "Prove the repair", "Blocked attacks + valid payment"],
    ["130–135", "Incident review", "Control owners + next work"]],
    notes="Create approval proposals immediately before review: they expire after ten minutes. Leave enough time for legitimate settlement and evidence reconstruction. A blocked attack suite alone is insufficient to prove the repaired business path.")
slide(w4, "Follow the money across the handoff", "8–20 min", steps=[
    ("Ticket", "Untrusted instructions"), ("NegotiatorBot", "Recorded settlement proposal"),
    ("PaymentsAgent", "Delegated execution request"), ("Vulnerable bank", "Valid request; harmful payment")],
    takeaway="Mark the point where information was treated as authority.",
    notes="Reveal the ticket, recorded proposal and handoff. Ask which checks are missing at each boundary. The console replays fixed server-owned scenarios; the prediction/view controls do not enforce policy.")
slide(w4, "Replay one incident; inspect two ledgers", "8–20 min", headers=["Ledger", "Expected delta", "Interpretation"], rows=[
    ["Isolated vulnerable ledger", "−900,000,000 paise; +1 payment", "Recorded harmful proposal executed"],
    ["Protected banking ledger", "0 paise; 0 new payments", "Separate protected state unchanged"]],
    takeaway="The replay establishes this fixed request’s result, not a live model compromise.",
    notes="The isolated sandbox is a presenter-only service with a separate disposable ledger and no protected volumes or provider/banking keys. Starting w4 alone does not enable it; follow the answer-key setup before delivery. Do not expose secrets in slides or exports.")
slide(w4, "The Triple-Gate model", "20–33 min", cards=[
    ("GATE 1", "Inference access and budgets: may this model request be dispatched?"),
    ("GATE 2", "MCP capability policy: may this identity call this tool with these arguments?"),
    ("GATE 3", "API access and banking rules: is this exact business operation authorized?")],
    takeaway="Independent review and delegation binding extend protection across the business process.",
    notes="These are logical responsibilities in the lab, sharing APISIX infrastructure. No single boundary owns every failure. Prompt refusal cannot establish that direct tool or API calls are controlled.")
slide(w4, "Gate 1: stop dispatch when the budget is exhausted", "20–33 min", cards=[
    ("PREDICT", "Would a model budget denial also block an independent direct tool request?"),
    ("RUN", "Execute the exhausted-headroom scenario. Inspect HTTP 429 before provider dispatch."),
    ("COMPARE", "Run the independent Gate 2 scenario and inspect its own response.")],
    takeaway="Inference limits govern inference dispatch. Tool authorization remains independent.",
    notes="Show zero dispatch evidence for the budget scenario. Optional live comparison makes one bounded call and executes no tools. Report the actual response, refusal or live_failed outcome without relabelling a recorded result.")
slide(w4, "Gate 2: isolate the reason for denial", "33–53 min", headers=["Request", "Expected result", "Ledger"], rows=[
    ["25,000 paise to prohibited beneficiary", "Prohibited-beneficiary denial", "No change"],
    ["900,000,000 paise to permitted vendor", "Transfer-ceiling denial", "No change"],
    ["25,000 paise to vendor-alpha", "Allowed after local repair", "−25,000; +1 payment"]],
    takeaway="Change one relevant dimension so the evidence identifies the control.",
    notes="Use the low amount for the prohibited-beneficiary test and a permitted beneficiary for the amount test. Conflating both would hide which rule stopped the request. Interpret the actual MCP decision rather than only the outer transport status.")
slide(w4, "Exercise: repair the prepared local policy", "33–53 min", code="cp workshops/w4/checkpoints/initial/policy.rego \\\n  spikes/spike3_opa/policy.rego\ndocker compose restart opa\n\n# Remove only vendor-alpha from the prepared prohibited list.\n# Keep fraud-account-66 blocked, restart OPA, then retest.",
    lead="The initial checkpoint also blocks the legitimate vendor-alpha payment.",
    takeaway="Work on the pair’s local instance and save before/after service results.",
    notes="Run prohibited beneficiary, excessive amount and permitted payment before the edit. Remove only vendor-alpha; retain attacker block and transfer ceiling. Repeating the success scenario creates payments; reconcile uncertain responses under the original run ID.")
slide(w4, "Retest the repair against both attack and business paths", "33–53 min", code="# Completed checkpoint if a pair needs recovery:\ncp workshops/w4/checkpoints/completed/policy.rego \\\n  spikes/spike3_opa/policy.rego\ndocker compose restart opa",
    lead="Attacker remains blocked. Excessive amount remains blocked. ₹250 vendor payment succeeds.",
    takeaway="A policy repair succeeds when legitimate work is restored and attacks remain denied.",
    notes="Collect actual denied and allowed responses, balance deltas and payment count. This is a running-policy change, not a UI toggle. If stalled, allow two minutes before supplying the completed checkpoint.")
slide(w4, "Gate 3: the attacker changes routes", "53–60 min", headers=["Attempt", "Expected status", "Missing authority"], rows=[
    ["Use an MCP-audience token at the API", "401", "Correct API audience"],
    ["Use a read-only token to write a payment", "403", "Payment-write scope"]],
    takeaway="The direct API path must enforce its own audience and scope checks.",
    notes="Ask what would happen if the API accepted every validly signed token regardless of audience. Then inspect the actual responses. A Gate 2 denial does not prove the direct API path is protected; test it independently.")
slide(w4, "Break / checkpoint recovery", "60–67 min", kind="statement",
    lead="Can the payment agent approve its own transaction?",
    takeaway="Seven-minute break. Facilitator restores stalled local checkpoints.",
    notes="Pause for the scheduled break. Restore completed policy/identity files where needed, restart OPA and refresh readiness. Export interrupted evidence first. Do not reset protected ledger state to hide an uncertain payment result.")
slide(w4, "Identity must narrow at the next boundary", "67–85 min", steps=[
    ("Principal", "Validated subject + role"), ("Exchange", "Check requested entitlement"),
    ("API token", "Correct audience + limited scopes"), ("Banking API", "Verify on every request")],
    takeaway="A valid signature proves origin; audience and scope constrain intended use.",
    notes="The lab demonstrates a constrained token-exchange pattern. Show sanitized claims rather than bearer credentials. Managed identity, key rotation and broader protocol conformance remain production work.")
slide(w4, "Exercise: request only an entitled scope", "67–85 min", code=".venv/bin/python workshops/w4/exercise_exchange.py initial\n\n# In checkpoints/initial/identity.json, change requested_scope\n# from api:payments:write to api:accounts:read, then rerun.\n\n.venv/bin/python workshops/w4/exercise_exchange.py completed",
    lead="The initial viewer request asks for payment-write authority.",
    takeaway="Original request: 403. Corrected/completed read-scope request: 200.",
    notes="The full edit path is workshops/w4/checkpoints/initial/identity.json. Change only requested_scope. The CLI writes sanitized timestamped evidence under workshops/w4/evidence. It mints lab credentials locally and does not load .env automatically: export matching JWT settings if the stack overrides defaults, using the answer-key instructions.")
slide(w4, "Explain the identity evidence", "67–85 min", headers=["Scenario", "Expected response", "Save"], rows=[
    ["Viewer requests payment-write scope", "403 entitlement denial", "Requested scope + decision"],
    ["Viewer requests account-read scope", "200 permitted exchange", "Sanitized audience + scopes"],
    ["MCP token sent to banking API", "401 audience denial", "Boundary response"],
    ["Read token attempts payment", "403 scope denial", "Zero ledger change"]],
    takeaway="Keep issued tokens and signing keys out of exported evidence.",
    notes="Have each pair explain one denied and one permitted identity request. View selection cannot grant authority. A successful token exchange does not by itself prove a subsequent payment is authorized.")
slide(w4, "Approval attaches to one exact transaction", "85–103 min", cards=[
    ("REVIEW THE VALUES", "Source account\nAmount in paise\nCurrency\nBeneficiary"),
    ("REVIEW THE CONTEXT", "Proposal ID\nTask ID\nExpiry\nIndependent reviewer"),
    ("EXPECTED RESULT", "₹1,500 / 150,000 paise\nOne approved settlement\nOne actual payment ID")],
    takeaway="Create the legitimate-delegation proposal immediately before review.",
    notes="Proposals expire after ten minutes. Read the actual proposal and task identifiers. Independent review should approve exact server-owned arguments; changed arguments must fail. W4's password-backed lab reviewer flow is not a claim of production IAM.")
slide(w4, "Use an independent reviewer session", "85–103 min", steps=[
    ("Requester", "Run legitimate delegation"), ("Reviewer", "Separate private browser"),
    ("Authorize", "Reviewer password + exact review"), ("Decide", "Approve or reject")],
    takeaway="Selecting “Independent reviewer” alone grants no authority.",
    notes="The facilitator configures and privately provides the reviewer password to the cofacilitator. The requester cannot approve its own proposal even with a reviewer cookie in its browser. Never paste the password into slides or evidence. Inspect the current proposal immediately before approval.")
slide(w4, "Attempt self approval and transaction tampering", "85–103 min", headers=["Attempt", "Expected result", "Meaning"], rows=[
    ["Payment agent approves itself", "403", "Requester/delegation rule enforced"],
    ["Independent exact review", "200", "Proposal approved"],
    ["Execute with changed arguments", "400", "Approval does not cover the change"],
    ["Execute exact approved request", "200", "Authorized settlement can proceed"]],
    takeaway="Inspect each boundary result and the actual ledger effect.",
    notes="The console approval path executes the server-owned exact arguments, tests tampering and retry, and binds the payment to the task. Use the actual evidence order shown by the run; these rows describe the controls, not a manual command sequence.")
slide(w4, "One effect survives a retry", "85–103 min", cards=[
    ("EXECUTE", "Use the approved exact arguments and stable financial key."),
    ("RETRY", "Return the existing result under the same key."),
    ("PROVE", "Balance delta: −150,000 paise\nPayment count delta: +1\nSame payment identity")],
    takeaway="For an uncertain response, select the original run and reconcile.",
    notes="Use Reconcile uncertain result after a lost response or process restart. Proposal status and keyed payments determine the result. Never invent a fresh run or financial key to retry an uncertain payment. If the API cannot be read, keep the result unresolved.")
slide(w4, "A second agent creates a second boundary", "103–119 min", steps=[
    ("NegotiatorBot", "Owns the delegated task"), ("PaymentsAgent", "Designated executor"),
    ("Reviewer", "Independent approval"), ("Banking API", "Exact settlement"),
    ("Task output", "Bound to the actual payment")],
    takeaway="Delegation needs explicit permissions for read, execute, approve and complete.",
    notes="The repository implements selected A2A controls; this is not a demonstration of complete A2A protocol conformance. Have pairs identify which principal may perform each operation before running the scenarios.")
slide(w4, "Test access to the delegated task", "103–119 min", headers=["Attempt", "Expected result", "Evidence"], rows=[
    ["Foreign principal reads task", "403", "Task-access denial"],
    ["Non-executor completes task", "403", "Completion denial"],
    ["Bind payment to mismatched task", "400", "Binding validation failure"],
    ["Valid bound task completion", "200", "Task output has actual payment ID"]],
    takeaway="A valid agent identity does not grant access to every task.",
    notes="Only task owner/designated executor can access the relevant task. Binding checks source, amount, currency, destination and optional proposal. Explain which principal made each tested request using sanitized evidence.")
slide(w4, "Bind completion to a business fact", "103–119 min", cards=[
    ("MATCH", "Source, amount, currency, beneficiary and proposal context."),
    ("LINK", "Task output payment ID equals the actual settled ledger payment ID."),
    ("REJECT", "A plausible success message or unrelated payment is insufficient.")],
    takeaway="Task completion is proven by its relationship to the real settlement.",
    notes="Inspect task, proposal and payment records side by side. The final legitimate path is delegate → propose → independently approve → execute exact arguments → bind the actual payment to the task.")
slide(w4, "Prove the repaired system in both directions", "119–130 min", headers=["Control", "Attack result", "Legitimate result"], rows=[
    ["Inference", "Budget exhaustion blocks dispatch", "Bounded access remains possible"],
    ["Tool policy", "Beneficiary / ceiling denials", "₹250 vendor payment"],
    ["Identity", "Wrong audience / escalation denied", "Entitled read-scope exchange"],
    ["Approval", "Self review / tampering denied", "Exact ₹1,500 settlement"],
    ["Delegation", "Foreign access / mismatch denied", "Payment bound to task"]],
    takeaway="Use your observed service results; keep unresolved outcomes visible.",
    notes="Run the attack suite and legitimate path on prepared state, or inspect the collected chapter evidence if time is short. The table lists expected outcomes, not fresh measurements. Do not conflate the separate ₹250 policy exercise with the ₹1,500 delegation payment.")
slide(w4, "Reconstruct the incident from familiar records", "119–130 min", steps=[
    ("Run", "Scenario, mode, time"), ("Proposal", "Exact request + reviewer"),
    ("Task", "Owner + executor"), ("Payment", "ID + stable key"),
    ("Ledger", "Balance + count deltas")],
    takeaway="Correlate observed spans, or explicitly label the trace incomplete.",
    notes="Evidence sheet: workshops/w4/incident-evidence.md. Save sanitized caller, audience/scopes, arguments and boundary responses as well as business IDs. Null ledger observations are unresolved, not zero. A generated trace ID alone is not collector evidence. Aggregate deltas need an isolated run without concurrent external mutations.")
slide(w4, "Incident review: what did your first vote miss?", "130–135 min", cards=[
    ("EXPLAIN A DENIAL", "Name the caller, arguments, boundary response and observed ledger delta."),
    ("PROVE A PAYMENT", "Link independent review, proposal, task, payment and one financial effect."),
    ("ASSIGN OWNERS", "Inference, tool policy, identity, approval, audit and incident operations.")],
    takeaway="Before production: managed identity, resilient state, audit operations and conformance.",
    notes="Revisit initial votes. Identify work for key rotation, distributed budget state, availability, audit retention, trace completeness and protocol conformance. Technical rehearsal evidence does not establish a completed 135-minute human delivery rehearsal or production readiness.")
slide(w4, "Restore useful work under explicit authority", "130–135 min", kind="statement",
    lead="The final evidence: blocked attacks alongside a correctly approved and bound payment.",
    takeaway="Capabilities → Governance → Durability → Incident-tested boundaries",
    notes="Close the four-workshop arc. Ask participants to name one control they would add to an existing agent integration and the evidence they would require to show it works.")
slide(w4, "Presenter preparation & source guide", "Reference / outside timed delivery", cards=[
    ("PREPARE", "Local w4 per pair. Independent reviewer session. Optional isolated presenter sandbox."),
    ("CHECK", "workshop status + verify w4\nIncident Room readiness\nCompleted local checkpoints"),
    ("RECOVER", "Timebox stalls to two minutes. Export evidence. Reconcile original runs.")],
    takeaway="Follow the W4 answer key for secret configuration, isolation and rehearsal setup.",
    notes="Do setup outside the timed workshop. See workshops/w4/answer-key.md for W4_REVIEWER_PASSWORD, W4_ENABLE_VULNERABLE, W4_SANDBOX_KEY, observation-only hosting and presenter sandbox startup. Do not put actual values in this deck. Technical runner: .venv/bin/python workshops/w4/rehearsal_w4.py --vulnerable --outage, only on the appropriately prepared stack. It creates fictional records and does not reset data. Human timing record: workshops/w4/delivery-rehearsal.md. Downloads/builds and profile switching happen before attendees arrive.")
