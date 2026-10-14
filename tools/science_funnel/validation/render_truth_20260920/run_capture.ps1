# run_capture.ps1 -- THE DELIVERABLE CAPTURE RUN (lane render-truth-20260920).
# One background command: the capture instrument (python, private headless
# bundled chromium, the page's own canvas bytes) -> frames + capture_record.
param(
    [string]$FramesDir = "",
    [string]$Record = ""
)
$ErrorActionPreference = "Stop"
$Lane = "E:\ChimeraWork\rendertruth-agent\tools\science_funnel\validation\render_truth_20260920"
if ($FramesDir -eq "") { $FramesDir = Join-Path $Lane "frames" }
if ($Record -eq "") { $Record = "capture_record.json" }

python -u (Join-Path $Lane "render_truth_capture.py") --out $FramesDir --record $Record
exit $LASTEXITCODE
