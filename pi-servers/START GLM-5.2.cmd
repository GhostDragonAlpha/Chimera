@echo off
title GLM-5.2 server (colibri, port 8080, CPU - leaves GPU free)
echo Stopping any existing GLM-5.2 server on :8080...
python "E:\colibri\c\coli" stop --port 8080 >nul 2>&1
timeout /t 3 /nobreak >nul

REM ---------------------------------------------------------------------------
REM CPU MODE - THE DEFAULT. Uses 0 VRAM so LM Studio keeps the GPU.
REM Measured 2026-07-23: GPU mode gives 0.289 tok/s vs ~0.26 on CPU - an 11%
REM gain that costs 13-18 GB of VRAM. LM Studio runs 50+ tok/s on that VRAM,
REM so CPU mode for GLM is the correct trade. Use "START GLM-5.2 (GPU).cmd"
REM only when LM Studio is unloaded and you want GLM slightly faster.
REM
REM --queue-timeout 3600 IS LOAD-BEARING: the 300s default kills requests
REM mid-prefill and the client reports "Stream ended without finish_reason".
REM Do not remove it. (Root cause found 2026-07-23.)
REM
REM ctx 32000 (operator, 2026-07-23): the measured ceiling this box handles
REM comfortably, and the right size for how this model is actually used -- a
REM SHORT opinion on a hard call, not a long document. Prior findings still
REM stand: 262144 evicts a third of the 621-expert hot set (387) and measured
REM 42%% slower; 128000 held the full set. Neither matters at 0.26 tok/s if the
REM prompt is short, and a long prompt is what makes this model unusable --
REM 2,900 tokens costs 6-18 min of PREFILL before the first token appears.
REM ---------------------------------------------------------------------------
set "COLI_MODEL=E:\glm52_i4"
set "COLI_MODEL_MIRROR=D:\glm52_i4"
set "COLI_DISK_WEIGHTS=1047,515"
set "COLI_CUDA=0"
set "PIN_GB=all"

echo.
echo Starting GLM-5.2 (colibri) on http://127.0.0.1:8080   [CPU mode - 0 VRAM]
echo KEEP THIS WINDOW OPEN = server is running.  Close it, or run "STOP GLM-5.2.cmd", to stop.
echo.
python "E:\colibri\c\coli" serve --host 127.0.0.1 --port 8080 --model-id glm-5.2-colibri --ctx 32000 --ngen 4096 --gpu none --queue-timeout 3600