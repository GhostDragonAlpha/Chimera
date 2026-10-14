# run_encode.ps1 -- cut real_body_slice_v2.mp4 at the MEASURED cadence
# (ffconcat true-time; motion speed exact), CRF ladder under the 25 MB
# delivery bound, record + sha in encode_record.json.
$Lane = "E:\ChimeraWork\rendertruth-agent\tools\science_funnel\validation\render_truth_20260920"
python -u (Join-Path $Lane "render_truth_encode.py") --frames (Join-Path $Lane "frames") --record (Join-Path $Lane "capture_record.json") --out (Join-Path $Lane "real_body_slice_v2.mp4") --truetime
exit $LASTEXITCODE
