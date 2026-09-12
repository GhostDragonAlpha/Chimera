# PREREGISTRATION — product-motion-sweep-01

Written BEFORE any build, render, capture, or judgment, on base `cb874a3a`
(task branch `astra/tasks/product-motion-sweep-01`, slot-04, claim generation 1).
No measured actuals appear in this commit. Trailer: `Agent: subagent-worker-03`.

## The product defect being answered (PR #97 blind dyad judge, verbatim)

> "(a) only the right arm visibly moves in these frames - the other 20+ joints
> never do, so the "all joints exercised" claim is carried by UI text and reel
> thumbnails, not observable motion"

Context: 28 named joints live in the rig; the rig carries leg/spine/tail/face
chains. The judge saw ONE region move. This lane authors the missing demo
content: one continuous scripted interaction that makes multi-region motion
OBSERVABLE.

## Rule 0 parts

**STATEMENT.** Today's engine API can drive visibly coupled multi-joint motion
in one take; the product defect is that no authored interaction demonstrates
it.

**PREDICTION (unmeasured at this commit).** A blind judge given 6 ordered
keyframes of the take names visible motion in **>= 3 body regions** without
prompting.

**FALSIFIER (named before the run).** The lane FAILS — and the product defect
stands confirmed as an API capability defect, recorded honestly — if the blind
judge names exactly ONE moving region (the PR #97 outcome repeated), OR if the
script requires engine-source edits to work. The engine-source half is
structurally excluded and checked: the script may only speak the engine's
public HTTP surface (POST /joint, POST /camera, POST /joints_bin, GET /joints,
GET /scene, GET /glass, GET /frame) plus the two harness wrappers the accepted
PR #97 probe used (tools/engine_demo.py launch/stop; cpp_bridge.load_mesh_bin —
itself POST /mesh_bin — and cpp_bridge.encode_movie). Any engine-source edit
inside this lane is forbidden and would be a finding, not a fix.

Exactly 2 regions named = prediction NOT met but falsifier NOT fired: recorded
as a partial result; the product defect remains open. Acceptance stays
NOT_CLAIMED beyond the measured verdict.

## Declared inputs (read, not measured by this lane)

Rig + assets IDENTICAL to PR #97: mesh `Saved/meshes/monkey_birth.bin` via
`cpp_bridge.load_mesh_bin`, rig pack `Saved/meshes/monkey_joints.bin` (JNT3,
nv 18459, nj 28) via `POST /joints_bin`; engine requires the mesh before the
pack; both loaded on MY private engine instance. The 28 joint names were
recorded from the live rig doc (`GET /joints`) by PR #97
(render_records.json, `rig.doc`); the per-joint ROM windows below were parsed
from the committed pack's ROM array with the canonical loader
(`tools/gait_mirror.py::load_pack`), the same fields `GET /joints` returns as
`ext`/`flex`. Rest theta is 0 for every joint; the engine clamps to the pack
ROM regardless of what is posted. The script re-reads `GET /joints` at runtime
and records any name/ROM deviation from this table as a finding (substitution
law of the PR #97 probe applies verbatim; none is expected).

### Scripted joint set — 13 joints, 4 body regions (arm + leg + spine + tail)

Regions as the packet names them: arm + leg + spine or tail — this take uses
all four non-face regions. Face joints (ear/lid/brow/mouth, 8 of the 28) are
EXCLUDED: at the framing that fits the whole body the face joints are
sub-legible (the PR #97 judge could not judge face joints even at the probe's
tighter framing). This exclusion is the packet's anticipated face limitation,
recorded here.

| joint | ext (deg) | flex (deg) | region | fraction | peak theta (deg) |
|---|---|---|---|---|---|
| shoulder_L | -149.0 | 60.0 | arm | 0.6 | 36.0 |
| elbow_L | -145.0 | 125.0 | arm | 0.6 | 75.0 |
| shoulder_R | -149.0 | 60.0 | arm | 0.6 | 36.0 |
| elbow_R | -145.0 | 125.0 | arm | 0.6 | 75.0 |
| hip_L | -159.0 | 119.0 | leg | 0.6 | 71.4 |
| knee_L | -131.0 | 147.0 | leg | 0.6 | 88.2 |
| hip_R | -159.0 | 119.0 | leg | 0.6 | 71.4 |
| knee_R | -131.0 | 147.0 | leg | 0.6 | 88.2 |
| spine_mid | -124.5 | 126.2 | spine | 0.3 | 37.86 |
| spine_upper | -169.7 | 119.2 | spine | 0.3 | 35.76 |
| tail_base | -30.0 | 87.1 | tail | 0.6 | 52.26 |
| tail_mid | -139.1 | 138.7 | tail | 0.6 | 83.22 |
| tail_tip | -45.0 | 45.0 | tail | 0.6 | 27.0 |

### Derivation of the two numbers that are not copies

- **Fraction 0.6 on limb and tail joints** is the PR #97-measured visible
  amplitude on this exact rig and camera: 0.6 x flex from rest put
  shoulder_R/elbow_R at 36/75 deg and the judge SAW that motion (the finding
  is that nothing ELSE moved). It is a calibration reuse, not a taste choice.
- **Fraction 0.3 on the two spine bands** is derived from a frame-fit bound:
  spine_mid and spine_upper compose through FK (parent map: upper -> mid ->
  lower-root), so the head chain's composed bend at peak is the SUM of the two
  scripted bends. The bound: composed bend <= 90 deg (beyond 90 deg the head
  axis points below the withers and the head leaves the fixed frame — the
  exact PR #97 framing defect). 0.3 x (126.2 + 119.2) = 73.6 <= 90; the
  uniform 0.6 would give 147.2 > 90. The bound, not preference, sets 0.3.
- **Sign law: one, uniform.** Every scripted joint targets the +flex side of
  ROM (every one of the 28 joints has flex > 0 in the pack) — the side and
  sign the probe validated as visible. No per-joint sign taste. If a sampled
  keyframe shows a limb intersecting the floor or the body, that is recorded
  as a cosmetic finding from the keyframes; visibility, not anatomy, carries
  the verdict.

## The interaction — one continuous take, frame-indexed at 10 fps, 70 frames (7.0 s)

One script, one camera, one continuous capture; regions move in SEPARATELY
READABLE time windows (the PR #97 lesson: simultaneous motion is unreadable;
sequential phases make each region nameable), then hold together, then return
together. s(t) is the smoothstep `t*t*(3-2t)` clamped to [0,1] (the probe's
validated ramp). Wave assignment: s_arm -> both shoulders+elbows; s_legL ->
hip_L+knee_L; s_legR -> hip_R+knee_R; s_spine -> spine_mid+spine_upper;
s_tail -> tail_base+tail_mid+tail_tip.

| frames | phase | law |
|---|---|---|
| f000–f009 | REST | all s = 0 |
| f010–f019 | ARMS-RISE | s_arm = s((i-9)/10); others 0 |
| f020–f029 | LEGS-STEP | s_legL = s((i-19)/6); s_legR = s((i-23)/6) — L leads, R follows +4 frames (0.4 s), a visible alternation |
| f030–f041 | SPINE-TAIL-WAVE | s_spine = s((i-29)/10); s_tail = s((i-31)/9) — distal tail lags proximal spine (follow-through) |
| f041–f049 | FULL-HOLD | every s = 1 — the frame where all 13 joints are simultaneously at peak |
| f050–f069 | RESPONSE | every s = 1 - s((i-49)/20) — the whole pose returns to rest |

Each frame: POST `/joint` per scripted joint (theta in degrees, the probe's
unit), then GET `/glass` (composited product surface, the judge artifact
channel) and GET `/frame` (pixel-clean twin, retained). 13 POSTs + 2 GETs per
frame, 70 frames, no other engine interaction.

## Camera (one declared change from the probe, derived from a measured defect)

Fixed for the whole take (one variable: the pose), set ONCE before f000 via
POST `/camera`: `cam_radius = 3.4 x extent`, `cam_theta = 0.5`,
`cam_phi = 0.35`, extent parsed from the GET /scene body row exactly as the
probe parses it (fallback 10.0). The probe's 2.7 x extent cropped the head in
every frame (PR #97 judge defect 3); this take must show arm AND leg AND
spine AND tail simultaneously, and the radius increase is the minimal
correction on the same public endpoint. theta/phi keep the probe's validated
3/4 view unchanged. If the subject still crops at any sampled keyframe, that
is a recorded finding — no silent retune.

## Sampling plan (declared before the run)

- **Judge keyframes — exactly 6:** f000 (rest), f019 (arms at peak, nothing
  else moving), f030 (both legs at peak, spine barely started), f041
  (spine+tail at peak, everything held), f049 (full hold), f069 (returned to
  rest). The six are the ordered-frames dyad artifact.
- **Engine-truth readback:** at each of the 6 keyframes, GET `/joints` and
  record the theta of all 28 joints -> `joint_thetas_keyframes.txt`. Gate
  (declared): at f049 every one of the 13 scripted joints must read theta
  >= 50% of its declared peak. If any fails, the "all joints exercised" claim
  is NOT demonstrated even if the judge passes — recorded honestly.
- **Records:** render_records.json/.txt in the probe's format (launch pid,
  exe sha256, load verdicts, per-keyframe thetas, encode hashes).
- **Movie:** `cpp_bridge.encode_movie` at 10 fps over the 70 /glass frames ->
  `product_motion_sweep.mp4`; the /frame twin encoded separately. Both + all
  140 PNGs retained in this directory.

## The judge spec (declared blind — the PR #97 protocol, unchanged)

- review_type `ordered_frames`; the six PNGs with sha256, in order.
- The judge is told the same class of physical context the probe's spec gave
  (a desktop application window, a creature on a grid floor, frames IN ORDER
  from a 7.0-second clip at 10 fps) and NOTHING else: not the joint count,
  not the regions scripted, not the defect under test, not any expected-answer
  string (the r7 law). On-screen application text may be read; numbers are
  observations, not measurements.
- Questions (verbatim, the probe's validated non-leading set):
  1. Describe what happens across the frames, in order.
  2. What kind of motion or behavior is being demonstrated — name it as you
     would to a friend.
  3. If a non-physicist watched this clip, what ONE sentence would you tell
     them about what they just learned?
  4. Is anything unclear, ambiguous, or unconvincing about the sequence?

## Acceptance rubric (declared BEFORE judging)

Region classes counted from the judge's Q1/Q2 words: **ARM** (any shoulder/
elbow/arm raise/wave), **LEG** (any hip/knee/leg step/kick), **SPINE**
(torso/back bend), **TAIL** (tail curl/lash/wag). HEAD/FACE counts only if
named; face is NOT scripted (limitation above) — a face claim is recorded
verbatim and scored as unscripted, not as a hit.

- **PREDICTION CONFIRMED** iff the judge names visible motion in >= 3 of the
  four classes, unprompted, in the answers to Q1/Q2.
- **FALSIFIER FIRED** iff the judge names exactly ONE moving region class —
  or the take is found to require engine-source edits (structurally excluded;
  see the import-surface check).
- **Exactly 2 classes:** prediction not met, falsifier not fired; recorded as
  PARTIAL; the product defect stays open.
- The judge's Q4 critiques are recorded verbatim as the gap list (the PR #97
  assembly pattern) — they are findings, never paraphrased away.
- Agreement is INCONCLUSIVE, never acceptance. If the judge cannot consume
  the frames, ONE rerun with the same spec (transport retry only), then the
  refusal is the result of record.

## Engine / resource / scope discipline

rtx4090 + engine_demo acquired through the session BEFORE any engine run
(granted rev 1089, request 87a8e6f67390605b, generation 1). Private build
under the slot's `.tmp/engine_build/` — `ChimeraEngine/engine/build/` and the
operator checkout NEVER touched. Engine port: the slot-04 candidate 8104 (a
candidate, not a reservation — availability checked, collision is a named
refusal); runtime CWD a fresh `.tmp/engine_runtime/product-motion-sweep-01/`;
`--no-restore`; executable + SPIR-V hashes recorded before any capture.
Process cleanup PID-scoped and self-created only; Alan's engine on 8080 is
never touched. Evidence outputs are `*.txt` (never `*.log`); retained
failures; every commit on this branch carries the trailer
`Agent: subagent-worker-03`.
