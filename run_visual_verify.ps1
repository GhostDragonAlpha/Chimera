# run_visual_verify.ps1 - own the engine lifecycle for the visual-verify lane.
# Port 8191 is OWNED by this lane. Port 8127 belongs to the operator: this
# script never binds it, never stops anything on it, and refuses to run if
# our own launch would collide with any existing listener on 8191.
param(
    [switch]$SkipBuild,
    [string]$Python = "E:\PythonChimera\.venv-hy3d\Scripts\python.exe"
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$root = 'E:\ChimeraWork\visual-verify-20260918'
$port = 8191
$outDir = Join-Path $root 'tools\science_funnel\validation\visual_scene_20260918'

if (-not (Test-Path $Python)) { throw "python missing: $Python" }

$listener = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
if ($listener) { throw "port $port already has a listener (OwningProcess $($listener.OwningProcess)); this lane never stops foreign processes." }
$operatorListener = Get-NetTCPConnection -LocalPort 8127 -State Listen -ErrorAction SilentlyContinue
if ($operatorListener) { Write-Host "[guard] operator listener on 8127 detected (pid $($operatorListener.OwningProcess)) - will not be touched." }

Push-Location $root
try {
    if (-not $SkipBuild) {
        Write-Host '[build] cmake configure'
        & cmake -S ChimeraEngine/engine -B .tmp/coupled-native-engine
        if ($LASTEXITCODE -ne 0) { throw "cmake configure failed" }
        Write-Host '[build] cmake build'
        & cmake --build .tmp/coupled-native-engine --config Release --parallel 6
        if ($LASTEXITCODE -ne 0) { throw "cmake build failed" }
    } else {
        Write-Host '[build] skipped (-SkipBuild)'
    }

    Write-Host "[launch] coupled scene on owned port $port"
    # The outer script owns building; the inner launcher always skips its build.
    # IMPORTANT: no output capture and no pipeline on this call. run_earth.ps1
    # Start-Processes the engine, which inherits the launcher's stdout pipe
    # handle; capturing (& $out = & powershell ...) would wait for pipe EOF
    # that only the engine can release, hanging this script forever. A plain
    # invocation waits on PROCESS EXIT only.
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $root 'tools\science_funnel\run_earth.ps1') -CoupledArm -Port $port -Python $Python -SkipBuild
    if ($LASTEXITCODE -ne 0) { throw "run_earth.ps1 failed" }

    $runtimePath = Join-Path $root '.tmp\coupled-native\runtime.json'
    if (-not (Test-Path $runtimePath)) { throw "runtime.json missing after launch" }
    $runtime = Get-Content -LiteralPath $runtimePath -Raw | ConvertFrom-Json
    $enginePid = [int]$runtime.pid
    Write-Host "[launch] engine pid $enginePid exe $($runtime.exe)"

    # path guard BEFORE any stop: the pid must be this worktree's chimera_engine.
    function Stop-OwnedEngine {
        param([int]$TargetPid, [string]$ExpectedExe)
        $proc = Get-CimInstance Win32_Process -Filter "ProcessId=$TargetPid" -ErrorAction SilentlyContinue
        if (-not $proc) { Write-Host "[stop] pid $TargetPid already gone"; return }
        if ($proc.CommandLine -notlike '*visual-verify-20260918*') {
            throw "refusing to stop pid ${TargetPid}: command line is not this worktree's ($($proc.CommandLine))"
        }
        if ($proc.CommandLine -notlike '*chimera_engine*') {
            throw "refusing to stop pid ${TargetPid}: not chimera_engine ($($proc.CommandLine))"
        }
        $exeOnDisk = if ($proc.ExecutablePath) { $proc.ExecutablePath } else { '' }
        if ($ExpectedExe -and $exeOnDisk -and ((Resolve-Path -LiteralPath $exeOnDisk).Path -ne (Resolve-Path -LiteralPath $ExpectedExe).Path)) {
            throw "refusing to stop pid ${TargetPid}: exe path mismatch ($exeOnDisk vs $ExpectedExe)"
        }
        Write-Host "[stop] path guard passed; stopping pid $TargetPid"
        Stop-Process -Id $TargetPid -Force
    }

    try {
        Write-Host '[harness] running visual_scene scenarios'
        $env:PYTHONUNBUFFERED = '1'
        & $Python -B -m tools.science_funnel.visual_scene --port $port --out $outDir --runtime .tmp/coupled-native/runtime.json
        if ($LASTEXITCODE -ne 0) { throw "visual_scene harness failed (exit $LASTEXITCODE)" }
    } finally {
        Stop-OwnedEngine -TargetPid $enginePid -ExpectedExe $runtime.exe
        $deadline = (Get-Date).AddSeconds(10)
        while ((Get-Date) -lt $deadline) {
            if (-not (Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue)) { break }
            Start-Sleep -Milliseconds 200
        }
        if (Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue) {
            throw "port $port still listening after stop"
        }
        Write-Host "[stop] port $port released"
    }

    Write-Host '[done] validation directory:'
    Get-ChildItem -Recurse $outDir | Select-Object -ExpandProperty FullName
} finally {
    Pop-Location
}
