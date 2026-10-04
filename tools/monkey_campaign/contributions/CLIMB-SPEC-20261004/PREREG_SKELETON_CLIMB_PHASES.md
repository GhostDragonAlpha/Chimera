# PREREG_SKELETON_CLIMB_PHASES.md — THE FROZEN-PREDICTION STRUCTURE FOR THE FIRST CLIMB-PHASE RUNS (ASCEND, HOLD-AT-HEIGHT, DESCEND, RESUME-GROUND)

Lane: `E:/ChimeraWork/monkey-coordination/climb-spec/` (records lane; phase 1
skeleton — this is NOT a preregistration of any run; NO run exists or is
scheduled by this file). Worker: wk-climb-spec. Date: 2026-10-04.

Status: SKELETON for the Lieutenant. When the named dependencies land, the
FIRST run per phase gets a full prereg authored FROM this skeleton, committed
ALONE FIRST (separate-first) by the Lieutenant; the committed bytes are the
freeze and every emitted receipt must embed `preregistration_sha256` of
exactly those bytes and refuse any mismatch. A seal does not replace the
required commit. This skeleton itself freezes: the outcome spaces, the
falsifier SHAPES, the numbers that are already pinned in the corrected
corpus, and the not-claims. It does NOT freeze run-dependent values — each
such slot is a named placeholder with its owner and its freeze event.

## 0. Gating law (inherited, restated once)

- NO first run of any climb phase starts until the K01 master conditionality
  section 0.4 is satisfied (the seven named prerequisites, each with its own
  sealed receipt) — in particular the qualified grasp configuration, and the
  two physics dependencies named in `PHASE_CONTRACTS.md` 0.1: DEP-N (the N1
  causal tier; state: prereg draft authored
  `58fd70493fb05c964b025a2ff30da17af8fb6b231d455ce652a2f7dd1f6c3a5d`, NOT
  RUN) and DEP-P (the press channel; state: ABSENT, x_press, TC-8 0/8). For
  any first run executed BEFORE DEP-P lands, the press must be the declared
  fixture operating point AND that fixture class must be declared IN THE
  PREREG as the run's certification ceiling (CERTIFIED FIXTURE-BASED — never
  runtime-integrated, never the playable objective).
- The prereg-first law: prediction and falsifier frozen BEFORE the
  implementation or measurement; no seed substitutions; no success-driven
  reruns; no re-pin of mu mid-run; no threshold re-derived mid-run (K01 F2).
- Seeds: the K01-declared climbing seeds 20261002, 20261003, 20261004 ONLY;
  runbook identity `climb1m-r1`; the macro-decomposition is the K03-entry
  obligation that pins the K01 seed block by hash and MAY NOT change the
  seeds.
- Wording law (Captain correction #3): a predicted refusal that is observed
  is a SUPPORTED PREDICTION — never a failure of the experiment and never a
  success of the skill. Each falsifier below NAMES the observation that
  would CONTRADICT its prediction.
- Friction wording law (this lane's `DERIVATION_UPDATE.md` R1-R6): the
  placeholder is quoted with its carrier chain; the 0.41 appears only as
  band-arithmetic sensitivity context; the bench is the Captain's item.

## 1. PHASE C1 — CLIMB (ASCEND): first-run prereg skeleton

### 1.1 Scenario arms (frozen now, from the K02 catalog)

- ARM A1 (the corridor arm): the three SUPPORTED closing catalog states
  band_lo/band_mid/band_hi at n=3 (RS-01..RS-03 class), placeholder mu_s=0.6
  effective (carrier chain quoted per R1), the G06 229-tick schedule,
  envelope [4,219], declared pads, press at the declared operating point.
- ARM A2 (the failure-region arms): the five NON-CLOSING catalog states
  (band_lo/band_mid/band_hi n=2; scene n=2; scene n=3) — EXPECTED refusals
  (slip during transfer), recorded as SUPPORTED PREDICTIONS.
- ARM A3 (the adhesion control): RS-09 zero-mu class — EXPECTED slide (sealed
  sibling 0.05150250000055512 m under full press).
- ARM A4 (scene-line hang control, optional arm if the mass-lineage decision
  has named a scene-line shape): scene n=3 static-hold control; its expected
  verdict table comes from the corrected static thresholds. THE n=4 SHAPE IS
  NOT AN ARM: its declaration is a separate decision; any n=4 arm requires
  its own prereg carrying the five demonstrations as the test plan.

### 1.2 Frozen-now prediction values (pinned corpus rows; the prereg cites
them by hash, never re-types them as new claims)

- Per-channel transfer capacity mu_s*jn = 0.18 N*s at the declared operating
  point; closing requirements 0.13243500000000002 / 0.15082875 /
  0.16922250000000003 N*s; thinnest margin 0.010777499999999968 N*s.
- Handover law: holder_mass_kg = m + m/2 (band_mid n=3: 3.075 kg) at the
  handover tick (template tick 31).
- Stage-D schedule and envelope: 229 ticks; [4,219]; travel
  0.38599999999999995 m; v_climb 0.5 m/s; full-trunk template 687 ticks /
  3.435 s; mean template rate 0.33711790393013097 m/s.
- Static rows at the post-attach (reading, n) per section 5 of the K01 spec.

### 1.3 Dependent placeholders (frozen at their own events; owners named)

- P-A1: the N1-fed native line identity and its feed-on bounds (owner: the
  N1 lane, at N1 publication; the N1 draft's Tier-3 declared bounds are that
  lane's own freeze).
- P-A2: the press derivation for any actuator-qualified arm (owner: the
  x_press debt line / K05 composition; freeze = the TC-3 re-declaration + a
  qualified N*m->N posture derivation, or the declared fixture-press
  re-authorization for a fixture-class run).
- P-A3: the grasp configuration (owner: the grasp chain; freeze = the
  stage-5 runtime receipt).
- P-A4: the reading set actually trained/run (owner: the mass-lineage
  decision, gap 9).
- P-A5: friction state at run time (owner: the Captain's bench docket or the
  explicit placeholder re-authorization; freeze = the admission record).

### 1.4 Falsifier shape (each names the contradicting observation)

- F-C1a CORRIDOR-BREACH (K01 F1 carried): prediction — under the frozen
  operating point the scene-line transfer rows cannot close (0.24618190095000003
  > 0.18). CONTRADICTING OBSERVATION: a supported transfer tick at a
  scene-line (reading, n) row inside its declared envelope span.
- F-C1b PLACEHOLDER-DRIFT (K01 F2): prediction — every receipt threshold
  reproduces bit-exactly from the pinned corrected rows. CONTRADICTING
  OBSERVATION: any threshold differing at any ulp, or any re-pin of mu
  mid-run.
- F-C1c ADHESION (K01 F3): prediction — the zero-mu arm slides. CONTRADICTING
  OBSERVATION: a sticking zero-mu arm.
- F-C1d HIDDEN-ASSIST (K01 F5 + the composed boundary law C5): prediction —
  every accepted sample carries exactly the declared key set; no reset
  machinery touches in-episode state. CONTRADICTING OBSERVATION: an
  undeclared/solver-internal/x_* key accepted, or any inter-phase state
  write, re-press, creep erasure, teleport or hidden anchor.
- F-C1e n=4-EXPANSION (K01 F7): prediction — n=4 stays a FEASIBILITY
  CANDIDATE. CONTRADICTING OBSERVATION: any text/receipt claiming n=4 closes
  or is the lawful ascent shape without the five sealed demonstrations.

### 1.5 Closed outcome space (exhaustive; every episode maps to exactly one)

{CORRIDOR_CLOSE (per C1.2 X1), SLIP_STOP (X2), ENVELOPE_BREACH (X3/T3),
UNDECLARED_RELEASE (T2), INTEGRITY_REFUSAL (T4), HORIZON_FAIL (T5)}.
Sub-verdicts per arm: arm A2/A3 outcomes are SUPPORTED-PREDICTION-REFUSED
when the refusal fires as predicted; the outcome space for them is
{REFUSED_AS_PREDICTED, CONTRADICTED (which is falsifier hit F-C1a or
F-C1c respectively), INTEGRITY_REFUSAL, HORIZON_FAIL}. A refusal is never
recorded as ascent success; an ascent success is never recorded from a
failure-region arm.

## 2. PHASE C2 — HOLD-AT-HEIGHT: first-run prereg skeleton

### 2.1 Scenario arms

- ARM H1 (the fixture-class hold-at-height arm): a DECLARED height-offset
  catalog state (constructed under the K02 validity law V1-V5 as a new
  declared fixture state in its own prereg — never a teleport) OR the
  hold2-exit state of an executed ARM A1 transfer; hold window = the hold2
  200-219 class, extended window declared in the prereg.
- ARM H2 (the release-discriminator arm): the K02 P4 release structure from
  the held state (20-hold + 40-release class) — the certified identity is
  the expected outcome at fixture class.
- ARM H3 (zero-mu hold control): EXPECTED slide (cannot hold).

### 2.2 Frozen-now prediction values

- The stick class at the operating point: zero slip ticks; press worst
  deviation class 1.01e-12 N*s (the K02 P1 measured class); stick-class
  cumulative creep EXACT ZERO (K02 P1) — the G07 alternative class (implied
  creep 0.0024525000000000007 m per 20 ticks, 1.2266e-4 m/tick) is the
  DECLARED alternative verdict, recorded if observed, never normalized.
- Press cost bound: 0.040346690644887555 J/tick (scene operating point,
  G07) as the declared account bound for the arm's window; band_hi|n=2
  stick-class account 0.5217391304347825 J press / 0.1660072724981848 J
  friction.
- Gravity==friction accounting exactness class (G07): delta 3.63e-12 J at
  ~zero KE.
- The release identity (H2): W_press == 0.0 J EXACTLY every release tick;
  free-fall recursion worst class 5.81e-12 m/s; gravity work 19.320355586443497
  J == KE gain 19.320355586289068 J within 1.54e-10 J; terminal speed delta
  1.27e-11; 120 post-release contact records RECORDED-NOT-SUPPORTING.
- The PE stake: per full trunk (standard-g) 61.322943779999996 / 69.840019305
  / 78.35709483 / 113.99251611439858 J by reading — the declared payback
  obligation on any failure.

### 2.3 Dependent placeholders

- P-H1: the height-offset state construction (owner: this contract's
  successor prereg; freeze = the declared state's validity receipts V1-V5).
- P-H2/P-A2/P-A3/P-A4/P-A5: as in 1.3 (the same owners; the same freezes).

### 2.4 Falsifier shape

- F-C2a HOLD-WITHOUT-PRESS/ANCHOR: prediction — the hold stands by the
  friction law at the declared press and falls/slides at zero mu. CONTRADICTING
  OBSERVATION: a standing zero-mu hold, or a hold whose ledger identity
  fails while remaining supported (an anchor defect).
- F-C2b CREEP-NORMALIZATION: prediction — stick-class creep stays EXACT
  ZERO; any nonzero creep is a recorded finding. CONTRADICTING OBSERVATION:
  nonzero creep erased, reset, or normalized without a declared dissipative
  term (the assist signature; K02 F4 class).
- F-C2c UNDECLARED-RELEASE: prediction — every release is intent-declared
  and reproduces the identity. CONTRADICTING OBSERVATION: a release not
  following the declared schedule, or an executed release whose gravity
  work != KE gain within the declared windows.
- F-C2d PE-VANISHING: prediction — stored PE is paid back through declared
  descent or release accounts only. CONTRADICTING OBSERVATION: an energy
  account whose PE decreases without a declared destination (destination
  closures class <= 5.33e-15 J is the landing card's closure bar).

### 2.5 Closed outcome space

{HOLD_CONFIRMED (stick class, accounts closed), HOLD_SLIP (T1 — at a lawful
arm this is the SUPPORTED PREDICTION), RELEASE_IDENTITY_CONFIRMED (H2),
RELEASE_IDENTITY_CONTRADICTED (F-C2c hit), SLIDE_AS_PREDICTED (H3),
CONTRADICTED (F-C2a), INTEGRITY_REFUSAL, HORIZON_FAIL}. The playable hold
objective is NEVER an outcome of this phase's first run (the objective-line
law in the K02 receipt's own words).

## 3. PHASE C3 — CONTROLLED DESCEND: first-run prereg skeleton

### 3.1 Scenario arms

- ARM D1 (metered descent arm): from a declared hold-at-height state, the
  descend intent, the brake template (the G06 brake segment class: full
  v_climb shed over the declared tick count, ending v=0, then hover);
  arrival = the hold2 state at the lower facet.
- ARM D2 (release arm): the uncontrolled release from the same height class
  — the certified failure arm; its identity IS the expected outcome.
- ARM D3 (zero-mu descent control): EXPECTED uncontrolled slide/fall (the
  direction-blind law does not hold without mu).

### 3.2 Frozen-now prediction values

- Metering channel: m_share*(g*DT - 0.0025) = 0.09542750000000001 N*s at the
  band_mid share for v_d = 0.5 m/s; the channel goes negative only when the
  schedule sheds > g*DT = 0.04905 m/s per tick.
- The K04 split metrics: descent rate profile inside the brake template for
  the declared window AND every executed release reproducing the identity
  (19.320355586443497 / 19.320355586289068 J; 1.9620000000000002 m/s in 40
  ticks).
- Closure equivalence: descent closes exactly where the hold law closes —
  the entry (reading, n) stage-B row is a frozen precondition, not a
  discovery.

### 3.3 Dependent placeholders

- P-D1: the descent window/template instantiation at the declared facet
  spacing (owner: the successor prereg; the template travel per facet is
  0.38599999999999995 m at G06 spacing; any other spacing is a declared
  parameter frozen pre-run).
- P-D2/P-A2/P-A3/P-A4/P-A5: as in 1.3.

### 3.4 Falsifier shape

- F-C3a PROFILE-SMUGGLING: prediction — a descent credit requires the rate
  profile inside the brake template AND the accounts closed. CONTRADICTING
  OBSERVATION: a descent success reported with the profile outside the
  template, or an observed free-fall release counted as descent credit.
- F-C3b RELEASE-IDENTITY: as F-C2c (the same identity at the descent
  height class).
- F-C3c DIRECTION-ASYMMETRY: prediction — the support law is direction-blind
  in impulse balance; descent closes exactly where hold closes. CONTRADICTING
  OBSERVATION: a descent closing at an (reading, n) where the static hold
  row is OUTSIDE (or the reverse) under identical declared conditions —
  either direction falsifies the shared-law form.
- F-C3d INTEGRITY (T4 classes) as in 1.4.

### 3.5 Closed outcome space

{DESCENT_CONFIRMED (profile inside template + accounts closed),
ARRIVAL_CONFIRMED (the lower-facet hold2 re-arm), RELEASE_AS_PREDICTED (D2
identity confirmed — the failure arm, recorded, never a descent credit),
SLIDE_AS_PREDICTED (D3), SLIP_STOP, CONTRADICTED (F-C3a/F-C3c hit),
INTEGRITY_REFUSAL, HORIZON_FAIL}. "An ascent success cannot stand in for
controlled descent" — no ascend/hold outcome may fill this phase's outcome
slots.

## 4. PHASE C4 — RESUME-GROUND: first-run prereg skeleton

### 4.1 Scenario arms

- ARM R1 (fixture-composition arm): the landing terminal state (the landing
  card's at-rest class) -> the walk intent -> the certified walk line's
  gates for a declared window, on the declared ground fixture. Certification
  ceiling: CERTIFIED FIXTURE-BASED composition — never the playable loop.
- ARM R2 (failure-path arm): a declared failure injection (a lawful failure
  class from C1/C2/C3) routed through X03's approved recovery/restart law —
  the EXPECTED outcome is the approved continuation or visible restart, per
  the X03 registry row; no new get-up skill required or assumed.
- ARM R3 (flat-walk control): the walk line alone from its own declared
  ground state — the control that separates resume-specific failures from
  walk-line failures.

### 4.2 Frozen-now prediction values

- The walk line's own gates (from the sealed W-tier): the stride law 0.2;
  the stop floor semantics (the certified zero-advance class, W08 P7/W10 P7:
  v at settle end 0.3139590061066735 m/s inside
  [0.2993197278911565, 0.3395772238044552] — quoted as the CLASS of the
  floor semantics, never as a resume prediction); velocity envelope
  V = 2.977443609022557 m/s; cross-build non-regression margin
  0.03103119967715015 m/s (K01 E6 carries these until a climbing
  re-derivation supersedes them by a recorded decision).
- The landing terminal class: at rest, restitution 0.0 (the landing card's
  own numbers are its receipt's; the resume prereg cites them by hash).
- THE HONEST HOLE (declared, not filled): there is NO recorded law for the
  landing->walk transition itself — the transition window, the arbitration
  tick and the evidence keys are P-R1 placeholders below. This skeleton
  claims NO transition prediction; freezing one is the successor prereg's
  first obligation, BEFORE any run.

### 4.3 Dependent placeholders

- P-R1: the transition window/arbitration tick/evidence-key declaration (owner:
  the resume-ground successor prereg — the phase has NO owner until the
  Lieutenant dispatches one; this lane claims authorship only).
- P-R2: the body identity at the resume boundary (owner: the mass-lineage
  decision gap 9 + the landing card's declared body class; until resolved,
  ARM R1 is fixture-composition only).
- P-R3: the walk physicalization state (owner: the F7 remediation lane,
  phase-1 design + prereg DRAFT; until its runs publish, "hands and feet
  transmit the forces" is NOT met by any resume arm and no arm may claim it).
- P-R4: terrain class of the resume surface (owner: F06 law; the certified
  walk is FLAT-ONLY, gentle-grade <= 2.6% the certified uneven envelope; a
  non-flat resume arm needs F06-class coverage).
- P-A5 (friction at the ground fixture) as in 1.3.

### 4.4 Falsifier shape

- F-C4a RESUME-TELEPORT: prediction — the resume transition is solver state
  evolution with bit-continuous state-chain heads. CONTRADICTING
  OBSERVATION: any discontinuity at the boundary (a state write, a snap, a
  pose-set, a stale grip, an unaccounted impulse) — the C22 classes.
- F-C4b SUPPORT-WITHOUT-CONTACT: prediction — post-transition support comes
  from the declared ground contact set by the solver's own contact
  resolution. CONTRADICTING OBSERVATION: support present without the
  declared contact set, or prescribed forces substituted without a declared
  surrogate label (the F7 honest label is mandatory wherever the surrogate
  is still in use).
- F-C4c WALK-CLAIM-INHERITANCE: prediction — resume success claims only the
  walk line's actual certified scope. CONTRADICTING OBSERVATION: a resume
  success claimed on uneven terrain beyond the certified route class, at a
  speed outside the sealed envelope, or with force transmission implied
  while P-R3 is unresolved.
- F-C4d BOUNDARY-ACCOUNT: prediction — the boundary enters no account
  discontinuously. CONTRADICTING OBSERVATION: an energy/ledger jump at the
  boundary outside the declared closure class.

### 4.5 Closed outcome space

{RESUME_CONFIRMED (walk gates held for the declared window, boundary
continuous), RESUME_FAIL_WALK (the walk line's own failure modes, recorded),
RECOVERY_AS_PREDICTED (R2: the approved continuation or visible restart),
CONTRADICTED (F-C4a/F-C4b/F-C4d hit), INTEGRITY_REFUSAL, HORIZON_FAIL}.
THE LOOP-LEVEL CLAIM IS OUT OF SCOPE: a RESUME_CONFIRMED outcome never
implies the ten-phase loop (K08 owns that composition; its honest negative
stands today).

## 5. CROSS-PHASE FALSIFIERS (binding on every first run of every phase)

- F-X1 ASSIST-SMUGGLING (K02 F4 extended across boundaries; C5 law):
  prediction — no reset machinery touches in-episode state at any phase
  boundary. CONTRADICTING OBSERVATION: any inter-phase performance
  difference attributable to reset machinery — a mid-episode state write, a
  re-press, an unexplained creep erasure, a force restore, a teleport, a
  hidden anchor, or a reset entering any account.
- F-X2 METRIC-SMUGGLING (K01 F4 / K04 law): prediction — per-phase metrics
  reported for every claimed phase, separately. CONTRADICTING OBSERVATION:
  an ascent success reported while hold/descend metrics are absent, a hold
  standing in for descent, or any phase's outcome slot filled by another
  phase's evidence.
- F-X3 RESET-EQUALS-SKILL / SPEC-EQUALS-SKILL (K01 F6/K02 F6): prediction —
  completions are construction/spec receipts. CONTRADICTING OBSERVATION: any
  claim that spec authoring, reset construction, or a diagnostic pass
  constitutes a trained skill, a physics qualification, or playable-objective
  progress.
- F-X5 ATTRIBUTION (K02 F2): prediction — every executed episode's initial
  state names fixture ids, pinned receipt provenance, seed/reset index, and
  the CONDITIONAL-CALCULATION labels. CONTRADICTING OBSERVATION: an executed
  episode lacking any of A1-A4, or any threshold quoted without its reading
  and A1-A7 assumptions, or any 0.41-as-scene-parameter carrier (R2).
- F-X4 DETERMINISM (K02 F1/D1): prediction — duplicated fresh processes
  produce identical boundary states. CONTRADICTING OBSERVATION: differing
  tick-0 or boundary state-chain heads for the same (state, seed).

## 6. NOT-CLAIMS (maximum form; carried into every successor prereg verbatim)

1. The climb phases are the LAST unrun behaviors in the demonstration chain:
   NOTHING in this skeleton asserts, implies, or pre-announces a successful
   climb, hold-at-height, descent, or resume. The outcome spaces are CLOSED
   so that failures are first-class recorded outcomes, not surprises to be
   rerun away.
2. No first run is scheduled, authorized, or enabled by this skeleton. The
   dispatch gates are the K01 0.4 prerequisites, DEP-N publication, the
   DEP-P state, the friction admission, and the mass-lineage decision —
   each owned elsewhere.
3. Fixture-class runs (if any are dispatched before DEP-P lands) are
   CERTIFIED FIXTURE-BASED at most: they never claim runtime integration,
   the playable objective, or the goal's force-transmission clause.
4. The n=4 shape, the mass lineage, the friction value, the bench schedule,
   and the resume-ground ownership are ALL open decisions owned elsewhere;
   this skeleton pre-commits none of them.
5. "DEMONSTRATED IMPOSSIBILITY CAN CLOSE AN INVESTIGATION, BUT IT CANNOT
   COMPLETE THE PLAYABLE-MONKEY GOAL": any predicted refusal observed in
   these phases closes only the claim it was made against, under its
   assumptions.
