# PREREGISTRATION (DRAFT) — K01 climb-chain opener: APPROACH-TO-GRASP + GRASP ESTABLISHMENT

Status: DRAFT authored by `wk-k01-prereg` for the Lieutenant. Per the publication
law this file is committed ALONE FIRST (separate-first; the M03/P04 law) BY THE
LIEUTENANT; the committed bytes are the freeze and every emitted receipt must
embed `preregistration_sha256` of exactly those bytes and refuse any mismatch.
No implementation file, harness run, measurement or capture frame of this card
exists at draft time. Write scope of the draft: the NEW lane dir
`E:/ChimeraWork/monkey-coordination/k-tier/` (NO_WORKTREES law honored; no
worktree, no clone; all CPU verification through
`python -B E:/PythonChimera/tools/monkey_campaign/task_package.py seal|run`).

- Card MAT2-K01 (planning id K01), agent-author `wk-k01-prereg`, lane
  `E:/ChimeraWork/monkey-coordination/k-tier/`.
- Registry row (verbatim, `MONKEY_COMPLETION_MAP.md`
  sha256 `0e3984578b0cae38ab435daaa77cc10559cceeadbaf9885c3f31b979a362ecae`,
  re-hashed 2026-10-01): "K01 | Freeze the climbing skill specification |
  G08, U05 | C10, C21 | Observations, actions, reward, termination, success
  metrics, seeds, envelope and falsifiers approved before training | First
  skill family: attach, ascend, hold, descend, release".
- Build line: the W10/U07 integrated line
  `a30bfb9fc0ac4c46fb677224a76814d349c1e286` — verified this session by
  `git cat-file -t` = commit; subject "MAT2-U07: runtime control commands
  (PR #312; r1 pixel-gate correction APPROVED by sgt-review-312b, evidence
  43f1a3b9)", committed 2026-10-01 19:20:08 -0500. The W10 walking acceptance
  (winner head `c31a14b6cf5357df070985ab83d0c040e824eee2`, w10 evidence
  receipt) is an ancestor side of this line and is SEALED — NOT re-claimed.
- Dispatch map position: K01 is the OPENER of the staged climb chain
  K01->K02->K03->K04->K05->K06->K07->K08
  (`climb-derivation/DERIVATION.md` section 5, sha256 of that file pinned in
  section 1 below). This prereg is ONE CHAIN STOP: K01 only. K02+ are NOT
  authored here.
- Criteria consumed: C10, C21 (per the registry row). Named registry
  prerequisites G08 and U05 are carried as prerequisite NAMES; their closure
  status is a dispatch concern of the Lieutenant and is not asserted here.

## 0. The provisional baseline and the lineage basis (applied, never approved)

THE PROVISIONAL BASELINE LAW (binding wording): the 10.037998 kg certified
line is the PROVISIONAL baseline for every K-tier card, PROVIDED its receipt
binds the actual body composition, mass ownership and runtime configuration.
A hash establishes identity; it does not by itself establish correct mass
accounting. Every K-tier document carries this law and the open items of
section 0.2.

THE LINEAGE BASIS (recorded verbatim in every K prereg): the Captain's
standing criterion is "select body mass and ownership from authoritative
assembly evidence, never to obtain a passing result" (goal text + correction
order #3). The assembly-identity comparison
(`assembly-identity/ASSEMBLY_IDENTITY.md` sha256
`2ab248bda4db799685a5be9f446bb3e731a47b40b9db1108072cce18bafad035`,
re-hashed 2026-10-01; its section 8 scoping) shows ONLY the 10.037998 kg line
is a body any sealed receipt hashes; the 5.4-6.9 kg band is three unsealed
scalars. THEREFORE the K-tier preregs assume the 10.037998 kg certified line
as DYNAMICS; climb-corridor arithmetic played NO role in the selection — the
comparison's own law is verbatim: "climb-corridor arithmetic is NOT and never
was a selection input to this document", and a corridor that closes more
easily at a lower declared mass is not evidence that a band-mass body exists
(ASSEMBLY_IDENTITY section 8).
LINEAGE APPLIED PER THE CAPTAIN'S EVIDENCE CRITERION; SUBJECT TO HIS ONE-WORD
VETO. This is the application of a stated selection criterion — never an
approval, and neither silence nor a veto-opportunity is approval of the
separately reserved decision. THE RESERVED DECISION STAYS OPEN in every
document: KEEP-10.038-AS-DYNAMICS | ORDER-BAND-MASS-ASSEMBLY |
ROUTE-TO-WALK-TIER-CARD (ASSEMBLY_IDENTITY section 5). No K-tier artifact
closes it.

### 0.1 What the 10.038 sealed receipts actually BIND (verified this session)

- COMPOSITION AND PER-PART MASS OWNERSHIP — `evidence-store/MAT2-D-MASSREG/
  numerical/mass_register.json` sha256
  `61fb79b1bf2df8c5e1a5b1bff2ab1c4f41700de25bc7f1a114cbc78fe693cc7a`
  (re-hashed 2026-10-01, matches the ASSEMBLY_IDENTITY section 7 pin): the
  scene system carries 15 register rows of which the 14 training/walk-scene
  bodies are, per part: pelvis 7.371998 kg (validation note: "pelvis = HAT
  8.184 - 2x0.406001 Oku arm-chain carve"), thigh 0.557 x2, shank 0.269 x2,
  foot 0.08 x2, toe 0.021 x2, fore upperarm 0.2737 x2, forearm 0.1323 x2,
  ground 0.0. Register totals: builder_order_sum_kg 10.037998000000004
  (bit_exact false, within_float_floor true, declared honestly), scene carve
  sum 10.037998 (reproduced bit-exact), scene_body_total_kg literal "10.038".
- RUNTIME CONFIGURATION — `b07-prereqs/RUNTIME_CONTRACT.md` sha256
  `f33c188bcb561b1946b104340cf36cba366709526c095874684529a599df338c`
  (re-hashed 2026-10-01): `assembly_mass_kg 10.037998000000004 (weight_N
  98.43913308670002)`; servo drive caps hip 11.2125 / knee 6.6375 / ankle
  7.4 / MP 0.8875 N*m (hind, both sides), fore shoulder 4.229 / fore elbow
  3.76 N*m; 18 coordinates. W04 qualification chain:
  `evidence-store/MAT2-W04/numerical/w04_certificate.json` sha256
  `07f05bfa982e066ae67413b04e3367c5ad7570830e99fc32edcb86cbe8d87598` and
  `w04_freeze_manifest.json` sha256
  `be632ffc85865515285f3d622a09882a3180a43101027914f1ed3408496f5d29`
  (both re-hashed 2026-10-01, matching the ASSEMBLY_IDENTITY section 7 pins).
- ADOPTION MASS LAW — `evidence-store/MAT2-B07/unclassified/
  adoption_record.json` sha256
  `f6952e8afc778f79a0ede05b61d73dd7c3fabd68789703552cd6136e25ef0199`
  (re-hashed 2026-10-01): `mass_law_carried.certified_walking_body_kg`
  = 10.037998 ("UNCHANGED in every scene/ledger"); counted mass of the
  adopted Buffy02-lineage assembly 0.0 kg; transported 17.039978509953905 kg
  deliberately non_consumed; TC-7 body-domain digest in THIS store revision
  = `chimera.b07.adoption.a971dce72c1d494b481ba06acf8e0dd4`, domain tag
  `material-assembly/buffy02-lineage`, qualification_state NOT
  runtime-qualified (TC-8 measured inputs 0/8 ports, honest refusal stands;
  drive table not re-declared).

### 0.2 Open items preserved (unresolved assembly discrepancies; explicit)

These are UNRESOLVED and stay open in every K-tier document:

- OI-1 The TC-7 adoption digest is revision-relative, not a stable body
  identity: three byte-revisions of `adoption_record.json` are
  decision-identical with THREE different tc7 digests (W04-bound
  `…240b457bc9612111173314b49f453b80`; evidence-store copy `…a971dce7…`
  (the revision re-hashed in section 0.1); sgt-pr294 determinism revision
  `…206012d8…`) — ASSEMBLY_IDENTITY section 6.1, flagged to the
  Lieutenant there and carried here.
- OI-2 Specimen class of the scene line is
  `internally-inconsistent-female-band` (register rows,
  specimen_class_receipt `c4d05e69…`): a standing biological inconsistency,
  escalation-flagged, carried as-is, NOT repaired by any K-tier artifact.
- OI-3 The two sealed mass systems stay DISTINCT (register reconciliation
  REFUSED upstream): the band 5.4 / 6.15 / 6.9 kg is a three-scalar BW
  reference with NO assembly identity; it never enters K-tier dynamics.
- OI-4 Builder-order 14-body sum 10.037998000000004 vs carve literal
  10.037998: declared float-floor disclosure (register totals block,
  bit_exact false, within_float_floor true) — carried, not silently
  rounded.
- OI-5 Provenance honesty of this session: the raw W03 `scene.json` bytes
  (sha256 `f6844eeae3dc87170a572ccdeedf326a6cac4f73d1448941808bd8b25a8db342`
  per `GAIT_BENCHMARK.md` line 25 and the sealed wave47 receipt anchors;
  re-hashed on disk in the assembly-identity lane's own session) were NOT
  re-hashable this session — the store copy path named by
  ASSEMBLY_IDENTITY (`MAT2-W03/scene_out/scene.json`) is absent on disk
  now. Identity is carried by the three independent records above; the Lt
  may order a byte-level re-anchor before dispatch. Recorded as unresolved.

## 0.3 The objective law (verbatim, binding on every outcome reading)

"DEMONSTRATED IMPOSSIBILITY CAN CLOSE AN INVESTIGATION, BUT IT CANNOT
COMPLETE THE PLAYABLE-MONKEY GOAL." Standing rule for every infeasible
configuration encountered under this prereg: record the result, then either
identify a physically justified change WITHIN the project's authority (a
declared-synthetic parameter, a geometry choice, an actuator within
anatomical bounds — NEVER a tuned measured value) or escalate the specific
decision needed to the Lieutenant with bounded options. The playable
objective stays OPEN until the positive behavior is demonstrated; no
measured value is ever tuned to force success. A correctly predicted refusal
can COMPLETE A DIAGNOSTIC EXPERIMENT but does NOT complete the playable
grasp objective — the objective needs the positive behavior or its
demonstrated impossibility under RESOLVED (not placeholder) parameters.

## 1. Scope — what K01 is here (one chain stop)

BEHAVIOR UNDER TEST: the walk-to-trunk APPROACH terminating in a physical
grasp ATTEMPT of the certified contact line — `trunk_01.lateral` (F01 asset,
exact analytic cylinder radius 0.037 m, diameter 0.074 m, height 1.158 m,
32-segment contact mesh; G06 fixture contact sites sit ON this trunk at
radial distance ~0.037 m), in the W10/U07 integrated build line a30bfb9f,
on the PROVISIONAL 10.037998 kg baseline.

IN SCOPE (the three legs this card measures):
1. THE APPROACH CONTROLLER SEAM: the declared transition from the certified
   walking behavior to the trunk-adjacent terminal state. F05 placement law
   ends the walk >= 2.0 m from the trunk (trunk min distance; obstacles
   route-around; step-over NAMED-ABSENT, owner F06) and NO
   approach-to-grasp transition geometry is declared anywhere in records
   (DERIVATION gap 10) — K01 DECLARES this seam as scaffold, labeled as
   scaffold, and measures the approach against it. The certified walking
   acceptance is NOT re-claimed and no walking policy is re-tuned.
2. THE GRASP CLOSURE ATTEMPT: the physical attempt to establish the grip at
   the declared diameter, in the declared pad-fixture class (the G04/G06
   DECLARED pad pattern, G04 section 9 disclaimer inherited) and, as a
   RECORDED arm only, the recorded fingertip configuration's wrap/pincer
   arithmetic. The attempt is measured; the refusal modes are measured with
   it.
3. THE CONTACT ESTABLISHMENT EVIDENCE: per-contact records at the declared
   sites — normal press jn, tangential jt, press impulse, stick/slip class
   per tick, the slip recursion when it fires — keyed per phase like the
   G05/G06 seam pattern.

OUT OF SCOPE (fenced, not smuggled in):
- ASCENT, HOLD-AT-HEIGHT, DESCENT, RELEASE-RESUME: later K cards
  (K02-K08 staged chain). The static-hold and transfer bounds appear in
  section 2 ONLY as the claim-fencing table requires; K01 runs no ascent,
  no descent and no transfer phase.
- THE n=4 SHAPE DECLARATION IS A SEPARATE DECISION, NOT MADE HERE. The
  four-contact FEASIBILITY CANDIDATE (DERIVATION section 8.3; five unmet
  demonstrations: (a) fourth-contact reachability, (b) simultaneous
  sustainability, (c) load-sharing, (d) contact independence, (e) dynamic
  transfer) becomes K01's test-plan obligation ONLY IF the Captain later
  declares n=4. None of the five demonstrations is assumed, cited or
  tested by this card.
- TRAINING SPEC ITEMS THIS LEG CANNOT GROUND: reward shaping, termination
  law and seeds for TRAINING are K01-registry done_when items that the
  chain freezes at K03-entry; they are carried in the honest-absent
  inventory (A8), never invented here.
- RESET SCENARIO CONSTRUCTION (K02), skill arbitration (K06), any
  substrate/strength measurement (gap 8), any friction measurement
  (acquisition lane owns NB-01/02).

## 2. The claim-by-claim table (SEPARATE CLAIMS; every numeric bound fenced)

LAW (Captain correction #2, binding): approach, contact establishment,
grasp, static hold and climbing transfer are SEPARATE claims. The
derivation's no-closing-transfer bound at the scenario parameters rules out
ONLY the transfer claim under its assumptions — it does NOT rule out
approach, contact establishment, or grasp. Every numeric bound in the corpus
is fenced below: exactly which behavior it constrains, and which behaviors
it does NOT touch. Labels: every threshold below is a
CONDITIONAL-CALCULATION of the declared models under assumption set A1-A7
(DERIVATION section 8.1: declared mass line; declared contact count from the
G06 fixture pattern; DECLARED 60.0 N press ceiling jn/DT with TC-8 ports 0/8;
DECLARED pad fixture class; mu placeholders; declared static
P_req = W/(n*mu), transfer (m/(n-1))*g*DT <= mu*jn = 0.18 N*s, and
two-contact Coulomb cone/chord law forms; DECLARED F-A band [0.3, 1.0]).
No number below is a measured monkey-bark value.

| # | bound (verbatim value, source) | constrains ONLY | does NOT touch |
|---|---|---|---|
| B1 | wrap margin `-0.01733690019744087` m (recorded span `0.056663099802559125` m vs diameter 0.074 m; sealed G01 OUTSIDE row; DERIVATION stage A; mu-INDEPENDENT — friction cannot add chord length, SGT_GEOMETRY_REVIEW MANDATE 1) | WRAP closure of the RECORDED fingertip configuration at 74 mm | approach; contact establishment of the declared pads; static hold (fixture class); transfer; the ACHIEVABLE aperture (unbounded — x_aperture ABSENT) |
| B2 | WRAP-2 pincer closure bound: span needs `>= 0.06345447650272827` m at mu=0.6, i.e. mu_crit `0.8399663223427114` (two-contact Coulomb model, smooth disk R=0.037, quasi-static; grasp-geometry derivation, Sergeant-verified, SCOPE-LABELED) | two-contact PINCER closure of the recorded span at the declared placeholder geometry | multi-contact press-class closure; approach; hold; transfer; any anatomical hand claim (achievable aperture ABSENT) |
| B3 | PINCH contact class NOT ANALYZABLE (palm patch record missing; grasp-geometry MANDATE 3) | nothing — an ABSENCE of analysis, recorded as absence | no numeric constraint exists; absence is never cited as a refusal |
| B4 | static hold, scene n=3: P_req `54.68840727038889` N std-g <= 60 N declared press -> WITHIN at placeholder mu=0.6; closure threshold mu >= `0.5468840727038888` std-g (`0.5470708910000001` rec-g) (CORRECTED 2026-10-01 static law; DERIVATION section 7 table). The full corrected static closure table consumed by K-tier (std-g; rec-g duals): band n=2 lo `0.44129925000000003` (`0.44145`), mid `0.5025908125` (`0.5027625`), hi `0.563882375` (`0.5640750000000001`); scene n=2 `0.8203261090558333` (`0.8206063365000001`); scene n=3 `0.5468840727038888` (`0.5470708910000001`) — all INSIDE the F-A band; at the declared parameter 0.41 only band n=3 static closes (thresholds `0.2941995` / `0.33506054166666666` / `0.37592158333333336` std-g) | STATIC HOLD of the declared pad-fixture class at the certified line, n=3, at/below the named mu threshold | approach; contact establishment; grasp closure; transfer (different law); NOT a prediction about mu=0.41 (see B7) |
| B5 | climbing transfer, scene line: requirement `0.24618190095000003` N*s > capacity 0.18 N*s at n=3; `0.49236380190000006` at n=2 -> DOES NOT CLOSE at any tested n (DERIVATION stage C / section 6 item 1) | the CLIMBING TRANSFER claim of the certified line under the declared law, at tested n | approach; contact establishment; grasp; static hold. THE STRUCTURAL NEGATIVE FENCES NOTHING ELSE |
| B6 | the hand problem: `m_eff = 0.048761970806378674` kg vs prop impulse `0.49236380190000006` N*s/tick (ratio ~1/205; PAIR-PATH finding a; DERIVATION section 2) | static support THROUGH THE ANATOMICAL 0.049 kg HAND BODY in this solver (hold-at-height UNDECIDABLE until TC-3 re-declaration + TC-8 ports or a declared solver treatment) | the fixture-class grasp diagnostic (declared pads inherit the `3.3459993333333333` kg declared trial inertia); approach; grasp-closure arithmetic |
| B7 | the mu=0.41 DECLARED SCENARIO PARAMETER (see section 3): scene n=3 static NOT closed (0.41 < 0.5469); NO transfer case closes at 0.41 anywhere (band_lo n=3 needs `0.13243500000000002` > capacity `0.12299999999999998`) | static hold and transfer verdicts AT THE DECLARED PARAMETER 0.41 | approach; contact establishment; grasp geometry (B1 is mu-independent); no claim at other mu |
| B8 | F05 placement: walk ends >= 2.0 m from the trunk; min route clearance 0.257478 m; step-over NAMED-ABSENT (owner F06); no declared approach-to-grasp transition geometry (gap 10) | the APPROACH's declared end state; the seam this card declares | contact establishment; grasp; hold; transfer. NOTHING in records predicts approach completion — that is K01's measurement obligation |
| B9 | actuator caps hip 11.2125 / knee 6.6375 / ankle 7.4 / MP 0.8875; fore shoulder 4.229 / elbow 3.76 N*m (RUNTIME_CONTRACT lines 111-112, 221-222); NO derivation caps -> 60 N grip normal exists (gap 6; TC-8 ports 0/8) | what any ANATOMICAL-drive grasp press must still demonstrate (x_press DEBT; actuator-capacity condition) | the DECLARED fixture press operating point (60.0 N, declared, never actuator-qualified); approach; hold arithmetic |
| B10 | x_aperture / x_reach ABSENT (C05 joint-kinematics OPEN INVENTORY; C01 frame round-trip debt; gaps 4-5) | nothing numerically — ABSENCE recorded | makes every achievable-aperture grasp prediction UNDECIDABLE-BY-RECORDS; it rules nothing out and nothing in |

## 3. Friction provenance and the mu label (binding on every use)

- mu_s = 0.6 / mu_k = 0.4 are NAMED PLACEHOLDERS (FRICTION_SOURCES verdict
  GAP; REPIN ORDER 2; acquisition gap NB-01/02 STANDS). Monkey-bark friction
  (macaque volar skin on bark at the 20-60 N operating load) is UNMEASURED —
  the corpus master verdict is verbatim: "NO measured macaque volar skin on
  bark value exists anywhere in the corpus" (DERIVATION section 8.4).
- THE 0.41 VALUE IS A DECLARED SCENARIO PARAMETER, labeled on EVERY use: it
  is the human-analogue transfer value (Gerhardt et al. 2008 — HUMAN volar
  forearm on cotton/polyester TEXTILE at 14.8±1.3 N, natural-dry 0.41-0.42)
  — NOT monkey-bark, NOT a measurement of the target interface. Every
  literature number in this corpus is nearest-available-analogue class
  (DERIVATION section 8.4 audit; NB-01/02 stands).
- The F-A falsifier band [0.3, 1.0] is a DECLARED screening band (A7), not a
  measurement envelope.
- THE PLACEHOLDER-MU LAW: no re-pin of mu mid-run. A K-tier run that begins
  at a declared mu finishes at that mu; parameter changes are new preregged
  runs, and no measured value is ever tuned to force success (section 0.3).

## 4. Frozen predictions and tolerances (at the certified n=3 line)

All outcomes are read from committed per-tick records of the a30bfb9f build
running the declared scene; every number a check compares against is
DERIVED AT RUN from the pinned corpus bytes (no hand-copied constants).
Honest predicted-outcome statement first, per discipline: UNDER THE CURRENT
PLACEHOLDERS the honest predicted outcome of K01 is a MIXED verdict — the
fixture-class contact establishment and n=3 static hold CLOSE (predicted);
the wrap/pincer grasp of the RECORDED configuration is REFUSED (predicted —
the refusal is the SUPPORTED prediction); the achievable-aperture grasp is
UNDECIDABLE (no prediction invented); transfer is fenced out (out of scope,
non-closing by B5). A prereg that predicts its own honest failure mode
where the parameters say so is correct discipline, NOT pessimism — and per
section 0.3 that predicted refusal completes a diagnostic experiment only.

- P1 APPROACH-SEAM `approach_terminates_at_declared_seam`: the frozen
  approach script drives the certified line from its sealed start to the
  declared trunk-adjacent terminal window; committed records show the walk
  in its certified state at termination, ZERO trunk contacts before the
  declared contact phase (no snap-to-tree — the K06 anti-snap law's
  upstream declaration), and the terminal base-to-trunk distance inside the
  frozen seam window. Tolerances: terminal distance within the declared
  window (declared below); contact count trunk == 0 pre-seam; zero
  undeclared contact sites. No corpus number predicts approach completion —
  this is a declared pass/fail measurement, honestly labeled as such.
- P2 CONTACT ESTABLISHMENT (fixture class)
  `declared_pads_establish_stick_class`: pressing the DECLARED pad set at
  the declared operating point on `trunk_01.lateral` records jn/jt at the
  operating point with stick-class contacts across the frozen window;
  per-tick press impulse inside the sealed fixture envelope. Negative
  control (falsifier arm FB2): the zero-mu control arm must SLIDE — the
  G04 zero-mu slide `0.05150250000055512` m under full press is the
  expected control reading; a zero-mu arm that sticks would contradict the
  friction law as applied and is preserved as a records discrepancy.
- P3 GRASP-WRAP OF THE RECORDED CONFIGURATION
  `recorded_config_grasp_refused`: PREDICTED REFUSAL. The recorded
  fingertip span `0.056663099802559125` m cannot wrap the 0.074 m trunk
  (margin `-0.01733690019744087` m, mu-independent, B1) and the two-contact
  pincer form at placeholder mu=0.6 requires span >=
  `0.06345447650272827` m (mu_crit `0.8399663223427114` > 0.6, B2).
  OBSERVING THE REFUSAL SUPPORTS P3 — it is not itself the falsifier. THE
  FALSIFIER: a SUSTAINED physical grasp by the recorded configuration at
  placeholder mu on the 74 mm trunk (sustained = holds the declared
  diagnostic load for the frozen window with zero slip-mode ticks) would
  CONTRADICT the wrap model or the span records — preserve as a records
  discrepancy for independent review, never as a win.
- P4 ACHIEVABLE-APERTURE GRASP `anatomical_grasp_undecidable`: NO success/
  failure prediction is made (x_aperture/x_reach ABSENT, B10; no synthetic
  constant occupies the absent slot). The run records the attempt evidence
  and its evidence class. Honest-absent, not a hidden pass.
- P5 STATIC HOLD AT THE CERTIFIED LINE (fixture pad class, n=3)
  `scene_n3_hold_closes_at_placeholder`: PREDICTED CLOSURE at placeholder
  mu=0.6 ONLY (P_req `54.68840727038889` N std-g <= 60 N declared press;
  threshold mu >= `0.5468840727038888` std-g, B4); PREDICTED NON-CLOSURE at
  the declared scenario parameter mu=0.41 (B7). Tolerance: per-channel
  press within the declared operating point; the mu=0.41 arm's failure
  mode must be the recorded slip recursion (named failure discriminator,
  not a harness error). FALSIFIER for the non-closure arm: a sustained
  static hold at declared parameter mu=0.41 with everything else frozen
  would CONTRADICT the static law as applied — preserve as a records
  discrepancy. Through the ANATOMICAL hand: NO hold prediction (B6,
  UNDECIDABLE) — K01 claims nothing about hand-body support.
- P6 TRANSFER (fenced, NOT run) `transfer_out_of_scope_nonclosing`: the
  scene-line transfer bound (B5: `0.24618190095000003` > 0.18 N*s at n=3)
  is recorded as the reason NO transfer phase is run by K01. If any later
  card runs it, its falsifier is: a sustained closing transfer under the
  frozen conditions would falsify the bound. Stated here ONLY so the B5
  refusal is never misread as a grasp, contact or hold refusal.

Refusal/prediction wording law (Captain correction #3, applied): a predicted
refusal observed is a SUPPORTED PREDICTION; each falsifier names the
observation that would CONTRADICT its prediction (P3: sustained recorded-
config grasp; P5: sustained hold at 0.41; P2/FB2: a sticking zero-mu arm;
P1: any undeclared contact, snap, or out-of-window terminal state).

## 5. Falsifier disposition summary

- Card-level falsifier class "refusal misread as completion" -> P3/P5
  wording law + section 0.3 objective law (a diagnostic pass is not the
  playable objective).
- "Placeholder drift" -> the placeholder-mu law (section 3) + run-time
  threshold re-derivation from pinned bytes (section 7).
- "Bound smuggling" -> section 2 claim table; any conclusion text that uses
  B5 (transfer) against grasp/contact/approach fails prereg compliance.
- "Undeclared n=4" -> section 1 fence; the five-demonstration plan activates
  ONLY on a Captain n=4 declaration.
- "Snap-to-tree assist" -> P1 zero-premature-contact requirement; a snap is
  a FAILED approach, recorded as such.
- "Hidden assist in the seam" -> the seam may not set any state the solver
  would refuse; the reset anti-assist law's upstream form (K02 row quoted
  in the dispatch map) is inherited as the seam's declaration.

## 6. Failure preservation, refinement checks, the standing infeasibility rule

- Every dev-run refusal and every failed arm is preserved in
  `DEV_RUN_REFUSALS.md` in the card package (honest negatives, never
  deleted); failure captures use the same declared views as success
  captures.
- REFINEMENT CHECKS: every threshold quoted in any report must be re-derived
  from the pinned corpus bytes at run time (section 7 pins); any mismatch is
  a refusal (`threshold_pin_mismatch`), never a silent update. The five
  RETRACTED defective static quotes (tabulated in DERIVATION.md section 7,
  including any use of the 0.9114-class value as a "scene n=3 static"
  label) MUST NOT appear in any K-tier artifact (DERIVATION section 7
  downstream requirement 1); the consistency gate asserts their literal
  absence from this prereg. The committed sensitivity prereg's mislabeled
  grid anchor is the wk-sens owner's amendment (k-tier/SENS_REPIN_NOTE.md),
  not a K-tier artifact.
- THE STANDING INFEASIBILITY RULE (section 0.3): on an infeasible
  configuration: record the result; then EITHER name a physically justified
  change within project authority (declared-synthetic parameter, geometry
  choice, actuator within anatomical bounds — never a tuned measured value)
  and prereg it, OR escalate to the Lieutenant with bounded options (the
  named-gap list of section 8 IS the option menu). The playable objective
  stays open until the positive behavior is demonstrated or its impossibility
  is demonstrated under RESOLVED parameters.

## 7. Input pins (verified byte-exact 2026-10-01; drift = refusal
`input_pin_mismatch` / `input_pin_missing`)

Corrected corpus (the numbers this prereg quotes live in these bytes):
- `E:/ChimeraWork/monkey-coordination/climb-derivation/DERIVATION.md`
  sha256 `da34420558f6632b0544ca94bc3e25ece515027628c7bd8cc54b9fdd30b7ebd9`
  (CURRENT corrected+scope-labeled bytes; supersedes the pre-correction
  `7e21792c…` and the post-correction pre-scope `59b8ab7f…` pins recorded in
  SCOPE_CORRECTIONS_EVIDENCE.md — the sensitivity harness re-pin is
  wk-sens's task, noted in k-tier/EVIDENCE.md)
- `climb-derivation/climb_derivation.py` `be1510dd3273fbc87d728b70bd65931a2381fee551fbf8f92da23cc9e31df237`
- `climb-derivation/derivation_output.txt` `534ac1f3dfe98bbfb14636704132ca192ca92f47e23cf1f065f9bd5032e2d73f`
- `climb-derivation/grasp-geometry/grasp_geometry.py` `e5614b3120dc9d663c204acf6a5db21f11e5c27c7616911f07eb385eee2cfc97`
- `climb-derivation/grasp-geometry/derivation_output.txt` `955956538d8b2e5236e77e14752352dd51c45065a1c5be8222efaa777965a4db`
- `climb-derivation/grasp-geometry/SGT_GEOMETRY_REVIEW.md` `30a2d6aeb6ed1059c1e416a7aa39ab3285cd3fa12013e8141dab20288a3ebc3b`
- `sensitivity/SCOPE_LABELS_ranked_table_20261001.md` `efe83ee027a5467af2349392469424a766dfb1eeadb4a3c373e1cd6d198590e4`
- `assembly-identity/ASSEMBLY_IDENTITY.md` `2ab248bda4db799685a5be9f446bb3e731a47b40b9db1108072cce18bafad035`
- `E:/PythonChimera/tools/monkey_campaign/MONKEY_COMPLETION_MAP.md` `0e3984578b0cae38ab435daaa77cc10559cceeadbaf9885c3f31b979a362ecae`

Sealed store pins:
- `evidence-store/MAT2-G01/report/REPORT.md` `e6d6c432680e503d5a70a1903ed59b52d5044cb8d3c7934da3b0db8acf3293a9` (the static-row standard-g authority)
- `evidence-store/MAT2-F05/source/FRICTION_SOURCES.md` `336118e929bd0b4fb067db5a448dc2e348fed073007787635549a4cf1cf5868b` (the friction GAP verdict)
- `evidence-store/MAT2-D-MASSREG/numerical/mass_register.json` `61fb79b1bf2df8c5e1a5b1bff2ab1c4f41700de25bc7f1a114cbc78fe693cc7a`
- `evidence-store/MAT2-W04/numerical/w04_certificate.json` `07f05bfa982e066ae67413b04e3367c5ad7570830e99fc32edcb86cbe8d87598`
- `evidence-store/MAT2-W04/numerical/w04_freeze_manifest.json` `be632ffc85865515285f3d622a09882a3180a43101027914f1ed3408496f5d29`
- `evidence-store/MAT2-B07/unclassified/adoption_record.json` `f6952e8afc778f79a0ede05b61d73dd7c3fabd68789703552cd6136e25ef0199`
- `b07-prereqs/RUNTIME_CONTRACT.md` `f33c188bcb561b1946b104340cf36cba366709526c095874684529a599df338c`

Git line pin: build line `a30bfb9fc0ac4c46fb677224a76814d349c1e286`
(commit verified this session; W10 winner head
`c31a14b6cf5357df070985ab83d0c040e824eee2` an ancestor side; w10 evidence
receipt `E:/ChimeraWork/monkey-coordination/w10_evidence_receipt.json`
sha256 `0e9c6de57665529d962a5ff3ec3fcf964a2283b9f7a665ad9abb160151bb7405`
records head_sha `c31a14b6…`).

Capture-gate pins (the standing two-stage gate of section 9):
- `E:/ChimeraWork/monkey-coordination/capture-gate-template/README.md`
  sha256 `331939f3156ca6158956e53c557cc324a3eeb0aa6a381b5170ec5ea83175ddb6`
  (the template's own-law file: two-stage gate, stage-0 palette blank-check
  retained, cannot-pass-without-gate, exit-code law)
- `E:/ChimeraWork/monkey-coordination/capture-gate-template/TEMPLATE_MANIFEST.json`
  sha256 `1c4d1dcad9af98c73e1aa4ebb46bff6359b9992e390b38c37fae578e779a59a7`
  (the manifest that pins every template module by sha256; card receipts
  cite it)

## 8. Honest-absent inventory (declared absences; the named-gap list per behavior)

Per behavior, the ACTUAL remaining conditions (Captain correction #5 — named
conditions, not "work" placeholders):

- A1 APPROACH — remaining conditions: the declared approach-transition
  geometry (ABSENT in records, gap 10; K01 declares it as labeled scaffold);
  F06 terrain-aware locomotion for any non-plan approach leg (step-over
  NAMED-ABSENT); the approach's contact qualification is the planar pad set
  only.
- A2 CONTACT ESTABLISHMENT — remaining conditions: contact QUALIFICATION is
  fixture-class only (DECLARED pads, G04 section 9); ANATOMICAL volar-skin
  contact on bark is unqualified and unmeasurable until NB-01/02 resolves;
  contact-site independence (pair-rule coupling) has no record.
- A3 GRASP — remaining conditions: GEOMETRY: achievable aperture x_aperture
  ABSENT (C05); hand-to-trunk transform x_reach ABSENT (C01); ACTUATOR
  CAPACITY: x_press ABSENT — no derivation from the N*m caps (B9) to a 60 N
  grip normal; TC-8 ports 0/8; CONTACT QUALIFICATION: palm patch record
  missing (B3); FRICTION UNCERTAINTY: monkey-bark UNMEASURED (NB-01/02);
  INTEGRATION EVIDENCE: runtime scene module executing the adopted assembly
  is named-missing (W04 section 7 heritage); the anatomical hand-body
  support problem (B6) is open (TC-3 re-declaration / TC-8 ports).
- A4 STATIC HOLD (as a later-card claim) — remaining conditions: the same
  friction uncertainty (B4 threshold 0.5469 vs unmeasured mu); the hand-body
  problem B6; press-cost accounting carries the G07 measured numbers
  (0.040346690644887555 J/tick scene hold) as fixture-class only.
- A5 TRANSFER (fenced to later cards) — remaining conditions: B5 stands;
  any n=4 route needs the Captain's declaration plus the five demonstrations
  of DERIVATION section 8.3; friction resolution per NB-01/02.
- A6 TRAINING-SPEC ITEMS: reward, termination and seeds for TRAINING are NOT
  frozen by this physical leg (K03-entry chain freeze; registry done_when
  items carried, honestly absent here).
- A7 n=4 DECLARATION: NOT made (reserved decision, section 1 fence).
- A8 MASS-ACCOUNTING OPEN ITEMS: OI-1..OI-5 (section 0.2) stay open in
  every downstream artifact.

## 9. Evidence obligations (numerical + visual)

- NUMERICAL: per-tick contact records (jn, jt, press impulse, stick/slip
  class per channel), the approach trace (base pose, contact set per tick),
  slip-recursion events keyed per phase (the G07 keyed per-phase extractor
  pattern), the negative-control arm (FB2), and the frozen-prediction
  verdicts P1-P6 as named variables with their derived constants. Every
  receipt embeds `preregistration_sha256` of the committed prereg bytes and
  refuses mismatch.
- VISUAL: captures use THE STANDING TWO-STAGE GATE once integrated through
  the card capture path (`capture-gate-template/` v1, 2026-10-01:
  stage-0 palette blank-check retained + stage-1 mask co-location; template
  law: a run cannot emit a pass without the gate having run). The
  "palette stage-0" minimum is the declared fallback floor if the template
  path is not yet wired for this card at capture time — the fallback is
  DECLARED here in advance, never silent, and a stage-0-only pass is labeled
  `gate_stage0_only` in the receipt. Declared views (candidate freeze, Lt
  may refine at commit): normal player camera; detail of the hand/trunk
  contact region; alternate-angle of the grasp site — each in clean +
  diagnostic pairs.
- All CPU verification through the runner: `python -B
  E:/PythonChimera/tools/monkey_campaign/task_package.py seal|run`; sealed
  manifest hash, base SHA, run receipt and exit status recorded in
  `k-tier/EVIDENCE.md` with sha256 of every load-bearing artifact.

## 10. Resource allowances (frozen draft values; the committed bytes are the freeze)

- Interpreter: `C:/Python314/python.exe -B` (the corpus's convention).
- CPU runner only; four fixed slots; BUSY (exit 75) = wait and retry with
  >= 10 s backoff; no new directories on BUSY.
- Scene cadence 300 Hz (the certified line's cadence). Frozen diagnostic
  windows (scaffold values, declared as scaffold): approach leg bounded by
  the certified run horizon 10500 ticks; grasp-attempt window 240 ticks
  (0.8 s) per arm; static-hold diagnostic window 20 ticks (the G07 20-tick
  hold precedent); zero-mu control arm 40 ticks (the G04 slide precedent).
  Declared-occlusion and gate receipts per section 9. Declared retained
  outputs per job <= the runner's 256 MiB admission.
- ONE chain stop: this card's package, seal, run and evidence land in
  `k-tier/` only; no other lane's bytes are edited (the sensitivity re-pin
  is wk-sens's; the note is delivered, not applied).

## 11. Resume state

- Draft authored by wk-k01-prereg in `k-tier/`; the Lieutenant commits this
  file ALONE FIRST, then hands back the commit pin; implementation lanes
  dispatch AFTER the committed prereg exists (a seal does not replace the
  required commit).
- The sensitivity harness RE-PIN + the 0.9114 anchor-label amendment are
  packaged in `k-tier/SENS_REPIN_NOTE.md` and `k-tier/EVIDENCE.md` for the
  wk-sens owner's next touch; no sensitivity-lane byte was edited from this
  lane.
- Open decisions awaiting the Captain/Lieutenant (bounded): the reserved
  lineage decision (section 0); any n=4 declaration (section 1); the
  approach-seam geometry adoption (A1); the friction bench acquisition
  (NB-01/02, acquisition lane). None is closed by this prereg.

## 12. Corrections ledger (applied verbatim obligations)

1. PROVISIONAL BASELINE — sections 0, 0.1, 0.2 (binding wording; receipts'
   actual bindings verified; open items preserved; lineage recorded as
   applied criterion, never approval; reserved decision open).
2. SEPARATE CLAIMS — section 2 claim-by-claim table (every bound fenced;
   B5 fenced to transfer only).
3. FALSIFIER WORDING — section 4 prediction/falsifier pairs (observed
   refusal SUPPORTS the prediction; each falsifier names the contradicting
   observation; refusal completes a diagnostic experiment, not the
   objective) + section 0.3.
4. MU LABEL — section 3 (0.41 = declared scenario parameter, human-analogue
   transfer, NOT monkey-bark; UNMEASURED; label on every use).
5. REMAINING CONDITIONS — section 8 named conditions per behavior (geometry,
   actuator capacity, contact qualification, friction uncertainty,
   integration evidence).
6. OBJECTIVE LINE — section 0.3 verbatim ("demonstrated impossibility can
   close an INVESTIGATION, but it cannot complete the PLAYABLE-MONKEY
   GOAL") + the standing infeasibility rule (justified change within
   authority or bounded escalation; never a tuned measured value).
