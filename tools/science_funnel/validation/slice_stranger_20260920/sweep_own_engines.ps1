# sweep_own_engines.ps1 -- kill THIS lane worktree's orphaned slice engines
# only (never another worktree's shared desktop): a hard-killed slice server
# orphans its engine child, and a clean lane is the boot bar's own
# precondition (measured, lane slice_real_body_20260920). Same contract as
# the inherited sweep; this copy is bound to THIS worktree's build.
# Param: the engine exe path (must exist in this worktree's .tmp/slice_build).
param([string]$ExePath = "")
$ErrorActionPreference = "Continue"
if ($ExePath -eq "") {
    $ExePath = "E:\ChimeraWork\buffy-stranger-20260920\.tmp\slice_build\Release\chimera_engine.exe"
}
if (-not (Test-Path $ExePath)) {
    Write-Output "sweep: engine not found at $ExePath (nothing to sweep)"
    exit 0
}
$procs = Get-Process chimera_engine -ErrorAction SilentlyContinue |
    Where-Object { $_.Path -eq $ExePath }
foreach ($p in $procs) {
    Write-Output ("sweep: killing orphaned engine pid {0}" -f $p.Id)
    Stop-Process -Id $p.Id -Force
}
Start-Sleep -Milliseconds 800
$left = (Get-Process chimera_engine -ErrorAction SilentlyContinue |
    Where-Object { $_.Path -eq $ExePath }).Count
Write-Output ("sweep: {0} own engines remaining" -f ($left | Out-String).Trim())