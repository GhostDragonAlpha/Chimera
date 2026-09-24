# F02 Report — matching terrain rendering and collision

Author: M-F02. Date: 2026-09-24. Checkout `E:/ChimeraWork/monkey-play-20260924`,
branch `monkey-play-20260924` (base = game lineage tip `33e7a444`; F01 integrated at
`c9aee37c`). Item F02, verbatim: "Rendered ground and physical query surfaces agree
within frozen geometric tolerance. Reuse engine geometry/collision paths." Contract C14:
"compute geometry and gradient/normal consistently with physical collision representation.
Render/query agreement and frozen slope/obstacle cases."

## What was done

1. **Discovery** (`discovery_note.md`): mapped all three live terrain paths — the native
   plane lane (`earth_environment.hpp` physics plane + `graph_earth.hpp` render built from
   the SAME slope; `engine.load_mesh` 9-float upload; the `engine.cpp:1854-1937`
   normal-hygiene gate that silently rewrites disagreeing normals), the Python walker lane
   (`heights_at` ONE-implementation law; `scene_around` rendering grains AT the query
   function), and the gait lane (flat `contact_plane_height_m` — no native heightfield
   exists). The reused agreement mechanism: **one surface, two projections**.
2. **Prereg frozen before implementation** (`PREREGISTRATION.md`): the identity design,
   frozen tolerances (1e-9 m height / 1e-12 normal / 1e-9 gradient; mesh↔analytic 0.01 m
   with derived bound 0.00925 m), the headless declaration-vs-declaration strategy, the
   frozen sample set (~21,700 points), frozen construction (diagonal rule, flat duplicated
   face normals, hexagonal posts), and falsifiers (a)-(d). One dated amendment (before any
   run): the anti-fake-ground extent check binds the GROUND surface, not post-marker
   girth, which necessarily straddles the edge by its 0.05 m radius.
3. **Implementation** (pure Python, stdlib-only):
   - `tools/monkey_campaign/data/monkey_clearing/terrain_bundle.py` — compiles
     `chimera.monkey_terrain.v1` from F01's committed declaration (pinned by file sha AND
     body pin; refuses drifted sources), builds the ground triangulation (40×40 cells,
     frozen diagonal 00–11, flat-shaded duplicated vertices, engine checker colours) and
     the 80 hexagonal post prisms (F01's ochre, exact base positions), plus
     `validate_bundle` mirroring the engine's own upload gates (mesh length/finite/index,
     `earth_render_degenerate` at 1e-16, the normal-hygiene gate, extent bounds).
   - `tools/monkey_campaign/data/monkey_clearing/terrain_bundle.json` — the compiled
     bundle: 877,752 canonical bytes, self-pinned `bundle_sha256`
     `8c7d60c88a75234a4ea94bc5ec83b666d620502b47cac8667e83b8713cb04fe0`.
   - `tools/monkey_campaign/data/monkey_clearing/terrain_query.py` — the physical query
     surface: `height_at`/`gradient_at` (containing triangle's exact plane values),
     `normal_at` (engine's `cross(b−a, c−a)` on the stored render positions),
     `classify` (strict-`>` `out_of_patch` semantics, `earth_environment.hpp:118`),
     refusal `f02_outside_extent` off the patch, `worst_triangle_slope`,
     `height_function` (analytic mounds, only for discretization measurement).
4. **Tests** (`tests/test_terrain.py`): 42 cases — determinism (in-process ×2 + subprocess
   + committed-file byte identity), intake strictness (digest, duplicate keys, non-finite,
   drifted grid/mounds, tampered post, ground past extent, degenerate triangle — each
   refused even when re-pinned), mesh shape + engine-gate mirrors, render↔query agreement
   over the frozen sample set, diagonal-drift non-vacuity proof, posts vs declaration,
   boundary semantics, frozen slope cases. **All 42 green**, standalone and via
   `python -m unittest` from the repo root.
5. **Receipts** (`receipts/`): `test_run.txt` (both invocations, exit 0),
   `determinism_receipt.txt` (4 compiles byte-identical), `validate_receipt.json`.

## Measured numbers

| Quantity | Value | Frozen bound |
|---|---|---|
| Bundle bytes | 877,752, canonical, self-pinned | byte-identical per compile |
| `bundle_sha256` | `8c7d60c88a75234a4ea94bc5ec83b666d620502b47cac8667e83b8713cb04fe0` | — |
| Byte identity (committed vs 2 in-process vs 1 subprocess) | True, 4/4 × 877,752 bytes | falsifier-free determinism |
| Mesh | 13,920 vertices / 13,920 indices / 4,640 triangles (3,200 ground + 1,440 post) | predicted exactly |
| **Render↔query height agreement** (20,177 points) | **worst 2.776e-17 m** | ≤ 1e-9 m |
| **Render↔query normal agreement** | **worst 0.0** | ≤ 1e-12 |
| **Gradient↔stored-normal consistency** | **worst 6.939e-18 m/m** | ≤ 1e-9 m/m |
| Query vs F01 grid at all 1,681 nodes | worst 8.674e-19 m | ≤ 1e-9 m |
| Normal-hygiene gate (engine mirror) | 0 broken, 0 deviant of 13,920 | 0 / 0 |
| Worst stored-normal error vs face cross | 0.0 | ≤ 1e-12 |
| Worst triangle slope (mesh plane gradients) | 0.042522 m/m at (17, 7) | ≤ 0.05 (F01's law) |
| F01 central-difference law on the bundle grid | 0.034606 m/m at (17, 6) | = F01's receipt, ≤ 0.05 |
| Mesh↔analytic (`height_at`) deviation | worst 6.460 mm at (19.5, 5.5) — mound 2's east flank | ≤ derived 9.25 mm ≤ frozen 10 mm |
| Posts | 80/80; base y exact `==` declaration; axis recovered within 3.6e-15 m; bases on grid nodes, on the mesh surface ≤ 1e-9, on the physical edge ≤ 1e-6 | falsifier (b) |
| Ground vertices outside closed extent | 0.0 (worst) | none (falsifier (c)) |
| Degenerate triangles | none; min cross length 2.165e-3 | > 1e-16 |
| Twisted cells (agreement test non-vacuity) | 388; max diagonal-split surface difference at a cell centre > 1e-6 m | — |

## Prediction vs measured (honesty row)

- Predictions that HELD: byte-identical compiles; mesh counts 13,920/4,640 exactly;
  hygiene 0/0; worst slope inside the predicted band 0.030–0.045 (measured 0.0425);
  discretization worst ≤ derived 0.00925 m (measured 6.46 mm, worst exactly on mound 2's
  east-edge flank as predicted); spawn cell exact (height 0.0, gradient (0,0), normal
  (0,1,0)).
- Predictions that MISSED (recorded, not tuned away): I predicted the render↔query height
  disagreement would be "exactly 0.0". Measured worst is **2.776e-17 m** (and 8.674e-19 m
  at the clamped max-edge grid nodes): the plane algebra `h00 + (h10−h00)` at `tx = 1.0`
  reorders one subtraction/addition and costs ~1 ulp. The frozen tolerance (1e-9 m) holds
  with 8 orders of margin, so **no falsifier fired** — but the "exactly zero" claim was
  wrong and is corrected here. Posts' base y is still exact `==` (copied bytes); only the
  query-recomputed surface height under them carries the ulp.

## Falsifier verdicts

- **(a) render↔query disagreement beyond frozen tolerance: NOT OBSERVED.** 20,177 sampled
  points (nodes, cell centres, centroids, edge midpoints, 4,096 seeded): worst height
  2.776e-17 m ≤ 1e-9; worst normal component 0.0 ≤ 1e-12; worst gradient/normal 6.9e-18
  ≤ 1e-9. Non-vacuity proven: 388 twisted cells exist and the two possible diagonals'
  surfaces differ by > 1e-6 m at a twisted cell's centre, so a diagonal drift could not
  hide.
- **(b) boundary post position mismatch vs F01's declaration: NOT OBSERVED.** 80/80 posts;
  base y exact `==` the declaration (copied, not re-derived); axes recovered from the mesh
  agree with the declaration to ≤ 3.6e-15 m (float midpoint round-trip); colour ochre and
  height 0.9 exact; every base on the physical edge (≤ 1e-6) and on the mesh surface
  (≤ 1e-9). Tampered post bases are refused even when the digest is re-pinned.
- **(c) physical bound not matching |x|>20/|z|>20 semantics: NOT OBSERVED.** `classify`
  says inside at every tested point with |x| = 20.0 or |z| = 20.0 (all four edges,
  corners included) and outside at +1e-9/+1e-6/+1.0 beyond; height/gradient/normal queries
  REFUSE (`f02_outside_extent`) off the patch; zero ground vertices outside the closed
  extent; the bundle's physical half-width (20.0) equals the rendered ring's max extent
  (invisible-wall guard) and F01's `boundary.physical`.
- **(d) frozen slope/obstacle cases failing F01's law: NOT OBSERVED.** Worst mesh triangle
  slope 0.042522 ≤ 0.05; F01's central-difference law re-derives exactly 0.034606 at
  (17, 6) from the bundle grid; the worst-slope-point case, all five mound crests
  (|mesh − A| ≤ 6.46 mm, normal_y ≥ 0.99, slope ≤ 0.05), the spawn cell (exact flat), the
  boundary-edge heights (exact grid equality on all 41 east/west edge nodes, served
  through the mound-2 straddle), and the discretization sweep (6.460 mm ≤ 9.25 mm derived)
  all pass.

## Live-engine follow-up needs (F04/W10 territory — recorded, not exercised)

1. **Mesh upload exercise**: the bundle's `render.vertices`/`render.indices` are verbatim
   `Engine::load_mesh` arrays (`engine.hpp:140`), but no engine process was launched (CPU-
   only prereg). F04/W10 should launch the engine, upload the bundle's arrays through the
   `--earth-patch`-style path (`main.cpp:753-766` pattern), and capture a frame: the
   posts' hexagons and the two-tone checker are the visual keys to verify.
2. **Normal-hygiene zero-repair proof live**: the tests mirror `engine.cpp:1854-1937`
   headlessly (0 broken / 0 deviant); the live run should confirm the engine prints NO
   `[load_mesh] normal hygiene: repaired` line for this mesh — that is the in-vivo proof
   that the engine uploads F02's normals untouched.
3. **Native heightfield contact does not exist** (`earth_environment.hpp` is a plane;
   `gait_controller.hpp` walks `contact_plane_height_m`). Terrain-aware contact for the
   walker in the native lane is an ENGINE change (frozen C++) and must be a decided,
   preregistered engine task, not an agent-file edit. Until then the clearing's physical
   surface is this Python binding; F05 (slope/friction envelope) and F06 (terrain-aware
   walking) should consume `terrain_query.TerrainSurface` and state that binding.
4. **Out-of-patch wiring**: the engine reports `out_of_patch` at the same strict-`>` rule;
   W10's walking demo should show the walker stopped at the post ring, never inside it,
   with phase `out_of_patch` — the visible/physical coincidence made testable live.
5. **F04's frozen tunnelling/ghost-support cases** should reuse this bundle: the same
   triangles that render are the ones the queries answer, so a tunnelling case has an
   unambiguous geometric reference.

## Integrity paste (git status --porcelain -uall at completion)

```
 M tools/monkey_campaign/agents/U02_camera/receipts/latency_run.json
?? tools/material_volume.py
?? tools/material_volume_admission.py
... (parallel sessions' files: material_volume*, rigid_body_mass*, U03_focus, X02_flow,
    W7_landing, product/focus_policy*, product/session_flow* — NOT M-F02's)
?? tools/monkey_campaign/agents/F02_terrain/PREREGISTRATION.md
?? tools/monkey_campaign/agents/F02_terrain/brief.md
?? tools/monkey_campaign/agents/F02_terrain/discovery_note.md
?? tools/monkey_campaign/agents/F02_terrain/receipts/determinism_receipt.txt
?? tools/monkey_campaign/agents/F02_terrain/receipts/test_run.txt
?? tools/monkey_campaign/agents/F02_terrain/receipts/validate_receipt.json
?? tools/monkey_campaign/agents/F02_terrain/tests/test_terrain.py
?? tools/monkey_campaign/data/monkey_clearing/terrain_bundle.json
?? tools/monkey_campaign/data/monkey_clearing/terrain_bundle.py
?? tools/monkey_campaign/data/monkey_clearing/terrain_query.py
```

M-F02's footprint is exactly `agents/F02_terrain/` (7 files) plus the three declared data
paths (`terrain_bundle.py`, `terrain_bundle.json`, `terrain_query.py` in
`data/monkey_clearing/`). The one modified file (`U02_camera/receipts/latency_run.json`)
and every other untracked path belong to parallel sessions — untouched by M-F02. No
existing file was modified by this agent; no engine C++ edits; no GPU; no servers
launched; scratch compiles went to gitignored `.tmp/f02_determinism/` and tempdirs.

Not committed (coordinator commits agent files, per campaign pattern).
