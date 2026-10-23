[CmdletBinding()]
param([string]$ProjectFile, [switch]$Empty, [switch]$Describe, [switch]$EnableClient)
$ErrorActionPreference = 'Stop'
if ($Empty -and $ProjectFile) { throw 'Choose a project file or an empty workspace, not both.' }
$studioIntegration = Split-Path -Parent $PSScriptRoot
$studioRoot = Split-Path -Parent $studioIntegration
$env:CHIMERA_STUDIO_ROOT = $studioIntegration
$env:BLENDER_USER_CONFIG = Join-Path $studioIntegration '.user/config'
$env:BLENDER_USER_SCRIPTS = Join-Path $studioIntegration '.user/scripts'
New-Item -ItemType Directory -Force -Path $env:BLENDER_USER_CONFIG,$env:BLENDER_USER_SCRIPTS | Out-Null
$forkExe = Join-Path $studioRoot 'build-blender/bin/Release/blender.exe'
$installedExe = 'C:\Program Files\Blender Foundation\Blender 5.0\blender.exe'
$exitMarker = Join-Path $studioRoot 'build-exit.txt'
$buildComplete = (Test-Path -LiteralPath $exitMarker) -and ((Get-Content -LiteralPath $exitMarker -Raw).Trim() -eq '0')
if ($buildComplete -and (Test-Path -LiteralPath $forkExe)) {
    $chosenExe = $forkExe
    Remove-Item Env:BLENDER_SYSTEM_SCRIPTS -ErrorAction SilentlyContinue
} else {
    $chosenExe = $installedExe
    $env:BLENDER_SYSTEM_SCRIPTS = Join-Path $studioRoot 'blender/scripts'
}
if (-not (Test-Path -LiteralPath $chosenExe)) { throw 'Blender executable is missing.' }
$studioArgs = @('--factory-startup', '--app-template', 'ChimeraStudio')
if (-not $Empty) {
    if (-not $ProjectFile) {
        $ProjectFile = Join-Path $studioRoot 'Projects/Membrane Workshop/Chimera Membrane Workshop.blend'
    }
    if (-not (Test-Path -LiteralPath $ProjectFile -PathType Leaf)) {
        throw "Project not found: $ProjectFile. Use -ProjectFile with an existing .blend, or -Empty."
    }
    $ProjectFile = (Resolve-Path -LiteralPath $ProjectFile).Path
    if ([IO.Path]::GetExtension($ProjectFile) -ne '.blend') { throw 'Choose a .blend project.' }
    $studioArgs += $ProjectFile
}
if ($EnableClient) {
    $studioArgs += '--python'
    $studioArgs += (Join-Path $PSScriptRoot 'enable_client.py')
}
if ($Describe) {
    [pscustomobject]@{
        executable=$chosenExe; arguments=$studioArgs; project=$ProjectFile
        workingDirectory=$studioRoot; integration=$studioIntegration; opensOffline=$true
        enableClient=[bool]$EnableClient
    } | ConvertTo-Json -Depth 4
    return
}
# Start-Process joins ArgumentList on Windows; quote paths with spaces.
$commandArguments = ($studioArgs | ForEach-Object { '"' + $_ + '"' }) -join ' '
Start-Process -FilePath $chosenExe -ArgumentList $commandArguments -WorkingDirectory $studioRoot -WindowStyle Normal
