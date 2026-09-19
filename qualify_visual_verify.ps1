# qualify_visual_verify.ps1 - the lane's QUALIFY gate, three checks:
#   1. funnel suite green      - science_funnel unittest discovery, exit 0
#   2. graphify HONEST         - creature_graph consumer round-trip verdict
#   3. evidence 11             - graph carries exactly 11 evidence-kind objects
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$root = 'E:\ChimeraWork\visual-verify-20260918'
$Python = 'E:\PythonChimera\.venv-hy3d\Scripts\python.exe'
Push-Location $root
try {
    Write-Host '[qualify 1/3] funnel suite'
    & $Python -B -m unittest discover -s tools/science_funnel/tests 2>&1 | Select-Object -Last 3
    if ($LASTEXITCODE -ne 0) { throw "funnel suite NOT green (exit $LASTEXITCODE)" }
    Write-Host '[qualify 1/3] funnel suite GREEN'

    Write-Host '[qualify 2/3] graphify HONEST'
    & $Python -B -m tools.creature_graph.graphify_consumer 2>&1 | Select-Object -Last 4
    if ($LASTEXITCODE -ne 0) { throw "graphify NOT HONEST (exit $LASTEXITCODE)" }
    Write-Host '[qualify 2/3] graphify HONEST'

    Write-Host '[qualify 3/3] evidence 11'
    $count = & $Python -B -c "import sys; sys.path.insert(0, '.'); from tools.creature_graph.store import CreatureGraph; from tools.science_funnel.earth_scene import ROOT; g = CreatureGraph.load(str(ROOT / 'tools/creature_graph/data/creature_graph.json')); print(len(g.by_kind('evidence')))"
    if ($LASTEXITCODE -ne 0) { throw 'evidence count probe failed' }
    if ("$count".Trim() -ne '11') { throw "evidence count is $count, expected 11" }
    Write-Host '[qualify 3/3] evidence 11 OK'
    Write-Host 'QUALIFY: PASS (funnel green, graphify HONEST, evidence 11)'
} finally {
    Pop-Location
}
