param([string]$Python='D:/Chimera-Maintenance/Runtime/local-ai/Strata/.venv/Scripts/python.exe', [switch]$SkipPin)
$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
Push-Location $root
try {
    cmake -S native/gpu_engine/engine -B build/gpu-engine -G 'Visual Studio 17 2022' -A x64
    if($LASTEXITCODE -ne 0) { throw 'GPU engine configure failed' }
    cmake --build build/gpu-engine --config Release --parallel 2
    if($LASTEXITCODE -ne 0) { throw 'GPU engine build failed' }
    if (-not $SkipPin) {
        & $Python tools/pin_gpu_runtime.py
        if($LASTEXITCODE -ne 0) { throw 'GPU engine pin failed' }
    } else {
        Write-Warning 'PIN SKIPPED: runtime/gpu and GPU_SOURCE_LOCK.json unchanged; Blender keeps using the pinned runtime.'
    }
} finally { Pop-Location }
