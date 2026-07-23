@echo off
REM Start sequential agent workflow in background
echo Starting Chimera Automated Sequential Workflow...
echo This will run agents continuously in order: research -> validation -> recombination -> integration -> documentation

REM Start the orchestrator as a detached process
start "Chimera Automation" /B python sequential_orchestrator.py

echo.
echo Workflow started! Check agent_logs/ for real-time updates.
echo Press any key to show status...
pause >nul

REM Show recent log files
if exist agent_logs (
    echo.
    echo Recent activity:
    dir /b /o-d agent_logs\*.log | findstr /N | findstr "1 2 3 4 5"
) else (
    echo No logs yet - workflow may still be initializing...
)
