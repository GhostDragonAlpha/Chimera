$ErrorActionPreference = 'Stop'
$integration = Split-Path -Parent $PSScriptRoot
$root = Split-Path -Parent $integration
$projectDir = Join-Path $root 'Projects/Membrane Workshop'
New-Item -ItemType Directory -Force -Path $projectDir | Out-Null
$project = Join-Path $projectDir 'Chimera Membrane Workshop.blend'
$trial = Join-Path $projectDir 'Starter membrane construction.matter.json'
$created = -not (Test-Path -LiteralPath $project)
if ($created) {
    Copy-Item -LiteralPath (Join-Path $integration 'evidence/membrane-assembly.blend') -Destination $project
}
if (-not (Test-Path -LiteralPath $trial)) {
    Copy-Item -LiteralPath (Join-Path $integration 'evidence/membrane-assembly.matter.json') -Destination $trial
}
$entry = Join-Path $root 'Start Chimera Studio.cmd'
$body = '@echo off' + [Environment]::NewLine + 'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0integration\launch\Start-ChimeraStudio.ps1" %*' + [Environment]::NewLine
[IO.File]::WriteAllText($entry, $body)
$desktop = [Environment]::GetFolderPath('DesktopDirectory')
if (-not $desktop) { throw 'Windows did not return the desktop directory.' }
$shortcutPath = Join-Path $desktop 'Chimera Blender.lnk'
$launcher = Join-Path $integration 'launch/Start-ChimeraStudio.ps1'
$shell = New-Object -ComObject WScript.Shell
if (Test-Path -LiteralPath $shortcutPath) {
    $existing = $shell.CreateShortcut($shortcutPath)
    if ($existing.Arguments -notlike "*$launcher*") { throw 'An unrelated shortcut already uses Chimera Blender.lnk; refusing overwrite.' }
}
$link = $shell.CreateShortcut($shortcutPath)
$link.TargetPath = Join-Path $env:SystemRoot 'System32/WindowsPowerShell/v1.0/powershell.exe'
$link.Arguments = '-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File "' + $launcher + '"'
$link.WorkingDirectory = $root
$link.Description = 'Open the Chimera membrane project in Blender; GPU simulation starts only when requested.'
$icon = Join-Path $root 'build-blender/bin/Release/blender.exe'
if (Test-Path -LiteralPath $icon) { $link.IconLocation = $icon + ',0' }
$link.Save()
[pscustomobject]@{shortcut=$shortcutPath;launcher=$entry;project=$project;createdProject=$created;preservedExistingProject=(-not $created)} | ConvertTo-Json
