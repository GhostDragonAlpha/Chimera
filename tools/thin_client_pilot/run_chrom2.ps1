# thincli lane: the five missing runs on the bundled chromium.
$ErrorActionPreference = "Continue"
$runs = @("R02_fall_15_full","R06_fall_30_tr50j","R07_fall_30_tail",
          "R08_fall_30_pos12","R13_press_30_full")
foreach ($r in $runs) {
  $out = "E:/ChimeraWork/thincli-agent/.tmp/suite_chrom2_$r"
  Write-Output "=== $r"
  python E:/ChimeraWork/thincli-agent/tools/thin_client_pilot/run_suite.py --out-dir $out --only $r *> "E:/ChimeraWork/thincli-agent/.tmp/chrom2_$r.log"
  Write-Output "exit=$LASTEXITCODE"
}
Write-Output "CHROM2-DONE"
