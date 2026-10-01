<#
    Sweep THIS lane's own leftovers: chimera_engine.exe / lesson_server.py
    processes whose command line carries THIS worktree's lesson paths.
    Everything else (other worktrees, other lanes, the desktop) is untouchable.
#>
$ErrorActionPreference = "SilentlyContinue"
$mine = @("buffy-lesson-agent\\.tmp\\lesson_build", "lesson_shell\\lesson_server.py")
$procs = Get-CimInstance Win32_Process -Filter "Name='chimera_engine.exe' OR Name='python.exe'"
$killed = 0
foreach ($p in $procs) {
    $cl = $p.CommandLine
    if (-not $cl) { continue }
    foreach ($m in $mine) {
        if ($cl -like "*$m*") {
            Stop-Process -Id $p.ProcessId -Force
            Write-Host "sweep: killed $($p.Name) pid $($p.ProcessId)"
            $killed++
            break
        }
    }
}
Write-Host "sweep: $killed own process(es) removed"
