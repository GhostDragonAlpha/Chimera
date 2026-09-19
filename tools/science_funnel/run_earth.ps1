param(
    [ValidateRange(1024,65535)][int]$Port=8125,
    [string]$Python="python",
    [string]$CMake="cmake",
    [switch]$SkipBuild,
    [switch]$ForceArm,
    [switch]$CoupledArm,
    [switch]$MacaqueScene,
    [string]$ContactPlaneHeightSource=""
)
$ErrorActionPreference="Stop"
if(@($ForceArm,$CoupledArm,$MacaqueScene).Where({$_}).Count -gt 1){throw "Choose one scene mode."}
if($CoupledArm -and -not $PSBoundParameters.ContainsKey("Port")){$Port=8127}
$projectRoot=(Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Push-Location $projectRoot
try {
    if(Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue) {
        throw "Port $Port is occupied; this launcher never stops existing processes."
    }
    $compiler=if($MacaqueScene){'tools.science_funnel.macaque_scene'}elseif($CoupledArm){'tools.science_funnel.coupled_scene'}elseif($ForceArm){'tools.science_funnel.force_arm'}else{'tools.science_funnel.earth_scene'}
    # Opt-in terrain-derived contact plane (work.environment.terrain
    # wiring_20260918): empty by default, so the default compile argv -- and
    # therefore the qualified default scene -- is untouched.
    $compileArgs=@()
    if($ContactPlaneHeightSource){
        if(-not $CoupledArm){throw "-ContactPlaneHeightSource applies only to -CoupledArm."}
        $compileArgs=@('--contact-plane-height-source',$ContactPlaneHeightSource)
    }
    & $Python -B -m $compiler @compileArgs
    if($LASTEXITCODE -ne 0){throw "Graph compilation refused."}
    $buildRelative=if($MacaqueScene){'.tmp/macaque-engine'}elseif($CoupledArm){'.tmp/coupled-native-engine'}elseif($ForceArm){'.tmp/force-arm-engine'}else{'.tmp/earth-engine'}
    $buildDir=Join-Path $projectRoot $buildRelative
    if(-not $SkipBuild) {
        & $CMake -S ChimeraEngine/engine -B $buildDir
        if($LASTEXITCODE -ne 0){throw "CMake configure failed."}
        & $CMake --build $buildDir --config Release --parallel 6
        if($LASTEXITCODE -ne 0){throw "Native build failed."}
    }
    $exe=Join-Path $buildDir "Release\chimera_engine.exe"
    if(-not (Test-Path -LiteralPath $exe)){throw "Executable missing: $exe"}
    $sceneRelative=if($MacaqueScene){'.tmp/macaque-scene/scene.json'}elseif($CoupledArm){'.tmp/coupled-native/scene.json'}elseif($ForceArm){'.tmp/force-arm/scene.json'}else{'.tmp/earth-patch/scene.json'}
    $scene=Join-Path $projectRoot $sceneRelative
    $outputDir=Split-Path $scene
    $stamp=Get-Date -Format "yyyyMMdd_HHmmss"
    $startArgs=@{
        FilePath=$exe;WorkingDirectory=(Split-Path $exe)
        ArgumentList=@("$Port","--hidden","1600","900","--no-restore","--earth-patch",('"' + $scene + '"'))
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
            $state=Invoke-RestMethod "http://127.0.0.1:$Port/earth_state" -TimeoutSec 2
            if($state.ok -and $state.scene_sha256 -eq $compiled.scene_sha256) {
                Write-Output "Running PID $($process.Id): http://127.0.0.1:$Port/earth"
                return
            }
        } catch {}
        Start-Sleep -Milliseconds 100
    } while([DateTime]::UtcNow -lt $deadline)
    throw "Process launched but readiness did not qualify. See $outputDir."
} finally {Pop-Location}
