# MAT2-F08 PREREGISTRATION — verify repeatable forest loading

Committed BEFORE any implementation file, harness run (beyond the disclosed
reconciliation probes of section 10), measurement or capture frame existed
(git-provable: this is the first commit of this contribution directory on the
attempt branch). Everything below is frozen now; amendments, if any, will be
separate commits BEFORE the implementation commit and BEFORE any build, each
disclosing what changed and why. No bar is tuned after a measurement is seen.

## 0. Task and criteria identity (verbatim, not paraphrased)

- card: MAT2-F08; planning id F08; attempt `d8a71eabe827417f90de09cd1f7048c3`;
  arrival `arrival-961642204b8c4a478a4457af12fbfdbb`; criteria sha256
  `8063e7175f9b9a638809b348606636d280a56d9165245a9f91ced21abb55fcd7`;
  scope sha256 `cb5475f8486197a973edc4360b177fc31a629c4f0979ebf80dd76aae57996097`;
  base revision `edd5ae079d5f0f64ae498e055a1b11bc5adab013` (branch-1 after
  fast-forward; the sealed line tip carrying merged F01-F07/B06; the slot
  branch head c525b82c7c3c was a verified git ancestor, fast-forward only).
- done_when (verbatim): "Scene seed/configuration reproduces assets, collision
  and initial state with clear failures for missing assets"
- falsifier (verbatim, card): "Rendered/collision mismatch, ghost support,
  missing boundaries or off-frame probe subject fails; tags alone do not
  establish contact."
- REGISTRY profile object (read READ-ONLY from
  `E:/ChimeraWork/monkey-coordination/agent_slots.sqlite3`,
  `kanban.cards[MAT2-F08].spec.ontology_qualification.task.verification_profile`;
  canonical sha256 recorded in the receipt): id `forest`, kind
  `visible_static`, subject "Terrain/trunk geometry and actual contact
  surfaces", scenario "Qualify only this task: Scene seed/configuration
  reproduces assets, collision and initial state with clear failures for
  missing assets Profile procedure: Inspect world frames and render/collision
  correspondence at representative ground/trunk probes, including silhouettes
  and depth. Use the task-owned subset of layers/behaviors. Inventory absent
  or unresolved components explicitly; do not require downstream skills to
  accept an upstream interface. Freeze exact applicable probes and views
  before execution.", diagnostic_layers ["render mesh", "collision surfaces",
  "normals/contact markers", "scene bounds", "stable 3D labels"], views
  ["clearing overview", "terrain/trunk seam close-up", "side and oblique
  depth checks"], clean_view_required true, numerical_evidence_required true,
  falsifier: "Rendered/collision mismatch, ghost support, missing boundaries
  or off-frame probe subject fails; tags alone do not establish contact."
  Known canonical sha256 of the identical `forest` profile object (F07's
  receipt): `3348d00194c8d920abe3c5902c36a0f23088838bd293172f10f65a3de2670852`;
  the build re-derives it and refuses on drift.
- task_id in the capture manifest/context: `F08` (SHORT form).
- card observation (verbatim): "Resource cleanup uses existing lifecycle
  machinery".

## 1. Reconcile-first: reused published bytes only (nothing re-derived)

All input pins are published bytes of merged cards at the base revision,
asserted by raw sha256 at every run; the harness refuses on any mismatch
(`f08_pin_*`). The sealed-line scene is the reproducibility subject: its
seeded generators and its merged evidence are the things that must reproduce.

| pin | published location | raw sha256 |
|---|---|---|
| terrain asset (render arrays = query triangulation) | contributions/MAT2-F02/pins/terrain_bundle.json | `446ed3fbd0f50205c61a7233ceca289bfc3316f76dfc672fec307b20d8305d52` |
| terrain query surface | contributions/MAT2-F02/pins/terrain_query.py | `b1e244b8843671afc29af530c4725bf812ffd5f8967130f0202792aeb7a8cce1` |
| terrain bundle module/validator | contributions/MAT2-F02/pins/terrain_bundle.py | `c6ada25a1b6192aa86add8b09bc19161c0cd81e3fb3d4bd267492660c0be8f2e` |
| clearing recipe (seeded terrain generator) | contributions/MAT2-F02/pins/clearing_recipe.py | `ab800d2257655118296519b606c77ddc7116f524ae0c2e6a0bab3b38473892dc` |
| clearing declaration | contributions/MAT2-F02/pins/clearing_declaration.json | `18dd2ff65410cd1cf184a7a8df61c7503a6ce15083f30159e727e9a8117bfbc1` |
| trunk declaration | contributions/MAT2-F02/pins/trunk_declaration.json | `94ff906ec5e8b8388e4de318aa3321bad9c791fbb168e8234c371ed1d327e3f1` |
| M06 shared contact path (imported, never forked) | contributions/MAT2-M06/local_contact.py | `1cd662b30343011eb4a0a01e461a1e82b00482d0371857c8e42d6bec8f9a28dc` |
| M06 contact law declarations | contributions/MAT2-M06/contact_law.json | `583962c29f18118a478dedb167f2c3667414b86f5cab4ee54763416f1df7e41b` |
| F03 pinned trunk mesh asset | contributions/MAT2-F03/assets/trunk_01_mesh.json | `3b17441764714c5e5e9c7a43c3253b3271a0f508954095e1960a57820cef6ee7` |
| F04 contact-qualification machinery (imported, never forked) | contributions/MAT2-F04/implementation.py | `5c398d22b4259d9e4c89ca3a7900610d629e318ac13b57681cbc7c617619e083` |
| F07 scene module (imported, never forked: seeded placement, contact bodies, render/classify law) | contributions/MAT2-F07/implementation.py | `49a975c7a1a14238eb79bd5edcb0e96bbd5231a2cdf329dccacd282f65b36a94` |
| F07 published obstacle declaration (seed-regeneration target) | contributions/MAT2-F07/assets/obstacle_declaration.json | `73525a3de022d5b8d9901ca90fde77124904471f33a67f2f79a94f7ad1636769` (A1) |
| F07 published contact trace (dynamics-reproduction target) | contributions/MAT2-F07/evidence/contact_trace.json | `710bfd1993894bd82c496c7c1c095d4201842ba1bebb248776f79392b925f0f7` (A1) |
| F07 published capture frames (render-reproduction targets, raw sha256, A1) | contributions/MAT2-F07/evidence/frame_V1_clearing_overview_clean.bmp \| _diagnostic \| frame_V2_seam_closeup_clean \| _diagnostic \| frame_V3_side_depth_clean \| _diagnostic | `6c9316279e1b231b5dd0352b4a10a1b191d7391ffb03895714bd953814a58b87` / `e241729012d1238ac643f66b5a078b9c66b570b079dc970739ef619824e57405` / `360e7eac5e1f0a0f78da600ca7b147d49d6b09c71dd71580f42eac739db4025f` / `6d4e64117e43ad867b7c2c22e5edec1ea17daa000fa939bd514264ff937a0210` / `407fd44a22ebcfbbfdd0df1f3885d7393ec24ae418a5e11f174c49e722d1cdf0` / `539888a720705d6bbbb68c7b0493d69a0b4f9f506f95c335fb80654344fd47c3` |

Merged-card constants reused as frozen (no new physics constants): seeds
`4598321` (terrain recipe, F01) and `4600823` (obstacle placement, F07); the
M06 law constants g 9.81, dt 0.005, slop/margin 1e-05 m, beta 0.2, restitution
0, CCD max_iters 64 / tol 1e-12 (contact_law.json); ground/trunk matter and
probe matter exactly as merged (F02/F03/F07, including F03's declared
UNEVIDENCED-PLACEHOLDER wood friction, G04 debt); trunk site
(11.976783, 0, 2.471766) radius 0.037 m height 1.158 m; spawn (0, 0, 0) with
declared body-radius envelope 0.25 m; impact speed 2 m/s, start clearance
0.25 m, 30 ticks per run (F07's frozen schedule).

## 2. F08-owned scene configuration (the implementation's declared input)

`assets/scene_configuration.json` is NEW scene data authored by F08 (canonical
JSON, self-pinned sha256, SI metres, clearing frame x east / y up / z south).
It is the "scene seed/configuration" of the done_when: ONE document that names
the seeds, the assets by published hash, the collision state and the initial
state. The loader `load_scene` intakes it with the F01 prereg vocabulary
(strict `require`/`Refusal`, named codes, no defaults):

- `seeds`: terrain_recipe 4598321; obstacle_placement 4600823 (the scene's
  declared seeds; F08 introduces NO new RNG).
- `assets`: one record per pinned input with its published contributions path
  and raw sha256 — the terrain declaration (seed-derived, verified by
  regeneration), the terrain bundle (declaration-derived, verified by
  regeneration), the obstacle declaration (seed-derived, verified by
  regeneration), the trunk declaration + trunk mesh + contact law (published,
  hash-pinned), and the four pinned modules.
- `collision_state`: solver `chimera.local_contact.v1` (pinned bytes), the
  contact law sha, ccd true, and the declared composition scope (F07
  heritage: each impact run instantiates exactly the struck obstacle's body;
  the ground co-instantiation is the F04 P0 refusal heritage, measured per
  obstacle, not assumed).
- `initial_state`: spawn (0, 0, 0) with the declared 0.25 m body envelope; the
  three frozen camera bookmarks; the frozen impact schedule (seven runs in the
  declared order rock_01, rock_02, rock_03, log_01, log_02, stand_01,
  stand_02, speed 2 m/s, start clearance 0.25 m, 30 ticks, facet/hull-aligned
  approach per F07's A2); tick_interval [0, 0].

The MATERIALIZED scene state document (built by the loader, never hand-edited)
records: every pin's resolved path + raw sha256; the three regeneration
equalities; the collision-state section (ground/trunk/obstacle contact bodies'
vertex arrays in the contact frame, law constants); the initial-state section
(declared spawn/schedule/cameras plus the DERIVED impact start coordinates and
the tick-0 solver state of every impact run); the re-derived dynamics trace
digest; and the rendered-frame digests. Its canonical sha256 is THE scene
fingerprint that must reproduce.

## 3. Frozen bars (all derived from pinned records; none tuned)

| id | bar | derivation |
|---|---|---|
| REGEN bar | sha256(regenerated) == sha256(published) for the terrain declaration (from seed), the terrain bundle (from the regenerated declaration) and the obstacle declaration (from seed) | the pinned generators are the declared seed->asset law; byte equality on canonical JSON is the byte-exact AND float-exact claim (every derived float sits on the generators' 1e-6 grid; the M06 trace floats are compared at full canonical repr) |
| CROSS bar | the materialized scene state document is BYTE-IDENTICAL across three fresh subprocess instantiations and the in-process instantiation | "reproduces ... across fresh instantiations" is measured, not asserted; canonical JSON bytes at full float repr = bit-exact |
| PUBLISHED bar | the re-derived dynamics trace equals the published F07 contact_trace.json bytes, and the re-derived V1 clean frame equals the published F07 gate artifact bytes | F08 must reproduce the merged line's own evidence from seed + configuration, not merely agree with itself |
| LEDGER bar | 1e-12 | M06 A2 identity per re-derived tick (F04/F07 frozen form), re-asserted from the re-derived records |
| REFUSAL bar | every missing/corrupt arm refuses with a named code that IDENTIFIES the missing/corrupt asset; zero arms substitute a default | the done_when's "clear failures for missing assets"; the F01 prereg vocabulary (strict require/Refusal, named codes) |
| FINGERPRINT bar | a lenient (default-substituting) loader MUST be caught by the declared-fingerprint gate | "no silent defaults" is enforced by comparison, not by trust |
| FLOAT-GATE bar | a 1e-9 perturbation of any declared initial-state scalar between two fresh instantiations MUST fire the cross-instantiation gate | proves the byte-exact gate has teeth at float resolution |
| MARKER bar | F07's frozen marker table reused verbatim; zero VISIBLE_BUT_MISMATCH; zero UNRENDERED required subjects | the sealed-line render/collision correspondence law, unchanged |

## 4. Frozen materialization procedure (measured, not asserted)

`load_scene(config)` executes, in order: (1) intake the configuration (self
sha, schema, section presence — refusals `f08_config_*`); (2) assert every
asset pin's presence and raw sha256 (`f08_pin_missing`, `f08_pin_hash_mismatch`
naming the asset); (3) regenerate the terrain declaration from
`seeds.terrain_recipe` with the pinned recipe and compare bytes to the
published declaration (`f08_seed_reproduction_mismatch` naming the asset and
seed); (4) regenerate the terrain bundle from the REGENERATED declaration with
the pinned bundle module and compare bytes; (5) regenerate the obstacle
declaration from `seeds.obstacle_placement` through the pinned F07 placement
and mesh functions and compare bytes; (6) load the trunk declaration + trunk
mesh + contact law (published bytes) and assert the law's slop/margin;
(7) build the collision-state section (ground contact body via the pinned F04
machinery, trunk bodies via the pinned trunk partition, every obstacle body
via the pinned F07 contact-body constructor); (8) build the initial-state
section (declared spawn/cameras/schedule + derived impact starts + tick-0
solver state of every run); (9) re-derive the full seven-run dynamics trace
through the unmodified pinned M06 `solve_tick` and compare bytes to the
published F07 trace; (10) fingerprint everything into the scene state
document. Fresh instantiations run the SAME procedure in fresh interpreter
processes (`python -B implementation.py materialize --out <scratch path>`);
the build compares all four documents byte-for-byte and refuses any difference
(`f08_scene_state_mismatch`, naming the differing top-level sections).

## 5. Frozen dynamics schedule (the collision reproduction, measured)

Exactly F07's frozen schedule, re-derived from regenerated assets: seven
normal-incidence impact runs (rocks at hull-extent + 0.25 m along the frozen
approach axes; logs/saplings at facet plane + 0.25 m), speed 2 m/s, 30 ticks,
CCD on, through the unmodified pinned M06 law. Every tick's state, contact
records and ledger residual are part of the re-derived trace; the re-derived
trace must equal the published F07 contact_trace.json byte-for-byte (PUBLISHED
bar) and the LEDGER bar applies to every re-derived tick.

## 6. Predictions (frozen before the build; each is falsifiable)

- P0_config_intake: the production loader loads ONLY the frozen configuration
  with every pin present and hash-matching; it refuses missing sections,
  missing assets, corrupted bytes and drifted profile records with named
  codes; no code path substitutes a default value anywhere (the lenient
  double exists only inside falsifier arm FB3).
- P1_seed_asset_reproduction: the three regeneration equalities hold at build
  time (REGEN bar): terrain declaration from seed, terrain bundle from the
  regenerated declaration, obstacle declaration from seed.
- P2_published_evidence_reproduction: the re-derived seven-run trace equals
  the published F07 contact_trace.json bytes and the re-derived V1 clean frame
  equals the published F07 gate artifact bytes (PUBLISHED bar); the ledger bar
  holds on every re-derived tick.
- P3_collision_state_reproduction: the collision-state document is
  byte-identical across three fresh subprocess instantiations and the
  in-process instantiation (CROSS bar).
- P4_initial_state_reproduction: the initial-state document (declared
  spawn/cameras/schedule + derived starts + tick-0 states) is byte-identical
  across the same instantiations (CROSS bar).
- P5_missing_asset_refusals: every falsifier arm of section 7 bites with its
  clean control passing; every refusal names the missing/corrupt asset; the
  lenient loader is caught by the fingerprint gate; a 1e-9 float perturbation
  is caught by the cross-instantiation gate.
- P6_visual_correspondence: with the render and collision arrays element-
  identical (the sealed-line P1 law, re-asserted from the regenerated
  declaration), the pinned ray/geometry classifier reports F07's frozen marker
  table exactly (zero VISIBLE_BUT_MISMATCH, zero UNRENDERED required
  subjects); the forest/visible_static capture is structurally valid with the
  single gate-bound artifact, task_id `F08`, and the profile read READ-ONLY
  from the registry.
- P7_determinism: two full builds produce byte-identical evidence artifacts;
  no RNG except the frozen seeded generators; no wall-clock anywhere in the
  build.

## 7. Falsifier arms (run FIRST, fail-first; each must bite; named refusals)

Every arm carries its OWN passing clean control (F04/F07 house standard) and a
named premature guard (`f08_fb*_premature`); the bite is credited only when
its clean control passes. A non-biting arm fails the whole build
(`f08_falsifier_did_not_bite`). Sandboxes are copies of the pinned siblings
under the attempt scratch; the production pins are never modified.

- FB1_missing_asset_refusal: four sandboxed configurations, each resolving one
  asset class to an absent file (terrain bundle, trunk mesh, obstacle
  declaration, contact law) — the loader MUST refuse each with
  `f08_pin_missing` naming the absent asset. Clean control: the COMPLETE
  sandbox materializes a scene state byte-identical to the production one.
- FB2_corrupt_asset_refusal: flip one byte of a sandboxed trunk mesh copy —
  the loader MUST refuse with `f08_pin_hash_mismatch` naming the asset.
  Clean control: the pristine sandbox copy loads.
- FB3_silent_default_detected: a declared lenient double of the loader
  substitutes an in-code default terrain bundle when the file is missing —
  the double must NOT refuse (the hazard, demonstrated), and the scene
  fingerprint gate MUST fire (default fingerprint != the fingerprint declared
  in the frozen checks of the clean build). Clean control: the same lenient
  double with nothing missing produces the declared fingerprint.
- FB4_seed_perturbation_detected: a configuration copy with
  `obstacle_placement = 4600824` — the regeneration equality MUST fire
  (`f08_seed_reproduction_mismatch`: derived bytes differ from the published
  declaration), proving the seed actually drives the assets. Clean control:
  the unperturbed seed regenerates byte-exact (P1).
- FB5_float_gate_teeth: two fresh instantiations, the second from a
  configuration copy whose declared spawn z is perturbed by +1e-9 — the
  cross-instantiation byte gate MUST fire (`f08_scene_state_mismatch`) naming
  the initial-state section. Clean control: two unperturbed fresh
  instantiations compare byte-identical.
- FB6_off_frame_probe_subject: a required subject 155.7 deg off the V2 view
  azimuth MUST classify OFF_FRAME (tags alone do not establish contact).
  Clean control: the same subject form V2-facing classifies VISIBLE_EXACT.

## 8. Views, cameras and capture binding (frozen)

- Exactly the three profile views, by their exact registry names:
  "clearing overview", "terrain/trunk seam close-up", "side and oblique depth
  checks" — the pinned F07 bookmarks, unchanged.
- Each view: one diagnostic row + one clean row (clean_view_required). Clean
  rows draw the reproduced scene ONLY (no overlays, no labels, depth-tested).
  Diagnostic rows carry ALL FIVE profile layers (render-mesh wireframes,
  collision-surface probe markers, contact-normal arrows + tick IDs, the
  scene-bounds rectangle, stable 3D labels).
- Profile kind `visible_static`: every row is an IMAGE locator (whole_frame
  BMP, 960x540); `capture_sha256` = sha256 of the single gate-bound artifact
  (`evidence/frame_V1_clearing_overview_clean.bmp`); the remaining stills are
  committed hash-listed supplementary files in `capture_layout.files`. Rows
  bind `state_binding.kind='state'` to `assets/scene_configuration.json`'s
  sha256.
- tick_interval [0, 0] (static). Transform-list gate NOT APPLICABLE to a
  static image capture (no video frames exist); the transform-list selftest
  still runs to prove the gate machinery refuses a flipped frame.
- Cameras: perspective, fixed bookmarks, quaternion convention
  quaternion_wxyz_camera_to_frame, forward -Z / up +Y, near/far and vfov per
  the pinned bookmarks, aspect == 960/540, one sample at tick 0; 16-field
  camera records in `evidence/capture_manifest.json`.
- REGISTRY profile validation: `visual_capture.validate_manifest` with the
  profile object read READ-ONLY from agent_slots.sqlite3 (canonical sha256
  3348d00194c8d920abe3c5902c36a0f23088838bd293172f10f65a3de2670852 re-derived
  at build); `visual_gate.verify` re-hashes camera JSON + capture and binds
  capture_sha256. `visual_acceptance` stays false BY DESIGN — independent
  visual review remains mandatory.

## 9. Honest boundaries (inventoried before the build)

- CPU-only, stdlib; no engine run, no native change, no GPU, no training, no
  runtime/playable-build acceptance. The collision path is the pinned M06 law
  through unmodified vendored bytes — no new physics.
- The trunk mesh and its contact binding are PUBLISHED F03 bytes (hash-pinned,
  loaded, not seed-regenerated): F03 authored them as data; no F03 generator
  was published for them. The reproducibility claim for the trunk layer is
  byte-identity of the loaded published bytes inside the materialized scene
  state, honestly scoped.
- The ground co-instantiation refusal (F04 P0 heritage) is re-measured per
  obstacle and recorded; impact runs still instantiate exactly the struck
  obstacle (declared composition scope).
- Cross-instantiation equality is measured on ONE host/interpreter (the
  attempt's Python 3.14); cross-platform/cross-version bit-identity is NOT
  claimed (the pinned generators' 1e-6 grid makes the ASSET bytes portable;
  the M06 trace floats are compared at full repr on this host only).
- Visual acceptance itself belongs to the independent visual reviewer; this
  build's capture machinery is structural (validator + hashes + committed
  stills), not acceptance.
- External read-only reference (not a build input): the world-build-20260928
  lane's composition (`E:\ChimeraWork\world-build-20260928`, WORLD_SEED
  20260928) was read for reconciliation only; recorded raw sha256s —
  composition/composed_meta.json
  `8168382ff2c852b9fbf2c49831ec2021c8c3f5178af95d6ffba0ce55fa3a42f7`;
  composition/composed_world.npz
  `7929e965d0b9fcdff200f76982e461b9f3d2a766c6e46d4154c9e6d25d075cbf`;
  composition/veg_regen_stage/vegetation_meta.json
  `7e6208bdbd4f3106b1fd9acc67e8eabc25564d97b230735884273b534d4f1657`;
  composition/terrain_grid.npz
  `9790fd252825278060f555f545f21b733cb6df9047d0ce1886d006fa87dfd012`.
  It is a DIFFERENT lane (GPU splat world); F08's subject is the sealed-line
  clearing scene; nothing from that lane enters the build.
- Budgets: <= 32 files and <= 16 MB in this contribution directory.

## 10. Amendments (each committed separately BEFORE the implementation/build)

- A1 (this commit, before any implementation commit or build): the pin row for
  F07's obstacle declaration originally carried
  `7164eaf7ef110a8259572526eed0f9e1a5433f95d585cd953c3411634669b81b` — which
  is the declaration's EMBEDDED self_sha256 (the sha of the canonical body
  WITHOUT the self_sha256 field, the value F07's report records), not the raw
  sha256 of the published file bytes that this contribution's pin scheme
  asserts. The raw sha256 of the file bytes at the base revision is
  `73525a3de022d5b8d9901ca90fde77124904471f33a67f2f79a94f7ad1636769`; the
  discovery was made when the strict loader refused on the raw-byte check
  BEFORE any build ran (no evidence existed). The embedded self_sha256 is
  unchanged and continues to be verified by F07's own intake; no published
  bytes differ and no bar moved. The same amendment freezes the RAW sha256 of
  the seven F07 reproduction-target evidence files (contact trace + six
  frames) listed in section 1, replacing "recorded at build".

## 11. Reconciliation disclosures (measured BEFORE this commit; no build run)

Read-only probes over the pinned bytes (attempt scratch only, never evidence),
disclosed here because the predictions rely on them; each is RE-MEASURED at
every build and refused on drift:

- seed 4598321 regenerates the terrain declaration byte-exact (raw file sha
  18dd2ff65410cd1cf184a7a8df61c7503a6ce15083f30159e727e9a8117bfbc1);
- the regenerated declaration regenerates the terrain bundle byte-exact (raw
  file sha 446ed3fbd0f50205c61a7233ceca289bfc3316f76dfc672fec307b20d8305d52);
- seed 4600823 regenerates the obstacle declaration byte-exact (raw file sha
  73525a3de022d5b8d9901ca90fde77124904471f33a67f2f79a94f7ad1636769; the
  declaration's embedded self_sha256 is 7164eaf7ef110a8259572526eed0f9e1a5433
  f95d585cd953c3411634669b81b, F07's recorded form);
- the re-derived seven-run trace equals the published F07 contact_trace.json
  byte-exact, twice in fresh subprocesses (raw sha
  710bfd1993894bd82c496c7c1c095d4201842ba1bebb248776f79392b925f0f7);
- the re-derived V1 clean frame equals the published F07 gate artifact
  byte-exact (sha 6c9316279e1b231b5dd0352b4a10a1b191d7391ffb03895714bd953814a58b87).
