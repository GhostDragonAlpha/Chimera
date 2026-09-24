# U02 Discovery Note — existing camera/viewer machinery, routes, capture path

Author: M-U02 (follow camera). Date: 2026-09-24. Checkout:
`E:/ChimeraWork/monkey-play-20260924`, branch `monkey-play-20260924`, HEAD `8c60bea3`
(base = game lineage master `32105f18`). Read-only discovery plus this dir; no
existing file modified. All paths relative to the checkout root unless absolute.

## 1. The two established camera surfaces (what exists today)

**The HTTP viewer** (`tools/product_viewer/server.py`, the product-http-viewer
lineage) is the only existing Python camera machinery over the engine:

- `EngineClient` (server.py:85-131): stdlib `urllib` GET/POST-json/POST-raw client;
  `up()` probes `GET /state`.
- `CameraPanel` (server.py:298-429): named presets. Contract nuance recorded there
  and re-verified below: `POST /camera` is radius/theta/phi ONLY; camera STATE reads
  go through `POST /project`'s `cam:[8]` echo (server.py:375-379) and bookmarks
  through `GET/POST /cameras`.
- `derive_fit` (server.py:311-372): the viewer's Python fit law — rig swept-envelope
  radius from `GET /joints` (+ `GET /scene` body row `r=` mesh extent), radius =
  `(R_rig + r_body)/tan(22.5°) × 1.05`, bookmark `v[8] = [radius, theta, phi,
  target_xyz, pan_xy]`, applied by `save`+`recall` bookmarks. **This save+recall
  pattern is the only existing full-camera (incl. target) write path — the follow
  camera reuses it.**
- Browser-side drag/keyboard orbit (server.py:587-639): throttled ~60 ms deltas off
  the cached cam echo — the operator's manual camera, not a controller.
- Capture: `CaptureThread` (server.py:208-287) pulls `GET /frame` at 10 Hz into a
  byte-exact `RingBuffer` ("the observer must not starve the observed": each tick
  yields `max(period, tick/4)`), `/frame` passthrough with NO re-encode
  (`_png_passthrough`, server.py:711-717), movies via `cpp_bridge.encode_movie`
  (server.py:479-489), window mirror via `window_capture` (server.py:29-74).

**The existing demos** fix the camera once and never move it:
`tools/product_features_walk/product_features_walk.py:247-257` — "the fixed camera
(one set, never touched — prereg)": `POST /camera {cam_radius: 3.4×mesh_extent,
cam_theta: 0.5, cam_phi: 0.35}`; the same constant in
`product_features_walk_realism.py:56`. Camera fixity is then a measured gate
(G6/G7): the SAME world point (knee_R pivot from the hinge facts) posted to
`/project` must project to constant pixels (product_features_walk.py:259-265,
383-391). `tools/membrane_demo_client.py:225-243` likewise sets a fixed demo camera
and records it as a sidecar fact. **So the follow camera is NEW behavior: nothing
existing follows the animal.**

## 2. The engine camera contract (verified in engine source; no C++ read-modified)

All from `ChimeraEngine/engine/` (READ ONLY — the frozen-service law):

| Fact | Citation |
|---|---|
| `POST /camera` accepts ONLY `cam_radius`, `cam_theta`, `cam_phi` (defaults 12/0/0.3); sets `camera_only=true`; waits ≤3 s for render-thread apply | main.cpp:2593-2610 |
| `POST /cameras` ops: `save` (live or exact `v:[8]`), `recall` (applies all 8), `fit`, `delete`; recall/fit go through the same membrane-request render-thread discipline | main.cpp:3400-3470 |
| `GET /cameras` lists bookmarks `{name, v:[8]}` | main.cpp:3380-3399 |
| Camera state vector `v[8] = [radius, theta, phi, target_x, target_y, target_z, pan_x, pan_y]`; `set_camera_full` clamps radius to `radius_floor()` | engine.cpp:3268-3274 |
| `radius_floor() = max(1.0, 1.02×mesh_sphere)` | engine.cpp:55 |
| Eye law: `eye = target + radius·[cosφ·sinθ, sinφ, −cosφ·cosθ] + pan`; up = `∂eye/∂φ = [−sinφ·sinθ, cosφ, sinφ·cosθ]`; standard right-handed look_at | engine.cpp:6670-6683 (`update_camera_matrices`) |
| Vertical FOV 45° (`tan_half = 0.41421356`), perspective near 0.1, far 1000 | engine.cpp:6672, 3244 |
| The engine's own fit law (bounding/per-axis, `×1.05` margin, floor extends to y=0) | engine.cpp:3186-3266 (`camera_fit`) |
| `POST /project {x,y,z}` → `{ok, sx, sy, cam:[8]}`: world→screen through the stashed VP + live cam echo | main.cpp:2106-2124 |
| `GET /joints` → `{loaded, t, current, n_joints, joints:[{name, ext, flex, theta(deg), J:[3], axis:[3]}], parents:[...]}` — J are REST centers; posed world positions are NOT exposed | engine.cpp:5538-5580 (`joints_editor_json`) |
| `GET /scene` → `{rows:[{id,label,detail,state,toggleable}]}`; body row detail carries `r=<mesh extent>` | main.cpp:3244-3297 |
| `GET /frame`: STRICTLY FRESH two-phase capture — the answer's capture is armed AT OR AFTER the request and collected before answering ("bytes POSTDATE the request"); `/frame?async=1` serves prior-frame bytes | main.cpp:2611-2668 (G8 contract) |
| F2 fast-path law: preview-quality `/frame` served in ≤ 200 ms | main.cpp:452-455 |

**Camera routes cannot move the body (the invariant's engine-side receipt):** both
camera write paths land in the membrane-request application block where
`cam_full_set → set_camera_full(...)` and `camera_only → set_camera(...)` — the
body-loading call `load_membrane(...)` is in the `else` branch those flags never
take, and nothing else in the block touches physics or pose
(main.cpp:4112-4135; flag semantics main.cpp:55-57). The animal is moved only by
separate routes this module never issues: `/hinge_bin`, `/gait*`, `/stride*`,
`/pose_apply`, `/joints_bin`, `/mesh_bin`, `/membrane` (body part).

## 3. The animal / scene the existing demos drive

- Rig: `Saved/meshes/monkey_joints.bin` via `POST /joints_bin`
  (product_features_walk.py:242-245); body mesh via `/mesh_bin` (ibid:240).
  The playable lineage pin is P02P03's task (parallel, read-only + bindings.json —
  no collision with U02; its brief verified). U02 tests against the contract, not
  that pin.
- Animal state reachable today: the rig doc (`GET /joints`) — per-joint rest
  centers J + parents, live `theta` per joint, and the show clock `t`. The anchor
  for a follow camera is therefore the rig's own geometry (envelope center /
  J-centroid); there is NO root-translation route in the current lineage — the
  current demos stride IN PLACE (that is exactly why camera fixity G6/G7 could be
  a gate). The follow camera takes the anchor from an injected provider so the
  future root-motion source slots in without rewriting it (declared in prereg).
- Scene: `GET /scene` rows only (labels + mesh extent). **The engine exposes NO
  obstacle geometry over HTTP** — no route returns the trunk/obstacle meshes.
  Honest consequence (frozen in prereg): obstruction avoidance runs against a
  DECLARED obstacle model injected into the module (vertical cylinders); tests use
  mocked cylinders whose constants cite F01's frozen bounds. Feeding it the real
  clearing declaration (F01's `tools/monkey_campaign/data/monkey_clearing/` — only
  `clearing_recipe.py` exists at discovery time; the compiled declaration is not
  yet written) is a recorded follow-up need.

## 4. Timing facts that constrain the latency design (C12/C23)

- The existing command seam is 20 Hz (C12 row; W08 "existing 20 Hz speed/heading
  seam is retained"; U01 "20 Hz boundary"). C12's own warning: "20 Hz implies a
  50 ms command interval, not an end-to-end latency guarantee." So the controller
  tick interval is REPORTED separately from measured latency, never conflated.
- `/frame` freshness is contractual (bytes postdate the request, §2 above) — this
  is what makes a headless presentation-latency PROTOCOL definable: t_state →
  command ack → first `/frame` whose capture armed after the ack.
- The engine's own documented frame budget is ≤ 200 ms (F2 fast path, §2). P06
  explicitly supplies NO product-wide latency limits yet ("do not fabricate them",
  map row P06 + map line 25). Therefore U02's 200 ms is a TEST-LEVEL budget sourced
  from the engine's own documented number, not a product limit; the product limit
  belongs to P06/U07 (declared follow-up).
- Engine HTTP is a single serialized worker; heavy routes are in an explicit
  competing set (`/hinge_bin /joints_bin /joints /joint /stride_bin /stride
  /gait_bin /gait /volp_bin /volp /matter /skin_bin /pose_apply /tick_rig
  /tick_flex /tick_joints /tick_classify /tick_vertbind /water_vis`, main.cpp:732)
  — camera routes are NOT in it, but the viewer's starvation law (§1) still binds:
  the follow camera must deadband its writes so idle ticks send nothing.

## 5. Declared paths for this task (all NEW; nothing existing modified)

- `tools/monkey_campaign/product/follow_camera.py` — the module (stdlib-only,
  importable as `tools.monkey_campaign.product.follow_camera` from the repo root;
  namespace packages, no `__init__` needed — `tools/` has no `__init__.py`, Python
  3.14 on this host; F01 declared the same convention).
- `tools/monkey_campaign/product/follow_camera_tests.py` — the headless test
  module (house style: sibling `*_tests.py`, cf. `tools/parser_tests.py`,
  `tools/port_tests.py`; `tools/monkey_campaign/test_campaign.py` co-locates the
  same way).
- `tools/monkey_campaign/agents/U02_camera/` — brief.md, discovery_note.md,
  PREREGISTRATION.md, receipts/, INTEGRATION_U07_W10.md.

## 6. REVISION 2 — re-verified after the mid-flight rebase (2026-09-24)

Coordinator correction: this branch was rebased from stale local master
`32105f18` onto the REAL game tip `33e7a444` (467 commits newer); campaign
commits (F01, P02P03) landed on top; my untracked files survived. All §1-§5
citations were RE-VERIFIED against the current tree (HEAD `8feea42a`,
base `33e7a444`). Discovery revision: BEFORE = base `32105f18` (HEAD `8c60bea3`),
AFTER = base `33e7a444` (HEAD `8feea42a`).

**Changed (module re-targeted accordingly):**

- `POST /camera` now carries the FULL camera state: optional `pan_x`, `pan_y`,
  `target_x`, `target_y`, `target_z` (all default 0), stored in `g_mem_req`
  (main.cpp:2655-2690) and applied by the `camera_only` branch through
  `set_camera(r, θ, φ, pan_x, pan_y, tx, ty, tz)` (main.cpp:4193-4196;
  engine.cpp:7312-7329 — the CAM-PAN/TARGET LAW, 2026-09-20 Defect C lane).
  ONE POST now moves the target: the §1 bookmark save/recall dance is no longer
  needed as the primary write path. New footgun, same shape as the old one:
  every omitted field DEFAULTS (radius→12, θ→0, φ→0.3, target→0), so a partial
  POST resets the rest — the module therefore always sends ALL 8 fields.
- Near-plane law (NEW): the projection near plane tracks the subject —
  `clearance = |eye−target| − g_mesh_sphere`; inside 0.1 it shrinks to
  `max(0.25×clearance, 2 mm)` (engine.cpp:6713-6725). Consequence for U02:
  pulling the eye INTO the subject's bounding sphere now degrades the depth
  precision as well as the framing — independent support for the frozen pull-in
  floor `R ≥ R_ground`.
- Walk machinery now IN-TREE: `ChimeraEngine/engine/gait_controller.hpp` (the
  qualified 14-coordinate walker, free-root solver, paw world positions),
  `tools/science_funnel/gait_scene.py` (the walker scene compiler), and the
  visible-walk rig-fit lineage (P02P03's pin: walker 10.038 kg Oku-2021 body, CT
  Macaca render). No HTTP route exposes walker root motion yet — the §3 anchor
  analysis stands; the gait scene bundle is the named future anchor source.

**Unchanged (re-verified, line numbers updated):** eye law
(engine.cpp:6730-6736), up = ∂eye/∂φ (6737-6739), `radius_floor`
(engine.cpp:56), FOV 45°/`tan_half = 0.41421356` (engine.cpp:3280, 6725, 6788),
G8 `/frame` STRICTLY FRESH contract (main.cpp:2685-2704), F2 ≤ 200 ms fast-path
law (main.cpp:458), serialized competing-route set WITHOUT camera routes
(main.cpp:794), `POST /project` echo `{ok, sx, sy, cam:[8]}` (main.cpp:2168-2186),
`GET /joints` editor doc with rest centers J + parents + live thetas
(engine.cpp:5574-5598), `GET /scene` rows (main.cpp:3318), `/cameras`
GET/POST unchanged (main.cpp:3454, 3474). The invariant receipt is intact at the
current lines: `camera_only` → `set_camera(...)` only; `load_membrane` sits in
the else-branch camera requests never take (main.cpp:4190-4204). The viewer
`tools/product_viewer/` is byte-identical to the old base (no diff).

**Addendum (final re-verification at HEAD `8550b634`, U01 integrated):** all
camera citations re-grepped and confirmed unchanged at the new HEAD
(`/camera` optional pan/target at main.cpp:2655-2690; eye law at
engine.cpp:6733; body-row `r=%.1f` format at engine.cpp:2678). U01's input
mapper landed on the `CommandRecord v1` seam in parallel; it issues body
commands at 20 Hz and is INDEPENDENT of this module (the invariant holds per
stream — U02's allowlist proof covers U02's own stream; U01's stream is U01's
to prove).

## 7. Follow-up needs recorded (not doable headless, per brief)

1. Engine-side frame cost and true presentation latency with the REAL renderer —
   needs a live engine (GPU, interactive session); U07 measures during actual play
   per its own row; W10 accepts walking with this camera in the real scene.
2. Feeding the real clearing/obstacle declaration (F01/F07 outputs) into the
   obstacle model instead of test mocks.
3. Human acceptance of the follow feel (C23's "human acceptance" field) — a human
   with the viewer; this task delivers the measurement hooks (INTEGRATION notes).
4. Re-deriving follow constants against P06's frozen latency/frame-time limits
   once P06 exists (the module exposes them as frozen constructor defaults).
