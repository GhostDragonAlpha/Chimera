$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$entry = Join-Path $root 'Start Chimera Studio.cmd'
$body = '@echo off' + "`r`n" + 'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0integration\launch\Start-ChimeraStudio.ps1"' + "`r`n"
[IO.File]::WriteAllText($entry, $body)
Write-Output $entry
