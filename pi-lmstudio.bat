@echo off
REM pi-lmstudio.bat -- double-click or CLI launcher for pi-lmstudio.ps1.
REM Detects whichever model is CURRENTLY LOADED in LM Studio and launches Pi against it.
REM Remote LM Studio box: set LMS_URL first, e.g.  set LMS_URL=http://192.168.3.169:1234
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0pi-lmstudio.ps1" %*
