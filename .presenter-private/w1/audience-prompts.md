# Workshop 1 audience prompts and optional follow-along

Facilitator reference. The observer questions below can be read aloud or placed on slides. This file includes presenter reveal notes and is versioned in the presenter repository; omit those notes from the future audience repository.

## Engagement rhythm

Every few minutes, invite a prediction, a vote, or a small design decision. Attendees may answer verbally, by raising hands, or in personal notes. Do not wait for anyone to catch up with an installation. Allow two responses, summarize, and move on.

| Minute | Prompt | Expected reasoning / recovery if quiet |
|---|---|---|
| 3 | Who already has OpenAPI descriptions for APIs an agent might need? | Show of hands establishes relevance; no knowledge test. |
| 5 | Start with the whole API specification or selected operations? | Both are plausible exploration choices. Let the runtime catalog make the tradeoff concrete. |
| 10 | What does “get data” fail to tell a model? | Purpose, required identifier, result meaning, and when to use it. Offer “Would you know whether this answers a balance question?” |
| 18 | Keep payment execution and database reset for this support job? | Remove from this catalog. Existing backend permissions still matter. |
| 21 | Pick the two operations our first release needs. | Account read and case read. Offer the five operation cards if discussion stalls. |
| 23 | Improve “Get account data” in one sentence. | Include a known account ID, balance/currency/status, and minor units. Do not promise authorization through prose. |
| 24 | Is a read-only tool safe for every user? | No; it may reveal sensitive records. Ask “Could it expose somebody else’s balance?” |
| 28 | Can someone call an excluded tool if they remember its name? | Predict; prove using an actual broad tool at the curated endpoint. |
| 33 | Will the tool succeed with an invalid API key? | Predict downstream rejection. Ask the audience where it should be enforced. |
| 35 | The MCP response says HTTP 200. Did the banking read succeed? | Inspect tool content and downstream status. |
| 38 | What evidence would an operator need? | Tool and API outcomes, timing, policy/auth decision, correlation, with sensitive data minimized. |
| 42 | Name one automated step, one human design choice, and one runtime control. | Generation; curation; tool lookup or downstream key authentication. |

## Five-minute design challenge: observer sheet

Task: design capabilities for a support employee who reads account information and inspects a case.

1. Keep two of these operations: account read; case read; payment execution; payment approval; database reset.
2. Rewrite “Get account data” so another engineer can tell what the tool returns and how to interpret money.
3. Write the required identifier and where the generator expects it in the call arguments.
4. Predict what happens when a caller supplies an excluded tool name, then when a caller supplies an invalid API key for a valid tool.

Facilitator answer: keep the two reads; give a purpose-oriented description with integer minor units; use `pathParameters.id` in this lab; expect tool-not-found at the curated endpoint and downstream authentication denial for the invalid key.

## Optional participant terminal sequence

Run only after the W1 profile is prepared. These commands are implementation references, not a requirement for audience participation:

```bash
.venv/bin/python workshops/w1/client.py list
.venv/bin/python workshops/w1/client.py --curated init
.venv/bin/python workshops/w1/client.py --curated list
.venv/bin/python workshops/w1/client.py --curated call-account acc-101
.venv/bin/python workshops/w1/client.py --curated call-unauthorized
```

Participants compare the existing broad and curated checkpoints and take notes on operation selection and descriptions. They do not need to edit gateway configuration during this short segment. Someone who falls behind can inspect the presenter’s result and finish later from the repo.

## Implementation reference map

| Participant need | Existing repository reference |
|---|---|
| Start and select profiles | `docs/workshops/participant-infra-guide.md`, `scripts/workshop` |
| Understand tool calls | `workshops/w1/client.py` |
| Compare capability contracts | `workshops/w1/checkpoints/initial/openapi-broad.json`, `workshops/w1/checkpoints/completed/openapi-curated.json` |
| Inspect generation and API enforcement | `docker/apisix/apisix-w1.yaml` |
| Reproduce case reads and excluded calls | `workshops/w1/rehearsal_w1.py` |
| Understand fixture data | `seed/v1_seed.json` |

Current public worksheet/answer-key timings differ from this private delivery flow. Their fixed catalog count and annotation statements also need care. For this session, verbally identify the optional commands above and use observed runtime output. Editing or publishing the shared participant materials is a separate change; none was made while authoring this private package.

## Likely questions

**Why not use REST directly?** That is possible. MCP provides a common tool interface for compatible hosts and clients; choose based on integration needs.

**Does a good description make a tool safe?** It helps selection and interpretation. Enforcement belongs in deterministic runtime controls.

**Why exclude a payment-list read?** It is outside this first support job and makes a low-impact test of runtime exclusion. Read operations can still expose sensitive information.

**Where is the real agent?** Today’s CLI exposes discovery and invocation directly. The UI opening is separate. This lab does not prove autonomous model tool selection; later sessions build on the integration foundation.

**Is this production-ready?** It is a teaching deployment with lab credentials. Production requires appropriate identity, ownership authorization, lifecycle operations, telemetry, and deployment controls.

**What about tool annotations?** Treat them as descriptive hints, not enforcement. Inspect actual generated metadata; this curated JSON does not contain the previously claimed readOnlyHint.

**Can a customer read any account ID?** This example proves key authentication, not customer ownership restrictions. Do not offer an ownership guarantee from this lab.
