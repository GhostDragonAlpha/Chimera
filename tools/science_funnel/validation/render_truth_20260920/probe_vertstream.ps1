# probe_vertstream.ps1 -- render-truth lane, 20260920.
# Starts this worktree's slice server on a private port (background job),
# waits for health, fetches /api/verts once, prints per-vertex floats
# (position, normal, color) for a few vertices + the payload header, then
# stops the server. Read-only probe: no POSTs, no page, no desktop.
param(
    [int]$Port = 8933
)
$ErrorActionPreference = "Stop"
$Root = "E:\ChimeraWork\rendertruth-agent"
$Slice = Join-Path $Root "tools\playable_slice"

function Say($msg) { Write-Host ("  " + $msg) }

# sweep OUR OWN orphaned engines only
$Exe = Join-Path $Root ".tmp\slice_build\Release\chimera_engine.exe"
& powershell -NoProfile -ExecutionPolicy Bypass -File `
    (Join-Path $Root "tools\science_funnel\validation\slice_stranger_20260920\sweep_own_engines.ps1") `
    -ExePath $Exe

$Stamp = Get-Date -Format "HHmmss"
$Log = Join-Path $Root ("tools\science_funnel\validation\render_truth_20260920\probe_server_" + $Stamp + ".log")
$proc = Start-Process -FilePath "python" -ArgumentList @("-u", (Join-Path $Slice "slice_server.py"), "--port", "$Port", "--no-browser") `
    -WorkingDirectory $Root -RedirectStandardOutput $Log -RedirectStandardError ($Log + ".err") `
    -WindowStyle Hidden -PassThru
Say ("server pid " + $proc.Id + " log " + $Log)

$up = $false
for ($i = 1; $i -le 90; $i++) {
    Start-Sleep -Seconds 1
    try {
        $h = Invoke-RestMethod -Uri ("http://127.0.0.1:" + $Port + "/api/health") -TimeoutSec 3
        if ($h.world_booted) { $up = $true; break }
    } catch { }
}
if (-not $up) { Say "server never booted"; try { Stop-Process -Id $proc.Id -Force } catch {}; exit 1 }
Say "world booted; fetching /api/verts"

python (Join-Path $PSScriptRoot "probe_vertstream.py") ("http://127.0.0.1:" + $Port)

try { Stop-Process -Id $proc.Id -Force } catch { }
Start-Sleep -Milliseconds 800
& powershell -NoProfile -ExecutionPolicy Bypass -File `
    (Join-Path $Root "tools\science_funnel\validation\slice_stranger_20260920\sweep_own_engines.ps1") `
    -ExePath $Exe
Say "done"
