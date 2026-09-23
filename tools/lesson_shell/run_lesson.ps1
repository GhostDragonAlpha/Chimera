<#
    Start LESSON ONE "THE FALL" -- the one-command boot (F-ONE-COMMAND).
    The R1 pattern: find python, check the engine, free the port (only our
    own lesson server), start the server, wait until it ANSWERS (not until
    the process exists), print the URL. The server owns the engine boot
    (the real CT body) and never opens a browser -- a shared desktop is
    never touched.
#>
param([int]$Port = 8912)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$Log  = Join-Path $env:TEMP "lesson_one_out.log"
$Err  = Join-Path $env:TEMP "lesson_one_err.log"

function Say($msg, $col = "Gray") { Write-Host "  $msg" -ForegroundColor $col }

Write-Host ""
Write-Host "  CHIMERA - LESSON ONE: THE FALL" -ForegroundColor Cyan
Write-Host "  a real body falls, the floor catches it, the forces balance" -ForegroundColor DarkGray
Write-Host ""

# 1. python
$py = $null
foreach ($c in @("python", "python3", "py")) {
    $cmd = Get-Command $c -ErrorAction SilentlyContinue
    if ($cmd) { $py = $cmd.Source; break }
}
if (-not $py) { Say "python is not on your PATH." "Red"; exit 1 }
Say "python  $py"

# 2. the engine must exist
$exe = Join-Path $Root ".tmp\lesson_build\Release\chimera_engine.exe"
if (-not (Test-Path $exe)) {
    Say "the engine binary is missing at $exe" "Red"
    Say "build it with:" "Red"
    Say "  cmake -S ChimeraEngine/engine -B .tmp/lesson_build" "Red"
    Say "  cmake --build .tmp/lesson_build --config Release" "Red"
    exit 1
}
Say "engine  ok"

# 3. free the port -- ONLY our own lesson server, never a foreign process
$stale = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
if ($stale) {
    foreach ($c in $stale) {
        $procId = $c.OwningProcess
        $cl = (Get-CimInstance Win32_Process -Filter "ProcessId=$procId").CommandLine
        if ($cl -and $cl -like "*lesson_server.py*") {
            Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
            Say "freed port $Port (our own stale lesson server)"
        } else {
            Say "port $Port is held by a foreign process (pid $procId) -- refusing to kill it" "Red"
            exit 1
        }
    }
    Start-Sleep -Milliseconds 700
}

# 4. start the server (it boots the real body itself)
$server = Join-Path $Root "tools\lesson_shell\lesson_server.py"
$p = Start-Process -FilePath $py -ArgumentList @("-u", $server, "--port", "$Port") `
        -WorkingDirectory $Root -WindowStyle Hidden `
        -RedirectStandardOutput $Log -RedirectStandardError $Err -PassThru
Say "lesson server starting (pid $($p.Id)) -- log $Log"

# 5. wait until it ANSWERS (the R1 law)
$base = "http://127.0.0.1:$Port"
$ok = $false
for ($i = 0; $i -lt 100; $i++) {
    try {
        $r = Invoke-WebRequest -Uri "$base/api/health" -UseBasicParsing -TimeoutSec 2
        if ($r.StatusCode -eq 200) { $ok = $true; break }
    } catch { Start-Sleep -Milliseconds 300 }
}
if (-not $ok) {
    Say "the lesson server did not answer within 30 s -- tail of the log:" "Red"
    Get-Content $Log -Tail 10 -ErrorAction SilentlyContinue
    Get-Content $Err -Tail 10 -ErrorAction SilentlyContinue
    exit 1
}
Say "LESSON ONE answers on  $base" "Green"
Say "(open it in a browser; the page teaches the rest)"
