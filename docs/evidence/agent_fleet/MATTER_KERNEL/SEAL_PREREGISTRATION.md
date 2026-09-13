# THE SEAL PREREGISTRATION — mitosis v1 + the hydraulic state (Appliance 4)

Rule 0: statement, derivation, predictions, falsifier — BEFORE the code.
Build order 2-3 of THE_CELL_MODEL: the interior is sealed by an internal
membrane wall; the sealed cells carry the hydraulic state.

## STATEMENT

One intent — the seal — divides the membrane creature into TWO sealed
cells (mitosis): a plane wall at height y_s seals the interior, every
triangle joins the lower or upper daughter cell, and each daughter
carries its own hydraulic state (volume V, pressure P) computed per tick
from its surface. The wall itself is membrane surface: it counts in the
daughters' area and closes their volumes. Pressure follows the hydraulic
law: dP = -dV / (kappa * V), with kappa the compressibility of the
medium. Volume is computed by the divergence theorem — a law that only
means anything because the cells are SEALED.

## DERIVATION (from the live creature, measured 2026-09-13)

- The creature: 36,630 triangles, sealed volume 13.8245 m^3, surface
  89.799 m^2 (divergence theorem, consistent sign — the unsealed mesh
  was already watertight; the seal ADDS the interior boundary so the
  daughters' volumes are independent).
- Seal plane v1: y = 2.6 m (between the ankle band 0.34 and the hip
  band 3.42, chosen at mid-thigh so the lower daughter is the LEG
  cell and the upper daughter the BODY cell — the walk's first
  hydraulic partition).
- Region assignment: triangle centroid y < y_s -> LOWER, else UPPER.
- Per-daughter volume: divergence contribution of the daughter's
  surface triangles + the wall disc's contribution (constant while the
  plane holds; the disc's own area enters the daughters' membrane area).
- Compressibility: water 4.6e-10 Pa^-1 at 25 C (ENGINEERING_TOOLBOX /
  standard tables); biological tissue is water-dominant — the same
  order. dP = -dV / (kappa * V0), V0 = the daughter's rest volume.
- Bars in newtons stay as certified: press intents load cells; the
  hydraulic P is the cell VOLUME response — separate quantities, both
  reported.

## PREDICTIONS

S1. Partition: all 36,630 triangles assigned (count_lower +
    count_upper = 36,630); the seal disc is authored internal surface.
S2. Conservation: V_lower + V_upper = 13.82 m^3 within 1% at rest, and
    the sum stays conserved under ANY pose (pose the hip 30 deg: the
    daughters trade volume, the sum holds).
S3. Hydraulics: a pose that shrinks the lower daughter by dV raises its
    P by dV/(kappa*V0); P returns to 0 when the pose returns to 0.
S4. Mitosis intent: POST /tick_seal {"y": 2.6} creates the wall and the
    two regions; the state reports per-daughter V, P, area, cell count.
S5. Refusals: seal outside the body's y-range (no triangles cross) ->
    refused by name; re-sealing an already sealed cell -> refused
    (one wall per plane; v1 allows one seal).

## FALSIFIER

V_lower + V_upper drifts from 13.82 m^3 under pose (the seal leaks —
it is not sealed), OR P moves without dV, OR a triangle lands in
neither daughter. On failure the successor is named: the divergence
contributions are crossing the plane (a triangle spans the seal —
split it at the plane, then assign), fix, re-run.

## OPEN (named)

- Triangle-splitting at the plane (v1 assigns by centroid; a
  straddling triangle's volume contribution smears across the seal —
  bounded by the straddling fraction, measured in the run record).
- Arbitrary wall patches (v1: plane walls only).
- Mitosis chains beyond two daughters (re-seal a daughter = allowed by
  re-running with a new plane — the partition code is per-plane).

## RUN RECORD (2026-09-13, live engine v1 seal)

- S1 partition: PASS — 36,630/36,630 triangles assigned to the two
  daughters; the seal intent created the wall and both regions.
- S2 conservation: PARTIAL PASS — the daughters' volume SUM is
  conserved under pose (70.54 before, 70.54 after a 25-deg ankle
  flex), but the ABSOLUTE values (28.4/42.2) are non-physical against
  the true 13.82 m^3. Cause, measured: the v1 seal wall is a floating
  disc — it does not WELD to the surface cross-section, so the
  daughter boundaries are not closed surfaces and the divergence sums
  are not volumes.
- S3 hydraulics: PASS as a mechanism — dV drove P by dP = -dV/(kappa*
  V0) (P_lower responded -332 kPa to a +0.0046 m^3 shift); the law is
  wired, waiting for a true seal.
- S4 mitosis intent: PASS — one POST creates the two regions.
- S5 refusals: PASS — an out-of-body plane is refused by name
  ('the seal plane must cross the body').

## THE NAMED SUCCESSOR (falsifier fired, next appliance)

THE SEAL WALL done right: cut the surface at the plane (intersect the
crossing triangles, chain the segments into the cross-section
polygon), weld the cap to that polygon, then the daughter divergence
sums are true volumes. The cap boundary must equal the cut edges
exactly. Split-straddling-triangle fraction measured at that point.
