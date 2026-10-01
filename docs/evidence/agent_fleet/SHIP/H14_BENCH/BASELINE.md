# H14 — PRE-BUILD BASELINE (the before-picture for the build window)

Date: 2026-09-14 (UTC). Binary: `.tmp/build_tick/Release/chimera_engine.exe`,
sha256 `3854de552013e8612ff46fbd3898a151dc114b15c59d27c09028c676a3f54b03`
(pre-build-window: BEFORE gait machine + async capture readback + sealed-cell
guard land). Host: Desktop-BI03LBO, RTX 4090, Windows 11. World: the live
world's own snapshot (sealed, 5 cells, 18,459 verts, 36,630 tris) replayed on
a scratch engine, private port 8141, isolated cwd.

Command (exactly the post-build form):

    python tools/game_shell/bench.py --scratch \
        --report docs/evidence/agent_fleet/SHIP/H14_BENCH/bench_baseline_pre_build.md

Full report: `bench_baseline_pre_build.md`. Overall verdict: **PASS 4/4** (exit 0).

## The numbers the after-run must beat or match (1% low of 5 s buckets, bar 60)

| scenario        | mean t/s | 1% low t/s | max t/s | load actually applied |
|---|---|---|---|---|
| IDLE            | 299.24 | **298.99** | 299.48 | none |
| GAME_PAGE_LOAD  | 298.92 | **298.44** | 299.37 | delta=1 3 Hz (2.0 MB/60s; keyframes 3, runs 172) + tick_state 1.4 Hz (116.7 KB/60s) |
| FRAME_THUMBNAIL | 161.10 | **134.14** | 190.04 | /frame?w=1024 every 2 s (105.1 MB/60s pulled, 30 pulls) |
| TOUCH_STORM     | 299.14 | **298.42** | 299.35 | 30 presses + 30 clears (press/clear every 1 s) |

R6 comparison (previous PASS, live 8107, rerun2 2026-09-14T04:53Z): IDLE 249.20,
GAME_PAGE_LOAD 298.18 (then: FULL-frame model, 117 MB/60s), FRAME_THUMBNAIL
130.65, TOUCH_STORM 291.76 — all 1% low. The scratch baseline is at or above
the R6 numbers in every scenario, so it is a FAIR (in fact slightly stricter)
before-picture.

## What the build window will move, and where to look

- **Gait machine ticking**: watch IDLE + TOUCH_STORM means (the per-tick solve
  grows); the 1% lows are the bar.
- **Async capture readback (G8)**: watch FRAME_THUMBNAIL — the R6/here stall
  (raw 250 ms min 0.00 t/s, bucket 1% low ~134) should shrink or vanish; the
  mean should climb toward IDLE. G8's own bar (ticks/min preserved through a
  /frame burst) is `SHIP/G8_CAPTURE/verify_g8_capture.py`.
- **Sealed-cell guard**: no bench scenario targets it directly; if any scenario
  suddenly FAILs with `sealed` semantics in the log, suspect the guard before
  the tick loop.
- **C3 regression watch**: GAME_PAGE_LOAD's load line must stay
  keyframes<=3, runs>=170 per 60 s, ~2 MB pulled — if keyframes balloon, the
  delta stream regressed (see POLL_COST.md for the byte baseline).
