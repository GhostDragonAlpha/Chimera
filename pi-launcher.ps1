#!/usr/bin/env pwsh
# pi-launcher.ps1 — Interactive launcher for Pi with multiple LLM providers.
#
# Supports: LM Studio (local), OpenRouter, DeepSeek, OpenAI, Anthropic, Gemini,
# Mistral, Groq, xAI, Azure OpenAI, AWS Bedrock, and more.
#
# Usage:   .\pi-launcher.ps1
#          .\pi-launcher.ps1 -provider openrouter
#          .\pi-launcher.ps1 -provider deepseek -model deepseek-chat
#
# Credentials are loaded from environment variables or ~/.pi/agent/auth.json

$ErrorActionPreference = 'Stop'

# ─── Define available providers ─────────────────────────────────────────────
$providers = @(
  @{
    name = "lm-studio"
    display = "LM Studio (local)"
    description = "Local models via LM Studio server (192.168.3.169:1234)"
    apiKeyVar = "none"
    # Never hardcode an id here -- pi-lmstudio.ps1 detects whatever is loaded at launch.
    defaultModel = "(currently loaded)"
  },
  @{
    name = "openrouter"
    display = "OpenRouter"
    description = "Access 200+ models via single API"
    apiKeyVar = "OPENROUTER_API_KEY"
    defaultModel = "openrouter/auto"
  },
  @{
    name = "deepseek"
    display = "DeepSeek"
    description = "DeepSeek V3 and R1 reasoning models"
    apiKeyVar = "DEEPSEEK_API_KEY"
    defaultModel = "deepseek-chat"
  },
  @{
    name = "anthropic"
    display = "Anthropic (Claude)"
    description = "Claude Opus, Sonnet, Haiku"
    apiKeyVar = "ANTHROPIC_API_KEY"
    defaultModel = "claude-opus-4-8"
  },
  @{
    name = "openai"
    display = "OpenAI"
    description = "GPT-4, GPT-4o"
    apiKeyVar = "OPENAI_API_KEY"
    defaultModel = "gpt-4o"
  },
  @{
    name = "google"
    display = "Google Gemini"
    description = "Gemini 2.0 models"
    apiKeyVar = "GEMINI_API_KEY"
    defaultModel = "gemini-2.0-flash"
  },
  @{
    name = "mistral"
    display = "Mistral"
    description = "Mistral Large, 7B"
    apiKeyVar = "MISTRAL_API_KEY"
    defaultModel = "mistral-large"
  },
  @{
    name = "groq"
    display = "Groq"
    description = "Ultra-fast inference"
    apiKeyVar = "GROQ_API_KEY"
    defaultModel = "mixtral-8x7b-32768"
  },
  @{
    name = "xai"
    display = "xAI (Grok)"
    description = "Grok models"
    apiKeyVar = "XAI_API_KEY"
    defaultModel = "grok-2"
  },
  @{
    name = "nvidia"
    display = "NVIDIA NIM"
    description = "NVIDIA hosted inference"
    apiKeyVar = "NVIDIA_API_KEY"
    defaultModel = "meta/llama-3.1-405b-instruct"
  },
  @{
    name = "together"
    display = "Together AI"
    description = "Together AI model hub"
    apiKeyVar = "TOGETHER_API_KEY"
    defaultModel = "meta-llama/Llama-3.1-70B"
  },
  @{
    name = "azure-openai-responses"
    display = "Azure OpenAI"
    description = "Enterprise Azure deployment"
    apiKeyVar = "AZURE_OPENAI_API_KEY"
    defaultModel = "gpt-4"
  }
)

# ─── Parse CLI args ────────────────────────────────────────────────────────
$provider = ""
$model = ""
$piArgs = @()

# Parse -provider, -model, and pass remaining args to Pi
$i = 0
while ($i -lt $args.Count) {
  if ($args[$i] -eq "-provider" -and $i + 1 -lt $args.Count) {
    $provider = $args[$i + 1]
    $i += 2
  } elseif ($args[$i] -eq "-model" -and $i + 1 -lt $args.Count) {
    $model = $args[$i + 1]
    $i += 2
  } else {
    $piArgs += $args[$i]
    $i++
  }
}

# ─── Select provider ──────────────────────────────────────────────────────
if ([string]::IsNullOrEmpty($provider)) {
  Write-Host ""
  Write-Host "═════════════════════════════════════════════" -ForegroundColor Cyan
  Write-Host "  Pi — Multi-Provider Launcher" -ForegroundColor Cyan
  Write-Host "═════════════════════════════════════════════" -ForegroundColor Cyan
  Write-Host ""

  for ($i = 0; $i -lt $providers.Count; $i++) {
    $p = $providers[$i]
    $num = $i + 1
    Write-Host "  [$num]  $($p.display)" -ForegroundColor Green
    Write-Host "        $($p.description)"
    Write-Host ""
  }

  $selection = Read-Host "Select provider (1-$($providers.Count))"
  $idx = [int]$selection - 1

  if ($idx -lt 0 -or $idx -ge $providers.Count) {
    Write-Host "Invalid selection." -ForegroundColor Red
    exit 1
  }

  $selectedProvider = $providers[$idx]
} else {
  $selectedProvider = $providers | Where-Object { $_.name -eq $provider }
  if (-not $selectedProvider) {
    Write-Host "Provider '$provider' not found." -ForegroundColor Red
    exit 1
  }
}

$providerName = $selectedProvider.name
$modelName = if ([string]::IsNullOrEmpty($model)) { $selectedProvider.defaultModel } else { $model }

# ─── Set up provider-specific environment ───────────────────────────────────
Write-Host ""
Write-Host "  Launching Pi..." -ForegroundColor Cyan
Write-Host "  Provider: $($selectedProvider.display)" -ForegroundColor Cyan
Write-Host "  Model:    $modelName" -ForegroundColor Cyan
Write-Host ""

# LM Studio special case: delegate to pi-lmstudio.ps1, which publishes every served model
# and defaults to whichever one is currently loaded. Keeping the detection in one place means
# the two launchers can never disagree about which model is live.
if ($providerName -eq "lm-studio") {
  $lmsScript = Join-Path $PSScriptRoot "pi-lmstudio.ps1"
  if (-not (Test-Path $lmsScript)) {
    Write-Host "  [ERROR] pi-lmstudio.ps1 not found next to this script." -ForegroundColor Red
    exit 1
  }

  $delegateArgs = @()
  if (-not [string]::IsNullOrEmpty($model)) { $delegateArgs += @('-Model', $model) }
  $delegateArgs += $piArgs

  & $lmsScript @delegateArgs
} else {
  # Non-local providers: verify env var is set, then launch
  $envVar = $selectedProvider.apiKeyVar
  if (-not $envVar -or $envVar -eq "none") {
    # LM Studio handled above
    Write-Host "  [Warning] No API key variable for this provider. Credentials should be in ~/.pi/agent/auth.json" -ForegroundColor Yellow
  } else {
    if (-not (Get-Item -Path "env:$envVar" -ErrorAction SilentlyContinue)) {
      Write-Host "  [ERROR] $envVar not set. Set it via:" -ForegroundColor Red
      Write-Host "    `$env:$envVar = `"your-api-key`"" -ForegroundColor Yellow
      Write-Host "  Or use `/login` in Pi to store credentials in ~/.pi/agent/auth.json" -ForegroundColor Yellow
      exit 1
    }
  }

  # Set PI_OFFLINE to skip the update nag (all providers are remote, no startup network needed beyond the API)
  $env:PI_OFFLINE = "1"

  & pi --provider $providerName --model $modelName @piArgs
}

exit $LASTEXITCODE
