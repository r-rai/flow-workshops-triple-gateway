# Workshop 1 presenter review · 2026-10-06

Reviewed the flow, package README, spoken script, slide storyboard, demo runbook, audience prompts and fallback extracts against the W1 client, route configuration, checkpoints and repository evidence. This was a document/source review; no live infrastructure or timed delivery was run.

## Corrections made

- The top-level flow described presenter material as local-only and excluded from participant access. The files are already tracked. Updated the flow to match the package README: the historical directory name and local exclusion provide no access restriction.
- The flow's closing beat suggested answering Maya from MCP results. Updated it to report separate Acme/account and customer/case fixtures and require verified ownership before answering Maya.
- Made the fixture distinction explicit in the flow and linked this review from the presenter index.

## Findings retained in the package

The existing detailed runbook uses actual discovery rather than a fixed broad catalog count, a read-only payment-list tool for exclusion, nested `pathParameters.id`, separate transport/downstream statuses, and an invalid-credential description matching the CLI implementation. It limits the authentication proof to the demonstrated boundary and does not claim account ownership checks or complete tracing.

The fallback extracts are labelled historical. Their invalid-key denial was recorded on broad `/mcp`, not curated `/mcp/curated`; preserve that distinction. Read-only annotations are not present in the curated checkpoint. The storyboard correctly keeps the customer UI outside the MCP call path.

## Delivery checks remaining

Run fresh broad/curated discovery, both curated reads, excluded-tool rejection and curated invalid-key denial on the intended machine. Preserve current output with date/mode labels and inspect available logs before choosing a routing excerpt. Build the slide deck and time the complete 45-minute presentation. The package currently supplies a Markdown storyboard, not a rendered deck.

Shared W1 worksheet/answer-key timings and older catalog/annotation claims are outside this presenter-folder update. Use the private package's observed-result guidance during delivery and reconcile audience material before creating the separate participant distribution.
