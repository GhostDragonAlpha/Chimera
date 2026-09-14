# Chimera engine bench - measured ticks/s

- engine: http://127.0.0.1:8107
- host: Desktop-BI03LBO (Windows-11-10.0.26200-SP0)
- date (UTC): 2026-09-14T02:19:02Z
- sample interval: 250 ms; scenario duration: 60.0 s; pass bar: 60.0 ticks/s
- PASS criterion per scenario: 1% low (1st percentile of per-interval ticks/s) >= 60.0. min is reported for transparency; a single bad interval is not the bar.
- ticks/s per interval = (ticks_now - ticks_prev) / (t_now - t_prev), from GET /tick_state. The first interval of each scenario is discarded as warm-up. Intervals where the counter moved backwards (engine restart) are excluded and counted as resets; a scenario also FAILs on any reset or if the engine is unreachable past the 60 s retry window.

## Scenario: IDLE - FAIL

| metric | value |
|---|---|
| mean ticks/s | 294.32 |
| min ticks/s | 0.00 |
| 1% low (p1) | 44.18 |
| max ticks/s | 308.76 |
| intervals | 233 used (1 warm-up discarded, 0 counter reset(s), 0 failed poll(s)) |

- load: none
- detail: 1% low 44.2 < bar 60.0

## Scenario: GAME_PAGE_LOAD - FAIL

| metric | value |
|---|---|
| mean ticks/s | 217.32 |
| min ticks/s | 0.00 |
| 1% low (p1) | 0.00 |
| max ticks/s | 651.30 |
| intervals | 146 used (1 warm-up discarded, 0 counter reset(s), 0 failed poll(s)) |

- load: /verts ok=118 err=0 (78.4 MB pulled); /frame?w=1024 ok=30 err=0 (105.1 MB pulled)
- detail: 1% low 0.0 < bar 60.0

## Scenario: TOUCH_STORM - FAIL

| metric | value |
|---|---|
| mean ticks/s | 294.98 |
| min ticks/s | 0.00 |
| 1% low (p1) | 58.18 |
| max ticks/s | 302.66 |
| intervals | 235 used (1 warm-up discarded, 0 counter reset(s), 0 failed poll(s)) |

- load: /tick_touch ok=30 err=0; /tick_touch_clear ok=30 err=0
- detail: 1% low 58.2 < bar 60.0

## Overall verdict: FAIL (0/3 scenarios at or above 60.0 ticks/s 1% low)

## R6 VERDICT (appended 2026-09-14 by lane A2)

Sources: the bench.py run above (2026-09-14T02:19:02Z) + `tools/game_shell/fps_probe.js`
(Playwright, channel `chrome`, 1600x900, `#play-btn` -> play, rAF counted by a
pre-load `addInitScript` shim wrapping `requestAnimationFrame` -- counts the
page's own frames only; pose animated twice per window via
`POST /api/pose {joint_index: 15 (knee_L), deg: 25}` then `deg: 0`;
3 x 10 s windows per mode). Raw probe JSON: `.tmp/fps_probe.json`.

| measurement | mean | min | 1% low | vs 60 bar (mean / 1% low) | verdict |
|---|---|---|---|---|---|
| engine ticks/s - IDLE (60 s) | 294.32 | 0.00 | 44.18 | 4.9x / 0.74x | FAIL (strict p1) |
| engine ticks/s - GAME_PAGE_LOAD (60 s) | 217.32 | 0.00 | 0.00 | 3.6x / 0.00x | FAIL (strict p1) |
| engine ticks/s - TOUCH_STORM (60 s) | 294.98 | 0.00 | 58.18 | 4.9x / 0.97x | FAIL (strict p1) |
| browser fps - headless (3 x 10 s, in play, pose animating) | 240.04 | 240.02 | 240.02 | 4.0x / 4.0x | PASS |
| browser fps - headed (3 x 10 s, in play, pose animating) | 239.84 | 239.58 | 239.58 | 4.0x / 3.99x | PASS |

Engine ticks/s UNDER live browser load (sampled by fps_probe.js during the
headed+headless windows, 250 ms intervals, 6 windows total): mean 298.5-299.6,
min 289.47 ticks/s -- never below 4.8x the bar, zero counter resets.

### Bottom line

**PASS at the player; FAIL on bench.py's strict per-scenario criterion. Both
are measured; neither is hidden.**

- The 60 fps bar as a player experiences it: met with 4.0x headroom. Headed
  Chrome on the real game page, in play, pose animating: 6/6 windows at
  239.58-240.05 fps -- locked to the display vsync (RTX 4090,
  CurrentRefreshRate = 239 Hz) with ZERO missed frames across 60 s of play.
- bench.py's automated criterion (1% low ticks/s >= 60 per scenario): FAIL 0/3,
  because the tick counter advances in bursts: min 0.00 in EVERY scenario
  (whole 250-700 ms sampling windows with zero tick advance, then catch-up
  bursts up to 651.30 ticks/s under load), p1 44.18 / 0.00 / 58.18. Even IDLE
  shows it (~1-2% of intervals). Cause is inside the engine (not probed; out of
  this lane's file scope).

### WHY GAME_PAGE_LOAD is the worst -- model drift, measured

index.html (the real game page) pulls `/api/verts` at 3 Hz and `/api/state` at
~1.4 Hz and NEVER calls `/api/frame` (verified by grep: no match in
tools/game_shell/index.html) -- it renders client-side from verts. bench.py's
GAME_PAGE_LOAD instead pulls `/frame?w=1024` every 2 s (105.1 MB in 60 s); each
engine-side frame render visibly blocks the tick loop (p1 = 0.00, max =
651.30). The scenario measures a load the player never imposes. The stall did
NOT reach the player in any probe window: under real page load the engine's
per-250 ms ticks stayed >= 289.47 and the browser missed no frames.

### Follow-ups (not done in this lane)

1. bench.py GAME_PAGE_LOAD should model the live page (`/api/verts` 3 Hz +
   `/api/state` 1.4 Hz) and keep `/frame?w=1024` as its own 4th scenario --
   the 0.00 p1 under /frame load is real and worth keeping visible.
2. Engine lane: why does the ticks counter freeze for entire 250 ms windows
   even at IDLE (~1-2% of intervals)? Single-threaded sim+serve contention or
   counter coalescing would explain bursts of 0 then 650/s.
3. TOUCH_STORM p1 = 58.18 is within 3% of the bar -- fine at 240 Hz today, no
   headroom to spare at exactly 60 Hz.
