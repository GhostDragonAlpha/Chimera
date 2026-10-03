# EVIDENCE — digit-scan lane (wk-digit-scan, chain stop 1: THE PREREG DRAFT)

Task: the Captain's order #1 via the Lieutenant — "Authorize the bounded
digit-side joint scan as an independent diagnostic lane. Run it against the
frozen geometry and report its actual result. Keep it off the critical path
for designing the replacement hand." The lane measures the exhausted ladder's
named unscanned DOF direction: the opposing-digit clearance rejection class
(distph2/distph3/distph4 crossing the trunk solid); the v2.2 posture scan
covered cmc_flexion x mp_flexion (thumb-side) only — the DIGIT-side joints
were outside its named scope (V2_2_ADDENDUM.md declared-scope-limit law).

Acceptance = sealed receipts, never prose; prereg-first (chain stop 1 = the
prereg draft; the Lieutenant commits; execution starts only on the Lt's pin).
NO_WORKTREES honored: no worktree, no clone; CPU only through
`python -B E:/PythonChimera/tools/monkey_campaign/task_package.py seal|run`
(runner slots 0/1 hold preserved scratch — this lane runs `--slot 2/3`).
Write scope: the NEW lane dir `E:/ChimeraWork/monkey-coordination/digit-scan/`
(+ later, this card's own package contribution dir). No other lane's bytes
touched. Campaign clock 2026-09-29; host 2026-10-03.

## 1. Chain-stop-1 artifacts (sha256)

| artifact | sha256 |
|---|---|
| PREREGISTRATION_DIGIT_SCAN.md (THE DRAFT; DRAFT until committed ALONE FIRST by the Lieutenant; the committed bytes are the freeze) | `05a2bba9774d9bf4bcfd8b376a5ed785bef56747ec3c9d1d093e173c31864328` |
| EVIDENCE.md (this file, chain-stop-1 version) | self-referential; re-hashed at every append |

No implementation file, harness run, measurement or capture frame exists at
chain stop 1. Zero runner jobs launched by this lane so far.

## 2. Pin verification performed at draft time (all byte-exact MATCH,
## 2026-10-03, by this lane's own sha256 runs)

| pin | declared | observed |
|---|---|---|
| instrument_v2.py (frozen instrument, byte-identical reuse; copy hashed: `grasp-candidates/package-v22/files/tools/monkey_campaign/contributions/GRASP-CANDIDATES-20261002/instrument_v2.py`; == `instrument-v2/package/files/...` copy) | `9514c5b15a27948c65563070f16dffee4a5a28347c281a5d7e255fe93e516ddd` | MATCH |
| grasp-candidates committed prereg (in-package copy == lane copy) | `e5bfa3cd32d26785bdcd7441f6af720fdc4a561938ff1c8de3f21dd7a6545106` | MATCH |
| V2_2_ADDENDUM.md (lane copy == in-package copy) | `cf7da1a8cc75f522acaa958045ce1977e12f37187211db6980c48f4f1a7c90f4` | MATCH |
| grasp_screen.py (v2.0 module, in-package copy) | `6b924e87151f5e2235b9d9c023be85d0f7602d42020b37df4ba7bf58c0e9e0ea` | MATCH |
| grasp_screen_v21.py (in-package copy) | `a35facd2f0876d5b7aa595c3af5be7151f121d315f151cdb7a42e9dee86c0407` | MATCH |
| grasp_screen_v22.py (in-package copy) | `96ad2809ed928969571fe3b943117d6dba5d9ae905620b963039595313c5cb1b` | MATCH |
| control_input_table.json (in-package copy) | `d8aacc23b27e2caaf60304c0e9a4fe711ac51245c0ca3bf6d021d8f7b5164bf2` | MATCH |
| A05 mutation structure `evidence-store/MAT2-A05/workspace_evidence/48b037593f63_mutation_structure.json` | `48b037593f63ec473947d787077ab6fbcd3b364afd15765bff508e7d54f45649` | MATCH |
| A05 XML `.../9c91124600ab_macaque_hand_mutation.xml` | `9c91124600abc67a4a33d78ce79ab1a0604a48b5a9a2e6377d15de05717e5adf` | MATCH |
| hand.vtp anchor envelope | `a06ea7e079c849df07d6eec001e9bcc2ea193ecd3914011c78a993a5faa94fc6` | MATCH |
| CANDIDATE_FORMULATION.md | `0c24657de95068eb7499c3b9f140b8467f58e5ba6bcc94d02c69207341dbd1b1` | MATCH |
| v2.1 runner receipt (lane copy `grasp-candidates/final_run_v21/runner_receipt.json`) | `5c373edf41a134790c0f8952d1e9b30b7c1c5d357ab8932fffe7b2ed45adf08c` | as recorded by grasp-candidates EVIDENCE.md CS2.1 (not re-hashed by this lane; the run gate re-verifies the operative pins) |
| v2.2 runner receipt (lane copy `grasp-candidates/final_run_v22/runner_receipt.json`) | `3359a0fcc8136bcf3d809678a73e7a231e36d7ffc5dbb316c65ad95556c58d5c` | as recorded by grasp-candidates EVIDENCE.md CS2.2 (not re-hashed by this lane; the run gate re-verifies the operative pins) |
| v2.2 sealed receipt `outputs/grasp_screen_v22_receipt.json` | `43f395e2d98935fb916a699f52b94d1775a27ced303ce01438167a26b298542b` | as recorded in the v2.2 runner receipt artifacts map (not re-hashed by this lane) |

(Probe-class digit joints named FROM the pinned A05 bytes and cross-checked
against the sealed q_c vector in `instrument_v2.Q_C_PRIMARY` at draft time:
mcp{2..5}_flexion [0.0, 1.5708]; mcp{2..5}_abduction [-0.261799, 0.261799];
pm{2..5}_flexion [0.0, 1.5708]; md{2..5}_flexion [0.0, 1.5708] — 16 joints.
At sealed q_c(PRIMARY) all digit-2/4/5 chain values are 0.0 (fully extended)
and digit 3 carries mcp3_abduction -0.22085923868312754, mcp3_flexion
0.1442324074074074, pm3_flexion 0.17150324074074075 — the relief DOF this
scan measures is real, not vacuous.)

## 3. What the draft declares (summary; the committed bytes are the law)

- Scanned joints: the 16 certified digit-side joints of digits 2-5 (named
  from the A05 sealed records); thumb-side + wrist HELD at sealed q_c
  values (the declared scope split: thumb side was v2.2's scope).
- Grid: R0 reference (sealed q_c, not a scan point) + 98 scan postures =
  Tier A 80 (16 joints x fractions {0.05, 0.275, 0.5, 0.725, 0.95}) +
  Tier B 12 (flexion waves, digits 2/3/4) + Tier C 6 (abduction extremes,
  digits 2/3/4); digit-5 Tier B/C omission declared (no digit-5-chain
  crossing event in any sealed q_c PRIMARY map; fifthmc is jointless).
  Stage 1 = 1,440 axes/posture (v2.2 coarse law) => 142,560 candidates;
  stage 2 = full 11,520-axis refinement on hitting postures only.
- Same cheap-screen law (S0/S3/S1, PROVEN events only), same instrument
  (instrument_v2.py `9514c5b1...` byte-identical), same caps discipline
  (CAP_S1_PER_POSTURE 96; S1 budget 2.5 h/job; s* bracket [0, 0.15] m;
  pad-orientation cos > 0 at S1-survivor recording; tau 1e-4, pi_c 1e-3),
  same trunk scenario FROZEN (R = 0.037 m; no joint-limit change; no
  tolerance change).
- Job split: JOB-1 = R0 + digits-{2,4,5} (73 postures); JOB-2 = digit-3
  (26 postures); slots 2/3 only; declared CPU envelope <= 5 CPU-hour.
- Honest prediction stated first: zero survivors predicted (the two
  structural causes); the scan is the DECLARED COMPLETION of this anatomy's
  placement search at the digit side; the answer goes in the record either
  way. Survivors => stage 2 => S1 => the force stage per the committed
  grasp-candidates prereg section 6 (ladder law, unmodified).
- Report law: the precise negative statement (exactly what was sampled and
  what was not; NO universal impossibility claim — a global bound would
  need separate justification).

## 4. Chain position

- Chain stop 1 COMPLETE at draft: prereg draft path
  `E:/ChimeraWork/monkey-coordination/digit-scan/PREREGISTRATION_DIGIT_SCAN.md`,
  bytes sha256
  `05a2bba9774d9bf4bcfd8b376a5ed785bef56747ec3c9d1d093e173c31864328`.
- NEXT (the Lieutenant): commit the file ALONE FIRST on the publication
  lineage (proposed contribution path
  `tools/monkey_campaign/contributions/GRASP-DIGIT-SCAN-20261003/PREREGISTRATION.md`);
  hand back the commit pin. THEN (this lane, on the Lt's pin): implement
  `grasp_screen_digit.py` in a sealed task package based on the committed
  prereg commit; dev smokes declared; seal/run with explicit `--slot 2/3`;
  results, receipts and every load-bearing sha256 recorded HERE; Sergeant
  review requested through the Lieutenant (no self-review; no picture
  claims from this text-only worker).
- Nothing else claimed; no other lane touched; no capacity claim made
  (this card's own CPU estimate is declared in the draft, section 5).

---

# CHAIN STOP 2 — implementation + sealed runs (on the Lieutenant's pin)

## CS2.0 — the pin (verified byte-exact by this lane from the origin ref)

- Commit `1a567c39164d4b44d9fa0efb048429f8b3d03fe8` on
  `origin/review/GRASP-DIGIT-SCAN-20261003`, parent
  `2ee691818ad365610665408f7445cf2b9f0d2ae2`; file
  `tools/monkey_campaign/contributions/GRASP-DIGIT-SCAN-20261003/PREREGISTRATION.md`;
  `git cat-file` blob sha256
  `05a2bba9774d9bf4bcfd8b376a5ed785bef56747ec3c9d1d093e173c31864328`,
  25,679 bytes — EXACT match to the lane draft bytes (the fetch touched no
  HEAD/index/branch/worktree; FETCH_HEAD only).
- ERRATUM APPLIED (the Lieutenant's ladder-erratum notice, sgt review
  aa1cc2c2 on PR #325, CHANGES-REQUIRED): the inherited
  `s0_reject_no_approach` class of the v2.1/v2.2 solves is a
  BRACKET-RESOLUTION ARTIFACT CLASS (the 41-sample tau-bracketing pre-scan,
  ~2.5 mm spacing — roots verified to EXIST at the v2.1/v2.2 audited axes,
  the predicates rejecting them there). THIS scan inherits the same
  pre-scan. REPORT LAW (binding here): every no_approach count in this
  lane's receipts/reports is labeled "bracket-resolution artifact class -
  roots unverified at this scan's postures" (for JOB-1 the identical
  frozen-tip axis set was fine-scanned by the PR #325 reviewer at q_c: all
  such axes have roots and reject on the predicates); no "no root exists"
  wording anywhere; the negative statement carries NOT-AN-IMPOSSIBILITY-
  PROOF through every sentence. Zero-survivor prediction UNCHANGED.

## CS2.1 — package, seal, smoke

| artifact | value/sha256 |
|---|---|
| Task package (`digit-scan/package/`, task GRASP-DIGIT-SCAN-20261003-DIGIT-SCREEN, owner wk-digit-scan) | base `1a567c39164d4b44d9fa0efb048429f8b3d03fe8` (verified == the pin); package.json sha256 `a31bc92150ae2d6bf008130714b3048239646c753c674933ba776733ca4e4b4f`; base tree input: the committed prereg (1 file, 25,679 bytes) |
| grasp_screen_digit.py (the ONLY new logic file; no new screen predicate — every verdict from the sealed v2.1/v2.2 path) | `3d05620ed3445e15cff71193cba9e760e8728984e854a5e74d55b956933b12e2` |
| In-package byte-identical copies (verified at copy time) | instrument_v2 `9514c5b1...`, grasp_screen `6b924e87...`, grasp_screen_v21 `a35facd2...`, grasp_screen_v22 `96ad2809...`, control_input_table `d8aacc23...`, INSTRUMENT_PREREGISTRATION `897ca164...`, V2_2_ADDENDUM `cf7da1a8...` — all MATCH |
| SEAL #1 (PRESERVED, never deleted; ERRATUM: included a stray `__pycache__/grasp_screen_digit.cpython-314.pyc` from a local compile check — contamination caught before any run; superseded) | sealed `f0913260f0164cc7842fdf9df8e8542b`, manifest sha256 `c62c90937ed2d6722f8979bbccdf4589a0834d48437cda67ae43c784ac39f26c` |
| SEAL #2 (THE CLEAN FINAL SEAL used by both runs; 8 changed files, all inside the declared write scope; the committed prereg is NOT a change — byte-identical to base) | sealed `10eb42add30c4252913501e920e8a401`, manifest sha256 `557e4946a38500466aeb677fa250ecb70a138cd14bc69f50f6c5fe96becf5cf2`, patch sha256 `a58a470c126ee3eefc38bd28a28dc83bad4c377de0dcfdb22d4c112c0b7b3bda` |
| Bounded dev smoke (DECLARED, no results taken; patched small-grid copies OUTSIDE the package: THETA_STRIDE 90, single fractions, job split 17/6; the patched v2.2 copy's sha pin updated in the smoke copy only — the REAL package's sealed module is unmodified `96ad2809...`) | smoke outputs (lane dir `smoke/outputs/`): job1 receipt `91d061c5aadb7af73f283ada361c023f1fc2faa6f16d37631ff3a5339ac6031f`, job1 report `0a34ceb6ed09fe189281070d9c28c397d367e2330f2a06989868f7d38999a89a`, job2 receipt `198b8056ee183e8ec28d201b9347223b23be015653331d6d973212db8502d94d`, job2 report `b07773a22eebe002beb865ffbfb1bf291b5dc04a41133da1087c4a1e4bb107e9`, gate receipt (the pin gate REFUSING the patched v2.2 copy — the drift law observed working) `c5b50b2f8d698b89bb1276967318231fc6d09fa4cecf5daa1b6ea336c09074be` |
| Smoke observations (plumbing only, NO results) | all identity gates + light gate + witness GREEN; DS-P2 replication gate ok=True (job1); R0 sealed-map replication passed; determinism slices 8/8 byte-identical both jobs; coverage exact every posture; both jobs end-to-end VERDICT path exercised; partial receipts written after every posture (the timeout-durability mechanism) |

## CS2.2 — the sealed runs (declared split; slots 2/3)

- JOB-1 (R0 + digits-{2,4,5} tiers, 73 postures, 105,120 stage-1
  candidates): slot 2. JOB-2 (digit-3 tiers, 26 postures, 37,440
  stage-1 candidates): slot 3. Command (both):
  `python -B E:/PythonChimera/tools/monkey_campaign/task_package.py run
  --sealed .../10eb42add30c4252913501e920e8a401 --keep
  outputs/grasp_screen_digit_receipt_<job>.json --keep
  outputs/grasp_screen_digit_report_<job>.txt --keep
  outputs/grasp_screen_digit_receipt_<job>_partial.json --slot <2|3>
  --timeout 14400 -- python -B
  tools/monkey_campaign/contributions/GRASP-DIGIT-SCAN-20261003/
  grasp_screen_digit.py <job>`.
- Slot-2 first admission returned BUSY/exit 75 (slot lock held by another
  lane's live job `3b31e817...` — router-bytelaw; observed, never touched);
  the declared >= 10 s backoff retry loop is running. JOB-2 admitted on
  slot 3. (Results and runner receipts recorded below on completion.)

### CS2.2.1 — INTERRUPTION RECORD (attempt A) and relaunch (attempt B)

- ATTEMPT A (both jobs): JOB-2 admitted on slot 3 (job
  `1e9bb70d2a604fe982e4175eecfd645a`); JOB-1 admitted on slot 2 after
  backoff (job `f55ab660cf9a40e4b6c7211823e882d6`, sealed manifest
  `557e4946...`). At ~13:30 the session's two background launcher wrappers
  were KILLED EXTERNALLY (harness side, cause unknown to this worker); the
  slot-2/3 RUNNER processes died with them. The slot-2 experiment child
  SURVIVED as an orphan (Windows Job Object without kill-on-close) and kept
  scanning until the next slot-2 admission.
- JOB-2 attempt A recovery: the next slot-3 admission (another lane's job)
  triggered the runner's sanctioned recovery — state INTERRUPTED_RECOVERED,
  cleanup_verified TRUE; the declared partial receipt was preserved:
  `E:/ChimeraWork/task-runner/results/1e9bb70d2a604fe982e4175eecfd645a/`
  (recovery.json sha256
  `5eef11109f2a6a1065cbfa9110ff5fd7e26b16b02263678c628ac5bf3829592d`;
  partial sha256
  `cf500f8107c12bdd79c4b40e65f3eddb61a86d30bd4e30722da3ddf11f2650c1`;
  24/26 postures scanned, ZERO S0-survivors at every scanned posture; the
  final receipt/report never written — the run did NOT complete).
- JOB-1 attempt A recovery: the detached relauncher's admission on slot 2
  recovered the orphan — `E:/ChimeraWork/task-runner/results/
  f55ab660cf9a40e4b6c7211823e882d6/` (recovery.json sha256
  `658256017627d6fe28cd7a33ab018c01e3edd2a008b45162b48757bad1dbbf8b`,
  INTERRUPTED_RECOVERED, cleanup TRUE; partial preserved at 27/73 postures,
  ZERO S0-survivors, sha256 inside the recovery artifacts map).
- ATTEMPT B (THE AUTHORITATIVE RUNS; detached launchers
  `digit-scan/job1_launch.cmd` sha256
  `e41a21e715987514ef6858d628947a1199f2be18bedf520851749d8d757466e7` /
  `digit-scan/job2_launch.cmd` sha256
  `0b4ad70e80292035fd95e350f7c67ac9c83b2096e1435337556d93edf5bf28a0`,
  surviving session wrapper kills; BUSY -> 60 s backoff -> retry, declared
  law): JOB-1 job `3a1ff276b9d84cabab33f558539deb05` on slot 2; JOB-2 job
  `5d68d67020fd49c6bb26c5c044d830b4` on slot 3; both on the CLEAN FINAL
  SEAL `10eb42add30c4252913501e920e8a401` (manifest `557e4946...`).
- CPU-ENVELOPE FINDING (declared F6-class handling, reported never
  normalized): the interruptions force attempt B re-runs; the projected
  cumulative CPU for the program now EXCEEDS the declared <= 5 CPU-hour
  envelope (attempt A ~0.6 h + ~0.9 h burned + attempt B ~1.0 h + ~3.1 h
  projected). The overflow is a finding routed to the Lieutenant with this
  record; nothing was normalized and no budget was silently extended.

## CS2.3 — JOB-2 RESULT (attempt B; PASSED)

- Job `5d68d67020fd49c6bb26c5c044d830b4`, slot 3, state PASSED, exit 0,
  cleanup_verified TRUE, base `1a567c39164d4b44d9fa0efb048429f8b3d03fe8`
  (== the pin), sealed manifest `557e4946a38500466aeb677fa250ecb70a138cd14
  bc69f50f6c5fe96becf5cf2`. Result dir
  `E:/ChimeraWork/task-runner/results/5d68d67020fd49c6bb26c5c044d830b4/`.
- VERDICT: `ZERO_SURVIVORS_DIGIT_SIDE`. 26 digit-3 postures x 1,440 coarse
  axes = 37,440 candidates, coverage exact, ALL rejected: tip_deep 29,968
  (80.1%), clearance 5,880 (15.7%), no_approach 1,592 (4.3%; per the CS2.0
  erratum law: BRACKET-RESOLUTION ARTIFACT CLASS — roots unverified at
  these moved-tip axes; concentrated at near-q_c fractions where the solve
  bracket is marginal). s3_bracket 0. Stage 2 never triggered; 0 exact S1
  cells; the force stage acquires no inputs from this job.
- Gates GREEN at run: prereg bytes + addendum + instrument copy + v2.0/
  v2.1/v2.2 module copies + control table all MATCH; inherited input gate
  ok (14 pins); light gate C1/C2/C3 ok; witness identity (sealed q_c tips +
  chord 0.0739999998849158 reproduced); determinism slice 8/8
  byte-identical. DS-P2 recorded not_applicable (digit-3 postures move the
  contact tip; DS-P4 honest re-solves observed — e.g. md3_flexion moves the
  tip MESH and the solve at constant T1 chord 0.074).
- Measured chord range across the digit-3 grid: 0.029146..0.075254 m — the
  abolished chord gate exercised both sides of the diameter; every
  rejection is geometric (per-posture class rows in the receipt).
- Artifact hashes (runner-verified): receipt
  `bd273f749e2589a62ef079fc555b80598971f24d9d26357af01c9c1e73061c86`;
  report `5efa64f7873b5e5e445b425154f2d9894df020a895bed474e32eb038a2f833d2`;
  partial `492d7cecc59ae655e45f281e5253df2adf0728aa3410d62ae94479f897a6064a`;
  runner.log `a49ca18b3919e1e5966e3e69df6e2fd8bcf7860ba204713fc86f643623b3ef24`.
- DS-P1 (job-2 scope): SUPPORTED (observed zero, as predicted).

## CS2.4 — JOB-1 RESULT (attempt B; PASSED)

- Job `3a1ff276b9d84cabab33f558539deb05`, slot 2, state PASSED, exit 0,
  cleanup_verified TRUE, base `1a567c39164d4b44d9fa0efb048429f8b3d03fe8`
  (== the pin), sealed manifest `557e4946a38500466aeb677fa250ecb70a138cd14
  bc69f50f6c5fe96becf5cf2`. Result dir
  `E:/ChimeraWork/task-runner/results/3a1ff276b9d84cabab33f558539deb05/`.
- VERDICT: `ZERO_SURVIVORS_DIGIT_SIDE`. 73 postures (R0 reference + 72
  digits-{2,4,5} scan postures) x 1,440 coarse axes = 105,120 candidates,
  coverage exact, ALL rejected: tip_deep 68,138 (64.8%), clearance 17,126
  (16.3%), no_approach 19,856 (18.9% — BRACKET-RESOLUTION ARTIFACT CLASS,
  roots unverified at this scan's postures; for the frozen-tip axis set the
  PR #325 reviewer's fine-scan audit verified roots exist at ALL such axes
  and the predicates reject them there), s3_bracket 0. Stage 2 never
  triggered; 0 exact S1 cells; S1 clock 0.0 (never entered).
- Gates GREEN at run: all pinned bytes MATCH (prereg/addendum/instrument/
  v2.0/v2.1/v2.2 modules/control table); inherited input gate ok (14 pins);
  light gate ok; witness identity (chord 0.0739999998849158 reproduced);
  axis-family identity 4/4 cells; determinism slice 8/8 byte-identical
  (R0).
- FROZEN PREDICTIONS (both jobs combined): DS-P1 SUPPORTED (0 stage-1
  S0-survivors across all 98 scan postures / 142,320 scan candidates +
  240 reference candidates — observed zero as predicted, refusal-wording
  law); DS-P2 SUPPORTED (no_approach = 272 and s3_bracket = 0 at EVERY one
  of the 73 JOB-1 postures — the solve-invariance identity held exactly);
  DS-P3 SUPPORTED (every digit-2/4/5-only posture zero survivors);
  DS-P4 recorded honestly (digit-3 re-solves; e.g. md3_flexion moves the
  tip mesh + solve at constant T1 chord 0.074); DS-P5 measured (below).
- DS-P5 THE RELIEF MEASUREMENT (recorded, never gating): R0 reference =
  234 PROVEN distph2 clearance events / 1,440 axes (min proven depth
  1.098e-4 m, max 3.363e-2 m). Across ALL 25 digit-2 postures of the
  certified grid the count stays in 174..252 — it NEVER approaches zero:
  the best relief postures (B_d2_f3 full curl wave: 180; C_d2_ab0: 174;
  C_d2_ab1: 186) still leave hundreds of PROVEN index-crossing events, and
  the minimum proven depth never leaves the ~1e-4 m scale while the max
  stays ~2.8e-2..3.7e-2 m. Digit-4 motion leaves distph2 counts constant
  (234 at every digit-4 posture; separate chain). Clearance-class bone
  decomposition across JOB-1: distph2 16,990 events, distph4 114, midph2
  22 (distal_thumb 66,868 and distph3 1,270 are the TIP fold events the
  per-bone counter also records).
- Artifact hashes (runner-verified): receipt
  `a4f9b62678b16efb287fe0e1792bd59e04b3dcf81ecd54e4e58800c8663000b7`;
  report `1b8414b1e385207e62d4b2772d5a2f954b4f7ba00ddc8daaef898496c6689aaa`;
  partial `79e2938378e76cfe92ea7d1efe27f8e6792aefe43f17c6f724656588988be191`;
  runner.log `3cb7964c9e7ff3c7fbfbd61e3e1bc90c085fe70ee2175bd6143711cdaa24ae65`.

## CS2.5 — THE PROGRAM VERDICT (chain stop 2)

`ZERO_SURVIVORS_DIGIT_SIDE` — both sealed jobs PASSED, 142,560 stage-1
candidates (99 postures x 1,440 axes; 98 scan + 1 reference), ALL rejected
at the inherited cheap screens with PROVEN geometry or declared
artifact-class labeling, ZERO S0-survivors anywhere, stage 2 never
triggered, 0 exact S1 cells, the contact-force stage acquires no inputs.
THE CAPTAIN'S DECISIVE FIELD: bone clearance NEVER passes at ANY
digit-side posture in this scan — 0 of 142,560 — and the index-crossing
relief measurement (DS-P5) shows the certified digit-2 DOF cannot clear
the crossing anywhere in its range at the frozen offsets. The digit-side
DOF direction is measured CLOSED at this frozen construction, and the
ladder's OPPOSING-DIGIT CLEARANCE cause survives its named unscanned
direction unchanged.

### THE PRECISE NEGATIVE STATEMENT (binding report law)

ALL TESTED PLACEMENTS FAILED. What was sampled: 142,560 stage-1 candidates
= 99 postures of the declared grid (R0 reference + 98 scan postures: 16
digit-side joints single-joint at fractions {0.05, 0.275, 0.5, 0.725,
0.95}; flexion waves and abduction extremes for digits 2/3/4) x the coarse
axis grid (90 theta x 8 phi x 2 mirrors) at the q_c(PRIMARY) contact pair
under the sealed v2.1 two-contact mesh-tangency offset solve, at the
represented geometry (19 pinned STLs + hand.vtp envelope, scale
0.5384048132470733). What was NOT sampled: the thumb-side joints beyond
the sealed q_c vector and v2.2's 25-point cmc/mp subgrid; the wrist joints
(frozen at 0); the continuous posture space between grid points and
between range fractions; the full-resolution axis space (stage 2 never
triggered — no hits to refine); the F1/F2/F3 contact pairs at digit-side
postures; pads/soft tissue (ABSENT); species-true anatomy (ABSENT — the
A05 hybrid disclosure); measured friction (ABSENT); dynamics (none).
EVERY no_approach count above is the bracket-resolution artifact class —
roots unverified at this scan's postures (at the frozen-tip axes the PR
#325 fine-scan audit verified roots exist and the predicates reject) —
never a claim that no root exists. THIS IS FEASIBILITY EVIDENCE OF ABSENCE
AT THE REPRESENTED GEOMETRY UNDER THE DECLARED FAMILIES — NOT AN
IMPOSSIBILITY PROOF IN ANY SENTENCE OF THIS RECORD; a universal
impossibility claim is not made and would need a justified global bound,
which a grid cannot supply. A universal impossibility claim is NOT made.

## CS2.6 — evidence anchoring and lane convenience twins

- ANCHORED (evidence-store anchor.py add, card MAT2-GP3-DIGIT-SCAN, class
  numerical; manifest rows appended, re-verify OK): the four sealed run
  artifacts (job1/job2 receipt + report; shas as CS2.3/CS2.4).
- Lane convenience twins (byte-copies of the runner-preserved artifacts):
  `digit-scan/final_run_job1/` receipt
  `a4f9b626...`, report `1b8414b1...`, runner_receipt.json
  `c68fae2f090582f2f6a01d2c3362307059baf3c2f959f2653ee55b00bffe6f75`;
  `digit-scan/final_run_job2/` receipt `bd273f74...`, report
  `5efa64f7...`, runner_receipt.json
  `924d82cd452f9a5b438e51f350642b2b585afc9ded721cb29627c9e8e7629308`.

## CS2.7 — findings and handoff

- CPU-ENVELOPE OVERFLOW (F6-class finding, routed to the Lieutenant): the
  program consumed ~6.2 CPU-hour against the declared <= 5 CPU-hour
  (attempt A ~1.5 h + attempt B ~4.1 h + smokes/gates < 0.1 h) — caused by
  the external wrapper kills forcing attempt B re-runs; nothing normalized.
- The interrupted attempt-A partials are preserved (results
  `1e9bb70d...` and `f55ab660...`, INTERRUPTED_RECOVERED, cleanup TRUE)
  and carry NO result weight.
- Sergeant review is requested through the Lieutenant (author self-review
  certifies nothing). Publication (contribution dir + PR from the review
  branch) stays with the Lieutenant; this lane's chain-stop-2 deliverable
  is the sealed runs + receipts + this record.
