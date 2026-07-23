@echo off
title GLM-5.2 server (colibri, port 8080, CPU - slow)
echo Stopping any existing GLM-5.2 server on :8080...
python "E:\colibri\c\coli" stop --port 8080 >nul 2>&1
timeout /t 3 /nobreak >nul

REM ---------------------------------------------------------------------------
REM CPU MODE: uses 0 VRAM so it coexists with LM Studio on the GPU.
REM VERY SLOW - measured ~14 s per layer x 78 layers. A single agent turn can
REM take 20-30 minutes. Use the GPU script unless you need the VRAM elsewhere.
REM ---------------------------------------------------------------------------
set "COLI_MODEL=E:\glm52_i4"
set "COLI_CUDA=0"

echo.
echo Starting GLM-5.2 (colibri) on http://127.0.0.1:8080   [CPU mode - SLOW]
echo KEEP THIS WINDOW OPEN = server is running.  Close it, or run "STOP GLM-5.2.cmd", to stop.
echo.
python "E:\colibri\c\coli" serve --host 127.0.0.1 --port 8080 --model-id glm-5.2-colibri --ctx 32768 --ngen 4096 --gpu none --queue-timeout 3600