# PREREGISTRATION — studio-grid-depth-01

Written BEFORE any measured actual. Commit order enforced: this file lands in its
own commit ahead of the fix and ahead of every capture.

## Rule 0 parts

**STATEMENT.** The Studio reference grid is a screen-space instrument drawn by the
UI overlay pass with no depth relation to the scene; on the fixed demo view it
draws through the lifted B2 membrane, and the DYAD reads those through-drawn grid
lines as additional physical tessellation of the membrane. The presentation, not
the geometry, is defective: the grid should not imply extra material topology nor
draw through occluding accepted geometry.

**PREDICTION (unmeasured at this commit).** A derived camera/depth/projection
comparison — engine VP consumed through the engine's own `/project`, frozen B2
fixture geometry at iteration 0, analytic depth comparison — partitions fixed-
camera capture samples into OCCLUDED and VISIBLE grid samples. BEFORE the fix,
grid ink is present at OCCLUDED samples (the overlay path cannot depth-test by
construction). AFTER the smallest declared fix (docs/THE_STUDIO_GRID_DEPTH.md),
grid ink is absent at OCCLUDED samples and unchanged at VISIBLE samples. The
frozen B2 numerical gate (`tools/membrane_demo_client.gate`, 20 PASS 1 INFO),
`faces 6`, and the accepted state are unchanged before and after.

**FALSIFIER (named before the run).** The theory loses if any of these is measured:
1. Geometry or tolerance changed to fit the visual description (fixture edit,
   gate tolerance edit, face-count edit).
2. The reference grid treated as physical mesh (grid enters the depth solution,
   writes depth, or marks stencil of its own).
3. Depth occlusion wrong — grid ink hidden where the grid is in FRONT of accepted
   geometry, or ink present where it is BEHIND, as decided by the derived probe.
4. Only cosmetic hiding without a declared contract (global dimming/dashing, or
   capture-only changes) — a fix is legal only with the declared presentation
   contract in `docs/THE_STUDIO_GRID_DEPTH.md`.
5. The ordinary mesh/creature view or the idle empty viewport regresses (grid
   vanishes where nothing occludes it, or new artifacts appear).

## Derived comparison method (no measured actuals here)

1. **Camera law (one projection).** The fixed demo camera is SET via
   `POST /camera {cam_radius: 3.0, cam_theta: 0.0, cam_phi: 0.35}` — the parent
   task's fixed view (docs/evidence/demo_studio_state/run_native.py). All screen
   coordinates come from the ENGINE's own projection via the `/project` endpoint —
   the probe never re-implements the matrix math, so camera, depth and projection
   cannot drift between probe and pixels.
2. **Geometry law (frozen).** `POST /membrane_demo {op: "reset"}` puts the
   accepted B2 state at iteration 0, where the rendered surface IS the frozen
   fixture (`ChimeraEngine/` membrane fixtures: positions_f32.npy,
   indices_u32.npy) lifted by the demo's `md_lift_` (read from
   `GET /membrane_demo`). Six faces. Nothing is re-tessellated.
3. **Occlusion partition (derived).** For sampled points P on the y=0 grid lines
   (the grid's derived spacing law: sp = 10^floor(log10(R/5)),
   extent = sp*ceil(R/sp), computed from the same camera radius), the probe
   depth-compares P against the lifted fixture triangles through the engine's
   reported depths: a sample is OCCLUDED iff some fixture triangle covers P's
   projected pixel with a strictly smaller depth. This is a 2-triangle-pair-
   exact comparison at iteration 0 — no CPU renderer of live state, a partition
   of a frozen state only.
4. **Pixel read (measured).** At each sample's projected pixel, the capture is
   classified by the declared ink law: grid ink alpha 0.70 RGB(0.30,0.34,0.46)
   over membrane fill (the 147..167 band) predicts ink-vs-fill classes within a
   stated tolerance; ambiguous pixels are reported as their own class, never
   folded into a passing class. Counts per class are reported per view, BEFORE
   and AFTER, raw verbatim.
5. **Numerical gates.** `tools/membrane_demo_client.gate()` runs BEFORE the fix
   build and AFTER: both must report the frozen verdict set (20 PASS 1 INFO),
   `faces 6`, accepted_state_id stable across captures.

## Controlled actual-window comparison plan

- Private build in this worktree's `.tmp/engine_build` (never
  `ChimeraEngine/engine/build/`), own runtime CWD under `.tmp/engine_runtime`,
  FREE port (probe asserts liveness via `_port_busy` first), visible window,
  launched with the granted engine_demo reservation
  (`tools/engine_demo.py::_launch`). Env `CHIMERA_MD_EDGE=1` — the DYAD's view.
- Views, each captured as BOTH `/frame` (pixel-clean render) and `/glass`
  (composited window the operator sees), at the FIXED camera:
  - V1 membrane demo, reset state — the defect view.
  - V2 gamma-0 raised state — the parent's retained view.
  - V3 regression: ordinary mesh view (`/mesh_bin`), grid over floor+shadow, no
    through-draw change for unoccluded segments.
  - V4 regression: idle empty viewport — grid must persist (UI-pass path).
- Sequence: BEFORE build measured first (V1-V4 + probe + gate), retained
  verbatim even if embarrassing; THEN the fix commit; THEN the identical probe.
- Every capture writes a sidecar JSON (sha256, camera, status). Raw outputs are
  `*.txt`/`*.json`/`*.png` — never `*.log` (the .gitignore trap, twice this
  wave); anything needed in the PR is explicitly `git add`-ed.
- Resources: rtx4090 + engine_demo held via the controller for the whole
  measured window; released with drain evidence before submit_review.
