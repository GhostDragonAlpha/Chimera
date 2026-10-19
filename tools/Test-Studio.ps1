param([string]$Blender)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$studio = Split-Path -Parent $root
if (-not $Blender) {
    $Blender = Join-Path $studio 'build-blender/bin/Release/blender.exe'
    if (-not (Test-Path -LiteralPath $Blender)) { $Blender = 'C:\Program Files\Blender Foundation\Blender 5.0\blender.exe' }
}
$env:CHIMERA_STUDIO_ROOT = $root
$env:BLENDER_USER_CONFIG = Join-Path $root '.user/test-config'
$env:BLENDER_USER_SCRIPTS = Join-Path $root '.user/test-scripts'
& $Blender --background --factory-startup --python-exit-code 7 --python (Join-Path $root 'tests/test_blender.py')
if ($LASTEXITCODE -ne 0) { throw 'Native integration tests failed' }
$env:BLENDER_SYSTEM_SCRIPTS = Join-Path $studio 'blender/scripts'
& $Blender --background --factory-startup --app-template ChimeraStudio --python-exit-code 7 --python (Join-Path $root 'tests/test_template.py')
if ($LASTEXITCODE -ne 0) { throw 'Application template test failed' }
