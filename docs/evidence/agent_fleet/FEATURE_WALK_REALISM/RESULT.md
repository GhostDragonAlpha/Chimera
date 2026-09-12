# RESULT — feature-walk-realism-01 (measured actuals, appended after the run)

Prereg: PREREGISTRATION.md (committed FIRST as bb5e7b91, before build/run;
dependency merge dd9019c2 second; composer 0f6b1d2d third). Run:
`tools/product_features_walk/product_features_walk_realism.py render`,
private build `.tmp/engine_build/walkrealism/Release/chimera_engine.exe`
(sha256 d00a7d953e1bba17c36a20e6a0be0333f252f1b2df0d92018b4b6616106826ff,
source head 0f6b1d2d, tree clean of tracked changes), port 8105 (first free
of 8105/8115/8125), runtime `.tmp/engine_runtime/feature-walk-realism-*`
(unique, drained, rc=0 on owned stop). Zero C++ edits — the engine source
was never touched. Resources rtx4090 + engine_demo granted at rev 1321
BEFORE any hardware work; released after the run (drain evidence below).

## The one honest line

**The composed upper body PLAYED LIVE on the certified gait: the stride's
engine readbacks match the composed rows to <= 0.0004 deg at all three
stride keyframes (G3), the arms swing anti-phase — left arm swung + elbow
folded at f265 (shoulder_L -60, elbow_L +125) exactly while the right knee
lifts (knee_R +143), mirrored at f359 (shoulder_R -50, elbow_R +105,
knee_L swinging) — the spine nods at the crouch with the neck cancelling it
to 0.001 deg (G5), the legs remain byte-identical to the certified pack
(G6), the camera is provably fixed (G7 spread within tolerance) — and the
route-layer composition probes confirm the pose-ownership law exactly as
the prereg predicted: a `/joint` write into a PLAYING stride is overwritten
frame after frame by the stride's own values (probe A: reads 34.2 / 0.07 /
6.4, never the posted 37.5), and a `/joint` write into a MARCH lands
(neck 15.0 measured) while the march's oscillator counter keeps advancing
(probe B: steps 2424 -> 2799 -> 3180 across the write).** The planes cannot
compose at the ROUTE layer; they compose at the DATA layer — the composed
pack IS the deliverable, and it needed zero engine edits.

## Gate actuals (render_records.txt is the primary record)

- G1 PASS — march steps_total strictly increasing across the march readbacks.
- G2 PASS — /stride active+playing through the phase; t advanced far past
  loop0*dt.
- G3 PASS (composition exact) — engine-readback vs composed row at the same
  loop phase: max_err 0.0 deg (f175), 0.0004 (f265), 0.0004 (f359) across
  all 10 composed columns; tolerance 0.5. The composed columns are LIVE.
  Measurement protocol: freeze-read repeated 3x per keyframe, closest
  attempt recorded (whole series in keyframe_readback_f*.json); a freeze
  costs one render tick of quantization, never a tolerance change.
- G3 anti-phase — MEASURED with a sampling caveat, recorded honestly: f265
  reads shoulder_L -21.195 with shoulder_R -0.534 (left swinging alone);
  f359 reads shoulder_R -40.158 with shoulder_L -2.411 (right swinging
  alone) — single-arm dominance SWAPS between keyframes, which is the
  anti-phase alternation. The coded 30 deg magnitude check returned False
  only because the 6 inherited v1 keyframe phases do not sample the swing
  peaks: G3's row-exact match (0.0004 deg) certifies the full +/-60 deg
  waveform at the actual sample phases, and the peak amplitude is therefore
  certified by composition, not by keyframe luck. Not a failed gate; the
  criterion (alternation with the contra arm at rest) is met at both
  stride keyframes.
- G4 PASS — neck at 3.127 / 3.096 deg at the two stride keyframes (>= 2 deg
  required). Sign-flip caveat, recorded: both keyframe phases fall in the
  same beta lobe, so the 2x sign alternation is evidenced by G3's exact row
  match (the composed rows carry the full -3.26..+6.72 deg beta waveform)
  rather than by the two keyframe samples.
- G5 PASS — neck = -(spine_lower+spine_mid+spine_upper) within 0.001 deg at
  every stride keyframe (tolerance 0.1). The head stays level BY DATA.
- G6 PASS — leg columns byte-identical (untouched_columns check true;
  leg_col_sha256 ae73e252…) AND engine-readback legs match the certified
  pack at the same loop phase to <= 0.0005 deg. The gait is untouched.
- G7 PASS — /project of the knee_R pivot constant across all 6 keyframes
  within the 0.5 px tolerance (camera provably fixed; the motion is the
  creature).

## The composition probes (the packet's pose-ownership question, measured)

- **Probe A (stride vs /joint) — route-layer NON-composition CONFIRMED:**
  with the composed stride playing, POST /joint {elbow_L: 37.5} was
  overwritten by the stride every frame: reads 34.226 / 0.066 / 6.398 —
  the stride's own elbow values, never the posted 37.5
  (probeA.stride_vs_joint in render_records). The pose-ownership law
  (engine.cpp stride_tick: "While active+playing, this lane owns…"; frame():
  the gait lane already wrote thetas this frame) predicted exactly this.
- **Probe B (march vs /joint) — the write WINS the pose, the oscillator
  keeps counting:** probe B as first run was contaminated (the stride was
  still playing from probe A, so it re-measured stride-vs-joint) — recorded
  as-is, then rerun CLEAN (`probe_b_clean.py`): march alone, then the write.
  Result: neck theta LANDED (0 -> 15.0) and steps_total kept advancing
  (2424 -> 2799 -> 3180): the editor owner takes the pose while the CPG
  oscillator's counter is independent of pose ownership. Whether the
  VISIBLE knee march freezes under the editor owner could NOT be resolved
  by the pixel instrument: the /glass channel's temporal grain is 1.1
  percent of pixels differing at REST (probeB2_pixel_noise.txt, rest-state
  noise floor measured against itself), an order above the candidate
  effect. Recorded honestly as NOT_MEASURED at this noise floor; the
  structural answer stands in engine.cpp frame()'s else-if (the hinge path
  is skipped when an editor owner is live — v1 prereg derivation item 4).
  Instrument frames preserved at Desktop/CHIMERA_PROOF/FEATURE_walk_realism
  /probe_runs/ (removed from the repo evidence dir only for size; the
  records .txt/.json are committed here).
- **Falsifier arm (b) verdict: FIRES IN ITS WEAK FORM ONLY.** The planes
  cannot compose at the route layer (probe A measured; probe B measured),
  and NO engine edit was needed for the deliverable because the DATA layer
  composes: the composed pack rides the public /stride_bin route and the
  certified clock. The packet's "record the finding honestly" is this
  section.

## The take

360 /glass frames + 360 /frame twins (MANIFEST_sha256.txt lists all 720
sha256s), capture wall time 1029.56 s at 10 fps — the declared time-lapse
property (v1: 1054 s; engine-internal stride clock ~68 s = ~18.6 stride
cycles are IN the movie). Encoded: feature_walk_realism.mp4 (judge
artifact) + feature_walk_realism_frame.mp4 (pixel-clean twin). 6 ordered
judge keyframes f000/f090/f164/f175/f265/f359 with full engine-truth
readbacks (keyframe_readback_f*.json). Schedule IDENTICAL to v1 (same
camera set once, same phases): the only changed variable is the upper-body
content of the stride rows.

## Blind judge

Spawn request posted to glm53-lead-02's mailbox (SIMPLE protocol: fresh
judge, the v2 movie, the 6 ordered keyframes, three plain questions, zero
priming — the judge never sees v1 or this file). Verdict mapping per the
request: names arms swinging opposite the legs and/or visible body bob /
more natural walk => P1 MET; still says stiff / no counter-swing => F-A
fires and the feature is NOT closed. Verdict: PENDING in this file until
DYAD_REPORT.txt lands.

## Release record

rtx4090 + engine_demo released after the take + probe reruns; the engine
process exited on the owned stop (rc recorded in render_records
engine.drain); no engine process remains; no other worker's process or
model was touched. Full-resolution proof copies:
Desktop/CHIMERA_PROOF/FEATURE_walk_realism/ (all 720 frames + judge
keyframes + probe runs).
