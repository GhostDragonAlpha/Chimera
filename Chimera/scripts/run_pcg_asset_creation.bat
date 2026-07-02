@echo off
setlocal enabledelayedexpansion

set UE_CMD="C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe"
set PROJECT="E:\PythonChimera\Chimera\Chimera.uproject"
set SCRIPT="E:\PythonChimera\Chimera\Scripts\create_pcg_assets.py"
set LOG="E:\PythonChimera\Chimera\Scripts\pcg_creation.log"
set PCG_DIR="E:\PythonChimera\Chimera\Content\ProceduralGenerated\PCG"

echo [%date% %time%] Starting PCG asset creation... > %LOG%
echo. >> %LOG%

%UE_CMD% %PROJECT% -ExecutePythonScript=%SCRIPT% -stdout -unattended -nopause -nosplash -log=%LOG% 2>&1

echo. >> %LOG%
echo [%date% %time%] PCG asset creation finished. >> %LOG%

echo.
echo ========================================
echo Checking for .uasset files...
echo ========================================

if exist %PCG_DIR% (
    dir /s /b %PCG_DIR%\*.uasset 2>nul >nul
    if !errorlevel! equ 0 (
        echo SUCCESS: .uasset files found in %PCG_DIR%
        dir /s /b %PCG_DIR%\*.uasset
    ) else (
        echo WARNING: No .uasset files found in %PCG_DIR%
    )
) else (
    echo WARNING: Directory %PCG_DIR% does not exist
)

echo.
echo Full log output:
echo ========================================
type %LOG%
echo ========================================

endlocal
