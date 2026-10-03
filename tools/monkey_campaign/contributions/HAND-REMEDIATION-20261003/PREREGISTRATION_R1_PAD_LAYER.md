# PREREGISTRATION (DRAFT) — R1: the declared-synthetic volar-pad contact-model class VPL-1

Status: DRAFT authored by `wk-hand-remediation` for the Lieutenant. Per the
publication law this file is committed ALONE FIRST (separate-first) BY THE
LIEUTENANT; the committed bytes are the freeze and every emitted receipt must
embed `preregistration_sha256` of exactly those bytes and refuse any mismatch.
No implementation file, harness run, sealed package, measurement or capture
frame of this card exists at draft time. Write scope of the draft: the NEW
lane dir `E:/ChimeraWork/monkey-coordination/hand-remediation/` (NO_WORKTREES
law honored; no worktree, no clone; all CPU verification through
`python -B E:/PythonChimera/tools/monkey_campaign/task_package.py seal|run`).

- Execution gate (declared BEFORE anything runs): R1 stage 1 executes ONLY if
  the Lieutenant/Captain release it after the digit-side bounded scan
  (wk-digit-scan lane) is on record. The scan is the standing evidence gate;
  this lane does not duplicate it. If the scan yields a lawful placement at
  the CURRENT geometry, R1's collision-geometry stage has no work and this
  prereg closes as NOT-NEEDED (a supported prediction, never a failure).
- Design law: `R1_PAD_LAYER_DESIGN.md` in this lane (same DRAFT discipline;
  its sha256 is pinned below; in any conflict THIS file's frozen constants
  govern).

## 0. Standing laws consumed

- The objective-line law: a completed specification is not a trained skill;
  demonstrated impossibility cannot close the playable-monkey goal; no
  measured value is ever tuned to force success.
- The wording law (Captain correction #3): a predicted refusal that is
  observed is a SUPPORTED PREDICTION; each falsifier NAMES the observation
  that would CONTRADICT its prediction; a refusal is never misread as a
  grasp, contact, hold, ascent or descent result.
- The anti-tuning law EXTENDED TO SYNTHETIC PARAMETERS: every VPL-1 parameter
  below is declared a priori from the sealed receipts' measured fold-depth
  distribution and from stated structural/anatomical rules, hash-pinned in
  THIS commit, and NEVER adjusted after any R1 result is seen. A post-result
  proposal to change any value is a FINDING routed to the Lieutenant, never
  an edit.
- The instrument anti-tuning law: tau = 1.0e-4 m, pi_c = 1.0e-3 m,
  r_joint = 5.0e-3 m remain frozen; no tolerance is enlarged; no pair is
  removed; no collision check is weakened. The pad admission window is a
  MODEL of a declared compliant layer, NOT a loosened tolerance: the
  bone-vs-solid checks are unchanged and remain hard failures.

## 1. Frozen parameters (VPL-1-GEOM and VPL-1-FORCE, declared now)

| id | parameter | frozen value |
|---|---|---|
| G-1 | covered bodies | distal_thumb, distph2, distph3, distph4, distph5 |
| G-2 | layer thickness t | 2.0e-3 m |
| G-3 | max admitted indentation u_max | 2.0e-3 m (= t, full-compression structural bound) |
| G-4 | admission window | rigid-proven tip fold depth d in (pi_c, t + u_max] = (1.0e-3, 4.0e-3] m |
| G-5 | patch rule | pad-covered vertex set of body B = {v : n_v . a_B > 0}; n_v = area-weighted vertex normal with incident triangles sorted lexicographically before summation; a_B = normalize(u_flex x e_extent), sign declared per body from the A05 joint-axis table in the implementation package (the sign is verified by control C6 before any candidate runs) |
| G-6 | evaluation law | post-hoc reclassification at the UNCHANGED rigid solution; the placement family, offset solve s*, and every bone-level class stay byte-identical to the sealed screens |
| F-1 | contact law | Winkler linear foundation, p = k * (u / t), valid to u_max (strain <= 1.0 by admission) |
| F-2 | areal stiffness k | 1.5e5 Pa — DECLARED-SYNTHETIC PLACEHOLDER, human-fingertip-pulp order (human-analogue placeholder class, like the 0.41 analogue); the macaque pad stiffness is UNMEASURED (acquisition-gap class) |
| F-3 | force column | F = p * A per pad contact, A = recorded patch area estimate; labeled DECLARED-MODEL-FORCE; consumed only by the capacity stage as load; never an actuator, solver input, or action channel |

Sizing basis (receipt-verified, sealed v2.0 receipt
`065328e4942a0bb8794138a96966aa8a3267fcd15ce084b9fb0490dff76b19ec`, per-axis
rows): distal_thumb TIP_DEEP at q_c_PRIMARY n = 954, min 1.000e-3, median
1.988e-3, p90 3.573e-3, max 3.673e-3 m, all inside (1.0e-3, 4.0e-3] m. The
window edge t + u_max = 4.0e-3 m covers that measured band with 8.2% headroom
and REFUSES the deep classes by construction (v2.1 q_c med 5.256e-3 /
max 35.442e-3; v2.2 med 6.851e-3 / max 36.813e-3; distph2 q_c median
9.336e-3, max 13.360e-3). t = 2.0e-3 m is proportionate to the covered
phalanges (thinnest covered thickness 2.55e-3 m). No pad parameter is chosen
to make any future stage pass.

## 2. The instrument entry (declared)

Two-level entry per the design document section 3: Level 1 bones unchanged +
one pad screening bound per covered body (bone sphere radius + t, proxy only);
Level 2 split into the UNCHANGED bone layer (all classes and the exclusions
ledger byte-identical) and the NEW pad layer with classes `PAD_CONTACT(u)`,
`PAD_REFUSED_DEPTH`, `PAD_REFUSED_PATCH`. The extended control battery
C1-C9 (C6 pad-indent, C7 over-compression refusal, C8 anti-masking, C9
pad-free) runs FIRST; the in-situ light gate re-runs the extended frozen
control table every run; the determinism slice extends to pad rows; the
stage-1 run gates identity against the sealed v2.0 q_c receipt rows
(`SEALED_ROW_DRIFT` on any mismatch). The named empty gate field
`pad_gate_failed` present in the sealed v2.1/v2.2 receipts is NOT inherited
or reinterpreted.

## 3. Honest scope (model law, repeated from the design)

VPL-1 addresses the Captain's cause 1 (tip fold) ONLY, inside the declared
window. Cause 2 (opposing-bone clearance; distph2 q_c median 9.336e-3 m,
442/486 events beyond 4.0e-3 m) is NOT fixed by a 1-2 mm layer and MUST NOT
be absorbed by growing the window — window growth toward the 9-18 mm class is
tune-to-success and forbidden. Cause 2 proceeds exclusively through the
in-flight digit-side scan (the standing evidence gate); if the scan zeroes
out, the next rung is the declared follow-on placement family, not pad
thickening.

## 4. Frozen predictions (each names its contradicting observation)

- P1 WINDOW CONVERSION: under the unchanged v2.0 perpendicular family at
  q_c_PRIMARY, every `S0_REJECT_TIP_DEEP` row with d in (1.0e-3, 4.0e-3] m
  whose deepest vertex lies in the declared pad patch reclassifies to
  `PAD_CONTACT` with recorded u = d - t in (0, 2.0e-3] m; the receipt basis
  is 954/954 rows inside the window. CONTRADICTION: any such row remaining
  `TIP_DEEP`, any `PAD_CONTACT` with u > u_max, or any conversion lacking a
  patch witness -> P1 falsified (instrument or patch-rule defect; the run is
  invalid).
- P2 DEEP-CLASS REFUSAL: zero rows of ANY body with d > 4.0e-3 m reclassify
  (the v2.1/v2.2 deep fold tails and every distph2 deep row stay refused).
  CONTRADICTION: any `PAD_CONTACT` derived from d > 4.0e-3 m.
- P3 TWO-CAUSE SURVIVAL: at q_c_PRIMARY the opposing-bone class remains the
  binding cause-2 evidence: at least 442 of the 486 distph2 rows stay refused
  (only the <= 9.05% shallow tail is even eligible, and only under the patch
  condition). CONTRADICTION: the distph2 class clearing entirely — which
  would falsify the phase-1 two-cause analysis itself and route back to the
  Lieutenant before anything else runs.
- P4 BATTERY IDENTITY (negative-control law): per-posture conversion counts
  equal exactly the window-and-patch row counts derived from the sealed
  receipts; C8 classifies `GENUINE_PENETRATION`; C9 shows zero pad rows; the
  q_zero CONTROL keeps its role (no vacuous pass). CONTRADICTION: any count
  mismatch or any battery misclassification -> instrument invalid, nothing
  carries.

## 5. The requalification ladder with RUN-TIME falsifiers

Concealed-falsification law: each falsifier is an executable check inside its
stage's sealed run and each MUST fire on its constructed trigger in the same
run (a falsifier path that never executes or cannot bite is concealed
falsification and fails its own stage). Order is the Captain's declared gate
order; no stage starts before its predecessor's sealed receipt exists.

1. COLLISION GEOMETRY: extended battery + light gate + determinism slice +
   sealed-row identity + P1-P4 checked per row in-run. Falsifier F1: the C8
   anti-masking trigger (pad engaged AND a non-covered-body bone vertex
   inside the solid) must classify `GENUINE_PENETRATION` in-run; any other
   class = `instrument_invalid_pad_masks_bone`, all results of the run
   carry not.
2. ACTUATOR CAPACITY: tau_j = (J^T f)_j from the DECLARED-MODEL-FORCE columns
   against the certified caps. Falsifier F2: the chain-structure check must
   fire `p2_chain_structure_failed` on a constructed off-chain trigger
   in-run; a capacity refusal (tau > cap, e.g. the recorded x_press debt row
   tau 1.392 N*m at cmc_abduction vs the 0.8875 N*m cap) is a SUPPORTED
   PREDICTION recorded, never relaxed, never dropped.
3. CONTACT FORCES: VPL-1-FORCE activates (parameters already frozen).
   Falsifier F3: the pad force identity (sum p*dA == recorded contact
   impulse within the declared tolerance, every audited tick) AND the mu = 0
   non-closing control (G04 FB2 / G06 mu=0 class) must fail to hold on its
   constructed trigger in-run. Friction stays placeholder-labeled; the 36 N
   figure stays a simulated capacity conditional on model + mu = 0.6.
4. SUPPORTED GRASP: the G01 transfer law re-armed per mass reading.
   Falsifier F4: the stage must exhibit at least one CLOSING and one FAILING
   corridor on its constructed controls; a stage where nothing can fail is
   vacuous and fails itself. The same-hands refusal (0.049 kg hand vs the
   10.038 kg line) is a SUPPORTED PREDICTION under the declared reading,
   routed to the TC-3/TC-8 debt line, never a silent pass.
5. RUNTIME EVIDENCE: sealed capture binds pad class states to the numeric
   receipt at every audited tick; missing or contradicting state-revealing
   content fails the stage. CPU/GPU parity and runtime identity gates are
   RE-BOUND to the changed contact dynamics; walking certification is not
   inherited (G08 law).

## 6. Named-unscanned list (updated per the Lieutenant's ruling)

- digit-side joints — owned by the in-flight bounded scan (wk-digit-scan);
  this lane does not duplicate it.
- the wrap-presentation placement family — a follow-on family ONLY if the
  bounded scan zeroes out; never a re-tune of any declared family.
- a continuous, non-gridded posture space.
- non-perpendicular pad presentations beyond the declared tilt grid.
Nothing in this prereg claims these directions are impossible; the phase-1
negative result remains feasibility-of-absence AT THE REPRESENTED GEOMETRY
UNDER THE DECLARED FAMILIES across all 54,720 TESTED placements, never a
universal impossibility claim.

## 7. What does not change

The 19 vendor STLs and pins; all joint limits; the trunk (74 mm / 1.158 m);
the declared placement families; tau, pi_c, r_joint; the bone-level classes
and the exclusions ledger; the merged instrument's C1-C5 (extended, never
replaced); TC-8 = 0/8 (x_press ABSENT); the C17 port debt (the pad is NOT an
attachment port and implies no lambda_min; G02 stays gated on real port
inputs; the B05 blocked-port rows stand); the K01 master conditionality
(training stays gated on the whole grasp chain).

## 8. Governance

The Lieutenant commits THIS file alone first; the implementation package
(a future seal of this lane) pins the published prereg commit and refuses on
drift. All CPU execution through the canonical runner with `--keep`-declared
outputs; every load-bearing artifact's sha256 lands in the lane EVIDENCE.md.
This lane claims no merge/review authority and requests Sergeant review
through the Lieutenant; author self-review certifies nothing.
