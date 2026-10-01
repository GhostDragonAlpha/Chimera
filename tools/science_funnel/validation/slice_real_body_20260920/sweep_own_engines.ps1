# sweep_own_engines.ps1 -- kill THIS repo's orphaned slice engines only
# (never another worktree's): a hard-killed slice server orphans its engine
# child, and orphaned engines made the next boot's /mesh_import die mid-parse
# (measured, lane slice_real_body_20260920). Param: the engine exe path.
param([string]$ExePath = "")
$ErrorActionPreference = "Continue"
if ($ExePath -eq "") {
    $ExePath = "E:\ChimeraWork\realbody-agent\repo\.tmp\slice_build\Release\chimera_engine.exe"
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
