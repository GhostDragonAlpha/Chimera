<#
.SYNOPSIS
    Point Claude Code at Moonshot's Kimi instead of Anthropic, and back again.

.DESCRIPTION
    Moonshot serves an ANTHROPIC-COMPATIBLE endpoint (verified live: api.moonshot.ai/anthropic
    answers 401 without a key, which is what "it exists" looks like). So Claude Code needs no shim
    and no patch -- three environment variables and it is talking to Kimi.

    THIS SCRIPT NEVER TOUCHES YOUR KEY. It reads $env:MOONSHOT_API_KEY (or OPENROUTER_API_KEY) if
    you have already set it, and passes it straight through. It does not print it, store it, or
    write it to disk. You set it once, yourself:

        [Environment]::SetEnvironmentVariable('MOONSHOT_API_KEY','sk-...','User')

    ...and then open a new terminal.

.EXAMPLE
    .\kimi.ps1 k3            # Kimi K3, 1M context   -- $3.00 / $15.00 per Mtok
    .\kimi.ps1 code          # Kimi K2.7-Code, 262k  -- $0.73 / $3.50  (4x cheaper, built for this)
    .\kimi.ps1 thinking      # Kimi K2-Thinking      -- $0.60 / $2.50
    .\kimi.ps1 openrouter k3 # same models via OpenRouter instead of Moonshot direct
    .\kimi.ps1 off           # back to Anthropic
#>
param(
    [Parameter(Position = 0)][string]$Mode = "status",
    [Parameter(Position = 1)][string]$Which = "code"
)

$ErrorActionPreference = "Stop"

# Prices are per million tokens, read off OpenRouter's public model list on 2026-07-29.
$MODELS = @{
    "k3"       = @{ id = "kimi-k3";            or = "moonshotai/kimi-k3";            ctx = "1M";   inp = 3.00; outp = 15.00 }
    "code"     = @{ id = "kimi-k2.7-code";     or = "moonshotai/kimi-k2.7-code";     ctx = "262k"; inp = 0.73; outp = 3.50 }
    "thinking" = @{ id = "kimi-k2-thinking";   or = "moonshotai/kimi-k2-thinking";   ctx = "262k"; inp = 0.60; outp = 2.50 }
    "k2.6"     = @{ id = "kimi-k2.6";          or = "moonshotai/kimi-k2.6";          ctx = "262k"; inp = 0.65; outp = 2.72 }
}

function Show-Status {
    $b = $env:ANTHROPIC_BASE_URL
    if ([string]::IsNullOrWhiteSpace($b)) {
        Write-Host "claude is pointed at ANTHROPIC (default)" -ForegroundColor Cyan
    } else {
        Write-Host "claude is pointed at $b" -ForegroundColor Yellow
        Write-Host "  model: $($env:ANTHROPIC_MODEL)"
    }
    Write-Host ""
    Write-Host "keys visible to this shell:" -ForegroundColor DarkGray
    foreach ($k in @("MOONSHOT_API_KEY", "OPENROUTER_API_KEY", "ANTHROPIC_AUTH_TOKEN")) {
        $v = [Environment]::GetEnvironmentVariable($k)
        # length only -- the value is never printed
        $state = if ([string]::IsNullOrWhiteSpace($v)) { "not set" } else { "set ($($v.Length) chars)" }
        Write-Host ("  {0,-22} {1}" -f $k, $state) -ForegroundColor DarkGray
    }
    Write-Host ""
    Write-Host "models:" -ForegroundColor DarkGray
    foreach ($k in $MODELS.Keys | Sort-Object) {
        $m = $MODELS[$k]
        Write-Host ("  {0,-10} {1,-18} {2,5} ctx    `${3,5:N2} in  `${4,6:N2} out  per Mtok" -f $k, $m.id, $m.ctx, $m.inp, $m.outp) -ForegroundColor DarkGray
    }
}

switch ($Mode.ToLower()) {

    "off" {
        Remove-Item Env:ANTHROPIC_BASE_URL   -ErrorAction SilentlyContinue
        Remove-Item Env:ANTHROPIC_AUTH_TOKEN -ErrorAction SilentlyContinue
        Remove-Item Env:ANTHROPIC_MODEL      -ErrorAction SilentlyContinue
        Remove-Item Env:ANTHROPIC_SMALL_FAST_MODEL -ErrorAction SilentlyContinue
        Write-Host "back on Anthropic. (this shell only -- a new terminal is already clean)" -ForegroundColor Cyan
    }

    "openrouter" {
        $key = $env:OPENROUTER_API_KEY
        if ([string]::IsNullOrWhiteSpace($key)) {
            Write-Host "OPENROUTER_API_KEY is not set. Set it yourself, then reopen the terminal:" -ForegroundColor Red
            Write-Host "  [Environment]::SetEnvironmentVariable('OPENROUTER_API_KEY','sk-or-...','User')"
            exit 1
        }
        if (-not $MODELS.ContainsKey($Which)) { Write-Host "unknown model '$Which'"; exit 1 }
        $m = $MODELS[$Which]
        # OpenRouter speaks OpenAI, not Anthropic -- so this path needs a translating proxy.
        # Moonshot direct does NOT. Told plainly rather than pretending it drops straight in.
        Write-Host "OpenRouter serves $($m.or), but its API is OpenAI-shaped." -ForegroundColor Yellow
        Write-Host "Claude Code speaks Anthropic, so this route needs a translator in between"
        Write-Host "(claude-code-router / litellm). Moonshot direct needs nothing -- use:"
        Write-Host "  .\kimi.ps1 $Which" -ForegroundColor Cyan
    }

    "status" { Show-Status }

    default {
        $Which = $Mode
        if (-not $MODELS.ContainsKey($Which)) {
            Write-Host "unknown mode/model '$Mode'" -ForegroundColor Red
            Show-Status
            exit 1
        }
        $key = $env:MOONSHOT_API_KEY
        if ([string]::IsNullOrWhiteSpace($key)) {
            Write-Host "MOONSHOT_API_KEY is not set." -ForegroundColor Red
            Write-Host ""
            Write-Host "Get one at platform.moonshot.ai, then set it yourself (I don't handle keys):"
            Write-Host "  [Environment]::SetEnvironmentVariable('MOONSHOT_API_KEY','sk-...','User')" -ForegroundColor Cyan
            Write-Host "then open a new terminal and run this again."
            exit 1
        }
        $m = $MODELS[$Which]
        $env:ANTHROPIC_BASE_URL   = "https://api.moonshot.ai/anthropic"
        $env:ANTHROPIC_AUTH_TOKEN = $key
        $env:ANTHROPIC_MODEL      = $m.id
        $env:ANTHROPIC_SMALL_FAST_MODEL = $MODELS["code"].id     # cheap model for the small calls
        Write-Host "claude -> $($m.id)  ($($m.ctx) context, `$$($m.inp) in / `$$($m.outp) out per Mtok)" -ForegroundColor Green
        Write-Host "set for THIS shell only. run 'claude' now; '.\kimi.ps1 off' to go back."
    }
}
