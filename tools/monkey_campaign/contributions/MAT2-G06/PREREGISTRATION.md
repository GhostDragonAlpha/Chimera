# PREREGISTRATION - MAT2-G06 (Prove a supported limb-transfer sequence)

Frozen BEFORE implementation and before any experiment run. Composed against
CARD_STARTER.md v3; house standards IMPLEMENTER_CHECKLIST.md (G1-G9) and
TOOLKIT.md (P1-P9) will be cited at the candidate commit. Base:
`fa02f07508ee15b7679d0f2a95ac6b1894f77962` (= origin/astra/gait-capture, the
MAT2-G05 merge PR #300). Attempt `815ae4e134ee41e8a2026f835324e4fd`,
agent `wk-g06-transfer`, branch `codex/monkey-mat2-g06-815ae4e1`,
criteria_sha256 `244ec17a4265b1eff67a541566bc68764ca37e4597554e4ddd6221896ca`
`30b83`, ontology scope_sha256
`cb5475f8486197a973edc4360b177fc31a629c4f0979ebf80dd76aae57996097`.

done_when (verbatim): "At least one reachable transfer retains admissible
support throughout its tested envelope"

Card observation (verbatim): "Static whole-body equilibrium alone is
insufficient". Profile falsifier (verbatim): "Unresolved owner, nonphysical
attachment, unsupported transfer, concealment behind the trunk or force/pose
inconsistency fails." Profile procedure (verbatim): "Replay approach, attach,
load, hold, transfer and release with attachment and force telemetry."

Ontology calculations C16 (grasp reach and anatomical correspondence) and C20
(vertical transfer and climbing load) are consumed at their recorded
inventory status: this card claims NO measured creature quantity and fills NO
named absent variable (section 7). C16's reachability is composed as a
DECLARED fixture reach envelope (x_reach stays ABSENT); C20's support
sequence is composed as a DECLARED, solver-replayed transfer sequence
(x_sequence, x_trajectory, x_losses, x_inertia stay ABSENT).

## 1. The established interfaces (imported, hash-asserted, never forked)

- THE SOLVER: MAT2-M06 `chimera.local_contact.v1` (`local_contact.py`, raw
  sha256 `1cd662b30343011eb4a0a01e461a1e82b00482d0371857c8e42d6bec8f9a28dc`)
  -- imported at run time, sha asserted, never forked. Every impulse in this
  card comes from `lc.solve_tick`.
- THE GRIP PHYSICS + FIXTURE: MAT2-G04's sealed `grip_contact.py` (sha256
  `0d6375484c350039468b31a2f7db2895d3365412aee52ce98de72b4173d69245`) -- the
  exact revision merged in PR #298. G06 consumes its trunk loader, facet
  channel selection, pad placement, vector helpers, press operating point,
  named-absent list and window forms. G06 adds NO new trunk geometry and NO
  new mu source.
- THE OBSERVATION TABLE: MAT2-G05's sealed `contact_support_obs.py` (sha256
  `3dae0a3805cec86bba8dbae9a6fc563f43cddc98fcd01a693f725e4f31c46bd3`) -- the
  exact revision merged in PR #300. G06 binds to the G05 32-slot declared
  table (imported as the live pinned object, bit-identical slot semantics)
  and the G05 seam law family, and declares the task-owned G06 phase
  universe (section 8). G06 does NOT extend or re-declare the W04 TC-2
  80-field walking interface and does NOT modify the G05 module.
- THE SEALED BOUNDARY: MAT2-G01's pinned feasibility receipt (sha256
  `4061d8ec604ddea5dfbdf605f0244874129a69a88d771d4f593c7a927c16be42`) -- its
  12-row case table IS the transfer-admissibility authority (section 5).

## 2. What "a supported transfer" means on this card (declared model)

The sealed G04 fixture abstracts one grip channel as a pad body whose
mass_kg is the load share routed through that channel (the declared equal
partition; per-port load share stays `x_share` ABSENT). G06 extends exactly
that abstraction with the DECLARED LOAD HANDOVER: when the relocating
channel releases, the load it carried is re-partitioned in equal shares over
the remaining (holding) channels -- holders carry `m/(n-1)` each (total m)
for the whole flight window, and the original partition `m/n` is restored at
re-attachment. Both handover events are DECLARED schedule events (recorded
per tick in the rows and in the header schedule), never silent: the per-tick
rows record each pad's `mass_kg` and the handover event log records the
ticks. There is no measured partition source (`x_share` ABSENT); the equal
re-partition is the declared model, the same disclosure class as G04's equal
`m/n`.

Under this model the transfer-phase support condition is EXACTLY the sealed
G01 row at `(reading, n-1)`: the holding configuration must carry the full
reading `m` over `n-1` channels, whose per-channel stick condition is
`(m/(n-1))*g*DT <= mu_s*P` -- the same arithmetic G01 sealed and G04's
solver reproduced. "A legal transfer lives where the multi-channel
arithmetic closes" is therefore not a metaphor here: the sealed
OUTSIDE-CONDITIONAL boundary, restricted to the holding configurations,
PREDICTS which transfers close (section 5).

The relocating limb is self-carried during the flight by the DECLARED CLIMB
CHANNEL: a recorded external impulse channel (exactly like the press channel
-- a fixture input at a declared schedule, NEVER an actuator qualification;
`x_press` stays ABSENT). Every climb impulse is recorded per tick and enters
the full-tick ledger identity. The channel schedule: gravity-cancelling
hover wherever the limb is self-carried (approach/attach, the post-brake
hover, attach2), an accel-cruise-brake profile at the declared climb speed
`V_CLIMB_MPS = 0.5` during the transfer window, and zero wherever the grip
carries the limb (load/hold/load2/hold2, release). The load phase of the
profile procedure is precisely the recorded climb-to-friction handover: at
the load ticks the climb channel goes to zero and the pad's friction begins
carrying its share (`jt = share*g*DT`, measured).

## 3. Frozen fixture (declared, inside the approved architecture)

Frame, trunk, pads, materials, press channel: EXACTLY the sealed G04
fixture (its `to_m06_frame`, `load_trunk_geometry` 64-lateral partition,
`channel_facets` selection, F03 `TETRA_LOCAL`/`TETRA_TRIS` pads at
`PAD_OFFSET_M = 0.9e-5`, trunk `wood_trunk_01` pinned body, pad mu_s 0.6 /
mu_k 0.4 NAMED placeholders, pair rule `elementwise_min`, press
`P = 0.30 N*s` inward along the facet normal). Deviations (all DECLARED
here):

- THE TRANSFER TARGET: lateral triangle 1 -- the same-column facet whose
  centroid z is `0.772` m (the source S1 facet, triangle 0, has centroid z
  `0.386` m). Measured at the pinned mesh (development shakedown, recorded
  here as a fixture declaration): triangle 1's outward normal equals
  triangle 0's (`[0.9951835289511874, -0.09802930023345664, 0.0]`) and the
  source centroid lies ON triangle 1's plane (offset `0.0` m, normal angle
  `0.0` deg) -- the trunk is a 32-column prism with two centroid bands per
  column, so the declared transfer is a straight vertical slide of
  `0.386` m within one coplanar column. The X6 probe re-measures this
  coplanarity at run time (refusal `target_facet_drift`).
- THE RELOCATING CHANNEL: channel 0 (the sealed S1 facet). Holders are the
  remaining channels. `n` in {2, 3} (the multi-channel cases; the
  single-channel row is OUTSIDE everywhere in the sealed boundary and is
  carried by the n=2 -> one-holder cases).
- APPROACH STAND-OFF: the flyer starts at `STANDOFF_M = 2.0e-5` m from its
  facet (outside the `1e-5` contact margin) instead of `PAD_OFFSET_M`; the
  holders start at the sealed `PAD_OFFSET_M`. The flyer is driven inward by
  the DECLARED APPROACH PRESS `A_PRESS = 0.0016 N*s` (the approach velocity
  accumulates over the off-contact ticks, so the creep accelerates until
  the gap crosses into the margin; per-case closed form in section 5).
  The contact-establishment event (declared CCD path) lands in tick 2
  (three-channel cases) or tick 3 (two-channel cases) at the accumulated
  approach impulse -- recorded with its impulse in the rows; from tick 4
  the press is at the operating point in every case and `jn = P` holds
  exactly (momentum bookkeeping, the sealed G04 form).
- THE CLIMB CHANNEL: declared external impulse along `+z` on the flyer
  (section 2), recorded per tick in the row's ledger extension and inside
  the full-tick identity.

## 4. Frozen schedule (228 ticks per scenario; M06 G = 9.81, DT = 0.005 s)

| ticks | phase | press (flyer) | press (holders) | climb channel | masses |
|---|---|---|---|---|---|
| 1..3 | approach | A_PRESS | P | hover (m*g*DT) | m/n each |
| 4..7 | attach | P | P | hover | m/n each |
| 8..10 | load | P | P | OFF (climb-to-friction handover) | m/n each |
| 11..30 | hold | P | P | OFF | m/n each |
| 31 | HANDOVER event | 0 | P | accel to V | holders -> m/(n-1) |
| 31..180 | transfer (climb) | 0 | P | accel + cruise | holders m/(n-1) |
| 181..190 | transfer (brake) | 0 | P | brake to v=0 (10 ticks) | holders m/(n-1) |
| 191..192 | transfer (hover) | 0 | P | hover | holders m/(n-1) |
| 193 | RE-ATTACH event | P | P | hover | holders -> m/n |
| 193..196 | attach2 | P | P | hover | m/n each |
| 197..199 | load2 | P | P | OFF | m/n each |
| 200..219 | hold2 | P | P | OFF | m/n each |
| 220..229 | release | 0 | 0 | OFF | m/n each |

Cruise tick count: `cruise = floor(travel/(V*DT)) - 1 - (BRAKE-1)//2` with
`travel = 0.386`, `V*DT = 2.5e-3`, `BRAKE = 10` -> `cruise = 148` full-speed
ticks after the accel tick; declared stop window: the brake ends at
`v = 0` exactly (the per-tick brake impulse is computed from the MEASURED
velocity), and the measured stop position must satisfy
`|stop_face_z - 0.772| <= CAPTURE_WINDOW_M = 5e-3` (the discretization
residue of one cruise step plus recorded contact events).

The brake/hover/climb schedule is applied from MEASURED velocity each tick
(a recorded channel; the resulting kinematics are verified against the
closed forms in section 5). Flight contact events (the pad face sweeping the
column-diagonal region can record a small CCD contact with a neighbouring
facet -- development shakedown measured `jn = 2.770691e-3 N*s` in one
configuration) are RECORDED in the event log with their impulse and tick;
they are part of the honest flight telemetry, and the kinematics checks
treat their ticks through the recorded `(toc, post-event velocity)` pair.
No teleportation exists anywhere in the schedule: every position change is
solver integration of recorded impulses.

## 5. Preregistered predictions (closed forms; the solver must reproduce them)

- P1 BOUNDARY COMPOSITION (the card's core prediction): the measured
  transfer-phase support (every holding channel stick at EVERY transfer
  tick 31..192) equals the sealed G01 row `(reading, n-1)` for all eight
  cases, which equals the closed form `(m/(n-1))*g*DT <= mu_s*P`:

  | case | holding row | closed form N*s | predicted transfer |
  |---|---|---|---|
  | band_lo 5.4, n=3 | (band_lo, 2) | 0.132435 <= 0.18 | SUPPORTED (closes) |
  | band_mid 6.15, n=3 | (band_mid, 2) | 0.15082875 <= 0.18 | SUPPORTED (closes) |
  | band_hi 6.9, n=3 | (band_hi, 2) | 0.1692225 <= 0.18 | SUPPORTED (closes) |
  | scene 10.037998, n=3 | (scene, 2) | 0.24618122 > 0.18 | NOT supported |
  | all readings, n=2 | (reading, 1) | m*0.04905 > 0.18 | NOT supported |

  The three band n=3 rows are the done_when transfers; the five others are
  EXPECTED honest non-closings executed by the solver (holders slip with the
  exact recursion `dv = g*DT - mu_k*P/m_holder` per tick, window 1e-9),
  consistent with the sealed G01 OUTSIDE-CONDITIONAL verdict. The two mass
  systems stay DISTINCT; verdicts per reading, never averaged.
- P2 HANDOVER TELEMETRY: at every transfer tick of a closing case, each
  holder records `jn = P` (window 1e-9) and `jt = (m/(n-1))*g*DT`
  (window 1e-9; the shakedown measured bit-exact 0.132435 / 0.15082875 /
  0.1692225); stick arrest `vt_post <= 1e-12 m/s`; holder downward
  displacement <= 1e-9 m per tick after the handover tick.
- P3 FLIGHT KINEMATICS: the flyer's face-centre z advances
  `v(t)*DT` per tick (window 1e-12 per non-event tick; event ticks through
  the recorded `(toc, post-event velocity)`), with `v(t)` the declared
  accel/cruise/brake/hover schedule; per-tick continuity
  `0 <= dz <= (V + 1e-2)*DT` at every flight tick (the teleportation
  discriminator); the climb impulse per tick is recorded and the stop
  satisfies the declared capture window (section 4).
- P4 ATTACHMENT AND FORCE TELEMETRY: at every pressed attached tick
  (non-flyer always; flyer outside the flight window), the pad's contact
  records sum to `jn = P` (window 1e-9; verified from tick 4 for the
  relocating channel -- the establishment ticks record their own smaller
  approach impulses, disclosed in section 3) and the declared force
  conversion `jn/DT = 60.0 N` holds; the full-tick identity
  `m*(v_after - v_before_press) == press + climb + gravity + contact +
  anchor` holds for every body, every tick, every scenario (window 1e-12);
  reciprocity residual 0; the trunk anchor equals minus the summed trunk
  contact impulse every tick (window 1e-12) -- a VISIBLE recorded anchor.
- P5 RELEASE: at every release tick every pad records
  `jn <= share_kg*1e-10` and `jt <= share_kg*1e-10` (the sealed G04 a2
  bars); the per-pad velocity follows `v(k) = v(k-1) + g*DT` from the
  measured release-entry velocity (window 1e-9); holders (released from
  clean stick, v = 0) additionally accumulate displacement
  `g*DT^2*(1+2+...+10) = 0.013488749999943705` m (window 1e-9). Nothing
  retains a force after the press stops.
- P6 SUPPORT LAW (declared, tick by tick): approach -- NOT supported
  (the relocating channel is establishing); attach/attach2 -- supported iff
  every holder records stick AND the flyer records pressed contact with
  `jn = P` (window 1e-9; the flyer is self-carried by its recorded climb
  channel); load/hold/load2/hold2 -- supported iff EVERY channel records
  stick; transfer -- supported iff every HOLDING channel records stick;
  release -- NOT supported. The done_when TESTED ENVELOPE is the contiguous
  tick span [4, hold2_end] = [4, 219] of each closing case; the claim of
  this card is that the band n=3 transfers record supported=true at EVERY
  tick of that envelope (the receipt carries the tick-by-tick verdict rows;
  the report renders them).
- P7 REACHABILITY AND IDENTITY (C16 composition, declared envelope): the
  measured face-centre transfer displacement `|dz| = 0.386` m satisfies
  `<= D_MAX_REACH_M = 0.5` (the DECLARED fixture reach envelope; x_reach
  stays ABSENT -- this is a fixture kinematic envelope, NOT a creature
  reach claim); the hold-phase flyer contact records include the source
  facet (triangle 0) and the hold2-phase records include the target facet
  (triangle 1); the run-time coplanarity probe reproduces the declared
  target geometry (refusal `target_facet_drift`).
- P8 ZERO-MU CONTROL: `band_mid|n=3|transfer|mu=0` (the G04 label-hygiene
  suffix law): with mu_s = mu_k = 0 the handover cannot hold -- the holders
  record slip at the transfer ticks and the transfer-phase support is
  False. Adhesion-free.

Where the physics says a case cannot close, it does not close. Named absent
variables are carried, never filled: x_press, x_share, x_aperture, x_reach,
x_com, x_inertia, x_trajectory, x_sequence, x_losses, x_trunk_strength
(verbatim provenance inherited from the pinned G04 module; no synthetic
constant occupies an absent slot; `lambda_min` occurs in no artifact of this
card). Creature-side components stay OUT of the fixture and inventoried
absent (no creature body, no wrist/digit anatomy, no tendons, no joint axes
beyond the declared pad/trunk frames; the A09 anatomical endpoint ids are
NOT used as fixture ids).

## 6. Named checks (test_g06_checks.py; executed, none skipped)

- X1 done_when_transfer_envelope: for each of the three band n=3 cases,
  EVERY tick 4..219 records supported=true under P6; the receipt carries
  the tick-by-tick verdict rows (phase, holding stick count, verdict) and
  the report renders them.
- X2 sealed_boundary_composition: the 8-case solver table (transfer-phase
  support) == the closed-form table == the pinned G01 receipt rows
  `(reading, n-1)`; the two mass systems split; no row flips under record-g
  vs standard-g arithmetic (largest g-delta 1.7e-4 N*s vs minimum row
  margin 2.16e-2 N*s).
- X3 flight_kinematics: continuity + per-tick closed forms + recorded
  climb impulses + the declared capture window (P3).
- X4 handover_and_force_telemetry: P2 + P4 (jn establishment, ledger
  identity with the climb channel, reciprocity, visible anchor, 60 N
  conversion at the operating point).
- X5 release_law: P5.
- X6 reachability_and_identity: P7 (D_max envelope, facet identities,
  coplanarity probe).
- X7 determinism: two independent main runs byte-identical (trace) with the
  declared augmentation keys scoped (card-kit X2 form).
- P-class: seam law (declared keys only; explicit timing; monotone; the
  x_* namespace refused live with `named_absent_occupied`; the pinned G05
  seam accepts the hold/release projections of the same samples and refuses
  the G06-only phases with `timing_unbound` -- the composition is at the
  shared-table level and the phase extension is real); named-variable law;
  input pins verified at run time (refusals: input_pin_missing,
  input_pin_drift, interface_pin_missing, interface_pin_drift);
  prereg-identity (criteria_sha256 identical across dispatch, registry,
  this preregistration and checks); regression (below).

## 7. Falsifier arms (F-class; every arm clean-control FIRST, named premature
guard `g06_fb<n>_premature`, receipt row with the clean-control block; a
non-biting arm fails the build)

- FB1 teleport_transfer: clean = the flight passes the continuity check;
  tamper = a scratch variant that sets the flyer's vertices to the target
  pose at the handover tick (the teleportation class); discriminator = the
  continuity check must PASS clean and FAIL tampered (dz jump ~ 0.386 m >>
  window).
- FB2 support_overclaim: clean = the support assertion matches the measured
  modes on band_mid|n=3 (supported) and scene|n=3 (honestly not);
  tamper = the stick mode substituted for the measured modes on the
  scene|n=3 transfer ticks (an unsupported transfer recorded as supported);
  discriminator = the assertion fails on the tampered trace (F03 B7 / G04
  FB5 heritage: the discriminator must discriminate).
- FB3 flight_hidden_anchor: clean = X4 residuals <= 1e-12 everywhere;
  tamper = an unrecorded 0.02 N*s per-tick impulse on the flyer during the
  flight window (an invisible anchor; the concealment class);
  discriminator = `ledger_imbalance` fires with residual ~ 2e-2.
- FB4 release_sticky: clean = P5 bars pass; tamper = a scratch variant that
  re-applies the last hold friction impulse after press-off (G04 FB1
  heritage); discriminator = the release law fires (free-fall displacement
  differs by >> window).
- FB5 force_pose_inconsistency: clean = the declared conversion
  `jn/DT = 60.0 N` holds with the recorded pose; tamper = the conversion
  doubled with the recorded pose unchanged; discriminator = the conversion
  check fires (the profile's named class; G05 FB4 heritage).

## 8. Observation seam (the G06 binding to the G05 table)

The G06 seam is the ONLY channel through which the transfer telemetry is
delivered. Its declared vector table IS the pinned G05 32-slot table
(imported from the hash-asserted module; bit-identical slot names, order,
units, frames, sources, alias rows, float32 delivery conversion, availability
law, privileged-forbidden registry, zero undeclared history). G06 declares:

- the PHASE UNIVERSE: approach, attach, load, hold, transfer, attach2,
  load2, hold2, release (the G05 universe was hold/release -- the extension
  is task-owned and disclosed; the pinned G05 seam REFUSES the new phases
  with `timing_unbound`, which the P-class check proves live);
- the G06 projection law for `agg_supported_flag` (P6) during the new
  phases; the hold/release projections of the same samples are bit-identical
  under both interfaces (proved by delivering them through a pinned G05 seam
  instance in the same check);
- the channel flag projection for the four-way recorded mode
  {stick, still, slip, no_contact}: contact = mode != no_contact,
  stick = (mode == stick), slip = (mode == slip); a `still` tick (the
  climb-hovered limb in pressed contact with zero tangential speed) is
  honestly contact=1, stick=0, slip=0.

Timing block: every sample carries t_tick (1..229), t_phase, t_dt_s = 0.005,
t_seconds = tick*dt (window 1e-12), strictly monotone per scenario,
delivered post-solve. Delivery gates keep the G05 refusal family:
undeclared_field, timing_unbound, timing_drift, named_absent_occupied,
privileged_source, nonfinite_value, dim_mismatch.

## 9. Input pins (verified at run time; drift refuses the run)

| pin | path | sha256 |
|---|---|---|
| local_contact_py | contributions/MAT2-M06/local_contact.py | 1cd662b30343011eb4a0a01e461a1e82b00482d0371857c8e42d6bec8f9a28dc |
| m06_test_suite | contributions/MAT2-M06/test_local_contact.py | b832d0dc07c1762a190d4b662ceed2b1b6dd469cbd22343cb39934e90eb08e77 |
| contact_law_json | contributions/MAT2-M06/contact_law.json | 583962c29f18118a478dedb167f2c3667414b86f5cab4ee54763416f1df7e41b |
| m06_experiment_receipt | contributions/MAT2-M06/experiment_receipt.json | 2956dd7aaf3682fc18de9b724ddd8a695011ec74c9a12a5a56744b3d738a9397 |
| trunk_mesh_json | contributions/MAT2-F03/assets/trunk_01_mesh.json | 3b17441764714c5e5e9c7a43c3253b3271a0f508954095e1960a57820cef6ee7 |
| f03_material_state | contributions/MAT2-F03/assets/trunk_01_material_state.json | 91c17a5c59ce79af3dc0e8a6dadb00c92a039075775a0a1de618da12dfca61bd |
| g04_grip_module | contributions/MAT2-G04/grip_contact.py | 0d6375484c350039468b31a2f7db2895d3365412aee52ce98de72b4173d69245 |
| g04_test_suite | contributions/MAT2-G04/test_g04_checks.py | a01b167e4393e2e513ba343f2bc6ba3fdf4d01ee08170f7fe8c3cb1c5c9a0ae1 |
| g05_obs_module | contributions/MAT2-G05/contact_support_obs.py | 3dae0a3805cec86bba8dbae9a6fc563f43cddc98fcd01a693f725e4f31c46bd3 |
| g05_test_suite | contributions/MAT2-G05/test_g05_checks.py | 83ba17604f66fdbe623b71ce481b539862ec39ebf81ee4c8bea2e5af29f9985b |
| g01_feasibility_receipt | E:/ChimeraWork/monkey-coordination/evidence-store/MAT2-G01/numerical/feasibility_receipt.json | 4061d8ec604ddea5dfbdf605f0244874129a69a88d771d4f593c7a927c16be42 |
| grasp_benchmark_md | E:/ChimeraWork/research-data/20260929/benchmark-grasp/GRASP_BENCHMARK.md | d936cebe38b1416dfc417db727ea81396eb8eb9217efed3f05b344db17f71610 |
| friction_sources_md | E:/ChimeraWork/monkey-coordination/g04-friction/FRICTION_SOURCES.md | 336118e929bd0b4fb067db5a448dc2e348fed073007787635549a4cf1cf5868b |
| g04_report | E:/ChimeraWork/monkey-coordination/evidence-store/MAT2-G04/report/REPORT.md | dfca5b5556efe018ca09be4577bf6fbb5df38bb5c9ebc33d15bd18646ba349c8 |
| g05_report | E:/ChimeraWork/monkey-coordination/evidence-store/MAT2-G05/report/REPORT.md | 1e5fcc7f81b5bd7b0ae3b460c72d5ed190510f66db4793c6b2e99756da8c8524 |

## 10. Capture plan (grasp/motion profile; registry row read mode=ro)

The capture replays the CLOSING case `band_mid|n=3` through the declared
schedule. Frames: 10 declared snapshot ticks (one per phase story beat:
attach 4, load 8, hold 20, handover 31, climb 60, mid-flight 120, brake 186,
attach2 193, hold2 208, release 224) at 1 video second per frame; the tick
axis is REAL (motion class: the W06 lesson -- state_or_tick_interval
declares the actual snapshot tick, tick_map declares tick->video-second
mapping, and the replay procedure re-runs the experiments then the
render). Views (task-owned realization, creature absence inventoried never
faked): 'whole-body/trunk relationship' -> trunk + all pads + support-state
labels; 'wrist/digit attachment close-up' -> the relocating channel's
attachment patch at the source facet (the wrist/digit anatomy absence is
the inventoried debt); 'orthogonal view of each loaded interface' ->
orthogonal cameras on the loaded holder interfaces and on the target
facade. Diagnostic layers: attachment patches and endpoint ids
(fixture-scoped pad ids and contact facet ids), contact normals and forces,
support state, declared pad/trunk frame axes; 'tendon paths' layer ABSENT
(inventoried; no tendons exist in this fixture); 'joint/frame axes'
realized as the declared pad/trunk frame axes (no joints exist in this
fixture). Clean view REQUIRED: clean pairs share the exact camera and the
exact physical state; the state hash is identical across every view row
(view toggles preserve the physical state). Full 17-field camera record on
every row. Codec: FFV1 `-level 3 -g 1 -fflags +bitexact` mkv; lossy never
evidence; ffmpeg version recorded. Pixel presence measured per frame
(stills re-measured from the DECODED video by check_capture_pixels.py);
task_id SHORT form (G06) in manifest AND context. visual_acceptance stays
false BY DESIGN: independent visual review remains the Sergeant/Lieutenant
gate (this text-only worker inspects no pictures).

## 11. Regression

The declared upstream suites re-run UNMODIFIED on this exact candidate
revision: M06 `test_local_contact.py`, sealed G04 `test_g04_checks.py`, and
sealed G05 `test_g05_checks.py` (this card binds to all three). Exit 0
required for each; receipt recorded.

## 12. Amendments

(none yet -- amendments after this freeze, both before the experiment runs;
each amendment recorded here with its scope.)
