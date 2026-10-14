# PREREGISTRATION AMENDMENT 4 — the floor-clearance terms (the fired v1 falsifier's operational repair; banked BEFORE the v2 solve)

Lane `agent/standing-pose-v2-20260921`, base `4ea008cb` (the v1 standing-pose lane's commit).
THE FIRED FALSIFIER THIS AMENDMENT ANSWERS: the v1 lane's own numbers + the lead's 2026-09-21
eyes-on verification. The v1 objective was V (pad-coplanarity deficit) + d (trunk-level deficit);
the solve drove V: 1.943840101124 -> 2.1e-11 mm^2 and d -> 0.0 with the battery hard_checks_pass
TRUE — and the rendered standing_still.png reads as a COLLAPSED HEAP: "skull resting ON the ground
plane, limbs still tucked, no four-point stance". Diagnosis from the lane's own numbers: (a) the
preregistration set x0 = feasible REST, and at rest V was already only 1.94 mm^2 and d 0.0104 —
the CT corpse lies ON the scanner plane, so the objective is nearly satisfied by the CORPSE; the
optimizer polished the lying pose to exactness without lifting anything; (b) the spine carries
ZERO DOFs in the committed class records — nothing can un-curl the trunk; (c) battery F6 honestly
recorded the curl contacts PERSISTING at the pose (0.066..1.306 mm) — the limbs stay tucked. The
render is faithful (rendered pad spread == battery spread, abs dev 0.0 m). THE OPERATIONAL
DEFINITION OMITTED FLOOR CLEARANCE. This amendment repairs the DEFINITION, not the machinery.

## 1. DESIGN-TIME DETERMINATIONS (read-only on committed bytes, made in the design phase, BEFORE
   this bank, before any v2 solve; the run re-measures everything)

- SIGN RULE (new, derived, zero free numbers): the pads'-plane normal n̂ from the v1 eigh is
  sign-arbitrary; v2 fixes it: n̂ is oriented so the axial composite's unique-vertex centroid has
  POSITIVE height: (mean(v_bone01) - c̄) . n̂ > 0 — "the trunk is above the pads' plane" (a
  standing quadruped's trunk is; the rule refuses SystemExit on exactly zero).
- THE V1 POSE OF RECORD UNDER THE SIGN RULE (design-time measured): its plane normal
  [0.205257, 0.933957, -0.292564]; ALL 21 non-pad membranes have h_min < 0 — min -41.688118 mm
  (bone_02, left femur); the SKULL REGION -15.8287 mm (see the head window below); bone_01's own
  argmin -20.0224 mm at x=114.68 (mid-body, a sternal/rib vertex). The v1 "standing" pose is a
  heap under the amended definition, in numbers.
- THE STRUCTURAL PIN (design-time measured): a plane containing the two FIXED hand-pad centroids
  (pads 08/09 ride the humeri by the 0-DOF positional contacts 04_08/05_09; the humeri carry no
  DOF — BONE_PLAN chains for 4/5/8/9 are empty) and parallel to the trunk axis (d = 0) is UNIQUE
  (up to sign): the normal is unit(cross(trunk_axis, c8 - c9)) = [0.205256, 0.933957, -0.292563]
  — EQUAL to the v1 pose's normal to 1e-6. Under the v1 objective at machine zero the pads' plane
  is THE pinned plane; it is a constant of the corpse.
- THE FIXED+FORCED CLEARANCE CONSTANTS at the pinned plane (these membranes' poses are constants
  of the records: empty BONE_PLAN chains 1/4/5/14/16/19; the forearms ride the elbow coordinates
  FORCED to the monkeyArm range floor 0.34906585 — the only class range excluding theta = 0):
  bone_19 -39.9118, bone_14 -36.7049, bone_16 -35.7727, bone_10 -28.7108, bone_12 -24.6276,
  bone_11 -21.9529, bone_01 -20.0224, bone_13 -16.7584, bone_04 -17.6413, bone_05 -14.6077 mm.
  The SMALLEST fixed-set violation magnitude is bone_05's 14.6077 mm: T3 (below) is violated by
  >= 14.69 mm on a membrane NO lawful coordinate can move.
- THE HEAD WINDOW (derived, zero free numbers): the skull region := {v in bone_01 : v.x > max_x
  (hand pads 08/09)} — the axial composite beyond the hands' distal extreme (cut = 157.04 mm;
  9903 of 14656 unique vertices; the hands are the last pre-head objects on the +x axis and the
  render shows the cranium at that end). Skull-region h_min at the pinned plane: -15.8287 mm.
- SCOPE NOTE (honest): the pads' contact class remains the v1 CENTROID-coplanarity (the curled
  hand pads' own vertices dip to -11.51/-11.12 mm below their centroid plane at the v1 pose —
  they are not flat soles); vertex-level sole contact is NOT claimed and would need
  re-segmentation (successor scope, never a tune here).

## 2. THE AMENDED OPERATIONAL DEFINITION (v2). A pose IS a standing pose iff the v1 lawfulness
   set (ranges, hip P6' v2 seats, tarsal loop seats under the committed cut, 0-DOF immobility,
   mass invariance, determinism, theta=0 identity — ALL UNCHANGED) AND:

- T1 (pad coplanarity, unchanged term): V(theta) at machine zero — the verdict band is the v1
  record's own achieved value V_v1 = 2.1e-11 mm^2 (pose.json, committed): V(x) <= V_v1.
- T2 (trunk level, unchanged term): d(theta) at machine zero: d(x) <= d_v1 = 0.0 (the v1 record).
- T3 (FLOOR CLEARANCE, NEW): for EVERY non-pad membrane m (21 of them), h_min(m; x) >= EPSILON_MM,
  where h_min(m; x) = min over the membrane's posed unique vertices of (v - c̄) . n̂ — the lowest
  vertex's signed height above the pads' least-squares CENTROID plane (n̂ sign-fixed as above,
  c̄ = the four pad centroids' mean). This is the term whose omission produced the heap.
- T4 (PADS-ONLY CONTACT, NEW): (i) exclusivity — T3 is exactly the statement that no non-pad
  membrane comes within EPSILON_MM of the plane; (ii) contact certificate — each pad's centroid
  lies within EPSILON_MM of the plane: |h_cen(pad)| <= EPSILON_MM for all four pads (at machine-
  zero V this is the v1 coplanarity made explicit; recorded as measured at whatever V lands).
- T5 (HEAD CLEARANCE, NEW, named explicitly — subsumed by T3, named because the fired render is
  a skull-on-the-floor reading): h_min of the SKULL REGION of mem.bone_01 (the head window above)
  >= EPSILON_MM.
- EPSILON_MM = 0.08 — the COMMITTED P6' interpenetration tolerance REUSED: tol_ip =
  specimen.resolution_um/2 = 0.08 mm (the definition's own resolution_um = 160; law doc section
  5B keeps tol_ip as the gap metric's RESOLUTION FLOOR: "readings below it lie inside the
  surfaces' own localization, where seated-impingement contact and through-crossing are
  indistinguishable"). WHY THIS FAMILY and not the 3.0 mm loop cut: floor clearance is a
  localization claim — "this membrane is OFF the plane by more than the scan itself can blur" —
  which is exactly what tol_ip means; the 3.0 mm cut is the SEAT family's separation cut (joint
  apposition touching class). The 3.0 mm reading is RECORDED AS A SECONDARY VERDICT (P-AV2-8):
  both constants are committed; no number is chosen between them by taste.

## 3. THE STRICT SOLVE (the outcome-S attempt; ONE derived problem, TWO declared starts)

- minimize J = V + kappa*d (the v1 objective UNCHANGED, kappa = V_rest/d_rest from committed
  bytes) subject to: T3's 21 inequalities (h_min(m; x) >= EPSILON_MM), the v1 seat constraints
  (both hip seats + both tarsal loop seats under the committed 3.0 mm cut — amendment 2's set),
  bounds = the recorded class ranges parsed at run time. Solver: scipy SLSQP, ftol 1e-12,
  maxiter 400, single-thread env. DECLARED STARTS (both banked here, both reported): (a) x0 =
  zeros(10) (the feasible rest projection — the v1 start); (b) x0 = the v1 pose of record
  x_R12 (permissible ONLY because this amendment declares it). OUTCOME S iff ANY declared start
  exits success with all 21 T3 constraints >= 0 and T1/T2 verdicts GREEN; that pose is minted as
  the v2 pose of record and runs the FULL battery + render. Otherwise OUTCOME I.

## 4. OUTCOME I — THE IMPOSSIBILITY RECORD (pre-declared; an honest COMPLETE deliverable)

If no declared start lands clearance-feasible: do NOT tune, do NOT widen any range or cut. The
deliverable is: (i) the strict solves' honest exits (both starts, verbatim messages, constraint
violations); (ii) the structural cause WITH the banked numbers — the plane pin (P-AV2-2) + the
fixed/forced constants (section 1) + the named binding records: the empty BONE_PLAN chains
(no shoulder DOFs; the axial composite IS the FK root — no spine DOFs), the hands rigid with the
humeri by the 0-DOF positional contacts, and the elbow coordinates FORCED to the range floor
0.34906585 (the monkeyArm record excludes theta = 0); the maximin's own joint-bound bindings are
MEASURED and named (which variable sits at which bound); (iii) THE MAXIMIN BEST-EFFORT POSE:
maximize t over (x, t) subject to: h_min(m; x) - t >= 0 for all 21 non-pad membranes;
V(x) <= V_rest AND d(x) <= d_rest (the CORPSE's own committed readings as the caps — the pose
must be no worse than the corpse on each v1 term: "V,d as close to zero as the records lawfully
admit" scaled by the only committed reference); the v1 seat constraints; bounds = the recorded
ranges; t bracketed to [-100, +100] (a solver bracket, not a physical bound). SLSQP, ftol 1e-12,
maxiter 400, single-thread env. DECLARED STARTS (both banked, both reported): (a) x = zeros(10)
with t0 = the sign-fixed rest min non-pad clearance; (b) x = the v1 pose of record with
t0 = its min non-pad clearance. The v2 POSE OF RECORD = the better t_max (tie -> start (a)).
The maximin pose runs the FULL lawfulness battery (F1-F8, unchanged checks) + the render.
(iv) THE NAMED SUCCESSOR (out of scope, named only): axial (spine) DOF class records and
shoulder ball records — both require cited sources (the joint-class lane's discipline), and a
re-segmentation of the curled pads if vertex-level sole contact is ever claimed.

## 5. PREDICTIONS P-AV2-* (banked BEFORE the run; measured after; inversions recorded, never tuned)

- P-AV2-1 (the fired falsifier, quantified): the v1 pose of record re-measures with ALL 21
  non-pad h_min < 0 (design-time: min -41.688118 mm at bone_02; skull region -15.8287 mm);
  T3 fails 21/21, T5 fails — the v1 pose is not a standing pose under the amended definition.
- P-AV2-2 (the structural pin): the v1 pose's pads'-plane normal equals the hand-pinned level
  normal to <= 1e-6 (design-time: [0.205257, 0.933957, -0.292564] vs [0.205256, 0.933957,
  -0.292563]) — under V,d at machine zero the pads' plane is a corpse constant.
- P-AV2-3 (OUTCOME I expected): no declared strict-solve start lands clearance-feasible; T3 is
  violated BY THE FIXED+FORCED SET ALONE at the pinned plane, smallest deficit bone_05's
  14.6877 mm (14.6077 + 0.08). INVERSION CLAUSE: if a start lands feasible with T1/T2 GREEN,
  outcome S executes instead and this prediction is recorded inverted.
- P-AV2-4 (the maximin lands honest): t_max <= -5.0 mm — the best lawful effort still leaves
  some non-pad membrane >= 5 mm below the pads' plane (derivation: the caps allow <= 5.9 deg of
  trunk pitch; a fixed bone's gain is bounded by lever x sin(5.9 deg); the smallest-leverage
  fixed bones (humeri, ~10-15 mm lever) can gain ~1-1.6 mm from -14.6/-17.6, and the argmin is
  expected to sit on a fixed/forced membrane). INVERSION CLAUSE: t_max >= EPSILON_MM refutes
  the impossibility and is recorded as such (and outcome I's premise dies).
- P-AV2-5 (the maximin is LAWFUL): F1-F5, F7, F8 GREEN on the maximin pose; V(x) <= V_rest and
  d(x) <= d_rest; every coordinate in its recorded range; seats under the cut.
- P-AV2-6 (render, OUTCOME I): the maximin still through the SAME proven triangle path +
  standing placement shows the skull-region lowest vertex BELOW the pad plane (scene-frame min
  height < 0, equal to the battery's CT number through the registration to 1e-6 m); corpse vs
  maximin stills differ in >= 1000 pixels (the joints DID move); coverage classes in [1%, 40%]
  (amendment-3 bone-tint mask); revisits byte-identical. The eyes-on reading — heap vs standing
  quadruped — is the LEAD'S OUTER GATE, recorded either way.
- P-AV2-7 (render, OUTCOME S only if S): the standing still shows the skull lowest vertex above
  the pad plane by >= EPSILON_MM; the rendered pad spread == the battery spread (amendment-3
  form); the still READS as a standing quadruped — the lead's outer gate.
- P-AV2-8 (epsilon robustness): the outcome is unchanged at the secondary epsilon (the 3.0 mm
  committed cut): recorded whichever way it lands.

## 6. FALSIFIERS (banked; any one fires an honest record)

- FV1: a strict-solve returned point outside a recorded range or violating a seat → nothing is
  minted from it; the exit IS the record (the strict solve is expected to fail INFEASIBLE).
- FV2: the maximin pose outside the caps (V > V_rest or d > d_rest), outside a recorded range,
  or a seat over the cut → the maximin is NOT MINTED; the failure is the record.
- FV3: pose_v2.json or battery_v2.json byte drift across fresh processes → VOID.
- FV4: any watched byte changed (the definition, the tris bins, every prior receipt/battery/
  preregistration/amendment, the v1 pose/battery/render artifacts) → VOID (theta = 0 untouched).
- FV5: a prediction inversion anywhere in P-AV2-* → recorded as measured, verbatim, never tuned
  (the inversion clauses name which inversions reroute the outcome).

## 7. THE RENDER (the proven path, unchanged)

Corpse still + maximin (or S) still through the byte-identical committed modules
ct_skeleton_layer.py + ct_skeleton_triangle.py over the committed meshes_preview + walker pin;
engine binary sha 16ca3c18... on THIS lane's own bind-tested free port (8127 and siblings never
touched; port argument ONLY); first-upload warmup + 3-consecutive-capture quiesce (amendment 3);
camera = the amendment-3 larger-extent fit; pixel mask = the amendment-3 bone-tint rule. New
files only: renders/corpse_still_v2.png, renders/standing_v2_still.png, render_record_v2.json —
every v1 artifact byte-untouched.

## 8. GATES + DETERMINISM

python -B -m unittest for test_definition (9/9) and test_glue (8/8) with both sys.path roots as
the v1 lane ran them; python tools/training_gate.py PASS. pose_v2.json and battery_v2.json
byte-identical across two fresh processes each (FV3). Receipt: receipt_v2.json (new file; every
pre-existing receipt byte untouched).

Trailer: Agent: GLM 5.3
