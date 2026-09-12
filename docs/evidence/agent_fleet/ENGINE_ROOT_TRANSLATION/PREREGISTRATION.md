# PREREGISTRATION — engine-root-translation-01

Written BEFORE any build, run, or capture, on base `ecec79af2b76f2ad482ab11f44f0894d720bc220`
(task branch `astra/tasks/engine-root-translation-01`, claim generation 1, owner
`subagent-worker-13`). No measured actuals appear in this commit. This is the
FIRST authored commit of the lane; the implementation lands after it.

Session succession (disclosed): read-only prep (packet analysis, engine source
derivation, this design) was done by the revoked `subagent-worker-02` host;
execution, measurement and publication happen under `subagent-worker-13`.
Trailers on every commit: `Agent: subagent-worker-13`.

## Rule 0

**STATEMENT.** The creature cannot travel because one number (a root world
offset) is absent from the engine contract; adding it is a pure coordinate
transform of the rig's data — not new physics — and composes with the gait
plane because it never touches a theta.

**PREDICTION (unmeasured at this commit).**
- P-TAKE (packet primary): with the route live, a scripted take shows the
  creature translating across the grid WHILE stepping (march playing), by
  composition — the march's oscillator keeps advancing and the knees keep
  oscillating while the root offset moves the whole body.
- P-EXACT: every parity control below passes at its frozen tolerance; the
  base-binary vs new-binary regression battery is byte-identical when the
  route is never posted.

**FALSIFIER (named before the run).**
- F-REG: any behavior change beyond root translation — measured as ANY byte
  difference in the regression battery (R2) between the base binary and the
  new binary with the route never posted, or any route-table change other
  than exactly one added entry (R1), or any failure of the untouched suites
  (R3, R4).
- F-PAR: the pose-parity control fails — thetas change under a root post
  (P1), pixels change outside the creature+shadow region (P2), or translating
  back to (0,0,0) does not restore the exact original frame (P4).
- F-COMP: the route fails to compose with the gait — with the march playing,
  a root post preempts or stalls the march (steps_total stops advancing), or
  the creature does not move (P3).
A fired falsifier stops the lane; the failure is recorded verbatim, never
tolerated away.

## The derivation (Rule 1) — the transform and its exact injection sites

**The law to implement.** p' = p + t, t = (tx, ty, tz) world units. Absolute
set semantics: `POST /root {x,y,z}` sets the rig's root world offset (per-axis
partial merge, missing axes keep their current target — the `/light` POST
pattern); `GET /root` reads it back. The offset is a STATE of the creature,
reapplied after every rig (re)load, not a one-shot impulse.

**Why data-layer injection is EXACT (the induction).** The joints FK law
(joints.comp, and its CPU mirror compute_strain_joints) composes per chain
level: `o_k = R_k(o_{k-1} - J_k) + J_k` — pure rotations about FIXED rest
pivots. Claim: shifting the rest positions AND every pivot by the same d
yields output shifted by exactly d for any pose:
`R_k((o_{k-1}+d) - (J_k+d)) + (J_k+d) = R_k(o_{k-1}-J_k) + J_k + d = o_k + d`.
Induction from `o_0 = rest + d`. The hinge band law is the single-level form
of the same identity. Therefore NO theta changes and NO pose-dependent
artifact can appear: the rendered creature is `fk(thetas) + t` exactly.

**Why the obvious alternatives are REJECTED (derived, not tasted).**
- Offsetting only the root joint's pivot: `o_2 = R_2(rest + d - J_2) + J_2 =
  fk_2 + R_2 d` — the child's rotation rotates the delta. Pose-dependent:
  F-PAR would fire. REJECTED.
- Offsetting the camera/view matrix: translates the WORLD (floor grid,
  cyclorama, water) with the creature — travel relative to the world becomes
  invisible; the product meaning ("walks and travels") is lost. REJECTED.
- Offsetting the skinned-splat lane's rest buffer (skin.comp):
  `p_new = Σ w_i (qrot(q_i, rest) + t_i)` — bone quaternions act on RAW rest,
  so a rest shift yields `Σ w_i R_i d`, pose-dependent. REJECTED for that
  lane (see scope boundary below).

**Injection sites (all inside the declared scope; zero shader edits).**
Every CPU consumer of pivots reads them LIVE per frame from `j_state_map_`
or `hinge_JL_/JR_`, so shifting these two sources moves the overlays, the
picking, the editor doc and the kernels together:
1. `hinge_rest_` (CPU rest, stride-9 records: pos3 nrm3 col3) — shift pos
   components of every vertex; re-uploaded to `hinge_rest_buf_` is NOT
   needed for correctness of the re-pose only if the kernels re-read it —
   they do NOT re-read the CPU vector; the SSBO must be refreshed (apply
   re-uploads via the existing `mesh_upload` staging path, which also
   refreshes the drawn baseline `tri_vbuf_`).
2. `hinge_JL_[3] / hinge_JR_[3]` — consumed per-dispatch as PUSH CONSTANTS
   (verified: the HingePC build site), so a CPU shift flows to the kernel
   next frame.
3. `j_state_map_` pivots `st[k*8 + 0..2]` (host-coherent mapped SSBO, the
   same lane `stride_tick` writes thetas into) — shifted in place on the
   render thread, before the dispatch recording; the exact write discipline
   of the existing edit-intent apply (C1).
4. Drawn baseline `tri_vbuf_`: when NO pose lane is live, tri_vbuf_ holds
   the authored rest; the apply refreshes it via `mesh_upload(hinge_rest_)
   ` (the proven in-frame staging-copy pattern of `pose_hinge`). When a
   pose lane IS live, its dispatch overwrites from the shifted inputs in
   the same frame — correct precedence by command-buffer order.
5. Load paths (`load_mesh`, `set_hinge`, `load_joints`) restore authored
   data, so each calls `root_invalidate()` (applied := 0); the next frame's
   apply re-shifts by the full target. The offset survives reloads as a
   STATE without double-shifting.
6. Threading: HTTP thread writes `root_tx_/ty_/tz_` + a pending flag
   (atomics — the `request_joint_edit` discipline); the render thread
   applies at the top of `frame()` before `stride_tick()`/dispatch
   recording. `GET /root` reads atomics only.

**Consumers verified to auto-follow (no edits):** contact shadow (reads
tri_vbuf_ xz/y), splat render of the mesh body (same buffer), joint tags /
rig overlay / gizmo / volp picking / `/joints` GET (live `j_state_map_`
reads), strain tint (areas are translation-invariant — byte-identical by
the induction), water kernels (read tri_vbuf_ after posing), `/project`
(raw world→screen semantics UNCHANGED — callers project pivots they read
from `/joints`, which now carry the offset).

**Scope boundary (recorded, not hidden).** The skinned-splat body
(`/skin_bin` + `/pose_apply`) and the membrane demo are NOT translated by
this exception: skin.comp's law has no pure-translation data site (shown
above), and the packet's composition test is defined against the gait plane
— the rig (tri-mesh) body the walk product drives. If the operator wants
the splat body to travel, that is a separate named appliance. The camera
fit (`g_mesh_*`, authored at load) is likewise untouched: the viewer owns
the follow camera. These boundaries are part of the route's CONTRACT.

## The parity controls and regression suite (frozen before the run)

Instruments: `/frame` (the pixel-clean offscreen capture), `/joints`,
`/gait_state`, `/project`, `/root`, sha256 over artifacts. Engine launched
from the PRIVATE build (.tmp), visible, slot-owned, port 8105-candidate.
Two binaries: BASE = build of ecec79af, NEW = build of the lane head.

- R1 ROUTE TABLE: unique route paths in main.cpp — measured at base: 59.
  At head: exactly 60, the one added entry being `/root`. Any other diff
  fires F-REG.
- R2 BINARY PARITY (the no-route-change control): base binary and new
  binary driven by the SAME script (boot, mesh+JNT3 rig load, a paused
  edit-pose state, fixed camera), route never posted: `/frame` captures
  and the GET dumps (`/state`, `/joints`, `/gait_state`) byte-identical
  (sha256 equal). ANY difference fires F-REG.
- R3 PYTHON CONTRACT SUITE: `python -m unittest tools.test_engine_demo -v`
  passes unchanged.
- R4 PHYSICS SUITE: `python tools/port_tests.py` passes unchanged (the
  engine change cannot touch the ports; running it is the full-suite
  discipline).
- P1 THETA PARITY: with the march PAUSED, `/joints` thetas read, `POST
  /root {d}`, thetas re-read: byte-identical theta fields. (Paused clock =
  deterministic; no tolerance needed — exact.)
- P2 PIXEL PARITY: at rest, `/frame` A (root 0) vs B (root d): the changed
  pixel mask lies inside (old body+shadow bbox) ∪ (new body+shadow bbox)
  inflated by 2 px; the mask centroid shift matches the `/project`-predicted
  screen delta of the rig's center pivot within 3 px. Floor/grid background
  pixels away from both boxes: byte-identical.
- P3 COMPOSITION (the walk-realism composition test): march playing, `POST
  /root {dx,0,0}`: steps_total strictly increasing across readbacks (the
  march is NOT preempted — the pose-ownership law is untouched); the
  creature's body region shifts by the predicted projected delta (centroid,
  3 px); knee oscillation continues (temporal variance in the body region
  across 10 consecutive frames is non-zero).
- P4 ROUND TRIP: `POST /root {0,0,0}` after P2 restores `/frame` BYTE
  -identical to capture A (camera fixed, rest pose).
- P5 READBACK: `POST /root {0.5, 0.25, -0.125}` → GET returns exactly those
  values; partial POST merges per-axis (`{"y": 2.0}` leaves x, z).

**The take (P-TAKE):** march playing, root x advanced in steps across
~2.5 wu; 300-frame `/glass` capture at 10 fps encoded to MP4; full-res
copies to `Desktop/CHIMERA_PROOF/ENGINE_root_translation/`; one dyad image
review per THE_DYAD_PROTOCOL (one image, context, zero priming). Predicted
judge reading: the creature moves across the grid while stepping.

## Scope and resources

Scopes (claim gen 1): `ChimeraEngine/engine/engine.cpp`,
`ChimeraEngine/engine/engine.hpp`, `ChimeraEngine/engine/main.cpp`,
`docs/evidence/agent_fleet/ENGINE_ROOT_TRANSLATION`. No shader source is
touched; `ChimeraEngine/engine/build/` is NEVER written. Private build under
`.tmp/engine_build/`, unique runtime CWD `.tmp/engine_runtime/<run-id>/`,
evidence `.tmp/engine_evidence/<run-id>/`. Candidate port 8105 (first free
wins; recorded). Resources rtx4090 + engine_demo requested BEFORE any
hardware work; released after drain evidence. Commit trailer on every
commit: `Agent: subagent-worker-13`. No force-push; PR READY (not draft)
against `astra/gait-capture`.
