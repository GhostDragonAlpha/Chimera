# PREREGISTRATION (DRAFT v1) — INSTRUMENT-V2: the corrected two-level collision/penetration instrument (mesh-level adjudication + control battery + GP1 recheck)

- Author lane: `wk-instrument-v2`, `E:/ChimeraWork/monkey-coordination/instrument-v2/`
  (NO_WORKTREES honored; CPU only via
  `python -B E:/PythonChimera/tools/monkey_campaign/task_package.py seal|run`).
- Binding law: `INSTRUMENT_V2_DECLARATION.md` in this lane (the Captain's
  five-item correction order, sections 0-6). THIS prereg freezes the
  predictions, tolerances, falsifiers, pins, and resource allowances BEFORE any
  gated experiment. It must be COMMITTED by the one publication owner (as
  `tools/monkey_campaign/contributions/INSTRUMENT-V2-<date>/PREREGISTRATION.md`
  or the Lieutenant's named equivalent) BEFORE implementation runs; the
  implementation package pins the published prereg commit and embeds its bytes
  hash (GP1 gate precedent, refusal on mismatch).
- Date: 2026-09-29 campaign clock. Status: DRAFT at chain stop 1 — nothing in
  this file is a result; no instrument-v2 measurement exists yet.

## 0. What this card is (and is not)

A MEASUREMENT-INSTRUMENT card: it replaces the GP1 bounding-sphere proxies
(necessary-condition, DERIVED-PROXY — their structural false-positive classes
are measured fact: the anchor-envelope sphere r = 0.0450782444410896 m overlaps
13 anchor-finger pairs at EVERY configuration of the 461-configuration review
sweep; the metacarpal spheres mutually overlap, >= 8/10 pairs at all 461,
secondmc-thirdmc exact clearance -0.028401369544040656 at q = 0) with a
two-level instrument whose Level 2 adjudicates the REPRESENTED surfaces at
triangle level, emitting the honest three-class verdict per pair:
`GENUINE_PENETRATION` | `PROXY_FALSE_POSITIVE` | `UNRESOLVED_GEOMETRY`.
GP1 (merge `c258ae1f...`, PR #317) is PRESERVED as the negative result under
its ORIGINAL instrument; the 0/1440 placement rejection (Sergeant labeled
CC2-bypass exercise; reviewer scratch, certifies nothing) is a fact about
THOSE placements at THAT instrument. Neither GP1 verdict is a rewrite target.

This card is NOT a grasp card: no reach, no placement path, no palm-contact
claim, no friction measurement, no dynamics, no GPU, no n=4 (all fenced as in
GP1 P8); a pass is feasibility evidence at the represented geometry only.

## 1. Frozen input pins (byte-exact; drift = refusal `input_pin_mismatch` / `input_pin_missing`)

Inherited from the GP1 prereg section 7 (all pins re-verified by this lane at
authoring time unless marked otherwise; the run gate re-verifies ALL of them):

- A05 certified kinematics/mesh pins:
  `E:/ChimeraWork/monkey-coordination/evidence-store/MAT2-A05/workspace_evidence/48b037593f63_mutation_structure.json`
  sha256 `48b037593f63ec473947d787077ab6fbcd3b364afd15765bff508e7d54f45649`
  (20 bodies/22 hinges/19 certified parent-child edges, joint axes + ranges,
  offsets `mutation.pos_m`, mass priors, allometry scale `0.5384048132470733`,
  `hand_vtp_bounds_m`, the 19 `stl_sha256` pins — RE-VERIFIED 19/19 MATCH
  against the on-disk STLs by this lane);
  `.../9c91124600ab_macaque_hand_mutation.xml`
  sha256 `9c91124600abc67a4a33d78ce79ab1a0604a48b5a9a2e6377d15de05717e5adf`.
- 19 STLs under `E:/PythonChimera/vendor/myo_sim/meshes/` (per-bone pins inside
  the A05 JSON; the frozen per-bone stats live in this lane's
  `mesh_input_table.json` sha256
  `6e5f3bac345a278eaa994203d48df71fa3a4d5d3f6d9be3e9c59f3b08491cfb2`).
- Anchor envelope: `hand_vtp_bounds_m` (A05); anchor VTP surface pin
  `a06ea7e079c849df07d6eec001e9bcc2ea193ecd3914011c78a993a5faa94fc6`
  (`E:/PythonChimera/tools/science_funnel/data/macaque_arm/Geometry/hand.vtp`;
  1920 points, 2114 polys; the scaled VTP AABB must reproduce
  `hand_vtp_bounds_m` at run).
- x-aperture records (dual-hash law inherited):
  `GRASP_MECHANISMS.md` pinned at current bytes `ac5e258360e45f46e26117147ab944167aafea55b65df549fb4cecbcbf3c1c5d`
  with prefix identity `855c1a9f...` verified at prefix length 22620;
  `EVIDENCE.md` pinned at `68b5e429...` with append-only prefix law
  (NOTE: these two files accepted +7536/+3934 appended errata bytes AFTER the
  GP1 FINAL run; any re-pin follows the GP1 review section 5 law — a new
  declared action, never a silent normalization).
- G01 report `e6d6c432680e503d5a70a1903ed59b52d5044cb8d3c7934da3b0db8acf3293a9`
  (trunk diameter 0.074 m); climb-derivation DERIVATION.md + outputs;
  grasp-geometry module + Sergeant review; FRICTION_SOURCES.md
  (`336118e929bd0b4fb067db5a448dc2e348fed073007787635549a4cf1cf5868b`);
  GRASP_BENCHMARK.md `d936cebe...`; RUNTIME_CONTRACT.md `f33c188b...`;
  mass_register.json `61fb79b1...`; W04 certificate; B07 adoption record;
  ASSEMBLY_IDENTITY.md; capture-gate template pins; MONKEY_COMPLETION_MAP.md —
  exact shas as in the GP1 prereg section 7 (inherited verbatim by reference to
  those pinned bytes; the run gate embeds the same table).
- GP1 sealed records (quoted-fact provenance, never rewrite targets):
  runner receipt `E:/ChimeraWork/task-runner/results/adcbe82b72564a858ef86ad31f2fc868/receipt.json`
  sha256 `ad082fc7d3f2e0bb7c12db9e3ab913b7f343fa4b03f9ed4702d721f85fb4fae7`;
  experiment receipt twins sha256 `e68e608936cacf9384f5701ba84df804e250683feb21b542f6c866f50f8808c5`;
  report twins `d1b9d22fa8eefb7cc9d11f6df119bc0f40d43dfde13ddc6e578c760b48ecffbb`;
  sgt-pr317 REVIEW_EVIDENCE.md and its scratch outputs (the labeled CC3-bypass
  0/1440 facts), lane-copied under `E:/ChimeraWork/monkey-coordination/kanban-reviews/GP1/sgt-pr317/`.
- This lane's declaration: `INSTRUMENT_V2_DECLARATION.md` (sha256 recorded in
  EVIDENCE.md; embedded in the implementation gate).

## 2. Frozen instrument constants (declared BEFORE any rerun)

- Mutation scale `0.5384048132470733`; anchor sphere radius
  `0.0450782444410896` m (AABB construction; reproduced independently by this
  lane from the pinned bytes, value-matching the GP1 receipt).
- Trunk (A4): exact analytic cylinder R = `0.037` m, D = `0.074` m,
  H = `1.158` m; 32-segment render-mesh sagitta `1.7816511312871363e-4` m
  (recorded context only, never a verdict input).
- `tau = 1.0e-4` m contact/adjudication tolerance (all pairs);
  `pi_c = 1.0e-3` m contact-segment allowance (the two declared contact
  segments only, vs the analytic cylinder); `r_joint = 5.0e-3` m joint-region
  radius (19 certified edges; center = certified child-body frame origin at q).
  Robustness columns (recorded, never decisive, never tuned): tau in
  {0.5e-4, 2.0e-4}; pi_c in {0.5e-3, 2.0e-3}; r_joint in {2.5e-3, 1.0e-2}.
- Placement family: the GP1-CC3 declared construction (720 angles x 2 mirrors =
  1,440 placements at the PRIMARY contact pair), reconstructed from the sealed
  GP1 code path with Level-2 adjudication substituted per body.
- Witness configurations: q_c(PRIMARY) exact joint values as sealed (chord
  `0.0739999998849158` m); q = 0; F1/F2/F3 q_c as declared secondaries.

## 3. Frozen predictions (the honest outcomes, including uncomfortable ones)

- P1 CONTROL BATTERY (gating, 5 controls incl. C4/C5 articulated):
  PREDICTED all five controls classify correctly (the constructed truths are
  gross relative to tau and the faceting column). This is the validity gate:
  any misclassification => INSTRUMENT_INVALID, no candidate/placement result
  carries this card, the defect is the finding.
- P2 METACARPAL MUTUAL CLASS (10 mc-mc pairs, at q = 0 and q_c): PREDICTED the
  sphere-level overlaps RESOLVE into a SPLIT: shaft-region pairs
  `PROXY_FALSE_POSITIVE`, CMC-base-region pairs `TOUCHING` or
  `GENUINE_PENETRATION` — the human-donor metacarpal bases in tight mutual
  contact plausibly interpenetrate as meshes. HONEST POSSIBILITY DECLARED: one
  or more GENUINE_PENETRATION verdicts among these structural pairs is a REAL
  finding about the modeled surfaces (the mutated donor meshes genuinely
  interpenetrate at rest) — an anatomical/modeling result, never an
  inconvenience to be tuned away. Falsified if all 10 pairs resolve
  `PROXY_FALSE_POSITIVE` (then the recorded finding is the opposite one).
- P3 ANCHOR-ENVELOPE CLASS (13 anchor-finger pairs): PREDICTED
  `UNRESOLVED_GEOMETRY` for the class — the anchor's only available surface is
  the 1920-point hand.vtp envelope (whole-hand, skin-scale, an order coarser
  than the bone STLs); bone-vs-palm-skeleton collision is untestable against it
  (the bones lie inside the envelope by construction). If the VTP proves
  fine-grained enough to adjudicate, the measured class stands and this
  prediction is FALSIFIED (either way measured, never forced).
- P4 WITNESS-POSTURE REMAINDER (thumb-opposition finger pairs at q_c,
  e.g., distal_thumb vs digit3 segments): PREDICTED `TOUCHING` or near-touch on
  the opposition axis (that is the pose's intent); genuinely open whether any
  finger-finger pair crosses (a crossing would be a REAL `GENUINE_PENETRATION`
  finding, recorded plainly).
- P5 THE 1,440 PLACEMENTS: PREDICTED the corrected instrument resolves the
  previously uniform FAIL class into a MIX: dominant `PROXY_FALSE_POSITIVE`
  (the anchor-envelope vs trunk artifact disappears at mesh level),
  `CONTACT_ONLY` states on the contact segments, and an HONEST OPEN existential:
  whether >= 1 placement is `PENETRATION_FREE`/`CONTACT_ONLY`-clean is THE
  measurement of this card — no predicted direction. A clean placement is
  feasibility evidence at the represented geometry only; zero clean placements
  with a green battery is a REAL geometry finding about these 1,440 placements
  under the represented surfaces — never universal impossibility.
- P6 DETERMINISM: every pipeline twice per run, byte-identical twins (GP1 CC6
  law); the 720x2 family and all Level-2 tests closed-form/deterministic.

## 4. Falsifiers (bite-first, each observable)

- F1: any control of P1 misclassified (e.g., C1 flagged; C3/C4 returned
  `PROXY_FALSE_POSITIVE` or `UNRESOLVED`; C2/C5 returned
  `GENUINE_PENETRATION`) => instrument-invalid; run records INSTRUMENT_INVALID,
  all downstream verdicts withheld, defect preserved.
- F2: any pair forced to a verdict where the declared geometry cannot decide
  (anchor pairs forced `GENUINE_PENETRATION` from a skin envelope; UNRESOLVED
  folded into pass/fail counts) => violates the three-class law; gate refuses.
- F3: any input pin hash mismatch, or the scaled VTP AABB failing to reproduce
  `hand_vtp_bounds_m` => refusal `input_pin_mismatch` (no measurement).
- F4: any deviation between this prereg's frozen constants (tau, pi_c,
  r_joint, family construction, pair set, witness q values) and the executed
  run => refusal `prereg_deviation`; a post-hoc tuning proposal routes to the
  Lieutenant as a FINDING (never an edit).
- F5: twin receipts differ on any pipeline repeat => invalid run.
- F6: a compute budget overflow handled by silently extending => forbidden;
  recorded as `TIMEOUT_AT_DECLARED_BUDGET`, extension requires a new
  declaration.

## 5. Resource allowances (declared, bounded)

- CPU ONLY, through the canonical task_package runner (four slots; this lane
  runs its jobs serially, auto slot). Stdlib-only Python, deterministic
  (fixed iteration order everywhere), NO physics engine, NO GPU, NO dynamics.
- Declared compute envelope: witness/self-collision adjudications (5
  configurations x <= 171 pairs, exact triangle tests with AABB prefilter over
  meshes of 1,566-8,360 triangles): <= 2 CPU-hour. The 1,440-placement x 20-body
  mesh-vs-cylinder sweep with Level-1 prefilter: <= 6 CPU-hour. Control
  construction + battery: <= 1 CPU-hour. Cumulative declared budget for the
  card: <= 9 CPU-hour across jobs; overflow per F6.
- Declared retained outputs (all via `--keep`, < 64 MiB total): the instrument
  receipt (embeds this prereg's published sha; full per-pair triple tables;
  per-placement verdict map; margin maps; control battery results;
  robustness columns; determinism receipt), the human-readable report, and the
  frozen control-input table. Evidence anchor via the existing anchor.py path
  before any registry reference.
- Storage/write scope: this lane dir + the contribution dir of the sealed
  package(s). No other lane's bytes are touched; GP1 records are read-only.

## 6. Report shape (binding; item 5 law)

Separate publication (new contribution dir + PR); classification triple on
every pair row; placement classes everywhere; UNRESOLVED rows first-class;
GP1 comparisons phrased only as instrument differences ("under the ORIGINAL
instrument X; under the CORRECTED instrument-v2 Y"); no GP1 byte rewritten;
honest-summary law per declaration section 5.

## 7. Governance

Prereg commit lands BEFORE gated experiments (one publication owner; the
implementation package seals pinned to the published prereg commit and embeds
the bytes hash with refusal on mismatch). Chain stop 2 (implementation) starts
only after the Lieutenant confirms the prereg commit. Author self-review
certifies nothing; Sergeant review is requested through the Lieutenant.
