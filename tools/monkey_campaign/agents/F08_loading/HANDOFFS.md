# F08 Handoffs — what W10, U07 and R05/F08-review consume from the loading layer

Author: M-F08. Date: 2026-09-24. The two files to load:

- `tools/monkey_campaign/data/monkey_forest/forest_loader.py` — the one-shot
  forest loader (`load_forest()`, `ForestScene`, `receipt_document`, CLI
  `receipt`/`selftest`). Stdlib-only, CPU-only, headless. Import from the repo
  root: `from tools.monkey_campaign.data.monkey_forest import forest_loader`.
- The suite that proved all of this:
  `tools/monkey_campaign/agents/F08_loading/verify_loading.py` (stdlib only;
  GREEN 66/66; receipts in `agents/F08_loading/receipts/` — `run.json` sha256
  `4ebd3a6c…37c` byte-identical across consecutive runs; three fresh-process
  loads byte-identical, `receipts/determinism.txt`).

## The verified loading layer, in one block

| Quantity | Value | Source |
|---|---|---|
| Recompile identity | all four declarations byte-identical to recipes: clearing 13,112 B / terrain 877,752 B / trunk 16,634 B / routes 8,495 B | verify T1 (falsifier (a) green, in-process ×2 + 3 fresh processes) |
| Committed file pins | `18dd2ff6…` / `446ed3fb…` / `94ff906e…` / `28dff2b3…` | prereg table, re-measured before and after the suite |
| Initial-state digest | `initial_state_sha256 = c3286e14a787f6bb65ccc93dc3e80b0412d777048d109d404ca49328fe1bf627`, schema `chimera.monkey_forest.v1` | verify T4 (identical in-process ×2 and across fresh processes) |
| Missing-asset contract | 4/4 omissions → `f08_missing_artifact` naming (artifact, absolute path), checked before any recompile | verify T2 |
| Corruption contract | 13/13 tamper cases refused by name: body/pin edits → `f08_invalid_artifact` carrying `f0X_digest_mismatch`/`f0X_invalid_json`; coherent re-forge → `f08_recompile_drift` | verify T3 |
| Teardown | 7/7 resources released by name, engine slot FIRST; second teardown a named no-op; failed release → loud `f08_teardown_leak`, retryable to clean | verify T5 (headless doubles, falsifier (d) green) |
| Loaded surface | ONE query implementation: `terrain_query.TerrainSurface`; worst triangle 0.042522289331596436 at (17.0, 7.0) == F02's receipt | verify T6 |

## To W10 (walking acceptance consumes this loader)

1. **Load through F08, never re-read the JSONs ad hoc.** The legal walking
   scene is what the loader proves:
   ```python
   from tools.monkey_campaign.data.monkey_forest import forest_loader
   with forest_loader.load_forest() as scene:
       surface = scene.terrain_surface        # THE ONE query surface (F02's law)
       state = scene.initial_state            # spawn, trunk site, route graph
       routes = scene.routes                  # full declared route layer
   ```
   Any second parse of the declarations in W10's own code is a second truth —
   the loader already refused anything that does not recompile byte-identically.
2. **The spawn and goal are in `scene.initial_state`**: spawn `[0, 0, 0]` on
   flat ground (height 0.0, gradient (0,0)), trunk approach at
   `(11.976783, 2.471766)` with the climbable surface `trunk_01.lateral`
   (radius 0.037, height 1.158), straight route `R0` length `12.229185` ending
   at the contact ring `0.287 m` from the axis — F07's handoff numbers,
   re-proven at load. If a live walking run starts anywhere else, the defect is
   in the boot wiring, not the data.
3. **Slope checks use the loaded surface** (`scene.terrain_surface.gradient_at`
   — never a second heightfield): worst measured slope remains 0.042522289
   (`worst_triangle_slope()`), under F01's 0.05 law. F04's L2 gap applies
   unchanged: the frozen engine has no heightfield contact; in-vivo terrain
   reading lives in the Python binding lane.
4. **If the loader refuses, STOP — the scene is not loadable.** A refusal
   (`f08_missing_artifact`, `f08_invalid_artifact`, `f08_recompile_drift`) is
   the F08 contract working: report the named code and artifact, never patch
   the committed file by hand. Re-compile through the recipes (F07's law).
5. **Compose teardown with the session flow**: `scene.teardown` is a zero-arg
   callable in `SessionFlow`'s exact `teardown` shape. Compose order for an
   in-vivo session: engine death first, data second —
   `teardown=lambda: (world.shutdown_engine(), scene.teardown())` or attach the
   engine callable via `scene.attach_engine_shutdown(world.shutdown_engine)`
   (declared referent; released FIRST by the reverse-load order). Calling
   teardown twice is safe by contract (second call is a named no-op).

## To U07 (play measurement)

1. **The measurement session's scene identity is the initial-state digest**:
   `c3286e14a787f6bb65ccc93dc3e80b0412d777048d109d404ca49328fe1bf627`. Stamp
   every run receipt with it (plus the four artifact file shas from
   `scene.receipt`) so any two play measurements are comparable scene-to-scene.
   A different digest means the scene changed — the runs are not comparable
   without saying so.
2. **Reproduce the environment honestly**: `python
   tools/monkey_campaign/data/monkey_forest/forest_loader.py receipt` prints
   the full deterministic scene identity (no wall clock in it — byte-identical
   across processes, so it can go verbatim into a run receipt).
3. **Teardown is part of the measured session** (R05's repeated-cycles
   requirement): use the context manager or call `scene.teardown()` on exit;
   a `f08_teardown_leak` in a measurement run is a defect to report, not to
   swallow.

## To R05 / F08-review hooks

1. **Owned-children closure (R05's C-row)**: the data-layer cleanup is
   `ForestScene.teardown()` — reverse-load order, engine slot first (its
   declared referent is `World.shutdown_engine`, slice_server.py:174-181 —
   terminate → wait(10 s) → kill), zero-live audit, exactly-one-real-teardown
   (SessionFlow's terminal law, session_flow.py:107-117). R05's repeated
   restart/exit cycles should hold a load→teardown→load loop: every cycle must
   end with `live_resources() == []` and every cycle's load must refuse
   identically under the same tamper (deterministic refusals, no order
   dependence — Phase A checks all four presences before any recompile).
2. **Review hooks (what would falsify this item now)**: (a) any recompile
   differing by one byte on any platform/Python — rerun `verify_loading.py`;
   (b) any load completing with an artifact absent/tampered; (c) any
   `initial_state_sha256` differing from `c3286e14…`; (d) any teardown leaving
   a name in `live_resources()`. All four are executable in seconds via the
   suite.
3. **Known scope (recorded, not silently dropped)**: the route recompile's
   live-input proof (`route_recipe.load_live_inputs`) reads the REAL pinned
   tree by design (the module's frozen pins) — the loader's own
   byte-identity check is what proves a configured root's copy faithful. The
   engine process itself is never owned by this loader (headless data layer);
   the engine teardown slot is an INJECTED callable whose referent is cited,
   not imported — no server was started for any of this.
4. **Amendment coupling**: if F05's evidence-based slope envelope re-freezes
   the route declaration (F07's declared amendment path), the loader will
   refuse `f08_recompile_drift` until the committed artifact is recompiled
   through the recipes — that is the contract working. Re-run this suite after
   any upstream re-freeze; the prereg's digest table then needs a recorded
   amendment (new pins, same laws).
