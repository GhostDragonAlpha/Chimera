# PREREGISTRATION (DRAFT) — VPL1-N1: the N1 FORCE-FEEDING TIER (the compliant pad becomes physically causal in the native solver)

Status: DRAFT authored by `wk-vpl1-native` for the Lieutenant's pin
(separate-first; the committed bytes are the freeze; every emitted receipt of
this card must embed `preregistration_sha256` of exactly those bytes and
refuse any mismatch). NO implementation file, injection patch, harness,
sealed package, runner job or capture frame of this card exists at draft
time. Write scope of the draft: the lane dir
`E:/ChimeraWork/monkey-coordination/vpl1-native/` (NO_WORKTREES honored; all
CPU verification through the canonical `task_package.py seal|run`, slots 2/3,
BUSY = retry >= 10 s). Authorization: the Lieutenant's N1 dispatch (the
named-next rung from the #348 publication; the completion audit's next
action), with the fresh-review TWO PRECONDITIONS ENFORCED AT PIN TIME.

N1 CHANGES CONTACT DYNAMICS. The standing laws apply AT THEIR STRICTEST: the
review's preconditions are Sections 2 and 3 of this file and are NON-
NEGOTIABLE at pin time; the G08 parity re-bind is Section 5; the binding
gate is carried (Section 6); the closed outcome space grows the causal
classes (Section 7); the k FORMULA is frozen (Section 4); the not-claims are
at maximum (Section 10).

## 0. Standing laws consumed (the strictest form for a dynamics-changing rung)

- The objective-line law; the wording law (a predicted refusal observed is a
  SUPPORTED PREDICTION; each falsifier names its contradicting observation).
- The anti-tuning law: EVERY constant below is frozen from the chain and is
  NEVER adjusted after any result is seen; a post-result change request is a
  FINDING routed to the Lieutenant, never an edit. **THE k FORMULA
  `k = 120.0 * 2.0e-3 / 5.160493e-5` (the frozen decimal
  4650.718448799368 Pa) IS IN CODE AS THE FORMULA AND IS NEVER RETUNED** —
  the feed-on arm changes WHERE the force acts, never its magnitude law.
- The instrument anti-tuning law: tau = 1.0e-4 m, pi_c = 1.0e-3 m,
  r_joint = 5.0e-3 m remain frozen; no tolerance enlarged; no pair removed.
- The anti-masking invariant, UNCHANGED AND ABSOLUTE: the bone stays rigid
  and fully checked; N1 adds a generalized pad force — it NEVER alters the
  rigid contact rows, the contact classifications, the exclusions ledger or
  any bone-level check. A pad-covered tip's rigid reading is identical with
  the feed ON and OFF (asserted per tick in-run; any change =
  `instrument_invalid_pad_masks_bone`).
- The additive discipline, EXTENDED HONESTLY FOR N1: N0 was pure-recording;
  N1 adds FORCE TERMS. Every injection is ANCHORED (count==1), gated, and
  reads the pad state computed by the SAME recording classifier from the
  SAME tick-start state; no existing expression is reordered; the added
  force enters as a NEW generalized-force term at declared injection points
  (Section 4); the injection points are enumerated in the implementation
  package and hash-pinned in its manifest.
- The concealment law: each falsifier fires on its constructed trigger
  in-run, or its stage fails itself.
- The hash law: script-emitted hashes only; keyed per-arm blocks; named
  artifacts; every emit-placeholder replacement asserted fired; superseded
  markers voided; `assert stated == computed` before exit.
- The receipt conventions: the delta_note carries ALL deviations (the
  CORRECTION-1 lesson); the canonical 582-char coexistence text and the
  complete ladder label are CITED (never carried/condensed) with the carrier
  repoint per CORRECTION-1 F4: the carrier of record = the stage-5 receipt
  `f37b2e9e...` (the sealed condensation; the canonical text attached in the
  stage-5 erratum, extracted from the adjudication receipt `4e465238...`).

## 1. The chain consumed (pins in force; verified hashes in the lane EVIDENCE.md)

| record | pin |
|---|---|
| The N0 prereg (this lane's father card) | commit `27f1d570`, bytes `5f775e0ec13a175229d9e87eaf2d2deefe15380addca05d8ad362b2d6fbd981a` |
| The N0 sealed battery receipt (TIER N0 PASSED; all verdicts TRUE) | `final_run/vpl1_receipt.json` sha256 `b63d5cca41a999e04bdf17d5271a29f93dc7f87c621cb9691c8f96e90fddc17d`; runner job `e2c652af81a541b49583d78c38d7bdcb` PASSED, exit 0, slot 2 |
| CORRECTION-1 (the SGT verdict landed; F1 routed, F2/F3/F4 corrected) | `CORRECTION-1_VPL1_NATIVE.md` sha256 `bb9273033c8e4af0ec33deacc20e89d5924af589a8865e84ea97a08b70f70b05` — ITS F1 DISPOSITION IS THE MANDATE FOR SECTION 2 |
| The VPL-1 chain constants | prereg `4def67e4` (bytes `9213bf7d...`), AMENDMENT-1 `0c06e093` (`018f0bc1...`), AMENDMENT-2 `ccb60023` |
| The sealed W03 anchor set | stdout `8c537cdb...`, stderr `c6f9b6c0...`, qdumps `b47b709c...` x2, record `6278f4b0...`; the walk identity dx `0.9131056683968011`, dy `-0.7178374101385098` is a fact of the sealed W03 records (per CORRECTION-1 F2: never cited as a per-arm re-derivation) |
| The pinned walk-line engine input | header blob `5863348f` (content `f0ffea12...`) -> the W03I seals (`2c72df55`/`9e32d94e`) -> the N0 instrument (`0af76b66`/`79fc239c`) -> the N1 instrument (derived in-slot, manifest hashed) |
| The sealed scene | `f6844eea...`, bytes unchanged in every arm |
| The authorization | the Lieutenant's N1 dispatch: the named-next rung from the #348 publication; the FINAL PASS authorization's two preconditions |

## 2. PRECONDITION 1 — THE F1 SUB-WINDOW AMENDMENT (declared BEFORE any run; no post-hoc resolution)

THE CONTRADICTION (CORRECTION-1 F1): the admission window's lower edge
pi_c = 1.0e-3 m sits below the layer thickness t = 2.0e-3 m, so for every
admitted d in (pi_c, t] the indentation u = d - t <= 0. N0's row path
admitted u <= 0 as PAD_CONTACT (flagged measured_anchored, unbounded below)
while N0's probe path treated u <= 0 as no-contact — a prereg-internal
contradiction and a row/probe divergence, found post-run and routed.

THE AMENDMENT, DECLARED NOW (the class-law: resolved HERE, pre-run):

- **OPTION (a) IS ADOPTED: the sub-window is EXCLUDED from PAD_CONTACT and
  receives its own named class.** For d in (pi_c, t] the tip is
  **`PAD_ENGAGED_UNCOMPRESSED`**: the pad is engaged (the bone is inside the
  declared window) but UNCOMPRESSED (u <= 0) — it transmits ZERO force.
- THE PHYSICAL REASONING: contact is unilateral — a Winkler foundation
  transmits no tension. The amended contact law (F-1-N1) is
  **`p = max(0, k * u / t)`**: at u <= 0, p = 0 and F = 0 by the law itself,
  not by a branch accident. The class makes the zero-force state VISIBLE and
  COUNTED instead of silently folded into PAD_CONTACT.
- **OPTION (b) IS DECLINED**: amending the window edges (moving the lower
  edge to d > t) would EDIT the frozen constants G-4/X-1 after the N0
  results exist — the anti-tuning law forbids exactly that. The window
  stays frozen; the CLASSIFICATION is amended.
- THE CLASS TABLE (complete, closed):
  - `NO_PAD_ROW` — d <= pi_c (no window event).
  - `PAD_ENGAGED_UNCOMPRESSED` — pi_c < d <= t (the F1 sub-window; ZERO
    force; counted; NEVER measured_anchored; NEVER a contact-force row).
  - `PAD_REFUSED_DEPTH` — d > t + u_max = 4.0e-3 m.
  - `PAD_REFUSED_PATCH` — t < d <= 4.0e-3 m and the patch witness absent.
  - `PAD_CONTACT` — t < d <= 4.0e-3 m, patch present: u = d - t in
    (0, u_max]; p = k*(u/t) > 0; F = p*A. THE ONLY FORCE-CARRYING CLASS.
- `measured_anchored` is DEFINED ONLY for u > 0 (X-2's bands (0, 0.8e-3] and
  (0.8e-3, 2.0e-3]); the F1 mis-flag class (u <= 0 flagged true) is
  structurally gone.

## 3. PRECONDITION 2 — HARMONIZED SIGN HANDLING (by construction; any residual divergence a declared delta)

- ONE CLASSIFIER: the probe path IS the row path's classifier evaluated over
  constructed inputs — the implementation declares a single classification
  function consumed by both the per-tick row path and the C-battery probe
  path. Agreement on u <= 0 is STRUCTURAL, not a matched pair of branches.
- THE PROBE TABLE (the harmonized band codes): u <= 0 -> `NO_FORCE` (the
  same outcome the row path emits for the sub-window); !patch ->
  REFUSED_PATCH; u > u_max -> REFUSED_DEPTH; 0 < u <= 0.8e-3 ->
  MEASURED_ANCHORED; 0.8e-3 < u <= 2.0e-3 -> EXTRAPOLATED. The C9-style
  control runs u = 0 (the boundary) AND a negative u (the sub-window probe):
  both -> NO_FORCE.
- RESIDUAL DIVERGENCE: NONE BY CONSTRUCTION. Should any future divergence
  exist, it is a DECLARED DELTA in the receipt's delta_note — never an
  implicit branch.

## 4. THE N1 FORCE-FEEDBACK DESIGN (the injection semantics; declared before any code)

- THE FEED GATE: `GAITPHYS_VPL1_FEED` (a NEW env; unset => ZERO feedback =>
  the solver is byte-identical to the N0 solver). The arms:
  - `mode0`: all envs unset — the plumbing fully inert.
  - `N0-gated` (= THE FEED-OFF CONTROL): GAITPHYS_VPL1=1, FEED unset — the
    N0 recording behavior, zero feedback.
  - `N1-feed-on`: GAITPHYS_VPL1=1 + DESCRIPTORS=1 + FEED=1 — the pad force
    feeds the generalized dynamics.
- THE INJECTION SEMANTICS (declared): per tick, at tick start, the pad force
  per tip is computed by the SAME frozen classifier from the SAME tick-start
  rigid solution N0 recorded; for each PAD_CONTACT tip the world force
  f = +F * n_up (the anti-penetration direction: the pad pushes the body
  AWAY from the solid, along the plane normal; the sign check is in-run,
  N1-R2); the generalized column is `J_tip^T f` via the engine's own
  `Evaluation::force` at the tip's (body, local) — the SAME Jacobian
  machinery the contact points use; the column is ADDED to the effective
  generalized force for EVERY substep of that tick (the declared explicit
  zero-order-hold scheme, consistent with the scene's own configure law).
  The injection points are the rhs assembly lines only; each is ANCHORED
  (count==1) and enumerated in the implementation package's manifest.
- THE FEED SCOPE: ONLY PAD_CONTACT rows feed. PAD_ENGAGED_UNCOMPRESSED,
  PAD_REFUSED_DEPTH, PAD_REFUSED_PATCH transmit NOTHING (the unilateral law;
  the refusal classes stay refusals — feeding a refused row would be a
  tune-to-success and is forbidden).
- THE LEDGER LAW: the pad work is accumulated and recorded as ITS OWN
  channel (never folded silently into any existing ledger class); the
  mechanical account across the feed window reconciles: d(KE+PE) = the pad
  work + the existing ledger delta, to the declared tolerance (1e-6 relative
  on the pad-work-magnitude timescale, with the reconciliation recorded per
  audited tick).
- THE ANTI-MASKING ASSERTION (carried, absolute): the rigid contact solve,
  the contact rows and every bone-level classification are UNTOUCHED by the
  injection (asserted per tick in-run: the rigid rows identical feed-on vs
  feed-off at the same tick index, recorded; any difference =
  `instrument_invalid_pad_masks_bone` — noting honestly that with feedback
  the TRAJECTORY diverges, so the per-tick same-index comparison is valid
  only up to the divergence onset; the assertion runs on the window ticks
  and the pre-divergence ticks, and the divergence onset itself is recorded
  as a first-class datum).

## 5. THE G08 PARITY RE-BIND (the new parity basis; never a silent anchor drop)

THE HONEST DECLARATION: **THE W03 ANCHORS CANNOT HOLD ON THE FEED-ON ARM.**
They were produced by the padless solver; N1 changes the dynamics by
construction. The prereg therefore DEFINES the parity basis in three tiers:

- TIER 1 — THE IDENTITY FLOOR (the non-contact arms): mode0 AND N0-gated
  reproduce the sealed W03 anchor set BIT-EXACTLY (stdout `8c537cdb...`,
  stderr `c6f9b6c0...`, qdumps `b47b709c...` x2) — the byte-inertness of the
  full N1 plumbing when the feed is off. ANY drift = `anchor_floor_drift`,
  the run invalid, nothing carries.
- TIER 2 — THE FEED-ON DIVERGENCE, REQUIRED (the causality tooth): the
  feed-on arm's streams MUST DIVERGE from the W03/N0 anchors. If the feed-on
  streams were byte-identical to the anchors, the pad would be pushing
  NOTHING: `feed_inert_failure` — the run is invalid (the causal claim dies
  with it). The divergence onset tick is recorded (first tick where any
  stream byte differs).
- TIER 3 — THE DIVERGENCE BOUNDS (the physical account, declared pre-run):
  the max total pad force at the declared tip indentations =
  0.20076 + 0.03826 + 0.07154 + 0.09905 = **0.40961 N** (per-tip F = p*A
  with the frozen formula; ~0.68% of the 6.15-kg band BW). The declared
  bounds, each with its 10x margin over the impulse/mass account
  (impulse over a 5-tick window ~6.8e-3 N*s; dv ~1.1e-3 m/s):
  - the feed-on walk identity (dx/dy, if the run emits them) diverges from
    the W03 numbers by NO MORE THAN 0.01 m in each component;
  - the refusal tick shifts by NO MORE THAN +/-15 ticks from the padless
    302;
  - the cumulative recorded pad impulse is reported and must be consistent
    with the declared force table (the N1-R3 identity);
  - ANY bound breach = `feed_divergence_out_of_bounds` — a FIRST-CLASS
    FINDING routed to the Lieutenant (a wrong physics account), never a
    moved constant, never a widened bound.
- THE G08 LAW STANDS: walking certification is NOT inherited by the feed-on
  arm; the feed-on identity gates are its own determinism (below) and the
  Tier-3 account.

## 6. THE BINDING-GATE CAPTURE (carried unchanged in design)

The N0 binding gate carries verbatim: the per-tick state hash `H_tick`
(now over the serialization INCLUDING the pad force rows and the feed flag —
the canonical field list is extended by exactly {feed_flag, per-tip
pad_force_N}; declared in the implementation package, byte-stable across
arms); the lossless pixel strip; the IN-RUN gate (gate1: the two independent
serializations byte-equal; gate2: the retained frames' strip bits ==
sha256 of the driver format); the constructed tampers T1 (perturbed-state
encode) and T2 (post-encode strip mutation) MUST FAIL in-run. THE ANCHOR
LAW lesson is carried structurally: the anchor comparison covers EVERY
stream, and the feed-on arm's extra telemetry goes to FILES only (the
battery instance's traces redirected, the dup2 pattern).

## 7. THE CLOSED OUTCOME SPACE (counts close; no unnamed state)

Per audited tick, per covered tip, EXACTLY ONE of: `PAD_CONTACT(u > 0,
F > 0)`, `PAD_ENGAGED_UNCOMPRESSED`, `PAD_REFUSED_DEPTH`,
`PAD_REFUSED_PATCH`, `NO_PAD_ROW`. Per tick, the feed state:
{FEED_APPLIED (>= 1 nonzero pad force injected), FEED_ZERO (all zero)}.
Per phase/schedule: {COMPLETED, REFUSED}. Capture: {GATE_PASS, GATE_FAIL}.
Anchors: mode0/N0-gated {ANCHOR_EXACT, ANCHOR_DRIFT}; feed-on
{FEED_DIVERGENCE_VERIFIED_IN_BOUNDS, FEED_INERT_FAILURE,
FEED_DIVERGENCE_OUT_OF_BOUNDS}. Binding triggers: {FIRED_BOTH,
TRIGGER_MISSED}. COVERAGE ARITHMETIC closes per arm; any unnamed state or
double-scored row = `vpl1_n1_outcome_space_broken` (refusal).

## 8. THE QUANTITY CODE-PATH TABLE (every number names its producer)

| quantity | producer code path | tier/label |
|---|---|---|
| pad class + u + patch witness + measured_anchored | the ONE frozen classifier (row path = probe path) | N1, DECLARED-MODEL |
| pad force p, F = p*A | the classifier's force law p = max(0, k*u/t), F = p*A | N1; DECLARED-MODEL-FORCE (now a solver input ON THE FEED-ON ARM ONLY) |
| the generalized pad column | J_tip^T f via the engine's Evaluation::force, injected at the declared rhs lines | N1 feed-on only |
| the pad work channel | the accumulator over the injected force and the tip displacement | N1, its own ledger class |
| bone-level classes, rigid rows, the exclusions ledger | the UNCHANGED rigid machinery (asserted unchanged per Section 4) | rigid, unchanged |
| per-tick state hash H_tick | the declared canonical serializer (extended field list) | N1, byte-stable |
| capture binding | the in-run gate (byte-equality + strip) + T1/T2 | capture stage |
| W03 anchors | the sealed W03 dump path (mode0 + N0-gated arms) | Tier-1 floor |
| feed-on divergence + bounds | the Tier-2/Tier-3 account (Section 5) | N1 |
| actuator capacity, law-form grids, walking certification | NOT PRODUCED HERE — cited, never re-run | cited |

## 9. THE FROZEN PREDICTIONS (each names its contradicting observation)

- N1-P1 THE IDENTITY FLOOR: mode0 and N0-gated reproduce the sealed W03
  anchors bit-exactly; N0-gated pad rows = zero in the walk scene (no
  descriptors registered). CONTRADICTION: any drift = `anchor_floor_drift`,
  the run invalid, nothing carries.
- N1-P2 THE CAUSAL REALITY: the feed-on arm DIVERGES from the N0-gated/feed-
  off arm (the state streams differ; the divergence onset recorded), AND the
  feed-on streams differ from the W03 anchors. CONTRADICTION: byte-identity
  anywhere here = `feed_inert_failure` — the pad pushes nothing, the causal
  claim dies, the run is invalid.
- N1-P3 THE SUB-WINDOW LAW: every d in (pi_c, t] row classifies
  PAD_ENGAGED_UNCOMPRESSED with ZERO force and a FALSE measured_anchored
  flag; zero PAD_CONTACT rows carry u <= 0; the probe and row paths agree on
  every constructed case (the harmonized table). CONTRADICTION: any
  u <= 0 PAD_CONTACT row (the F1 defect class); any flag-true sub-window
  row; any row/probe disagreement = `sub_window_law_violated`.
- N1-P4 THE ANTI-MASKING INVARIANT: the rigid contact rows and bone-level
  classifications are identical feed-on vs feed-off up to the recorded
  divergence onset (asserted in-run on the window and pre-onset ticks).
  CONTRADICTION: any rigid-row difference attributable to the pad gate =
  `instrument_invalid_pad_masks_bone`, the run invalid.
- N1-P5 THE PHYSICAL ACCOUNT: the per-tick injected pad forces match the
  frozen force table (F = p*A per tip, the FORMULA); the cumulative impulse
  matches sum(F*dt) over the FEED_APPLIED ticks (the R3 identity, 1e-12
  relative); the divergence bounds of Section 5 Tier-3 hold; the pad-work
  reconciliation closes. CONTRADICTION: any bound breach =
  `feed_divergence_out_of_bounds` — a routed FINDING (the physics account is
  wrong), never a moved constant.
- N1-P6 THE SIGN LAW: every injected pad force points ANTI-PENETRATION
  (world-up at the plane; never into the solid), and the force exists ONLY
  on PAD_CONTACT rows. CONTRADICTION: any force on a refusal/sub-window row
  or any sign violation = `feed_sign_violated`.
- N1-P7 THE CAPTURE + DETERMINISM: the binding gate GATE_PASS on the feed-on
  arm (the serialization now includes the feed state); T1/T2
  MUTANT_REJECTED in-run; the feed-on arm byte-identical across its
  independent re-run (every file). CONTRADICTION: any gate fail, missed
  trigger, or re-run divergence.

## 10. THE HONEST SCOPE (the not-claims at maximum)

- N1 makes the pad CAUSAL IN THE HEADLESS NATIVE SOLVER ONLY — a ~0.41 N
  contact-model force on probe geometry riding a walk scene. **NO
  GRASP-COMPLETION CLAIM: the grasp still needs the press channel — TC-8 =
  0/8 and x_press ABSENT stand; the pad pushes, the hand still has nothing
  to press WITH.** The same-hands debt stands; friction PLACEHOLDER; the
  mass lineage UNRESOLVED; the C17 non-identity stands (the pad is NOT an
  attachment port); K01 conditionality stands.
- WALKING CERTIFICATION IS NOT INHERITED (the G08 law): the feed-on arm is a
  dynamics perturbation study on the sealed scene, not a locomotion
  qualification.
- THE PRODUCT RUNTIME IS EXCLUDED (readiness 0/5, PR #334; MembraneTick
  untouched). The compliant layer's scope = the headless W03 body class.
- THE PAD IS NOT A SUPPORT ELEMENT: 0.41 N total against a ~60 N support
  task — the physical account ITSELF (Section 5) is the demonstration of how
  far the compliant layer is from carrying the grasp; the number is
  recorded, never tuned upward.
- THE VISCOELASTIC PRONY CLASS: NAMED-NOT-MODELED (the quasi-static elastic
  law, the soft/relaxed reading). N1 = the FORCE-FEEDBACK TIER ONLY; the
  pad-interface runtime claim and the exact-candidate adjudication at the
  pad-interface scope remain named-unmet rungs (the complete ladder label
  cited per CORRECTION-1 F4). THE GOAL STAYS OPEN.
- The ARM-B topology deviation (the probe descriptors on the sealed scene;
  CORRECTION-1 F3) carries into N1 UNCHANGED and is declared in the
  delta_note again.

## 11. THE QUALIFICATION ORDER AND GOVERNANCE

1. PIN: the Lieutenant commits THIS file alone (separate-first; the
   committed bytes are the freeze) — the preconditions of Sections 2-3 are
   ENFORCED AT PIN TIME per the FINAL PASS authorization.
2. THE PACKAGE: the additive-force patch on the N0 lineage (the pins of
   Section 1, hash-asserted at build); the injection points enumerated in
   the manifest; build logs retained from the first failure; the seal bytes
   captured into the lane seal-store/ at creation.
3. THE ARMS: mode0 -> N0-gated (the Tier-1 floor) -> N1-feed-on (the causal
   arm: capture + tampers + the C-battery with the harmonized classifier +
   the N1-P3/P4/P6 assertions) -> the feed-on determinism re-run (N1-P7);
   the feed-off comparison = the N0-gated arm (N1-P2).
4. THE RECEIPT: script-emitted hashes; keyed per-arm blocks; the delta_note
   carrying EVERY deviation (the CORRECTION-1 lesson) including the Section
   2-3 amendment execution; the canonical text cited per F4; the verdicts
   N1-P1..P7 decided in-run; a falsified prediction is a recorded result.
5. Sergeant review through the Lieutenant; author self-review certifies
   nothing; no merge/review authority claimed; no Git mutation in any shared
   checkout by this lane; slots 2/3, BUSY = retry >= 10 s; --keep-declared
   outputs only; anchor.py before any registry reference.

Anti-tuning, final form: the schedule, the arms, the bounds of Section 5
(declared from the physical account BEFORE the run), and every constant
above are frozen pre-run. k IS THE FORMULA. Any post-run change request is a
FINDING routed to the Lieutenant, never an edit.
