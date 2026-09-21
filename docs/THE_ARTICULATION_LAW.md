# THE ARTICULATION LAW — a corpse-pose is what the scan saw; a creature-pose is what the bonds must make possible

<!-- CHIMERA-LAW -->
> **RULE 0 — EVERY MEMBRANE IS A THEORY. STATE IT BEFORE YOU BUILD IT.** Three parts, all three
> required: a **STATEMENT** someone could disagree with · a **PREDICTION** you have not measured
> yet · a **FALSIFIER** named *before* the run. **A description survives any result; a theory can
> lose.** No falsifier, no build.
>
> **RULE 1 — DERIVE IT BEFORE YOU TRAIN IT.** A parameter sweep is an admission the derivation was
> not done. Before any run, any sweep, any "let's try N variants": trace the variables and show the
> equations close. If you are choosing a number, you broke the chain and substituted taste for a
> law. Ask what QUESTION each variant answers — if the answer is "which number is best", STOP.
>
> **RULE 0 IS ENFORCED AT S-1 VALIDATE** — every port tested alone, and `port_test()` REFUSES to
> register a test that names no falsifier. The model it feeds: `docs/THE_COMPILER.md` — ports →
> primitives → programs → parser → runtime → calibration.
>
> **[docs/THE_LAW.md](THE_LAW.md)** · the method: `docs/THE_WORKFLOW.md` §0
> · 26 rules: `Chimera/docs/EXPERIMENTAL_METHOD.md` · gate: `python tools/training_gate.py`
<!-- CHIMERA-LAW -->

*2026-09-21. Lane `agent/articulation-semantics-20260921`, base `1dc38688` (the hip-bond adoption:
23 bonds, 6 recorded pose_contacts, components 8 → 6). Status: **DESIGN + PREREGISTRATION. The
proof is NOT BUILT** — §6 says exactly why, and what would make the refusal dishonest. This lane
changes no committed byte of the kernel, the engine, or the skeleton definition; it consumes them.*

---

## 0. THE QUESTION

The pose_contacts discovery made this timely: the infant matter skeleton (`Macaca mulatta`
USNM 497136-3, 160 µm CT) is bonded at 23 measured joints and carries 6 recorded curl
appositions — hands, forearms and feet pressed against the composite — because the specimen was
CT-scanned **curled in fetal position**. A standing, walking creature needs those joints to
ARTICULATE: to rotate within anatomical ranges under the muscle/tension laws, instead of either
holding the corpse-pose forever or failing at the glue line the first time a stride demands a
swing. **The difference between a corpse-pose and a creature-pose is articulation.** This doc
surveys what the kernel and the house actually say about joint motion today (all paths cited),
designs the articulation law from the four candidates that derivation admits, and preregisters
the minimal proof: the hip bond `bond.joint_01_02` (bone_01 ↔ bone_02) articulating through its
anatomical range with every kernel law intact.

---

## 1. THE SURVEY — what exists today, cited

### 1.1 The matter kernel: the four laws, and no rotational DOF anywhere

The kernel is `tools/matter_kernel/` (reference models B1–B5, each born from a preregistration in
`docs/evidence/agent_fleet/MATTER_KERNEL/`) plus the definition format it validates. Its laws, as
they live in committed code:

| law | where it lives | what it refuses |
|---|---|---|
| **L1 — materials carry SOURCED constants** | `tools/matter_kernel/definition.py:31-41` (`validate_material`, "spec law 4"); `tools/matter_kernel/constants.py` (every row a citation) | an uncited material constant |
| **L2 — mass derives from geometry × density, cross-checked, never guessed** | `definition.py:44-71,113-117` (`validate_membrane` derives area·thickness·density and holds stated mass to 5%) | a stated mass past tolerance |
| **L3 — bonds are materials** | `definition.py:74-86` (`validate_bond`: exactly two membrane members, a known material, `cure_strength > 0`); `tools/matter_kernel/glue.py` (B2) | a defaulted cure; a bond to a non-membrane |
| **L4 — force is a REQUIRED input, never defaulted** | the refusal clauses of `scratch.py`, `glue.py`, `tensile.py`, `drape.py` ("operator law 2026-09-12: how much force you put on the object must be known") | a computation with an unknown load |

The bond's whole mechanical semantics is `glue.py`'s pull law:

```
F_fail = min(cure·A_glue, yield_a·A_a, yield_b·A_b)     (B2: the weakest load line fails first)
```

**THE SURVEY'S ANSWER: the kernel does not articulate, and it does not merely lack an
integrator — it lacks any rotational quantity at all.** `grep -iE 'rotat|torque|angular|
quaternion|axis|dof|revolute|hinge|moment' tools/matter_kernel/*.py` returns one hit: the English
word "moment" in `tensile.py`'s docstring. Per module: B1 `scratch.py` (contact pressure pinned at
hardness), B2 `glue.py` (normal pull on a bond line), B3 `tensile.py` (a 1-D series chain under
one pull), B4 `drape.py` (tension-only membrane; its own `fold_pitch` field honestly says
"OPEN — needs bending stiffness"), B5 `residency.py` (GPU liveness). None carries a torque, a
moment arm, an axis, an angle, or a range. **"Bonds are rigid after cure" is therefore not a
stated law — it is an ABSENCE**: no committed text claims rigidity; rigidity is what falls out
because no rotational DOF exists to be anything else. Under the current semantics the only legal
way for the femur to change its angle to the pelvis is for the bond to FAIL (`F > cure·A`):
articulation-as-fracture. A stride would be two hip dislocations per cycle.

Two honesty lines. First, the kernel's docstrings cite `KERNEL_SPEC.md` (sections 2 and 4) as
their spec; that file is **not committed on this branch** — this survey reads the committed
validators and reference models, which is what the lane can be held to. Second, the fifth
validator convention — extra keys ride as inert metadata (`refined_gap_mm`, `closest_points_mm`,
`anatomical_reading` all live on committed bonds today) — is not a law but a fact of
`validate_bond`'s exact accepted schema, and it is load-bearing for the design below.

### 1.2 The measured artifact the law must serve

`tools/science_funnel/data/morphosource_ct/matter_skeleton/infant_skeleton.body.json`
(schema `chimera.matter_body.v1`): 25 membranes, **23 bonds** (material `mat.cartilage`, cure
13 MPa per Yamada 1970, `rest_length_mm` = the measured law gap per the pinned refinement law
"bonds are defined on the vertex metric"), **6 pose_contacts** (status: "RECORDED, NOT BONDED …
the specimen's actual contacts in the curled fetal pose … they ride this metadata section, never
the bond graph"), **5 refused_joints** (shoulders 4.60/5.00 mm; singletons 5.82/6.99/7.71 mm —
measured, never tuned), and the adoption receipt of the hip bonds. The hip bonds carry the
richest records in the file:

- `bond.joint_01_02` — femur (left) ↔ axial composite: gap 1.44 mm, refined 1.403 mm,
  `closest_points_mm` on both membranes, anatomical reading "hip joint: femoral head apposed to
  the acetabular region" (Hartman & Straus 1933).
- `bond.joint_01_03` — femur (right) ↔ composite: gap 1.49 mm, refined 1.343 mm, same reading.

**The structural fact that decides the design below: the bond graph is NOT a tree.** 22 bonded
membranes, 23 edges, **4 independent cycles** — including two measured 3-cycles in the hind
chains (06–20–25 and 07–21–24, each a real tarsal triangle). Receipts:
`tools/science_funnel/validation/{matter_skeleton_20260920, axial_adjacency_20260920,
hip_adoption_20260921}/` — the hip adoption's receipt (schema `chimera.rule0_receipt.v1`,
falsifiers F1–F6) is the house pattern this doc's §5 follows.

### 1.3 The house's rotational prior — three places rotation ALREADY exists

The kernel has no rotation; the house has three, and the design must reuse them, not fork them.

**(a) The engine's hinge columns** — `ChimeraEngine/engine/shaders/joints.comp` +
`engine.cpp` (the joints pack, `/joints`, `/joints_bin`). Per joint an **8-float record
`[Jx Jy Jz Ax Ay Az 0 θ_rad]`** — a pivot J, an axis A, one angle θ: a 1-DOF hinge. The pack also
carries per-joint **ROM limits** (`j_rom_` = ext/flex degrees per joint, `engine.cpp:5261`; the
show "sweeps each through its ROM"; the editor clamps an intent into `[lo, hi]` at
`engine.cpp:7963`), FK **parents** (JNT2) and second owners (JNT3), and two pose laws: JNT1
dominant-joint Rodrigues, and JNT2/JNT3 — linear-blend skinning over COMPOSED FK world frames
about fixed rest pivots ("the law of every rigged character"). Below it sits **THE MATTER PASS
(M1)**: the posed surface is a COMMAND and matter relaxes against mesh rest-edge lengths (the
triangle law, `k_stretch`) plus a measured ground plane — the closest thing the house has to
"pose, then let matter answer". Two hard facts matter to this doc: the FK chain is a **TREE**
("chains deeper than 8 are rejected by the loader"), and the kernel's own falsifier idiom — "at
rest every constraint is already satisfied: the pass is a no-op bit-for-bit" — is the same
rest-identity bar §5 preregisters here. Lineage and named debts: `docs/THE_MASTER_LIST.md` H15
(per-joint derived center/axis/ROM; the axial rigid-band and shoulder weight-competition problems
recorded, not patched).

**(b) The captured pivot (the operator's joints-are-membranes frame)** —
`docs/THE_CATEGORIES.md`, the joint/lever line. Joint v1: **"the joint is the first membrane
whose falsifiers are entirely INHERITED from settled members except one: that rotation itself
emerges from pull + fulcrum"** — verdict CONFIRMED (rotation ≥25°, the torque law exact to
0.000 rel err against the pairwise-DRAW moment), with the pivot TRANSIENTLY dislocating and
re-seating ("in a universe where everything attracts, dislocations HEAL — the joint is
self-reducing"). Lever v6: the saddle — **"the fulcrum must CAPTURE the arm so rotation is the
only free degree of freedom"** — held −13.10° rock-steady to 0.01°. The physics of a joint, per
the operator's own line: a captured contact (the pivot), rotation as the one free DOF, torque
from named pulls, and a STOP at derived contact. This is articulation in one paragraph, proven in
the CPM shaker — it just never moved into the bond-graph matter kernel.

**(c) The gait engines' published ranges** — `tools/train_stand.py` reads every primary joint's
range "from the model. No defaults" (`m.jnt_range`), and `seat_in_limits` is the house's range
law in action: the incumbent keyframe sat **10.4° beyond the body's own declared hip extension
stop** and the fix was to seat the pose into the body's own limits — "THE REWARD WAS NEVER THE
DEFECT" (`tools/train_stand.py:86-110`; consumed by `ChimeraEngine/walker.py`, which imports
`joint_ids, seat_in_limits`). `docs/THE_LOCOMOTION_LANE.md` derives the per-joint hinge penalty
(a joint past its range "is resting on capsule and ligament at the end of its EXTENSIVE" range —
the aggregate is a SUM over joints, measured: 3.1 of 29 joints past their stop at any instant).
`tools/chimera_gait.py` contributes the behavioral definition the walker will be judged by
(Hildebrand footfall metrics: duty factor, suspension, periodicity — "distance is a receipt, not
a gait").

### 1.4 The biomechanical prior — OpenSim records already held, sha-pinned

The lineage holds musculoskeletal models whose joints are **records with exactly the fields this
law needs: a name, a motion type, and a closed range** — never an invented number:

| record | file (held) | joints and ranges |
|---|---|---|
| macaque forelimb — the Wiseman-lineage model | `tools/science_funnel/data/macaque_arm/monkeyArm_current.osim`, receipt `download_receipt.json` (limblab/monkeyArmModel @ `4fb7ddde`, MIT, sha256-pinned per file; the operator names this the Wiseman lineage) | 8 CustomJoint / 12 WeldJoint; **7 rotational coordinates with ranges** (rad): shoulder adduction [−1.7453, 0.8727], shoulder rotation [−1.3963, 1.5708], shoulder flexion [−1.3090, 1.5708]; **elbow flexion [0.3491, 2.4435] — a one-sided hinge**; radioulnar pronation [−1.5708, 1.5708]; wrist flexion [−1.3090, 1.5708], wrist abduction [−1.0472, 0.7854]. DOF census: shoulder 3, elbow 1, radioulnar 1, wrist 2 |
| human full body | `research_references/human/opensim/Rajagopal2016.osim` | **10 literal PinJoint records** (ankle [−0.6981, 0.5236], subtalar [−0.3491, 0.3491], mtp [−0.5236, 0.5236], **elbow [0, 2.618]**, radioulnar [0, 1.5708] — per side) + 10 CustomJoint + 2 UniversalJoint: PinJoint = 1-DOF revolute, the range on the coordinate |
| human gait | `research_references/human/opensim/gait2392_thelen2003muscle.osim` | **hip: 3 rotational coordinates, each [−2.0944, +2.0944] rad** (a ball-and-socket as three named DOFs); knee [−2.0944, +0.1745]; ankle [−1.5708, +1.5708] |

The capsule/constraint semantics these records encode, and which §3 adopts verbatim: a joint DOF
is a **coordinate with a closed range**; the range ends are the body's own declared stops
(capsule/ligament/bone-contact); a pose outside the model's own limits is a broken body, not a
sharp reward (the `seat_in_limits` precedent, §1.3c). **The stage caveat, in the open:** these
are ADULT models; the specimen is an infant macaque, and no infant-macaque range citation exists
in the held set. The house already carries this exact shape of honesty — `mat.bone_cortical`'s
`stage_note` uses the adult cortical range as "the cited UPPER ANCHOR … the deviation named,
never tuned". Ranges get the same treatment: adult cited band, stage gap named, no number
invented.

---

## 2. THE CANDIDATES (each answers a question; four exist)

**C1 — Status quo (articulation = fracture).** The question: is a DOF even needed, or is a
welded skeleton enough? Derived answer: no committed text says "rigid" (§1.1 — it is an absence,
not a law), and under the only committed bond semantics a pose change requires `F > cure·A` at
the hip: gait is dislocation, and the curled scan is the only legal pose forever. This also
contradicts the house's own newest measured artifact — `pose_contacts` exists precisely because
the bond graph and the pose state were found to be DIFFERENT kinds of fact. **Rejected: it fails
the mission premise, and it is not even what the kernel says.**

**C2 — Bonds become kinematic hinges (an FK tree over the bond graph).** The question: should the
kernel gain a rigid-body joint object and rotate a spanning tree of it? Derived answer: three
independent failures. (a) *Law L3 dies*: a kinematic joint has no cure semantics — the validator's
required `cure_strength` becomes dead data, i.e. the bond stops being a material. (b) *The
measured graph forbids a tree*: 4 independent cycles (§1.2) — the engine's own FK loader rejects
what is not a parent chain ("chains deeper than 8 are rejected"), and closed-loop kinematics is
machinery no house lane owns. (c) *Rule 1*: choosing a representation for its own sake is a
taste sweep — no question is answered that C3 does not answer with less. **Rejected.**

**C3 — The joints-are-materials law (pose records + DOF metadata on the bond; the operator's
frame, kernel-conformant).** The question: where does a rotational DOF live so that every one of
the four laws still closes? Answer: **in metadata and pose state, with the bond remaining a
material.** The definition format already carries pose state as recorded metadata
(`pose_contacts`) and derived metadata on bonds (`refined_gap_mm`, `closest_points_mm`) without
the validator caring; the engine already owns the hinge wire record (§1.3a); the CPM line already
proved the joint's statics (§1.3b); the lineage already holds the ranges (§1.4). **CHOSEN —
§3.**

**C4 — Per-joint constraint membranes (invent triangle patches straddling each joint to enforce
range through the triangle law).** The question: can range limits be matter instead of records?
Derived answer: the joint gap is EMPTY in the scan — the cartilage is not meshed — so a straddling
membrane means inventing triangles that no measurement owns (against the doctrine that meshes are
clothing, not substrate, and against the adoption receipts' geometry-preserved discipline), and
its stiffness would be a free number (L1 dies). The engine's M1 matter pass already shows matter
answering a pose without inventing geometry. **Rejected.**

---

## 3. THE CHOSEN LAW — the joints-are-materials articulation law

**One paragraph.** An articulation-class bond keeps every field it has today — material, members,
cure, rest_length — and gains three MEASURED-or-CITED records: `joint_class` (the anatomical
class, cited — e.g. the hip bonds' existing Hartman & Straus reading, promoted to the class
record), `pivot_mm` (the rotation center, DERIVED from geometry already committed — for the hip,
the femoral-head center fit on bone_02's committed vertices; §5), and `range` (the closed
anatomical range per coordinate, CITED to a lineage record in the §1.4 table, adult-band with the
infant stage gap named). A **pose** is a separate top-level section — the `pose_contacts` move
repeated for state instead of contact: per joint a named θ in its recorded range, with the
DEFAULT pose being θ = 0 ≡ the scanned corpse-pose (the rest-pose twin of the rest_length law:
"the definition's zero is the measurement"). The posed geometry of a child membrane is the RIGID
Rodrigues transform of its committed triangle set about (pivot, axis) — nothing is resampled, so
area, thickness, density and therefore **mass are exactly invariant**; at θ = 0 the transform is
the identity, so the committed bytes are reproduced bit-for-bit. Cure keeps its number and gains
its rotational READER: it remains the failure strength of the joint's contact, so a posed joint
that demands more than `cure·A` across the apposition DISLOCATES — bond failure exactly as B2
computes it, now at any θ. A pose enters physics only through named forces or torques (a muscle
law, an external load) — an unnarrived pose is metadata only, exactly like a pose_contact. The
serialisation is the engine's existing 8-float joint record (J, axis, θ) plus the ROM record, so
the matter lane and the render lane speak one wire instead of two.

**The four laws re-checked, one by one (the derivation that closes):**

| law | does articulation break it? | the closing |
|---|---|---|
| L1 sourced constants | No new material constant exists. Pivots are DERIVED from committed geometry; axes are DERIVED (the hip's flexion slice: the bilateral line through the two hip pivots; sign set by the recorded curl — the fetal curl IS the measured flexion direction, `pose_contacts`); ranges are CITED to the §1.4 records with the stage caveat | every new number is measured, derived, or cited — the validator's own trichotomy |
| L2 mass from geometry | A rigid transform preserves every triangle's area exactly; thickness and density are untouched | derived mass is EXACTLY invariant (to float), not within-tolerance — a stronger statement than the 5% law needs |
| L3 bonds are materials | Cure is not reinterpreted away: it stays the per-bond failure strength. What changes is that the joint can now ROTATE below that failure instead of only holding or breaking | the B2 law `F_fail = min(cure·A_glue, yield_a·A_a, yield_b·A_b)` holds verbatim at every θ along the posed bond line |
| L4 force is known | A pose is not a force. Physics sees a pose only when a named torque/force drives it (theMuscle's successor lane); recorded poses are metadata, like pose_contacts | nothing moves without a known load; the kernel's refusal clauses keep their meaning |

**What the law does NOT claim.** (1) No infant range exists yet — the adult band is the cited
anchor, the stage deviation is named when measured, never tuned. (2) No dynamics: the kernel has
no integrator and this law adds none; it is STATICS PER POSE — measured quantities (gaps,
contacts, capacities) re-derived on posed geometry. (3) The corpse-pose is not "wrong": it stays
the rest pose; a standing creature is a POSE the definition may carry, and the 6 pose_contacts
belong to θ = 0 only — a posed animal loses them, and they are recorded, never enforced.
(4) Fusion-class bonds (sutures, the tarsal 3-cycles' syndesmosis-class pairs) get NO DOF: for
them today's semantics IS the law, and the class record says so explicitly rather than by
omission — the one thing §1.1 found indefensible.

---

## 4. THE FALSIFIER BATTERY THE DESIGN IMPLIES

Each articulation-class bond inherits every settled law and adds exactly the claims below (the
CPM line's precedent: "falsifiers entirely INHERITED from settled members except one"). Per bond,
before any build:

- **A1 rest identity.** θ = 0 reproduces the committed triangle bytes bit-for-bit (the
  `joints.comp` idiom: "at rest … a no-op bit-for-bit — the falsifier that keeps it honest").
  Fires if a transform, pivot convention or axis sign shifts the rest state.
- **A2 seat through range.** At each cited range endpoint, the posed child's re-derived gap to
  the parent stays inside the touching class (the same 3.0 mm law cut that admitted the bond);
  the pivot is wrong or the class is wrong if the head leaves the apposition region.
- **A3 cure at every angle.** The B2 battery reproduced at a posed θ: holds below `cure·A`,
  fails AT `cure·A`, site named — identical failure force at θ = 0 and θ = extreme.
- **A4 mass exact.** Posed derived mass equals rest derived mass exactly (float-exact; any
  resampling fires).
- **A5 range is a stop, not a suggestion.** A pose request outside the recorded range REFUSES BY
  NAME (`out_of_anatomical_range`), never clamps silently — the `seat_in_limits` law read
  backwards: the definition refuses to mint a pose its own records forbid.
- **A6 definition untouched.** The committed `infant_skeleton.body.json` is read, never written;
  a PoC that edits the definition or its receipts is VOID (the hip adoption's F1/F5 discipline).

---

## 5. RULE 0 — THE PREREGISTRATION (the hip, `bond.joint_01_02`)

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

## 5A. AMENDED PREREGISTRATION — P6′, the two-sided predicate (banked 2026-09-21, BEFORE the contrast re-runs)

**THE VOID STANDS IN THE RECORD: §5-P6 as written is VOID** — fired by its own clause on 2026-09-21
(the null arm PASSED the one-sided cut exactly as the proof lane's banked derivation predicted, while
its head left the socket by 5.7458/3.9460 mm; receipt
`tools/science_funnel/validation/hip_pivot_proof_20260921/receipt.json`, battery sha256
`18f0ef0641cdcba610bb0a67109540220cfb3400bdff1eee2ae6451fb7d81c16`). Nothing above is edited; this
block REPLACES THE PREDICATE ONLY. Successor lane:
`tools/science_funnel/validation/p6_repreregistration_20260921/` — its full derivation and banked
predictions live in its `preregistration.md`, sha256
`3cbb37d878b3bca798f73d83b334e347dcf97c5a8c71502ed45df86ac35a1407`, banked before the re-run.

**STATEMENT.** An arm (head-fit pivot, or the null midpoint) is SEATED at θ of the cited range iff
(i) the law-metric min gap g is in the TWO-SIDED band [tol_ip, 3.0 mm] — upper edge the committed
touching-class cut; lower edge DERIVED: tol_ip = specimen.resolution_um/2 = 0.08 mm, the CT
isosurface's own localization class, because a vertex-vertex reading below half the sampling step
cannot certify that the shells are not THROUGH each other — interpenetration beyond the tolerance is
NOT a seat; and (ii) the head center stays within the fit's own RMS band of its seat:
‖pose(c*) − c*‖ ≤ rms_residual (band_02 = 0.155477725893 mm, band_03 = 0.147474758014 mm) — the
pivot's measured radius+residual ARE the socket's geometry, and a displacement beyond the fit's own
localization is a DISLOCATION. Someone can disagree: the half-voxel edge may be too loose to mean
anything, and the RMS band may be too tight for honest fits — both disagreements are measurable and
both are named as falsifiers below.

**PREDICTION (banked before the re-run).** The REAL arm PASSES P6′ on both hips (displacement 0.0
exactly at every θ; every grid seat reading in [0.08, 3.0] mm, extremes reproducing the committed
0.098475213606/0.160824534903 mm); the NULL arm FAILS P6′ on both hips (displacement 5.745805839276/
3.945980865254 mm at ±R = 36.96×/26.76× beyond the bands, reproducing 2·|c⊥|·sin(θ/2) to 1e-9; hip 03
additionally breaches the seat band at 0.046718998681 < 0.08). The contrast is the proof's content
again; the verdict is reported whichever way it lands.

**FALSIFIERS.** The real arm fails any clause, or the null arm passes both clauses on either hip →
the amendment FAILS and the design REMAINS VOID. The real arm's seats fall below tol_ip anywhere on
the derived grid {−R} ∪ {R·k/5, k = −4..4} ∪ {+R} → the half-voxel derivation is mis-derived and the
amendment voids. Kernel gates red, watched bytes changed, or double-run byte drift → the lane is
void on its own falsifiers (L1–L6 of its preregistration).

---

## 6. WHY THIS LANE DID NOT BUILD THE PROOF (the fence, in the open)

The battery's machinery is small (a Rodrigues transform, a mesh closest-point pass, the existing
`pull_bond`); the PROOF is not, because its load-bearing number — the pivot — is a NEW
MEASUREMENT on committed geometry, and the rule that fixes the femoral-head fit's inliers is
itself a claim that must be pre-registered before fitting (F4 exists precisely because the
obvious failure is tuning the inlier rule until the head stays seated). The house's settled
pattern for "measure a new quantity on the specimen" is a preregistered measurement lane with a
banked hash (`axial_adjacency_20260920` → `hip_adoption_20260921`), not an in-line derivation
inside a design doc. Building half the battery here — the pivot-free invariants P1/P3/P4/P5 —
was considered and REFUSED: green checkmarks on bookkeeping while the seat claim (P2/P6) went
unmeasured is the "passing run in which the channel did nothing" disease
(`docs/THE_MATTER_LANE.md` Phase 8), and a doc with earned-looking greens is worse than an
honest un-proven one. **This doc ships as: design + preregistration + receipt, falsifier
status PREREGISTERED-ONLY.**

---

## 7. THE GATE

Nothing in this lane changes committed behavior; the gates are the repo's own, run unchanged:

```bash
python -m tools.matter_kernel.test_definition      # the definition format, unmodified
python -m tools.matter_kernel.test_glue            # B2, the law cure keeps
python tools/training_gate.py                      # the rules gate
```

The successor proof lane adds its own battery file and its own falsifier registration before its
first measurement (S-1: `port_test()` refuses a test that names no falsifier — A1–A6 are its
list).

---

## 8. SUCCESSION

- The proof lane fires F1 → pivot re-derivation or class re-record; F2 → the joints-are-materials
  law dies and C2 (kinematic joints, a non-material semantics) inherits the question; F3 → the
  transform law is resampling and dies with it; F4 → the lane voids itself.
- When a muscle law arrives (theMuscle's matter-side successor), it drives θ through named
  torques under this law; the captured-pivot statics of `docs/THE_CATEGORIES.md` (§1.3b) are its
  closed-form referee — the pairwise moment about the pivot at every θ.
- The walker inherits: one wire (J, axis, θ, range) from matter to engine, `seat_in_limits`
  semantics on both sides, and a body whose pose is legal because its own records say so —
  a creature-pose, not a corpse-pose.
