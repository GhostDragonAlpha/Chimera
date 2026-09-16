param(
    [ValidateRange(1024,65535)][int]$Port=8108,
    [string]$Python="python",
    [string]$CMake="cmake",
    [switch]$SkipBuild
)
$ErrorActionPreference="Stop"
$projectRoot=(Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Push-Location $projectRoot
try {
    if(Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue) {
        throw "Port $Port is occupied; this launcher never stops existing processes."
    }
    & $Python -B -m tools.science_funnel.thermal_scene
    if($LASTEXITCODE -ne 0){throw "Graph compilation refused."}
    $buildDir=Join-Path $projectRoot ".tmp\thermal-engine"
    if(-not $SkipBuild) {
        & $CMake -S ChimeraEngine/engine -B $buildDir
        if($LASTEXITCODE -ne 0){throw "CMake configure failed."}
        & $CMake --build $buildDir --config Release --parallel 6
        if($LASTEXITCODE -ne 0){throw "Native build failed."}
    }
    $exe=Join-Path $buildDir "Release\chimera_engine.exe"
    if(-not (Test-Path -LiteralPath $exe)){throw "Executable missing: $exe"}
    $scene=Join-Path $projectRoot ".tmp\thermal-salvage\scene.json"
    $outputDir=Split-Path $scene
    $stamp=Get-Date -Format "yyyyMMdd_HHmmss"
    $startArgs=@{
        FilePath=$exe;WorkingDirectory=(Split-Path $exe)
        ArgumentList=@("$Port","--hidden","1600","900","--no-restore","--thermal-salvage",('"' + $scene + '"'))
        WindowStyle="Hidden";PassThru=$true
        RedirectStandardOutput=(Join-Path $outputDir "engine_$stamp.stdout.log")
        RedirectStandardError=(Join-Path $outputDir "engine_$stamp.stderr.log")
    }
    $process=Start-Process @startArgs
    $compiled=Get-Content -LiteralPath $scene -Raw | ConvertFrom-Json
    [ordered]@{
        pid=$process.Id;exe=$exe;exe_sha256=(Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash
        scene=$scene;scene_file_sha256=(Get-FileHash -LiteralPath $scene -Algorithm SHA256).Hash
        graph_hash=$compiled.graph_hash;scene_sha256=$compiled.scene_sha256;port=$Port
        launched_utc=[DateTime]::UtcNow.ToString("o")
    } | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $outputDir "runtime.json") -Encoding utf8
    $deadline=[DateTime]::UtcNow.AddSeconds(25)
    do {
        if($process.HasExited){throw "Native process exited with $($process.ExitCode); see $outputDir"}
        try {
            $state=Invoke-RestMethod "http://127.0.0.1:$Port/thermal_state" -TimeoutSec 2
            if($state.ok -and $state.scene_sha256 -eq $compiled.scene_sha256) {
                Write-Output "Running PID $($process.Id): http://127.0.0.1:$Port/thermal"
                return
            }
        } catch {}
        Start-Sleep -Milliseconds 100
    } while([DateTime]::UtcNow -lt $deadline)
    throw "Process launched but readiness did not qualify. See $outputDir."
} finally {Pop-Location}
