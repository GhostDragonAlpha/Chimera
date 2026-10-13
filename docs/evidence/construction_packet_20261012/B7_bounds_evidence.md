# B7 — Bound cost and preserve state (construction gate, M4 release gate)

Gate row (GAME_PLAN_ACTION_RPG.md §13), verbatim:

> B7 / B2 onward, M4 release gate — bound cost and preserve state | Resident
> native working set, independent physical clock, bounded topology pools,
> recovery and compatible render LOD | No routine full-state CPU round trip;
> declared 4090 memory/frame-time envelope; repeated construction has stable
> RAM/VRAM/disk use

Battery: `tools/construction_packet/test_b7_bounds.py` (port 8798, own engine,
stdout captured for the frame-time window). Envelope:
`B7_declared_envelope.json` — written BEFORE the measurements below, against
the plan's reference machine (RTX 4090 + i9-13900K + 128 GB; this host).

Result: **8/8 green, twice**, and the full B0–B6 regression stays green
(23 + 5 + 8 + 6 + 6 + 4 + 6 + 7 = 65 prior tests + 8 B7 = 73).

## What the engine gained

1. **Independent physical clock** (`MembraneTick::b2_clock_loop_`,
   membrane_tick.cpp): one dedicated `std::chrono::steady_clock` thread wakes
   every 2 ms, measures real elapsed time, clamps catch-up at 50 ms per wake,
   and steps the B2 scene under `b2_mtx_`. The render loop's
   `g_tick.b2_step(tick_dt)` call is REMOVED — physical outcomes no longer
   depend on the display cadence (gallery item 12). Every bound applied is
   counted (`catchup_clamps`), every wake that overran 2× the budget is
   counted (`slow_ticks`), and the worst gap is kept (`max_gap_ms`) — a
   stalled engine reports itself instead of silently teleporting the
   simulation (plan: "slow frames are reported"). Joined in the shutdown tail
   (`shutdown: b2_clock_stopped`) before `engine.shutdown()`; the destructor
   joins as a backstop. Route: `GET /tick_b2_clock`.
2. **Bounded topology pools** (b2_scene): fixed caps
   parts 6 / welds 15 / chambers 6 / valves 12 / heat 12 / pistons 6, each
   over-cap transaction refused with a self-named message
   (`"valve: pool cap reached (12 connectors); remove one first"`), usage
   reported every tick as `state.pools = [used, cap]`. The weld cap equals
   C(6,2) so that pool is bounded by construction.
3. **Round-trip accounting** (b2_scene): `save_count_ / restore_count_ /
   hash_count_` (mutable instrumentation, never serialized) exposed as
   `state.round_trips`. Saves/restores happen only on the explicit routes;
   hashing only on `GET /tick_b2_hash`.
4. **Display LOD** (b2_scene): `POST /tick_b2_render_lod {"level":0|1}`.
   Level 0 renders/picks the physical boundary triangles; level 1 renders
   each part's world AABB (12 tris) through the same nearest-hit law.
   Physics, the save document and the state hash never see the level; picks
   resolve the same part ids and hit points at either level; the attached
   reaction force is bit-identical across a switch (plan §13: "never swap
   attached physics out for a visual-only representation").
5. **Two gate-driven engine corrections** (the gate found real defects):
   - `admit()` did not reset `paused_` — a scene admitted after a paused one
     inherited the pause and never stepped. A fresh admission is a fresh
     scene: it now runs.
   - `telemetry_json()` embedded `state_hash()` in EVERY `/tick_b2_state`
     response — that full serialise-and-hash on the routine read channel WAS
     the routine full-state CPU round trip the gate forbids. Removed; the
     transaction proof lives on the explicit `/tick_b2_hash` route (and no
     battery ever consumed the embedded copy).

## Measurements vs the declared envelope

| clause | declared bound | measured | verdict |
|---|---|---|---|
| clock sim/wall ratio | [0.95, 1.05] | 1.000 (2 s window, 700 ticks) | pass |
| catch-up bounds applied | reported | 0 clamps, 0 slow ticks, max gap 3.77 ms | pass |
| routine payload | ≤ 65 536 B | state 1 392 B, process 717 B | pass |
| round trips while stepping | 0 saves/restores/hashes | 0/0/0 over 0.5 s physics | pass |
| RSS growth, 25 construction cycles | ≤ 8 MiB | 0.05 MiB over 10 cycles (probe); ≤ bound in battery | pass |
| VRAM growth, 25 cycles | ≤ 256 MiB (shared-GPU tolerance) | within bound (host at ~23.5 GB from other processes) | pass |
| Saved/ disk growth | 0 B | 0 B | pass |
| frame time avg (engine 5 s window) | ≤ 16.7 ms | 0.54–0.58 ms avg, ≤ 0.86 ms max, 63 FPS | pass |
| pool caps | 6/15/6/12/12/6 | usage sits AT each cap; over-cap refused by name; refusals hash-invariant | pass |

## Test-by-test

- `test_independent_physical_clock` — thread live, ratio in envelope, ticks
  > 100/s, zero clamps in steady state, slow-tick counter reported.
- `test_no_routine_full_state_round_trip` — full plant (chambers, valve,
  heat, piston); 0.5 s of stepping moves no round-trip counter; both routine
  payloads inside the declared bound.
- `test_bounded_topology_pools` — every pool filled to cap (usage == cap),
  over-cap admit/place/chamber/valve/heat/piston refused with named errors,
  all refusals hash-invariant (paused scene).
- `test_repeated_construction_plateau` — 25× (admit → welds → chambers →
  valve → piston → 50 ms physics → save): RSS growth after warm-up ≤ 8 MiB,
  VRAM growth ≤ 256 MiB, Saved/ byte total unchanged (gallery item 11's
  "memory reaches a bounded plateau").
- `test_recovery_preserves_state` — save → 0.2 s of evolution → restore:
  state hash bit-equal, part ids survive, chamber inventories equal to 1e-12.
- `test_display_lod_compatible` — LOD switch hash-invariant, reaction force
  identical, picks agree (id + hit point), LOD 1 = 12 tris/part, level 2
  refused hash-invariant.
- `test_triangle_order_invariance` — same box with the boundary-triangle
  list rotated by one and by five faces settles to the same reaction
  (1e-9 rel), same sink, same mass (gallery item 13: triangle order does not
  change material strength; no engine change needed — the solver walks the
  list order-independently).
- `test_frame_time_envelope` — the engine's own `ft ms avg` window ≤ 16.7 ms
  while a B2 scene is live.

## Gate honesty

- "Change the display cadence or stop rendering entirely" is tested only as
  far as the resident runtime allows: the clock thread is structurally
  independent of the frame loop (the frame loop no longer steps physics at
  all), and the ratio holds while frames run at 63 FPS; a true
  render-stopped window would need a headless mode the runtime does not
  expose. The independence is structural, not inferred.
- VRAM is measured on a GPU shared with other processes; the bound tolerates
  their noise (256 MiB) rather than pretending to isolate the engine's own
  allocations. The overlay re-upload lane is the only B2 VRAM path and it
  reuses one slot.
- The clock thread steps at wall rate (~350 wakes/s); the fixed 1/4000 s
  substep inside `step()` keeps physics deterministic per sim-second
  (B2–B6 batteries re-verified green on the clock-driven runtime).
