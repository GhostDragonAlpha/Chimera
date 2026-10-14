<#
    Run the LESSON ONE walkthrough x N (default 3): one-command boot check,
    sweep own leftovers, start the lesson server, wait for answers, run the
    scripted stranger, collect the artifacts. Never touches other lanes.
#>
param([int]$Runs = 3)

$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)))
$Lane = Join-Path $PSScriptRoot ""
$Stamp = Get-Date -Format "HHmmss"

function Say($msg, $col = "Gray") { Write-Host "  $msg" -ForegroundColor $col }

Write-Host ""
Write-Host "  LESSON ONE walkthrough x $Runs" -ForegroundColor Cyan

# 0. sweep our own leftovers (own worktree path only, own names only)
$sweep = Join-Path $Lane "sweep_own_engines.ps1"
if (Test-Path $sweep) { powershell -NoProfile -ExecutionPolicy Bypass -File $sweep }

# 1. the one-command boot (F-ONE-COMMAND is itself measured here)
$tBoot = Get-Date
& (Join-Path $Root "tools\lesson_shell\run_lesson.ps1") -Port 8912
$rc = $LASTEXITCODE
if ($rc -ne 0) { Say "boot FAILED (exit $rc)" "Red"; exit 1 }
$bootS = ((Get-Date) - $tBoot).TotalSeconds
Say ("boot-to-answers: {0:N1} s" -f $bootS) "Green"

# 2. the walkthrough runs
$artifacts = @()
for ($i = 1; $i -le $Runs; $i++) {
    $out = Join-Path $Lane ("lesson_walk_{0}_{1}.json" -f $Stamp, $i)
    Say "run $i -> $out" "Cyan"
    node (Join-Path $Lane "walkthrough.js") "http://127.0.0.1:8912" $out 2>&1 |
        Tee-Object -Variable runOut | Out-Null
    $tail = ($runOut | Select-Object -Last 3) -join " | "
    Say "  run ${i}: $tail"
    if (Test-Path $out) { $artifacts += $out }
}

# 3. stop OUR lesson server (own process only)
$conn = Get-NetTCPConnection -LocalPort 8912 -State Listen -ErrorAction SilentlyContinue
if ($conn) {
    foreach ($c in $conn) {
        $procId = $c.OwningProcess
        $cl = (Get-CimInstance Win32_Process -Filter "ProcessId=$procId").CommandLine
        if ($cl -and $cl -like "*lesson_server.py*") {
            Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
            Say "lesson server stopped (pid $procId)"
        }
    }
}
& $sweep
Say "artifacts: $($artifacts.Count)/$Runs" "Green"
