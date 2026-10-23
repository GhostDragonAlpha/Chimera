param([string]$Python='D:/Chimera-Maintenance/Runtime/local-ai/Strata/.venv/Scripts/python.exe')
$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
Push-Location $root
try {
    # bpy-free headless check against the LOCALLY BUILT engine (no repin).
    & $Python tests/test_membrane_forces.py
    if ($LASTEXITCODE -ne 0) { throw 'Membrane forces endpoint checks failed' }
} finally { Pop-Location }
