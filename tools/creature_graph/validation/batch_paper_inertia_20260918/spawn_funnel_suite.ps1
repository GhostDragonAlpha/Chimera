# Spawn-only launcher (integrator directive #2): starts the funnel suite
# fully detached and returns immediately; logs land in this validation dir
# and are polled by separate short calls. No waiting parent to be killed.
$ErrorActionPreference = 'Stop'
$lane = 'E:\ChimeraWork\paper-inertia-20260918'
$val  = Join-Path $lane 'tools\creature_graph\validation\batch_paper_inertia_20260918'
$py   = 'E:\PythonChimera\.venv-hy3d\Scripts\python.exe'
$out = Join-Path $val 'funnel_suite_stdout.log'
$err = Join-Path $val 'funnel_suite_stderr.log'
$done = Join-Path $val 'funnel_suite_done.txt'
Remove-Item $out, $err, $done -ErrorAction SilentlyContinue

# Inner script: run the suite, then stamp the exit code into a marker file.
$inner = Join-Path $val 'spawn_inner.ps1'
@"
`$ErrorActionPreference = 'Continue'
& '$py' -B -m unittest discover -s 'tools/science_funnel/tests' 1> '$out' 2> '$err'
`$LASTEXITCODE | Set-Content -Path '$done'
"@ | Set-Content -Path $inner -Encoding UTF8

Start-Process -FilePath 'powershell' `
    -ArgumentList '-NoProfile','-ExecutionPolicy','Bypass','-File', $inner `
    -WorkingDirectory $lane -WindowStyle Hidden
Write-Output ("spawned inner launcher; logs at " + $out)
