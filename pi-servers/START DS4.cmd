@echo off
title DS4 server (DeepSeek-V4, port 8000)
cd /d E:\PythonChimera\Chimera
echo Starting DS4 (DeepSeek-V4) in WSL - loads ~80 GB RAM, ~60s to come online...
python -m core.ds4_brain serve
echo.
echo DS4 endpoint: http://localhost:8000   (runs in the background - use "STOP DS4.cmd" to stop it)
echo Check when ready:  python -m core.ds4_brain status
pause
