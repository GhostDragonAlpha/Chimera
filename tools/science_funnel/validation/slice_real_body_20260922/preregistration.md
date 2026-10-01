# Rule 0 preregistration — THE SLICE'S REAL BODY (slice_real_body_20260922)

Lane: `agent/slice-real-body-20260922` @ `2909bb4e` (the playable slice).
Worktree: `E:/ChimeraWork/realbody-agent` (sparse clone, canonical
`git@github.com-fleetdeploy:GhostDragonAlpha/Chimera.git`). Engine port law:
8127 refused by code; master untouched; only this branch is pushed.

## THE THEORY (statement / prediction / falsifier)

**STATEMENT** (someone could disagree): the committed CT skeleton — repaired to
the aliveness importer's own closure rule and decimated under its own 500,000
triangle cap by a uniform, cap-derived ratio — can replace the playable slice's
bbox stand-in tick body, so the slice's physics rides the real anatomy.

**PREDICTION** (not yet measured): after repair + decimation, the merged
25-bone body (a) passes the importer's closure rule with ZERO refusals, (b)
boots through `/mesh_import` with the engine's own law intact (the fall
identity vt = m·g/c = 0.223719 m/s holds to 1e-6 relative as it did on the
capsule, because the constants are banked, geometry-independent), and (c) the
page renders the real skeleton through the triangle stream at launch inside the
slice's 10 s first-frame bar (the committed posed payload removes the compose
from the boot path to pay for the engine's parse of ~500k tris).

**FALSIFIER** (named before the run): any of F-BODY-CLOSURE / F-BODY-CAP /
F-SLICE-MOCK-TRUTH / F-SLICE-VISUAL / F-SLICE-RESTART / F-SLICE-FALL /
F-SLICE-LAUNCH below failing = the theory loses, recorded RED, not tuned.

## THE MEASURED DEBT (this prereg's orientation, measured 2026-09-22 on
`2909bb4e`'s committed `meshes_preview/`)

The importer's own closure rule (importer.cpp `finish()`, mirrored in
`check_body_closure.py`) refused **19/25** committed previews:
`index_degenerate_faces` **312**, `nonmanifold_edges` **174**,
`winding_violations` **348**, `boundary_edges` **0** (the hole class is EMPTY —
measured; no hole-fill op is applied where the check names none), total
**712,522** triangles vs `kMaxTris` **500,000**. All 348 winding violations sit
ON the 174 non-manifold edges (measured per bone): duplicate faces (53 sorted
triple duplicates in bone_01 alone) and pinched fin faces left by the CT
intake's decimation. So the repair spec, one op per class the check names:
(1) drop index-degenerate faces; (2) drop exact duplicate faces (keep first);
(3) non-manifold edges: keep exactly one face per traversal direction (greedy,
fewest other over-shared edges, face-index tie-break — the minimum that
restores one-face-per-direction), remove the rest; (4) orientation propagation
per connected component, then per-component positive signed volume (the
importer's own divergence sign law); (5) boundary loops created by (3) — if any
— traced and ear-clip filled in the best-fit plane.

## DERIVED, NOT TUNED (Rule 1)

- The decimation ratio is forced by the cap, not chosen: `r = kMaxTris /
  N_repaired` (N_repaired = total faces after repair, measured). Per-bone
  target = `floor(r · n_i)`; `Σ floor(r·n_i) ≤ Σ r·n_i = kMaxTris` — under the
  cap by construction, and the engine refuses only `> kMaxTris`. No margin
  constant exists in this lane.
- Decimation is quadric error metric (Garland–Heckbert) edge collapse with the
  topology-safety set: link condition (manifoldness preserved by
  construction), normal-flip guard, boundary-plane constraints included though
  the boundary class measured empty. Quality is MEASURED and recorded (per-bone
  signed-volume delta pre/post repair and pre/post decimation; sampled
  vertex-to-surface deviation), never thresholded by this lane: the acceptance
  falsifiers are the check's own classes.
- Bone count 25 is anatomy, not a parameter: every committed preview maps 1:1
  to one output body mesh. A bone merged away = F-BODY-CLOSURE RED.
- The launch bar is the slice's own bar (first `/api/verts` < 10 s, zero
  console errors), unchanged; the pose compose leaves the boot path by
  committing the posed payload (bytes produced by the SAME
  `scene_boot.build_standing_layer` compose the ghost runs live, from the
  committed repaired/decimated bones through the pinned pose.json +
  registration pin), so the import payload is committed bytes, sha-pinned.

## FALSIFIERS

| id | class | pass condition |
|----|-------|----------------|
| F-BODY-CLOSURE | the closure check that refused 19/25 must ACCEPT every output mesh | per repaired bone, per decimated bone, per merged payload: boundary_edges=0 ∧ nonmanifold_edges=0 ∧ winding_violations=0 ∧ index_degenerate_faces=0; bone count 25 (1:1 with the committed previews) |
| F-BODY-CAP | the importer's own cap | merged body ≤ 500,000 tris AND `/mesh_import` answers `ok` with the engine's own stats |
| F-SLICE-MOCK-TRUTH | the slice's mock registry honesty (re-run) | grep both directions PASS with fantasy ids == {mock_carry} exactly (mock_physics_body retired, one fewer mock, grep-auditable: 0 code sites repo-wide); declared == {ghost_standing_pose}, whose declaration now resolves to the real rendered skeleton |
| F-SLICE-VISUAL | the eyes-on class | committed before/after PNGs captured through the real page at launch: before = bbox stand-in capsule + ghost; after = the real skeleton riding the tick (both via /verts+/topology triangles; F-SLICE-NO-SPLAT re-run green) |
| F-SLICE-RESTART | byte-clean boot (re-run; the boot changed) | 3 boots: identical scene sha (== the committed payload's sha) and identical settled start-state sha |
| F-SLICE-FALL | the fall law rides the real body (re-run; the body changed) | the engine's own root law: terminal descent median |vy| == m·g/c = 0.223719 m/s to ≤1e-6 relative (banked constants; geometry-independent identity) |
| F-SLICE-LAUNCH | the slice's own launch bar (re-run) | t_first_verts < 10 s, zero console errors |

## GATES (must stay green — the slice's own receipts name them)

creature_graph both roots (19 + 27), matter_kernel test_definition 9/9,
training_gate PASS.

Receipt: this directory (`tools/science_funnel/validation/slice_real_body_20260922/`).
Artifacts: `tools/science_funnel/data/morphosource_ct/meshes_body_20260922/`
(repaired + decimated bones + manifest) and
`tools/playable_slice/standing_body.obj` (the committed import payload).

Agent: GLM 5.3
