# MUTATION MANIFEST — MAT2-A05 "First Mutation"

Attempt b4ad70883ac2480a928dcc828f33c65f, arrival-b22e42ce0ecf4204acb2f99d0aecff97,
2026-09-28. This manifest IS the done_when "sources and adaptations approved" leg:
it itemizes (a) the human-derived base elements with vendor pins, (b) the macaque
constraints with osim/graph evidence pins, (c) the DECLARED deviations including the
species-mixing disclosure, and (d) the governing Captain decision. Companion records:
`mutation_structure.json` (full machine-readable structure) and
`macaque_hand_mutation.xml` (MJCF body/joint/geometry record).

## (d) Governing Captain decision (first, per chain of authority)

- Record: E:/ChimeraWork/monkey-coordination/kanban-attempts/MAT2-A05/CAPTAIN_DECISION_2_MUTATION.json
- sha256: 3c34168ef28b00b1dc60c2362cc9d2d6ffb273a8c28a1663d9bff729596dd1d7
- decision_id: A05-DIGIT-MUTATION-20260928, authority "Captain (highest)".
- Verbatim (excerpt): "...use a human data then modify it to fit macaque data And then
  we'll get a new set of numbers that we train off of new structure of the hand...
  our first mutation where we take something like a human hand and augment it with
  what you would call macaque DNA... take what exists and then modify".
- Decision summary: hybrid A+B — human myo_sim digit framework as base, modified
  toward macaque anatomy using in-repo macaque evidence, NEW derived structure + NEW
  numbers, explicit mutation manifest.

## (a) Human-derived base elements (vendor pins)

Vendor: E:/PythonChimera/vendor/myo_sim @ git rev 33f3ded946f55adbdcf963c99999587aadaf975f
(unpinned upstream clone MyoHub/myo_sim; rev + per-file sha256 recorded at use time;
vendor tree read-only).

| element | source | pin (sha256) | taken as |
|---|---|---|---|
| per-digit body topology (5 digits: mc + phalanx chains; thumb 2-segment) | hand/assets/myohand_body.xml | 21a6649236801439649ae992459c29bbc020767c2022c4d79de688689462ed28 | verbatim parent-child structure |
| digit joint pattern (mcp flexion+abduction, pip, dip; cmc x2 + mp + ip thumb) | same + finger/finger_v0.xml (pattern corroboration only) | 6975e5c56d2adbd41c1b9ad8cdbece90b84611c80288337338adc7951a8b4b5f | joint names/axes/ranges verbatim |
| per-digit joint axis directions | myohand_body.xml | (as above) | verbatim (dimensionless, scale-invariant) |
| per-digit inter-segment directions | myohand_body.xml body pos vectors | (as above) | direction preserved; magnitude x s |
| 19 digit bone shapes (STL meshes) | meshes/{1mc..5mc, thumbprox, thumbdist, {2..5}{proxph,midph,distph}}.stl | per-asset full sha256 in mutation_structure.json body geometry bindings (stl_sha256, all 19 recorded and validator-checked against the vendor files) | referenced at recorded uniform scale s (no re-authoring) |
| per-body relative mass fractions | myohand_body.xml inertial masses | (as above) | renormalized to macaque hand mass |

## (b) Macaque constraints applied (evidence pins)

Sources: E:/PythonChimera/tools/science_funnel/data/macaque_arm/monkeyArm_current.osim
sha256 4148aee2c8dda1dcb0918496ad7c5e1adcf4ebabde0a68a3e0dc67faec67b895
(Limblab monkeyArmModel rev 4fb7dddeec06a0df9525c18f37234a824cb1b5b1);
Geometry/hand.vtp sha256 a06ea7e079c849df07d6eec001e9bcc2ea193ecd3914011c78a993a5faa94fc6;
creature_graph.json sha256 eeaace01160f7a585e3c57fb4a7b2fbe19e2067cd59e1834fb86c972c33eca56
(nodes geom.macaque_arm.hand / .ulna / .radius, schema 2.0.0 intake conventions).

| constraint | evidence | applied as |
|---|---|---|
| hand body mass 0.0490 kg, mass_center [0.012, -0.025, 0.007], inertia [3.82e-05, 1.56e-06, 3.82e-05, 0, 0, 0] | osim Body "hand" (line 1147ff) | anchor body properties verbatim |
| wrist_flexion range [-1.30899694, 1.57079633] rad | osim wrist Coordinate | mutant wrist anchor joint (axis 1 0 0 = TransformAxis rotation1) |
| wrist_abduction range [-1.04719755, 0.78539816] rad | osim wrist Coordinate | mutant wrist anchor joint (axis 0 0 1 = TransformAxis rotation2) |
| hand length 0.08360625 m | geom.macaque_arm.hand bounds_m Y extent (= hand.vtp bbox x 0.001 mm->m) | MUTATION_SCALE s = 0.08360625 / 0.155285 = 0.538404813 |
| forearm reference ulna 0.157971 m / radius 0.139561 m | geom.macaque_arm.ulna/.radius bounds_m | allometric ratio check |
| digit-named muscle anchors ext_digitorum P3 [0.00106101,-0.00804001,0.00594996], P2 [0.00222721,-0.0391191,0.00429738]; flex_digit_profundus P4 [-0.00139132,-0.0172483,-0.00108922] (hand frame, m) | osim Schutte1993Muscle_Deprecated PathPoints on body "hand" | recorded in the mutant anchor frame at osim coordinates; nearest mutant body at rest pose: P3->macaque_hand_anchor (0.010058 m), P2->proxph3 (0.004675 m), P4->fifthmc (0.012604 m) |
| intake conventions: stable ids, sha256 pins, mm->m, species labels | creature_graph.json schema 2.0.0 (ref.macaque_arm.* / geom.macaque_arm.* shapes) | mirrored with model namespace macaque_arm_hand_mutation |

## Stated formula and arithmetic (every derived number traces here)

1. HUMAN_HAND_LENGTH = max over digit chains of |chain displacement from lunate
   origin| in myohand_body.xml = 0.155285 m (thumb 0.103801, d2 0.151999, d3 0.155285,
   d4 0.145358, d5 0.130651).
2. MACAQUE_HAND_LENGTH = 0.08360625 m (hand.vtp Y extent via graph geom node; verified
   against direct hand.vtp bbox parse).
3. s = 0.08360625 / 0.155285 = 0.538404813 (dimensionless).
4. mutant body offset = s x human offset (componentwise). Mutant chain lengths (m):
   thumb 0.055887, d2 0.081837, d3 0.083606, d4 0.078262, d5 0.070343; max = 0.08360625
   = MACAQUE_HAND_LENGTH (identity, diff 0.0).
5. mass prior_i = 0.049 kg x human_mass_i / 0.1589 kg (0.1589 kg = human 19-body sum).
6. digit joint ranges = human ranges verbatim; wrist = macaque ranges verbatim.
7. allometry: human hand/forearm = 0.155285/0.244726 = 0.6345 (forearm = |lunate y|
   0.242 + radius.stl +Y extent 0.0027); macaque hand/forearm(ulna) = 0.08360625/0.157971
   = 0.5293; mutant = 0.5293 (exact). The mutation moves the modeled ratio from 0.6345
   to 0.5293.

## Per-digit derived structure (anchor frame, m; s = 0.538404813)

| digit | body | parent | pos (m) | segment len (m) | joints (range rad) | geometry |
|---|---|---|---|---|---|---|
| thumb | firstmc | anchor | (+0.014260, -0.013473, -0.005643) | 0.020413 | cmc_abduction [-0.5, 0.78]; cmc_flexion [-0.78, 0.7] | 1mc.stl @ s |
| thumb | proximal_thumb | firstmc | (+0.008884, -0.015721, -0.006838) | 0.019309 | mp_flexion [-0.785398, 0.698132] | thumbprox.stl @ s |
| thumb | distal_thumb | proximal_thumb | (+0.007538, -0.013945, -0.005438) | 0.016758 | ip_flexion [-1.309, 0.436332] | thumbdist.stl @ s |
| 2 | secondmc | anchor | (+0.010056, -0.028360, +0.003962) | 0.030350 | (welded to palm, as human) | 2mc.stl @ s |
| 2 | proxph2 | secondmc | (+0.001885, -0.015206, +0.001949) | 0.015446 | mcp2_flexion [0, 1.5708]; mcp2_abduction [-0.261799, 0.261799] | 2proxph.stl @ s |
| 2 | midph2 | proxph2 | (+0.004043, -0.022222, +0.003944) | 0.022928 | pm2_flexion [0, 1.5708] | 2midph.stl @ s |
| 2 | distph2 | midph2 | (+0.001795, -0.013400, +0.000657) | 0.013535 | md2_flexion [0, 1.5708] | 2distph.stl @ s |
| 3 | thirdmc | anchor | (+0.002406, -0.029232, +0.005225) | 0.029792 | (welded to palm, as human) | 3mc.stl @ s |
| 3 | proxph3 | thirdmc | (+0.000129, -0.014155, +0.000957) | 0.014188 | mcp3_flexion [0, 1.5708]; mcp3_abduction [-0.261799, 0.261799] | 3proxph.stl @ s |
| 3 | midph3 | proxph3 | (+0.000888, -0.023803, +0.003354) | 0.024055 | pm3_flexion [0, 1.5708] | 3midph.stl @ s |
| 3 | distph3 | midph3 | (+0.000735, -0.015639, +0.001052) | 0.015692 | md3_flexion [0, 1.5708] | 3distph.stl @ s |
| 4 | fourthmc | anchor | (-0.004336, -0.029921, +0.003144) | 0.030396 | (welded to palm, as human) | 4mc.stl @ s |
| 4 | proxph4 | fourthmc | (-0.000985, -0.012754, -0.000093) | 0.012793 | mcp4_flexion [0, 1.5708]; mcp4_abduction [-0.261799, 0.261799] | 4proxph.stl @ s |
| 4 | midph4 | proxph4 | (-0.001899, -0.021673, +0.000724) | 0.021769 | pm4_flexion [0, 1.5708] | 4midph.stl @ s |
| 4 | distph4 | midph4 | (-0.001247, -0.013347, +0.000303) | 0.013408 | md4_flexion [0, 1.5708] | 4distph.stl @ s |
| 5 | fifthmc | anchor | (-0.009640, -0.026779, -0.001018) | 0.028479 | (welded to palm, as human) | 5mc.stl @ s |
| 5 | proxph5 | fifthmc | (-0.000860, -0.011539, -0.000805) | 0.011599 | mcp5_flexion [0, 1.5708]; mcp5_abduction [-0.261799, 0.261799] | 5proxph.stl @ s |
| 5 | midph5 | proxph5 | (-0.002842, -0.019147, -0.001550) | 0.019419 | pm5_flexion [0, 1.5708] | 5midph.stl @ s |
| 5 | distph5 | midph5 | (-0.001546, -0.011133, -0.001208) | 0.011304 | md5_flexion [0, 1.5708] | 5distph.stl @ s |

Totals: 19 digit bodies (5 metacarpals + 14 phalanges), 20 explicit digit joints,
2 macaque wrist dof on the anchor. Fingertip anchor-frame Y positions all inside the
hand.vtp Y span [-0.0837075, -0.00010125] (thumb -0.043139, d2 -0.079188, d3 -0.082829,
d4 -0.077695, d5 -0.068597).

## (c) Declared deviations (honest adaptation record; species-mixing disclosed)

1. SPECIES MIXING (the core declared adaptation, per the Captain decision): human
   base structure + base bone shapes (Homo sapiens, MoBL-ARD myo_sim) with macaque
   frame numbers (Macaca mulatta research model). This is a derived hybrid for
   training, NOT a species-true macaque scan and NOT a REALITY-category claim.
2. Uniform allometric scale: no macaque per-phalanx proportions exist in-repo
   (PR #229/#230 search evidence); one scale s is applied to all segments instead of
   segment-wise macaque proportions.
3. Carpals not duplicated: the human carpal chain (lunate, scaphoid, pisiform,
   triquetrum, capitate, trapezium, trapezoid, hamate) is folded into the palm anchor
   positionally (firstmc..fifthmc anchor-relative offsets include the carpal offsets);
   the macaque hand body owns the carpus mass/geometry.
4. Radial envelope mismatch (derived observation, recorded not hidden): with the
   human inter-segment directions preserved, the thumb tip lands at X +0.030681 m /
   Z -0.017919 m (outside the hand.vtp X span [-0.0124375, 0.020731] and Z span
   [-0.00152775, 0.00463975]); d2/d3 Z +0.010512/+0.010588 above the +0.00464 Z span;
   d5 X -0.014887 below the -0.0124375 X span. Y-span coherence (the preregistered
   falsifier) holds for all five chains. A uniform scale cannot match the macaque
   envelope in all three axes simultaneously; per-axis anisotropic correction is
   future work requiring macaque per-digit data.
5. Masses are declared training priors (proportional redistribution of the macaque
   hand mass over the digit chains; anchor mass and digit priors are alternative
   allocation views of the same 0.049 kg, not additive). No per-phalanx macaque mass
   data exists.
6. Muscle/tendon paths are anchor points only (osim hand-frame points recorded in the
   mutant anchor frame; nearest-body ownership computed at rest pose); no muscle
   volume, no skin geometry, no wrap objects.
7. Digit joint ranges remain the human base values (no macaque per-digit ROM data
   in-repo); only the wrist carries macaque ranges. Falsifier-relevant: this is a
   constraint-sourcing gap, disclosed rather than invented.
8. Geometry = vendor human STLs at recorded scale s + explicit scaled segment
   vectors; no fabricated mesh, no mesh re-authoring. The macaque hand.vtp envelope
   remains bound to the anchor via the graph record (VTP is not MuJoCo-loadable; the
   MJCF anchor therefore carries no mesh geom and the binding lives in
   mutation_structure.json).

## Artifact identities

Pin refresh 2026-09-29 post-#263/#264 (lane lead/a05-docsync, base 22464551): rows
re-pinned to on-disk sha256 at this head, including this commit's make_manifest_json.py
note fix and its regenerated mutation_manifest.json; the 2026-09-28 seal-time narrative
elsewhere in this manifest is preserved as history.

| artifact | sha256 |
|---|---|
| PREREGISTRATION.md | 0cab8cf7a834d3ac64b634d5a2082ded676a56b4059c237f55974eff296e4cc1 |
| build_mutation.py | 76b8b1476ced544183d36dd3f6af4666ec6a7f2746e44dc49571724f6c3cd266 |
| macaque_hand_mutation.xml | 9c91124600abc67a4a33d78ce79ab1a0604a48b5a9a2e6377d15de05717e5adf |
| mutation_structure.json | 48b037593f63ec473947d787077ab6fbcd3b364afd15765bff508e7d54f45649 |
| derivation_output.txt | c9314d9044d4a0fd35afb46bed78e4d921692f1d1d530092db4729bf1e6ed103 |
| validate_mutation.py | a090c0d17606a42154a6705e134f3d298b5b5cd8bb11fc92e6170f0054d9d292 |
| validation_receipt.json | fa507700611cfdc89149eae6b07a962974945667fcc0bfe14d472e4b74858618 |
| make_manifest_json.py | f7128c5f2e22091bff74c5e5dc505ab75b4b737b02c0da98f4cfa1056a2bfff9 |
| mutation_manifest.json | db7af71636af6c2a2c34a0162bbf1fa3e3d7e3bfb5e829cae754f410d261c329 |

Validator result at manifest time: 37/37 checks passed, 0 failed
(validation_receipt.json; two validator-side defects in the first run were corrected
and are documented in report.md — structure values were unaffected).

## Visible_static capture (anatomy profile)

Labeled capture evidence (preregistered P7): capture/capture_mat2_a05_mutation_20260928.png
(1280x4320 sheet, 6 rows = 3 profile views x diagnostic/clean; 2D orthographic projection
of the mutant skeleton over the macaque hand.vtp envelope point cloud; state binding =
sha256 of mutation_structure.json, hash strip 48b037593f63ec47 rendered on every row).
Manifest + context + validator receipt: evidence/capture_manifest.json,
evidence/capture_context.json, evidence/cameras.json, evidence/validation_receipt.json.
visual_capture.validate_manifest verdict: structurally_valid=True, profile_id anatomy,
capture_kind image, view_count 6 (profile read read-only from the registry sqlite).
Capture sheet sha256: 5f6656c52d7320070c4f2a89b4f2d1d4c8b12ddded43a64f2978ca0853cb1eee.
