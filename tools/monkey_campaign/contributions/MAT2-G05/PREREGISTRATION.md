# PREREGISTRATION - MAT2-G05 (Implement contact/support observations)

Frozen BEFORE implementation and before any experiment run. Composed against
CARD_STARTER.md v3; house standards IMPLEMENTER_CHECKLIST.md (G1-G9) and
TOOLKIT.md (P1-P9) will be cited at the candidate commit. Base:
`4421349823dd071742a065414bffc0c5e2372e36` (= origin/astra/gait-capture, the
MAT2-G04 merge PR #298). Attempt `e20294c681f64128bad610a7e98ba1d8`,
agent `wk-g05-observe`, branch `codex/monkey-mat2-g05-e20294c6`.

done_when (verbatim): "Controller receives only declared measurable
contact/pose signals with explicit timing"

Card observation (verbatim): "No hidden simulator information represented as
sensed information"

Profile falsifier (verbatim): "Unresolved owner, nonphysical attachment,
unsupported transfer, concealment behind the trunk or force/pose
inconsistency fails."

Verification profile: `grasp` kind `motion` (read from the sealed dispatch;
re-read READ-ONLY from the registry at capture time). Calculation C21:
"Define observable state and action limits; test aliasing and hidden-state
dependence before training." The observation feeds U06 and G06 downstream.

## 1. The established interfaces (material-first; imported, hash-asserted,
never forked)

- THE SOLVER: MAT2-M06 `chimera.local_contact.v1` (`../MAT2-M06/
  local_contact.py`, raw sha256 `1cd662b30343011eb4a0a01e461a1e82b00482d
  0371857c8e42d6bec8f9a28dc`) -- the same pinned module G04 imported. Not one
  byte is modified; every impulse in this card comes from `lc.solve_tick`.
- THE GRIP PHYSICS + FIXTURE: MAT2-G04's sealed `grip_contact.py`
  (`../MAT2-G04/grip_contact.py`, raw sha256 `0d6375484c350039468b31a2f7db
  2895d3365412aee52ce98de72b4173d69245`, the exact revision merged in PR
  #298). G05 consumes the sealed G04 fixture through its own module:
  `load_interface`, `load_trunk_geometry`, `channel_facets`, `place_tetra`,
  `orthobasis`, `run_scenario`, the closed forms, the press channel
  (P = 0.30 N*s per tick per channel), the named-absent list `NAMED_ABSENT`
  (the ten x_* variables with verbatim provenance), and the frozen window
  set. G05 adds NO physics and NO fixture constant of its own.
- THE FROZEN OBSERVATION CONTRACT (W04, TC-2): `observation_interface_v2.json`
  (policy_observation_interface, freeze `policy-interface/2.0.0`, dim 80,
  OBS_SCHEMA_VERSION 2), host path
  `E:/ChimeraWork/pass3-integ/repo/tools/science_funnel/validation/
  policy_interface_freeze_20260920/observation_interface_v2.json`,
  raw sha256 `e8c2d698dee0337414c48e8d2f6569c45f6f61828dabdeff6a4f1188b1
  c0671c` (the sha pinned in the sealed W04 freeze manifest). G05 does NOT
  extend or re-declare the 80-field walking interface (its owner is W04);
  G05 declares a TASK-OWNED grasp-side observation table that composes with
  the frozen contract's DECLARED LAWS (fixed dim, fixed order, float32
  dtype, declared source per field, availability recipe, privileged_
  forbidden, zero un-declared history) and pins the contract bytes at run
  time.
- THE W04 FREEZE MANIFEST (`E:/ChimeraWork/monkey-coordination/
  evidence-store/MAT2-W04/numerical/w04_freeze_manifest.json`, raw sha256
  `be632ffc85865515285f3d622a09882a3180a43101027914f1ed3408496f5d29`) is the
  provenance record for the contract pin above.

## 2. The declared observation interface (the task-owned deliverable)

`contact_support_obs.py` declares OBS_FIELDS -- a fixed-order, fixed-dim
(OBS_DIM = 32), float32 observation vector plus a mandatory timing block,
delivered to the controller ONLY through `ObservationSeam.deliver`.

Timing law (EXPLICIT; every sample carries all four):

- `t_tick`: the integer solver tick the sample is taken AFTER (post
  `lc.solve_tick`, before the next tick's press); 1-based, no tick 0 sample.
- `t_phase`: `'hold'` or `'release'` -- the press-channel state DURING that
  tick (hold = ticks 1..20, release = 21..30; G04's frozen phase split).
- `t_dt_s`: 0.005 (the pinned M06 DT).
- `t_seconds`: t_tick * t_dt_s (window 1e-12 s; asserted at delivery).
- Cadence: EXACTLY one sample per solver tick, delivered in tick order; no
  interpolation, no extrapolation, no resampling, no hidden lookahead
  (history law: 0 undeclared history -- the only cross-tick quantities are
  the DECLARED cumulative displacement and pose fields, both running sums of
  recorded per-tick values).

Vector law (32 slots, fixed order, float32):

- channels 0..2 (the fixture's declared channel order; channels k >=
  n_channels are UNAVAILABLE this tick and carry the declared fill 0.0):
  - `ch{k}_contact_flag` 1.0 iff the pad recorded at least one contact
    record this tick (source: row pads[k] mode != 'no_contact')
  - `ch{k}_stick_flag` / `ch{k}_slip_flag` 1.0 iff the recorded mode is
    stick / slip (disjoint projections of the recorded mode; declared
    aliasing: both derive from row pads[k].mode)
  - `ch{k}_jn_Ns` / `ch{k}_jt_Ns` the recorded per-tick impulse sums (source:
    row pads[k].jn_sum_Ns / jt_sum_Ns)
  - `ch{k}_contact_force_N` the DECLARED conversion jn/dt (declared aliasing:
    alias_of ch{k}_jn_Ns via the declared conversion)
  - `ch{k}_disp_down_cum_m` cumulative downward displacement (source: row
    pads[k].disp_down_m_cum)
  - `ch{k}_centroid_z_m` the DECLARED pose signal: the pad centroid z
    measured from the pinned solver's body state through the observer loop
    (cross-checked against the row-derived z0_k - disp_down_m_cum; window
    1e-9 m)
- aggregates (always available):
  - `agg_support_count` count of AVAILABLE channels in recorded stick mode
  - `agg_supported_flag` 1.0 iff every available channel is stick AND
    t_phase == 'hold' (the declared support law; a slip channel is honestly
    recorded as NOT supported -- the sealed G01 slip rows stay slips)
  - `agg_release_flag` 1.0 iff t_phase == 'release' (support removed)
  - `agg_trunk_anchor_z_Ns` the recorded trunk anchor reaction z-component
    (source: row ledger.trunk_anchor[2]; the VISIBLE, recorded anchor)
  - `agg_ledger_residual_max_Ns` the full-tick identity residual this tick
    (source: row ledger.residual_full_max; the integrity signal)
  - `agg_reciprocity_max_Ns` max |reciprocity residual| this tick (source:
    row ledger.reciprocity_residual; the recorded action-reaction integrity
    signal)
  - `obs_mask_mean` mean availability over the 32 vector slots this tick
  - `obs_frac_avail` fraction of slots with an available source (W04
    sensor-health law, mask_mean/mask_frac_avail composition)

Dtype law: every vector value is delivered through float32 rounding
(struct pack/unpack); the check window is |f32(v) - v| <= 1e-6 *
max(1.0, |v|); flags stay exact 0.0/1.0.

Aliasing law (C21): every field row declares its `source` trace key and, when
the same recorded quantity feeds two fields, an explicit `alias_of`/declared
derivation. The aliasing audit refuses two fields sharing a source key with
no declared alias row.

Privileged-forbidden law (W04 composition): NO solver-internal quantity has a
slot. Named privileged-non-grata (never deliverable, never declared): the
contact records' pre-solve penetration proxy, any Baumgarte/bias term, the
pad velocity before the press impulse, any quantity not reconstructible from
the G04 row/header record or the pinned body state at the tick.

Named absent variables: the ten x_* variables are inherited VERBATIM from the
pinned G04 module (`gc.NAMED_ABSENT`) and remain ABSENT; no synthetic
constant occupies an absent slot; the seam REFUSES any sample whose keys
include a name in the absent registry (refusal `named_absent_occupied`).

## 3. The seam (the only channel the controller receives)

`ObservationSeam.deliver(sample)` performs the declared delivery gates and
REFUSES with named codes (nothing silently repaired):

- `undeclared_field` -- any delivered key outside the declared set (timing
  block + 32 vector slots).
- `timing_unbound` -- missing timing keys, non-integer t_tick, t_tick < 1,
  t_phase outside {hold, release}.
- `timing_drift` -- t_dt_s != M06 DT or |t_seconds - t_tick*t_dt_s| > 1e-12
  or non-monotone t_tick across deliveries.
- `named_absent_occupied` -- any x_* name present.
- `privileged_source` -- any key in the privileged-non-grata registry.
- `nonfinite_value` -- any non-finite vector value.
- `dim_mismatch` -- the vector payload is not exactly OBS_DIM values.

The seam records a delivery census (accepted samples, refusal codes) into
the receipt. Every falsifier arm's tamper is a scratch seam/tamper VARIANT
(never the production seam); the production seam's census on the clean run
is zero refusals.

## 4. The observer (G05-owned loop; the pinned G04 runner cross-checked)

`observe_scenario` re-runs the frozen fixture through a G05-owned tick loop
that performs EXACTLY G04's per-tick operations in the same order (press
impulse from the imported constants; `lc.solve_tick`; the same row fields)
and additionally measures the pad centroid poses from the pinned body state
each tick. The observation sample is projected from those rows + the measured
pose and delivered through the seam.

Cross-validation prediction: for every scenario, the G05 observer rows are
BIT-IDENTICAL to `gc.run_scenario`'s rows (per tick, per pad: jn_sum_Ns,
jt_sum_Ns, mode, disp_tick_m) -- same operations, same order, same pinned
solver. A mismatch refuses with `observer_drift`. The pose measurement is
therefore validated as the same physics G04 sealed.

## 5. Frozen battery and preregistered predictions

The G04 battery replayed through the observer: the 12 grip cases (readings
{band_lo 5.4, band_mid 6.15, band_hi 6.9, scene 10.037998} kg x channels
{1,2,3}) plus the zero-mu control (band_mid, n=3, mu=0, label suffix
`|mu=0`); 30 ticks each (hold 1..20, release 21..30); 13 scenarios, 390
samples, every one delivered through the seam. CPU-only, no RNG, no wall
clock.

- P1 declared-only: the union of delivered keys over the battery equals the
  declared set exactly (4 timing keys + 32 vector slots); the clean census
  records 0 refusals in 390 deliveries; 390 accepted samples = 13 x 30.
- P2 explicit timing: every sample has t_tick in 1..30, t_phase matching the
  press state, t_seconds == t_tick * 0.005 (window 1e-12), delivery strictly
  monotone in t_tick within each scenario.
- P3 measurable traceability: every ch_{k} value equals its recorded row
  value inside the f32 window; agg_trunk_anchor_z_Ns equals the ledger value;
  centroid_z equals both the measured centroid and z0_k - disp_cum (window
  1e-9 m); contact_force_N == jn/dt (declared conversion, f32 window).
- P4 support law: the SEVEN stick cases (band_lo/band_mid/band_hi x n=2,3
  and scene n=3 -- per the sealed G01 boundary table) carry
  agg_supported_flag = 1.0 on every hold tick and 0.0 on every release tick;
  the slip rows (band_* n=1, scene n=1 and n=2, zero-mu control) carry 0.0
  everywhere (honest non-closing cases stay non-supported); agg_release_flag
  = 1.0 exactly on ticks 21..30 of every case; the attach transition lands at
  tick 1 and the release transition at tick 21 in every case.
- P5 W04 contract composition: the pinned contract loads with the exact sha;
  its law fields assert (kind policy_observation_interface, obs_schema_
  version 2, dim 80, legacy_dim 64, dtype float32, privileged_forbidden
  True, history_ticks 0, availability_recipe present); the OBS table
  conforms to the same law family (declared above); no OBS field name
  collides with a privileged-non-grata entry.
- P6 determinism: two independent runs byte-identical (trace + receipt;
  declared augmentation key set empty).
- P7 regression: the M06 suite AND the sealed G04 named-check suite re-run
  UNMODIFIED on this revision, both exit 0.

Honest carry-overs (never repaired here): single-channel support and scene
n=2 do NOT close (solver slips -- carried as not-supported observations);
mu_s/mu_k stay the NAMED placeholders; x_press and the nine other x_*
variables stay ABSENT with their verbatim provenance; the press channel
stays a declared fixture input, never an actuator qualification; no
creature-side anatomy, tendons, reach, aperture or transfer exists in this
fixture (inventoried ABSENT, never faked -- owners stay unresolved in
records).

## 6. Named checks (test_g05_checks.py; executed, none skipped)

- X1 declared_only_delivery (P1): union of delivered keys == declared set;
  clean census 0 refusals / 390 accepted.
- X2 explicit_timing (P2): timing law on every sample, monotone delivery.
- X3 measurable_traceability (P3): every value traces to its declared source
  inside the declared windows; the observer rows are bit-identical to the
  pinned G04 runner rows (`observer_drift` refusal armed).
- X4 support_state_law (P4): the support/release flags and the transition
  census (attach tick 1, release tick 21; slip rows honestly unsupported).
- X5 w04_contract_composition (P5): contract pin + law asserts + OBS table
  conformance + aliasing audit (declared alias rows for jn/force and
  stick/slip projections; no undeclared shared source).
- X6 no_hidden_state: no delivered quantity lacks a declared source; no
  privileged-non-grata name appears in OBS_FIELDS or in any delivered
  sample; the delivered-key scan over the battery is empty beyond the
  declared set.
- X7 determinism (P6).
- X8 regression (P7): both upstream suites green, unmodified, exit 0.
- P-class: named-variable law (ten x_* ABSENT verbatim from the inherited
  registry; no absent name ever delivered); input pins verified at run time
  (refusals: input_pin_missing, input_pin_drift, interface_pin_missing,
  interface_pin_drift, contract_pin_missing, contract_pin_drift);
  `vacuous_guard_selftest` required before any receipt.

## 7. Falsifier arms (F-class; clean control FIRST, named premature guard,
discriminator; a non-biting arm fails the build)

- FB1 undeclared_field_injection: clean = the production seam accepts the
  clean sample AND refuses the injected key `solver_penetration_m` (a
  solver-internal quantity) with `privileged_source`; tamper = an UNGUARDED
  scratch channel (a seam variant whose deliver accepts unconditionally --
  the exact defect a consumer sees when wired to an unguarded bus); the
  declared-only predicate must FAIL on the tampered delivery. Discriminator:
  the unguarded channel delivers the solver-internal key and breaks the
  predicate; the guarded seam refuses it.
- FB2 timing_strip: clean = samples accepted; tamper = a sample with
  t_dt_s = 0.0 (unbound timing); the seam must refuse `timing_unbound`.
- FB3 named_absent_fill: clean = accepted; tamper = a sample carrying
  `x_press`: 5.0 (a synthetic constant in an absent slot); the seam must
  refuse `named_absent_occupied`.
- FB4 force_pose_inconsistency (the card falsifier's force/pose prong):
  clean = contact_force_N == jn/dt holds; tamper = force delivered as
  2*jn/dt with the pose fields unchanged; the P3 conversion predicate must
  FAIL on the tampered sample.
- FB5 hidden_state_privileged: clean = ch_jn_Ns equals the recorded jn;
  tamper = ch_jn_Ns sourced from a privileged pre-solve penetration proxy
  (not the record); the traceability predicate must FAIL (delivered value
  != record value).

## 8. Capture plan (grasp/motion profile; registry row read mode=ro)

The profile procedure (replay attach, load/hold, release with attachment and
force telemetry) is realized on the observed scene|n=3 case (the closing
multi-channel case): 8 declared snapshot ticks (1, 4, 8, 12, 16, 20, 24, 28)
spanning attach (tick 1), hold (4..20) and release+fall (24, 28); every
frame is bound to the observed sample at that tick. The diagnostic layer
draws the DECLARED observation telemetry: per-channel support state, force
arrows scaled by the declared contact_force_N = jn/dt, and the timing stamp
(tick, phase, dt). Profile views mapped task-owned exactly as sealed G04
(realization wording inherited): 'whole-body/trunk relationship',
'wrist/digit attachment close-up', 'orthogonal view of each loaded
interface'; the 'tendon paths' diagnostic layer stays ABSENT (inventoried;
no tendons exist in this fixture). Clean view REQUIRED: clean/diagnostic
pairs share the exact camera and the exact physical state binding; state
hash preserved across view toggles. TIMING CONFORMANCE (motion class): the
tick interval is REAL -- tick_interval [1, 30] over the trace's true tick
axis, one tick = 0.005 s (pinned M06 DT) declared in tick_map and in every
camera record's `state_or_tick_interval`; frames are declared snapshot ticks
rendered at 1 video second per frame (the sealed G04 capture pattern at the
same grasp/motion profile). Full 17-field camera record on every row.
Codec: FFV1 `-level 3 -g 1 -fflags +bitexact` mkv; lossy never evidence;
ffmpeg version recorded; pixel presence measured per frame and re-measured
by check_capture_pixels.py. task_id SHORT form (G05) in manifest AND
context. visual_acceptance stays false BY DESIGN: independent visual review
remains the Sergeant/Lieutenant gate (this text-only worker inspects no
pictures).

## 9. Regression

The declared upstream suites re-run UNMODIFIED on this exact candidate
revision: (a) M06 `test_local_contact.py` (P1-P13, F1-F4); (b) the sealed
G04 `test_g04_checks.py` (the grip physics this card observes). Both exit 0;
receipts recorded.

## 10. Input pins (verified at run time; drift refuses the run)

| pin | path | sha256 |
|---|---|---|
| local_contact_py | ../MAT2-M06/local_contact.py | 1cd662b30343011eb4a0a01e461a1e82b00482d0371857c8e42d6bec8f9a28dc |
| m06_test_suite | ../MAT2-M06/test_local_contact.py | b832d0dc07c1762a190d4b662ceed2b1b6dd469cbd22343cb39934e90eb08e77 |
| contact_law_json | ../MAT2-M06/contact_law.json | 583962c29f18118a478dedb167f2c3667414b86f5cab4ee54763416f1df7e41b |
| m06_experiment_receipt | ../MAT2-M06/experiment_receipt.json | 2956dd7aaf3682fc18de9b724ddd8a695011ec74c9a12a5a56744b3d738a9397 |
| trunk_mesh_json | ../MAT2-F03/assets/trunk_01_mesh.json | 3b17441764714c5e5e9c7a43c3253b3271a0f508954095e1960a57820cef6ee7 |
| f03_material_state | ../MAT2-F03/assets/trunk_01_material_state.json | 91c17a5c59ce79af3dc0e8a6dadb00c92a039075775a0a1de618da12dfca61bd |
| g04_grip_contact_py | ../MAT2-G04/grip_contact.py | 0d6375484c350039468b31a2f7db2895d3365412aee52ce98de72b4173d69245 |
| g04_test_suite | ../MAT2-G04/test_g04_checks.py | a01b167e4393e2e513ba343f2bc6ba3fdf4d01ee08170f7fe8c3cb1c5c9a0ae1 |
| g04_report_sealed | E:/ChimeraWork/monkey-coordination/evidence-store/MAT2-G04/report/REPORT.md | dfca5b5556efe018ca09be4577bf6fbb5df38bb5c9ebc33d15bd18646ba349c8 |
| w04_freeze_manifest | E:/ChimeraWork/monkey-coordination/evidence-store/MAT2-W04/numerical/w04_freeze_manifest.json | be632ffc85865515285f3d622a09882a3180a43101027914f1ed3408496f5d29 |
| obs_interface_v2 | E:/ChimeraWork/pass3-integ/repo/tools/science_funnel/validation/policy_interface_freeze_20260920/observation_interface_v2.json | e8c2d698dee0337414c48e8d2f6569c45f6f61828dabdeff6a4f1188b1c0671c |
| g01_feasibility_receipt | E:/ChimeraWork/monkey-coordination/evidence-store/MAT2-G01/numerical/feasibility_receipt.json | 4061d8ec604ddea5dfbdf605f0244874129a69a88d771d4f593c7a927c16be42 |
| grasp_benchmark_md | E:/ChimeraWork/research-data/20260929/benchmark-grasp/GRASP_BENCHMARK.md | d936cebe38b1416dfc417db727ea81396eb8eb9217efed3f05b344db17f71610 |
| friction_sources_md | E:/ChimeraWork/monkey-coordination/g04-friction/FRICTION_SOURCES.md | 336118e929bd0b4fb067db5a448dc2e348fed073007787635549a4cf1cf5868b |

## 11. Refusal codes (named; nothing silently repaired)

input_pin_missing, input_pin_drift, interface_pin_missing,
interface_pin_drift, contract_pin_missing, contract_pin_drift,
undeclared_field, timing_unbound, timing_drift, named_absent_occupied,
privileged_source, nonfinite_value, dim_mismatch, observer_drift,
aliasing_undeclared, vacuous_comparison_refused + vacuous_guard_selftest
(G5 law), tamper_site_missing, scenario_refusal:* for any
preregistration-scenario mismatch.

## 12. Amendments

- a1 (pre-experiment, pre-implementation-commit): P4's supported-case count
  corrected from "9 stick cases" to the SEVEN cases the sealed G01 boundary
  table actually yields (band_lo/band_mid/band_hi x n=2,3 plus scene n=3;
  the five slip rows band_* n=1 and scene n=1,2 plus the zero-mu control
  stay honestly unsupported). Arithmetic slip in the frozen text only; no
  physics, constant, window, arm design or scenario changes.
- a2 (pre-receipt-run): the declared vector's aggregate group is EIGHT
  fields, not seven: `agg_reciprocity_max_Ns` (max |ledger reciprocity
  residual| this tick, a recorded action-reaction integrity signal) is the
  declared 32nd slot. Reason: the frozen text said OBS_DIM = 32 but listed
  only 31 slots -- a development shakedown run caught the discrepancy
  (audit count 7 shared sources, OBS_DIM 31); the declared dim is restored
  to match the frozen number. No physics, constant, window, arm design or
  scenario change; the timing law, availability law and every other field
  are unchanged.
- a3 (pre-receipt-run): FB1's tamper sharpened to an UNGUARDED scratch
  channel (deliver accepts unconditionally) and its clean control extended
  to include the production guard's `privileged_source` refusal of the
  injected key (the injected name sits in the privileged registry, so the
  guard's refusal class is privileged_source; the unguarded variant is what
  breaks the declared-only predicate). Arm class unchanged (undeclared
  field injection; clean control first; discriminator unchanged in kind).
