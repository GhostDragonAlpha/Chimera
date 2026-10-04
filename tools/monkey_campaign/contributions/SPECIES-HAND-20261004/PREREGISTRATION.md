# PREREGISTRATION (DRAFT v1) — SPECIES-TRUE HAND SCREEN: the proven instrument ladder re-run against true Macaca mulatta hand-bone geometry

- Lane: `wk-species-hand`, `E:/ChimeraWork/monkey-coordination/species-hand/`.
  NO_WORKTREES honored: no worktree, no clone; CPU only via
  `python -B E:/PythonChimera/tools/monkey_campaign/task_package.py seal|run`
  (slots 2/3 only). Acquisition + screening records = phase 1 (COMPLETE, see
  EVIDENCE.md); THIS file is the prereg draft for the phase-2 gated run and
  NOTHING has been executed against the instrument yet.
- Status: DRAFT at chain stop 1 — the committed bytes are the freeze. The
  Lieutenant commits this file ALONE FIRST on the publication lineage; the
  implementation packages pin the committed prereg commit. No instrument run
  of any kind starts before that pin. Author self-review certifies nothing;
  Sergeant review is requested through the Lieutenant.
- Binding precedent inherited verbatim: the frozen instrument
  (`instrument_v2.py` sha256
  `9514c5b15a27948c65563070f16dffee4a5a28347c281a5d7e255fe93e516ddd`),
  the INSTRUMENT-V2 prereg law (control battery gates everything; three-class
  verdicts; F4 no-deviation), the grasp-candidates ladder law, the digit-scan
  extension law (erratum wording: "bracket-resolution artifact class"), and
  the report law (ALL TESTED PLACEMENTS FAILED is the only permitted negative
  form; NO impossibility claim in any sentence).

## 0. The question this card answers (and the verdict it inherits)

The proven verdict (PR #344 merged at astra tip `28a110f2`; sgt FINAL APPROVE;
354/354 GENUINE at the bone level): at the A05 hybrid anatomy (19 human-donor
STLs at scale 0.5384048132470733 + macaque frame numbers), 0 of 197,280
tested placements (54,720 ladder + 142,560 digit-side scan) cleared the
74 mm trunk; bone clearance NEVER passed at any tested digit-side posture;
the pad is the interface. This card asks the Captain's referral question:

    Can TRUE rhesus (Macaca mulatta) hand bones clear the same 74 mm trunk
    at ANY lawful placement, under the SAME frozen instrument, tolerances
    and placement families?

It is a screening card. A pass is feasibility evidence at the scanned
geometry only; a fail is evidence of absence at the tested placements only.
This card is NOT a grasp card: no force stage inputs, no friction, no
dynamics, no claim about the playable objective.

## 1. Frozen source pins (the ONLY species-true geometry inputs; drift = refusal)

- Pisa rhesus skeleton, `Macaca_mulatta_3d_scan_Natural_History_Museum_University_of_Pisa_C_1549.stl`,
  Wikimedia Commons, CC BY-SA 4.0 verified AT RETRIEVAL 2026-10-04 (API
  extmetadata + archived file page rev 1146578100; artist Patrizia17, own
  work; specimen C 1549, Museo di Storia Naturale dell'Università di Pisa).
  - bytes `124518634`; source-declared SHA1 `67e0dcbffb7f64195da29d4507bfd7f0bc9a8ff4`
    reproduced EXACTLY on download; local SHA256
    `3f1536a9ab5c60479364535238d1531bd0b05862bd692edcf53047af51e526fe`
    (`E:/ChimeraWork/research-data/20261004-species-hand/`).
  - MEASURED segmentation state (sealed runner job `cb5d4a640caf4020ab6874d4361e7570`,
    slot 2, PASSED, cleanup_verified true): binary STL, 2,490,371 triangles,
    global AABB extents (270.199, 493.65, 369.055) units, and exactly TWO
    connected components under both bit-exact and crack-tolerant (eps =
    max_extent x 1e-5) welds: the skeleton as ONE merged surface
    (2,490,359 triangles) plus one stray 12-triangle chip. THE HAND BONES
    ARE NOT PER-BONE SEGMENTED IN THE SOURCE. This measured fact makes
    Stage 0 (below) a precondition of any ladder rerun, and it is the
    honest crux of the go/no-go.
  - Units: unitless STL; max extent 493.65 sits in the declared
    millimeters-plausible band for an adult rhesus skeleton. RECORDED
    REASONING, not a verdict; Stage 0 must pin the unit conversion as a
    declared, reproducible step (meters in the certified frame).
  - License obligations carried: attribution (artist + museum) and
    share-alike — any DERIVED mesh published outside the working
    environment must carry CC BY-SA 4.0. Internal screening is unencumbered.
- A05 certified chain conventions (registration target, unchanged):
  mutation structure
  `evidence-store/MAT2-A05/workspace_evidence/48b037593f63_mutation_structure.json`
  sha256 `48b037593f63ec473947d787077ab6fbcd3b364afd15765bff508e7d54f45649`
  (20 bodies/22 hinges/19 certified parent-child edges; allometry scale
  `0.5384048132470733`; `hand_vtp_bounds_m`); XML
  `9c91124600ab_macaque_hand_mutation.xml` sha256
  `9c91124600abc67a4a33d78ce79ab1a0604a48b5a9a2e6377d15de05717e5adf`;
  anchor surface `hand.vtp` sha256
  `a06ea7e079c849df07d6eec001e9bcc2ea193ecd3914011c78a993a5faa94fc6`;
  measured rhesus references carried from Limblab `monkeyArm_current.osim`
  sha256 `4148aee2c8dda1dcb0918496ad7c5e1adcf4ebabde0a68a3e0dc67faec67b895`
  (hand mass 0.0490 kg; wrist ranges; hand-length Y extent 0.08360625 m).
- Frozen instrument + modules, byte-identical reuse only: `instrument_v2.py`
  `9514c5b1...` (above); `grasp_screen.py` `6b924e87...`;
  `grasp_screen_v21.py` `a35facd2...`; `grasp_screen_v22.py` `96ad2809...`;
  `control_input_table.json` `d8aacc23...`; INSTRUMENT_PREREGISTRATION
  `897ca164...`; V2_2_ADDENDUM `cf7da1a8...` (as pinned by the digit-scan
  lane, all re-verified there byte-exact). The run gate re-verifies every
  pin; any mismatch = refusal `input_pin_mismatch`, no measurement.
- Sources (b)/(c) are NOT inputs: MorphoSource M84422 (Nasalis hand micro-CT)
  is license-checked ONLY (record states NO Creative Commons license,
  Copyright Undetermined, Standard agreement, Commercial Use Not Permitted,
  login + click-through + intent statement; download REFUSED this phase and
  this card forbids adopting it without an authorized human acceptance of
  the agreement AND a species-transfer justification — N. larvatus is not
  M. mulatta). Visible Monkey (CC BY-NC + ETRI gate) likewise excluded.
  If the Lieutenant later adopts any such source, THIS prereg is amended by
  a new declared action, never silently.

## 2. Stage 0 (precondition gate): segmentation + registration, fidelity-authored, never outcome-tuned

Stage 0 exists because the source is one fused surface. It is a
GEOMETRY-AUTHORING step and is therefore held to the campaign's
anti-tuning law (the R3 precedent: bone thinning was REJECTED as
tune-to-success):

1. Segment the fused skeleton surface into per-bone components by declared
   geometric criteria (declared BEFORE labeling: the exact cutting rule,
   written into the Stage-0 implementation package, referencing only source
   geometry). Every cut surface is AUTHORED: each bone's authored-cut area
   fraction is computed and recorded per bone; a bone whose authored-cut
   fraction exceeds the declared ceiling (Stage-0 constant, frozen in the
   implementation package) is classed `UNRESOLVED_BONE` and is NOT
   verdict-bearing (it may be visualized, never used for pass/fail).
2. Anatomical labeling of the 19-bone set (or the reduced set: distal
   phalanges + metacarpals) REQUIRES independent visual review (Sergeant
   through the Lieutenant). This text-only lane does not label from pictures
   and makes no picture claims. Labels + review receipt are Stage-0 outputs.
3. Register to the certified frame: wrist-anchored root at the macaque hand
   body origin, `-Y` long axis, the 19-edge/22-hinge naming from the A05
   bytes, units -> meters, a declared similarity registration (unit
   conversion + rigid + uniform scale) whose parameters are recorded. The
   per-bone volume/extent table of the registered true geometry is a Stage-0
   output and MUST be compared against the hybrid's corresponding per-bone
   extents; the comparison table is recorded BEFORE any ladder run and is
   never edited after.
4. NO joint axes, ranges or resting offsets are invented from the scan: the
   certified A05 joint conventions (axes/ranges from the A05 bytes) are
   carried and DECLARED as carried (section 5 absent list). The mounted
   specimen's fixed finger pose is a scan fact, not a kinematic statement.
5. Fidelity gate: Stage 0 fails (and the ladder rerun is NO-GO) if any
   verdict-bearing bone cannot be extracted without fabricating surface that
   the source does not resolve (e.g., inter-osseous fusion across a scanned
   gap must remain visible as an authored seam, never filled to look
   anatomical). Stage 0 optimizes fidelity to the SOURCE BYTES, never the
   ladder outcome; its workers and reviewers are firewalled from any ladder
   result.

## 3. Frozen instrument constants and families (INHERITED, UNMODIFIED)

- Instrument: `instrument_v2.py` sha256 `9514c5b1...` byte-identical; the
  same two-level law (screening spheres -> triangle-level adjudication vs
  the bone meshes + the analytic trunk; `GENUINE_PENETRATION` |
  `PROXY_FALSE_POSITIVE` | `UNRESOLVED_GEOMETRY`, never forced).
- Tolerances: `tau = 1.0e-4` m; `pi_c = 1.0e-3` m (the two declared contact
  segments vs the analytic cylinder); `r_joint = 5.0e-3` m joint-region
  radius (19 certified edges). Robustness columns recorded, never decisive,
  never tuned: tau in {0.5e-4, 2.0e-4}; pi_c in {0.5e-3, 2.0e-3}; r_joint in
  {2.5e-3, 1.0e-2}.
- Trunk: exact analytic cylinder R = 0.037 m, D = 0.074 m, H = 1.158 m —
  UNCHANGED. No trunk shrink, no joint-limit change, no tolerance change,
  no weakened check (Order #19 item 3).
- Control battery: the same five controls (incl. C4/C5 articulated
  constructed truths) run FIRST against the true geometry registration;
  any misclassification => INSTRUMENT_INVALID, no placement result carries
  the card.
- Placement families: the GP1-CC3 declared construction (720 angles x 2
  mirrors = 1,440 coarse axes at the PRIMARY contact pair) + the digit-side
  extension law (digit-side joints at fractions {0.05, 0.275, 0.5, 0.725,
  0.95} single-joint + flexion waves + abduction extremes, exactly as the
  sealed digit-scan grid defines them) applied to the TRUE geometry's
  certified joints. Contact-pair selection for the true geometry: the pair
  mapping is re-derived from the registered anatomy by the same rule used
  for the hybrid (the primary pinch pair), recorded in the implementation
  package BEFORE the run. Same caps discipline (CAP_S1_PER_POSTURE 96; S1
  budget 2.5 h/job; s* bracket [0, 0.15] m; pad-orientation cos > 0 at
  S1-survivor recording); stage 2 full 11,520-axis refinement on hits only;
  stage 3 force stage per the committed grasp-candidates prereg section 6
  (ladder law, unmodified). Pads/soft tissue remain ABSENT (the verdict's
  cause 1 is out of scope for the species question).
- Evidence anchoring: all sealed artifacts through anchor.py before any
  registry reference.

## 4. Frozen predictions (stated BEFORE any run; the honest ones)

- SP-P1 CONTROL BATTERY (gating): PREDICTED all five controls classify
  correctly at the true-geometry registration (the constructed truths are
  gross relative to tau). Any misclassification => INSTRUMENT_INVALID; the
  defect is the finding.
- SP-P2 THE PLACEMENT QUESTION: **UNKNOWN — no predicted direction.** This
  is deliberately different from every prior card in this line (the digit
  scan predicted zero survivors and observed zero). Geometric reasoning,
  stated without guessing a verdict:
  - The hybrid's rejections were placement-scale, not tolerance-scale:
    median crossing depths ~9.3 mm against 2.5-4 mm bones; proven crossing
    depths spanned ~1e-4..3.7e-2 m; the certified digit-2 DOF could not
    clear the crossing anywhere in range (DS-P5: 174-252 crossing events
    per 1,440 axes at every digit-2 posture). The dominant mechanism is a
    rigid digit-fan whose segment lengths and inter-segment proportions are
    HUMAN, uniformly scaled by 0.5384, wrapped on a 37 mm-radius cylinder.
  - A true rhesus fan differs in exactly the quantities that set that
    mechanism: metacarpal/phalanx length ratios (rhesus digits are shorter
    relative to the palm; phalanges more curved), segment mass distribution
    (irrelevant to clearance), and joint spacing. Shorter proximal segments
    reduce the chord a fan can span (the hybrid's measured max chords
    0.0752-0.0796 m only barely exceeded the 0.074 m diameter; the wrap arc
    to a symmetric opposing contact is ~pi*R ~= 0.1163 m) — a direction
    that makes the true hand WORSE at reaching a wrap. More curved,
    relatively longer distal segments against a shorter palm can change
    WHERE the fan meets the solid — the crossing class could open or close.
    The certified frame fixes the hand's total reference length
    (0.08360625 m) for BOTH models, so the two fans differ in distribution,
    not total length. These two directions point oppositely; the card
    measures rather than guesses.
- SP-P3 (recorded, never gating): the Stage-0 per-bone extent comparison
  table will show the true bones shorter/lighter-boned than the hybrid's
  scaled human donor bones. This is an input-quality observation, not a
  placement prediction, and is recorded whether or not it is convenient.
- SP-P4 DETERMINISM: every pipeline twice per run where the inherited law
  requires twins; byte-identical (GP1 CC6 law).

## 5. The honest absent list (every carried assumption, declared)

Carried from the hybrid unless the source provides them (the source is a
dry mounted skeleton surface scan; it provides NONE of these):

1. NO species-true tendon/muscle data: no morphometry, no attachment points,
   no force capacities on the true anatomy. (The Cheng tables are
   Macaca mulatta/fascicularis limb-level morphometry but carry a license
   flag and are NOT inputs to this card.)
2. NO species-true joint axes/ranges for the digit chains: the A05
   conventions carry the human digit-joint PATTERN with human-scaled ranges;
   only the wrist ranges are measured-rhesus (Limblab). The mounted scan
   pose contributes no kinematics.
3. NO cartilage/soft tissue, NO pads (A2-class absent), NO volar friction
   (0.6/0.4 remain NAMED placeholders; the NB-01/02 gap stands).
4. NO per-bone certified provenance beyond this card's Stage-0 outputs: the
   19-bone mapping of the Pisa specimen is authored + reviewed, not
   museum-cataloged. n=1 specimen; age/sex/pathology status of C 1549 as
   cataloged by the museum is recorded, not verified by this lane.
5. Cut surfaces are authored (declared-degradation law, section 2.5);
   inter-osseous articulation gaps in the living animal are NOT resolved by
   a surface scan of mounted bones.
6. The wrist/kinematic chain assumptions of the A05 frame (wrist-anchored
   root, -Y long axis, 19-edge naming) are carried unchanged; the true
   carpals from the scan are registered INTO that frame, which is an
   approximation declared here and reviewed in Stage 0.
7. Units inference (millimeters) is recorded reasoning; Stage 0 pins the
   conversion as a declared step and the comparison table exposes any
   inconsistency.

## 6. Falsifiers (bite-first, observable)

- FA1: any verdict-bearing bone without verified provenance + license (the
  Pisa pins above; any added source without a license determination recorded
  in the lane) => the run refuses (`input_pin_mismatch` / `provenance_missing`).
- FA2: any deviation from the frozen instrument bytes, tolerances, trunk,
  family construction, caps, or witness values => refusal `prereg_deviation`
  (post-hoc tuning proposals route to the Lieutenant as findings, never
  edits).
- FA3: any Stage-0 quantity (cut fractions, label set, registration
  parameters, comparison table) altered after the ladder result existed =>
  card invalid; the alteration itself is the finding (anti-tuning law).
- FA4: any prediction stated without the geometric basis above, or any
  possibility sentence converted into an impossibility sentence anywhere in
  the report => violates the report law; the reviewer is instructed to
  reject on that sentence alone.
- FA5: any no_approach count reported without the "bracket-resolution
  artifact class - roots unverified at this scan's postures" label => report
  defect (inherited erratum law).
- FA6: compute/storage budget overflow handled by silent extension =>
  forbidden; recorded as `TIMEOUT_AT_DECLARED_BUDGET`; extension needs a new
  declaration.

## 7. Resource allowances (declared, bounded)

- CPU ONLY through the canonical task_package runner, slots 2/3 only (slots
  0/1 hold preserved scratch). Stdlib + numpy/scipy; deterministic; NO
  physics engine, NO GPU, NO dynamics.
- Stage 0 authoring/review jobs: <= 2 CPU-hour total (the fused surface is
  2.49 M triangles; the declared geometric cuts are local). Ladder rerun at
  the true geometry: the same declared envelopes as the inherited law
  (screening <= 2 CPU-hour; 1,440-axis sweep with Level-1 prefilter <= 6
  CPU-hour; digit-side extension <= 5 CPU-hour cumulative; battery <= 1
  CPU-hour). Cumulative declared card budget: <= 16 CPU-hour across jobs;
  overflow per FA6.
- Declared retained outputs (< 64 MiB total via --keep): Stage-0 receipts
  (component table, cut-fraction table, label set + review receipt,
  registration parameters, comparison table), ladder receipts + reports,
  determinism receipts. Large intermediates stay out of the package
  (referenced by hash from the data store).

## 8. Report shape (binding)

- Verdict classes everywhere; UNRESOLVED rows first-class; every negative
  stated precisely (exactly what was sampled: the true-geometry registered
  bones, the named joints, the grid postures, the coarse axes; what was NOT:
  continuous space, full-resolution refinement on zero hits, pads, friction,
  dynamics, other specimens). NO impossibility claim in any sentence.
- The Stage-0 provenance block precedes any placement result: source pins,
  license state, cut fractions, labels + review receipt, registration
  parameters, comparison table. A placement verdict without its Stage-0
  block is unpublished.
- Separate publication (new contribution dir + PR); no other lane's bytes.

## 9. Governance

Chain stop 1 (THIS draft) => the Lieutenant commits it ALONE FIRST =>
implementation packages pin the committed prereg commit (refusal on bytes
mismatch) => Stage 0 => Sergeant review of Stage 0 (including the visual
labeling review this lane cannot do) => only then the ladder rerun =>
sealed receipts + EVIDENCE.md => Sergeant review through the Lieutenant =>
publication by the one publication owner. The Captain's referral stays open
until the Lieutenant records this card's verdict.
