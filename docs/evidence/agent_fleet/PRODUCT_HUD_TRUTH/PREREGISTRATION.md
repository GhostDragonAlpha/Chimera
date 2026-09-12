# product-hud-truth-01 — RULE 0 PREREGISTRATION

Committed BEFORE any implementation or run. Zero measured actuals of the
prediction below appear in this commit. Prior evidence cited: PR #97 retained
artifacts (product-feel-probe-01, integrated) — the negative arm.

## STATEMENT

The product surface's only wired time/joint readouts describe the SHOW sweep, so
the product lies exactly when the demo path drives it. After the fix, no readout
displays a number that is not the live value of the thing it names: while the
pose is edit-held, the joint row names the driven joint(s) with live thetas from
the same state buffer the pose kernel reads (st +7), and the clock plane shows
the interaction timeline the script drives through the product's own /show
endpoint — never an unlabeled 112 s sweep lap beside scripted motion.

## PREDICTION (with concrete tolerances)

Rerunning the PR #97 probe protocol — same rig (monkey_birth.bin /
monkey_joints.bin), same REST(f0-09) -> PERTURB(f10-19) -> HOLD(f20-29) ->
RESPONSE(f30-44) right-arm script, same fixed camera, same 10 fps declared clip
and the same 6 ordered keyframes (g000/g012/g020/g025/g035/g044), with one
declared addition: the probe pins the show clock (`POST /show {"playing":false}`
once) and drives the declared interaction timeline through it (`POST /show
{"time": i*0.1}` per frame, no ownership effect) — after the fix:

P1. Joint row (judge-visible; GET /studio_chrome serves the exact drawn strings):
  - In the driven regime (f10..f44) the row starts "EDIT " and every joint name
    it contains is in {shoulder_R, elbow_R}.
  - At g020 and g025 the row names BOTH driven joints with displayed values
    36.00 and 75.00 deg within ±0.05 deg (commanded peaks: 0.6 x flex).
  - |displayed theta − commanded theta| <= 0.05 deg at every captured keyframe
    for each named joint (float32 rad round-trip + %.2f quantization bound,
    >=10x margin).
P2. Engine truth channel (GET /joints, st +7 readback): driven thetas vs
    commanded <= 0.05 deg at every keyframe.
P3. Clock plane (judge-visible timeline readout, transcribed per keyframe from
    the glass and cross-checked against the drawn string):
  - In the driven regime the readout starts "EDIT t = " and contains "sweep
    paused"; the substring "/ 112.0 s (lap" does NOT appear while the pose is
    edit-held.
  - Displayed age at keyframe i = (i − 10) x 0.1 s ± 0.10 s (claim at f10).
  - Adjacent-keyframe deltas g012->g020->g025->g035->g044 = 0.8 / 0.5 / 1.0 /
    0.9 s, each ± 0.10 s. The g000->g012 pair spans the claim transition (the
    plane lawfully switches at the claim) and is EXEMPT, declared here.
  - GET /show "time" at each capture = i x 0.1 s ± 0.001 s (the scrub pins it).
P4. Rest regime (f0..f09): the row prefix remains "SHOW " (no regression of the
    sweep's own truthful context) and the readout remains the sweep clock form.
P5. Reel caption (GET /reel + glass): in the driven regime the newest reel
    entries name "EDIT <driven joint>" with a live theta (st +7), not the sweep's
    cycling joint.
P6. Blind dyad re-run (lead-spawned judge, PR #97 ordered-frames pattern: same
    six keyframes in order, same four questions, judge blind to family,
    scripting, and expected behavior): the verdict does NOT report the 4(b) /
    4(d) class — no "names a joint different from the one moving / ambiguous
    numbers" finding, no "timing is inconsistent / not a real-time capture"
    finding. Other defect classes are out of scope for this task.

## FALSIFIER

The prediction FAILS if any of:
  F1. A judge-visible frame where a displayed theta differs from the commanded
      theta by more than the preregistered 0.05 deg, or the driven-regime row
      names a joint outside {shoulder_R, elbow_R}, or g020/g025 fail to name
      both peaks.
  F2. Clock deltas inconsistent with frame spacing: any driven-regime keyframe
      age off by > 0.10 s from (i−10) x 0.1 s, any adjacent-keyframe delta off
      by > 0.10 s, or the sweep lap string visible beside edit-held motion.
  F3. The blind dyad judge re-run still reporting the 4(b)/4(d) class.
A failure is RETAINED (no tolerance widening, no silent re-run); a failed gate
reopens the claim per the law.

## RESOURCES AND IDENTITY

- Build: private, under slot-03 `.tmp/engine_build` (NEVER
  ChimeraEngine/engine/build/). Runtime under `.tmp/engine_runtime`, evidence
  under `.tmp/engine_evidence` plus this committed dir (evidence files *.txt).
- Runtime: rtx4090 + engine_demo via controller resource_request, before any
  launch. Engine lanes serialize; authoring stays on CPU until granted.
- Judge: spawned by the lead via mailbox request (PR #97 pattern, message
  a5f70dbe7d7b precedent); spec + exact prompt + rubric hash-verified; verdict
  assembles into this directory.
- Every commit carries trailer `Agent: subagent-worker-02`.

## PROTOCOL IDENTITY ( comparability with the negative arm )

Same interaction script, thetas, keyframes, camera, capture endpoints (/glass
judge artifact + /frame clean twin), encode path, and blind-judge contract as
docs/evidence/agent_fleet/PRODUCT_FEEL_PROBE/. Declared additions: (a) the
/show pin+scrub above — part of the fix's product surface exercise, needed to
make the declared 10 fps timeline real on the engine's own clock; (b) numeric
verification captures (/studio_chrome, /joints, /show, /reel) per keyframe —
they do not alter what the judge sees.
