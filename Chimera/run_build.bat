@echo off
REM =============================================================================
REM Chimera Build Pipeline Launcher
REM =============================================================================
REM Batch wrapper for easy build invocation with quick commands.
REM Supports: build, validate, clean, status, plugins
REM =============================================================================

setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "PS_SCRIPT=%SCRIPT_DIR%build_pipeline.ps1"
set "LOG_DIR=E:\PythonChimera\build_logs"

REM Ensure execution policy allows running scripts
powershell -Command "Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force" > nul 2>&1

REM Check if PowerShell script exists
if not exist "%PS_SCRIPT%" (
    echo ERROR: build_pipeline.ps1 not found at %SCRIPT_DIR%
    echo Please ensure the build pipeline files are in place.
    goto :end
)

REM Parse arguments
set "CMD=%~1"

if "%CMD%"=="" (
    call :show_help
    goto :end
)

if /i "%CMD%"=="build" (
    powershell -ExecutionPolicy Bypass -File "%PS_SCRIPT%" -Full
    goto :check_status
)

if /i "%CMD%"=="validate" (
    powershell -ExecutionPolicy Bypass -File "%PS_SCRIPT%" -Validate
    goto :end
)

if /i "%CMD%"=="clean" (
    powershell -ExecutionPolicy Bypass -File "%PS_SCRIPT%" -Clean
    echo Clean complete. Run 'run_build.bat build' to rebuild.
    goto :end
)

if /i "%CMD%"=="status" (
    call :show_status
    goto :end
)

if /i "%CMD%"=="plugins" (
    powershell -ExecutionPolicy Bypass -File "%PS_SCRIPT%" -PluginsOnly
    goto :check_status
)

if /i "%CMD%"=="incremental" (
    powershell -ExecutionPolicy Bypass -File "%PS_SCRIPT%" -Incremental
    goto :check_status
)

if /i "%CMD%"=="help" (
    call :show_help
    goto :end
)

REM Pass remaining arguments to the PowerShell script
powershell -ExecutionPolicy Bypass -File "%PS_SCRIPT%" %*
goto :check_status

:show_help
echo.
echo Chimera Build Pipeline Launcher
echo ===================================
echo.
echo Usage: run_build ^<command^> [options]
echo.
echo Commands:
echo   build          Full rebuild (default)
echo   incremental    Incremental build (detects changes)
echo   plugins        Compile only the plugins
echo   validate       Run post-build validation only
echo   clean          Clean Intermediate, Saved, Binaries directories
echo   status         Show last build status and time
echo   help           Show this help message
echo.
echo Options (passed through to build_pipeline.ps1):
echo   -Target ^<name^>     Build target (default: ChimeraEditor)
echo   -Platform ^<plat^>  Platform (default: Win64)
echo   -Config ^<cfg^>     Configuration (default: Development)
echo.
goto :end

:show_status
if exist "%LOG_DIR%" (
    for /f "delims=" %%f in ('dir /b /o:a "%LOGDIR%\*build.json" 2^>nul') do set "LAST_LOG=%%f"
) else (
    set "LAST_LOG="
)

if defined LAST_LOG (
    echo Last build log: %LOG_DIR%\%LAST_LOG%
    powershell -Command "^
$log = Get-Content '%LOG_DIR%\%LAST_LOG%' -Raw | ConvertFrom-Json; ^
Write-Host 'Status:   ' $log.Status; ^
Write-Host 'Time:     ' $log.Timestamp; ^
Write-Host 'Duration: ' $log.TotalDuration; ^
Write-Host 'Errors:   ' $log.ErrorCount" 2>nul
) else (
    echo No previous build logs found.
)

goto :end

:check_status
if %ERRORLEVEL% equ 0 (
    echo.
    echo Build completed successfully.
) else (
    echo.
    echo Build failed with errors. Check the output above for details.
)

:end
endlocal
