# Modernizing APIs for AI Agents: From OpenAPI to MCP

Private presenter flow — Workshop 1 — 45 minutes.

## Delivery

Audience: experienced API architects and integration engineers. Deliver from the presenter screen, with audience predictions and decisions throughout. A short optional lab lets participants follow along; observers receive the complete learning experience without running infrastructure. Prepare infrastructure before the session.

Use the participant repository for code, setup, implementation references, and optional exercises. Keep this narrative, speaker cues, reveal timing, and fallback instructions local. This folder is excluded through .git/info/exclude, which is not shared with participants. Local Git exclusion prevents ordinary staging; it is not access control or a backup.

## Story

Maya wants to know her account balance and what is happening with her support case. Flo Bank already has APIs. The audience becomes the architecture team responsible for exposing appropriate MCP capabilities while preserving existing API controls.

Opening script:

> Maya has a simple request: “What’s my account balance, and what’s happening with my support case?” Flo Bank already has APIs for both. Your team has 45 minutes to make those capabilities available through MCP. What would you expose—and how would you prove the existing controls still work?

The customer UI introduces the business scenario. Its existing tools do not call the Workshop 1 MCP endpoint. Make this distinction explicit when moving to the workshop client.

## Timed flow

| Minutes | Beat | Presenter action and audience cue |
|---|---|---|
| 0–4 | Meet Maya | Show Flo’s customer experience with a prepared account question. Establish the need; invite a quick show of hands on API modernization experience. |
| 4–8 | You own the architecture | Give the assignment: account and case reads, no payments or administration, existing controls preserved. Ask what the agent needs to discover and invoke these capabilities. |
| 8–14 | From documentation to tools | Compare one OpenAPI operation with its generated MCP tool. Explain initialization, tools/list, and tools/call. Show client → MCP gateway → API gateway boundary → banking API. |
| 14–20 | First success, then reveal | Discover the broad catalog and read an account. Highlight payment and admin names. Ask which capabilities belong in Maya’s support journey. Discovery and permission to execute are separate. |
| 20–29 | Design Flo’s toolbox | Lead the optional mini-lab: select operations, improve a description, identify arguments and money units. Reveal the prepared curated contract. Initialize and list /mcp/curated, showing get_account and get_case. |
| 29–36 | Prove the boundary | Read the account and case through the curated endpoint. Predict then demonstrate rejection of an actual excluded broad tool. Predict then demonstrate rejection of an account read using invalid downstream credentials. Explain the two mechanisms. |
| 36–41 | Show evidence | Follow the MCP-to-REST route through Gate 3. Inspect success, excluded-tool rejection, downstream authentication error, and available gateway evidence. State the limits of what the demonstration proves. |
| 41–45 | Answer Maya and bridge | Answer using returned data. Ask attendees for one generated detail, one curated decision, and one runtime control. Reserve two minutes for questions, then bridge to Workshop 2. |

Closing bridge:

> Flo now has a purposeful tool catalog, and the API gateway still checks credentials. Next, what happens when a permitted tool is requested with arguments this agent should never be allowed to use?

## Demo preparation and optional lab

Use workshops/w1/client.py for discovery and account reads. Prepared command sequence:

```bash
python workshops/w1/client.py init
python workshops/w1/client.py list
python workshops/w1/client.py call-account acc-101
python workshops/w1/client.py --curated init
python workshops/w1/client.py --curated list
python workshops/w1/client.py --curated call-account acc-101
python workshops/w1/client.py --curated call-unauthorized
```

The client has no dedicated case-read command. Prepare the get_case request using the request structure in workshops/w1/rehearsal_w1.py. For excluded-tool rejection, capture a real broad tool name and attempt it on /mcp/curated using the same rehearsal request structure. Do not invoke payment mutation or admin reset as part of the story.

Compare workshops/w1/checkpoints/initial/openapi-broad.json with workshops/w1/checkpoints/completed/openapi-curated.json. Demonstrate the prepared curated endpoint rather than depending on a live contract edit refreshing plugin caches. Explain that participant description edits are design decisions until applied and verified in the runtime.

Observers can take notes against three prompts: which tools to keep/remove; how to improve one description; which boundary rejects each request.

## Accuracy and fallback cues

- Use actual discovered tool names and counts; older notes hard-code 13 tools.
- Verify seeded fixture identities and case details before connecting them to Maya’s story.
- If the account returns 1500000 INR minor units, explain it as ₹15,000.
- OpenAPI and MCP are complementary; avoid claiming agents cannot call REST or MCP guarantees reliability/security.
- The curated endpoint excludes operations; the broad endpoint remains a teaching checkpoint. Removing a tool from this catalog does not revoke it everywhere.
- The invalid-key example demonstrates downstream authentication, not account ownership authorization.
- Inspect emitted metadata before discussing annotations. The current curated checkpoint does not contain the readOnlyHint claimed in older worksheet text.
- Show available route/log evidence; do not infer backend non-execution from a status code alone.
- Check MCP and APISIX terminology against current official documentation while developing slides.
- Keep clearly labelled saved catalog, successful reads, denials, and routing evidence. Allow at most 60 seconds to troubleshoot before switching to saved evidence, preserving predictions and explanation.
- Rehearse within 45 minutes before delivery. Saved evidence is not a fresh runtime verification.

## Facilitator package

The authored package is in [w1/README.md](w1/README.md): spoken script, 12-slide storyboard, exact demo runbook, observer prompts and optional lab, and labelled historical fallback extracts. The package uses separate Acme/customer fixtures for MCP rather than identifying them as Maya’s records. No shared participant files were changed. Rendering a slide deck and a timed live rehearsal remain delivery preparation tasks.
