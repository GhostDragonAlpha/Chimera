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

9. **The splat view is declared, not silent.** The 3DGS splat pipeline runs with
   depth/stencil OFF in the same scene pass, so the clause does not bind there.
   Declared in full below (`DECLARED: THE SPLAT VIEW`, 2026-09-11 — PR #65 review
   followup F1).

## DECLARED: THE SPLAT VIEW (2026-09-11)

**The behavior.** In any view whose body is presented by the 3DGS splat pipeline
(`Engine::create_pipeline`), the occlusion clause (contract item 2) does NOT hold:
splat fragments run no depth test and write no stencil, so every pixel they cover
keeps the attachment's stencil at 0 and the grid twin draws there — grid lines
remain visible through/behind the splat body. That is the pre-fix draw-through
degradation, bounded to the splat presentation.

**The engine condition at base `d59518b9d9dc002cba43d071495576a236b9d498`** —
`ChimeraEngine/engine/engine.cpp`, quoted verbatim (line numbers from
`git show d59518b9:ChimeraEngine/engine/engine.cpp`):

```text
1330:    ds.depthTestEnable   = VK_FALSE;   // 3DGS: sorted back-to-front + alpha blend, no depth test
1331:    ds.depthWriteEnable  = VK_FALSE;
1334:    ds.stencilTestEnable = VK_FALSE;
1348:    gpci.renderPass                   = rt_render_pass_;   // frame() renders to the offscreen target
```

The splat pipeline therefore renders into the SAME stencil-carrying offscreen
scene pass the contract uses, but leaves no stencil: the contract's mark comes
only from the accepted fill draw (`create_triangle_pipeline`,
`ds.depthTestEnable = VK_TRUE` / `ds.stencilTestEnable = VK_TRUE` marking
stencil 1 on depth-passed fragments, engine.cpp 1481/1485), and the grid twin
draws only where that mark is absent (`ui.cpp` `create_scene_grid_pipeline`,
`dss.stencilTestEnable = VK_TRUE` with `dss.front.reference = 0` — stencil
EQUAL 0). No splat-covered pixel ever carries the mark.

**The exact observable condition.** A view exhibits this declared degradation if
and only if the body geometry in it is drawn by `create_pipeline` (splat
presentation): grid lines are visible across splat-covered pixels where no
accepted fill left stencil 1. Views whose body is drawn by the accepted fill
family are unaffected — the clause holds there and was measured working
(`docs/evidence/studio_grid_depth/after/records.txt`: `darkline_at_occluded_frac`
2e-4 against 0.1581 bright-line at visible). The shadow and floor twins pin
stencil OFF by design (ink ON the grid's plane — contract item 4), which is a
different, already-declared case.

**Declaration.** This is recorded as DEGRADATION, bounded to the splat view —
named, observable, and unchanged by this document (docs/evidence-only lane; no
engine file is modified here). Whether to extend the clause to splats (e.g.
stencil-marking from the splat draw itself) is a future lane's decision; this
section exists so the behavior is a stated limit of the contract, not a silent
gap.

## WHAT THIS CONTRACT FORBIDS

- Changing the B2 fixture, gate tolerances, or face count to fit a visual
  description.
- Treating the grid as scene geometry (it never enters the depth solution; it
  writes no depth, marks no stencil of its own).
- Cosmetic global hiding (dimming, dashing) as a substitute for occlusion.

## AMENDMENT 2026-09-11 (fleet-followups-batch-03 item C5, origin PR #76
MINOR-1; append-only, prior text unchanged)

The parenthetical above ("the contract's mark comes only from the accepted
fill draw (`create_triangle_pipeline`, `ds.depthTestEnable = VK_TRUE` /
`ds.stencilTestEnable = VK_TRUE`") is incomplete on one point: the accepted
fill is a FAMILY, not a single pipeline. The frost pipeline also marks the
stencil when live - engine.cpp ~4865-4879 at d59518b9: "frost REPLACES the
fill when live - the accepted body, so it must mark the stencil exactly
like create_triangle_pipeline's fill (grid contract)" (same
VkStencilOpState mark). Read the sentence as: the mark comes only from
accepted fill-family draws (create_triangle_pipeline family incl. frost
when live), never from the splat or the grid's own draws.
