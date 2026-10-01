# run_judge.ps1 -- THE BLIND JUDGE RUN (lane render-truth-20260920).
# ONE senses.watch call over 12 ordered 384 px resizes of the captured
# frames, the realbody-movie lane's prompt VERBATIM, verdict recorded
# verbatim in judgement.json. No re-roll: whatever comes back is the
# finding.
$Lane = "E:\ChimeraWork\rendertruth-agent\tools\science_funnel\validation\render_truth_20260920"
python -u (Join-Path $Lane "render_truth_judge.py") --frames (Join-Path $Lane "frames") --capture-record (Join-Path $Lane "capture_record.json") --n 12
exit $LASTEXITCODE
