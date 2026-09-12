# RESULT — studio-grid-depth-01

Agent: subagent-worker-02 · branch `astra/tasks/studio-grid-depth-01` · base 8d72c4f3 (merged tip 5199d9c3)
Resources: `rtx4090` + `engine_demo` granted via controller (rev 662), released with drain before submit_review.

## VERDICT: FIXED — measured, gate-green, regressions held

Feedback `ffd13d48` (the DYAD reads the ground grid as additional physical
tessellation of the 6-face B2 membrane) was a real presentation defect: the
grid was drawn by the UI overlay pass with NO depth relation to the scene, so
its lines crossed the lifted membrane's pixels. The fix draws the grid INSIDE
the scene render pass, stencil-tested against the accepted fills' depth-passed
coverage — exact occlusion by the GPU's own depth test
(`docs/THE_STUDIO_GRID_DEPTH.md` for the contract and the floor-plane
equivalence proof). No geometry, tolerance, face-count, or ink changes.

## The measurement (preregistered; see PREREGISTRATION.md)

Fixed demo camera (r=3.0, θ=0, φ=0.35 via `POST /camera`); membrane at reset
(iteration 0 — the rendered surface IS the frozen B2 fixture under the
documented present-stage mapping `vec3(x, z+0.5, -y)`); grid samples projected
through the engine's own `/project`; occlusion partitioned by the monotone-ray
equivalence (lift 0.5 > 0 over the opaque floor); pixels classified by local
line structure (9×9 contrast vs the 80th-percentile background; 14px
boundary-exclusion zone). **Probe channel: `/glass`** — the composited window
the operator and the DYAD see (see "the channel lesson", below).

| view | DARK_LINE at occluded samples | occluded total | fraction |
|---|---|---|---|
| BEFORE (`before_glass/`, pre-fix binary) | 2818 | 4160 | **67.74%** |
| AFTER (`after/`, fixed binary) | 1 | 4160 | **0.02%** |

- BEFORE: the UI overlay grid crosses two-thirds of the occluded samples —
  the dense false-topology the DYAD read.
- AFTER: one sample; the sheet shows only its own fan wire; the floor grid
  remains outside the silhouette (BRIGHT_LINE at visible samples 21.5% →
  15.8%, present both sides — the lines' AA differs: UI swapchain quads vs
  the MSAA canvas).
- Frozen B2 gate (`tools/membrane_demo_client.gate`): rc=0, **20 PASS 1
  INFO** in both phases (`before_glass/b2_gate_records.txt`,
  `after/b2_gate_records.txt`). `faces 6`; accepted_state_id stable across
  captures.
- Regressions: V3 ordinary mesh (`/mesh_bin` box) — the grid yields to the
  box, draws on the floor; V4 idle viewport — grid + triad + honesty hint
  unchanged; V2 gamma-0 raised — the parent's retained view, probe identical
  to V1.

## Mechanism proof (inversion diagnostic)

With the grid twin's stencil reference temporarily set to 1 (draw ONLY where
the fills marked), the grid appeared EXACTLY on the sheet's coverage and
NOWHERE on the floor — the fills mark, the twin tests, the floor doesn't mark.
Reverted to reference 0 before the retained runs. Screens described in
MEASUREMENT.json; the diagnostic build never left this worktree.

## The channel lesson (retained, not hidden)

The first three probe generations measured `/frame` — the pixel-clean offscreen
render — and showed no defect on EITHER side: pre-fix, `/frame` never contained
the grid at all (the grid was a UI-pass overlay composited after the blit). The
defect exists only in `/glass`. The superseded runs are retained with hash
manifests (`*_retired/`, `before/MANIFEST_sha256.txt`; full PNGs remain in this
branch's git history). The v1 absolute-color detector additionally misread the
sheet's shaded fill as ink — superseded by the structure detector. Both
instrument corrections happened BEFORE the retained comparison; the final
before/after pair used one binary pair and one detector.

## DYAD review: NOT_TESTED (handoff prepared)

This lane cannot spawn subagents (the template's spawn is the lead's Agent
call) and the operator's LM Studio eye is off-limits to fleet lanes.
`dyad_review_handoff/` holds hash-verified specs + the exact prompts for both
captures (`plan_before/`, `plan_after/`) — one image per review, non-leading
questions, ready for the lead to spawn and `assemble` at integration.

## Resource record

- Granted: rtx4090 + engine_demo (controller rev 662, served immediately).
- Engine builds: `.tmp/engine_build/studio01` (private); runtimes
  `.tmp/engine_runtime/grid_*`; port 8127 (free-checked before each launch).
  `ChimeraEngine/engine/build/` and the operator's engine were never touched;
  LM Studio untouched; no operator processes signalled (an unrelated operator
  engine PID was observed and explicitly left alone).
- Drains: both owned instances stopped via `_stop_owned`; exit recorded in
  `records.json` (`*.instance.drain`); one orphaned instance from a crashed
  first probe attempt was killed BY PID+PORT+start-time verification before
  any rerun.
- Released back to the controller with this document in place.

## Suites

CPU suite + full fleet suite from the repo root: `suite_cpu.txt`,
`suite_fleet.txt` (verbatim, `*.txt` — the `*.log` gitignore trap).
