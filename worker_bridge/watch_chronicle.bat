@echo off
cd /d E:\PythonChimera\worker_bridge
echo Watching chronicle files...
echo New files will appear here as the agents write them.
echo.
:loop
for %%f in (chronicle\*.txt) do (
    if not defined SEEN_%%~nf (
        echo.
        echo ===== %%~nf =====
        type "%%f"
        echo.
        set SEEN_%%~nf=1
    )
)
timeout /t 3 /nobreak >nul
goto loop
