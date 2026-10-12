# B2 design and DOF ownership — two parts on the first shared resident runtime

Gate wording (GAME_PLAN_ACTION_RPG.md §13, verbatim):
"Two independent parts, gravity/support, loose contact and one finite-area
connector on the first shared resident runtime state | Off-center load gives
correct reactions/torque; slide, tip, separate and power/support-removal
controls; numerical envelope measured"

This is the pre-coding ownership note required by the §13 discipline:
explicit material/DOF ownership and source identities before any native edit.
No engine file is modified by this document.

## 1. Source identities (pinned at this design)

| File | SHA-256 |
|---|---|
| `ChimeraEngine/engine/membrane_tick.hpp` | `a79f7c37d01f4fdc8a390c412aaf8239ceea42961120069e1c93d4ca9516a3fc` |
| `ChimeraEngine/engine/membrane_tick.cpp` | `0a0624fbbd10b8e8788eff8c00d3dcfd3b24866b478fc359ca01f31099ea95e3` |
| `ChimeraEngine/engine/main.cpp` | `56c554b0727b15f0b3958c6be48a7ffea221df77fa10c66b4934d4bd9458028f` |
| `tools/finite_area_attachment/native/native_coupon.cpp` | `fe580fbae21a754559af69ed56d5d18d56a446d96a0317e25d21feedfca8f3e6` |

Baseline commit: `f5fb52c5` (B1 construction packet, branch
`WK-ENGINE-PATHS-20260929-PR`, published to
`origin/WK-ENGINE-PATHS-20260929-PR-GAME`). The three engine files are clean
against HEAD in the shared checkout (verified `git status --porcelain` —
other agents' dirty files do not intersect the change surface in §5).

Geometry and mass properties come from the B1 packet compiled by
`tools/material_volume.py` (sha256 `a4eb96e6d59c51d9c673ad6df8675639cd0b25a1652b0f6f5203de737a4327ec`,
byte-identical to the frozen reference family): part masses, COMs and inertia
tensors are the compiler's closed-form outputs, already verified to 1e-12
against analytic references (`B1_construction_packet_compile.md`).

## 2. What the resident runtime is today (verified citations)

- One resident body per process: `static MembraneTick g_tick`
  (`main.cpp:95`); the tick runs inside the render frame
  (`main.cpp:4522-4534`), dt wall-clock clamped to 0.1 s.
- Geometry admission: `/mesh_bin` (`main.cpp:1044-1089`), exact-size header
  check (:1061-1063); the only physics path is slot 0 →
  `g_tick.init(...)` (`main.cpp:4255-4258`). While the body is active,
  competing POST routes are refused with `shared_body_owns_surface`
  (`main.cpp:741-748`) — one pose owner owns the surface.
- Gravity + support today is THE FALL: scalar one-DOF Y rung
  (`membrane_tick.cpp:880-903`), `G_EARTH = 9.81f` (:71),
  `mass_kg_ = 13824.5f`, `k_ground_ = 1.3562e7f`, `c_ground_ = 6.062e5f`
  (`membrane_tick.hpp:533-537`), one-sided spring+damper on the lowest
  vertex, force cap `50·m·g`, reaction telemetry `g_contact_n`
  (`membrane_tick.cpp:5052`), evaluation counter `ground_evals_`
  (`membrane_tick.hpp:545`). No friction, no per-site contact, no body-body
  contact, no inter-body connector in the resident runtime.
- The accepted formulations B2 must reuse already exist natively in the
  gated coupon `tools/finite_area_attachment/native/native_coupon.cpp`:
  - rigid body state `BodySpec/BodyState` with mass `M`, diagonal inertia
    `J`, pose `(c, R)`, spatial velocity `(v, ω)` (:162-182), integrated
    with world inertia `R·diag(J)·Rᵀ` plus Euler term (:854-862);
  - per-site one-sided ground rung `contact_forces()` (:754-771):
    `g = (P−plane_p)·n`, `fn = −(k·g + c·ġ)`, active only when `g<0` and
    `fn>0` — the same law as THE FALL, vector-valued and per-site;
  - finite-area weld `Weld { av, al, w, k }` (:161) with exact Newton-3
    force pair and torque in `total_forces()` (:798-806), weights summing
    to 1 (parsed :297-308);
  - gravity on both representations (:812-815), energy/momentum bookkeeping
    including contact dissipation (:872-894).
  The coupon is gated by `test_finite_area_attachment.py`,
  `test_membrane_coupon.py`, `test_dynamics_and_corrections.py` and
  `DERIVATION.md` — B2 ports these formulations into the resident tick
  rather than writing a new physics system (plan mandate: "reuse existing
  body force/support formulations, no separate game physics system").

## 3. Scene (same accepted geometry drives loads, drawing, selection)

Two B1 packet templates admitted as ONE slot-0 `/mesh_bin` upload whose
vertices carry a part tag (no new admission path, no change to the
single-owner guard):

- **Part A — wedge A** (`WEDGE_A`, asymmetric right triangular prism):
  rests on the ground plane y = 0. Its rigid DOF set carries mass, COM and
  inertia exactly as compiled by `material_volume` for `part_wedge_a`.
- **Part B — wedge B** (`WEDGE_B`, the asymmetric counterpart): rests on
  wedge A's hypotenuse face — LOOSE contact (one-sided penalty, may
  separate, no bonding across the whole face).
- **One finite-area connector**: a `Weld` over the B1 interface discipline
  — a strict sub-area of the A–B contact patch (finite area, N weighted
  anchors, weights = anchor areas / total, summing to 1), distinct from the
  loose-contact sites. Interface identity uses B1's stable `face_key`s so
  the connector, the drawing and selection all reference the same interface.

Part membership is a partition: every vertex belongs to exactly one part,
enforced at admission (a vertex tagged twice is refused with
`overlapping_ownership`, mirroring the compiler's `duplicate_mass_owner_id`
discipline). Material/DOF ownership table:

| Owner | Owns | Source of truth |
|---|---|---|
| part A rigid DOF | pose/velocity of V_A, mass/COM/inertia_A | material_volume compile of `part_wedge_a` |
| part B rigid DOF | pose/velocity of V_B, mass/COM/inertia_B | material_volume compile of `part_wedge_b` |
| ground rung | per-site normal force on A (plane y=0) | `k_ground_`, `c_ground_` (existing constants) |
| loose contact A↔B | per-site one-sided compression pair | same rung law, coupon `contact_forces()` form |
| connector weld | finite-area anchor pair + torque | coupon `Weld` form; anchors from B1 interface faces |
| membrane tick (unchanged) | everything else: seal, gait, drives | untouched |

## 4. Acceptance measurements (gate right-hand column, mapped)

| Gate requirement | Measurement | Reference |
|---|---|---|
| off-center load gives correct reactions/torque | static hang with part B placed at offset d along A's top; sum of ground-rung site forces = (m_A+m_B)·g within envelope; moment balance about the support edge = analytic statics of two rigid bodies | closed-form statics from B1 mass properties |
| slide control | tangential load ramp on B: static below μ·N, slides above; friction ratio measured | Coulomb threshold from authored μ |
| tip control | load/moment ramp on A until restoring moment about the support edge is exceeded; tipping condition vs analytic edge-moment criterion | analytic tip criterion from support polygon |
| separate control | normal pull on B: loose-contact sites deactivate (one-sided), connector alone carries; then connector removal → free fall of B | one-sidedness of the rung |
| power/support-removal control | `/tick_gravity` off and ground-rung removal routes: reactions → 0, bodies follow free-fall law | existing `/tick_gravity` route (`main.cpp:1595-1604`) |
| numerical envelope measured | max penetration depth, contact-force oscillation, energy drift vs dt across the run; recorded in evidence | coupon's energy/momentum bookkeeping as pattern |

## 5. Change surface (smallest honest surface, from full-source exploration)

1. `membrane_tick.hpp/cpp`: per-part rigid DOF state (pose, velocity, mass,
   inertia) for parts A/B; part-tag partition at `init`; per-part ground
   rung and A↔B loose-contact rung (coupon formulation, existing k/c
   constants); one `Weld` port (coupon struct verbatim in spirit); telemetry
   fields beside `g_contact_n` (per-part reactions, contact site counts,
   weld force, envelope counters).
2. `main.cpp`: control routes (load offset, tangential ramp, normal pull,
   connector removal, support removal) beside existing `/tick_*` routes;
   `/tick_state` gains the new fields. No new mesh admission path; the
   single-owner guard stays.
3. NOT doing: a second `MembraneTick` global or new mesh slot — that forks
   the tick loop (`main.cpp:4522-4534`), route guard (:741-748), handoff
   (:4243-4260) and every telemetry route for no formulation gain.

Default-OFF gating convention of the repo applies: the two-part scene is
inert until admitted; existing single-body behavior is bit-identical when
no part tags are present.

## 6. Order of work after this note

1. Native: part-tag admission + two rigid DOFs + per-part ground rung
   (statics: two blocks on the ground, reactions vs analytic).
2. Native: A↔B loose contact (stack, off-center reactions/torque).
3. Native: weld port (connector carries after separation control).
4. Controls + envelope measurement + evidence run via
   `tools/science_funnel/run_creature.ps1` rails; scoped commit per step.
