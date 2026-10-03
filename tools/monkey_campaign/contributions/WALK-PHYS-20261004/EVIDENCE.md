# EVIDENCE — wk-walk-physicalization, phase 1 (design + prereg DRAFT; NO runs)

Lane: `E:/ChimeraWork/monkey-coordination/walk-physicalization/` (sole write
scope). Task: completion-matrix finding F7 (hands/feet force transmission)
phase 1. NO_WORKTREES.md obeyed (sha `7d3fe1029f727b95ff2c832b06a89b3bac40f5
9e14993440255636218645f433` cited from MATRIX.md header; no worktree, no
clone, no Git mutation, no runner job). Reading checkout:
`E:/PythonChimera` branch `WK-ENGINE-PATHS-20260929-PR`, HEAD
`7222729eca6e9f97f25061c8b1dc3d229bb703d8` (== the base_sha the sealed
D-PAIRPATH/K01-era packages pin), dirty state preserved, used read-only.
All hashes below computed by this lane 2026-10-02 (sha256, sha256sum);
"claimed" = the prefix another sealed record cites; MATCH rows verified.

## 0. Lane deliverables (phase 1 output; the pin targets)

| artifact | sha256 |
|---|---|
| `INVENTORY.md` | (recorded after write; see section 4) |
| `DESIGN_RANKING.md` | (recorded after write; see section 4) |
| `PREREGISTRATION_WALKPHYS_V1_DRAFT.md` | (recorded after write; see section 4) |
| `EVIDENCE.md` (this file; self-hash excluded) | - |

## 1. F7 verification artifacts (sealed store rows, read in place)

| artifact | path (under `E:/ChimeraWork/monkey-coordination/` unless absolute) | sha256 | note |
|---|---|---|---|
| W10 walk trace (store row `0dc4dc75`) | `evidence-store/MAT2-W10/numerical/trace_walk.json` | `0dc4dc75db1e4facff2cfcd8c8b6c4750beaf749771e9be5bb475032ed1d83c8` | claimed `0dc4dc75...` MATCH; this lane scanned all 10,500 rows: front-4 forces constant 0.25 at all 42,000 contact entries; COM v tracks stride cmd |
| W10 receipt | `evidence-store/MAT2-W10/numerical/walking_demo_receipt.json` | `2fa7dbf180db6090611fdc0d074ebe80d79b43eb25a4a7162e218cbacd22aa02` | claimed `2fa7dbf1...` MATCH; FB2 clean control = stride-law deviation + velocity recursion |
| W10 report | `evidence-store/MAT2-W10/source/REPORT.md` | `7bc443f9b3896d6d6f93e6160dbe1337ed4dc3e88beae3fe2cb76a13afab3726` | claimed `7bc443f9...` MATCH |
| W10 dev refusals | `evidence-store/MAT2-W10/source/DEV_RUN_REFUSALS.md` | `10b9a84837689433ada996e5ea62db86158268443f5b74c3219da44d40005606` | claimed `10b9a848...` MATCH |
| W10 capture context | `w10_evidence_receipt.json` | `0e9c6de57665529d962a5ff3ec3fcf964a2283b9f7a665ad9abb160151bb7405` | subject_sha256 row `0dc4dc75...` |
| pinned W10 scene module | U07 review repro pinned tree `kanban-reviews/MAT2-U07/sgt-pr312-69772e91/repro/tmp/w10_pins_e0dd5f03/pinned_root/tools/policy_compat/scene_cpu.py` | `ab4257024df63d9755e9c1ae524ee631339ce24a2fd36615d40575335f835af2` | == receipt `physics_build.scene_module_sha256`; command-channel law read from lines 283-289 |
| sealed W10 driver (dominant sealed iteration `02e52304...`) | `kanban-attempts/MAT2-W10/e0dd5f03572f4b95b7f5a6013327d906/package/sealed/02e52304035745a6b519667cd015c96b/files/tools/monkey_campaign/contributions/MAT2-W10/walking_demo.py` | `d63eb3e1ea0b9b0d925d84fda4359bc0b51904e2682a5ed96e4df3210e4a9ed3` | majority hash across the attempt's 44 sealed iterations |

## 2. The articulated (M-chain) line and its evidence

| artifact | path | sha256 / git blob | note |
|---|---|---|---|
| sealed gait scene (anchor `f6844eea`) | `acceptance-chain/scenarios/common/gitrepo/tools/monkey_campaign/contributions/MAT2-W03/scene_out/scene.json` | `f6844eeae3dc87170a572ccdeedf326a6cac4f73d1448941808bd8b25a8db342` | claimed `f6844eea...` MATCH; 14 bodies / 18 coords / 12 capped drives / 8 contact points incl. 4 fore knuckle pads / 10.037998 kg; read by this lane |
| W03 trace (q,v only) | same tree `viswalk_dump/states_run1.jsonl` | `b47b709c43a021d24bfee13bb2fe4592167cf205ee0abf9971de462319389c93` | claimed `b47b709c...` MATCH; 302 rows, tick/q/v only — no contact/force/work channels |
| W03 report | `evidence-store/MAT2-W03/source/REPORT.md` | `6692f07fc5314210c854884d1c17d7a8e561b1c9fa131c02131e3611198d64fa` | anchors table: stdout `8c537cdb`, stderr `c6f9b6c0`, dx 0.9131056683968011, ledger 30.970714 J @ tick 300, refusal 302 |
| W03 independent review | `evidence-store/MAT2-W03/independent_review/REVIEW_EVIDENCE.md` | `a8525098f4f3ace984c051c085069b1bc18c10a0c6320448464652e96034f8b3` | |
| walk-anchor source revision | shared object DB commit `17ba94b948ca217c1bbf8f7dee5b51b995b387bb` (exists; `git cat-file -t` = commit) | blob `5863348f2deef1f01e3cf761d0c4151a10035a6d` = `ChimeraEngine/engine/gait_controller.hpp` (204,652 B); blob `a7bfe15e34e25a34c5316d65038b072d79ac529a` = `tools/science_funnel/validation/visible_walk_20260923/native/gait_unit_viswalk_dump.cpp` (153,332 B; == the W03 report's cited statedump git object `a7bfe15e...`); blob `8cd6004fc4a65f2f804ff1e00c18f1962bbaa9f0` = `native/build_dump.ps1`; blob `99b5530415bf3f04b2d6205b1edda6ca4348bea8` = `run_dump_walk.py` | dump source READS `s["contact"]["points"]` (gap_m/touching/reaction_N/friction_force_N/slip_speed_m_s) + full energy ledger channels; files NOT at HEAD (worktree gait_controller.hpp copy is untracked dirty state, `??`) |
| runtime/training contract | `b07-prereqs/RUNTIME_CONTRACT.md` | `f33c188bcb561b1946b104340cf36cba366709526c095874684529a599df338c` | claimed `f33c188b...` MATCH; TC-1..TC-12; drive caps; TC-11 cost gap |

## 3. The fixture solver line, the hand map, the route class, the audit

| artifact | path | sha256 | note |
|---|---|---|---|
| M06 solver | `evidence-store/MAT2-M06/source/local_contact.py` | `1cd662b30343011eb4a0a01e461a1e82b00482d0371857c8e42d6bec8f9a28dc` | == G04's pin `1cd662b3...`; translation-only free bodies; solve_tick ledger |
| G04 report | `evidence-store/MAT2-G04/report/REPORT.md` | `dfca5b5556efe018ca09be4577bf6fbb5df38bb5c9ebc33d15bd18646ba349c8` | claimed `dfca5b55...` MATCH; 60 N per-channel press; ledger 1.0e-15; zero-mu control |
| D-PAIRPATH result | `evidence-store/MAT2-D-PAIRPATH/numerical/pairpath_result.json` | `3d3dfae1fe6bfb759045a450e7a66bc7b3fd2e670eb9ed925e06163fd65a03a9` | claimed `3d3dfae1...` MATCH; declared hand 3.346 kg (G04 pad share) vs 0.049 kg anatomical; base_sha `7222729e...` |
| K01-impl lane | `k01-impl/EVIDENCE.md` | `c0eae7bcc5d9408d2910c3edb69e6614be36b35e4bfd2f657e93027ace2275d2` | approach = declared SCAFFOLD (`distance = start - speed*dt*tick`, k01_physics.py read at `k01-impl/package3/files/.../K01-CLIMB-20261001/k01_physics.py`); no drives, no body propulsion |
| actuator map (22 joints, statics) | `evidence-store/WK-ACTUATOR-MAP-20260929/verdict_ref/EVIDENCE__423ef0d4.md` | `423ef0d451e17b04346af8413c107416516e734b6784cf5099a282c0aaf68218` | MP cap 0.8875; frontier 38.25-41.34 N per contact; gait-scene caps recorded NOT-APPLICABLE to the hand chain |
| F06 report | `evidence-store/MAT2-F06/unclassified/report.md` | `87abd293dc5b09b48332f0b78e9ef2f9e8e9475435e555aac226b009236131ad` | claimed `87abd293...` MATCH; A1 2.6% traverse; A2 stall grade 0.0365707; A3 ceiling 0.11599999 vs log_02 0.128476 |
| F06 receipt | `evidence-store/MAT2-F06/unclassified/walking_receipt.json` | `7c309a8de4ab2d0cffad478d4383c74c5179fb317091c66507d6125e9f7f127c` | claimed `7c309a8d...` MATCH |
| PLAYABLE_BUILD record | `E:/PythonChimera/tools/monkey_campaign/PLAYABLE_BUILD.json` | `1d0d7bb3fe2b3ae64a3cbee9c9bb5377355093669c10c4c846eb24add3dc2643` | claimed `1d0d7bb3...` MATCH; UNQUALIFIED, all null |
| completion matrix (the tasking source) | `completion-matrix/MATRIX.md` | `fdc923c5866c90d34af9f94575c853e7d048a33270e9f73109e2efa7db30cef3` | F7 + section 1.12 + critical path 3b |
| matrix EVIDENCE | `completion-matrix/EVIDENCE.md` | `17484144ca83bc92f8722e950bf06dc217901fdc95d7ef6891684cbf0385a955` | |
| skill roadmap (gait benchmark context) | `skill-roadmap/SKILL_ROADMAP.md` | `989f43403de22ef4be1e1141ffc3e49377c7d7e87e2c2ce7a481e41b875d0cb7` | design study; W03 302-tick walk placement; duty factor MISSING |

## 4. Lane file hashes (final, after all writes)

Recorded by sha256sum at write time (also pasted into the final report to
the Lieutenant):

- `INVENTORY.md`
  `5b3cc72aba2ebb6bbe7b849315d7e8f736b4853ec37bdacef001ecd7fa92a5e3`
- `DESIGN_RANKING.md`
  `746cc9b0f59e8ab94161d150c3dab21a801ba59e68d57c982b502a3c6640ca38`
- `PREREGISTRATION_WALKPHYS_V1_DRAFT.md` (the pin target)
  `b4326a0971326db3d6267c9e00a9372ce33707d084b11a897417406e319de3fe`

(If any lane file is amended after this EVIDENCE write, the amendment and its
new hash must be recorded in a dated appendix below; no in-place edits.)

## 5. What this lane did NOT do (phase-1 law)

- No runner job, no seal, no GPU queue entry, no build, no physics run.
- No write outside this lane directory; no other lane's file read-modified.
- No Git mutation in `E:/PythonChimera` (read-only blob/commit reads only).
- No picture inspected (text-only model): the W10 mkv/bmp visual rows were
  NOT opened; visual verification is the Sergeant's, via the Lieutenant.
- No claim that any design is qualified: the prereg above is a DRAFT; the
  rank-1 design's feasibility probe is phase 2 and may return BLOCKED
  (native toolchain in the runner) as the smallest missing prerequisite.

## 6. Corrections to the dispatching tasking (records-based, with receipts)

1. "the K01 reach line moved the body through certified drives w/ scaffold
   contact": the K01 approach leg is a DECLARED SCAFFOLD distance schedule
   (k01_physics.py `run_approach`: `distance = start - speed*dt*tick` with
   `solve_tick` contact checks; no drives act; the body is not propelled).
   The line that DID move the body through certified drives without a COM
   command channel is the W03 native walk (302 ticks, dx 0.9131056683968011,
   sealed anchors). The design consequence is in DESIGN_RANKING.md Rank 1.
2. "the W10 scene with the command channel DISABLED and limb drives pushing"
   (option a) is infeasible as stated: the W10 scene has no limbs, drives,
   joints, mass, or contact dynamics (scene_cpu.py; INVENTORY section 1).

---

## APPENDIX (2026-10-04): PHASE 2 — the sealed battery (chain stop 2)

Pin: prereg commit `2b58118cae81110b8e1c69a26e83d0aadab002f4` on
`origin/review/WALK-PHYS-20261004` (parent `aa413b9c`), blob sha256
`b4326a0971326db3d6267c9e00a9372ce33707d084b11a897417406e319de3fe` ==
the phase-1 draft byte-for-byte (verified in the object store).

Package: `battery-package/` (base = the pin; writes = the WALK-PHYS-20261004
contribution dir). SEALS (lineage, superseded ones preserved in
`battery-package/sealed/` history and the runner results): cddcac69 (first,
vcvars quoting refusal dc253914), 78cb43ee (cl PATH refusal 501fdc4d), then
the include-closure + full-arm-smoke line: 6a3f6246 (f9582e50: 1-tick
truncation crashes the native post-walk falsifier stack, 0xC0000005), 
4e555157 (5c6567e0 + 373a33f5: keep-path lessons, science already green),
b99442fd (SMOKE OF RECORD: job `dd38403cc6064ee883cc546b6de17a1e` PASSED
exit 0 cleanup_verified; anchor identity ALL 8 checks true — the instrument
binary reproduces stdout `8c537cdb...` + stderr `c6f9b6c0...` + q-dumps
`b47b709c...` x2 + dx/dy + the 302-tick refusal EXACTLY with telemetry on).
- SEAL OF RECORD for the battery: `cc0b63f647714167a2a9946c40226983`,
  manifest sha256 `a1758df0478d62cf0994f1a35464a13d24a8c91b7fe6c935d2c3070
  ad46302d2`. SUPERSEDED battery: job `075ada58` (seal b99442fd) — its P3
  numbers are INVALID (evaluator unit bug: force compared against impulse);
  preserved as history; corrected offline analysis and the re-run supersede.
- BATTERY OF RECORD: job `28b28e4730524d4fa2cb2f83e6237bf9` — state PASSED,
  exit 0, cleanup_verified true. Receipt sha256 `e3806cd1d3f6e5ab...`
  (lane copy `final_run/walkphys_receipt.json`; runner receipt
  `5fbbb0d7acfccf86...`).

VERDICT (the prereg's own class): **FALSIFIED_OR_PARTIAL** —
G_BACKSTOP true, G_COMMAND_ROLE true, G_DETERMINISM true,
G_ENERGY false (the pre-accepted negative), G_PROPULSION false.

Prediction outcomes (exactly):
- P1 PASS — anchor identity EXACT on the clean instrument arm.
- P2 PASS — support census complete, zero unexplained ticks; fore knuckle
  pads touch (103+95 of 240 window ticks) at LIGHT load (2.1 of 41.6 N*s
  total reaction = 5.0%; hind heels 39.5 N*s = 94.9%; the MP-head points
  never load) — the certified gait is hind-dominated with real, light
  fore/hand transmission.
- P3 FAIL (corrected impulse units) — 112/240 window ticks violate the
  containment |m*d(COMx)| <= sum(|friction_force_N|)*dt + 1e-9 (median
  |imp| 0.0330 vs median bound 0.0379 N*s, worst resid 0.0327 N*s): the
  direction-free serialized friction scalars do NOT fully account the COM
  momentum change. REAL FINDING + feed-forward: the contact record needs a
  signed tangent component and the other generalized channels (candidates:
  joint-stop impulses, the free-base posture servo/damping generalized
  forces) before an exact per-tick propulsion attribution can close.
- P4 FAIL = the PRE-ACCEPTED ledger negative, now localized AND
  anchor-identical: bal(300) = 30.970713623726674 J == the sealed W03 raw
  value bit-for-bit; the imbalance accumulates INSIDE the walk window at up
  to 0.3556 J/tick (window 1e-6). The native walk line's energy ledger does
  not close; closure is engine debt (a new prereg through the publication
  owner would own it).
- P5 FAIL AT THE FROZEN WINDOW (anti-tuning law applies to this lane's own
  prereg; the window stands): mu=0 COM_x advance 0.011216 m > the frozen
  1e-4 m. The PHYSICAL reading is decisive and recorded: clean COM advance
  0.735053 m vs mu0 0.011216 m = 1.5% (a 65x collapse) — propulsion without
  friction is absent; the frozen window simply also counts the entry-
  momentum shuffle my derivation missed.
- P6 PASS — drive cut at 150: zero horizontal COM momentum rise (no hidden
  cruise channel).
- P7 PASS — cap tamper (hip x1.5): 26 ticks with torque beyond the SEALED
  cap, zero in clean — the certified caps bind the physics; the audit bites.
- P8 PASS — two-pass byte-identical (stdout, stderr, qdumps, telemetry).
- P9 PASS — the tick-100 state-write probe DIVERGED exactly at the injected
  tick (first_divergence_tick 100): the seam cannot silently move the body.

Infrastructure refusals preserved (all runner-retained): dc253914 (vcvars
quoting), 501fdc4d (cl PATH search), f9582e50 (1-tick truncation crash),
5c6567e0/373a33f5 (keep-name resolution; the science green in both).

Coordination fact: slots 2/3 were held by wk-digit-scan jobs
(`3a1ff276`, `5d68d670`) for the first ~40 min; this lane waited (no
preemption). Lane copies: `final_run/` (hashes in the table below).

| phase-2 artifact (lane copy) | sha256 |
|---|---|
| `final_run/walkphys_receipt.json` | `e3806cd1d3f6e5ab1e58374f261bc6cc8556e1563da93107267a3db21d7e60ab` |
| `final_run/runner_receipt_28b28e47.json` | `5fbbb0d7acfccf860063a78804a6d231cf9940f442d1087bbcd46213f672e4c9` |
| `final_run/smoke_receipt.json` | `d5ede95f9df164600d1527ce3080fefc5a956072f6ab7053b04a11c6b4d871a9` |
| `final_run/runner_receipt_dd38403c.json` | `5ec0aa80bd07670b493c9d10fc390a303690a1fef64744ff9ed468826bf8a385` |
| `final_run/seal_manifest.json` | `a1758df0478d62cf0994f1a35464a13d24a8c91b7fe6c935d2c3070ad46302d2` |
| `final_run/telemetry_clean1.jsonl` | `69e988a3f4cc77a1da6c017fc88b9a80df5c4b44bfd4f6e3d00647ae07f6e26a` |
| `final_run/telemetry_mu0.jsonl` | `89f55aa95d221e1f772c962963cd6c0fb4baaced6f82a7c41f1520eaf2dae24b` |
| `final_run/telemetry_cut.jsonl` | `c9f551dd381d81307a2b6fe8d3b9a453fb3255158a41256d5ab440db575edae7` |
| `final_run/telemetry_cap15.jsonl` | `455e238696ccc86e00f2025cb46cdf54d2dbc9f6b805551a79e76d62e1cc6118` |
| `final_run/telemetry_inject.jsonl` | `9150438e975cd05c0d7a0b74df5c3319d0e33c299aa09296cfeb46de2ddba0ca` |

---

## APPENDIX 2 (2026-10-04): SGT WALKPHYS REVIEW — CHANGES_REQUIRED amendments

Review verdict: "the verdict DIRECTION stands and is STRENGTHENED"; three
records amended below per the no-in-place-edit law (sections above are
preserved; where they are wrong, THIS appendix supersedes them). No new
physics run: the reviewer's numbers were recomputed from the already-sealed
telemetry and this lane re-verified them from `final_run/*.jsonl` before
adopting (exact matches marked).

### (a) P3 ERRATUM (supersedes the P3 paragraph in the phase-2 appendix and the P3 note inside the sealed INSTRUMENT_PROVENANCE.md)

- The sealed eval_p3 in seal of record `a1758df0` (job `28b28e47`) is
  dimensionally INCOHERENT: `imp = mass*Δeast` has units kg·m (a momentum
  change times dt, mislabeled as impulse) while the bound
  `Σ|friction_force_N|*dt` is N·s. This is the same disease class that
  invalidated job `075ada58` — "the fix did not fix exactly that".
  Additionally, the sealed `INSTRUMENT_PROVENANCE.md` states a THIRD form
  ("|m*d(COMx)| <= sum(|friction_force_N|)*dt"), contradicting the evaluator
  beside it; those sealed bytes stand under seal `a1758df0` and are
  superseded by THIS appendix (no sealed byte is edited).
- ADOPTED (the reviewer's dimensionally-correct momentum-CHANGE identity):
  |M*(east[t+2] − 2*east[t+1] + east[t])/dt| <= Σ|f|*dt — the per-tick
  CHANGE of horizontal momentum must be covered by the tick's friction
  impulse (the only serialized horizontal force channel; coast costs
  nothing, which the superseded level-form wrongly counted).
- Recomputed on the sealed telemetry (adopted as the record; this lane's
  independent recount agrees EXACTLY on the load-bearing numbers):
  61/240 window ticks fail (bound-from-row-b), 72 (bound-from-row-a),
  25 under the reviewer's generous max-alignment (this lane's narrower
  max{row-a,row-b} recount gives 49 — the falsification count is
  alignment-dependent; EVERY reading is nonzero); worst residual
  0.8439 N·s at tick 297 (exact match); aggregate Σ|Δp| = 11.679 N·s vs
  total friction impulses 14.095 N·s (reviewer; this lane's row-b recount
  15.227 — under BOTH aggregates the total friction impulse EXCEEDS the
  total momentum change, so the failure is per-tick alignment/direction,
  not aggregate capacity). Sub-counts by convention (reviewer's): 35/61
  failing ticks carry nonzero serialized impact impulse; 16/61 carry ZERO
  serialized friction despite loaded pads (this lane's recount of the last:
  15 under its own window convention).
- VERDICT: the direction HOLDS and the failures CLUSTER at impacts and at
  the direction-free-serialization blind spots. G_PROPULSION=false STANDS.
  Feed-forward unchanged and sharpened: the contact record needs a signed
  tangent component (and the impact-impulse channel must be part of the
  attribution set) before an exact per-tick propulsion identity can close.

### (b) P6 DISCLOSURE (restates the phase-2 appendix's "P6 PASS — zero momentum rise", which is FALSE as written)

- IMPLEMENTED check (faithful to the sealed code): a HIGH-WATER test —
  momentum after the cut must never exceed its tick-150 value. Measured 0.0.
  FROZEN PREREG WORDING: "horizontal COM momentum is non-increasing from the
  cut through cut+100 ... FIRES if COM momentum rises beyond the window" —
  an any-rise test. The data falsifies the FROZEN wording: 24 local per-step
  rises in [150,250], 20 beyond 1e-6 (this lane's recount: 20), max
  +0.0247 kg·m/s, cumulative +0.128 over ticks 193-202 (this lane's recount
  summing rises > 1e-6: +0.1502 — convention-dependent, same conclusion).
- The PHYSICAL conclusion survives and is STRENGTHENED: the rises do not
  form a cruise channel — the 150-157 post-cut flight phase is exactly
  conserved, the momentum decays monotonically in the large (10.28 → 9.99
  kg·m/s by tick 230) and reaches 0 at the drive-cut arm's own refusal at
  tick 233 (verified). HONEST P6 RECORD: frozen wording FALSIFIED (the
  implemented invariant was weaker than the frozen text); implemented
  invariant HELD; no-cruise reading STANDS. Lesson 2 below applies to this
  lane's own prereg drafting.

### (c) P5 DISCLOSURE (restates the phase-2 appendix's "1.5% / 65x collapse" reading, which was a window artifact)

- The mu0 arm REFUSED at tick 65 (this lane re-verified: the sealed
  telemetry carries ticks 0..65 only), so the frozen [60,300] window was
  silently measured over [60,65] — the early-refusal truncation was not
  declared at freeze time (lesson 2).
- The mu0 COM coasts at ~0.6736 m/s from tick 0 (per-tick east advance
  0.002243-0.002246 m — the declared entry-momentum class), so the 0.0112 m
  displacement is COAST, not collapsed propulsion. Like-for-like per-tick
  advance: clean 0.00306 vs mu0 0.00224 m/tick = 1.37x — the phase-2
  appendix's "1.5% / 65x collapse" reading is RETRACTED.
- THE HONEST RECORD: without friction the gait COLLAPSES (refusal at 65)
  and the COM merely coasts at the declared entry velocity — no
  friction-independent propulsion exists. EVERY reading still fires the
  frozen 1e-4 m window: P5 FAIL and the overall verdict are UNAFFECTED.

### Seal-lineage canonical naming (supersedes the phase-2 appendix's lineage block; receipts index by MANIFEST hash)

| manifest sha256 (canonical) | jobs | outcome |
|---|---|---|
| `cddcac69` | none | superseded, never run |
| `78cb43ee` | none | superseded, never run |
| `b768830d` | dc253914 | FAILED (vcvars quoting refusal) |
| `6a3f6246` | 501fdc4d | FAILED (cl PATH search) |
| `c99a903d` | f9582e50 | FAILED (1-tick truncation crash, 0xC0000005) |
| `6fb2b888` | 5c6567e0, 373a33f5 | FAILED on keep-path resolution; anchor identity GREEN in both |
| `4e555157` | dd38403c (SMOKE — PASSED, anchor identity all-true); 075ada58 (battery — P3 unit bug, superseded) | |
| `4d55272a` | none | accidental unmodified re-seal, superseded |
| `a1758df0` | 28b28e47 | **SEAL OF RECORD** — battery PASSED, amended by this appendix |

(The phase-2 appendix's block mixed seal-DIRECTORY ids (`d6b0cffb`,
`8eee85ad`, `90cb7c63`, `03bfe49e`, `b99442fd`) with manifest hashes and
mis-mapped two jobs; the directory ids remain recoverable from
`battery-package/sealed/` for lineage but are not receipt keys.)

### INPUT_PRODUCT_INTEGRATION (restated)

The battery is an integration-evidence consumer of already-sealed products:
scene `f6844eea...`, the W03 anchor set, the pinned blobs at revision
`17ba94b9...`, and the pin commit's tree — all hash-pinned as package inputs.
It introduces NO new physics constant and modifies NO sealed physics byte;
its products are the instrument (a recording/control-seam layer, proven
non-perturbing by P1) and the P1-P9 evidence receipt. Fixtures composing into
loop evidence remains exactly the goal-text law: this lane's receipt is
integration evidence for the walk-class limbs, not the ten-phase loop.

### DURABLE LESSONS (three, now law for this lane and proposed for the memory index)

1. Dimensional analysis of evaluator formulas is a REVIEW STEP: a receipt
   can be honest about what it computed and still publish unit-inconsistent
   numbers (P3 was published twice — force-vs-impulse in 075ada58, kg·m-vs-
   N·s in 28b28e47 — before the momentum-change form).
2. Frozen-window evaluators must state their early-refusal behavior AT
   FREEZE TIME: truncated windows silently manufacture collapse ratios
   (P5's [60,300] was measured over [60,65]).
3. One canonical naming for seal identity: MANIFEST hashes are receipt
   keys; seal-directory ids are lineage convenience and never receipt keys.

---

## APPENDIX 3 (2026-10-04): F7 RE-REVIEW ROUND 2 — three record corrections + the joint durable lesson

Append-only. The battery of record (job `28b28e47`, seal `a1758df0`), the
gates, and the FALSIFIED_OR_PARTIAL verdict are UNCHANGED and need no re-run
and no re-seal. Every corrected clause below was re-derived from raw rows and
raw receipts before landing.

### 1. Seal-lineage table CORRECTED (supersedes the Appendix 2 table)

Canonical key = `results/<job>/receipt.json -> sealed_manifest_sha256`.
Seal-DIRECTORY ids are NOT receipt keys, and `battery-package/sealed/` no
longer holds the full lineage (only the seal of record survives there); the
runner-retained receipts are the lineage authority.

| manifest sha256 (canonical) | jobs (receipt-verified) | outcome |
|---|---|---|
| `cddcac69` | none | superseded, never run |
| `78cb43ee` | 0ea202a0 | FAILED exit 2 — `build_failed`: `fatal error C1083: Cannot open include file: 'coupled_articulation.hpp'` (the include-closure refusal; 7th superseded job) |
| `b768830d` | dc253914 | FAILED exit 2 — vcvars quoting refusal |
| `6a3f6246` | 501fdc4d | FAILED exit 1 — `cl` PATH search (FileNotFoundError) |
| `c99a903d` | f9582e50 | FAILED exit 2 — 1-tick truncation crash (0xC0000005) |
| `6fb2b888` | 5c6567e0 | FAILED exit 0 — keep-path resolution; anchor identity GREEN |
| `4e555157` | dd38403c — SMOKE **PASSED** (anchor identity all-true); 373a33f5 — FAILED exit 0 (keep-path; anchor identity GREEN); 075ada58 — battery PASSED, P3 unit bug (superseded) | |
| `4d55272a` | none | accidental unmodified re-seal, superseded |
| `a1758df0` | 28b28e47 | **SEAL OF RECORD** — battery PASSED, as amended by Appendices 2-3 |

Appendix 2's errors corrected here: job `373a33f5` (receipt manifest
`4e555157`) was mis-placed on the `6fb2b888` row and now sits on its own
receipt-exact row; job `0ea202a0` (receipt manifest `78cb43ee`) was omitted
and now stands as the 7th superseded job; the directory-id parenthetical is
replaced by the receipt-provenance law above. The receipt-exact cells
(`b768830d`->dc253914, `6a3f6246`->501fdc4d, `c99a903d`->f9582e50,
`a1758df0`->28b28e47) STAND.

### 2. P6 terminal-state CORRECTION (supersedes Appendix 2's "momentum ... reaches 0 at the drive-cut arm's own refusal at tick 233" — that clause is FALSE)

Re-derived from `final_run/telemetry_cut.jsonl` raw rows: the cut arm's last
complete pair is 232->233 with momentum **9.9888 kg·m/s** (constant east
advance 0.003317 m/tick) and **6 pads touching** at the final row
(left heel+MP, right heel+MP, fore_left heel+MP); tick 234 is absent. The
guard REFUSES the arm while it is still supported and moving ~1 m/s —
refusal, NOT momentum exhaustion, terminates the arm. THE DEFENSIBLE
STATEMENT: the implemented high-water invariant HELD (momentum never rose
above the post-cut 10.2775 kg·m/s at tick 150); the rises were a transient
(193-202); the arm is refused while still at ~9.99 kg·m/s. The no-cruise
conclusion stands; the "momentum exhaustion" narrative is RETRACTED.
PROVENANCE OF THE ERROR, recorded honestly: the clause originated in the
reviewer's own first report (a faulty index expression) and this lane's
"verification" adopted it after sampling only ticks 150/160/200/230 — the
terminal row was never opened. Both parties own the lesson below.

### 3. Zero-friction sub-count: this lane's convention DOCUMENTED; the reviewer's 16 recorded as the convention-robust count

Appendix 2's "15 under its own window convention" is reproducible under
exactly this convention: among the 61 failing ticks (momentum-change form,
bound-from-row-b), BOTH second-difference endpoints carry EXACTLY zero
serialized friction (F[t]==0 AND F[t+1]==0) AND the bound-side row (t+1)
carries a REACTION-LOADED pad (touching && reaction_N > 1e-9) -> 15.
The reviewer's 16/61 holds under four natural conventions (any-touching,
reaction-loaded, raw-zero, shifted window); this lane's variant scan
reproduces 16 under any-touching@t+1 and reaction-loaded@t+1 with only
F[t+1]==0 required. The sub-count is not decision-bearing: the direction
holds under every convention. RECORD: 16/61 (convention-robust), 15/61
(this lane's stricter documented convention).

### THE NEW DURABLE LESSON (verbatim; BOTH parties own it)

"independently re-verified before adopting" must include RE-DERIVING
QUANTITATIVE CLAUSES FROM THE RAW ROWS, not confirming narrative consistency
— the one clause adopted from the reviewer's report without a raw-row
re-derivation ("reaches 0 at t233") was the one that was wrong, and the
canonical-table fix introduced a new mapping error of exactly the class it
was written to eliminate.
