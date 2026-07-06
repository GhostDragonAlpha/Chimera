@echo off
title Claude Code + LM Studio
setlocal enabledelayedexpansion

:: ============================================================
:: Claude Code + LM Studio Launcher
:: ============================================================
:: Usage:
::   claude-lmstudio              - Opens in current directory
::   claude-lmstudio E:\Project   - Opens in specified directory
::   claude-lmstudio . E:\Project - Uses default URL in specified dir
::   claude-lmstudio http://localhost:1234/v1 E:\Project
:: ============================================================

set "LM_URL=http://192.168.3.169:1234/v1"
set "LM_KEY=lm-studio"
set "TARGET_DIR=%CD%"

:: Parse arguments
if not "%1"=="" (
    echo "%~1" | findstr /i "http" >nul
    if !errorlevel! equ 0 (
        set "LM_URL=%~1"
        if not "%2"=="" set "TARGET_DIR=%~2"
    ) else (
        set "TARGET_DIR=%~1"
    )
)
if not "%2"=="" (
    echo "%~2" | findstr /i "http" >nul
    if !errorlevel! equ 0 set "LM_URL=%~2"
)

:: Resolve directory
if not exist "%TARGET_DIR%" (
    echo [ERROR] Directory not found: %TARGET_DIR%
    exit /b 1
)

:: Resolve to full path
for %%i in ("%TARGET_DIR%") do set "TARGET_DIR=%%~fi"

echo =============================================
echo   Claude Code + LM Studio
echo =============================================
echo   Endpoint : %LM_URL%
echo   Directory: %TARGET_DIR%
echo =============================================
echo.

:: Kill any stale Claude daemon so it picks up fresh settings
echo Killing stale Claude processes...
taskkill /F /IM claude.exe >nul 2>&1
timeout /t 1 /nobreak >nul

:: Set LM Studio as the backend
set "ANTHROPIC_BASE_URL=%LM_URL%"
set "ANTHROPIC_API_KEY=%LM_KEY%"

:: Launch Claude Code
echo Launching Claude Code...
cd /d "%TARGET_DIR%"
claude
