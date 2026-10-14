# PREREGISTRATION — the femoral-head PIVOT measurement + the hip proof (`hip_pivot_proof_20260921`)

Lane `agent/hip-pivot-proof-20260921`, base `7b752929` (branch `agent/articulation-semantics-20260921`,
the design head). Read-only consumption of the committed kernel, engine-independent, definition-untouched.
This file is banked (`preregistration.sha256`) BEFORE any sphere is fit and BEFORE any seat number is
measured. The design's §5 preregistration (`docs/THE_ARTICULATION_LAW.md`, hashed
`f4a1390e3a960917a9651ff93b45bd78872946819438cb14a30a7e3838e835a0` in the design lane's
`preregistration.sha256`) is this lane's PRIOR; everything below it is this lane's pre-registered block,
written before measurement. No number in this file is chosen by taste: each is committed, cited, derived
by a stated formula, or a PREDICTION carrying its own falsifier.

---

## 1. THE PRIOR — §5 of docs/THE_ARTICULATION_LAW.md, VERBATIM

**STATEMENT.** The hip bond is an articulation-class bond: with a derived pivot (femoral-head
center fit on bone_02's committed vertices), a derived flexion axis (the bilateral line through
the two hip pivots of `bond.joint_01_02` and `bond.joint_01_03`; sign set by the recorded curl —
the pose_contacts carry the specimen's own flexion direction), and a cited adult-band range
record, the femur membrane rigidly re-orients about the pivot through the anatomical range while
the seat holds, cure still fails at exactly `cure·A`, mass is exactly invariant, and θ = 0 is the
committed bytes. Someone can disagree: the head fit may not localize the true rotation center at
160 µm on an under-mineralized infant specimen, and the adult range band may not contain the
infant's seats.

**PREDICTIONS (not yet measured).**

- **P1 rest identity (A1):** posed bone_02 bytes hash-equal to `tris/bone_02.bin` at θ = 0.
- **P2 seat through range (A2):** at the cited flexion and extension endpoints, the closest-point
  distance between posed bone_02 and bone_01 stays ≤ 3.0 mm (the touching-class cut that admitted
  the bond; dislocation band = the cut, named now, not after the run).
- **P3 cure invariance (A3):** `pull_bond` at θ = 0 and at each endpoint: identical
  `failure_force_n = cure·A`, identical holds/fails at the same test loads (13 MPa × the
  measured apposition area — the area record the successor lane pins at preregistration time).
- **P4 mass exact (A4):** derived mass of posed bone_02 equals rest to float equality.
- **P5 stop (A5):** θ beyond the recorded range refuses `out_of_anatomical_range`.
- **P6 the control's teeth:** the SAME protocol on a NULL pivot — the midpoint of the recorded
  `closest_points_mm` pair, zero new derivation — BREACHES the 3.0 mm cut at range extremes
  (rotating about the apposition point instead of the head center swings the head out of the
  socket). The design predicts arm A (head-fit pivot) passes P2 where the null arm fails: that
  contrast is the proof's content, and if the null arm PASSES, the pivot derivation is doing no
  work and the design's pivot law is void.

**FALSIFIERS (named before the run — any one voids the design as written).**

- **F1** P2 fails on the head-fit pivot at either endpoint → the pivot derivation or the class
  record is wrong; successor: re-derive the pivot (acetabular-side fit) or re-class the bond.
- **F2** P3 fails → cure is not rotation-invariant as a failure law → "joints are materials" is
  void; the successor must give joints a non-material semantics (C2's territory).
- **F3** P4 fails → the transform resamples → L2 is broken by the design, not by the kernel.
- **F4** the pivot derivation needs a number with no source and no derivation from committed
  geometry — e.g. a sweep over head-region rules until P2 passes → Rule 1 violation, VOID by
  definition.

**STATUS: PREREGISTERED-ONLY. UN-PROVEN, HONESTLY.** §6 states why this lane did not build it.

**THE PROOF SKETCH (for the successor lane, fenced exactly like this).** A read-only validation
lane `tools/science_funnel/validation/hip_articulation_<date>/` in the
`axial_adjacency_20260920` pattern: preregistration file (this §5 verbatim + the pinned range
record and apposition area) → `preregistration.sha256` banked BEFORE any measurement → the two
arms (head-fit pivot vs null midpoint pivot) → the A1–A6 battery on committed
`tris/bone_01.bin`/`tris/bone_02.bin` (36-byte triangles, stdlib `struct`) → `receipt.json`
(schema `chimera.rule0_receipt.v1`, falsifier verdicts verbatim). The pivot fit must be
pre-registered to the rule that fixes its inliers with zero free numbers; a fit tuned until P2
passes is F4 and the lane dies by its own receipt.

---

## 2. THE PINNED RANGE RECORD (cited, adult band, stage gap named)

- Record: `research_references/human/opensim/gait2392_thelen2003muscle.osim`, sha256
  `18e5b3e406a619a78d109e81e6e2cd4f58681a967808fb52a992bbd2b27db019` (committed on this base).
- Coordinates `hip_flexion_l` and `hip_flexion_r`, each `<range> -2.0943950999999998
  2.0943950999999998 </range>` rad — the closed flexion/extension band [−R, +R] with
  R = 2.0943950999999998 rad (±2π/3 ≈ ±120°), parsed FROM the committed file at battery time
  (no retyped constant).
- STAGE GAP, NAMED IN THE OPEN: this is an ADULT human gait model; the specimen is an infant
  macaque and no infant-macaque range citation exists in the held set. The adult band is the
  cited UPPER ANCHOR (the `mat.bone_cortical` stage_note pattern); any infant deviation is named
  when measured, never tuned away. The battery measures the seats AT the adult endpoints; an
  infant whose true range is narrower still has its seats inside this band (the band is a superset
  claim), and the endpoint seats are exactly what P2 measures.

## 3. THE PINNED APPOSITION AREA (the A of P3, derived — estimator fixed, number recorded)

- ESTIMATOR (zero free numbers): the apposition area of a hip = the summed kernel-formula area
  (definition.py's per-triangle cross-product accumulation, float64, blob order) of the CHILD
  bone's committed triangles whose CENTROID lies within 3.0 mm — the committed touching-class cut
  `bone_identification_v3.json derived_cuts.joint_gap_mm`, never re-chosen — of bone_01's
  committed bin VERTEX set (scipy cKDTree, float64). Conservative (centroid rule); deterministic.
- DERIVED NUMBERS (computed from committed geometry before banking; the battery recomputes
  canonically and must agree to ≤ 1e-9 mm²):
  - `bond.joint_01_02` (child bone_02): patch = 492 triangles, **apposition area
    A = 22.541335701 mm²**, nearest-centroid margin to the 3.0 mm cut = 0.000182 mm.
  - `bond.joint_01_03` (child bone_03): patch = 710 triangles, **apposition area
    A = 31.993611826 mm²**, nearest-centroid margin to the 3.0 mm cut = 0.000195 mm.
- The patch cut margins are positive (≥ 1.8e-4 mm ≫ float pose noise ~1e-12 mm), so the patch
  membership is stable under the rigid pose: the posed patch recompute must return the SAME
  triangle set (P3's area-invariance carrier).

## 4. THE INLIER RULE (F4's demand — fixed BEFORE any sphere is fit; zero free numbers)

The femoral-head surface class: the near-spherical cap region of bone_02/03's pelvis-side end,
selected by the following DETERMINISTIC rule on the committed bin geometry (36-byte triangles,
float32 LE; canonical unique-vertex dedup in first-occurrence order; face graph adjacency from
the bin's own triangles). The only numbers that enter are the committed apposition record, the
committed CT resolution, and formulas over the mesh's own resolution.

1. **SEED (committed data):** the bin vertex nearest (Euclidean, float64) the bond's recorded
   `closest_points_mm.on_0X` — the apposition point on the femoral head, measured and committed
   by the adoption lane. Reconnaissance (mesh resolution only): the recorded point matches a bin
   vertex to 4.3e-4 mm (bone_02) / 3.5e-4 mm (bone_03) — the record's own 0.001 mm rounding.
2. **BAND ε (the mesh's own resolution):** ε = the MEDIAN of the committed triangle set's edge
   lengths (each triangle's 3 edges, float64, all faces pooled), computed canonically by the
   battery: bone_02 → 0.310857620079 mm, bone_03 → 0.302305969593 mm. A vertex sampled on a
   sphere at spacing ε lies within one sampling step of the ideal surface; no multiplier, no
   margin. (The committed CT voxel, 0.16 mm = `specimen.resolution_um`, is the floor of that
   sampling scale and sits inside ε.)
3. **GROWTH (monotone-by-construction, anchored, to a fixed point):** S₀ = {seed}. Each
   iteration: (a) if |S| < 4 (the algebraic minimum to define a sphere — DERIVED, not chosen),
   S ← S ∪ graph-neighbors(S) (pure one-ring growth); (b) else fit the least-squares sphere to S
   (Kåsa algebraic lstsq init, then geometric Gauss–Newton refinement, max 200 iterations, stop
   at parameter step < 1e-13 — deterministic), and set S ← {v ∈ S ∪ graph-neighbors(S) :
   |‖v − c‖ − r| ≤ ε} ∪ {seed} (the seed is an ANCHOR: the bond record commits that the
   apposition point lies on the head). Stop when S stops changing (fixed point). If an iterate
   REPEATS a previous state (cycle), the rule REFUSES on this mesh (honest refusal → F1
   successor; no fallback, no re-tune). Iteration cap 10000 (machine guard, unreachable except
   as a refusal).
4. **MINIMUM INLIER COUNT (from the mesh's own resolution, derived):** the femoral head is a
   hemispherical articular cap (Hartman & Straus 1933, the bond's own anatomical reading), so the
   inlier set must hold at least the hemisphere tiled at the mesh's own area quota:
   N_min = ceil(2π·r_fit² / q) with q = (kernel-formula total area of the committed mesh) /
   (its unique vertex count) — bone_02 q = 0.086237072414 mm²/vertex, bone_03 q =
   0.086547724483 mm²/vertex. If |S*| < N_min the rule REFUSES (F1 successor).
5. **THE PIVOT:** c* = the Gauss–Newton geometric least-squares sphere center on S*; the fit's
   radius r, RMS and max residuals, and |S*| are reported per hip.
6. **SUBJECT CHECKS (the fit's subject must BE the femoral head):** (a) the recorded apposition
   point lies ON the fit: |‖on_0X − c*‖ − r| ≤ ε; (b) the center is on the pelvis side:
   ‖c* − on_01‖ < ‖c* − distal‖, distal = the committed vertex farthest from c*; (c) the scale
   band P0 below.

## 5. THE AXIS AND THE FLEXION SIGN (derived)

- **AXIS:** the bilateral line through the two fitted pivots: u = (c*_03 − c*_02)/‖c*_03 − c*_02‖
  (bone_02 = side "left" per its membrane record; bone_03 = the right femur per the bond's
  anatomical reading and the adoption receipt). One axis, shared by both hip rotations — the
  ball-and-socket reading: each head center lies ON the axis.
- **SIGN (the recorded curl is the measured flexion direction — §3):** θ_probe = R/5
  (in-range by construction). For each hip: d₊ = ‖pose(distal, +θ_probe) − q_chain‖ and
  d₋ = ‖pose(distal, −θ_probe) − q_chain‖, where q_chain is the hip's own hind chain's RECORDED
  curl contact on the composite (pose.joint_01_15.on_01 for bone_02; pose.joint_01_17.on_01 for
  bone_03 — committed pose_contacts). The flexion sign s* = +1 if d₊ < d₋ else −1 (the curl-ward
  rotation deepens the measured fetal curl). The demo pose is θ_demo = s*·θ_probe; the flexion
  endpoint is s*·R, the extension endpoint −s*·R.

## 6. THE PREDICTED NUMBERS (stated BEFORE the fit and the control run)

- **P0 pivot radius band (both hips):** r_fit ∈ [1.5, 4.5] mm. Derivation: a hemispherical cap at
  the mesh's own area quota q with a cap population in the 200–800-vertex window (the seed's
  graph neighborhood at rings 8–16, reconnaissance) gives r = sqrt(N·q/2π) ∈ [1.66, 3.31] mm;
  the prediction band is the widened envelope. OUTSIDE the band → the inlier rule failed to
  isolate a femoral-head cap → refusal → F1 successor. LITERATURE SANITY, stage gap named: no
  infant-macaque femoral-head-radius citation exists in the held set (Casteleyn et al. 2021/2023
  confirm the CLASS — a spherical head, fovea inferior — but publish no radius); the adult rhesus
  head is larger; the infant fit is expected at the band's LOW side. Absence recorded, never
  tuned (the definition's own stage_note pattern).
- **P6-as-written tick (the null arm CANNOT breach the ≤ 3.0 mm predicate — a DERIVED
  prediction, with the derivation):** let M be the recorded closest-points midpoint and w =
  on_0X − on_01 (|w| = the recorded refined gap). For EVERY rotation about ANY axis through M,
  pose(on_0X) − on_01 = (R(w/2) + w/2), whose length is |w|·|cos(θ/2)| ≤ |w| = 1.403 mm
  (bone_02) / 1.343 mm (bone_03) — inside the 3.0 mm cut for ALL θ, NOT just the endpoints. The
  realizing vertex is a committed bin vertex (matches the record to ≤ 4.3e-4 mm). PREDICTION: the
  null arm's law-metric min gap at ±R ≈ |w|·cos(R/2) = 1.403·cos(60°) ≈ 0.7015 mm (bone_02) /
  1.343·cos(60°) ≈ 0.6715 mm (bone_03) — the null arm PASSES §5-P2-as-written, and §5-P6's own
  clause ("if the null arm PASSES, the pivot derivation is doing no work and the design's pivot
  law is void") triggers ON ITS OWN TERMS. This lane reports that verdict VERBATIM and, with it,
  the diagnosis the derivation forces: the DEGENERACY is the PREDICATE's, not the pivot's — a
  global-min-gap cut cannot see a dislocation when the pivot sits inside the apposition gap. The
  two arm-discriminating numbers, pre-registered HERE:
  - **head-center displacement** ‖pose(c*) − c*‖: real arm == 0.0 EXACTLY (float-exact: c* is on
    the axis, (c−c)=0 in IEEE); null arm == 2·‖c*−M‖·sin(θ/2) at each endpoint (≈ 2(r+0.70)·
    sin 60° mm for bone_02 — the head demonstrably leaves the socket). Checked to 1e-9 mm against
    the formula.
  - **apposition-patch persistence:** the child's within-3.0-of-bone_01 patch recomputed at each
    endpoint pose (same estimator as §3, on posed centroids): real arm predicted to KEEP an
    apposition patch of the same order as rest (the head stays a sphere about an on-axis
    center); null arm's patch profile recorded without a cut-prediction (the head is driven past
    the cup wall — the coarse 1.6 mm composite shell makes vertex-level interpenetration
    readings genuinely open; MEASURED, REPORTED, NOT PREDICTED).
- **P2 real-arm tick:** the head's apposition gap profile is rotation-invariant about its own
  center, so the real arm's law-metric min gap at ±R is predicted ≤ 3.0 (seat HOLDS) with the
  realizing pair in the acetabular region (provenance recorded). F1 fires if it exceeds.
- **P4 ticks:** the posed patch recompute returns the SAME triangle set (margins 1.8e-4 mm ≫
  pose noise); P4b (numpy float64 areas of the transformed vertex set vs rest) deviates ≤ 1e-12
  relative (expected ~1e-16); the kernel-format mass derivation on the pose's canonical blob is
  BITWISE the rest derivation (the pose is a placement; nothing is resampled).

## 7. THE BATTERY (A1–A6, §4 of the design, verbatim obligations) + this lane's additions

- **A1 rest identity:** the θ=0 pose IS the committed blob (identity path — the engine's
  no-op-at-rest idiom): sha256(posetrib(0)) == sha256(tris/bone_0X.bin), both hips. ABSOLUTE.
- **A2 seat through range:** law metric = identify_bones_v2 symmetric min vertex-to-nearest-
  vertex (scipy cKDTree, float64) on the BIN vertices; child posed about (pivot, axis, θ),
  parent at rest. Measured at θ ∈ {−R, 0, +R}: min gap ≤ 3.0 mm, realizing pair provenance,
  patch stats. Metric-transfer preamble: the θ=0 gap must reproduce the committed measured_gap
  (1.44 / 1.49 mm) within 0.005 mm (the house transfer tolerance).
- **A3 cure at every angle:** glue.py `pull_bond` verbatim, inputs: members mat.bone_cortical
  (yield 100 MPa, Cowin/Currey via the kernel constants table), glue_area = §3's A (mm² → m²),
  member areas = the kernel-formula areas of the child/composite blobs (m²), cure 13e6 Pa
  (Yamada 1970). At θ ∈ {−R, 0, +R}: failure_force_n identical BITWISE across θ and == cure·A
  bitwise; force = F/2 → holds; force = F → fails AT the glue line; force = 1.5F → fails.
  Plus the posed patch-recompute equality (§6 ticks).
- **A4 mass exact:** P4a: the kernel mass law (validate_membrane formula) on the pose's canonical
  blob == the rest derivation BITWISE, and within the kernel's 5% of the membrane's stated mass;
  P4b: the resampling detector (transformed float64 areas vs rest) ≤ 1e-12 relative. Measured at
  θ ∈ {0, demo, −R, +R}.
- **A5 range is a stop:** pose requests at math.nextafter(hi, +inf), math.nextafter(lo, −inf),
  2R, −2R REFUSE with the exact name `out_of_anatomical_range` (carrying the recorded range and
  the offending θ); requests at −R, 0, demo, +R are ACCEPTED. The minimal violation
  (math.nextafter) is DERIVED — zero free numbers.
- **A6 definition untouched:** the committed definition, its tris bins, the osim record, and
  every prior lane's receipt files are opened READ-ONLY; sha256 before == after the run.
- **THE CONTROL ARM (P6):** pivots = the recorded closest-points midpoints (per hip), axis =
  (M_03 − M_02)/‖·‖ (the same construction on null pivots — zero new derivation), same range,
  same A2 protocol at {−R, 0, +R}, plus the §6 center-displacement and patch readings. The
  verdict is reported WHICHEVER WAY IT LANDS.
- **THE POSE RECORD (mission):** the top-level pose θ=0 ≡ the scanned corpse-pose (the DEFAULT,
  bytes-identical, A1), and ONE demonstrated non-zero pose per hip: θ_demo = s*·R/5 (in-range
  flexion by the §5 sign rule), with its Rodrigues-transformed vertex set (float64, NOT
  requantized — nothing resampled), its geometry hash, bbox, seat numbers, and the mass checks.
  L4 note: the recorded pose carries NO force or torque — metadata only, exactly like a
  pose_contact.
- **DETERMINISM:** byte-exact. The battery is timestamp-free, sorted-key, fixed-rounding JSON;
  run twice; the two battery.json sha256s must be EQUAL (falsifier: any drift VOIDs the lane's
  determinism claim).
- **KERNEL GATES (unchanged, must stay green):** `python -m tools.matter_kernel.test_definition`,
  `python -m tools.matter_kernel.test_glue`, `python tools/training_gate.py`.

## 8. THIS LANE'S FALSIFIERS (beyond the prior's F1–F4, named before the run)

- **L1 determinism:** the two battery runs' battery.json differ → the lane is not
  checkout-invariant → VOID.
- **L2 identity absolute:** any θ=0 path that does not reproduce the committed blob bytes
  bit-for-bit → VOID (the 2d585c7b LF law's spirit: bytes are the contract).
- **L3 gates:** any kernel gate fails → VOID (the lane consumed the kernel; it may not break it).
- **L4 untouched:** any committed file's sha256 changes during the run → VOID (F6 of the design).
- **L5 honest control:** the control is run exactly as registered (recorded midpoints, no
  substitution); its verdict is reported whichever way it lands. Suppressing or retuning it is
  VOID by definition.

Trailer: Agent: GLM 5.3
