# PREREGISTRATION — MAT2-F05, Specify the terrain range for walking

Frozen BEFORE implementation. Card MAT2-F05, planning id F05, calculation
contract C14 ("Terrain and traversability"), ontology group "Small forest
environment", dependency layer 14, depends on MAT2-F02 (sealed) and MAT2-W06
(sealed). Attempt `264ce332f8cb4db1833ae6eee612b668`; checkout branch-4;
base revision `fa02f07508ee15b7679d0f2a95ac6b1894f77962` (the sealed line tip;
origin/astra/gait-capture; PR #300 merge). Criteria sha256
`cf28ed888e4020f15f00ddd071758e647a55e8dbd6597368bda2a3f2a546dca5` (identical
across dispatch, registry kanban.cards[MAT2-F05], this file, and checks.json
identity — the build re-derives the digest over the registry card and
asserts equality). Scope sha256
`cb5475f8486197a973edc4360b177fc31a629c4f0979ebf80dd76aae57996097`.

done_when (verbatim): **"Slope, obstacle size and surface-friction envelope is
declared from evidence"**. Card observation (verbatim): "Do not assume
flat-ground training transfers to arbitrary terrain".

Verification profile (registry `kanban.cards[MAT2-F05].spec.ontology_qualification
.task.verification_profile`, read READ-ONLY at capture time, canonical sha256
`9a8863e424aef3ca6fcf5a39f30cbdb27723f8df23ecc25b5f5604f80a3fa1e7`):
id `forest`, kind `visible_static`, views ["clearing overview",
"terrain/trunk seam close-up", "side and oblique depth checks"],
clean_view_required true, diagnostic_layers ["render mesh", "collision
surfaces", "normals/contact markers", "scene bounds", "stable 3D labels"],
numerical_evidence_required true, 16 required camera fields. PROFILE-KIND
CAPTURE CHECK (done at join, before this prereg): kind is visible_static —
static-image evidence (committed BMP stills + depth, clean/diagnostic pairs)
is profile-conformant; NO motion capture is required for this card (the
motion-capture law applies to `motion` profiles, e.g. F04/W06r1). CPU-only
card: derivation + records + static renders; no GPU, no engine run, no
training.

## 1. Reconcile-first (what is reused, never re-implemented)

The sealed line at the base revision already carries the C14 heritage this
card declares over; all of it is reused as pinned bytes:

- **F01/F02** — the certified clearing scene: render arrays == collision
  query surface (exact), frozen resting window [0.0015, 0.0025]+site_band,
  ground material `clearing_ground_topsoil` mu_s 0.9 / mu_k 0.65 declared
  **synthetic_authored, recorded-not-derived** (F02 PREREGISTRATION section 2).
- **F04** — frozen contact cases (no tunnelling: worst penetration 0 m;
  ghost-support bites; seam/trunk rest windows).
- **F07** — the declared obstacle vocabulary: 7 obstacles (3 rocks, 2 logs,
  2 stands) whose render sections and collision bodies are the same vertex
  arrays; the invisible-wall audit (0 unattributed blocked cells); 12 BFS
  routes with measured clearance and slope.
- **W03** — the sealed walk scene `scene.json` (sha `f6844eea...`): a FLAT
  plane, `contact_plane_height_m` 0.004, `contact_friction` 0.6, 300 Hz.
- **W05/W06** — the walk-tier receipts: three seeds trained and evaluated on
  flat ground only; all three degraded (verdict FAILURE x3); velocity
  envelope 2.977443609022557 m/s; zero tuned runs.
- **G04 + the g04-friction records lane** — the friction law is placeholder
  class with the measured human-volar envelope (L1/L2) as falsifier-band
  context only; REPIN ORDER 2 holds (mu_s 0.6 / mu_k 0.4 are NAMED
  placeholders; no measured macaque volar friction exists).

This card adds NO physics constant and NO solver: it is a derivation card.
Its "implementation" is the mechanical derivation of the declared envelope
from pinned sources, its proof (falsifiers + correspondence probes), and the
generated declaration artifact.

## 2. The frozen statement (what "declared from evidence" means here)

Every envelope row is one of exactly four classes, and the declaration is
refused if any row claims a class its source cannot support:

1. **MEASURED** — read from a pinned receipt/record produced by a sealed run
   (e.g. F07 route slopes, terrain-pass grid statistics, W06 seed outcomes).
2. **AUTHORED-DECLARED** — an authored law on a pinned carrier (e.g. the
   clearing `max_slope_bound`, the W03 plane height, walkability class
   thresholds). Carried with its carrier and its recorded-not-derived status.
3. **NAMED-PLACEHOLDER** — a declared placeholder whose measured replacement
   is an acquisition debt (all friction values; each names its debt owner).
4. **ABSENT** — a named variable with a recorded debt; never a synthetic
   value (the G04 "named absent variables" form).

## 3. Pins (raw sha256 asserted at every run; the pin wall)

In-tree (base `fa02f075`):

| pin | path (contributions/) | sha256 |
|---|---|---|
| clearing_declaration_json | MAT2-F01/evidence/pins_materialized/clearing_declaration.json | `18dd2ff65410cd1cf184a7a8df61c7503a6ce15083f30159e727e9a8117bfbc1` |
| terrain_bundle_json | MAT2-F01/evidence/pins_materialized/terrain_bundle.json | `446ed3fbd0f50205c61a7233ceca289bfc3316f76dfc672fec307b20d8305d52` |
| f01_implementation_py | MAT2-F01/implementation.py (render law + classify) | `f01 sha at base; re-hashed in build` |
| obstacle_declaration_json | MAT2-F07/assets/obstacle_declaration.json | `73525a3de022d5b8d9901ca90fde77124904471f33a67f2f79a94f7ad1636769` |
| f07_checks_json | MAT2-F07/evidence/checks.json | `0a7e94b545e4add955eb3f0315f8a783f00e2ebbcf4a2a44f43398b72916fb70` |
| w03_scene_json | MAT2-W03/scene_out/scene.json | `f6844eeae3dc87170a572ccdeedf326a6cac4f73d1448941808bd8b25a8db342` |
| w05_seed_20260919_receipt | MAT2-W05/receipts/seed_20260919_receipt.json | `b866e9b1e2a3d516a960a88362c95d2f8211d28b894cc4d8c16dcebc4dc8b896` |
| w05_seed_20260920_receipt | MAT2-W05/receipts/seed_20260920_receipt.json | `3d795b5ca523289c1ceac7dac72070875d8cc4b8e24e4ac2a5a64a9733e766ff` |
| w05_seed_20260921_receipt | MAT2-W05/receipts/seed_20260921_receipt.json | `10c4090473c75ec99559dd9f1f13729d96c3c7d5cf037569c63253e308f472af` |
| w06_eval_summary | MAT2-W06/receipts/evaluation_summary.json | `a1af58baf15edd7ac595b5bb4571e13ed44780f77faf5a761355140f456b075a` |
| w06_seed_20260921_evaluation | MAT2-W06/receipts/seed_20260921_evaluation.json | `89baa5472076a1a8669389bc207fd49e6b06645b6db2519ca5d333cafe26015b` |
| g04_report_md | MAT2-G04/REPORT.md | `dfca5b5556efe018ca09be4577bf6fbb5df38bb5c9ebc33d15bd18646ba349c8` |
| f02_prereg_md | MAT2-F02/PREREGISTRATION.md | `19c4277b9d2c102ea5ce77bc1b4fa8d128370ce344f782a79d088d0cf458331d` |
| f02_checks_json | MAT2-F02/evidence/checks.json | `9531edf1f74ba6dc85e3cd5e2029711dc6803b78b23d8b75df736f4c36fa719d` |
| f04_checks_json | MAT2-F04/evidence/checks.json | `4ff2ee5d00d046ce6a734c10a39b3562c306ac245074a872a824efecabe50c55` |
| contact_law_json | MAT2-M06/contact_law.json | `583962c29f18118a478dedb167f2c3667414b86f5cab4ee54763416f1df7e41b` |

Evidence-store (durable vault, store-relative paths, verified by the store
manifest; copied via `anchor.py add --card MAT2-F05` before this prereg):

| pin | store path | sha256 |
|---|---|---|
| friction_sources_md | MAT2-F05/source/FRICTION_SOURCES.md | `336118e929bd0b4fb067db5a448dc2e348fed073007787635549a4cf1cf5868b` |
| terrain_meta_json | MAT2-F05/source/terrain_meta.json | `ff15fb1db3dcc128a531d21ef64d3ab62ae78190b64db36f70b5d273c1425681` |
| terrain_report_md | MAT2-F05/source/TERRAIN_REPORT.md | `2b4d9905be1f9f888a3ff33cb4c22a23f009053471c4fd609280bc7b2cba4672` |
| composed_meta_json | MAT2-F05/source/composed_meta.json | `8168382ff2c852b9fbf2c49831ec2021c8c3f5178af95d6ffba0ce55fa3a42f7` |
| ingestion_spike_md | MAT2-F05/source/INGESTION_SPIKE.md | `218b34614d8917eceb3f4ea2a6404c5715f8e25f71e57989c53213d7498e512b` |
| terrain_grid_npz | MAT2-F05/source/terrain_grid.npz | `9790fd252825278060f555f545f21b733cb6df9047d0ce1886d006fa87dfd012` |

The f01 pin's exact base sha is filled by the build's pin wall (the prereg
freezes the PATH and the assertion, not a hand-copied digest, per the P7
lesson that hand-copies rot).

## 4. Frozen checks and predictions (P1-P8)

- **P1 pin wall** — every pin above raw-sha256 verified at every run;
  any drift refuses (`f05_pin_drift`). No prediction (assertion).
- **P2 slope-envelope derivation** — from the pinned clearing declaration:
  the mound law `h = A*(1+cos(pi*d/R))/2, d<R` has max grade exactly
  `A*pi/(2R)`; predicted per-mound grades in (0.025, 0.039) m/m and scene
  max = m3 = 0.03795552514626025 m/m (1.0 deg window, measured from the pin
  at build time); ALL mound grades <= the declared `max_slope_bound` 0.05
  m/m (prediction: margin in (0.012, 0.025)). From the pinned F07 receipt:
  measured max sampled route slope == 0.026054 (exact seal equality) and
  measured global min route clearance == 0.257478 m (exact seal equality);
  8 of 12 routes carry slope 0.0 (flat; the sealed correction-recorded
  count). From the pinned terrain-pass record (context, world-scale): law
  grid slope mean 3.8120480234530243 deg, max 29.59015617654052 deg; core
  4 km tile max 25.62 deg-class recorded in TERRAIN_REPORT section 3;
  walk classes easy<10 / moderate 10-20 / steep 20-30 / impassable>=30 deg
  are AUTHORED-DECLARED for a reference earth-contract biped and NOT
  qualified for this walker (TERRAIN_REPORT section 8 item 6 — carried as
  class AUTHORED-DECLARED, never as a walker capability).
- **P3 obstacle-envelope derivation** — from the pinned obstacle
  declaration: exactly 7 obstacles in the frozen splitmix64 (seed 4600823)
  order; rocks' bbox extents within (0.30, 0.57) m per axis; logs capsule
  radii {0.141408, 0.128476} m and half-lengths {1.249721, 1.035033} m;
  stands disc radius 0.51 m, height 1.6 m; placement constraints body
  envelope 0.25 m, spawn_min_dist 2.5 m, trunk_min_dist 2.0 m, pair_gap
  0.5 m, centre box +/-19 m. From the pinned F07 receipt: the walkability
  audit attributes EVERY blocked cell to a declared record (0 unattributed);
  all 12 routes reached; global min clearance 0.257478 m >= the declared
  0.25 m body envelope (bar >= 0.25 - 1e-9). Traversal mode: route-around
  avoidance; NO step-onto-obstacle walk case exists anywhere in the sealed
  line (F07 honest boundary heritage — recorded as ABSENT with owner F06).
- **P4 friction-envelope derivation** — from the pinned W03 scene:
  `contact_friction` == 0.6 exactly. Class table: walk plane 0.6
  (NAMED-PLACEHOLDER; G04/REPIN ORDER 2 debt), ground 0.9/0.65
  (synthetic_authored, F02 prereg), obstacle/trunk matter 0.6/0.6 (F03
  UNEVIDENCED-PLACEHOLDER, G04 debt), probes 0.6/0.4 (M06 block), pair rule
  `elementwise_min` (pinned contact_law.json). Measured context band (L1/L2,
  quoted from the pinned FRICTION_SOURCES record): no macaque value exists
  (GAP P3/L9); human-volar dry load-matched class centers 0.41-0.42 at
  14.8 N; low-load span 0.5-3.0 across 0.03-1.64 N; the placeholders are
  INSIDE the broad span and OUTSIDE every load-matched class — carried as
  the falsifier band, never a re-pin. Slope-friction consistency: at the
  declared scene slope bound 0.05 m/m, tan(slope) = 0.05 < mu_s/12 for every
  declared mu_s >= 0.6 (prediction: margin factor >= 12.0 exactly
  12.0-18.0); the F02 P6 heritage expectation (gravity alone must not
  sustain sliding on the declared envelope) is thereby consistent with the
  declared numbers.
- **P5 walk-plane identity (the load-bearing flattening)** — the pinned W03
  scene `contact_plane_height_m` == the pinned composition flatten
  `plateau_z_m` == 0.004 exactly (to the last bit); the pinned composition
  flatten block: plateau r <= 6.0 m, splice ring to 18.0 m, authored rise
  32.296774070867706 m at the plateau centre (0.4590553506803305,
  -0.027113024817603366). The terrain-law grid bilinear read at the same
  centre is predicted < -30.0 m (measured exactly at build; preflight class
  -32.29 m, the composition2 report section 8 item 1 disagreement): the
  walk surface is the AUTHORED plateau, NOT the raw grid — any consumer
  binding the plane to the grid read is 32 m-class wrong (R3). Prediction:
  |grid_read - plateau| in (30.0, 35.0) m.
- **P6 render/collision correspondence at frozen probes** — reusing the
  pinned F01 render law + classify (pure ray/geometry, markers never read
  pixels): the frozen probe set (P-sites below) classified across the three
  registry views; prediction: zero VISIBLE_BUT_MISMATCH; every view carries
  >= 1 VISIBLE_EXACT required subject; scene-bounds layer renders the post
  ring (F01 heritage).
- **P7 capture** — campaign manifest `chimera.visual_capture_manifest.v1`,
  task_id SHORT form `F05`, profile object read READ-ONLY from the registry
  (canonical sha asserted `9a8863e4...`); 3 view rows x (clean + diagnostic
  + depth), 16-field camera records; single gate-bound artifact
  `evidence/frame_V1_clearing_overview_clean.bmp`; per-row raw_sha256 from
  committed bytes; `visual_capture.validate_manifest` structurally_valid on
  the committed bytes.
- **P8 determinism** — two full builds; canonical receipts byte-identical;
  no wall-clock, no RNG.

## 5. Falsifier arms (each bites fail-first, each against its own passing
clean control, named `<task>_fb<n>_premature` guards; a non-biting arm
refuses the build)

- **FB1_slope_envelope_mute** — perturb the declared `max_slope_bound` to
  0.01 (< the derived mound max 0.03796): the envelope build must refuse
  (`f05_declared_bound_below_measured`). Clean: 0.05 passes. (A declared
  slope envelope BELOW the measured terrain grade would be a false
  declaration.)
- **FB2_undeclared_blocker** — inject one undeclared blocker cell into the
  walkability attribution: unattributed count > 0 must refuse
  (`f05_invisible_wall`). Clean: 0 unattributed (F07 FB1 heritage re-proven
  on this card's audit copy).
- **FB3_unnamed_placeholder** — emit any friction row with its
  placeholder/debt naming stripped: the declaration validator must refuse
  (`f05_unnamed_placeholder`). Clean: every friction row carries
  class + debt owner. (The GAP verdict law: a placeholder presented without
  its name is laundered evidence.)
- **FB4_grid_plane_binding** — bind the walk plane to the terrain-grid
  bilinear read (-32.29 m class) instead of the authored +0.004: the plane
  identity check must refuse with the measured 32.297 m-class disagreement
  (`f05_grid_plane_mismatch`). Clean: 0.004 == 0.004 exact.
- **FB5_off_frame_probe_subject** — a required subject 155.7 deg off the
  V2 seam camera classifies OFF_FRAME (F01/F02 heritage; tags alone do not
  establish contact). Clean: the in-frame subject is VISIBLE_EXACT.
- **FB6_render_collision_decouple** — perturb one render vertex vs the
  collision surface at a probe ray: the classify must report the mismatch
  class, not VISIBLE_EXACT (`f05_decouple_detected` in the bite record).
  Clean: unperturbed ray VISIBLE_EXACT.

## 6. Frozen probes and views (before execution)

- Views (the registry profile, verbatim): V1 `clearing overview`,
  V2 `terrain/trunk seam close-up`, V3 `side and oblique depth checks`;
  clean + diagnostic pairs share the bound camera per view (F01 pattern);
  depth renders per view; diagnostic layers = the five registry layers.
- Probes (clearing frame, from the pinned declaration/sealed receipts):
  P-spawn (0, 0); P-mound-top m1 (-18.312917, -6.422639); P-mound-flank m1
  (-15.035646, -6.422639); P-seam (11.226783, 2.471766); P-mound-top m3
  (19.265584, 6.057064) — the m3 site is the steepest declared mound
  (grade 0.03795552514626025); each probe carries its query height + normal
  recorded beside the classify outcome (the numerical-evidence requirement).
- Cameras: the F01 frozen view definitions reused byte-identical in
  parameters (eye/target/FOV recorded in the 16-field rows); frame_id
  prefix `MAT2-F05/`.

## 7. Disclosure policy

Amendments land as separate commits AFTER this prereg and BEFORE the first
build run, each citing what motivated it. Measurement-driven disclosures go
in the generated report. No bar is loosened after measurement. The report is
GENERATED from checks.json; every number is lint-traced
(lint_report_numbers.py with --selftest); the suite runs 0 skips.

## Amendment A1 (2026-09-29, before the first completed build run)

P3's rock-extent prediction band is corrected from "(0.30, 0.57) m per axis"
to "(0.25, 0.57) m per axis". Motivation: the band was hand-derived from the
F07 report's prose instead of the pinned declaration bytes; the first build
attempt exposed the sealed per-axis extents rock_02 z = 0.254639 m and
rock_03 z = 0.285039 m below the preregistered band. These are READS of
declared data (not measurements), so this is a prediction-typo correction
against the pinned bytes — the sealed declaration is unchanged and no
measured bar is touched. The envelope's size-band text is corrected to
"rocks 0.25-0.57 m bbox" accordingly.

## Amendment A2 (2026-09-29, before the candidate commit; naming only)

Two refusal-code NAMES in section 5 prose are corrected to the implemented
codes the receipts record: FB1's observed refusal is
`f05_bound_margin_band`/`f05_mound_exceeds_bound` (the prose had
`f05_declared_bound_below_measured`), and FB4's observed refusal is
`f05_plane_identity` (the prose had `f05_grid_plane_mismatch`). No bar, no
arm, no probe, no view, and no prediction is changed — the arms bite on the
tampered input and pass on the clean input exactly as frozen; only the
identifier strings are aligned with the receipt bytes. The generated report
renders the ACTUAL codes from checks.json.

## Amendment A3 (2026-09-29, before the candidate commit; packaging only)

P7's committed capture set is the SIX profile frames (3 registry views x
clean + diagnostic). The per-view depth renders are COMPUTED and RECEIPTED
(per-view depth range in checks.json P7) but their BMPs are NOT committed:
nine 1280x720 BMPs would put the contribution at 23.7 MiB, over the P9
request cap (<= 32 files / <= 16 MB); six committed frames are 15.82 MiB.
Depth-ordering evidence remains in the receipt: the pure ray/geometry
classify (OCCLUDED outcomes and the analytic trunk-silhouette predictions,
F07 precedent) plus the recorded depth ranges; the depth BMPs are
deterministically regenerable from the pinned bytes. No frame, view, probe,
bar or prediction is changed — a packaging-bound disclosure only. (The
prereg's P7 wording "3 view rows x (clean + diagnostic + depth)" is hereby
amended to "3 view rows x (clean + diagnostic), depth receipted not
committed".)

## Amendment A4 (2026-09-29, before the candidate commit; committed-still
carrier only)

The six committed stills are carried as LOSSLESS PNGs written by a
card-local deterministic stdlib encoder (filter-type-0 rows, zlib level 6),
not as BMPs: the six 1280x720 BMPs alone are 15.82 MiB and put the head
contribution at 16.17 MiB, over the P9 request cap. The build writes the
pinned render law's BMP output, encodes the PNG, RE-DECODES it and proves
pixel identity against the BMP (`png_pixel_identity`, receipted per frame),
records each BMP's sha256 in checks.json (the V1 clean BMP run output is
byte-identical to the sealed F01/F02 overview capture,
sha `b4aab2898a01afd9...`), then removes the run-output BMP. The committed
PNG is therefore the lossless, identity-proven carrier of the SAME pixels
the sealed render law produced; no pixel, view, probe, bar or prediction is
changed. W06 precedent: committed PNG stills are established campaign
practice for static captures.

Composed against CARD_STARTER.md v3; house standards IMPLEMENTER_CHECKLIST.md
(G1-G9) and TOOLKIT.md (P1-P9) cited at the candidate commit.
