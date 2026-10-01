@echo off
REM Double-click this. It starts the playable slice and opens it in your browser.
REM Nothing else needed -- no terminal, no agent, no commands.
title CHIMERA playable slice
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_slice.ps1" %*
