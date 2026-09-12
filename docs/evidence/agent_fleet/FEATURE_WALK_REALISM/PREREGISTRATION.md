# PREREGISTRATION — feature-walk-realism-01

Written BEFORE any build, render, capture, or judgment, on base `31c5cfbb`
(task branch `astra/tasks/feature-walk-realism-01`, claim generation 1). No
measured actuals appear in this commit. Trailer: `Agent: subagent-worker-11`.
Commit-order note: this is the FIRST authored commit of the lane; the
dependency merge of `astra/tasks/feature-walk-01` (integrated as PR #108,
tip `fca093df`) lands as the SECOND commit — every number below was derived
by reading the ALREADY-INTEGRATED v1 evidence through git (`git show
astra/tasks/feature-walk-01:...`), not from any working-tree state.

## The product defect being answered (operator doctrine: visually verifiable)

The v1 walk judge (PR #108, `FEATURE_WALK/DYAD_REPORT.txt`) confirmed the
gait march but wrote the realism spec verbatim: *"The upper body is
unnaturally stiff: no weight shift, no pelvic rotation, no torso bob, and
the arms never counter-swing the way they do in a real walk."* The certified
stride pack moves exactly 4 of 28 joints (hip_L/R, knee_L/R — measured from
`FEATURE_WALK/stride_certified_pack.json`: every other column is 0.000
throughout the loop; wrists/ankles sit at a constant −3.043°). The defect is
UPPER-BODY DEATH, and the fix must ride the EXISTING gait march.

FEATURE: WALK REALISM — arms counter-swinging anti-phase to the legs, torso
bob synced to the step cycle, head stabilization, layered ON the gait march
through public routes. ZERO C++ edits.

## Rule 0 parts

**STATEMENT.** The walk reads dead because the pose data carries no upper
body; upper-body life can be composed into the pose data the gait plane
already owns, without touching the engine.

**PREDICTION (unmeasured at this commit).**
- P1 (packet primary): a blind judge, shown ONLY the v2 take, describes a
  MORE NATURAL walk than the v1 verdict — names the arms swinging (opposite
  the legs) and/or a visible body bob. The v1 verdict text is the baseline
  for MY analysis; the judge never sees v1.
- P2 (composition): the composed upper-body columns play LIVE on the stride
  clock — engine readbacks match the composed rows (arms anti-phase, spine
  nodding at 2× per stride cycle, neck cancelling the spine) — while the leg
  columns remain byte-identical to the certified pack.

**FALSIFIER (named before the run).**
- F-A (packet arm a): the judge still says stiff / no counter-swing. The
  lane records the verdict verbatim and the feature is NOT closed.
- F-B (packet arm b): the planes cannot compose — the composed upper-body
  columns never appear in the live readbacks (engine ignores them), so the
  realism layer is impossible without engine edits. Recorded as an
  engine-service gap with the exact ownership law quoted; NOT patched in C++.
- F-B-weak is expected and distinct: the ROUTE layer cannot compose
  (`/joint` edits on a playing stride) while the DATA layer does. That split
  is a FINDING to record, not a failure to hide — see the probes below.
- F-C: any C++ edit becomes necessary. Structurally excluded (architecture
  directive); if it fires the lane stops and records the gap.

## The pose-ownership law (read from engine source at base, verbatim pointers)

- `engine.cpp stride_tick()`: *"While active+playing, this lane owns the
  leg/face thetas; /joint edits and the show clock do not fight it"* — it
  writes ALL `j_n_joints_` thetas every frame into the same state lane.
- `engine.cpp frame()`: `stride_drives` skips BOTH legacy owners (*"the
  gait lane already wrote thetas this frame"*), so a `/joint` edit intent
  (`request_joint_edit` sets `joints_owner_=1`, `edit_pending_=true`) is
  consumed ONLY when the stride is not driving.
- The hinge path (CPG march) is an `else if` after the joints path: engaging
  an editor owner PREEMPTS the march. The two pose planes never run in one
  frame ("SEQUENTIALLY, never simultaneously", v1 prereg item 4).

**Derived consequence (before running anything):** at the ROUTE layer the
gait plane and the pose plane cannot mix — a playing stride overwrites every
`/joint` write, and a `/joint` owner freezes the march. The only composition
the contract offers is at the DATA layer: the stride pack is a Python-built
artifact uploaded via public `/stride_bin`, so the upper-body columns can be
composed INTO it. The v2 deliverable is exactly that composition; the two
probes below MEASURE and RECORD the route-layer gap so the finding is honest.

## The composition probes (run AFTER the 360-frame capture, so the take stays pure)

- **Probe A (stride vs /joint):** with the composed stride playing, POST
  `/joint {"joint":"elbow_L","theta":37.5}` then read `GET /joints` on 3
  consecutive frames. Predicted: theta stays at the stride value; the edit
  intent queues unconsumed (law above). Firing-counter: if theta reads
  37.5, the routes DO compose (F-B-weak falsified, even better).
- **Probe B (march vs /joint):** re-engage the CPG march
  (`/hinge_bin`+`/gait_bin`+`/gait on`), POST
  `/joint {"joint":"neck","theta":15}`, read knees + `steps_total` on 3
  consecutive frames. Predicted: the owner flips to edit, the hinge is
  preempted, the knee march freezes. Firing-counter: the march continues
  with the neck posed — planes compose at the route layer.

## The derivation (Rule 1) — every constant below was computed from prior
## committed evidence (certified pack + rig pack), zero taste numbers

**Sources (already integrated, read-only):**
`docs/evidence/agent_fleet/FEATURE_WALK/stride_certified_pack.json`
(sha256 883ed9d8…f50a, v1-gated) and `Saved/meshes/monkey_joints.bin`
(the JNT3 rig the engine itself loads).

**Cycle timing (measured from the pack):** dt = 1/60 s, 331 samples,
startup segment loop0 = 110 samples = 1.83196 s (= T_stance, LIPM), loop
span 220 samples = 3.66393 s = THE STRIDE CYCLE (pack `stride_t`). Two
lift events per cycle (knee_L peaks at 0.014 cyc, knee_R at 0.514 cyc —
measured extremums): the STEP is half a cycle, T_step = 1.83196 s, so
anything "synced to the step cycle" runs at 2× per stride loop.

**Rig facts (measured from the joints pack):** every limb joint axis is
+x on BOTH sides (shoulder/elbow/hip/knee; +θ swings the hanging-limb tip
POSTERIOR (−z), −θ ANTERIOR (+z) — Rodrigues probe, re-run at runtime and
recorded). Wrist/ankle axes are mirrored. Spine/neck axes +x with the
up-tip moving +z for +θ (forward nod). ROMs (ext,flex) deg: shoulder
[−149, 60], elbow [−145, 125], wrist [−30, 60], spine_lower
[−117.87, 152.51], spine_mid [−124.51, 126.17], spine_upper
[−169.73, 119.16], neck [−35.84, 130.23].

**1. ARM COUNTER-SWING (contralateral coordination, ROM-clipped mirror):**
the arm's peak swing coincides with the CONTRALATERAL leg's lift event;
waveform = that leg's own normalized knee waveform k̂ (measured, not a
sinusoid — the certified data's own lift shape, k̂_L peaks 0.014 cyc,
k̂_R peaks 0.514 cyc):
- θ_shoulder_L(φ) = −A_sh·k̂_R(φ)  (anterior peak at R's lift)
- θ_shoulder_R(φ) = −A_sh·k̂_L(φ)  (anterior peak at L's lift)
- θ_elbow_L(φ) = +A_el·k̂_R(φ);  θ_elbow_R(φ) = +A_el·k̂_L(φ)
  (posterior fold peaking with the same event — the marching-arm carry)
- amplitudes: A_sh = min(hip p2p 63.719°, shoulder flex bound 60°) = **60.0°**
  (girdle-to-girdle mirror: the forelimb swings as far as the hind hip is
  measured to swing, clipped to the rig's own bound); A_el = min(knee p2p
  148.730°, elbow flex bound 125°) = **125.0°** (joint-to-joint mirror,
  same clip rule). Range check: shoulder cols ∈ [−60, 0] ⊂ ROM; elbow cols
  ∈ [0, 125] ⊂ ROM (verified against the pack ROMs).
- θ_wrist_L/R = the ankle column copied exactly = **−3.0429° constant**
  (the certified ankle is locked; the mirror keeps the wrist locked).
  p2p of the certified ankle column measured 0.000000 — the copy is exact.

**2. TORSO/SPINE BOB (2× per cycle, amplitude from leg FK, not chosen):**
the body height above the stance foot is recomputed per sample by
forward kinematics of the stance leg (the straighter knee's side) from the
rig pivots + certified thetas: body_h ∈ [2.3641, 3.0825] (p2p 0.7184),
lowest at 0.487 cyc (the R lift), highest at 0.746 cyc. The trunk pitch
that renders this bob:
- β(φ) = (mean(body_h) − body_h(φ)) / L_spine,  L_spine = 4.1248
  (spine_lower→neck chain length from the rig pivots)
- β ∈ [−3.256°, +6.723°]; positive = forward nod at the crouch (support
  shortens). Split EQUALLY over the three spine joints (the chain shares
  the correction): θ_spine_lower = θ_spine_mid = θ_spine_upper = β/3
  ∈ [−1.085°, +2.241°]. No ROM clipping fires.
- the stance foot itself lifts up to 1.051 above the ground plane in the
  certified rows — the KNOWN v1 "feet hover/slide" defect (v1 judge), out
  of scope here (foot planting is a separate roadmap item); recorded, not fixed.

**3. HEAD STABILIZATION (zero-parameter law):** the head stays level in
space: θ_neck(φ) = −(θ_spine_lower+θ_spine_mid+θ_spine_upper) = −β(φ)
∈ [−6.723°, +3.256°] ⊂ neck ROM. The neck cancels the whole spine pitch,
so the chest rocks with the steps and the head does not nod.

**4. EVERYTHING ELSE IS UNTOUCHED:** hip_L/R, knee_L/R, ankle_L/R columns
byte-identical to the certified pack; all face/tail/ear/lid/brow/mouth/jaw
columns stay exactly 0. 19 of 28 columns untouched, 9 composed.

**The take schedule is INHERITED VERBATIM from FEATURE_WALK v1** (same
camera cam_radius = 3.4×extent, cam_theta 0.5, cam_phi 0.35 set once; same
10 fps, same 360 frames; f000–014 REST, f015–164 CPG MARCH via
`/hinge_bin`+`/gait_bin`+`/gait on` exactly as v1 drove it, f165–174
SETTLE, f175–354 the stride phase — now the COMPOSED pack — f355–359 HOLD).
The only changed variable vs v1 is the upper-body content of the stride
rows; that is what makes the judge comparison honest.

## Gates (declared before the run; *.txt records, sha256 manifests)

- G1 MARCH: steps_total strictly increasing across march readbacks (v1 G1 twin).
- G2 STRIDE LIVE: /stride active+playing through the phase; t advances past loop0·dt.
- G3 COMPOSITION + ANTI-PHASE: at ≥3 stride keyframes the engine-readback
  arm/spine/neck thetas match the composed row at the same loop phase within
  0.5° (the composed columns are LIVE — P2), and |θ_shoulder_L| > 30° only
  near R's lift while θ_shoulder_R ≈ 0 there (and mirrored) — arms alternate.
- G4 BOB: |θ_neck| ≥ 2° at ≥1 stride keyframe, with sign flip across the two
  lift keyframes (2× per cycle, step-synced).
- G5 HEAD LEVEL: θ_neck = −Σθ_spine within 0.1° at every stride readback.
- G6 LEGS CERTIFIED: leg-column bytes identical (sha256 over the 6 leg
  columns of both packs) AND readback leg thetas match the certified row at
  the same loop phase within 0.5°.
- G7 CAMERA FIXITY: /project of the knee_R pivot constant to ≤ 0.5 px across
  all keyframes (v1 G6 twin).
- PROBE A/B actuals recorded (the route-layer composition finding).
- Blind judge: SIMPLE protocol via glm53-lead-02's mailbox — fresh judge,
  the v2 movie + 6 ordered keyframes only, three plain questions, zero
  priming. The judge never sees v1 or this file. Verdict recorded verbatim.

## Scope and resources

Scopes: `tools/product_features_walk` + `docs/evidence/agent_fleet/FEATURE_WALK_REALISM`.
Private build under `.tmp/`; fleet ports (8105/8115/8125 candidates, first
free wins, recorded); resources rtx4090 + engine_demo requested at claim
generation 1 (granted rev 1321) BEFORE any hardware work. Full-resolution
proof copies to `Desktop/CHIMERA_PROOF/FEATURE_walk_realism/`. Evidence
records as *.txt; every commit trailer `Agent: subagent-worker-11`.
