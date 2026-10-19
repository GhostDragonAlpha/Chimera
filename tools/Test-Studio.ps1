param([string]$Blender, [switch]$Gui)
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
New-Item -ItemType Directory -Force -Path $env:BLENDER_USER_CONFIG,$env:BLENDER_USER_SCRIPTS | Out-Null
& $Blender --background --factory-startup --python-exit-code 7 --python (Join-Path $root 'tests/test_blender.py')
if ($LASTEXITCODE -ne 0) { throw 'Native integration tests failed' }
if ($Blender -eq (Join-Path $studio 'build-blender/bin/Release/blender.exe')) {
    Remove-Item Env:BLENDER_SYSTEM_SCRIPTS -ErrorAction SilentlyContinue
} else { $env:BLENDER_SYSTEM_SCRIPTS = Join-Path $studio 'blender/scripts' }
& $Blender --background --factory-startup --app-template ChimeraStudio --python-exit-code 7 --python (Join-Path $root 'tests/test_template.py')
if ($LASTEXITCODE -ne 0) { throw 'Application template test failed' }

if ($Gui) {
    $guiScript = Join-Path $root 'tests/test_gui.py'
    $run = Start-Process -FilePath $Blender -ArgumentList @('--factory-startup','--app-template','ChimeraStudio','--window-geometry','50','50','1200','850','--python',('"' + $guiScript + '"')) -WorkingDirectory $studio -WindowStyle Normal -PassThru -Wait -RedirectStandardOutput (Join-Path $root 'evidence/gui-stdout.log') -RedirectStandardError (Join-Path $root 'evidence/gui-stderr.log')
    if ($run.ExitCode -ne 0) { throw 'Blender GUI process failed' }
    $report = Get-Content -LiteralPath (Join-Path $root 'evidence/gui-smoke.json') -Raw | ConvertFrom-Json
    if (-not $report.pass) { throw 'Blender GUI checks failed' }
    $report | ConvertTo-Json
}
