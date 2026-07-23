@echo off
title GLM-5.2 server (colibri, port 8080, GPU - needs LM Studio unloaded)
echo Stopping any existing GLM-5.2 server on :8080...
python "E:\colibri\c\coli" stop --port 8080 >nul 2>&1
timeout /t 3 /nobreak >nul

REM ---------------------------------------------------------------------------
REM GPU MODE - only worth it when LM Studio is unloaded. Measured 2026-07-23:
REM 0.289 tok/s vs ~0.26 on CPU, at a cost of 13-18 GB VRAM. Prefill is much
REM faster (4.50 s/layer vs 14.0) but decode barely moves - and decode is what
REM you wait on. All settings below were measured, not guessed.
REM ---------------------------------------------------------------------------
set "COLI_MODEL=E:\glm52_i4"
set "COLI_MODEL_MIRROR=D:\glm52_i4"
set "COLI_DISK_WEIGHTS=1047,515"
set "COLI_CUDA=1"
set "CUDA_DENSE=1"
set "CUDA_EXPERT_GB=13"
set "COLI_CUDA_PIPE=2"
set "PIN_GB=all"

echo.
echo Starting GLM-5.2 (colibri) on http://127.0.0.1:8080   [GPU mode]
echo KEEP THIS WINDOW OPEN = server is running.
echo.
python "E:\colibri\c\coli" serve --host 127.0.0.1 --port 8080 --model-id glm-5.2-colibri --ctx 128000 --ngen 4096 --queue-timeout 3600 --vram 13