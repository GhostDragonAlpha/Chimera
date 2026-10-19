$ErrorActionPreference = 'Stop'
$studio = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$source = Join-Path $studio 'blender'
$build = Join-Path $studio 'build-blender'
& cmake -S $source -B $build -G 'Visual Studio 17 2022' -A x64 -DWITH_CYCLES=OFF -DWITH_OPENIMAGEDENOISE=OFF -DWITH_USD=OFF -DWITH_HYDRA=OFF -DWITH_OPENVDB=OFF -DWITH_MOD_FLUID=OFF -DWITH_NANOVDB=OFF -DWITH_GTESTS=OFF -DWITH_WINDOWS_BUNDLE_CRT=ON
if ($LASTEXITCODE -ne 0) { throw 'Blender configure failed' }
$env:_CL_ = '/MP1'
& cmake --build $build --config Release --target INSTALL --parallel 2 -- /p:CL_MPCount=1 2>&1 | Out-File -LiteralPath (Join-Path $studio 'build.log') -Encoding utf8
$buildCode = $LASTEXITCODE
[IO.File]::WriteAllText((Join-Path $studio 'build-exit.txt'), [string]$buildCode)
if ($buildCode -ne 0) { throw 'Blender build failed; inspect build.log' }
