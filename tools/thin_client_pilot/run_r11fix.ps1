# thincli lane: re-measure R11 on the fixed DELTA transport.
$ErrorActionPreference = "Continue"
python E:/ChimeraWork/thincli-agent/tools/thin_client_pilot/run_suite.py --out-dir "E:/ChimeraWork/thincli-agent/.tmp/suite_r11fix" --only R11_fall_30_delta *> "E:/ChimeraWork/thincli-agent/.tmp/r11fix.log"
Write-Output "exit=$LASTEXITCODE"
