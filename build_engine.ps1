# build_engine.ps1 - one-shot build of the coupled native engine for this lane.
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$root = 'E:\ChimeraWork\visual-verify-20260918'
Push-Location $root
try {
    & cmake -S ChimeraEngine/engine -B .tmp/coupled-native-engine
    if ($LASTEXITCODE -ne 0) { throw 'cmake configure failed' }
    & cmake --build .tmp/coupled-native-engine --config Release --parallel 6
    if ($LASTEXITCODE -ne 0) { throw 'cmake build failed' }
    $exe = Join-Path $root '.tmp\coupled-native-engine\Release\chimera_engine.exe'
    if (-not (Test-Path -LiteralPath $exe)) { throw "executable missing: $exe" }
    Write-Host "[build] OK $exe"
    Write-Host ("[build] exe sha256 " + (Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash)
} finally {
    Pop-Location
}
