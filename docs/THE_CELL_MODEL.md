# THE CELL MODEL — surface computation, sealed cells, mitosis

Written 2026-09-13 on the operator's directive. This supersedes any
interior/bone computation idea: THE OLD WAY — computing triangles inside
the body to build a bone structure — IS RETIRED. The new way:

## THE LAW

1. ALL COMPUTATION HAPPENS ON THE MEMBRANE SURFACE. The surface
   triangles are the only computer. Nothing is computed on interior
   skeletons.
2. THE SURFACE IS CATEGORIZED: surface triangles are typed by CA class
   (per-triangle joint/material/binding — the classification already
   shipped in the tick).
3. THE INTERIOR IS SEALED BY MEMBRANE: internal triangle walls seal off
   sub-volumes inside the object — CELL DIVISION, a mitosis of the
   membrane. One sealed body becomes two sealed cells; each division
   inserts a wall and assigns each surface patch to a side.
4. HYDRAULICS REQUIRE THE SEAL: surface tension is a hydraulic-type
   equation. A sealed cell holds volume V and internal pressure P; an
   open surface holds nothing. The seal is not decoration — it is what
   makes the math possible.

## THE MATH FRAME (per sealed cell)

- Volume: V = |1/6 * sum over triangles det(v0, v1, v2)| (divergence
  theorem; valid only for a SEALED boundary — the seal is what makes V
  exist).
- Surface tension: the membrane carries tension per unit length; the
  Laplace relation across a curved sealed membrane, dP = g * (1/R1 +
  1/R2), ties the cell's internal pressure to its surface curvature.
  Hydraulic response: volume change dV drives pressure change by the
  cell's compressibility — pressure drives the surface back.
- The tick's per-triangle state (load, damage) stays; the cell-level
  state (V, P) is added above it.

## MITOSIS (the division operation)

A seal wall is an authored internal membrane patch whose boundary ring
welds to surface triangles. Inserting it: one cell becomes two, each
with its own V and P; the wall's two faces belong one to each daughter.
Dividing further is the same operation on either daughter. The
creature's organs are its cells: the leg is sealed from the torso, the
foot from the leg — mitosis IS the body-part boundary, made hydraulic.

## THE BUILD ORDER (named appliances)

1. VOLUME BASE STATE: compute V of the current closed mesh per CA
   region (done live tonight — see the run record).
2. THE SEAL WALL: authored internal patch + region assignment.
3. THE HYDRAULIC TICK: per-cell V, P update from surface motion;
   dP = surface-tension + compressibility response.
4. MITOSIS OP: the divide operation, authored or intent-driven.

## RUN RECORD (2026-09-13, first live classified creature)

- The REAL monkey mesh (18,459 verts / 36,630 tris, recovered and
  rebuilt with regenerated normals) posted to the tick engine with:
  per-triangle CA types (nearest measured joint, all 28 types
  populated, L/R symmetric), per-vertex smooth-travel bindings
  (3 nearest pins, inverse-distance^2 weights), and the 28 measured
  pins.
- Poses applied to the LIVE creature: ankle_R 25 deg changed 6,460
  pixels; knee_R -35 deg changed 10,298 pixels — the sculpted body
  travels smoothly under the blended membrane tick, no tears.
- Engine-measured: 36,630 cells, capacity_sum 1.347e9 N, ticks
  advancing with zero intents (the heartbeat law).
- HYDRAULIC BASE STATE (the seal): surface area 89.8 m^2, sealed
  volume 13.82 m^3 by the divergence theorem — the creature is a
  closed hydraulic vessel. The editor window must stay FOREGROUND:
  backgrounded, the present path stalls and every downstream client
  starves (measured twice, 2026-09-13).

## RUN RECORD (2026-09-13, THE SEAL WALL live — the cut-and-weld)

Build-order appliance 2 is live: POST /tick_seal cuts the creature at
plane y and welds the cap to the TRUE cross-section (336 straddling
triangles split exactly, 14 cross-section loops chained, 308 cap
triangles per daughter, both windings). The daughters are TRUE sealed
cells: V_lower + V_upper = 13.8245 m^3 at rest (2.6e-4 % of the
divergence-theorem whole), conserved under pose to 1.4e-05 %, and the
pressures P = -dV/(kappa*V0) respond to real dV (hip 30 deg:
-298 MPa on the leg cell) and return to 0 EXACTLY when the pose
returns. Evidence and bars: docs/evidence/agent_fleet/MATTER_KERNEL/
SEAL_PREREGISTRATION.md (v2 prereg + run record; falsifier did not
fire). The growth law ahead is recursive mitosis — the same cut op on
a daughter, per scale.

## THE REFERENCE (operator directive, 2026-09-13, after THE SEAL v2)

The operator's standing hint for the road ahead: "everything's been
described in nature." Defects along the way are expected and
acceptable — progress is the measure. Read as law: where a design
question has no derivation in these docs, NATURE is the spec. Real
compressibilities (water for tissue), real vessel mechanics (Laplace's
law, capillary vs aorta wall tension), real division (mitosis at the
membrane), constants cited from measurement, never invented. The
successor appliances derive from physiology first, build second.
