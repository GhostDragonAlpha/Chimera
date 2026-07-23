@echo off
title Stop DS4 server
cd /d E:\PythonChimera\Chimera
python -m core.ds4_brain stop
echo.
echo DS4 (DeepSeek-V4) stopped - the ~80 GB frees shortly.
pause
