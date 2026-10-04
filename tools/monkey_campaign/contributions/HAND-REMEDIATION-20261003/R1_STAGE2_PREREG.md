# R1 STAGE-2 PREREGISTRATION (DRAFT) — the actuator-capacity stage at the FINAL survivor set, authored against the corrected reading

Status: DRAFT authored by `wk-hand-remediation` for the Lieutenant's pin
(separate-first; the committed bytes are the freeze). PRE-RUN of the
capacity class: no stage-2 result exists. The run executes on the
Lieutenant's explicit release AFTER this pin; the implementation package
seals against the pin commit and refuses on drift.
NO_WORKTREES honored; all CPU through
`python -B E:/PythonChimera/tools/monkey_campaign/task_package.py seal|run`.

## 0. The corrected reading this prereg is authored against (the erratum's law)

The published erratum (PR #335, astra `2944ea90`) re-scored P1 as
LITERALLY FROZEN partially falsified: "partially falsified as literally
frozen (534+292+128, identical at the raised cap)" — the outcome
decomposition of the q_c TIP_DEEP rows into PAD_CONTACT / PAD_ABSORBED
(u = 0) / PAD_REFUSED_DEPTH. Three laws carry forward and BIND this
prereg:

1. ABSORBED-BAND EXPLICITNESS: the u = 0 absorbed class is a REAL,
   NAMED, PREDICTED class in every stage-2 outcome space — never merged
   into a pass path.
2. BITE-ABLE TEETH AGAINST THE FULL OUTCOME SPACE: every falsifier names
   its contradicting observations across ALL outcome classes (counts must
   close over the named space; no unnamed state may occur unnamed).
3. THE DEPTH-BASIS LESSON (instrument-quantity code paths): every cited
   quantity names the exact code path that produces it (section 4).

Standing results consumed: the FINAL survivor set of 354 placements from
the raised-cap receipt (P5 314 >= 84 / P6 40 >= 14 stand; P3 stands at
0/486; P2/P4 stand as coded). Cause 2 remains unconverted (0/486 at the
full set).

## 1. INPUTS (each names its artifact and code path)

| quantity | code path / artifact | identity |
|---|---|---|
| THE SURVIVOR SET (354: 314 q_c + 40 q_zero; 348 PAD_CONTACT + 6 PAD_ABSORBED) | the raised-cap receipt's per-posture `survivors` arrays (fields: theta_index, mirror, s_star, o, u, pad_body, pad_class, pad_u, pad_force_N, anchor_envelope, bodies) | `final_run_raised_cap/stage1_pad_receipt.json` sha `4df5f48020c4dd601b7d6fc7c3047c4eb3c1e5c829bf450e07427c32c3835900`; job `e4a5447b...`; pin commit `ccb60023...` |
| pad_u per survivor | `vpl1_pad.classify_pad` -> u = d_covered_max - t (d_covered_max = `pad_scan_verts` deepest pad-covered vertex depth vs the analytic cylinder via `iv.cyl_sdf`) | the raised-cap code `4f4b6925...` |
| pad_force_N per survivor | `vpl1_pad.pad_force_column(u, mask_area_m2)` = K*(u/t)*A, K = K_eff*t/A_thumb | amendment-1 `018f0bc1...`; code `4f4b6925...` |
| mask_area_m2 | `vpl1_pad.build_pad_data` (per-facet half-space mask sum) | the raised-cap receipt's C10 column (ratio 0.9572) |
| the posture q per survivor | the sealed GP1 constants (`iv.Q_C_PRIMARY` / zero) via `gs.build_postures` | the sealed instrument constants |
| J(q), the joint set, the loaded-chain structure (6 joints per tip chain = 2 wrist + 4 chain; off-chain `structural_zero`; terminal exact-zero arms) | the actuator-map revision-2 map of record | EVIDENCE `b56f1819...`; receipt `013f3157...`; jacobian map `96a4610f...` |
| the certified caps | MP 0.8875 N*m + the W04 scene drive table | `b07-prereqs/RUNTIME_CONTRACT.md` sha `f33c188b...` |
| the law | tau_j = sum_i ((p_i - o_j) x F_i) . u_j = (J(q)^T f)_j (the GP1 CC5 law) | the map of record |
| the frozen control truths (F2/P4 constructions) | this prereg, frozen before any run | committed bytes |

## 2. THE CAPACITY OUTCOME SPACE (declared BEFORE the run; counts must close)

Every survivor is classified into EXACTLY ONE of:
- `CAP_SATISFIED` — max_j tau_j <= the certified cap of joint j.
- `CAP_EXCEEDED` — some tau_j > its cap (the binding joint recorded).
- `ARM_NONFINITE_REFUSED` — a nonfinite moment arm or force enters the
  product (C18's law: unresolved bodies cannot appear as zero arms; the
  survivor is refused, recorded, never silently zeroed).
COVERAGE ARITHMETIC: the three class counts sum to 354 exactly, both ways,
refused otherwise (`capacity_coverage_broken`).

## 3. THE FROZEN PREDICTIONS (each with teeth against the FULL outcome space)

- S2-P1 CAPACITY COVERAGE: ALL 354 survivors classify `CAP_SATISFIED` at
  the DECLARED-MODEL-FORCE magnitudes (receipt-basis max 0.22926 N; the
  pad is a contact-geometry layer, never a support element). Binding
  joints RECORDED per survivor, never gating.
  TEETH (any one falsifies S2-P1, scored over the full space): any
  `CAP_EXCEEDED`; any `ARM_NONFINITE_REFUSED`; the class counts not
  summing to 354; any survivor absent from the classification. A
  falsified S2-P1 is a RESULT (the mapping or the lever-arm assumption is
  wrong) — recorded and routed, never relaxed.
- S2-P2 THE ABSORBED BAND (the erratum's explicit-class law): EXACTLY 6
  survivors carry `pad_class = PAD_ABSORBED` (6 q_c + 0 q_zero — the
  raised-cap receipt basis) and their force columns are IDENTICALLY ZERO:
  no contact force, no tau contribution, no capacity verdict input from
  any u = 0 row. TEETH: any nonzero force or tau derived from a u = 0
  row; the 348/6 split not reproducing the receipt; an absorbed survivor
  counted in any force-bearing total.
- S2-P3 THE CHAIN-STRUCTURE BITE (F2): the P2 chain-structure check runs
  in-run and FIRES `p2_chain_structure_failed` on the constructed
  off-chain trigger (a force applied through a joint the map declares
  off-chain). TEETH: the trigger classified as a legal chain (the map's
  structure claim is vacuous -> instrument/map invalid, everything
  carries not); the check not executing.
- S2-P4 NON-VACUITY (F2-consistency): the constructed declared-press-class
  case (a 60 N-class force injected at a survivor posture through the
  recorded debt-row joint class) MUST classify `CAP_EXCEEDED` with a
  binding joint recorded. TEETH: it classifies `CAP_SATISFIED` (the cap
  comparison cannot bite -> the stage is vacuous and fails itself).
- RECORDING LAW: the x_press debt rows (e.g. tau 1.392 N*m at
  cmc_abduction vs the 0.8875 cap at the declared 60 N press) are
  RECORDED per posture, never decisive, never dropped.

## 4. THE QUANTITY CODE-PATH TABLE (gate (c); every cited quantity names its producer)

Every emitted stage-2 number carries `code_path`: the function/field above
that produced it. In particular: any depth-like quantity is NAMED as
either `d_receipt` (the sealed scan's first-proven depth; identity-witness
only) or `d_covered_max` (the full-scan admission depth) — the two are
never conflated (the depth-basis lesson); u and force name their chain
(`classify_pad` -> `pad_force_column`); tau names its chain
(`J^T f` at the map's conventions vs the RUNTIME_CONTRACT constants).

## 5. WHAT STAGE 2 DOES NOT CLAIM (the honest scope, restated)

A CAP_SATISFIED verdict at the pad's <= 0.23 N forces is a
ladder-consistency result, NOT a grasp-capacity qualification: the
support forces of a real grasp route through the press channel, which is
ABSENT (TC-8 = 0/8, x_press ABSENT, DERIVATION gap 6; the same-hands
finding stands). No stage-2 output may be phrased as "the hand can hold".
Stages 3-5 own contact forces (mu placeholders stay labeled), supported
grasp (G01 law re-armed per reading), and runtime evidence (parity gates
re-bound; walking certification not inherited).

## 6. EXECUTION

Gate: the Lieutenant pins THIS file (separate-first), then releases; the
package seals against the pin commit; run class `stage2_capacity` with a
receipt-level delta note naming its delta vs the raised-cap class (new
stage, new outcome space, survivor-set input). Slot discipline: slot 2
first, fallback slot 3; the slot-2 lock_busy preservation note stands
(two FAILED rows kept; another lane's replay job shares the slot; nothing
deleted). Receipt conventions: hash-citing fields name their artifacts;
per-posture blocks keyed; delta note present. Anti-tuning: every constant
above is frozen pre-run; post-run change requests are FINDINGS, never
edits. No merge/review authority claimed; Sergeant review requested
through the Lieutenant; author self-review certifies nothing.
