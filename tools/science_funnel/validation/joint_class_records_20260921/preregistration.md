# PREREGISTRATION — THE CLASS RECORDS (lane `agent/joint-class-records-20260921`)

Banked BEFORE the amendment is applied and BEFORE this lane's battery first runs.
Bank file: `preregistration.sha256` (sha256 of THIS file). Base: `cf1857c2`
(`agent/tarsal-cycle-pivots-20260921`, the tarsal receipt that names this lane:
"the class-gap amendment is the named successor work").

## 1. RULE 0

**STATEMENT** (someone can disagree). The joints-are-materials law's records are what bind DOFs,
and the committed definition is missing them everywhere but the hips: the law prescribes a pivot
form for ONE class only (the femoral-head sphere, law doc §3/§5/§5A/§5B), and 21 of the 23
committed bonds carry NO class record at all — no `joint_class`, no DOF count, no range source,
no pivot-form prescription. This lane amends the definition: every one of the 23 bonds gains a
`joint_class` record drawn from a five-class taxonomy derived from the held, sha-pinned
citations plus this specimen's own anatomy — including the honest fifth class for the four
in-chain corpse-pose appositions (femur-foot, humerus-hand) that no held model holds a joint
record for, because they are positional contacts of the scanned fetal curl, not anatomical
articulations (this definition's own `pose_contacts` finding). The records are metadata WITH
TEETH: a class's `dof_count` binds what poses may vary, and geometry alone binds nothing (the
tarsal receipt's verdict, now law: the syndesmosis pairs discriminate geometrically yet hold NO
DOF by class record). The amendment changes NO measurement: θ = 0 stays the committed bytes,
and the committed P6/hip/tarsal batteries re-verify green with the records present, differing
from their committed outputs in nothing but the definition-hash echoes their `untouched`
watches must record.

**PREDICTIONS** (not yet measured at banking time).

- **P-A (coverage/teeth).** After the amendment, the definition parses under the committed
  `validate_bond` (extra keys ride as inert metadata, law doc §1.1); all 23 bonds carry
  `joint_class`; the class counts are exactly ball_and_socket 2, hinge_revolute 8,
  condyled_gliding 7, syndesmosis_nodof 2, positional_contact 4; DOF census 3×2 + 1×15 + 0×6;
  every 0-DOF record has `range_rad` null; every 1-DOF record a finite ascending range pair;
  each hip three pairs.
- **P-B (citation).** Every recorded band equals the sha-pinned held record PARSED AT BATTERY
  TIME (no retyped constant passes): hips = gait2392 hip_l/r three coordinates each
  [-2.0943951, 2.0943951] rad; knees = gait2392 knee_angle [-2.0943951, 0.17453293] rad; elbows
  = monkeyArm elbow_flexion [0.34906585, 2.44346095] rad; radioulnar = monkeyArm
  radial_pronation [-1.57079633, 1.57079633] rad; tarsal class = Rajagopal2016 subtalar_l/r
  [-0.34906585, 0.34906585] rad (the registered band of tarsal_cycle_pivots_20260921); the two
  NO-DOF classes cite ABSENCE (no tibiofibular joint in any held model; no anatomical joint at a
  positional contact) and record no number.
- **P-C (byte-identity, A1 static).** The amendment's diff is EXACTLY the 23 inserted
  `joint_class` blocks: all 25 membranes' `vertex_sha256` books still match their committed tris
  bins (the geometry is the rest state, byte for byte), and every pre-existing bond field
  (members, material, cure_strength, rest_length_mm, measured_gap_mm, refined_gap_mm,
  closest_points_mm, evidence, both hips' `anatomical_reading`) is byte-identical to the banked
  pre-amendment snapshot (pre-amendment definition sha256
  `95ddd2802d811f852cb842cfdcda4c1b6b4cc4160151589ec73c38e03d0b6a6c`).
- **P-D (the records change no measurement).** The three committed batteries re-run GREEN with
  the records present — hip_pivot_proof (A1–A6), p6_contrast (P6' v2 both hips, real PASS /
  null FAIL), tarsal_cycle_battery (all six bonds discriminate; the loop closes on both cycles)
  — each `hard_checks_pass` TRUE, and each regenerated `battery.json` differs from its
  committed file ONLY in the definition-sha256 echoes its within-run watches must record (leaf
  paths ending `definition_sha256`, or leaf values equal to the pre-/post-amendment definition
  sha); every other leaf byte-equal, every verdict field identical.
- **P-E (kernel gates).** test_definition 9/9 OK; test_glue 8/8 OK; training_gate PASS.
- **P-F (determinism).** This lane's battery.json is byte-identical on an immediate re-run.

**FALSIFIERS** (named before the run; any one voids the amendment as written).

- **F1** any bond without a `joint_class`, or a class value outside the taxonomy, or counts
  differing from §P-A → the amendment does not cover the graph → VOID.
- **F2** any recorded band not exactly equal to the parsed held-record value, or a cited-file
  sha mismatch, or a number recorded where the class cites absence → an uncited constant in the
  definition (L1 dies) → VOID.
- **F3** any geometry or pre-existing bond field changed by the amendment beyond the inserted
  blocks (P-C) → the amendment moved a measurement or a rest state → VOID.
- **F4** any committed battery re-run differs outside the predicted echo set, or any verdict
  flips, or `hard_checks_pass` FALSE anywhere → the records changed a measurement → VOID, and
  the metadata-teeth claim ("the records change nothing until a pose uses them") dies with it.
- **F5** any kernel gate red → VOID.
- **F6** double-run byte drift in this lane's battery.json → VOID.

## 2. THE TAXONOMY AND THE PER-BOND EXPECTATIONS (the amendment, registered before applying)

Classes (citations per class): **ball_and_socket** — gait2392 hip as three named rotational
coordinates (law doc §1.4), pivot form `sphere_fit` REGISTERED (the hip lane's fits, predicate
P6' v2); **hinge_revolute** — the gait engine's 1-DOF hinge columns (§1.3a) and the OpenSim
one-coordinate hinge records (gait2392 knee; monkeyArm elbow and radioulnar; Rajagopal2016's
PinJoints), pivot form `pin_axis` PRESCRIBED with the axis derivation OPEN per bond;
**condyled_gliding** (the tarsal class) — the Rajagopal2016 subtalar PinJoint band, the
registered band on this class; pivot form `pin_axis` PRESCRIBED (the held PinJoint records; the
receipt's sphere-form results recorded as measured admissible EVIDENCE, never prescription);
**syndesmosis_nodof** — the tibiofibular pairs, DOF 0 by CITED ABSENCE in every held model (law
doc §3(4)); **positional_contact** — the in-chain corpse-pose appositions, DOF 0 because no
anatomical joint exists at the contact to own a coordinate (the `pose_contacts` finding applied
to the in-chain touching edges; flagged for anatomical review).

Sides: chain A of the hind set is the left leg (mem.bone_02 side left, mem.bone_15 side left),
chain B the right (mem.bone_07 side right, mem.bone_17 side right); side read from the membrane
records where present, by chain otherwise. The tasking's "23+2" reads as: all 23 bonds, of
which 2 hips already carry readings — the hips' records are PROMOTIONS (their Hartman & Straus
reading preserved verbatim and referenced), the other 21 are NEW records; no bond exists beyond
the 23 (counted; cyclomatic 23−25+6 = 4).

Per-bond expectations (class | DOF | range_rad | pivot_form):

```
| bond.joint_01_02 | ball_and_socket | 3 | [[-2.0943951, 2.0943951], [-2.0943951, 2.0943951], [-2.0943951, 2.0943951]] | sphere_fit |
| bond.joint_01_03 | ball_and_socket | 3 | [[-2.0943951, 2.0943951], [-2.0943951, 2.0943951], [-2.0943951, 2.0943951]] | sphere_fit |
| bond.joint_02_06 | hinge_revolute | 1 | [-2.0943951, 0.17453293] | pin_axis |
| bond.joint_03_07 | hinge_revolute | 1 | [-2.0943951, 0.17453293] | pin_axis |
| bond.joint_02_15 | positional_contact | 0 | null | none |
| bond.joint_03_17 | positional_contact | 0 | null | none |
| bond.joint_04_08 | positional_contact | 0 | null | none |
| bond.joint_05_09 | positional_contact | 0 | null | none |
| bond.joint_04_10 | hinge_revolute | 1 | [0.34906585, 2.44346095] | pin_axis |
| bond.joint_04_12 | hinge_revolute | 1 | [0.34906585, 2.44346095] | pin_axis |
| bond.joint_05_11 | hinge_revolute | 1 | [0.34906585, 2.44346095] | pin_axis |
| bond.joint_05_13 | hinge_revolute | 1 | [0.34906585, 2.44346095] | pin_axis |
| bond.joint_10_12 | hinge_revolute | 1 | [-1.57079633, 1.57079633] | pin_axis |
| bond.joint_11_13 | hinge_revolute | 1 | [-1.57079633, 1.57079633] | pin_axis |
| bond.joint_06_20 | syndesmosis_nodof | 0 | null | none |
| bond.joint_07_21 | syndesmosis_nodof | 0 | null | none |
| bond.joint_06_25 | condyled_gliding | 1 | [-0.34906585, 0.34906585] | pin_axis |
| bond.joint_20_25 | condyled_gliding | 1 | [-0.34906585, 0.34906585] | pin_axis |
| bond.joint_07_24 | condyled_gliding | 1 | [-0.34906585, 0.34906585] | pin_axis |
| bond.joint_21_24 | condyled_gliding | 1 | [-0.34906585, 0.34906585] | pin_axis |
| bond.joint_07_18 | condyled_gliding | 1 | [-0.34906585, 0.34906585] | pin_axis |
| bond.joint_22_25 | condyled_gliding | 1 | [-0.34906585, 0.34906585] | pin_axis |
| bond.joint_23_24 | condyled_gliding | 1 | [-0.34906585, 0.34906585] | pin_axis |
```

Anatomical readings per bond (registered with the records themselves, in
`apply_class_records.py`): 01_02/01_03 hips (Hartman & Straus 1933, promoted verbatim);
02_06/03_07 knees (femorotibial); 04_10+04_12 and 05_11+05_13 the two osseous appositions of
one elbow hinge per forelimb (humerus articulates with BOTH forearm membranes); 10_12/11_13
radioulnar (the paired-bone morphology that holds 1 DOF here by the held record and NO DOF as
the tibiofibular syndesmosis by cited absence — the record, not the geometry, decides);
06_25/07_24 tarsal 3-cycle DRIVER bonds (the tarsal trochlear region against the tibia);
20_25/21_24 the LOOP bonds (fibulotarsal, lateral malleolar contact) — cycle A loop margin
0.357668256426 mm; cycle B loop margin 0.040529146675 mm at the registered band, THIN, RECORDED
THIN; 07_18 tibiocrural contact of pes fragment 18 (not among the six measured cycle bonds);
22_25/23_24 intertarsal appositions inside the pes masses (the held models carry NO intertarsal
record — the class's cited band is applied as the class record, the joint-level gap named, never
tuned); 02_15/03_17 pes-tucked-against-femur and 04_08/05_09 hand-carried-against-humerus curl
appositions.

## 3. THE CYCLE-B THIN MARGIN, AND ITS CONSEQUENCE (registered)

The tarsal receipt measured cycle B's max loop-bond seat at 2.959470853325 mm against the 3.0 mm
committed touching-class cut: margin 0.040529146675 mm = 1.35% of the cut. The consequence is
registered with the record, not left in prose: on cycle B the practical edge of the subtalar
class band IS the cut — the band cannot widen (no seat room remains), so a future pose that
needs margin narrows the BAND lawfully (a pre-registered, derived narrowing of the class's own
range record on that cycle), never the cut; and the class-prescribed `pin_axis` form is the
receipt's named lawful route to widen the margin itself. The record on bond.joint_21_24 carries
this verbatim.

## 4. RULE 1 — DERIVATION PLAN (no number is chosen)

Every number in the records is CITED from a sha-pinned committed record or banked measurement:
the gait2392/Rajagopal2016/monkeyArm bands are parsed at battery time from the committed files
(the hip lane's "no retyped constant" idiom); the hip fits' radii/RMS are the committed
hip_pivot_proof_20260921 battery's registered values; the tarsal band is the tarsal receipt's
registered R; the margins are the tarsal receipt's L7 numbers; the 3.0 mm cut and the A5 refusal
name `out_of_anatomical_range` are committed law/kernel facts. The pivot-form prescriptions are
the held records' own forms (sphere-fit: the registered hip fit; pin-axis: the engine's hinge
record and the PinJoint records); `none` is prescribed where no joint exists to own a form. No
parameter was swept; one taxonomy was derived; the ONE free structural choice — the fifth
(positional_contact) class — is forced by this definition's own `pose_contacts` finding and is
registered openly here rather than smuggled into a cited class.

## 5. SCOPE AND DISCIPLINE

The lane writes ONLY: its own directory under
`tools/science_funnel/validation/joint_class_records_20260921/` and the 23 `joint_class`
insertions in `infant_skeleton.body.json`. The kernel, the engine, the tris bins, every prior
lane's receipts/batteries/preregistrations, the three osim records and
`docs/THE_ARTICULATION_LAW.md` are READ-ONLY — the law doc specifically CANNOT move, because the
committed p6_contrast hard-banks its stage-5B hash (`law_amendment_b_bank_matches_file`); the
class-taxonomy prose amendment therefore lives in THIS lane's documents, and a §5C append to the
law doc is successor work that must re-bank the stage hashes in its own lane. Exploration before
banking (committed-data determinations only, no run outcomes): reading the committed
definition/validator/batteries/receipts, parsing the three osim records' coordinate ranges, and
composing the records table above.

Banked by: lane `agent/joint-class-records-20260921`. Trailer: `Agent: GLM 5.3`.
