# Modernizing APIs for AI Agents: From OpenAPI to MCP

Presenter package · Workshop 1 · 45 minutes

Start with [facilitator-script.md](facilitator-script.md). Use [slide-storyboard.md](slide-storyboard.md) to assemble the presentation, [demo-runbook.md](demo-runbook.md) at the terminal, and [audience-prompts.md](audience-prompts.md) for interactions and optional follow-along. [fallback-evidence.md](fallback-evidence.md) contains readable extracts from previously recorded evidence.

## Delivery contract

The audience watches a complete demonstration and makes architecture decisions. Following along is optional. Installation happens before the session. Keep the published workshop title exactly as written above.

Maya’s UI introduces the customer need. The MCP demonstration then uses independent enterprise fixtures: Acme Retail Checking (`acc-101`) and customer `cust-8801`’s dispute (`case-501`). Never identify those fixtures as Maya’s account or case. The workshop client invokes MCP directly; it does not demonstrate a model autonomously selecting a tool.

Presenter material is versioned in this repository under `.presenter-private/`. The directory name is retained for existing links; it is not an access-control boundary. This repository currently includes presenter scripts, reveal notes and rehearsal evidence. A separate audience repository will be prepared later; omit facilitator-only notes from that future distribution.

## Timing

| Slide | Minutes | Duration |
|---|---|---|
| 1 | 0–2 | 2 |
| 2 | 2–4 | 2 |
| 3 | 4–8 | 4 |
| 4 | 8–11 | 3 |
| 5 | 11–14 | 3 |
| 6 | 14–17 | 3 |
| 7 | 17–20 | 3 |
| 8 | 20–25 | 5 |
| 9 | 25–29 | 4 |
| 10 | 29–36 | 7 |
| 11 | 36–41 | 5 |
| 12 | 41–45 | 4 |

## Status and preparation

Authored: spoken script, 12 slide beats, exact read/denial demo requests, optional lab, engagement cues, routing visual, historical fallback extracts, and implementation reference map.

The storyboard is Markdown ready for slide authoring, not a rendered PowerPoint deck. No profile was switched, database reset, live model called, or fresh infrastructure rehearsal performed while authoring. Before delivery, rehearse on the intended machine, confirm current tool names, refresh evidence locally, and time the full spoken run. A fast API rehearsal does not establish a 45-minute delivery rehearsal.
