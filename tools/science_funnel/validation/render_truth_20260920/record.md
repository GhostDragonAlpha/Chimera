# Rule 0 record — THE RENDER TRUTH, lane render-truth-20260920

Lane: `lane/render-truth-20260920`, branched from `ae1b4599` (the landed
stranger tip; verified `git log -1` == "STRANGER PASS COMPLETE" before the
worktree add). Worktree: `E:/ChimeraWork/rendertruth-agent`. Git trailer on
this lane's commits: `Agent: rendertruth`. Only this lane branch is pushed.

## THE INHERITANCE (the finding this lane fixes)

The realbody-movie lane (20260920, `E:/ChimeraWork/rbmovie-agent`, separate
clone) banked the real body's movie and preregistered F3: the blind ollama
judge (qwen3.8, think:false, 12 ordered 384 px frames, VERBATIM, no re-roll)
read the frames as — recorded verbatim in that lane's `judgement.json`:

> Verdict: It reads as SEPARATE FLOATING PARTS. … Lack of Structure: The
> "body" is an amorphous, chaotic tangle of lines rather than a distinct
> shape with a head, torso, and limbs.

The judge's own words name the mechanism ("tangle of lines", "does not
resolve into head/torso/limbs at judge scale") and the finding names the
page: the body does not read as SURFACES at judge scale. This lane's job is
to make the real CT body read as one connected animal — without moving the
engine, the GLB payload, the scene pin, or the physics, and without breaking
the stranger layer (the on-page guide, the 13 named keys, the error beacon,
the restart pill) that landed on this very tip.

## THE THEORY (Rule 0)

**STATEMENT** (someone could disagree): rendering the UNCHANGED GLB payload
as SHADED TRIANGLES in the page's own WebGL2 draw path — one connected
surface, fixed-light lambert, backface culling on, the body framed by the
page's own client camera — makes the real body read as ONE CONNECTED ANIMAL
with identifiable head/torso/limbs to the blind judge at 384 px, without
moving any physics byte and without breaking the stranger layer.

**PREDICTION** (not yet measured by anyone):

- P-JUDGE: the judge names at least 2 body parts (head/torso/limbs class)
  and DROPS the floating-parts / separate-line class entirely.
- P-BOOT: boot stays in the cached seconds class — t_first_verts < 10 s
  (predicted ~2 s + page-side GLB index upload, a ONE-TIME 6 MB bufferData
  at page load, never a per-frame serialization of the 500k-tri index).
- P-FPS: the capture sustains 15–25 fps (the established toDataURL
  same-task loop, 640x360; the render fix adds one cull toggle and no
  per-frame upload).

## THE ROUTE (derived from the page's existing draw path, Rule 1)

The page (`tools/playable_slice/index.html` at this tip) ALREADY has the
triangle path: `MESH_P` is a fixed-light lambert (`d = max(dot(n,L),0)`),
`meshFromTopo` uploads an index buffer, `draw()` calls
`drawElements(gl.TRIANGLES, ...)`. The engine's `/verts` stream carries 9
floats per vertex — pos3 + nrm3 + col3 — with the engine's own normal
repair (engine.cpp: broken normals re-derived as area-weighted face sums).
Measured against the finding, three named defects remain in the draw path:

1. **No backface culling**: `draw()` enables depth test only. Every thin
   bone draws front AND back faces plus interior geometry through itself;
   at 384 px the surface collapses into the "chaotic tangle of lines" the
   judge named. Fix: `gl.CULL_FACE` around the body draw only (the ghost
   overlay stays double-sided translucent, as declared).
2. **The index buffer rides a late engine round trip** (`/api/topology`
   only after the first verts answer). The committed
   `standing_body.glb` (sha `adb6aff2…dbae5`) is ALREADY position+index —
   the mission's preferred route: the page parses the GLB's BIN chunk
   client-side at load and uploads the index buffer ONCE. The live vertex
   stream keeps coming from `/api/verts` (the physics truth, untouched);
   the mesh-parse lane proved the GLB indices bit-identical to the
   engine's own topology payload, so the GLB index buffer indexes the live
   positions exactly. `/api/topology` stays as the named fallback if the
   GLB fetch fails. Server change: one additive GET route serving the
   committed file's bytes. Nothing else in the server moves.
3. **Judge-scale framing**: the page's default camera (`dist 2.2`) puts
   the 0.605 m body at ~18% of frame height — measured in the finding's
   own frames (a green tangle ~40 px tall). The camera is the page's OWN
   client view (the player's zoom keys reach 0.5); the capture sets it as
   a recorded RUNTIME VIEW STATE, exactly the movie lane's recorded
   precedent (it set `cam.dist=1.6` capture-side; this lane goes closer
   because the falsifier names judge-scale readability). The ghost overlay
   is hidden the same way (the movie lane's recorded view state). No page
   file edit carries either choice; both are recorded in the receipt.

NOT chosen: a display-LOD decimation. The WebGL path rides the proven
capture route (the canvas's own `toDataURL` in the same JS task as the
page's own `draw()`; bundled chromium + `--enable-gpu
--enable-unsafe-swiftshader` keeps the GL context — the movie lane's
AMENDMENT 2 measurements), so the LOD fallback's premise ("IF WebGL cannot
ride the page's capture path") does not fire. The physics payload, the GLB
bytes, and the scene pin do not move.

## FALSIFIERS (named before the run; any one failing = the theory loses;
the RED is recorded verbatim and reported, never tuned away)

| id | class | pass condition |
|----|-------|----------------|
| F-CONNECTED | the visual truth (the judge bar, pre-registered, exact) | the movie machinery re-run through the REAL page (capture), same choreography classes — settle / carry / fall — and the SAME blind judge shown the frames (ollama qwen3.8, think:false, 12 ordered 384 px frames, ONE senses.watch call, blind prompt naming neither origin nor expected verdict). PASS iff the verbatim verdict names a single connected creature AND identifiable body parts (head/torso/limbs class) AND never uses the floating-parts / separate-line class. VERBATIM recording, no re-roll, no prompt-tuning to flatter. |
| F-PAYLOAD-INVARIANT | the frozen physics | `standing_body.glb` sha256 == `adb6aff2…dbae5`, `standing_body.obj` sha256 == `bc9033bf…9111`, `ghost_standing.obj` sha256 == `d07d976c…771d`, the boot's scene sha256 == the payload pin, and `git diff` of `ChimeraEngine/` + the slice's physics behavior surface EMPTY vs `ae1b4599`. Any LOD temptation is named here: none is built. |
| F-STRANGER-REGRESSION | the layer beneath | the stranger walkthrough (the committed instrument, re-targeted to this worktree) re-runs GREEN after the render change: 13/13 named keys by key path, beacon 0, harness console 0, restart clean (pill, boot counter 1->2, scene pin stable, re-settles), first action < 60 s. 1x minimum. |
| F-BUDGETS | the measured costs | boot `t_first_verts` < 10 s (the slice's own launch clause; the render path must NOT serialize a 500k-tri upload per frame — the index upload happens once at page load); capture fps >= 15 sustained (the movie floor); ZERO console-class errors / page errors / failed requests during the capture. |

All four can fire honestly. A RED F-CONNECTED after the fix is recorded as
the finding it is — the route may be wrong even when everything else is
green — and is never re-rolled with a re-worded prompt.

## DERIVED, NOT TUNED (Rule 1)

- The judge bar is the finding's own words, verbatim: a single connected
  creature, identifiable parts, no floating-parts class. The prompt is the
  realbody-movie lane's prompt UNCHANGED (blind: names no origin, no
  "CT", no "macaque", no expected verdict); tuning it would flatter, not
  measure.
- The choreography is the slice's OWN endpoints (`/api/send` carry mock,
  `/api/drop_test` fall, the boot's own settle), at the slice's own
  constants (1.2 m at 0.4 m/s; the fall's own law). The restart segment is
  excluded exactly as the movie lane's AMENDMENT 1 recorded (restarts
  drive the slice's own designed 502-during-boot class); the mission's
  choreography classes are settle/carry/fall.
- Camera framing numbers come from the body's own measured extent
  (0.605 m nose-to-tail, height ~0.27 m — the slice's own manifest) and
  the page's own projection math; no number is picked for taste. The
  zoom keys' floor (0.5) bounds the framing from below.
- The movie's fps is the MEASURED capture cadence (ffconcat true-time
  cut); no fps is chosen for smoothness.
- Frame budget ~30 s total is the slice's own sequence lengths, not a
  runtime picked for a target.

## RUN PLAN

Prereg (this file + receipt.json, committed BEFORE any render code) ->
data probe of the live vertex stream (normals/colors measured, not
assumed) -> the render fix in the page's existing draw path (GLB index
buffer + culling; additive server route) -> probe frames (a private
headless bundled-chromium screenshot sweep at candidate framings) ->
capture + blind judge (F-CONNECTED) -> regressions: stranger walkthrough
1x, boot bar, fps, zero errors -> encode `real_body_slice_v2.mp4` at the
measured cadence -> copies (repo `CHIMERA_PROOF/REAL_BODY_SLICE/`, this
lane dir at a sane size, `C:/Users/allen/Desktop/CHIMERA_PROOF/REAL_BODY_SLICE/`)
-> receipt.json per-falsifier with the judge's verdict VERBATIM -> tests
if the pattern carries -> commits ("Agent: rendertruth") -> push ONLY
lane/render-truth-20260920.

Receipt: `tools/science_funnel/validation/render_truth_20260920/receipt.json`.

Agent: rendertruth
