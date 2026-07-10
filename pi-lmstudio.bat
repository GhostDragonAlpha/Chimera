@echo off
REM pi-lmstudio.bat -- double-click or CLI launcher for pi-lmstudio.ps1.
REM Publishes every LM Studio model to Pi and defaults to whichever one is CURRENTLY LOADED.
REM
REM   pi-lmstudio.bat              launch Pi on the loaded model
REM   pi-lmstudio.bat -List        show what LM Studio is serving
REM   pi-lmstudio.bat -Model <id>  force a specific model
REM   pi-lmstudio.bat -c           (any other args are forwarded to pi)
REM
REM Remote LM Studio box: set LMS_URL first, e.g.  set LMS_URL=http://192.168.3.169:1234
REM
REM Prefer PowerShell 7 (pwsh). Windows PowerShell 5.1 works too, but is the fallback.
setlocal
where pwsh >nul 2>&1
if %errorlevel%==0 (
    pwsh -NoProfile -ExecutionPolicy Bypass -File "%~dp0pi-lmstudio.ps1" %*
) else (
    powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0pi-lmstudio.ps1" %*
)
exit /b %errorlevel%
