# D-W04-MASS-20260924 — frozen walking acceptance denominator vs actual training body

- card: **D-W04-MASS-20260924** (planning ids W04/P02)
- attempt: **26382263eb094eaf98a8354a2fe8592c**
- arrival: **arrival-9e17bf8ab0f340619eb21c1b83976fa2**
- branch: **branch-1**
- criteria: **ee0cc5fb27850b82c9b24decf50d06c306ba82fae8c8aa4e9148d66032ff55b1**
- source repo (READ-ONLY): `E:/ChimeraWork/monkey-play-20260924` — all citations `file:line@commit`
- date: 2026-09-25

## VERDICT

**NO — the frozen walking acceptance denominator is NOT bound to the actual training body.**
The finding is determinate, not ambiguous: both the acceptance expression and the training
body are unambiguous; they are simply **different bodies**. The acceptance CoT denominator
is the **playable-slice membrane creature's material inventory (13824.5 kg)**, while the
trainer env that produces `work_J` simulates the **10.038 kg Oku-2021 gait walker** — a
**1377.2166x** mismatch (recomputed: 13824.5 / 10.038 = 1377.2166). W04 must not be
declared ready on this axis; the binding is RESOLVED-AS-WRONG and needs a lead-authorized
NEW registration (see correction proposal). This confirms and sharpens the prior P02P03
flag (section 6).

## 1. The exact frozen CoT expression

`tools/science_funnel/first_skill/acceptance.py` — blob `3df32b59b09411721913229c8df4eb3efa04379e`,
first landed @ `8294053b` (FIRST-SKILL PRESTAGE, the direct child of lane base `73f3a860`),
byte-identical through trainer builds `82ebea49`, `eab5de13`, and typeb tip `a62b286e`
(verified: same blob at all four). ABSENT at `43b599a7` and at origin/master `33e7a444`
(the acceptance path exists only on the training lanes).

```python
# line 18
M_BODY_KG = 13824.5       # the measured membrane inventory at water density
# line 43 (inside episode_bars)
cot = work / (M_BODY_KG * dist) if dist > 0.0 else INF
```

where `work = float(record.get("work_J", 0.0))` (line 42) and `dist` is the episode's
along-heading CoM displacement. The same expression is frozen in two more places:

- `tools/science_funnel/validation/first_skill_prestage_20260922/RUNBOOK.md` line 76 (blob
  `73a41120fce27a6bf85073712ccc7a68382ff46b` @ `8294053b`), step 5:
  `CoT = E_ledger/(13824.5 kg x d_reached)`.
- `tools/science_funnel/validation/first_skill_prestage_20260922/run_manifest.json` line 54
  (blob `3188e72f949149a335ea6aa1863db90b51e402f6` @ `8294053b`), `hard_conditions.cot_within_band.definition`:
  `CoT = E_episode / (m_body * d_reached); ... m_body = 13824.5 kg (the measured membrane inventory at water density)`.

## 2. Four-mass lineage table

Every number below recomputed, not trusted from prose.

| Mass | Semantic identity | Definition site (file:line@commit, blob) | Derivation (recomputed) | Consumers | NOT consumers |
|---|---|---|---|---|---|
| **13824.5 kg** | Playable-slice membrane creature material inventory (13.824536 m^3 sealed cells at water density 1000 kg/m^3); also the slice engine's membrane body-mass default | Origin: `docs/evidence/agent_fleet/MATTER_KERNEL/SEAL_PREREGISTRATION.md:127,199` @ `0a1a7c5f` (13.824536 m^3); first code `ChimeraEngine/engine/membrane_tick.hpp:188` @ `0a1a7c5f` (mass_kg_ = 13824.5f); later `membrane_tick.hpp:423` @ `a62b286e`, `membrane_tick.cpp:1684` (`LIMB_MASS_TARGET_KG`); **CoT denominator**: `acceptance.py:18` @ `8294053b` (blob `3df32b59`) | 13.824536 x 1000 = 13824.536 -> frozen literal 13824.5 (0.036 kg low vs sealed sum; creature-graph band compartments 0.287914+0.334578+0.693006+12.5091 = 13.824598 -> 13824.598, a second, slightly larger, inventory figure @ `a3d63215`) | first-skill acceptance.py + RUNBOOK step 5 + run_manifest.json:54; `tools/report_first_skill_checkpoint.py:120` @ `a62b286e` (report label); `tools/gait_verify.py:110` (slice movement-law root DOF y''=-g+F/m); slice engine membrane tick; XPBD diagnostic `tools/xpbd_diagnostic.py:308`; creature_graph `param.mass_inventory` (`build_seed.py:691`) | **NOT** the trainer env: `walker_env.cu` includes only `walker_kernels.cuh` (verified includes @ `a62b286e`); `build_dll.ps1` compiles `walker_env.cu` alone. The pinned copy `tools/science_funnel/typeb_gpu/engine_inc/membrane_tick.hpp:423` carries the literal but is NOT a build input of walker_env.dll |
| **10.038 kg** | **THE TRAINING BODY** — the gait walker rigid assembly authored from Oku 2021 (Commun Biol 4:308) Table 1 segment masses | `tools/science_funnel/validation/gait_controller_20260918/derived_numbers.json:11` (`"mass_kg": 10.038`, blob `8b6d75fbd408a8e1e2db31cdf15fc4a104b9a36a`) @ `33e7a444`; arithmetic `docs/research/20260918_monkey_assembly_derivation.md:112-114` @ `33e7a444`; scene builder `tools/science_funnel/gait_scene.py:70-97` (blob `5c8792aef60f9eb2eb2e10549546ff12a2efe21b`) @ `33e7a444` | HAT 8.184 + 2 x (thigh 0.557 + shank 0.269 + foot 0.080 + phalanges 0.021 = 0.927) = **10.038 kg**; weight 10.038 x 9.80665 = **98.4391527 N** — exactly the measured gait_scene receipt value (`validation/gait_zero_20260919/receipt_wave8_trunk_vault.json:26`: "weight=98.4391527 N, mass=10.038 kg"); scene carve cancels: (8.184 - 2x0.406001) + 1.854 + 2x(0.2737+0.1323) = 10.037998 | **THE execution chain into the trainer env** (all @ `a62b286e`): compiled scene `.tmp/gait-walker/scene.json` -> `typeb_gpu/walker_model.py:149-155` (`self.body_mass[i] = float(b["mass_kg"])`) -> `typeb_gpu/walker_nb_env.py:35-36` (`build_model_arrays`, mdl at `OF_body_mass = 90`) -> `typeb_gpu/walker_kernels.cuh:401-402,826` (`m = body_mass[b]` in the dynamics) -> work battery `bat[12]` -> `bat_sum` -> `rb[e*6+5]` (kernels 4963-4972) -> `tools/train_first_skill.py:379` (`"work_J": float(st["rb"][i,5] - self._work0[i])`) -> `acceptance.py:42`. Also the Oku demand anchor: `validation/k_fill_20260920/derive_k_fill.py:65` (`OKU_MODEL_TOTAL_KG = 10.038`, blob `bfce9681...`) and ankle adjudication demand (`adjudication_table.json:62,104`) | Not the CoT denominator. (Caveat: `typeb_gpu/walker_numba_split.py:511` contains "-10.038" as a freefall acceleration comment, m/s^2 — NOT a mass usage) |
| **6.15 kg** | Turnquist & Kessler 1989 adult-female rhesus band midpoint (band 5.4-6.9 kg) — the muscle/deposit BOOK mass context ("the game's 6.15 kg animal"), NOT the walker's rigid mass | `tools/science_funnel/validation/k_fill_20260920/derive_k_fill.py:71` (`AF_MIDPOINT_KG = 6.15`, blob `bfce9681049b7d9354bd498fbf011a633f0ed26f`) @ `33e7a444`; `validation/ankle_adjudication_20260920/derive_adjudication.py:74` (`BAND_MIDPOINT_KG = 6.15`, blob `53c324f354576f32d99bbc67b70fce2dc7744f6a`); `validation/deposit_mass_20260921/deposit_mass_book.json:16` | (5.4 + 6.9) / 2 = 6.15 exactly; k-fill D3 target = Oku chain fraction x 6.15 = (2x0.927/10.038) x 6.15 = **1.135894** kg (matches `k_fill_20260920/receipt.json:232`) | k_fill_book (D3 mass set), deposit_mass_book scaling, ankle adjudication verdict-B demand-mass context, `README.md:391`, `docs/THE_SHIP_GOAL.md:167` | **NOT** the trainer env, **NOT** the acceptance math, **NOT** the gait walker's rigid bodies |
| **17.039978509953905 kg** ("17.04") | Buffy transported assembly, class `transported_source_effective` — declared owned, **counted 0.0**, readiness false | `agent_logs/local_buffy_qwen/assembly_handoff_02.md` lines **83 / 184 / 210** (UNTRACKED working file in `E:/PythonChimera`; verbatim extract preserved @ `8feea42a` `tools/monkey_campaign/agents/P02P03/receipts/buffy02_mass_lines.txt`; the "@43b599a7" pin = forearm-package-20260924 lane carrying the producing package). Producer outputs @ `43b599a7`: `forearm_package/baseline_snapshot/runs/actual_monkey_fit.json:52460` (`"all_transported": 17.039978509953905`), `tools/assembly_handoff/produce_inputs.py:109` | line 184: `validated_tissue_volume=0, counted_mass_kg=0.0, uncounted_mass_kg=17.039978509953905`; line 210: `components_with_validated_tissue_mass = 0`; readiness stays false | Assembly-handoff readiness accounting only (refuses mass ownership -> no manifest emitted) | **Deliberately separate** from the play/training body (map B06; decisions memo 20260924 section 2). Note: the "17.04" hits in `agent_logs/stand_survival*.json` are a parameter-sweep linspace (…16.98, 17.0, 17.02, **17.04**, 17.06…), NOT this mass — excluded from the lineage |

## 3. Which mass does the CURRENT CoT definition consume?

**13824.5 kg** — the slice membrane inventory — as quoted verbatim in section 1
(`acceptance.py:18,43@8294053b`; `RUNBOOK.md:76@8294053b`; `run_manifest.json:54@8294053b`).
The `work_J` numerator, however, is measured on the **10.038 kg** body:
`bat_sum = sum(bat[0..11])` over the walker's 12 drives (`walker_kernels.cuh:4963-4972@a62b286e`),
read as `rb[:,5]` (`train_first_skill.py:379@a62b286e`). Denominator body != numerator body.

## 4. Source/consumer matrix

| Source (definition) | slice engine membranes | slice movement law (`gait_verify.py`) | **trainer env dynamics** (`walker_kernels.cuh` mdl[OF_body_mass]) | `train_first_skill.py` record `work_J`/`distance_m` | **acceptance.py CoT denominator** | report_first_skill_checkpoint.py label | k-fill/deposit books | ankle adjudication | buffy assembly readiness |
|---|---|---|---|---|---|---|---|---|---|
| 13824.5 kg (membrane inventory) | DEFINES (mass_kg_ / LIMB_MASS_TARGET_KG) | DEFINES (MASS_KG) | not compiled in (verified) | no | **DEFINES M_BODY_KG** | DEFINES label constant | no | no | no |
| 10.038 kg (Oku walker assembly) | no | no | **DEFINES body_mass[]** | measures this body's work & distance | consumed-but-IGNORED (uses 13824.5) | no (wrong label) | demand anchor (OKU_MODEL_TOTAL_KG) | demand_source_animal_kg | no |
| 6.15 kg (T&K 1989 AF midpoint) | no | no | no | no | no | no | **DEFINES target-sum context** | game_band_midpoint_kg | no |
| 17.039978509953905 kg (Buffy transported) | no | no | no | no | no | no | no | no | **DEFINES uncounted_mass_kg (counted 0.0)** |

## 5. Mechanical consequence (derived, not measured on a run)

1. **Selection invariance**: every CoT on both policy and baseline sides carries the same
   1/13824.5 factor; `cot_band_ok` (median <= median + (max - median)) and the frozen
   ranking are invariant to the constant. Correcting the constant changes **no pass/fail
   decision** and requires **no retraining, no seed change, no threshold change**.
2. **Absolute-number wrongness**: any reported absolute CoT is understated by x1377.2166
   vs the physically honest work/(10.038 x d) of the simulated body. The label
   `work_J/(13824.5 kg x distance)` (`report_first_skill_checkpoint.py:120@a62b286e`)
   propagates a body identity that the run never simulated. Any literature comparison
   against that number (C11 walking envelope territory) would be invalid.
3. **Identity wrongness (the W04 axis)**: W04's done_when is "Exact dynamics, observations/
   actions, model revision, seeds and runbook identity are frozen and checked". The frozen
   runbook/acceptance names a body (membrane inventory) that is not the runbook's own step-1
   env body. The runbook identity is therefore not honestly checkable as written.

## 6. Reconciliation with prior W04-related receipts

- Prior P02P03 report (`tools/monkey_campaign/agents/P02P03/report.md` @ `8feea42a`, branch
  `monkey-play-20260924`) flagged acceptance.py M_BODY_KG as "UNRECONCILED ... Recorded, not
  resolved". **My findings CONFIRM that flag** and go further: I traced the full execution
  path (scene.json -> walker_model.body_mass -> mdl[OF_body_mass=90] -> kernel dynamics ->
  bat_sum -> rb[:,5] -> work_J), proved the mismatch constant 1377.2166x, proved the
  walker_env.dll does NOT compile the membrane header, and proved selection invariance.
  Lineages for 10.038 / 6.15 / 17.04 in that report are CONFIRMED at the cited sites.
- Bindings receipt (P02/W04, working file) — CONFIRMED on all four masses. Two pin
  corrections: (a) the frozen first_skill modules + RUNBOOK first EXIST at `8294053b`
  (lane `first-skill-prestage-20260922` tip), whose direct parent is `73f3a860`; `73f3a860`
  itself is the obs-split-channels tip and contains NO first_skill files — the RUNBOOK's own
  "@ 73f3a860" is the lane-base pin, so the bindings citation is a lane reference, not a
  file-bearing commit; (b) `assembly_handoff_02.md` is an UNTRACKED working file
  (`E:/PythonChimera/agent_logs/local_buffy_qwen/`), not tree-reachable at `43b599a7`; the
  verbatim lines survive only via the `8feea42a` receipt extract — verified byte-identical
  against the working file today.

## 7. Smallest correction proposal (no training seeds, thresholds, or source edits made by this card)

Per the RUNBOOK's own law ("Any change to a frozen field is a NEW registration, never an
amendment"), the W04 owner registers ONE new registration that:

1. `acceptance.py` line 18: `M_BODY_KG = 10.038  # the compiled gait_scene assembly (Oku 2021 Table 1; weight 98.4391527 N)` —
   stronger form: read the denominator from the same compiled scene bundle the env consumed
   (`assembly_mass_kg`), structurally binding denominator to training body.
2. `run_manifest.json` `hard_conditions.cot_within_band.definition`: `m_body = 10.038 kg
   (the compiled gait_scene assembly)`; restate the manifest sha (trainer sha-asserts it).
3. `RUNBOOK.md` step 5: `CoT = E_ledger/(10.038 kg x d_reached)`.
4. `tools/science_funnel/first_skill/tests/test_first_skill_prestage.py:70` assertion string.
5. `tools/report_first_skill_checkpoint.py:120` label.

Zero effect on any acceptance decision (scale-invariant, section 5.1); reported CoT values
rescale by x1377.2166. This simultaneously discharges G01's dependency note ("Grip load
feasibility must bind to the actual certified body or an explicitly reconciled source model").

## 8. Escalation

No AMBIGUITY escalation: the expression and the training body are each unambiguous; the
mismatch is proven. The lead decision required is only the AUTHORIZATION of the section-7
new registration (frozen-field law forbids this card from amending), plus choosing literal
10.038 vs scene-derived binding (recommendation: scene-derived, so the class of defect
cannot recur).

## 9. Falsifier self-check

- "a conclusion using masses from different lineages as interchangeable" — NOT FIRED: the
  report keeps all four lineages separate with distinct semantic identities; every
  cross-mass statement is a mismatch claim with the ratio derived, never an exchange.
- "claiming W04 ready while its denominator/body binding is unresolved" — NOT FIRED: the
  verdict is NO (not bound); W04 readiness on this axis is explicitly withheld.
- Method discipline: every quoted number carries file+line+commit; literals enumerated via
  `git log --all -G` pickaxe across all 607 refs / 3864 commits PLUS line-level `git grep`
  at pinned revisions; derived numbers recomputed (ratio 1377.2166; 13.824536x1000;
  13.824598 band sum; 8.184+2x0.927; 98.4391527 N; 6.15 midpoint; 1.135894 k-fill target;
  10.037998 scene carve).

## 10. Remaining gates

1. W04 owner: register the section-7 correction (new registration) BEFORE any first-skill
   training run consumes the frozen runbook (the trainer reads the manifest sha).
2. G01: re-point its W04 dependency note to the reconciled denominator after registration.
3. Unaffected but adjacent: W03's named items (anchor-drift v1/v2 decision; tick-40/41
   contact-residual knife; clean-window C3 bars) are OUT of this card's scope and untouched.
