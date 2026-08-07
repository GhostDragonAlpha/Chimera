# theSkeleton — spec draft (operator review)

*2026-08-07. Read-only draft. Does not run. Builds on theLeg v2 verdict
and the settled membranes in docs/THE_CATEGORIES.md. Drafted by a
planning agent; leg v3's verdict landed after this draft — see the
note at the bottom.*

## 0. STATEMENT

A skeleton, in this kernel, is not a collection of bones; it is a grounded
frame of hollow-tube bones joined by captured saddles, whose geometry is
the primary stability membrane — muscles are routed through it, not propped
against it, and the frame's own anchored shape decides which configurations
are stable.

## 1. DEPENDENCY TABLE

| part | supplied by | settled law it carries |
|---|---|---|
| hollow-tube bones | theBone / theLever v5 | bone is a plastic-set compression column; a 1-grain-thick 4×4 shell with 2×2 void carries stiffness without the solid arm's weight |
| captured saddle (fulcrum cheeks) | theJoint v2 / theLever v6 | cushion contact is a bondless fulcrum; a saddle pinned to the parent bone allows rotation only and does not roll away |
| rope tendon | theTendon v4 + theLeg v3 | tendon is pull-only; a single-file chain crumples when slack and never routes compression |
| anchored muscle droplet | theMuscle + theLeg v2 | a free muscle climbs to the bone and becomes a prop; the origin must be pinned outside the moving arc |
| full-arc static gate | theLeg v3 | R_true(theta) must be priced on both sides of the print pose out to both derived end-stops; unpriced arc is where the machine lives |

## 2. FIRST PRINT PROPOSAL: theSpine (minimal two-vertebra print)

Why the spine first: the pelvis branches; branching needs the branched-chain
membrane, which is not settled. The spine is a serial chain, so each joint
inherits the single-saddle mechanics proven in theLeg, and the frame claim
reduces to "a chain of anchored saddles carries static stability." We start
with two vertebrae; more links wait on this print.

Bodies and counts:
1. Pinned ground plate: 6×6 lattice at z = 0 (36 grains, grain_id = -1).
2. Sacrum (base vertebra): 4×4×8 hollow tube, 1-grain shell, 2×2 void,
   printed vertical. 8 rings × 12 grains = 96 grains (grain_id = 0).
   Bottom face seated d_eq above the plate; bottom plate of sacrum pinned
   to ground plate.
3. Captured saddle on sacrum top: 4×4×4 block + one-grain-thick cheeks
   (4×1×3 each side), pinned to the sacrum (64 + 24 = 88 grains,
   grain_id = 1). The block is part of the sacrum; the cheeks rise from it
   to capture the lumbar vertebra.
4. Lumbar vertebra: 4×4×8 hollow tube, 96 grains (grain_id = 2), seated
   d_eq above the saddle block. Rotation about the saddle is the only free
   degree of freedom.
5. Anchored muscle droplet: 4³ = 64 grains (grain_id = 3), pinned in a well
   beside the sacrum base, outside the lumbar's swing arc.
6. Rope tendon: single-file chain from droplet apex to the lumbar far-end
   underside (grain_id = 4). Length derived so the rope is taut at the
   print pose and can crumple into the well when the muscle wins.
7. Load block: 4³ = 64 grains (grain_id = 5), resting d_eq above the lumbar
   far end.

All separations are cushion spacing 0.05 or d_eq = 0.0484; counts follow
the lever v6 / leg v2 conventions.

What is pinned:
- Ground plate (world frame).
- Sacrum bottom plate (to ground plate) and the saddle block+cheeks
  (to sacrum).
- Muscle droplet (to well floor).

What is derived:
- Saddle contact point x_s on the sacrum top: bisected so that
  min_R_taut(theta) >= 1.0 over the muscle-side arc and max_R_slack(theta)
  <= 1.0 over the load-side arc, with both arcs ending at derived
  geometric stops.
- Rope length: from droplet apex to lumbar attachment at print pose, plus
  the derived slack allowance (never chosen; set by the requirement that
  the rope is straight at print and does not compress).
- Well depth: bisected so the lumbar tip's full arc stays at least d_eq
  from the droplet (same derivation as theLeg v2 well).

Static gate:
The full-arc gate from theLeg v3: for each candidate saddle contact,
compute R_true(theta) on recorded positions across the reachable arc on
both sides of the print pose. Main print: leftmost contact where
min_R_taut >= 1.0 on the muscle side and R_true stays above 1 out to the
derived muscle-side stop. Control print: contact where R_slack(0) in
[0.5, 1.0] and R_slack(theta) <= 1.0 over the load-side arc. The sacrum
remains vertical and pinned; the lumbar rotates only.

## 3. PREDICTION AND FALSIFIERS

Prediction: because the sacrum is anchored and the saddle captures the
lumbar, the frame's geometry (not a wandering muscle) sets the stable
configuration; the main print settles muscle-side, the control settles
load-side, and the rope stays tension-only.

"Stable" in tick-table terms:
- Settled angle stays within a derived band of ±2° around the
  static-torque prediction for the last 60% of the run.
- No reversal spike: the angular velocity sign does not flip after the
  first 10% of the run.
- No rope compression events: rope axial force stays positive (or, if
  slack, the chain crumples with at least one kink angle > 90° and zero
  compressive thrust).
- Sacrum pinned base migration < 0.5 d_eq.

Falsifiers:
(a) LIFT — main: the lumbar far-end height rises at least two lattice
    steps above print through the muscle-side arc while the saddle holds
    (perch gap stays within the seated band [S_WALL, d_eq] or recovers
    within the joint v2 recovery window).
(b) HOLD — control: the lumbar far-end never rises more than one lattice
    step above print through the whole run.
(c) BALANCE — settled sign matches the full-arc static torque: main
    settles on the muscle side, control on the load side; settled angle
    within ±2° of the static prediction.
(d) INTEGRITY — each vertebra remains one cluster; the saddle block and
    sacrum stay pinned; the rope remains one chain (cluster count 1) when
    taut and fragments only by crumpling, not rupture, when slack.
(e) SLACK — rope never transmits compression: in main, no sample shows
    rope force negative; in control, when the rope goes slack it
    crumples/folds with at least one kink angle > 90° and does not prop
    the lumbar.
(f) FRAME — the sacrum does not tilt or migrate: its base plate gap to
    ground stays within the seated band and its top axis angle stays
    within ±2° of vertical.

## 4. RISKS

1. Relaxation lurch at neutral balance. The leg v2 print at R_true ≈ 1.003
   was knocked load-down by the tick-400 relaxation spike. In a multi-bone
   frame the same lurch can propagate through the chain. Answer: the
   full-arc gate must keep R_true well above 1 on the muscle side and well
   below 1 on the load side; "neutral" is not an allowed saddle placement.

2. Rope crush/prop. The leg v2 rigid rod crushed under +17° and became a
   strut. A single-file rope is supposed to crumple instead, but if the
   rope is too short or the well too shallow it can jam between droplet
   and bone. Answer: theTendon law (tension only) plus the sheet law
   (crumpling is the slack phase); the rope length and well depth must be
   derived to leave slack volume.

3. Unpriced arc regions. The leg v2 gate priced only [0, theta_stop] and
   the machine settled on the unpriced load side. In the spine, each extra
   joint adds another dimension to the reachable space. Answer: theLeg v3
   full-arc gate prices both sides of each joint; the first print keeps
   only one joint so the arc remains 1-D.

4. Base-anchor migration. If the sacrum's pinned seat fails under the
   lumbar's torque, the whole frame walks. Answer: theBone law — a pinned
   compression column holds its seat; the sacrum bottom plate area is
   4×4, the same cross-section that held bone's preload cycles.

## 5. WHAT THIS DRAFT DOES NOT DECIDE

- Whether theLeg v3's rope-tendon + full-arc gate actually settles
  muscle-side. This draft assumes it does; if v3 fails, the skeleton's
  claim moves up one level and the frame must carry stability by geometry
  alone.
- The exact single-file rope construction: count, spacing, and crumpling
  metric. These are theLeg v3's print decisions.
- The multi-joint extension: three or more vertebrae introduce sequential
  error and a higher-dimensional arc space. This draft does not specify
  how to gate a chain; that waits on the two-vertebra result.
- Whether the spine needs an antagonist pair. The first print uses one
  muscle and one rope; the opposite-side stabilizer is the frame itself.
  If the frame cannot hold without an antagonist, that becomes a
  successor membrane.
- The pelvis: branching is explicitly out of scope until branched chains
  are settled.

---

## POST-DRAFT NOTE (2026-08-07, after theLeg v3 verdict)

theLeg v3 landed as this draft was written, and it changes two
assumptions above:

1. **The full-arc gate REFUSED** at the leg scale — no contact and no
   droplet size in {4,5,6} gives min_R_taut >= 1 across the full arc.
   Section 2's static gate inherits that refusal; the skeleton print
   must expect the gate to refuse and must decide in advance what a
   frame-first build does when muscle-dominance is unachievable. This
   is now the draft's hardest open problem, not a risk.
2. **The cheek saddle is escaped upward** (leg v3: gap 0.21, arm lifted
   off the perch and the machine settled off-saddle). The cheeks in
   section 2 (item 3) are an OPEN capture; theLeg v3 names the socket
   (theJoint v2's capture, which self-reduces) as the successor
   standard. The spine print should price the joint-line socket
   geometry, not the lever-line cheeks, before any build.

*Draft ends. No run, no code, no commit.*
