# Requires g++ from the project's MinGW toolchain.
param()

$root = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..\")).Path
$outDir = Join-Path (Join-Path $root ".tmp") "engine_http_lifecycle"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$exe = Join-Path $outDir "http_server_lifecycle_harness.exe"

Push-Location $PSScriptRoot
Set-Location $root
& g++ -std=c++17 -I . -o "$exe" `
    "docs/evidence/engine_http_lifecycle/http_server_lifecycle_harness.cpp" `
    "ChimeraEngine/engine/http_server.cpp" `
    -lws2_32
$rc=$LASTEXITCODE
if ($rc -ne 0) { throw "compile failed: $rc" }

& "$exe"
$code=$LASTEXITCODE
if ($code -ne 0) { throw "harness failed: $code" }
Pop-Location
