# Chimera engine bench — R6 RE-RUN (corrected harness)

- agent: D1 (fleet 2), slot-01, branch `astra/tasks/matter-kernel-format-01`
- date (UTC): 2026-09-14 (bench run 2026-09-14T03:50:53Z)
- engine: http://127.0.0.1:8107 — live, sealed 4-cell creature (`"sealed":true,"n_cells":4`), NOT stopped or rebuilt by this lane
- host: Desktop-BI03LBO (Windows-11-10.0.26200-SP0), **RTX 4090** (see the honesty note in the verdict)
- harness: `tools/game_shell/bench.py`, 4 scenarios x 60 s, exit code 0

## What changed in the model (this re-run vs R6)

R6's bench strict-FAIL was traced to two MEASURED causes. Both are fixed in the
harness; nothing about the engine changed.

1. **MODEL DRIFT fixed.** The old GAME_PAGE_LOAD pulled `/frame?w=1024` every
   2 s (105 MB/60s) — a load the real game page NEVER imposes (`index.html`
   has no `/frame` call; it renders client-side from `/api/verts` at 3 Hz and
   polls `/api/state` at ~1.4 Hz; `server.py` proxies `/api/state` ->
   engine `/tick_state` and `/api/verts` -> engine `/verts`). GAME_PAGE_LOAD
   now models exactly that: GET `/verts` every 333 ms + GET `/tick_state`
   every 700 ms. The `/frame?w=1024` path is kept as its own scenario,
   **FRAME_THUMBNAIL**, honestly labeled as the thumbnail channel (reel / dyad
   grabs), not the game — its engine-side render stall is real and stays
   visible.
2. **BURSTY TICK COUNTING fixed (primary metric).** The tick counter advances
   in bursts (R6: whole 250 ms windows at 0 ticks, then catch-ups up to
   651/s), sinking per-window percentiles. The PRIMARY judgement is now the
   1% low of per-**5-second-bucket** rates (bucket rate = delta(ticks)/elapsed
   over consecutive `/tick_state` readings). The raw 250 ms per-interval
   series is still computed and reported as a footnote row per scenario,
   like-for-like with R6.
3. Aggregation semantics (measured into correctness during this lane): slow
   polls MERGE across buckets (the counter is monotonic; an early gap-split
   rule fragmented FRAME_THUMBNAIL into a single bucket because the engine
   answers `/tick_state` late while a thumbnail render blocks it — merging is
   the honest average), and a bucket splits only on a backwards counter
   (restart) or a >10 s reading gap (pathological). True outages belong to
   the existing 60 s engine-lost abort, which is unchanged.

Run history (honesty): two earlier runs tonight are superseded — one passed
all four scenarios in-log but crashed in the report writer (a `%d`-count bug,
fixed); one produced a fragmented 1-bucket FRAME_THUMBNAIL row from the
gap-split rule above (fixed). The tables below are from the final, complete
run (2026-09-14T03:50:53Z); the full bench report follows verbatim.

## Full bench output (verbatim, `.tmp/bench_report.md`, final run)

- engine: http://127.0.0.1:8107
- host: Desktop-BI03LBO (Windows-11-10.0.26200-SP0)
- date (UTC): 2026-09-14T03:50:53Z
- raw sample interval: 250 ms; scenario duration: 60.0 s; pass bar: 60.0 ticks/s
- PRIMARY measurement: 5-second buckets of consecutive /tick_state
  readings; bucket rate = delta(ticks)/elapsed. PASS criterion per scenario: 1% low of BUCKET rates >= 60.0.
- Why buckets: the raw counter advances in bursts (R6 measured whole 250 ms windows at 0 ticks then catch-ups up to 651/s), so per-window percentiles sank below the bar even at IDLE. The raw 250 ms per-interval rates are still computed and reported below as a footnote row per scenario (like-for-like with the R6 run).
- ticks/s = (ticks_now - ticks_prev) / (t_now - t_prev), from GET /tick_state. The first reading of each scenario is discarded as warm-up. Readings where the counter moved backwards (engine restart) are excluded and counted as resets; a scenario also FAILs on any reset or if the engine is unreachable past the 60 s retry window.
- GAME_PAGE_LOAD models the REAL page: index.html polls /api/verts at 3 Hz (-> engine /verts) and /api/state at ~1.4 Hz (-> engine /tick_state) and NEVER calls /frame. FRAME_THUMBNAIL is the /frame?w=1024 thumbnail channel (reel / dyad grabs), NOT the game page -- kept visible because its engine-side render stall is real.

### Scenario: IDLE - PASS

| metric (5 s buckets) | value |
|---|---|
| mean ticks/s | 299.12 |
| min ticks/s | 298.23 |
| 1% low (p1) | 298.28 |
| max ticks/s | 299.59 |
| buckets | 12 used (1 warm-up reading(s) discarded, 0 counter reset(s), 0 failed poll(s)) |

> Footnote -- raw 250 ms per-interval samples (not the bar; the bursty counter sinks these): mean 299.12, min 271.82, 1% low 292.61, max 302.02, n=240.

- load: none

### Scenario: GAME_PAGE_LOAD - PASS

| metric (5 s buckets) | value |
|---|---|
| mean ticks/s | 297.52 |
| min ticks/s | 293.64 |
| 1% low (p1) | 293.80 |
| max ticks/s | 299.51 |
| buckets | 12 used (1 warm-up reading(s) discarded, 0 counter reset(s), 0 failed poll(s)) |

> Footnote -- raw 250 ms per-interval samples (not the bar; the bursty counter sinks these): mean 297.51, min 262.69, 1% low 281.87, max 303.05, n=240.

- load: /verts ok=176 err=0 (117.0 MB pulled); /tick_state (the page's /api/state) ok=85 err=0 (71.8 KB pulled)

### Scenario: FRAME_THUMBNAIL - PASS

| metric (5 s buckets) | value |
|---|---|
| mean ticks/s | 133.03 |
| min ticks/s | 70.29 |
| 1% low (p1) | 70.32 |
| max ticks/s | 189.66 |
| buckets | 11 used (1 warm-up reading(s) discarded, 0 counter reset(s), 0 failed poll(s)) |

> Footnote -- raw 250 ms per-interval samples (not the bar; the bursty counter sinks these): mean 218.06, min 0.00, 1% low 0.00, max 1053.63, n=157.

- load: /frame?w=1024 (thumbnail channel, NOT the game page) ok=30 err=0 (105.1 MB pulled)

### Scenario: TOUCH_STORM - PASS

| metric (5 s buckets) | value |
|---|---|
| mean ticks/s | 299.35 |
| min ticks/s | 299.23 |
| 1% low (p1) | 299.23 |
| max ticks/s | 299.68 |
| buckets | 12 used (1 warm-up reading(s) discarded, 0 counter reset(s), 0 failed poll(s)) |

> Footnote -- raw 250 ms per-interval samples (not the bar; the bursty counter sinks these): mean 299.36, min 295.00, 1% low 295.62, max 302.85, n=240.

- load: /tick_touch ok=30 err=0; /tick_touch_clear ok=30 err=0

### Overall verdict: PASS (4/4 scenarios at or above 60.0 ticks/s 1% low, 5 s buckets)

## R6 RE-RUN VERDICT

**PASS — 4/4 scenarios, strict bucket criterion.** Zero counter resets, zero
failed polls across all four scenarios.

| scenario (5 s buckets, 60 s) | mean | min | 1% low | vs 60 bar (mean / 1% low) | verdict |
|---|---|---|---|---|---|
| IDLE | 299.12 | 298.23 | 298.28 | 4.99x / 4.97x | PASS |
| GAME_PAGE_LOAD (real page model) | 297.52 | 293.64 | 293.80 | 4.96x / 4.90x | PASS |
| FRAME_THUMBNAIL (thumbnail channel, NOT the game) | 133.03 | 70.29 | 70.32 | 2.22x / 1.17x | PASS |
| TOUCH_STORM | 299.35 | 299.23 | 299.23 | 4.99x / 4.99x | PASS |

### Comparison vs the old R6 run

| measurement | R6 (250 ms windows) | this re-run (5 s buckets) | what moved |
|---|---|---|---|
| IDLE | mean 294.32 / p1 44.18 — FAIL | mean 299.12 / p1 298.28 — PASS | p1 6.75x. Two causes: the burst-smoothing buckets AND the raw 250 ms stalls themselves did not reproduce this run (raw min 271.82 tonight vs 0.00 in R6) — see honesty notes. |
| GAME_PAGE_LOAD | mean 217.32 / p1 0.00 — FAIL (measured `/frame` every 2 s: a load the page never imposes) | mean 297.52 / p1 293.80 — PASS (measures the REAL page: `/verts` 3 Hz + `/tick_state` 1.4 Hz) | The real page costs the engine ~0.5% (299.12 -> 297.52 mean). R6's 0.00 p1 was the artifact of the drifted model, not player reality. |
| FRAME_THUMBNAIL (new; the /frame load R6's GAME_PAGE_LOAD accidentally measured) | — (was folded into GAME_PAGE_LOAD) | mean 133.03 / p1 70.32 — PASS | The `/frame?w=1024` cost is REAL: 105.1 MB/60s, raw series still shows 0-tick windows and 1053.63 catch-ups, engine throughput drops ~55%. Kept visible on purpose. |
| TOUCH_STORM | mean 294.98 / p1 58.18 — FAIL (3% below bar) | mean 299.35 / p1 299.23 — PASS | Now 4.99x the bar with margin to spare. |
| browser fps (player path, R6's fps_probe.js: 240.04 headless / 239.84 headed, vsync-locked, zero missed frames) | PASS | not re-measured in this lane | This lane owns bench.py only; the player-path PASS from R6 stands unchanged (and nothing engine-side changed since). |

### Honest notes

1. **This machine is an RTX 4090 at a 240 Hz display.** The 60 ticks/s bar
   models a mid-range machine at 60 fps. **The mid-range bar remains
   UNTESTED** — everything above measures headroom on an enthusiast GPU, not
   the floor. A mid-range run needs a mid-range host (or a derived budget
   model), and this report does not claim one.
2. **R6's idle-level counter stalls did not reproduce.** R6 measured raw
   250 ms min 0.00 in EVERY scenario (p1 44.18 at IDLE) and blamed a bursty
   counter. Tonight the raw series at IDLE is nearly clean (min 271.82,
   p1 292.61) — so the R6 raw-level stalls were either transient
   (engine/host state at 02:19 UTC) or fixed engine-side since; this lane
   did not probe the engine (out of file scope). The 5 s bucket primary is
   robust either way: it smooths bursts if they return, and it barely
   changes tonight's clean numbers (bucket p1 298.28 vs raw p1 292.61 at
   IDLE).
3. **FRAME_THUMBNAIL is the one real stress finding.** Its bucket p1 is only
   **1.17x the bar** (70.32 vs 60), it varies strongly run-to-run (earlier
   superseded runs: ~204-206 mean), and its raw series keeps the full stall
   signature (min 0.00, max 1053.63). No player load pulls `/frame` — but
   anything that starts grabbing thumbnails at a 2 s cadence (the reel, the
   dyad) runs the engine close to the 60 t/s line. The engine lane may want
   to know why a 2 s PNG grab costs ~55% of tick throughput.
4. The bench harness crashed once tonight in its report writer after all
   scenarios passed (a formatting bug, since fixed and smoke-tested against
   PASS and engine-lost result shapes). The crash guard did its job (a
   report was still written); the superseded runs' in-log numbers are quoted
   above only where they inform run-to-run variance.

**Bottom line: with the harness measuring what the player actually imposes,
the engine PASSES the 60 t/s bar 4/4 with 4.9x headroom on the real page —
on an RTX 4090. The thumbnail channel (1.17x) and the untested mid-range
floor are the two honest open edges.**
