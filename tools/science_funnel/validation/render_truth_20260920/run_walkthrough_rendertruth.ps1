# run_walkthrough_rendertruth.ps1 -- F-STRANGER-REGRESSION's instrument run
# (lane render-truth-20260920). The COMMITTED stranger walkthrough
# (tools/science_funnel/validation/slice_stranger_20260920/walkthrough.js,
# byte-unmodified) re-targeted to THIS worktree's server: sweep this
# worktree's orphaned engines, start the slice server on a fixed private
# port, wait until it ANSWERS, run the scripted stranger (private headless
# browser, never the shared desktop), stop the server, report. Exits nonzero
# on any falsifier failure.
param(
    [int]$Port = 8937,
    [string]$OutJson = ""
)
$ErrorActionPreference = "Stop"

$Root = "E:\ChimeraWork\rendertruth-agent"
$Lane = Join-Path $Root "tools\science_funnel\validation\render_truth_20260920"
$Stranger = Join-Path $Root "tools\science_funnel\validation\slice_stranger_20260920"
$Exe  = Join-Path $Root ".tmp\slice_build\Release\chimera_engine.exe"
if ($OutJson -eq "") { $OutJson = Join-Path $Lane ("walkthrough_run_{0}.json" -f (Get-Date -Format "HHmmss")) }

function Say($msg, $col = "Gray") { Write-Host ("  " + $msg) -ForegroundColor $col }

Say ("root " + $Root) "DarkGray"

# 1. sweep THIS worktree's orphaned engines (never another worktree's)
& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $Stranger "sweep_own_engines.ps1") -ExePath $Exe

# 2. free the port ONLY if one of OUR OWN slice servers holds it
$stale = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
if ($stale) {
    foreach ($c in $stale) {
        $owner = Get-CimInstance Win32_Process -Filter ("ProcessId=" + $c.OwningProcess) -ErrorAction SilentlyContinue
        $ours = $owner -and $owner.CommandLine -like "*slice_server.py*" -and $owner.CommandLine -like "*" + $Port + "*"
        if ($ours) {
            Say ("freeing port " + $Port + " (our stale slice, pid " + $c.OwningProcess + ")")
            Stop-Process -Id $c.OwningProcess -Force -ErrorAction SilentlyContinue
        } else {
            Say ("port " + $Port + " is held by pid " + $c.OwningProcess + " which is NOT our slice -- refusing to touch it") "Red"
            exit 1
        }
    }
    Start-Sleep -Milliseconds 700
}

# 3. start the slice server (it boots the real body through the cached GLB)
$Stamp = Get-Date -Format "HHmmss"
$Log = Join-Path $Lane ("walkthrough_server_" + $Stamp + ".out.log")
$Err = Join-Path $Lane ("walkthrough_server_" + $Stamp + ".err.log")
$server = Join-Path $Root "tools\playable_slice\slice_server.py"
$proc = Start-Process -FilePath "python" -ArgumentList @("-u", $server, "--port", "$Port", "--no-browser") `
    -WorkingDirectory $Root -RedirectStandardOutput $Log -RedirectStandardError $Err `
    -WindowStyle Hidden -PassThru
Say ("server pid " + $proc.Id + " log " + $Log) "DarkGray"

# 4. wait until it ANSWERS (not until the process exists)
$up = $false
for ($i = 1; $i -le 90; $i++) {
    Start-Sleep -Seconds 1
    try {
        $h = Invoke-RestMethod -Uri ("http://127.0.0.1:" + $Port + "/api/health") -TimeoutSec 3
        if ($h.world_booted) { $up = $true; break }
    } catch { }
}
if (-not $up) {
    Say "the slice did not boot in 90 s" "Red"
    if (Test-Path $Log) { Get-Content $Log -Tail 15 | ForEach-Object { Say $_ "DarkRed" } }
    try { Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue } catch { }
    exit 1
}
Say ("slice answers on port " + $Port) "Green"

# 5. the stranger plays (the committed walkthrough, unmodified)
node (Join-Path $Stranger "walkthrough.js") ("http://127.0.0.1:" + $Port) $OutJson
$rc = $LASTEXITCODE

# 6. the server stops; its engine child is swept after
try { Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue } catch { }
Start-Sleep -Milliseconds 800
& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $Stranger "sweep_own_engines.ps1") -ExePath $Exe

Say ("artifact " + $OutJson)
exit $rc
