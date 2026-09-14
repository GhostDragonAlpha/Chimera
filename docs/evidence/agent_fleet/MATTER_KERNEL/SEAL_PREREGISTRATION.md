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

## RUN RECORD (2026-09-13, live engine HYDRAULIC PRESS — the physics pushes back)

One clean instance on the final binary (driver: the HP sequence, log
.tmp/press_run.log; cells re-seeded foot/body/thigh/shin first).

- HP1: PASS — knee_L 1000 N -> dimple_m = 0.019894 (predicted
  0.019894); failed = 0.
- HP2: PASS — 500 N -> dimple_m 0.009947, ratio 1.999964.
- HP4: PASS — ankle_L 10 kN -> foot cell dV -0.000678 m^3,
  P +5.118 MPa (independent kappa recompute +5.119); conservation
  -7.59e-05 %.
- HP3: PASS — release -> dimple_m = 0, worst |P| = 0, frame
  pixel-exact (press2_released.png vs press0_before.png, 0 px).
- HP5: PASS — force <= 0 refused.
- VISIBILITY (the features law): the first lit pair moved only 756 px
  (max 109) — the dimple displaced vertices but kept AUTHORED normals,
  so the shading stayed flat. Fixed in-appliance: normals recomputed
  from the DEFORMED pressed cells (face-normal accumulation,
  normalized; restored from authored base on release). Final pair:
  2,450 px (max 168), the pressed wrist crease visibly pinched
  (press9/pressA/pressB in CHIMERA_PROOF\FEET\).

### Defects found on the road here (all fixed in this appliance, disclosed)

1. SLIVER CELLS FIRE THE DAMAGE LAW: the sculpt has 206 triangles with
   capacity < 2 N (min area exactly 0). Equal-share load spread handed
   them force; damage += load/~0 -> inf, 20 cells died on the first
   1 kN press. Fix: a capacity floor (0.1 N) — a degenerate patch is
   not a membrane and carries no share. Presses now fail nothing.
2. RELEASE DID NOT EXIST: clear_intent() only cleared the FOOT forces;
   per-joint presses had no release. Fix: /tick_intent_clear releases
   ALL standing intents.
3. THE RACE WAS STILL OPEN — my mitosis lock guarded only the SEAL
   block of step(), while apply_travel at the TOP of step() read the
   bindings that init() clears (crash at /cameras recall right after a
   fresh boot + payload re-post; offset symbolized via the map:
   apply_travel+0x104, the third AV of this class). Fix: ONE try_lock
   at step() entry covers the whole tick body — the render loop still
   never blocks (a cut or mesh upload in flight skips that frame).

FALSIFIER: DID NOT FIRE. The surface now answers load like tissue:
press and it dimples by the membrane law, the sealed cells answer by
kappa, release and it is pixel-exact again.

---

# THE HYDRAULIC RETURN PREREGISTRATION — appliance 3 completed (tension response)

THE_CELL_MODEL appliance 3: "dP = surface-tension + compressibility
response — pressure drives the surface back." The compressibility half
is live (kappa answers dV). The tension half is NOT: recovery today is
INSTANT (release -> dimple zeroed same tick). Nature recovers over
TIME — soft-tissue stress relaxation. This completes the appliance.

## STATEMENT

A released dimple decays exponentially with tissue relaxation time
tau instead of vanishing instantly: offset_i(t) = offset_i(0) * 
exp(-t/tau). The press holds its forced value while active (force
balances tension — steady state); on release the same offsets decay.
Below a 0.1 mm cutoff the field clears fully (deterministic rest is
preserved; frames taken after 3*tau are pixel-exact).

## DERIVATION

- Soft-tissue stress relaxation is exponential in time (standard
  viscoelastic first-order decay); tau = 0.5 s is the named choice at
  Yamada's cited skin-creep scale — falsifiable by the decay bar.
- dt: the tick now takes the MEASURED frame time (clamped 0..0.1 s);
  decay factor per tick = exp(-dt/tau). No fixed-step assumption.
- The cutoff 1e-4 m is 0.5% of the 2 cm working dimple — sub-pixel,
  and the deterministic-rest law survives.

## PREDICTIONS

HR1. Press ankle_L 10 kN, release: dimple_m(0) = 0.1989; dimple_m at
     ~0.5 s = 0.1989*e^-1 = 0.0732 within 25% (frame-timing jitter);
     dimple_m at ~2 s < 0.0036; shortly after 3*tau (1.5 s) EXACTLY 0.
HR2. During decay the foot cell's P decays on the same exponential
     (P is driven by the offset volume): P(t)/P(0) = dimple_m(t)/
     dimple_m(0) within 10%.
HR3. Conservation holds through the decay (sum conserved < 1e-3%);
     the frame at rest AFTER the decay is pixel-exact vs pre-press.

## FALSIFIER

The decay is not exponential in MEASURED time (fixed-step smuggled
in), OR rest never returns exactly (the cutoff leaks), OR conservation
breaks during decay. Successor if fired: audit the dt plumbing from
the frame loop and the offset clear condition.

## SUPERSEDES

HP3 (instant release) is superseded by HR1/HR3: "release" now means
"exponential recovery with tau = 0.5 s, exact rest after 3*tau". The
HP3 pixel-exactness bar moves to post-decay frames.

## RUN RECORD (2026-09-13, live engine HYDRAULIC RETURN + COMPONENT SPLIT)

One clean instance on the final binary (log .tmp/roadmap_run.log;
frames return*/split* in CHIMERA_PROOF\FEET\).

- HR1: PASS — released dimple decays exponentially in MEASURED time;
  tau per interval 0.499 / 0.498 / 0.501 / 0.501 / 0.500 s against the
  declared 0.5; dimple reaches EXACT 0 at the cutoff (~4 s).
- HR2: PASS — foot-cell P decays on the same exponential (ratios
  0.50/0.52, 0.26/0.28, 0.11/0.13, 0.04/0.04).
- HR3: PASS — conservation through decay -6.9e-05 %; rest after decay
  worst |P| = 0; the post-decay frame is the deterministic rest state.
- SS refusals: PASS — the body cell (one closed surface) refused by
  name.
- SS splits: PASS — feet, thigh, shin cells each split into their
  components; n_cells = 15; the sum holds 13.824502 vs 13.824536
  (2.5e-04 %). The cells come in L/R mirror pairs with identical
  volumes — including the feet's separated digits (0.0111 m^3 pairs).
- SS3 per-side hydraulics: PASS — knee_L 25 deg moves exactly 9 cells
  while their 6 L/R mirrors sit at dV = 0.000000; conservation
  6.9e-05 %; pose return worst |P| = 0.

### Defect found + fixed here (disclosed)

dimple_m_ reported the THEORETICAL delta while the true max applied
offset was smaller (the Gaussian peak can fall between mesh vertices —
for the ankle, 0.052 vs 0.199). That lie made the first HR run's decay
head look wrong (the physics tail was already exact tau). Fixed:
dimple_m_ = the true max APPLIED offset, measured during application.

### The lock completed (third race class, disclosed)

seal()/split()/state_json() ran on HTTP threads reading bindings, the
cell state, and the blend table with no lock while loaders/init
rewrote them (the map kept attributing the AVs to inlined
apply_travel). Now every entry point — step (try_lock), seal, split,
state_json, the loaders, init — holds the SAME mutex; the render loop
still never blocks.

## THE BUILD ORDER IS COMPLETE

THE_CELL_MODEL's four appliances are now all live: 1 volume base
state, 2 the seal wall (cut-and-weld), 3 the hydraulic tick (BOTH
halves: compressibility answers dV, tension recovers the surface in
declared time), 4 the mitosis op (recursive cuts + component
separation). The creature is 15 sealed hydraulic compartments —
per-side feet (with digits), thighs, shins, plus the torso — that
pose, dimple under load, relax like tissue, and divide on intent.

## OPEN (beyond the recorded roadmap; named for successors)

- Press POINT selection (ray-hit) and press+pose composition (posed
  normals).
- Laplace curvature flow (the wall deforms under its pressure delta —
  today walls are rigid and the surface recovers by relaxation).
- Rendering the internal walls on demand (the invisibles law: see the
  seal).
- Gait: the per-side hydraulic states are the signal a walk cycle can
  read (stance cell pressurizes, swing cell relaxes).

---

# THE TOUCH PREREGISTRATION — R3 (press where you point, in motion)

Rule 0 before the code. THE REFERENCE: you touch a creature WHERE your
hand lands, not "its left foot group"; and your touch deforms the skin
along the skin's CURRENT direction, wherever the body has moved.

## STATEMENT

A touch intent carries a screen pixel and a force. The engine casts the
camera ray through that pixel (eye from the spherical camera law in
update_camera_matrices, 45-degree vertical fov), intersects the POSED
surface, and presses AT THE HIT POINT: a Gaussian dimple around the
posed location, along the posed skin's normals, with the hydraulic
answer in whatever cells the dent lands in. Release recovers by the
tau law (already live).

## DERIVATION

- Ray: eye = target + r*(cos(phi)sin(theta), sin(phi),
  -cos(phi)cos(theta)) + pan; forward = normalize(target - eye);
  up = (-sin(phi)sin(theta), cos(phi), sin(phi)cos(theta)) (the
  no-pole up already in the camera); right = normalize(cross(forward,
  up)); dir = normalize(forward + right*(2u-1)*aspect*tan(22.5deg)
  + up*(1-2v)*tan(22.5deg)) for pixel fractions u (left->right),
  v (top->bottom).
- Intersection: Moller-Trumbore over the POSED vertex buffer (36,630
  triangles — sub-millisecond on the HTTP thread), nearest hit wins.
- THE CLOSED-LOOP CORRECTNESS BAR (no visual judgement needed for the
  math): the hit point, re-projected through the same camera
  (project_world, already live), MUST land back on the requested
  pixel within one pixel.
- Posed normals: the travel pass writes positions; normals are now
  recomputed from the POSED surface every tick (also the general
  lighting fix under pose). Touch direction then rides the true skin.

## PREDICTIONS

T1. Closed loop: pick(px,py) -> project_world(hit) = (px,py) within
    1 pixel of 2560x1440, for at least 5 spread pixels.
T2. A ray at empty space (miss) is REFUSED by name; no press happens.
T3. Touch at the belly (posed creature): dimple visible in the frame
    at the touched spot; the torso cell's V drops and its P answers
    by kappa; release -> tau recovery, rest exact.
T4. Touch while POSED (knee 40): the dimple lands on the POSED limb
    (frame evidence), direction along the posed skin; the closed-loop
    bar still passes in the posed state.
T5. Touch + joint press coexist without corrupting each other's
    offsets (release both -> pixel-exact rest).

## FALSIFIER

The closed loop misses (ray/camera convention wrong — fix the
handedness, do not nudge pixels), OR a posed touch lands at the
AUTHORED location (the stale-normal bug), OR release leaves residue.
Successor if fired: audit the ray handedness against project_world
and the normal-recompute placement in the tick order.

## RUN RECORD (2026-09-13, live engine R3 TOUCH — press where you point)

- T1 closed loop: PASS — pick -> hit -> re-project = the requested
  pixel, 0.0 px error on three probes (belly, belly+right, belly+up).
  The live camera targets the origin (the boot fit), so the belly
  sits at screen (0.500, 0.295) — the probe casts where the body IS,
  not where a center-framing assumption puts it.
- T2: PASS — a ray at empty space refused by name.
- T3: PASS — belly 30 kN: dimple 0.2415 m, torso cell dV -0.003 m^3,
  P +0.534 MPa (independent kappa recompute +0.521); conservation
  -4.1e-05 %; release recovers to dimple 0, all P 0.
- T4: PASS — THE POSED TOUCH: knee_L 40 deg, the pin re-projected and
  touched through the camera — the hit returned at (0.4827, 1.9032,
  -0.0154) against the pin (0.483, 1.903, -0.015): SUB-MILLIMETER on
  the moved limb. The dimple follows the body. (posed normals now
  recompute from the posed surface EVERY tick — the stale-normal bug
  class is dead by construction, and lighting under pose is true.)
- T5: PASS — combined release (touch + pose): exact rest (dimple 0,
  all P 0, conserve -6.9e-05 %). First sample at 4 s read mid-decay
  (0.000128 m — the honest tau tail on a compound deformation); the
  true rest verified 3 s later. Evidence: CHIMERA_PROOF\TOUCH\
  (t0_rest / t1_dimpled: 954 px changed at the belly silhouette;
  t2_recovered / t3_posed_touch / t4_rest).

### Disclosure: the falsifier fired on an INSTRUMENT, not the physics

The first T1 run FAILED — every /project query returned the screen
center. Cause, found by the prereg's own audit: my verification calls
used the wrong JSON key ("p" array instead of x/y/z), so the instrument
projected the ORIGIN every time and answered the center. The pick was
re-audited against the corrected instrument and passes at 0.0 px. The
engine's /project contract is x/y/z floats; nothing in the engine
changed for T1 to pass.

R3 THE HOOK IN MOTION: **PASS** — touch lands where you point, on the
posed body, with the hydraulic answer and the honest recovery.

---

# THE WEB KERNEL PREREGISTRATION — the browser renders the world itself

Operator directive: "we need some sort of separate kernel system for the
user's web viewer — some sort of web GPU mechanism." Agreed and made
law here: THE BROWSER SHIPS NO PIXELS FROM THE ENGINE. The engine
streams STATE (posed vertices + cell colors, one-time topology); the
browser renders the creature locally (WebGL2, its own camera, its own
orbit/zoom at its own framerate); touches become browser-side ray-casts
sent as world-space hits. The engine's render loop never encodes a PNG
for a player — the 28 fps 1% lows die at the root.

## STATEMENT

/world = engine simulation. /viewer = a local WebGL2 renderer fed by
/state. The player's camera is LOCAL: dragging orbits the browser's own
scene at 60 fps with zero engine work. A click ray-casts LOCALLY against
the streamed mesh and posts the world-space hit; the engine presses
there (its own hydraulics answer). The engine's camera is no longer a
player's dependency.

## PREDICTIONS

W1. With the game page open, the engine's own FPS readout is
    UNCHANGED from no-page-open (no /frame polls: the page never
    requests a PNG). The 1% lows recover to the engine's normal.
W2. Orbiting in the browser is smooth at the page's framerate with
    zero HTTP during the drag (camera is local math).
W3. A browser click posts a world hit; the engine's dimple forms AT
    that point (state P responds in the cell that owns it).
W4. /verts stream = 18,459 verts x 9 f32 = 664 KB per pull at ~3 Hz
    (~2 MB/s, localhost); the topology pull is one-time 440 KB.
W5. The press path is the SAME tau/kappa machinery — rest exactness
    untouched (dimple 0, P 0 after release+decay).

## FALSIFIER

The engine FPS still dips while the page streams (state route reading
the buffer unlocked — it must share the tick mutex), OR the browser
renders a STALE creature (stream too slow to follow a pose — stream
rate must rise, not the engine polling), OR a browser-side touch lands
off the creature. Successor if fired: delta compression for the stream
(only changed verts) — named now as the internet-scale successor.

---

# THE MESH IMPORT PREREGISTRATION — the aliveness law, one POST (fleet C1)

Operator directive (docs/THE_SHIP_GOAL.md, THE ALIVENESS LAW): any mesh +
skeleton comes alive. C1 delivers the front door: `POST /mesh_import` takes
a static OBJ or glTF 2.0 body and walks it through the SAME four moves the
hand-authored creature uses — import -> classify -> bind -> seal — with
`tools/bring_alive.py` as the orchestrating client.

## STATEMENT

One POST brings a static mesh alive: import (OBJ subset or glTF 2.0 ->
the engine's full mesh format) -> classify (nearest joint pin per triangle
centroid) -> bind (3 nearest pins, inverse-distance^2 weights) -> seal
(the cut-and-weld at a chosen plane). No step is new physics — each
replays a law the engine already certifies; the new claim is that the
CHAIN holds for arbitrary closed input surfaces, not just the authored
creature.

## DERIVATION

- The mesh format (the only one the engine admits):
  [u32 N][u32 idxCount][f32 cam_radius][f32 cam_theta][f32 cam_phi]
  [f32 slotmode][9 f32/vertex: pos3, normal3, color3][u32 indices * idxCount].
- Normals are recomputed area-weighted (the cross-product sum over a
  vertex's triangle fan — each term's magnitude IS the triangle area, so
  the vector sum is the area-weighted average); colors are uniform warm
  tan (0.80, 0.55, 0.35) — the aliveness law needs no authored palette.
- Classification = nearest joint pin per triangle centroid
  (tools/classify_run.py's exact law); binding = 3 nearest pins,
  w = 1/(d^2 + 1e-6)^2 normalized — the same math, any mesh.
- Seal = the cut-and-weld at a plane (mitosis v2, machinery unchanged).
- THE FALSIFIER MECHANISM, named before the run: a leaky/open mesh is
  REFUSED BY NAME. The importer computes the divergence closure — every
  directed edge (a->b) must be matched by exactly one (b->a); boundary
  edges are counted and named ("mesh not closed: K boundary edges"). The
  divergence volume V = sum(dot(a, cross(b, c)))/6 must clear a
  scale-relative epsilon (1e-6 x bounding-box volume) — zero/flat volumes
  refused ("zero enclosed volume"). Winding is normalized so V > 0
  (outward) and the body is centered at the origin, so the seal plane at
  mid-height cuts a standing body. Degenerate limits refused by name:
  > 500000 triangles, faces that cannot fan-triangulate (< 3 vertices),
  repeated-index triangles.

## PREDICTIONS

A1. VOLUME: the imported creature's cells conserve volume — after
    /tick_seal at mid-height, /tick_state reports |conserve_pct| <= 1
    (sum of cell volumes vs the whole divergence volume).
A2. POSES TRAVEL: posing a spine pin 25 deg moves the bound region and
    conservation HOLDS under the pose (|conserve_pct| <= 1); pose 0
    restores the rest volumes exactly.
A3. TOUCH ANSWERS: the sealed creature answers a /tick_touch press
    (dimple forms, P moves in the owning cell) — the press path needs
    no mesh-specific code.

## FALSIFIER

A mesh that fails the closure check must be refused BY NAME — if the
import instead admits an open surface, the falsifier fired. Conversely,
if a mesh that PASSES the closure check then cannot seal (the cut graph
does not close into loops), the closure test is insufficient — the named
successor: per-component edge-walk validation inside the importer before
it answers ok. If A1 fails on a CLOSED mesh, the divergence bookkeeping
(inventory: seal caps vs the wall disc) is the suspect, not the import.

## RUN RECORD (2026-09-13, accepted-import crash — closed by C1)

- The closure falsifier HELD live: a leaky mesh was refused by name
  ("mesh not closed: K boundary edges"). The ACCEPTED path crashed the
  engine (AV in a _Tree op, blob wrote through first).
- OFFLINE REPRO: the exact sphere class (2946 verts, pole caps, quad
  rings, plain + slashed faces) through import_mesh under
  _GLIBCXX_DEBUG bounds checking — ALL PASS, payload size equation and
  index bounds verified. The importer does not corrupt the heap.
- ROOT CAUSE (engine-side, not the importer): MembraneTick::init()
  rebuilds the cell field but does NOT clear the seal tree
  (seal_cells_/sealed_/seal_nv_/cut_src_/cut_pos_), so step()'s seal
  block keeps reading verts9 through the RESIDENT creature's slot ids on
  the first tick after a mesh swap — far out of bounds when the old body
  had more vertices than the import (18459 -> 2946 is a ~600 KB
  over-read). The boot restore replays the seal history, so a fresh boot
  of a sealed session is armed for it.
- FIXES: (1) /mesh_import no longer replays /mesh_bin via nested
  invoke_api — it applies g_mesh_req directly under g_mesh_mutex with
  the wait_for_shutdown ack (/mesh_bin's own discipline), and writes NO
  snapshot blob (an import is reproducible from its source file; a
  poisoned blob must not boot-loop the engine). (2) Importing onto a
  SEALED tick is refused BY NAME until init() clears seal state — the
  one-stanza engine-side fix that retires the guard is init()'s to make
  (membrane_tick.cpp is not C1's file).




---

# THE MOVEMENT LAW PREREGISTRATION — THE FALL (fleet C2)

Operator directive (docs/THE_SHIP_GOAL.md): "no move-forward — the
creature sits in a gravity environment; the only way to operate is to
move your limbs and adjust your body relative to the surface of
gravitational resistance." The falsifier that keeps it honest: A
CREATURE THAT CANNOT FALL CANNOT WALK. The first bar is the FALL.

## STATEMENT

The body has mass; gravity pulls it; the ground holds what presses it;
nothing else holds the creature up. One rigid root DOF along Y carries
the whole body: y'' = -g + F_contact/m, F_contact a penalty spring read
ONLY at the body's lowest vertex against the floor y=0. Uniform
translation changes no volume, no normal, no pose, no sealed cell —
the seal/press/touch arithmetic is untouched BY CONSTRUCTION (the
offset applies after every other pass in the tick).

## DERIVATION

- MASS (from the sealed cells, not chosen): the sealed whole is
  13.824536 m^3 (this file, the 2-cell and 15-cell run records; the
  cells sum to 13.824502). Water at 25 C: rho = 1000 kg/m^3 ->
  m = 1000 x 13.8245 = 13,824.5 kg.
  Weight W = m g = 13,824.5 x 9.81 = 135,618 N.
- GROUND (penalty spring, derived from the 1-cm bar): at rest the
  spring carries exactly the weight, k x sink = W. Target sink
  s* = 0.01 m (the bar: <= 1 cm at rest) ->
  k = 135,618 / 0.01 = 1.3562e7 N/m.
  omega_n = sqrt(k/m) = sqrt(1.3562e7 / 13824.5) = sqrt(981.0)
          = 31.32 rad/s   (= sqrt(g/s*), mass-independent).
  Damping ratio zeta = 0.7 (settle without ringing):
  c = 2 zeta sqrt(k m) = 1.4 x sqrt(1.3562e7 x 13824.5)
    = 1.4 x 4.330e5 = 6.062e5 N s/m.
  Settle time ts = 4/(zeta omega_n) = 4/21.92 = 0.18 s.
  Force cap 50 W = 6.78e6 N (a floor, not a launcher: the worst
  clamp-escape deceleration stays <= 49 g). Clamps: |root_y| <= 3 m,
  |root_vy| <= 30 m/s.
- THE MEASURED INITIAL CONDITION (2026-09-13,
  session_snapshot/mesh_bin.blob — the exact blob the boot restore
  replays; 18,459 verts, 36,630 tris): authored rest lowest vertex
  y = -0.019507 m, 50 verts below the floor — the sculpt already
  presses 1.95 cm into a floor at y=0 (the matter pass's
  y_ground = -0.0195 corroborates). Consequence, derived: at enable,
  depth 0.0195 m gives contact 1.95 W = 2.65e5 N against W = 1.36e5 N
  — net UP 0.95 W. From THIS rest the root RISES 9.5 mm to the
  equilibrium; from any state with the lowest vertex at/above the
  floor it FALLS (free fall at g until contact), settling at the same
  W/k = 1.0 cm penetration. One law, two branches, pinned by one
  measured number.

## PREDICTIONS

F1. THE FALL: with gravity enabled and muscles slack the root moves
    along Y measurably (>= 3 mm) within 1 s (derived: the motion is
    complete in ~0.2 s) from ANY start. A body whose lowest vertex is
    at/above the floor DROPS — the directive's fall, testable the
    moment a pose, step or lift law raises the body clear of y=0. The
    measured authored rest (2 cm pressed in) RISES to equilibrium.
    If the root does neither — or sinks through the floor — the law
    failed, not the sculpt.
F2. REST: settled penetration = W/k = 1.0 cm (bar: <= 1 cm + float
    tolerance), root velocity -> 0, and every sealed-cell pressure
    stays EXACTLY 0 (uniform translation: dV = 0 so dP = 0 — volumes
    are computed on the un-offset verts each tick by construction).
F3. NOTHING ELSE CHANGES: pose, touch, lessons and the seal sums are
    untouched — |conserve_pct| holds its pre-gravity value (bar:
    <= 0.01%) and the 13.8245 sum stands.

## FALSIFIER

The body neither drops (from a floor-clear start) nor rises to the
1-cm equilibrium (from the measured start), OR rest penetration
exceeds 1 cm, OR rest pressures go non-zero, OR conservation breaks:
the movement law failed. Named successor audit, in order: (1) the
contact sign/depth convention in the step() gravity block,
(2) the translation-invariance assumption in the seal divergence
sums, (3) the boot-restore mesh placement — a sculpt whose feet live
2 cm under the floor is a modeling artifact the WALK law must own,
and the walk (the next bar) needs a root that can leave the floor
entirely.

## RUN RECORD

(open — the lead wires POST /tick_gravity {"on":true|false} ->
MembraneTick::set_gravity at the build window, flips the
gravity_on_ initializer to true after the bar passes, runs
tools/gravity_test.py, and appends the measured curve here.)

---

# THE KERNEL STREAM PREREGISTRATION — delta compression for /verts (fleet C3)

The named successor of the web-kernel prereg above (its falsifier: "delta
compression for the stream (only changed verts) — named now as the
internet-scale successor"). W4 measured the cost: 18,459 verts x 9 f32 =
664 KB per pull at ~3 Hz — ~2 MB/s of state per viewer, localhost-free
only because localhost forgives. The internet does not.

## STATEMENT

The stream shrinks >10x on a resting/posed body with no visible
stutter: /verts?delta=1 answers with a kernel-stream frame — a version
byte + changed-run encoding ([u32 start][u32 count][f32*9*count] per
run, bitwise "unchanged" = bit-identical) chained against the route's
previous delta-served export, with a full keyframe every 60 delta
polls (resync bound) and a u32 seq on every delta-framed emission
(a dropped or interleaved poll is DETECTED, and one keyframe pull
heals the chain immediately). The legacy framing [u32 n][f32*9n] is
untouched for every request without ?delta=1.

## DERIVATION (why the honest delta is "changed verts", before any code)

- The payload is already f32 — quantization is spent; nothing is left
  to squeeze there. The only honest redundancy left is TEMPORAL: the
  same vertices re-sent unchanged.
- IDLE IS BIT-STABLE, not approximately stable (membrane_tick.cpp,
  read before writing this): apply_chain with all rig angles 0 assigns
  verts9 = base_pos_ — a copy, bit-identical every tick; the tint
  rewrite is a pure function of load (load = 0 at rest -> base color);
  the posed-normal pass is a pure function of the positions. Pure
  functions of identical inputs give identical outputs, so consecutive
  exports of a resting body are byte-identical and the idle delta is
  the frame header alone.
- POSE (rig path): a pose rotates one part's vertex RANGE
  (start..start+count) — the moved set is a fraction of the body.
  Press: a 3 cm Gaussian with a 9*r0^2 cutoff — the moved set is a
  local patch, and a HELD press is steady state (bit-stable again);
  only the press/release transients stream.
- WORST CASE IS BOUNDED BY CONSTRUCTION: if every vertex changed, the
  run encoding would cost payload + 8 bytes/run, so the route emits a
  keyframe whenever the runs would not beat the full frame — a delta
  must never cost more than the thing it compresses.
- THE CHAIN IS EXPLICIT BECAUSE IT MUST BE: a delta is defined against
  the previous DELTA-SERVED export, so a dropped poll (or a second
  interleaved delta client) would silently corrupt any client that
  kept applying. Hence the seq on every emission: gap -> one keyframe
  pull -> healed. The periodic keyframe bounds whatever the seq cannot
  see. 60 polls was named in the directive; at the page's 3 Hz that is
  a ~20 s bound, and the seq gap makes it a backstop, not the healer.

## PREDICTIONS

K1. IDLE: mean delta pull < 60 KB over a 30 s idle phase (>10x vs the
    664 KB legacy pull) — the derivation says the header alone
    (16 bytes) unless the bit-stability premise is wrong.
K2. POSE: mean delta pull < 200 KB over a knee cycle (25 deg <-> 0
    every 5 s) — the posed part's range, not the body.
K3. BIT-EXACT RECONSTRUCTION: the stream is a transport encoding, not
    an approximation — a client that applies every frame reconstructs
    the exported state byte-for-byte (the bench applies each delta to
    a reference copy and demands equality with the next keyframe's
    payload).
K4. THE PAGE NEVER STUTTERS: delta frames apply into the persistent
    Float32Array with zero per-poll payload allocation (validation is
    a header walk; runs copy in place); the GL upload path is
    unchanged; a malformed delta costs one extra full pull, never a
    freeze.
K5. TORN FRAMES ARE REFUSED, NOT SHOWN: a truncated run body, a run
    past the vertex count, trailing bytes, a bad header — every one
    throws BEFORE any state is touched (the page keeps its last full
    state until a keyframe lands); a dropped poll (transport loss
    simulated in the bench) is caught by the seq gap and healed by one
    keyframe pull, and the state then verifies bit-exact again.

## FALSIFIER

A torn frame visible in the browser: any state written by a failed
decode, any partial run applied, OR the bars missed (idle mean >= 60 KB
or pose mean >= 200 KB), OR a reconstruction mismatch the seq did not
explain. On failure the successor is named, in order: (1) per-vertex
quantization inside the runs (f32 -> 16-bit fixed point — the values
came from authored sculpts, not instruments), (2) a real wire codec
(LZ4 class) under the same framing, (3) a per-client chain (session
state server-side) if interleaved viewers prove common.

## OPEN (named)

- Multi-client concurrency: v1 keeps ONE chain (single-viewer law).
  A second delta client survives by seq gap -> keyframe resync every
  interleaved poll (correct, degraded to full pulls), never corrupts.
- The game_shell front door (tools/game_shell/server.py) strips query
  strings on /api/verts — until the lead passes the query through,
  page deltas degrade to full frames (safe: the decoder accepts both
  framings). The bench hits the engine directly, so the measurement
  does not depend on the door.
- Tint-only churn (the visibility pass rewrites colors every tick):
  at rest it is provably constant; under load it rides in the runs
  with everything else. If K1 fails with position-stable colors, the
  successor splits color channels from position runs.
- GET with a body-less 502 from the front door during engine restarts
  is unchanged behavior — the stream adds no new failure mode there.

---

# F2: /FRAME FAST PATH — PREREGISTRATION (agent F2, fleet 2, slot-01, 2026-09-13)

Rule 0: statement, derivation, prediction, falsifier — BEFORE the code.
The target: GET /frame's ~1.1 s floor (the trailer had to be time-remapped
because of it; the website's thumbnail channel pays it too).

## STATEMENT

A preview-quality fast path serves /frame frames in <= 200 ms: JPEG
(Windows Imaging Component — in-box, no new libs) when the request asks
`?fmt=jpg`, encoder quality `?q=` (default 85), and the box-filter
downscale applied BEFORE encode so the encoder sees the small buffer,
never the full 14.7 MB one. The default route (no params) stays
byte-identical: full-resolution PNG. The capture/fence discipline
(request_capture -> capture_ready -> capture_frame) is untouched.

## DERIVATION (where the 1.1 s goes, from the code as it stands)

1. Fence: the route waits capture_ready — paced by the render thread,
   one frame + vkQueueWaitIdle inside readback_captures (engine.cpp).
   Milliseconds at a healthy frame pace. NOT this task's file.
2. Copy: capture_frame() copies capture_rgba_ — 2560x1440x4 = 14.7 MB,
   ~2-5 ms. Unavoidable at the route; the staged-downscale successor
   would have to live on the render thread.
3. Encode: png::encode_rgba is an UNCOMPRESSED stored-deflate PNG — a
   second 14.7 MB scanline copy + a bitwise CRC32 (8 iterations per
   byte, ~118M ops) + Adler-32 over the whole buffer: the measured
   0.5-0.8 s single-threaded, the DOMINANT term. The honest wins:
   (a) JPEG at q85 through WIC — ~5-10x over the stored-PNG encode;
   (b) downscale BEFORE encode (the existing ?w= nearest-skip upgraded
       to a box average): every encoder-side term shrinks from 14.7 MB
       to ~2.4 MB at w=1024;
   (c) ?q= clamps 1-100, default 85 — a taste number that belongs to
       the HUMAN; the machine does not pick it.

## PREDICTION

/frame?w=1024&fmt=jpg serves in <= 200 ms at ~60-400 KB; /frame?fmt=jpg
(full res) also beats the PNG floor. The lead benches at the build
window (port 8107), two runs each with the first discarded (one-time
COM init on the server thread), and appends the RUN RECORD below:

```
curl -s -o /dev/null -w 'png full      %{time_total}s  %{size_download}B\n' 'http://localhost:8107/frame'
curl -s -o /dev/null -w 'png w=1024    %{time_total}s  %{size_download}B\n' 'http://localhost:8107/frame?w=1024'
curl -s -o /dev/null -w 'jpg q85 w1024 %{time_total}s  %{size_download}B\n' 'http://localhost:8107/frame?w=1024&fmt=jpg'
curl -s -o /dev/null -w 'jpg q60 w1024 %{time_total}s  %{size_download}B\n' 'http://localhost:8107/frame?w=1024&fmt=jpg&q=60'
curl -s -o /dev/null -w 'jpg q85 full  %{time_total}s  %{size_download}B\n' 'http://localhost:8107/frame?fmt=jpg'
```

(One engine launch with CHIMERA_FRAME_BENCH=1 gives the stderr
copy/downscale/encode decomposition; fence = curl total minus those.)

## FALSIFIER

The fast path serves slower than 400 ms, OR q85 artifacts are visible
to the eye on the thumbnail channel, OR the default PNG route's bytes
change. Named successor, in order: (1) render-thread-side staged
downscale (blit to a small target before readback) — engine.cpp
surgery, explicitly NOT agent F2's file; (2) a real compression stage
in png_encoder.hpp; (3) the operator's taste on q.

## RUN RECORD

(open — the lead runs the bench commands at the window and appends the
measured numbers here.)

---

# THE STANCE PREREGISTRATION — THE BALANCE RUNG (fleet 2, F1)

Operator directive (the movement law, next rung): the body keeps itself
balanced by adjusting ankle/hip poses; the falsifier that keeps it
honest: CUT THE BALANCE AND IT FALLS. Gravity is live (the movement-law
rung above): the body has mass, the floor holds what presses it, and
nothing else holds the creature up. This rung adds the second law:
THE BODY RIGHTS ITSELF.

## STATEMENT

A stance controller reads the body's LEAN — the horizontal (xz) offset
of the whole-body posed centroid from its support — and drives BOTH
ankles (pins 17/18, joints28 order: 17 = ankle_L, 18 = ankle_R) as ONE
servo:

  dtheta/dt = -k_p * lean_z,   |theta| <= 5 deg,   only while gravity is on.

Poses only: no root teleporting, no invented forces (the movement law:
locomotion comes later, by limb forces against the ground; stance is
the keep-your-feet-under-you law that precedes it). The loop is an
INTEGRAL servo: the plant theta->lean is a static gain and the
controller integrates lean into theta, so a PERSISTENT disturbance — a
held touch, a held pose — nulls exactly: lean_ss -> 0 with
theta_ss = D/|S|. Poses the servo does not own (every pin except
17/18) are the disturbance channel; the touch is the force channel.

## DERIVATION (measured on the mesh BEFORE implementation —
monkey_full.bin, the 18,459-vert / 36,630-tri body the boot restore
replays; the vertbind replicated exactly as classify_run.py posts it)

- THE SUPPORT SET IS FROZEN AT STANCE-ENGAGE, and that is a measured
  necessity, not a convenience. The support is the rest blend's min-y
  band (y <= lowest + 5 cm): 186 verts. A per-frame re-selected band
  CHASES the ankle pitch — the toe dives into the band while the heel
  rises out — and self-cancels the very channel the servo drives:
  measured d(lean_z)/d(theta) = 0.056 m/rad re-selected vs 0.283 m/rad
  frozen (a 5x collapse). The contact patch is identified ONCE, at
  engage; its membership is then fixed while its positions keep riding
  the posed surface every tick.
- THE ACTUATED SUBSPACE IS SAGITTAL ONLY (disclosed): apply_travel
  rotates EVERY pin about the X axis (a YZ-plane rotation; the pin
  axis field is inert). Ankle flex moves the support centroid along z
  only. The coronal (x) lean is measured and reported but UNACTUATED —
  the hips are no reserve for it (they are X-axis too); coronal stance
  needs a twist axis in the travel law and is named OPEN. The touch is
  delivered sagittally (+z at the hip) so its lean lands in the
  actuated subspace.
- SENSITIVITY AND GAIN (no magic numbers): with the support frozen,
  symmetric ankle flex measures d(lean_z)/d(theta) = -0.283 m/rad at
  1 deg and -0.316 m/rad at 5 deg (12% superlinear). The engine probes
  its OWN arithmetic at enable — a +1 deg symmetric ankle pose on the
  rest blend, the same travel path step() runs — and derives
  k_p = 1/(|S| * tau) with tau = 1 s (the nulling bar: a disturbance
  nulls to 1/e in one tau, so a 2 cm step is under 0.5 cm at 2 s),
  k_p ~= 3.5 rad/(m s). Discrete stability at the tick:
  k_p*|S|*dt = 3.5*0.283*0.016 = 0.017 << 2 — a monotone first-order
  lag. Timescale separation: contact settle 0.18 s << tau_lean 1 s —
  the root spring tracks the ankle rock (sole lever ~+-theta*0.1 m,
  about +-9 mm at 5 deg) without fighting it.
- AUTHORITY (the honest budget): A = |S| * 5 deg = 2.5-2.8 cm of lean.
  THE BRIEF'S "A 5 CM LEAN CORRECTS WITHIN +-5 DEG" DOES NOT CLOSE AND
  IS NOT FAKED: 5 cm needs 9-10 deg of ankle. The within-authority
  disturbance class is |D| <= 2.8 cm; S2b below MEASURES the authority
  itself. The hips-as-reserve extension is quoted, not built: the leg
  lever is ~3.1 m (hip pin y 3.415, sole y ~0), so hip flex carries
  ~5.4 cm/deg — 1.8 deg per cm — the next rung's actuator.
- THE FLAT BLEND BOUNDS THE DISTURBANCE CHANNELS (measured per pin,
  cm of lean_z per +1 deg, frozen support): ankle 0.247 each (the
  servo); knee 0.177 (EXCLUDED — knees bind the same foot verts as the
  support, so a knee disturber moves both sides of the ledger); wrist
  0.080, elbow 0.016, neck 0.008, the spine trio ~0.002 EACH.
  apply_travel is a FLAT blend (no FK chaining): posing spine_lower
  tilts its own ~1 m belly patch and the head never follows — the
  torso trio at 5 deg each measures 0.05 cm of lean, worthless as the
  brief's spine-lean disturber. The measured mass-shift channel is THE
  ARM SWING: symmetric wrists -0.16 cm/deg, symmetric wrists+elbows
  -0.19 cm/deg (wrist ROM -30/+60, elbow -145/+125) — the physical
  "shift your own weight" disturbance, ~50-60 deg of ramp to cross
  10 cm.
- THE TOUCH CHANNEL IS SMALL (measured, and said plainly): a 20 kN
  press at the hip dimples the 50 verts inside its 9 cm Gaussian reach
  by up to delta = F/(4 pi sigma) = 0.398 m, which shifts the
  whole-body centroid by D = 0.11 mm. The touch bar is therefore
  NULLING of a persistent force-channel disturbance (residual <= 25%
  of the excursion at 2 s — the integral action is what passes it),
  not a centimeter excursion; the centimeter scale belongs to the pose
  channel. The brief's "lean returns under 2 cm within ~2 s" is
  contained by the measured bars at every scale.
- THE REST REFERENCE: at authored rest the body centroid is NOT over
  the support — rest lean = (-0.0002, -0.8366) m (x, z): the tail
  (tail_tip z = -4.21) puts 0.84 m of rest "lean" into the metric.
  The controller nulls the ERROR FROM AUTHORED REST: lean_ref is
  measured at enable on the rest blend (the same arithmetic path
  seal() uses for v0), not assumed zero.

## PREDICTIONS

S1. TOUCH NULLING (gravity on, stance on): a 20 kN sagittal hip touch
    (hit = the +z-most vert of the hip band 2.0 <= y <= 4.5 — measured
    vert 16140 at (-2.68, 3.32, 0.83), authored normal (0.12, 0.25,
    0.96)), held 3 s, excites lean by ~0.1 mm and the servo nulls it:
    residual <= max(25% of the excursion, 0.02 mm) within 2 s, ankles
    within +-5 deg. On touch_clear the dimple decays (tau 0.5 s, the
    0.1 mm cutoff at ~4.2 s) and lean returns to baseline.
S1b. POSE-LEAN NULLING (the within-authority bar): a symmetric wrist
    step sized to ~2 cm of lean (~12 deg at -0.16 cm/deg) with stance
    on: lean nulls to <= 0.5 cm within 2 s (tau = 1 s predicts 27%
    remaining), ankles settle at theta_ss = D/|S| ~ 3.8 deg <= 5 deg —
    no saturation; on release the servo unwinds to ~0.
S2. THE FALL DIRECTION (stance OFF): the arm-swing channel ramped
    (wrists+elbows, +5 deg steps) crosses |lean| = 10 cm within the
    ROM (predicted ~50-60 deg of ramp) and HOLDS >= 90% of its
    end-of-ramp value through a 2 s hold: the un-righted body keeps
    its lean. Disclosed: the kernel root is ONE DOF along Y, so the
    uncontrolled body cannot topple yet — the fall analogue is
    UN-RIGHTED LEAN; the divergent toppling bar (lean growing without
    a growing push) becomes testable when the kernel gains root xz
    and is named for that rung.
S2b. THE AUTHORITY LAW (stance ON, the same ramp): the servo nulls the
    early ramp, then the ankles PIN at 5.0 +- 0.2 deg and lean holds
    at (disturbance - authority). Because the travel blend is an exact
    per-vertex weighted sum, the channels superpose exactly, so the
    measured |lean_off - lean_on| at the final hold IS the ankle
    authority: predicted 2.76 cm (|S| at 5 deg = 0.316 m/rad), bar
    [2.3, 3.3] cm, with no oscillation across the hold (the
    state-clamped integrator degrades gracefully — no windup, no
    ringing).
S3. NOTHING ELSE LIES: |conserve_pct| <= 0.01 at every phase; sealed
    pressures EXACTLY 0 at rest before and after (while the servo runs
    the ankles bend the surface and the water law answers dP there BY
    DESIGN — rest is rest); teardown returns the ankles to exactly 0
    and lean to baseline; the root rest state (root_y, root_vy) is
    unchanged by stance having run.

## FALSIFIER

Stance-on fails to null a within-authority disturbance (S1b), or
stance-on is indistinguishable from stance-off (S1b/S2 — the
controller is theatre), or the ankles saturate on a disturbance inside
the derived authority (2.8 cm), or S2b's measured authority falls
outside [2.3, 3.3] cm, or conservation breaks while the servo runs.
Named gain audit, in order: (1) the SIGN of S in step() — a positive
sign fights the lean and diverges monotonically, unmistakable within
one second; (2) the support set — frozen membership vs a re-selected
band (the measured 5x self-cancel is the known failure); (3) the |S|
probe — the engine's own +1 deg ankle probe at enable vs this file's
0.283 m/rad; (4) the dt clamp / tick rate (the servo integrates at
most k_p*lean*0.05 per tick); (5) the rest reference (lean_ref
measured on the rest blend, not assumed zero).

## RUN RECORD

(open — the lead wires POST /tick_stance {"on":true|false} ->
MembraneTick::set_stance next to POST /tick_gravity at the build
window, runs tools/walk_test.py, and appends the measured curves here.
The script is HTTP-only and does not build or run the engine.)

---

# THE GAIT CHECKPOINT PREREGISTRATION — THE ROBOT STACK'S RUNG 2
## (agent G1, fleet, slot-01, branch astra/tasks/matter-kernel-format-01, 2026-09-13)

Per docs/THE_SHIP_GOAL.md "THE ROBOT STACK LAW": the character must carry the
concepts of people who build and train robots — checkpoint systems, sensing,
knowing where to put its foot, what-if questions asked before acting.

## STATEMENT

Stepping on this body is produced by a per-leg checkpoint machine — STANCE ->
LIFT -> REACH -> LOAD, plus RECOVER (the measured abort) — in which EVERY
transition is gated by a number the body reports (per-side foot contact depth
against the floor plane, sealed-cell pressures, lean and support geometry
measured from the posed surface) and NO phase advances on a timer; dt enters
only through the rate caps and the servo integration. The machine actuates
ONLY through joint_deg_ poses on hip/knee pins 13-16, rate-capped so the
foot's arc speed never exceeds its own support-patch radius per second — no
teleporting. The ankles (pins 17/18) stay F1-owned: the G1 block runs AFTER
the stance block in step() and composes over it. SCOPE (lead-approved): the
root DOF is Y-only, so this rung delivers the checkpoint machine and MEASURED
weight transfer in the planted frame; horizontal advance belongs to the rung
that owns a horizontal root. No z-root snapping from G1 — a root snap would
slide the feet, which is the glide the falsifier forbids.

## DERIVATION (no sweeps — every number traced to a named law)

- NO new tunings. Bars reused: clearance = STANCE_BAND_M (F1's 0.05 m band)
  above the floor, i.e. a total rise of sink + band = 0.06 m from rest;
  contact = world min-y < 0; bearing = depth >= 0.8 x the derived rest sink
  (0.01 m, header); settle = |root_vy| <= 1e-3 m/s (the 0.1 mm press-cutoff
  scale); stride = the swing foot's centroid must pass the STANCE foot's live
  centroid by the swing foot's own measured patch radius (the new footfall
  lands outside the old support patch — geometric necessity); pose-relax
  witness = the repo's named 50 kPa gentle-hand threshold, LOGGED at every
  transition, NOT gating (reason: F1's held ankle pitch keeps real pressure
  in the leg cells between strides — a hard p-gate would stall honestly but
  forever; the depth+settle gates carry the transition).
- CHANNELS PROBED, NOT GUESSED (the F1 +1 deg probe precedent): at enable,
  on the exact rest blend (the seal()/set_stance path), each hip/knee is
  probed at +1 deg and the SIGNED d(foot-set min y) and d(foot centroid z)
  are measured per pin. Servo law is F1's own structure: dtheta =
  err/(channel*TAU) with STANCE_TAU_S — angle signs come from the measured
  channel, never from anatomy assumptions. Enable REFUSES if any pin's arc
  channel < 1e-3 m/rad (the F1 no-channel refusal) — a body whose legs
  cannot rise is honestly refused, not tuned around.
- THE LIFT COMBO: hip and knee are driven together by the ratio that nulls
  the centroid z drift (a_h = dcz_knee, a_k = -dcz_hip), with rise channel
  ch = a_h*dminy_hip + a_k*dminy_knee — derived from the probes, not chosen.
  Rationale: this sculpt's sagittal rotations about X give a first-order
  rise of -(z_foot - z_pin)*theta, which can be near zero for a planar leg;
  the LIFT gate is measured (min-y >= STANCE_BAND_M), so the linear-channel
  estimate only sizes the step, and the measured error closes the rest.
- RATE CAPS: per pin, rate = (patch_radius / STANCE_TAU_S) / |arc channel|
  — the foot's linear speed never exceeds its own footprint per second.
- FROZEN SETS (the F1 lesson, measured 0.056 vs 0.283 m/rad): per-side foot
  vertex sets, patch radii, rest foot z and lean references are frozen at
  enable from the rest blend. The REACH reference is the STANCE foot's live
  centroid only — including the swing foot in the reference set would chase
  the actuated limb (the exact self-cancel failure F1 measured).
- THE WHAT-IF GATE (rung 4, answered from live numbers before acting):
  LIFT entry requires the body centroid to already lie inside the would-be
  stance foot's measured patch — "if I lift this foot, does the support hold
  my weight?" Refusal to lift is logged with the blocking number.
- THE SCHEDULE: when both legs qualify, the leg that stepped LONGER AGO
  swings — a deterministic controller decision, never a gate; the gates
  stay measured. init() clears all gait state (the C1 stale-index class).
- LOAD/RECOVER actuation is return-to-zero at the measured rate caps (the
  authored rest pose IS bearing: home + ground), with the EXIT gated on the
  body's numbers (depth >= bearing bar AND |root_vy| settled). DEVIATION
  from the plan as posted to the lead: the posted LOAD design servoed foot
  z and y independently; implementation returns the pose to bearing and
  lets the measured gates decide — fewer channels, same gates, documented
  here per docs-last.

## PREDICTIONS (unmeasured at prereg time)

- P1 (weight transfer): during single support, d_swing < 0.2*sink while
  d_stance converges to the same 1 cm sink within [0.8, 1.2]x — the mass
  rides one foot, measured; leg-cell pressures exceed the noise floor
  mid-swing and the transition log's pmax returns under 50 kPa at LOAD exit.
- P2 (cadence): each phase converges in ~tau per the 1/(channel*TAU) law;
  a full stride completes within ~8 tau, readable from the gait_log ticks.
- P3 (THE CUT): POST /tick_gait {"on":false} mid-swing -> within one tick
  every controller-driven foot motion stops (pins 13-16 at authored 0) and
  a root transient |root_vy| > 1e-3 appears — the stumble number. The cut
  is logged with the measured depth/vy/pose (the "cut" gate entry).
- P4: |conserve_pct| stays < 0.01 (F1's S3 bar) through every phase — the
  machine adds no volume leak.
- P5: no gateless moves — every gait_log entry carries its measured gate
  values; state and log cannot contradict.

## FALSIFIER (named before the run)

- F-GLIDE: any controller-driven foot motion beyond one tick after the cut,
  or stepping that continues with the machine off -> it is animation, not
  control -> FAIL.
- F-STALL: any phase not reaching its measured gate within 10 tau without
  ROM (89 deg, under pose_index's law) or rate saturation -> the derivation
  is wrong -> FAIL; amend with the logged channel and deficit.
- F-TELEPORT: foot centroid jump > rate_cap*|channel|*dt between ticks while
  on -> the pose channel teleported -> FAIL.
- F-LIE: a transition logged without its measured gate values, or a LIFT
  entered outside the what-if envelope -> the gates are decorative -> FAIL.

## RUN RECORD

(open — the code is landed, marked // G1 in membrane_tick.{hpp,cpp},
syntax-checked (g++ -std=c++17 -fsyntax-only -Wall -Wextra: clean; the only
warnings are pre-existing in touch_press). The lead wires POST /tick_gait
{"on":true|false} -> MembraneTick::set_gait next to POST /tick_stance at the
build window. Arm order: gravity on (live) -> /tick_stance on -> /tick_gait
on; watch /tick_state (gait_* fields). The falsifier run: cut /tick_gait
mid-swing and read P3 off gait_log. Not persisted across boots (the same
switch class as gravity/stance): after a restart the lead re-arms. The
harness is HTTP-only and does not build or run the engine.)
