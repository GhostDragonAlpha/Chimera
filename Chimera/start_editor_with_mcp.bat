@echo off
setlocal enabledelayedexpansion

:: start_editor_with_mcp.bat
:: Opens the Unreal project with MCP enabled, verifies plugin, displays startup log

set PROJECT_PATH=E:\PythonChimera\Chimera\Chimera.uproject
set PLUGIN_NAME=McpAutomationBridge
set LOG_FILE=E:\PythonChimera\Chimera\Saved\Logs\start_editor_mcp.log

echo ============================================
echo  Chimera Editor Startup with MCP Bridge
echo ============================================
echo.

:: Verify project file exists
if not exist "%PROJECT_PATH%" (
    echo [ERROR] Project file not found: %PROJECT_PATH%
    exit /b 1
)
echo [OK] Project file found: %PROJECT_PATH%

:: Verify McpAutomationBridge plugin directory exists
set PLUGIN_DIR=E:\PythonChimera\Chimera\Plugins\McpAutomationBridge
if not exist "%PLUGIN_DIR%" (
    echo [ERROR] Plugin directory not found: %PLUGIN_DIR%
    exit /b 1
)
echo [OK] McpAutomationBridge plugin directory found

:: Verify plugin DLL exists
set PLUGIN_DLL=%PLUGIN_DIR%\Binaries\Win64\UnrealEditor-McpAutomationBridge-Win64-DebugGame.dll
if not exist "%PLUGIN_DLL%" (
    echo [WARN] Plugin DLL not found: %PLUGIN_DLL%
    echo        Plugin may need to be rebuilt in Unreal Editor
) else (
    echo [OK] Plugin DLL found: %PLUGIN_DLL%
)

:: Verify DefaultGame.ini has MCP settings
set GAME_INI=E:\PythonChimera\Chimera\Config\DefaultGame.ini
if not exist "%GAME_INI%" (
    echo [WARN] DefaultGame.ini not found at %GAME_INI%
) else (
    findstr /C:"NativeMCPPort" "%GAME_INI%" >nul 2>&1
    if %errorlevel%==0 (
        echo [OK] Native MCP settings found in DefaultGame.ini
    ) else (
        echo [WARN] NativeMCPPort setting not found in DefaultGame.ini
    )
)

echo.
echo Starting Unreal Editor...
echo Opening: %PROJECT_PATH%
echo.

:: Open the project with Unreal Editor
call "E:\PythonChimera\UnrealEngine\Engine\Binaries\Win64\UnrealEditor.exe" "%PROJECT_PATH%" -log -mcp

if %errorlevel%==0 (
    echo.
    echo [OK] Unreal Editor started successfully
) else (
    echo.
    echo [WARN] Unreal Editor exited with code: %errorlevel%
)

echo.
echo ============================================
echo  Startup Complete
echo ============================================
echo.
pause
