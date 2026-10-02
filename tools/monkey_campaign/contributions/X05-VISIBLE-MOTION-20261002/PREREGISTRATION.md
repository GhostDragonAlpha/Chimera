# PREREGISTRATION (DRAFT) — card MAT2-X05 / lane x05: visible motion in the clean views on the certified line

STATUS: DRAFT for Lieutenant commit (separate-first law, M03/P04). These bytes
are NOT frozen until the Lieutenant commits them ALONE on the `e814433c`
lineage through the publication owner and hands back the commit sha (the pin).
Phase B (the gated implementation and capture) starts ONLY after that handoff.
Every receipt of this card will embed `preregistration_sha256` of the COMMITTED
bytes and refuse any mismatch.

- Card MAT2-X05 (planning id X05), worker `wk-x05-prereg` (Captain Order #9,
  item 1: "X05 DISPATCHED (agent_99122fb3, prereg-first): the visible-motion
  card on the X04-merged tip e814433c"). This lane is prereg-first: this draft
  is the chain-stop deliverable; NO implementation file, harness run,
  measurement or capture frame of this card exists yet.
- Write scope: the NEW lane dir `E:\ChimeraWork\monkey-coordination\x05\`;
  the Phase B contribution dir
  `tools/monkey_campaign/contributions/MAT2-X05/` in a pinned file package.
- NO_WORKTREES law: pinned file packages only; CPU runs only through
  `python -B E:/PythonChimera/tools/monkey_campaign/task_package.py seal|run`;
  no Git clone, worktree, ref or index mutation by this lane (the single named
  ref refresh `refs/remotes/origin/astra/gait-capture` 76df495d -> e814433c
  was the documented publisher-refresh read; recorded in the lane EVIDENCE).
- X04 IS PRESERVED UNCHANGED: the X04 card bytes at the base tip are pinned by
  sha256 (section 1) and are NOT re-claimed, re-opened or re-gated. X04's
  P1-P12 verdicts stand on X04's own committed bytes. This card does not
  modify one byte of any other contribution.

## 0. The governing frame (what X05 adds and what it must never fake)

THE CERTIFIED LINE IS FROZEN — scene `cpu-walk-scene/1.0.0`, build
`cpu-walk-scene-build-N`, SEED 20260920, 300 Hz, the W10 records-only
renderer and the pinned pose law. X05 adds NO policy, NO reissue, NO retune,
NO runtime change. X05 adds a DECLARED PRESENTATION LAYER in its own
contribution, carrying the Captain's ruling ("Use runtime-derived velocity
cues and stationary world landmarks; any stride changes must follow contact
mechanics") into three scoped items:

- (a) THE VELOCITY INDICATOR IN THE CLEAN VIEWS: a rendered instrument,
  derived at render time from the committed rows' measured state
  (`com_v_m_s` of the row at the presented frame's consumed tick), honestly
  labeled AS AN INSTRUMENT. It is an on-screen gauge — the manifest rows and
  every report say so. It is NEVER a claim that the monkey's body displays
  speed. The body carries no velocity-bearing visual feature (absent
  inventory A4).
- (b) STATIONARY WORLD LANDMARKS: a declared landmark set (trees, rocks) at
  fixed clearing coordinates, rasterized through the SAME pinned F04 camera
  and depth buffer as the body. The camera is body-anchored (the sealed
  translation-invariance mechanism), so the LANDMARKS' apparent motion is the
  velocity signal: their rendered per-frame displacement is exactly the
  projection of the body's committed per-frame travel. This directly fixes
  the WK-LATENCY-20261002 finding that the clean follow view was STRUCTURALLY
  blind to speed (whole-frame diff 0 on every pair at both brake depths,
  REPORT_a12_structural_invisibility.md).
- (c) STRIDE-VELOCITY COUPLING: DETERMINED ABSENT — see the determination
  below. X05 records this honestly and ships (a)+(b) only. A cosmetic stride
  change keyed to velocity is FORBIDDEN: it would be a second pose source
  (X04 P4 law) and exactly the "overlay masquerading as stride" the Captain
  excluded.

### The coupling determination (from the sealed contact/gait records; re-derived at run, never hand-copied)

Inputs: the SEALED attempt-12 driver records of WK-LATENCY-20261002
(job `ca111cdc917e420eb78c41339d88c41b`, pinned in section 1), which carry
per-tick `phase_left`, `phase_right`, `com_v_m_s`, `com_x_m` for BOTH arms of
the brake pairs over the declared window. Derived, at design time and again
at run from the pinned bytes:

- The gait phases are IDENTICAL between the brake arm and the control arm in
  42/42 window frames (both depths, all 21 presented ticks of P01 SHORT and
  P02 LONG).
- The velocity state GENUINELY diverged in the same frames: `com_v_m_s`
  0.746530 -> 0.694329 (SHORT) / 0.623221 (LONG) vs held 0.747357; com_v
  differs between arms in 40/42 frames; com_x travel 0.7004 m (SHORT) /
  0.6787 m (LONG) vs 0.7472 m control.
- Therefore: the certified scene's phase oscillators do not consume the
  measured speed in this regime. There is NO contact-record basis for a
  stride-velocity coupling: any rendered stride change keyed to velocity
  would require a phase source OTHER than the committed row's recorded phase
  (the pinned pose law `pose_at` input), which is the forbidden second pose
  source.
- Disposition: coupling is DECLARED ABSENT on this card (absent inventory
  A1). The named follow-up — a certified-line change in which the scene's
  phase law consumes the measured speed — is a RUNTIME change, outside this
  card's no-runtime-change scope; it requires its own prereg and card. It is
  recorded here so the absence is a routed requirement, not a silent gap.

### Why this is not an X04 clean-view regression

X04's P7 zero-diagnostic law binds X04's frozen bytes: X04's CLEAN frames
carry zero X04-layer pixels, and that law is honored on X04's own artifacts
forever — it is not re-opened here. X05 is the carrier the Captain selected:
X05's OWN prereg declares the NEW clean-view objects (the instrument and the
landmarks) with their own palettes, floors and classes, and X05's clean law
preserves P7's substance: zero pixels of any X04 DIAGNOSTIC layer palette on
every X05 clean frame (X-P7). The X04 diagnostic layers stay diagnostic-only.

## 1. Input pins (byte-verified at draft time from the base tip `e814433c`; drift = refusal `input_pin_mismatch` / `input_pin_missing`)

Base build identity (verified 2026-10-02 from the shared repository's object
database, read-only; the named remote ref was refreshed 76df495d -> e814433c
after `git ls-remote` confirmed the remote tip):

- `e814433c8dd18d2fe9abf467b563afc440efc815` == `refs/heads/astra/gait-capture`
  on the remote == `refs/remotes/origin/astra/gait-capture` after refresh =
  "MAT2-X04 ... (PR #320 ...)", a MERGE with parents `76df495d1d5f13c9e30c6b9bbd56a7680e98f57e`
  (the F06 tip, PR #318) and `97c5a3b10bc311fa67e63c679f7ad2029e8459b2`
  (the X04 prereg+impl union line). Ancestry verified by `git log`/`git show -s --format=%P`.

Base-blob pins (content sha256 at `e814433c`, read-only `git cat-file blob`
through the DECLARED read-only access in `source_access.py`):

- `tools/monkey_campaign/contributions/MAT2-X04/PREREGISTRATION.md`
  `2e62487fa4569990c1e569b6829295fa6a7f498b0d07a12c97f1ebbcac56d418`
  (the X04 frozen prereg: P1-P12, FB1-FB5, the three body-anchored views,
  the window law — PRESERVED UNCHANGED; this card cites, never re-claims)
- `tools/monkey_campaign/contributions/MAT2-X04/presentation_harness.py`
  `6ab579a41bc92348b89fedb9def6d3ca24e87e73bd98ee973d28db1051f890da`
- `tools/monkey_campaign/contributions/MAT2-X04/state_readout.py`
  `fe8bcf421430141a1825d5065e5b3a2aa1ce34400456e64ef0b943d14d01a556`
  (the palette-disjointness law form this card re-executes for its new palettes)
- `tools/monkey_campaign/contributions/MAT2-X04/capture_card/card/view_spec.json`
  `f87e2574b7bdb7706d2d17f6f557df311ceb54c78dacee7783919bebd24f5180`
- `tools/monkey_campaign/contributions/MAT2-X04/capture_card/card/card_prereg.json`
  `f7cab07e0a44388e0d654ce5e73953c7ae5acd3a7b91a10f749de92b970ce715`
- `tools/monkey_campaign/contributions/MAT2-X04/capture_card/TEMPLATE_MANIFEST.json`
  `1c4d1dcad9af98c73e1aa4ebb46bff6359b9992e390b38c37fae578e779a59a7`
  (the integrated two-stage capture-gate template manifest; X05 embeds the
  template verbatim from its own capture_card and receipts cite this manifest)
- `tools/monkey_campaign/contributions/MAT2-W10/visualization.py`
  `2e98e8d803f1fde383b00f648100bc8404eac41e3e27db9f6bc32a03de71fafb`
  (the records-only renderer: the follow-camera law `render_frame`, the pose
  drawing `draw_pose`, the W/H 960x540 law, the background fill, the declared
  clearing frame "x, y up, z; ground y=0; trunk at [11.976783, 0, 2.471766]
  as scene furniture" — physics-side furniture this renderer does NOT draw,
  which is precisely why the clean view was translation-invariant)
- `tools/monkey_campaign/contributions/MAT2-W10/walking_demo.py`
  `fb394677306bcb3d808271cce72212c000b82455567e74c1090d3c1003d90ea1`
  (the certified line loader: `gate_and_load`, `run_commanded`)
- `tools/monkey_campaign/contributions/MAT2-W10/command_model.py`
  `0f9fa1a37092760ab4de05bcd32a7b0c769202dddd4347ff54fbdb5c77d184aa`
- `tools/monkey_campaign/contributions/MAT2-W10/verify_inputs.py`
  `25c5fc289a48f24886510d8849856044016e155c627b92c78c15a8781f18f4f6`
  (the W10 certified-line pin table, extracted UNMODIFIED and executed first —
  the X04 discipline)
- `tools/monkey_campaign/contributions/MAT2-U07/camera_views.py`
  `0bb53f98de48df1b0541370930614a937e0287b99b8a1a10845a8947786d4b8c`
  (the declared follow views; C_V1 constants pinned in section 5)
- `tools/monkey_campaign/contributions/MAT2-U07/controls_harness.py`
  `b4c71813fe05008976611d12b954c5a07dbdfb616556dff62ecc513ca1e28b95`
- `tools/monkey_campaign/contributions/MAT2-U07/pixel_gate.py`
  `784b78032da10816647245b535ab9b88e17586f0e5d76d5183f799c5aadcb0d7`
- `tools/monkey_campaign/contributions/MAT2-U07/source_access.py`
  `0563d123b51bd65a28f74b01afa0daa766001830890b4babb458f407e475759b`
  (the declared read-only cat-file access; imported, never copied)
- `tools/monkey_campaign/contributions/MAT2-U01/reconcile/pinned_seam/tools/monkey_campaign/product/input_mapper.py`
  `7a36a45ead6637d9ba5659ea43b54a6b424803c8e57d02720ac970b42cfe6b44`
- `tools/monkey_campaign/contributions/MAT2-U01/reconcile/pinned_seam/tools/science_funnel/typeb_export/command_record.py`
  `6771175933ad20ac6d20c360df96f6a9729a56deb31c58a13be5e76e1cc4355e`
- `tools/monkey_campaign/contributions/MAT2-F04/implementation.py`
  `5c398d22b4259d9e4c89ca3a7900610d629e318ac13b57681cbc7c617619e083`
  (the pinned camera projection `Camera.ndc/pixel` and `raster_tri` — the
  ONLY projection this card's landmarks are rendered and verified through)
- `tools/monkey_campaign/contributions/MAT2-M12/m12_lod.py`
  `f08fd1d2e24f8b72b9833936d49db23cae9d5ef8c3bbedd1bdc2b9ec792849cc`
  (the render-binding audit law heritage)
- `tools/monkey_campaign/contributions/K01-CLIMB-20261001/capture_card/card/view_spec.json`
  `ce5c82d5e04f44af4819c76ef725eddc9c5502dd8e9ef04e07069a4182e00534`
  (the K01 precedent: `scale_px_per_m` declared view constants, 150.0/900.0 —
  the declared-scale law this card generalizes to the perspective projection)
- `tools/monkey_campaign/contributions/K01-CLIMB-20261001/capture_card/card/render_k01.py`
  `3659f5448f1b3abd86c7634b79e26b6955df2128779830790d230139e9c62b54`
- `tools/monkey_campaign/visual_capture.py`
  `5ee55d5ab52beb05ffc33e9b66858f94b706cb22c290786db4a79ab344a4ff05`
- The seam modules are NOT in-tree (in-tree paths hold the empty placeholders,
  the U07 D1 law); resolution through the W10 extraction layer
  (`verify_inputs` + `walking_demo.gate_and_load`), byte-equal to the pinned
  U01 lineage hashes above.

Evidence-store pins (verified by sha256 at draft time; store root
`E:/ChimeraWork/monkey-coordination/evidence-store/`):

- `MAT2-P06/numerical/numerical`
  `a590ba2a5135607867015f052ba1ec9d2ef85080838f6eb710a45a084ba789b8`
- `MAT2-W10/numerical/walking_demo_receipt.json`
  `2fa7dbf180db6090611fdc0d074ebe80d79b43eb25a4a7162e218cbacd22aa02`
- `MAT2-W10/numerical/checks_receipt.json`
  `999fc693dab04199fe3459ff332577d1d73a7e9506a335e2db5f0a3f7ec142b2`
- `MAT2-X04/numerical/REPORT.md`
  `3e24a78a6126b0bf881db01be357286d4165f69d019409f29729962217a27463`
- `MAT2-X04/numerical/result.json`
  `699aa1a1b188819994568fd2461f046dbf376c64a0209ca59ed82fd9759b9728`
- `MAT2-X04/numerical/checks_receipt.json`
  `7e5a42fb02389d9a3a5249b2c8f2cfddbc73458fee9cfb55f2df7e8d41a6cb33`
- `MAT2-X04/numerical/presentation_receipt.json`
  `4d0e52849d2d2c18ea609c9f702296d33c1bc3c445c5bfa570ad4ab6c83c7603`
- `MAT2-X04/numerical/capture_manifest.json`
  `4856dc1fd2b220b844454053ffedea87fad9d97be4fde28db0f19a9c97578188`
- `MAT2-X04/visual/capture_x04_presentation.mkv`
  `f648372d2928620635077bf734b7ebd41b858836a025e87418a46920b1672570`
  (cited heritage; NOT re-claimed)
- `WK-LATENCY-20261002/numerical/REPORT_a12_structural_invisibility.md`
  `4520ec3d168c8c1174030af914b1a7166bf73316b08a1f2c975a8bfb3df48efd`
  (the sealed structural-invisibility finding this card remediates)
- `WK-LATENCY-20261002/numerical/result_a12.json`
  `959e0114acb2297077e76d7dbe7ac05f25ec801fb6941e4cbc133b6631111df6`
- `WK-LATENCY-20261002/numerical/pair_receipt_P01_BRAKE-SHORT_a12.json`
  `7d22b68cb7cc85a2dedec95b729404ae013a68985fa3ffb9782395ee5ac3ca6f`
- `WK-LATENCY-20261002/numerical/pair_receipt_P02_BRAKE-LONG_a12.json`
  `e3120fb066d29fb86fc2d16bd6f806ccc10af9f84f34ee8d49490acad0a921fb`
- `WK-LATENCY-20261002/numerical/depth_law_receipt_a12.json`
  `0ae8c5874cd008c76e6158544db16c7771f332780ae916f2689d16cd754eee4b`
- `WK-LATENCY-20261002/numerical/cadence_receipt.json`
  `ad031ab1215864f7e4bfcb9b2beba1278499370ae152cd084ca3091c740e5172`

Coupling-determination inputs (the sealed attempt-12 driver records; these
carry the per-tick phase/velocity rows and were preserved by the runner, not
yet anchored — their anchoring rides this card's Phase B anchor batch, and
until then they are cited at their runner-results path with sha):

- `E:/ChimeraWork/task-runner/results/ca111cdc917e420eb78c41339d88c41b/receipt.json`
  `f85c0447ce0ff8cf9b27840dca31dd2dc4b309212171724d96c20359a761ef24`
  (the sealed run receipt: manifest
  `4d7bb0ae26a063a7f0a16823d6332de7f8e7d01176d4b0be2c15dc89d9b09fd9`,
  PASSED, cleanup_verified)
- `E:/ChimeraWork/task-runner/results/ca111cdc917e420eb78c41339d88c41b/artifacts/outputs/driver_pair_P01_BRAKE-SHORT.json`
  `5a3ca1be4778a60d9c99ec424b3047c503f473fe665ebb1e8df079f7f77f14fb`
- `E:/ChimeraWork/task-runner/results/ca111cdc917e420eb78c41339d88c41b/artifacts/outputs/driver_pair_P02_BRAKE-LONG.json`
  `d63301e76da53a2ec3ae6d368a3439dbca2b78ed65281a347f58f12c90dcbc48`

## 2. The added presentation layer (this card's only new render content; additive and auditable)

- ONE render entry point in the contribution (`render_frame_x05`) that
  (1) re-executes the pinned pose law over the committed row,
  (2) builds the camera EXACTLY as the pinned `render_frame` follow law,
  (3) draws the declared LANDMARK triangles through the pinned `f04.raster_tri`
  into the SAME colour/depth buffers (depth-tested; drawn before the body),
  (4) draws the body through the pinned `draw_pose` (imported, unmodified),
  (5) draws the declared INSTRUMENT strip (its own glyph drawer),
  (6) returns. The certified `visualization.py` bytes are imported, never
  edited. The landmark-free path of `render_frame_x05` (landmarks and
  instrument disabled by declared flags) MUST be byte-identical to the pinned
  renderer's own frame for the same rows (X-P2a) — the executable proof that
  the layer is purely additive.
- PALETTE LAW (declared constants; the disjointness assertion executes at
  spec load like X04's `state_readout` discipline; any collision refuses
  `x05_palette_collision`):
  - existing (pinned, untouched): ground (168,198,150); body (120,80,60);
    left leg (200,60,50); right leg (60,90,200); diagnostic-only: contact
    (0,255,0)/(255,140,0), chip (180,30,30), tick text (20,20,20), stride bar
    (30,90,200)/(210,210,210); X04 layers L1 (250,250,250)/(15,15,15)/(0,90,220),
    L2 (255,238,200)/(90,45,10), L3 (232,242,232).
  - X05 instrument: chip bg (252,252,252), ink (10,82,10), border (90,20,120).
  - landmarks, one palette per object (per-object mask identity):
    tree_far trunk (94,61,38) + canopy (34,94,44);
    tree_near trunk (84,51,30) + canopy (26,82,36);
    rock_far (132,132,126); rock_near (108,108,102).
- THE INSTRUMENT (declared object `x05_velocity_instrument`): a screen-space
  strip, rect x[12,300] y[8,40]: 1-px border (90,20,120), bg (252,252,252),
  text (10,82,10) at declared origin (18,14), scale 2. Content law: the
  string `V<m/mm/mm>=<com_v rounded 3 decimals>` rendered from a declared 3x5
  glyph table (set: `V 0-9 . =`), drawn by the contribution's own drawer
  (the pinned `draw_glyph` covers digits only and is NOT modified). The
  displayed value is DERIVED at render time from the presented frame's
  consumed row: `round(row.com_v_m_s, 3)`. Manifest rows record the object as
  `declared_instrument: velocity_indicator` — an instrument, never a body cue.
- THE LANDMARK SET (four declared objects; the FROZEN design constants; the
  coordinates are DERIVED at run from the certified rows and then HELD FIXED
  for every frame of both arms and all repeats — declared offsets from the
  anchor base `(x0, 0.0)`, where `x0` is the body anchor x at the first
  presented tick of the window (prefix-identical across arms on the
  deterministic line; receipted; never hand-copied into this prereg)):
  - `landmark_tree_far`: tree at `(x0 - 6.5, 0.0 - 2.5)`
  - `landmark_tree_near`: tree at `(x0 - 3.5, 0.0 - 3.0)`
  - `landmark_rock_far`: rock at `(x0 - 6.5, 0.0 - 4.0)`
  - `landmark_rock_near`: rock at `(x0 - 3.5, 0.0 - 5.0)`
  - DECLARED tree geometry (metres, clearing frame): trunk box half-width
    0.12, height 1.0 (8 triangles); canopy tetrahedron radius 0.42 centred at
    height 1.25 (4 triangles).
  - DECLARED rock geometry: ground tetrahedron, apex height 0.45, base
    radius 0.40 (4 triangles).
  - DESIGN VALIDATION (recorded; the run RE-VERIFIES live and refuses on
    violation — the design numbers are not load-bearing at run, the live
    checks are): projected through the pinned F04 camera over the sealed
    attempt-12 anchor series (both arms, both depths, 21 ticks each), every
    landmark vertex stays in-frame; minimum clearance from the body-target
    pixel 110.83 px (>= the declared 110 px floor); maximum per-frame apparent
    motion 2.62 px; window total spans 112-240 px; minimum pairwise landmark
    separation 34.4 px (>= the declared 25 px floor). Design artifact:
    `landmark_set_design.json` (lane dir; schema
    `chimera.x05.landmark_preflight.v1`; produced by `landmark_preflight.py`,
    which replicates the pinned F04 projection formulas exactly).
  - NON-OCCLUSION LAW: no landmark intersects the body's declared ROI on any
    presented frame (live check; refusal `x05_landmark_occludes_roi`). The
    profile's `occlusion_or_xray_mode` stays honestly `depth_tested` (the
    X04 A6 heritage; no occluder is declared).

## 3. Frozen arms, probes and window (the certified velocity-perturbation instrument)

- Scene identity: the certified declared scene, SEED 20260920, build
  `cpu-walk-scene-build-N`; constants from the UNMODIFIED
  `walking_demo.gate_and_load()` (deploy ALLOW or refusal). Tick rate 300 Hz.
- The probe design REUSES the sealed WK-LATENCY-20261002 attempt-12 (A3)
  classes verbatim — the certified velocity perturbation with a PROVEN state
  channel: N = 10 pairs = BRAKE-SHORT x5 (n odd) / BRAKE-LONG x5 (n even):
  release `W` at `T_in(n)`, re-press at `+150 ms` (SHORT) / `+300 ms` (LONG)
  on the injected clock; the CONTROL arm holds `W`. Common script bytes
  through tick 4350, then per-arm; horizon 4800 ticks;
  `T_in(n) = 4351 + (n-1)`.
- Declared render window: consumed ticks [4351, 4651]; presentation frames
  at ticks 4365..4665 step 15 (21 per arm); presented lag <= 15 ticks (the
  U07 sealed law on exactly this window). Diagnostic context frames at ticks
  {4365, 4500, 4650} only, excluded from attribution.
- Attribution law (amendment-A1 form; the jointly-unsatisfiable-clause defect
  class is excluded by construction): the zero-law binds
  `presented_tick < consumed_tick` of the pair's command chain; the FIRST
  LAWFUL slot for a nonzero diff is the first `presented_tick >= consumed_tick`
  (`consumed = issued + 1`; first presented >= consumed). Pair prefix
  byte-identity through the consumed tick is a gated prediction (X-P1b); a
  violation brands the pair `attribution_contaminated` and excludes it from
  aggregates (reported, never silently dropped).
- Diff channels (computed on decoded FFV1 clean frames, A vs B per pair):
  whole-frame diff count; the declared LANDMARK channel (union of the four
  landmark palette masks); the declared INSTRUMENT channel (the strip rect);
  the declared BODY channel (body+legs palettes). Per-frame series recorded
  in full, no thresholding beyond `count >= 1`.

## 4. Frozen predictions (named variables; every number derived at run from pinned bytes; exceeding a bound is a RECORDED FINDING, never tuned away)

- X-P1a `determinism_zero_control`: the control arm re-executed reproduces
  its per-tick state chain and all decoded frame bytes exactly.
- X-P1b `prefix_identity`: brake and control state chains are byte-identical
  through the consumed tick.
- X-P1c `control_silence`: for every presentation slot with
  `presented_tick < consumed_tick`, the A-vs-B whole-frame diff is 0.
- X-P2a `additive_layer_proof`: the landmark-free, instrument-free render of
  `render_frame_x05` is byte-identical to the pinned renderer's frame for the
  same rows (colour-buffer sha equality) on every rendered row.
- X-P2b `body_invariance_under_landmarks`: the body-palette pixel SET
  (positions and count) is identical between the landmark-bearing and
  landmark-free renders of the same rows — the body's rendered position is
  unchanged by the landmark addition (the Captain's invariance check; the
  landmarks ride the world, not the body).
- X-P3 `landmarks_world_fixed` (the optic-flow deliverable): for every
  rendered clean frame and every landmark, the rendered landmark mask bbox
  equals the bbox of the pinned F04 projection of that landmark's declared
  world vertices through the row-derived camera, within the declared +/-2 px
  per-edge raster tolerance; consequently the per-frame apparent displacement
  equals the projection of the body's committed per-frame anchor travel
  (rows), and the receipt records the derived pixels-per-meter scale per
  frame per landmark (the K01 `scale_px_per_m` precedent generalized to the
  perspective projection: the scale is a DERIVED function of the shared
  camera model and depth, recorded — never asserted as a constant).
- X-P4 `indicator_truthful`: every clean frame's instrument renders exactly
  the string derived from its consumed row (`round(row.com_v_m_s, 3)`, tick),
  glyph-law bbox equality per string (the X04 P9 measured-geometry form); the
  displayed velocity equals `com_v_m_s` to rendering precision; across each
  pair, the brake arm's displayed value diverges from the control arm's at
  the first lawful slot (the rows say it must — the A1 records already
  measured the divergence).
- X-P5 `velocity_visible_in_clean` (THE FALSIFIER TARGET): for every pair,
  the A-vs-B whole-frame diff count on the first lawful slot is >= 1, and the
  diff persists in the declared channels (landmark union and instrument)
  through the window. A pair whose whole-frame diff REMAINS 0 on every
  declared frame records finding `no_pixel_reflection_in_window_persists` —
  the remediation FAILED for that pair; recorded, never tuned.
- X-P6 `flow_discriminates_speed`: on every pair, the control arm's
  cumulative landmark-channel displacement exceeds the brake arm's (the
  sealed travel ordering: 0.7004/0.6787 m vs 0.7472 m), and the LONG depth's
  brake-arm displacement is smaller than the SHORT depth's (the sealed
  depth-ordering, positive image of the recorded inversion law).
- X-P7 `clean_view_layer_law` (X04 P7 preserved): every X05 CLEAN frame
  contains ZERO pixels of any X04 diagnostic-layer palette and zero
  diagnostic-only W10 palette pixels (exact-RGB probe over the committed
  stills); the declared instrument and landmark palettes are the ONLY added
  content; diagnostic context frames carry the declared layers.
- X-P8 `frame_cadence`: the presented stride is exactly 15 ticks on every
  consecutive pair (the L-P5 heritage; deviation = finding `cadence_anomaly`).
- X-P9 `seam_crosscheck`: on every probe chain,
  `command_emitted.t_ms - input.t_ms <= 50.0` ms and consumed lag exactly 1
  tick (the L-P6 heritage; anchor U07 P1 = 27 ms worst).
- X-P10 `coupling_honest_absence`: the contribution contains NO code path
  from velocity to stride/phase rendering (the render signature admits no
  such channel; the structural audit executes); the receipt embeds the
  coupling determination WITH its derivation inputs re-derived at run from
  the pinned sealed records (phase identity 42/42, com_v divergence 40/42,
  com_v endpoints) — the determination is re-executed, never hand-copied, and
  the declared-absent disposition is restated in the report.

## 5. Views, capture and the two-stage gate (the X04 production pattern)

- View: `C_V1_normal_follow_distance` (pinned U07 constants: position offset
  [1.2, 1.6, 3.2], target offset [0.0, 0.5, 0.0], follow True, vfov 50 deg,
  near/far [0.05, 50.0]), viewport 960x540, aspect 16:9, projection
  "perspective", coordinate_unit "m", right-handed Y-up.
- Capture: ONE FFV1 video per arm per pair (20 videos; `-level 3 -g 1
  -fflags +bitexact -pix_fmt bgr0`; 21 clean + 3 diagnostic context frames);
  decode probes pixel-exact at independently recomputable indices; the pinned
  `visual_capture.validate_manifest(manifest, context, PROFILE)` with the
  registry profile (mode=ro) checked BEFORE any capture (G7).
- THE TWO-STAGE CAPTURE-GATE TEMPLATE is embedded verbatim in the
  contribution (`capture_card/`; TEMPLATE_MANIFEST pinned in section 1);
  cards import it, never fork it. `card_prereg.json` pins the canonical
  view-spec prereg hash via `capture_gate.view_spec.spec_prereg_sha256`
  (the canonical-JSON hash — the X04 lesson: it is NOT the file-byte sha)
  with `declared_before_run/declared_before_capture: true`, BEFORE any
  capture. `run_all.py` calls `capture_gate.pipeline.run_pipeline` per case;
  there is no skip path (`GateNotRun` refuses); the exit-code law is 0 GREEN
  / 1 REJECTED (failed evidence, receipts kept) / 2 REFUSED (pre-render).
  X05's view-spec classes: every clean frame must carry body, instrument and
  all four landmark palettes at declared floors (tree 120 px, rock 25 px,
  instrument 400 px) and ZERO X04-diagnostic/W10-diagnostic palette pixels;
  the stage-1 mask co-location executes X-P3's projected-bbox law and the
  instrument-strip co-location per frame.

## 6. Falsifier disposition (card falsifier clause -> executing arm)

- "The remediation failed" -> X-P5: any pair with zero clean-view diff on
  every declared frame is the recorded finding
  `no_pixel_reflection_in_window_persists`; the card then reports the
  remediation as FAILED on the measured evidence — it does not pass.
- "Landmarks are not world-fixed (rigged motion)" -> X-P3 (equality to the
  pinned projection of declared world coordinates through the row-derived
  camera, per frame) + X-P2b (body pixels unchanged by the landmark
  addition). A landmark whose rendered motion does not equal the projected
  body-travel motion is a defect, not a measurement.
- "The instrument fakes the value" -> X-P4 (string derived from the row at
  run, glyph-bbox equality, per-frame divergence law) + the palette
  disjointness assertion + `declared_instrument` manifest labeling.
- "Cosmetic stride coupling" -> X-P10 (auditable absence) + X-P2a (the pose
  source remains the pinned law) + the section-0 determination: the coupling
  is declared absent BECAUSE the sealed records show no velocity response in
  the phases; no render path may fabricate one.
- "A clean-view regression" (the X04 clause, carried forward) -> X-P7.
- "Placeholder/misleading state cues; missing playback evidence" (the X04
  clause, carried forward) -> X-P4's derivation law + the decode-probe law
  (pixel-exact FFV1 probes; the window's landmark motion and indicator
  divergence are the playback evidence).

## 7. Consistency-script discipline

Before any sealed run, the lane's consistency script
(`x05_consistency_check.py`, lane dir) re-derives, from the pinned bytes
only: the base-tip identity and parentage; every base-blob pin in section 1;
every evidence-store pin in section 1; the coupling determination numbers
from the pinned driver records; the landmark design eligibility (re-running
the design projection over the sealed anchors); and the draft-internal sha
mentions. Its machine receipt (`consistency_receipt.json`) records each check
GREEN/RED and is a Phase B precondition: any RED refuses the run
(`x05_consistency_red`). Dev-run failures and refusals are preserved in
`DEV_RUN_REFUSALS.md` (honest negatives), never deleted.

## 8. Resource allowances (bounded; nothing silent)

- Execution: ONE command through
  `python -B E:/PythonChimera/tools/monkey_campaign/task_package.py seal`
  then `run` (CPU slot; BUSY = exit 75, wait and retry with backoff; four
  threads via the runner's cooperative limits). All declared keeps use the
  `outputs/` prefix (the attempt-4 lesson): receipts (pipeline, gate,
  capture, checks), per-pair pair/driver records, diff-channel series,
  landmark scale receipts, the coupling-determination receipt, the REPORT,
  the lint receipt, and the 20 FFV1 videos — bounded by the runner's declared
  output budget; videos are the only large keeps and match the sealed
  attempt-12 precedent within its verified envelope.
- Phase B contribution files (planned):
  `tools/monkey_campaign/contributions/MAT2-X05/`: `PREREGISTRATION.md`
  (these bytes), `render_x05.py`, `landmarks_x05.py`, `instrument_x05.py`,
  `probe_driver.py`, `diff_channels.py`, `coupling_determination.py`,
  `verify_inputs_x05.py`, `state_readout_x05.py`, `run_checks.py`,
  `run_all.py`, `make_report.py`, `lint_report_numbers.py`,
  `capture_card/` (the embedded template + `card/` view-spec, card prereg,
  render callback, run_all), `test_x05.py`, `DEV_RUN_REFUSALS.md`.
- Evidence: artifacts anchored through `anchor.py` into the sealed evidence
  store under this card before registry reference; every load-bearing
  artifact sha256-recorded in the lane `EVIDENCE.md`.

## 9. Absent inventory (honest negatives; declared up front)

- A1 STRIDE-VELOCITY COUPLING: DECLARED ABSENT (section 0 determination; the
  phases do not consume velocity on this certified line; a cosmetic coupling
  is forbidden; the certified-line follow-up is named and out of scope).
- A2 BODY-DISPLAYED VELOCITY CUE: ABSENT. The body carries no
  velocity-bearing visual feature; the only velocity readout in the clean
  view is the declared screen-space instrument, labeled as an instrument.
- A3 AUDIO CUES: NOT this card (C24 unexercised; X04 A4 heritage).
- A4 NATIVE ENGINE FRAME: ABSENT; the presented frames are the declared
  CPU-line frame records of the records-only renderer (W10/U07 heritage).
- A5 OCCLUDERS: none declared; landmarks verified non-occluding for the
  declared window; `depth_tested` recorded on every row.
- A6 WALL-CLOCK SLA: none exists (P06 `network-latency-sla-ms` UNRESOLVED);
  all milliseconds are injected-clock arithmetic (A2 heritage).
- A7 HUMAN FEEL / PICTURE ACCEPTANCE: the readable-motion law here is the
  measured pixel geometry (X-P3/X-P4/X-P5); human acceptance remains the
  independent sergeant picture review (visual_acceptance stays false BY
  DESIGN on this card's own receipts).
- A8 WORLD FURNITURE PHYSICS: the declared landmarks are presentation-state
  objects rendered from declared coordinates; they add NO collision, NO
  contact and NO state channel (the render writes no state — W10 FB6
  heritage; X04 P4 form). The pinned scene's own trunk furniture
  ([11.976783, 0, 2.471766]) remains physics-side and undrawn, unchanged.

## 10. Publication and Phase-B mechanics

- This draft is committed ALONE first (the M03/P04 separate-first law) by the
  Lieutenant on the `e814433c` lineage through the publication owner; the
  gated work starts only after the commit sha (the pin) is handed back to
  `wk-x05-prereg`.
- Phase B package: pinned to the published prereg commit (or a descendant
  containing these bytes identically); certified-line bytes read at
  `e814433c` through `source_access.py` (read-only cat-file).
- Claim class: offline/trace presentation verification on the certified CPU
  line. Findings are recorded as findings. Nothing here re-claims W08/W09/
  W10/U07/X04 or WK-LATENCY sealed results. The card closes only through the
  lead-approved exact-head PR with the full qualification evidence, the
  two-stage gate GREEN, and the independent sergeant picture review.
