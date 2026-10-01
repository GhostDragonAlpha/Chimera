# parallel_test.ps1 - run all science_funnel test MODULES in parallel.
#
# Each module (test_batch.py, test_coupled_scene.py, ...) runs as an
# independent python process (unittest, repo-root cwd); up to -Jobs processes
# at once on the 24-core operator box. Output goes to a per-module log file
# (no pipe draining, no deadlock); exit codes + wall time are collected and a
# JSON summary is written to .tmp/compute_harness/parallel_last.json.
#
# Usage:
#   powershell -NoProfile -ExecutionPolicy Bypass -File tools\parallel_test.ps1 [-Quick] [-Jobs 12]
#
# -Quick skips the known-slow modules (test_surface_scene, test_force_compiler)
# for iteration cycles.
#
# work.data.compute_harness falsifier (test half): the FULL suite must complete
# in <8 minutes (was 15-30 serial). This script measures that number.
param(
    [string]$Python = "E:\PythonChimera\.venv-hy3d\Scripts\python.exe",
    [int]$Jobs = 12,
    [switch]$Quick,
    [string]$RepoRoot = (Split-Path -Parent (Split-Path -Parent $PSCommandPath)),
    [int]$TimeoutSec = 1800,
    [string]$OutFile = "",
    # Comma-separated module stems (powershell -File cannot bind arrays).
    [string]$Modules = ""
)

$ErrorActionPreference = "Continue"
$repo = $RepoRoot
$outDir = Join-Path $repo ".tmp\compute_harness"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
if ($OutFile -eq "") { $OutFile = Join-Path $outDir "parallel_last.json" }

# Known-slow modules for iteration cycles.
$quickSkip = @("test_surface_scene", "test_force_compiler")

# Discover funnel test modules (tools/science_funnel/tests/test_*.py).
$testsDir = Join-Path $repo "tools\science_funnel\tests"
if ($Modules.Trim() -ne "") {
    $stems = $Modules -split "," | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne "" }
} else {
    $stems = Get-ChildItem -Path $testsDir -Filter "test_*.py" |
        ForEach-Object { $_.BaseName } | Sort-Object
}
if ($Quick) {
    $stems = $stems | Where-Object { $quickSkip -notcontains $_ }
}

# NOTE: do NOT name this $modules - it collides with the $Modules parameter
# (PowerShell variables are case-insensitive) and corrupts the list.
$testItems = @()
foreach ($s in $stems) {
    $testItems += [pscustomobject]@{
        Name   = $s
        Dotted = "tools.science_funnel.tests.$s"
    }
}

Write-Host ("parallel_test: {0} modules, jobs={1}, quick={2}, python={3}" -f $testItems.Count, $Jobs, $Quick, $Python)

$queue = [System.Collections.Generic.Queue[object]]::new()
foreach ($m in $testItems) { $queue.Enqueue($m) }

$running = [System.Collections.Generic.List[object]]::new()
$results = [System.Collections.Generic.List[object]]::new()
$swTotal = [System.Diagnostics.Stopwatch]::StartNew()

function Start-ModuleJob($mod) {
    # PowerShell job: the job's powershell runs python directly (native wait,
    # no pipe draining, no wrapper that can exit early), redirects all output
    # to the module's log file, and exits with python's exit code.
    $log = Join-Path $outDir ("pt_{0}.log" -f $mod.Name)
    $job = Start-Job -ScriptBlock {
        param($py, $dotted, $repo, $logPath, $codePath)
        Set-Location $repo
        & $py -m unittest -v $dotted *> $logPath
        # Write the exit code to a file: bulletproof across job serialization.
        Set-Content -Path $codePath -Value ([int]$LASTEXITCODE)
    } -ArgumentList $Python, $mod.Dotted, $repo, $log, (Join-Path $outDir ("pt_{0}.code" -f $mod.Name))
    $running.Add([pscustomobject]@{
        Name = $mod.Name
        Job  = $job
        Log  = $log
        Sw   = [System.Diagnostics.Stopwatch]::StartNew()
    })
}

function Stop-ModuleJob($entry, [bool]$timedOut) {
    $entry.Sw.Stop()
    if ($timedOut) {
        Stop-Job $entry.Job -Force
        $code = "timeout"
    } else {
        Wait-Job $entry.Job | Out-Null
        $codePath = Join-Path $outDir ("pt_{0}.code" -f $entry.Name)
        if (Test-Path $codePath) {
            $code = [int](Get-Content $codePath)
        } else {
            $code = "no_code_file"
        }
    }
    Remove-Job $entry.Job -Force
    $rec = [pscustomobject]@{
        module    = $entry.Name
        exit_code = $code
        seconds   = [math]::Round($entry.Sw.Elapsed.TotalSeconds, 2)
        passed    = $(if ($timedOut) { $false } else { $code -eq 0 })
        log       = $entry.Log
    }
    $results.Add($rec)
    Write-Host ("  [{0,7}s] {1}  rc={2}" -f $rec.seconds, $entry.Name, $rec.exit_code)
}

# Throttled pump: start up to $Jobs, reap finished, until the queue empties.
while ($running.Count -gt 0 -or $queue.Count -gt 0) {
    while ($queue.Count -gt 0 -and $running.Count -lt $Jobs) {
        Start-ModuleJob $queue.Dequeue()
    }
    Start-Sleep -Milliseconds 250
    for ($i = $running.Count - 1; $i -ge 0; $i--) {
        $e = $running[$i]
        if ($e.Job.State -ne "Running") {
            $running.RemoveAt($i)
            Stop-ModuleJob $e $false
        } elseif ($e.Sw.Elapsed.TotalSeconds -gt $TimeoutSec) {
            $running.RemoveAt($i)
            Stop-ModuleJob $e $true
            Write-Host ("  TIMEOUT (>=$TimeoutSec s): $($e.Name)")
        }
    }
}

$swTotal.Stop()
$failed = @($results | Where-Object { -not $_.passed } | ForEach-Object { $_.module })
$allPassed = ($results.Count -gt 0) -and ($failed.Count -eq 0)
$summary = [ordered]@{
    phase          = "parallel_funnel_tests"
    mode           = $(if ($Quick) { "quick" } else { "full" })
    jobs           = $Jobs
    modules_run    = $results.Count
    skipped_quick  = $(if ($Quick) { $quickSkip } else { @() })
    failed_modules = $failed
    all_passed     = [bool]$allPassed
    wall_seconds   = [math]::Round($swTotal.Elapsed.TotalSeconds, 2)
    python         = $Python
    recorded_utc   = (Get-Date).ToUniversalTime().ToString("o")
    results        = $results
}
$summary | ConvertTo-Json -Depth 4 | Out-File -FilePath $OutFile -Encoding utf8

Write-Host ("parallel_test: done in {0}s  passed={1}/{2}  (quick={3})" -f `
    [math]::Round($swTotal.Elapsed.TotalSeconds, 1), `
    @($results | Where-Object { $_.passed }).Count, $results.Count, $Quick)
if (-not $allPassed) {
    Write-Host ("FAILED: " + ($failed -join ", "))
}
exit $(if ($allPassed) { 0 } else { 1 })
