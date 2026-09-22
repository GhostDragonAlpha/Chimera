# matrix_run.ps1 -- rebuild both probes, then run the mechanism-split matrix
# (baseline / no-contact / no-power) on both sides with full state dumps.
$ErrorActionPreference = "Stop"
Set-Location -LiteralPath "E:\ChimeraWork\finish-agent\tools\science_funnel\typeb_gpu"
& cmd /c "E:\ChimeraWork\finish-agent\tools\science_funnel\typeb_gpu\build_probes.cmd" 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) { "BUILD FAILED"; exit 1 }
"BUILD OK"

$env:CP_FULL = "1"
$env:HL_FULL = "1"
$scene = "E:\ChimeraWork\finish-agent\.tmp\gait-walker\scene.json"

& cmd /c "cpu_probe.exe $scene walk 45 > cp_base.txt 2>nul"
$env:CP_CFG = "contact_enabled:0"
& cmd /c "cpu_probe.exe $scene walk 45 > cp_nocontact.txt 2>nul"
$env:CP_CFG = "power:0"
& cmd /c "cpu_probe.exe $scene walk 45 > cp_nopower.txt 2>nul"
Remove-Item Env:CP_CFG

$env:HL_NOCONTACT = "1"
& cmd /c "host_loop.exe > hl_nocontact.txt 2>nul"
Remove-Item Env:HL_NOCONTACT
$env:HL_NOPOWER = "1"
& cmd /c "host_loop.exe > hl_nopower.txt 2>nul"
Remove-Item Env:HL_NOPOWER
& cmd /c "host_loop.exe > hl_base.txt 2>nul"
"DONE"
