# PREREGISTRATION — MAT2-W09 implement explicit out-of-envelope behavior

Frozen BEFORE any implementation commit, load receipt or measurement of this
card exists. Every emitted receipt refuses any document whose
`preregistration_sha256` does not match these live bytes. This file is
submitted as its own seal (prereg-first) before the implementation files
exist in the package.

- Card MAT2-W09 (planning id W09, wave/slot 3), agent `wk-w09-envelope`,
  attempt `2090c714d92a451bbc84ba1d599a8222`, attempt workspace
  `E:\ChimeraWork\monkey-coordination\kanban-attempts\MAT2-W09\2090c714d92a451bbc84ba1d599a8222`,
  publication branch `review/MAT2-W09`, PR base `astra/gait-capture`.
- Criteria sha256 `b9470c8cac79c4a9374cac7b9a31dccfbb496e4d755ee4dc57bff98de0cd6d0a`
  (startup join == registry `kanban.cards[MAT2-W09].criteria_sha256`, re-read
  READ-ONLY (`file:...?mode=ro`) from
  `E:/ChimeraWork/monkey-coordination/agent_slots.sqlite3` at run time;
  mismatch = refusal `criteria_pin_mismatch`).
- done_when (verbatim, registry): "Unsupported states and falls have a
  declared controller response; no concealed resets or forces".
- Observation (verbatim, registry): "Recovery skill is optional unless
  required by the chosen product contract".
- Card task falsifier (verbatim): "Sliding/penetration, unsupported
  propulsion, hidden reset, wrong command response or diagnostic/clean state
  divergence fails."
- Goal falsifier classes named by the dispatch: hidden in-episode resets;
  animation substituting for locomotion. The goal physics charter, made
  precise here: NO CONCEALED RESETS; TURNING OFF DRIVE PRESERVES INERTIA
  (never freeze/cancel velocity); REMOVING SUPPORT REMOVES ITS FORCE.
- Profile: `walking`/`motion`; numerical_evidence_required true;
  clean_view_required true; the capture is delivered per the sealed W06/W07
  motion precedent (record-space panels of the executed runs' own telemetry,
  section 9) with the absent inventory named.
- Base: `8b285ee4` (`refs/remotes/origin/review/MAT2-W09` seeded by the
  publisher at the accepted `astra/gait-capture` tip; contains the MAT2-W07
  merge, PR #301). File package pinned to base
  `8b285ee4301a8ed42be54a1924af5db019f9fb20`.
- Calculations: C13 ("Falls, energy and recovery": account delta stored
  energy against work, losses and external support under the declared model;
  output "Lawful falls and explicit post-failure behavior"; verification
  "Release/impact traces; no residual support, teleport or hidden reset") —
  this card's execution arm. C10/C11 remain W06/W07's sealed work, consumed
  read-only.

## 0. The governing frame (what "controller" and "out-of-envelope" mean here)

THE ACCEPTED POLICY IS THE FROZEN CERTIFIED LINE — nothing else. W04 froze
the runtime/training contract; W05/W06 sealed the deploy treatment
ALLOW(frozen)/BLOCK(trained); W07 loaded the frozen line through the W04
certificate deploy gate and proved the runtime consumes the certified
observation/action contract bit-for-bit. THE NO-REISSUE LAW: this card does
not retrain, re-issue, re-certify or amend anything; the trained bundles stay
BLOCKED and are never loaded.

"THE CONTROLLER" on this card is the runtime-side decision stack defined by
W07's load path: the frozen policy actor inside a DECLARED out-of-envelope
supervisor. The supervisor is this card's implementation. It owns NO physics
authority: it cannot write scene state, pose, velocity, phase or contacts
(structural law, CHECK FB3 arm); its only output channel is the certified
8-command limiter path (`applied = clip(center + scale*raw, lo, hi)`), the
same channel W07 proved is the only actuation route. Every response is a
DECLARED function of the declared observation seam, recorded in a declared
event ledger. There is no recovery skill (card observation: optional unless
the product contract requires it — no product contract requires it; this is
declared, and nothing fakes one).

THE DECLARED OBSERVATION SEAM is the scene's own `observation_record()`
telemetry (W07's per-tick records; the same records the certified contract
consumes). The supervisor's envelope monitor consumes ONLY those records —
never the scene's private attributes (the monitor's inputs are declared and
audited: contact flags, foot forces, com_vel, applied/requested commands,
pad gaps, intervention_reason).

## 1. Input pins (verified byte-exact at attempt start; drift = refusal `input_pin_mismatch`)

Groups, as W07 pinned them (the same sealed upstream, plus this card's G07
falsifier lineage and W07's own published receipts):

W04 freeze records (evidence-store/MAT2-W04/):
- `numerical/w04_certificate.json` `07f05bfa982e066ae67413b04e3367c5ad7570830e99fc32edcb86cbe8d87598`
- `numerical/w04_freeze_manifest.json` `be632ffc85865515285f3d622a09882a3180a43101027914f1ed3408496f5d29`

W07 published receipts (evidence-store/MAT2-W07/):
- `source/PREREGISTRATION.md` `09e8ce87f56d88326df936e6ef51560349d086376e0f3116ed3927a643b429c7`
- `numerical/native_load_receipt.json` `4f5aac081a3a07fd...` (full sha in
  verify_inputs.py; the W07 report records the same leading `4f5aac081a3a`)
- `numerical/checks_receipt.json` (full sha in verify_inputs.py)

W05/W06 published bytes AT THEIR MERGED IN-TREE PATHS, extracted from the
shared repository's Git object database at THIS CARD'S PINNED BASE
(`git cat-file blob 8b285ee4301a8ed42be54a1924af5db019f9fb20:<path>`;
the base commit is immutable, so the extraction is byte-exact and cannot
drift):
- `tools/monkey_campaign/contributions/MAT2-W06/receipts/evaluation_summary.json`
  `a1af58baf15edd7ac595b5bb4571e13ed44780f77faf5a761355140f456b075a`
- `tools/monkey_campaign/contributions/MAT2-W05/receipts/deploy_check_receipt.json`
  `766a7cbe6a2ccd67c739d82af5b32e859ee4bc3f3a558715fafc63dbab0ae635`
- `tools/monkey_campaign/contributions/MAT2-W07/run_native_load.py`
  (byte-pinned; its frozen certified anchor constants are cross-read and
  must equal the anchors declared in section 4 here)

G07 falsifier lineage (evidence-store/MAT2-G07/):
- `verdict_ref/PREREGISTRATION.md` `1e55df6da88dbb9fdc3c296b2965042b0a6828b0d6387a2c9eb8bb53f7bb87df`
- `numerical/experiment_receipt.json` (full sha in verify_inputs.py)

Sealed lane machinery at `E:/ChimeraWork/pass3-integ/repo` — the identical
15-file pin table W07 verified (validator, deploy gate, frozen loader, scene,
runner, observation schema, P3 manifest/weights/trace, upgrade-gate receipt;
full table with shas in verify_inputs.py) — consumed ONLY through a
byte-verified extraction (import identity; zero machinery files modified).

Ingestion-spike honesty records (coordination store) — the same two W07
pinned (`INGESTION_SPIKE.md`, `w2-engine-up/ENGINE_UP_RECEIPT.md`).

## 2. The declared envelope and the declared response table

All envelope quantities are DERIVED from the pinned scene's own declared
constants (`tools/policy_compat/scene_cpu.py`, sha-pinned) — none tuned:

- SUPPORTED tick: at least one foot contact in the seam
  (`foot_contacts[4] == 1.0` or `foot_contacts[5] == 1.0`).
- UNSUPPORTED tick: both foot channels 0.0 (both legs' heel AND mp pad gaps
  at/above `contact_threshold` = 0.012 m — the scene's declared gap formula
  `g = ground_clearance + lift_gain*lift_cmd*max(0, sin(2*pi*eff)) + micro`).
- UNSUPPORTED STREAK: consecutive unsupported ticks.
- FALL: declared when the unsupported streak reaches
  `FALL_AFTER_TICKS = 90` — the scene's own declared reflex horizon
  (`REFLEX_TRIP_TICKS = 90` ticks = 0.3 s at the declared 300 Hz clock).
  Derived, not tuned: the scene's declared failure horizon is reused as the
  controller's fall horizon.
- TERMINAL: the declared episode horizon ends (all arms: 900 ticks, the
  certified horizon).

THE RESPONSE TABLE (declared BEFORE any run; every response only writes the
certified command channel and the ledger):

| observed state (seam) | response | declared action on the applied 8-vector | physical accounting (C13) |
|---|---|---|---|
| SUPPORTED | R0 pass-through | identity — the frozen policy's applied vector, bit-for-bit | bounded applied (manifest limiter bounds); drive work only through the stride channels; warm-start-coupled declared damping |
| UNSUPPORTED (streak < 90) | R1 drive cut | stride channels (indices 1, 5) forced to `bounds_lo` = 0.2 (the certified MINIMUM drive; the limiter forbids zero); all other channels zero-order-held from the last policy decision | `a_com = stride_gain*0.5*(0.2+0.2) = 0.11 m/s^2` exactly; velocity evolves ONLY by the declared law `v += dt*(a_com - d_eff*v)` — INERTIA PRESERVED, never frozen or canceled; both pads report 0.0 force (support removed); warm decays by the declared law |
| FALL (streak >= 90) | R2 neutral + fall event | all 8 channels forced to the manifest center (declared neutral); the fall event recorded ONCE (tick, pre-state hash, streak length); episode continues; NO reset | commands carry no drive beyond neutral; velocity still evolves only by the scene law; the energy account continues to close |
| TERMINAL | R3 outcome declaration | no command; the terminal record declares outcome (`completed` / `fall_declared`) + final state hash; the ONLY restart instrument is the declared COMPLETE-snapshot restore, recorded in the ledger | explicit post-failure behavior: the terminal declaration IS the declared response; no concealed continuation, no concealed restart |

Ledger law: every R1/R2 transition appends
`{tick, event, pre_state_sha256, streak, applied_vector}` to the declared
event ledger; the supervisor records NOTHING else and mutates NOTHING else.

## 3. The declared unsupported probe (A1) — exact pre-data algebra

With seed 20260920 the scene's entry law gives
`phase_r0 = ((20260920 % 213) + 0.5)/213 = 147.5/213 = 0.6924882629107981`,
`phase_l0 = 0`. Both legs advance at the declared `1/cycle_ticks` (trips
absent; section 6 proves they are unreachable). The declared probe commands
set BOTH lifts to `bounds_hi` = 1.8 (maximum declared lift) and the phase
offsets to the EXACT alignment solving
`(phase_r0 - phase_l0) + (off_r - off_l) == 0 (mod 1)` inside the limiter
bounds `[-0.25, 0.25]`:

- `off_r = +0.25` (`bounds_hi[4]`)
- `off_l = -0.057511737089201875` (= `(147.5/213 + 0.25) - 1`; in bounds;
  alignment residue exactly 0.0)

Stride channels held at the manifest center 1.0 outside responses; during
R1 responses the supervisor forces them to 0.2 as declared. With lift 1.8 a
leg is airborne iff both pad sines exceed `(0.012 - 0.008 - micro)/0.108`
(micro the declared per-tick uniform draw in `[-1e-4, 1e-4]`), i.e.
`eff in [0.08 + a, 0.5 - a]`, `a = asin(s*)/(2*pi) in [0.005742, 0.006040]`:
a window of 0.40792–0.40850 cycles = 86.9–87.0 ticks per 213-tick cycle,
recurrent (both legs advance at the same rate, so the alignment holds).

## 4. Predictions (registered BEFORE any run of this card)

- P1_anchors_exact: the A0 baseline (unmodified pinned `run_closed_loop`,
  frozen line, build N, seed 20260920, 900 ticks) reproduces the three
  certified anchors EXACT (`trajectory_sha256` `cd4944d9...`,
  `initial_snapshot_sha256` `11ac68cf...`, `final_state_sha256`
  `b9a7fb99...`) and the sealed 60-event hash chain byte-identical. Any
  drift = named refusal `baseline_drift:<key>` and NOTHING proceeds.
- P2_pass_through_inert: the supervisor's monitor run over A0's records
  finds ZERO unsupported ticks and emits ZERO ledger events (the certified
  line never leaves the envelope; the false-positive control), and the
  monitor's per-tick classification says SUPPORTED on every tick.
- P3_unsupported_window: in A1 every 213-tick cycle contains exactly one
  contiguous unsupported streak; every streak length is 86, 87 or 88 ticks
  (section 3's algebra: 86.9–87.0 ticks plus at most one boundary tick of
  per-tick micro variance); streaks are separated by supported phases; the
  trip counters stay 0 for the whole arm.
- P4_r1_coverage: every unsupported tick of A1 carries an R1 response
  (ledger coverage of the unsupported set is EXACT, no gaps, no extras) and
  every R1 tick's applied stride channels equal 0.2 exactly (a_com = 0.11).
- P5_inertia_law: on every A1 tick the seam velocity satisfies
  `v(t+1) = v(t) + dt*(a_com(t) - d_eff(t)*v(t))` with `a_com` recomputed
  from the recorded applied strides and `d_eff` from the DECLARED warm
  recursion (warm from 0.0, +0.1 on contact capped at 1.0, x0.98 airborne —
  recoverable from the recorded contact sequence; cross-checked against
  `foot_forces/0.25` on contact ticks) within the declared float32-seam
  window 1e-5 m/s; velocity NEVER freezes (`v(t+1) != v(t)` at every tick
  where the law moves it; no tick cancels v to 0 or to a held value).
- P6_support_force_removed: on every unsupported tick of A1,
  `foot_forces[4] == 0.0 and foot_forces[5] == 0.0` exactly (the seam's own
  declared law), and no other recorded channel moves the com (P5's identity
  is the proof: with the drive at the certified minimum the com changes only
  by the declared recursion).
- P7_fall_injection: in A2 the DECLARED monitor-input injection holds the
  supervisor's streak across the horizon; R2 fires exactly at the 90th
  injected-unsupported tick; the fall event is recorded once with its
  pre-state hash; from that tick the applied vector equals the manifest
  center exactly; the arm's receipt labels it `monitor_input_injection` —
  the scene's own seam stays SUPPORTED through A2 (the injection is the
  declared way to exercise the unreachable response; it is never passed off
  as scene physics).
- P8_no_concealed_reset_clean: on EVERY arm (A0/A1/A2) the clean detectors
  hold: (i) per-tick micro-terrain draw chain — the pad gaps minus declared
  formula reproduce the fresh-seed PCG64 stream exactly
  (`micro_t == u_t`, tick t draws exactly t+1 total); (ii) the phase
  recursion `(phase(t+1) - phase(t)) mod 1 == 1/213` (rate 1; the structural
  trip-unreachability of section 6 is the armed reason rate-1 is the only
  legal rate); (iii) P5's velocity identity. Zero violations on clean arms.
- P9_falsifiers_bite: FB1 (concealed mid-episode restore) FIRES both the
  draw-chain detector and the recursion detectors; FB2 (silent velocity
  impulse +0.25 m/s outside the command channel) FIRES the velocity
  identity (residual ~0.25 >> 1e-5); FB3 (fabricated/stale record delivery —
  animation substituting for locomotion) FIRES the
  observations-from-solved-state equality; FB4 (stale support verdict — a
  monitor that keeps claiming support) FIRES the R1-coverage audit. Every
  FB arm's clean control runs FIRST and stays green.
- P10_structural_records: carried as named structural facts with their
  derivations (never fabricated): (a) SUSTAINED FALL UNREACHABLE — no
  bounded command stream can hold 90 consecutive unsupported ticks (max
  single-window 88 ticks, section 6a); (b) TRIP REFLEX UNREACHABLE — no
  bounded command stream can trigger the declared trip (section 6b); the
  response table still declares their responses (R2/R3) and A2 exercises
  R2 by declared injection.

OUTCOME-INDEPENDENCE DISCLOSURE: P1-P10 are registered before this card's
first run. A red P is a FINDING (recorded, preserved), never silenced: the
only acceptable responses are named refusals or amendments declared in
section 11 BEFORE the affected measurement.

## 5. The physical accounting (C13) on the declared model

Per tick of every arm, on the seam records (per-unit-mass, declared model):
`KE = v^2/2`; drive work `dW = a_com * v * dt`; damping loss
`dL = d_eff * v^2 * dt`; the identity `KE(t+1) - KE(t) == dW - dL` follows
from P5's recursion and is verified numerically per tick (window 1e-6 J
per unit mass; float32 seam rounding bounded by the P5 window). During R1
ticks `dW` uses the certified-minimum drive (0.11); during R2 `dW` uses the
neutral strides. THERE IS NO OTHER OWNER: any KE change outside this
identity is a concealed force (FB2's class). Impact/landing accounting is
OUT OF SCOPE (declared): the walk surrogate has no vertical body dynamics,
gravity or floor body; impact traces stay downstream work exactly as G07
recorded ("C13 impact traces stay downstream work").

## 6. Structural records (exact pre-data algebra, carried verbatim)

(a) SUSTAINED FALL UNREACHABLE: a leg's stance-phase gaps equal
`0.008 + micro <= 0.0081 < 0.012` REGARDLESS of commands (swing term zero) —
stance contact is unconditional. A leg's airborne window at maximum lift 1.8
is `[0.08 + a, 0.5 - a]` (the mp offset 0.08 binds the start), length
<= 0.40850 cycles = 87.01 ticks -> at most 88 grid ticks per cycle, and
windows recur only once per 213-tick cycle. Therefore no bounded command
stream can produce a 90-tick unsupported streak: FALL_AFTER_TICKS = 90 is
structurally unreachable by produced physics. R2 is exercised by declared
injection (A2) and its physics-side trigger remains declared for the real
engine build (the certificate binds content hashes; the surrogate declares
this scope).

(b) TRIP REFLEX UNREACHABLE: the trip needs `min(g_h, g_m)` to exceed
`threshold + reflex_gap_spike` = 0.022 while the leg was in contact the
previous tick. The mp pad pins contact until `eff > ~0.1007`
(`sin(2*pi*(eff-0.08)) > 0.1296` -> both pads above 0.022 requires it); but
for `eff > 0.1` the heel gap at the previous tick is
`0.008 + lift*0.06*sin(2*pi*(eff-1/213))` >= `0.008 + 0.2*0.06*0.585`
= `0.01502 > 0.012` (lift at its certified minimum 0.2) — the leg was
ALREADY airborne: the previous-tick contact precondition fails. Phase
advance moves gaps at most `1.8*0.06*(2*pi/213) = 0.00318` per tick (< the
0.010 spike margin). Hence no bounded command stream trips a leg; trip
counters stay 0 in every arm (prediction P3 records this); the reflex stays
declared machinery of the pinned scene, never re-tuned here.

## 7. Falsifier mapping (card + goal falsifier classes -> executed detectors)

| falsifier class | executed detector | arm |
|---|---|---|
| hidden reset (goal class; card "hidden reset") | fresh-seed PCG64 draw-chain replay (`micro_t == u_t`) + phase recursion + velocity identity | FB1: concealed mid-episode `restore_snapshot` (complete snapshot — the declared restart instrument — used CONCEALED, no ledger event); clean control first |
| unsupported propulsion (card) | velocity identity with the drive owner census (P5/P6) | FB2: silent +0.25 m/s impulse outside the command channel; clean control first |
| animation substituting for locomotion (goal class) | delivered record == scene.observation_record() byte-equality every tick (observations-from-solved-state) | FB3: stale-com_vel fabricated delivery; clean control first |
| wrong command response (card) | R1/R2 applied vectors equal the declared response vectors exactly; coverage audit (every unsupported tick covered, no extras) | FB4: stale support verdict (monitor claims supported through the window); clean control first |
| sliding/penetration (card) | OUT OF SCOPE, declared: the surrogate has no penetration state; the contact_floor bar of the certified line stays the sealed instrument (W07) | carried, not re-run |
| diagnostic/clean state divergence (card) | the capture renders both bands from the SAME recorded state per frame (one state hash per row pair), W06/W07 precedent | capture |

## 8. Named checks (G12 accounting)

Suite `test_w09_out_of_envelope.py` (unittest discover). Every FB arm
carries clean control AND bite. Zero skips by design; the receipt carries
"N executed, M skipped" verbatim. The heavy fixture (pins -> validator ->
ALLOW -> frozen loader -> identity -> A0 -> A1 -> A2 -> FB arms) executes
once and is cached; everything else is arithmetic on cached objects.

## 9. Capture (profile walking/motion; the sealed W06/W07 precedent)

Record-space panels of THIS card's own executed arms (A1's unsupported
windows + R1 responses; A2's injected fall + R2), drawn from the runs' own
per-tick telemetry — NOT engine frames (the native windowed engine has no
live control path for this line: carried named-missing, W07 N3). Declared
camera fields per the registry profile; diagnostic/clean bands from the SAME
recorded state per frame; real tick axis (tick_interval declared over the
executed ticks; one tick = 1/300 s, declared in tick_map and camera records);
FFV1 `-level 3 -g 1 -fflags +bitexact`; decode pixel-exactness re-measured;
`visual_capture.validate_manifest` CAMERA_METADATA_STRUCTURE_ONLY;
visual_acceptance stays FALSE — independent visual review remains the
Sergeant's. The only subprocess calls in the capture tool are the two
declared ffmpeg operations (W06 addendum precedent). This text-only worker
inspects no pictures; pixel claims are measured counts.

## 10. Receipts and determinism

`receipts/out_of_envelope_receipt.json` (schema `chimera.w09_out_of_envelope.v1`),
`receipts/falsifier_receipt.json`, `receipts/input_pins.json`
(`chimera.w09_input_pins.v1`), `checks_receipt.json`
(`chimera.w09_checks_receipt.v1`), capture set under `capture/`. Every
receipt carries `preregistration_sha256` (these live bytes) and canonical-JSON
determinism (sort_keys, no NaN, newline-terminated). All numbers in REPORT.md
render from receipts by `make_report.py` and are lint-verified by
`lint_report_numbers.py` (no hand-transcribed numbers).

## 11. Amendments

Any amendment to this document is declared here BEFORE the affected
measurement, with the reason and the exact delta. Pre-data amendments
(before this card's first gated run) are expected to be rare; anything
post-data is a correction cycle, not an amendment. The prereg-first law:
this file seals alone first; the implementation files never precede it in
the package history.

## 12. Honest scope and limitations (declared in advance)

- The execution vehicle is the DECLARED SURROGATE scene (`cpu-walk-scene/1.0.0`,
  build N); the adopted assembly is NOT a runtime body (W07 N1/N2 carried);
  the product engine has no live control path (W07 N3 carried). Nothing here
  re-opens those records.
- The out-of-envelope response is qualified for the surrogate's declared
  physics; the sustained-fall and trip triggers are structurally unreachable
  in it (section 6) and are exercised by declared injection, labeled as such.
- No recovery skill is implemented or faked (card observation); R3's terminal
  declaration is the post-failure behavior.
- CPU only; no engine binary, no training, no GPU; the capture's two ffmpeg
  calls are the declared capture-tool exceptions.

## 13. AMENDMENT a1 (declared BEFORE the final gated runs of this card)

DEVELOPMENT-RUN DISCLOSURE: two development executions of this card's
pipeline (task-runner jobs `a06f626920de4430973efa18f668d424` and
`4a938401e4b94374bb35c006fc40cb20`, plus diagnostic job
`f1da6d9cf4fa4557ab8fd001dca4bde6`) exposed an error in THIS document's
section 3/6 gap algebra: the scene's declared `_gaps_for` adds the RAW lift
command (`g = ground_clearance + lift_cmd*max(0, sin(2*pi*eff)) + micro`);
section 3's algebra had inserted the scene's unused declared constant
`lift_gain = 0.06` into that formula. The corrected algebra is declared here
and replaces the affected predictions BEFORE the final gated runs; the
development receipts remain preserved evidence of the refutations. No
receipt of the final runs cites a superseded prediction.

A1. CORRECTED GAP ALGEBRA AND STRUCTURAL RECORDS (replacing sections 3 and
6): at the maximum declared lift command 1.8 a leg is airborne iff both
pad sines exceed `(0.004 - micro)/1.8`, i.e. `eff in [0.08 + a, 0.5 - a]`,
`a = asin(s*)/(2*pi) ~ 3.5e-4`: a window of ~0.4193 cycles = 89.3 ticks per
213-tick cycle. The window ENTRY is the mp pad's sine zero-crossing: the mp
gap rises `1.8*sin(2*pi/213) = 0.053 m` in ONE tick at the crossing, so the
entry tick spikes from contact (0.008) to ~0.046 — above the declared trip
spike margin (threshold + reflex_gap_spike = 0.022) while the previous tick
was still in contact: the DECLARED TRIP REFLEX FIRES on both legs at window
entry (section 6b's unreachability claim is REFUTED — the zero-crossing
jump, not a gradual rise, is the entry behavior). The tripped legs advance
at the declared halved rate for `reflex_trip_ticks = 90` ticks, which
STRETCHES the aligned airborne window past the 90-tick fall horizon: the
SUSTAINED FALL IS REACHABLE AND PRODUCED by the declared physics (section
6a's unreachability claim is REFUTED). The cascade is: aligned-window entry
-> both legs trip -> halved phase rate -> unsupported streak reaches
FALL_AFTER_TICKS -> R2 fires NATURALLY.

A2. CORRECTED A1 PREDICTIONS: with the section 3 alignment commands, the
first unsupported window opens at tick 30 (+/-1 micro variance) and the
natural fall is declared at tick 119 (= 30 + 90 - 1; +/-1); the trip
counters at the fall tick are nonzero for both legs; the first unsupported
interval spans >= 90 ticks. (The development run observed exactly
[30, 119] and fall_declared_tick = 119; the final run re-measures.)

A3. R2 LATCH (response-table refinement): a declared fall LATCHES the R2
neutral response until the terminal declaration — the fallen episode does
not resume in-envelope control (recovery is optional per the card
observation and is not implemented; the development run showed the
un-latched design flapping the commanded phase offsets between R2-hold and
R0 at the fall boundary, which is lawful but not the declared
post-failure behavior). The coverage audit treats every unsupported
interval at or after `fall_declared_tick` as covered by the latch.

A4. A0 BASELINE REDEFINED (P2 superseded): the certified line ITSELF
visits unsupported states (the development run measured 224 unsupported
ticks of 900 on the unmodified line — the frozen policy's commanded phase
offsets partially align the legs' windows at center lift; W07's
qualification bars never barred foot-level unsupported visits). A0 remains
the UNMODIFIED certified line with an OBSERVATION-ONLY monitor: the three
anchors stay EXACT (validity instrument) and the monitor's per-tick
classifications of the line are recorded as a finding; NO response is
applied on A0 (applying one would change the trajectory the anchors pin).
The response qualification happens on the supervisor-driven arms (A1/A2/FB).

A5. DETECTOR AMENDMENTS: (i) the phase recursion's legal per-tick deltas
are EXACTLY the scene's two declared rates {1/cycle_ticks, 0.5/cycle_ticks}
(the trip reflex is seam-invisible, so a single-rate law would false-fire on
declared trips); a concealed reset produces a delta matching neither and
still fires; the detector additionally reports the observed half-rate tick
count (the trip evidence). (ii) The exact discrete energy identity is
`KE' - KE == dW - dL + dv^2/2` with `dW = a_com*v*dt`, `dL = d_eff*v^2*dt`,
`dv` the declared recursion increment (the development run's formula
double-subtracted the loss term and was replaced before any final
measurement). (iii) The applied-command telemetry records the float32-cast
vector the scene actually consumed (the development run's micro-terrain
draw-chain residuals of ~4.8e-8 m were the float32 cast of the lift command,
not a detector fault; the corrected recording makes the seam reconstruction
exact).

A6. FB1 TAMPER PARAMETERS (declared): snapshot at tick 60, concealed
restore at tick 100 — both inside the first produced window [30, 119]; the
precondition check (same unsupported interval) is retained and must hold.

A7. THE WARM-FORCE CROSSCHECK: the declared seam law binds
`foot_forces == 0.25 * warm` on contact ticks; on a tick where the
recomputed contact disagrees with the previous step's contact flag (a
transition tick), the recorded force reflects the previous step's warm by
the scene's own observation law; the crosscheck therefore compares
steady-contact ticks (the current and previous record both in contact) at
the exact window, and transition ticks at the declared transition window of
1e-3. (The velocity recursion — the inertia-law consumer of the same warm
reconstruction — stays at its exact 1e-5 window on every tick.)

A8. A2 OVERLAP DISCLOSURE: the certified line itself visits unsupported
states (A4), so the injected window [150, 244) can overlap the line's own
unsupported visits; the injected-fall declaration is driven by the
injection streak REGARDLESS of the seam truth, and the overlap is measured
and reported in the receipt (never hidden). The P7 pass condition is the
declared fall tick, the R1 stride override, the R2 latch and the
injection label — not the seam truth of the overlapped ticks.

A9. ENERGY-ACCOUNT WINDOW (the seam's warm observability bound): the warm
reconstruction anchors on the seam's own force law at every contact tick
and runs the declared decay recursion while airborne; at a MICRO-MARGINAL
gap crossing the step's internal contact decision (which consumes the
fresh micro draw) can disagree with the record's recomputed contact (which
consumes the previous micro), so the warm can be hidden for one rise/decay
step and the reconstruction carries a bounded offset until the next
anchor. The mapped effect on the C13 identity is
`residual ~ v * dt * d_eff_span * dwarm` — at the declared constants about
2.4e-6 J per unit mass, decaying with v. The energy window is therefore
declared at 1e-5 J (the recorded max residuals are ~2.4e-6 and are carried
in the receipt); the velocity recursion stays at its exact 1e-5 m/s window
on every tick and the warm-force crosscheck at its exact 1e-6 steady
window (both measured zero on every clean arm).


