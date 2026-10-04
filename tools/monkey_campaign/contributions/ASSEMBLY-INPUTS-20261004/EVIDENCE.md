# EVIDENCE.md — wk-assembly-inputs (phase 1 chain stop)

Lane: `E:/ChimeraWork/monkey-coordination/assembly-inputs/` (sole write scope). Worker:
wk-assembly-inputs (chimera-worker under the main Lieutenant). Date: 2026-10-03.
NO_WORKTREES.md obeyed: no worktrees, no clones, NO runner jobs (phase 1 = inventory +
acquisition plan only). All verification reads were read-only against `E:/PythonChimera`
(shared repo + working tree), the shared git object database (`git cat-file`/`git ls-tree`
against commits `43b599a7` / `d2c23741` / `cd2edceb` — the NO_WORKTREES source path), and the
coordination/evidence stores. Every sha256 below was recomputed this session with
`C:\Python314\python.exe` unless marked (blob = git blob id, sha1 content identity).

This file records the EVIDENCE for the assigned RT-1 named prerequisite: the
ASSEMBLY_HANDOFF packet inputs (material-volume / mechanical-requirements / frames /
root-frame / ownership evidence the product runtime needs before a physical body can
exist). The W03 10.038 kg SCENE lineage belongs to mass-reg/lineage-verify/assembly-identity;
this lane owns the RUNTIME ASSEMBLY body line (different objects; no duplication).

## 0. This lane's artifacts (sha256)

| artifact | role | sha256 |
|---|---|---|
| `REQUIREMENTS_TABLE.md` | the requirements table (per-checker enumeration + declared absences) | `fa33a8dea8eade7bb8a066b9e76fee09996b979a48e5c8978f43c73214c6808a` |
| `PROVENANCE_SWEEP.md` | what exists today, where + gap list with owners + findings P-1/P-3 | `c12cd5233b7e3c0533fad15bf9d4cdb888a47d6225e0706e736a77fbaaca83bc` |
| `ACQUISITION_PLAN.md` | per-gap derived/synthetic-declared/blocked plan + falsifiers AF-1..AF-7 | `12722a102cbb163b1f464637e952172ebcabec1719d823530a7ed863f78b3fa6` |
| `DELIVERABLE_SPEC.md` | inputs/ directory design + READY state + PREREG DRAFT (section 4) for the authoring run | `477607598325b418c06a46c55285c627be838a97d31e51b8b266413906402bdc` |
| `EVIDENCE.md` | this file (self-hash impossible; excluded) | (this file) |

## 1. The packet under audit (recomputed this session)

| artifact | sha256 / identity |
|---|---|
| `E:/PythonChimera/tools/assembly_handoff/out/real_packet_readiness.json` | `4f24571bf6f14cd3032af263adeaa649a5a02e4bc3bc7c74deeba6f578a69f3b` (STALE pre-fix report — finding P-1) |
| `tools/assembly_handoff/inputs/` | ABSENT from tree (checked; both required inputs exists:false) |
| `.tmp/anatomy_compiler/runs/actual_monkey_fit.json` | `a447555069748d7fe421ff2a4ddeaa108729924ae088478741c86c38c3880937` |
| `.tmp/anatomy_compiler/runs/attachment_candidates.json` | `854f70976deb10264f052a8dafc3247c9bf6bf03761748e343329ce30e1032ae` |
| `.tmp/anatomy_compiler/runs/admission_actual_monkey.json` | `833ca65b282eab83180bdbe65bbd8f934924fdd1416c8058d510e5481d86b4ad` |
| `tools/assembly_handoff/__pycache__/assembly_handoff.cpython-314.pyc` | `89901e0243635763bab23abfcfaa0b86a29862b92b1503ded56d6e36fe8bf819` |
| `tools/assembly_handoff/__pycache__/produce_inputs.cpython-314.pyc` | `6580adc706a5dc8b9d34cf83949d929ea26cdb0c061b191b41812da04a5dde5e` |
| `tools/assembly_handoff/__pycache__/real_packet_readiness.cpython-314.pyc` | `585de4d088a3ac46863116df15e6053281227eabd8a2e357765dcf34ece55294` |
| `tools/assembly_handoff/__pycache__/run_fixtures.cpython-314.pyc` | `be12ea5bfd2a5ecba2adccbd8e891fff6faf79a59c9fe9b68719c42e69b7c533` |
| `tools/assembly_handoff/out/complete_assembly_manifest.json` (READY fixture output) | `67d7842e9f2bff14414d7f27e3099dc77c41f7cff6e78d6f8aaa06b4d6239af4` |

## 2. Recovery identities in the shared object database (read-only; application via publication owner)

Commit `43b599a7c1f11e789cd414b40d7305b9be05066d` (2026-09-24 13:59:56 -0500; branches
`forearm-package-20260924`, `remotes/origin/census/wk-clonecensus/verified-set`,
`remotes/origin/census/wk-q2-migration/verified-set`):

| path | blob | content sha256 |
|---|---|---|
| tools/assembly_handoff/assembly_handoff.py | `0dd7077c5ad4ceae93a11a05bc7d52d69cf3edcc` | `1a0615ff043cc6465c786ab50d1ae1c68a5854a5e6fb922608ac05ddd8974eab` |
| tools/assembly_handoff/produce_inputs.py | `7365aa043d158e6fc73225dd3bec87e37781848f` | `9ac51d2607616d8a14915865bd2dfa27d504546495cb237d04cfbb2529700774` |
| tools/assembly_handoff/real_packet_readiness.py | `634c431e22b6d15400a3760e44171548e56b2569` | `aaaada16d77e571326fff28db89e504aecfd632c2d323b11dc1f511805bd6d5d` |
| tools/assembly_handoff/run_fixtures.py | `ca8d0ecd146264144dc6a06b60042aecd9619f04` | `613df590d1791004c2e284fbe76dc62691a1bbc64ef09e8bea68159f27cda3cb` |
| tools/assembly_handoff/DERIVATION.md | `6c64797629afb0f938fed10475ca99d4b5541852` | (git blob identity; sha1 in-object) |
| tools/assembly_handoff/inputs/ownership_bindings.json | `c6c7006b819fde49bfc7bc0308907ac0bce02668` | `364fb4238c8b92c8afd477b05b6e4b52fbac7d6bc5fa79136853d45611ab735b` |
| tools/assembly_handoff/inputs/material_volume_document.cannot_produce.json | `e3e45869fcb977643236aa363ddb7eb635f60d3b` | `912b72fcc2f2659a956a0d14d12ee8728db83787ef8c9580d1e36a44536a7c43` |
| tools/assembly_handoff/inputs/mechanical_requirements.cannot_produce.json | `8c13c1c5e48178ab0e8e1b2d258caa7ae4f11448` | `639a4a4b7ab6039ad61a23aced8d838f01ee744d44efcb042e01d0303cfe40b6` |
| tools/assembly_handoff/inputs/prepared_root_frame_definition.json | `f11ff153084eeeb16f2bdbe83b4e862374c0028b` | `58b36024f26abd9914c83fbbce43f693694173412719a2a39ca493c862d2f57b` |
| tools/assembly_handoff/fixtures/ (incl. requirements_complete.json, material_volume_synthetic.json blob `ac54c235`) | tree `a7731098` | (per-blob at ls-tree) |

`tools/material_volume.py` (adapter upstream): blob `3d46b030e75d6200a1764aadf72d81be9942bcdc`
at commits `d2c23741` and `cd2edceb` (branches `monkey-play-20260924`,
`I-U07-TRACE-correction-fsum-overflow`, `remotes/origin/census/wk-clonecensus/verified-set`).
Present-in-tree gate: `tools/finite_area_attachment/finite_area_attachment.py`
`33ee530653daf8673f582763f986faa679bf1554bdc5a1da7ae7426a4dfb802a`; dependency_pin.json
`613567d20fccc0cff4848f6f37cbbbbaaa8b9d4f1c1f0e1ce1b9e438c2423e87`.

## 3. Law + lane-record carriers (recomputed this session)

| artifact | sha256 |
|---|---|
| `E:/PythonChimera/tools/monkey_campaign/NO_WORKTREES.md` | `7d3fe1029f727b95ff2c832b06a89b3bac40f59e14993440255636218645f433` |
| `assembly-identity/ASSEMBLY_IDENTITY.md` (the "record 2ab248bd") | `2ab248bda4db799685a5be9f446bb3e731a47b40b9db1108072cce18bafad035` |
| `lineage-verify/REPORT.md` (LV-1..LV-5; W03 verdict) | `b7801ce08b53f9f16edbbf67607406e48cdd919d95b44fc6f7f5055e3fbe384f` (== the evidence-package citation) |
| `lineage-verify/EVIDENCE.md` | `e0dee3afe0bf4f922d169886ae4460f4df92f612411fc1f7d1c888483d5393a3` |
| `runtime-slice/EVIDENCE.md` (RT-1 owner request) | `a91917bdfc94c8a587d754f82ef71d80191efb69077ee1bb712bbf63057630f0` |
| `runtime-slice/PREREG_DRAFT.md` | `5233067b5f5a430d1c44d0d86db52a5621e15734b21b3c99b31a6674c8a76b41` |
| `runtime-slice/EVIDENCE_JOIN_SPEC.md` | `ea73c8c300aca564993b19354f1d4a85da438507eafbfc3996752ba9fb618c15` |
| `evidence-package/PACKAGE_SPEC.md` (LV-1 emission-receipt law) | `54325a3d77baa0b6a728102ce94129e701c5b39bf48a06847094f66bffe5e053` |
| `b07-prereqs/numerical/mass_audit_receipt.json` (17.04 kg decomposition, bit-exact) | `3aea85bc7e07ebceb3d1f6f9e969fc9af14edc198620d28ef955da619d351922` |
| `evidence-store/MAT2-D-MASSREG/numerical/mass_register.json` | `61fb79b1bf2df8c5e1a5b1bff2ab1c4f41700de25bc7f1a114cbc78fe693cc7a` |
| `mass-reg/MASS_REG.md` | `f57d5e6b6719b54294e3aeb76193f3c48ee22d847dd86b645e1293b3a39f7dfd` |
| `mass-reg/mass_reg_output.json` | `db716fa2467ced72bcc830f371d25b23691418b686b3e73519f74d8ecf463d65` |
| `mass-reg/mass_reg.py` | `7e48683c1d975eb6c1e314f4c8f094ef909dd658d3c59eea96775cd6770a4271` |
| Cheng M2-8 `E:/ChimeraWork/research-data/20260929/cheng_tables/M2-8_regressions.csv` | `b185ee8e98b6e663defed0abd4d004fec053eb6417e027c54801070cd894ec22` |
| sealed osim `E:/ChimeraWork/research-data/20260929/atlas/_tip_monkeyArm_current.osim` (hand 0.049 kg anchor) | `4148aee2c8dda1dcb0918496ad7c5e1adcf4ebabde0a68a3e0dc67faec67b895` |
| Isler 2006 extraction CSV `E:/ChimeraWork/research-data/20260929/lit-inertia-bmd/extraction/isler2006_table3_segment_inertials.csv` | `4ac0b65cbfa278b2f0d197b52d0f871fdbfccb698872e3720ef2e915125cbaa8` |
| Isler retrieval receipt `.../lit-inertia-bmd/RETRIEVAL.md` | `fdc2c0b972814f292a6582e055d33233893f96359731ca6ea78133a285c0a5e7` |

## 4. Findings (load-bearing, each with its evidence row above)

- **P-1 stale report:** the on-disk readiness report binds PRE-FIX input revisions
  (`67116710`/`5efaf0f2`/`c68abaad`/`5cdc83cb`); the committed post-fix inputs hash
  `364fb423`/`912b72fc`/`639a4a4b`/`58b36024`. Any future run regenerates the report and
  records the new manifest digest; the stale digest `504deec6...` binds only the pre-fix bundle.
- **P-2 recoverability:** the full toolchain + authored inputs + READY fixtures + the
  material-volume compiler are all reachable in the shared object database — the absence of
  `tools/assembly_handoff/inputs/` from the HEAD tree is a recovery/replay gap, not an evidence loss.
- **P-3 store observation:** `evidence-store/MAT2-W03/scene_out/scene.json` (cited path) not found
  this session; W03 scene identity stays bound by the lane records + stdout anchor; not this packet's
  dependency. Flagged for the store owner.
- **P-4 ownership answer:** no existing lane owns the packet inputs (verified against mass-reg,
  lineage-verify, assembly-identity records); RT-1's requested owner is THIS lane.

## 5. Mass reconciliation (the 17.04 vs 10.04 answer, by enumeration)

Two disjoint objects; never averaged:
- **17.039978509953905 kg** = the assembly line's own transported matter (Buffy 02; 9 det-scaled
  segments; pelvis 11.777 root-reference + 5.262978509953907 under a recorded uniform-density-scale
  assumption; admitted 0.0) — counted nowhere BY DESIGN (counts_toward_component_mass=false),
  which is exactly the readiness report's `uncounted_mass_kg`.
- **10.037998 kg** = the sealed W03 scene-line (14 bodies, Oku-derived; the only sealed dynamics body).
- Name overlap (pelvis, humerus/upperarm, radius/forearm, femur/thigh, tibia/shank) is NOT shared
  matter: different source models (36.3256 kg source .osim vs Oku Table 1), different scaling laws
  (|det D| vs carve arithmetic), different partitions (the scene forearm strut 0.1323 carries the
  whole distal chain incl. the 0.049 kg osim hand; the assembly radius is 0.00794446 det-scaled).
- Full enumeration in PROVENANCE_SWEEP section 1.4; subsumption law (B03 bones) in ACQUISITION_PLAN A4.

## 6. What this lane did NOT do (honest-absent)

- No runner job (no seal/run; phase 1). No recovery applied to the tree (publication owner's act).
- No frames authored, no attachments authored, no density declared, no material-volume document
  produced. No scene-line mass imported anywhere. No fresh readiness report generated (P-1 replay
  awaits the prereg + recovery path). The two measurement debts (macaque wet-tissue density;
  tendon-bone couple stiffness) remain NAMED and UNDISCHARGED.
- Commands run (all read-only): git rev-parse/log/ls-tree/cat-file (object database reads),
  python JSON/pyc-constant extraction + sha256 recomputation, filesystem existence checks, lane
  record reads. No source or sealed byte mutated anywhere.

---

# PHASE 2 ADDENDUM (2026-10-03) — recovery + sealed replay + authoring

## P2.0 Prereg and its amendments

`PREREG_PHASE2.md` (written before the first run; sha below) + Amendments 1-3, each recorded
BEFORE the next run, each naming its root cause. Every prediction miss was stop-and-report,
root-caused, and never silently absorbed.

| artifact | sha256 |
|---|---|
| `PREREG_PHASE2.md` (incl. amendments 1-3) | recomputed at report time (see section P2.4) |
| `_recovery/RESTORED_BYTES.json` (23 restored files, blob+sha+bytes each) | recomputed at report time |
| `_recovery/AUTHORED_APPLIED.json` (byte/content/canonical identities of the applied authored docs) | recomputed at report time |

## P2.1 Restored-bytes table (delegated recovery; ADD-ONLY proof)

All 23 files restored from the shared object database at commit `43b599a7` (+ blob `3d46b030` for
`tools/material_volume.py`), staged in `_recovery/` first, hash-verified against the object DB
BEFORE and AFTER the tree write. `git status` after recovery: ONLY untracked additions
(`?? tools/assembly_handoff/`, `?? tools/material_volume.py`); zero tracked-file modifications
(the pre-existing dirty state is untouched). Full table: `_recovery/RESTORED_BYTES.json`
(generated inside the verified script; entries match section 2 of this file).

| path | blob | content sha256 (LF bytes) |
|---|---|---|
| tools/assembly_handoff/assembly_handoff.py | `0dd7077c5ad4ceae93a11a05bc7d52d69cf3edcc` | `1a0615ff043cc6465c786ab50d1ae1c68a5854a5e6fb922608ac05ddd8974eab` |
| tools/assembly_handoff/produce_inputs.py | `7365aa043d158e6fc73225dd3bec87e37781848f` | `9ac51d2607616d8a14915865bd2dfa27d504546495cb237d04cfbb2529700774` |
| tools/assembly_handoff/real_packet_readiness.py | `634c431e22b6d15400a3760e44171548e56b2569` | `aaaada16d77e571326fff28db89e504aecfd632c2d323b11dc1f511805bd6d5d` |
| tools/assembly_handoff/run_fixtures.py | `ca8d0ecd146264144dc6a06b60042aecd9619f04` | `613df590d1791004c2e284fbe76dc62691a1bbc64ef09e8bea68159f27cda3cb` |
| tools/assembly_handoff/DERIVATION.md | `6c64797629afb0f938fed10475ca99d4b5541852` | `3e5e48d0b849cad381a570376aa22b6a2d6325a9da54916506a5bc3553f033fc` |
| tools/assembly_handoff/inputs/ownership_bindings.json (rev 1) | `c6c7006b819fde49bfc7bc0308907ac0bce02668` | `364fb4238c8b92c8afd477b05b6e4b52fbac7d6bc5fa79136853d45611ab735b` |
| tools/assembly_handoff/inputs/material_volume_document.cannot_produce.json | `e3e45869fcb977643236aa363ddb7eb635f60d3b` | `912b72fcc2f2659a956a0d14d12ee8728db83787ef8c9580d1e36a44536a7c43` |
| tools/assembly_handoff/inputs/mechanical_requirements.cannot_produce.json | `8c13c1c5e48178ab0e8e1b2d258caa7ae4f11448` | `639a4a4b7ab6039ad61a23aced8d838f01ee744d44efcb042e01d0303cfe40b6` |
| tools/assembly_handoff/inputs/prepared_root_frame_definition.json | `f11ff153084eeeb16f2bdbe83b4e862374c0028b` | `58b36024f26abd9914c83fbbce43f693694173412719a2a39ca493c862d2f57b` |
| tools/material_volume.py | `3d46b030e75d6200a1764aadf72d81be9942bcdc` | `a4eb96e6d59c51d9c673ad6df8675639cd0b25a1652b0f6f5203de737a4327ec` |
| tools/assembly_handoff/fixtures/** (13 files) | per-file blobs at 43b599a7 | in RESTORED_BYTES.json (e.g. requirements_complete.json `6e67c1944fc5514ed89aaa8469e975c2936a92c1e545512fafe54147558ed444`) |

## P2.2 Sealed run receipts (all slot 2; interpreter C:\Python314 3.14.3)

| # | job | sealed manifest sha256 | exit | outcome |
|---|---|---|---|---|
| 1 | `3925715383ca47ad9591d8bf4d02f85b` | `5ac2c576f3a422e5e046d003893ab8b4308130c5baa9e376842e910eba3c522e` | 1 | stage-1 byte prediction MISS -> root-caused (CRLF/LF); driver KeyError; amendments 1 |
| 2 | `f1c86846d6eb410bae42b3f316d88bd4` | `45b75e10cc2e1feec18236fd6d5a0fec1aebc518f61debaa762bb0fcba105a0c` | 1 | stages 1-2 ALL PASS; stage 3 fixture crash -> compiler omitted (my error); amendment 2 |
| 3 | `304144ef524842eab9da6deafb56209a` | `14448b8d070e1df689461a813ca3a5d91e3ddca092dfcbcd60e225a54ee3080d` | 4 | 33/36 PASS; stage-5 seg-pelvis frame + frame-count constant wrong (my error); amendment 3 |
| 4 | `763a174e8a5c462db683385404913bf6` | `9bd2dbca9796e99397873161c14aeab03d2b58b7973c02cbaa8393025e095650` | 0 | **PASSED, cleanup_verified=true, 36/36 checks** — result `E:/ChimeraWork/task-runner/results/763a174e8a5c462db683385404913bf6` |

Seal lineage note (SGT review housekeeping): a SECOND, never-run seal of `_pkg2` —
`_pkg2/sealed/f5dc44f3f1f84876b60601553bfcd943` (manifest sha256 `56a1ec4d...`)
— existed from a duplicate seal invocation, was referenced by NO run receipt, and was
DELETED 2026-10-03 during the SGT revision (zero-references check recorded in the repair
script output); the executed run-1 seal `7db08f28998e400192cab9aa26aaf12f` remains the only
`_pkg2` seal. All other seals (`_pkg3/3aa995b6`, `_pkg4/45aa372d`, `_pkg5/eb53481c`) were
executed exactly once each.

## P2.3 The verdicts (the chain stop 2 substance)

- **Replay verdict (A1/P-1 REVISED):** the committed producer deterministically reproduces the
  on-disk readiness report's exact input hashes (`67116710` / `5efaf0f2` / `c68abaad` / `5cdc83cb`);
  the committed inputs are the LF normalization of the SAME content (canonical diff 0 lines).
  There is NO revision skew anywhere. The on-disk report's own manifest digest (`504deec6...`) is
  bundle-layout-sensitive and was never reproduced; the replay digests are RECORDED:
  `9efa7611efffec7bf213caaf3122cac3e407f2e7c0618e33668c75b7d6156bcc` (run 2 layout),
  `eabb99e10fffe2c9863beb48483948955535d240d586bf1c931706b0418c02ea` (run 4 layout: gate +
  compiler present). Substantive replay state CONFIRMED: ready FALSE, counted 0.0,
  uncounted 17.039978509953905, census {8,9,9,3,2,1}, policy block all-false, no soundness trip.
- **READY-SYNTHETIC (A5):** run_fixtures exit 0 — complete synthetic assembly ready=TRUE with
  lambda_min = 32.0 N*m/rad; all refusal/negative controls behave as asserted. The checker CAN say
  ready when everything is authored.
- **Authoring (A2+A3):** authored artifacts APPLIED to the tree at the canonical paths:
  - `tools/assembly_handoff/inputs/ownership_bindings.json` REVISION 2 — tree bytes sha256
    `51cce1b23572060d5586a0a08a3bea9d5063388ac6b9ed1530020c0f8005cb38` (CRLF, 8,815 B; LF normalization 8,610 B);
    LF content sha `9dbe7fc6bb2783d05b01b05872c61865ce03d7f881fac0578b3e18eb72d39c4d`;
    parent rev-1 content: the document's `_revision.parent_content_sha256` records the CRLF twin
    `6711671030b914af97a79b97bef0cf290eac301acee995a14b80286a7544d4a0` of the canonically identical
    LF rev-1 content `364fb4238c8b92c8afd477b05b6e4b52fbac7d6bc5fa79136853d45611ab735b` (newline
    law applied to the prereg constant); 17 components (9 seg + 8 zero-mass membrane bond patches),
    9 claims UNCHANGED (all counts_toward_component_mass=false).
  - `tools/assembly_handoff/inputs/mechanical_requirements.json` NEW — tree bytes sha256
    `110d486ab418d1d8f287e3ac44a86802919b6f770eae04a176bfd33d5b7f817e` (CRLF, 22,175 B; LF normalization 21,391 B);
    LF content sha `ab1d7a1d58f65136ef5c61b2b19dd1a314e47376229e6104ff047facdc666768`;
    10 authored frames (root with the six authored values + 9 segment frames derived from the
    packet's fitted_origin/frame_basis) + 8 attachments (anchors derived by the packet's own
    fitted_pos_local law, round-trip verified; weights/patch declared; kappa_areal_n_m3 +
    k_couple_min_n_m_per_rad + stiffness_kbar HONESTLY ABSENT).
  - Round-trip proof: max |computed q − packet fitted_pos_local| = 9.14e-10 m (packet print
    precision); max global reconstruction error 2.78e-17 m (8/8 ports).
- **Readiness state (A4/A5):** the authored-state manifest
  (digest `26721b8ac8f8c8301fb73e40c8e15f9f313223ccb89a580f7a6b08c75f32324b`) reports
  **dynamics_trial_ready = FALSE** — the honest intermediate:
  census {attachment_not_qualified 8, attachment_parameter_missing 24, attachment_port_unqualified 8,
  component_mass_undecided 9, frame_observed_not_bound 3 (notes), required_input_absent 1
  (material_volume_document — the density debt, named, not discharged)};
  checks: every_authored_frame_bound TRUE (10/10), no_unbound_frame_is_referenced TRUE,
  no_matter_unowned TRUE, units_consistent TRUE; counted 0.0 / uncounted 17.039978509953905
  (unchanged); the stiffness gate was NEVER REACHED (8x incomplete_parameters_missing,
  gate_result null). The on-disk Sep-24 report was NOT overwritten (preserved evidence); the
  authored-state report lives in the sealed job's artifacts.
- **READY-SYNTHETIC vs READY-REAL verdict (A5):** READY-SYNTHETIC = PROVEN (fixtures).
- **THE F2 VERDICT (the load-bearing one):** no ready-on-unvalidated-density refutation
  event occurred. READY-REAL stays honestly FALSE and GATED on the two campaign measurement
  debts (macaque wet-tissue density; tendon-bone areal/couple stiffness). A ready verdict on
  unvalidated density WOULD be the DERIVATION F2 refutation event; it did not occur and cannot
  occur through this lane.

## P2.4 Falsifier outcomes

| ID | outcome | evidence |
|---|---|---|
| AF-1 no ready while required input absent | CLEAR | runs 2-4: ready FALSE in every real-packet manifest; no soundness_violation anywhere; fixtures ready TRUE only on the complete synthetic bundle |
| AF-2 no validated mass on unvalidated density | CLEAR | 0 components validated in all real-packet manifests; every_component_has_validated_tissue_mass false; the 9 claims stay transported/root-reference |
| AF-3 no waypoint covered | CLEAR | authored attachments reference ONLY the 8 candidate_port sites; 24 waypoints untouched; no waypoint_promoted_to_attachment anywhere |
| AF-4 no double counting; B03 subsume law | CLEAR | one binding per claim, all counts=false; no counted row added anywhere; the authored documents add zero mass claims |
| AF-5 no counted mass without hashed source | CLEAR | counted_mass_kg = 0.0 in every real-packet manifest |
| AF-6 no cross-line averaging | CLEAR | stage-5 check `no_scene_mass_imported` PASS — authored documents carry no Oku/scene constants; uncounted total unchanged at 17.039978509953905 |
| AF-7 no replay/derivation drift | FIRED ONCE, ROOT-CAUSED, CLOSED | run 1 byte miss = CRLF/LF serialization (content canonically identical, diff 0 lines); runs 2-4 deterministic; anchor round-trip <= 9.14e-10 m |

## P2.5 Durable laws discovered (for the Lieutenant's consolidation)

1. **Newline law:** the producer/fixtures write CRLF on Windows; the committed inputs are LF
   normalizations of identical content. ALL hash comparisons between producer output and committed
   bytes must be canonical-form aware. The committed rev-1 inputs and the report's recorded hashes
   are ONE consistent state (finding P-1 of phase 1 is REVISED accordingly).
2. **Pelvis law:** the pelvis is NOT a segment in the anatomy packet; it is the referenced-but-
   unsegmented natural root. Component seg-pelvis binds to the authored assembly root itself.
3. **Observed-frame law:** observed packet frames (anatomy target, candidates bodies) can NEVER
   bind — the adapter records them as observed_unbound notes by design; only authored frames bind,
   and only through the single authored root.
4. **Fixture dependency law:** run_fixtures requires the material-volume compiler upstream
   (fixture claims are compiler-materialized); any fixture rerun without `tools/material_volume.py`
   refuses unknown_claim_reference.

## P2.6 Collaborator-wave routings folded in (2026-10-03, SGT re-issue)

Both routings arrived through the Lieutenant's re-issue; this lane owns the packet inputs, so both
ride this record. TEXT-ONLY round: the recovered wrapper source, the Sep-24 preserved report, and
every sealed artifact are byte-unchanged (wrapper re-verified `aaaada16...` this session).

### (1) Root-frame coordination ruling (collaborator record `12f0cfb5`, relayed identifier)

- CITATION AS COORDINATION REFERENCE: the collaborator wave's authorized synthetic root-frame
  values are EXACTLY what this lane authored. Programmatic match recorded this session against the
  applied `tools/assembly_handoff/inputs/mechanical_requirements.json` frames[0]:
  frame_id `frame:assembly-root`; parent_frame_id null; coordinate_unit m; scale_to_m 1.0;
  origin_m [0,0,0]; basis_rows identity; handedness right — the identity basis is +X right /
  +Y up / +Z anterior under the packet's own coordinate conventions
  (right [1,0,0], up [0,1,0], anterior [0,0,1], right-handed; packet sha `a4475550...`).
  The ruling record itself was NOT found on this host's searched paths (monkey-coordination,
  E:/Chimera/parallel-budget-probe); the citation is by the routing's identifier `12f0cfb5` and the
  values were verified against the authored document, not against a local copy of the ruling.
- **DECLARED VIOLATION `SYNTHETIC_ASSEMBLY_ROOT_PLACEMENT`** (added to this record; cross-reference
  the authored document's `_root_placement_decision` field, which carries the same declaration and
  its violation observables): the assembly root placement is a SYNTHETIC, AUTHORIZED placement —
  its uncertainty stays VISIBLE in every manifest that consumes it; it is NEVER a measured landmark
  and never promoted to one.
- SCOPE LINE (binding): the ruling supplies ONLY the root fields. NOTHING synthetic is promoted
  toward qualification by it: counted mass stays 0.0, the density and stiffness debts stay named,
  and the F2 verdict stands (no ready-on-unvalidated-density refutation event occurred; READY-REAL
  remains honestly FALSE).

### (2) Readiness-wrapper staleness (collaborator record `39f33b27`, relayed identifier) — NAMED FINDING W-RPR-1

- EVIDENCE (re-verified this session): the wrapper `tools/assembly_handoff/real_packet_readiness.py`
  (content sha `aaaada16d77e571326fff28db89e504aecfd632c2d323b11dc1f511805bd6d5d`, blob `634c431e`
  at `43b599a7`; tree copy byte-identical, 16,518 B) special-cases ownership presence at lines
  104-111 (`if OWNERSHIP_INPUT.is_file():` admit, else declare absent) but lines 113-117 append
  `material_volume_document` and `mechanical_requirements` as declared ABSENT **UNCONDITIONALLY** —
  even when the canonical JSONs exist at `INPUTS/<role>.json`.
- THE TRAP IS NOW LIVE: this lane's authored `mechanical_requirements.json` EXISTS at the canonical
  path, so any tree rerun of the wrapper would report `required_input_absent(mechanical_requirements)`
  DESPITE presence — repeat staleness, exactly the collaborator finding.
- RECONCILIATION CHOSEN: NAMED FINDING with the wrapper's OWN DEBT (the alternative — editing the
  recovered hash-pinned source — would break the restored-bytes provenance and is a publication-path
  act, not a lane act). The Sep-24 preserved report `out/real_packet_readiness.json` was NOT touched.
  The wrapper's own debt, named: its example bundle builder predates the authored inputs and needs
  the lines 113-117 loop made presence-conditional (mirror lines 104-111) plus its comment block
  (lines 100-103) updated; owner of any such fix: the publication path as a scoped proposal on top
  of blob `634c431e`.
- LAWFUL CURRENT PATH (no wrapper edit needed): the direct-bundle class this lane already executed
  in sealed run `763a174e8a5c462db683385404913bf6` — the bundle admits the canonical authored
  documents by path and the adapter core (`assembly_handoff.py`, which has NO such special-case)
  reports the true authored state (manifest digest `26721b8ac8f8c8301fb73e40c8e15f9f313223ccb89a580f7a6b08c75f32324b`,
  honest FALSE). Until the wrapper fix is published, wrapper output MUST NOT be cited as the
  authored-state readiness; the stage-5 sealed report is the citation of record.
