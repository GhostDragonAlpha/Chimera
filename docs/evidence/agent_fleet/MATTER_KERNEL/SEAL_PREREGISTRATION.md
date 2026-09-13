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

---

# THE SEAL v2 PREREGISTRATION — the cut-and-weld wall (the named successor)

Rule 0 again, before the code: statement, derivation, predictions,
falsifier. The v1 falsifier FIRED (floating disc, daughters were not
volumes). v2 replaces the v1 mechanism entirely — no disc, no centroid
smearing: the wall is the welded cross-section itself.

## STATEMENT

Cutting the closed surface with the plane y = 2.6 and welding a cap onto
the EXACT cross-section boundary divides the creature into two SEALED
daughters whose divergence sums are TRUE volumes: V_lower + V_upper =
V_whole to floating-point noise, at rest and under any pose. The weld
holds because inserted cut points ride their surface edges (fixed
parameter t on edge (a,b)) — they cannot drift off the surface, so the
daughters' boundaries stay closed while the surface moves.

## DERIVATION (offline, monkey_full.bin, double precision — before any C++)

Cut rule: strict y < 2.6 is below. A straddling triangle (one or two
vertices below) splits at the plane into a below-piece and an
above-piece; the cut points live on the crossing edges, one per edge,
shared by the adjacent straddling triangles. Segment direction = the
below-piece's boundary walk, so chained loops inherit a consistent
orientation from the surface winding.

Measured on the real mesh (18,459 verts / 36,630 tris, orientation
signed +13.824536 m^3 whole):

- Straddling triangles: 336 of 36,630 (0.92%) — the smearing v1
  tolerated, v2 removes. 336 cut points, 336 segments.
- Loops: 14 closed cross-section rings — two thigh rings (52 edges
  each, x = ±0.48) and twelve small finger tubes of the hanging hands
  (|x| ≈ 3, 11–28 edges). All out-degrees exactly 1: the cut graph is
  a union of disjoint cycles (manifold at the plane).
- Caps: fan from each ring's first vertex, built in both windings:
  308 triangles per daughter (616 total). Fan is exact for volume —
  the divergence integral is triangulation-independent; the caps are
  internal membrane (not rendered), per THE_CELL_MODEL.
- Rest volumes: V_lower = 0.158736 m^3 (the leg cell), V_upper =
  13.665830 m^3 (the body cell); sum 13.824566 vs whole 13.824536 —
  error 2.1e-4 % (double). Both daughters sign-positive: winding
  consistent through the cut.
- Conservation under deformation (smooth warp stand-in for a pose,
  cut slots lerped at fixed t): sum error 2.6e-4 %. The partition
  identity is pose-independent algebra: the daughters' boundaries
  always tile the posed closed surface.
- Pressure law check: dV = +0.008234 m^3 on the lower daughter gives
  P = -dV/(kappa*V0) = -112.76 MPa (kappa = 4.6e-10 Pa^-1, water
  25 C). Expansion lowers P, compression raises it.

## PREDICTIONS (live engine, v2)

S1'. Partition: 36,630 original triangles accounted exactly — 7,306
     pure lower + 28,988 pure upper + 336 split (each into a below-
     and an above-piece); 336 cut points each welded into BOTH
     daughters' boundaries; 14 loops; 308 cap triangles per daughter.
S2'. Conservation: V_lower + V_upper = 13.8245 m^3 within 1% at rest,
     and under a 30-deg hip pose the sum equals the POSED whole-mesh
     divergence volume within 1% (the whole volume itself may move —
     conservation means the daughters tile it exactly).
S3'. Hydraulics: P_lower and P_upper follow P = -dV/(kappa*V0) with
     their own dV; returning the pose to 0 returns both P to ~0
     (|P| < 1 kPa after return; step() recomputes from base, so the
     return is exact up to float32).
S4'. The intent POST /tick_seal {"y":2.6} performs the cut-and-weld
     and /tick_state reports V_lower, V_upper, P_lower, P_upper, the
     split count, loop count, cut-point count, and the conservation
     error.
S5'. Refusals: a plane outside the body's y-range (-0.0195..9.9712)
     is refused; re-sealing a sealed creature is refused; a cut graph
     that fails to close (non-manifold plane crossing) is refused BY
     NAME rather than guessed around.

## FALSIFIER

V_lower + V_upper deviates from the posed whole volume by > 1% at
rest or under pose (the weld leaks), OR P moves without a matching dV,
OR any cut point lands in fewer than two daughter boundaries. If it
fires, the successor is named: audit per-edge weld topology (which
edge, which two triangles) and the plane classification epsilon —
do NOT patch by nudging volumes.

## RUN RECORD (2026-09-13, live engine v2 cut-and-weld, final binary)

One clean instance: restart -> classify_run.py payloads -> bars in
prereg order. Full log: .tmp/seal2_run.log (driver: tools/seal2_run.py;
offline derivation: tools/seal2_derivation.py).

- S5'a refusals: PASS — y=99.9 and y=-5 both refused by name, BEFORE
  the seal (cause unambiguous: plane outside the body y-range
  -0.0195..9.9712).
- S4' mitosis intent: PASS — POST /tick_seal {"y":2.6} -> ok.
- S1' partition: PASS — seal_split=336, seal_cuts=336, seal_loops=14,
  seal_caps=308; 7,306 pure lower + 28,988 pure upper + 336 split =
  36,630 accounted. Every cut point welded into both daughters
  (336/336 each in the offline derivation; the live weld is proven by
  conservation below).
- S2' conservation at rest: PASS — V_lower 0.158736 + V_upper 13.6658
  = 13.824536 m^3 vs the 13.8245 target (2.6e-4 %); conserve_pct = 0.
- S3' rest pressure: PASS — P_lower = P_upper = 0 EXACTLY.
- S5'b re-seal: PASS — refused by name.
- S2' conservation under pose: PASS — hip_L (joint 13) 30 deg:
  V_whole moved 13.8246 -> 13.8241 m^3 (blended travel is not
  volume-preserving — that is the hydraulic signal); conserve_pct =
  -1.38e-05 %. The daughters traded volume: dV_lower +0.0218,
  dV_upper -0.0223 m^3.
- S3' hydraulics: PASS — dV_lower +0.021788 m^3 -> P_lower
  -298.39 MPa (expansion lowers P); kappa-law recompute from the
  reported V and v0 agrees to ~1e-3 relative (the state prints V at 7
  significant digits; the law lives in the tick, the check only
  re-reads the print). P_upper +3.54 MPa for its own dV.
- S3' return: PASS — pose back to 0: volumes restored to v0 exactly,
  P_lower = P_upper = 0 exactly, conserve 0.
- Frames (CHIMERA_PROOF\FEET\): seal2_before_rest.png,
  seal2_posed_hipL30.png (6,096 px changed, bbox x[1101,1334]
  y[385,712] of 2560x1369 — the left hip/thigh region),
  seal2_returned_rest.png (0 px changed vs before — pixel-exact
  restore). Vision check on the crops: the brown sculpted monkey on
  the engine grid; the posed crop shows the hip/leg asymmetry, the
  rest crops show the legs symmetric; long spread fingers at the
  sides — the anatomy the 12 small cross-section loops decode to.

### The mid-run fix (disclosed, not hidden)

The first live seal (same cut-and-weld, v0 evaluated on base_pos_)
measured P at rest = -3265 / +2731 Pa: v0 was computed on the authored
base while the live volume ran on the tick's blended rest verts, and
float32 blend rounding (1.3e-6 relative volume) amplified by water's
kappa is ~3 kPa of phantom pressure. Fixed by extracting apply_travel()
(the classified blend) and evaluating the cut AND v0 on the tick's own
zero-angle rest blend — the same arithmetic path per frame, so the
rest dV is exactly 0, not float-noise. The preregistered 1 kPa bar
then passed exactly (0 Pa) on the final binary. The fix changed the
REFERENCE evaluation, not the bar; both runs are recorded here.

FALSIFIER: DID NOT FIRE. v2 stands.

## OPEN (v2)

- Recursive mitosis (the growth law): re-cut a daughter by the same
  plane op at a finer scale — leg -> shin -> foot. The partition code
  is already per-plane; the intent needs a daughter selector.
- Wall dynamics: the wall is currently rigid (cut slots ride edges at
  fixed t); a tensioned wall that deforms under the pressure delta is
  the next hydraulic appliance (Laplace).
- Rendering the internal wall on demand (it is deliberately invisible
  internal membrane; a debug view would show the cut line).

---

# THE MITOSIS PREREGISTRATION — the growth law (recursive cut-and-weld)

Rule 0 again, before the code. THE REFERENCE (operator, 2026-09-13):
"everything's been described in nature" — the compartments follow the
measured joint bands (hip 3.415, knee 1.903, ankle 0.338 — the pins),
the way fascial compartments divide a limb.

## THE WINDING-LAW CORRECTION (defect in the shipped v2, found while
## deriving this appliance — disclosed before the fix)

Preparing the hip cut exposed it: at y=3.415 the below closure signed
NEGATIVE (-1.19), impossible for a consistent mesh. Cause: the v2 cap
windings were SWAPPED. Topology law: every edge of a closed oriented
surface appears exactly twice, once per direction — the below pieces
walk each cut edge in the chained direction, so the LOWER cap must
traverse the ring REVERSED and the UPPER cap as chained. v2 did the
opposite. At y=2.6 BOTH closures stay positive (computed 0.159 vs true
0.779), so every v2 SUM bar passed while the daughter SPLIT was wrong.
Ground truth by ray parity: occupancy area at 2.6 = 0.376 m^2 → the
true below-cap divergence is +0.326 (chained gave -0.310). Corrected
v2 split at rest: V_lower = 0.779, V_upper = 13.046 (sum unchanged).
The v2 run record's S2'/S3' bars measured sums and returns — those
stand; the per-daughter values recorded there are corrected here.

## STATEMENT

The cut-and-weld generalizes from the creature to ANY sealed cell:
POST /tick_seal {"y": Y, "cell": k} cuts cell k into two sealed cells.
Repeated cuts grow the body-part tree — the growth law. Inserted points
become convex blends over original vertices (merged, <= 8 entries), so
every point rides the posed surface at fixed weights: the weld argument
is depth-independent algebra.

## DERIVATION (offline, corrected winding, plane at the measured bands)

- hip y=3.415 (whole creature): 392 straddlers, 392 cuts, 6 loops
  [56, 84, 56] mirrored — two hip lobes and hollow-arm annuli at
  |x| ~ 2.6-2.8; 380 caps. V_below = 1.315499, V_above = 12.509037
  (err -1.13e-06 %).
- knee y=1.903 on the leg cell: 108 straddlers, 2 loops, 104 caps.
  shin+foot = 0.622492 | thigh = 0.693007 (err -1.23e-06 %).
- ankle y=0.338 on the shin+foot cell: 130 straddlers, 2 loops, 126
  caps. foot = 0.287914 | shin = 0.334577 (err -1.12e-07 %).
- Four cells sum to 13.824536 (-1.25e-06 %); under a smooth warp the
  sum tracks the whole to -1.19e-05 %; each cell's P = -dV/(kappa*V0)
  responds to its own dV.

## PREDICTIONS (live engine, mitosis build)

M1. First cut (hip): cell volumes match the derivation within 1%;
    sum = 13.8245 within 1%; P = 0 exactly at rest (v0 on the tick's
    rest blend, as fixed in v2).
M2. Recursion: knee then ankle cuts via the "cell" selector; each cut
    conserves (V_A + V_B = V_parent within 1e-3 %); the four-cell sum
    equals the posed whole within 1% at rest AND under a knee pose.
M3. Hydraulics per cell: a knee_L 25-deg pose changes the shin+foot
    and thigh cells' volumes by their own real dV (pressures respond
    by the kappa law); pose return brings every P back to 0 exactly.
M4. Refusals, by name: cell index out of range; plane outside the
    named cell's y-range; a cut graph that fails to close. Re-cutting
    a cell is LEGAL recursion now — cutting IS the operation
    (supersedes v2's one-seal-per-creature guard).

## FALSIFIER

Any live cell volume off its derivation by > 1%, or the cells' sum off
the posed whole by > 1% at rest or under pose, or any P != 0 at rest,
or a real-mesh cut refusing (graph fails to close = the blend-slot
port broke the weld). Successor if fired: audit the blend merge and
the per-cell piece lists against the offline prototype, cell by cell.

## RUN RECORD (2026-09-13, live engine MITOSIS — the growth law, 4 cells)

One clean instance on the final binary (driver: tools/mitosis_run.py;
full log: .tmp/mitosis_run.log; offline derivation:
.tmp/proto_mitosis.py). Cell order in state = [foot, body, thigh, shin]
(0 replaced at each cut of cell 0, the above-daughter appends).

- M4 refusals (before any cut): PASS — cell=7 (no such cell), y=99.9,
  and later y=2.0 on the foot cell (y-range tops at 0.338) all refused
  by name.
- M1 hip cut: PASS — split=392, cuts=392, loops=6, caps=380; v0
  1.315500/12.509000 vs derived 1.315499/12.509037 (7.6e-05 % /
  2.96e-04 %); P = 0 EXACTLY at rest; conserve -8.28e-05 %.
- M2 knee cut on cell 0: PASS — shin+foot 0.622491 | thigh 0.693010
  (1.6e-04 % / 4.3e-04 % vs derived). Ankle cut on cell 0: PASS —
  foot 0.287914 | shin 0.334578 (0.0e+00 % / 3.0e-04 %). Four cells
  sum 13.824502 vs whole 13.824536 (conserve -6.9e-05 %).
- M3 per-cell hydraulics: PASS — knee_L 25 deg: foot dV -0.007396 ->
  P +55.843 MPa; thigh dV +0.007284 -> P -22.849 MPa; shin dV
  -0.001971 -> P +12.807 MPa; body dV +0.000000 -> P 0.000000. An
  independent kappa-law recompute from the reported (v0, V) matches
  every pressure to 3 decimals. Pose return: worst |P| = 0.0 Pa.
- Frames (CHIMERA_PROOF\FEET\): mitosis0_before.png,
  mitosis1_rest4cells.png, mitosis2_posed_kneeL25.png (8,604 px
  changed, bbox x[1095,1332] y[463,700] — the bent knee; vision check:
  the left calf visibly kicked back), mitosis3_returned.png (0 px
  changed — pixel-exact restore).

### The two crashes on the road here (both found, both fixed — disclosed)

1. seal_nv_ never set at publish (stayed 0): step()'s slot_read treated
   every original vertex as a cut slot and read far out of bounds ->
   NaN volumes (first live seal), then the AV class. Fixed: publish
   sets seal_nv_ under the lock.
2. THE BOOT-RESTORE RACE (the 06:36 crash under the OLD binary too,
   and the two refusals-then-frame kills): boot-restore replays
   mesh_bin on its own thread 1.5 s after launch while the render
   thread travels; classify_run.py's mesh re-POST re-ran init() and
   CLEARED vert_bind_idx_ mid-travel — apply_travel crashed indexing
   the cleared bindings. Symbolized both offsets against a freshly
   enabled linker map (crash instrumentation now ships in the build:
   /Zi + /DEBUG:fastlink + /MAP). Fix: one mutex shared by init(), the
   /tick_* loaders, and seal()'s entry/publish; step() try_locks and
   skips a frame's volume update instead of blocking the render loop.
   The exact kill sequence (refused cuts -> /frame) then ran clean,
   and the full bar sequence passed on one instance.

FALSIFIER: DID NOT FIRE. The growth law stands: the creature divides
on intent, one sealed cell per body compartment, volumes conserved
under the growth, pressures honest per cell.

---

# THE HYDRAULIC PRESS PREREGISTRATION — appliance 3 (the physics pushes back)

Rule 0 before the code. THE REFERENCE: nature — press skin, it dimples
by its tension; release, it recovers. Until now poses moved the surface
and pressures only REPORTED; nothing deformed under load. This
appliance makes the press intents physical: the pressed surface
DIMPLES, the divergence sums see the dimple, and the cell pressure
answers — control on a natural level.

## STATEMENT

A press intent F on a joint's cells displaces those surface vertices
inward (along their authored normals) by the linear-membrane law, with
a smooth falloff; releasing the force restores the surface exactly.
The dimple is real geometry: the per-cell divergence sums (already
live) see its volume change and the kappa law answers with pressure.

## DERIVATION (cited, before implementation)

- Linear membrane under uniform tension, central point load
  (Timoshenko, Plates & Shells): delta = F / (4*pi*sigma).
- sigma (N/m) from the repo's own material law (mat.skin, Yamada 1970):
  skin ULS ~8 MPa x 1.5 mm thickness = 12000 N/m failure tension;
  working tension at safety factor 3: sigma = 4000 N/m.
- Predicted depths: 500 N -> 9.9 mm; 1000 N -> 19.9 mm;
  10000 N -> 198.9 mm (the last is the VISIBLE bar — 2 cm on a 10 m
  creature is sub-pixel at 2560).
- Falloff: Gaussian, r0 = 30 mm (a named choice: the skin distress
  radius; it shapes the dimple, not its depth — falsifiable by
  geometry, not by volume).
- Volume coupling: a 10 kN dimple ~ pi*r0^2*delta/3 = 1.9e-4 m^3 ->
  foot cell (V0 0.288): P +1.4 MPa (measurable); body cell
  (V0 12.5): +33 kPa (water truth: big cells barely notice).
- Recovery: force -> 0 restores offsets to 0 (deterministic, same
  arithmetic as the pose return; bar is pixel-exact).

## PREDICTIONS (live engine)

HP1. /tick_intent-joint knee_L 1000 N -> state dimple_m = 0.0199 m
     within 20%; a frame diff shows the dimple region changed.
HP2. Linearity: 500 N -> dimple_m exactly half of the 1000 N value.
HP3. Release -> dimple_m = 0 and the frame pixel-exact vs pre-press.
HP4. Hydraulic coupling (10 kN on ankle_L): the foot cell's V drops,
     its P rises ~ +1.4 MPa by the kappa law; the cells' sum stays
     conserved to < 1e-3 %.
HP5. Refusals stand: force <= 0 refused (existing law).

## FALSIFIER

dimple_m not force-linear (bug in the offset application), OR the
dimple fails to move the cell volumes (the offset is not in the
geometry the divergence sums read), OR release leaves a residual
(the surface did not restore). Successor if fired: audit where the
offset is applied relative to the travel/pose write and the seal read
— it must land between them, on the same verts9 buffer.

## OPEN (named)

- Press + pose composition (dimple directions use AUTHORED normals —
  wrong under a pose; composition needs posed normals).
- Press POINT selection (today the press region = the joint's whole
  cell group; a ray-hit press point is the game-facing op).
