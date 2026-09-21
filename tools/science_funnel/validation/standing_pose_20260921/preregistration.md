# THE STANDING POSE PREREGISTRATION — the first non-zero pose the class records lawfully admit

Lane `agent/standing-pose-20260921`, base `52f101c1` (agent/joint-class-records-20260921:
the 23 bonds of the committed skeleton definition all carry joint_class records; theta = 0 is
the committed corpse). Banked BEFORE the solve ran. Nothing in this file was measured after a
run; the design-time declarations are labeled as such.

## 1. RULE 0 MEMBRANE

**STATEMENT.** The class records admitted at `52f101c1` admit exactly one non-zero pose family
beyond the corpse: a SMALL CONSTRAINED OPTIMIZATION over the recorded DOFs whose objective is
the operational definition of standing — the four limb-end pads near one plane and the trunk
near level w.r.t. that plane — and the pose it returns is lawful iff every joint angle sits
inside its recorded class range, the P6' v2 predicate holds on both hips through the whole
transition path from theta = 0, both tarsal loops close at the pose, the six 0-DOF-class bonds
do not move relative to themselves, every posed mass is exactly invariant, the corpse
pose_contacts do exactly what their members' DOF paths say they must, and theta = 0 remains
the committed bytes. Someone can disagree: the objective's scalarization may not be THE
standing (a curled fetus and a standing animal can both satisfy pads-coplanar + trunk-level —
the measured rest readings below say the scan is nearly flat-packed already), and the solved
angles may be so small the pose is visually indistinguishable from the corpse. Both
disagreements are answered with numbers, not words: the solved angles, the achieved objective,
and the rendered before/after stills are recorded whichever way they land.

**DESIGN-TIME DECLARATIONS (read-only determinations on committed bytes/records, made in the
design phase, before this bank, before any solve; the battery re-measures them at run time):**
- rest pad scatter eigen-readings (pad set = the four distalmost limb-end membranes, section
  4): population-variance along the least eigenvector V_rest = 1.94384 mm^2; trunk-axis dot
  with the rest pad-plane normal d_rest = 0.010404 (a·n̂ = 0.102, the trunk ~5.9 deg off the
  pads' plane). The corpse is therefore NEAR-OPTIMAL in the objective already: the predicted
  standing pose is an IN-RANGE, INTERIOR, SMALL perturbation of rest (section 5, P-A3).
- the four forelimb elbow-apposition coordinates are the only DOFs whose recorded ranges EXCLUDE
  theta = 0 (monkeyArm elbow_flexion [0.34906585, 2.44346095]); every other movable class
  contains 0 (hips ±2.0943951, knees [-2.0943951, 0.17453293], radioulnar ±1.57079633, tarsal
  ±0.34906585). The first lawful non-zero pose is thus FORCED at the elbows and DERIVED
  everywhere else.

**PREDICTIONS (banked before the solve; measured after).** See section 5 (P-A..P-G) and
section 7 (P-R1..P-R4).

**FALSIFIERS (named before the run; any one fires an honest record, never a tune).** See
section 6.

## 2. THE POSE VARIABLES (the class records bind the DOFs; 10 solved + 2 forced + 9 at rest)

Per bond, the recorded range is parsed from the committed definition's joint_class record at
run time — no retyped constant.

- SOLVED (10): hip L 3 (bond.joint_01_02, flexion/adduction/rotation), hip R 3
  (bond.joint_01_03), knee L (bond.joint_02_06), knee R (bond.joint_03_07), tarsal driver L
  (bond.joint_06_25), tarsal driver R (bond.joint_07_24). These are exactly the DOFs whose
  child subtrees carry a pad.
- FORCED (2 coordinates, 4 bonds): the elbow apposition pairs — bond.joint_04_10 +
  bond.joint_04_12 (one anatomical hinge L), bond.joint_05_11 + bond.joint_05_13 (one
  anatomical hinge R). The class record names the two appositions of ONE hinge per forelimb;
  both bonds carry the SAME theta. theta = the range floor 0.34906585 rad, DERIVED as the
  value nearest the rest state 0 inside the recorded range (argmin |theta - 0| s.t. theta in
  [0.34906585, 2.44346095]); theta = 0 is not in the recorded range, so the corpse state is
  not lawful at the elbows and the minimal lawful departure is the floor.
- AT REST (9): radioulnar bond.joint_10_12, bond.joint_11_13 = 0 (in range, minimal motion);
  tarsal loop bonds 20_25/21_24 carry NO pose variable at all (the FK tree spans <= 2 edges of
  each 3-cycle — the tarsal receipt's counted contrast; their seats are MEASURED, never
  applied); bond.joint_07_18, bond.joint_22_25, bond.joint_23_24 = 0 (in range, minimal
  motion). The 0-DOF classes (syndesmosis 06_20/07_21, positional 02_15/03_17/04_08/05_09)
  carry no coordinate by their class records.

## 3. DERIVATIONS, ZERO FREE NUMBERS (the axis record the records left OPEN)

All pivots/axes are in the committed CT millimetre frame. The registered primitives are
imported VERBATIM from the committed hip module (rodrigues, law_gap, inlier_rule, sphere_fit,
pose_request, OutOfAnatomicalRange).

- HIP PIVOTS: the registered femoral-head fits, re-derived at run time by hp.inlier_rule and
  asserted equal to the committed hip battery values (c2 = [58.481285783297, 40.201005541148,
  43.245619125234], c3 = [57.206718169476, 41.501776979145, 22.591386466803]; bands =
  rms_residual 0.155477725893 / 0.147474758014 mm — the P6' v2 displacement bands).
- HIP AXES: e1 = the committed bilateral unit through the two fit centers (left->right, the
  hip battery's "u"); e3(k) = the femoral long axis, unit(cross-orthogonalized): raw =
  (knee-bond recorded closest point on the femur) - c_k, then Gram-Schmidt against e1; e2(k) =
  cross(e3(k), e1). Composition order = the record's coordinate listing order (flexion,
  adduction, rotation): R_k = R(e1, th_f) @ R(e2(k), th_a) @ R(e3(k), th_r), about the single
  pivot c_k. All three axes pass through c_k, so the head-center displacement is exactly 0.0
  at any coordinate combination — the P6' v2 Leg-2 signature.
- KNEE: pivot = the bond's recorded closest-point pair midpoint (on_02/on_06, on_03/on_07 —
  committed definition fields); axis = e1 (the committed bilateral unit; no new number).
  Sign mapping sigma_knee = -s_k where s_k = +1 iff the probe rotation +R/5 about e1 brings
  the child's distal landmark (child vertex farthest from the pivot, argmax convention) nearer
  the recorded pes apposition point on the femur (bond.joint_02_15/03_17 closest point on the
  femur) — the hip battery's curl-deepening rule; the minus carries the cited gait2392
  knee_angle record's own asymmetry (flexion at the NEGATIVE end, band [-2.0943951,
  0.17453293], law doc section 1.4). Geometric rotation = sigma * theta.
- ELBOW (per forelimb, shared by its two apposition bonds): pivot = midpoint of the two
  recorded apposition midpoints; axis = unit(second apposition midpoint - first). Sign
  mapping sigma_elbow = +s_e, s_e derived by the same curl-deepening probe (child forearm
  landmark vs the recorded hand apposition point on the humerus, bond.joint_04_08/05_09
  closest point on the humerus; probe = +R_e/5, R_e = 2.44346095 - 0.34906585): the positive
  recorded end is the flexion end per the cited monkeyArm one-sided hinge.
- TARSAL DRIVERS: pivots = the driver bonds' own registered child fits (re-derived by
  hp.inlier_rule, asserted equal to the tarsal battery's BANKED constants); axis = the
  registered shared unit through the two driver fit centers (the tarsal battery's banked
  axis, re-derived and asserted); sign labeling inherited DEFERRED exactly as the tarsal
  receipt ruled (the band is symmetric; no clause is sign-bound).
- SIGNS ARE NOT SWEPT: each sigma is computed once by its named probe and recorded; a probe
  outcome never re-rolls.

## 4. THE OBJECTIVE AND THE SOLVE (stated before the run; one run, no sweep)

- PADS: the four distalmost limb-end membranes — mem.bone_08, mem.bone_09 (hands), mem.bone_22,
  mem.bone_23 (the tarsal-chain feet' distal members; 22 rides 25, 23 rides 24 at their
  in-range rest intertarsal coordinates). Pad point = the membrane's canonical unique-vertex
  centroid (hp.unique_verts, first-occurrence dedup; posed by the composed FK).
- V(theta): the population variance of the four posed pad centroids measured along the
  least principal axis of their centered scatter = lambda_min(scatter)/4 (np.linalg.eigh;
  the pads' coplanarity deficit, mm^2 — placement-invariant).
- d(theta): (a . n̂)^2, a = the axial composite's PCA first axis (sign fixed toward the
  composite vertex farthest from the hip-fit midpoint — zero free numbers), n̂ = the same
  least-eigenvector as V. This is sin^2 of the trunk-to-pad-plane pitch: the trunk-level
  deficit (placement-invariant, dimensionless). Both terms reduce to the same numbers under
  any whole-body placement, so the solve never sees a placement.
- SCALARIZATION: J = V + kappa * d with kappa = V_rest / d_rest computed at run time from the
  committed bytes (the rest-state commensuration: one unit of squared-pitch costs what one
  mm^2 of pad variance costs at rest). No weight is tasted.
- SOLVER: scipy.optimize.minimize, method SLSQP, x0 = the feasible rest projection (10 zeros),
  bounds = the recorded ranges parsed from the definition, constraints = the two hip seats
  (3.0 - law_gap(posed femur, composite) >= 0, the committed touching-class cut), options
  ftol = 1e-12, maxiter = 400. Environment pinned: OMP/OPENBLAS/MKL_NUM_THREADS = 1.
  The elbows are NOT variables (no pad or trunk authority — both their pad and their parent
  are fixed by the class records) and carry the forced floor value; no other DOF is moved
  outside the solve.
- OUTPUT: pose.json with the solved coordinates at full float repr AND rounded to the house
  R12 = 12 decimals; THE POSE OF RECORD is the R12 rounding. Determinism falsifier: a fresh
  process re-run of the solve is byte-identical (pose.json sha256 twice).

## 5. PREDICTIONS (banked)

- P-A1 (ranges): every recorded coordinate of the pose (10 solved + 2 forced elbow
  coordinates + 9 at-rest values) is inside its recorded range; pose_request accepts all 23
  bonds' pose states; a nextafter beyond any moved class's band refuses by name
  (out_of_anatomical_range).
- P-A2 (P6' v2 on the hips through the transition): at path stations t in {0, 1/5, 2/5, 3/5,
  4/5, 1} of the solved hip coordinates (the registered probe fraction), BOTH hips hold
  displacement == 0.0 exactly (rotation about the own fit center) and seat gap in
  [0, 3.0] mm (gap < 0.08 recorded as below-resolution readings, never clause-binding).
- P-A3 (the pose's class): the solved angles are an IN-RANGE, INTERIOR, SMALL perturbation of
  rest (design-time declared: the corpse is near-optimal; expected |th_flex| <= 1.0 rad,
  |th_add| <= 0.5, |th_rot| <= 0.5, |th_knee| <= 0.5, |th_driver| <= 0.2). If a band fires,
  the pose is recorded honestly — the LAWFULNESS battery owns void; this prediction owns the
  class reading only.
- P-A4 (knees, elbows, drivers seats): every moved non-hip bond's law gap at the pose is
  <= 3.0 mm (each non-hip pivot is its own recorded apposition midpoint or own registered fit
  center: the realized pair's separation is non-increasing under rotation about it).
- P-A5 (loops): both tarsal loop bonds' seats at the pose equal their rest seats to
  1e-9 mm (the loop members share one rigid transform because the syndesmosis bonds are
  0-DOF and the drivers' relative transforms are identity) and are <= 3.0 mm (the cycle-B
  thin margin survives BECAUSE the drivers stay off their band edges; rest seats
  2.468359650708 / 2.899930898961 mm).
- P-A6 (0-DOF immobility): all six 0-DOF-class bonds (06_20, 07_21, 02_15, 03_17, 04_08,
  05_09) and the two at-rest radioulnar bonds (10_12, 11_13) show law gaps BITWISE equal to
  their rest values at the pose (both members of each bond ride one identical transform).
- P-A7 (mass): every moved membrane's posed triangle areas equal rest to <= 1e-12 relative
  (the hip battery's resampling detector; rigid Rodrigues, no resample).
- P-A8 (releases): the corpse pose_contacts split by their members' DOF paths, derived from
  the class records BEFORE the run: pose.joint_01_08 and pose.joint_01_09 PERSIST (both
  members immovable: the hands ride the humeri by 0-DOF positional records and the humeri
  carry no DOF at all) with bitwise-unchanged gaps; pose.joint_01_11, pose.joint_01_13,
  pose.joint_01_15, pose.joint_01_17 RELEASE (their moving members ride the elbow/hip
  coordinates): gap > 3.0 mm at the pose. Each measured gap is recorded; none is dropped.
- P-A9 (determinism): pose.json byte-identical on a fresh-process re-run; battery.json
  byte-identical on a second run.
- P-A10 (identity): theta = 0 is untouched — the definition, the tris bins, and every prior
  receipt/battery watched before/after equal (the joint-class lane's A1 discipline).

## 6. FALSIFIERS (any one fires an honest record)

- F1: any recorded coordinate outside its recorded range, or a refused-band probe accepted,
  or an in-range probe refused => the pose is unlawful => VOID (A5-class, refuses by name).
- F2: a hip P6' clause fails at any station (displacement != 0.0 exact, or seat > 3.0 mm) =>
  the pivot/axis derivation or the composition is wrong => the pose is NOT MINTED.
- F3: a loop seat deviates from rest by > 1e-9 mm, or exceeds the cut => transform aliasing
  or a moved loop DOF => VOID.
- F4: a 0-DOF-class bond's gap is not bitwise rest => the class record did not bind the pose
  => VOID and the joint-class lane's teeth finding is contradicted.
- F5: a posed area drifts > 1e-12 relative => resampling => the transform law is broken.
- F6: a release prediction inverts (a persist contact moves, or a release contact stays
  <= 3.0 mm) => the DOF-path derivation is wrong => recorded, the release table stands as
  measured.
- F7: solve or battery double-run byte drift => nondeterminism => the lane's numbers are not
  a record => VOID.
- F8: any watched byte changes (definition, tris, prior receipts/batteries/preregistrations)
  => VOID (theta = 0 was touched).
- F9: SLSQP exits with a constraint-violating or non-converged point => the pose is NOT
  MINTED; the failure is the record.

## 7. THE RENDER (the proven triangle path; predictions banked before any capture)

- PATH: the copied byte-identical committed modules ct_skeleton_layer.py +
  ct_skeleton_triangle.py (from agent/triangle-monkey-grid-20260920, commit 1b08b29d, sha256
  b98626bf.../d2528d6e... — provenance in the receipt) over the committed meshes_preview OBJs
  (blob-identical across the branches), the committed walker pin (sha 013810f8...), and the
  engine's /mesh_bin triangle route (binary the walk-movie lane proved: sha256 16ca3c18...,
  launched on THIS lane's own bind-tested free port; 8127 and siblings' ports never touched;
  launch with the port argument ONLY — the measured argc trap).
- COMPOSE: each posed bone = its committed preview OBJ vertices transformed by the composed
  FK in CT mm, then through the ONE committed registration (ct_registration, scale pinned to
  the walker HAT length; the corpse compose reproduces the committed layer_triangle_mesh
  path). Corpse still = theta = 0 through the same path (the committed compose). Standing
  still = the pose of record plus the STANDING PLACEMENT: the rigid scene-frame placement
  carrying the posed pads' plane normal to the scene up (Rodrigues about
  cross(n̂_scene, +Y), zero free numbers) and setting the pads' mean plane to y = 0 — the
  derived "pads on the ground" placement; recorded with the still.
- CAMERA: each still framed by the layer's own bbox through the proven rule (derive radius
  from the 45 deg vertical FOV with margin 1.35; camera (0, -2.7*extent, 0.72*extent); the
  compose's recenter) — one rule, both stills.
- PREDICTIONS:
  - P-R1 (coverage class): each still shows a real rendered skeleton: object pixels (any
    channel differing from the frame's corner-sampled background by > 8/255) in
    [1%, 40%] of the frame — non-blank, not a fill.
  - P-R2 (the pose is SEEN): corpse vs standing stills differ in >= 1000 pixels.
  - P-R3 (revisit identity): two consecutive settled captures of the same uploaded still are
    byte-identical (the within-upload bit-stability the visual lane measured; cross-upload
    GPU sort drift is out of scope and not claimed).
  - P-R4 (render/verify consistency): the standing layer's pads' scene-frame spread along
    its plane normal, recomputed through the render path, equals the battery's posed spread
    to 1e-6 scene units (what is rendered is what was verified).
- FALSIFIERS: a coverage class out of band, a < 1000-px difference, a revisit mismatch, or a
  consistency break — recorded, the render claim fails honestly.

## 8. GATES

The repo's own gates, run unchanged at the lane's final state: test_definition, test_glue,
training_gate. The lane writes only its own directory, the two copied provenance modules +
walker pin (byte-identical, recorded above), and nothing else.

Trailer: Agent: GLM 5.3
