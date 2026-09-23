# run_smoke.ps1 -- the trainer-build lane's smoke launch (F-SMOKE).
# 2 iterations x 512 envs on ONE seed, the runbook's declared smoke shape.
# Queues politely behind any GPU job (the env create retries for --QueueWaitS).
# Usage:  powershell -File run_smoke.ps1 [-QueueWaitS 2700] [-Seed 20260922]
param(
    [float]$QueueWaitS = 2700,
    [int]$Seed = 20260922
)
$ErrorActionPreference = "Stop"
$repo = Resolve-Path (Join-Path $PSScriptRoot ".." | Join-Path -ChildPath ".." |
    Join-Path -ChildPath ".." | Join-Path -ChildPath "..")
$manifest = Join-Path $repo "tools\science_funnel\validation\first_skill_prestage_20260922\run_manifest.json"
$out = Join-Path $PSScriptRoot ("smoke_seed" + $Seed)
Write-Host "[run_smoke] repo=$repo"
Write-Host "[run_smoke] manifest=$manifest"
Write-Host "[run_smoke] out=$out"
python -u (Join-Path $repo "tools\train_first_skill.py") `
    --manifest $manifest --smoke --seed $Seed `
    --out $out --queue-wait-s $QueueWaitS
exit $LASTEXITCODE
