<#
    Start the PLAYABLE SLICE and open it. Reached by double-clicking
    PlayableSlice.bat -- no terminal knowledge, no agent, no arguments.
    The R1 pattern: find python, free the port, start the server, wait until
    it ANSWERS (not until the process exists), then open the browser.

    The server owns the rest: it starts its own engine on a bind-tested free
    port (8127 is refused by code), boots the standing start, and serves the
    page. A launcher that fails silently is worse than no launcher, so every
    step reports.
#>
param([int]$Port = 0)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Log  = Join-Path $env:TEMP "slice_out.log"
$Err  = Join-Path $env:TEMP "slice_err.log"

function Say($msg, $col = "Gray") { Write-Host "  $msg" -ForegroundColor $col }

Write-Host ""
Write-Host "  CHIMERA — the playable slice" -ForegroundColor Cyan
Write-Host "  the standing start: one creature, one marker, honest physics" -ForegroundColor DarkGray
Write-Host ""

# 1. python
$py = $null
foreach ($c in @("python", "python3", "py")) {
    $cmd = Get-Command $c -ErrorAction SilentlyContinue
    if ($cmd) { $py = $cmd.Source; break }
}
if (-not $py) {
    Say "python is not on your PATH. Install it from python.org and run this again." "Red"
    Read-Host "`n  press Enter to close"; exit 1
}
Say "python  $py"

# 2. the engine must exist (built once by the lane; no dev tools needed to play)
$exe = Join-Path $Root ".tmp\slice_build\Release\chimera_engine.exe"
if (-not (Test-Path $exe)) {
    Say "the engine binary is missing at $exe" "Red"
    Say "this slice folder ships beside its built engine -- rebuild with:" "Red"
    Say "  cmake -S ChimeraEngine/engine -B .tmp/slice_build" "Red"
    Say "  cmake --build .tmp/slice_build --config Release" "Red"
    Read-Host "`n  press Enter to close"; exit 1
}
Say "engine  ok"

# 3. free the port (a stale slice from a previous run is the usual 'nothing happens')
if ($Port -ne 0) {
    $stale = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if ($stale) {
        foreach ($c in $stale) { Stop-Process -Id $c.OwningProcess -Force -ErrorAction SilentlyContinue }
        Say "freed port $Port (a slice was already running)"
        Start-Sleep -Milliseconds 700
    }
}

# 4. start it (the server picks its own free port when none is passed)
$server = Join-Path $Root "tools\playable_slice\slice_server.py"
$args = @($server)
if ($Port -ne 0) { $args += @("--port", "$Port") }
Start-Process -FilePath $py -ArgumentList $args -WorkingDirectory $Root `
              -RedirectStandardOutput $Log -RedirectStandardError $Err -WindowStyle Hidden
Say "starting the slice..."

# 5. wait until it ANSWERS
$ok = $false
for ($i = 1; $i -le 30; $i++) {
    Start-Sleep -Seconds 1
    $line = $null
    if (Test-Path $Log) { $line = (Get-Content $Log | Select-String "slice: http" | Select-Object -Last 1) }
    if ($line) {
        $url = ($line -replace ".*slice:\s*", "").Trim()
        Say "ready: $url" "Green"
        Start-Process $url
        $ok = $true
        break
    }
    if (Test-Path $Err) {
        $errTail = Get-Content $Err -Tail 3 -ErrorAction SilentlyContinue
        if ($errTail -and $errTail[0] -match "Traceback|Error") {
            Say "the slice failed to start:" "Red"
            $errTail | ForEach-Object { Write-Host "    $_" -ForegroundColor DarkRed }
            break
        }
    }
}
if (-not $ok) {
    Say "the slice did not come up in 30 s. Last output:" "Red"
    if (Test-Path $Log) { Get-Content $Log -Tail 8 | ForEach-Object { Write-Host "    $_" -ForegroundColor DarkRed } }
    if (Test-Path $Err) { Get-Content $Err -Tail 8 | ForEach-Object { Write-Host "    $_" -ForegroundColor DarkRed } }
    Read-Host "`n  press Enter to close"; exit 1
}
Read-Host "  press Enter to close this window (the slice keeps running)"
