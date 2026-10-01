# PREREGISTRATION — MAT2-W08 verify commanded start, stop, speed, and heading

Frozen BEFORE any command-verification receipt exists. This file is committed
ALONE (separate-first; the M03/P04 law). Every emitted receipt refuses any
document whose `preregistration_sha256` does not match these live bytes.

- Card MAT2-W08 (planning id W08, wave 8, slot 2), agent `wk-w08b-arrival-1`,
  attempt `c38b22e505874601aa3f3a3ba9035e4d`, attempt workspace
  `E:\ChimeraWork\monkey-coordination\kanban-attempts\MAT2-W08\c38b22e505874601aa3f3a3ba9035e4d`,
  file package `package` (NO_WORKTREES law: pinned file package, no clone, no
  worktree), publication branch `review/MAT2-W08`, PR base `astra/gait-capture`.
- Criteria sha256 `f38c2c96ef22cca080accba4b71b3370ca5b0272b824975c650cd543db9821ea`
  (startup join == registry `kanban.cards[MAT2-W08].criteria_sha256`, re-read
  READ-ONLY (`file:...?mode=ro`) from
  `E:/ChimeraWork/monkey-coordination/agent_slots.sqlite3` at run time;
  mismatch = refusal `criteria_pin_mismatch`).
- done_when (verbatim, registry): "Frozen command sequence satisfies tracking
  and physical-stability limits".
- Observation (verbatim, registry): "Existing 20 Hz speed/heading seam is
  retained".
- Card task falsifier (verbatim): "Sliding/penetration, unsupported
  propulsion, hidden reset, wrong command response or diagnostic/clean state
  divergence fails."
- Profile: `walking`/`motion`; numerical_evidence_required true;
  clean_view_required true; the capture is delivered per the sealed W07
  record-space precedent (section 8) with the absent inventory named.
- Base: `8b285ee4301a8ed42be54a1924af5db019f9fb20` = the file package's base
  (the MAT2-W07 merge, PR #301; the worker_start preparation pinned it from
  `origin/review/MAT2-W08`).
- Composed against CARD_STARTER v5 and the house standards:
  `IMPLEMENTER_CHECKLIST.md` (G1-G9) + `TOOLKIT.md` (P1-P9), cited at the
  candidate commit. Dispatch brief: card slot 2 of MAT2-W08
  ("Verify commanded start, stop, speed, and heading — Frozen command
  sequence satisfies tracking and physical-stability limits").
- Calculations: C11 (walking tracking and stability — this card's execution
  arm) and C12 (input timing and control mapping — the 50 ms seam law this
  card retains). C10 was sealed by W06 and is not recomputed.

## 0. The governing frame (what "commanded" means on this card)

THE CERTIFIED WALKING RUNTIME IS THE FROZEN CERTIFIED LINE — nothing else.
W07 loaded the accepted walking policy through the W04 certificate machinery
(validator VALID -> deploy gate ALLOW -> frozen loader -> bit-for-bit bundle
identity -> certified anchors EXACT). This card commands THAT certified
runtime with a FROZEN command sequence issued through the ACTUAL player
command port (the U01 pinned seam: `InputMapper` -> versioned `CommandRecord`
v1 at the existing 20 Hz speed/heading boundary), and measures commanded vs
achieved speed/heading plus the declared physical-stability limits. The 20 Hz
speed/heading seam is RETAINED, not re-modeled: the port emits at its own
frozen INTERVAL_MS=50 over 300 Hz physics (C12: a command cadence, not a
latency guarantee).

- BQ-1 (CPU-first): CPU-only. No GPU work exists in this lane; no engine
  process is started. The certified execution vehicle stays the DECLARED
  SURROGATE scene (`cpu-walk-scene/1.0.0`, build `cpu-walk-scene-build-N`)
  exactly as certified; the claim class stays offline/trace at the 300 Hz
  tick (COST-GAP, quoted from the certificate).
- TC-6 (the gate): the frozen line runs THROUGH the certificate machinery on
  this card too: re-validate the pinned W04 certificate with the machinery's
  own validator, run `check_deploy` (ALLOW required), then load through the
  frozen loader and verify bit-for-bit identity, THEN verify build identity.
  The commanded runs execute on that verified build.
- Physics charter: commands choose actuator setpoints, never inject position
  or hidden motion. The card-owned adapter projects each CommandRecord into
  the certified scene's 8-channel walk interface (stride/phase/lift/stiff
  setpoints) through the manifest's own limiter law
  `applied = clip(requested, lo, hi)`, saturation named per channel; the
  scene's public stepping API (`step(applied, saturation)`) is the only
  motion path; there is no pose-write channel (W7's structural law carries).
- The no-reissue law: this card deploys the EXISTING certificate; it does not
  re-issue, re-certify or amend anything, and it loads no trained bundle.
- OUTCOME-INDEPENDENCE: the certified closed-loop anchors were reproduced by
  W07 and are NOT re-claimed here; this card's runs are OPEN-LOOP commanded
  executions on the certified build (the machinery's registered open-loop
  case pattern: `runner.run_open_loop`, "a pinned command stream into ONE
  build"), with the policy's role as command source REPLACED by the frozen
  player-port script. The baseline gate -> loader identity checks are
  re-executed because commanding an UNVERIFIED build would command nothing
  certified; the closed-loop trajectory anchors are not re-registered here.

## 1. Input pins (verified byte-exact at attempt start; drift = refusal `input_pin_mismatch`)

Store pins (evidence-store `E:/ChimeraWork/monkey-coordination/evidence-store/`):
- `MAT2-W04/numerical/w04_certificate.json` `07f05bfa982e066ae67413b04e3367c5ad7570830e99fc32edcb86cbe8d87598`
- `MAT2-W04/numerical/w04_freeze_manifest.json` `be632ffc85865515285f3d622a09882a3180a43101027914f1ed3408496f5d29`
- `MAT2-P06/numerical/numerical` `a590ba2a5135607867015f052ba1ec9d2ef85080838f6eb710a45a084ba789b8`
- `MAT2-U01/numerical/qualification_receipt.json` `94887cc14ba6d2fc7a76c04949d5015cbfada899a817c3acb497e5d53a7a0c61`
- `MAT2-W07/numerical/native_load_receipt.json` `4f5aac081a3a07fd56733d84ac3069950b00309e54f6402e78ebd22c55e490e9`

Base-blob pins (read from the shared repository's Git object database at the
package base `8b285ee4301a8ed42be54a1924af5db019f9fb20` through the DECLARED
read-only `git cat-file` access in `source_access.py`; NO_WORKTREES law; the
blob identities equal the U01 receipt's own `pinned_lineage` hashes — no
drift between the store lineage and the base tree):
- `tools/monkey_campaign/contributions/MAT2-U01/reconcile/pinned_seam/tools/monkey_campaign/product/input_mapper.py`
  `7a36a45ead6637d9ba5659ea43b54a6b424803c8e57d02720ac970b42cfe6b44`
- `tools/monkey_campaign/contributions/MAT2-U01/reconcile/pinned_seam/tools/monkey_campaign/product/input_mapper_tests.py`
  `95f44e90998f9728802ff5f7cb8628f18f2026bef1fb2c4de681e5253381216e`
- `tools/monkey_campaign/contributions/MAT2-U01/reconcile/pinned_seam/tools/science_funnel/typeb_export/command_record.py`
  `6771175933ad20ac6d20c360df96f6a9729a56deb31c58a13be5e76e1cc4355e`
- `tools/monkey_campaign/contributions/MAT2-W07/receipts/native_load_receipt.json`
  `4f5aac081a3a07fd56733d84ac3069950b00309e54f6402e78ebd22c55e490e9`
- `tools/monkey_campaign/visual_capture.py`
  (sha256 stated in `verify_inputs.py` PINS and re-verified at run time)

Sealed lane machinery (`E:/ChimeraWork/pass3-integ/repo`; consumed read-only,
pinned bytes, identical to W07's pin table — no drift): `tools/policy_compat/`
`__init__.py` `11d523c8...`, `__main__.py` `74d592d0...`, `certificate.py`
`2b6a75ba...`, `engine_cert.py` `c1aa0536...`, `injections.py` `1b5b978b...`,
`runner.py` `1fa8d8b7...`, `scene_cpu.py` `ab425702...`, `snapshot_api.py`
`c47a0959...`; `tools/science_funnel/typeb_export/` `infer_numpy.py`
`8030b609...`, `observation_schema.py` `8876e1a6...`, `policy_manifest.py`
`a65cf875...`; validation `typeb_p3_20260921/policy_manifest.json`
`aa5334f7...`, `dummy_actor.npz` `5fb2b785...`,
`trace_slice_wave38.json` `69babe84...`;
`upgrade_gate_20260920/receipt.json` `2c7794e6...`.
(Full 64-hex values live in `verify_inputs.py` PINS and are re-verified every
run; this section is the frozen pin DECLARATION.)

Registry: criteria hash and card identity read READ-ONLY at run time;
profile `walking`/`motion` read from the card's own
`ontology_qualification.task.verification_profile`.

## 2. The frozen protocol (order is law)

1. Verify every section-1 pin; re-read the registry READ-ONLY and require the
   criteria hash and the profile identity. Any drift is a named refusal
   BEFORE anything runs.
2. Pin-extract the machinery tree AND the base-blob seam tree under a
   slot-scratch directory and import ONLY pinned bytes (zero upstream files
   modified).
3. Re-validate the pinned W04 certificate (machinery validator; the only
   authority): zero violations, else refusal `certificate_validator_violation`.
4. Build the deployment request from the certificate's OWN relation
   (policy_bundle, physics_build, runtime_profile, body_domain, test_suite);
   `check_deploy` must return ALLOW BEFORE any load, else refusal
   `deploy_gate_sanity`.
5. Load the bundle through the FROZEN loader and require bit-for-bit identity
   (manifest_hash, weights, file shas, architecture, activation, clip), else
   refusal `load_identity_mismatch`. Verify build N identity (params sha,
   scene module sha, timestep 1/300 s).
6. Run the pinned U01 port module's own import identity, then execute the
   FROZEN INPUT SCRIPT (section 4) through the pinned `InputMapper` over an
   injected integer-millisecond clock into a recording sink; assert the seam
   laws (C12) on the emitted records.
7. Project each record through the FROZEN ADAPTER LAW (section 4.2) and
   execute the certified scene OPEN-LOOP (`scene.step(applied, saturation)`
   per physics tick, ZOH at the tick boundary), collecting per-tick records.
   Runs: R1 the clean commanded run (horizon 10500 ticks), R2 an identical
   re-execution of R1 (the determinism zero-control), R3 the wrong-command
   variant (section 4.4). Every run is a full re-execution from tick 0 — no
   snapshot injection, no state reuse.
8. Evaluate the frozen predictions (section 3) and the falsifier detectors
   (section 5); emit `receipts/command_verification_receipt.json` with the
   named-variable command table. Any failed prediction is a named refusal
   (`prediction_failed:<name>`), never a silent pass.

## 3. Frozen predictions (registered BEFORE the runs; disclosed either way)

All bounds are DERIVED at run time from the pinned scene constants
(STRIDE_GAIN g=0.55, DAMPING d=0.35, WARM_DAMP_LO=0.95, WARM_DAMP_SPAN=0.10
-> the pinned step law's effective-damping span
d_lo = 0.35*0.95 = 0.3325, d_hi = 0.35*(0.95+0.10) = 0.3675; the certified
velocity envelope uses the LOW edge and is unaffected) and the pinned
manifest action bounds; the values below are the pinned-constant
evaluations, recomputed live in the receipt. Dev-run disclosure (before any
sealed run): the first harness draft used the nominal damping as the span's
top; the P4 segment-range detector REFUSED on the real trajectory
(prediction_failed:P4_segment_range) and the pinned constants were re-read —
this document is amended BEFORE any sealed run, with the refusal preserved
in the attempt record.

- P1_gate_load_allow: the certificate path of section 2 steps 3-5 is ALLOW
  with bit-for-bit bundle identity (manifest_hash `9ca7e976dfb0dedd...`,
  weights `5fb2b785...`), build N, params sha `3e770bef...`.
- P2_port_seam_laws (C12, the seam retained): the frozen script's records
  carry record_version 1, v_forward in [0, 0.763625] (the port's own
  in-band ceiling), |yaw_rate| <= 1.6 (the port's input-side bound);
  consecutive issued ticks inside a continuous command segment differ by
  EXACTLY 15 physics ticks (INTERVAL_MS=50 at 300 Hz); a held key re-issues
  every interval; the release-decay lands its exact-zero demand by
  released_ms + 100 (the port's own deadline); idle emits NOTHING; the sink
  log contains ONLY `("emit", CommandRecord)` entries (the no-teleport law:
  the port cannot touch state).
- P3_projection_within_bounds: every projected applied vector lies within
  the manifest bounds on all 8 channels; every clipped channel carries the
  named saturation indicator (the limiter's own law
  `sat = |applied - requested| > 0`); the zero-advance demand projects to
  the stride floor 0.2 with stride channels 1,5 saturated at EVERY tick of
  the zero/floor segments (declared: the plant cannot stride below its
  bounded floor; never silent); the seam-max yaw demand (+-1.6 rad/s)
  projects to phase offsets +-0.25 with phase channels 0,4 saturated and the
  achieved plant yaw rate +-1.0 (the plant's declared representable range).
- P4_start_tracking: after the start command (issued tick 300) the applied
  setpoint changes within 15 ticks (predicted onset 1 tick); the speed rises
  monotonically while below the derived ceiling band low edge; and at the
  segment end (tick 5415; 5115 applied steps) the two-sided comparison bound
  (d_eff in [d_lo, d_hi]) with the nominal-damping inversion
  (s = v_cmd*d/g, a = v_cmd*d) gives
  v(5415) in [a/d_hi - (a/d_hi - v0_ub)e^{-d_hi*5115/300}, a/d_lo]
  = [0.726509, 0.8038157894736843] m/s with v0_ub = 0.330827067669173 (the
  priming floor band top), so |v(5415) - 0.763625| <= 0.040190790 m/s (the
  largest distance from the demand to the derived band edges
  max(v_cmd - a/d_hi, a/d_lo - v_cmd), plus a 1e-9 float guard; recomputed
  live). The measured band-entry tick is RECORDED informationally: the
  crossing time depends on the warm-cache path and is NOT bounded by the
  declared constants alone (found by the dev refusals before any sealed run;
  recorded honestly, never claimed as a bound).
- P5_turn_exactness: during the in-range turn commands (+-0.8 rad/s) the
  scene's yaw_rate observation equals the commanded yaw to within 1e-6 rad/s
  (the power-of-two routing yaw/4 + yaw/4 leaves only float32 routing dust,
  ~1.2e-8 measured-scale — orders below any physical residual; the measured
  per-tick residual is recorded); the speed setpoint is unchanged by yaw
  commands and the P4 claim continues to hold across the turn sub-segments.
  During the seam-max turn (+1.6 rad/s) the achieved yaw is +1.0 rad/s within
  the same 1e-6 bound, with saturation named on channels 0,4 at every tick
  (declared saturation residual 0.6 rad/s = |1.6 - 1.0|; the limiter's named
  clip, disclosed not hidden).
- P6_speed_step_decay: the release-decay's mid demand (0.57271875 m/s, one
  15-tick block) yields a strictly decreasing speed across the block
  (derived: the speed starts above the new band top 0.6028618421), and
  the exact-zero demand lands by released_ms + 100 (the port deadline) with
  the plant at/below the pre-release speed.
- P7_stop_floor_settle: after the zero-advance command lands (tick 5431) the
  speed strictly decreases while above the floor band top 0.330827067669173
  and can never cross below the floor band low edge 0.3142857142857143 (the
  drive-law invariant a/d_hi). The comparison lemma (d_eff >= d_lo) gives
  v(t) <= floor_hi + (v0 - floor_hi)e^{-d_lo*(t-5431)/300} for every t after
  the onset (v0 <= the ceiling band top 0.8038157894736843), so at the settle
  window end (tick 9031; 3600 steps) v(9031) in [0.2993197278911565,
  floor_hi + (0.8038157894736843 - floor_hi)e^{-3.99}] = [0.2993197278911565,
  ~0.339577] (recomputed live), and the upper bound only tightens through
  the horizon. The measured band-entry tick is RECORDED informationally (the
  crossing time is warm-path dependent — same dev-refusal disclosure as P4).
  The floor is the plant's own bounded minimum advance — the surrogate's
  zero-advance state, declared in P3; it is NOT claimed as a zero-speed stop
  bar (the port's own semantics note is carried verbatim in the receipt).
- P8_stability_bars: at EVERY tick of R1: |v| <= 2.977443609022557 m/s (the
  derived envelope); contact_count >= 2 (the certificate's contact-floor
  bar; observed structural floor 4 is recorded); no NaN/Inf in any recorded
  state quantity; intervention_reason == "none"; x never decreases (v >= 0
  is a derived invariant of the nonnegative drive domain — no reverse
  sliding); every pad gap > 0 (no penetration below the pad plane);
  com_x advances exactly by dt*v per tick (the records come from the solved
  state; recomputation exact).
- P9_wrong_command_response_MUST_FIRE: R3 runs the WRONG-KEY script from
  the stop boundary (section 4.4): the R1/R3 state hashes are IDENTICAL
  through tick 5430 (identical prefix), DIVERGE from tick 5431 (first
  differing state hash at 5431), and at tick 5999 the physical responses
  separate beyond the derived two-sided brackets: v_R3(5999) >= a/d_hi +
  (v_prefix - a/d_hi)e^{-d_hi*568/300} (rising under the wrong held ceiling;
  a = v_cmd*d) and v_R1(5999) <= floor_hi + (v_prefix - floor_hi)
  e^{-d_lo*568/300} (decaying under the clean stop), where v_prefix = the
  shared prefix speed at tick 5430 (measured; both brackets recomputed live
  from the pinned constants). R1 vs R2 (the zero-control) are bit-identical
  over the whole horizon. A runtime whose state ignored the wrong key would
  leave the hashes equal: the detector firing is the card's falsifier class
  executed, not a formality.

## 4. The frozen command sequence, adapter law, and probe

### 4.1 The frozen input script (injected integer milliseconds; the port's own semantics)

| t_ms | event |
|---|---|
| 1000 | press "W" (start: v_forward 0.763625; held through 18025) |
| 12000..16450 | steering windows, counts fed before each boundary poll under the port's own rate law (raw = counts*sens/interval_s): mouse +20 counts at each boundary in [12000,13450] (= +0.8 rad/s in-range); mouse -20 at each boundary in [13500,14950] (= -0.8 in-range); press "A" at 15000, release "A" at 16500 (yaw +1.6 saturating for records in [15000,16450]) |
| 18025 | release "W" (decay tail: mid sample 0.57271875 at the 18050 boundary, exact zero at 18100, then the port is INERT) |
| 20000 | press "S" (live-zero records every interval through 22950) |
| 22975 | release "S" (last emitted 0.0; no tail — the port decays only what it commanded; INERT after 22950) |

Scene horizon H = 10500 ticks (35 s at 300 Hz). Before the first record the
scene is primed with the declared IDLE projection (the zero-advance floor
vector, stride at bounds_lo 0.2, phase/lift/stiff at manifest center) — the
surrogate has no inert state; the priming segment (ticks 0..300) is excluded
from tracking claims and disclosed; every stability bar (P8) holds from
tick 0.

### 4.2 The frozen adapter law (the card-owned command consumer)

For an active CommandRecord (v_forward, yaw_rate):
- requested stride setpoint s = v_forward * damping / g (the nominal-
  damping inversion of the scene's own drive law; the declared band
  straddles the demand: [a/d_hi, a/d_lo] = [0.727262, 0.803816] m/s at the
  ceiling); channels 1,5 = s; channel 0 =
  clip(-yaw_rate/4, -0.25, 0.25); channel 4 = clip(+yaw_rate/4, -0.25, 0.25)
  (the plant's yaw_rate observation is 2*(phase_off_r - phase_off_l));
  channels 2,3,6,7 stay at manifest center (1.0, 1.25).
- applied = clip(requested, bounds_lo, bounds_hi) (the manifest's own limiter
  law); saturation named per channel (`|applied - requested| > 0`).
- ZOH: the record issued at tick b applies to steps b+1..b+15 ("the ZOH
  applies it at the next step() and holds >= HOLD_TICKS", the port's own
  law); between records the applied vector is constant (asserted per tick).
- Port-inert semantics: the pinned mapper declares a CONSUMER-SIDE expiry
  contract by name for this card (`is_expired`: a record older than
  EXPIRY_TICKS = 30 reverts the consumer to the seam's inert path until a
  fresh record arrives). The adapter implements it: after 30 ticks without
  a fresh record the applied vector reverts to the declared IDLE floor
  projection — byte-identical to the zero-demand projection in this script
  (asserted), so the revert is contract-exact and motion-neutral here.
  Dev-run disclosure (before any sealed run): the first draft continued
  the last applied vector instead; the pinned mapper's own contract text
  was re-read and this section amended BEFORE any sealed run.
- The projection is float64, cast float32 at the scene boundary (the
  machinery's applied dtype); records feed `scene.step(applied, saturation)`
  ONLY. No other scene mutation exists in this card (structural scan FB9).

### 4.3 The command-verification table (every row a named variable in the receipt)

| command | issued (tick) | tracking claim | stability claim |
|---|---|---|---|
| start / ceiling hold | 300 (re-issued each 15 to 5400) | P4 residual + band entry + onset | P8 bars every tick |
| turn left in-range (+0.8) | 3600..4035 | P5 exact yaw residual | P8; speed claim continues |
| turn right in-range (-0.8) | 4050..4485 | P5 exact yaw residual | P8 |
| turn left seam-max (+1.6, saturating) | 4500..4935 | P5 declared saturation residual 0.6, sat named | P8 |
| speed step (decay mid sample) | 5415 (one block) | P6 monotone decrease | P8 |
| stop / zero-advance floor | 5430, then live-zero 6000..6885 | P7 settle claim at the window end + invariants | P8; stride sat named |
| wrong-command probe | injected at 5430 in R3 | P9 MUST-FIRE divergence + physical separation | R1/R2 bit-identity control |

### 4.4 The wrong-command probe (P9) and the zero-control

R3 executes the declared WRONG-KEY script: identical to R1 through tick 5429
(no input events differ before the injection); at tick 5430 — the stop
boundary where R1's port goes silent before the S segment — the wrong
operator PRESSES "W" AND KEEPS IT HELD (the port re-issues the ceiling
command every interval through the probe window; the clean script's S
segment never happens in R3). Dev-run disclosure (before any sealed run):
the first draft injected a single wrong RECORD, but the pinned expiry
contract (section 4.2) correctly reverts a stale record after 30 ticks, so a
one-record injection is not a held wrong key — the probe was re-declared as
the wrong-key SCRIPT, which is the operator-level falsifier the card names.
Instruments: (i) the R1/R2 bit-identity zero-control proves the harness
resolves state hashes deterministically; (ii) the R1/R3 prefix equality
through tick 5430 localizes the divergence to the wrong-key choice; (iii)
the physical separation at tick 5999 proves the runtime's RESPONSE (not
just its hash chain) distinguishes commands. The detector MUST fire on R3
and MUST stay silent on R1 vs R2.

## 5. Falsifier mapping (card falsifier -> executed detector)

| falsifier class | executed detector on this card |
|---|---|
| sliding/penetration | pad gaps > 0 and x non-decreasing at every tick (P8); FB bite arms feed synthetic negative-gap and negative-x-step rows and the detector fires |
| unsupported propulsion | velocity envelope |v| <= 2.977443609022557 at every tick (P8) + contact floor bar; FB bite arm feeds an over-envelope synthetic row |
| hidden reset | continuous per-tick state-hash chain over each run + the R1/R2 bit-identity control (any reset/restart moves the chain); FB bite arm tampers one chain event |
| wrong command response | P9's MUST-FIRE divergence + physical separation, with the R1/R2 zero-control |
| diagnostic/clean state divergence | the capture renders diagnostic and clean bands from the SAME recorded per-tick state (one state hash per frame row-pair, section 8); FB bite arm tampers a band hash |

The falsifiers must be able to FAIL: every detector carries a bite arm that
proves it fires on tampered input and stays green on the clean run (section
7). Surrogate-scope classes that cannot occur inside the declared surrogate
(see section 6) are ARMED and reported, never claimed as exercised.

## 6. The named-missing recording protocol (never fabricate a claim)

- N1 vertical/fall channel: the certified surrogate has NO vertical body
  coordinate, no roll/pitch and no airborne ballistic state (its contact
  floor is structural: contact_count = 4 + contact_l + contact_r >= 4). The
  profile scenario's "fall" segment is therefore exercised ONLY as the
  scene's DECLARED destabilization instrument (the reflex-trip state
  channels trip_l/trip_r, measured and reported if they fire; their presence
  or absence is recorded, never gated), and the true fall/roll physics is
  recorded NAMED_MISSING (surrogate scope; the adopted assembly's runtime-use
  gate carried from W07's N1-N4). The P06 stability-settle-sink-m limit
  (0.01 m vertical) has NO surrogate channel: recorded NAMED_MISSING, not
  silently dropped.
- N2 C09 ledger limits: the P06 walking-worst-ledger-j (30.970714 J) and the
  C09 episode caps belong to the native coupled line's own acceptance; the
  surrogate commanded runs carry no energy ledger. Recorded NAMED_MISSING;
  the P06 limits this card CONSUMES are the ones with a declared surrogate
  channel: simulation-tick-hz 300 (the scene's dt, verified equal), the
  20 Hz command clock (the port's INTERVAL_MS/HOLD_TICKS), and the derived
  velocity envelope. The settle acceptance uses the port's own deadline law
  plus the P7 derived floor-band settle; the P06 stability-settle-vy-ms
  (0.05 m/s) is recorded as NOT applicable to the bounded floor band (the
  plant's minimum advance exceeds it by declaration — the number is quoted
  in the receipt, never silently ignored).
- N3 product-engine live control path: carried NAMED_MISSING from the pinned
  spike evidence (W07's N3); this card starts no engine process.
- N4 trained bundles: BLOCK at the gate; nothing trained is loaded (W07's
  executed discrimination is pinned and carried; this card re-runs only the
  ALLOW direction it needs, plus the certificate validator).

## 7. Named checks and gates

- Suite `test_w08_commands.py` (unittest discover -p test_*.py), G12
  accounting executed/skipped claimed in the report. Clean control + bite
  arm per detector: FB1 pin-verifier bite (tampered pin ->
  `input_pin_mismatch`); FB2 gate bites (foreign bundle tuple BLOCK, missing
  certificate BLOCK); FB3 bounds bite (out-of-bounds projected vector ->
  detector fires); FB4 envelope/penetration bites (synthetic over-envelope
  v, negative gap, negative x-step -> detectors fire); FB5 wrong-command
  MUST-FIRE bite (R3 diverges, R1/R2 identical — the zero-control); FB6
  chain-tamper bite (a tampered event hash -> detector fires); FB7 yaw-route
  bite (mirrored yaw sign -> the exactness detector fires on the tampered
  row, clean rows exact); FB8 tracking-band bite (a tampered measured speed
  outside the derived band -> detector fires); FB9 structural scan (the
  contribution launches no engine/simulation/training process; the only
  subprocess modules are `source_access.py` (the DECLARED read-only git
  cat-file base-blob access, NO_WORKTREES law) and `run_capture.py` (the
  DECLARED ffmpeg capture-tool calls)); FB10 pinned-port behavior spot
  checks against the extracted U01 seam bytes (decay deadline, live-zero
  vs inert distinction, named refusals), with the port's own sealed 26/26
  receipt consumed read-only (pin `94887cc1...`), never re-claimed.
- The 12 campaign gates run over the card dir via the card-kit
  `batch_gates.py`; results written to scratch (never the card dir).
- Report GENERATED from the receipts by `make_report.py`; every numeric
  literal proven traceable by `lint_report_numbers.py`.

## 8. Capture protocol (profile walking/motion; the W07 sealed precedent)

The one declared capture arm: 60 frames of the CLEAN commanded run R1, each
frame a sheet of the three profile views (full-body ground overview | side
view of stance/swing | close-up of foot-ground contact) with the five
declared diagnostic layers in the diagnostic band and the clean band below,
rendered from the SAME recorded per-tick state; frame ticks = the declared
event anchors (300, 301, 3601, 5415, 5416, 5431) plus a uniform declared
sample across the horizon, exactly 60 ticks, each frame's real tick
recorded; encoded FFV1 (`-c:v ffv1 -level 3 -g 1 -fflags +bitexact`); G4
pixel-exactness decode check; camera record fields complete per row;
validated with `visual_capture.validate_manifest`
(CAMERA_METADATA_STRUCTURE_ONLY; visual_acceptance stays False — independent
visual review remains the Sergeant's). The subject receipt binds THIS card's
command-verification receipt, and the honesty label names the record-space
delivery: the frames are record-space panels of the commanded runtime's own
per-tick telemetry — NOT engine frames (N3). Diagnostic/clean bands render
from one recorded state per frame, so a view toggle cannot move the state
identity (the falsifier's instrument).

## 9. Deviations (recorded, none silent)

- Under the NO_WORKTREES amendment this card is a pinned file package
  (attempt c38b22e505874601aa3f3a3ba9035e4d, base 8b285ee), not an isolated
  clone; upstream in-tree bytes are consumed through DECLARED read-only
  `git cat-file` base-blob reads (`source_access.py`) instead of checkout
  paths. The declared-subprocess structural law (FB9) names this exception.
- The commanded runs are OPEN-LOOP executions of the certified scene (the
  machinery's registered open-loop pattern) with the player port as command
  source through the card-owned adapter law; the W07 closed-loop policy line
  is not re-run (its anchors are pinned upstream evidence). The adapter law
  and the idle projection are NEW DECLARED code on this card, frozen in
  sections 4.1-4.2 BEFORE any run.
- The prior paused attempt 665129de2af14e47ad7ff56c72ff0d5a (agent
  wk-g06b-arrival-1, misroute era) was reconciled READ-ONLY: its workspace
  directory is EMPTY (no files, no receipts); nothing was recovered and
  nothing was overwritten.
