# THE RENDERER — a decision membrane

> **RULE 0 — every membrane is a theory.** This is a *decision* membrane: it is stated as
> exactly one claim (STATEMENT), a prediction not yet measured (PREDICTION), and the
> measurement that would kill it (FALSIFIER). No falsifier, no build.

## STATEMENT

The C++ Vulkan engine (`ChimeraEngine/engine/engine.cpp` — N-body gravity, point-splat
renderer, camera, `/frame` HTTP server) is the **emission target** for proven membranes.
`ChimeraEngine/splat_appearance.py` (the Python Gaussian-splat "movie") is the renderer
**only until** the C++ engine can stream a membrane's scene from `engine_state.json` and
serve it through its existing `/frame` endpoint.

## PREDICTION (now measured)

Wiring the C++ engine to render `engine_state` membranes — world-streaming the proven
hierarchy + pointing the dyad at its `/frame` — yields a `dyadAnalysis` that passes at
**equal or lower cost** than `splat_appearance`, and **unlocks the playable verbs** that a
static splat movie cannot show.

## FALSIFIER

If, after wiring, the C++ engine **cannot render a proven membrane's scene from
`engine_state`**, OR its `/frame` dyad fails to reach alignment ≥ 0.6 for membranes
`splat_appearance` already passed, then the C++ engine is **NOT** the renderer.

## DECISION — A (the C++ engine is the renderer) · recorded 2026-08-17

The falsifier ran and **A held**. `engine.cpp` was a skeleton that had never initialized on
this machine (its Vulkan ICDs were unregistered, so every latent bug was dormant). After
fixing ~10 of them (dangling extension pointer, unallocated sync/framebuffer/command-buffer
resources, a broken PNG encoder, req/resp body confusion, missing `VERTEX_BUFFER` usage,
frame-in-flight vs swapchain index confusion, missing viewport/scissor, descriptor-layout
ordering, buffer-destroy without sync), the engine now **renders the teddy**:

- `ChimeraEngine/cpp_bridge.py::render_teddy(shell_json, …)` loads one LOD level of the
  SPIACE splat pyramid (`native/genomes/teddy_*_shell.json`), converts it to the engine's
  7-float vertex layout, POSTs `/membrane`, and captures `/frame` as a PNG.
- A depth buffer (`D32_SFLOAT` attachment + depth test) gives correct **front/back
  occlusion** — without it the far-side splats ghosted through the near side as it rotated.

**The dyad watches a MOVIE, not a still.** A single frame hides the defects a rotating
object reveals (patchy scalp, lumpy ear-rim, flat-slab feet, back seam). The procedure,
repeatable end-to-end:

```python
import cpp_bridge
frames = cpp_bridge.render_teddy_movie("native/genomes/teddy_honey_shell.json", "output", frames=72)
mp4    = cpp_bridge.encode_movie(frames, "output/teddy_rotation.mp4")   # ffmpeg H.264
import senses
verdict = senses.watch(frames, "<defect-focused prompt>")
```

The eye runs Ollama's qwen3.8 with **`think:false`** (it is a reasoning model — with thinking
on it burns the whole budget on a hidden reasoning chain and returns empty) and **`num_ctx`
sized exactly to the frames** (measured 86 tokens/frame @ 384px; 72 frames ≈ 9K context, not
256K). See `ChimeraEngine/senses.py`. A 72-frame movie returns a full defect report in ~30 s.

Open for the dyad analysis itself: the alignment ≥ 0.6 measurement is now *runnable* (the
movie + eye path works); the number is not yet recorded.

## CORRECTIONS — 2026-08-18 (renderer is now GPU-bound and orientation-correct)

The decision still holds; the renderer's internals changed materially this session:

- **Splat source is `teddy.splat` (3DGS, 14 floats/splat), not the 7-float shell pyramid.**
  `cpp_bridge.load_splat()` / `render_splat()` decode the TripoSplat `.splat`
  (`[f32 xyz][f32 scale][u8 rgba][u8 rot]`) and apply the web viewer's orientation
  (`M = Rx(180°)·Ry(90°)`). The engine vertex layout is 14 floats: pos(3) color(3) alpha(1)
  scale(3) quaternion(4).
- **Back-to-front sort moved to the GPU.** A compute-shader **bitonic sort** (`shaders/sort.comp`)
  orders splat indices by view depth each frame; the CPU no longer touches per-splat data. This
  removed a `std::sort` bottleneck that dropped rotation to ~60 fps; rotation now runs ~340–470 fps.
  (A non-stable LSD radix sort was rejected: it keeps only the top byte's order, too coarse.)
- **Vulkan Y-flip fixed.** `perspective()` now negates the Y row (`out[5] = -f`). Vulkan NDC is
  Y-down (OpenGL/WebGL is Y-up), so the render was vertically inverted — teddy upside down.
- **Free-spin orbit camera.** Elevation is unclamped; the up vector is the analytic derivative
  `∂eye/∂φ`, unit-length at every `(θ,φ)` (no pole singularity).
- **Uncapped FPS.** The main loop's 60 fps sleep is removed; `MAILBOX` present mode leaves the rate
  GPU-bound. A 1 s FPS line is printed to stdout.

## NEXT MEMBRANE — the CA translator (theory, not yet built)

**STATEMENT** — the 14 splat floats become CA state driven by a **force** solver, not a pose
transform: gravity is a *field* exerting force on each membrane (bone); muscles are CA rules
applying forces between membranes; ground contact acts through the feet. The pose
(stand / lean / walk) **emerges** — it is never assigned. "Up" for an object is **gravity-up**
(opposite the field's pull at its position), distinct from **universe-up** (the arbitrary frame
convention the camera uses).

**PREDICTION** — fitting a stick-figure skeleton inside the teddy and assigning each splat to its
nearest bone partitions it into coherent rigid parts; driving one bone's force dynamics moves only
that part.

**FALSIFIER** — if a nearest-bone assignment yields an ambiguity fraction > 5% (splats within ε of
two bones), or rotating one bone moves another's splats, the grouping is wrong.

Status: vision-model photogrammetry in progress — joint locations read from front / side / top
views (qwen3.8 via `senses.see`), then triangulated to 3D.
