@echo off
REM Double-click this. It starts the Chimera viewer and opens it in your browser.
REM Nothing else needed -- no terminal, no agent, no commands.
title Chimera
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\run_demo.ps1" %*
