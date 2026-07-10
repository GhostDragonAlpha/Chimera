#!/usr/bin/env pwsh
# pi-lmstudio.ps1 -- launch the Pi coding agent against LM Studio.
#
# Publishes EVERY chat-capable model LM Studio knows about into Pi's model list, and makes
# whichever one is CURRENTLY LOADED the default. That means:
#   * `pi` starts on the loaded model, always -- no stale hardcoded id.
#   * Pi's in-session `/model` picker lists all the others, and LM Studio JIT-loads
#     whichever you pick.
#
# Runs on Windows PowerShell 5.1 and PowerShell 7+ (no version-specific cmdlet params).
#
# Usage:   .\pi-lmstudio.ps1 [any pi args]      e.g.  .\pi-lmstudio.ps1 -c
#          .\pi-lmstudio.ps1 -List              show what LM Studio is serving, then exit
#          .\pi-lmstudio.ps1 -Model <id>        force a specific model as the default
# Remote LM Studio box: set LMS_URL first, e.g.  $env:LMS_URL = "http://192.168.3.169:1234"

$ErrorActionPreference = 'Stop'

$LmsUrl = if ($env:LMS_URL) { $env:LMS_URL } else { "http://192.168.3.169:1234" }

# Models that are not chat endpoints, regardless of how LM Studio types them: it reports
# TTS and image-edit models as "llm", so `type` alone is not a sufficient filter. Match on
# `arch` (the model architecture) rather than the id -- ids are branding, arch is structural.
$NotChatArch = '(?i)(bert|tts|image|whisper|clip|rerank)'

# Whether Pi may send `reasoning_effort`. Set `reasoning: true` and LM Studio honours it:
# "none" disables thinking, any other value enables it (measured, see PI_LAUNCHER_README).
# This is deliberately NOT inferred from the model id. Thinking is a per-request server-side
# setting, not a property of the weights -- the same model answers with or without a
# reasoning_content block depending on what the request asks for. Marking every chat model
# `reasoning: true` hands the switch to Pi's own /thinking control, which is where you want
# it. Escape hatch:  $env:PI_LMS_REASONING = "0"  (never send reasoning_effort)
$ThinkingLevelMap = [ordered]@{
    off     = 'none'
    minimal = 'low'
    low     = 'low'
    medium  = 'medium'
    high    = 'high'
    xhigh   = 'high'
}

# ─── Parse args: consume ours, forward the rest to pi ───────────────────────────────────
$ForceModel = ""
$ListOnly = $false
$PiArgs = @()
$i = 0
while ($i -lt $args.Count) {
    $a = [string]$args[$i]
    if (($a -eq '-List' -or $a -eq '--list') ) {
        $ListOnly = $true; $i++
    } elseif (($a -eq '-Model' -or $a -eq '--model') -and $i + 1 -lt $args.Count) {
        $ForceModel = [string]$args[$i + 1]; $i += 2
    } else {
        $PiArgs += $a; $i++
    }
}

# ─── JSON helpers that behave the same on 5.1 and 7+ ────────────────────────────────────
# ConvertFrom-Json -AsHashtable does not exist before PowerShell 6, so we work with
# PSCustomObject and set properties defensively.
function Read-JsonObject([string]$Path) {
    if (Test-Path $Path) {
        $raw = Get-Content $Path -Raw
        if ($raw -and $raw.Trim()) {
            try { return ($raw | ConvertFrom-Json) } catch { }
        }
    }
    return [pscustomobject]@{}
}

function Set-Prop($Object, [string]$Name, $Value) {
    if ($Object.PSObject.Properties.Name -contains $Name) { $Object.$Name = $Value }
    else { $Object | Add-Member -NotePropertyName $Name -NotePropertyValue $Value }
}

# Set-Content -Encoding utf8 emits a BOM on 5.1, which some JSON parsers reject.
function Write-JsonFile([string]$Path, $Object) {
    $dir = Split-Path -Parent $Path
    if ($dir -and -not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    $json = $Object | ConvertTo-Json -Depth 10
    [System.IO.File]::WriteAllText($Path, $json, (New-Object System.Text.UTF8Encoding $false))
}

# ─── Ask LM Studio what it is serving ───────────────────────────────────────────────────
try {
    $all = (Invoke-RestMethod "$LmsUrl/api/v0/models" -TimeoutSec 5).data
} catch {
    Write-Host ""
    Write-Host "  [ERROR] Can't reach LM Studio at $LmsUrl" -ForegroundColor Red
    Write-Host "  Start LM Studio's local server (Developer tab), or run: lms server start"
    Write-Host ""
    exit 1
}

$chat = @($all | Where-Object {
    ($_.type -eq 'llm' -or $_.type -eq 'vlm') -and ($_.arch -notmatch $NotChatArch)
})

if ($chat.Count -eq 0) {
    Write-Host ""
    Write-Host "  [ERROR] LM Studio at $LmsUrl is serving no chat-capable models." -ForegroundColor Red
    Write-Host "  Download or load one in the LM Studio UI, then run this again."
    Write-Host ""
    exit 1
}

# Pick the default: an explicit -Model wins, then whatever is loaded, then the first available.
# Falling through to "first available" is deliberate -- LM Studio JIT-loads on the first
# request, so an unloaded model is a valid target, not an error.
$loaded = @($chat | Where-Object { $_.state -eq 'loaded' })

if ($ForceModel) {
    $active = $chat | Where-Object { $_.id -eq $ForceModel } | Select-Object -First 1
    if (-not $active) {
        Write-Host ""
        Write-Host "  [ERROR] '$ForceModel' is not served by LM Studio at $LmsUrl" -ForegroundColor Red
        Write-Host "  Run with -List to see available model ids."
        Write-Host ""
        exit 1
    }
} elseif ($loaded.Count -gt 0) {
    $active = $loaded[0]
} else {
    $active = $chat[0]
}

# ─── Build one Pi model entry per LM Studio model, active one first ─────────────────────
$reasoningOff = ($env:PI_LMS_REASONING -eq '0')

function New-ModelEntry($m, [bool]$IsActive) {
    $ctx = if ($m.loaded_context_length) { $m.loaded_context_length }
           elseif ($m.max_context_length) { $m.max_context_length }
           else { 8192 }

    # Assign, don't return-from-if: PowerShell unrolls a single-element array coming out of
    # an if-statement into a bare scalar, so `@('text')` would serialize as "text" and Pi's
    # schema check rejects it with `input: must be array`.
    $inputTypes = @('text')
    if ($m.type -eq 'vlm') { $inputTypes = @('text', 'image') }

    $tag = if ($IsActive) { 'loaded' } else { $m.state }

    $entry = [ordered]@{
        id            = $m.id
        name          = "$($m.id) [$tag]"
        reasoning     = (-not $reasoningOff)
        input         = [string[]]$inputTypes
        contextWindow = [int]$ctx
        cost          = [ordered]@{ input = 0; output = 0; cacheRead = 0; cacheWrite = 0 }
    }
    if (-not $reasoningOff) { $entry['thinkingLevelMap'] = $ThinkingLevelMap }
    return $entry
}

$entries = @()
$entries += (New-ModelEntry $active $true)
foreach ($m in $chat) {
    if ($m.id -ne $active.id) { $entries += (New-ModelEntry $m $false) }
}

if ($ListOnly) {
    Write-Host ""
    Write-Host "  LM Studio @ $LmsUrl" -ForegroundColor Cyan
    Write-Host ""
    $entries | ForEach-Object {
        $mark = if ($_.id -eq $active.id) { '*' } else { ' ' }
        $vis  = if ($_.input -contains 'image') { 'vision' } else { '      ' }
        "{0} {1,-40} {2,9} ctx  {3}" -f $mark, $_.id, $_.contextWindow, $vis
    }
    Write-Host ""
    Write-Host "  * = default (currently loaded). Others JIT-load when selected via /model." -ForegroundColor DarkGray
    Write-Host "  Thinking is controlled from inside Pi (/thinking), not by LM Studio's toggle." -ForegroundColor DarkGray
    Write-Host ""
    exit 0
}

# ─── Refresh models.json: replace only the "lmstudio" provider, preserve any others ─────
$modelsJsonPath = Join-Path $env:USERPROFILE ".pi\agent\models.json"
$config = Read-JsonObject $modelsJsonPath

$providers = if ($config.PSObject.Properties.Name -contains 'providers' -and $config.providers) {
    $config.providers
} else {
    [pscustomobject]@{}
}

Set-Prop $providers 'lmstudio' ([ordered]@{
    baseUrl = "$LmsUrl/v1"
    api     = "openai-completions"
    apiKey  = "lm-studio"
    models  = @($entries)   # @() so a lone model still serializes as a JSON array
})
Set-Prop $config 'providers' $providers
Write-JsonFile $modelsJsonPath $config

# ─── Point settings.json's default at the active model, preserve every other field ──────
$settingsPath = Join-Path $env:USERPROFILE ".pi\agent\settings.json"
$settings = Read-JsonObject $settingsPath
Set-Prop $settings 'defaultProvider' 'lmstudio'
Set-Prop $settings 'defaultModel' $active.id
Write-JsonFile $settingsPath $settings

# ─── Silence Pi's startup update nags ───────────────────────────────────────────────────
# This setup runs entirely against local LM Studio, so Pi has no reason to phone the npm
# registry on every launch. PI_OFFLINE disables ALL startup network ops: the "New version
# available" banner, the package-update banner, install telemetry, and auto-downloading
# optional helper binaries (fd/ripgrep -- already present, system versions used as
# fallback). Model inference, MCP, extensions, and subagents are NOT affected.
# To re-enable update checks, run:  pi update --all
$env:PI_OFFLINE = "1"

$ctxActive = ($entries[0]).contextWindow
Write-Host ""
Write-Host "  ==================================================" -ForegroundColor Cyan
Write-Host "   Pi  --  LOCAL via LM Studio" -ForegroundColor Cyan
Write-Host "   endpoint : $LmsUrl"
Write-Host "   model    : $($active.id)  ($ctxActive ctx)"
Write-Host "   also available : $($chat.Count - 1) more via /model"
Write-Host "  ==================================================" -ForegroundColor Cyan
Write-Host ""

& pi --provider lmstudio --model $active.id @PiArgs
exit $LASTEXITCODE
