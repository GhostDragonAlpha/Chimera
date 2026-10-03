# EVIDENCE — grasp-candidates lane (wk-grasp-candidates, chain stop 1)

Task: the Captain's grasp order via the Lieutenant — formulate the next
candidate using ACTUAL CONTACT SURFACES and FULL-HAND CLEARANCE; distinguish
joint origins (T1), mesh surfaces (T2), contact points (T3); NO universal
chord condition; NO off-surface contact points; reject cheap geometric
failures BEFORE another expensive sweep; then contact forces on survivors.
Acceptance = sealed receipts, never prose. NO_WORKTREES honored (no worktree,
no clone; CPU through `python -B E:/PythonChimera/tools/monkey_campaign/task_package.py
seal|run`). Write scope: this lane directory only; no other lane's bytes
touched; the E:/PythonChimera dirty checkout and other agents' work preserved.
Date: campaign 2026-09-29 (host 2026-10-03).

## 0. VERDICT (chain stop 1)

The candidate family v2.0 (perpendicular pinch, mesh-tangency offset) is
CHEAPLY REJECTED EVERYWHERE: 7,200 of 7,200 candidates (5 postures x 720
theta x 2 mirrors) rejected at the S0/S3 screens with ZERO exact-level cells;
no sweep ran. Receipt verdict
`ZERO_SURVIVORS_CHEAP_REJECTION_NO_SWEEP`. The rejection is at the cheap
geometric screens exactly as ordered — the expensive instrument sweep was
saved, and the contact-force stage has no inputs at this stop.

## 1. Chain-stop-1 artifacts (all sha256; lane copies are the referenced bytes)

| artifact | sha256 | role |
|---|---|---|
| CANDIDATE_FORMULATION.md | `0c24657de95068eb7499c3b9f140b8467f58e5ba6bcc94d02c69207341dbd1b1` | THE FROZEN v2.0 SCREEN LAW: taxonomy T1/T2/T3 with measured v1 failure numbers; family v2.0 construction; screen stages; caps (S1 per-posture 96; S1 cumulative 2.5 h; offset bracket [0, 0.15] m); branch law; force plan; honest-absent inventory. Amended ONCE before any run (S1 timing budget declared) — the code pins THIS sha and refuses on drift. |
| PREREGISTRATION_GRASP_CANDIDATES.md | `e5bfa3cd32d26785bdcd7441f6af720fdc4a561938ff1c8de3f21dd7a6545106` | THE DRAFT PREREG (DRAFT until committed ALONE by the Lieutenant): v2.0 rejection map; family v2.1 (axis tilt phi grid x two-contact offset solve) declared with predictions P1-P5 + falsifiers + the program ladder (v2.2 posture variation, then EXHAUSTED); force plan; identity pins; honest-absent inventory. Hash taken AFTER the final numeric correction of this lane (an earlier draft copy hashed `2c0e4a06d8ac9c3b8227df6ab8ff1d307ff5d51ad8b088aa0417a16ad7041b64`; superseded by these bytes before any commit; the committed-file sha is the freeze). |
| grasp_screen.py (in-package) | `6b924e87151f5e2235b9d9c023be85d0f7602d42020b37df4ba7bf58c0e9e0ea` | The screen implementation; imports the merged instrument UNMODIFIED; serial, deterministic; refuses on formulation/instrument/table sha drift. |
| instrument_v2.py (in-package copy) | `9514c5b15a27948c65563070f16dffee4a5a28347c281a5d7e255fe93e516ddd` | REUSED MERGED INSTRUMENT, byte-identical to the FINAL seal `ee7c1a24bfb343519e3b03b7a62644d1` (manifest `beb077ed7ba78aa27abc163ce2e27cd8d3d4de4d442f584cbb05bb0df0c1c477`, job `dac7d830d1cf4daf83df2db4fec5f38a` PASSED). Not edited, not rebuilt. |
| PREREGISTRATION.md (in-package copy) | `897ca164ac5a63437c465783af2dd8f9c743d6c587d5423f4d3cec1b7190bdaf` | The instrument-v2 committed prereg bytes; input-gate authority of the reused instrument. |
| control_input_table.json (in-package copy) | `d8aacc23b27e2caaf60304c0e9a4fe711ac51245c0ca3bf6d021d8f7b5164bf2` | The frozen instrument control table (light gate C1/C2/C3 constructions). |
| package/package.json | `3ca1e7c55e923965f71e0769d1a1622a9b40cafb8b687122dcc0f026a492728d` | Package identity: owner wk-grasp-candidates, task GRASP-CANDIDATES-20261002-SCREEN, base `7222729eca6e9f97f25061c8b1dc3d229bb703d8` (verified == E:/PythonChimera HEAD at creation; other lanes' dirty state preserved). |
| sealed/32fedcafc7014adfbd8f3980e78ef52b/manifest.json | `c270429a9a0c1110eec6df47fb1045c4a3ed92bce6ff779b8140e27d2f966a4a` | THE SEALED MANIFEST of the screen run (4 changed files, all inside the declared write scope). |
| sealed/32fedcafc7014adfbd8f3980e78ef52b/change.patch | `2cebc0d38f635a8ccca7465a5342f47efb9ab16e5b35cdf78c64c41a4b869938` | The sealed binary patch vs base. |
| final_run/grasp_screen_receipt.json | `065328e4942a0bb8794138a96966aa8a3267fcd15ce084b9fb0490dff76b19ec` | THE SCREEN RECEIPT (runner-verified copy). |
| final_run/grasp_screen_report.txt | `eeea10e9247fe97c2e305d686b71c96f2e5cb390de7466a61823157aadca4266` | The human-readable run report. |
| final_run/runner_receipt.json | `e6fbc96c100013a83d9565553da7defea7f01a837d2795e3065a1790a27f4911` | Runner receipt: job `7b8e4127ca5c46a69bc1a8b3a18f2abc`, state PASSED, exit 0, slot 0, cleanup_verified true, declared budget 2 GiB, artifacts hash-pinned by the runner. |
| EVIDENCE.md (this file) | self-referential; the committed/pinned sha is recorded by the Lieutenant at handoff | This record. |

## 2. The screen run (observed facts)

- Command: `python -B E:/PythonChimera/tools/monkey_campaign/task_package.py
  run --sealed .../package/sealed/32fedcafc7014adfbd8f3980e78ef52b --keep
  outputs/grasp_screen_receipt.json --keep outputs/grasp_screen_report.txt
  --timeout 14400 -- python -B
  tools/monkey_campaign/contributions/GRASP-CANDIDATES-20261002/grasp_screen.py`
  (slot auto-selected -> 0). Result dir
  `E:/ChimeraWork/task-runner/results/7b8e4127ca5c46a69bc1a8b3a18f2abc`.
- Gates observed GREEN at run: formulation sha MATCH; instrument copy sha
  MATCH; control table MATCH; inherited input gate ok=True (14 pins; 19/19
  STL pins; VTP AABB identity); LIGHT GATE C1 zero-flags/all-CLEAR, C2
  TOUCHING d=0.0, C3 GENUINE 4.987e-3 m; witness identity (GP1 sealed tips +
  chord 0.0739999998849158 reproduced); axis-family identity vs
  `iv.placement_family` 16/16 cells identical; per-posture coverage
  arithmetic exact (counts sum to 1,440 each; refuse otherwise);
  determinism slice 40/40 cells byte-identical.
- In-run refusals available and unused (no drift occurred).

## 3. THE CHEAP-REJECTION ACCOUNTING (how many rejected at which screen)

Per posture (720 theta x 2 mirror = 1,440 candidates each):

| posture | pair | T1 chord (m) | S0 tip_deep | S0 clearance | S0 no_approach | S3 bracket | S0 survivors | S1 cells | survivors |
|---|---|---|---|---|---|---|---|---|---|
| q_c_PRIMARY | distal_thumb x distph3 | 0.0739999998849158 | 954 | 486 | 0 | 0 | 0 | 0 | 0 |
| q_zero_CONTROL | distal_thumb x distph3 | 0.05560023493843668 | 1032 | 408 | 0 | 0 | 0 | 0 | 0 |
| F1 | distal_thumb x distph4 | 0.07399999923615011 | 24 | 1416 | 0 | 0 | 0 | 0 | 0 |
| F2 | distal_thumb x distph5 | 0.07399999954408089 | 0 | 0 | 1440 | 0 | 0 | 0 | 0 |
| F3 | distal_thumb x distph2 | 0.0739999996051494 | 1336 | 0 | 0 | 104 | 0 | 0 | 0 |
| TOTAL | | | 3,346 | 2,310 | 1,440 | 104 | 0 | 0 | 0 |

(3,346 + 2,310 + 1,440 + 104 = 7,200 exactly.)

Dominant bones (proven-by vertex, first-found): distal_thumb (the thumb tip
mesh folds deeper than pi_c at its own tangency: 3,298 proven events =
954 + 1008 + 1336), distph2 (opposing index distal crosses the solid:
1,936 clearance events = 486 + 408 + 1042), fifthmc (374, F1), distph4
(24, F1), distph3 (24, q_zero). Full-precision markers:
q_c minimum proven non-contact depth 1.048209e-3 m (median 9.336e-3);
q_c minimum proven tip depth 1.000217e-3 m (median 1.988e-3) — minima sit
at the pi_c boundary by threshold construction. F3 bracket rows have
s* in [-1.0e-4, 0) m (wrong mirror side, marginally outside the declared
bracket). Class soundness law: rejects require a PROVEN event (mesh vertex
= surface point inside the instrument's shrunk solid, or deeper than pi_c
in the unshrunk solid); NO_APPROACH rejects the SOLVED-OFFSET CONSTRUCTION
at that axis (no vertex root) and is NOT a mesh-level impossibility proof.
The q_zero control confirms no vacuous pass and does not discriminate
posture feasibility (all postures reject).

## 4. Dev smokes (declared; carry NO results)

- Taxonomy verification (local, ~1 min): fk_origin tips reproduce the sealed
  Q_C_PRIMARY_TIPS; chord/h_len reproduce the merged E1 structural cause;
  mesh extents beyond T1 origins measured (distal_thumb max |v| 0.011926 m,
  nvert 10452; distph3 0.01003 m, nvert 7638; min |v| 0.001971 / 0.001233 m
  — the origins are not on their own meshes).
- Bounded pipeline smokes (local, N_THETA=12 grid, ~30 s total): verified
  gates, plumbing, output shape; one `run_input_gate` tuple-return bug fixed
  BEFORE sealing; determinism-slice dependence on survivors fixed BEFORE
  sealing; a suspected posture-mixing bug was INVESTIGATED AND EXCLUDED
  (per-axis reject rows and depths differ between q_c and q_zero; the
  12-axis aggregate equality was a coarse-grid coincidence).
- Aggregate dev CPU < 0.05 h. The sealed run itself used one slot for
  minutes (runner receipt holds the authoritative accounting).

## 5. Chain position and handoff

- This was chain stop 1 (formulation + cheap screen + prereg draft). The
  gated next steps (v2.1 screen/sweep, force evaluation) require the
  Lieutenant to commit `PREREGISTRATION_GRASP_CANDIDATES.md` ALONE FIRST;
  the implementation package then pins the published prereg commit.
- Reuse discipline kept: the merged instrument was imported byte-identical;
  no byte of any GP1/instrument-v2 record modified; no other lane touched;
  no merge/review authority claimed; Sergeant review requested through the
  Lieutenant. Author self-review certifies nothing.

---

# CHAIN STOP 2 — the ladder executed (v2.1, then v2.2 per its outcome)

Prereg committed by the Lieutenant FIRST: `655047b466f5d959e065252670bd275153a4d775`
(origin/review/GRASP-CANDIDATES-20261002, parent `27ba0ff8` = the
instrument-merged tip), file
`tools/monkey_campaign/contributions/GRASP-CANDIDATES-20261002/PREREGISTRATION.md`,
bytes sha256 `e5bfa3cd32d26785bdcd7441f6af720fdc4a561938ff1c8de3f21dd7a6545106`
(verified == this lane's draft bytes via `git show` before the v2.1 run;
the named-ref fetch touched no HEAD/index/branch/worktree).

## CS2.1 — v2.1 (axis-tilt phi grid x two-contact offset solve)

- Law: the committed prereg section 5 (grid 720 theta x phi in
  {+/-15,+/-30,+/-45,+/-60} deg x 2 mirror = 11,520 axes; two-contact offset
  solve: bisection, 40 iterations, tau_vh bracket +/-0.05 m; q_c-first
  posture cap law; pad-orientation cos > 0 active at S1-survivor recording;
  same caps/tolerances). Implementation: `grasp_screen_v21.py`
  (sha256 `a35facd2f0876d5b7aa595c3af5be7151f121d315f151cdb7a42e9dee86c0407`)
  importing the unmodified v2.0 module and merged instrument; declared
  bracketing pre-scan (41 uniform tau samples) added because bisection
  requires a bracket and the per-vertex discriminants are concave in tau
  (documented in the sealed file header).
- Package: `package-v21/` (task GRASP-CANDIDATES-20261002-V21-SCREEN, base
  `655047b466f5d959e065252670bd275153a4d775` — the base tree carries the
  frozen prereg bytes; the code verifies them at run), package.json sha256
  `970beffc0bf5306a4781057323e5773883753a107629a0f4f2db0c856c439cea`; seal
  `7e10a979d1494153b2d1804e6bb16665`, manifest sha256
  `1940fd803ea8ad7eb0d9495af00363202aa02860da15b40ce69363a56b2bf492`, patch
  sha256 `430cc6dfaa7dc56e9b4defc1bc33deecd8b2f5b99f01c155404f508f5be547de`.
- Run: job `f0da9bb122bb411f9acef57b650f674c` state PASSED, exit 0, slot 2
  (the auto-selected slot refused with runner-side
  `recovery_output_budget_exceeded_preserved` BEFORE this lane's code ran —
  leftover preserved scratch on that slot, reported to the Lieutenant;
  nothing deleted by this lane), cleanup_verified true; receipt sha256
  `b9c5892326c69392579ca4a3dcd6454eec9f3a7cfa56343e8eefaf8ef8c47b84`;
  report sha256
  `dd8570acc1451c311142915f931bcea539cacadf28fb104a06c43ed270c68e82`;
  runner receipt copy sha256
  `5c373edf41a134790c0f8952d1e9b30b7c1c5d357ab8932fffe7b2ed45adf08c`
  (lane dir `final_run_v21/`).
- RESULT: q_c PRIMARY 0 S0-survivors over the full 11,520 axes
  (`ZERO_SURVIVORS_V22_LADDER_BRANCH`): no_approach 2,156 (18.7% — ~~the
  two-contact equalization has no root in the bracket~~ [CORRECTED-BY-ERRATUM
  2026-10-03: the declared 41-sample bracketing pre-scan (2.5 mm spacing) found
  no bracket because g = S_A - S_B is defined only inside a ~1-2 mm window at
  these axes; reviewer audit A proves exactly one root at ALL 2,156 axes and the
  sealed S0 screens reject every one at those fine-scan roots — 1,174 tip_deep
  + 982 clearance, 0 survivors; see ERRATUM E-1a/E-2 below]), tip_deep 7,458
  (64.7% of all axes; = distal_thumb 7,326 + the declared tip distph3 132),
  clearance 1,906 (= distph2 1,894 + distph4 12). 0 exact S1 cells; other
  postures NOT run (the declared cap law). Coverage exact
  (2,156+7,458+1,906 = 11,520); determinism slice 8/8 byte-identical; all
  identity gates + light gate GREEN.
- FROZEN PREDICTIONS: P1 FALSIFIED (0 survivors vs predicted >= 1);
  P2 FALSIFIED (tip-deep share of reachable 79.6% >= 50% — WORSE than
  v2.0's 66.3%: adding the tilt and the two-contact constraint did not
  relieve the dominant fold class; it concentrated it). P3-P5 not reached
  (no S1 cells, no force inputs).
- LADDER BRANCH: v2.2 per the committed prereg (declared before the v2.2
  run in `V2_2_ADDENDUM.md`, sha256
  `cf7da1a8cc75f522acaa958045ce1977e12f37187211db6980c48f4f1a7c90f4`:
  cmc_flexion x mp_flexion at certified-range fractions {0.05, 0.275, 0.5,
  0.725, 0.95} = 25 postures, all other joints at the sealed q_c values;
  stage 1 coarse theta (every 8th) x v2.1 phi grid x 2 mirrors = 1,440
  axes/posture; stage 2 full-resolution re-run for hitting postures only;
  V2.2-P1/P2 frozen; the thumb-only scope limit and the unscanned
  opposing-digit DOF direction declared honestly).

## CS2.2 — v2.2 (posture variation: cmc_flexion x mp_flexion scan)

- Law: committed prereg section 5 ladder + `V2_2_ADDENDUM.md` (frozen
  BEFORE the run; sha above). Implementation: `grasp_screen_v22.py`
  (sha256 `96ad2809ed928969571fe3b943117d6dba5d9ae905620b963039595313c5cb1b`)
  importing the unmodified v2.1/v2.0 modules and merged instrument.
- Package: `package-v22/` (task GRASP-CANDIDATES-20261002-V22-SCREEN, base
  `655047b466f5d959e065252670bd275153a4d775`), package.json sha256
  `6aac923797e1f9e24bd1ca9c4e1015cf8fad69bdf31b6f08a0328d8c9b91b84c`; seal
  `f1083a0baf214748a566b594d2fa99a3`, manifest sha256
  `70274feda909459985cd43eacb7e6d93995571e693901f6fd36e8b68152cb337`, patch
  sha256 `01268925b32b35844cb55ffde8263be1bf6eddac5180aa468115e040960eab41`.
- Run: job `a784c5f7d062445b922eeb6fccd7425b` state PASSED, exit 0, slot 2,
  cleanup_verified true; receipt sha256
  `43f395e2d98935fb916a699f52b94d1775a27ced303ce01438167a26b298542b`;
  report sha256
  `121243a672a7510a48a382a0ccc58eb57d95dd1c3023c3a92ff567a68fe33fb3`;
  runner receipt copy sha256
  `3359a0fcc8136bcf3d809678a73e7a231e36d7ffc5dbb316c65ad95556c58d5c`
  (lane dir `final_run_v22/`).
- RESULT (`ZERO_SURVIVORS_LADDER_EXHAUSTED`): all 25 scanned postures
  rejected at the coarse stage-1 grid; 0 S0-survivors anywhere; stage 2
  never triggered; 0 exact S1 cells; 0 force inputs. 36,000 candidates:
  tip_deep 29,674 (82.4% = distal_thumb 28,066 + the declared tip distph3
  1,608), clearance 5,338 (14.8% = distph2 4,926 + distph4 412),
  no_approach 988 (2.7%). The scan moved the T1 chord across the diameter
  in BOTH directions (0.040808-0.079645 m vs 0.074) — the abolished chord
  gate exercised both ways; ~~every rejection is geometric~~
  [CORRECTED-BY-ERRATUM 2026-10-03: false for the 988 sealed no_approach rows;
  corrected v2.2 decomposition 474 no_approach / 5,544 clearance / 29,982
  tip_deep; 514 of the 988 are proven geometric at reviewer-derived fine-scan
  roots, 474 are genuine construction-refusals — see ERRATUM E-1b/E-2 below]
  (per-class rows
  per posture in the receipt). Coverage exact per posture (25 x 1,440);
  determinism slice 8/8 byte-identical; all identity gates + light gate
  GREEN.
- FROZEN PREDICTIONS: V2.2-P1 FALSIFIED (0/25 postures with a stage-1
  S0-survivor); V2.2-P2 FALSIFIED (best reachable tip-deep share 76.8%
  at P18, >= 50%). Varying the thumb's cmc/mp flexion did not relieve
  the dominant fold class; the opposing-digit crossing class persisted
  (distph2 4,926 proven events) — exactly the declared scope limit.

## CS2.3 — THE LADDER'S ANSWER: EXHAUSTED (the report to the Captain)

Per the committed prereg's program law: v2.0, v2.1, and v2.2 all reject at
the cheap geometric screens with ZERO survivors at every stage — the
candidate-family line for this hand is EXHAUSTED at the declared
posture/placement space. The honest statement of what was measured:

- 54,720 candidate placements evaluated across three sealed runs (v2.0:
  7,200; v2.1: 11,520; v2.2: 36,000), ~~every one rejected by PROVEN
  geometry~~ (a mesh vertex — a surface point — inside the instrument's
  shrunk solid, or deeper than pi_c at the solved tangency), ~~never by
  proxy or guess~~ [CORRECTED-BY-ERRATUM 2026-10-03: as sealed, 3,144 rows
  (2,156 v2.1 + 988 v2.2) were S0_REJECT_NO_APPROACH construction-refusals with
  NO proven geometric event; corrected accounting: 51,576 formed candidates
  rejected by proven geometry + 2,670 reviewer-proven geometric rejections at
  fine-scan roots + 474 genuine construction-refusals = 54,720; 0 survivors
  anywhere; see ERRATUM E-1b/E-2 below]; zero candidates required, and none
  received, the exact
  Level-2 sweep; the contact-force stage never acquired inputs.
- The two structural causes, stable across all three families:
  (1) TIP FOLD — the rigid hybrid thumb-tip surface pressed onto the
  37 mm trunk folds deeper than pi_c at its own solved tangency for
  ~66-90% of reachable axes in every family (pad curvature/presentation
  mismatch; pads themselves ABSENT per A2);
  (2) OPPOSING-DIGIT CLEARANCE — the index digit (distph2) and neighbors
  cross the solid at the pinch offsets.
- THIS IS FEASIBILITY EVIDENCE OF ABSENCE AT THE REPRESENTED GEOMETRY
  UNDER THE DECLARED FAMILIES — NOT IMPOSSIBILITY. Named absences bound
  it: measured friction ABSENT, x_press ABSENT, pads/soft tissue ABSENT,
  species-true anatomy ABSENT (hybrid surfaces), C01 round-trip REQUIRED.
  Unscanned DOF directions are declared (digit-side joints; wrist; a
  continuous — non-gridded — posture space; non-perpendicular pad
  presentations beyond the 8-value tilt grid).
- P3/P4/P5 and the force stage: NOT REACHED (no survivors anywhere); no
  capacity claim is made or testable at this stop.
- Dev smokes this stop: bounded v2.1/v2.2 pipeline smokes (patched small
  grids, < 1 min total CPU, no results taken); two runner-slot refusals
  observed (one auto-slot recovery refusal, reported; slot 2 used for
  both sealed runs).
- No byte of any other lane modified; no merge/review authority claimed;
  Sergeant review requested through the Lieutenant. All results above are
  runner-verified sealed receipts; lane file copies are convenience twins.


# ERRATUM — 2026-10-03 (record correction only; sgt verdict CHANGES-REQUIRED)

Author: wk-ladder-erratum (worker under the Lieutenant; task
wk-ladder-erratum). Scope: RECORD CORRECTION ONLY. No sealed receipt byte
changed; no rerun; no candidate code edited; the lane `EVIDENCE.md` original
is preserved untouched (sha256
`21edf13ecebc890f0a74348f8954c20d30c64d3ab0f7881ddb3a01359e75d377`). This
successor file reproduces the original record verbatim above; the false
sentences remain visible, struck through and marked CORRECTED-BY-ERRATUM with
their replacements beside them. It implements the review's required changes
1-2 (`REVIEW_EVIDENCE.md` section 8, sha256
`aa1cc2c20d6283595a993538f37e736dddfab05d8cc2d49aee9fb995e5f4f789`,
hash-verified before use). Every number below was re-verified per-row from
the reviewer audit JSONs before this erratum was authored.

## E-1. The two false sentences and their replacements

(a) CS2.1, struck above: "the two-contact equalization has no root in the
bracket" — FALSE for 100% of the v2.1 no_approach class. Mechanism: the
sealed solver brackets the two-contact equalization with a uniform 41-sample
pre-scan (tau in [-0.05, 0.05], 2.5 mm spacing); at those axes g = S_A - S_B
is DEFINED only inside a ~1-2 mm window around tau ~ 0, so the pre-scan can
never observe two defined samples of opposite sign and returns None — a
solver-resolution artifact, not a proof of rootlessness. Replacement
sentence: "the declared 41-sample bracketing pre-scan (2.5 mm spacing) found
no bracket; reviewer audit A proves exactly one root exists at ALL 2,156
v2.1 no_approach axes, and at those fine-scan roots the sealed S0 screens
reject every one (1,174 S0_REJECT_TIP_DEEP + 982 S0_REJECT_CLEARANCE;
0 survivor candidates)."

(b) The PR-head commit message of `ddbd0655f25b1561700639bb48c7df0d64027069`
("...54,720 candidate placements across three sealed runs, ALL rejected by
proven geometry...") — FALSE as sealed for the 3,144
S0_REJECT_NO_APPROACH rows (2,156 v2.1 + 988 v2.2): those rows recorded
construction refusals with no proven geometric event. Commit messages are
immutable; THIS erratum commit on the PR is the vehicle that carries the
correction. The struck CS2.3 sentence above is the same claim's record twin
and carries the same replacement; the struck CS2.2 clause "every rejection
is geometric" is its v2.2 instance.

## E-2. Corrected decompositions (class order no_approach / clearance / tip_deep)

| family | as sealed | corrected | sum (must be exact) |
|---|---|---|---|
| v2.0 | 7,200 geometric | 7,200 geometric (unchanged) | 7,200 |
| v2.1 | 2,156 / 1,906 / 7,458 | 0 / 2,888 / 8,632 | 11,520 |
| v2.2 | 988 / 5,338 / 29,674 | 474 / 5,544 / 29,982 | 36,000 |

- v2.1 reclassification (audit A, all 2,156 axes): 2,156 no_approach ->
  1,174 tip_deep (distal_thumb) + 982 clearance (distph2); 0 remain
  no_approach; every axis has exactly one root. Corrected sum
  0 + 2,888 + 8,632 = 11,520 exactly.
- v2.2 reclassification (audit B, all 988 axes): 514 axes have exactly one
  root and are proven geometric at it (308 tip_deep distal_thumb + 206
  clearance distph2); 474 axes have NO root in the bracket even at fine
  resolution — GENUINE CONSTRUCTION-REFUSALS. Corrected sum
  474 + 5,544 + 29,982 = 36,000 exactly.
- Campaign totals UNCHANGED: 7,200 + 11,520 + 36,000 = 54,720 tested; ZERO
  S0-survivors anywhere — the EXHAUSTED verdict is STRENGTHENED, not
  weakened.
- Honest accounting (replaces "ALL rejected by proven geometry"): 51,576
  candidates formed and rejected by proven geometry in the sealed runs
  (7,200 v2.0 + 9,364 v2.1 + 35,012 v2.2); 2,670 more axes proven geometric
  rejections at reviewer-derived fine-scan roots (2,156 + 514; 0 survivors
  among them); 474 genuine construction-refusals;
  51,576 + 2,670 + 474 = 54,720. Geometric rejections total 54,246; genuine
  construction-refusals 474.

## E-3. Corrected summary numbers (basis labeled)

- v2.1 P2: sealed basis "tip-deep 79.6% of reachable" = 7,458/9,364
  (reachable = 11,520 - 2,156 sealed no_approach). Corrected basis (ALL
  axes; the no_approach class is empty): 8,632/11,520 = 74.9%. BOTH bases
  falsify P2 (>= 50%).
- v2.2: corrected basis (ALL candidates): tip_deep 29,982/36,000 = 83.3%
  (sealed 82.4% = 29,674/36,000); clearance 5,544/36,000 = 15.4%;
  no_approach 474/36,000 = 1.3%. V2.2-P2 stays FALSIFIED under every basis.
  Per-posture corrected bases are derivable from audit B's pid-keyed rows
  (514 reclassified axes).
- The "~66-90%" tip-fold band: P00's 91.25% (sealed reachable basis)
  exceeds the band's upper end — noted by the review, not material.

## E-4. Evidence citations (paths + sha256; hash-verified 2026-10-03)

- Review: `E:/ChimeraWork/monkey-coordination/kanban-reviews/grasp-ladder/sgt-final/REVIEW_EVIDENCE.md`
  sha256 `aa1cc2c20d6283595a993538f37e736dddfab05d8cc2d49aee9fb995e5f4f789`
  (VERDICT CHANGES-REQUIRED; section 8 = this erratum's mandate).
- AUDIT A (v2.1): `E:/ChimeraWork/monkey-coordination/kanban-reviews/grasp-ladder/sgt-final/scratch/audit_a_v21_no_approach.json`
  sha256 `1edecddb0a87355039afb9bda9bba9bf7c84f88c1750a7efddac070594a3b1f4`
  (fields: n_audited 2156; axes_with_root 2156; class_counts
  {S0_REJECT_TIP_DEEP: 1174, S0_REJECT_CLEARANCE: 982};
  survivor_candidates: 0).
- AUDIT B (v2.2): `E:/ChimeraWork/monkey-coordination/kanban-reviews/grasp-ladder/sgt-final/scratch/audit_b_v22_no_approach.json`
  sha256 `3436dc4aadcb477c02b5d26f1e7bb605e22830c2d7cf2ca2fe2ce27389f91a51`
  (fields: n_audited 988; axes_with_root 514; 474 rows with n_roots = 0;
  class_counts {S0_REJECT_TIP_DEEP: 308, S0_REJECT_CLEARANCE: 206};
  survivor_candidates: 0).
- Original lane record preserved:
  `E:/ChimeraWork/monkey-coordination/grasp-candidates/EVIDENCE.md` sha256
  `21edf13ecebc890f0a74348f8954c20d30c64d3ab0f7881ddb3a01359e75d377`.

## E-5. DURABLE LESSON (campaign law going forward)

A finite bracketing pre-scan's "no bracket found" must NEVER be summarized
as "no root exists". Solver-resolution artifacts keep the "NOT an
impossibility proof" qualifier through EVERY downstream claim — aggregate
summaries and commit messages included. A "proven geometry" claim may only
count rows carrying a recorded proven geometric event; construction-refusals
are named as such wherever the totals are restated.

— wk-ladder-erratum, 2026-10-03
