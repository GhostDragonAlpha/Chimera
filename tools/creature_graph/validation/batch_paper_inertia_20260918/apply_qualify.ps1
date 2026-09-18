# PAPER-TABLE-INERTIA-INTAKE: final batch qualification per the integrator's
# timeout-recovery directive. Start-Process -Wait keeps the qualification
# detached from the calling shell's process tree; the receipt is hashed and
# copied in the same script, immediately after the writer exits, closing the
# window in which the file has gone missing after previous runs.
$ErrorActionPreference = 'Stop'
$lane = 'E:\ChimeraWork\paper-inertia-20260918'
$val  = Join-Path $lane 'tools\creature_graph\validation\batch_paper_inertia_20260918'
$py   = 'E:\PythonChimera\.venv-hy3d\Scripts\python.exe'
$receipt = Join-Path $val 'receipt.json'

# Quiet-window guard: other lanes' qualify/consumer suites share this host.
$deadline = (Get-Date).AddMinutes(10)
while ((Get-Date) -lt $deadline) {
    $busy = (Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
        Where-Object { $_.CommandLine -match 'batch_qualify|graphify_consumer' } |
        Measure-Object).Count
    if ($busy -eq 0) { break }
    Start-Sleep -Seconds 45
}

# The qualification, detached, stdout+stderr to logs (per the directive).
$out = Join-Path $val 'apply_stdout.log'
$err = Join-Path $val 'apply_stderr.log'
$p = Start-Process -FilePath $py `
    -ArgumentList '-B','-m','tools.creature_graph.batch_qualify',
                  '--reprove','all','--admit','oku_paper_table','--apply',
                  '--out','tools/science_funnel/validation/batch_paper_inertia_20260918/receipt.json' `
    -WorkingDirectory $lane -RedirectStandardOutput $out -RedirectStandardError $err `
    -NoNewWindow -PassThru -Wait
Write-Output ("apply exit code: " + $p.ExitCode)
Get-Content $out -Tail 3

# Immediate post-exit capture: hash + copy in the same breath as the writer's exit.
if (Test-Path $receipt) {
    $hash = (Get-FileHash $receipt -Algorithm SHA256).Hash.ToLower()
    $bytes = (Get-Item $receipt).Length
    Copy-Item $receipt (Join-Path $val 'receipt_backup.json') -Force
    Write-Output ("receipt pinned: sha256 " + $hash + " (" + $bytes + " bytes)")
} else {
    Write-Output "RECEIPT MISSING immediately after writer exit"
    Get-Content $err -Tail 5
}
