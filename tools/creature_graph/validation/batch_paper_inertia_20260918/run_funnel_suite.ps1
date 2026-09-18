# Full funnel suite as the final gate, per the integrator's timeout directive:
# Start-Process detached + bounded log polling (60s intervals, 15 min max).
# The lane's own module (test_batch_paper) already passed green.
$ErrorActionPreference = 'Stop'
$lane = 'E:\ChimeraWork\paper-inertia-20260918'
$val  = Join-Path $lane 'tools\creature_graph\validation\batch_paper_inertia_20260918'
$py   = 'E:\PythonChimera\.venv-hy3d\Scripts\python.exe'
$out = Join-Path $val 'funnel_suite_stdout.log'
$err = Join-Path $val 'funnel_suite_stderr.log'

$p = Start-Process -FilePath $py `
    -ArgumentList '-B','-m','unittest','discover','-s','tools/science_funnel/tests' `
    -WorkingDirectory $lane -RedirectStandardOutput $out -RedirectStandardError $err `
    -NoNewWindow -PassThru
Write-Output ("suite started, pid " + $p.Id)

$deadline = (Get-Date).AddMinutes(15)
while ((Get-Date) -lt $deadline -and -not $p.HasExited) {
    Start-Sleep -Seconds 60
}

if (-not $p.HasExited) {
    Write-Output "SUITE TIMEOUT (15 min) - killing my own pid only"
    Stop-Process -Id $p.Id -Force
    exit 2
}
Write-Output ("suite exit code: " + $p.ExitCode)
$tail = Get-Content $out -Tail 4
$tailErr = Get-Content $err -Tail 6
Write-Output "stdout tail:"
$tail
Write-Output "stderr tail:"
$tailErr
