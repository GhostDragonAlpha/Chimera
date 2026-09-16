param(
    [ValidateRange(1024,65535)][int]$Port = 8107,
    [string]$Python = "python",
    [switch]$SkipBuild
)
$ErrorActionPreference = "Stop"
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Push-Location $projectRoot
try {
    if (Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue) {
        throw "Port $Port is occupied. Existing processes are never stopped by this launcher."
    }
    & $Python -m tools.science_funnel.surface_scene
    if ($LASTEXITCODE -ne 0) { throw "Graph compilation refused." }
    $buildDir = Join-Path $projectRoot ".tmp\science-engine"
    if (-not $SkipBuild) {
        & cmake -S ChimeraEngine/engine -B $buildDir
        if ($LASTEXITCODE -ne 0) { throw "CMake configure failed." }
        & cmake --build $buildDir --config Release --parallel 6
        if ($LASTEXITCODE -ne 0) { throw "Native build failed." }
    }
    $exe = Join-Path $buildDir "Release\chimera_engine.exe"
    if (-not (Test-Path -LiteralPath $exe)) { throw "Native executable missing: $exe" }
    $scene = Join-Path $projectRoot ".tmp\surface-feature\surface_scene.json"
    $outDir = Split-Path $scene
    $previousEdge = $env:CHIMERA_TRI_EDGE_CONTRAST
    try {
        $env:CHIMERA_TRI_EDGE_CONTRAST = "1"
        $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $startArgs = @{
          FilePath=$exe; WorkingDirectory=(Split-Path $exe)
          ArgumentList=@("$Port","--hidden","1600","900","--no-restore","--science-surface", ('"' + $scene + '"'))
          WindowStyle="Hidden"; PassThru=$true
          RedirectStandardOutput=(Join-Path $outDir "engine_$stamp.stdout.log")
          RedirectStandardError=(Join-Path $outDir "engine_$stamp.stderr.log")
        }
        $proc = Start-Process @startArgs
    } finally { $env:CHIMERA_TRI_EDGE_CONTRAST = $previousEdge }
    $compiled = Get-Content -LiteralPath $scene -Raw | ConvertFrom-Json
    [ordered]@{
        pid=$proc.Id; exe=$exe; exe_sha256=(Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash
        cwd=(Split-Path $exe); scene=$scene; scene_sha256=(Get-FileHash -LiteralPath $scene -Algorithm SHA256).Hash
        graph_hash=$compiled.graph_hash; port=$Port; launched_utc=[DateTime]::UtcNow.ToString("o")
    } | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $outDir "runtime.json") -Encoding utf8
    $deadline = [DateTime]::UtcNow.AddSeconds(25)
    do {
        if ($proc.HasExited) { throw "Native engine exited with $($proc.ExitCode); see $outDir." }
        try {
            $state = Invoke-RestMethod "http://127.0.0.1:$Port/science_surface" -TimeoutSec 2
            if ($state.ok -and $state.graph_hash -eq $compiled.graph_hash) {
                Write-Output "Running PID $($proc.Id): http://127.0.0.1:$Port/science"
                return
            }
        } catch { }
        Start-Sleep -Milliseconds 200
    } while ([DateTime]::UtcNow -lt $deadline)
    throw "Launched PID $($proc.Id), but readiness was not verified. See $outDir."
} finally { Pop-Location }
