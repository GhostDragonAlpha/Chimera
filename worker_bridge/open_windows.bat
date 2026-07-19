@echo off
start "Bridge" cmd /k "cd /d E:\PythonChimera\worker_bridge && python -m uvicorn main:app --host 127.0.0.1 --port 8895"
timeout /t 3 /nobreak >nul
start "Chronicle" cmd /k "cd /d E:\PythonChimera\worker_bridge && watch_chronicle.bat"
echo Windows launched. Check taskbar.
