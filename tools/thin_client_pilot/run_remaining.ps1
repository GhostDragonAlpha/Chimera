# thincli lane: drive the remaining runs ONE PER SUITE INVOCATION (fresh
# worlds each time -- cross-run engine state was the source of the wedges).
$ErrorActionPreference = "Continue"
$runs = @("R02_fall_15_full","R03_fall_10_full","R04_fall_60_full",
          "R06_fall_30_tr50j","R07_fall_30_tail","R08_fall_30_pos12",
          "R09_fall_30_pos16","R10_fall_30_z12","R11_fall_30_delta",
          "R13_press_30_full")
$i = 0
foreach ($r in $runs) {
  $i++
  $out = "E:/ChimeraWork/thincli-agent/.tmp/suite_run_$r"
  Write-Output "=== [$i/$($runs.Count)] $r -> $out"
  python E:/ChimeraWork/thincli-agent/tools/thin_client_pilot/run_suite.py --out-dir $out --only $r
  if ($LASTEXITCODE -ne 0) { Write-Output "!!! $r FAILED (exit $LASTEXITCODE)" }
}
Write-Output "ALL-INVOCATIONS-DONE"
