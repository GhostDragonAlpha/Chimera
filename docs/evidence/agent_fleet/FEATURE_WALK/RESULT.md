# RESULT — feature-walk-01 (measured actuals, appended after the run)

Prereg: PREREGISTRATION.md (committed FIRST as 86a06523, before build/run).
Run: `tools/product_features_walk/product_features_walk.py render`, private
build `.tmp/engine_build/featurewalk/Release/chimera_engine.exe`
(sha256 0fadf8b989d095a1f7b1110f31d1c3963b259958251e5b41fb1c150bc8472ecd),
port 8105 (first free of 8105/8115/8125), runtime
`.tmp/engine_runtime/feature-walk-20260912-*` (unique, drained, rc=1 on
owned stop recorded). Zero C++ edits — the engine source was never touched.

## The one honest line

**The creature STEPPED IN PLACE — travel = 0.0 (falsifier F1 fired exactly as
the prereg derivation predicted); gates G1-G6 all PASS; the take is a
360-frame fixed-camera capture (camera-fixity probe spread 0.0 px, tol 0.5)
covering TWO gait phases: the CPG march (f015-164) with steps_total
1806 -> 45009 strictly increasing and knee thetas sweeping the full declared
ROM (G2: max deviation 72.768 deg >= 58.78 required), then the certified
stride (f175-354) streaming t = 0.400 -> 72.598 s = ~19.7 loops of the
3.664 s stride cycle (G4/G5 PASS).** The walk feature is NOT closed as
"traveling"; the gap is an ENGINE-SERVICE gap, recorded per the prereg:
no public route in the engine's route table can translate the creature's
root — both pose planes are rotation-only about fixed pivots (prereg
derivation items 1-5). Not a lane failure and NOT fixed with a C++ edit
(architecture directive; F3 structurally excluded).

## Gate actuals (render_records.txt is the primary record)

- G1 PASS — steps_total series [1806, 4743, 7740, 10740, 13716, 16683,
  19749, 22776, 25863, 28854, 31923, 35127, 38433, 41676, 45009]:
  >0 and strictly increasing across 15 MARCH readbacks (closes PR #97's
  "gait steps=0").
- G2 PASS — max |theta - mid| = 72.768 deg; required >= 0.8 x 73.475 = 58.78
  (the H7 law live at near-full declared amplitude).
- G3 PASS — /gait_state phase ring: cap 262144, min per-oscillator std
  88.0 > 0 (the CPG is stepping, not parked); steps_total 49635 at read.
- G4 PASS — /stride active=true, playing=true, t = 72.598 s advanced far
  past loop0*dt = 1.833 s (the stride entered its loop and kept looping).
- G5 PASS — leg-joint thetas >= 10 deg at exactly 2 of 3 STRIDE keyframes
  (f265 knee_L 10.8 deg; f359 knee_R 32.769 deg, hip_L 14.1 deg) — foot
  movement is measured (closes PR #97's "no foot movement").
- G6 PASS — /project of the SAME world point (knee_R pivot) at all 6
  keyframes: sx = 1302.358276, sy = 623.499146 EVERY time; spread 0.0 px
  (camera provably fixed; any apparent motion is the creature, not a pan).
- G7 MEASURED — travel = 0.0; falsifier F1 FIRES (the honest partial is the
  deliverable; the derivation said it would, before the run).

## The take

360 /glass frames + 360 /frame twins captured (MANIFEST_sha256.txt lists all
720 sha256s; sampled pairs verified distinct — motion is in the pixels).
Encoded: feature_walk.mp4 (judge artifact, 36.0 s at 10 fps) +
feature_walk_frame.mp4 (pixel-clean twin). 6 ordered judge keyframes
f000/f090/f164/f175/f265/f359 with full engine-truth readbacks
(keyframe_readback_f*.json). Capture wall time 1054.25 s for 360 frames —
the declared time-lapse property (prereg: capture-rate measured, never
hidden); engine-internal stride clock advanced 72.2 s over the stride
phase, i.e. ~19.7 real stride cycles are IN the movie.

## Blind judge

Spawn request posted to glm53-lead-02's mailbox (SIMPLE protocol: fresh
judge, the movie, the 6 ordered keyframes, three plain questions, zero
priming). Verdict mapping per prereg: stepping-in-place / no travel named
by the judge = F1 confirmed from the SEEING side; the judge's words are
recorded verbatim when they return.

## Claim-gate disclosure

This lane was parked ~3.2 h at the claim gate on a prior host
(capability_missing; every ~2.5 min retry refused; escalations posted) —
through no fault of the lane. This host resumed from the preserved scratch
(E:/ChimeraWork/evidence/w05-scratch/), claimed cleanly once qualified, then
waited ~1.2 h in the resource queue behind product-http-viewer-01 (holder
actively running; auto-promoted on their release at rev ~1276).

## DYAD VERDICT (SIMPLE protocol, lead-executed spawn 2026-09-12)

See DYAD_REPORT.txt (verbatim). The judge independently CONFIRMS falsifier
F1: marching in place, zero travel, feet pinned to one spot — the feature
is visually verified as stepping, and the root-translation engine-service
gap stands as the recorded honest partial. Bonus roadmap from the judge's
fakeness findings (backlog): arm counter-swing, torso bob/weight shift,
foot planting, reactive contact shadow, balance adjustment. The stride
phase visually read as a crouch — stride-lane followup finding.

Completion: judge spawn + assembly by glm53-lead-02 per mailbox 8c60f6b66263
(owner host ended after submit_review at rev 1279). Agent: glm53-lead-02
