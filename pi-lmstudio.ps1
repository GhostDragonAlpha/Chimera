#!/usr/bin/env pwsh
# pi-lmstudio.ps1 -- launch the Pi coding agent against whatever model is CURRENTLY LOADED in LM Studio.
#
# Re-detects the active model on every run and rewrites Pi's config (~/.pi/agent/models.json,
# ~/.pi/agent/settings.json) to match. Never trusts a stale hardcoded model id -- LM Studio can
# report the same weights under different ids depending on how they were loaded (full GGUF path
# vs. short alias), and the loaded model can change between runs.
#
# Usage:   .\pi-lmstudio.ps1 [any pi args]
#          e.g. .\pi-lmstudio.ps1 -c        (continue last session)
# Remote LM Studio box: set LMS_URL before running, e.g.
#          $env:LMS_URL = "http://192.168.3.169:1234"

$ErrorActionPreference = 'Stop'
$PiArgs = $args

$LmsUrl = if ($env:LMS_URL) { $env:LMS_URL } else { "http://192.168.3.169:1234" }

try {
    $models = (Invoke-RestMethod "$LmsUrl/api/v0/models" -TimeoutSec 5).data
} catch {
    Write-Host ""
    Write-Host "  [ERROR] Can't reach LM Studio at $LmsUrl" -ForegroundColor Red
    Write-Host "  Start LM Studio's local server (Developer tab), or run: lms server start"
    Write-Host ""
    exit 1
}

$active = $models | Where-Object { $_.state -eq 'loaded' -and ($_.type -eq 'llm' -or $_.type -eq 'vlm') } | Select-Object -First 1

if (-not $active) {
    Write-Host ""
    Write-Host "  [ERROR] No LLM/VLM is loaded in LM Studio at $LmsUrl" -ForegroundColor Red
    Write-Host "  Load a model in the LM Studio UI (or: lms load <model>), then run this again."
    Write-Host ""
    exit 1
}

$contextWindow = if ($active.loaded_context_length) { $active.loaded_context_length } elseif ($active.max_context_length) { $active.max_context_length } else { 8192 }
$inputTypes = if ($active.type -eq 'vlm') { @('text', 'image') } else { @('text') }

# -- refresh models.json: replace only the "lmstudio" provider, preserve any others ----------------
$modelsJsonPath = "$env:USERPROFILE\.pi\agent\models.json"
$config = if (Test-Path $modelsJsonPath) {
    Get-Content $modelsJsonPath -Raw | ConvertFrom-Json -AsHashtable
} else {
    @{ providers = @{} }
}
if (-not $config.ContainsKey('providers')) { $config['providers'] = @{} }

$config['providers']['lmstudio'] = [ordered]@{
    baseUrl = "$LmsUrl/v1"
    api     = "openai-completions"
    apiKey  = "lm-studio"
    models  = @(
        [ordered]@{
            id            = $active.id
            name          = "$($active.id) (LM Studio, live)"
            reasoning     = $false
            input         = $inputTypes
            contextWindow = $contextWindow
            cost          = [ordered]@{ input = 0; output = 0; cacheRead = 0; cacheWrite = 0 }
        }
    )
}
$config | ConvertTo-Json -Depth 10 | Set-Content -Path $modelsJsonPath -Encoding utf8

# -- point settings.json's default at the active model, preserve every other field -----------------
$settingsPath = "$env:USERPROFILE\.pi\agent\settings.json"
$settings = if (Test-Path $settingsPath) { Get-Content $settingsPath -Raw | ConvertFrom-Json -AsHashtable } else { @{} }
$settings['defaultProvider'] = 'lmstudio'
$settings['defaultModel'] = $active.id
$settings | ConvertTo-Json -Depth 10 | Set-Content -Path $settingsPath -Encoding utf8

Write-Host ""
Write-Host "  ==================================================" -ForegroundColor Cyan
Write-Host "   Pi  --  LOCAL via LM Studio" -ForegroundColor Cyan
Write-Host "   endpoint : $LmsUrl"
Write-Host "   model    : $($active.id)"
Write-Host "  ==================================================" -ForegroundColor Cyan
Write-Host ""

& pi --provider lmstudio --model $active.id @PiArgs
exit $LASTEXITCODE
