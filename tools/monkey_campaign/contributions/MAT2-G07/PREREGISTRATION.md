# PREREGISTRATION - MAT2-G07 (Measure unsupported release and falls)

Frozen BEFORE implementation and before any experiment run. Composed against
CARD_STARTER.md v3; house standards IMPLEMENTER_CHECKLIST.md (G1-G9) and
TOOLKIT.md (P1-P9) will be cited at the candidate commit. Base:
`fa02f07508ee15b7679d0f2a95ac6b1894f77962` (= origin/astra/gait-capture, the
MAT2-G05 merge PR #300). Attempt `6a00d37939ef4f258ae8fb730f3c96fb`,
agent `wk-g07-falls`, branch `codex/monkey-mat2-g07-6a00d379`.

done_when (verbatim): "Loss/release of support removes its forces and yields
accounted motion and energy"

Card observation (verbatim): "Preserve failures; no reset or leftover
constraint concealing loss of support"

Profile falsifier (verbatim): "Unresolved owner, nonphysical attachment,
unsupported transfer, concealment behind the trunk or force/pose
inconsistency fails."

Verification profile: `grasp` kind `motion` (read from the sealed dispatch;
re-read READ-ONLY from the registry at capture time). Calculations:

- C13 "Falls, energy and recovery": "Account delta stored energy against
  work, losses and external support under the declared model"; verification
  "Release/impact traces; no residual support, teleport or hidden reset".
- C20 "Vertical transfer and climbing load": verification "Static versus
  dynamic tests separated; release and missed-grasp controls".

Checkpoint V06 (grasp). Catalog refs CTRL-03, CTRL-04, BIO-02, CON-03,
CON-04, DYN-02. This card feeds K08 boundary work and X03 fall experience.

## 1. The established interfaces (material-first; imported, hash-asserted,
never forked)

- THE SOLVER: MAT2-M06 `chimera.local_contact.v1` (`../MAT2-M06/
  local_contact.py`, raw sha256 `1cd662b30343011eb4a0a01e461a1e82b00482d
  0371857c8e42d6bec8f9a28dc`) -- the pinned module G04 and G05 imported.
  Not one byte is modified; every impulse in this card comes from
  `lc.solve_tick`. The solver's recorded per-contact dissipation
  `w_f_ke_J` is the declared losses line of the C13 account.
- THE GRIP PHYSICS + FIXTURE: MAT2-G04's sealed `grip_contact.py`
  (raw sha256 `0d6375484c350039468b31a2f7db2895d3365412aee52ce98de72b
  4173d69245`, the exact revision merged in PR #298). G07 consumes the
  fixture builders, the press channel (P = 0.30 N*s per tick per channel),
  the closed forms, the frozen window set, the falsifier injection hooks
  (`sticky_release_weld`, `hidden_anchor`), and the named-absent list.
  G07 adds NO fixture geometry and NO contact law of its own. The one
  declared scenario-level change: the battery calls the UNMODIFIED
  `run_scenario` / observer with `release_ticks = 40` (a declared
  `run_scenario` parameter; G04's default 10 stays sealed) so the fall is
  long enough to measure (40 release ticks = 0.2 s; closed-form free-fall
  drop 0.1962 m from rest).
- THE OBSERVATION SEAM: MAT2-G05's sealed `contact_support_obs.py`
  (raw sha256 `3dae0a3805cec86bba8dbae9a6fc563f43cddc98fcd01a693f725e4f31
  c46bd3`, the exact revision merged in PR #300). Every scenario's
  measurement is delivered to the controller ONLY through G05's
  `ObservationSeam` + `project_sample` (the declared 32-slot table, timing
  block, refusal codes); G07 does not extend the table.
- THE W04 FREEZE MANIFEST and CONTRACT, THE G01 FEASIBILITY RECEIPT, THE
  FRICTION_SOURCES verdict and THE GRASP BENCHMARK: pinned as provenance
  records (section 10).

## 2. The declared measurement (the task-owned deliverable)

`release_fall_account.py` -- a G07-owned tick loop performing EXACTLY the
sealed G04/G05 per-tick operations in the same order (press impulse;
`lc.solve_tick`; the same row fields), additionally recording, per tick and
per body:

- `v_start` (velocity at tick start, before the press) and `v_press`
  (after the press impulse, i.e. the velocity the solver receives);
- the recorded ledger impulse vectors per body (`gravity`, `contact`,
  `anchor`) and the per-pad contact records in solver order;
- the measured pad centroid (full 3-vector, from the pinned body state).

Cross-validation prediction (the G05 heritage law): the G07 rows are
BIT-IDENTICAL to `gc.run_scenario`'s rows for every scenario (per tick, per
pad: jn_sum_Ns, jt_sum_Ns, mode, disp_tick_m, surfaces; the whole ledger
block). A mismatch refuses with `observer_drift`.

### 2a. The energy account (C13; the exact discrete impulse-work identity)

The M06 tick is: press (recorded channel, applied before `solve_tick`) ->
gravity impulse -> contact impulses (sequential records: normal, then
friction) -> anchor -> position integration. For one body of inverse mass
`w = inv_mass`, an impulse `J` applied to pre-impulse velocity `u` changes
the kinetic energy by EXACTLY `W = J.u + (w/2)|J|^2` (the discrete
work). Because the solver applies the owners sequentially and the account
replays them in the same order from the RECORDED impulses, the per-tick
identity is exact:

  KE(t) - KE(t-1) == W_press + W_gravity + W_contact + W_anchor

with `W_press = P.v_start + (w/2)|P|^2`, `W_gravity = J_g.v_press +
(w/2)|J_g|^2`, and `W_contact = sum over the pad's contact records
(applied in solver order) of [J_rec.v_current + (w/2)|J_rec|^2]`. The
replay closes with the internal identity `v_replay == v_after_solve`
(window 1e-12 m/s; refusal `impulse_replay_incomplete` if a record were
missed). The anchor line is exactly zero for this fixture (free pads carry
zero anchor; the pinned trunk's inverse mass is 0 and its velocity stays
(0,0,0) -- asserted every tick).

Declared windows: `WIN_ENERGY = 1e-12 J` per body per tick (float noise of
the identity; measured development values are O(1e-16)); losses
cross-check `sum(W_friction_records) == -sum(recorded w_f_ke_J)` within
`WIN_LOSS = 1e-12 J` (pinned trunk => relative tangential KE is the pad's;
the exact per-record identity above reproduces the solver's recorded
dissipation).

### 2b. The fall-phase stored-energy account (C13; declared discretization)

During release ticks the press is off. With PE defined as
`m*g*(z - z_release_start)` per pad (z UP, the pinned record-g convention
g = 9.81), the stored energy `KE + PE` changes per free-fall tick by the
EXACT discrete amount

  d(KE+PE) == -(m/2)*(g*DT)^2  +  W_contact

(the symplectic artifact: gravity work is measured at the pre-gravity
velocity while the position integrates the post-gravity velocity). The
declared prediction window is `WIN_DRIFT = 1e-9 J` per pad-tick: the
recorded release-tick contact noise (share-scaled bars, section 2c) makes
`W_contact` O(1e-10) J, so the drift identity is falsifiable four orders
above its window; any hidden impulse or propulsion of realistic size lands
far outside it.

### 2c. The release account (the done_when: forces REMOVED)

At every release tick of every scenario (the press channel recorded zero):

- `jn_sum_Ns` and `jt_sum_Ns` per pad within the sealed G04 share-scaled
  bars: `share_kg * 1e-10 N*s` (G04 prereg amendment a2);
- `W_press == 0` exactly (P = 0 recorded); the hold-to-release owner
  census changes exactly at the declared release tick (21);
- the trunk anchor reaction within `total_mass * 1e-10 N*s`;
- `agg_release_flag == 1.0` from the G05 seam exactly on ticks 21..60.

### 2d. The motion account (C13: "no residual support, teleport or hidden
reset"; C20 static/dynamic separation)

- Free-fall velocity recursion (declared per release tick, per pad):
  `v_down(k) == v_down(k-1) + g*DT` within the sealed
  `WIN_RECURSION_V = 1e-9 m/s` (the jt noise bar contributes
  <= 1e-10 m/s per tick);
- cumulative downward displacement vs the gravity-only closed form from
  the release-start state, within the sealed `WIN_DISP = 1e-9 m`
  (G04 heritage window; the measured fall here is ~0.196 m, four orders
  above the window);
- pose continuity (the anti-teleport identity, every tick of every
  scenario): `z(t-1) - z(t) == v_z_after(t) * DT` within
  `WIN_CONT = 1e-9 m` (the solver integrates positions with the post-solve
  velocity; a teleport or state reset breaks it);
- phases are TAGGED at emission (`hold` / `release`) and every phase
  metric is extracted ONLY through a keyed per-phase extractor that
  refuses mixed scans and unknown phases (P6; C20 static-versus-dynamic
  separation). The hold (static, supported) account and the release/fall
  (dynamic) account are reported separately per case class:
  stick / slip / zero-mu.

### 2e. The seam delivery (the G05 composition)

Every scenario's 60 ticks are delivered through a fresh G05
`ObservationSeam` (declared key set unchanged: 4 timing + 32 vector
slots): 13 x 60 = 780 accepted deliveries, 0 refusals expected. The seam's
declared slots bind to THIS card's account: `ch{k}_disp_down_cum_m`
equals the account's cumulative displacement (float32 window), and
`agg_release_flag` flips exactly at the declared release tick.

## 3. Frozen battery

The G04 battery: readings {band_lo 5.4, band_mid 6.15, band_hi 6.9,
scene 10.037998} kg x channels {1,2,3} = the 12 grip cases, plus the
zero-mu control (band_mid, n=3, mu=0, label suffix `|mu=0`) = 13
scenarios; 20 hold ticks + 40 release ticks = 60 ticks each (the declared
`release_ticks = 40`); 780 seam deliveries. CPU-only, no RNG, no wall
clock. The rendered capture scenario is `scene|n=3` (the closing
multi-channel case; stick arrest at release => the fall starts from rest).

## 4. Preregistered predictions

- P1 release removes the forces: on every release tick of all 13
  scenarios the recorded pad impulses sit inside the share-scaled noise
  bars, `W_press == 0`, the trunk anchor is inside its bar, and the
  delivered `agg_release_flag == 1.0` (ticks 21..60 exactly).
- P2 motion accounted: every release-phase pad satisfies the velocity
  recursion and the closed-form displacement within the sealed windows;
  the pose-continuity identity holds on every tick of every scenario
  (no teleport, no reset).
- P3 energy accounted: the exact impulse-work identity closes within
  `WIN_ENERGY` for every body and tick of every scenario; the losses line
  matches the solver's recorded `w_f_ke_J` sums within `WIN_LOSS`; the
  release-phase stored-energy drift equals the declared discretization
  value within `WIN_DRIFT`.
- P4 phase separation (C20): hold and release metrics are extracted per
  phase by the keyed extractor (phase state counts recorded: 20 + 40 per
  scenario); the static hold account (press work, friction losses) and the
  dynamic release account (gravity work, free fall) are reported
  separately; the zero-mu control is the missed-grasp control: never
  supported, its release still removes the press, and its account closes.
- P5 seam delivery: 780 accepted, 0 refusals; every delivered value
  traces to the recorded row/account inside the float32 window.
- P6 determinism: two independent runs byte-identical (trace + receipt;
  declared augmentation key set empty).
- P7 regression: the M06 suite, the sealed G04 suite AND the sealed G05
  suite re-run UNMODIFIED on this revision, all exit 0.

Honest carry-overs (never repaired here): mu_s = 0.6 / mu_k = 0.4 stay the
NAMED placeholders of the sealed upstream (the measured-volar acquisition
stays G04's recorded debt); the press channel stays a declared fixture
input, never an actuator qualification; the ten x_* variables stay ABSENT
with verbatim provenance; single-channel support and scene n=2 do NOT
close (honest slip rows); NO impact is modeled or claimed (no floor body
exists in this fixture; the pad falls alongside the trunk within the
declared window) -- C13's impact trace is out of scope and disclosed; the
creature-side anatomy stays ABSENT (owners unresolved in records).

## 5. Named checks (test_g07_checks.py; executed, none skipped)

- X1 release_removes_support (P1).
- X2 motion_accounted (P2: recursion, closed form, continuity).
- X3 energy_account_exact (P3: impulse-work identity + replay identity +
  losses cross-check).
- X4 fall_energy_drift (P3: the declared discretization account).
- X5 seam_delivery_composition (P5 + the displacement/release-flag
  bindings of section 2e).
- X6 phase_separation (P4: keyed per-phase extraction, per-class
  accounts, zero-mu missed-grasp control).
- X7 named_absent_law (the ten x_* ABSENT verbatim; no absent name
  delivered).
- U-class upstream identity (M06/G04/G05 pins; imported-not-forked).
- F-class falsifiers all bite (with clean controls and premature guards).
- D-class determinism (P6).
- R-class regression (P7: three upstream suites green, unmodified).
- P-class: input pins verified at run time (refusals input_pin_missing,
  input_pin_drift, interface_pin_missing, interface_pin_drift);
  `vacuous_guard_selftest` required before any receipt (G5 law: the guard
  refuses an identically-zero comparison; this card's tolerance gates are
  absolute-window, and the guard still arms the account totals).
- Accounted-count law (G12): claims state "N executed, M skipped" from the
  suite summary; no KNOWN_SKIPS file exists on this card.

## 6. Falsifier arms (F-class; clean control FIRST, named premature guard,
discriminator; a non-biting arm fails the build)

Ground case for every clean control: the observed `scene|n=3` battery run
(clean, no injection). Tamper variants run in the SAME process after their
clean control, through scratch copies or recorded hooks (never silent):

- FB1_release_residual_support (the leftover-constraint class): clean =
  the release account holds (bars + `W_press == 0` + free fall). Tamper =
  G04's recorded `sticky_release_weld` hook: a leftover constraint holds
  the pad after release. The release account must FAIL on the tampered
  trace (held pad: release displacement ~0 vs the 0.196 m closed form;
  weld work appears in the account owner census). Guard `g07_fb1_premature`.
- FB2_energy_owner_concealment (the unresolved-owner / hidden-impulse
  class, measured in JOULES): clean = the per-tick energy identity closes
  within `WIN_ENERGY`. Tamper = G04's `hidden_anchor` hook: an impulse
  applied to the body but absent from every recorded channel. The energy
  identity must FAIL on the tampered run (KE appears with no recorded
  owner). Guard `g07_fb2_premature`.
- FB3_hidden_reset_teleport (the reset class; card observation): clean =
  the pose-continuity identity holds on every tick. Tamper = a scratch
  runner variant that teleports the falling pad back to its release-start
  pose (and zeroes its velocity) mid-fall, the injection RECORDED in the
  scenario header. The continuity identity must FAIL on the tampered run.
  Guard `g07_fb3_premature`.
- FB4_unsupported_propulsion: clean = the release-phase velocity recursion
  and closed-form displacement hold while the recorded force bars also
  hold. Tamper = a scratch runner variant injecting a small upward
  (anti-gravity) impulse per release tick through the unrecorded channel:
  the recorded forces STILL read inside the bars, but the motion account
  must FAIL (motion not supported by recorded forces). Guard
  `g07_fb4_premature`.
- FB5_force_pose_inconsistency (the profile falsifier's named prong):
  clean = the declared support verdict (G05 law: supported iff every
  available channel records stick AND phase hold) agrees with the
  force/pose record everywhere (stick forces inside the hold band while
  supported; noise-bar forces while released). Tamper = a verdict variant
  that keeps claiming support from a stale stick flag after release: the
  claimed verdict contradicts the recorded forces/pose (falling pose,
  noise-bar forces) and must FAIL. Guard `g07_fb5_premature`.

## 7. Capture plan (grasp/motion profile; registry row read mode=ro)

The profile procedure (replay attach, load/hold, release with attachment
and force telemetry) is realized on the observed `scene|n=3` case: 8
declared snapshot ticks (1, 8, 16, 20, 24, 32, 44, 56) spanning attach
(1), hold (8..20), the release transition (24) and the measured fall
(32..56; closed-form drop from rest 0.128 m by tick 56). Pads are drawn at
their TRACE centroids (the measured falling poses) and the in-frame gate
runs on the DRAWN poses at every snapshot tick. The diagnostic layer draws
the declared support state (stick/slip/RELEASE), contact normal arrows
scaled by the recorded jn, force arrows by jt, the joint/frame triad, the
attachment endpoint ids, and the release telemetry (tick/phase/dt,
support count, cumulative fall displacement). Profile views mapped
task-owned exactly as sealed G04/G05: 'whole-body/trunk relationship',
'wrist/digit attachment close-up', 'orthogonal view of each loaded
interface'; 'tendon paths' stays ABSENT (inventoried; no tendons exist in
this fixture). Clean view REQUIRED: clean/diagnostic pairs share the exact
camera and the exact physical state binding; state hash preserved across
view toggles. TIMING CONFORMANCE (motion class, checked BEFORE building
the capture -- the W06 lesson): the profile kind is `motion`, so the tick
axis is REAL -- tick_interval [1, 60] over the trace ticks, one tick =
0.005 s (pinned M06 DT), declared in tick_map and in every camera record's
`state_or_tick_interval`; frames are the declared snapshot ticks rendered
at 1 video second per frame (the sealed G04/G05 capture pattern at the
same profile). Full camera record on every row (the registry's required
fields plus handedness/axes: frame_id, coordinate_unit, position,
orientation_convention_and_values, target, distance_to_target, projection,
vertical_fov_or_orthographic_span, near_far_planes, aspect_ratio,
viewport_resolution, camera_motion_or_bookmark_sequence, visibility_
layers, label_ids, occlusion_or_xray_mode, state_or_tick_interval).
Codec: FFV1 `-level 3 -g 1 -fflags +bitexact` mkv; lossy never evidence;
ffmpeg version recorded; pixel presence measured per frame and re-measured
from the DECODED frames by check_capture_pixels.py. task_id SHORT form
(G07) in manifest AND context. visual_acceptance stays false BY DESIGN:
independent visual review remains the Sergeant/Lieutenant gate (this
text-only worker inspects no pictures).

## 8. Regression

The declared upstream suites re-run UNMODIFIED on this exact candidate
revision: (a) M06 `test_local_contact.py`; (b) sealed G04
`test_g04_checks.py`; (c) sealed G05 `test_g05_checks.py`. All exit 0;
receipts recorded.

## 9. Input pins (verified at run time; drift refuses the run)

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
| g05_contact_support_obs_py | ../MAT2-G05/contact_support_obs.py | 3dae0a3805cec86bba8dbae9a6fc563f43cddc98fcd01a693f725e4f31c46bd3 |
| g05_test_suite | ../MAT2-G05/test_g05_checks.py | 83ba17604f66fdbe623b71ce481b539862ec39ebf81ee4c8bea2e5af29f9985b |
| g04_report_sealed | E:/ChimeraWork/monkey-coordination/evidence-store/MAT2-G04/report/REPORT.md | dfca5b5556efe018ca09be4577bf6fbb5df38bb5c9ebc33d15bd18646ba349c8 |
| g05_report_sealed | E:/ChimeraWork/monkey-coordination/evidence-store/MAT2-G05/report/REPORT.md | 1e5fcc7f81b5bd7b0ae3b460c72d5ed190510f66db4793c6b2e99756da8c8524 |
| g01_feasibility_receipt | E:/ChimeraWork/monkey-coordination/evidence-store/MAT2-G01/numerical/feasibility_receipt.json | 4061d8ec604ddea5dfbdf605f0244874129a69a88d771d4f593c7a927c16be42 |
| w04_freeze_manifest | E:/ChimeraWork/monkey-coordination/evidence-store/MAT2-W04/numerical/w04_freeze_manifest.json | be632ffc85865515285f3d622a09882a3180a43101027914f1ed3408496f5d29 |
| obs_interface_v2 | E:/ChimeraWork/pass3-integ/repo/tools/science_funnel/validation/policy_interface_freeze_20260920/observation_interface_v2.json | e8c2d698dee0337414c48e8d2f6569c45f6f61828dabdeff6a4f1188b1c0671c |
| grasp_benchmark_md | E:/ChimeraWork/research-data/20260929/benchmark-grasp/GRASP_BENCHMARK.md | d936cebe38b1416dfc417db727ea81396eb8eb9217efed3f05b344db17f71610 |
| friction_sources_md | E:/ChimeraWork/monkey-coordination/g04-friction/FRICTION_SOURCES.md | 336118e929bd0b4fb067db5a448dc2e348fed073007787635549a4cf1cf5868b |

## 10. Refusal codes (named; nothing silently repaired)

input_pin_missing, input_pin_drift, interface_pin_missing,
interface_pin_drift, observer_drift, impulse_replay_incomplete,
phase_unknown, phase_metric_key_missing, mixed_phase_scan,
energy_identity_broken, release_bar_exceeded, continuity_broken,
drift_identity_broken, seam_refusal:* (the sealed G05 delivery codes),
tamper_site_missing, scenario_refusal:* for any preregistration-scenario
mismatch, vacuous_comparison_refused + vacuous_guard_selftest (G5 law).

## 11. Amendments

- a1 (pre-experiment, pre-implementation-commit; development shakedown of
  the falsifier mechanics; NO physics, constant, window, scenario or arm
  change):
  (i) FB1's tampered trace books the weld as a RECORDED owner
  (`work_weld_J`, the exact discrete impulse work at the weld's
  pre-velocity `v_start + press*inv_m`); the line is exactly 0.0 on every
  clean run. Reason: the weld is a recorded channel in G04's hook, so the
  account must close on the tampered trace and the RELEASE predicates
  (bars + free-fall closed form) are the declared bite -- otherwise the
  energy identity would fire first on a recorded (legitimate) owner.
  (ii) FB2-FB4's tampered runs use the falsifier-only measurement mode
  `enforce_account=False`: the account residuals are still computed and
  RECORDED per row but not enforced, so the tampered trace is MEASURED
  (worst energy residual in joules for FB2, continuity break in meters
  for FB3, motion-account break via the release account refusal for FB4)
  instead of dying at its first refusal. The production law
  (`enforce_account=True` + `require_ledger=True`) stays armed on every
  clean run and on the whole battery. The stored-energy prediction now
  books the recorded weld line in its predicted work (`W_press + W_weld +
  W_contact + ...`; 0.0 on clean runs).
- a2 (pre-experiment, pre-implementation-commit; development shakedown of
  the 60-tick battery; NO physics, constant, window, scenario or arm
  change): the shakedown measured a REAL new phenomenon at the longer
  release window that the frozen text did not anticipate: in 2 of the 13
  scenarios (scene|n=1 at tick 60, band_mid|n=3|mu=0 at tick 56) a
  SLIDING pad's corner strikes a facet ridge of the pinned trunk mesh and
  the solver fires a recorded CCD collision event (recorded jn 0.033 /
  0.0069 N*s -- a genuine transient contact force, NOT residual support;
  the exact energy identity closes through it at 1.4e-14 J). The scoping
  below is declared by the SOLVER'S OWN record kind (`kind == 'ccd'`),
  never by a tuned threshold:
  (i) the release noise bars (section 2c) and the free-fall recursion /
  closed-form motion account (section 2d) are enforced on the
  UNOBSTRUCTED release ticks; collision-event ticks are RECORDED
  per-event (tick, jn, jt, anchor) as collision evidence in the receipt;
  (ii) the pose-continuity law (section 2d) becomes two-tier: the exact
  identity `z(t-1)-z(t) == -v_z_after(t)*DT` on unobstructed ticks; on a
  CCD-advance tick the KINEMATIC anti-teleport bound (the body cannot
  advance farther than free fall from its pre-solve velocity, nor move
  upward) with the exact-form residual still recorded;
  (iii) the stored-energy account (section 2b) is enforced on
  unobstructed ticks; on a collision tick its residual is recorded as
  the collision's stored-energy exchange (the impact dissipates through
  the recorded contact impulse, which the exact KE identity carries);
  (iv) the closed-form displacement claim is asserted on the
  unobstructed prefix (39/40 and 35/40 release ticks for the two
  affected scenarios; 40/40 for the other eleven).
  The done_when is unaffected: the press/support forces are removed
  (W_press == 0 exactly, bars on unobstructed ticks) and the motion and
  energy stay accounted THROUGH the collision events (the account closes
  at every tick; the collisions are recorded, disclosed and carried).
