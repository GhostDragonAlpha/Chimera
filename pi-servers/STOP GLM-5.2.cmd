@echo off
title Stop GLM-5.2 server
REM ---------------------------------------------------------------------------
REM THIS SCRIPT USED TO LIE (fixed 2026-07-23). `coli stop` fails on Windows --
REM it reads /proc, which does not exist here -- and the old script printed
REM "server stopped" regardless. The server kept running, spin-waiting one core
REM at 101%, and had burned 11.9 CPU-HOURS doing nothing before anyone noticed.
REM
REM So: ask coli nicely, then VERIFY, then stop the process for real.
REM ---------------------------------------------------------------------------
python "E:\colibri\c\coli" stop --port 8080 >nul 2>&1
timeout /t 2 /nobreak >nul

powershell -NoProfile -Command ^
  "$p = Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object { $_.CommandLine -like '*coli*serve*' };" ^
  "if ($p) { $p | ForEach-Object { Write-Host ('stopping coli serve pid ' + $_.ProcessId); Stop-Process -Id $_.ProcessId -Force } ; Start-Sleep -Seconds 2 };" ^
  "$q = Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object { $_.CommandLine -like '*coli*serve*' };" ^
  "if ($q) { Write-Host 'STILL RUNNING - stop it manually' } else { Write-Host 'GLM-5.2 (colibri): stopped, port released' }"
echo.
pause
