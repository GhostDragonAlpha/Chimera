$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
& cmake -S (Join-Path $root 'native') -B (Join-Path $root 'build/native') -G 'Visual Studio 17 2022' -A x64
if ($LASTEXITCODE -ne 0) { throw 'Native configure failed' }
& cmake --build (Join-Path $root 'build/native') --config Release --parallel 2
if ($LASTEXITCODE -ne 0) { throw 'Native build failed' }
