$ErrorActionPreference = 'Stop'
$studioIntegration = Split-Path -Parent $PSScriptRoot
$studioRoot = Split-Path -Parent $studioIntegration
$env:CHIMERA_STUDIO_ROOT = $studioIntegration
$env:BLENDER_USER_CONFIG = Join-Path $studioIntegration '.user/config'
$env:BLENDER_USER_SCRIPTS = Join-Path $studioIntegration '.user/scripts'
$forkExe = Join-Path $studioRoot 'build-blender/bin/Release/blender.exe'
$installedExe = 'C:\Program Files\Blender Foundation\Blender 5.0\blender.exe'

$exitMarker = Join-Path $studioRoot 'build-exit.txt'
$buildComplete = (Test-Path -LiteralPath $exitMarker) -and ((Get-Content -LiteralPath $exitMarker -Raw).Trim() -eq '0')
if ($buildComplete -and (Test-Path -LiteralPath $forkExe)) {
    $chosenExe = $forkExe
    $studioArgs = @('--factory-startup', '--app-template', 'ChimeraStudio')
} else {
    $chosenExe = $installedExe
    $env:BLENDER_SYSTEM_SCRIPTS = Join-Path $studioRoot 'blender/scripts'
    $studioArgs = @('--factory-startup','--app-template','ChimeraStudio')
}
if (-not (Test-Path -LiteralPath $chosenExe)) { throw 'Blender executable is missing' }
Start-Process -FilePath $chosenExe -ArgumentList $studioArgs -WorkingDirectory $studioRoot -WindowStyle Normal
