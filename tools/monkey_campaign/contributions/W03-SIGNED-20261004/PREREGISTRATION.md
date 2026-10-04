# PREREGISTRATION DRAFT — W03I-V1: signed-channel instrumentation on the sealed W03 walk line — per-tick attribution closure and the ledger-localization re-attempt

Status: **DRAFT (chain stop 1).** Authored by wk-w03-instrumentation
(dispatch event 609; agent_6b7a6fb2; roster "the signed channels prereg
draft"), lane-host clock 2026-10-04 00:2x CDT (the recorded host-clock
anomaly; the authoring context date 2026-10-02 differs — both stated, no
date is evidence). Phase 1 = design + prereg DRAFT only: ZERO runner jobs,
ZERO seals, ZERO Git mutations by this lane. This draft awaits the
Lieutenant's pin; FINALIZE-AT-FREEZE slots are filled once at run time; any
required prereg commit goes through the publication owner BEFORE any gated
experiment. Nothing here is a run claim.

Inheritance of record: the WALK-PHYS-20261004 battery (prereg pin commit
`2b58118cae81110b8e1c69a26e83d0aadab002f4` on `origin/review/WALK-PHYS-20261004`,
blob content sha256 `b4326a0971326db3d6267c9e00a9372ce33707d084b11a897417406e319de3fe`;
seal of record manifest `a1758df0478d62cf0994f1a35464a13d24a8c91b7fe6c935d2c3070ad46302d2`,
battery job `28b28e4730524d4fa2cb2f83e6237bf9`; published as PR #328, merged
at `42614bac`) returned verdict **FALSIFIED_OR_PARTIAL**: G_PROPULSION=false
(the corrected momentum-change identity fails 61/240 window ticks; failures
cluster at impacts and at the direction-free serialization blind spots) and
G_ENERGY=false (the pre-accepted ledger negative, localized in-window:
`balance_error_J` raw `30.970713623726674` at tick 300, bit-identical to the
sealed W03 anchor). This lane does NOT repair that record — it is the
long-queued instrument extension the record's own feed-forward names, and it
re-answers the physics with new sealed evidence through the same chain.

## 0. The question this lane answers, and the claims it never makes

THE QUESTION (either answer is a result): with SIGNED channels recorded, does
per-tick propulsion attribution CLOSE at the headless class, and does the
30.970713623726674 J imbalance localize to named channels/substeps?

QUALIFIES (at the HEADLESS CLASS only): the sealed W03-class articulated walk
scene's per-tick momentum change attributed to a NAMED, SIGNED channel set;
the energy-ledger imbalance localized per tick/substep/channel; the signed
evaluators proven non-vacuous by executed mutants.

NEVER CLAIMS (the not-claims, at maximum): this is instrumentation physics —
NOT player control, NOT the product runtime, NOT a launchable build
(PLAYABLE_BUILD.json nulls stand), NOT real-time play (TC-11), NOT a trained
policy, NOT anatomical-hand or grasp/climb transfer, NOT uneven-ground
traversal (F06 negatives stand). No change to any sealed W10/W03/WALK-PH row:
PR #328's FALSIFIED_OR_PARTIAL verdict is the standing record and is
superseded only by new sealed evidence through the chain, never "repaired".
Fore-LIMB pads, never "hands" (the accepted claim-wording law). The withdrawn
universal "nothing-hidden-moves-the-body" is NOT restored by this lane under
any outcome; a P3-SIGNED closure supports only the narrow claim that the
NAMED channel set accounts the per-tick momentum change on the clean arm at
the headless class. No engine-ledger fix is delivered here: a closure debt
repair is a NEW prereg through the publication owner.

## 1. Design of record and the declared instrument extension

Design: the SAME sealed physics bytes on every clean arm — scene
`chimera.earth_scene.v1` sha256
`f6844eeae3dc87170a572ccdeedf326a6cac4f73d1448941808bd8b25a8db342`, 14
bodies / 18 coordinates / 12 capped drives / 8 contact points /
10.037998000000004 kg — with an EXTENDED declared instrument arm
(`W03I`), the WALK-PHYS instrument lineage plus a NEW declared
engine-recording patch. Source lineage (all extracted read-only from the
shared object database; NO worktree, NO clone — NO_WORKTREES.md sha
`7d3fe1029f727b95ff2c832b06a89b3bac40f59e14993440255636218645f433` obeyed):

- revision `17ba94b948ca217c1bbf8f7dee5b51b995b387bb`: blob
  `5863348f2deef1f01e3cf761d0c4151a10035a6d` = `gait_controller.hpp`
  (content sha256 `f0ffea12795bd47f7c48f5ed9b8aa98869725467d94a1081b1d942f6fba129bd`),
  blob `a7bfe15e34e25a34c5316d65038b072d79ac529a` =
  `gait_unit_viswalk_dump.cpp` (content sha256
  `dea2be78762860b201a348824fd6a4a4fe9f2a1dd3f9552157187729568f1cab`),
  blob `8cd6004fc4a65f2f804ff1e00c18f1962bbaa9f0` = `build_dump.ps1`
  (content sha256 `2e3fcf50933d177c932bacf18dbbcf12f7e79b4346fcfa9512dcddbdb0b33200`).
- WALK-PHYS layer (hash-verified this lane): `INSTRUMENT_PATCH.py`
  (`d71777d357a08c161ff1b9934b47175f9c8aead47d3f7da8fcd6d65786424e20`)
  producing `gait_unit_viswalk_dump_walkphys.cpp`
  (`35ae38c131818f4def9d116a335b2e66a0050c4f8b56e0b11837735b497b2086`);
  runner driver `run_battery.py`
  (`88d781e2f7455f9cc57bbef603ae8a5c968b53607df3a072c1253b584ae077e7`).
- NEW (this lane): `INSTRUMENT_SIGNED_PATCH.py` — a declared patch script
  producing (a) a derived engine-recording header from pinned blob
  `5863348f...` and (b) the `W03I` dump from the WALK-PHYS instrument
  bytes. Every added line is anchored, enumerated, ADDITIVE-ONLY,
  PURE-RECORDING (reads existing values into new recording accumulators;
  no assignment to any physics-reachable state; no reordering of any
  original expression), and gated behind `GAITPHYS_SIGNED=1` so unset envs
  keep the original code path (the P1 anchor law, extended to the engine
  recording layer). The patch manifest enumerates every added line with its
  read-only justification and ships in the sealed package.

Why the engine-recording layer is REQUIRED (declared, not hidden): the dump
process sees only the public interface (`status()/speeds()/angles()/
configure()/timestep()`; `State s_` is private). The missing signed data —
per-substep friction directions, impact-solve tangent and joint-stop row
multipliers, the rhs decomposition, the mass-metric positional-correction
du — exists only inside `rate()/free_step()/impact()/advance()`. The
WALK-PHYS telemetry serialized the engine's direction-free scalars; that
serialization gap IS the P3 blind spot (35/61 failing ticks at impacts;
16/61 zero-serialized-friction-despite-loaded-pads, convention-robust).

### The declared v2 telemetry schema (recorded to FILES only; no new stdout/stderr byte in any mode)

S1 PER-CONTACT SIGNED IMPULSE VECTORS, split by attribution class
   (continuous-solve vs impact-solve, never merged):
   world-space `impulse_east_N_s` / `impulse_up_N_s` / `impulse_south_N_s`
   per contact point per tick — up = the signed normal impulse
   (`contact_force_impulse` class), east/south = RK4-weighted signed
   tangent components `sum_substeps h*(lambda_t_stage*dir_stage)/6` where
   `dir_stage` is the engine's own per-stage friction direction (slip
   direction when planar slip > kSlip, else the sticking
   bias+acceleration-prediction direction — exactly the engine's law), plus
   the per-point per-coordinate generalized impulse row (at minimum the
   `base_trans_x` row; full rows emitted), plus the existing per-tick
   aggregate `contact_generalized[n]` carried as a cross-check (per-point
   rows must sum to it within FP; a mismatch is an instrument defect).
S2 IMPACT IMPULSE CHANNEL (exists as scalars `impact_impulse_N_s`/
   `normal_impulse_N_s`; extended): the impact-solve's per-point signed
   world vector (normal lambda_n + tangent lambda_t*dir at the impact
   solve's own direction), its per-coordinate generalized row, and the
   event-split provenance (the `advance()` event tree, bounded by the
   engine's own 3000-call require).
S3 JOINT-STOP CHANNELS: per-drive signed generalized stop impulse per tick
   (the `stop_row` multipliers from both the continuous projection and the
   impact solve — currently unrecorded), plus stop constraint work split
   out of `constraint_work_J` (the engine's own E8 discrete form
   `lambda*(v_start+v_end)/2` applied per stop row).
S4 CONTACT CONSTRAINT WORK SPLIT: the same per-row E8 form for contact
   rows, so `constraint_work_J` == contact + stop + any other row class,
   enumerated, with the sum identity emitted.
S5 GENERALIZED MOMENTUM `p_i = (M v)_i` recorded per tick (a pure read of
   an existing product) — makes the attribution identity EXACT rather than
   a mass-scalar finite-difference approximation.
S6 ACTUATOR/SERVO/RHS CHANNELS: per-drive actuator impulse (the engine's
   own `sum_substeps tau*dt/4` law) beside the existing per-drive
   `actuator_work_J`; the posture/trunk drive named separately (it is
   joints[12] today); per-coordinate RK4-weighted rhs decomposition
   `grav_bias_ext_imp[i]` (gravity - bias + external piece) and
   `damping_imp[i]` (the drive-damping piece), with the rhs-sum identity
   emitted; battery/brake/empty counts carried.
S7 SUBSTEP DECOMPOSITION: per tick, per `advance()` call (4 nominal
   substeps; event splits counted): {delta actuator work, delta damping
   heat, delta friction heat, delta impact heat, delta constraint work
   (contact/stop), delta external}. DECLARED ABSENT: the RK4 stage
   internals inside `free_step` remain unrecorded; the localization
   granularity is the advance() boundary (the recipe's `substeps==4`
   require stands, never relaxed).
S8 POSITIONAL-CORRECTION CHANNEL: per correction event {point set, dq_max,
   du, per-point lam*gap} — the engine's mass-metric least-norm q shift and
   its booked `s.impact -= du`; today visible only as GAIT_EVENT_TRACE
   stderr lines; in W03I it is recorded to the TELEMETRY FILE (no new
   stderr byte; the stderr anchor must remain byte-exact).
S9 RECEIPT CENSUS: every config key and every GAITPHYS_* env recorded in
   the receipt (carried from the WALK-PHYS runner law).

Emission law: telemetry FILES only; `GAITPHYS_TELEMETRY`-class env-gated;
with every env unset the W03I binary must produce byte-identical
stdout/stderr/qstream to the sealed anchors (P1). Telemetry volume is
bounded (8 contact points, 18 coordinates, 4+ event-bounded substeps) and
the emission path never allocates conditionally on physics values
(determinism).

## 2. Frozen predictions (all evaluated with named variables; acceptance = sealed receipt)

Units law (durable lesson 1, made procedure AT FREEZE): every evaluator
formula in the receipt carries a UNITS line naming the physical unit of
every term, and the receipt records a dimensional-analysis check per
formula BEFORE any numeric claim. Canonical naming law (lesson 3): manifest
hashes are receipt keys; seal-directory ids are lineage convenience only.
Early-refusal law (lesson 2): every windowed evaluator below declares its
truncation behavior AT FREEZE — a windowed gate evaluated on a truncated
tick set can never produce a full-window PASS; it reports
TRUNCATED(prefix_len) with the common-prefix comparison, and the truncation
itself is part of the recorded result.

- P1 ANCHOR IDENTITY, EXTENDED FLOOR: the clean W03I arm (all GAITPHYS
  envs unset; the instrumented engine-recording header compiled in) must
  reproduce EXACTLY at recorded precision: scene sha
  `f6844eea...a8db342` (input identity); stdout sha
  `8c537cdb7cb8c43cf9423cb50056787bcc31ee487d70d3c2a1e73ed5d60b06cc`;
  stderr sha `c6f9b6c00a1d549a4bc709724d2f62f8f28b37823696de4689e1950651c37481`
  (recorded-hash comparison; no stderr bytes preserved anywhere — the
  carried W03 law); q-dump run1 sha
  `b47b709c43a021d24bfee13bb2fe4592167cf205ee0abf9971de462319389c93`;
  run2 == run1 bit-identical; ticks 302 (0..301) ending in the sealed
  refusal; base dx `0.9131056683968011`, dy `-0.7178374101385098`; worst
  ledger balance raw `30.970713623726674` J at tick 300 (store
  `30.970713623726652`). FAILURE = the recording layer perturbs physics —
  the lane records the failure and stops (no tuning to recover).

  THE PAIRED-INSTRUMENTATION HONEST SCOPING (mandated by the accepted
  claim-wording audit; part of the gate's meaning, not a footnote): P1 is
  TRACE-REPRODUCTION EVIDENCE AT RECORDED PRECISION. It is NOT a proof of
  zero perturbation, and this lane runs NO paired instrumented/uninstrumented
  test. The declared assurance class is exactly: (i) the pure-read
  recording law, line-enumerated in the sealed patch manifest; (ii) the P1
  anchor identity; (iii) two-pass determinism (P8). No stronger
  non-perturbation language may appear in any receipt or report from this
  lane.

- P2 SIGNED TELEMETRY COMPLETENESS: every tick of the clean arm emits the
  complete S1-S8 schema, finite, with the declared units; the receipt
  carries the channel census (any structurally-zero channel named, e.g.
  `external` with push_N=0). A missing or non-finite channel = instrument
  defect: the run is recorded as FAILED INSTRUMENTATION and stops — never
  silently tolerated, never imputed.

- P3-SIGNED PER-TICK ATTRIBUTION (the re-evaluation; the honest either-way):
  window [60, 300] (the carried walk window; the clean arm provides ticks
  0..301). For every tick t and every coordinate i, the EXACT discrete
  impulse-momentum identity on the recorded channels:
  `p_i(t+1) - p_i(t) - (contact_gen[i] + contact_impact_gen[i] +
  stop_imp[i] + actuator_imp[i] + damping_imp[i] + grav_bias_ext_imp[i])
  = residual_i(t)`  [all terms N*s = kg*m/s; units line emitted].
  Reported for the full vector; decided at minimum on `base_trans_x`
  (east). The world-space companion (units N*s = kg*m/s on both sides):
  `m_total * (COM_east(t+1) - COM_east(t)) - (sum_k fx_signed_k(t) +
  sum_k fx_impact_k(t) + external_east_imp(t)) = residual_east(t)`.
  FINALIZE-AT-FREEZE window: the identity class closes at the 1e-12
  relative per-tick house noise; the declared PASS window is set once at
  freeze with its derivation (candidate: 1e-9 absolute on N*s per
  coordinate per tick, justified against the recorded FP scale), never
  after seeing data.
  OUTCOME A (CLOSURE): all window ticks inside the window — per-tick
  attribution CLOSES on the named signed channel set; the WALK-PHYS P3
  blind-spot diagnosis (direction-free serialization) is answered
  affirmatively at the headless class.
  OUTCOME B (RESIDUAL): any violating tick is localized by tick,
  coordinate, and residual channel-class; the residual IS the result
  (an unrecorded or non-additive channel exists; the named-candidates list
  stays open). No tuning; no window sweep; the gate never moves.
  Either way the prior G_PROPULSION=false record stands until the chain
  supersedes it with this sealed evidence.

- P4 LEDGER RE-ATTEMPT (both-ways frozen): per tick, the recorded split
  with the NEW channels: `|d(KE) + d(PE_grav) - (W_actuator + W_external +
  W_damping + heat_impact(incl. the positional-correction du split out) +
  heat_friction + W_brake + W_constraint_contact + W_constraint_stop)|`
  emitted per tick AND per advance() call (S7). Two mandatory properties:
  (m1) IDENTITY-WITH-ANCHOR: the cumulative balance at tick 300 EQUALS the
  sealed raw `30.970713623726674` J at recorded serialization precision —
  if it does not, the instrument is not accounting the same ledger: that
  is an INSTRUMENT DEFECT (stop), not a physics finding; (m2) LOCALIZATION
  (either answer is a result): the imbalance is attributed per tick,
  substep, and channel. The pre-registered candidates (named BEFORE any
  run, from the engine source): the joint-stop rows' unattributed share of
  `constraint_work_J`; the contact rows' share (all rows share one E8
  scalar today); the positional-correction du (booked inside the impact
  aggregate today); per-point impact-vs-friction heat shares; the drive
  store-bisection tau rescaling; damping; battery/brake bookkeeping; the
  external channel (structurally zero here, push_N=0). A channel that
  closes the ledger within the FINALIZE-AT-FREEZE window (1e-6 J/tick
  class) is NAMED; if none does, the receipt says so: "energy ledger NOT
  closed on the native walk line; the imbalance does not localize to the
  declared channel set; closure is engine debt". No repair in this lane.

- P5 ZERO-FRICTION CONTROL (carried; frozen form corrected per the P5
  lesson): declared delta = scene `friction_mu` 0.6 -> 0 (one field),
  everything else identical, same seed. The sealed mu0 arm refused at tick
  65; the frozen evaluator: on the COMMON window [60, min(last_clean,
  last_mu0)) report the per-tick COM-east advance ratio and the refusal
  tick; the FIRES condition (no-animation law): mu0 mean per-tick advance
  exceeds the clean arm's mean per-tick advance by more than 1% on the
  common window (friction-independent propulsion would have to ADVANCE the
  body faster than the frictional gait, not merely coast); the collapse/
  coast classification (coast at the declared entry-velocity class) is
  recorded beside it. TRUNCATED reporting per the early-refusal law; the
  common window may be short — that is a recorded fact, never normalized
  away.

- P6 DRIVE-CUT CONTROL (carried; frozen form = the IMPLEMENTED invariant,
  per the Appendix-2(b) correction): `power=false` at declared t_cut=150.
  GATE (high-water form): horizontal COM momentum never exceeds its
  tick-150 post-cut value through t_cut+100, within the frozen window.
  EMITTED, NOT GATED: the per-step rise census (the sealed arm showed 24
  local rises, 20 beyond 1e-6, transient at ticks 193-202) — emitted every
  run so the weaker wording can never silently masquerade as the frozen
  one. The no-cruise reading is a reported interpretation, not a gate.

- P7 CAP-RAISE TAMPER (carried): one drive cap x1.5 (the sealed arm used a
  hip). MUST be caught: the cap/work-envelope detector fires (sealed
  evidence: 26 ticks beyond the sealed cap, zero in clean) AND the new
  signed actuator channel (S6) independently shows the raised impulse
  envelope. A clean-running cap-raise = vacuous detector = tooth fired.

- P8 DETERMINISM: two full clean passes, byte-identical stdout, stderr
  (hash), q-dumps, and telemetry files (house standard, extended to the
  v2 streams).

- P9 STATE-WRITE INJECTION (carried): a declared state write through the
  public accessor at a declared tick must diverge exactly at the injected
  tick against the clean continuation (sealed evidence: first_divergence_tick
  100). Divergence elsewhere = the probe is not surgical = recorded and
  investigated before any further claim.

- P10 SIGN-FLIP TOOTH (NEW; the signed evaluator's non-vacuity; mandated
  by the mission): a declared TELEMETRY-ONLY mutant arm
  (`GAITPHYS_MUTANT=signflip`): the emitter flips the sign of the emitted
  east/south tangent components of S1 (both attribution classes) on the
  otherwise clean run. TWO frozen assertions, BOTH must hold:
  (t1) the P3-SIGNED world-space evaluator's pass-count on the flipped
  stream is strictly smaller than on the clean stream, with at least one
  tick failing flipped while passing clean at which the flipped tick's
  total |tangent impulse| exceeds the frozen floor (1e-9 N*s class);
  (t2) the flipped stream's median |residual_east| strictly exceeds the
  clean stream's.
  The mutant arm's P1 anchor set (stdout/stderr/q-dumps) must STILL be
  exact — proving the mutant touched only telemetry bytes. If either
  assertion fails, the signed evaluator is VACUOUS: tooth fired, G-TEETH
  false, and no P3-SIGNED claim may be entered from this lane.

## 3. Qualification gates and verdict classes

- G-ANCHOR: P1 (the extended floor) + the P10 mutant-arm anchor side-condition.
- G-INSTRUMENT: P2 (completeness) + P4(m1) (identity-with-anchor at tick 300).
- G-ATTRIBUTION: P3-SIGNED — Outcome A = CLOSED; Outcome B = RESIDUAL with
  the localization receipt. Both are recordable outcomes; NEITHER is
  downgraded by the other's class.
- G-LEDGER: P4(m2) — LOCALIZED (a named channel closes the window) or
  NOT_LOCALIZED (the honest negative, sharpened); m1 failing is never a
  ledger outcome, it is an instrument refusal.
- G-TEETH: P7 caught + P9 exact-divergence + P10 both assertions.
- G-DETERMINISM: P8.
VERDICT CLASSES (this lane's own receipt):
- ATTRIBUTION_CLOSED: G-ANCHOR/G-INSTRUMENT/G-TEETH/G-DETERMINISM green AND
  G-ATTRIBUTION = CLOSED (G-LEDGER either way, reported in its own class).
- LOCALIZED_PARTIAL: gates green, G-ATTRIBUTION = RESIDUAL and/or
  G-LEDGER = NOT_LOCALIZED, with the localization receipts.
- FALSIFIED: any anchor, instrument, tooth, or determinism failure — the
  negative is the result and is reported to the Lieutenant unchanged.
The overall W03-class verdict remains the chain's business: this lane's
receipt FEEDS it; it does not self-advance any gate.

## 4. Anti-tuning law (standing, carried + extended)

No drive cap, friction value, gait table, zero map, mass, inertia, entry
speed, servo gain/frequency, tick rate, substep count, contact point, or
plane height may differ between the sealed scene and any CLEAN arm. The
only declared deltas: the control arms (P5 mu=0, P6 power-cut at 150, P7
cap x1.5), the P9 injected tick, and the P10 telemetry-only mutant — each
declared BEFORE any run, each expected to be visible or to lose
support/motion. Instrument schema, windows, tolerances, and mutant
semantics are declared in this prereg BEFORE any run and never swept; a
FINALIZE-AT-FREEZE constant is set once at freeze with its derivation,
never after seeing data. Any gate that would pass only under a clean-arm
parameter change (including a tolerance relaxation) is a tune_to_success
refusal: the lane records it and stops. The engine-recording patch may not
touch any existing expression: an anchor failure traced to the recording
layer is recorded as FALSIFIED, never patched around.

## 5. Execution plan (phase 2, not started; zero jobs launched at stop 1)

- All execution through `E:/PythonChimera/tools/monkey_campaign/
  task_package.py seal|run` with absolute paths; dispatched runner slots
  per this lane's dispatch (slots 2/3); BUSY = wait/retry >= 10 s, never a
  second directory. Package: NEW lane package; base = this lane's prereg
  pin; writes = a NEW contribution directory `W03-SIGNED-20261004`
  (distinct from WALK-PHYS-20261004; no other lane's byte touched).
- PREREG-FIRST: this draft, once pinned by the Lieutenant, is committed
  through the publication owner (the WALK-PHYS alone-first pattern, commit
  `2b58118c`) BEFORE any gated experiment; the package seal then pins that
  commit. A seal is not a substitute for the commit.
- PRE-GATED FEASIBILITY PROBE (declared, not a qualification run): build
  the W03I binary from the pinned chain (orig blob + WALK-PHYS patch +
  signed patch) inside a slot; 1-tick smoke with telemetry on. Outcomes:
  OK / BLOCKED(toolchain) — a BLOCKED is reported as the smallest missing
  prerequisite (the known class: vcvars quoting, cl PATH, include closure,
  1-tick truncation crash, keep-path resolution — all five prior refusals
  preserved in the lineage), never worked around outside the runner.
- Battery: P1 x2 (clean, envs unset), P2-S8 channels on the clean arm,
  P5/P6/P7 control arms, P8 second pass, P9 injection, P10 sign-flip
  mutant. All receipts + traces declared with --keep; evidence anchored
  through anchor.py before any reference.
- Cost estimate (from the sealed lineage): ~7-14 s CPU per 302-tick arm at
  the measured 23-46 ms/tick; the whole battery well under 15 min CPU
  across the seven arms; slots 2/3 with retry-on-BUSY.

## 6. Honest-absent list (declared BEFORE any run)

- RK4 stage internals inside `free_step`: UNRECORDED (the substep
  decomposition granularity is the advance() boundary; declared in S7).
- The engine-ledger REPAIR: ABSENT (a localization result, either way; the
  fix is a future prereg through the publication owner).
- Paired instrumented/uninstrumented perturbation test: ABSENT BY
  DECLARATION (the P1 scoping above; the collaborator's accepted
  correction stands).
- Launchable build / real-time / product runtime / player control: ABSENT
  (out of scope by the not-claims; the headless class only).
- Measured volar friction: ABSENT (0.6/0.4 remain NAMED PLACEHOLDERS,
  NB-01/02; fixed declared inputs, never tuned here).
- The universal no-hidden-channel claim: WITHDRAWN CLASS (never restored;
  P3-SIGNED outcome A supports only the narrow named-set closure claim).
- The P6 per-step-rise behavior: EMITTED, NOT GATED (the frozen gate is
  the high-water form; the sealed transient rises at 193-202 are recorded
  history, not a target).
- Truncated-window full-window claims: IMPOSSIBLE BY LAW (the early-refusal
  law; P5's common-window form is the standing example).

## 7. Preservation law

The W10 sealed rows, the W03 anchor set, the WALK-PHYS lane (its EVIDENCE
appendices are part of the record), every store row, and every other
lane's bytes are UNTOUCHED. This lane's writes: this lane directory only
(phase 1) + a NEW package contribution directory (phase 2) emitting NEW
artifacts. No Git mutation from this lane; the prereg commit goes through
the publication owner; no merge authority is claimed anywhere. Every
load-bearing artifact this lane reads or writes is hash-recorded in
`EVIDENCE.md` (this lane's file; hashes recorded at write time, amendments
append-only).
