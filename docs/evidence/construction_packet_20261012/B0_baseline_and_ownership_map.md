# B0 / M0 — Identify the real path: baseline pin and position-ownership map

Date: 2026-10-12. Gate: §13 construction-qualification table, row **B0 / M0 —
identify the real path** in `docs/GAME_PLAN_ACTION_RPG.md` (lines 1936–1937):
"Pin the current executable/source, materials and mesh; map every position writer
and every physical/render consumer." Exit evidence claimed here: *baseline can be
recovered; current demo, standalone references and target architecture are
distinguished.*

This is the first artifact of the **construction packet** assignment (§13
"Immediate next engineering assignment", lines 1919–1926): reconcile the geometry
and attachment reference code into one narrowly scoped packet — two asymmetric
material parts, one loose-contact case, one finite-area connection — with the same
accepted geometry driving loads, native drawing and selection.

## 1. Pinned identities

| Item | Identity |
|---|---|
| Branch | `WK-ENGINE-PATHS-20260929-PR` |
| Source HEAD at map time | `f5afc75131b45b2ac990eaa2277bbdae0ddbc9de` ("Engine fix: book drive elastic baseline at arm time; ledger continuous across sever/re-arm") |
| Native executable | `.tmp/body-engine/Release/chimera_engine.exe`, 2,625,536 bytes, built 2026-10-11 16:53, SHA-256 `2e892160f5234260d3802f8366a3e0523f5227e468883dcb1abfe5f43654b0fd` |
| Build command | `cmake -S ChimeraEngine/engine -B .tmp/body-engine` then `cmake --build .tmp/body-engine --config Release` (driven by `tools/science_funnel/run_creature.ps1`) |
| Launch | `chimera_engine.exe 8110 --hidden 1600 900 --no-restore` + `tools/game_shell/server.py 8210` |
| Materials/mesh inputs | membrane demo mesh armed via `/mesh_bin`; science surface / thermal salvage / earth patch optional JSON bundles (`--science-surface`, `--thermal-salvage`, `--earth-patch`); tendon drive armed via HTTP (`{"joint_index":…,"u":…}`) |
| Working-tree caveat | many files dirty from other agents (`.roo/`, screenshots, `ui.cpp`, evidence churn). This gate commits explicit paths only; nothing else is touched. |

Recovery: a clean checkout at this HEAD plus the build command reproduces the
executable; the stale `ChimeraEngine/engine/build/Release/chimera_engine.exe`
(2026-10-09) is *not* the pinned build.

## 2. Position ownership: one owner, three stores

The live physical world is a **single owned membrane body** in
`ChimeraEngine/engine/membrane_tick.{hpp,cpp}`:

| Store | Location | Role |
|---|---|---|
| `base_pos_` | membrane_tick.cpp:260 | reference/rest positions (9 floats/vertex: pos, normal, color) |
| `verts9` | membrane_tick.cpp:369–418 | working positions during the tick (pose transforms write here) |
| `published_verts_` | membrane_tick.hpp:365 | "final posed/contact surface, under seal_mtx_" — the accepted surface |

### Every position writer (live runtime)

| Writer | Location | What it writes |
|---|---|---|
| Arm / initial publish | membrane_tick.cpp:261 | `published_verts_ = base_pos` |
| Tick publish | membrane_tick.cpp:917 | `published_verts_ = verts9` |
| Body activation | membrane_tick.cpp:1015 | `published_verts_ = base_pos_` + `body_active_` release-store |
| Pose/rotation transforms | membrane_tick.cpp:369, 384–386, 416–418 | `verts9` (rigid/pose edits inside the tick) |
| Full-mesh import/update | engine.cpp:2172 `Engine::update_mesh()` → `mesh_upload()`; HTTP `/mesh_bin` (main.cpp route list :107) | replaces the whole mesh — **not a live assembly API** (plan §11.14) |

### Single-owner guard

`main.cpp:739–746`: while the membrane body is live, a static set of *competing*
pose routes (`/hinge_bin`, `/joints*`, `/stride*`, `/gait*`, `/volp*`, `/matter`,
`/skin_bin`, `/pose_apply`, `/tick_rig`, `/tick_flex`, `/tick_joints`,
`/tick_classify`, `/tick_vertbind`, `/water_vis`) and any mesh update are refused
with `{"ok":false,"error":"shared_body_owns_surface"}`. This is the engine's
existing enforcement of "one pose owner" and the hook point where construction
transactions must pass (or be refused) in the future.

### Every physical/render consumer of the accepted surface

| Consumer | Location | Uses |
|---|---|---|
| Contact/ground readback | membrane_tick.cpp:1428 (`surface()` = `published_verts_` when body active, else `verts9`), :1438 (base surface) | ground rung `k_ground_ = 1.3562e7 N/m`, `c_ground_ = 6.062e5 N·s/m`, touch/stance checks |
| Vulkan triangle lane | engine.cpp:2168, 2403 `vkCmdCopyBuffer(tri_staging_buf_ → tri_vbuf_)` | native drawing of the posed surface |
| Particle/GPU lanes | engine.cpp:5997/6031 (`vel_buf_`, `pos_buf_` uploads) | particle demo lanes (separate from the membrane body) |
| Selection / picking | engine.cpp:6885–6995 `pick`/`pick_cam` raycasts over `verts9`; main.cpp:1532, 1567 routes over `g_tick_verts` | mouse picking against the physical surface |
| Browser shell proxy | tools/game_shell/server.py:76, 180–183 — `/api/verts` → engine `/verts` at 3 Hz | visible display of the accepted surface |

## 3. Current demo vs standalone references vs target architecture

- **Current demo (live runtime):** one membrane body, one pose owner, triangle
  render lane, HTTP-driven mesh/pose. Body force/support exists (`gravity_on_`,
  ground rung, sealed-cell pressure rungs per `SEAL_PREREGISTRATION.md`).
- **Standalone references (CPU, untracked on this branch — see §5):**
  `tools/material_volume.py` (conservative tetrahedral material-volume compiler:
  stable `MaterialSpec`/`RegionSpec`/`BoundaryFace`/`MaterialInterface` IDs,
  `MassProperties`, `CompilerReason` refusals incl. `OPEN_BOUNDARY`);
  `tools/finite_area_attachment/` (area-weld connector: energy/forces/tangent,
  admission gate `assert_min_couple_stiffness`, native two-body + ground fixtures);
  `tools/assembly_handoff/` (readiness judge; its own verdict
  `dynamics_trial_ready = false`). All 48 tests of the first two pass at this HEAD
  (2026-10-12, `python -m pytest tools/material_volume.py
  tools/finite_area_attachment/ -q` → 48 passed).
- **Target architecture (plan §11, not yet in the runtime):** region-and-interface
  complex with material regions, boundary patches, physical ports, active
  interaction records, conservative topology transactions, and the accepted state
  consumed by contact, rendering, picking and persistence. None of these exist as
  runtime code; `docs/PHYSICAL_PORTS.md` is an adopted definition, explicitly
  "not a runtime qualification".

## 4. Known limitations at this baseline

- No second independent body, no loose contact, no finite-area connector in the
  native runtime (B2 not started).
- `/mesh_bin` full-mesh replacement is the only geometry admission path; there is
  no transactional edit, no old→new lineage, no stable material IDs in the runtime.
- The three reference tools are untracked on this branch (they live on
  `origin/review/ASSEMBLY-INPUTS-20261004` / `origin/astra/gait-capture` history);
  the construction packet commits its own scoped copies/tests so the gate evidence
  is reproducible from this branch.
- Do not confuse `docs/evidence/agent_fleet/MATTER_KERNEL/B1…B5_PREREGISTRATION.md`
  (matter-kernel gauntlet, 2026-09-25) with §13 construction gates B0–B4.

## 5. Consequence for the next gate (B1)

B1 compiles the packet's geometry with the existing conservative compiler:
two asymmetric solid templates, one tapered layer, one open-surface refusal
control; checks stable material/region/boundary IDs, positive volumes,
mass/COM/inertia against reference arithmetic, correct interface orientation, and
no overlapping ownership — reusing `tools/material_volume.py` checks rather than
writing a second compiler. See `B1_construction_packet_compile.md` in this
directory.
