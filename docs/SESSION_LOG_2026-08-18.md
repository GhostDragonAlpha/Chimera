# SESSION LOG — 2026-08-18

Sweeps into git the work that had been sitting uncommitted on the working tree. It is a
record, not a theory: each subsystem below keeps its own Rule-0 membranes in its own doc.
The renderer's claims live in [`THE_RENDERER_DECISION.md`](THE_RENDERER_DECISION.md).

## 1. The renderer — C++ Vulkan engine (`ChimeraEngine/engine/`)

The C++ engine is the renderer (decision recorded in `THE_RENDERER_DECISION.md`). This
session's corrections are appended there. In one line: the engine now renders **3DGS
splats** (`teddy.splat`, 14 floats/splat), sorts them **back-to-front on the GPU** (a
compute-shader bitonic sort in `shaders/sort.comp`), renders **upright** (Vulkan Y-flip
fixed in `perspective()`), has a **free-spin orbit camera** (analytic derivative up
vector, no pole clamp), and runs **uncapped FPS** (GPU-bound, ~340–470 fps rotating).

- `engine.cpp` / `engine.hpp` — offscreen target + present path, pipeline/render-pass
  alignment, GPU bitonic sort, Y-flip, free-spin camera, vertical-drag sign.
- `main.cpp` — uncapped render loop with a 1 s FPS line.
- `CMakeLists.txt` — compiles `sort.comp`; copies compiled `.spv` beside the exe (the
  engine loads shaders relative to CWD).
- `shaders/sort.comp` — one shader, two modes: depth→sortable-key, bitonic compare-swap.
- `cpp_bridge.py` — `load_splat()` / `render_splat()` decode the TripoSplat `.splat`
  format and apply the web viewer's orientation (`M = Rx(180°)·Ry(90°)`), so the C++
  window matches `viewer.html?ply=teddy.splat`.

## 2. The SPIACE body — the membrane hierarchy (`ChimeraEngine/engine_state.py`)

The story hierarchy was rewritten from the old solar-system/verb tree to the **teddy-bear
body** — the progression the membranes actually prove:

```
theSeed → theShape → theMuscle → theRig → theGait → theScan → theChoose
        → theControl → theWorld → theAppearance → theMeaning
```

Each movement now names a body stage (voxel lattice → muscle columns → derived rig → gait
beat machine → retinal senses → Q-learning policy → control → training world → splat skin
→ the eye judges it). `BUILT`, `GRANDFATHERED_TERMS` (now empty — every new membrane must
earn its pointer), and the seed/first-open bookkeeping were aligned to it. `_appearance()`
now routes through `cpp_bridge.render_term()` first (C++ engine as emission target), with
`splat_appearance` as the fallback.

## 3. LightEngine — the CA growth engine (`LightEngine/`)

A new engine for growing the teddy's body as a cellular automaton. Modules:

- `kernel.py`, `modifier.py`, `neighbor.py`, `referee.py` — CA kernel, rule modifiers,
  neighbor topology, and the referee that adjudicates growth.
- `rope_network.py`, `spine_structures.py`, `skeleton_structures.py` — the body scaffold:
  rope networks, spine, skeleton.
- `kinematic/` — dynamics (Numba-accelerated), including a standing demo
  (`build_standing_demo.py`, `serve_standing_demo.py`).
- `demo_*`, `trace_search.py`, `queue_runner.py`, `hierarchy_import/` — demonstrations,
  search, and WordNet term grafting.

This is "the physics system is the rendering system": the same CA that grows the body is
what later emits the splats.

## 4. The unified SDF substrate (`ChimeraEngine/core/` + `sdf_body.py` + `master_loop_sdf.py`)

A membrane whose **shape IS a signed distance field** — not a mesh, not a convex hull.

- `ChimeraEngine/core/sdf_grid.py` — sparse hash-grid SDF. Same grid answers collision,
  surface extraction, and deformation.
- `ChimeraEngine/core/sdf_gpu.py` — GPU-native SDF contact (CUDA kernel samples the sparse
  volume trilinearly; `∇SDF` = contact normal, `-sdf` = penetration). CPU solver kept as
  the Rule-0 oracle (penetration must agree within 1e-3).
- `ChimeraEngine/sdf_body.py` — `SDFBody`: physics acts on the grid; rendering reads the
  same grid.
- `ChimeraEngine/master_loop_sdf.py` — end-to-end wiring (genome → skeleton → sparse SDF
  grid → contact solver + surface splats).
- `ChimeraEngine/hierarchical_verifier.py` — proves each SDF level (voxel → surface voxels
  → contact pair → SDFBody → SDFWorld → rendered world).

## 5. The teddy skin (`ChimeraEngine/native/teddy_pyramid.py`)

Removed the color **deviation clamp** and the aggressive **luminance floor + gain** — they
were lifting the teddy's black eyes/nose toward the brown neighborhood mean, which is why
the face was missing. Only near-black is lifted now (pure black reads as a hole); eyes stay
dark. This is the OTHER half of the face fix, beside the renderer's orientation.

## 6. Perception (`ChimeraEngine/senses.py`)

Vision rides Ollama's `qwen3.8` over the OpenAI-compatible endpoint, with `think:false`
(it is a reasoning model; with thinking on it burns the budget on a hidden chain and
returns empty). `num_ctx` is sized exactly to the frames (measured 86 tokens/frame @ 384px).
`see()` reads one image; `watch()` reads an ordered frame sequence as a movie. This is the
eye used for the skeleton photogrammetry in `THE_RENDERER_DECISION.md`'s NEXT MEMBRANE.

## 7. Splat appearance bridge (`ChimeraEngine/splat_appearance.py`, `terms_data.py`)

- `splat_appearance.py` — the bridge from story membranes to splat buffers: each
  `story/*/physics.py` `emit(nums, t)` returns an `(N, 28)` buffer; `movie_buffers()`
  picks the two frames that carry a term's claim and shares them between the Python
  renderer and `cpp_bridge`.
- `terms_data.py` — the declared term list, realigned to the body hierarchy.

## 8. Docs

- `Chimera/docs/THE_STORY.md` — rewritten around the body progression above.
- `Chimera/docs/DREAM_REPORT.md`, `HERALD.md`, `HISTORY_BOOK.md`, `chimera_dna_graph.json`
  — the story's dream/herald/history and the DNA graph, updated to match.
- `AGENTS.md`, `ChimeraEngine/ONBOARDING.md` — pointers realigned.

## Excluded (never commit)

`models/` (tens of GB of downloaded PLY/GLB/.splat — several exceed GitHub's 100 MB
limit), `/output/`, `/test-results/`, `/LightEngine/output/`,
`/ChimeraEngine/native/genomes/` (regenerated splat-pyramid data + LOD caches),
`/ChimeraEngine/demo_output/`, `/ChimeraEngine/matrix_out/`, `cookies.txt` (secret),
`/ChimeraEngine/native/viewer.exe` (binary), and root-level `_*` scratch. All added to
`.gitignore`.

Agent: Kilo (chimera-code)
