# MAT2-F04 PREREGISTRATION — ground and trunk contact geometry, frozen cases

Committed BEFORE any implementation file, harness run, measurement or capture
frame existed (git-provable: this is the first commit of this contribution
directory on the attempt branch). Everything below is frozen now; amendments,
if any, will be separate commits BEFORE the implementation commit and BEFORE
any build, each disclosing what changed and why. No bar is tuned after a
measurement is seen.

## 0. Task and criteria identity (verbatim, not paraphrased)

- card: MAT2-F04; planning id F04; attempt `c4064f0e999c40b3a9b18892b034f83c`;
  arrival `arrival-a6cc16fce0954ee789086633f911e1a3`; criteria sha256
  `4c0a901840d34736a3bcd4dee6a70e750b731a83ef4152a573b99e2dae6b7669`;
  scope sha256 `cb5475f8486197a973edc4360b177fc31a629c4f0979ebf80dd76aae57996097`;
  base revision `459ab80136c1491138dece91ebbbf62ab8349cb1` (branch-3 after
  fast-forward; = merge of PR #249 review/MAT2-F02 and carries merged F02/F03).
- done_when (verbatim): "No unacceptable tunnelling, ghost support,
  interpenetration or visual/collision disagreement in frozen cases"
- falsifier (verbatim, card): "A violated task acceptance clause, hidden/clipped
  required geometry, inconsistent numeric evidence or mismatched clean/diagnostic
  state fails."
- REGISTRY profile object (read READ-ONLY from
  `E:/ChimeraWork/monkey-coordination/agent_slots.sqlite3`,
  `kanban.cards[MAT2-F04].spec.ontology_qualification.task.verification_profile`;
  canonical sha256 recorded in the receipt): id `contact-motion`, kind `motion`,
  subject "Verify ground and trunk contact geometry", scenario "Qualify only
  this task: No unacceptable tunnelling, ghost support, interpenetration or
  visual/collision disagreement in frozen cases Profile procedure: Replay
  crossing and impact trajectories at ground, trunk and seams; inspect full
  tick intervals for tunnelling and render/collision disagreement. Use the
  task-owned subset of layers/behaviors. Inventory absent or unresolved
  components explicitly; do not require downstream skills to accept an upstream
  interface. Freeze exact applicable probes and views before execution.",
  diagnostic_layers ["render and collision surfaces", "probe trajectories",
  "contact normals and tick IDs"], views ["clearing contact overview",
  "terrain/trunk seam impact close-up", "opposite-trunk and oblique depth
  checks"], clean_view_required true, numerical_evidence_required true,
  falsifier: "A violated task acceptance clause, hidden/clipped required
  geometry, inconsistent numeric evidence or mismatched clean/diagnostic state
  fails."
- task_id in the capture manifest/context: `F04` (SHORT form).

## 1. Reconcile-first: reused published bytes only (nothing re-derived)

All input pins are published bytes of merged cards, asserted by raw sha256 at
every run; the harness refuses on any mismatch (`f04_pin_*`). Paths are the
committed sibling contribution directories at the base revision.

| pin | published location | raw sha256 |
|---|---|---|
| terrain asset (render arrays = query triangulation) | contributions/MAT2-F02/pins/terrain_bundle.json | `446ed3fbd0f50205c61a7233ceca289bfc3316f76dfc672fec307b20d8305d52` |
| terrain query surface | contributions/MAT2-F02/pins/terrain_query.py | `b1e244b8843671afc29af530c4725bf812ffd5f8967130f0202792aeb7a8cce1` |
| terrain bundle module/validator | contributions/MAT2-F02/pins/terrain_bundle.py | `c6ada25a1b6192aa86add8b09bc19161c0cd81e3fb3d4bd267492660c0be8f2e` |
| clearing recipe | contributions/MAT2-F02/pins/clearing_recipe.py | `ab800d2257655118296519b606c77ddc7116f524ae0c2e6a0bab3b38473892dc` |
| clearing declaration | contributions/MAT2-F02/pins/clearing_declaration.json | `18dd2ff65410cd1cf184a7a8df61c7503a6ce15083f30159e727e9a8117bfbc1` |
| trunk asset declaration | contributions/MAT2-F02/pins/trunk_declaration.json | `94ff906ec5e8b8388e4de318aa3321bad9c791fbb168e8234c371ed1d327e3f1` |
| F01 render law | contributions/MAT2-F02/pins/f01_implementation.py | `50e191cfc6f592fd9919534c8986c049939a4e88c4922e135f383bbf06e693af` |
| M06 shared contact path | contributions/MAT2-M06/local_contact.py | `1cd662b30343011eb4a0a01e461a1e82b00482d0371857c8e42d6bec8f9a28dc` |
| M06 contact law declarations | contributions/MAT2-M06/contact_law.json | `583962c29f18118a478dedb167f2c3667414b86f5cab4ee54763416f1df7e41b` |
| F03 pinned trunk mesh asset | contributions/MAT2-F03/assets/trunk_01_mesh.json | recorded at run time from the bytes (published F03 asset) |

Merged-card constants reused as frozen (no new physics constants): ground
`monkey_clearing_ground`/`clearing_ground_topsoil` mu 0.9/0.65 thickness 0.002
(F02); trunk `trunk_01.*`/`wood_trunk_01` mu 0.6/0.6 thickness 0.0 solid (F03,
friction remains the declared UNEVIDENCED-PLACEHOLDER, G04 debt); probe shell
matter `mass_tetra` 0.12 kg mu 0.6/0.4 thickness 0.002 (F02/M06); M06 law
constants g 9.81, dt 0.005, slop/margin 1e-5, beta 0.2, restitution 0,
CCD max_iters 64 / tol 1e-12 (contact_law.json). Pre-trunk-scene scratch
measurements (attempt workspace only, before this prereg): minimum
ground<->trunk-base distance is exactly 0.0 m at the seam ring — recorded here
because P0 below predicts its consequence under the pinned law.

## 2. Frame map and instantiated-parts scope (declared)

- ONE global frame map for BOTH assets (F02's declared proper rotation,
  det=+1): clearing (x, y up, z) -> contact (x, -z, y); M06 gravity (-Z) maps
  back to clearing gravity (-Y). Inverse contact->clearing (a, b, c) -> (a, c,
  -b). Ground AND trunk bodies and all probes use this same map; records are
  mapped back before any comparison with clearing-frame surfaces.
- Contact-frame trunk geometry: base at (11.976783, -2.471766, 0.0), axis +z,
  R = 0.037 m, H = 1.158 m, 128 pinned triangles.
- Pinned-pinned scoping (F03 Amendment A3 heritage, now measured at the
  ground/trunk seam): the trunk base ring touches the ground plane at exactly
  0.0 m, so any solve containing BOTH a ground body near the trunk AND a trunk
  part presents the pinned law a both-pinned exact-contact pair, which M06
  refuses (`nonfinite_state`, inv_mass sum 0). P0 measures and records this
  refusal first. Every dynamic experiment therefore instantiates exactly the
  static parts it touches (declared per scenario in section 4); asset identity
  (P1) is always measured on the FULL pinned bodies. The limitation of that
  composition is inventoried in section 8, never silently repaired.

## 3. Frozen numerical bars (all derived from pinned records; none tuned)

| id | bar | derivation |
|---|---|---|
| PEN_BAR_M | 1e-4 m | P06 operator-decision request `contact-geometric-tolerance` option 2 (solver-anchored); M06 X1 steady penetration measured 0.0 against the same bar. Worst violation of: probe vertex below the local query height (ground solves), vertex inside the analytic trunk solid (trunk solves), over all ticks of all CCD-on runs |
| REST window | [0.0015, 0.0025] m + site_band | F02 P3 frozen form, verbatim, incl. the site's own within-cell diagonal relief |
| TRUNK_REST_DISP_BAR | 2e-3 m | F03 S3 frozen cap-rest displacement bar |
| PRE_OVERLAP | gap_m > 0.0 | every first-contact record of every CCD-on run must be detected BEFORE mid-surface overlap (M06 X4 form); any `kind='ccd'` detection with gap <= 0 is unacceptable tunnelling |
| LEDGER_BAR | 1e-12 | per-tick ledger residual and reciprocity residual of every run (M06 Amendment A2 identity) |
| PLANE_BAR / NORMAL_BAR | 1e-9 | F02 P4: contact points lie ON render triangles; face normal == query normal at the recorded triangle centroid |
| TRUNK_RADIAL_TOL | 2e-4 m | F03 declared render/collision tolerance; collision vertices vs analytic cylinder and contact-point radial identity |
| SPEED_BAR | 1e-4 m/s | F02 resting-speed bar |
| SEAM_BAND_M | [0.0, 0.15] altitude (clearing y) | declared seam region: the lowest lateral segments at the trunk/ground crease; the seam impact's contact altitude must land inside |

## 4. Frozen probes and scenarios (exact, deterministic, no RNG, no wall-clock)

Probe shell: F02's 12-triangle box, half 0.1 m, mass_tetra 0.12 kg, mu 0.6/0.4,
thickness 0.002. All ticks through unmodified `local_contact.solve_tick`.
Scenario = (instantiated static parts, probe initial state, tick count).

| scenario | static parts instantiated | probe initial state (contact frame) | ticks |
|---|---|---|---|
| G_HIGH (ground crossing, CCD on) | ground (full 3200-tri render slice) | centre above S1 (0,0): bottom at h_query+0.5, v=(0,0,-4) m/s | 30 |
| T_CROSS (trunk crossing, CCD on) | trunk_01.lateral (64 tris) | centre at clearing (11.626783, 0.5, 2.471766), i.e. contact (11.626783, -2.471766, 0.5), v=(+4,0,0) m/s at the lateral facet nearest +x | 30 |
| SEAM_HIGH (seam crossing/impact, CCD on, phased; Amendment A1) | phase A: none (ballistic approach, clearance measured); phase B: trunk_01.lateral | start clearing (11.263783, 0.14, 2.471766), v=(+4,0,+0.5) m/s; phase A runs until the PRE-tick remaining face-to-cylinder distance is within one per-tick motion (0.02 m), then the trunk is instantiated and phase B continues to the first trunk contact + 3 ticks (within the window) | 40 |
| G_SEAM_REST (ground rest at the seam approach) | ground | F02 S4 site (11.226783, 2.471766), bottom at h_query+0.05, v=(+0.2,0,0) toward the trunk | 40 |
| TRUNK_TOP_REST (cap rest) | trunk_01.base_cap, trunk_01.top_cap (never mutually touching) | F03 S3 form: tetra on top_cap at (0.02, 0.01) cap-plane offset, 2e-5 above | 40 |

Per-tick inspection (the profile's "inspect full tick intervals"): every
scenario records, for EVERY tick, the probe vertices, velocity, all contact
records (kind, toc, gap, jn, jt, normal, points, surfaces, tick id) and the
clearance numbers; the committed trace `evidence/contact_trace.json` is the
state binding of every capture row. Interpenetration and clearance are measured
per tick over the FULL interval, not at the last tick only.

## 5. Predictions (frozen before the build; each is falsifiable)

- P0_combined_instantiation_refusal: solving ground (near-trunk region present)
  together with ANY trunk part is REFUSED by the unmodified M06 law with
  `nonfinite_state` (both-pinned exact contact at the seam ring). Any other
  outcome is disclosed as an amendment before the build proceeds.
- P1_tied_asset_identity: the collision bodies ARE the rendered assets, exact:
  ground body vertices == frame-mapped render ground vertices (exact equality,
  both mapped orders hashed; extent == rendered half width 20.0); trunk body
  vertices == the pinned trunk render mesh (exact); surface ids match the
  render sections/declaration.
- P2_shared_path: every support/impact impulse in every scenario appears as a
  `chimera.local_contact.v1` record of the byte-identical M06 module; per-tick
  ledger and reciprocity residuals <= 1e-12; declarations match
  contact_law.json.
- P3_no_tunnelling_ccd_on: in every CCD-on scenario, the FIRST contact record
  of each contact episode has kind 'ccd' with gap_m > 0 (pre-overlap), and the
  per-tick interpenetration metric never exceeds PEN_BAR_M (1e-4).
- P4_no_interpenetration: worst penetration over all CCD-on runs <= 1e-4 m;
  ground rests land inside the frozen REST window (with site_band); the trunk
  cap rest displaces <= 2e-3 m; every rest speed <= 1e-4 m/s.
- P5_no_ghost_support: no support impulse exists without a real contact record
  (ledger identity, P2); rests at the seam approach site and on the trunk rest
  in their frozen windows with NO support records pointing at surfaces the
  probe does not touch; combined-instantiation refusal (P0) means no seam
  support is invented by composition.
- P6_contact_geometry_identity: every ground contact point lies ON its render
  triangle (plane err <= 1e-9) with face==query normal (1e-9); every trunk
  contact point lies within TRUNK_RADIAL_TOL of the analytic cylinder surface
  and on its recorded render triangle; seam-band contacts land at altitude in
  [0, 0.15].
- P7_no_visual_collision_disagreement: with render and collision arrays
  element-identical (P1), the pure ray/geometry marker classify (F01/F02/F03
  oracle form, markers never read pixels) reports every assigned marker in
  every view VISIBLE_EXACT (normal from the incident-face set at 1e-12); zero
  VISIBLE_BUT_MISMATCH, zero UNRENDERED required subjects; the seam impact
  marker is inside the V2 frustum with margin >= 3% per side (clipped-geometry
  guard).
- P8_determinism: the full pinned pass run twice produces byte-identical
  artifacts (checks, bites, trace, stills) and a byte-identical video; no RNG,
  no wall-clock anywhere in the build.

## 6. Falsifier arms (run FIRST, fail-first; each must bite; named refusals)

- FB1_ccd_off_ground_tunnels: rerun G_HIGH with `ccd_enabled=False` — the
  control MUST first contact only after mid-surface overlap (penetration >
  PEN_BAR), demonstrating the tunnelling the shipped law prevents. Bites iff
  the control's first detection shows penetration > 1e-4 while the same
  trajectory under the shipped law is pre-overlap clean.
- FB2_ccd_off_trunk_tunnels: rerun T_CROSS with CCD off — the control MUST
  first detect with a vertex already inside the analytic cylinder (> PEN_BAR).
  (Operationalized by Amendment A2: the solver's first-contact mid-surface
  overlap, gap_m < 0 with penetration_m = -gap_m > PEN_BAR.)
- FB3_ghost_support_ground: raise ONE ground contact vertex under S1 by +1 cm
  (render/query untouched, F02 FB1 form) — the resting window MUST be
  violated (ghost support detected).
- FB4_ghost_support_trunk: move ONE trunk lateral vertex radially inward by
  1 cm (F03 B1 form) — the render/collision correspondence bar (2e-4) MUST be
  violated.
- FB5_forced_interpenetration: place the probe initially 1 cm inside the trunk
  solid — the interpenetration metric MUST read the forced overlap (> PEN_BAR)
  and the run is refused by the P3/P4 bars (the metric has teeth).
- FB6_visual_collision_decouple: perturb ONE vertex of a COPY of the render
  ground arrays by +1 cm while the collision body is untouched — P1 array
  equality MUST fire (render/collision decoupled detected) and the marker
  classify MUST flip to VISIBLE_BUT_MISMATCH.
  (Operationalized by Amendment A3: the +1 cm raise is applied to ALL THREE
  vertices of the ground triangle the marker's classify ray actually hits.)
- FB7_off_frame_probe_subject: a required subject 155.7 deg off the V2 view
  azimuth MUST classify OFF_FRAME (tags alone do not establish contact).

Every bite records the failing numbers in `evidence/bites.json` before the
pinned pass is assembled; a non-biting falsifier fails the whole build
(`f04_falsifier_did_not_bite`).

## 7. Views, cameras and capture binding (frozen)

- Exactly the three profile views, by their exact registry names:
  "clearing contact overview" (wide bookmark over the clearing),
  "terrain/trunk seam impact close-up" (bookmark framed on the trunk base at
  the seam), "opposite-trunk and oblique depth checks" (bookmark from the
  opposite side of the trunk, oblique elevation).
- Each view: one diagnostic row + one clean row (clean_view_required).
  Clean rows draw the pinned assets and the replaying probe shell ONLY — no
  overlays, no labels, depth-tested. Diagnostic rows carry ALL THREE profile
  layers: render mesh wireframe + collision-surface probes (render and
  collision surfaces), the probe path polyline (probe trajectories), and
  contact-normal arrows + tick IDs at impact points (contact normals and tick
  IDs).
- Profile kind is `motion`: every row is a VIDEO locator (lossless FFV1 in a
  single MKV, 1 fps) whose window replays the sha-bound solver states of its
  scenario set; the single video file is THE capture artifact and
  `capture_sha256` = its sha256 (one on-disk artifact in the attempt
  workspace, path+hash recorded; independent review consumes the hashes and
  committed stills). Rows bind `state_binding.kind='trace'` to
  `evidence/contact_trace.json`.
- Committed stills: the arrest/impact-tick frame of each of the six rows,
  rendered by the same rasterizer, as `evidence/frame_<row>.bmp`,
  sha256-listed in the manifest capture layout (supplementary, not manifest
  rows). Viewport 960x540 (publication byte budget; declared per row in the
  16-field camera record; the pinned render law is otherwise unchanged).
- Cameras: perspective, fixed bookmarks, quaternion convention
  quaternion_wxyz_camera_to_frame, forward -Z / up +Y, declared near/far,
  declared fov, aspect == 960/540; two or more samples spanning the manifest
  tick interval. 16-field camera records in `evidence/camera_manifest.json`.
- REGISTRY profile validation: `visual_capture.validate_manifest` with the
  profile object read READ-ONLY from agent_slots.sqlite3;
  `visual_gate.verify` re-hashes camera JSON + video and binds
  capture_sha256. `visual_acceptance` stays false BY DESIGN — independent
  visual review remains mandatory.
- tick_interval: [0, 109] (the concatenated frozen replay timeline; per-row
  windows recorded in seconds).

## 8. Honest boundaries (inventoried before the build)

- The pinned M06 law refuses a full combined ground+trunk co-instantiation at
  the seam (P0, A3 heritage). The seam crossing is therefore demonstrated as a
  declared phased composition (ballistic approach -> trunk phase), with each
  phase through the unmodified law and the handover tick declared. A static
  seam solve (one probe supported by the ground WHILE contacting the trunk)
  is NOT demonstrated and is recorded as an unresolved upstream component for
  the integrator — never claimed.
- SEAM_HIGH's trunk phase runs without the ground body instantiated; the
  post-arrest unsupported sink inside the frozen 3-tick tail is MEASURED and
  reported as a composition artifact, not hidden; it is excluded from the
  interpenetration bar by the declared instantiation scope and its measured
  value is published either way.
- CPU-only, stdlib + ffmpeg for encoding; no engine run, no native change, no
  GPU, no training, no runtime/playable-build acceptance; friction values are
  the merged cards' declared placeholders (G04 debt).
- Visual acceptance itself belongs to the independent visual reviewer; this
  build's capture machinery is structural (validator + hashes + committed
  stills), not acceptance.

## 9. Amendments (each committed separately BEFORE the implementation/build)

- A1 (this commit, before any implementation or build run): SEAM_HIGH's
  frozen window is extended 32 -> 40 ticks and the phase-A handover rule is
  made checkable (PRE-tick remaining face-to-cylinder distance <= one per-tick
  motion, 0.02 m). Reason: the pre-freeze scratch measurement (attempt
  workspace only) put the ballistic handover at tick 32 with the face 0.006 m
  from the cylinder, so a 32-tick window cannot contain the trunk contact plus
  the frozen 3-tick tail. No bar is loosened: impact/pre-overlap, seam-band,
  penetration and ledger bars are unchanged; the extension only makes room for
  the contact the profile requires. Scratch also recorded the first trunk
  contact altitudes 0.0735-0.0935 m (inside the declared seam band [0, 0.15])
  and the phase-B composition sink (about 6.6e-3 m over the tail), which the
  build must publish as disclosed in section 8.
- A2 (this commit, before any implementation or build run): FB2's frozen
  wording ("a vertex already inside the analytic cylinder") is operationalized
  as the solver's own first-contact overlap: gap_m < 0 at the first detection
  with penetration_m = -gap_m > PEN_BAR_M (the same frozen 1e-4 bar). Reason:
  at edge/face feature contacts the overlap lives in the solver gap, not in a
  per-vertex predicate, and at the frozen speed the per-tick motion
  (0.02 m) is smaller than the trunk diameter (0.074 m), so a full pass-through
  is geometrically impossible; late detection after overlap IS the tunnelling
  signature M06's X4 declared for its no-CCD controls ("detect late (after
  overlap) with a spurious bias velocity kick"). No bar is loosened; FB1's
  ground control still exhibits the full pass-through (0.03 m/tick vs the
  0.004 m ground contact band) and keeps its original form.
- A3 (this commit, before any implementation or build run): FB6's perturbation
  target is made outcome-independent: the +1 cm raise is applied to ALL THREE
  vertices of the ground triangle the marker's classify ray hits first (the
  single-vertex form measured a 2-of-3 chance of remaining VISIBLE_EXACT at
  the flat spawn site, where the hit point sits near the edge opposite the
  raised corner and the height error cancels to first order). Raising the
  whole hit triangle moves the rendered surface +1 cm everywhere the ray can
  land, so the classify MUST read the height error against the untouched
  query oracle. No bar is loosened; the 1e-9 height bar and the
  VISIBLE_BUT_MISMATCH refusal are unchanged.
