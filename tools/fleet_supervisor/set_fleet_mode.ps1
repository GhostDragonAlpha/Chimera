# set_fleet_mode.ps1 -- the operator's one-line mode setter (hotkey target).
# Writes E:\ChimeraWork\control\fleet_mode and prints ONE line. No UI, no
# popups, no focus changes. Modes: gaming | fleet | training (default fleet).
param(
    [Parameter(Mandatory = $false)]
    [ValidateSet("gaming", "fleet", "training")]
    [string]$Mode = "fleet"
)
$ErrorActionPreference = "Stop"
$dir = "E:\ChimeraWork\control"
if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir | Out-Null }
Set-Content -Path (Join-Path $dir "fleet_mode") -Value $Mode -NoNewline
Write-Output ("fleet_mode=" + $Mode)
