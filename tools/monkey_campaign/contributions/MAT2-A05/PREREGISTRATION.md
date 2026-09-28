# PREREGISTRATION — MAT2-A05 "First Mutation" (Captain Decision 2, hybrid A+B)

Preregistered 2026-09-28 by the Sergeant-implementer (arrival-b22e42ce0ecf4204acb2f99d0aecff97,
attempt b4ad70883ac2480a928dcc828f33c65f) BEFORE authoring the mutation structure,
manifest or any capture frame. Inputs read read-only from pinned sources; the
arithmetic below is the statement the deliverables must reproduce.

## Task identity

- Card: MAT2-A05, slot 2, state CHANGES_REQUESTED -> Development (mutation implementation).
- Criteria sha256: 34411771f7bd5dea2ec2cc4775d44b33df422e5454d283eae40676d1e3346544
- done_when: "The modeled grasp has sufficient explicit bodies, joints and geometry;
  sources and adaptations approved".
- Governing ruling: E:/ChimeraWork/monkey-coordination/kanban-attempts/MAT2-A05/CAPTAIN_DECISION_2_MUTATION.json
  (decision_id A05-DIGIT-MUTATION-20260928): hybrid A+B "first mutation" — use the
  human myo_sim digit framework as the known base structure, modify it toward macaque
  anatomy using the macaque evidence in-repo (hand body geometry/scale, wrist joint
  ranges, digit-named muscle attachments, arm allometry), producing a NEW derived hand
  structure with a NEW set of numbers for training, recorded with an explicit mutation
  manifest (human-derived base / macaque constraints / deviations).
- Profile: anatomy (visible_static), subject "Creature structure, bone/muscle/skin
  correspondence and attachment ownership"; 3 profile views, clean_view_required=true,
  6 diagnostic_layers, 16 camera_required_fields, numerical_evidence_required=true.

## What the mutation IS (declared in advance)

A DERIVED structure record, not a claim of macaque-scan anatomy. Human per-digit
topology is taken verbatim from myo_sim; every length is multiplied by one stated
dimensionless scale; macaque wrist ranges, hand-body mass, muscle anchor points and
frame replace their human counterparts. Species mixing (human base shapes + macaque
frame numbers) is DECLARED per the Captain decision, itemized in the manifest — this
is not a REALITY-category species-true scan claim.

### Human elements taken (per-digit topology) — source pins

- E:/PythonChimera/vendor/myo_sim @ 33f3ded946f55adbdcf963c99999587aadaf975f
  (git log verified clean).
- hand/assets/myohand_body.xml sha256 21a6649236801439649ae992459c29bbc020767c2022c4d79de688689462ed28
  — body tree: radius->lunate (wrist joints deviation/flexion) -> {scaphoid, pisiform,
  triquetrum, capitate}; capitate-> {trapezium->firstmc, trapezoid, hamate, secondmc,
  thirdmc, fourthmc, fifthmc}; thumb chain firstmc->proximal_thumb->distal_thumb
  (joints cmc_abduction, cmc_flexion, mp_flexion, ip_flexion); fingers 2-5
  <n>mc->proxph<n>->midph<n>->distph<n> (joints mcp<n>_flexion+mcp<n>_abduction,
  pm<n>_flexion, md<n>_flexion). Digit bodies carry no euler/quat (verified): chain
  geometry is pure translation composition.
- finger/finger_v0.xml sha256 6975e5c56d2adbd41c1b9ad8cdbece90b84611c80288337338adc7951a8b4b5f
  — corroborates the per-digit joint PATTERN (adb/mcp, pip, dip hinge chain), cited as
  pattern evidence only (toy scale, not anatomical numbers).
- 19 digit mesh STLs under meshes/ (1mc..5mc, thumbprox, thumbdist,
  {2..5}{proxph,midph,distph}) — referenced as geometry at a recorded uniform scale,
  never re-authored.

### Macaque constraints applied — source pins

- E:/PythonChimera/tools/science_funnel/data/macaque_arm/monkeyArm_current.osim
  sha256 4148aee2c8dda1dcb0918496ad7c5e1adcf4ebabde0a68a3e0dc67faec67b895:
  hand body mass 0.0490 kg; wrist joint (parent radius1) ranges wrist_flexion
  [-1.30899694, 1.57079633] rad, wrist_abduction [-1.04719755, 0.78539816] rad;
  digit-named muscles attach to the single hand body (ext_digitorum P3
  [0.00106101, -0.00804001, 0.00594996], P2 [0.00222721, -0.0391191, 0.00429738];
  flex_digit_profundus P4 [-0.00139132, -0.0172483, -0.00108922]).
- Geometry/hand.vtp sha256 a06ea7e079c849df07d6eec001e9bcc2ea193ecd3914011c78a993a5faa94fc6,
  displayed at scale_factors 0.001 (mm->m); graph node geom.macaque_arm.hand records
  bounds_m [[-0.0124375, -0.0837075, -0.00152775], [0.020731, -0.00010125, 0.00463975]]
  -> hand length (Y extent) 0.08360625 m.
- radius.vtp / ulna.vtp Y extents 0.139561 / 0.157971 m (allometry denominator).
- Graph intake conventions (creature_graph.json schema 2.0.0): ref.<model>.body.<name>
  model_definition nodes with mass_center_m/units/frame; geom.<model>.<name>
  geometry_asset nodes with asset {path, sha256, source_units_to_m} and metrics
  {vertices, triangles, bounds_m}; stable ids, sha256 pins, m/rad/kg units,
  species/specimen labels on sources.

### The stated formula (all derived numbers come from this; arithmetic shown)

1. HUMAN_HAND_LENGTH := max over the 5 digit chains of |chain displacement from the
   lunate origin to the distal body origin| in myohand_body.xml.
   Chains (m): thumb 0.103801, d2 0.151999, d3 0.155285, d4 0.145358, d5 0.130651
   -> HUMAN_HAND_LENGTH = 0.155285 (digit 3).
2. MACAQUE_HAND_LENGTH := geom.macaque_arm.hand bounds_m Y extent = 0.08360625 m.
3. MUTATION_SCALE s := MACAQUE_HAND_LENGTH / HUMAN_HAND_LENGTH = 0.08360625 / 0.155285
   = 0.538404813 (dimensionless).
4. Every mutant per-digit body offset := s * (human offset vector), componentwise,
   preserving the human inter-segment directions (no invented per-phalanx proportions).
   Example: capitate->thirdmc (+0.000477, -0.039239, +0.007377) * s =
   (+0.000257, -0.021126, +0.003972) m, len 0.039929 -> 0.021498 m.
5. Mutant per-digit-body mass := 0.049 kg * (human body mass / 0.1589 kg), where
   0.1589 kg is the human 19-digit-body mass sum in myohand_body.xml and 0.049 kg is
   the macaque hand body mass. Example: firstmc 0.016 -> 0.004934 kg.
6. Mutant joint ranges := human myohand ranges for digit joints (unchanged base);
   the mutant wrist anchor carries the MACAQUE wrist ranges (wrist_flexion
   [-1.30899694, 1.57079633], wrist_abduction [-1.04719755, 0.78539816] rad).
7. Allometry cross-check: human hand/forearm = 0.155285 / 0.244726 = 0.6345 where
   0.244726 m is the human radius-origin-to-wrist distance (|lunate y offset| 0.242 +
   radius.stl +Y extent 0.0027, radius.stl tris=390); macaque hand/forearm(ulna) =
   0.08360625 / 0.157971 = 0.5293. The mutation moves the modeled ratio from 0.6345
   (human base) to 0.5293 (macaque reference) — the intended modification.
8. Mutant frame: macaque hand body frame (frame_id macaque_arm_hand_mutation_frame,
   unit m); the chain root (five metacarpal anchors) is wrist-anchored at the macaque
   hand body origin, matching location 0 0 0 of the macaque wrist joint; the human
   -Y long axis coincides with the hand.vtp -Y span.

### Geometry choice (stated in advance)

Mutant digit geometry references the vendor human STLs at recorded uniform scale
s (transform recorded per body), NOT fabricated meshes. Why: no macaque phalanx
mesh exists in-repo (round-2 search, PR #229/#230 evidence); vendor STLs carry
provenance (path + sha256 + vendor rev); a recorded scale transform keeps every
rendered number reproducible. Explicit scaled dimensions (the scaled segment vectors
of formula 4) are additionally recorded per body for validators that do not load meshes.

## Falsifiable predictions

- P1 Structure: the mutation deliverable contains exactly 19 explicit digit bodies
  (5 metacarpals + 14 phalanges: prox/mid/dist x digits 2-5 + prox/dist thumb),
  20 explicit joints (thumb cmc x2 + mp + ip; fingers 2-5 mcp flexion + mcp abduction
  + pip + dip), each body parented into a connected chain rooted at the macaque hand
  body anchor; digit count 5, phalanx count 14, thumb 2-segment. FALSIFIER: any
  missing/duplicate/extra body, broken parent link, or joint not inside its body.
- P2 Numbers: every mutant offset equals s * human offset to <= 1e-12 relative error,
  recomputed from the pinned files by the committed validator; s recomputes to
  0.538404813 from the pins. FALSIFIER: any number not reproducible from formula 1-5.
- P3 Allometric coherence: mutant chain total length (max chain displacement from
  anchor) = 0.083606 m within 1e-9 of MACAQUE_HAND_LENGTH; mutant
  hand/forearm(ulna) ratio = 0.5293 = macaque ratio within 1e-3; the human base
  ratio 0.6345 is reported as the modified-from value. FALSIFIER: allometric
  incoherence — deviation beyond stated tolerance, or a mutant chain that does not
  fit inside the hand.vtp Y span when anchored at the macaque hand origin.
- P4 Units: every mutant length is in meters (m), angles in radians, masses in kg;
  mm->m conversion appears exactly once, as the recorded hand.vtp/radius.vtp/ulna.vtp
  source_units_to_m [0.001, 0.001, 0.001]. FALSIFIER: unit error (mm number used as
  m, scale applied twice, or rad/deg mixing).
- P5 Constraints: mutant wrist anchor carries the macaque ranges verbatim; each
  digit joint's range equals its human source range verbatim; the three macaque
  muscle anchor points are recorded in the mutant frame mapped to their owning
  chain bodies (ext_digitorum -> secondmc/thirdmc region, flex_digit_profundus ->
  midph2 region) with the mapping transform stated. FALSIFIER: a range or anchor
  number that cannot be traced to its pinned source line.
- P6 Structure loads as XML and passes the committed validator
  (validate_mutation.py): all chains connected, all ranges within [-pi, pi],
  per-body references resolve to pinned sources or recorded transforms.
- P7 Capture (visible_static): 6 image rows (3 profile views x diagnostic/clean)
  rendered by pure-Python orthographic projection of the mutant skeleton over the
  macaque hand.vtp envelope point cloud; validator validate_manifest returns
  structurally_valid=True with profile_id 'anatomy', capture_kind 'image',
  view_count 6; every camera row carries all 16 camera_required_fields with
  distance_to_target exactly |position - target|. FALSIFIER: label ambiguity
  (a drawn label not bound to a stable id), camera field missing, or clean row
  carrying diagnostics.
- P8 Honest gaps: NO macaque per-phalanx proportions exist in-repo (uniform scale
  applied — declared deviation); NO skin/muscle volume geometry (muscle anchors are
  points); NO fabricated mesh; NO dynamic simulation (pure derivation, no GPU);
  carpals are NOT duplicated as mutant bodies (the macaque hand body already owns
  the carpus mass/geometry — declared deviation). Each gap is inventoried in the
  manifest and on-canvas.

## Validation plan (committed, runnable read-only)

validate_mutation.py recomputes every derived number from the pinned sources
(vendor XML + graph JSON), checks P1-P6, and writes a validator receipt with
pass AND fail lines. Capture manifest built by make_manifest.py against the
registry profile read from E:/ChimeraWork/monkey-coordination/agent_slots.sqlite3
in read-only mode, validated with E:/PythonChimera/tools/monkey_campaign/visual_capture.py
validate_manifest (same code visual_gate.verify calls).

## CORRECTION_PREREGISTRATION (A4-1, MAT2-A05 correction round)

Preregistered 2026-09-28 by the Sergeant-implementer
(arrival-b22e42ce0ecf4204acb2f99d0aecff97, attempt b4ad70883ac2480a928dcc828f33c65f)
BEFORE applying the correction, per review finding A4-1 (reviewer
sergeant-a05-glm5flash, independent review of revision a76e683e464beae54511a88693fbc995eccace83).

- Defect: MUTATION_MANIFEST.md line 36 claims per-asset STL sha256 values are
  "in mutation_structure.json (all 19 recorded)" — FALSE at the reviewed
  revision: mutation_structure.json contained 0 STL hashes; they existed only as
  16-hex prefixes in derivation_output.txt lines 93-111.
- Fix (reviewer's stronger option): record FULL per-asset sha256 values in
  mutation_structure.json — a new `stl_sha256` field (full 64-hex) in each of the
  19 digit-body geometry bindings, recomputed from the pinned vendor STLs at
  E:/PythonChimera/vendor/myo_sim/meshes/ (read-only), NOT copied from the
  16-hex prefixes; extend validate_mutation.py to check them (each recorded
  stl_sha256 must equal the sha256 recomputed from the pinned vendor STL);
  update MUTATION_MANIFEST.md line 36 so the claim is true.
- Expected changed files (exactly 4): PREREGISTRATION.md (this section),
  mutation_structure.json (+19 stl_sha256 fields), validate_mutation.py
  (+2 checks), MUTATION_MANIFEST.md (line 36 only). No other file changes;
  the MJCF, positions, masses, ranges and all structural numbers are untouched
  (metadata-only correction).
- Prediction: the extended validator reports 39/39 checks passed (the prior 37
  plus the 2 new STL-hash checks), exit 0.
- Falsifier: any recorded stl_sha256 that is not 64-hex, duplicates another
  binding, or differs from the recomputed vendor sha256 (a copied 16-hex prefix
  fails the 64-hex length test); or any of the prior 37 checks regressing.
- Scope note: the committed capture sheet binds state by the sha256 of
  mutation_structure.json as it was at capture time (8d51b55180965d41 hash
  strip). This correction changes that file, so the existing capture evidence
  remains bound to the pre-correction JSON revision; this correction adds
  provenance metadata only and changes no structural number, geometry binding
  or derived value. Re-capture would be required to rebind visual evidence to
  the corrected JSON identity.
- Out of scope for this round (point-in-time artifact identity tables and
  machine mirrors such as mutation_manifest.json / validation_receipt.json are
  NOT regenerated; that is a separate round if commissioned).
