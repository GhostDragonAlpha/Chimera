# THE LEG PREREGISTRATION — a hinged membrane chain (Appliance 3)

Rule 0: statement, derivation, predictions, falsifier — BEFORE the code.
The operator's law this appliance embodies: THIGH IS A MEMBRANE, SHIN IS
ANOTHER, THE JOINT BETWEEN THEM A THIRD — hinged boundaries, authored as
triangle sets in the mesh system.

## STATEMENT

The leg is THREE membranes — thigh (hip pin to knee pin), shin (knee
pin to ankle pin), foot (the existing ankle membrane) — joined at
shared hinge rings so the chain has no gaps under articulation. Each
segment is a rigid triangle set; poses rotate chains hierarchically
(hip rotation moves everything below it; knee rotation moves shin and
foot); flex 0 restores the authored rest exactly; every cell stays a
tick cell (load/damage/press keep working under any pose).

## DERIVATION (pins measured from live /joints; segment dims derived)

- Pins (measured): hip (+/-0.1734, 3.4153, 0.1155);
  knee (+/-0.4833, 1.9033, -0.0155); ankle (+/-0.4609, 0.3378, 0.0678).
- Thigh length = |hip - knee| = 1.55; shank = |knee - ankle| = 1.57
  (measured; the chibi proportion is the subject's true proportion).
- Tubes: 8-sided prisms along each segment; thigh radius 0.17, shin
  radius 0.13 (hand-and-a-half of the segment length, chibi scale);
  the knee ring is SHARED GEOMETRY: thigh's end ring = shin's start
  ring (same vertices) so the boundary cannot gap.
- The foot's collar center = ankle pin (already measured in B-FEET).
- Cells: every triangle of every segment is a tick cell with exact
  per-triangle capacity (mat.skin yield x area) — the tick already
  computes this from the posted blob.
- Poses: {"hip": h, "knee": k, "ankle": a} per side, degrees, applied
  as planar (X-axis) rotations in chain order: hip about the hip pin
  moves thigh + knee pin + shin + ankle pin + foot; knee about the
  (moved) knee pin moves shin + ankle pin + foot; ankle about the
  (moved) ankle pin moves the foot.

## PREDICTIONS

T1. Rest: both legs render; hip->knee->ankle distances match the
    measured pins; the knee boundary shows no gap (shared ring).
T2. Hip flex +30: the WHOLE leg (thigh, shin, foot) rotates rigidly
    about the hip pin; segment lengths unchanged; no gap at the knee.
T3. Knee flex -40 (hip 0): shin + foot rotate about the knee pin; the
    thigh does not move; the knee boundary stays sealed.
T4. Ankle flex +25: only the foot rotates about the ankle pin.
T5. Chain pose (hip 25, knee -45, ankle 20): a stride-like stance;
    reversibility to 0 restores the authored rest pixel-exactly
    (max pixel diff 0, the TRAVEL bar).
T6. Cells alive: a press intent on the foot still distributes and the
    state sums exactly, in any pose.
P7. Refusals: non-finite or |angle| > 90 refused by name.

## FALSIFIER

Any bar fails, OR a gap/tear opens at a membrane boundary under
articulation, OR a segment deforms non-rigidly, OR the rest state
drifts. On failure the successor: the boundary rings are not sharing
vertices (authoring bug — re-index, never paper over), then re-run.

## OPEN (named)

- Torso/arms/head: the next authored membranes after the legs stand
  and articulate; the walk (stride drive on the authored chain) comes
  after the body exists — training stays forbidden.
- Skeleton integration: the 28-joint pack rebuild so live joint state
  (not posted poses) drives the chain.
