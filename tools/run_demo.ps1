<#
    Start the Chimera viewer and open it. Meant to be reached by double-clicking DEMO.bat at the
    repo root -- no terminal knowledge, no agent, no arguments.

    It does four things and reports each one, because a launcher that fails silently is worse than
    no launcher: find python, free the port, start the server, wait until it actually ANSWERS
    (not just until the process exists), then open the browser.
#>
param([int]$Port = 8765, [switch]$NoBrowser)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Log  = Join-Path $Root "gallery_out.log"
$Err  = Join-Path $Root "gallery_err.log"

function Say($msg, $col = "Gray") { Write-Host "  $msg" -ForegroundColor $col }

Write-Host ""
Write-Host "  CHIMERA" -ForegroundColor Cyan
Write-Host "  the story, as a hierarchy you can turn" -ForegroundColor DarkGray
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

# 2. free the port -- a stale server from a previous run is the usual reason this "does nothing"
$stale = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
if ($stale) {
    foreach ($c in $stale) { Stop-Process -Id $c.OwningProcess -Force -ErrorAction SilentlyContinue }
    Say "freed port $Port (a viewer was already running)"
    Start-Sleep -Milliseconds 700
}

# 3. start it
$gallery = Join-Path $Root "ChimeraEngine\gallery.py"
if (-not (Test-Path $gallery)) { Say "cannot find $gallery" "Red"; Read-Host "`n  press Enter"; exit 1 }
Start-Process -FilePath $py -ArgumentList $gallery, $Port -WorkingDirectory $Root `
              -RedirectStandardOutput $Log -RedirectStandardError $Err -WindowStyle Hidden
Say "starting the viewer..."

# 4. wait until it ANSWERS. The first start compiles CUDA kernels, so this can take a while --
#    reporting progress beats a launcher that looks hung.
$url = "http://127.0.0.1:$Port/live"
$ok = $false
for ($i = 1; $i -le 90; $i++) {
    Start-Sleep -Seconds 1
    try {
        $r = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 3
        if ($r.StatusCode -eq 200) { $ok = $true; break }
    } catch { }
    if ($i % 10 -eq 0) { Say "still warming up ($i s) -- the GPU kernels compile on first run" "DarkGray" }
}

if (-not $ok) {
    Say "the viewer did not come up. Last errors:" "Red"
    if (Test-Path $Err) { Get-Content $Err -Tail 15 | ForEach-Object { Write-Host "    $_" -ForegroundColor DarkRed } }
    Read-Host "`n  press Enter to close"; exit 1
}

Say "ready" "Green"
Write-Host ""
Write-Host "  $url" -ForegroundColor Cyan
Write-Host ""
Write-Host "  click any membrane on the left to go down the hierarchy." -ForegroundColor DarkGray
Write-Host "  drag to turn it, scroll to zoom." -ForegroundColor DarkGray
Write-Host "  the sliders on the right change the world; the LENS sliders change only the picture." -ForegroundColor DarkGray
Write-Host ""
Write-Host "  close this window to stop the viewer." -ForegroundColor DarkGray

if (-not $NoBrowser) { Start-Process $url }

# hold the window open so closing it is the obvious way to stop
try { while ($true) { Start-Sleep -Seconds 3600 } }
finally {
    Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
        ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
}
