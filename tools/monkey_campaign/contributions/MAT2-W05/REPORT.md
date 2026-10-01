# REPORT — MAT2-W05 the frozen walk1m-r1 runbook, executed on all three prescribed seeds

Generated from the receipts; no hand-transcribed numbers (P2/P3). Profile: records (offline); numerical evidence required; no camera record (G4/G8 disclosed NOT-APPLICABLE — no image is evidence for this card).

## Identity

- Card MAT2-W05 (planning id W05), agent `wk-w05-runbook`, attempt `ce1576896a454f109a52de3a136c5117`.
- Criteria sha256 `8ce5e298aad11b2f1a6efa5e5d5b59ada4c5d436e9ca21e08415da55346ea2c4` (join == registry read-only re-read; card state at run time: OPEN, registry revision 1604).
- Base: `ced16473` (the MAT2-W04 merge, PR #295).
- Preregistration sha256 `260c6d53e66c79689e95b5f880c1f6828f5316d4d7d6e172132296137d3f1c2a`; addendum 1 sha256 `a257826f26936f4bf388d140ff7158eac851a0c9dae4ca01a9db3a6abdd886d7` (committed separately, BEFORE any experiment — the M03/P04 law).
- Runbook `walk1m-r1` (schema chimera.w05_runbook.v1), document sha256 `b8dbd4ede862aff425764a2c1a4268ea4d81c9d7d4f2ea9ae4ef2ff317529991`.
- Upstream freeze: the W04 freeze manifest (sha `be632ffc85865515285f3d622a09882a3180a43101027914f1ed3408496f5d29`) froze the seeds/runbook slot at SLOT SHAPE with values null (TC-10 / FC-4 / LT ruling BQ-3); the governing laws bound there are K01 and P04.

## The TC-10 slot fill (this card's values)

- `runbook_id`: **walk1m-r1**
- `seeds`: [20260919, 20260920, 20260921] — the three registered closed-loop corpus seeds of upgrade_gate_20260920/registered_cases_v1 (suite registered cases sha `d6fa74bd89d14f2e49b4d196a974e00f7a19d167e516122e790f5b564937dea7`).
- `acceptance_criteria`: the frozen object in `w05_freeze_fill.json` (execution-integrity gates, failure retention, termination codes, held-out checks, certificate mismatch rejection, and the success metrics reported per seed without cherry-picking).
- Decisions per seed: 1000000 (2000 iterations x 2 antithetic evaluations x 250 decisions), i.e. 15000000 ticks per seed at 300 Hz; the runbook bound "approximately 1M-decision" is exact at 1000000.

## Prediction outcomes (registered in the prereg BEFORE the run)

- P1 baseline exactness: true — all three anchors reproduced EXACTLY (trajectory, initial snapshot, final state).
- P2 per-seed integrity: true.
- P3 training signal (per seed, recorded NOT gated): seed 20260919 improved=false; seed 20260920 improved=false; seed 20260921 improved=false.
- P4 gate mechanics: trained tuple BLOCK, frozen relation ALLOW, foreign build BLOCK.

## Retained baseline arm (the certified line, unchanged)

The sealed certified reference line re-executed through the UNMODIFIED pinned machinery: frozen P3 policy closed loop, build N, seed 20260920, 900 ticks.
- final_state_sha256: EXACT (`b9a7fb99c32013e2e993c8c81a88b0abea2d5e0ce19e010e344b5d4e8cb27d72`).
- initial_snapshot_sha256: EXACT (`11ac68cfb2c237445902b65bd1ee3bd228d915e1009d01d1cd16a3e5aab13346`).
- trajectory_sha256: EXACT (`cd4944d99be1270951926be53859828a6b0aef21d32d6551f68e78d504ef6c7a`).
- Recipe equivalence (controller-change proof): the trainable policy class with the FROZEN bundle weights reproduced the frozen NumpyPolicy applied bytes tick-for-tick: true (trajectory sha `cd4944d99be1270951926be53859828a6b0aef21d32d6551f68e78d504ef6c7a`).

## The three seed outcomes (verbatim; failures retained)

### Seed 20260919

- status: **EXECUTED_COMPLETED**
- decisions executed: 1000000 of 1000000 declared; iterations 2000; ticks 15000000.
- SPSA constants (frozen in the prereg, never tuned): c=0.05, a_s=0.01, parameter dim 25864; exploration noise: NONE anywhere in this runbook (deterministic rollouts).
- mean iteration fitness, first 100 vs last 100 iterations: 15.44039271957343 -> 11.444787669784418; improved: false.
- final deterministic window (250 decisions): fitness 8.894332472928278 m; total dx 8.894332472928278 m; mean speed 0.7115465978342622 m/s; max |v| 0.8999990977122645 (envelope 2.977443609022557 m/s); saturation fraction 0.0.
- hard gates: all six held at every tick of every rollout (the executor's status law: any breach raises a retained termination record; this seed finished with no termination code).
- theta identity: initial `970f278419d42ffe8c7f69fdfa80a7b99906d053a3c7c7e85e6ea11ea419047e` -> final `e433340b369616a5e344c1972d34181ba6e61d1bc806a5adc4a2d35e91f0efa6`; theta npz sha `eacdafdb1de9034a39084f4fd81eaad8c4d3d9a09496c9d6b6758e2391388589`; fitness curve sha `d2e8de96d28ab9aeed1de6ccdd0dea84c0158ba18c612d990734c76a8478f8fc`; state chain head `d77abf034dcd9c5f67198d641832d87710e28a8eea817f33f0e0b11bc6dd97fd` (anchors every 4096 ticks).
- measured resources (non-canonical block): wall 430.3 s of the 5400 s per-seed budget; GPU jobs used: none (BQ-1; the GPU-03/GPU-05 catalog refs are NOT-APPLICABLE to this card's runs).

### Seed 20260920

- status: **EXECUTED_COMPLETED**
- decisions executed: 1000000 of 1000000 declared; iterations 2000; ticks 15000000.
- SPSA constants (frozen in the prereg, never tuned): c=0.05, a_s=0.01, parameter dim 25864; exploration noise: NONE anywhere in this runbook (deterministic rollouts).
- mean iteration fitness, first 100 vs last 100 iterations: 15.686209528073409 -> 11.422063862161158; improved: false.
- final deterministic window (250 decisions): fitness 8.872841644128576 m; total dx 8.872841644128576 m; mean speed 0.7098273315302861 m/s; max |v| 0.897132456507337 (envelope 2.977443609022557 m/s); saturation fraction 0.0.
- hard gates: all six held at every tick of every rollout (the executor's status law: any breach raises a retained termination record; this seed finished with no termination code).
- theta identity: initial `970f278419d42ffe8c7f69fdfa80a7b99906d053a3c7c7e85e6ea11ea419047e` -> final `54a4b7d42525c24f4f9fbfa66e7d869bdb51f038bbed78f46c56cc308c6b5155`; theta npz sha `89df7ac6ca3c94c547be5692da55c98e0e510050ff0b1e8df6912f2bb4d949aa`; fitness curve sha `5b19d59b9f9f20e032174c2d30a70b40ce4b64ca5cdf9245daa86d23d110aeb0`; state chain head `fd7c86aee1540959fe6e97ca19d751956200edbe39b8bf3cb7af1c6697f1592d` (anchors every 4096 ticks).
- measured resources (non-canonical block): wall 430.8 s of the 5400 s per-seed budget; GPU jobs used: none (BQ-1; the GPU-03/GPU-05 catalog refs are NOT-APPLICABLE to this card's runs).

### Seed 20260921

- status: **EXECUTED_COMPLETED**
- decisions executed: 1000000 of 1000000 declared; iterations 2000; ticks 15000000.
- SPSA constants (frozen in the prereg, never tuned): c=0.05, a_s=0.01, parameter dim 25864; exploration noise: NONE anywhere in this runbook (deterministic rollouts).
- mean iteration fitness, first 100 vs last 100 iterations: 15.46322027908788 -> 11.435178660784368; improved: false.
- final deterministic window (250 decisions): fitness 8.925413122530959 m; total dx 8.925413122530959 m; mean speed 0.7140330498024767 m/s; max |v| 0.9048679008874374 (envelope 2.977443609022557 m/s); saturation fraction 0.0.
- hard gates: all six held at every tick of every rollout (the executor's status law: any breach raises a retained termination record; this seed finished with no termination code).
- theta identity: initial `970f278419d42ffe8c7f69fdfa80a7b99906d053a3c7c7e85e6ea11ea419047e` -> final `fd711fbaf94418be7c27261b391d3cfffb7516a62191fdb031269e7ae541ca4d`; theta npz sha `7b11dd01f8495068f46def84a072d211fe47b778bfc0fbc3f53fe3e82a7fe1a7`; fitness curve sha `704038c303505a012d90d6a2b363bc0cba9cf3b7fe32e168bb203008522da311`; state chain head `b864045fc700e77b99f0a2606c9dedabbc451f8f26f0832457ed9f52d88eb19d` (anchors every 4096 ticks).
- measured resources (non-canonical block): wall 478.0 s of the 5400 s per-seed budget; GPU jobs used: none (BQ-1; the GPU-03/GPU-05 catalog refs are NOT-APPLICABLE to this card's runs).

## Held-out evaluation (C10; separate train/evaluation cases)

Each seed's final theta evaluated deterministically on all three seed scenes (1500 ticks / 100 decisions per cell; the 6 off-diagonal cells are the held-out cases).

| theta seed | scene seed | held out | fitness (m) | mean speed (m/s) | max |v| |
|---|---|---|---|---|---|
| 20260919 | 20260919 | false | 2.4519699186819754 | 0.4903939837363951 | 0.7615615310830239 |
| 20260919 | 20260920 | true | 2.451395184387545 | 0.490279036877509 | 0.7614270501926432 |
| 20260919 | 20260921 | true | 2.451366014143735 | 0.490273202828747 | 0.7614239282955511 |
| 20260920 | 20260919 | true | 2.4502160222955607 | 0.49004320445911215 | 0.7606012044016266 |
| 20260920 | 20260920 | false | 2.4496159767225167 | 0.48992319534450335 | 0.7605040138661803 |
| 20260920 | 20260921 | true | 2.4498551748042816 | 0.4899710349608563 | 0.7608914440538379 |
| 20260921 | 20260919 | true | 2.457445688796291 | 0.4914891377592582 | 0.7635010047686593 |
| 20260921 | 20260920 | true | 2.457432864046284 | 0.49148657280925684 | 0.7634925786889509 |
| 20260921 | 20260921 | false | 2.457422259696217 | 0.49148445193924345 | 0.7634866343289674 |

## Certificate mismatch rejection (C10; the frozen deploy gate)

- The certificate's own relation: ALLOW (the gate still closes on the certified tuple).
- The trained bundle tuple: BLOCK — reasons: ["BLOCKED: compatibility key mismatch -- the request's 5-tuple (5006d524d76c2d90...) is NOT the certificate's (dbda388b4797cfaa...); the bundle/build/runtime/body/suite is not the certified one"].
- A foreign build: BLOCK — reasons: ["BLOCKED: compatibility key mismatch -- the request's 5-tuple (fc3cd885d79fbd5d...) is NOT the certificate's (dbda388b4797cfaa...); the bundle/build/runtime/body/suite is not the certified one"].
- The trained candidates bind ONLY by reissuance through the TC-6 gate; FC-3 (trained walking policy) stays explicitly-unresolved; W06 evaluates these per-seed outcomes.

## Named checks (G12 accounting)

- Suite: test_w05_runbook.py (unittest discover -p test_*.py).
- Accounting claim: **31 executed, 0 skipped**; known skips: none (zero skips by design; no KNOWN_SKIPS entries); pass: true.

## Gate disclosure (G1-G9)

- G1 falsifier arms with clean controls and bites: FB1 pin bite, FB2 baseline bite, FB3 missing-certificate bite, FB4 slot-fill bite, FB5 structural no-retry scan — all executed in the named-check suite.
- G2 lint: `python -B lint_report_numbers.py --selftest` must exit 0; every number in this report traces to the bound artifacts.
- G3: this report is GENERATED from the receipts; no hand-written qualitative claim.
- G4/G8: NOT-APPLICABLE (records profile; camera record not required; no image is evidence) — disclosed, not skipped silently.
- G5: `refuse_vacuous_comparison` + `vacuous_guard_selftest()` run at import in the named checks.
- G6: keyed extractors; the runbook's phases are iteration windows carried in the per-seed receipts (first/last 100-iteration keyed fields).
- G7: registry identity read-only (card state OPEN, revision 1604); criteria sha identical across join/registry/prereg/checks.
- G9: prereg committed separate-first; ONE publication commit on `review/MAT2-W05` with the full lineage; contribution within the file/size bounds; commit-message metrics generated from these FINAL receipts.

## Evidence pins (G10: every pin hashes against the on-disk file)

- runbook.json | f173a1c5993929e10bac3365a46739aad0f9856b640b5de66ae06eaac2e1d6b0
- w05_freeze_fill.json | 258749b826bc1dcd86d2b3a127606e11792c3b014d904f0e105cea124a48bf63
- checks_receipt.json | 69e315a1e1aa54eb0221127acd7e4a93ff9036eaedade1f21d6170ae68683677
- receipts/baseline_receipt.json | 6ede18c05e9cd31b9c6cf493bfe471a1711439980dbe55723dfe4fc6f4bc3bb2
- receipts/recipe_equivalence_receipt.json | bbb6dbd34dff0d9f8a3f4940e947eba428b330f25bff3c15b7fcbdb7bbf22bdd
- receipts/heldout_receipt.json | 4deff1a2efec7112b975230fba24fa8818715fc378f453654e57a5cb05fce4f1
- receipts/deploy_check_receipt.json | 766a7cbe6a2ccd67c739d82af5b32e859ee4bc3f3a558715fafc63dbab0ae635
- trained/trained_policy_manifest.json | 02538194cad7f200985e628c55c86fb3fb6d2b76bfb6b44220fab7d32343571e
- receipts/seed_20260919_receipt.json | b866e9b1e2a3d516a960a88362c95d2f8211d28b894cc4d8c16dcebc4dc8b896
- receipts/seed_20260919_curve.json | 56e645a2a6ba7b594e0d98ab682c169e5132bca70abc233aa67eae19548fb450
- trained/theta_20260919.npz | eacdafdb1de9034a39084f4fd81eaad8c4d3d9a09496c9d6b6758e2391388589
- receipts/seed_20260920_receipt.json | 3d795b5ca523289c1ceac7dac72070875d8cc4b8e24e4ac2a5a64a9733e766ff
- receipts/seed_20260920_curve.json | 185ac6e3afa5b891d4032256f59c1340421ae7c649ed5cac173adc18c2e4835c
- trained/theta_20260920.npz | 89df7ac6ca3c94c547be5692da55c98e0e510050ff0b1e8df6912f2bb4d949aa
- receipts/seed_20260921_receipt.json | 10c4090473c75ec99559dd9f1f13729d96c3c7d5cf037569c63253e308f472af
- receipts/seed_20260921_curve.json | 145b2eb6069913719f7a1f575fad76a32764127ae62b736ad5209c2ce0c09972
- trained/theta_20260921.npz | 7b11dd01f8495068f46def84a072d211fe47b778bfc0fbc3f53fe3e82a7fe1a7

## Honest limitations (named, not skipped)

- The P04 handoff/admission machinery governs GPU training launches on the live controller; no live controller session is provisioned to this attempt. The operative admission of record for this CPU-only runbook is the frozen bounded-resource envelope (per-seed wall 5400 s, memory bound, no trajectory retention) plus the separate-first prereg; the GPU mailbox was unused (no GPU work exists under BQ-1).
- P3 outcomes are recorded per seed above whether improved or not; a failed training outcome is not hidden and not retried (the executor contains no retry path).
- The trained candidates are NOT a certified trained walking policy (the W04 freeze's TC-9 explicitly-unresolved closure stands).

