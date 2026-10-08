# Workshop 1: Give Flo the right tools

Modernizing APIs for AI Agents: From OpenAPI to MCP

Duration: 45 minutes. Last slide is presenter reference outside the timed agenda.

Expected outcomes in these slides are instructional targets, not fresh execution results.

## 01. Give Flo the right tools

**Timing:** 0–5 min

Open with the support request: Flo needs to read an account and understand a case. Introduce fictional Flo Bank and the audience's role as the integration team. W1 uses the native APISIX openapi-to-mcp plugin; this CLI lab needs no provider key. Prepare the stack before the clock starts.

Sources: [workshop-1-story.md](../../../docs/workshops/workshop-1-story.md), [worksheet.md](../../../workshops/w1/worksheet.md), [answer-key.md](../../../workshops/w1/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md)

## 02. One bank. Four engineering questions.

**Timing:** 0–5 min

Briefly position W1 within the series. W2 adds execution governance, W3 durable work, and W4 incident response and delegation. Each workshop starts independently from prepared lab data.

Sources: [workshop-1-story.md](../../../docs/workshops/workshop-1-story.md), [worksheet.md](../../../workshops/w1/worksheet.md), [answer-key.md](../../../workshops/w1/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md)

## 03. The 45-minute route

**Timing:** 0–5 min

Use these as segment boundaries, not time allocated to every individual slide. Downloads and profile setup are outside the 45-minute session. Open the worksheet for copyable commands.

Sources: [workshop-1-story.md](../../../docs/workshops/workshop-1-story.md), [worksheet.md](../../../workshops/w1/worksheet.md), [answer-key.md](../../../workshops/w1/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md)

## 04. Start with the customer's job

**Timing:** 0–5 min

Show the live method, path, input and response, then connect it to the bank page. Browser demo accounts are demo-checking and demo-savings; the MCP exercise uses acc-101. Documentation access does not authorize banking operations. Keep optional card/dispute mutations out of the timed path.

Sources: [workshop-1-story.md](../../../docs/workshops/workshop-1-story.md), [worksheet.md](../../../workshops/w1/worksheet.md), [answer-key.md](../../../workshops/w1/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md)

## 05. An HTTP contract becomes a tool interface

**Timing:** 5–12 min

Ask what a generator can infer from a contract and what requires business context. Keep the comparison grounded in this lab, rather than presenting an exhaustive protocol comparison.

Sources: [workshop-1-story.md](../../../docs/workshops/workshop-1-story.md), [worksheet.md](../../../workshops/w1/worksheet.md), [answer-key.md](../../../workshops/w1/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md)

## 06. Follow the generated call

**Timing:** 5–12 min

These are logical stages, not four separate gateway products. W1 demonstrates API-key validation at Gate 3. W2–W4 introduce richer signed identities and scope controls. Show the actual route/log evidence later.

Sources: [workshop-1-story.md](../../../docs/workshops/workshop-1-story.md), [worksheet.md](../../../workshops/w1/worksheet.md), [answer-key.md](../../../workshops/w1/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md)

## 07. Demo: initialize and discover

**Timing:** 12–22 min

Run from the repository root. The supplied CLI does not retain a session between commands. Locate the generated payment and reset tools without invoking them. The broad tool count depends on the served API contract; do not promise a fixed number.

```bash
.venv/bin/python workshops/w1/client.py init
.venv/bin/python workshops/w1/client.py list
```

Sources: [workshop-1-story.md](../../../docs/workshops/workshop-1-story.md), [worksheet.md](../../../workshops/w1/worksheet.md), [answer-key.md](../../../workshops/w1/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md)

## 08. Generated correctly. Scoped too broadly.

**Timing:** 12–22 min

Let participants inspect the broad checkpoint at workshops/w1/checkpoints/initial/openapi-broad.json. Existing authorization still applies to broad tools; discovery alone does not prove a call is authorized.

Sources: [workshop-1-story.md](../../../docs/workshops/workshop-1-story.md), [worksheet.md](../../../workshops/w1/worksheet.md), [answer-key.md](../../../workshops/w1/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md)

## 09. Design two tools that explain their job

**Timing:** 22–32 min

Compare workshops/w1/checkpoints/completed/openapi-curated.json. Generated inputs use pathParameters.id. The completed checkpoint contains no readOnlyHint annotation. Descriptions or hints alone are not authorization.

Sources: [workshop-1-story.md](../../../docs/workshops/workshop-1-story.md), [worksheet.md](../../../workshops/w1/worksheet.md), [answer-key.md](../../../workshops/w1/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md)

## 10. Exercise: curate the support contract

**Timing:** 22–32 min

Allocate a short pair discussion within this ten-minute block. Use the prepared completed endpoint for executable comparison. A local file edit does not update the running catalog by itself; check plugin caching/refresh before claiming a live change.

Sources: [workshop-1-story.md](../../../docs/workshops/workshop-1-story.md), [worksheet.md](../../../workshops/w1/worksheet.md), [answer-key.md](../../../workshops/w1/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md)

## 11. Demo: a useful account read

**Timing:** 22–32 min

Explain integer minor units: 100 paise equals one rupee. If the ledger has changed, record the returned result rather than asserting the fresh-seed balance. This read demonstrates an actual governed API result.

```bash
.venv/bin/python workshops/w1/client.py call-account acc-101
```

Sources: [workshop-1-story.md](../../../docs/workshops/workshop-1-story.md), [worksheet.md](../../../workshops/w1/worksheet.md), [answer-key.md](../../../workshops/w1/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md)

## 12. Demo: invoke the curated endpoint

**Timing:** 22–32 min

The broad endpoint is /mcp. The curated endpoint is preconfigured. Use the W1 rehearsal's case-read and excluded payment-list checks as additional evidence. A rejected removed read/list operation proves exclusion without executing a financial mutation.

```bash
.venv/bin/python workshops/w1/client.py --curated init
.venv/bin/python workshops/w1/client.py --curated list
.venv/bin/python workshops/w1/client.py --curated call-account acc-101
```

Sources: [workshop-1-story.md](../../../docs/workshops/workshop-1-story.md), [worksheet.md](../../../workshops/w1/worksheet.md), [answer-key.md](../../../workshops/w1/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md)

## 13. Exclusion must hold at invocation too

**Timing:** 32–40 min

The rehearsal invokes an actual broad payment-list tool against the curated endpoint. Do not invoke payment mutations or administrative resets merely to show absence. Evidence for routing is needed to attribute the downstream denial to Gate 3.

Sources: [workshop-1-story.md](../../../docs/workshops/workshop-1-story.md), [worksheet.md](../../../workshops/w1/worksheet.md), [answer-key.md](../../../workshops/w1/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md)

## 14. Demo: the banking boundary still applies

**Timing:** 32–40 min

Ask participants to find the embedded HTTP status and confirm that no successful account result was returned. W1 proves the lab's API-key boundary; it does not prove full customer-specific authorization or production identity management.

```bash
.venv/bin/python workshops/w1/client.py --curated call-unauthorized
```

Sources: [workshop-1-story.md](../../../docs/workshops/workshop-1-story.md), [worksheet.md](../../../workshops/w1/worksheet.md), [answer-key.md](../../../workshops/w1/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md)

## 15. What evidence earns a pass?

**Timing:** 40–45 min

Have pairs report their removed operation, clearer description and authorization evidence. Save the contract and invocation/denial output. Ask where the evidence would be insufficient without routing logs.

Sources: [workshop-1-story.md](../../../docs/workshops/workshop-1-story.md), [worksheet.md](../../../workshops/w1/worksheet.md), [answer-key.md](../../../workshops/w1/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md)

## 16. Next: the tool reads an attacker’s instructions

**Timing:** 40–45 min

Close the story: Flo now has tools matched to support work. Invite questions about generation, cache refresh and downstream enforcement. Bridge to a legitimate case read containing malicious instructions.

Sources: [workshop-1-story.md](../../../docs/workshops/workshop-1-story.md), [worksheet.md](../../../workshops/w1/worksheet.md), [answer-key.md](../../../workshops/w1/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md)

## 17. Presenter preparation & source guide

**Timing:** Reference / outside timed delivery

Preparation commands: ./scripts/workshop switch w1; after preserving evidence, ./scripts/workshop reset w1 --yes; ./scripts/workshop verify w1. Optional technical rehearsal: .venv/bin/python workshops/w1/rehearsal_w1.py. It overwrites workshops/w1/evidence/rehearsal-evidence.json. See docs/workshops/w1-api-walkthrough.md and docs/workshops/participant-infra-guide.md. These decks do not run or reset the labs.

Sources: [workshop-1-story.md](../../../docs/workshops/workshop-1-story.md), [worksheet.md](../../../workshops/w1/worksheet.md), [answer-key.md](../../../workshops/w1/answer-key.md), [delivery-plan.md](../../../docs/workshops/delivery-plan.md)
