@echo off
echo Launching Foundry Visible Windows...
echo.

echo [1/2] Starting Bridge Server...
start "Foundry Bridge" cmd /k "cd /d E:\PythonChimera\worker_bridge && python -m uvicorn main:app --host 127.0.0.1 --port 8895"
timeout /t 3 /nobreak >nul

echo [2/2] Starting Live Monitor...
start "Foundry Monitor" powershell -NoExit -Command "cd E:\PythonChimera\worker_bridge; .\monitor.ps1"

echo.
echo Windows launched. Check your taskbar.
echo.
echo To watch agent output directly:
echo   In a new PowerShell window:
echo     Get-Content E:\PythonChimera\worker_bridge\chronicle\turn_001_worker_questions.txt -Wait
echo.
pause
