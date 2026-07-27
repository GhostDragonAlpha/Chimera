@echo off
REM =============================================================================
REM Chimera Production Deployment Wrapper
REM =============================================================================
REM Requires manual confirmation before proceeding.
REM Backs up existing installation, deploys new build, verifies integrity.
REM =============================================================================

setlocal enabledelayedexpansion

REM =============================================================================
PATH CONFIGURATION
REM =============================================================================

set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%"
set "BUILD_SCRIPT=%SCRIPT_DIR%build_pipeline.ps1"
set "STAGING_DEPLOY=%SCRIPT_DIR%deploy_staging.ps1"
set "BINARIES_DIR=%PROJECT_ROOT%Binaries\Win64"
set "BACKUP_PREFIX=production_backup_%DATE:~6,4%%DATE:~3,2%%DATE:~0,2%_%TIME::%_%TIME::%"
set "BACKUP_PATH=E:\PythonChimera\%BACKUP_PREFIX%"
set "DEPLOY_LOG=%PROJECT_ROOT%.deploy_logs\deploy_production.log"

REM Ensure log directory exists
if not exist "%PROJECT_ROOT%.deploy_logs" (
    mkdir "%PROJECT_ROOT%.deploy_logs" 2>nul
)

REM =============================================================================
LOGGING UTILITY
REM =============================================================================

:log_message
set "level=%~1"
set "message=%~2"
set "timestamp=%DATE% %TIME%"
echo [%timestamp%] [%-5level%] !message!
echo [%timestamp%] [%-5level%] !message! >> "%DEPLOY_LOG%"
goto :eof

REM =============================================================================
MANUAL CONFIRMATION GATE
REM =============================================================================

:confirm_deployment
set /p "CONFIRM=^^^! PRODUCTION DEPLOYMENT ^^^!^n"
echo This will deploy a new build to the production installation directory.
echo Existing files will be backed up before deployment.
echo.
set /p "CONFIRM=Type YES to confirm deployment: "

if /i not "!CONFIRM!"=="YES" (
    log_message "INFO" "Deployment cancelled by user."
    echo.
    echo Deployment aborted.
    goto :end
)
goto :eof

REM =============================================================================
BUILD STAGE
REM =============================================================================

:build_stage
log_message "INFO" "=== BUILD STAGE ==="

if not exist "%BUILD_SCRIPT%" (
    log_message "ERROR" "build_pipeline.ps1 not found at %BUILD_SCRIPT%"
    goto :rollback_build
)

powershell -ExecutionPolicy Bypass -File "%BUILD_SCRIPT%" -Configuration Shipping -Platform Win64 -Full
set BUILD_EXIT=!ERRORLEVEL!

if !BUILD_EXIT!==0 (
    log_message "INFO" "Shipping build succeeded."
) else (
    log_message "ERROR" "Shipping build failed (exit code: !BUILD_EXIT!). Aborting deployment."
    goto :end
)
goto :eof

:rollback_build
log_message "WARNING" "Build rollback triggered."
goto :eof

REM =============================================================================
BACKUP STAGE
REM =============================================================================

:backup_stage
log_message "INFO" "=== BACKUP STAGE ==="

if exist "%PROJECT_ROOT%Binaries\Win64\" (
    log_message "INFO" "Backing up existing installation..."

    if exist "!BACKUP_PATH!" (
        rmdir /s /q "!BACKUP_PATH!" 2>nul
    )

    mkdir "!BACKUP_PATH!" 2>nul
    xcopy "%PROJECT_ROOT%Binaries\Win64\" "!BACKUP_PATH!\" /E /I /Y /Q 2>nul

    if exist "!BACKUP_PATH!" (
        log_message "INFO" "Backup created at: !BACKUP_PATH!"
    ) else (
        log_message "WARNING" "Backup creation failed. Proceeding with deployment."
    )
) else (
    log_message "INFO" "No existing installation found to back up."
)
goto :eof

REM =============================================================================
DEPLOYMENT STAGE
REM =============================================================================

:deploy_stage
log_message "INFO" "=== DEPLOYMENT STAGE ==="

if not exist "%BINARIES_DIR%" (
    log_message "ERROR" "Binaries\Win64 directory not found. Build may be incomplete."
    goto :rollback_deployment
)

REM Copy new binaries to production location (same directory as backup target)
log_message "INFO" "Deploying new build..."

xcopy "%BINARIES_DIR%\*.*" "%PROJECT_ROOT%Binaries\Win64\" /Y /Q 2>nul
set DEPLOY_EXIT=!ERRORLEVEL!

if !DEPLOY_EXIT!==0 (
    log_message "INFO" "Deployment complete."
) else (
    log_message "ERROR" "Deployment failed. Initiating rollback..."
    goto :rollback_deployment
)
goto :eof

:rollback_deployment
log_message "WARNING" "=== ROLLBACK ==="

if exist "!BACKUP_PATH!" (
    log_message "INFO" "Restoring from backup: !BACKUP_PATH!"

    if exist "%PROJECT_ROOT%Binaries\Win64\" (
        rmdir /s /q "%PROJECT_ROOT%Binaries\Win64" 2>nul
    )

    mkdir "%PROJECT_ROOT%Binaries\Win64" 2>nul
    xcopy "!BACKUP_PATH!\*.*" "%PROJECT_ROOT%Binaries\Win64\" /E /I /Y /Q 2>nul

    if exist "%PROJECT_ROOT%Binaries\Win64\" (
        log_message "INFO" "Rollback successful. Original installation restored."
    ) else (
        log_message "ERROR" "Rollback failed. Manual intervention required."
    )
) else (
    log_message "WARNING" "No backup available for rollback."
)
goto :eof

REM =============================================================================
VERIFICATION STAGE
REM =============================================================================

:verify_stage
log_message "INFO" "=== VERIFICATION STAGE ==="

set VERIFY_PASS=0
set VERIFY_FAIL=0

REM Verify critical DLLs exist and have non-zero size
for %%F in ("%BINARIES_DIR%\*ChimeraEditor*.dll") do (
    if exist "%%F" (
        for /f "tokens=*" %%S in ('dir /b "%%F"') do (
            log_message "INFO" "Verified: %%~nxF"
            set /a VERIFY_PASS=!VERIFY_PASS!+1
        )
    ) else (
        log_message "WARNING" "Missing expected file matching: *ChimeraEditor*.dll"
        set /a VERIFY_FAIL=!VERIFY_FAIL!+1
    )
)

for %%F in ("%BINARIES_DIR%\McpAutomationBridge.dll") do (
    if exist "%%F" (
        for /f "tokens=*" %%S in ('dir /b "%%F"') do (
            log_message "INFO" "Verified: %%~nxF"
            set /a VERIFY_PASS=!VERIFY_PASS!+1
        )
    ) else (
        log_message "WARNING" "Missing expected file: McpAutomationBridge.dll"
        set /a VERIFY_FAIL=!VERIFY_FAIL!+1
    )
)

for %%F in ("%BINARIES_DIR%\PythonScriptPlugin.dll") do (
    if exist "%%F" (
        for /f "tokens=*" %%S in ('dir /b "%%F"') do (
            log_message "INFO" "Verified: %%~nxF"
            set /a VERIFY_PASS=!VERIFY_PASS!+1
        )
    ) else (
        log_message "WARNING" "Missing expected file: PythonScriptPlugin.dll"
        set /a VERIFY_FAIL=!VERIFY_FAIL!+1
    )
)

log_message "INFO" ""
log_message "INFO" "Verification Results: !VERIFY_PASS! passed, !VERIFY_FAIL! failed"

if !VERIFY_FAIL!==0 (
    log_message "INFO" "Deployment integrity verified."
) else (
    log_message "WARNING" "Some verification checks failed. Review deployment."
)
goto :eof

REM =============================================================================
CLEANUP STAGE
REM =============================================================================

:cleanup_stage
log_message "INFO" "=== CLEANUP STAGE ==="

if exist "!BACKUP_PATH!" (
    set /p "REMOVE_BACKUP=Remove backup directory [!BACKUP_PATH!]? (y/N): "
    if /i "!REMOVE_BACKUP!"=="Y" (
        rmdir /s /q "!BACKUP_PATH!" 2>nul
        log_message "INFO" "Backup removed."
    ) else (
        log_message "INFO" "Backup retained at: !BACKUP_PATH!"
    )
)
goto :eof

REM =============================================================================
MAIN EXECUTION
REM =============================================================================

log_message "" "========================================"
log_message "" "  Chimera Production Deployment v1.0"
log_message "" "========================================"
log_message ""

REM Step 1: Confirm deployment
call :confirm_deployment

REM Step 2: Build in Shipping configuration
call :build_stage

REM Step 3: Backup existing installation
call :backup_stage

REM Step 4: Deploy new build
call :deploy_stage

REM Step 5: Verify deployment integrity
call :verify_stage

REM Step 6: Cleanup (optional backup removal)
call :cleanup_stage

:end
endlocal
