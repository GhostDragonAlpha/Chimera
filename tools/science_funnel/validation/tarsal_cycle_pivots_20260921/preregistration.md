# PREREGISTRATION — the tarsal cycles: class-honest pivots, the per-bond contrast, and the loop-closure demo (`tarsal_cycle_pivots_20260921`)

Lane `agent/tarsal-cycle-pivots-20260921`, base `13d7c31e` (branch `agent/p6-repreregistration-20260921`,
the reinstatement head; sparse clone `E:/ChimeraWork/tarsal-agent`, branch
`agent/tarsal-cycle-pivots-20260921`). This file is banked (`preregistration.sha256`) BEFORE the
deciding run; the battery (`tarsal_cycle_battery.py`) re-derives everything below from committed
bytes and is run only after banking. The committed skeleton, the kernel, the engine, and every
prior receipt are consumed READ-ONLY. Nothing below is chosen by taste: every number is committed,
parsed, derived by a stated formula from committed geometry, or a PREDICTION carrying its own
falsifier.

---

## 1. THE QUESTION AND THE PRIOR (the record, never edited away)

The joints-are-materials design (`docs/THE_ARTICULATION_LAW.md` §3, receipt
`articulation_design_20260921/`) was REINSTATED on the hips by the corrected predicate P6′ v2
(`p6_repreregistration_20260921/`: real PASS, null FAIL, 36.96×/26.76× band breaches). THE DESIGN'S
DIFFERENTIATOR — why it beat the FK-tree candidate C2 — is THE CYCLES: the 23-bond graph carries
**4 independent cycles** (§1.2 of the law doc), including two measured tarsal 3-cycles in the hind
chains: **06–20–25 and 07–21–24** ("each a real tarsal triangle"). FK-trees cannot span cycles
(§1.3a: the engine's FK chain is a TREE; C2's failure (b): "closed-loop kinematics is machinery no
house lane owns"). Bonds-as-materials should articulate a cycle natively: pose ONE member and the
OTHER bonds of the cycle carry the motion with their rest lengths and pivots UNCHANGED. This lane
measures exactly that, on the P6 machinery, with the predicate's class-adapted bands.

**TASKING CORRECTION, RECORDED NEVER REPAIRED.** The tasking named "bone 19↔24" among the tarsal
chain joints. THE COMMITTED GRAPH CONTAINS NO SUCH BOND: `mem.bone_19` is a committed unpaired
singleton (hip adoption receipt: refusal row-min 7.71 mm on the law metric; "19 stays isolated");
it is a member of NO bond and NO cycle. The tarsal 3-cycle members are exactly the six bonds
registered in §4. The named `21↔24` IS one of them.

## 2. THE CLASS QUESTION (what the law says, what the held records say)

- **The design's own class statement** (§3(4)): "Fusion-class bonds (sutures, the tarsal
  3-cycles' syndesmosis-class pairs) get NO DOF: for them today's semantics IS the law." That is
  the ONLY class statement the design holds for these bonds.
- **The committed definition carries NO class record on any tarsal bond**: no `anatomical_reading`
  (only the two hip bonds carry one), no `joint_class` — only `evidence: bone_identification_v3
  chain hind touching_edge [a, b], gap_mm g`.
- **The held OpenSim records** (law doc §1.4): `Rajagopal2016.osim` (sha256
  `4ed1b573715b5747a203f6ea1dfdbbc6480ce8f24cf70fb00447591b1f599a1e`, parsed at battery time)
  models the tarsal complex as **literal PinJoint records — 1-DOF revolute with closed ranges**:
  `ankle_l/r [−0.69813170000000002, 0.52359878000000004]`, `subtalar_l/r
  [−0.34906585000000001, 0.34906585000000001]`, `mtp_l/r [−0.52359878000000004, 0.52359878000000004]`.
  `gait2392_thelen2003muscle.osim` (sha256 `18e5b3e406a619a78d109e81e6e2cd4f58681a967808fb52a992bbd2b27db019`)
  carries CustomJoint `ankle/subtalar/mtp` coordinates at the wide ±1.5707963300000001 band
  (recorded context only). **Neither held model contains a tibiofibular joint** (the fibula
  appears as body names only): the held records carry NO DOF for the syndesmosis pairs —
  concordant with §3(4).
- **THE CLASS-HONEST FINDING CLAUSE (stated before any measurement).** The law's pivot
  prescription is written for ONE class only: "`pivot_mm` (the rotation center, DERIVED from
  geometry already committed — for the hip, the femoral-head center fit on bone_02's committed
  vertices)". For gliding/condyled/hinge classes the law prescribes NO pivot form — not a contact
  frame, not a hinge axis, nothing. This lane therefore states, up front: **the hip sphere pivot
  is transplanted here as a MEASURED CANDIDATE, never as a prescribed form.** Whatever the
  contrast shows, the law's next amendment must state the pivot form per class (hinge axis for
  ginglymus; contact-normal frame or equivalent for gliding; NO DOF for fusion/syndesmosis). If
  the transplanted form discriminates on a bond, that is ADMISSIBLE EVIDENCE for the amendment; if
  it does not, the class-gap finding is CONFIRMED BY MEASUREMENT on that bond. Either way the
  finding is recorded with the numbers; neither outcome is tuned away.

## 3. REGISTERED CONSTRUCTIONS (zero free numbers)

- **Bonds and members.** Cycle A = {`bond.joint_06_20` (tibia↔fibula, the syndesmosis pair),
  `bond.joint_06_25` (tibia↔foot, the driver), `bond.joint_20_25` (fibula↔foot, the loop)}; cycle
  B = {`bond.joint_07_21`, `bond.joint_07_24`, `bond.joint_21_24`}. The child of a bond is its
  SECOND member (the committed `members` arrays are ordered proximal-first — verified on all six:
  the fibula is distal to the tibia, the foot distal to both). The demo drives the FOOT member
  (child 25 on A, child 24 on B) about the DRIVER bond's pivot — the tibio-foot motion.
- **Seeds.** The hip lane's rule seeds at the bond's RECORDED closest point; the tarsal bonds
  record none, so the seed is the child-side realized vertex of the committed law metric
  (`hip_pivot_proof.law_gap`, the metric that produced the committed `measured_gap_mm`), taken at
  rest. Correctness guard: the rest law gap must equal the committed `measured_gap_mm` within the
  0.005 mm house metric-transfer tolerance (and equals the banked 12-dp rest readings of §5
  exactly).
- **Pivot candidates.** The hip machinery is imported VERBATIM (F4 discipline):
  `hip_pivot_proof_20260921.hip_pivot_proof.inlier_rule` (band = the child mesh's own median edge;
  anchored monotone growth to a fixed point) + `sphere_fit` (Kasa + Gauss-Newton least-spheres).
  REAL arm pivot = the fitted center c_b on the child's inliers. NULL arm pivot = M_b, the
  midpoint of the realized rest closest pair (the transplant of the hip's "recorded closest-points
  midpoint", derivation-free).
- **Axis.** ONE shared axis for both arms, the hip's bilateral construction transplanted: u = the
  unit line through the two HOMOLOGOUS DRIVER fit centers (cycle A's `bond.joint_06_25` child fit
  and cycle B's `bond.joint_07_24` child fit), left-to-right unspecified (A→B labeling only). The
  pivot is thus the only arm difference — the P6 logic preserved.
- **Bands.** Seat clause upper edge cut = 3.0 mm (the committed touching-class cut);
  `tol_ip = specimen.resolution_um/2 = 160/2/1000 = 0.08 mm` KEEPS its derived value as the gap
  metric's RESOLUTION FLOOR — readings below it are RECORDED per pose (reading_class
  `below_resolution_floor`), never clause-binding (§5B). Displacement band = the bond's OWN fit
  RMS residual (§5A Leg 2 verbatim: the fit's own localization; no multiplier).
- **Range.** R = the Rajagopal2016 `subtalar_angle_l` band edge `0.34906585000000001` rad — the
  tarsal-class cited band, symmetric and identical on both sides (guard at parse time); the
  gliding-class record. Grid = {−R} ∪ {R·k/5 : k = −4..4} ∪ {+R}: 11 poses, the registered probe
  fraction. Sign labeling DEFERRED (no held curl-contact rule binds a tarsal child; every clause
  below is sign-symmetric; the class amendment owns dorsi/plantar labeling).
- **Demo loop reading.** For the loop bonds, the pose-dependent seat clause is evaluated with the
  loop pivot REUSED from rest (ONE derivation per bond for the whole lane — the "pivots unchanged"
  claim, measured by construction). The transported displacement of the loop pivot about the
  driver pivot is RECORDED per pose and is NOT clause-binding (the form prescribes no loop
  displacement clause — the class-gap clause of §2 owns this).
- **FK contrast (counted, no geometry).** From the parsed definition: bonded graph V = 25
  membranes, E = 23 bonds; components C by union-find; cyclomatic number E − V + C must equal 4
  (guard). Both 3-cycles must exist as bond sets (guard). Any spanning tree of a 3-node cycle
  holds ≤ 2 of its 3 edges: the FK representation (§1.3a) cannot carry the cycle-closing bond at
  ANY pose — the counted content of "the thing FK cannot do", which the demo's loop-bond seat
  readings exist to test in the materials graph.

## 4. BANKED CONSTANTS (committed-data determinations, 12 dp)

Exploration DECLARATION: the fits and the analytic constructions below were derived ONCE, from
committed bytes, in the design phase of this lane (before banking, before any grid run); the
deciding run re-derives every one of them by the same committed machinery and must reproduce them
EXACTLY (reproduction guards), then measures the pose-dependent readings for the first time.

```
bond.joint_06_20: gap0=0.479999542236 inl=653 it=62 seed=855
  center=[42.510281096263, 28.580577124817, 49.84341727624]  radius=1.798457133157  rms=0.085764861488
  M=[42.400001525879, 28.799999237061, 47.839998245239]
  cpar=-1.810106381765 cperp=0.893034348418 null_d(±R)=0.310147574043  ratio=3.616255
bond.joint_06_25: gap0=0.659698121371 inl=2079 it=80 seed=6897
  center=[36.83565478293, 32.260135932044, 46.224951880972]  radius=2.725501481479  rms=0.083161873871
  M=[39.039999008179, 30.719999313354, 44.959999084473]
  cpar=-2.104964542012 cperp=2.097709255799 null_d(±R)=0.728526778265  ratio=8.760346
bond.joint_20_25: gap0=2.468359650708 inl=1940 it=115 seed=7017
  center=[37.102235303594, 32.005134837085, 46.103602819749] radius=2.568014657909  rms=0.084481592551
  M=[39.839998245239, 30.159997940063, 47.840000152588]
  cpar=0.488059902892 cperp=3.698208934346 null_d(±R)=1.284374482709  ratio=15.203010
bond.joint_07_21: gap0=0.452547908376 inl=572 it=43 seed=627
  center=[47.968308156265, 28.636882624647, 20.432938517872] radius=2.199498152185  rms=0.080396592835
  M=[48.479999542236, 28.319999694824, 22.799999237061]
  cpar=2.005378537752 cperp=1.394157894337 null_d(±R)=0.484185954915  ratio=6.022469
bond.joint_07_24: gap0=0.861625547431 inl=2221 it=62 seed=7244
  center=[43.784032845164, 29.623876636742, 26.559001107115] radius=2.69091894703   rms=0.079898136736
  M=[46.879999160767, 29.119998931885, 25.760000228882]
  cpar=-1.83384129355 cperp=2.667269893034 null_d(±R)=0.926333111495  ratio=11.593926
bond.joint_21_24: gap0=2.899930898961 inl=2216 it=60 seed=6641
  center=[43.783660151501, 29.630446227854, 26.556460834362] radius=2.68938625145   rms=0.079675095915
  M=[46.680000305176, 28.639999389648, 23.639999389648]
  cpar=-3.809625572542 cperp=1.833649797708 null_d(±R)=0.636819890982  ratio=7.992709
axis u = [0.330508327523, -0.125396983699, -0.935435642851]  separation = 21.023307080657 mm
R = 0.34906585000000001 rad;  grid step R/5 = 0.06981317000000002 rad;  cut = 3.0 mm;  tol_ip = 0.08 mm
```

CLASS SIGNATURE (recorded, non-binding): all six fits reach `fixed_point` with radii
1.798–2.726 mm and RMS residuals 0.0797–0.0858 mm — the tarsal curvature spheres localize at the
isosurface's own half-step (≈ tol_ip = 0.08 mm), about 1.8× TIGHTER than the hip head fits
(0.1475/0.1555 mm). Within each cycle the two foot-member fits land at nearly the SAME center
(A: 0.406 mm apart; B: 0.0038 mm apart) — one convex tarsal surface (the trochlear region)
carrying both appositions. These are the measured materials for the class amendment; they bind
nothing.

## 5. PREDICTIONS (banked BEFORE the deciding run)

- **P-A IDENTITIES (must hold; a miss is an implementation fault, VOID).** REAL arm: d ≡ 0.0
  EXACTLY (float equality) at every grid pose, all six bonds (rotation about an axis through c_b
  fixes c_b). NULL arm: measured d(θ) reproduces 2·|c⊥|·sin(|θ|/2) to ≤ 1e-9 mm at every grid
  pose, all six bonds; d(rest) = 0; d monotone in |θ|. Rest identity: posed vertex arrays at
  θ = 0 are `array_equal` to the committed dedup vertices. Side-bond identity (demo): the
  unposed members' bytes are untouched — g_side(θ) equals g_side(rest) EXACTLY at every pose of
  every demo arm. Untouched watch: every watched sha256 before == after.
- **P-B NULL DISPLACEMENT (banked exact, must hold).** At the grid endpoints the null arm reads
  the §4 `null_d(±R)` values (12 dp) on all six bonds — ratios 3.62×, 8.76×, 15.20×, 6.02×,
  11.59×, 7.99× their own bands: **the NULL arm FAILS the displacement clause at the endpoints on
  ALL SIX bonds.**
- **P-C REAL SEATS (the load-bearing seat prediction).** Every REAL-arm grid seat on every bond
  lands in [0, 3.0] mm (contact class; below-floor readings recorded, never binding).
  FALSIFIER P-C/F: any REAL seat > 3.0 mm → the sphere-pivot form does not seat that bond through
  the registered tarsal band → recorded with the numbers; that bond's articulation claim FAILS at
  this band and the class amendment inherits it.
- **P-D THE PER-BOND DISCRIMINATION (the headline).** REAL PASS ∧ NULL FAIL on each of the six
  bonds (PASS = every grid seat in [0, cut] ∧ d ≡ 0 everywhere; FAIL = displacement clause
  breached at ANY grid pose). FALSIFIER P-D/F: the null passes both clauses on a bond → the
  sphere-pivot form does NO discriminating work at the tarsal band on that bond — the class-gap
  finding is CONFIRMED BY MEASUREMENT on that bond, recorded with its margins; the design's cycle
  claim then rests on the demo alone and the receipt says so.
- **P-E THE LOOP CLOSURE (the differentiator, the demo).** Driving the FOOT member about the
  DRIVER bond's pivot through the registered grid: (i) the DRIVER bond's own predicate holds
  (P-C/P-B legs); (ii) the LOOP bond's seat reading stays in [0, 3.0] mm at EVERY pose under the
  REAL motion, with the loop pivot reused from rest — the loop closes. FALSIFIER P-E/F: any loop
  seat > 3.0 mm under the real motion → the loop does NOT close at this band with this pivot form
  → the design's cycle differentiator is NOT PROVEN on the tarsal class at the registered band →
  recorded with the numbers; the honest successor is the class amendment (a hinge-axis or
  contact-frame pivot form), not a re-run.
- **P-F GRAPH GUARDS.** Cyclomatic number E − V + C = 23 − 25 + 6 = 4; the two 3-cycles exist as
  bond sets; the committed parse reproduces the hip lane's counts (25 membranes, 23 bonds).
- **P-G DETERMINISM AND GATES.** The battery run twice is byte-identical; kernel gates green at
  final state (`test_definition` 9/9, `test_glue` 8/8, `training_gate` PASS).

## 6. FALSIFIERS (named before the run)

- **L1 determinism:** any double-run byte drift → the lane is not checkout-invariant → VOID.
- **L2 untouched:** any watched sha256 changes during a run → VOID (the committed skeleton, the
  kernel inputs, every prior receipt are read-only).
- **L3 gates:** any kernel gate red → VOID.
- **L4 honest arms:** both arms run exactly on the registered constructions (REAL: fitted centers
  and the shared bilateral axis; NULL: realized-pair midpoints on the same axis); verdicts
  recorded whichever way they land; suppressing or retuning either arm is VOID by definition.
- **L5 = P-D/F** the per-bond discrimination, with the honest class-gap alternative as specified.
- **L6 = P-C/F** the real-seat band, with the honest alternative as specified.
- **L7 = P-E/F** the loop closure, with the honest alternative as specified.
- **L8 reproduction:** any re-derived fit, rest gap, axis, or analytic null value differing from
  the §4 banked constants at 12 dp → the lane is not running the registered derivation → VOID.

Trailer: Agent: GLM 5.3
