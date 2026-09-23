# run_full_seed.ps1 -- THE ONE-COMMAND FULL-SEED LAUNCH (RUNBOOK Step 2).
# Seed 20260922, the frozen manifest, NO --smoke: 10 iterations x 4096 envs =
# 983,040 decisions, eval every 25,000 decisions on the frozen eval seed set,
# per-iteration + per-eval checkpoints, DLL sha hash-bound into every checkpoint.
#
# Usage (the lead fires this when the qualified build lands):
#   powershell -File run_full_seed.ps1 -Dll <path-to-walker_env_*.dll> [-OutDir <dir>] [-Seed 20260922]
# Without -Dll it binds typeb_gpu\walker_env.dll (whatever is on disk).
param(
    [string]$Dll = "",
    [string]$OutDir = "",
    [int]$Seed = 20260922,
    [float]$QueueWaitS = 2700
)
$ErrorActionPreference = "Stop"
$repo = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..\..\")).Path
$manifest = Join-Path $repo "tools\science_funnel\validation\first_skill_prestage_20260922\run_manifest.json"
if (-not $OutDir) {
    $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $OutDir = Join-Path $PSScriptRoot ("full_seed" + $Seed + "_" + $stamp)
}
Write-Host "[run_full_seed] repo     = $repo"
Write-Host "[run_full_seed] manifest = $manifest"
Write-Host "[run_full_seed] dll      = $(if ($Dll) { $Dll } else { '<default walker_env.dll>' })"
Write-Host "[run_full_seed] out      = $OutDir"
Write-Host "[run_full_seed] seed     = $Seed  (training seeds frozen: 20260922/23/24; this is seed 1 of 3)"
if ($Dll) {
    python -u (Join-Path $repo "tools\train_first_skill.py") `
        --manifest $manifest --seed $Seed --dll $Dll `
        --out $OutDir --queue-wait-s $QueueWaitS
} else {
    python -u (Join-Path $repo "tools\train_first_skill.py") `
        --manifest $manifest --seed $Seed `
        --out $OutDir --queue-wait-s $QueueWaitS
}
exit $LASTEXITCODE
