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
| **LM Studio** (local) | Just run — auto-detects loaded model from 192.168.3.169:1234 |
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
4. **LM Studio special case**: auto-queries the server for the currently-loaded model

## Automatic Features

- **PI_OFFLINE=1** is set automatically (suppresses update checks for remote providers)
- **Default models** are sensible choices for each provider (can override with `-model`)
- **Model refresh** (LM Studio only): queries the live server each run to follow model changes
- **Credential fallback**: checks auth.json first, then environment variables

## Troubleshooting

**"Can't reach LM Studio"**: Start LM Studio's server (Developer tab) and ensure it's listening on `192.168.3.169:1234`

**"API key not set"**: Either:
- Set the environment variable: `$env:OPENROUTER_API_KEY = "..."`
- Or add it to `~/.pi/agent/auth.json` and use `/login` in Pi

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
