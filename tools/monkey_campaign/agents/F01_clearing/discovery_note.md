# F01 Discovery Note — existing scene machinery and the engine's coordinate convention

Author: M-F01 (clearing authoring). Date: 2026-09-24. Checkout:
`E:/ChimeraWork/monkey-play-20260924`, branch `monkey-play-20260924`, HEAD `8c60bea3`
(base = game lineage master `32105f18`). Read-only discovery; no files modified.

## 1. What exists today (the scene-declaration pattern this task reuses)

The live product path for native-engine scenes is the **compiled scene bundle** used by
`tools/science_funnel/*_scene.py` and consumed by the native engine through frozen CLI
flags + HTTP routes:

1. **Python compiles a JSON bundle** (`earth_scene.py::compile_scene`,
   `surface_scene.py::compile_scene`) and writes it as **canonical bytes**:
   `json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',',':'),
   allow_nan=False).encode('utf-8')` — `tools/science_funnel/common.py::canonical`
   (lines 21-23). The bundle pins its own identity:
   `bundle['scene_sha256'] = sha256(canonical(bundle))` (`earth_scene.py:46`).
2. **The native side loads the file and `require`s the schema string** before anything
   runs: `require(bundle.at("schema")=="chimera.earth_scene.v1", ...)` —
   `ChimeraEngine/engine/graph_earth.hpp:42`; the per-trial contract re-checks
   `schema=='chimera.earth_patch.v1' and tick_hz==300`
   (`earth_environment.hpp:91`). The engine launches with the scene path as a CLI flag
   (`--earth-patch <scene.json>`, `main.cpp:697-705`), builds render geometry from the
   bundle, and uploads it (`engine.load_mesh`).
3. **Strict intake helpers** are the house style: `require(condition, code, detail)`
   raising `Refusal`, duplicate-key refusal, non-finite-number refusal
   (`common.py:10-56`); the campaign's own `integrity.py` uses the same canonical-digest
   scheme (`ALGORITHM='sha256-chimera-json-v1'`).
4. **Schema naming convention**: `chimera.<thing>.v<N>` (`chimera.earth_scene.v1`,
   `chimera.earth_patch.v1`, `chimera.surface.v1`, `chimera.coupled_scene.v1`).
5. **The render mesh contract** (what F02 will consume): vertices are **9 floats =
   position(3) + normal(3) + color(3)**, `uint32` indices, triangle normals computed as
   `cross(b-a, c-a)` (`graph_earth.hpp:26-30, 82`); ground geometry is authored
   directly in world metres as quads (`graph_earth.hpp:84-87`).
6. **Extent semantics already exist**: the earth patch is a square of half-width
   `patch_half_width_m` centred at the origin; "outside" is
   `abs(x[0])>half || abs(x[2])>half` (`earth_environment.hpp:118`) — a **declared rule,
   not a wall mesh**. Status reports phase `out_of_patch`.

What I reuse: canonical bytes + self-pinned sha256; `chimera.*.v1` schema naming;
strict `require`/`Refusal` intake; SI metres with `_m` field suffixes; square
half-width extent; declared-boundary (not invisible-wall) semantics; deterministic
compile from a frozen recipe.

Not reused / explicitly out of scope: `Chimera/core/level_composer.py` (the retired
UE5 pipeline), `Chimera/core/scene3d.py` (the old planet/world-model software
rasteriser, Z-up, planet-relative — a different lineage), and the science funnels'
graph-store admission (`CreatureGraph`) — F01's clearing is authored data for the
monkey product lane, not a graph admission, so no graph writes are needed or made.

## 2. The engine's coordinate convention (with citations)

**Right-handed, Y-up, metres, origin at scene centre, ground plane at y=0.**

| Fact | Citation |
|---|---|
| Gravity is −Y, so +Y is UP | `ChimeraEngine/engine/coupled_dynamics.hpp:52` — `gravity_{0,-gravity,0}` |
| y is height; metres | `earth_environment.hpp:44` — potential `m_*g_*x[1]`; `:68` — acceleration `{0,-geff_,0}` |
| Ground plane y=0, normal +Y | `earth_environment.hpp:41` — `n_{0,1,0}`; `:110` reset guard `dot(position,n_)>=r_` ("hand_below_ground") |
| Local frame EUS (x=east, y=up, z=south) | `earth_environment.hpp:13-23` (`local_to_ecef` composes east·x + up·y + south·z); Python twin `tools/science_funnel/earth_scene.py::local_frame` |
| Frame is right-handed | `ChimeraEngine/engine/tests_environment/native.cpp:13` — `right_handed_frame`: `norm(cross(east,up)-south)<1e-14` |
| Units are SI metres | `tools/science_funnel/units.py` — canonical length unit `m`; field suffix `_m` throughout scenes |
| Extent = square half-width, centred | `earth_environment.hpp:118` |
| Renderer consumes world-space metres as uploaded | `graph_earth.hpp:84-87` (ground quads at y = tan(slope)·x in metres); `main.cpp:700-703` (`load_mesh` + camera) |
| Camera is spherical r/theta/phi + look_at | `engine.hpp:46` (`set_camera`), `engine.hpp:334` (`set_camera_full(float[8])`); `engine.cpp:5978` `look_at` is a standard right-handed look-at; Vulkan Y-down NDC flip handled at projection (`engine.cpp:5967`) — clip space, not world space |
| Fixed tick 300 Hz | `earth_environment.hpp:91,98` |

The F01 clearing adopts this exactly: **metres, +Y up, right-handed (x east, y up,
z south), square extent centred at the origin with the physical boundary at
|x| = half_width and |z| = half_width, base ground at y=0.**

## 3. Where the new files go (declared before implementation)

The existing data convention is `tools/<area>/data/<scene>/`
(`tools/science_funnel/data/earth`, `data/coolprop`). `Chimera/data/` does not exist.
Declared paths (all NEW; nothing existing is modified):

- `tools/monkey_campaign/data/monkey_clearing/clearing_recipe.py` — stdlib-only
  deterministic recipe + strict loader/validator (importable as
  `tools.monkey_campaign.data.monkey_clearing.clearing_recipe` from the repo root;
  namespace packages, no `__init__` needed, Python 3.11+).
- `tools/monkey_campaign/data/monkey_clearing/clearing_declaration.json` — the
  compiled, canonical-bytes declaration (`chimera.monkey_clearing.v1`).
- Ownership stays inside `tools/monkey_campaign/agents/F01_clearing/` (notes, prereg,
  tests, receipts) plus the two declared data files.

## 4. Follow-up needs recorded (not done here, per brief)

- Exercising the engine HTTP contract with the clearing (launching the native engine)
  is a follow-up need — F02's task (rendering + collision), not exercised in this
  CPU-only data-authoring task.
- The walking anchors' scene `f6844ee` is referenced only in the completion map; no
  scene file by that id exists in this worktree. The clearing declaration is written
  so F02 can bind whatever collision/render path the walking runtime actually uses.
