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
- TTS, image-edit, and embedding models are filtered out (they aren't chat endpoints).
- Vision models get `input: [text, image]`; `<think>`-emitting families get `reasoning: true`.

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
