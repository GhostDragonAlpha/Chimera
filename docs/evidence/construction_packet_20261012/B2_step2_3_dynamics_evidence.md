# B2 steps 2–3 — off-center load, tip, loose contact, slide, power removal, finite-area connector

GAME_PLAN_ACTION_RPG.md §13, B2 gate, evidence column: *"Off-center load
gives correct reactions/torque; slide, tip, separate and power/support-removal
controls; numerical envelope measured."* Steps 2 (commit d364446a) and 3
(commit f4f337a5) close the whole column on the same shared resident runtime
as step 1 (`B2Scene` on `MembraneTick g_tick`, no membrane body loaded).
Design ownership per B2_design_and_dof_ownership.md.

## What was built

**Step 2 — controls + loose contact + friction** (`b2_scene.hpp/.cpp`,
routes in `main.cpp route_b2`, lock-wrapped in `membrane_tick.cpp`):

- `POST /tick_b2_load {part, force_n[3], point_world[3]}` — persistent
  force whose application point is captured in the part's **local axes** at
  set time, so the load rides the pose (a weight sitting on the part, not a
  thruster chasing it); zero vector removes it. `load_n` reported back.
- `POST /tick_b2_support {"on":bool}` / `POST /tick_b2_gravity {"on":bool}` —
  scene-wide switches: the ground rung and the gravity term (weight
  telemetry included) go truly to zero.
- Loose contact (`pp_pair_`): vertices of each part against boundary
  triangles of the other, the coupon's **one-sided penalty rung**
  (`g = signed distance`, `fn = −(k·g + c·ġ)`, active only when
  `g < 0 && fn > 0`), strict triangle containment plus a 5 cm contact
  radius, regularised Coulomb friction
  `f = −μ·fn·vt/max(|vt|, 1e-3)`; pair constants = mean of the two parts'
  rung constants and friction ratios. Exact Newton-3 pairs (equal, opposite,
  same line of action). Two-pass substep: all forces before any integration.

**Step 3 — finite-area connector** (the gate's "one finite-area connector"):

- Coupon `Weld { av, al, w, k }` (native_coupon.cpp :161) ported to two
  rigid parts: `POST /tick_b2_weld {a, b, k, c_damp?, anchors_world:[[ax,ay,az,bx,by,bz],…]}`
  — **≥ 3 anchor pairs** (a finite AREA, not a pin), each captured in local
  axes (the weld rides the parts), weights 1/N, central spring pair per
  anchor `f = w_j·k·(pb−pa)` applied +on a at pa and −on b at pb — exact
  Newton-3 in force AND torque. Optional along-line dashpot `c_damp` is the
  scene's own penalty-damper law (`c = 0` is the coupon port exactly).
  `POST /tick_b2_weld_remove {a, b}` breaks it; a re-set replaces the weld
  on the same pair. Telemetry: scene-level `welds[]` with `n_anchors`,
  `k_n_per_m`, `c_n_s_per_m`, `force_n`; weld elastic energy joins the
  energy ledger.

## Measured (live engine, Release, port 8792, 2.5 s settle)

Off-center load — 50 N down at (0.20, ·, −0.05) on A (sites s0=(0,0,0)
s1=(0.3,0,0) s2=(0,0,−0.2), W_A = 95.3532 N):

| quantity | measured | expectation |
|---|---|---|
| total reaction_n | 144.884 | W_A + 50 = 145.353 (0.32 %) |
| site reactions [f0,f1,f2] | [33.963, 66.003, 44.918] | exact statics on the **measured pose** [34.132, 66.146, 45.075] → rel ≤ 0.5 % |
| same vs nominal lever rule | — | [35.935, 65.118, 44.300] → rel ≤ 5.5 % (penalty pose shifts ~cm under load) |
| top-vertex reactions | [0, 0, 0] | one-sided: tops carry nothing |

Tip — 200 N at (−0.1, ·, −0.1), outside triangle s0s1s2 (lever rule gives
f1 = −34.88 N, which a one-sided rung cannot deliver): within 37 ms a site
deactivates (`min_contacts = 2`) and the attitude moves (`min |q·q0| =
0.9941`); load off → rest again, no divergence.

Loose contact — B yawed `q=(0.5,−0.5,−0.5,−0.5)` facing A's back plane with
a 0.5 mm gap, 1 N push applied exactly at the contact corner (0.0867, 0.09):

| quantity | measured | expectation |
|---|---|---|
| Newton-3 worst rel over 10 active samples | 0.0 | equal & opposite, same active count |
| peak pair force | 4.18 N | rings around the 1 N it carries (soft penalty) |
| A drift_z | −0.28 mm | friction (μ=0.8, capacity 76 N) holds A |
| pen_pp_run_m | 0.0300 | finite, bounded by the 5 cm contact radius |
| after load zero | separated, fn = 0 | one-sided sites release |

The flush-on-shared-ground press is dynamically fragile (a soft penalty pair
under a follower corner load rings and can pitch through ground coupling),
so the gate evidence is the **interaction law + separation + measured
envelope**, not a static flush hold — per the design note.

Slide — μ=0.6 on A (μ·N = 57.2 N): 20 N hold → speed 1.6e-3 m/s, drift
3.5 mm (regularised sticking creep, orders below the slide case); 120 N >
μ·N → speed 1.40 m/s; load removed → stopped in 0.41 s, total travel 0.31 m.

Support / gravity switches — support off: `total_reaction_n = 0`, parts
fall (1.43 m/s in 0.15 s); restore → 354.564 N = weight. Gravity off:
`total_weight_n = 0`, reactions → 0; restore → 354.564 N, `energy_drift_j
= −1.773` (damping dissipates, bounded by W·s* ≈ 3.5 J).

Finite-area connector — B yawed flush (0.5 mm gap), weld k = 50 000 N/m,
c_damp = 2000 N·s/m, 3 anchor pairs on a sub-area of A's back rectangle:

| quantity | measured | expectation |
|---|---|---|
| preload settle | B flush, weld force 0 | 0.5 mm preload pulls B to the plane |
| 40 N normal pull | weld force 38.6 N, **contacts_pp_active = 0, contact force 0** | one-sided sites OPEN; the connector ALONE carries |
| B level | \|q·q0\| = 1.0 | finite anchor pattern resists the pull's yaw couple |
| A creep under weld pull | 1.7 mm | under the 76 N friction capacity |
| weld removal | `welds = []`, B accelerates to 0.63 m/s under the continued pull | connector removal → free motion |

Numerical envelope — `dt_substep_s = 0.00025` (h = 1/4000 s), ~10 000 steps
per 2.5 s, ground `pen_run = 0.010452` m (the designed 1 cm sink + ζ=0.7
overshoot), energy drift negative and bounded, `diverged:false` throughout;
the divergence latch freezes the scene on any non-finite state.

## Bugs the battery caught (engine fixes, in f4f337a5 / d364446a)

1. **Dashpot sign inverted** in the first weld cut: `f = k·d − c·vn·n` is
   negative damping (power +c·vn² > 0) — the scene exploded 18 ms after
   `set_weld`. Corrected to `f = k·d + c·vn·n` (power −c·vn² ≤ 0).
2. **UB pointer walk** in the part-part containment test (`w0 + 3*e` off a
   3-element stack array) → `const double *wv[3]`.
3. **Boundary-counted-as-inside** containment let coplanar knife-edge
   projections fire spurious contacts → strict `<= 0` edge rejection plus
   the 5 cm contact radius.

## Test battery

`tools/construction_packet/test_b2_dynamics.py` (unittest, launches the
Release engine fresh on port 8792, no membrane body loaded): **8/8 OK** —
off-center lever rule, tip, loose contact + separation, slide, support/
gravity switches, control refusals (no-scene, unknown part, wrong array
length, missing field, bad switch bodies, weld refusals: < 3 anchors,
self-weld, unknown part, k ≤ 0, c_damp < 0, removing an absent weld),
weld finite-area connector, envelope reported. Statics battery
`test_b2_statics.py` re-run green (5/5) after every engine change.

Reproduce: `cmake --build .tmp/body-engine --config Release` then
`python tools/construction_packet/test_b2_statics.py && python
tools/construction_packet/test_b2_dynamics.py`.

## Gate honesty

The §13 B2 row is closed by steps 1–3 together: two independent parts +
gravity/support (step 1), loose contact + off-center load + slide/tip/
separate + power/support removal (step 2), one finite-area connector with
separate control (step 3), numerical envelope measured (all steps). What is
**not** claimed: material failure of the weld (breakable by removal, not by
stress), friction pair μ from a material table (the scene owns one ratio per
part), and continuous collision (the discrete rung with contact radius is
the accepted coupon law).
