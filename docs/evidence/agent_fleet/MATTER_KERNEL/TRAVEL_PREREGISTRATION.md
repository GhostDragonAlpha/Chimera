# TRAVEL PREREGISTRATION — ankle-pin flex (Appliance 2, stage 1)

Rule 0: statement, derivation, predictions, falsifier — BEFORE the code.

## STATEMENT

A membrane foot travels WITH its ankle pin: a flex intent rotates the
foot's vertices about the ankle pivot (the collar-ring center, axis X),
and flex 0 restores the exact authored base positions. The foot is not
re-drawn and not re-authored by the pose — the SAME membrane grain moves.

## DERIVATION

- Pivot: the foot's collar-ring center, computed at tick init from the
  foot's own vertices (mean of top-ring region: y >= 0.25) — measured
  from the membrane, not hand-placed.
- Rotation: rigid rotation about the X axis through the pivot by the
  flex angle (left and right feet independent). Rigid = every vertex
  keeps its distance to the pivot; the membrane does not stretch.
- Driver: POST /tick_flex {"deg_L": a, "deg_R": b} — a POSE INTENT.
  Poses are intents (the studio's EDIT pose is the precedent); the tick
  applies them per frame. Flex 0 is the authored rest.
- The sole leaves the ground under flex (rotation lifts/pushes the
  sole line) — that is EXPECTED at this stage: contact under flex is
  P5's press law after the contact solver lands (OPEN, named).

## PREDICTIONS

P1. Flex +25 deg on the left foot: the foot's vertices rotate about the
    measured pivot; the toe line RISES (or digs, by sign) while the
    collar stays at the pivot; the right foot does not move.
P2. Reversibility: flex back to 0 -> every vertex returns to its base
    position to within 1e-4 (the authored membrane is exactly restored).
P3. Rigid: all vertices keep their distance to the pivot within 1e-3.
P4. Independence: flexing L does not move R's vertices (separate pins).
P5. Visible: /frame pictures show the angled foot; before/after land in
    CHIMERA_PROOF.

## FALSIFIER

Any bar fails, OR the membrane stretches under flex (non-rigid), OR the
rest position drifts, OR the pose re-authors the geometry. On failure
the successor: the rotation center is wrong (measure the true hinge
line from the skin's ankle), recalibrate, re-run.

## OPEN (named)

- Skeleton integration: flex driven BY the engine's live joint state
  (the stride/EDIT pose) instead of posted intents — needs the joints
  pack rebuilt for the membrane scene (the current pack binds the old
  18,459-vert skin). Named next stage; the intent driver proves the
  mechanism now.
- Sole contact under flex (P5 of the FEET prereg) — after the contact
  solver.

## RUN RECORD (2026-09-13, live engine, tick binary with travel)

- P1 flex+travel: PASS — /tick_flex {deg_L: 25} rotates the left foot
  about its measured collar pivot; 50,762 pixels changed in /frame;
  the right foot did not move (P4 independence holds).
- P2 reversibility: PASS EXACTLY — flex 0 restores the authored base
  with max pixel diff 0 (pixel-for-pixel, not approximately).
- P3 rigid: PASS by construction (rigid rotation about the pivot) and
  visually (the wedge reads angled, not stretched).
- P5 visible: PASS — travel_flex_L25.png / travel_rest.png in
  CHIMERA_PROOF/FEET.
- OPEN (unchanged): skeleton integration (flex driven by the live
  joint state — needs the joints pack rebuilt for the membrane scene);
  sole contact under flex (the press-law contact solver).
