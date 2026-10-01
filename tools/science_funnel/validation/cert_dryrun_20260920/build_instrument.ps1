# certdry lane: scene regen + OUT-OF-TREE instrument builds A and B (independent configure)
$ErrorActionPreference = "Stop"
Set-Location E:\ChimeraWork\certdry-agent
$out = ".tmp\certdry"
$inst = "tools\science_funnel\validation\snapshot_apis_20260920\instrument"
New-Item -ItemType Directory -Force -Path "$out\runs" | Out-Null

# ---- 1. the scene of record (regenerated; sha must equal the pin f6844ee...)
if (-not (Test-Path "$out\gait-walker\scene.json")) {
  python -m tools.science_funnel.gait_scene --output "$out\gait-walker" 2>&1 | Select-Object -Last 2
  if ($LASTEXITCODE -ne 0) { throw "scene generation failed" }
}
$sceneSha = (Get-FileHash "$out\gait-walker\scene.json" -Algorithm SHA256).Hash.ToLower()
Write-Output ("SCENE " + $sceneSha)
if ($sceneSha -ne "f6844eeae3dc87170a572ccdeedf326a6cac4f73d1448941808bd8b25a8db342") { throw "scene pin mismatch" }

# ---- 2. build A (independent configure)
if (-not (Test-Path "$out\instA\CMakeCache.txt")) {
  cmake -S $inst -B "$out\instA" 2>&1 | Select-Object -Last 3
  if ($LASTEXITCODE -ne 0) { throw "cmake configure A failed" }
}
cmake --build "$out\instA" --config Release --target gait_snap 2>&1 | Select-Object -Last 4
if ($LASTEXITCODE -ne 0) { throw "build A failed" }
$exeA = Convert-Path "$out\instA\Release\gait_snap.exe"
Write-Output ("EXE_A " + (Get-FileHash $exeA -Algorithm SHA256).Hash.ToLower())

# ---- 3. build B: the FRESH RECOMPILE (independent configure tree, byte-irrelevant)
if (-not (Test-Path "$out\instB\CMakeCache.txt")) {
  cmake -S $inst -B "$out\instB" 2>&1 | Select-Object -Last 3
  if ($LASTEXITCODE -ne 0) { throw "cmake configure B failed" }
}
cmake --build "$out\instB" --config Release --target gait_snap 2>&1 | Select-Object -Last 4
if ($LASTEXITCODE -ne 0) { throw "build B failed" }
$exeB = Convert-Path "$out\instB\Release\gait_snap.exe"
Write-Output ("EXE_B " + (Get-FileHash $exeB -Algorithm SHA256).Hash.ToLower())

Write-Output "BUILDS DONE"
