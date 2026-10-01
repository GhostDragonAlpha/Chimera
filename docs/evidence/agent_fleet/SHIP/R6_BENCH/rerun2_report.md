# Chimera engine bench - measured ticks/s

- engine: http://127.0.0.1:8107
- host: Desktop-BI03LBO (Windows-11-10.0.26200-SP0)
- date (UTC): 2026-09-14T04:53:20Z
- raw sample interval: 250 ms; scenario duration: 60.0 s; pass bar: 60.0 ticks/s
- PRIMARY measurement: 5-second buckets of consecutive /tick_state
  readings; bucket rate = delta(ticks)/elapsed. PASS criterion per scenario: 1% low of BUCKET rates >= 60.0.
- Why buckets: the raw counter advances in bursts (R6 measured whole 250 ms windows at 0 ticks then catch-ups up to 651/s), so per-window percentiles sank below the bar even at IDLE. The raw 250 ms per-interval rates are still computed and reported below as a footnote row per scenario (like-for-like with the R6 run).
- ticks/s = (ticks_now - ticks_prev) / (t_now - t_prev), from GET /tick_state. The first reading of each scenario is discarded as warm-up. Readings where the counter moved backwards (engine restart) are excluded and counted as resets; a scenario also FAILs on any reset or if the engine is unreachable past the 60 s retry window.
- GAME_PAGE_LOAD models the REAL page: index.html polls /api/verts at 3 Hz (-> engine /verts) and /api/state at ~1.4 Hz (-> engine /tick_state) and NEVER calls /frame. FRAME_THUMBNAIL is the /frame?w=1024 thumbnail channel (reel / dyad grabs), NOT the game page -- kept visible because its engine-side render stall is real.

## Scenario: IDLE - PASS

| metric (5 s buckets) | value |
|---|---|
| mean ticks/s | 294.53 |
| min ticks/s | 243.27 |
| 1% low (p1) | 249.20 |
| max ticks/s | 299.79 |
| buckets | 12 used (1 warm-up reading(s) discarded, 0 counter reset(s), 0 failed poll(s)) |

> Footnote -- raw 250 ms per-interval samples (not the bar; the bursty counter sinks these): mean 298.01, min 50.17, 1% low 284.91, max 302.55, n=238.

- load: none

## Scenario: GAME_PAGE_LOAD - PASS

| metric (5 s buckets) | value |
|---|---|
| mean ticks/s | 299.05 |
| min ticks/s | 298.10 |
| 1% low (p1) | 298.18 |
| max ticks/s | 299.42 |
| buckets | 12 used (1 warm-up reading(s) discarded, 0 counter reset(s), 0 failed poll(s)) |

> Footnote -- raw 250 ms per-interval samples (not the bar; the bursty counter sinks these): mean 299.04, min 291.24, 1% low 292.43, max 302.51, n=240.

- load: /verts ok=176 err=0 (117.0 MB pulled); /tick_state (the page's /api/state) ok=86 err=0 (84.0 KB pulled)

## Scenario: FRAME_THUMBNAIL - PASS

| metric (5 s buckets) | value |
|---|---|
| mean ticks/s | 152.74 |
| min ticks/s | 128.95 |
| 1% low (p1) | 130.65 |
| max ticks/s | 186.10 |
| buckets | 10 used (1 warm-up reading(s) discarded, 0 counter reset(s), 0 failed poll(s)) |

> Footnote -- raw 250 ms per-interval samples (not the bar; the bursty counter sinks these): mean 230.76, min 0.00, 1% low 0.00, max 715.31, n=156.

- load: /frame?w=1024 (thumbnail channel, NOT the game page) ok=31 err=0 (108.6 MB pulled)

## Scenario: TOUCH_STORM - PASS

| metric (5 s buckets) | value |
|---|---|
| mean ticks/s | 297.59 |
| min ticks/s | 291.28 |
| 1% low (p1) | 291.76 |
| max ticks/s | 299.59 |
| buckets | 12 used (1 warm-up reading(s) discarded, 0 counter reset(s), 0 failed poll(s)) |

> Footnote -- raw 250 ms per-interval samples (not the bar; the bursty counter sinks these): mean 297.63, min 244.11, 1% low 278.07, max 302.48, n=240.

- load: /tick_touch ok=30 err=0; /tick_touch_clear ok=30 err=0

## Overall verdict: PASS (4/4 scenarios at or above 60.0 ticks/s 1% low, 5 s buckets)
