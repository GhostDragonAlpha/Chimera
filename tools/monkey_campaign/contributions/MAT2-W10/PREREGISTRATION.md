# PREREGISTRATION — MAT2-W10 accept walking in the actual game scene

Frozen BEFORE any implementation file, harness run, measurement or capture
frame of this card exists. This file is committed ALONE (separate-first; the
M03/P04 law). Every emitted receipt refuses any document whose
`preregistration_sha256` does not match these live bytes.

- Card MAT2-W10 (planning id W10, wave 10, slot 2), agent `wk-w10-arrival-1`,
  attempt `e0dd5f03572f4b95b7f5a6013327d906`, attempt workspace
  `E:\ChimeraWork\monkey-coordination\kanban-attempts\MAT2-W10\e0dd5f03572f4b95b7f5a6013327d906`,
  file package `package` (NO_WORKTREES law: pinned file package, no clone, no
  worktree), publication branch `review/MAT2-W10`, PR base `astra/gait-capture`.
- Criteria sha256 `044fd755f9bcf10895e50ef1c569dc584415ab5cce67497848197621cbc1b23d`
  (startup join == registry `kanban.cards[MAT2-W10].criteria_sha256`, re-read
  READ-ONLY (`file:...?mode=ro`) from
  `E:/ChimeraWork/monkey-coordination/agent_slots.sqlite3` at run time;
  mismatch = refusal `criteria_pin_mismatch`. Registry join verified at prereg
  freeze: card state OPEN, criteria equal, profile `walking`/`motion`.)
- done_when (verbatim, registry): "Player can walk, turn and stop in the scene
  on a supported surface; numerical and visual receipts match. Material-first
  addition: Show the existing monkey asset walking under player commands in
  one pinned forest clearing build, with clean and diagnostic views; no
  cosmetic skin over an unrelated qualified body."
- Observation (verbatim, registry): "Walking demo is a product milestone
  before climbing".
- Card task falsifier (verbatim): "Sliding/penetration, unsupported
  propulsion, hidden reset, wrong command response or diagnostic/clean state
  divergence fails."
- Profile: `walking`/`motion` (registry read-only at capture time; G7);
  numerical_evidence_required true; clean_view_required true; diagnostic
  layers ["skeleton", "foot contacts and normals", "support/COM markers",
  "command and tick overlay", "stable 3D labels"]; views ["full-body ground
  overview", "side view of stance/swing", "close-up of foot-ground contact"];
  profile procedure (verbatim): "Replay the frozen start/stop/turn/speed/fall
  sequence; inspect stance and swing over the full declared interval. Use the
  task-owned subset of layers/behaviors. Inventory absent or unresolved
  components explicitly; do not require downstream skills to accept an
  upstream interface. Freeze exact applicable probes and views before
  execution."
- Base: `273d7e592ceec83b272416cf4ce9f4e16a9e3720` = the seeded
  `refs/remotes/origin/review/MAT2-W10` (the publisher-seeded integrated tip:
  the W08 correction merge, W09, G06, everything through revision 1675). The
  file package is pinned to this base by worker_start preparation.
- Composed against CARD_STARTER v5 and the house standards:
  `IMPLEMENTER_CHECKLIST.md` (G1-G9) + `TOOLKIT.md` (P1-P9), cited at the
  candidate commit. Dispatch brief:
  `E:/ChimeraWork/monkey-coordination/gap-analysis/wave-10.md` (MAT2-W10
  section).
- Calculations: this card declares NO new calculation (`calculation_ids` is
  empty in the registry). It INTEGRATES sealed upstream work read-only: C11
  (walking tracking and stability, sealed by W08), C12 (input timing and
  control mapping, sealed by W08), C13 (falls/energy/post-failure behavior,
  sealed by W09). Nothing sealed is recomputed or re-decided.

## 0. The governing frame (what "the scene", "player" and "walking" mean here)

THE CERTIFIED WALKING RUNTIME IS THE FROZEN CERTIFIED LINE — nothing else.
W04 froze the runtime/training contract and issued the certificate; W06
sealed the deploy treatment ALLOW(frozen)/BLOCK(trained); W07 loaded the
frozen line through the certificate machinery with bit-for-bit bundle
identity; W08 commanded THAT certified runtime through the ACTUAL player
command port with a frozen script; W09 wrapped the declared out-of-envelope
supervisor around the same seam. This card adds no policy, no reissue, no
retune: it replays the sealed start/stop/turn/speed/fall sequence at THIS
card's pins and delivers the numerical receipts BESIDE the visual receipts of
the same runs.

- "THE SCENE" is the certified declared scene `cpu-walk-scene/1.0.0`, build
  `cpu-walk-scene-build-N` — the walking scene of record, the only runtime
  with a live certified control path. The product engine has NO live control
  path for the certified policy (W07 N1/N2/N3 carried, never re-opened);
  `PLAYABLE_BUILD.json` stays UNQUALIFIED for native integration and this
  card does not update it (rule: only source-bound integrated runtime
  evidence can; the absent inventory, section 8, names what that requires).
  Claim class stays offline/trace at the 300 Hz tick (TC-11 COST-GAP; no
  real-time claim).
- "PLAYER" is the pinned player command port exactly as W08 consumed it: the
  U01/U03 pinned seam (`InputMapper` -> versioned `CommandRecord` v1 at the
  existing 20 Hz speed/heading boundary, INTERVAL_MS=50, the pinned
  consumer-side expiry contract) over an injected integer-millisecond clock
  into a recording sink. The X02 session controls (Return/Escape/R/Q
  semantics) and U02 follow camera are consumed as declared context where
  cited; the certified scene has no interactive process to attach them to
  (absent inventory, section 8) — the port seam IS the player surface that
  exists, and W08 is its sealed command precedent.
- "WALK, TURN AND STOP" is W08's sealed command script (section 3): start /
  ceiling hold, in-range turns both directions, the seam-max saturating turn,
  the release-decay speed step, and the zero-advance stop. STOP keeps W08's
  sealed plant semantics: the surrogate's bounded minimum advance floor
  (stride floor 0.2) settles the speed into the derived floor band
  [0.2993197278911565, ~0.339577] m/s — the certified zero-advance state,
  declared and carried verbatim, never re-modeled as a zero-speed claim.
- "ON A SUPPORTED SURFACE" is the W09 SUPPORTED definition executed on every
  tick of the declared walk interval: at least one foot contact in the seam
  (observed structural contact floor 4; certificate contact-floor bar >= 2),
  every pad gap > 0, and the W09 supervisor's ledger records ZERO R1/R2
  response events over the whole clean walk arm (the certified line never
  leaves the envelope — W09 P2 re-proven at this card's pins).
- THE MATERIAL-FIRST ADDITION is a DECLARED VISUALIZATION BINDING, not a new
  runtime body. "The existing monkey asset" is declared as the certified
  walking body's own model lineage: the creature-graph
  `model.dynamics.gait_walker` contract (the 14-coordinate free-root
  hindlimb macaque walker derived from the measured Oku macaque data — the
  SAME 10.037998 kg body the certified line certifies), pinned bytes in the
  sealed lane, plus the pinned gait controller constants. Its skeleton is
  posed per-tick by a DECLARED PURE FUNCTION of the certified run's own
  recorded state (section 6), rendered inside ONE pinned forest clearing
  build (section 5), with the profile's clean and diagnostic views.
- "NO COSMETIC SKIN OVER AN UNRELATED QUALIFIED BODY" is executed, not
  asserted: (i) the rendered pose at every frame is a pure function of the
  qualified run's records at that tick (same com path, same per-leg phase,
  same contacts); (ii) the diagnostic views expose the qualified body's own
  telemetry (skeleton, foot contacts and normals, support/COM markers,
  command and tick overlay, stable labels) directly from the records; (iii)
  the FB5 tamper arm proves the binding — posing the asset from a DIFFERENT
  run's records must produce a detectably different frame set. No surface
  mesh unrelated to the qualified body is introduced; the M02 macaque
  FOREARM geometry (humerus/radius/ulna/hand .vtp) is pinned as context and
  DECLARED NOT USED as a walking-body skin (posing forelimb meshes as hind
  legs would fabricate anatomy; no full-body monkey surface mesh exists in
  any pinned lane — absent inventory, section 8).
- Physics charter: commands choose actuator setpoints; the visualization
  WRITES NOTHING. The scene's public stepping API (`step(applied,
  saturation)`) is the only motion path in every arm; the render path
  consumes records only (FB6 proves a state-writing diagnostic render
  diverges and refuses). The W09 supervisor is attached in its sealed role:
  observation monitor over the clean arms (emits nothing on the certified
  line), declared response owner on the replayed unsupported probe arm.
- The no-reissue law: the EXISTING certificate is deployed; nothing is
  re-issued, re-certified or amended; no trained bundle is loaded (the gate
  BLOCKs them; W07's executed discrimination is pinned and carried).

## 1. Input pins (verified byte-exact at attempt start; drift = refusal `input_pin_mismatch` / `input_pin_missing`)

Store pins (evidence-store `E:/ChimeraWork/monkey-coordination/evidence-store/`):
- `MAT2-W04/numerical/w04_certificate.json` `07f05bfa982e066ae67413b04e3367c5ad7570830e99fc32edcb86cbe8d87598`
- `MAT2-W04/numerical/w04_freeze_manifest.json` `be632ffc85865515285f3d622a09882a3180a43101027914f1ed3408496f5d29`
- `MAT2-U01/numerical/qualification_receipt.json` `94887cc14ba6d2fc7a76c04949d5015cbfada899a817c3acb497e5d53a7a0c61`
- `MAT2-W07/numerical/native_load_receipt.json` `4f5aac081a3a07fd56733d84ac3069950b00309e54f6402e78ebd22c55e490e9`
- `MAT2-W07/numerical/checks_receipt.json` `f599720bbcd06e4888d933d11a7e48f29430635189acf79bd79ad7305559d342`
- `MAT2-W08/numerical/checks_receipt.json` `cd9998ab612b0e320b657a196d672e668199bb92188527d887aafeb321014c37`
- `MAT2-W09/numerical/out_of_envelope_receipt.json` `0880a18a46b99e9463cde8f64fafc6daff82a9b78f04ea5e2960abef963cb4c7`
- `MAT2-W09/numerical/checks_receipt.json` `e4cd94ae5c77a7dc9a5ecfba0e02ad4ae100ebabf1995132bbe9f41a3c2b4430`
- `MAT2-W09/numerical/falsifier_receipt.json` `3a61cdbf43f7b11b4b284c7be969c5f0a36208556942f0832f1022fe87b1204c`
- `MAT2-W09/numerical/input_pins.final.json` (the W09 pin table; re-verified
  at this attempt's start; the four runner-scratch paths inside it are
  consumed through their BASE-BLOB equivalents below, which carried equal
  shas at verification time)
- `MAT2-G07/verdict_ref/PREREGISTRATION.md` `1e55df6da88dbb9fdc3c296b2965042b0a6828b0d6387a2c9eb8bb53f7bb87df`
- `MAT2-G07/numerical/experiment_receipt.json` `c539617b098190918187d9a7dcbb0a5e33a85998adaa58f6b781703bbdeb88f8`

Base-blob pins (read from the shared repository's Git object database at the
package base `273d7e592ceec83b272416cf4ce9f4e16a9e3720` through the DECLARED
read-only `git cat-file`/`git show` access; the blob identities were verified
at prereg freeze):
- `tools/monkey_campaign/contributions/MAT2-U01/reconcile/pinned_seam/tools/monkey_campaign/product/input_mapper.py` `7a36a45ead6637d9ba5659ea43b54a6b424803c8e57d02720ac970b42cfe6b44`
- `tools/monkey_campaign/contributions/MAT2-U01/reconcile/pinned_seam/tools/monkey_campaign/product/input_mapper_tests.py` `95f44e90998f9728802ff5f7cb8628f18f2026bef1fb2c4de681e5253381216e`
- `tools/monkey_campaign/contributions/MAT2-U01/reconcile/pinned_seam/tools/science_funnel/typeb_export/command_record.py` `6771175933ad20ac6d20c360df96f6a9729a56deb31c58a13be5e76e1cc4355e`
- (the U03 `pinned_seam` copies of the same two modules carried the SAME
  shas at the base — one lineage, asserted at run time)
- `tools/monkey_campaign/visual_capture.py` `5ee55d5ab52beb05ffc33e9b66858f94b706cb22c290786db4a79ab344a4ff05`
- `tools/monkey_campaign/contributions/MAT2-W05/receipts/deploy_check_receipt.json` `766a7cbe6a2ccd67c739d82af5b32e859ee4bc3f3a558715fafc63dbab0ae635`
- `tools/monkey_campaign/contributions/MAT2-W06/receipts/evaluation_summary.json` `a1af58baf15edd7ac595b5bb4571e13ed44780f77faf5a761355140f456b075a`
- `tools/monkey_campaign/contributions/MAT2-W07/run_native_load.py` `780dde4e0ea9fa0d6ecab41a42cbac85f73192d552aceef7fd2cb8ff4d75f766`
- `tools/monkey_campaign/contributions/MAT2-W08/PREREGISTRATION.md` `00a04e08411ed079aee9e0ef43f9221c69abc84612f66311e4db4822f6c8412a`
  (THE FROZEN COMMAND SCRIPT AUTHORITY: its section 4.1 script, 4.2 adapter
  law and 4.4 wrong-command probe are replayed VERBATIM; the full 64-hex pin
  lives in `verify_inputs.py` PINS and is re-verified every run)
- `tools/monkey_campaign/contributions/MAT2-W08/receipts/command_verification_receipt.json` `bb9e014b160062d486002745571fd4485a50431cfdbc25038ebb9bed1171f787`
- `tools/monkey_campaign/contributions/MAT2-W09/PREREGISTRATION.md` `6a3e0f6f5e0a0d7cbad595e0d16285556608b93fa77ef77dc59c30ae962f9d7b`
  (THE DECLARED UNSUPPORTED PROBE AUTHORITY: its section 3 A1 arm is
  replayed VERBATIM as the fall sequence)
- `tools/monkey_campaign/contributions/MAT2-F02/pins/terrain_bundle.json` `446ed3fbd0f50205c61a7233ceca289bfc3316f76dfc672fec307b20d8305d52`
- `tools/monkey_campaign/contributions/MAT2-F02/pins/terrain_query.py` `b1e244b8843671afc29af530c4725bf812ffd5f8967130f0202792aeb7a8cce1`
- `tools/monkey_campaign/contributions/MAT2-F02/pins/terrain_bundle.py` `c6ada25a1b6192aa86add8b09bc19161c0cd81e3fb3d4bd267492660c0be8f2e`
- `tools/monkey_campaign/contributions/MAT2-F02/pins/clearing_recipe.py` `ab800d2257655118296519b606c77ddc7116f524ae0c2e6a0bab3b38473892dc`
- `tools/monkey_campaign/contributions/MAT2-F02/pins/clearing_declaration.json` `18dd2ff65410cd1cf184a7a8df61c7503a6ce15083f30159e727e9a8117bfbc1`
- `tools/monkey_campaign/contributions/MAT2-F02/pins/trunk_declaration.json` `94ff906ec5e8b8388e4de318aa3321bad9c791fbb168e8234c371ed1d327e3f1`
- `tools/monkey_campaign/contributions/MAT2-F02/pins/f01_implementation.py` `50e191cfc6f592fd9919534c8986c049939a4e88c4922e135f383bbf06e693af`
- `tools/monkey_campaign/contributions/MAT2-F03/assets/trunk_01_mesh.json` `3b17441764714c5e5e9c7a43c3253b3271a0f508954095e1960a57820cef6ee7`
- `tools/monkey_campaign/contributions/MAT2-M06/local_contact.py` `1cd662b30343011eb4a0a01e461a1e82b00482d0371857c8e42d6bec8f9a28dc`
- `tools/monkey_campaign/contributions/MAT2-M06/contact_law.json` `583962c29f18118a478dedb167f2c3667414b86f5cab4ee54763416f1df7e41b`
- `tools/monkey_campaign/contributions/MAT2-F04/implementation.py` `5c398d22b4259d9e4c89ca3a7900610d629e318ac13b57681cbc7c617619e083`
  (the capture/state-binding/camera-record precedent consumed as PATTERN
  source, never forked silently; consumed read-only)
- `tools/monkey_campaign/contributions/MAT2-F04/evidence/camera_manifest.json` `79cf207b8b53f07ef2f5ff8fa42133144feeccf75f7b2b0fd4cfe5fb0ce09b3a`
- `tools/monkey_campaign/contributions/MAT2-F01/evidence/pins_materialized/gait_controller.hpp` (sha recorded in
  `verify_inputs.py` PINS; the pinned native walker constants used as the
  declared geometry fallback under the section 6 refusal law)
- `tools/monkey_campaign/contributions/MAT2-B07/adoption_record.json` `638884569ac106cb7ed738381e804e4f936877f05fd572a5763064cdcb711a0a`
- `tools/monkey_campaign/contributions/MAT2-M02/data/macaque_arm/monkeyArm_current.osim` `4148aee2c8dda1dcb0918496ad7c5e1adcf4ebabde0a68a3e0dc67faec67b895`
  and the seven `Geometry/*.vtp` files (shas in `verify_inputs.py` PINS;
  pinned as CONTEXT, declared NOT USED as a skin, section 0)
- `tools/monkey_campaign/contributions/MAT2-M12/capture_manifest.json` `0ea48c70af67b9336a3b95ca03a5a6ad0ccdad7a0d80db1e77c6dffff8139d40`

Sealed lane machinery (`E:/ChimeraWork/pass3-integ/repo`; consumed read-only,
pinned bytes, the identical 15-file table W07/W08/W09 verified — full
64-hex values live in `verify_inputs.py` PINS and are re-verified every run):
`tools/policy_compat/` `__init__.py`, `__main__.py`, `certificate.py`,
`engine_cert.py`, `injections.py`, `runner.py`, `scene_cpu.py`,
`snapshot_api.py`; `tools/science_funnel/typeb_export/` `infer_numpy.py`,
`observation_schema.py`, `policy_manifest.py`; validation
`typeb_p3_20260921/policy_manifest.json`, `typeb_p3_20260921/dummy_actor.npz`,
`typeb_p3_20260921/trace_slice_wave38.json`,
`upgrade_gate_20260920/receipt.json`. PLUS this card's added lane pin:
- `tools/creature_graph/data/authored/project_program.json`
  `3e5182f5a8bd85995f3dd0dac1ae24a27cdc0a9539e4da9ec0aef17018b1555c`
  (THE EXISTING MONKEY ASSET BYTES: the `model.dynamics.gait_walker` record
  with the declared 14-coordinate contract, per-joint tables, zero map and
  contact points — the qualified body's own model)

Ingestion-spike honesty records (coordination store; the same two W07/W09
pinned): `ingestion-spike/INGESTION_SPIKE.md`,
`ingestion-spike/w2-engine-up/ENGINE_UP_RECEIPT.md`.

Registry: criteria hash and the `walking`/`motion` profile read READ-ONLY at
run time (G7). A missing required profile key = refusal
`registry_profile_missing_key`.

## 2. The frozen protocol (order is law)

1. Verify every section-1 pin; re-read the registry READ-ONLY and require the
   criteria hash and the profile identity. Any drift is a named refusal
   BEFORE anything runs.
2. Pin-extract the machinery tree AND the base-blob seam tree under a
   slot-scratch directory and import ONLY pinned bytes (zero upstream files
   modified; the NO_WORKTREES source-access declaration).
3. Re-validate the pinned W04 certificate (machinery validator; the only
   authority): zero violations, else refusal `certificate_validator_violation`.
4. Build the deployment request from the certificate's OWN relation;
   `check_deploy` must return ALLOW BEFORE any load, else refusal
   `deploy_gate_sanity`.
5. Load the bundle through the FROZEN loader and require bit-for-bit identity
   (manifest_hash, weights, architecture, activation, clip), else refusal
   `load_identity_mismatch`. Verify build N identity (params sha, scene
   module sha, timestep 1/300 s), else refusal `build_identity_mismatch`.
6. Run the pinned U01 port module's own import identity, then execute the
   FROZEN INPUT SCRIPT (W08 prereg 4.1, pinned) through the pinned
   `InputMapper` over an injected integer-millisecond clock into a recording
   sink; assert the seam laws on the emitted records (W08 P2 claims,
   re-executed).
7. Project each record through the FROZEN ADAPTER LAW (W08 prereg 4.2,
   pinned) and execute the certified scene OPEN-LOOP
   (`scene.step(applied, saturation)` per physics tick, ZOH at the tick
   boundary), collecting per-tick records, with the W09 supervisor attached
   in its sealed observation role. Arms: R1 the clean commanded walk
   (horizon 10500 ticks), R2 an identical re-execution of R1 (the
   determinism zero-control), R3 the wrong-command variant (W08 prereg 4.4).
   Every run is a full re-execution from tick 0 — no snapshot injection, no
   state reuse.
8. Replay the DECLARED UNSUPPORTED PROBE (W09 prereg section 3 A1, pinned)
   verbatim at this card's pins as arm R4 (the fall sequence): the sealed
   algebra re-executed, the R1/R2 responses owned by the supervisor exactly
   as sealed, receipt compared against W09's pinned receipt values; any
   drift = refusal `w09_replay_drift` (investigated and disclosed, never
   silently accepted).
9. Render the visualization (section 5/6) from R1's and R4's OWN recorded
   records inside the pinned clearing build; the render path is
   records-only.
10. Evaluate the frozen predictions (section 4) and the falsifier detectors
    (section 7); emit the receipts. Any failed prediction is a named refusal
    (`prediction_failed:<name>`), never a silent pass.

## 3. The frozen sequence (pinned authorities; nothing re-scripted)

- The start/stop/turn/speed sequence IS W08's frozen input script (W08
  prereg 4.1 at the pinned bytes): W press at 1000 ms held through 18025;
  the three steering windows (+0.8, -0.8, saturating +1.6) at 12000..16450;
  the W release decay tail at 18025; live-zero S at 20000..22975; scene
  horizon 10500 ticks; the declared IDLE priming projection for ticks
  0..300, excluded from tracking claims, every stability bar from tick 0.
- The fall sequence IS W09's declared unsupported probe A1 (W09 prereg
  section 3 at the pinned bytes): seed 20260920, both lifts to bounds_hi
  1.8, the exact alignment offsets `off_r = +0.25`,
  `off_l = -0.057511737089201875`, stride channels at the manifest center
  outside responses; the supervisor owns R1 (stride channels to the
  certified minimum 0.2) and R2 (neutral latch at the declared fall) exactly
  as sealed.
- The wrong-command probe IS W08's declared R3 script (W08 prereg 4.4 at the
  pinned bytes): identical prefix through tick 5429, the held wrong W from
  tick 5430.
- STANCE/SWING INSPECTION (profile procedure) is executed on R1 over the
  full declared interval: the per-leg phase from the records marks stance
  (pad in contact) and swing (pad lifted inside the declared clearance law)
  on every tick; the phase_state_counts and per-phase contact statistics are
  keyed per phase (G6 `phase_metric`) and rendered in the receipt; the side
  view samples lie inside declared stance and swing windows (section 6).

## 4. Frozen predictions (registered BEFORE any run; disclosed either way)

All bounds are re-derived live from the pinned constants exactly as W08/W09
derived them; the values quoted here are the pinned-constant evaluations
recorded at freeze.

- P1_gate_load_allow: the certificate path of section 2 steps 3-5 is ALLOW
  with bit-for-bit bundle identity (manifest_hash `9ca7e976dfb0dedd...`,
  weights `5fb2b785...`), build N, params sha `3e770bef...` (full values in
  `verify_inputs.py`), identical to the sealed W07/W08 loads.
- P2_port_seam_laws: W08's P2 claim set re-executed (record_version 1;
  v_forward in [0, 0.763625]; |yaw_rate| <= 1.6; consecutive issued ticks
  inside a continuous segment differ by EXACTLY 15 physics ticks; held keys
  re-issue every interval; release-decay exact zero by released_ms + 100;
  idle emits NOTHING; the sink log contains ONLY emit(CommandRecord)
  entries).
- P3_projection_within_bounds: W08's P3 claim set re-executed (all applied
  vectors within manifest bounds; every clipped channel named; the
  zero-advance stride floor 0.2 saturation on channels 1,5 at every
  zero/floor tick; the seam-max yaw projection to +-0.25 with channels 0,4
  saturated and achieved yaw +-1.0).
- P4_start_tracking: W08's P4 claim re-executed: onset within 15 ticks
  (predicted 1), monotone rise below the derived ceiling band low edge, and
  the two-sided comparison bound at the segment end (tick 5415):
  v(5415) in [0.726509, 0.8038157894736843] m/s,
  |v(5415) - 0.763625| <= 0.040190790 m/s; measured band-entry tick recorded
  informationally (never claimed as a bound).
- P5_turn_exactness: W08's P5 claim re-executed: in-range turns track the
  commanded yaw within 1e-6 rad/s (float32 routing dust scale recorded);
  seam-max achieves +1.0 rad/s within the same bound with saturation NAMED
  on channels 0,4 at every tick (declared residual 0.6).
- P6_speed_step_decay: W08's P6 claim re-executed: strictly decreasing speed
  across the one-block mid sample; exact zero demand by the port deadline;
  plant at/below the pre-release speed.
- P7_stop_floor_settle: W08's P7 claim re-executed: after the zero-advance
  lands, the speed strictly decreases while above the floor band top and can
  never cross below the floor band low edge 0.3142857142857143; the settle
  window end (tick 9031) v in [0.2993197278911565, ~0.339577]; the floor
  carried as the certified zero-advance semantics (never a zero-speed claim).
- P8_stability_bars: at EVERY tick of R1 (and R2/R3/R4): |v| <=
  2.977443609022557 m/s; contact_count >= 2 (observed structural floor 4
  recorded); no NaN/Inf; intervention_reason == "none"; x never decreases;
  every pad gap > 0 (no penetration below the pad plane); com_x advances
  exactly by dt*v per tick.
- P9_wrong_command_response_MUST_FIRE: R1/R3 state hashes identical through
  tick 5430, diverge from tick 5431; at tick 5999 the physical responses
  separate beyond the derived two-sided brackets (recomputed live from the
  pinned constants and the shared prefix speed); R1 vs R2 bit-identical over
  the whole horizon.
- P10_supported_surface (THIS CARD): every tick of R1's declared walk
  interval [301..9031] is SUPPORTED (at least one foot contact flag;
  observed floor 4 recorded) and the W09 supervisor's observation ledger
  over R1 contains ZERO response events (the certified line never leaves
  the envelope; the false-positive control of W09 P2 re-executed at this
  card's pins). Zero unsupported ticks is the PASS shape; any unsupported
  tick is a named refusal `walk_unsupported_tick:<tick>` (and would
  falsify the certified-line claim).
- P11_no_sliding_no_penetration (THIS CARD): R1's com_x(t+1) - com_x(t) ==
  dt*v(t) exactly at every tick (records from the solved state); during the
  straight segments the lateral coordinate is constant exactly (heading
  unmoved, no crab drift); every pad gap > 0 at every tick; no contact
  record carries a negative gap (no interpenetration event).
- P12_w09_replay_faithful (THIS CARD): R4 reproduces W09's sealed A1
  receipt values EXACT at the pinned seed (the first unsupported interval
  open [30, 119], length 90; the natural fall declaration at tick 119 with
  trips [1, 1]; the R1 applied strides exactly 0.2 on every pre-fall
  unsupported tick with a_com = 0.11000000000000001 m/s^2; both foot force
  channels exactly 0.0 on every unsupported tick; the velocity recursion
  identity within 1e-5 m/s; never_frozen true). Any drift =
  `w09_replay_drift`.
- P13_visual_binding (THIS CARD): (a) every rendered frame records the state
  hash of the run record at its tick; each diagnostic/clean view pair is
  state-hash IDENTICAL (the view toggle writes no state — G8's identical
  composite state hash law); (b) the tampered-binding control (FB5) produces
  a detectably different frame set; (c) the capture manifest's
  state_binding binds every capture row to the committed per-tick trace
  (F04 precedent).

## 5. The pinned forest clearing build (ONE build, declared)

The build is composed ONLY of pinned bytes; the composed manifest
(`clearing_build_manifest.json`) records every part sha and the composed
build identity at run time. Parts: F02's tied terrain asset (render arrays =
query triangulation), terrain query surface, terrain bundle module/validator,
clearing recipe and clearing declaration, trunk declaration, F03's pinned
trunk mesh asset, the F01 render law, M06's shared contact path and contact
law declarations (constants cited: ground mu 0.9/0.65 thickness 0.002;
trunk mu 0.6/0.6; g 9.81; the M06 law slop/margin/beta/restitution/CCD
constants). ONE global frame map (F02's declared proper rotation, det=+1;
clearing (x, y up, z) -> contact (x, -z, y); gravity -Y in clearing). The
F04 measured seam facts are carried: the trunk base ring touches the ground
plane at exactly 0.0 m and a solve containing BOTH pinned static parts is
REFUSED by the pinned law (`nonfinite_state`) — the visualization therefore
instantiates exactly the static parts it touches (the ground; the trunk is
rendered from its pinned mesh as scene furniture and is never added to a
dynamic solve), the composition limitation inventoried (F04 A3 heritage),
never silently repaired.

The walker placement map (declared, pure): the walk path starts at the
clearing spawn and proceeds along the declared heading; the body's clearing
position at tick t is spawn + R(yaw(t)) * (com_x(t), 0, com_z(t)) with the
scene's planar com mapped to the clearing ground through the declared
ground-height query at the mapped x/z (the surrogate walks on flat declared
ground; the mapped ground height is recorded per frame). The declared body
scale is the gait contract's own (10.037998 kg body; the contract's own
contact geometry), placed at the P06-declared clearance band; no scaling is
invented (any missing geometric constant = refusal `asset_geometry_absent`).

## 6. The visualization pose law (pure function of the run's records)

For a run record at tick t: base position and heading from section 5's map;
per-leg phase from the record's own phase channels (the declared 1/213
recursion, recovered from the records); joint angles (hip, knee, ankle, MP
per leg) = the PINNED 21-node tables evaluated at the recorded phase with
the pinned zero map applied (the contract's own coordinate convention); foot
contact markers and normals at the contract's declared contact points
(heel [-0.012, 0, 0], mp head [0.074, 0, 0], radius 0.004 per foot) with
contact/force state from the records; the support/COM marker at the recorded
com with the recorded velocity vector; the command/tick overlay reads the
applied vector and tick from the records. ALL geometric constants come from
the pinned contract bytes (and the pinned gait controller constants as the
declared fallback); an absent constant is refusal `asset_geometry_absent`,
never an invented number. The mapping is float64, deterministic, seedless.

Skeleton rendering: the declared hindlimb segments and foot bodies are
drawn from the pinned constants through the F01 render law into the pinned
clearing (the same render/camera tooling F04 sealed; no new render law).
Diagnostic layers (profile): skeleton; foot contacts and normals;
support/COM markers; command and tick overlay; stable 3D labels (tick and
command text rendered as stable screen-space labels with recorded anchor
projections). Clean views draw the scene without the diagnostic overlay —
the SAME state, no state write (FB6 arm proves the divergence detector).

HONESTY LABEL (recorded in every capture manifest and the report): RENDERED
FIXTURE of the certified run's own per-tick telemetry inside the pinned
clearing; the visual body is the DECLARED gait-walker visualization of the
qualified hind-pad-surrogate state; the adopted B07 assembly is NOT
runtime-qualified (TC-7/TC-8 open) and is not presented as a runtime body;
visual_acceptance stays false BY DESIGN (independent visual review remains
the Sergeant's).

## 7. Falsifier arms (G1: clean control FIRST, named guard, receipt row; every arm can fail)

| arm | clean control | tampered | detector | discriminator |
|---|---|---|---|---|
| FB1_hidden_reset | R1 detectors green (draw chain, phase recursion, velocity identity, zero violations) | tick 60 snapshot restored at tick 100 inside R1's produced windows | the fresh-seed draw chain breaks at the restore tick; phase recursion residual; velocity identity residual | W09's FB1 form at this card's pins |
| FB2_unsupported_propulsion | R4's own R1 responses: applied strides EXACTLY 0.2 on every pre-fall unsupported tick | ceiling strides (manifest bounds_hi) injected during R4's declared unsupported window | applied-stride deviation from the sealed R1 law; velocity identity residual > 1e-5 m/s | the propulsion class: motion beyond the declared law without support |
| FB3_wrong_command | R1/R2 bit-identical (zero-control) | R3 (the pinned wrong-key script) | state-hash divergence at 5431; physical separation beyond the derived brackets at 5999 | W08's P9 form |
| FB4_sliding | P11 exact com identity on R1 | com_x advanced by 2x dt*v at one declared tick | the com identity residual fires | the sliding class: position moving beyond the solved velocity |
| FB5_skin_unrelated | the R1-bound frame set (binding law) | the SAME tick's frame posed from R4's records | the rendered frame sha differs from the bound frame at the same tick (detector MUST fire); the clean pair is hash-identical | the cosmetic-skin class: a visual not bound to the qualified state |
| FB6_diagnostic_state_divergence | each diagnostic/clean pair state-hash identical | a scratch render path that writes scene state during the diagnostic toggle | the state hash changes across the toggle (MUST fire) | the divergence class the profile names |

Guard naming: `w10_fb<n>_premature`. A non-biting arm, or an arm that fires
on its clean control, fails the whole build.

## 8. Capture plan (profile check BEFORE capture; G7/G8/G4)

- The registry profile is read READ-ONLY (`file:...?mode=ro`) BEFORE any
  capture; required keys asserted; `CANONICAL_LAYERS` tripwire present;
  `task_id` SHORT form (`W10`) in manifest AND context; the registry profile
  snapshot + provenance written to evidence; `criteria_sha256` identical
  across dispatch / registry / prereg / checks identity.
- Views (profile verbatim, each x diagnostic/clean): full-body ground
  overview; side view of stance/swing (the side-view bookends sample one
  declared stance tick and one declared swing tick of R1, keyed per phase,
  G6); close-up of foot-ground contact. `state_or_tick_interval` carries the
  real tick axis; one tick = 1/300 s; the walk arm's tick interval and the
  fall arm's declared window are recorded.
- Camera record: ALL 17 registry fields per view (F04 camera-manifest
  schema); `camera_motion_or_bookmark_sequence` records the declared
  bookmark samples; `visibility_layers` and `label_ids` name the diagnostic
  layers actually drawn; `occlusion_or_xray_mode` recorded.
- Codec: FFV1 `-level 3 -g 1 -fflags +bitexact` mkv (the codec standard;
  lossy codecs never evidence); the ffmpeg version string recorded; frames
  are the determinism unit; decode == committed stills at independently
  recomputable indices under identity ONLY (G4); ONE gate-bound capture
  identity per arm (video sha256 == manifest == context == determinism
  record; image sets bind by ordered concat sha + per-frame hashes, G8).
- The diagnostic/clean pairs are the state-identity proof (P13); the
  capture's state_binding binds every capture row to the committed per-tick
  trace of the SAME run.

## 9. Named checks, gates and refusal codes

- Suite: `test_w10_walking_demo.py` (unittest; zero skips by design;
  KNOWN_SKIPS: none). Receipt-semantics changes land TOGETHER with the named
  check that asserts them.
- The 12 card-kit gates run through the runner on the card directory
  (py_compile, ast checks, receipt schema, named-check suite, prereg
  exists, gitattributes text flag, CRLF byte stability, job-JSON
  forward-slash, G10 pin-vs-disk, G11 agent trailer, G12 skip accounting);
  red gates block submission.
- Refusal codes (frozen): `criteria_pin_mismatch`, `input_pin_missing`,
  `input_pin_drift`, `certificate_validator_violation`, `deploy_gate_sanity`,
  `load_identity_mismatch`, `build_identity_mismatch`, `port_import_identity`,
  `prediction_failed:<name>`, `walk_unsupported_tick:<tick>`,
  `w09_replay_drift`, `asset_geometry_absent`, `registry_profile_missing_key`,
  `profile_read_failure`, `capture_codec_violation`,
  `vacuous_comparison:<name>`, `w10_fb<n>_premature`.
- The report is GENERATED from the bound receipts (zero hand-transcribed
  numbers; `lint_report_numbers.py` exits 0 with the selftest proving the
  detectors); receipts report MEASURED values BESIDE nominals with deviation
  flags; no format placeholders.

## 10. Honest limitations and absent inventory (declared, never imputed)

- The certified execution vehicle is the DECLARED SURROGATE scene; the
  product engine has no live control path for the certified policy (W07
  N1/N2/N3 carried). "The scene" on this card is the walking scene of record
  the certificate binds; the native engine integration and
  `PLAYABLE_BUILD.json` qualification stay downstream work with their named
  prerequisites (an engine binary bound to the certified line; a live
  control path), not produced here.
- No full-body monkey SURFACE mesh exists in any pinned lane. The
  visualization renders the declared gait-walker skeleton (the qualified
  body's own model) — not a skinned cosmetic mesh; the M02 macaque forearm
  geometry is pinned context and is NOT used as a walking-body skin.
  TC-7 (body domain) stays OPEN with the adopted assembly as binding target;
  TC-8 (ports) stays 0/8; nothing here re-issues the certificate or claims
  the assembly as a runtime body.
- Real-time 300 Hz interactive execution is NOT claimed (TC-11 COST-GAP);
  the claim class is offline/trace qualification at the 300 Hz tick.
- The trunk is rendered furniture in the clearing build and never enters a
  dynamic solve together with the ground (the F04 measured both-pinned
  refusal); the walker's support surface is the declared ground plane
  (F02's tied terrain asset) — this composition limitation is carried from
  F04 verbatim.
- No impact/landing accounting exists beyond W09's sealed records (no
  vertical body dynamics in the surrogate); the fall arm replays the sealed
  record-space behavior with the supervisor's declared responses.
- This text-only worker will inspect no pictures: pixel claims stay MEASURED
  decode checks and image review is owned by the Sergeant/Lieutenant.
