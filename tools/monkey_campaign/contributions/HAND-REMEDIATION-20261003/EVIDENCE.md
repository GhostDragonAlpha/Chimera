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

---

# PHASE 6 — stage 1 PUBLISHED (PR #333, astra 28e372ff, APPROVE w/ full recompute); the raised-cap amendment + stage-2 prep (PRE-RUN; no raised-cap run exists)

## 15. Publication record (received)

- PR #333 MERGED at astra `28e372ff`; review APPROVE with full recompute;
  the lane's two minor findings carried in the publication note verbatim.

## 16. Phase-6 artifacts (this lane)

| artifact | sha256 |
|---|---|
| R1_AMENDMENT_2.md (DRAFT for the Lieutenant's pin: the raised-cap declaration CAP_POST_PAD = 1500 = all pad-satisfied rows; compute cost from stage-1 throughput 63.5 ms/cell -> ~75 s S1; frozen count-floor predictions P5 >= 84 (q_c) / P6 >= 14 (q_zero), NO which-rows prediction; the three receipt-convention fixes) | `e96e09a1a925b12d68763139958eaae5897e27c027ecd3670336f5df5bc597cf` |
| R1_STAGE2_CAPACITY_PREP.md (stage-2 prep ONLY: inputs/law/method/honest reading/F2-F3 triggers; waits for the FINAL survivor set) | `cf85a805fe311c95a554697fabe0ea63cdd83583fdf0d0525649e44bd65f2dad` |
| package/files/.../vpl1_pad.py (REVISED, UNSEALED: AMENDMENT_2_SHA pin + CAP_POST_PAD) | `4f4b6925bf8682f17f544ad9c9b3b424370a4c27f2e968d5bd18468d1c485daa` |
| package/files/.../run_stage1_pad.py (REVISED, UNSEALED: raised cap in the post-pad stage; digit_scan_gate names its artifact + correct sha `a4f9b626...`; predictions keyed per posture, not update()d; receipt-level run_class + delta_note; P5/P6 floor verification) | `c9e68190c6871c3b932f37c43fdf1ce45b7054c7a71947932495f3894c8b36ab` |

Revision smoke (bounded grid, no results taken): all gates green;
post_pad_s0_only_cap = 0 at both postures (the raised cap runs every
satisfied row); arithmetic ok. The raised-cap seal happens ONLY after the
Lieutenant pins AMENDMENT-2 (the code pins its committed sha and refuses on
drift); the run executes on explicit release.

---

# PHASE 7 — AMENDMENT-2 PINNED + THE RAISED-CAP RUN EXECUTED AND PASSED

## 17. Pins in force

- AMENDMENT-2 pinned: commit `ccb60023568fb7c4d2cbd8d8e4855c0f5c18d372` on
  review/HAND-REMEDIATION-20261003 (parent = the stage-1 publication
  `1f700f3f`); committed blob content sha256 `e96e09a1...` = this lane's
  draft (byte-verified by the Lieutenant; re-verified by this lane from the
  object store before execution).
- The published tree at the pin commit was verified to carry EXACTLY the
  stage-1 sealed bytes (vpl1_pad `54af4a49...`, driver `33392b97...`, table
  `9cd8a56d...`, screen `6b924e87...`, instrument `9514c5b1...`) — so the
  raised-cap revision rebased cleanly with a 2-file delta.

## 18. The raised-cap package and run

| artifact | sha256 |
|---|---|
| package/package.json (task HAND-REMEDIATION-20261003-R1-RAISED-CAP, base `ccb60023...`) | `39720c5cc8d51de9c268edaf474d811b706fc1023b731858e28852ab8a936418` |
| vpl1_pad.py (raised-cap revision: AMENDMENT_2_SHA pin + CAP_POST_PAD = 1500) | `4f4b6925bf8682f17f544ad9c9b3b424370a4c27f2e968d5bd18468d1c485daa` |
| run_stage1_pad.py (raised-cap revision: cap raise; digit_scan_gate names its artifact + sha `a4f9b626...`; predictions keyed per posture; run_class + delta_note; P5/P6 floors) | `770ddd9a8c16d994afcfdf89e96340b9d00e549fc67237e5318a71ee4d0e1569` |
| FINAL seal: package/sealed/c4006dae631e4411922e2e5ba6d0996b/manifest.json (changed files: EXACTLY run_stage1_pad.py + vpl1_pad.py vs the pin commit) | manifest sha256 `c0c3fe755c3c52156a085444eebe7825900004800d092284f8e385a514706e23`; change.patch `708b91bf0662cc1ae02fe372e0b7b55b32a2ab99dbf685b739fb46455c7c22d1` |
| runner receipt: job `e4a5447bcef64b328f33d1f74cfd892d`, state PASSED, exit 0, SLOT 3, cleanup_verified true | `cb47edd28444c57e0ed1370516d693d714eafd7b5225c1d0875d38a189fc0439` |
| stage1_pad_receipt.json (runner-retained) | `4df5f48020c4dd601b7d6fc7c3047c4eb3c1e5c829bf450e07427c32c3835900` |
| stage1_pad_report.txt (runner-retained) | `3414973156bc80540572c99c80af7ca187ac18369aa600e9afe5dc77e891676f` |

Slot note (CORRECTED 2026-10-03, see section 26 C1 — the original note
misattributed other lanes' runner rows as this lane's attempts): this
lane's two slot-2 attempts were refused by the runner with BUSY responses
(`"state": "BUSY", "reason": "lock_busy"`, retry_after_seconds 10 — the
runner's stdout, this lane's only slot-state evidence) and left NO runner
rows at all. The two preserved FAILED slot-2 rows in the window are OTHER
LANES' jobs, preserved and correctly attributed to them:
`b892365d...` (19:03:54, the PAIR-ASSEMBLY retry,
CMP-ASMB-HG/test_pair.py) and `39257153...` (19:09:01, the
ASSEMBLY-INPUTS run_phase2.py, which retained six artifacts). The declared
fallback slot 3 took the run; nothing was deleted by this lane.

## 19. THE RAISED-CAP RESULTS (the full set; runner-verified)

- VERDICT: `PAD_ADMITTED_SURVIVORS_PRESENT_RAISED_CAP`;
  post-pad survivors total **354** (q_c 314 + q_zero 40).
- q_c_PRIMARY: ALL 826 pad-satisfied rows exact-adjudicated
  (post_pad_s0_only_cap = 0): **314 FULL-SET survivors**, 394
  S2_REJECT_DEEP (the opposing declared tip distph3), 118
  S2_REJECT_NO_CONTACT. P5 TRUE (floor 84).
- q_zero_CONTROL: ALL 358 rows adjudicated: **40 survivors**, 292 deep,
  26 no-contact. P6 TRUE (floor 14).
- P1-P4 TRUE and IDENTICAL to stage 1 (the S0 mirror reproduced the sealed
  receipt byte-identically again; the pad class splits are identical:
  826/614/0 at q_c). P3: distph2 486 rows, pad-satisfied 0, refused 486 —
  cause 2 remains untouched by the pad at the full set.
- Identity gates both ok; battery C1-C10 ok; pad determinism slice 16/16;
  wall 659.8 s (S1 clock 120.5 s vs the declared ~75 s estimate — the
  delta is the per-cell exact work at deep-fold rows; within budget).
- The three convention fixes CONFIRMED in the receipt: delta_note present;
  run_class `stage1_pad_raised_cap (AMENDMENT-2)`; digit_scan_gate names
  `digit-scan/final_run_job1/grasp_screen_digit_receipt_job1.json` with sha
  `a4f9b626...` (no v2.0-receipt mislabel); predictions keyed per posture
  (`predictions[q_c_PRIMARY][P1]`, ...).
- The FINAL survivor set for stage 2: 354 placements (314 q_c + 40
  q_zero), each carrying its pad row (class, u, witness, DECLARED-MODEL-
  FORCE) and anchor-envelope record — the input the capacity prep
  (`cf85a805...`) waits for.

---

# PHASE 8 — THE ERRATUM CARRIED (PR #335, astra 2944ea90; the P1 re-scoring is the governing label for this lane's records)

## 20. The label mapping (carried VERBATIM for the review; the erratum is a RESULT, never an error; no run invalidated)

- GOVERNING LABEL FOR P1 (superseding the coded label in this lane's
  raised-cap receipt): **"P1 partially falsified as literally frozen
  (534+292+128, identical at the raised cap)"** — the outcome decomposition
  of the 954 q_c TIP_DEEP rows: 534 PAD_CONTACT + 292 PAD_ABSORBED
  (u = 0, outside the literally-frozen u-range "(0, 2.0e-3]") + 128
  PAD_REFUSED_DEPTH; identical at the stage-1 cap and at the raised cap.
- This lane's raised-cap receipt's "P1-P4 all TRUE" labels carry the SAME
  code-scoring convention the adjudication corrected (the coded P1 verdict
  scored the pinned falsifier-condition list, under which the u = 0
  absorbed class was not a named contradiction). The coded labels remain
  in the receipt bytes as the record of what the code scored; the ERRATUM'S
  label above is the governing reading for every downstream citation.
- STANDING RESULTS (the erratum leaves them intact): the P5/P6 floor
  verdicts (q_c 314 >= 84; q_zero 40 >= 14 — the capped samples
  representative, slightly conservative) are the NEW results and stand.
  P3's full-set confirmation stands (distph2 486 rows, pad-satisfied 0).
  P2/P4 stand as coded.
- The stage-2 prereg is authored against this corrected reading: the
  absorbed band is an EXPLICIT predicted class (S2-P2), every falsifier's
  contradiction teeth are stated against the FULL outcome space, and every
  cited quantity names its instrument-quantity code path.

## 21. Slot-2 preservation note (CORRECTED 2026-10-03, see section 26 C1)

This lane's slot-2 refusals left NO runner rows (BUSY responses on the
runner stdout only — slot-state evidence). The two preserved FAILED slot-2
rows in the window are OTHER LANES' jobs, kept and correctly attributed:
`b892365d...` (the PAIR-ASSEMBLY retry, CMP-ASMB-HG/test_pair.py) and
`39257153...` (the ASSEMBLY-INPUTS run_phase2.py, six retained artifacts).
The declared fallback slot 3 took the raised-cap run (job `e4a5447b...`,
PASSED, cleanup_verified true).

---

# PHASE 9 — THE STAGE-2 PREREG DRAFT (authored against the corrected reading; for the Lieutenant's pin; no stage-2 run exists)

## 22. Phase-9 artifact

| artifact | sha256 |
|---|---|
| R1_STAGE2_PREREG.md (DRAFT: the capacity outcome space {CAP_SATISFIED, CAP_EXCEEDED, ARM_NONFINITE_REFUSED} with coverage arithmetic; S2-P1 full-set capacity coverage at the declared-model forces; S2-P2 the EXPLICIT ABSORBED-BAND prediction (exactly 6 u=0 survivors, identically zero force/tau, the 348/6 split reproduced); S2-P3 the chain-structure bite; S2-P4 non-vacuity via the constructed 60 N-class CAP_EXCEEDED case; the quantity code-path table incl. the d_receipt-vs-d_covered_max naming law; the not-claims section) | `2d7ff4172388fff75bb6bf46710a3c8c8857933d6c315166f3d7f7371610b3ec` |

Receipt-basis numbers cited by the draft (from the raised-cap receipt
`4df5f480...`): 354 survivors = 348 PAD_CONTACT + 6 PAD_ABSORBED (6 q_c +
0 q_zero); contact force columns 1.21e-3 - 2.29e-1 N; the survivor-set
input is pinned to the raised-cap receipt bytes.

---

# PHASE 10 — STAGE-2 PREREG PINNED + THE CAPACITY RUN EXECUTED AND PASSED

## 23. Pins in force

- Stage-2 prereg pinned: commit `662362e335e0078fc93d4c1bb0ee856875efa34f1`
  (per the Lieutenant's citation `662362e3`) on
  review/HAND-REMEDIATION-20261003; committed blob content sha256
  `2d7ff417...` = this lane's draft (byte-verified by the Lieutenant;
  re-verified by this lane from the object store).
- The tree at the pin carries the stage-1 vpl1_pad (`54af4a49...`) — the
  stage-2 module defines its own AMENDMENT_2_SHA literal (the stage-1
  module predates amendment-2).

## 24. The stage-2 package and run

| artifact | sha256 |
|---|---|
| package/package.json (task HAND-REMEDIATION-20261003-R1-STAGE2, base `662362e3...`) | `6a9ebd77ddc351ed42011924598cafbf61f456a53ceb1981d9f2d664cd31adea` |
| stage2_capacity.py (NEW: the map-gated jacobian machinery, the outcome-space classifier, the F2 chain-structure check) | `b0836daa1877c176ee2716ee59170d50bf714f434f61fac9aa602540d10cf3bf` |
| run_stage2_capacity.py (NEW: the driver — pins, identity gates, per-survivor capacity, S2-P1..P4) | `d399a3a6b69962da9ef61f705dc4aa9a2db32bd1c41d0ae36e85689c923bb283` |
| raised_cap_receipt.json (NEW copy; the survivor-set input, pinned `4df5f480...`) | in-package copy of the raised-cap receipt |
| jacobian_map.json (NEW copy; the map of record, pinned `96a4610f...`) | in-package copy |
| FINAL seal: package/sealed/8cd676bc73164367a1a87ab37fd031d7/manifest.json (changed: jacobian_map.json, raised_cap_receipt.json, run_stage2_capacity.py, stage2_capacity.py) | manifest sha256 `f8dde9e3460950e7e64d9002b01f1f30353942cc13cb80c193f6c62ba4bb341c`; change.patch `a2aa55159e7764f7de35030c41fa5215cadc04ebae9dff7cca12245bd587142f` |
| runner receipt: job `3e9768f72f794e26824386c75bc07210`, state PASSED, exit 0, SLOT 3, cleanup_verified true | `adad65e42c06e00934af196ec797f768faaded0875d0ab17db1c6851d53b2bb7` |
| stage2_capacity_receipt.json (runner-retained) | `8b93464c6ee206570c60fd00a750a2229ea650b0afaf589b8bbce6ed0bde174d` |
| stage2_capacity_report.txt (runner-retained) | `b33d80e90f3501936d1fc803237bd0f812a9f3c4a3d469aa7f3f851ef9a7b017` |

Slot note (CORRECTED 2026-10-03, per the section 26 C1 lesson): this
lane's stage-2 slot-2 attempt was refused by the runner with a BUSY
response (`"reason": "lock_busy"`, stdout only) and left NO runner row;
the preserved FAILED slot-2 row `6b0ed8b4...` in the window is NOT this
lane's job and is not attributed to this lane. Slot 3 took the run;
nothing deleted.

## 25. THE STAGE-2 RESULTS (the runner-verified receipt; the not-claims section governs every reading)

- VERDICT: `STAGE2_CAPACITY_SATISFIED_FULL_SET`. Wall 6.8 s.
- Outcome space CLOSED over 354: q_c 314/314 `CAP_SATISFIED` +
  q_zero 40/40 `CAP_SATISFIED`; 0 CAP_EXCEEDED; 0 ARM_NONFINITE_REFUSED;
  coverage arithmetic exact both postures.
- S2-P1 TRUE (all 354 satisfied at the DECLARED-MODEL-FORCE magnitudes;
  binding joints recorded per survivor). S2-P2 TRUE (the absorbed band:
  exactly 6 u = 0 survivors — 6 q_c + 0 q_zero — zero force, zero tau, 0
  violations). S2-P3 TRUE (the off-chain trigger FIRED:
  thumb/mcp2_flexion -> off_chain_structural_zero). S2-P4 TRUE
  (non-vacuity: the constructed 60 N-class force classifies CAP_EXCEEDED,
  binding mutation_wrist_abduction, worst 2.8308 N*m — the comparison
  bites).
- Jacobian identity gates: the map's PRIMARY columns reproduced by the
  column law from the map's own joint_records (diffs = []), and the sealed
  FK reproduced the map's joint_records (22 joints).
- Receipt conventions: run_class `stage2_capacity`, delta_note present,
  governing_labels carries the erratum's P1 label verbatim, survivor-set
  input named + pinned, per-posture keyed blocks.
- THE GOVERNING READING (the pinned not-claims): this stage is ladder
  consistency at the pad's <= 0.23 N declared-model forces — it is NOT a
  grasp-capacity qualification; the press channel is ABSENT (TC-8 = 0/8);
  the same-hands finding stands; stages 3-5 own the rest of the ladder.

---

# 26. CORRECTIONS AND DISCLOSURES (dated 2026-10-03; the Sergeant raised-cap verdict, CHANGES_REQUIRED - NARROW: the sealed run itself APPROVE-grade)

## C1 (MUST FIX - APPLIED above, in sections 18/21/24, in place)

The original slot-2 narratives in sections 18/21 (and the same defect in
section 24) borrowed OTHER LANES' runner rows as this lane's attempts:
`b892365d...` (19:03:54) is the PAIR-ASSEMBLY retry
(CMP-ASMB-HG/test_pair.py - the disputed physics finding) and
`39257153...` (19:09:01) is the ASSEMBLY-INPUTS run_phase2.py (six
retained artifacts, not "only runner.log"). THE TRUE RECORD: this lane's
slot-2 refusals left NO runner rows at all (the reviewer's exhaustive
window scan found exactly three result dirs); this lane's only slot-state
evidence is the runner's BUSY stdout responses
(`"reason": "lock_busy"`, retry_after_seconds 10). The two named rows are
other lanes' jobs, preserved, correctly attributed to them. THE LESSON
(now law for this lane): EXECUTION NARRATIVES NEVER BORROW OTHER LANES'
ROWS AS THEIR OWN ATTEMPTS - the same claims-vs-record class the erratum
polices.

## C2 (MUST DISCLOSE - APPLIED; the retention disclosure)

The raised-cap seal directory `package/sealed/c4006dae631e4411922e2e5ba6d0996b/`
(manifest sha256 `c0c3fe755c3c52156a085444eebe7825900004800d092284f8e385a514706e23`;
change.patch `708b91bf0662cc1ae02fe372e0b7b55b32a2ab99dbf685b739fb46455c7c22d1`;
the 16-file sealed tree) WAS DELETED during the stage-2 packaging
recreation (this lane's `rm -rf` of the package dir), contradicting the
retention promise, undisclosed until this entry. The recorded hashes stand;
the Sergeant reviewer's PRE-DELETION VERIFICATION is the reconstruction
basis for the deleted delta. The SAME deletion class applies to the
stage-1 seal directory `package/sealed/db7a8649101b43dab4428dba44bd4907/`
(manifest `0737f0c2f9f0b8051db1bd6dab5d4a71d28eb0e250742ae31a2e90ec221be1e8`;
change.patch `4cf28d1574096f929d37fe2c683253b9b5c6d114a2d22c6d6b41bfa9abbf986d`),
deleted in the earlier package recreation - disclosed here in the same
entry. THE MECHANICAL FIX (now law): publications CAPTURE SEAL BYTES
(manifest + patch) INTO A RETAINED STORE AT PUBLICATION TIME - hash
records alone do not preserve a deleted delta. APPLIED IMMEDIATELY: the
surviving stage-2 seal `8cd676bc73164367a1a87ab37fd031d7` is captured into
`seal-store/` (`8cd676bc..._manifest.json` sha256 `f8dde9e3460950e7e64d9002b01f1f30353942cc13cb80c193f6c62ba4bb341c`;
`8cd676bc..._change.patch` sha256 `a2aa55159e7764f7de35030c41fa5215cadc04ebae9dff7cca12245bd587142f`),
and every future seal of this lane is captured at creation.

## The commission-citation convention (adopted; STRENGTHENED 2026-10-03)

A stale EVIDENCE sha was cited in a commission (the file grew during the
stage-2 work). STANDING CONVENTION: the EVIDENCE sha is FROZEN and stated
in this file's newest dated entry BEFORE the next review dispatch.

## The section-26 hash correction (dated 2026-10-03, per the stage-3 review)

The section-26 freeze recorded the hash `410c16ad...f9496aa` BY HAND; the
hand-copied value DROPPED A LEADING ZERO (a sha256 is 64 hex digits; the
recorded literal is short one) and the referenced content state can no
longer be reconstructed byte-exactly (the file grew through phases 10-12).
THE CORRECTION: the recorded value is marked UNVERIFIED-AS-RECORDED; it is
NOT a citable identity. THE CONVENTION (now law): EVERY hash line in this
file is SCRIPT-EMITTED (computed and written by the same script that
measures the bytes) - hand-copied hashes drop zeros and are prohibited.
The authoritative current hash is the script-emitted line at the end of
this file.

## The section-29 condensation omission RESTORED (dated 2026-10-03)

Section 29 condensed away the per-survivor capacity detail of the sealed
stage-2 receipt (`.../stage2_capacity_receipt.json` sha
`8b93464c6ee206570c60fd00a750a2229ea650b0afaf589b8bbce6ed0bde174d`).
RESTORED from those bytes: the binding-joint distribution over all 354
capacity rows is {mutation_wrist_abduction: 336, mutation_wrist_flexion:
12, cmc_abduction: 6}; the per-row worst |tau| range is 0 (the 6
PAD_ABSORBED survivors - zero force, zero torque, the absorbed band made
physical) to 1.081312e-02 N*m (the PAD_CONTACT class, three orders below
the 0.8875 N*m cap basis - the capacity stage's ladder-consistency
reading, never a grasp claim).

## The heredoc disclosure (dated 2026-10-03; relay-only disclosures are unverifiable downstream - the law)

The phase-12 EVIDENCE append was authored through a shell heredoc that
malfunctioned and appended stray shell lines to this file's tail; the
stray lines were removed by script in the same session. DISCLOSED HERE IN
THE FILE ITSELF (a relay-only disclosure in a chat message is
unverifiable downstream - the law): the tail was inspected post-cleanup
and ends on the phase-12 not-claims text; no other content was touched.

## The publication merge note (carried)

`2944ea90` (the erratum) is NOT an ancestor of the branch tip; the
publication carries an EXPLICIT merge/rebase step. Recorded for every
future citation of astra hashes from this lane.

## The frozen EVIDENCE hash for the next review dispatch

recorded after this section: see the hash line below (the file is frozen
at that hash until the next dated entry).

FROZEN EVIDENCE SHA256 (section 26, dated 2026-10-03): `410c16ad2e74eb40e1ccb1751d9118e95a29c60305826c56f5e1c8095f9496aa` - UNVERIFIED-AS-RECORDED (hand-copied; dropped leading zero; see the section-26 hash correction above). NOT a citable identity.

---

# PHASE 12 — STAGE-3 PREREG PINNED + THE CONTACT-FORCES RUN EXECUTED AND PASSED

## 27. Pins in force

- Stage-3 prereg pinned: commit `6c1aa445f2fa81fb1ec5c5e393e8fa7c4f645a5c`
  on review/HAND-REMEDIATION-20261003 (parent `662362e3...`);
  committed blob content sha256 `4dfb62e0...` = this lane's draft
  (byte-verified by the Lieutenant; re-verified by this lane from the
  object store).

## 28. The stage-3 package and run

| artifact | sha256 |
|---|---|
| package/package.json (task HAND-REMEDIATION-20261003-R1-STAGE3, base `6c1aa445...`) | `314251f15baa0eb8eeeb792910efa093b2d9c47b99ba767b6ac2aae7179cfdf4` |
| stage3_forces.py (NEW: the frozen tick law, the closed-form cumulative identity, the mu law forms) | `81b17b2792dccb59f5ad51390c819df5478822fd02e2af46d4a548d10ab288e1` |
| run_stage3_forces.py (NEW: the driver — pins, per-survivor ticked sequences, the outcome partition, S3-P1..P5) | `0c41e0d373e05262ec2b4a638540b16b8bf2ec785b2105c5f5de68c860b095e5` |
| FINAL seal `6d4ac09c2c5c40ce887a5f03989b923a`: manifest sha256 `9c68f541f3f9c330a0e6b064ea05b1d654c99d50ab103b69b5e61a4da0b7901b`; change.patch sha256 `932630ac7653583a3727daec7c963114b5d6f08da0d1d6555b1a89b4711fb947` — CAPTURED INTO seal-store/ AT CREATION (the C2 law) | |
| runner receipt: job `2b355a46de924a3b82acedf2862b5379`, state PASSED, exit 0, SLOT 3, cleanup_verified true | `5340ccb199c1f132151967777e19a6bb86f4498ddc9589ded56fa33207326328` |
| stage3_forces_receipt.json (runner-retained) | `63ec1a8e38abc0ba1a05ae594db1241cc2acc642d1d82e7eebb3d945a167d01f` |
| stage3_forces_report.txt (runner-retained) | `6043b24e11d03cca0fdaff04300334150fdf05d7a7a85da2755c04f62900d8af` |

Slot note (the corrected record discipline): slot 2 was skipped after the
prior lock_busy observations; slot 3 took the run directly; no slot-2 rows
were created by this lane and none are attributed to it.

## 29. THE STAGE-3 RESULTS (the runner-verified receipt; the not-claims govern)

- VERDICT: `STAGE3_FORCES_IDENTITY_FULL_SET`. Wall 0.34 s.
- OUTCOME PARTITION over 354 (coverage exact both postures):
  q_c_PRIMARY 314 = 308 IDENTITY_CLOSED + 6 ZERO_FORCE_CLASS + 0
  IDENTITY_MISMATCH; q_zero_CONTROL 40 = 40 IDENTITY_CLOSED + 0 + 0.
- S3-P1 TRUE: all 348 PAD_CONTACT survivors IDENTITY_CLOSED (308 + 40);
  0 violations (no tick carries a signed reversal; every cumulative
  impulse matches the independent closed form within 1e-12 relative).
- S3-P2 TRUE: exactly 6 ZERO_FORCE_CLASS (6 q_c + 0 q_zero — the absorbed
  band, all 40 ticks F = 0, J = 0).
- S3-P3 TRUE: mu = 0 -> `NON_CLOSING_AT_MU0` (the law-form divergence;
  no P_req evaluated).
- S3-P4 TRUE: mu = 0.6 -> `CLOSES`, P_req = 54.68840727038889 N (the
  positive control bites; the 54.69 N vs the 60 N declared ceiling is the
  A6 law form at the placeholder, CONDITIONAL-CALCULATION, never a
  measured hold).
- S3-P5 TRUE: the constructed reversal case records min signed force
  -0.2292 N and classifies IDENTITY_MISMATCH — the instrumentation shows
  reversals, never absorbs them.
- Dev-smoke defect caught and fixed PRE-SEAL (the erratum lesson applied
  to this lane's own scoring): the first smoke scored S3-P1 against all
  314 q_c survivors (falsely false through the 6 absorbed rows); the
  pinned text scores the PAD_CONTACT class (348) — the scoring was fixed
  to the pinned words BEFORE any sealed run.
- THE GOVERNING READING (the pinned not-claims): friction PLACEHOLDER
  (A5); no monkey-bark value exists; NO solver integration claimed (the
  identity here is the declared law form on constructed schedules); the
  36 N figure stays conditional on model + mu = 0.6; TC-8 = 0/8; the
  same-hands finding stands; no hold or grasp result exists in this
  class — the hold law is stage 4's, on its own gates.

[HISTORICAL - SUPERSEDED BY THE FILE-END LINE] SCRIPT-EMITTED EVIDENCE SHA256 (emitted by script 2026-10-03; THE HASH COVERS THIS FILE'S BYTES PRIOR TO THIS LINE - the self-exception rule): 181618a5ded850f6ed78d53adb0eac3c924f4140f54ce2006ac2024cbe25cc74
(verification: hash this file's bytes up to just before this line, with the trailing single newline retained; the result must equal the stated value.)


---

# PHASE 13 — THE THREE RECORD ACTIONS APPLIED + THE STAGE-4 PREREG DRAFT (dated 2026-10-03; for the Lieutenant's pin; no stage-4 run exists)

## 30. The record actions (each dated; the stage-3 review's items, applied)

- THE HEREDOC DISCLOSURE: recorded in the dated entry above (the phase-12
  heredoc malfunction, the stray shell lines, the script cleanup - IN THIS
  FILE, per the relay-only law).
- THE SECTION-26 HASH: marked UNVERIFIED-AS-RECORDED (the hand-copied
  literal dropped its leading zero and the referenced content state cannot
  be reconstructed byte-exactly); THE SCRIPT-EMIT LAW adopted - the
  authoritative identity line at this file's end is script-emitted with
  the self-exception rule and was independently verified after writing.
- THE SECTION-29 RESTORATION: the per-survivor capacity detail restored
  from the sealed stage-2 receipt bytes (binding joints
  {mutation_wrist_abduction: 336, mutation_wrist_flexion: 12,
  cmc_abduction: 6}; worst |tau| 0 to 1.081312e-02 N*m).

## 31. The stage-4 prereg draft (DECLARED-MODEL SCOPE)

| artifact | sha256 |
|---|---|
| R1_STAGE4_PREREG.md (DRAFT: the scope decision and why; the 4x5 (reading, n) grid; the outcome space incl. the explicit TRANSFER_UNDEFINED_AT_N1 class; the FROZEN partitions S4-P1 15 CLOSES + 5 EXCEEDED (the scene line exceeds at n=1 AND n=2) and S4-P2 11 CLOSES + 5 EXCEEDED + 4 UNDEFINED; S4-P3 the mu=0 bite retained; the quantity code-path table; the honest-absent list with the same-hands debt named) | `4438c4d76c2d904d08a09eb1f29db55b25bdccaeb399f2d8db26ad0d78e5dfc1` |

Scope answer recorded for the pin: stage 4 freezes the DECLARED-MODEL
SCOPE (the G01 law forms as CONDITIONAL-CALCULATIONS at declared inputs)
because the press channel has NO actuator derivation (TC-8 0/8) - a
physical hold run would overclaim. The same-hands debt stands and is
named.


---

# PHASE 14 — STAGE-4 EXECUTED AND PASSED + THE COLLISION-IDENTITY CORRECTION ACCEPTED + THE ADJUDICATION PREREG (dated 2026-10-03)

## 32. THE COLLISION-IDENTITY CORRECTION (ACCEPTED; verified from the stored rows by this lane BEFORE executing)

The collaborator's claim VERIFIES EXACTLY: the 314 q_c survivors' s_star
offsets span 2.828788e-03 - 9.634829e-03 m (the raised-cap receipt,
stored rows) against R2's ~0 antipodal construction offset (h_len =
2.0635200292263314e-06 m, the frozen GP1-CC3 v1 formulation) - the exact
origins differ by 2.83-9.63 mm; the q_zero survivors carry 2.56-2.60e-02
m and have NO R2 counterpart. CONSEQUENCE (the corrected label): the 354
survivors are ACTUATOR-CAPACITY SURVIVORS, NOT collision-cleared
candidates; R2's GENUINE_PENETRATION labels neither clear nor reject
them; the 'collision geometry done' ladder wording OVERSTATES. THE
CORRECTED LABEL: pad-geometry + capacity + law-form stages complete; the
EXACT-CANDIDATE COLLISION ADJUDICATION = a named unmet stage. The
stage-3/4 law-form partitions STAND (declared-model scope fences them);
the LABELS correct. The correction note is embedded in the stage-4
receipt (`collision_identity_correction`) and the next publication's
merge message carries the same note.

## 33. THE STAGE-4 RUN (executed as pinned; the correction note embedded)

| artifact | sha256 |
|---|---|
| package/package.json (task HAND-REMEDIATION-20261003-R1-STAGE4, base `79b26394...`) | `55f0e22fbdaef7348bd197919bb4e097dce7f653807c4a3e7043a05db89fc4d1` |
| stage4_grasp.py (NEW: the law-form module) | `baf2a7a31f88f5ae87fa4d5ebf7a65fdc45ef6e044c57e4241ae763bf44332ba` |
| run_stage4_grasp.py (NEW: the driver - the 4x5 grid, the frozen partitions, the mu=0 bite, the debt-row side-by-side, the correction note) | `0e6c3cfbbe0df304e118ab13b6ecc4127c230a0936d16ff32535633bd7a2bf44` |
| FINAL seal `988b2cf0fa0b4b6eb4335c1b9612b35d`: manifest sha256 `7f9d9db7deccd6759543873b0301ad3c9563a78f63c3dad76bd93f5a5c0fb402`; change.patch sha256 `d1e5ec112a389c613fe097c91f420b62393830632fe7b2ae766c50b9cb5357a3` - CAPTURED INTO seal-store/ AT CREATION (the C2 law) | |
| runner receipt: job `ef225dcdca804417be46f73bdb12c3b9`, state PASSED, exit 0, SLOT 3, cleanup_verified true | `e54ec771c1304250ce73c0be821544ec01a10ef6bf84d72ef2bb1c32dcd9152e` |
| stage4_grasp_receipt.json (runner-retained; the correction note embedded) | `53914096eaddce71379e7cde43c737e30b25240177b182d90f6d1d6b0702309e` |
| stage4_grasp_report.txt (runner-retained) | `30ee708478f822c987a052cd493b465112eb027e2091c241a40565c5e2c647c9` |

## 34. THE STAGE-4 RESULTS (the runner-verified receipt; the not-claims govern)

- VERDICT: `STAGE4_PARTITIONS_REPRODUCED_FULL_GRID`. All predictions TRUE
  (S4_P1, S4_P2, S4_P3, S4_P4).
- STATIC partition: 15 HOLD_CLOSES + 5 HOLD_EXCEEDED - the 5 exceeded
  cells EXACTLY the frozen ones: (10.037998, n=1) 164.065 N, (10.037998,
  n=2) 82.033 N, (5.4, n=1) 88.260 N, (6.15, n=1) 100.518 N, (6.9, n=1)
  112.776 N. The scene line exceeds at n=1 AND n=2.
- TRANSFER partition: 11 TRANSFER_CLOSES + 5 TRANSFER_EXCEEDED
  (all four readings at n=2; the scene line also at n=3: 0.2461 N*s) +
  4 TRANSFER_UNDEFINED_AT_N1 (the explicit named class). 5+4+11 = 20.
- S4_P3: mu = 0 -> NON_CLOSING (the bite, retained).
- S4_P4: the debt-row side-by-side recorded (the law-form cell
  (10.037998, n=2) HOLD_EXCEEDED 82.033 N BESIDE the capacity debt row
  tau 1.391986171 N*m vs the 0.8875 N*m cap at cmc_abduction - a
  FORCE-ceiling reading and a TORQUE-vs-CAP reading, DIFFERENT
  quantities, neither substitutes for the other).
- THE GOVERNING READING: stage 4 is the DECLARED-MODEL law grid - it
  demonstrates NO PHYSICAL HOLD; the same-hands debt stands; TC-8 = 0/8;
  the goal stays open.

## 35. THE EXACT-CANDIDATE COLLISION ADJUDICATION PREREG (the coordinator's action 2; DRAFT for the Lieutenant's pin)

| artifact | sha256 |
|---|---|
| R1_COLLISION_ADJUDICATION_PREREG.md (DRAFT: reconciliation-first (the R2 rows labeled a different placement family, retained); the CURRENT UNCHANGED strict instrument (no candidate-specific exemption, no threshold change); the exact 354 (posture, theta, mirror, o, u) tuples; the closed outcome space {COLLISION_CLEAR, GENUINE_PENETRATION, UNRESOLVED_GEOMETRY}; the honest predictions S5-P1 (every candidate GENUINE at its pad-body pair - the basis: the admitted bone vertices sit (pi_c, 4mm] inside the trunk and the strict instrument has no pad), S5-P2 (zero COLLISION_CLEAR - any hit is a MAJOR routed result), S5-P3 (zero trunk-pair UNRESOLVED), S5-P4 (the self-collision sweep recorded)) | `1362f92fa410fe743ecc0d2639e54105c2167fcd21f47f4b1317acc5de4855dd` |
SCRIPT-EMITTED EVIDENCE SHA256 (script-emitted 2026-10-03; the hash covers this file's bytes PRIOR to this line - the self-exception rule): 4cc7960cebb54d5d8fc14c907728420917d5a651621b8da797eeec86923ce836
(verification: sha256 of the file bytes strictly before the marker, final newline included as stored, equals the stated value.)
