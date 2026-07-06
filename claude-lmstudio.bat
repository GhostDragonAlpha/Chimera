@echo off
title Claude Code + LM Studio
setlocal

REM ================================================================
REM  claude-lmstudio.bat  --  run Claude Code against LM Studio
REM
REM  Auto-detects whatever model is CURRENTLY LOADED in LM Studio
REM  and routes Claude Code at it (Anthropic-compatible endpoint).
REM  All overrides live only inside this window: normal `claude`
REM  elsewhere still uses the real Anthropic API.
REM
REM  Usage:  claude-lmstudio.bat [any claude args]
REM          e.g.  claude-lmstudio.bat -c        (continue last convo)
REM  Remote LM Studio box: set LMS_URL before running, e.g.
REM          set LMS_URL=http://192.168.3.169:1234
REM ================================================================

if not defined LMS_URL set "LMS_URL=http://localhost:1234"

REM -- ask LM Studio which LLM/VLM is currently loaded --------------
set "LMS_MODEL="
for /f "usebackq delims=" %%m in (`powershell -NoProfile -ExecutionPolicy Bypass -Command "try { $r = Invoke-RestMethod '%LMS_URL%/api/v0/models' -TimeoutSec 5; $m=''; foreach ($x in $r.data) { if (-not $m -and $x.state -eq 'loaded' -and ($x.type -eq 'llm' -or $x.type -eq 'vlm')) { $m = $x.id } }; $m } catch { '' }"`) do set "LMS_MODEL=%%m"

if not defined LMS_MODEL goto :no_model

echo.
echo  ==================================================
echo   Claude Code  --  LOCAL via LM Studio
echo   endpoint : %LMS_URL%
echo   model    : %LMS_MODEL%
echo  ==================================================
echo.

REM -- route Claude Code at LM Studio (this window only) ------------
set "ANTHROPIC_BASE_URL=%LMS_URL%"
set "ANTHROPIC_AUTH_TOKEN=lmstudio"
set "ANTHROPIC_MODEL=%LMS_MODEL%"
set "ANTHROPIC_DEFAULT_OPUS_MODEL=%LMS_MODEL%"
set "ANTHROPIC_DEFAULT_SONNET_MODEL=%LMS_MODEL%"
set "ANTHROPIC_DEFAULT_HAIKU_MODEL=%LMS_MODEL%"
set "ANTHROPIC_SMALL_FAST_MODEL=%LMS_MODEL%"
set "CLAUDE_CODE_SUBAGENT_MODEL=%LMS_MODEL%"
set "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1"
set "API_TIMEOUT_MS=600000"

call claude %*
exit /b %ERRORLEVEL%

:no_model
echo.
echo  [ERROR] No model is loaded in LM Studio ^(or the server at %LMS_URL% is not running^).
echo.
echo     1. Open LM Studio and start the local server ^(Developer tab^), or run:  lms server start
echo     2. Load a model in the LM Studio UI ^(or:  lms load^)
echo     3. Run this batch file again.
echo.
pause
exit /b 1
