# Modernizing APIs for AI Agents: From OpenAPI to MCP

Spoken script and stage cues · 45 minutes

Use the quoted passages as speaking anchors. Expand through demonstrations and audience responses; do not read every note aloud. Ask for a prediction before each reveal. Allow two answers per prompt and then summarize. If nobody responds within five seconds, offer the two alternatives listed in the audience sheet.

## Slide 1 · 0–2 · The customer request

**On screen:** Original workshop title and a customer message: “What’s my balance, and what’s happening with my support case?”

> “Maya opens Flo Bank and asks a question that feels simple. She wants information the bank already has. The APIs exist. The documentation exists. The gateway exists. Today, we’re the team responsible for making those capabilities available to an AI assistant through MCP.”
>
> “By the end, we’ll have a small, purposeful tool catalog, a successful invocation, and evidence that an invalid API credential is still rejected.”

Pause on the customer request. Avoid starting with a product diagram or a list of infrastructure services.

**Transition:** “Let’s start where Maya starts: the banking experience.”

## Slide 2 · 2–4 · Show Flo, then go behind the experience

**Demo A:** Open the customer UI at `http://localhost:9080`. Use the sample login and a balance query. If chat is unavailable, show the account screen or a prepared screenshot. The business question remains valid without a live model call.

> “This is the experience the customer sees. Now we’ll switch to the integration behind an assistant’s capabilities. This UI has its own existing banking tools. The MCP endpoint we’re about to inspect is a separate implementation exercise.”
>
> “For that exercise, we’ll use an Acme account and a separate seeded support case. They let us inspect the exact request and result without suggesting they are Maya’s records.”

**Audience cue:** “Who already has an OpenAPI description for the services an agent might need?” Use a show of hands; no round-robin introductions.

**Transition:** “You have those APIs. Which capabilities would you ship?”

## Slide 3 · 4–8 · Give the architecture team a job

**On screen:** Three requirements: read an account; inspect a support case; preserve existing API checks.

> “Our first release helps a support employee retrieve account information and inspect a case. It does not settle a dispute, approve a refund, or administer the bank. Decide what this assistant needs to discover, how it should express arguments, and where permission is checked.”

Ask: “Would you begin by exposing the whole API specification or a contract selected for this job?” Take two responses without resolving the choice yet.

> “Hold that choice. We’ll generate a catalog first and see what it gives us. Your decision will become concrete when we inspect the result.”

**Success criteria:** Two curated tools; both reads work; a known excluded operation fails on the curated endpoint; an invalid API credential fails downstream.

**Transition:** “First, what changes when an HTTP operation becomes an MCP tool?”

## Slide 4 · 8–11 · OpenAPI supplies the starting contract

**On screen:** `GET /api/v1/accounts/{id}` beside a tool descriptor with a name, description, and input schema. Use a captured live descriptor for actual input fields.

> “OpenAPI describes an HTTP API: its operations, parameters, and response schemas. Our gateway uses that description to generate callable MCP tools. The existing banking service can continue serving HTTP requests.”
>
> “Agents can also use REST through other integrations. Here, MCP gives compatible clients a common tool interface. The conversion automates a useful starting point. The quality of that starting point depends on the source contract.”

Ask: “If a description says only ‘get data,’ what decision does the agent still have to make?” Expected: whether the tool fits the task and how to interpret its result.

**Transition:** “Let’s look at the conversation between the client and that interface.”

## Slide 5 · 11–14 · Discover, then invoke

**On screen:** Conceptual lifecycle: initialize → initialized notification → tools/list → tools/call → tool result.

**Demo B:** Run the existing client’s initialization and list commands.

> “A compatible client establishes the supported protocol and capabilities, discovers the tools and their input schemas, and calls a named tool with structured arguments. The server returns the tool outcome.”
>
> “Our lab CLI is deliberately small: it sends separate requests so we can see these methods. It is not an example of a full client lifecycle implementation. In an agent application, the host manages the MCP client and supplies relevant tool definitions to the model.”

Point to the protocol version actually returned. Do not call the lab’s `2024-11-05` value the latest MCP version. Treat tool output as application data, including possible errors.

**Transition:** “Now let’s see how much of the bank appeared in that generated catalog.”

## Slide 6 · 14–17 · The catalog works

**Demo C:** List the broad catalog; run the account read against `/mcp`.

> “The generator has made an account operation discoverable and callable. We can supply an account identifier, execute through the gateway, and get a real response from the lab banking API.”

Point to `acc-101`, `balance: 1500000`, and `currency: INR`. Explain integer minor units: this balance is ₹15,000. Use the current response if it differs; do not narrate a preset value over a changed result.

> “We have working invocation. Before we celebrate the catalog, take a look at the other operations.”

The historical catalog contains 23 tools; announce the current count from discovery. Do not read every name.

**Transition:** “Which of these tools would you give our support assistant?”

## Slide 7 · 17–20 · The reveal: the job is smaller than the API

**On screen:** Highlight account read, case read, payment execution, approval, and database reset entries from the discovered catalog.

Ask: “Keep or remove payment execution? Keep or remove database reset?” Use hands or verbal votes.

> “Those operations may be valid enterprise APIs. Their presence in the source document does not make them appropriate for this assistant’s task. Exposing a tool also does not prove the caller can execute it: downstream checks still matter.”
>
> “Generation mapped operations. We must decide the capability boundary for this job. Let’s make that decision together.”

Do not invoke payment execution or reset to create drama. The reveal is the unexpected capability catalog, not a staged financial incident.

**Transition:** “You have nine minutes to give Flo a toolbox you can explain.”

## Slide 8 · 20–25 · Audience curation challenge

**On screen:** Operation cards and a weak description: “Get account data.”

Spend one minute choosing operations, two minutes improving the description, one minute checking inputs and units, and one minute summarizing.

Ask attendees to keep exactly the two operations needed for this first release. They can discuss with a neighbor or simply write their decision. Optional participants inspect the broad and curated JSON files locally.

> “Describe the tool in terms of the decision it helps the assistant make. Include the identifier it needs and how to interpret money. A description can improve selection and interpretation. Runtime checks must still enforce permission.”

Suggested description for discussion: “Retrieve the balance, currency, and status for a known account ID. Balance is returned as integer minor units. Use for account inquiries.” Explain that this is proposed wording; the prepared runtime contract uses its existing description.

Ask: “Is a read-only tool automatically safe to give every user?” Expected: no; sensitive data and ownership still require controls.

**Transition:** “Here is our prepared implementation of that smaller contract.”

## Slide 9 · 25–29 · Reveal the curated endpoint

**Demo D:** Show the completed contract; initialize and list `/mcp/curated`.

> “This checkpoint exposes `get_account` and `get_case`. We selected the operations, gave them usable names and descriptions, and made their input requirements visible.”
>
> “For today’s delivery, I’m switching to a prepared endpoint. Our wording exercise illustrates a design change; editing a local JSON file alone does not establish that the running generator has refreshed its catalog.”

Compare one source operation and its emitted descriptor. Keep `pathParameters.id` visible: the generated input shape matters as much as the friendly name.

Ask: “If someone remembers a payment tool’s old name, can they still call it here?” Collect a prediction and defer the answer to the next slide.

**Transition:** “A catalog is a promise. Let’s check what happens at invocation time.”

## Slide 10 · 29–36 · Two different denials

**Demo E:** Curated account read, `get_case(case-501)`, excluded-tool attempt, and curated account read with an invalid credential.

Spend two minutes on successful reads, two on the excluded-tool attempt, and three on invalid credentials and result interpretation.

> “First, our intended reads succeed. The support case is open; the account response supplies a balance and currency. These are separate fixtures, not proof that this customer owns this account.”

Attempt an actual broad catalog payment-list tool on the curated endpoint with valid lab credentials. This is a read operation, chosen to avoid unintended business effects if the catalog changes. Proceed only after confirming it is excluded.

> “Knowing the old name did not make it part of this endpoint’s contract. The runtime rejected the call.”

Before invalid-key invocation ask: “Will MCP make this credential acceptable to the API?” Then inspect the result.

> “The HTTP exchange carrying the MCP response can succeed while the downstream API request fails. Here we must read the tool content: it reports a downstream `401`, not an account balance.”

Do not equate an outer HTTP `200` with business success. The recorded plugin result represents downstream failure in text content and does not necessarily set `isError`.

**Transition:** “Which boundary made each decision? Let’s follow the request.”

## Slide 11 · 36–41 · Keep the API gateway in the path

**On screen:** Two logical boundaries inside the same APISIX deployment; use the storyboard diagram.

**Demo F:** Inspect the W1 route configuration. Show captured responses and, if rehearsed, actual logs or available backend spans. Do not spend the segment searching for a trace.

> “The MCP route fetches the API contract and translates tool invocation. Its configured base URL sends generated API requests back through APISIX at `/api/v1/*`. That API route checks the forwarded lab key before proxying to the banking service.”
>
> “These are logical boundaries in one gateway for this workshop. We have demonstrated contract exclusion and downstream key authentication. We have not demonstrated customer ownership authorization.”

Ask: “What evidence would your operations team want?” Summarize: tool name, outcome, downstream status, policy or authentication decision, timing, and a correlation identifier. Explain that credentials and unnecessary customer data should not be logged.

> “A production implementation needs evidence across the client, tool layer, and API. The W1 route file does not configure a gateway tracing plugin. We should describe the observations we actually have, and identify the instrumentation needed for stronger correlation.”

**Transition:** “We can now explain what we shipped and what the next workshop must add.”

## Slide 12 · 41–45 · Resolve the task and carry the story forward

Spend one minute on the outcome, one minute on audience recall, and two minutes on questions and the bridge.

> “We started with a customer's request. We generated tools from existing OpenAPI, chose the capabilities for a support job, invoked the two intended reads, and observed two different rejection paths.”
>
> “For the Acme fixture, the returned balance is ₹15,000 INR. The separate seeded dispute case remains open. In a real customer journey, identity and ownership checks must establish which records belong together before we answer Maya.”

Ask attendees for one automated step, one human design decision, and one runtime check. Expected: contract conversion; operation/description curation; API authentication or tool lookup enforcement.

> “Flo now has a purposeful tool catalog, and the API gateway still checks credentials. Next, what happens when a permitted tool is requested with arguments this agent should never be allowed to use?”

Invite questions. Answer deep policy, approval, and workflow questions with a short explanation and point to Workshops 2 and 3 rather than introducing a second architecture lesson.

## Pacing and recovery

At minute 20, start the curation challenge. At minute 29, begin runtime proofs. At minute 41, move to the closing slide. If behind, replace UI chat with the dashboard, summarize the OpenAPI comparison in one minute, and show prepared evidence instead of scrolling logs. Preserve the challenge, the two denials, and the closing questions.

For a failed live step, spend at most 60 seconds checking the endpoint or command, then say: “This is recorded evidence from an earlier run. Let’s inspect the outcome we expected and the boundary responsible.” Never imply the recording proves today’s deployment succeeded.
