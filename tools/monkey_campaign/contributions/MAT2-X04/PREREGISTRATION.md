# PREREGISTRATION — MAT2-X04 render readable animal and environment state

Frozen BEFORE any implementation file, harness run, measurement or capture
frame of this card exists. This file is committed ALONE (separate-first; the
M03/P04 law). Every emitted receipt refuses any document whose
`preregistration_sha256` does not match these live bytes.

- Card MAT2-X04 (planning id X04, slot 3), agent `wk-x04-arrival-1`,
  attempt `50ff462483fd487db3ec9d38fa656f92`, attempt workspace
  `E:\ChimeraWork\monkey-coordination\kanban-attempts\MAT2-X04\50ff462483fd487db3ec9d38fa656f92`,
  file package `package` (NO_WORKTREES law: pinned file package, no clone, no
  worktree), publication branch `review/MAT2-X04` (seeded at the package
  base).
- Criteria sha256 `e5c1d5517a78d74f22eb4692236dcd716d0f82c9e49c9586023b913a56a0e72a`
  (startup join == registry `kanban.cards[MAT2-X04].criteria_sha256`, re-read
  READ-ONLY (`file:...?mode=ro`) from
  `E:/ChimeraWork/monkey-coordination/agent_slots.sqlite3` at run time;
  mismatch = refusal `criteria_pin_mismatch`).
- done_when (verbatim, registry): "Connected animal, contact and climbing
  states are readable in actual captures with no second locomotion pose.
  Material-first addition: Deform/render from the actual material state and
  verified mapping. Debug layers can be invisible in play but cannot be
  missing from verification."
- Observation (verbatim, registry): "Connected CT rendering reported; reuse
  and check affected paths".
- Card task falsifier (verbatim, registry brief): "Placeholder values,
  misleading state cues, missing playback evidence or a clean-view regression
  fails."
- Profile: `presentation`/`motion` (registry read-only at capture time; G7);
  numerical_evidence_required true; clean_view_required true; diagnostic
  layers ["selected state labels", "event/tick trace", "debug isolation of
  the affected layer"]; views ["normal player camera", "detail of affected
  display/asset", "alternate-angle visibility"]; profile procedure
  (verbatim): "Exercise the actual game flow while correlating
  visible/audible events to live values. Use the task-owned subset of
  layers/behaviors. Inventory absent or unresolved components explicitly; do
  not require downstream skills to accept an upstream interface. Freeze exact
  applicable probes and views before execution."
- Base: `a07ac859d4ef16bb34d4006a75c4de8dbee462b4` = the seeded
  `refs/remotes/origin/review/MAT2-X04` (the publisher-seeded integrated tip:
  the MAT2-W10 merge, PR #311; the worker_start preparation pinned it after
  the named ref was seeded). The file package is pinned to this base by
  worker_start preparation. Ancestry at prereg freeze: the W10, F08, M12 and
  G04 winner heads are all ancestors of this base (merge-base verified at
  attempt start; deps W10/F08/M12 all DONE).
- Composed against CARD_STARTER v5/v6 and the house standards:
  `IMPLEMENTER_CHECKLIST.md` (G1-G9) + `TOOLKIT.md` (P1-P9), cited at the
  candidate commit. Dispatch brief: card slot 3 of MAT2-X04.
- Calculations: none owned (`calculation_ids` empty). The C23 camera law is
  CONSUMED through the pinned U02/F04 camera geometry (imports; nothing
  re-decided); C24 audio is NOT this card (X05's scope; absent inventory A4).

## 0. The governing frame (what "actual captures" and "state" mean here)

THE CERTIFIED WALKING RUNTIME IS THE FROZEN CERTIFIED LINE — nothing else.
W07 loaded the accepted walking policy through the certificate machinery;
W08 commanded it through the ACTUAL player command port with a frozen script;
W10 delivered the walking acceptance in the pinned clearing build and the
material-first records-only visualization; F08 reproduced the scene
(seed/configuration -> assets/collision/initial state, byte-exact); M12
qualified mechanical vs render detail independently and sealed the
render-binding audit law (the rendered mesh must equal the mechanical
snapshot, vertex-for-vertex, full coverage). This card adds no policy, no
reissue, no retune, no runtime change: it DRIVES the same certified line
through W10's own sealed `run_commanded` and, for the first time, makes the
line's ACTUAL STATE READABLE in captures — connected-chain, contact and
climbing state labels derived per frame from the run's own committed records.

- "ACTUAL PLAY" is the W08/W10 sealed open-loop form: the pinned U01
  InputMapper (INTERVAL_MS=50) produces versioned CommandRecord v1 records
  into a recording sink; the frozen adapter projects; the certified scene
  `cpu-walk-scene/1.0.0`, build `cpu-walk-scene-build-N`, steps at 300 Hz.
  The arm loop is W10's own `run_commanded` (imported UNMODIFIED from the
  byte-verified extraction; the feed_events law, the no-teleport sink, the
  ZOH pending law and the consumer-side expiry contract are its sealed code,
  not re-implemented). No engine process, no GPU, no training.
- "STATE" is what the certified scene actually reports per tick: the
  PRE-decision telemetry record (`scene_cpu.observation_record`, pinned
  bytes) — gait phases, six declared ground-pad contacts, hind-pad forces,
  pad gaps, applied command — plus the declared pose law's kinematic chain
  (W10 `visualization.pose_at`, pinned bytes) over the certified 10.037998 kg
  body lineage. A label that does not derive from these records is a
  PLACEHOLDER and the falsifier bites (FB1).
- "READABLE" is EXECUTED, not asserted: the state labels are drawn glyphs
  (declared 3x5 font, declared palettes) whose pixel extents are probed on
  the COMMITTED STILLS (P3 discipline: measurement-driven disclosures); each
  frame's label receipt binds the exact strings, their source row fields and
  the derivation (P11).
- "CONNECTED ANIMAL" is the declared gait-walker skeleton: both hindlimb
  chains (hip->knee->ankle->MP->heel, W10's pinned pose law) attached to the
  declared body box. The connection state is DERIVED per frame by a chain
  audit (segment endpoints shared exactly; attachment offsets from pinned
  bytes) and shown as `LINK L5/5 R5/5` (P1). "Connected CT rendering
  reported" is RECONCILED as: the connected rendering on this certified line
  is the declared skeleton chain visualization (W10's material-first
  heritage; no cosmetic skin — W10 FB5 sealed heritage cited); this card
  reuses and checks those affected paths (P5 re-executes the mapping law).
- "CLIMBING STATE" is HONEST: the certified scene's pinned observation schema
  contains NO climbing state and no climb contact channel (the run re-executes
  the schema audit over the pinned scene module bytes and derives
  `climb_state = "absent_declared"` — a DERIVED value, proven live by the FB
  scratch-copy arm, never a hardcoded string). The label reads `CLIMB NONE`:
  the TRUE state of the line while walking (A9's law: anatomy completion does
  not itself prove climbing). Rendering a climbing pose here would be exactly
  the forbidden SECOND LOCOMOTION POSE (FB2 bites it).
- Physics charter: commands choose actuator setpoints; the render WRITES NO
  state (P4 structural arm; W10 FB6 sealed heritage cited). ONE pose source
  exists: the committed per-tick records through the pinned pose law. No
  second pose generator exists in the contribution (FB2 is the live proof
  that a second pose is DETECTED, not that one is tolerated).
- OUTCOME-INDEPENDENCE: W10's walking acceptance, F08's scene reproduction,
  M12's LOD comparison and U07's controls/latency verdicts are SEALED and are
  NOT re-claimed. This card measures STATE READABILITY and the
  material-mapping law of the same line.

## 1. Input pins (verified byte-exact at attempt start; drift = refusal `input_pin_mismatch` / `input_pin_missing`)

Store pins (evidence-store `E:/ChimeraWork/monkey-coordination/evidence-store/`):
- `MAT2-P06/numerical/numerical` `a590ba2a5135607867015f052ba1ec9d2ef85080838f6eb710a45a084ba789b8`
  (the frozen P06 limits record: `ui-poll-cadence-ms` carried;
  `camera_visible_player_outcomes`; the open `network-latency-sla-ms`
  operator decision — unchanged from the sealed U07 consumption)
- `MAT2-W10/numerical/walking_demo_receipt.json` `2fa7dbf180db6090611fdc0d074ebe80d79b43eb25a4a7162e218cbacd22aa02`
- `MAT2-W10/numerical/checks_receipt.json` `999fc693dab04199fe3459ff332577d1d73a7e9506a335e2db5f0a3f7ec142b2`
- `MAT2-F08/numerical/checks.json` `837644333f9412f9074cc47d26dbf06f38b202613fac1e6f49097e4ad20a0da5`
  (the scene-reproduction named-check receipt; dependency receipt)
- `MAT2-M12/numerical/experiment_receipt.json` `db516434a1034d0703a362aaecfd7b983b9a38d36dbcd390b31d2e15f1b4c589`
  (the mechanical/render-detail receipt; dependency receipt)
- `MAT2-M12/numerical/falsifier_receipt.json` `f42004d6320cb54ffa167a95ab555d78af8bdf6f88e55b481467e8cc5632766c`
  (the binding-audit falsifier heritage: FB1 stale render, FB2 dropped-ring
  remap)

Base-blob pins (read from the shared repository's Git object database at the
package base `a07ac859d4ef16bb34d4006a75c4de8dbee462b4` through the DECLARED
read-only `git cat-file` access in `source_access.py`; NO_WORKTREES law).
The W10 certified-line pin table (W04 certificate machinery, lane repo
machinery, scene, F04 rasterizer, terrain, visual validator, W09 supervisor)
is verified by W10's own `verify_inputs.py`, extracted UNMODIFIED at the base
and executed first (it pins its own base `273d7e59…`, an ancestor blob-identical
for every file it names — the W10 merge is contained in this base). The
X04-ADDED pins, all computed at prereg freeze from the base tree:
- `tools/monkey_campaign/contributions/MAT2-W10/command_model.py`
  `0f9fa1a37092760ab4de05bcd32a7b0c769202dddd4347ff54fbdb5c77d184aa`
- `tools/monkey_campaign/contributions/MAT2-W10/visualization.py`
  `2e98e8d803f1fde383b00f648100bc8404eac41e3e27db9f6bc32a03de71fafb`
- `tools/monkey_campaign/contributions/MAT2-W10/verify_inputs.py`
  `25c5fc289a48f24886510d8849856044016e155c627b92c78c15a8781f18f4f6`
- `tools/monkey_campaign/contributions/MAT2-W10/walking_demo.py`
  `fb394677306bcb3d808271cce72212c000b82455567e74c1090d3c1003d90ea1`
- `tools/monkey_campaign/contributions/MAT2-W10/run_capture.py`
  `a078928fcdbe78b7982d20fc362f7f9e021c3360c47523fb2af6cc564af9bf2a`
- `tools/monkey_campaign/contributions/MAT2-W10/lint_report_numbers.py`
  `c2f046439ad330a1d748468b20fefdfc452f67deaa64272b931f0eb8ccfd1405`
- `tools/monkey_campaign/contributions/MAT2-U01/reconcile/pinned_seam/tools/monkey_campaign/product/input_mapper.py`
  `7a36a45ead6637d9ba5659ea43b54a6b424803c8e57d02720ac970b42cfe6b44`
- `tools/monkey_campaign/contributions/MAT2-U01/reconcile/pinned_seam/tools/science_funnel/typeb_export/command_record.py`
  `6771175933ad20ac6d20c360df96f6a9729a56deb31c58a13be5e76e1cc4355e`
- `tools/monkey_campaign/contributions/MAT2-M12/m12_lod.py`
  `f08fd1d2e24f8b72b9833936d49db23cae9d5ef8c3bbedd1bdc2b9ec792849cc`
  (the sealed render-binding audit law: `render_binding_audit` — the rendered
  mesh must equal the mechanical snapshot bitwise, vertex-for-vertex, full
  coverage; this card re-executes that LAW in the walking-frame form)
- `tools/monkey_campaign/contributions/MAT2-M12/capture_manifest.json`
  `0ea48c70af67b9336a3b95ca03a5a6ad0ccdad7a0d80db1e77c6dffff8139d40`
  (the verified capture-binding precedent; W10's own pin, re-pinned here)
- `tools/monkey_campaign/contributions/MAT2-F08/report.md`
  `fcd973c335a1163694bc4a57a87550890e94f214e0c92d06dbec18756b2033c1`
  (the scene-reproduction qualification receipt: seed/configuration ->
  assets/collision/initial state byte-exact; cited, not re-claimed)
- `tools/monkey_campaign/contributions/MAT2-A09/report.md`
  `feb132dca3b2da0df58bc7fea9bd27581613fb48999beb9c4be8be3eacd7daf2`
  (the honest-scope law source: "anatomy completion does not itself prove
  climbing" — the climbing absent-inventory's citation)
- `tools/monkey_campaign/visual_capture.py`
  `5ee55d5ab52beb05ffc33e9b66858f94b706cb22c290786db4a79ab344a4ff05`
  (the pinned structural capture validator; import identity)
- The seam modules are NOT in-tree at this base (the U07 D1 lesson): the
  runtime resolves `tools.monkey_campaign.product.input_mapper` and
  `tools.science_funnel.typeb_export.command_record` through the W10
  extraction's stripped namespace (bootstrap_pinned_imports; byte-equal to
  the pinned U01 lineage hashes above).

## 2. The state-derivation law (the card's instrument)

Every state label is a PURE function of committed bytes: the per-tick record
row (W10 `run_commanded`'s export fields) + the pinned pose law + the pinned
scene schema. Nothing else feeds a label.

- `derive_state(row, geom)` (this card's module, over pinned inputs):
  - connected: for each side, the W10 pose law's chain
    (hip, knee, ankle, mp, heel) from the row's recorded phase through the
    pinned tables/zero-map/segment lengths; the chain audit requires (a) five
    joint sites, (b) consecutive-segment endpoint identity EXACTLY (the same
    float object the law produced — deviation bitwise 0.0 m), (c) hip
    attachment at the declared offsets (0.0 m left / 0.04 m right, W10's
    declared leg z offset 0.02 m per side). Label: `LINK L5/5 R5/5`.
  - contact: `foot_contacts[4]/[5]` (left/right hind pads) and
    `foot_forces[4]/[5]` (N, declared nominal fore-foot support scale 0.25
    N_bw_frac times the warm value, reported at the row's own precision).
    Label: `CT L<0|1> R<0|1> <fL>N <fR>N`.
  - climb: the DECLARED schema audit over the pinned scene module bytes:
    the observation record's key set (extracted at run from the pinned
    `scene_cpu.observation_record` source by AST, never hand-copied) contains
    no climbing key, and the scene's declared contact set is exactly the six
    ground pads; the derived value is `absent_declared`. Label: `CLIMB NONE`.
    A scratch-copy arm that INJECTS a climb key flips the derived value
    (the FB3 live proof that the label is derived, not planted).
  - mode: `WALK` when the row's contact set is the declared ground-pad set
    and the derived climb state is `absent_declared` (the certified line's
    only declared locomotion); refusal otherwise (`x04_mode_undeclared`).
  - event: the row's tick, com speed and the contact TRANSITIONS versus the
    previous committed row (`CON L+`, `CON L-`, `CON R+`, `CON R-`, else `-`).
- The layers (registry names, this card's palettes; distinct from every W10
  render color):
  - L1 "selected state labels": screen-space panel, rect x[12,300]
    y[40,190]; panel bg (250,250,250); text (15,15,15); border (0,90,220).
  - L2 "event/tick trace": screen-space strip, rect x[12,300] y[500,532];
    bg (255,238,200); text (90,45,10).
  - L3 "debug isolation of the affected layer": screen-space inset, rect
    x[640,948] y[40,190]; bg (232,242,232); the L1 state-label content ONLY
    (re-drawn inside the inset; no body/skeleton pixels inside the rect —
    probed). This layer IS the debug isolation: it proves the label layer
    renders independently of the body render.
- Glyph law: declared 3x5 pixel font (A-Z, 0-9, `/ . + - : N` set as
  needed), glyph advance 4 px, scale 2 (panel) — every drawn string's
  expected bounding box is DERIVED from the glyph law and compared EXACTLY
  against the committed still's palette-pixel bbox (P9).

## 3. Frozen arms and window (the repeatable scenes)

Scene identity: certified declared scene, SEED 20260920, horizon 10500 ticks
(W10's declared R1 horizon), the frozen W08/W10 input script through W10's
own `run_commanded`. "Repeatable" is EXECUTED: A2 is a fresh re-execution of
A1 and must reproduce A1's per-tick state chain exactly (P10).

- A1 WALK: the full frozen script, horizon 10500 — the actual play run whose
  records feed every label and frame.
- A2 REPEAT: identical re-execution (determinism zero-control).
- Presentation window: consumed ticks [4260, 4686) — PW0 = 20 x 213
  (the pinned `CYCLE_TICKS`), exactly two gait cycles, inside the scripted
  turn/hold segment (mouse-right window ends tick 4485; key A saturating turn
  from tick 4500). All constants above are FROZEN from pinned bytes; the run
  must OBSERVE >= 1 left and >= 1 right contact transition among the window's
  committed rows (the transition-coverage precondition; absence = failed
  prediction P2, honest).
- Frozen frame plan (39 frames; every number above is frozen, none observed):
  - V1 "normal player camera" CLEAN: ticks 4260 + 15k, k = 0..28 (29 frames;
    the video's motion axis; lag bound: presented tick covers its consumed
    tick within the 15-tick stride).
  - V1 DIAGNOSTIC: ticks {4275, 4470, 4665}.
  - V2 "detail of affected display/asset" CLEAN: ticks {4470, 4650};
    V2 DIAGNOSTIC: tick {4470}.
  - V3 "alternate-angle visibility" at tick 4275: CLEAN x2 (S_pass1, S_pass2)
    and DIAGNOSTIC x2 (S_pass1_diag, S_pass2_diag) — the repeatability
    identity: byte-identical piped frame bytes within each mode pair (P4).
- Views (body-anchored follow offsets; clearing frame x,z ground / y up;
  metres; right-handed Y-up; perspective; viewport 960x540; aspect 16:9):
  - V1 "normal player camera": position offset [1.2, 1.6, 3.2], target
    offset [0.0, 0.5, 0.0], vfov 50 deg, near/far [0.05, 50] — THE CLEAN
    VIEW (clean_view_required).
  - V2 "detail of affected display/asset": position offset [0.35, 0.7, 0.9],
    target offset [0.0, 0.5, 0.0], vfov 45 deg, near/far [0.01, 10].
  - V3 "alternate-angle visibility": position offset [0.0, 1.2, 4.0], target
    offset [0.0, 0.5, 0.0], vfov 40 deg, near/far [0.05, 50].
- Capture: ONE FFV1 video (`-level 3 -g 1 -fflags +bitexact -pix_fmt bgr0`;
  the codec standard; ffmpeg version recorded), montage in declared plan
  order at 1 fps metadata; decode probes at independently recomputable
  indices; the pinned `visual_capture.validate_manifest(manifest, context,
  PROFILE)` with THE registry profile (mode=ro).

## 4. Frozen predictions (named variables; every number derived at run from pinned bytes, none hand-copied)

- P1 `connected_chain_complete`: over EVERY rendered frame's row, the pose
  law yields both chains with five joint sites and the chain audit passes
  (endpoint identity bitwise 0.0 m; declared attachments); the label reads
  `LINK L5/5 R5/5` derived from those counts.
- P2 `contact_labels_follow_actual_state`: per rendered frame, the contact
  label values equal the committed row's `foot_contacts[4]/[5]` and
  `foot_forces[4]/[5]` exactly (no rounding, no defaults); the window's
  committed rows contain >= 1 left and >= 1 right contact transition, and
  the label receipts at a transition tick and its predecessor DIFFER — the
  labels follow actual events.
- P3 `climb_state_honest`: every label receipt's climb value is
  `absent_declared`, DERIVED by the schema audit over the pinned scene
  module's observation-record key set (AST-extracted at run); the scratch
  arm with an injected climb key derives a DIFFERENT value (FB3's live
  proof); the label text is `CLIMB NONE` — the true state, never a claimed
  capability.
- P4 `single_pose_source`: (a) the V3 mode pairs are byte-identical within
  each mode; (b) re-rendering one V1 clean frame from the same records is
  byte-identical; (c) a tampered row (declared +0.25 phase_left delta)
  renders a DIFFERENT frame (> 0 pixels differ) — the pose follows the
  records; (d) structural: the render consumes committed records only; the
  state chain is recorded BEFORE any render and is byte-identical after
  (W10 FB6 heritage cited; the loop signature admits no camera channel).
- P5 `material_mapping_verified`: for EVERY rendered frame, the render-time
  joint positions equal the pinned pose law re-executed over the committed
  row (max deviation bitwise 0.0 m; M12's `render_binding_audit` law form:
  rendered == mechanical snapshot, full coverage — five joints x two legs
  plus the body box per frame, no dropped sites); the mapping identity is
  pinned (W10 `visualization.py` + `derived_numbers.json` sha256 pins).
- P6 `camera_fields_complete`: every manifest row's camera record carries
  ALL the profile's `camera_required_fields` (15; recorded per row with
  declared units); `occlusion_or_xray_mode` = "depth_tested" on every row
  (no occluder is declared in this profile's views — A6).
- P7 `clean_view_no_diagnostics`: every CLEAN frame contains ZERO pixels of
  any declared layer palette (executed exact-RGB probe over the committed
  still bytes) and its manifest row carries zero labels/layers (the
  validator's own clean law re-proven).
- P8 `debug_layers_present`: every DIAGNOSTIC frame carries all three
  declared layers (manifest row) and the pixel probes confirm each layer's
  palette present on the committed still; the L3 inset contains state-label
  pixels and ZERO body/skeleton palette pixels inside its rect.
- P9 `readability_measured`: on the committed V2 diagnostic still, the
  probed pixel bbox of each state-panel text row EQUALS the glyph-law
  expected bbox exactly (declared font, scale, origin); the panel's
  measured pixel count is recorded. Readability is the measured geometry,
  never a prose claim.
- P10 `repeatable_states`: A2's per-tick state chain == A1's (bit-identical
  certified line); the label receipts derived from A2 rows == A1's (the
  states the labels report are reproducible).
- P11 `label_content_bound`: every rendered frame's label receipt binds the
  exact strings, their source row fields (tick, phases, contacts, forces)
  and the derivation identity; the diagnostic stills' palette pixel counts
  match the receipt's expected per-string pixel counts exactly.
- P12 `deform_follows_state`: the 29 V1 clean frames' pose identifiers
  (chain joint coordinates hashed per frame) take >= 2 DISTINCT values
  across the window (the render DEFORMS with the actual gait cycle), with
  the non-vacuity guard that 29 frames were rendered (a single-pose render
  would fail this prediction — the "no second locomotion pose" law's
  positive form: the ONE pose moves because the material state moves).

## 5. Falsifier disposition and bite arms (each with its own passing clean control FIRST and a named premature guard; G1/P1)

- "Placeholder values" -> FB1 `x04_fb1_placeholder_state`: render a
  diagnostic frame whose state source is replaced by DECLARED placeholder
  constants (contact always 1, force always 0.25 N, link always 5/5) at the
  first window tick whose actual row differs from those constants; the
  binding audit must REFUSE the placeholder frame (label receipt != row
  derivation) and the placeholder pixels must differ from the actual frame.
  Clean control: the actual frame at that tick passes the same audit; guard
  `x04_fb1_premature` requires the actual row to genuinely differ from the
  placeholders (else the arm is vacuous and dies loudly).
- "misleading state cues" -> FB2 `x04_fb2_second_pose`: a canned-pose render
  (a CONSTANT reference pose, no row input) at a window tick must be
  DETECTED: it fails the material-mapping audit (re-executed pose law !=
  canned joints, deviation > 0.0 m) and differs from the actual-pose frame
  (> 0 pixels). Clean control: the actual frame passes the mapping audit
  bitwise; guard `x04_fb2_premature`. This arm is the executable proof that
  a second locomotion pose CANNOT pass this card's verification.
- "missing playback evidence" -> FB3 `x04_fb3_missing_layer`: the layer
  probe must REFUSE (`x04_layer_missing`) a diagnostic frame rendered
  WITHOUT the state-label layer; the climb schema audit must REFUSE a
  scratch copy whose scene schema lost the audit's inputs
  (`x04_schema_audit_refused`). Clean controls: the real diagnostic frame
  passes both probes; guards `x04_fb3_premature`.
- "a clean-view regression" -> FB4 `x04_fb4_clean_leak`: planting exactly
  one declared palette pixel on a clean still must be CAUGHT (> 0 layer
  pixels on a clean frame = refusal `x04_clean_leak_refused`). Clean
  control: the real clean stills have zero layer pixels; guard
  `x04_fb4_premature`.
- FB5 `x04_fb5_stale_mapping` (M12 FB1 heritage, walking-frame form):
  auditing frame A's render against row B's re-executed pose (a declared
  different window tick, non-vacuous by construction) must REFUSE
  (`x04_stale_render_refused`, deviation > 0.0 m). Clean control: frame A
  against row A is bitwise 0; guard `x04_fb5_premature`.

## 6. Profile consumption (the presentation profile as caller data)

The registry profile (read-only at run; G7 — checked BEFORE any capture) is
consumed, never hand-copied: `views` (the three declared view names above
are the profile's verbatim strings; the validator refuses undeclared
view_ids), `diagnostic_layers` (the three declared layers; the validator
refuses a diagnostic view that omits any), `clean_view_required` (every
view pairs clean + diagnostic of the SAME state binding and camera), the 15
`camera_required_fields` (P6), `numerical_evidence_required` (the receipts
and named variables are the evidence), `nonvisual_reason` (null — visual
evidence IS required; the captures carry it). The occlusion probe of the
`controls` profile was U07's arm; this profile declares NO occluder —
`occlusion_or_xray_mode` is honestly "depth_tested" everywhere (A6).

## 7. Falsifier disposition summary (card falsifier clause -> executing arm)

- "Placeholder values" -> FB1 (+ P2/P3's derivation law, P11's binding).
- "misleading state cues" -> FB2 (+ P1/P3: labels derive from the actual
  chain/schema audits; `CLIMB NONE` is the true state, never a claim).
- "missing playback evidence" -> FB3 (+ the video/decode-probe law: the
  committed video's decode is pixel-exact at recomputable indices; the
  window's transitions and 29-frame deform are the playback evidence).
- "a clean-view regression" -> FB4 (+ P7's zero-leak probe on every clean
  still; the validator's clean law).

## 8. Absent inventory (honest negatives; declared, not discovered at run time)

- A1 CLIMBING CONTROLLER/STATE: ABSENT on the certified walking line (the
  pinned scene schema has no climbing state; the label reports the derived
  `absent_declared` value). No climbing pose is fabricated — that would be
  the forbidden second locomotion pose. A9's law is cited at the pin.
- A2 NATIVE ENGINE FRAME: ABSENT; the presented frames are the DECLARED
  CPU-line frame records of the records-only renderer (W10 N1/N2/N3 and U07
  A1 heritage carried; no native engine process is started).
- A3 COSMETIC SKIN: ABSENT; the visual body is the DECLARED gait-walker
  skeleton visualization of the qualified hind-pad-surrogate state (W10 FB5
  sealed heritage cited, not re-claimed).
- A4 AUDIO CUES: NOT claimed on this card (X05's scope; C24 not exercised).
- A5 SESSION/INSPECTOR OVERLAYS: the X02/X06 surfaces are NOT exercised.
- A6 OCCLUSION/CAMERA-COLLISION PROBES: NOT declared in this profile's
  views (U07's arm; `depth_tested` recorded honestly on every row).
- A7 HUMAN FEEL/READABILITY-AS-FELT: the readability law here is the
  measured glyph geometry (P9); human acceptance remains the independent
  picture review (visual_acceptance stays false BY DESIGN).

## 9. Publication and honesty mechanics

- This file is committed ALONE first (the M03/P04 law), by the Lieutenant;
  every receipt embeds `preregistration_sha256` of THESE bytes and refuses
  any mismatch.
- The sealed run executes ONE command (`run_all.py`) through the CPU runner
  (task_package.py): pins -> registry/profile (BEFORE capture; G7) -> W10
  certified-line layer -> gate and load identity -> arms A1/A2 (W10's own
  `run_commanded`) -> state derivation + material-mapping audit -> frozen
  predictions P1-P12 -> falsifier bites FB1-FB5 (clean controls first) ->
  receipts + traces -> named checks -> bounded capture (FFV1 video +
  manifest + validator) -> report -> report-number lint. First failure stops
  with that stage's exit code.
- The 12 card-kit gates run against the card directory
  (card-kit/batch_gates.py). Dev-run failures and refusals are preserved in
  `DEV_RUN_REFUSALS.md` (honest negatives), never deleted.
- Claim class: offline/trace presentation verification on the certified CPU
  line. A diagnostic or scaffold alone cannot close this card; the card
  closes only through the lead-approved exact-head PR with the full
  qualification evidence.
