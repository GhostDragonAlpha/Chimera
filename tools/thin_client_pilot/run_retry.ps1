# thincli lane: retry the five failed runs, FULL output to per-run files.
$ErrorActionPreference = "Continue"
$runs = @("R02_fall_15_full","R06_fall_30_tr50j","R07_fall_30_tail",
          "R08_fall_30_pos12","R13_press_30_full")
foreach ($r in $runs) {
  $out = "E:/ChimeraWork/thincli-agent/.tmp/suite_retry_$r"
  Write-Output "=== $r"
  python E:/ChimeraWork/thincli-agent/tools/thin_client_pilot/run_suite.py --out-dir $out --only $r *> "E:/ChimeraWork/thincli-agent/.tmp/retry_$r.log"
  Write-Output "exit=$LASTEXITCODE"
}
Write-Output "RETRY-DONE"
