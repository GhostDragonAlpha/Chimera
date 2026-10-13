# B3 — three dissimilar layers, loose and bonded, on the resident runtime

GAME_PLAN_ACTION_RPG.md §13, B3 gate row: *"Three dissimilar layers in
loose and bonded variants, same initial visible shape, inspection by stable
IDs"* — evidence column: *"Distinct shear/slip behavior; no double mass;
render/pick/contact agree; delamination exposes the intended material."*
All four claims are measured below on the live Release engine (port 8793,
`--hidden 1600 900 --no-restore`), same resident runtime as B2
(`B2Scene` on `MembraneTick g_tick`, no membrane body loaded).

## What was built

**Scene generator** (`tools/construction_packet/b2_scene_gen.py`,
`make_stack(bonded=False|True)`): three rectangular layers of different
material, density, size and thickness — granite base
(0.30×0.12×0.30 m, ρ 2700, μ 0.5), steel middle (0.24×0.10×0.12 m,
ρ 7850, μ 0.4), timber top (0.18×0.08×0.06 m, ρ 600, μ 0.3) — stacked
face-on-face so every upper layer's bottom vertices project strictly
inside the layer below. Rest poses are derived from the scene's own
penalty law (each interface pre-sunk by its static sink), so the admitted
scene starts at equilibrium. Masses: 29.160 kg / 22.608 kg / 0.5184 kg.
Both variants admit the **identical** part records; the bonded variant
additionally gets the finite-area weld across the steel/timber interface
(`stack_weld_document()`, 3 coincident anchor pairs — zero preload —
k 50 kN/m, c_damp 300) through the live control.

**Engine** (`b2_scene.hpp/.cpp`, routes in `main.cpp route_b2`,
lock-wrapped in `membrane_tick.cpp`):

- Admission now accepts **2–3 parts** (was exactly 2); refusals name
  themselves.
- `POST /tick_b2_inspect {"id":"..."}` — stable-ID inspection: the full
  record for that part (mass, μ, COM, inertia, ground rung constants,
  vertex/triangle counts, current pose, telemetry). Unknown id and
  non-string id are refusals.
- `render_mesh()` / `pick()` — the render/pick lane: the scene's world
  meshes as a 9-float render stream (pos, normal, rgb; fixed palette by
  admission order: base red, middle green, top blue) and a Møller-Trumbore
  ray pick **against the same vertex/triangle arrays the contact solver
  walks**. Route `POST /tick_b2_pick {"px","py"}` casts the engine
  camera's ray (shared `Engine::camera_ray` law with `Engine::pick`) and
  answers `{"ok":true,"id":...,"hit":[x,y,z]}`.
- Render loop: while a B2/B3 scene is live its world meshes upload to the
  renderer's overlay slot every frame; `Engine::frame()` and the
  triangle-pass branch now open for the overlay alone (previously a
  creature mesh was required for anything to draw).

## The contact-law fix this gate forced

The first stacked scenes exploded: at rest the timber/steel interface
carried **686 N** where the timber weighs 5.09 N. Root cause: a convex
surface is the intersection of its face half-spaces, so a vertex that
entered the volume through the top face is also *behind* every side-face
plane it lies inside of — the old loop fired a penalty rung on **all** of
them, and the side faces' 30 mm "penetrations" (~85 N each, lateral)
ejected the upper part. The fix (`pp_pair_`): a vertex contacts the face
it entered through — the **shallowest (max g) candidate face** — one face
per vertex per substep. Measured after: timber/steel 5.086 N = the
timber's own weight 5.0855 N; steel/base 226.87 N = steel + timber;
ground reaction 512.93 N = the whole stack, matching
`total_weight_n` 512.929584 exactly (no double mass: the sum of the three
layer weights is the scene weight to 1e-6 relative). The B2 battery
(8/8 dynamics, 5/5 statics) re-verifies the two-part scenarios on the
fixed law.

## Measured (live engine, Release, port 8793, 2.5 s settle)

**No double mass.** `total_weight_n` 512.929584 = Σ m·g; per-part
`weight_n` match m·g to 1e-6 relative; at rest the whole stack is static
(speed < 5e-3) and `total_reaction_n` equals the total weight.

**Stable-ID inspection.** All three ids return full records matching the
admitted document to 9 decimal places (mass, μ, COM, 9 inertia entries,
8 verts / 12 tris each); `layer_nonexistent` → `no part with id` refusal;
non-string id refused; inspect before admit refused.

**Same initial visible shape.** `make_stack(bonded=True/False)` part
records compare equal field-for-field; after settle the two variants'
rest poses agree to 1e-3 m (the weld anchors are coincident at rest —
zero preload — so bonded dynamics equal loose dynamics until a load asks
the connector to carry).

**Distinct shear/slip.** A 3 N horizontal pulse (0.08 s) on the timber
top, through the timber COM:

| variant | timber↔steel slip | steel↔base slip |
|---|---|---|
| loose | **12.6 mm** | 0.054 mm |
| bonded | **0.225 mm** | 0.138 mm |

Loose slips 56× more at the loaded interface; the unloaded interfaces
stay closed in both variants (thresholds: μ_pair·W_top = 0.35·5.09 =
1.78 N < 3 N at the timber interface; 0.45·(W_mid+W_top) = 102 N ≫ the
shear it feels at the steel interface). During the bonded pulse the weld
telemetry reports **2.94 N** — the connector carries the shear the loose
interface could not hold.

**Delamination exposes the intended material.** A 7 N vertical pull
(> W_top = 5.09 N) on the timber opens the one-sided interface: the top
rises 23.5 mm with `contacts_pp_active` 0, while the steel still sits on
the granite base (4 sites, 220.7 N ≈ the steel's own weight). Inspecting
the exposed layer by its stable ID returns the steel's own μ (0.4) and
mass — the material the player would now act on. Release drops the top
back; the scene stays finite (`diverged` false).

**Render/pick/contact agree.** With the camera aimed at the stack
(`/cameras` bookmark, all 8 floats), for each layer the engine's own
projection (`/project`) of a point on that layer's exposed top face
lands on a pixel that (a) `/tick_b2_pick` answers with **that layer's
stable ID**, the hit point on the projected plane to <1 mm, and (b) the
`/frame` capture renders in **that layer's palette hue** (frame census:
red 5180 / green 2553 / blue 1734 samples — three distinct regions in
the correct stacking order). The agreement tracks the contact state: a
point just inside the timber's trailing edge picks and renders timber
before the shear; after the timber slides 12.6 mm off it, the same pixel
refuses the pick and no longer renders timber, while the timber's NEW
center still picks `layer_top_timber` by its stable ID.

## Bugs the battery caught (engine fixes, this commit)

- **Side-face ejection** (above): the shallowest-face rule replaced
  fire-on-every-behind-face; caught as a 686 N rest force at a 5 N
  interface.
- **Overlay index count**: the render feed passed the triangle count
  where `load_overlay` wants the index count — only the base box drew.
- **`Engine::frame()` idle short-circuit**: with no creature mesh the
  3D pass never ran, so the overlay could not appear; the idle condition
  now includes the overlay slot.
- **Weld-test instrument** (`test_b2_dynamics.py`): the pull point moved
  to B's COM height (the yaw couple the finite-area check needs stays;
  the incidental pitch moment that dipped a face corner into A's plane
  is gone), and the contact-site assert now measures the force the sites
  carry (< 5% of the pull) instead of an instantaneous zero — the
  regularized ground friction under A puts the assembly in a small
  documented stick-slip during which a corner can graze the plane for
  < 2 N. The weld-force assert (within 5% of 40 N) remains the load
  statement.

## Test battery

`tools/construction_packet/test_b3_layers.py` — 6/6:
`test_three_layers_no_double_mass`, `test_stable_id_inspection`,
`test_variants_share_visible_shape`, `test_shear_slip_distinct`,
`test_delamination_exposes_material`, `test_render_pick_contact_agree`.
Regressions on the same engine: `test_b2_statics.py` 5/5,
`test_b2_dynamics.py` 8/8 (weld test 5/5 consecutive runs after the
instrument fix), `test_construction_packet.py` 23/23.

## Gate honesty

- The render lane draws through the overlay slot with the creature
  pipeline's Lambert shading; palette hues are asserted by dominant
  channel, not exact RGB (lighting modulates brightness).
- The pick and the render share `Engine::camera_ray` and the scene's own
  world meshes, so render/pick/contact agreement is structural; the test
  proves it end-to-end through HTTP (projection → pick → frame pixel →
  post-shear re-check).
- Per-frame `load_overlay` waits the device (its own discipline); the
  scene is a measurement rig, not a shipped view — the cost gate is B7.
- Slip numbers are single-run measurements with the scene's own settle
  discipline; the battery asserts margins (loose > 8 mm, bonded < 2 mm,
  ratio > 4×) far from the measured 12.6 mm / 0.225 mm / 56×.
