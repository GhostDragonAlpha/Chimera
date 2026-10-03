# EVIDENCE — hand-remediation lane (wk-hand-remediation, chain stop 1, phase 1)

Task: the Captain's order #2-3 via the Lieutenant. PHASE 1 ONLY: the anatomy
inventory + the two-cause analysis + the ranked correction proposal. NO geometry
changes, NO joints touched, NO gated run, NO seal/run of this lane (phase 1 is
an inventory/design deliverable; every number below is cited from already-sealed
records or labeled lane-dev arithmetic). NO_WORKTREES honored: no worktree, no
clone; no CPU experiment executed by this lane. Write scope: this lane directory
only; no other lane's bytes touched; the E:/PythonChimera dirty checkout and
other agents' work preserved. Date: campaign 2026-10-02 (host clock 2026-10-03
at write). Acceptance = sealed receipts, never prose.

## 0. Scope law for this phase

- Preservation statement (binding on every later phase of this lane): the trunk
  scenario is FROZEN (74 mm diameter / 1.158 m declared branch-scale cylinder,
  `trunk_01.lateral`); the declared placement families and tolerances
  (tau = 1.0e-4 m, pi_c = 1.0e-3 m, r_joint = 5.0e-3 m, offset bracket [0, 0.15] m)
  are FROZEN under the instrument anti-tuning law; joint limits are FROZEN
  (human digit ranges verbatim + macaque wrist ranges verbatim per A05
  deviations 6-7); no collision check is weakened (19 certified joint-region
  exemptions only); no measured property is tuned (osim masses/ranges/anchors,
  Cheng/Isler/Young/lit-hands measurements untouched). The qualification gate
  order as the Captain declared: collision geometry -> actuator capacity ->
  contact forces -> supported grasp -> runtime evidence.
- The GP1 negative result and all three ladder receipts are PRESERVED
  byte-for-byte; this lane is a consumer, never a rewriter.

## 1. Consumed sealed records (all sha256 computed by this lane at read time)

### The exhausted ladder (the negative result and its receipts)

| artifact | sha256 |
|---|---|
| tools/monkey_campaign/NO_WORKTREES.md | `7d3fe1029f727b95ff2c832b06a89b3bac40f59e14993440255636218645f433` |
| grasp-candidates/EVIDENCE.md (the 54,720-placement record, chain stops 1-2) | `21edf13ecebc890f0a74348f8954c20d30c64d3ab0f7881ddb3a01359e75d377` |
| grasp-candidates/CANDIDATE_FORMULATION.md (frozen v2.0 screen law, T1/T2/T3 taxonomy) | `0c24657de95068eb7499c3b9f140b8467f58e5ba6bcc94d02c69207341dbd1b1` |
| grasp-candidates/PREREGISTRATION_GRASP_CANDIDATES.md (committed prereg bytes; Lieutenant commit `655047b466f5d959e065252670bd275153a4d775`) | `e5bfa3cd32d26785bdcd7441f6af720fdc4a561938ff1c8de3f21dd7a6545106` |
| grasp-candidates/V2_2_ADDENDUM.md (frozen before the v2.2 run) | `cf7da1a8cc75f522acaa958045ce1977e12f37187211db6980c48f4f1a7c90f4` |
| grasp-candidates/final_run/grasp_screen_receipt.json (v2.0, 7,200 candidates) | `065328e4942a0bb8794138a96966aa8a3267fcd15ce084b9fb0490dff76b19ec` |
| grasp-candidates/final_run/grasp_screen_report.txt | `eeea10e9247fe97c2e305d686b71c96f2e5cb390de7466a61823157aadca4266` |
| grasp-candidates/final_run/runner_receipt.json (job `7b8e4127ca5c46a69bc1a8b3a18f2abc` PASSED, cleanup_verified) | `e6fbc96c100013a83d9565553da7defea7f01a837d2795e3065a1790a27f4911` |
| grasp-candidates/final_run_v21/grasp_screen_v21_receipt.json (v2.1, 11,520 axes) | `b9c5892326c69392579ca4a3dcd6454eec9f3a7cfa56343e8eefaf8ef8c47b84` |
| grasp-candidates/final_run_v21/grasp_screen_v21_report.txt | `dd8570acc1451c311142915f931bcea539cacadf28fb104a06c43ed270c68e82` |
| grasp-candidates/final_run_v21/runner_receipt.json (job `f0da9bb122bb411f9acef57b650f674c` PASSED, slot 2) | `5c373edf41a134790c0f8952d1e9b30b7c1c5d357ab8932fffe7b2ed45adf08c` |
| grasp-candidates/final_run_v22/grasp_screen_v22_receipt.json (v2.2, 36,000 candidates, EXHAUSTED) | `43f395e2d98935fb916a699f52b94d1775a27ced303ce01438167a26b298542b` |
| grasp-candidates/final_run_v22/grasp_screen_v22_report.txt | `121243a672a7510a48a382a0ccc58eb57d95dd1c3023c3a92ff567a68fe33fb3` |
| grasp-candidates/final_run_v22/runner_receipt.json (job `a784c5f7d062445b922eeb6fccd7425b` PASSED, slot 2) | `3359a0fcc8136bcf3d809678a73e7a231e36d7ffc5dbb316c65ad95556c58d5c` |

### The corrected instrument and the anatomy it pins

| artifact | sha256 |
|---|---|
| instrument-v2/INSTRUMENT_V2_DECLARATION.md (two-level law, exclusions ledger, tolerances, provenance 3.1-3.3) | `71e31cdd4122e20bfefdf343df28b0e01fc2a51e70cba11296924ca97ce991ea` |
| instrument-v2/PREREGISTRATION_INSTRUMENT_V2.md | `897ca164ac5a63437c465783af2dd8f9c743d6c587d5423f4d3cec1b7190bdaf` |
| instrument-v2/mesh_input_table.json (19 STL pins, scale, AABBs, spheres, faceting) | `6e5f3bac345a278eaa994203d48df71fa3a4d5d3f6d9be3e9c59f3b08491cfb2` |
| instrument-v2/EVIDENCE.md | `8174415cacd41fe270b2dfbd1cd210cc0a1af26be837e55e2a82e307fbae91c7` |
| evidence-store/MAT2-A05/workspace_evidence/93599fbb26d7_mutation_manifest.md (the A05 hybrid anatomy record) | `93599fbb26d712d5b386bd92022de985cf75d21a21ac29cef62d08d3a0724103` |
| evidence-store/MAT2-A05/workspace_evidence/eb5c3ebeee7b_mutation_manifest.json | `eb5c3ebeee7bf13f1ca2966eb8353cb597f3d24242ab99c59225b56417876a44` |
| evidence-store/MAT2-A05/workspace_evidence/48b037593f63_mutation_structure.json | `48b037593f63ec473947d787077ab6fbcd3b364afd15765bff508e7d54f45649` |
| evidence-store/MAT2-A05/workspace_evidence/9c91124600ab_macaque_hand_mutation.xml | `9c91124600abc67a4a33d78ce79ab1a0604a48b5a9a2e6377d15de05717e5adf` |
| evidence-store/MAT2-A05/workspace_evidence/1781aa6bfe70_validation_receipt.json (37/37 at manifest time) | `1781aa6bfe7069183c225d54be21f8788c460b24b9abeca1aaac25ff0fa6c3ff` |
| E:/PythonChimera/tools/science_funnel/data/macaque_arm/Geometry/hand.vtp (anchor envelope; re-hashed from current source, == A05 pin) | `a06ea7e079c849df07d6eec001e9bcc2ea193ecd3914011c78a993a5faa94fc6` |
| E:/PythonChimera/tools/science_funnel/data/macaque_arm/monkeyArm_current.osim (re-hashed from current source, == A05/A06 pin) | `4148aee2c8dda1dcb0918496ad7c5e1adcf4ebabde0a68a3e0dc67faec67b895` |
| THE 19 VENDOR STLs `E:/PythonChimera/vendor/myo_sim/meshes/*.stl` | RE-VERIFIED 19/19 by this lane against the `mesh_input_table.json` `stl_sha256` pins from the current vendor tree (per-asset hashes live in the table, sha above; no copy made) |

### The contracts binding the hand

| artifact | sha256 |
|---|---|
| k-spec/PREREGISTRATION_K01_SKILL_SPEC.md (DRAFT; action space section 2, master conditionality section 0.4 = the G04 contact line) | `fdc2e79aea9479fd4d6f9d761694ba1edbe6430b1bf1ee9df6fed64ca9ac0935` |
| climb-derivation/DERIVATION.md (hold law, x_aperture/x_press/x_inertia debts, assumptions A1-A7, section 8 scope labels) | `da34420558f6632b0544ca94bc3e25ece515027628c7bd8cc54b9fdd30b7ebd9` |
| actuator-map/EVIDENCE.md (revision-2 map of record) | `b56f181923fc85621ae112b536ea8b4bfc66926e993920b4e0abd24682eab189` |
| actuator-map/final_run/actuator_map_receipt.json | `013f3157c3455dc66c736fee465f8ac2341bc72ebbb8ca6bafdb7f545c2e9175` |
| actuator-map/final_run/jacobian_map.json | `96a4610ffb37e6729763cb13455b7d6b6b3d582a3ab35dc4975a3b67f64f31b3` |
| b07-prereqs/RUNTIME_CONTRACT.md (certified drive caps) | `f33c188bcb561b1946b104340cf36cba366709526c095874684529a599df338c` |
| b07-prereqs/rown04-fitting/inputs/a07_placement_resolution.json (A07 port/mechanics law: `inputs_unavailable_in_pinned_sources`, no synthetic lambda_min) | `cd596d7c21fa81a4c2632e13b63ba26e62da51d44eca2355147fd5dff1587490` |
| g04_evidence_receipt.json (G04 done_when_verified; grip contact line artifacts) | `eadab670c7839a0e31f07d8739eceddcf7991206c82eaf277866a53fb8f80b28` |
| g04-friction/FRICTION_SOURCES.md | `336118e929bd0b4fb067db5a448dc2e348fed073007787635549a4cf1cf5868b` |
| MONKEY_COMPLETION_MAP.md rows A06/A07/A09/G02/G03/G04/C05/C17/B05/TC-8 (read at `E:/PythonChimera/tools/monkey_campaign/MONKEY_COMPLETION_MAP.md`; not copied) | read-only citation; row text quoted in the phase-1 report |

### Measured species sources available to a correction (the measured-vs-synthetic ledger)

| artifact | sha256 |
|---|---|
| research-data/20260929/cheng_tables/M2-3_mulatta_morphometry.csv (21 muscles, n=6 M. mulatta) | `16ca8bcd9be48b3766125801eb05a8f4f10b446b4caed76d9fddeb2e45df71fa` |
| research-data/20260929/cheng_tables/M2-5_fascicularis_morphometry.csv | `9469449f8735df84a163d364a67402d127ca8ac54a402595ce4cebb6d16cf148` |
| research-data/20260929/cheng_tables/M2-6_mulatta_inertials.csv (segment bands incl. hand) | `1948a2d8399b5253461c6ed70eed87ea38c5df4083b75437e1e3dbd1a4ce93f3` |
| research-data/20260929/cheng_tables/M2-7_fascicularis_inertials.csv | `d1d601feaf61b033bdbccf8509be946d0e1884fec62388c8630287703fc63133` |
| research-data/20260929/atlas/MUSCLE_ATLAS.md (screening verdict vs the sealed claim set) | `e51c8bb211ec15ea9fbe84cfb6c8f5dae421d276b48f39b4703936d6c88d1a16` |
| research-data/20260929/lit-hands/HANDS_RETRIEVAL.md (macaque intrinsic-hand PCSA lane; supplements S1/S2 NOT acquired) | `b15744391d7a1799306e5cc985f65b52422520577e5db08311f89356056cda65` |
| research-data/20260929/lit-hands/extracted/intrinsic_hand_quantitative.csv | `4b0cc98dd1a62ca9afd9d214587a553273ae8ba7e9a58242d2b5dbf73d507aad` |
| research-data/20260929/benchmark-grasp/GRASP_BENCHMARK.md (measured primate grasp forces, other species) | `d936cebe38b1416dfc417db727ea81396eb8eb9217efed3f05b344db17f71610` |
| b07-prereqs/rown05-stiffness/MEASURED_SOURCES.md | `c181a0b5cdf01cb377abe32e0c18abec278ebd52b43c8d0a5d0a4c631efb7574` |
| Isler 2006 forelimb inertials incl. M. fascicularis Table 10 | held under `E:/ChimeraWork/research-data/20260929/lit-inertia-bmd/` (cited via the inertia-compare lane records; not re-pinned by this phase) |

MEASURED-MACAQUE-PHALANX-DIMENSION ABSENCE (the load-bearing negative for
candidate ranking): NO sealed record contains measured macaque per-phalanx,
per-digit-section, fingertip-pad or tip-bone dimensions. A05 deviation 2 states
it for proportions ("no macaque per-phalanx proportions exist in-repo,
PR #229/#230 search evidence"); deviation 6 records "no skin geometry"; the
instrument declaration 3.2(iv) records pads/soft tissue ABSENT; this lane's
sweep of `research-data/20260929/` (Cheng = muscles + SEGMENT inertials only;
Isler = per-SEGMENT CoM/rg only; vanhoof2021 = species-level PCSA percents only;
hand.vtp = whole-hand 1920-point envelope, mesh ancestry unconfirmed) found none.
Any tip/section geometry correction is therefore EXPLICITLY DECLARED SYNTHETIC
until a measured acquisition lands.

## 2. Lane-dev arithmetic performed this phase (no result-bearing claims)

- Re-hash verification of the 19 STL pins, hand.vtp, osim and every table row
  above (all MATCH; mismatches would have been reported, none seen).
- Re-read of the three sealed receipts to extract per-posture/per-bone
  rejection counts (values in the phase-1 report; identical to the lane
  EVIDENCE.md summary rows where they overlap).
- Declared-constant arithmetic on the frozen R = 0.037 m: chord-sagitta margins
  L^2/(8R) (L = 40 mm -> 5.4 mm; L = 74 mm -> 18.5 mm) and a 6 mm-wide patch
  conformity dip w^2/(2R) ~ 0.12 mm — used ONLY to interpret the published
  rejection depths, never as a new verdict.
- No seal, no run, no slot use, no output artifacts beyond this EVIDENCE.md.

## 3. Handoff

Phase 1 report (inventory, two-cause analysis, ranked proposal, preservation
statement, negative-result scope) is returned by wk-hand-remediation to the
Lieutenant as the chain-stop-1 deliverable. Phase 2 (any geometry change) is
GATED on Lieutenant/Captain approval of a candidate AND its own prereg-first
cycle: the committed prereg pins the exact mesh revisions / declared-synthetic
parameters BEFORE the requalification chain (collision geometry -> actuator
capacity -> contact forces -> supported grasp -> runtime evidence) executes
through sealed packages. No merge/review authority claimed by this lane;
Sergeant review requested through the Lieutenant; author self-review certifies
nothing.

EVIDENCE.md (this file) self-referential; hash to be recorded by the
Lieutenant at handoff.

---

# PHASE 2 — R1 authoring (design + prereg DRAFT; no runs, no geometry changes, nothing sealed)

Lieutenant ruling on phase 1: ADOPTED with dispositions — R0 = the
wk-digit-scan lane ALREADY IN FLIGHT (the standing evidence gate; do not
duplicate); R3 (bone thinning) REJECTED as recommended (tune-to-success); R4
stays ruled out; R2 held (no measured species tip data exists; not the
smallest correction). R1 (declared-synthetic volar pad layer) adopted for
AUTHORING: design + prereg DRAFT only.

## 4. Phase-2 artifacts (this lane; sha256 computed at write)

| artifact | sha256 |
|---|---|
| R1_PAD_LAYER_DESIGN.md (the VPL-1 model-class design: sizing basis, instrument entry, TC-8, C17, scope, ladder) | `297b8628e061a3d33294e3fde98c69bf5500eb04bfff2854ec28a7d24b9fb063` |
| PREREGISTRATION_R1_PAD_LAYER.md (DRAFT prereg: frozen parameters G-1..G-6/F-1..F-3, predictions P1-P4, run-time falsifiers F1-F5, named-unscanned list) | `9213bf7d91ed9a6e6b2c5bbddc05d5ee36db63c600dfce42b559632f6f565da9` |

## 5. Receipt-derived sizing statistics (lane-dev arithmetic on the SEALED v2.0/v2.1/v2.2 receipts; no new run)

Re-read from the per-axis reject rows of the three sealed receipts (hashes in
section 1; files unmodified):

- TIP FOLD distal_thumb q_c_PRIMARY (v2.0): n=954, min 1.000e-3, median
  1.988e-3, p90 3.573e-3, max 3.673e-3 m; ALL 954 events inside
  (1.0e-3, 4.0e-3] m (0.5 mm bands: 362/116/106/104/138/128).
- TIP FOLD v2.1 q_c (tilt family): n=7,326, med 5.256e-3, max 35.442e-3 m;
  declared tip distph3 n=132, med 5.048e-3, max 13.930e-3 m.
- TIP FOLD v2.2 (25 postures, coarse grid): n=28,066, med 6.851e-3,
  max 36.813e-3 m; distph3 n=1,608, med 2.771e-3, max 17.535e-3 m.
- OPPOSING distph2 q_c_PRIMARY (v2.0): n=486, min 1.048e-3, median 9.336e-3,
  max 13.360e-3 m; only 44/486 inside (1.0e-3, 4.0e-3] mm; 442/486 beyond.
- OPPOSING v2.1: n=1,894, med 12.876e-3, max 34.674e-3 m; v2.2: n=4,926,
  med 17.716e-3, max 35.965e-3 m.
- Chain-detail observation recorded honestly: the sealed v2.1/v2.2 receipts
  carry a named empty gate field `pad_gate_failed: []` (green in all runs);
  VPL-1 does not inherit or reinterpret it.
- Declared-constant arithmetic used for sizing: window edge = t + u_max =
  4.0e-3 m covers the measured q_c fold band [1.000, 3.673] mm with 8.2%
  headroom; u_max = t (full-compression structural bound).

These statistics are INPUTS to the frozen declarations (anti-tuning law:
declared BEFORE any R1 result exists; never adjusted after results).

---

# PHASE 3 — prereg PINNED; standby readiness plan (no runs, no code shipped)

- Prereg PINNED by the Lieutenant: commit `4def67e400953e8c4b833ce04345f75426a6180d`
  on `origin/review/HAND-REMEDIATION-20261003` (parent = astra tip
  `5b098a37`), path
  `tools/monkey_campaign/contributions/HAND-REMEDIATION-20261003/PREREGISTRATION_R1_PAD_LAYER.md`,
  committed-blob sha256 `9213bf7d91ed9a6e6b2c5bbddc05d5ee36db63c600dfce42b559632f6f565da9`
  (BYTE LAW VERIFIED by the Lieutenant: == this lane's draft bytes).
  Execution gate unchanged: stage 1 runs ONLY on explicit Lieutenant release
  AFTER the digit-scan result is on record.
- Reused sealed code identities (verified at read): merged instrument
  `instrument_v2.py` sha `9514c5b15a27948c65563070f16dffee4a5a28347c281a5d7e255fe93e516ddd`;
  v2.0 screen `grasp_screen.py` sha
  `6b924e87151f5e2235b9d9c023be85d0f7602d42020b37df4ba7bf58c0e9e0ea`
  (both read from
  `E:/ChimeraWork/monkey-coordination/grasp-candidates/package/files/tools/monkey_campaign/contributions/GRASP-CANDIDATES-20261002/`).

## 6. Phase-3 artifact (this lane)

| artifact | sha256 |
|---|---|
| R1_IMPLEMENTATION_READINESS.md (code-change plan: vpl1_pad.py + run_stage1_pad.py function specs, C6-C9 constructions, sealed-row identity gate comparison set, stage-1 package spec + envelope, P1-P4 skeletons with F1-F5 triggers, Reading Note N-1, release checklist) | `f73d69a8de6cb83d15b412acc127ec925c8e81b1f9cc19689118a7ab8f87ea09` |

---

# PHASE 4 — R1 AMENDMENT-1 (pre-run measured-source upgrade; DRAFT for the Lieutenant's pin; no runs, no code shipped)

## 7. Source verification (STEP 0, performed by this lane — PASS)

PMC4403516 (Kumar, Liu, Schloerb & Srinivasan 2015, ASME J Biomech Eng
137(6):061002, DOI 10.1115/1.4029985) fetched and independently verified
2026-10-03 against the collaborator citation; all five load-bearing numbers
confirmed with quoted sentences (9.5 kg male rhesus macaque, n=1; five pads /
86 curves incl. the 19x4+10 breakdown; "mean stiffness of 0.120 mN/um" on
the A0-vs-depth linear fit = 120.0 N/m; t1 = 2.279±0.233 s, t2 = 0.149±0.022 s;
static indentations 200/400/600/800 um; ADINA multilayer viscoelastic FE).
Nomenclature nuance recorded: the text says "rhesus macaque" without the
binomial; Macaca mulatta is the standard binomial and matches the hybrid's
constraint lineage. Per-pad breakdowns and the Prony modulus fractions are
NAMED absences (transcribable later under the cheng_tables discipline).

## 8. Amendment-1 frozen numbers (all lane-dev arithmetic on declared constants)

| quantity | value |
|---|---|
| declared patch areas A_pad = A_total/2 (vendor STLs at s; scaled A_total) | distal_thumb 5.160493e-5 m^2 (1.032099e-4); distph2 3.290597e-5 (6.581194e-5); distph3 3.845808e-5 (7.691615e-5); distph4 3.549538e-5 (7.099076e-5); distph5 3.522939e-5 (7.045877e-5) |
| k (F-2 replacement) | `K_eff * t / A_thumb` = 120.0 * 2.0e-3 / 5.160493e-5 = `4650.718448799368 Pa` (prior 1.5e5 Pa was ~32.25x stiffer; DOWNWARD, pre-run) |
| per-pad max force at window edge | K_eff * t = 0.24 N (thumb); digits k*A_body = 0.153-0.178 N — the measured-stiffness pad is NOT a support element at the declared 60 N/channel operating point (TC-8 stays 0/8) |
| digit implied spring rates k*A_body/t | 76.5 / 89.3 / 82.5 / 82.0 N/m (0.64-0.76x of the 120 N/m mean; per-body k_body DECLINED, recorded) |
| envelope split at q_c | measured-anchored u <= 0.8 mm: 646 of 954 TIP_DEEP rows; declared-extrapolated (0.8, 1.673] mm: 308 rows |
| timescales | DT = 0.3/60 = 5.0e-3 s; t2 = 29.8 ticks, t1 = 455.8 ticks; viscoelasticity NAMED-NOT-MODELED (instantaneous bound = stiffer, untranscribed Prony split named) |
| C10 control | F = K_eff*u = 0.024/0.048/0.072/0.096 N at 200/400/600/800 um; light gate extends to C1-C10 |

## 9. Phase-4 artifact

| artifact | sha256 |
|---|---|
| R1_AMENDMENT_1.md (verification record; the k upgrade with explicit conversion; envelope scoping; viscoelastic named-not-modeled; C10; anti-tuning statement; readiness delta) — DRAFT for the Lieutenant's pin, LAWFUL ONLY PRE-RUN | `018f0bc120c0fa44cdcc1f611ab883764eb91e2d668975573f792218b93f94ac` |

---

# PHASE 5 — R1 STAGE 1 EXECUTED (the Lieutenant's release; the digit-scan 0/98 record opened the gate)

## 10. Pins in force at execution

- Prereg: commit `4def67e400953e8c4b833ce04345f75426a6180d` (bytes `9213bf7d...`).
- Amendment-1: commit `0c06e093566dcf6bfdf59665ea55a5ca68106444` (bytes
  `018f0bc1...`, verified IDENTICAL to this lane's draft; the amendment's
  own committed blob was re-hashed from the object store before execution).
- Gate condition verified by this lane before running:
  `digit-scan/final_run_job1/grasp_screen_digit_receipt_job1.json` sha
  `a4f9b62678b16efb287fe0e1792bd59e04b3dcf81ecd54e4e58800c8663000b7`,
  verdict `ZERO_SURVIVORS_DIGIT_SIDE` (job `3a1ff276...`).

## 11. The stage-1 package (base = the amendment commit)

| artifact | sha256 |
|---|---|
| package/package.json (owner wk-hand-remediation, task HAND-REMEDIATION-20261003-R1-STAGE1, base `0c06e093...`) | `304da443aa31246c9b6b0e97a2d5073e94274c93fd7df91c4c953f34c832d94b` |
| vpl1_pad.py (NEW; the VPL-1 layer) | `54af4a49ce57736cf0d90fe2a5d57ea98dd24d568efcae635b8e20479575794e` |
| run_stage1_pad.py (NEW; the driver: S0 mirror + identity gate + pad layer + post-pad S1 + P1-P4) | `33392b97f275c640d3a5e562f88996cbb3881e9cbd6621e897dd1167bd94a884` |
| control_input_table_vpl1.json (NEW; C6-C10 frozen truths) | `9cd8a56d89bdbe403a0c8513f04a32b2a43de85eea3d38c34f39931be9317783` |
| byte-identical reuse copies (verified against pins at run): instrument_v2.py `9514c5b1...`, grasp_screen.py `6b924e87...`, control_input_table.json `d8aacc23...`, PREREGISTRATION.md `897ca164...`, sealed v2.0 receipt `065328e4...`, mesh_input_table.json `6e5f3bac...`, mutation_structure.json `48b03759...`, + the base-tree prereg/amendment bytes | (pins in sections 1/4) |
| FINAL seal (5th): package/sealed/db7a8649101b43dab4428dba44bd4907/manifest.json | manifest sha256 `0737f0c2f9f0b8051db1bd6dab5d4a71d28eb0e250742ae31a2e90ec221be1e8`; change.patch `4cf28d1574096f929d37fe2c683253b9b5c6d114a2d22c6d6b41bfa9abbf986d` |

## 12. THE PASSED RUN (the accepted evidence)

| artifact | sha256 |
|---|---|
| runner receipt: job `d29113a12fb94cdba30501bcef327034`, state PASSED, exit 0, slot 2, cleanup_verified true, base `0c06e093...`, sealed manifest `0737f0c2...` | `f4304a68ab110edbd4adb3f458ece95f3711664a0b25b7dd8cc9964eeb16e386` (lane copy `final_run_stage1/runner_receipt.json`) |
| stage1_pad_receipt.json (runner-retained artifact) | `2b52b55d25767348cab7892fcd6dd2f8478ef05d97b4cd4b7ef332cba0161f7b` |
| stage1_pad_report.txt (runner-retained artifact) | `ba9a98d8ac36d3d8d07aa9aa64da7d8c6b04c8c17f2995d1c3f1349db4eaa177` |

## 13. Observed results (the runner-verified receipt; lane copies are convenience twins)

- VERDICT: `PAD_ADMITTED_SURVIVORS_PRESENT_STAGE1`, post-pad survivors 98.
- Gates ALL GREEN: 9 in-package pins; inherited input gate (14 pins);
  sealed C1-C3; palmar FK identity (all 5 bodies); battery C6-C10 (C6
  PAD_CONTACT u=1.0e-3 exact; C7 refused; C8 anti-masking
  GENUINE_PENETRATION 1.86e-3 m + tip PAD_CONTACT; C9 zero pad rows; C10
  identity rel_err 0.0, mask-area ratio 0.9572 within the declared 2x);
  witness chord reproduced; axis-family identity 16/16.
- SEALED-ROW IDENTITY GATE: q_c_PRIMARY ok (diffs=[]), q_zero_CONTROL ok
  (diffs=[]) — the mirror S0 reproduced the published v2.0 receipt rows,
  counters, by-bone maps and determinism slices byte-identically.
- P1 TRUE, P2 TRUE, P3 TRUE, P4 TRUE (both postures where stated).
- q_c conversions: 1,440 rows evaluated; PAD_CONTACT 534 + PAD_ABSORBED 292
  = 826 pad-satisfied; PAD_REFUSED_DEPTH 614; PAD_REFUSED_PATCH 0;
  window-exceeded-after-full-scan 0. Measured-anchored (u <= 0.8 mm):
  184; declared-extrapolated: 350. u range 4.39e-6 - 1.996e-3 m; force
  columns 5.04e-4 - 2.29e-1 N (DECLARED-MODEL-FORCE).
- P3 (the Captain's bone-clearance field): distph2 rows 486,
  pad-satisfied 0, refused 486 (>= 442 required) — the full-scan depths
  refuse EVERY opposing-bone row: the pad converts ZERO of the cause-2
  class; the causes remain fully separated.
- Post-pad S1 (caps inherited, never enlarged): 96 cells/posture
  (730 + 262 recorded S0_ONLY_CAP); survivors 84 (q_c) + 14 (q_zero);
  S2_REJECT_DEEP 12 (q_c: the opposing declared tip distph3) / 69+13
  (q_zero). Pad determinism slice 16/16 byte-identical. Wall clock 139 s.

## 14. Preserved failures on the way to the accepted run (all FAILED, cleanup_verified true; kept as records)

| job | cause (this lane's defect, fixed before the accepted run) |
|---|---|
| `6d9f08fb...` | mirror counters dict lacked the sealed schema's 8 zero keys -> identity gate refused (sealed_row_drift) |
| `8d435f3d...` | post-pad arithmetic identity omitted the cap terms -> refused (post_pad_arithmetic_broken) |
| `9a51c4a9...` | verdict block KeyError ('counters' vs 'pad_counters') after ALL gates/predictions completed green |
| `57e90a44...` | NameError from an incomplete edit of the measured_anchored column |
| `43846762...` | PASSED but SUPERSEDED: its receipt carried the mislabeled measured_anchored column (bone-depth test instead of u test); the accepted run is `d29113a1...` |

Dev smoke (lane-side, bounded grid, no results taken) exercised the F1
trigger for real: the first construction of C8 failed the battery and the
driver refused instrument_invalid_pad_masks_bone — the falsifier path is
proven able to bite (fixed pre-seal: the C8 construction now intrudes past
the body's MEASURED exact tangency, the sealed C2->C3 pattern).
