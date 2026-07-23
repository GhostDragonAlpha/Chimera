# Pi Multi-Provider Launcher

Interactive launcher for Pi coding agent with support for 12+ LLM providers.

## Quick Start

```powershell
.\pi-launcher.ps1
```

Select your provider from the menu.

## Supported Providers

| Provider | Setup |
|----------|-------|
| **LM Studio** (local) | Just run — defaults to whichever model is loaded, and offers the rest under `/model` |
| **OpenRouter** | Set `$env:OPENROUTER_API_KEY = "sk-..."` |
| **DeepSeek** | Set `$env:DEEPSEEK_API_KEY = "sk-..."` |
| **Anthropic (Claude)** | Set `$env:ANTHROPIC_API_KEY = "sk-ant-..."` |
| **OpenAI** | Set `$env:OPENAI_API_KEY = "sk-..."` |
| **Google Gemini** | Set `$env:GEMINI_API_KEY = "..."` |
| **Mistral** | Set `$env:MISTRAL_API_KEY = "..."` |
| **Groq** | Set `$env:GROQ_API_KEY = "..."` |
| **xAI (Grok)** | Set `$env:XAI_API_KEY = "..."` |
| **NVIDIA NIM** | Set `$env:NVIDIA_API_KEY = "..."` |
| **Together AI** | Set `$env:TOGETHER_API_KEY = "..."` |
| **Azure OpenAI** | Set `$env:AZURE_OPENAI_API_KEY = "..."` |

## Setting API Keys

### Option 1: Environment Variable (temporary)
```powershell
$env:OPENROUTER_API_KEY = "sk-or-..."
.\pi-launcher.ps1
```

### Option 2: Persistent (auth.json)
Use Pi's `/login` command in interactive mode, or add to `~/.pi/agent/auth.json`:
```json
{
  "openrouter": { "type": "api_key", "key": "sk-or-..." },
  "deepseek": { "type": "api_key", "key": "sk-..." },
  "anthropic": { "type": "api_key", "key": "sk-ant-..." }
}
```

## Usage Examples

```powershell
# Interactive menu
.\pi-launcher.ps1

# Direct provider + model selection
.\pi-launcher.ps1 -provider deepseek -model deepseek-chat

# Pass args to Pi (e.g., continue last session)
.\pi-launcher.ps1 -provider openrouter -c
```

## How It Works

1. **Display menu** if no provider specified
2. **Verify API key** is set (environment variable or auth.json)
3. **Launch Pi** with the selected provider and default model
4. **LM Studio special case**: delegates to `pi-lmstudio.ps1` (see below)

## LM Studio

`pi-lmstudio.ps1` (or `pi-lmstudio.bat`) re-reads the server on every launch and rewrites
`~/.pi/agent/models.json`. It publishes **every** chat-capable model LM Studio is serving and
makes the **currently loaded** one the default, so:

- Launching always lands on whatever you have loaded — no hardcoded model id to go stale.
- Pi's in-session `/model` picker lists the others; LM Studio JIT-loads whichever you pick.
- TTS, image-edit, and embedding models are filtered out by `arch` (they aren't chat endpoints).
- Vision models get `input: [text, image]`.

### Thinking / reasoning

Thinking is **not** a property of the weights — it's decided per request by the
`reasoning_effort` parameter, so it cannot be inferred from the model id. Measured against
this server with the LM Studio UI toggle *off*:

| request | completion tokens | reasoning emitted |
|---|---|---|
| no `reasoning_effort` sent | 122 | yes (633 chars) |
| `reasoning_effort=none` | 2 | no |
| `reasoning_effort=low`/`medium`/`high` | ~150–170 | yes (~700–800 chars) |

Note the first row: **omitting the parameter leaves thinking on**, and the per-request value
overrides the UI toggle. So every chat model is published with `reasoning: true` plus a
`thinkingLevelMap` mapping Pi's `off` level to `"none"`. That puts the switch in Pi, where you
can reach it — `/thinking` in-session, or `--model <id>:off` / `:high` on the command line:

```
<id>:off   ->  0 thinking blocks,  2 output tokens
<id>:high  -> 28 thinking blocks, 24 output tokens
```

Set `$env:PI_LMS_REASONING = "0"` to publish `reasoning: false` instead, which makes Pi never
send the parameter at all (and therefore leaves thinking at the server's default: on).

```powershell
.\pi-lmstudio.ps1                 # launch on the loaded model
.\pi-lmstudio.ps1 -List           # show what LM Studio is serving
.\pi-lmstudio.ps1 -Model <id>     # force a specific model as the default
.\pi-lmstudio.ps1 -c              # any other args are forwarded to pi

$env:LMS_URL = "http://other-box:1234"   # point at a different LM Studio
$env:PI_LMS_REASONING = "0"              # force reasoning:false on every model
```

## Automatic Features

- **PI_OFFLINE=1** is set automatically (suppresses update checks)
- **Default models** are sensible choices for each provider (can override with `-model`)
- **Model refresh** (LM Studio only): queries the live server each run to follow model changes
- **Credential fallback**: checks auth.json first, then environment variables

## Troubleshooting

**"Can't reach LM Studio"**: Start LM Studio's server (Developer tab) and ensure it's listening on `192.168.3.169:1234`

**"API key not set"**: Either:
- Set the environment variable: `$env:OPENROUTER_API_KEY = "..."`
- Or add it to `~/.pi/agent/auth.json` and use `/login` in Pi

**Pi won't let you pick the loaded model**: you launched bare `pi`, which reads a config that
may name a model LM Studio isn't serving. Launch via `pi-lmstudio.ps1` — it resyncs the config
first. Run `.\pi-lmstudio.ps1 -List` to see what's actually available.

**Wrong model loaded**: For non-LM Studio providers, set it explicitly:
```powershell
.\pi-launcher.ps1 -provider openai -model gpt-4
```

## Edit the Launcher

To add a provider, edit `pi-launcher.ps1` and add an entry to the `$providers` array with:
- `name`: The Pi provider ID (e.g., "openai", "together")
- `display`: Human-readable name
- `description`: What it does
- `apiKeyVar`: Environment variable name (or "none" if not applicable)
- `defaultModel`: Default model ID for that provider

## Extensions

Project-local extensions live in `.pi/extensions/` and load per the list in
`.pi/settings.json`. Two of note (added/repaired 2026-07-10):

### `web-browsing.ts` — real browsing via local Chromium

Provides `web_browse`, `web_search_real`, `web_extract`, `web_screenshot`. **This
was silently non-functional and is now repaired** — worth knowing if an agent has
been "refusing to research":

- `web_browse` passed `params` into `page.evaluate()` as a closure. That callback
  runs *inside the browser*, where `params` doesn't exist, so every call threw
  `ReferenceError` and the `catch` returned a polite string. It had never worked.
- `web_search_real` scraped Google `div.g`, which returns nothing headless (bot
  wall) and reported `status: "success"` anyway.

Repaired: arguments are passed into `evaluate()`; search uses **Startpage**
(primary) with a **Bing** fallback (its `ck/a` redirects are base64-unwrapped);
**zero results is now an error, never success.** Backend survey, headless, realistic
UA: `startpage 200` / `bing 200 (needs networkidle)` / `ddg-lite 403` /
`ddg-html 403` / `mojeek captcha` / `marginalia 502`.

### `proof-of-use.ts` — research enforced at the harness

Blocks any `write`/`edit` into `Source/` that introduces an Unreal API symbol the
agent has not read, blocks calls to symbols that do not exist, and reverts any file
whose `#include`s do not resolve. Enforcement is external (ripgrep + the engine
source on disk), fails closed, and provides `research_engine` / `research_cite`
tools plus a `/proof` command to inspect the citation ledger.

Full design, measured evidence, and known limitations:
[`Chimera/docs/RESEARCH_ENFORCEMENT.md`](Chimera/docs/RESEARCH_ENFORCEMENT.md).

```powershell
CHIMERA_PROOF_OF_USE=0   # make the gate advisory (records citations, never blocks)
```
