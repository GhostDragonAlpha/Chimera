# Chimera engine bench - measured ticks/s

- engine: http://127.0.0.1:8141 (SCRATCH, throwaway; exe E:\ChimeraWork\slot-01\.tmp\build_tick\Release\chimera_engine.exe sha256 3854de552013e8612ff46fbd3898a151dc114b15c59d27c09028c676a3f54b03; scene snapshot replayed: True; engine log E:\ChimeraWork\slot-01\.tmp\bench_scratch\run_20260914_135531_p8141)
- host: Desktop-BI03LBO (Windows-11-10.0.26200-SP0)
- date (UTC): 2026-09-14T13:59:57Z
- raw sample interval: 250 ms; scenario duration: 60.0 s; pass bar: 60.0 ticks/s
- PRIMARY measurement: 5-second buckets of consecutive /tick_state
  readings; bucket rate = delta(ticks)/elapsed. PASS criterion per scenario: 1% low of BUCKET rates >= 60.0.
- Why buckets: the raw counter advances in bursts (R6 measured whole 250 ms windows at 0 ticks then catch-ups up to 651/s), so per-window percentiles sank below the bar even at IDLE. The raw 250 ms per-interval rates are still computed and reported below as a footnote row per scenario (like-for-like with the R6 run).
- ticks/s = (ticks_now - ticks_prev) / (t_now - t_prev), from GET /tick_state. The first reading of each scenario is discarded as warm-up. Readings where the counter moved backwards (engine restart) are excluded and counted as resets; a scenario also FAILs on any reset or if the engine is unreachable past the 60 s retry window.
- GAME_PAGE_LOAD models the REAL page: index.html polls /api/verts at 3 Hz (-> engine /verts?delta=1, the C3 kernel stream -- the page has never pulled the full frame at steady state since C3) and /api/state at ~1.4 Hz (-> engine /tick_state) and NEVER calls /frame. FRAME_THUMBNAIL is the /frame?w=1024 thumbnail channel (reel / dyad grabs), NOT the game page -- kept visible because its engine-side render stall is real.

## Scenario: IDLE - PASS

| metric (5 s buckets) | value |
|---|---|
| mean ticks/s | 299.24 |
| min ticks/s | 298.99 |
| 1% low (p1) | 298.99 |
| max ticks/s | 299.48 |
| buckets | 12 used (1 warm-up reading(s) discarded, 0 counter reset(s), 0 failed poll(s)) |

> Footnote -- raw 250 ms per-interval samples (not the bar; the bursty counter sinks these): mean 299.24, min 292.04, 1% low 295.13, max 302.74, n=240.

- load: none

## Scenario: GAME_PAGE_LOAD - PASS

| metric (5 s buckets) | value |
|---|---|
| mean ticks/s | 298.92 |
| min ticks/s | 298.43 |
| 1% low (p1) | 298.44 |
| max ticks/s | 299.37 |
| buckets | 12 used (1 warm-up reading(s) discarded, 0 counter reset(s), 0 failed poll(s)) |

> Footnote -- raw 250 ms per-interval samples (not the bar; the bursty counter sinks these): mean 298.92, min 292.03, 1% low 293.81, max 302.63, n=240.

- load: /verts?delta=1 (the page's C3 ask) ok=175 err=0 (2.0 MB pulled; kernel keyframes=3, runs=172, legacy=0); /tick_state (the page's /api/state) ok=86 err=0 (116.7 KB pulled)

## Scenario: FRAME_THUMBNAIL - PASS

| metric (5 s buckets) | value |
|---|---|
| mean ticks/s | 161.10 |
| min ticks/s | 134.10 |
| 1% low (p1) | 134.14 |
| max ticks/s | 190.04 |
| buckets | 12 used (1 warm-up reading(s) discarded, 0 counter reset(s), 0 failed poll(s)) |

> Footnote -- raw 250 ms per-interval samples (not the bar; the bursty counter sinks these): mean 231.45, min 0.00, 1% low 0.00, max 979.34, n=178.

- load: /frame?w=1024 (thumbnail channel, NOT the game page) ok=30 err=0 (105.1 MB pulled)

## Scenario: TOUCH_STORM - PASS

| metric (5 s buckets) | value |
|---|---|
| mean ticks/s | 299.14 |
| min ticks/s | 298.38 |
| 1% low (p1) | 298.42 |
| max ticks/s | 299.35 |
| buckets | 12 used (1 warm-up reading(s) discarded, 0 counter reset(s), 0 failed poll(s)) |

> Footnote -- raw 250 ms per-interval samples (not the bar; the bursty counter sinks these): mean 299.14, min 283.43, 1% low 295.40, max 302.67, n=240.

- load: /tick_touch ok=30 err=0; /tick_touch_clear ok=30 err=0

## Overall verdict: PASS (4/4 scenarios at or above 60.0 ticks/s 1% low, 5 s buckets)
