# PREREGISTRATION (DRAFT) — K01 climbing skill specification: OBSERVATIONS, ACTIONS, REWARD, TERMINATION, SUCCESS METRICS, SEEDS, ENVELOPE, FALSIFIERS

Status: DRAFT authored by `wk-k-spec` for the Lieutenant. Per the publication
law this file is committed ALONE FIRST (separate-first) BY THE LIEUTENANT; the
committed bytes are the freeze and every emitted receipt must embed
`preregistration_sha256` of exactly those bytes and refuse any mismatch. No
implementation file, harness run, training run, measurement or capture frame of
this card exists at draft time. Write scope of the draft: the NEW lane dir
`E:/ChimeraWork/monkey-coordination/k-spec/` (NO_WORKTREES law honored; no
worktree, no clone; all CPU verification through
`python -B E:/PythonChimera/tools/monkey_campaign/task_package.py seal|run`).

- Card K01 (planning id K01, registry group "Climbing skills (core)"),
  agent-author `wk-k-spec`, lane `E:/ChimeraWork/monkey-coordination/k-spec/`.
- Registry row (verbatim, `MONKEY_COMPLETION_MAP.md`
  sha256 `0e3984578b0cae38ab435daaa77cc10559cceeadbaf9885c3f31b979a362ecae`,
  re-hashed 2026-10-02): "K01 | Freeze the climbing skill specification |
  G08, U05 | C10, C21 | Observations, actions, reward, termination, success
  metrics, seeds, envelope and falsifiers approved before training | First
  skill family: attach, ascend, hold, descend, release".
- Gate state: G08 and U05 are DONE receipts, not open work. G08 evidence
  receipt `E:/ChimeraWork/monkey-coordination/g08_r1_evidence_receipt.json`
  sha256 `992851c5c9fbc6ef6b8a6ee6f13a3436d51c848fdb0b62b5b3ee1f04c5a73b96`
  (`task_id` "G08", `done_when_verified` true, head_sha
  `9bfd29d8975a04c748c490d0a7340d3ac3a94841`). U05 climb intent seam:
  `E:/ChimeraWork/monkey-coordination/evidence-store/MAT2-U05/independent_review/REVIEW_REPORT_MAT2-U05_CLIMB_INTENT_SEAM.md`
  sha256 `c63cd335e981e9b193b8a3e924f4b61492df0602982758a0e7463da0d19736dc`.
- Build line: `E:/PythonChimera` HEAD `7222729eca6e9f97f25061c8b1dc3d229bb703d8`
  (dirty state preserved; nothing in the repo was modified by this lane). The
  W10/W04/W05 walking acceptance line and the U07-integrated line are ancestors
  of the current HEAD lineage and are SEALED — NOT re-claimed by this draft.
- Dispatch-map position: K01 and K02 are the SPEC-AUTHORING pair of the staged
  climb chain K01->K02->K03->K04->K05->K06->K07->K08
  (`climb-derivation/DERIVATION.md` section 5,
  sha256 `da34420558f6632b0544ca94bc3e25ece515027628c7bd8cc54b9fdd30b7ebd9`).
  Authoring K01 NOW removes it from the critical path: this draft is gated on
  NOTHING in flight. What stays gated is TRAINING, not the spec.

## 0. The three standing laws this draft consumes (binding on every reading)

### 0.1 The objective-line law

"A COMPLETED SPECIFICATION IS NOT A TRAINED SKILL." Approval of this document
freezes a contract; it trains nothing, qualifies no physics, and completes no
playable behavior. It carries the verbatim standing rule: "DEMONSTRATED
IMPOSSIBILITY CAN CLOSE AN INVESTIGATION, BUT IT CANNOT COMPLETE THE
PLAYABLE-MONKEY GOAL" — the playable objective stays OPEN until the positive
behavior is demonstrated; no measured value is ever tuned to force success; any
infeasible configuration encountered under this spec is either changed by a
physically justified move WITHIN project authority (a declared-synthetic
parameter, a geometry choice, an actuator within anatomical bounds — NEVER a
tuned measured value) or escalated with bounded options.

### 0.2 The refusal/prediction wording law (Captain correction #3)

A predicted refusal that is observed is a SUPPORTED PREDICTION; it is never a
failure of the experiment and never a success of the skill. Each falsifier
below NAMES the observation that would CONTRADICT its prediction. A refusal is
never misread as a grasp, contact, hold, ascent or descent result.

### 0.3 The corrected-corpus and scope-label law

This draft consumes ONLY the corrected corpus numbers
(`DERIVATION.md` section 7 CORRECTIONS, 2026-10-01) and carries the section 8
SCOPE LABELS forward: every friction threshold quoted here is a
CONDITIONAL-CALCULATION — a closed-form consequence of DECLARED inputs and the
sealed law forms under assumptions A1-A7 (mass reading, contact count, press
ceiling, pad fixture class, friction placeholders, law forms, screening band) —
and is never a measured monkey-bark value. "Monkey-bark friction (macaque volar
skin on bark at the 20-60 N operating load) is UNMEASURED" — the standing
obligation string of the K01-chain opener prereg (`k-tier/PREREGISTRATION_K01.md`
sha256 `227a06c83180b68846b921e3ea36a0b594b5395d331fd487d9c36cdac764a65e`),
grounded in the FRICTION_SOURCES L9/P3 CONFIRMED GAP rows
(`evidence-store/MAT2-F05/source/FRICTION_SOURCES.md`
sha256 `336118e929bd0b4fb067db5a448dc2e348fed073007787635549a4cf1cf5868b`)
and the DERIVATION section 8.4 master verdict ("NO measured macaque volar
skin on bark value exists anywhere in the corpus"); acquisition gap
NB-01/02 stands. THE 0.41 VALUE IS A DECLARED SCENARIO PARAMETER
(a human forearm-on-textile analogue transfer), NOT a monkey-bark measurement;
every mu_s = 0.6 / mu_k = 0.4 quote is a NAMED placeholder. THE RESERVED
DECISION STAYS OPEN: the mass lineage (band 5.4 / 6.15 / 6.9 kg register scalars
vs the certified 10.037998 kg walking line, weights 52.95591 / 60.3108975 /
67.665885 / 98.4391330867 N) is unresolved (gap 9); every threshold is
per-reading and cannot be quoted without naming its reading, and corridor
arithmetic is NOT a lineage-selection input. THE n=4 SHAPE DECLARATION IS A
SEPARATE DECISION, NOT MADE HERE.

## 0.4 Master conditionality: this spec is CONDITIONAL ON THE GRASP CHAIN

Every training-bearing element below (reward, success metrics, seeds, envelope)
is a CONDITIONAL-SPECIFICATION: it becomes executable ONLY when a qualified
grasp configuration exists. NO TRAINING RUN starts until ALL of the following
exist, each with its own sealed receipt:

1. the A09 grasp anatomy input package issued with supported mappings,
   parameters, provenance and explicit gaps (A05 digit structure, A06
   attachment/waypoint ownership, A07 lawful resolution of failed placements,
   A08 evidenced muscle/tendon envelope);
2. G01-G04 grip feasibility THROUGH THE PHYSICAL SOLVER at trunk_01 (support
   feasibility, finite-area attachment qualification, tendon/moment-arm
   finiteness, physical grip contact with friction, reaction loads and release —
   no invisible anchors), including a QUALIFIED press derivation: x_press is
   ABSENT today (TC-8 ports 0/8, honest refusal stands), so the press channel
   has NO actuator derivation, and the drive table must be re-declared from the
   assembly's OWN sealed sources (TC-3; the certified scene's caps never
   transfer silently);
3. the friction acquisition (gap 1; NB-01/02) resolved by measurement, or the
   placeholder-mu corridor explicitly re-authorized for training by its owner —
   never by this spec;
4. the mass-lineage decision (gap 9) taken by its owner (until then the corridor
   is quoted per-reading and the reserved decision stays open);
5. G08-relevant CPU/GPU parity and runtime identity gates RE-BOUND to the
   training revision (do not inherit walking certification for changed
   hand/contact dynamics);
6. the U05 climb intent seam contract unchanged from
   `REVIEW_REPORT_MAT2-U05_CLIMB_INTENT_SEAM.md` (frozen walk contract
   unchanged);
7. P04 training reservations admitted (GPU/CPU mailbox serialization; training
   throughput is bound to the P04 reservation discipline, not to hope).

The grasp chain is otherwise SEPARATE: "approach, contact establishment, grasp,
static hold and climbing transfer are SEPARATE claims." This spec's reward and
success metrics credit SUPPORTED ASCENT, HOLD and DESCENT only. They contain NO
grasp-success term: grasp establishment is owned and gated by the grasp chain
(A01-A09, G01-G08), and no reward, metric or termination clause of this spec
may stand in for it. "Rules out ONLY" wording applies per-claim: a refusal in
one claim rules out ONLY that claim under its assumptions.

## 1. Observation space (C21) — pinned to the certified line's actual observables

The climbing controller receives ONLY declared, measurable, explicitly-timed
signals. Three certified records define the space; no invented channel exists.

### 1.1 The certified seam schema (primary)

- `chimera.g05_obs.v1` (G05 contact/support observations,
  `evidence-store/MAT2-G05/report/REPORT.md`
  sha256 `1e5fcc7f81b5bd7b0ae3b460c72d5ed190510f66db4793c6b2e99756da8c8524`;
  experiment receipt
  `evidence-store/MAT2-G05/numerical/experiment_receipt.json`
  sha256 `468185796db949ffd97b7e390de4adbc80aef74d1021445a8cfa28a74ef3dfbe`):
  OBS_DIM 32; dtype float32 through the declared rounding (window 1e-06 *
  max(1, |v|)); fixed slot order; timing block mandatory on every sample
  (`t_tick`, `t_phase`, `t_dt_s`, `t_seconds`); cadence exactly one sample per
  solver tick, post-solve, no interpolation, no hidden lookahead; history law 0
  undeclared history (the only cross-tick slots are the DECLARED cumulative
  displacement and measured pose).
- Per-channel group (8 slots x 3 declared channels): contact flag, stick flag,
  slip flag, `jn`, `jt`, contact force (DECLARED conversion `jn/dt`),
  cumulative downward displacement, measured centroid z. Channels k >=
  n_channels are UNAVAILABLE with declared fill 0.0; `obs_mask_mean` /
  `obs_frac_avail` report availability (the W04 sensor-health law composition).
- Aggregates (always available): support count, supported flag, release flag,
  trunk anchor z (the VISIBLE recorded anchor), full-tick residual max,
  reciprocity max, and the two availability slots.
- Phase universe (G06 extension,
  `evidence-store/MAT2-G06/report/REPORT.md`
  sha256 `2e4343191591322dca4667e428c09d1dc8dcae39c8a90a53cb5298d90ab2f206`;
  experiment receipt
  `evidence-store/MAT2-G06/numerical/experiment_receipt.json`
  sha256 `cf5c9cc5b7d51a23f282313974f853edca83ca30c19edd51a36eb9ddf0d3feff`):
  approach, attach, load, hold, transfer, attach2, load2, hold2, release. The
  composition is at the shared-table level: the pinned G05 seam accepts the
  hold/release projections and refuses out-of-class phases (the recorded
  pattern: 270 accepted deliveries across the battery, 1791 refusals, all
  timing_unbound); the phase extension is real, declared, and refuses
  undeclared phases at the seam.

### 1.2 The certified walking interface law (composition partner)

- `policy_observation_interface v2` (dim 80; OBS_SCHEMA_VERSION 2; dtype
  float32; `privileged_forbidden: true`; history_ticks 0), pinned by sha
  `e8c2d698dee0337414c48e8d2f6569c45f6f61828dabdeff6a4f1188b1c0671c`
  (`observation_interface_v2.json`); FIELDS[:64] is field-for-field the frozen
  v1 width replaying bitwise-identically; normalization per
  `obs_section_v2.json` sha `3de82a1156ac2f39ed04da24c7fd40357642d7bc029e09b509dfc3ea1af63079`
  (mean/std over available ticks; never-available -> 0/1; std floored; clip 8.0;
  the P3 normalization law). The 80-field walking interface is NOT re-declared
  by this spec; the climb-side task-owned table is the G05/G06 schema of 1.1,
  and any composed controller consumes both under their own pinned hashes
  (the G05 X5 composition pattern: the frozen contract's DECLARED LAWS govern
  the task-owned 32-slot grasp table; the aliasing audit declares all 7 shared
  sources).

### 1.3 Command and intent echo

- The declared command echo slots (`prev_req_*`, `prev_app_*`, `lim_sat_*`
  classes of the v2 order) extend to the climb intent: the U05 climb/let-go
  intent (versioned semantics; one explicit intent reaches the skill selector)
  and the resulting per-channel applied commands are observable ONLY through
  declared echo slots — never as privileged state.

### 1.4 Anti-hidden-information law (C21, binding)

- The privileged registry is empty in every delivery; the `x_*` namespace is
  refused at the seam (`named_absent_occupied`): the ten named-absent variables
  (x_press, x_share, x_aperture, x_reach, x_com, x_inertia, x_trajectory,
  x_sequence, x_losses, x_trunk_strength) stay ABSENT with verbatim provenance;
  no synthetic constant occupies an absent slot; no hidden simulator
  information is represented as sensed information (the FB1/FB5 arms proved the
  guard load-bearing).
- Delivery gates at the seam: undeclared_field, timing_unbound, timing_drift,
  named_absent_occupied, privileged_source, nonfinite_value, dim_mismatch.
- Aliasing law: all shared sources carry declared alias rows; BEFORE any
  training run, the C21 aliasing and hidden-state-dependence tests must pass on
  the composed climb observation set (frozen train/eval specification and
  independent failure cases).
- CONDITIONAL binding: any TC-7 body-domain rebind or TC-3 drive re-declaration
  invalidates the observation binding; a future policy binds ONLY by reissuance
  through the W04 compatibility gate (the recorded reusability verdict: the old
  sealed 5-tuple BLOCKs against the rebound contract).

## 2. Action space (C07/C10) — ONLY the certified actuators

### 2.1 Certified body drives

The certified 10.038 kg scene's capped servo drives ONLY: hind hip 11.2125 /
knee 6.6375 / ankle 7.4 / MP 0.8875 N*m; fore shoulder 4.229 / fore elbow
3.76 N*m (`b07-prereqs/RUNTIME_CONTRACT.md`
sha256 `f33c188bcb561b1946b104340cf36cba366709526c095874684529a599df338c`;
`w04_freeze_manifest.json`
sha256 `be632ffc85865515285f3d622a09882a3180a43101027914f1ed3408496f5d29`).
The certified-caps-never-transfer law and TC-3 (RE_DECLARE_PENDING_FROM_THE_
ASSEMBLY_OWN_SEALED_SOURCES) apply verbatim. Action laws: no pose-writing, no
teleport, no force outside the capped channels, no human-norm torque
substituted for this animal (C07).

### 2.2 The hand joint set (actuator-map frontier)

The climbing action space's hand portion is the actuator-map frontier's joint
set, and nothing else:
- Law: `tau_j = sum_i ((p_i - o_j) x F_i) . u_j = (J(q)^T f)_j` (the GP1 CC5
  law); per-tip loaded chain = 6 joints (the two wrist joints on
  `macaque_hand_anchor` — `mutation_wrist_flexion`, `mutation_wrist_abduction` —
  plus the 4 chain joints); the digit metacarpals `secondmc`..`fifthmc` declare
  NO joints; the thumb chain `firstmc` declares `cmc_abduction` + `cmc_flexion`;
  18 joints per tip are off-chain `structural_zero`; the terminal exact-zero
  arms (`ip_flexion`, `md{k}_flexion`) are recorded per posture. This is the
  revision-2 map of record (the anchor-inclusion correction; the P2 structure
  falsifier is CHECKED AT RUN, hard refusal `p2_chain_structure_failed`).
- Sources: `actuator-map/EVIDENCE.md`
  sha256 `b56f181923fc85621ae112b536ea8b4bfc66926e993920b4e0abd24682eab189`;
  light prereg sha256 `4e0472aff62ff7c8c6f148817e20505ba4bebca559c04aa22a801da260360c98`;
  receipt `actuator-map/final_run/actuator_map_receipt.json`
  sha256 `013f3157c3455dc66c736fee465f8ac2341bc72ebbb8ca6bafdb7f545c2e9175`;
  report `actuator_map_report.txt`
  sha256 `036d3af275c4c4234b879fe80bde29048d91f75e3a399f8b266f35dc572fefe2`;
  jacobian map `jacobian_map.json`
  sha256 `96a4610ffb37e6729763cb13455b7d6b6b3d582a3ab35dc4975a3b67f64f31b3`.
- Cap basis: the declared MP cap 0.8875 N*m applied to every loaded joint
  (RECORDED, never decisive). Frontier F* (posture-conditional
  CONDITIONAL-CALCULATION over the 4 GP1 candidate POSTURES + 22x9
  coordinate-wise joint-box grid): F1 pair [thumb, digit4] chord
  0.073999999236 m, F* = 38.254690383428 N (binding joint cmc_abduction); F2
  pair [thumb, digit5] chord 0.073999999544 m, F* = 41.337217959487 N (binding
  joint mcp5_flexion); F3 pair [thumb, digit2] chord 0.073999999605 m, F* =
  40.101569932379 N (binding joint cmc_flexion). x_press DEBT rows at the
  declared 60 N press are RECORDED, not decisive (e.g. tau
  1.391986171 N*m at cmc_abduction > 0.8875 cap).
- THE PRESS CHANNEL HAS NO ACTUATOR DERIVATION: x_press is ABSENT (TC-8 0/8).
  The 0.3 N*s per-tick per-channel press (jn/dt = 60.0 N) is a DECLARED fixture
  operating point (F03 S1), never an actuator qualification; no action channel
  may write contact forces, welds or poses directly; the trained climb channel
  must DECOMPOSE INTO CAPPED SERVO INTENTS (the K05 composition law). The G06
  climb channel (a declared kinematic schedule) is NOT an available actuator.

### 2.3 Intent seam

The only climb-specific commands are the U05 climb / let-go intents (versioned
semantics) at the existing command boundary; the frozen walk contract remains
unchanged; no retraining is required for a UI remapping (U01 law).

## 3. Reward — the goal's physical criteria ONLY

Reward credits exactly three physical outcomes of the registry row's skill
family, evaluated per tick from delivered observables only:

- R1 SUPPORTED ASCENT: per-tick credit for measured rise ONLY while the per-tick
  support law holds (transfer phase: every HOLDING channel records stick;
  load/hold/load2/hold2: every channel stick) and the transfer-phase
  admissibility equals the sealed G01 row at (reading, n-1): closed form
  (m/(n-1))*g*DT <= mu_s*jn per channel, per-channel transfer capacity
  mu_s*jn = 0.18 N*s at the declared operating point. Ascent needs
  potential-energy change plus losses under the declared model (C20); energy is
  accounted, never assumed.
- R2 HOLD: per-tick credit for supported hold with EXACT gravity==friction
  accounting and the press/losses account inside the declared bound (the
  measured press cost at the scene operating point is 0.040346690644887555
  J/tick — a CONDITIONAL-CALCULATION, not a budget grant).
- R3 CONTROLLED DESCENT: credit only for descent following the declared
  brake-template profile. Controlled descent closes exactly where the hold law
  closes; release is separated from descent by exact identities (release:
  gravity work == KE gain == 19.320355586443497 / 19.320355586289068 J; free
  fall to 1.9620000000000002 m/s in 40 ticks). An observed free-fall release is
  the failure arm of descent, never a descent credit.

Exclusions (law, not preference): NO reward term for grasp establishment,
approach geometry or contact acquisition (the grasp chain and the K01
approach-seam scaffold own those; the approach seam is declared scaffold — gap
10 — and is never rewarded); NO shaping on simulator-internal quantities; NO
term may read privileged or `x_*` information (privileged_forbidden). Reward
components are computed from the delivered observation samples of section 1
only.

## 4. Termination conditions

- T1 SLIP-STOP: the first slip-mode tick recorded at a HOLDING channel during
  load/hold/transfer terminates the episode (the sealed slip recursion is the
  stop law). Slip observed at a lawful failure case is the honest outcome, is
  recorded, and is never reset away.
- T2 RELEASE: removal of support removes its forces (G07 law); an undeclared
  release (one not following the declared descent/release schedule) terminates
  the episode as a failure.
- T3 ENVELOPE BREACH: a transfer whose (reading, n-1) admissibility row is
  falsified mid-episode (the m/(n-1) law breach) terminates with the slip
  recursion; the envelope is never expanded mid-episode to hide the failure.
- T4 INTEGRITY: any seam refusal (undeclared_field, named_absent_occupied,
  privileged_source, dim_mismatch, timing_*), any ledger-identity breach
  (intervention ledger fires), or any NaN/Inf terminates the episode as a
  harness verdict, distinct from physical failure.
- T5 HORIZON: the declared scenario horizon (the G06 template shape: 229 ticks
  per scenario; climb-template envelope span 219 ticks from attach) ends the
  episode; horizon end without success metrics met is a failure, never a pass.
- Termination codes are recorded per seed per episode; failures are retained;
  there is no concealed reset, no teleport, no leftover constraint (C13); a
  termination is not a success.

## 5. Success metrics — the map's frozen gates, evaluated separately (K04 law)

Success is claimed per phase, per seed, with failures visible; "each claimed
behavior meets frozen metrics; failures and unsupported cases are visible";
"an ascent success cannot stand in for controlled descent":

- M-ASCENT: every declared envelope tick of every executed transfer records
  admissible support (the 219-tick contiguous span class from attach through
  hold2 end), and the completed rise matches the declared template accounting
  (3 transfers x 0.38599999999999995 m = 1.158 m = trunk height; 687 ticks;
  mean template rate 0.33711790393013097 m/s; stage D
  accel/cruise/brake/hover schedule) with the energy account closed.
- M-HOLD: supported hold for the declared window with exact gravity==friction
  accounting, press cost inside the declared account, and zero cumulative
  creep in the stick class (the fixture stick class records EXACT ZERO creep;
  any nonzero creep is recorded as a finding, never normalized).
- M-DESCENT: the descent rate profile stays inside the brake template for the
  declared window, AND every executed release reproduces the free-fall identity
  (19.320355586443497 / 19.320355586289068 J; 1.9620000000000002 m/s in 40
  ticks) within the declared windows.
- Threshold law: the frozen numeric thresholds are the corrected-corpus rows —
  band n=3 transfer requirements 0.13243500000000002 / 0.15082875 /
  0.16922250000000003 N*s vs capacity 0.18 N*s (thinnest margin
  0.010777499999999968 N*s); the FROZEN FAILURE REGIONS are every scene-line
  transfer row (scene n=3 required 0.24618190095000003 N*s; scene n=2
  0.49236380190000006 N*s) and all n=1/n=2 transfer rows (band n=2
  0.26487000000000005 / 0.3016575 / 0.33844500000000005 N*s); static closure
  thresholds are per-reading corrected values (scene n=3 0.5468840727038888
  standard-g / 0.5470708910000001 record-g; band n=3
  0.2941995 / 0.33506054166666666 / 0.37592158333333336 standard-g; band n=2
  0.44129925000000003 / 0.5025908125 / 0.563882375 standard-g; scene n=2
  0.8203261090558333 standard-g). All are CONDITIONAL-CALCULATION rows carrying
  assumptions A1-A7; all are frozen BEFORE training; no threshold is re-derived
  or re-pinned mid-run.
- Reporting law: per-seed receipts; no cherry-picking; no additional tuned runs
  (W06 law); a failed result is not an implementation success; verdicts
  numerical/visual/human stay separate.

## 6. Seeds (declared NOW, before any training exists)

- The climbing runbook executes THREE preregistered seeds, fixed by this
  specification before any training run: **20261002, 20261003, 20261004**.
  These are preregistered constants (declared following the operator-prescribed
  walk1m-r1 dating convention), not measurements and not tunables. Any change
  is an amendment to this spec BEFORE training; "no seed substitutions or
  success-driven reruns" (K03 law) applies verbatim thereafter.
- Runbook identity: runbook_id `climb1m-r1` (the climbing analogue of the
  executed walk1m-r1 = chimera.w05_runbook.v1, whose precedent is 1,000,000
  decisions per seed = 2000 SPSA iterations x 2 antithetic evaluations x 250
  decisions = 15,000,000 ticks per seed at 300 Hz —
  `w05_evidence_receipt.json`
  sha256 `732da7185b8033a862836ad0e143998a6e52e34761e2b61f649d06e586943f60`,
  head_sha `7aaf145981e767b1296f2c3e0ebf3b62f2f66856`, seed receipt raw_sha256
  `b866e9b1e2a3d516a960a88362c95d2f8211d28b894cc4d8c16dcebc4dc8b896`). The
  exact climb macro-decomposition (iterations x antithetic x horizon) is a
  K03-entry prereg obligation that MUST pin this spec's seed block by hash and
  MAY NOT change the seeds. All of it is CONDITIONAL on section 0.4.
- Every episode's RNG draws derive from the declared seed; determinism,
  checkpoints and unchanged acceptance criteria are K03 obligations under P04
  reservations.

## 7. Training envelope (frozen before training; CONDITIONAL-SPECIFICATION)

- E1 CORRIDOR LAW: training runs against THE CLOSING REGION ONLY — the band
  n=3 corridor at the placeholder mu_s = 0.6 (transfer rows
  0.13243500000000002 / 0.15082875 / 0.16922250000000003 vs 0.18 N*s; static
  rows 0.2941995 / 0.33506054166666666 / 0.37592158333333336 standard-g).
  Training against a non-closing region would optimize impossible physics and
  is refused by this spec.
- E2 FROZEN FAILURE REGIONS: the scene-line transfer rows and all n=1/n=2
  transfer rows (numbers in section 5) are frozen failure regions; an episode
  executed there is a failure-region episode, reported as such, never trained
  into a pass.
- E3 n=4: the n=4 shape (required 0.1641212673 N*s <= 0.18; P_req
  54.70708910000001 record-g / 54.68840727038889 N standard-g; mu_crit
  0.5470708910000001) is a DERIVED-PREDICTION and FEASIBILITY CANDIDATE —
  "the only shape this arithmetic does not refute". Its five unmet
  demonstrations — (a) fourth-contact reachability, (b) simultaneous
  sustainability, (c) load-sharing, (d) contact independence, (e) dynamic
  transfer — are the test plan; none is closed by any current document; the
  declaration is a SEPARATE DECISION, NOT MADE HERE.
- E4 TRUNK: ONE rigid trunk (trunk_01; declared 0.074 m diameter x 1.158 m
  height; lateral sites); the grasp closure at the declared 74 mm trunk is
  OUTSIDE for the recorded hand (wrap margin -0.01733690019744087 m,
  mu-independent) and UNDECIDABLE for the anatomical achievable aperture
  (pincer mu_crit 0.8399663223427114 vs placeholder 0.6; chord window
  0.06345447650272827 m) — the grasp chain, not this spec, resolves it. This
  spec consumes the trunk geometry as the F03-declared rigid environment only.
- E5 TEMPLATE: the G06 229-tick scenario shape (approach 1, attach 4, load 8,
  hold 11, handover 31, transfer 31, re-attach 193, attach2 193, load2 197,
  release 220); climb-template envelope span 219 ticks from attach;
  fixture reach envelope 0.5 m (template travel 0.38599999999999995 m;
  x_reach ABSENT — fixture kinematics, not anatomy).
- E6 DYNAMICS IDENTITY: training and shipped dynamics are identical within the
  W04 certificate machinery; the 300 Hz tick, 20 Hz policy cadence, hold_ticks
  15 identity carries; the velocity envelope V = 2.977443609022557 m/s and the
  cross-build non-regression margin 0.03103119967715015 m/s are the declared
  walking-line envelopes carried until a climbing re-derivation supersedes them
  by a recorded decision. Claim class: offline/trace qualification at the 300 Hz
  tick is the ONLY satisfied execution class; interactive real-time 300 Hz is
  NOT satisfied (COST-GAP fired) and is never claimed by training receipts.
- E7 SCREENING BAND: the F-A falsifier band [0.3, 1.0] is a DECLARED screening
  band, not a measurement envelope. The mu = 0.41 scenario (capacity
  0.12299999999999998 N*s; NO transfer case closes; only band n=3 static
  closes) is a declared scenario parameter producing a NON-CLOSING corridor —
  usable only as an honest failure arm, never as a training corridor.

## 8. Falsifiers (each names the observation that would CONTRADICT it)

- F1 CORRIDOR-BREACH: prediction — under the frozen operating point the
  scene-line transfer rows cannot close (required 0.24618190095000003 N*s >
  capacity 0.18 N*s). A sustained closing scene-line transfer under the frozen
  conditions would falsify the bound. Observing the predicted refusal supports
  the prediction; the contradicting observation is NAMED: a supported transfer
  tick at a scene-line (reading, n) row inside its declared envelope span.
- F2 PLACEHOLDER-DRIFT: prediction — every threshold in a receipt reproduces
  bit-exactly from the corrected canonical paths of the pinned corpus. The
  contradicting observation is NAMED: any receipt threshold differing at any
  ulp from the pinned corrected rows, or any re-pin of mu mid-run ("no re-pin
  of mu mid-run" — the placeholder-mu law).
- F3 ADHESION: prediction — a zero-mu arm slides under full press (sealed
  control: 0.05150250000055512 m). The contradicting observation is NAMED: a
  sticking zero-mu arm (an adhesion defect in the contact law).
- F4 METRIC-SMUGGLING: prediction — reported success carries per-phase metrics
  for every claimed phase. The contradicting observation is NAMED: an ascent
  success reported while descent metrics are absent (or vice versa) — an ascent
  success cannot stand in for controlled descent.
- F5 HIDDEN-ASSIST: prediction — every accepted observation sample carries
  exactly the declared key set with an empty privileged registry. The
  contradicting observation is NAMED: an accepted sample containing an
  undeclared, solver-internal or `x_*` key (the seam must refuse it;
  unguarded-bus acceptance is the contradiction).
- F6 SPEC-EQUALS-SKILL: prediction — this card's completion is a frozen,
  approved specification. The contradicting observation is NAMED: any claim or
  receipt text asserting that this approval constitutes a trained policy, a
  physics qualification, or progress toward the playable objective ("a
  completed specification is not a trained skill"; "DEMONSTRATED IMPOSSIBILITY
  CAN CLOSE AN INVESTIGATION, BUT IT CANNOT COMPLETE THE PLAYABLE-MONKEY GOAL";
  a diagnostic pass is not the playable objective).
- F7 n=4-EXPANSION: prediction — n=4 remains a FEASIBILITY CANDIDATE until its
  five demonstrations are sealed. The contradicting observation is NAMED: any
  text or receipt claiming n=4 closes, opens the corridor, or is the lawful
  ascent shape without the five sealed demonstrations.

## 9. Approval and the training gate order

1. The Lieutenant commits this draft ALONE FIRST (separate-first); the
   committed bytes are the freeze. A seal does not replace the required commit.
2. This spec is then APPROVE-ABLE on its own evidence: hash consistency against
   the corrected corpus (the sealed consistency gate of this lane), the gate
   receipts of G08/U05, and the pinned certified records cited above.
3. K03 training dispatch waits ONLY on (a) the grasp chain producing a
   qualified grasp configuration (section 0.4 items 1-7), and (b) this spec's
   committed freeze. Nothing else. The K02 lane (reset scenarios) proceeds on
   the K02 draft pinned to this spec's bytes.

## 10. Out of scope (explicitly)

Ascent/hold/descent EXECUTION (K03/K04); reset construction (K02 draft, this
lane, separate file); friction measurement (NB-01/02, acquisition lane);
substrate strength (gap 8); the n=4 shape declaration (separate decision); the
mass-lineage selection (gap 9, owner's decision); any anatomical reset (K02's
fixture-only law); any claim that this document trains, qualifies or completes
anything.
