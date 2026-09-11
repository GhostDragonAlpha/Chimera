# THE STUDIO GRID DEPTH — the reference grid's presentation contract

Task: `studio-grid-depth-01` (feedback `ffd13d484e32cd09dad00399`: "DYAD repeatedly
reads overlaid ground grid as additional physical tessellation despite numerical B2
six faces"). Rule-0 preregistration and the measured comparison live in
`docs/evidence/studio_grid_depth/PREREGISTRATION.md`; this file holds the contract
that survives the run.

## THE CONTRACT

1. **The grid is an instrument, never matter** — the standing law
   (`ChimeraEngine/engine/ui.hpp`, 2026-08-31). It is the viewport's frame of
   reference, the way a Blender grid is. Nothing here changes the face count, the
   B2 fixture, or any gate tolerance.

2. **THE OCCLUSION CLAUSE (this task).** The grid must not draw through occluding
   accepted geometry. Where a depth-passed fragment of an accepted body covers a
   pixel, the grid yields that pixel. Where no accepted geometry covers it, the
   grid draws exactly as before.

3. **Why the implementation is exact, not approximate.** Every grid fragment lies
   on the floor plane (y = 0 — the same `floor_y` the UBO publishes), and the
   floor quad is opaque and depth-writing. Therefore a grid fragment's true depth
   at a pixel EQUALS the floor's depth at that pixel, and an accepted-body
   fragment that PASSED the depth test against the floor at that pixel is
   strictly nearer than the grid. Hiding the grid exactly where such fragments
   exist IS depth occlusion — computed by the GPU's own depth test. No CPU
   second renderer, no depth-bias tuning, no readbacks.

4. **Mechanism (all inside existing scopes).** The accepted fill draw
   (`tri_pipeline_` family — mesh, membrane demo, water, overlay, frost) writes
   stencil 1 on depth-passed fragments. The grid draw moves INTO the scene render
   pass (`rt_render_pass_`, the pass that owns the depth attachment), stencil-
   tested `EQUAL 0`, using the UI's own vertex format and shaders (`ui.vert` /
   `ui.frag` via the solid-white atlas cell = RGBA passthrough) and the UI's own
   quad-built line segments — same clip, same thickness, same projection law
   (`project_world`, one camera). No new shader files, no CMake changes.

5. **The idle/empty viewport keeps the UI-pass grid.** With nothing loaded
   (`n_ == 0 && !has_mesh_ && !md_active_`) nothing occludes, and the eye's #1
   defect law stands: an empty viewport shows the reference frame, never a void.

6. **The ink law is untouched.** Grid color/alpha stay the measured 2026-09-02
   perception-floor values; the axes-of-the-plane distinction and the triad are
   unchanged. This task changes WHERE the grid draws, never WHAT it draws.

7. **Depth attachment format.** The offscreen depth attachment becomes
   `VK_FORMAT_D32_SFLOAT_S8_UINT` (was `VK_FORMAT_D32_SFLOAT`) so the same
   attachment carries the stencil the clause needs. The RTX 4090 class this
   fleet renders on supports it for depth/stencil attachment at 1x and 4x; the
   MSAA fallback path (1x) is structurally identical.

8. **Degradation, declared.** If the scene-grid pipeline cannot build (stale
   shader modules, lost device), the grid falls back to today's UI-overlay path
   (draws through, as before) — the engine's standing instrument policy: an
   instrument upgrade never becomes a load-bearing wall. The fallback is
   observable (`StudioUI::scene_grid_ok()`), never silent-by-design.

## WHAT THIS CONTRACT FORBIDS

- Changing the B2 fixture, gate tolerances, or face count to fit a visual
  description.
- Treating the grid as scene geometry (it never enters the depth solution; it
  writes no depth, marks no stencil of its own).
- Cosmetic global hiding (dimming, dashing) as a substitute for occlusion.
