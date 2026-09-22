# run_framing_probe.ps1 -- starts this worktree's slice server on a private
# port, waits for the world, runs framing_probe.js (private headless bundled
# chromium, never the shared desktop), stops the server. One background run.
param(
    [int]$Port = 8935
)
$ErrorActionPreference = "Stop"
$Root = "E:\ChimeraWork\rendertruth-agent"
$Slice = Join-Path $Root "tools\playable_slice"
$Exe = Join-Path $Root ".tmp\slice_build\Release\chimera_engine.exe"

& powershell -NoProfile -ExecutionPolicy Bypass -File `
    (Join-Path $Root "tools\science_funnel\validation\slice_stranger_20260920\sweep_own_engines.ps1") `
    -ExePath $Exe

$proc = Start-Process -FilePath "python" -ArgumentList @("-u", (Join-Path $Slice "slice_server.py"), "--port", "$Port", "--no-browser") `
    -WorkingDirectory $Root -RedirectStandardOutput (Join-Path $PSScriptRoot "framing_server.log") `
    -RedirectStandardError (Join-Path $PSScriptRoot "framing_server.err") `
    -WindowStyle Hidden -PassThru
Write-Output ("server pid " + $proc.Id)

$up = $false
for ($i = 1; $i -le 90; $i++) {
    Start-Sleep -Seconds 1
    try {
        $h = Invoke-RestMethod -Uri ("http://127.0.0.1:" + $Port + "/api/health") -TimeoutSec 3
        if ($h.world_booted) { $up = $true; break }
    } catch { Start-Sleep -Milliseconds 200 }
}
if (-not $up) { Write-Output "server never booted"; try { Stop-Process -Id $proc.Id -Force } catch {}; exit 1 }
Write-Output "world booted"

node (Join-Path $PSScriptRoot "framing_probe.js") ("http://127.0.0.1:" + $Port) (Join-Path $PSScriptRoot "framing_frames")
$rc = $LASTEXITCODE

try { Stop-Process -Id $proc.Id -Force } catch { }
Start-Sleep -Milliseconds 800
& powershell -NoProfile -ExecutionPolicy Bypass -File `
    (Join-Path $Root "tools\science_funnel\validation\slice_stranger_20260920\sweep_own_engines.ps1") `
    -ExePath $Exe
Write-Output ("framing probe rc=" + $rc)
exit $rc
