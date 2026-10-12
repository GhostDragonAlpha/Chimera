# B2 step 1 — two independent parts, gravity/support, on the shared resident runtime

GAME_PLAN_ACTION_RPG.md §13, B2 gate, first of three parts: *"Two independent
parts, gravity/support, loose contact and one finite-area connector on the
first shared resident runtime state."* This commit lands **the two parts +
gravity/support + loose contact** (the connector is step 3). Design ownership
per B2_design_and_dof_ownership.md.

## What was built

- `ChimeraEngine/engine/b2_scene.hpp/.cpp` — `B2Scene`: exactly two rigid
  parts, each owning its full 6-DOF state (c, v, R, ω) on the single resident
  `MembraneTick g_tick`. Gravity + support through the coupon's **one-sided
  ground rung** (ported from `native_coupon.cpp`: `g = P·ŷ`,
  `fn = −(k·g + c·ġ)`, active only when `g < 0 && fn > 0`), integrated by the
  coupon's semi-implicit rigid step (world inertia `R·I_local·Rᵀ`, Euler term
  `−ω×(Iw·ω)`, rotation by `exp(h·[ω]×)`), fixed substep `h = 1/4000 s`,
  frame dt clamped 0.05 s (the engine's own clamp). Strict
  `chimera.b2_scene.v1` JSON admission: unknown fields, non-finite numbers,
  asymmetric inertia, triangle-inequality violations, bad quaternion norms,
  duplicate ids, out-of-range indices and malformed documents are **refused
  by name** and never touch the live scene. Energy bookkeeping
  (KE + gravitational + penalty) and a divergence latch (non-finite state →
  `diverged:true`, scene frozen) make numerical failure visible, not silent.
- Routes (main.cpp, dispatched via file-scope `route_b2` **after** the ladder
  — the ladder sits at MSVC's C1061 block-nesting limit):
  `POST /tick_b2_admit` (body IS the scene document), `POST /tick_b2_clear`,
  `GET /tick_b2_state` (telemetry), `GET /tick_b2_parts` (admitted data
  round-trip). Refusal text is JSON-escaped in the route.
- Driving: `MembraneTick::b2_step(dt)` is called from the render loop
  **independent of the membrane body** (B2 is body-independent; `step()` only
  runs with verts loaded). Lock discipline: `b2_mtx_` alone everywhere —
  the scene never nests under `seal_mtx_` and never touches `verts9`; the
  single-body FALL rung and the creature surface are untouched. Default OFF:
  nothing exists until `/tick_b2_admit`; a mesh swap clears the scene.
- `tools/construction_packet/b2_scene_gen.py` — builds the scene document
  from the **B1 packet templates** (same compiled masses, COMs, inertias,
  vertices, boundary triangles as `test_construction_packet.py` verifies):
  granite wedge A at origin, steel wedge B at x = 0.6 m (loose: x-extents
  [0, 0.3] and [0.6, 0.82] never touch), pose `R_x(−90°)` so the authored
  bottom face z = 0 lands exactly on y = 0.

## Per-part rung derivation (why the ground moved into the part)

The resident FALL constants (k = 1.3562e7, c = 6.062e5, m = 13824.5 kg) are
that body's constants; reusing them verbatim on a ~10 kg part gives explicit
damping `h·c/m ≈ 15 ≫ 2` → divergence. Each part therefore carries its own
per-site `(k, c)`, derived from the same **law** the FALL uses — rest sink
`s* = 1 cm` and damping ratio `ζ = 0.7`:

    k_total = m·g/s*,  c_total = 2ζ√(k_total·m),  per site ÷ N_bottom

with `N_bottom = 3` (the wedge bottom face is a triangle; only its vertices
can penetrate y = 0). The stability ratios become mass-independent:
`h·c_site/m = 2ζh√(g/(s*·N)) ≈ 6.3e-3 ≪ 2` and `h·ω_site ≈ 4.5e-3 ≪ 1`.

## Measured envelope (live engine, Release, port 8792, 2.5 s settle)

| quantity | A (granite) | B (steel) | expectation |
|---|---|---|---|
| mass_kg | 9.72 | 26.4231 | B1 packet compile |
| weight_n | 95.3532 | 259.210611 | m·g |
| reaction_n | 95.3532 | 259.210611 | = weight at rest |
| contacts_active | 3 | 3 | bottom-face sites |
| pen_step_m | 0.010000 | 0.010000 | s* = 1 cm |
| pen_run_m | 0.010452 | 0.010452 | ζ=0.7 overshoot 4.6 % → 4.5 % measured |
| speed_m_s | 6.3e-15 | 6.3e-15 | at rest |
| k_n_per_m, c_n_s_per_m | 3178.44, 142.07 | 8640.35, 386.21 | derivation above |

Scene totals: `total_reaction_n = total_weight_n = 354.563811` (exact to
output precision); `energy_drift_j = −1.7728` — negative (the damping
dissipates) and bounded by the weight×sink work `m·g·s* ≈ 3.5 J`;
`steps = 10223` in 2.5 s at `dt_substep_s = 0.00025`; `diverged:false`;
`admission_reason` round-trips. COM heights at rest: A y = 0.05 = H/2 − s*,
B y = 0.035 = H/2 − s* — the sink is exactly the designed 1 cm.

## Test battery

`tools/construction_packet/test_b2_statics.py` (unittest, launches the
Release engine fresh on port 8791, no membrane body loaded — proving B2's
body-independence): **5/5 OK**.

1. `test_statics_reactions_and_loose_contact` — the table above as asserts
   (reaction = weight rel 1e-3, 3 sites, speed < 1e-3, pen_run ∈
   [9 mm, 12 mm], parts ≥ 0.4 m apart, drift < 0 and > −2·W·s*).
2. `test_steps_advance_while_resident` — the resident runtime is stepping.
3. `test_parts_roundtrip` — admitted mass/inertia/counts/quaternion
   (up to sign) return exactly what was sent.
4. `test_refusals_name_themselves` — 13 malformed documents (wrong schema,
   1 or 3 parts, negative mass, asymmetric inertia, triangle-inequality
   inertia, bad quaternion, unknown field, duplicate id, out-of-range index,
   missing ground, zero k, negative c) + a raw `NaN`; every refusal names
   itself and the live scene survives untouched.
5. `test_clear_disarms` — clear → inactive, steps reset, re-admit works.

Reproduce: `cmake --build .tmp/body-engine --config Release` then
`python tools/construction_packet/test_b2_statics.py`.

## Not in this commit (gate honesty)

Off-center load reactions/torque, slide/tip/separate and power-removal
controls, and the finite-area connector are the §13 B2 evidence items that
belong to steps 2–3 and are **not** claimed here.
