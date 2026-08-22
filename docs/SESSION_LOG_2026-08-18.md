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

---

## 2026-08-18 (evening) — SOURCE gate PASSED (second agent session)

- **Engine fix:** `engine.cpp` blend state `dstAlphaBlendFactor` ZERO →
  ONE_MINUS_SRC_ALPHA. The old state wrote straight alpha (the front-most splat's)
  instead of accumulated coverage; every low-alpha Gaussian skirt composited over white
  on readback, washing any dense cloud to white. Measured with a 3-splat RGB probe
  (white skirts, correct centers), fixed, rebuilt, re-probed (clean colored Gaussians).
  Baseline `teddy.splat` re-rendered through the fixed engine: crisp, correct.
- **cpp_bridge:** `_shell_level_buf` now expands the retired 7-float shell rows to the
  14-float 3DGS layout (the engine rejects anything else — silently, 200 + {"ok":false},
  so `_post_membrane_bin` now checks the body). New `render_splat_movie()` — orbit movie
  of a `.splat`, no CPU pre-sort (GPU bitonic sort is authoritative).
- **New bear:** SDXL-Turbo seeds 310/420/530/640 with the §2 T-pose prompt; the eye
  counted duplicated limbs in 310/420 and picked **640** (clean symmetric T). TripoSplat
  (262,144 gaussians, via `C:/Python314` — the torch+CUDA interpreter; the repo venv has
  no torch) → `models/imagegen/tpose2_640.splat`.
- **GATE:** the eye watched the 24-frame orbit movie — exactly 2 arms, back fur ==
  front fur, no defects: **PASS**. Data agrees: arm z-spread σ≈0.05 (no merged
  front+back copies), back ~8–11% darker (failed bear: 40–50%). THE_BEAR_WORKFLOW.md
  step 1 is green; next is RIG (`skeleton.py`) on `tpose2_640.splat`.
- **Dead end recorded:** a TRELLIS-GLB → 14-float sampling detour (mesh sampler,
  `classic.cells/.chimera` voxelization) was reverted and its artifacts deleted — TRELLIS
  stays rejected (THE_BEAR_PIPELINE.md §1).

Agent: Kimi (kimi-code)


---

## 2026-08-18 (late evening) — EXTRACT gate PASSED; workflow reframed

- **Step 3 EXTRACT: DONE on the new bear.** `ChimeraEngine/native/extract_materials.py`
  (new) — k-means, kmeans++ init, z-scored features = chromaticity direction `rgb/|rgb|` +
  `ln(|rgb|)`, fit on 40k subset, 25 iters → per-cluster genome {n, color, log_size, aniso,
  opacity, bbox}. The eye named 3 materials (tan plush, cream pads, black smooth).
  Final genomes → `ChimeraEngine/native/teddy2_materials.json` + per-splat assignment
  `teddy2_assignment.npy`: tan plush n=249,184 rgb (0.58,0.44,0.31) opacity 0.113; cream
  pads n=10,958 rgb (0.84,0.71,0.54) opacity 0.116; black smooth n=2,002 rgb (0,0,0)
  log_size −5.79 aniso 19.2 opacity 0.293.
- **Measured extraction pitfalls (recorded in THE_BEAR_WORKFLOW.md step 3 so nobody repays
  them):** blind global k-means cannot isolate cream (same hue as tan, tiny population);
  black needs a 2-means split on **log** intensity over the darker half (raw-intensity
  swallows shaded fur); cream needs eye-drawn freeform regions
  (`active_labeler.query_region`) then 2-means on **raw** intensity, keep bright half (log
  compresses the bright tail).
- **GATE:** the eye confirmed the recolor preview
  (`ChimeraEngine/output/teddy2_recolor_front.png`) — tan body, cream muzzle/paws, dark
  nose/eyes present and separated (soft edges expected: a material-average repaint). PASS.
- **Workflow reframe (operator directive):** THE_BEAR_WORKFLOW.md is now titled THE
  GAME-ASSET WORKFLOW — the bear is instance #1, and the steps generalize to every asset.
  Recorded the long-term goal there: reproduce the whole workflow as a tool-call system,
  possibly an MCP server. Not built yet.
- **Engine insight from the operator:** the bear's see-through back is a *model-generation*
  property (measured opacities are 0.09–0.29) and the expected fix is step 4 REAPPLY
  material control — not a renderer defect. The Vulkan blend/sort path stays as-is.

Agent: Kimi (kimi-code)


---

## 2026-08-18 (late evening, cont.) — REAPPLY gate PASSED

- **Step 4 REAPPLY: DONE.** New `ChimeraEngine/native/reapply_materials.py` (theory stated
  in its header, Rule 0): repaint each splat to its material genome — color = material mean
  RGB, geomean(scale) = material front mean (anisotropy preserved), alpha = material FRONT
  mean so the back inherits the front's coverage. Writes raw 32-byte `.splat` records;
  positions/rotations untouched. Output: `models/imagegen/tpose2_640_repainted.splat`.
- **Theory confirmed by measurement:** the see-through back WAS a generation asymmetry —
  pre-repaint tan opacity 0.102 back vs 0.129 front, cream 0.021 back vs 0.173 front.
  Post-repaint the distributions are identical by construction; the eye confirmed the back
  render is fully opaque, uniform tan, defect-free.
- **Region refinement:** the front-only material regions had bled through z (4,105 cream +
  1,761 black splats on the back half — the eye saw a beige oval + dark smudge on the back).
  Reassigned to tan plush; final counts tan 255,050 / cream 6,853 / black 241.
- **Workflow docs:** THE_BEAR_WORKFLOW.md reframed as THE GAME-ASSET WORKFLOW (bear =
  instance #1), steps 3 and 4 marked DONE with the measured pitfalls recorded; the
  tool-call/MCP-server reproducibility goal is logged in the header.
- **Next:** step 5 RIG — `ChimeraEngine/native/skeleton.py analyze|mark|triangulate|assign`
  on the repainted bear.

Agent: Kimi (kimi-code)

---

## 2026-08-19 — RIG gate: SKIN membrane PASSED (LBS band on the splat teddy)

- **Research first (operator directive):** how people rig static objects —
  `docs/research/rigging_static_objects_reference.md`. Conclusions applied: rigid
  nearest-bone IS the standard rigid floor; plush wants a narrow smooth LBS band; the 3DGS
  literature skins means by LBS, transports Gaussian rotations by weighted quaternion
  average, and leaves scale/opacity/color untouched.
- **Eye symmetrization (step 3 refinement):** the eye's two anchored eye rings were
  asymmetric (x=-0.042 vs +0.126 — one eye read as "on the snout"). A close-up render of
  the face showed the true eyes symmetric at |x|~0.07-0.08. Fix: `_symmetrize_eyes`
  mirror-averages the pair across x=0 (same philosophy as the stick figure) with bead
  radius = mean of the two rings' own radii. Symmetric bead eyes confirmed in the render.
- **Joint axis lines (operator request):** `stickfigure.py hinge_axes` draws each joint's
  hinge axis as a magenta dashed centerline in the overlay, mechanical-drawing style,
  with a center cross when the axis is seen end-on. Derivation rule: bone_dir x world_up,
  fallback bone_dir x world_front.
- **New `ChimeraEngine/native/skin.py` — the SKIN membrane (Rule 0 header):**
  `weights` = primary bone from the part labels + a smooth LBS band at each joint
  (band = 0.8 x the limb's MEASURED cross-section radius at the joint — the seam a bend
  opens is ~r*theta — along-bone distance to the joint plane + a lateral gate; 87k blended,
  175k rigid). `pose` = FK over the bone tree (BONE_TREE, root=torso), means by LBS,
  rotations by sign-aligned weighted quaternion blend, scale/alpha/color untouched.
- **The streak hunt (why the cut changed again):** the first posed render had a spike
  below the bent arm. Measured: NOT the giant fillers, but armpit/chest-wedge splats
  (x~0.15, medial of the shoulder at 0.268) bound to the short uparm stub by segment
  Voronoi. A radial cap failed (wedge contiguous with the arm cylinder — no percentile
  separates it); the **limb-root plane rule** (a limb claims only splats beyond its root
  joint along the limb axis) fixed it. Arms now section from the torso edge.
- **Gates:** posed orbit (shoulder 45 + elbow 40 + neck 15) — eye verdict **PASS** (fur
  continuous at shoulder/elbow, no cracks, no artifacts); confirmed on the frames directly.
  The painted-verify eye run returned a one-line "FAIL: bleed", then specifics-on-demand
  named only the arms' OWN palette colors on side views = end-on arm discs misread as
  foreign blobs. FALSE POSITIVE (frames f00/f05/f08/f13 checked directly: no bleed);
  `section.py verify` prompt amended to tell the eye about end-on arms.
- **Housekeeping:** 314 giant filler splats are alpha-hidden in POSED renders only
  (static haze, but they streak when rotated).
- **Next membrane:** step 6 DRIVE — pose should EMERGE from the CA/force solver, not from
  a spec file; the skin weights + FK machinery are the interface it drives.

Agent: Kimi (kimi-code)

## 2026-08-19 (cont.) — THE KOALA PIVOT: real-capture 3DGS, quadruped branch, full pipeline PASSED

- **The pivot (operator directive):** ALL single-image AI-generated 3D rejected — TripoSplat
  AND TRELLIS ("ability to generate objects from 2D imagery is unacceptable"). Sources must
  be real-capture 3DGS, mesh-derived 3DGS (exact geometry), or native-3D generative models
  (GaussianCube/DiffSplat lane, noted for background props, with our gates as the quality
  filter). What matters is THE STEPS recorded correctly — the pipeline, not the bear.
- **SOURCE (instance #2):** the koala from marcelpadilla/splats — `models/koala/koala_500k.splat`
  (500k splats, sha256 verified against published meta, CC-BY-3.0 YahooJAPAN / Marcel
  Padilla). Mesh2splat from a known mesh = exact geometry; monochrome green (LOD color
  encoding), alpha all 1.0, no SH. Wrote `koala_500k_front.splat` (raw-space rotation
  applied to positions+quats, repacked 32-byte records) so front=+z and the f08=front orbit
  convention holds. **Use the _front file for everything downstream.**
- **STICK FIGURE (quadruped):** new `ChimeraEngine/native/stickfigure_quad.py` — measure the
  cloud (feet = k-means(4) on the bottom band, floor = p3 y, back = flat trunk top,
  head-lobe span) then fit a SYMMETRIC 14-joint quadruped (head/neck/chest/pelvis + 4 legs
  as 2-bone chains). **The neck rule that works:** ears = the width MAXIMUM of the front
  region; neck = the width minimum strictly between chest and ear_z. (First version's
  unbounded minimum ran into the head and grabbed the narrowing snout — measured.)
- **Anatomy is RESEARCHED, not guessed (operator directive: "nothing more than physics and
  biometrics"):** `docs/research/koala_anatomy_reference.md` (Hawkins 2022 humerus CT
  morphometry; Finch & Freedman 1988 via Black et al. 2012). `LEG_MID_FRAC` derived:
  elbow = radius/(humerus+radius) = 0.526 up the leg column; knee = tibia/(femur+tibia) =
  0.441 (tibia markedly shorter than femur). Overlay gate: bones inside the silhouette on
  all 4 views.
- **SECTION + SKIN are now species-parameterized:** `section.py SPECIES_SPECS` (biped
  default untouched; quadruped = QUAD_SKEL_BONES/TIPS/ROOT_PLANE selected from the skeleton
  JSON's "species" field). Quadruped torso bone runs pelvis->NECK (not chest — a
  pelvis->chest bone orphans the shoulder region between them). `skin.py _skin_spec` does
  the same for BONE_TREE/JOINT_BONES/FK order; `_quad_hinge_axes` replicates the
  stickfigure hinge rule over the quad tree. Teddy path untouched.
- **Eye marks on a MONOCHROME face (token discipline kept: one watch() per stage):**
  nose/muzzle/ear rings anchored fine; eyes (3 vs 2 points) and mouth (ring_r=0.151 = the
  whole lower face) were junk — dropped from marks3d.json before the cut. `_symmetrize_eyes`
  strengthened to pool asymmetric evidence (was a silent no-op under 3+3).
  `section.py mark` gained `--subject` (prompt noun) and `--rings-only` (the skeleton cut
  path needs only face rings + spacing — seeds/bands skipped, saving eye tokens).
- **Cut (quadruped):** 10 bones + 4 paw tips + 4 face rings; counts plausible (torso 131k,
  head 85k, thighs 24-40k, paws 2.7-4.8k). Eye verify verdict **PASS** (no bleed, no
  splits); confirmed on the frames directly. Note: the front view shows chest-blue under
  the chin — the koala's head is forward-flexed (per anatomy), so the chest is genuinely
  visible under it face-on; not bleed.
- **POSE GATES — the LBS envelope is now MEASURED on a second species:**
  - `pose_reach.json` (shoulder 55 deg — the arboreal reach): FK numerics correct (front
    foot +0.27 forward, head up), but the eye verdict **FAIL**: a background gap opens at
    the armpit at 55 deg — the surface-only cloud has NO splats on the concavity the lifted
    leg exposes (not a bug; a coverage property). The eye's "streaky/banded shading"
    complaint was the source asset's own LOD shading, not skinning.
  - `pose_walk.json` (shoulder 30, elbow -15, neck 15, hip -10, knee 15 — gait range):
    eye verdict **PASS**, no artifacts; confirmed on the frames directly.
  - **Envelope: LBS passes at <= ~30 deg shoulder, fails at 55 deg.** Beyond the envelope
    needs DQS or corrective coverage splats — the same open LBS-vs-DQS question as the
    teddy's stress poses (95/90 deg, never eye-verified), now with a measured edge.
- **Next:** DRIVE (pose emerges from the CA/force solver); the CA <-> 14-float skin bridge
  (THE_RENDERER_DECISION.md NEXT MEMBRANE); eyes for the koala (monochrome face defeated
  the eye rings — needs shading-independent marking or manual anchors); envelope-widening
  (DQS or corrective splats) if poses past ~30 deg are wanted.

Agent: Kimi (kimi-code)
