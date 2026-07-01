@echo off
REM MCP Integration Test Suite — Batch runner for Windows
REM Executes the full test suite via Python

set SCRIPT_DIR=%~dp0
set PYTHON_PATH=%SCRIPT_DIR%Chimera\Python

echo ========================================
echo MCP INTEGRATION TEST SUITE
echo ========================================
echo.

REM Set up Python path
set PYTHONPATH=%PYTHON_PATH%

REM Run the full test suite
echo Running all MCP integration tests...
echo.

python "%PYTHON_PATH%\mcp_integration_test_runner.py" ^
    inspection ^
    actor_control ^
    level_management ^
    --report-path "E:\PythonChimera\test_results.json"

set EXIT_CODE=%ERRORLEVEL%

echo.
echo ========================================
if %EXIT_CODE%==0 (
    echo ALL TESTS PASSED
) else (
    echo SOME TESTS FAILED (exit code: %EXIT_CODE%)
)
echo ========================================
echo.
echo Report saved to E:\PythonChimera\test_results.json
echo.

pause
