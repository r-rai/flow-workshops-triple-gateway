# OpenRouter setup for participants

Use your own OpenRouter API key to run optional live inference with free models
on your local workshop stack. Complete the [infrastructure setup](participant-infra-guide.md)
first. Commands below run from the repository root in Bash (Linux, macOS, or
Windows WSL). No OpenRouter SDK installation is needed.

Gate 1 currently follows `APISIX → Python adapter → configured provider`.
These settings switch that adapter from MiniMax to OpenRouter; they select one
provider for the stack. The existing replay exercises still work without a key.

## 1. Create your API key

1. Sign in or create an account at [OpenRouter](https://openrouter.ai/).
2. Open [API Keys](https://openrouter.ai/settings/keys), choose **Create Key**,
   and name it `flo-bank-workshop`.
3. Copy the key into your local `.env` in the next step. Keep it private; do not
   commit it or paste it into chat, screenshots, or workshop evidence.

Free models have zero token cost. A paid credit purchase is optional for the
basic free-model tier. Creating a key does not make paid models free.
See the [OpenRouter quickstart](https://openrouter.ai/docs/quickstart).

## 2. Configure the local environment

If `.env` does not exist yet, copy the sample once:

```bash
cp .env.example .env
```

If you already have `.env`, edit it instead of replacing it. Update the existing
entries and add `LLM_API_KEY` and `DEMO_CHAT_MODE` if missing. Use one entry per
variable:

```dotenv
USE_REPLAY_FIXTURES=false
MINIMAX_API_KEY=
LLM_API_KEY=<paste-your-openrouter-key-here>
LLM_PROVIDER_URL=https://openrouter.ai/api/v1/chat/completions
LLM_MODEL=openrouter/free
DEMO_CHAT_MODE=live
```

Replace the key placeholder with your actual key. Use `LLM_API_KEY`: the current
Compose configuration does not pass an `OPENROUTER_API_KEY` variable to the
adapter. Leave `MINIMAX_API_KEY` empty because it takes precedence over
`LLM_API_KEY`, even when the URL points to OpenRouter. `LLM_API_KEY` takes
precedence over the sample's mock `OPENAI_API_KEY`.

Docker Compose reads `.env`; you do not need to source it in your shell. If you
previously exported any of these variables in the current shell, clear them so
they do not override `.env`:

```bash
unset MINIMAX_API_KEY LLM_API_KEY LLM_PROVIDER_URL LLM_MODEL USE_REPLAY_FIXTURES DEMO_CHAT_MODE
```

### Choose a free model

`openrouter/free` is a quick starting point. It selects an available free model
and filters for features requested by the client, including tool calling. The
selected model can change between requests. See the
[free router description](https://openrouter.ai/openrouter/free).

For repeatable workshop behavior, use the facilitator's tested model ID instead:

1. Browse the [OpenRouter model catalog](https://openrouter.ai/models).
2. Select a currently available free model that supports **Tools / tool calling**.
   Flo and the W3 agent need function calling; text-only success is insufficient.
3. Copy its exact ID, including the `:free` suffix, into `LLM_MODEL`.
4. Recreate the services below after any model change.

Free model availability changes. Confirm the model is still free and run the
relevant live exercise before the session.

## 3. Start or recreate your chosen profile

Run one profile at a time. Stop your current profile before moving between the
customer demo and workshop stacks; see [profile switching](participant-infra-guide.md#8-switching-between-workshops--resetting-lab-state).
Choose one option below. `docker compose restart` alone does not reload `.env`.

### Customer chatbot: `demo`

```bash
docker compose --profile demo up -d --build --force-recreate
```

Open **http://localhost:8000**, sign in with `maya@flobank.demo` / `flo-demo`,
and ask Flo to check your balance. This profile passes `LLM_MODEL` to both the
inference adapter and chatbot.

### Governance Studio: `w2`

```bash
ACTIVE_PROFILE=w2 docker compose --profile w2 up -d --build --force-recreate
```

Open **http://localhost:9080/workshop-2** and follow the
[W2 worksheet](../../workshops/w2/worksheet.md). Select **Ask Flo to review the
case** for live inference. **Replay the unsafe proposal** uses recorded data and
does not test OpenRouter.

### Durable agent: `w3`

```bash
ACTIVE_PROFILE=w3 docker compose --profile w3 up -d --build --force-recreate
```

The adapter and worker both receive the configured model. Follow the
[W3 worksheet](../../workshops/w3/worksheet.md) for the workflow commands, but
keep `USE_REPLAY_FIXTURES=false` for the optional live run. The worksheet's
recorded refund amount is a replay expectation; live model proposals can differ.

W1's core MCP exercise does not need a model key. W4's recorded Incident Room
exercises also do not need live inference; keep the worksheet defaults unless
your facilitator requests a live comparison. For the chatbot, use the `demo`
profile above: the customer chatbot mounted inside workshop/enterprise profiles
currently has a separate MiniMax model default.

## 4. Verify Gate 1 and make one live request

For W2/W3, inspect readiness through APISIX:

```bash
curl --fail-with-body --silent --show-error http://localhost:9080/ai/status
```

For `demo`, whose inference gateway is internal, use:

```bash
docker compose --profile demo exec -T demo-inference python -c 'import httpx; r = httpx.get("http://localhost:8080/ai/status"); r.raise_for_status(); print(r.text)'
```

Expect `mode: "live"`, `use_replay_fixtures: false`, `provider_configured: true`,
and your configured model. Readiness checks only establish that a key is present;
they do not validate the key or call OpenRouter.

For W2/W3, make one small live smoke request:

```bash
curl --fail-with-body --silent --show-error \
  http://localhost:9080/ai/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"messages":[{"role":"user","content":"Reply with: workshop ready"}],"max_tokens":128}'
```

The request omits `model` so the adapter uses `LLM_MODEL`. Expect a completion
with `choices` and an assistant message. Check [OpenRouter Activity](https://openrouter.ai/activity)
for the request and model used. Then run one tool-based chatbot or workshop
exercise; this text smoke request does not verify tool calling. In `demo`, use
the balance query from step 3 and check Activity instead of the localhost curl.

## 5. Free-tier limits and troubleshooting

As checked on 2026-10-06, OpenRouter documents these free-model limits:

| Total credits purchased | Requests per minute | Requests per day |
|---|---:|---:|
| Less than $10 | 20 | 50 |
| At least $10 | 20 | 1,000 |

Limits apply across keys on the account. One agent interaction may make several
model requests, including tool follow-ups; 50 requests does not mean 50 chat
turns. Free providers can also reach capacity before your quota is exhausted.
Check the [current limits](https://openrouter.ai/docs/api_reference/limits) and
[published limit constants](https://github.com/OpenRouterTeam/docs/blob/main/snippets/exports/constants.mdx)
before the workshop. Each participant should use their own key for their local
stack. A shared hosted stack uses its server's configured key.

| Symptom | What to check |
|---|---|
| `401` or invalid key | Replace the placeholder with a valid OpenRouter key; clear `MINIMAX_API_KEY`; recreate services. |
| `402` or insufficient credits | Confirm the selected model is free and inspect the account/key credit limits. |
| `429` or provider capacity error | Honor `Retry-After` if present, wait before retrying, or select another free tool-capable model. Changing models does not reset account daily quota. |
| Model not found or unsupported tools | Copy the exact current model ID and confirm tool-calling support. |
| Status still says replay or MiniMax | Check `.env` and shell overrides, then recreate services. In W3, recreate the worker too. |
| Inference budget exceeded | The adapter's local token budget is separate from OpenRouter quota. Recreate the adapter (`demo-inference` for demo) to reset its in-memory counter. |
| Chatbot stays scripted | Set `DEMO_CHAT_MODE=live` and recreate the demo; check Gate 1 readiness. |

## 6. Return to replay or MiniMax

For recorded workshop exercises, set `USE_REPLAY_FIXTURES=true`. For the offline
customer chatbot, also set `DEMO_CHAT_MODE=scripted`. Recreate the active profile
using the command from step 3 and resume the worksheet.

To switch back to MiniMax, update `.env`:

```dotenv
MINIMAX_API_KEY=<your-minimax-key>
LLM_API_KEY=
LLM_PROVIDER_URL=https://api.minimax.io/v1/chat/completions
LLM_MODEL=MiniMax-M2.7-highspeed
USE_REPLAY_FIXTURES=false
DEMO_CHAT_MODE=live
```

Recreate the active profile again. These instructions do not configure automatic
fallback between OpenRouter and MiniMax.
