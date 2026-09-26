# F02 Discovery Note — how the lineage renders terrain and answers collision/height queries today

Author: M-F02 (terrain rendering + collision). Date: 2026-09-24. Checkout:
`E:/ChimeraWork/monkey-play-20260924`, branch `monkey-play-20260924` (base = game lineage
tip `33e7a444`; F01 integrated at `c9aee37c`). Read-only discovery; no files modified.
Item F02, verbatim: "Rendered ground and physical query surfaces agree within frozen
geometric tolerance. Reuse engine geometry/collision paths." Calculation contract C14:
"Terrain and traversability — compute geometry and gradient/normal consistently with
physical collision representation. Render/query agreement and frozen slope/obstacle cases."

There is no single "terrain system". There are THREE live paths, and F02 must reuse the
agreement MECHANISM each one already proves rather than invent a new one.

## 1. The native engine lane (C++, FROZEN — no edits)

### 1.1 Physics ground: an authored plane, not a heightfield

`ChimeraEngine/engine/earth_environment.hpp`:

- `:41` the ground contact plane is `n_{0,1,0}` by default; `:107` `configure()` rotates it
  from the scene's own `slope_deg`: `n_={-std::sin(s),std::cos(s),0}`,
  `tangent_={std::cos(s),std::sin(s),0}`.
- `:110` reset guard `dot(position,n_)>=r_` ("hand_below_ground"); `:119` per-tick guard
  `dot(x,n_)>=r_-1e-10` ("earth_ground_penetration"). Contact/slide/impact (`:48-86`) are all
  plane algebra on `dot(x,n_)-r_`. There is NO heightfield query anywhere in the native lane.
- `:118` the physical boundary is a DECLARED RULE, not geometry:
  `outside = std::abs(x[0])>patch_half_width_m || std::abs(x[2])>patch_half_width_m`
  (strict `>`); `:124` reports phase `"out_of_patch"`. This is the exact semantics F01's
  declaration binds (`boundary.physical`) and F02 must bind identically.

### 1.2 Render ground: built FROM the same number the physics uses

`ChimeraEngine/engine/graph_earth.hpp::render()`:

- `:102-105` `double size=patch_half_width_m, slope=sim_->config().slope_deg*pi/180;
  auto ground=[&](double x,double z){return V{x,std::tan(slope)*x,z};};` — the rendered
  ground is `y = tan(slope)·x` over a 12×12 quad grid spanning `[-size,size]²`, i.e. exactly
  the plane `n_` the physics presses on. **This is the lineage's render↔query agreement
  mechanism: one number, two projections.** F02 generalizes it: one triangle set, two readers.
- `:100` authored triangles are flat-shaded: `n=cross(sub(b,a),sub(c,a))`, normalized,
  `require(l>1e-16,"earth_render_degenerate")`; every triangle pushes its OWN three vertices
  carrying that face normal (fully duplicated vertices — no shared/smooth normals on
  authored ground).
- `:105` ground colours: two-tone checker `(0.16,0.22,0.17)` / `(0.18,0.24,0.19)` on
  `(i+j)%2` — the exact visual F02 reuses for the clearing ground.

### 1.3 The mesh upload path (the render intake F02's bundle targets)

- `ChimeraEngine/engine/engine.hpp:140-141`:
  `bool load_mesh(const std::vector<float>& verts, const std::vector<uint32_t>& indices,
  uint32_t vcount, uint32_t icount)` — 9 floats per vertex (position 3 + normal 3 + color 3),
  `uint32` triangle indices; `engine.hpp:441` `set_mesh_mode(2)` (fill + wire overlay).
- `ChimeraEngine/engine/main.cpp:753-766` the `--earth-patch` launch flag:
  bundle load → `g_earth.render()` → `engine.load_mesh(...)` → camera. The same upload call
  serves `--science-surface` (`:736`) and `--thermal-salvage` (`:751`); a raw mesh HTTP route
  feeds `g_mesh_req` at `:4266`. Layout is identical on every path.
- `graph_earth.hpp:47-48` the file twin of the same layout: 24-byte header, `nv` vertices ×
  36 bytes, `ni` indices × 4 bytes, with `earth_mesh_length`/`earth_mesh_nonfinite`/
  `earth_mesh_index` strict refusals.
- **`ChimeraEngine/engine/engine.cpp:1854-1937` THE NORMAL-HYGIENE GATE (loads against any
  disagreement):** every uploaded vertex whose stored normal is non-finite or outside
  unit-length `[0.5,2.0]` ("broken"), or whose stored normal points OPPOSITE to the
  winding-consistent area-weighted sum of its adjacent face normals (`dot < 0`, "deviant"),
  is SILENTLY RE-DERIVED by the engine. A mesh whose stored normals disagree with its own
  winding therefore renders with normals the uploader never wrote — render≠query by the
  engine's own correction. **Consequence for F02: the bundle must store normals the gate
  leaves untouched (flat face normals on duplicated vertices: each vertex's normal IS its
  triangle's cross product), and the tests must prove the gate would fire on ZERO vertices.**

### 1.4 Scene bundle intake (the compile/intake pattern F02 follows)

- `tools/science_funnel/common.py:10-56` — `Refusal`, `require`, canonical bytes
  (`json.dumps(sort_keys=True, ensure_ascii=False, separators=(',',':'), allow_nan=False)`),
  `sha`/`digest`, strict `loads` (duplicate-key + non-finite refusals).
- `tools/science_funnel/earth_scene.py::compile_scene` — the bundle pins its own identity:
  `bundle['scene_sha256']=digest(bundle)` (`:46`); `graph_earth.hpp:46` re-checks
  `schema=="chimera.earth_scene.v1"` before anything runs. Schema naming convention
  `chimera.<thing>.v<N>`.

## 2. The Python game lane (the walker — the only live heightfield)

`ChimeraEngine/walker.py` (Z-up frame, the human walker — mechanism, not frame, is what
F02 reuses):

- `:163-196` `heights_at`: THE GROUND UNDER A FOOT, bilinear between the four cells; the
  docstring states the law F02 inherits: "ONE IMPLEMENTATION, and the scalar `height_at`
  below is a call into it. A separate scalar copy is how a foot ends up standing on a
  slightly different surface than the one being drawn, and that gap is invisible until the
  body floats."
- `:199-211` `gradients_at`: central differences with the baseline `h` as an explicit
  argument ("A SLOPE IS SCALE-DEPENDENT").
- `:556-563` THE RENDER: `scene_around` places every ground grain AT
  `Z = heights_at(X, Y)` with `nrm = [-gx, -gy, 1]` normalized from `gradients_at` — the
  render does not approximate an independent surface, it SAMPLES the query surface. This is
  the second agreement mechanism: **the render projection is generated from the query
  function itself.**
- `:329-363` the walker's physical boundary: horizontal position clamped into the patch
  (`max(-patch/2+4, min(...))`) plus a slope gate (repose angle) that refuses moves onto
  ground steeper than the surface can hold.
- `tools/terrain_witness.py:53-161` the lineage's contact witness pattern: sample the WHOLE
  patch including edges (the 13,414 m extrapolation bug appeared ONLY at the edge),
  continuity between adjacent samples, and drive the real walker checking the foot-to-ground
  gap at EVERY step ("floating and sinking are the same bug seen from two sides, and both
  are invisible at one point").
- `tools/stand_in_world.py:113-115` the composition pattern: `ground = scene_around(w)`,
  body offset `gz = height_at(BODY_AT)` — one ground function feeds render placement and
  physics placement alike.

## 3. The gait lane (what walking physics actually touches today)

`tools/science_funnel/gait_scene.py` `:162,178,394` — the gait walker's ground is the scene
contract's `contact_plane_height_m`: contact gap = `pos[1] + radius − plane` on a flat
plane; `ChimeraEngine/engine/gait_controller.hpp` walks that plane (height-hold emergency,
plant heights, all plane-referenced). **No native heightfield exists.** Until one is
qualified (engine C++ is frozen; that is an engine-change decision, not an agent-file edit),
the clearing's terrain collision surface can only live Python-side, consuming F01's grid —
which is exactly what this task declares.

## 4. What F02 reuses (and what it refuses to invent)

| Reused | Citation | Use |
|---|---|---|
| One number → two projections (render built FROM the physics surface) | `graph_earth.hpp:102-105`; `walker.py:556-563` | the bundle's triangle set is written once; renderer and query binding both read it |
| Flat-shaded duplicated vertices, face normal = `cross(b-a, c-a)` normalized, degenerate refusal at 1e-16 | `graph_earth.hpp:100` | ground + post mesh construction and the query normal formula (identical arithmetic both sides) |
| `load_mesh` 9-float vertex layout + uint32 indices | `engine.hpp:140`; `main.cpp:736,751,764` | the bundle's `render.vertices`/`render.indices` are the upload arrays verbatim |
| Normal-hygiene gate as an acceptance criterion | `engine.cpp:1854-1937` | tests prove 0 broken/0 deviant vertices → engine uploads normals untouched |
| Canonical bytes + self-pinned sha256 + strict `require`/`Refusal` intake | `common.py:10-56`; `earth_scene.py:46`; `graph_earth.hpp:46` | `chimera.monkey_terrain.v1` bundle |
| Two-tone ground checker | `graph_earth.hpp:105` | ground colours (post colour is F01's ochre, from the declaration) |
| `out_of_patch` strict-`>` extent rule | `earth_environment.hpp:118` | the boundary binding (`classify`) and query refusal outside |
| Whole-patch sampling incl. edges; every-step contact gap; continuity | `terrain_witness.py:53-161` | the agreement test's sample set and the frozen slope cases |

Not invented here: smooth/shared vertex normals (they would disagree with the piecewise-
linear collision planes and invite the hygiene gate to rewrite them); a bilinear duplicate
of F01's grid (a second scalar truth is the exact bug `walker.py:163-174` documents); any
native-side heightfield (frozen C++; recorded as follow-up).

## 5. The physical collision representation F02 declares

F01's stored 41×41 grid is the geometry source of truth (handoff). The collision
representation built on it is the **triangulated grid**: each 1 m cell splits along the
frozen diagonal `(x_i,z_j)–(x_{i+1},z_{j+1})` into triangle A `(00,01,11)` (covers `tz ≥ tx`)
and triangle B `(00,11,10)` (covers `tz ≤ tx`), wound so `cross(b−a, c−a)` points +Y. Height
and gradient on the surface are the containing triangle's OWN plane values (exact, piecewise
constant); the normal is the engine's formula on the same stored positions. The mesh is not
an approximation OF the collision surface — it IS the collision surface, and the renderer
uploads those exact triangles.

## 6. Frozen input numbers (read from F01's committed declaration, file sha
`18dd2ff65410cd1cf184a7a8df61c7503a6ce15083f30159e727e9a8117bfbc1`, body pin
`aa2607df...8474`)

- Mounds (amplitude, centre, radius): (0.093056, −18.312917, −6.422639, 5.462244),
  (0.094601, −12.927758, 17.030711, 5.220007), (0.104618, 19.265584, 6.057064, 4.329635),
  (0.109930, 13.807676, −18.304543, 5.417989), (0.082347, −9.268795, −11.772370, 5.015110).
- Worst central-difference grid slope 0.034606 m/m at (x=17, z=6) (F01's receipt agrees:
  0.034606 ≤ 0.05). Mound 2 STRADDLES the east extent edge (centre x 19.2656, R 4.3296),
  so boundary-edge height cases stand on a real flank, not the flat base.
- 80 posts at even-integer perimeter coordinates (all are grid nodes); spawn (0,0,0); trunk
  site (11.976783, 0.0, 2.471766).
