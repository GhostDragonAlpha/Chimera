@echo off
setlocal
REM bionic.cmd ^<session-id^> "^<task pointer^>" [requested-model-id]
REM
REM Launch a visible Pi coding agent through the canonical LM Studio launcher.
REM The explicit third argument wins, then BIONIC_MODEL, then the model LM Studio
REM currently reports as loaded.  pi-lmstudio.ps1 publishes every served model and
REM passes the chosen exact id in each OpenAI-compatible request, allowing LM Studio
REM JIT/per-model loading to select the requested weights.
REM
REM Example:
REM   bionic.cmd zcode-01 "Run MONKEY_RUN.md" "kwaipilot_kat-coder-v2.5-dev-mtp"
REM
REM The operator watches/steers the TUI. Session transcripts live under:
REM   %%USERPROFILE%%\.pi\agent\sessions\--E--PythonChimera--\

cd /d "%~dp0"

set "REQUESTED_MODEL=%~3"
if not defined REQUESTED_MODEL if defined BIONIC_MODEL set "REQUESTED_MODEL=%BIONIC_MODEL%"

if defined REQUESTED_MODEL (
    call "%~dp0pi-lmstudio.bat" -Model "%REQUESTED_MODEL%" --session-id "%~1" --tools read,bash,edit,write --append-system-prompt ChimeraEngine/AGENT_PROTOCOL.md "%~2 Work from E:/PythonChimera (all task paths are relative to it). The appended AGENT_PROTOCOL.md is binding - follow THE STANDING RULES and the task's DONE MEANS exactly. Do the work yourself with your tools. Do NOT git commit. When DONE MEANS is fully satisfied, your last message is the final report."
) else (
    call "%~dp0pi-lmstudio.bat" --session-id "%~1" --tools read,bash,edit,write --append-system-prompt ChimeraEngine/AGENT_PROTOCOL.md "%~2 Work from E:/PythonChimera (all task paths are relative to it). The appended AGENT_PROTOCOL.md is binding - follow THE STANDING RULES and the task's DONE MEANS exactly. Do the work yourself with your tools. Do NOT git commit. When DONE MEANS is fully satisfied, your last message is the final report."
)

exit /b %ERRORLEVEL%
