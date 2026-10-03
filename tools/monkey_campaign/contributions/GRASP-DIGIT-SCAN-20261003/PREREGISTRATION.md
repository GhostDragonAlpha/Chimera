# PREREGISTRATION (DRAFT) — digit-scan: the DIGIT-SIDE JOINT SCAN of the
# opposing-digit clearance rejection class (the exhausted ladder's named
# unscanned DOF direction), as an independent diagnostic lane

Status: DRAFT (chain stop 1), authored by `wk-digit-scan` for the Lieutenant.
Per the publication law the Lieutenant commits these bytes ALONE and FIRST on
the publication lineage (the GP1/instrument-v2/grasp-candidates precedent);
the committed file is the freeze and every emitted receipt must embed
`preregistration_sha256` of exactly those bytes and refuse any mismatch. No
implementation file, harness run, measurement or capture frame of this card
exists at draft time. Write scope of the draft: the NEW lane dir
`E:/ChimeraWork/monkey-coordination/digit-scan/` (NO_WORKTREES honored: no
worktree, no clone; all CPU verification through
`python -B E:/PythonChimera/tools/monkey_campaign/task_package.py seal|run`;
runner slots 0/1 hold preserved scratch — this lane runs with an explicit
`--slot 2` or `--slot 3`).

- DISPATCH PROVENANCE (Captain's order #1, binding, verbatim intent):
  "Authorize the bounded digit-side joint scan as an independent diagnostic
  lane. Run it against the frozen geometry and report its actual result. Keep
  it off the critical path for designing the replacement hand." The scan is
  the DECLARED COMPLETION of this anatomy's placement search at the digit
  side; its answer goes in the record either way.
- Card: MAT2-GP3-DIGIT-SCAN (Lieutenant-owned mapping), agent-author
  `wk-digit-scan`, lane `E:/ChimeraWork/monkey-coordination/digit-scan/`.
- Campaign clock 2026-09-29 (host 2026-10-03). Independent DIAGNOSTIC lane:
  it is OFF the critical path for the replacement-hand design; no gate of any
  other lane waits on it and it gates nothing but its own record.
- THE TRUNK SCENARIO IS FROZEN: no trunk change (the exact analytic cylinder
  R = `0.037` m, D = `0.074` m, H = `1.158` m, surface `trunk_01.lateral`),
  NO joint-limit change (the certified A05 ranges parsed at run; a value
  outside a certified range is a refusal `posture_outside_certified_ranges`),
  NO tolerance change (tau = `1.0e-4` m, pi_c = `1.0e-3` m — never enlarged,
  no pair removed, no post-hoc tuning).
- EXPERIMENT CLASS: deterministic, sealed, stdlib-only derivation/screen
  battery (the sealed grasp-candidates class). NO physics-engine run, NO
  dynamics claim, NO GPU work, NO friction measurement, NO training, NO
  reach/path claim (the GP2/x_reach fence inherited), NO anatomy redesign.

## 0. What this card is (and is not)

THE EXHAUSTED LADDER (preserved, never rewritten): the grasp-candidates
program (committed prereg `655047b466f5d959e065252670bd275153a4d775`, bytes
`e5bfa3cd32d26785bdcd7441f6af720fdc4a561938ff1c8de3f21dd7a6545106`; PR #325
open, head `ddbd0655`) evaluated 54,720 candidate placements across three
sealed runs — v2.0 7,200 (job `7b8e4127ca5c46a69bc1a8b3a18f2abc` PASSED),
v2.1 11,520 (job `f0da9bb122bb411f9acef57b650f674c` PASSED), v2.2 36,000
(job `a784c5f7d062445b922eeb6fccd7425b` PASSED) — ALL rejected by PROVEN
geometry, zero reaching the exact sweep, the force stage never acquiring
inputs. THE TWO STABLE CAUSES: (1) TIP FOLD — the rigid hybrid thumb-tip
mesh folds deeper than pi_c at its own solved tangency (~66-90% of reachable
axes in every family); (2) OPPOSING-DIGIT CLEARANCE — the opposing digit
crosses the trunk solid at the pinch offsets (proven-by events: distph2
1,936 + 1,894 + 4,926 across v2.0/v2.1/v2.2; distph4 24 + 12 + 412; distph3
24 at the q_zero CONTROL only; fifthmc 374 at F1 only).

THE NAMED UNSCANNED DIRECTION (binding provenance, quoted-in-substance): the
v2.2 addendum (`V2_2_ADDENDUM.md` sha256
`cf7da1a8cc75f522acaa958045ce1977e12f37187211db6980c48f4f1a7c90f4`, frozen
BEFORE the v2.2 run) declared: "the v2.1 rejection class 'opposing digit
crosses the solid' (distph2/distph3/distph4 proven events) is NOT addressed
by cmc_flexion/mp_flexion; ... if the scan rejects everywhere, the class is
named in the EXHAUSTED report as an unscanned DOF direction (a finding for
the Captain, never a silent omission)." The v2.2 scan varied THUMB-side
joints only (cmc_flexion x mp_flexion); the DIGIT-side joints were outside
its named scope. THIS card measures exactly that direction: whether the
certified DIGIT-side joint ranges contain a posture that relieves the
opposing-digit clearance class at the frozen construction.

WHAT THIS CARD IS NOT: it is not a redesign input by construction (the
replacement-hand design does not wait on it — Captain's order); it does not
rewrite any GP1/grasp-candidates verdict (all prior records are
quoted-fact provenance, never rewrite targets); a pass is feasibility
evidence at the represented geometry ONLY, never a grasp-capacity or
biological claim; zero survivors is feasibility evidence of absence under
the DECLARED families, never impossibility (the precise negative statement,
section 6, is binding report law).

## 1. Identity chain (frozen input pins; drift = refusal
## `input_pin_mismatch` / `input_pin_missing`)

All hashes below were re-verified byte-exact by this lane at draft time
(2026-10-03); the run gate re-verifies ALL of them plus the inherited
instrument input gate (14 pins, 19/19 STL pins, VTP AABB identity).

| pin | sha256 |
|---|---|
| instrument_v2.py — THE FROZEN INSTRUMENT, reused BYTE-IDENTICAL (== FINAL seal `ee7c1a24bfb343519e3b03b7a62644d1`, manifest `beb077ed...`, job `dac7d830d1cf4daf83df2db4fec5f38a` PASSED; == the copy in every sealed grasp-candidates package) | `9514c5b15a27948c65563070f16dffee4a5a28347c281a5d7e255fe93e516ddd` |
| grasp-candidates committed prereg (the ladder + screen law + force plan section 6 this card inherits; commit `655047b466f5d959e065252670bd275153a4d775`, file `tools/monkey_campaign/contributions/GRASP-CANDIDATES-20261002/PREREGISTRATION.md`) | `e5bfa3cd32d26785bdcd7441f6af720fdc4a561938ff1c8de3f21dd7a6545106` |
| V2_2_ADDENDUM.md (the scope-limit provenance; frozen before the v2.2 run) | `cf7da1a8cc75f522acaa958045ce1977e12f37187211db6980c48f4f1a7c90f4` |
| grasp_screen.py (v2.0 module: model build, light gate, posture prep, sound vertex scan, exact predicate; reused UNMODIFIED) | `6b924e87151f5e2235b9d9c023be85d0f7602d42020b37df4ba7bf58c0e9e0ea` |
| grasp_screen_v21.py (v2.1 module: axis construction, two-contact offset solve, per-axis screen; reused UNMODIFIED) | `a35facd2f0876d5b7aa595c3af5be7151f121d315f151cdb7a42e9dee86c0407` |
| grasp_screen_v22.py (v2.2 module: stage-1/stage-2 coarse-to-full law, range-fraction posture grid builder; reused UNMODIFIED) | `96ad2809ed928969571fe3b943117d6dba5d9ae905620b963039595313c5cb1b` |
| control_input_table.json (the frozen instrument light gate C1/C2/C3 constructions) | `d8aacc23b27e2caaf60304c0e9a4fe711ac51245c0ca3bf6d021d8f7b5164bf2` |
| A05 certified kinematics/mesh structure `evidence-store/MAT2-A05/workspace_evidence/48b037593f63_mutation_structure.json` (20 bodies / 22 hinges, axes + certified ranges, offsets, mass priors, allometry scale `0.5384048132470733`, `hand_vtp_bounds_m`, the 19 `stl_sha256` pins) | `48b037593f63ec473947d787077ab6fbcd3b364afd15765bff508e7d54f45649` |
| A05 XML rendering cross-check `.../9c91124600ab_macaque_hand_mutation.xml` | `9c91124600abc67a4a33d78ce79ab1a0604a48b5a9a2e6377d15de05717e5adf` |
| anchor envelope surface `E:/PythonChimera/tools/science_funnel/data/macaque_arm/Geometry/hand.vtp` (pin `a06ea7e0...` inside the A05 bytes) | `a06ea7e079c849df07d6eec001e9bcc2ea193ecd3914011c78a993a5faa94fc6` |
| v2.1 runner receipt (job `f0da9bb122bb411f9acef57b650f674c`, PASSED, exit 0, cleanup_verified true; lane copy `grasp-candidates/final_run_v21/runner_receipt.json`) | `5c373edf41a134790c0f8952d1e9b30b7c1c5d357ab8932fffe7b2ed45adf08c` |
| v2.2 runner receipt (job `a784c5f7d062445b922eeb6fccd7425b`, PASSED, exit 0, cleanup_verified true; lane copy `grasp-candidates/final_run_v22/runner_receipt.json`) | `3359a0fcc8136bcf3d809678a73e7a231e36d7ffc5dbb316c65ad95556c58d5c` |
| v2.2 sealed receipt `outputs/grasp_screen_v22_receipt.json` (the rejection decomposition this card diagnoses) | `43f395e2d98935fb916a699f52b94d1775a27ced303ce01438167a26b298542b` |
| CANDIDATE_FORMULATION.md (the frozen taxonomy/screen law of the ladder; T1/T2/T3, S0/S3/S1 stages, caps) | `0c24657de95068eb7499c3b9f140b8467f58e5ba6bcc94d02c69207341dbd1b1` |
| instrument-v2 committed prereg bytes (input-gate authority of the reused instrument) | `897ca164ac5a63437c465783af2dd8f9c743d6c587d5423f4d3cec1b7190bdaf` |
| instrument-v2 lane declaration | `71e31cdd4122e20bfefdf343df28b0e01fc2a51e70cba11296924ca97ce991ea` |

Inherited further pins (x-aperture dual-hash law, G01 trunk report,
GRASP_BENCHMARK, RUNTIME_CONTRACT, mass_register, W04, B07, ASSEMBLY_IDENTITY,
MONKEY_COMPLETION_MAP, capture-gate template): carried VERBATIM by reference
to the grasp-candidates prereg identity chain (section 1 of the committed
bytes); the reused instrument's `run_input_gate` re-verifies the full table
at run.

## 2. The declared scope: WHICH joints, which construction

### 2.1 The scanned joints (16, named from the pinned A05 bytes)

The certified digit-side joints of digits 2-5 (the opposing digits), parsed
FROM the pinned A05 structure at run (the values quoted here are recorded
from those bytes for humans; any grid value outside the parsed range is a
refusal). Per digit k in {2, 3, 4, 5}:

- `mcp{k}_flexion` on body `proxph{k}` — certified range [0.0, 1.5708] rad
  (proximal phalanx flexion);
- `mcp{k}_abduction` on body `proxph{k}` — certified range
  [-0.261799, 0.261799] rad (proximal phalanx ab/adduction);
- `pm{k}_flexion` on body `midph{k}` — certified range [0.0, 1.5708] rad
  (middle phalanx flexion);
- `md{k}_flexion` on body `distph{k}` — certified range [0.0, 1.5708] rad
  (distal phalanx flexion).

16 joints total. THE DECLARED SCOPE SPLIT: the thumb-side joints
(`cmc_abduction`, `cmc_flexion`, `mp_flexion`, `ip_flexion`) and the wrist
joints (`mutation_wrist_flexion`, `mutation_wrist_abduction`) are HELD at
their sealed q_c(PRIMARY) values — the thumb side was v2.2's declared scope
(its 25-point cmc/mp subgrid stands as that direction's scan); the wrist is
fenced (named unscanned direction, section 6 negative statement). The
remaining digit-side joints ARE this card's scan.

### 2.2 The frozen construction (inherited, byte-identical reuse)

- CONTACT PAIR: `distal_thumb` x `distph3` (the certified aperture argmax
  pair; the sealed q_c(PRIMARY) pair). BASE POSTURE: the sealed
  q_c(PRIMARY) 22-joint vector (`instrument_v2.Q_C_PRIMARY`); its witness
  identity (tips + chord `0.0739999998849158` m) is re-verified at run
  (refuse on drift).
- PLACEMENT SOLVE: the sealed v2.1 two-contact construction REUSED VERBATIM:
  the sealed GP1-CC3 axis enumeration (m, vh from the tip origins) x the
  v2.1 tilt phi grid (8 values) x 2 mirrors; the SOLVED mesh-tangency offset
  pair (s*, tau_vh) per axis (41-point bracketing pre-scan + 40 bisections,
  tau bracket +/-0.05 m; s* in the declared bracket [0, 0.15] m).
- SCREENS (the same cheap-screen law, soundness class inherited): S0 vertex
  envelope + S0-CLEARANCE (all 19 bones, sphere-flag prefilter, exact
  `cyl_sdf` vertex scan, early-exit on first hit; PROVEN events only —
  a mesh vertex is a surface point), S3-REACH (certified-range check,
  s* bracket, chord RECORDED gated by nothing, pad-orientation column),
  S1 exact (Level-2 adjudication on S0-survivors under the caps), T3-only
  contacts, anchor envelope class RECORDED never merged, robustness columns
  arithmetic-only. Caps discipline IDENTICAL: CAP_S1_PER_POSTURE = 96,
  cumulative S1 wall-clock budget 2.5 h per job, pad-orientation cos > 0
  active at S1-survivor recording. Class order and counters identical to
  the sealed v2.1 `screen_axis_v21` path.
- STAGE LAW (the v2.2 two-stage structure, inherited): STAGE 1 coarse grid
  — theta every 8th of 720 (90 values) x the 8-value phi grid x 2 mirrors
  = 1,440 axes per posture. STAGE 2 (refinement, hits only): any stage-1
  posture with >= 1 S0-survivor re-runs at FULL resolution (720 theta x
  8 phi x 2 mirror = 11,520 axes); then S1 exact under the caps; a stage-2
  hit list may run in a deterministic follow-up job under THIS prereg.

### 2.3 The posture grid (declared exactly; no addendum needed)

All grid values are computed FROM the parsed certified ranges at run at the
declared fractions f of [lo, hi] (v = lo + f*(hi - lo); v2.2's fraction
convention). Non-scan joints always at the sealed q_c values.

- R0 (REFERENCE posture, not a scan point): all 22 joints at the sealed
  q_c(PRIMARY) values. Role: the in-run anchor for the witness identity,
  the light gate and the DS-P3 replication gate; also the FIRST coarse-grid
  evaluation of the certified posture itself (no sealed coarse-grid q_c run
  exists — recorded for the record, never merged into scan counts).
- TIER A (single-joint relief scan): each of the 16 digit-side joints ALONE
  at f in {0.05, 0.275, 0.5, 0.725, 0.95} => 16 x 5 = 80 postures.
- TIER B (flexion wave, the targeted relief probes for the proven-crossing
  digits): digits {2, 3, 4}: the digit's flexion triple
  (mcp{k}_flexion, pm{k}_flexion, md{k}_flexion) TOGETHER at f in
  {0.275, 0.5, 0.725, 0.95}, mcp{k}_abduction at its sealed q_c value
  => 3 x 4 = 12 postures.
- TIER C (abduction extremes at full curl): digits {2, 3, 4}:
  mcp{k}_abduction at f in {0.05, 0.95} with the flexion triple at 0.95
  => 3 x 2 = 6 postures.
- DIGIT-5 TIER B/C OMISSION, declared honestly: no digit-5-chain crossing
  event exists in any sealed q_c PRIMARY map (the fifthmc events belong to
  the JOINTLESS fifthmc body at the F1 pair — outside any joint DOF and
  outside this lane's pair); digit 5 is covered by Tier A. Named, never
  silent.
- TOTAL: 1 reference + 98 scan postures; stage-1 candidates = 99 x 1,440
  = 142,560. THE SEALED q_c POINT ITSELF IS NOT A SCAN POINT (it is v2.1's
  own evaluated and rejected posture; R0 carries it as reference only).
- NO FRACTION-0 POINTS: the certified digit postures at q_c are already
  inside R0; every scan point moves at least one digit joint (f >= 0.05).

## 3. The honest prediction (stated first, per discipline)

UNDER THE CURRENT DECLARED CONSTRUCTION the honest predicted verdict is
ZERO SURVIVORS — the two structural causes predict rejection: (1) for every
digit-2/4/5-only posture the contact tips and hence the trunk placement are
JOINT-INVARIANT (the axis solve depends only on the two tip meshes and
origins), so the proven thumb-tip fold events persist at every axis that
carries one, and a survivor can only emerge from an axis with NO tip event
(an empirical question — the sealed maps never scanned past the first
proven event); (2) for digit-3 postures the distph3 tip moves and the solve
re-forms per axis, but the thumb-tip fold class dominated every sealed
family at 66-90% of reachable axes and no sealed record shows a
fold-free neighborhood. THE SCAN IS THE DECLARED COMPLETION of this
anatomy's placement search at the digit side: ITS ANSWER GOES IN THE RECORD
EITHER WAY (Captain's order). A prereg that predicts its own honest failure
mode where the structural evidence points is correct discipline, NOT
pessimism; per the refusal-wording law, OBSERVING the predicted rejection is
a SUPPORTED prediction, and OBSERVING survivors is the decisive positive
answer the ladder never reached.

## 4. Frozen predictions and falsifiers

- DS-P1 (THE SCAN'S QUESTION, total): at least one of the 98 scan postures
  yields >= 1 S0-survivor at the stage-1 coarse grid (then stage 2 runs per
  section 2.2). PREDICTED: zero survivors (section 3). OBSERVING ZERO
  SUPPORTS DS-P1. FALSIFIED if any scan posture yields >= 1 stage-1
  S0-survivor — the digit-side DOF relieves the full screen stack at some
  axis, the ladder's force stage acquires its first inputs, and the
  finding is reported as the scan's positive answer.
- DS-P2 (validity/replication gate, decisive, gating): in every job —
  (i) the witness identity holds (R0 FK reproduces the sealed
  Q_C_PRIMARY_TIPS and chord `0.0739999998849158`); (ii) the light gate
  C1/C2/C3 classifies correctly against the frozen control table;
  (iii) the axis-family identity vs `iv.placement_family` matches
  (16-cell check, inherited); (iv) the determinism slice is
  byte-identical. IN ADDITION, in JOB-1: the `s0_reject_no_approach` and
  `s3_reject_bracket` per-posture counts are IDENTICAL across R0 and every
  digit-2/4/5-only posture (their per-axis solves are digit-joint-invariant
  by construction). FALSIFIER: any drift => the defect is the finding;
  results are withheld, the run is preserved
  (INSTRUMENT_INVALID_IN_SITU handling inherited), nothing normalized.
- DS-P3 (the frozen-in fold, subset attribution): every digit-2/4/5-only
  posture yields 0 S0-survivors (the thumb-tip fold leaves no clearance-
  only axis that also passes the tip screens). FALSIFIED if any
  digit-2/4/5-only posture yields >= 1 S0-survivor — then digit motion
  ALONE relieved the opposing-digit class at that axis; recorded as the
  scan's sharpest positive finding.
- DS-P4 (digit-3 postures are honest re-solves): no invariance is predicted
  or asserted for digit-3 postures (the contact tip moves; m, vh and the
  solve re-form per posture). The per-posture decomposition is recorded.
  FALSIFIER: none beyond DS-P2's gates (declared openly).
- DS-P5 (relief measurement, recorded never gating): for the digit-2 postures
  the receipt records the distph2 clearance-event trajectory across the
  grid (counts + first-proven depths, min/median at R0 vs the most-relieving
  posture) — the measured answer to "can the certified index DOF clear the
  crossing at the frozen offsets", reported regardless of survivor counts.

## 5. Execution identity (deterministic, sealed, bounded)

- CODE: ONE new file `grasp_screen_digit.py` in the contribution dir
  `tools/monkey_campaign/contributions/GRASP-DIGIT-SCAN-20261003/` (the
  Lieutenant may refine the dir date at commit), importing the UNMODIFIED
  sealed modules `instrument_v2`, `grasp_screen`, `grasp_screen_v21`,
  `grasp_screen_v22` (byte-identical in-package copies of the pinned
  section-1 bytes; the code pins the committed prereg bytes hash and every
  module/control-table/addendum sha and refuses on drift — the v2.2
  discipline). Serial, deterministic, stdlib-only; fixed iteration order
  everywhere.
- PACKAGE BASE: the Lieutenant's commit of THIS prereg (the implementation
  package seals pinned to the published prereg commit and embeds its bytes
  hash; a seal does not replace the required commit).
- JOB SPLIT LAW (declared; deterministic): JOB-1 = R0 + all digits-{2,4,5}
  postures (Tiers A/B/C: 1 + 72 = 73 postures, 105,120 stage-1 candidates);
  JOB-2 = the digit-3 postures (Tier A 20 + Tier B 4 + Tier C 2 = 26
  postures, 37,440 stage-1 candidates). Stage-2 follow-up jobs (hits only)
  run under the same prereg with the deterministic hit list from the
  stage-1 receipts. Slots: explicit `--slot 2` or `--slot 3` (slots 0/1
  hold preserved scratch — operator instruction; BUSY/exit 75 => wait and
  retry with >= 10 s backoff, no new directories).
- DEV SMOKES: bounded local smokes (a few axes/postures, minutes) declared
  and recorded in the lane EVIDENCE.md; NO result is taken from a smoke.
- DECLARED CPU ENVELOPE for the whole program: <= 5 CPU-hour (basis: the
  v2.2 stage-1 measured-rate class — 36,000 candidates in a declared ~1.1 h
  estimate; 142,560 candidates ~ 3.2 h + stage-2 headroom; the instrument
  lane's measured-envelope lesson applied BEFORE the run). Overflow per the
  F6-class law: recorded finding routed to the Lieutenant, never normalized,
  never silently extended. Per-job timeout 4 h.
- DECLARED RETAINED OUTPUTS (< 64 MiB, all via `--keep`): per job the
  receipt JSON (embeds `preregistration_sha256`; per-posture counters,
  class rows, proven-bone/depth decompositions, DS-P2/DS-P3/DS-P5 records,
  determinism slice, coverage arithmetic) + the human-readable report text;
  stage-2 receipts if triggered. Every load-bearing artifact's sha256 lands
  in `digit-scan/EVIDENCE.md`; evidence anchored through anchor.py before
  any registry reference.
- COVERAGE: per posture the class counts sum exactly to the axis total
  (asserted at run, refuse otherwise); every scan posture's grid values
  re-derived from the parsed certified ranges at run (refusal on any
  out-of-range value).

## 6. Report shape (binding)

- SURVIVORS EXIST: the stage-2 refinement, the S1 exact adjudication under
  the inherited caps, and — on any exact survivor — THE FORCE STAGE per the
  committed grasp-candidates prereg section 6 (the actuator-map frontier,
  `run_actuator_map.py` sha256
  `334ba389cb13e914135a2994d7e56cc1894941f55e86d5c443c23eb67df43e61`, MP
  cap 0.8875, posture-conditional tau(q, f), applied to the survivor's T3
  established contacts at THAT posture). The ladder law runs unmodified.
- ZERO SURVIVORS: the rejection decomposition (per posture per class per
  proven bone, with depths) + THE PRECISE NEGATIVE STATEMENT, verbatim law:
  "ALL TESTED PLACEMENTS FAILED. What was sampled: the 142,560 stage-1
  candidates (+ any declared stage-2 refinement) = 99 postures of the
  declared grid x the coarse axis grid (90 theta x 8 phi x 2 mirrors) at
  the q_c(PRIMARY) contact pair under the sealed v2.1 two-contact
  mesh-tangency offset solve, at the represented geometry (19 pinned STLs
  + hand.vtp envelope, scale 0.5384048132470733). What was NOT sampled: the
  thumb-side joints beyond the sealed q_c vector and v2.2's 25-point
  cmc/mp subgrid; the wrist joints (frozen at 0); the continuous posture
  space between grid points and between range fractions; the full-
  resolution axis space except declared stage-2 hits; the F1/F2/F3 contact
  pairs at digit-side postures; pads/soft tissue (ABSENT); species-true
  anatomy (ABSENT — the A05 hybrid disclosure); measured friction (ABSENT);
  dynamics (none). A UNIVERSAL IMPOSSIBILITY CLAIM IS NOT MADE AND WOULD
  NEED A JUSTIFIED GLOBAL BOUND — none is offered by a grid." The named
  unscanned DOF directions after this card are recorded (wrist; thumb-side
  beyond the v2.2 subgrid; continuous posture space; non-perpendicular pad
  presentations beyond the 8-value tilt grid; anatomy replacement itself —
  the Captain's critical path, which does not wait here).
- Every reading carries the labels: feasibility-at-the-represented-geometry,
  DERIVED-GEOMETRY/DERIVED-PROXY classes as inherited, CONDITIONAL-
  CALCULATION of the certified model class (measured ROM is ABSENT — the
  joint box is the declared A05 mutation-model ranges).
- Separation law: no GP1/grasp-candidates/instrument-v2 byte is rewritten;
  all comparisons phrased as scope differences ("the digit side was outside
  v2.2's named scope; under the same frozen construction the digit-side
  scan yields Z").

## 7. Honest-absent inventory (inherited unchanged by any result here)

Measured friction ABSENT; x_press ABSENT; fingertip pads/soft tissue ABSENT
(contact at pad level untestable; bone-level T2 readings only); species-true
anatomy ABSENT (hybrid human-shape/macaque-scale surfaces; source-fidelity
gap UNQUANTIFIED); certified collision geometry ABSENT (the merged
instrument's mesh adjudication of the REPRESENTED surfaces is the declared
instrument); measured ROM ABSENT (the certified ranges are the declared
mutation-model box); C01 frame round-trip verification registered REQUIRED.
These absences bound every result of this lane to feasibility-at-the-
represented-geometry; no grasp-capacity or biological claim is made.

## 8. Governance and resume state

- Chain stop 1 (THIS file): draft only. The Lieutenant commits these bytes
  ALONE FIRST; implementation dispatches AFTER the committed prereg exists;
  the package pins the committed bytes (`preregistration_sha256` embedded,
  refusal on mismatch). Author self-review certifies nothing; Sergeant
  review is requested through the Lieutenant (no self-approval, no
  picture-inspection claims — visual output is not planned for this
  derivation-class card; any future visual goes through the standing
  two-stage gate).
- This lane edits ONLY: `digit-scan/` + its own contribution dir. The
  grasp-candidates, instrument-v2, grasp-posture, x-aperture and all other
  lanes' bytes are read-only. The E:/PythonChimera dirty checkout and other
  agents' work are preserved.
- Corrections ledger: the refusal-wording law (a predicted refusal observed
  is a SUPPORTED prediction) applies at DS-P1/DS-P3; the K01 finding-1
  lesson applies (no tick windows; the frozen executable quantities are the
  grid sizes/counts; the only timing labels are the inherited S1 cumulative
  clock and the declared CPU envelope); the trunk-frozen order is applied
  verbatim (no trunk/joint-limit/tolerance change).

## 9. Chain identity (for the record)

- Task: the Captain's order #1 via the Lieutenant (bounded digit-side joint
  scan; independent diagnostic lane; off the critical path; frozen geometry;
  actual result reported).
- Graph/criteria identity: the grasp-candidates committed prereg
  (`655047b...`) + `V2_2_ADDENDUM.md` (`cf7da1a8...`) + the sealed ladder
  receipts (jobs `7b8e4127...`, `f0da9bb1...`, `a784c5f7...`) are the
  consumed criteria; PR #325 (head `ddbd0655`) is the preserved
  EXHAUSTED report this card completes at the digit side.
- Candidate revision: THIS draft's bytes (sha256 recorded in
  `digit-scan/EVIDENCE.md` at handoff; the committed bytes are the freeze).
