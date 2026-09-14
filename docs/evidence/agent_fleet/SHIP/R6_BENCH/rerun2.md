# Chimera engine bench — R6 RE-RUN 2 (independent confirmation of the corrected harness)

- agent: R6-rerun (fleet 3), slot-01, branch `astra/tasks/matter-kernel-format-01`
- date (UTC): 2026-09-14 (bench run 2026-09-14T04:53:20Z)
- engine: http://127.0.0.1:8107 — live, sealed 4-cell creature, NOT stopped or rebuilt by this lane
- host: Desktop-BI03LBO (Windows-11-10.0.26200-SP0), RTX 4090 (see the honest note)
- harness: `tools/game_shell/bench.py` (fleet 2/D1's corrected model, already in the tree — read, not re-explored), 4 scenarios x 60 s, raw 250 ms sampling, PRIMARY judgement on 5 s buckets, exit code 0
- full bench output (verbatim): [rerun2_report.md](rerun2_report.md)

Zero counter resets, zero failed polls across all four scenarios.

## Per-scenario table (5 s buckets, 60 s, vs the 60 t/s bar)

| scenario | mean | min | 1% low | vs 60 bar (mean / 1% low) | mission verdict (mean >= 60 AND 1% low >= 40) | bench verdict (1% low >= 60) |
|---|---|---|---|---|---|---|
| IDLE | 294.53 | 243.27 | 249.20 | 4.91x / 4.15x | PASS | PASS |
| GAME_PAGE_LOAD (real page model) | 299.05 | 298.10 | 298.18 | 4.98x / 4.97x | PASS | PASS |
| FRAME_THUMBNAIL (thumbnail channel, NOT the game) | 152.74 | 128.95 | 130.65 | 2.55x / 2.18x | PASS | PASS |
| TOUCH_STORM | 297.59 | 291.28 | 291.76 | 4.96x / 4.86x | PASS | PASS |

Bench's own stricter criterion (1% low >= 60) also passes 4/4, so the mission
criterion (1% low >= 40) is met with margin everywhere; the tightest row is
FRAME_THUMBNAIL at 2.18x the mission bar on the 1% low.

## Comparison vs the prior runs

| scenario | R6 original (250 ms windows, drifted model) | D1 corrected re-run (5 s buckets) | THIS re-run (5 s buckets) |
|---|---|---|---|
| IDLE | mean 294.32 / p1 44.18 — FAIL | mean 299.12 / p1 298.28 — PASS | mean 294.53 / p1 249.20 — PASS |
| GAME_PAGE_LOAD | mean 217.32 / p1 0.00 — FAIL (measured `/frame` every 2 s — a load the page never imposes) | mean 297.52 / p1 293.80 — PASS (real page model) | mean 299.05 / p1 298.18 — PASS |
| FRAME_THUMBNAIL | — (folded into the drifted GAME_PAGE_LOAD) | mean 133.03 / p1 70.32 — PASS | mean 152.74 / p1 130.65 — PASS |
| TOUCH_STORM | mean 294.98 / p1 58.18 — FAIL | mean 299.35 / p1 299.23 — PASS | mean 297.59 / p1 291.76 — PASS |

- IDLE 294.32 -> 294.53 mean: unchanged to within noise; the R6 FAIL was the
  bursty-window percentile artifact, not lost throughput.
- GAME_PAGE_LOAD 217.32 -> 299.05 mean: the entire R6 gap was the drifted
  model's engine-side `/frame` renders (105 MB/60s the player never triggers).
  Under the real page model the page costs ~1.5% vs IDLE (294.53 -> 299.05 —
  within run noise; D1 measured ~0.5%). Confirmed independently of D1.
- FRAME_THUMBNAIL varies strongly run-to-run (mean 204-206 in D1's superseded
  runs, 133.03 in D1's final, 152.74 here) and its RAW series keeps the full
  stall signature every time (this run: raw min 0.00, max 715.31 catch-up,
  108.6 MB/60s). The engine-side render stall under a 2 s `/frame?w=1024`
  cadence is real and reproducible; only its bucket-level depth varies.
- IDLE raw this run caught one slow 250 ms window (min 50.17) — exactly the
  burst behavior the 5 s bucket primary exists to smooth; it cost nothing at
  bucket level (p1 249.20).

## Honest note (the bar this host cannot test)

**This host is an RTX 4090 driving a 240 Hz display.** The 60 ticks/s bar
models a MID-RANGE machine at 60 fps. **The 60 t/s mid-range bar remains
UNTESTED here** — every number above measures HEADROOM on an enthusiast GPU
(~2.2x-5.0x the bar), not the floor. A mid-range run needs a mid-range host
(or a derived per-frame budget model); this report does not claim one.

## R6 RE-RUN 2 VERDICT

**PASS — 4/4 scenarios.** Every mean >= 60 t/s (lowest: FRAME_THUMBNAIL
152.74) and no 1% low below 40 t/s (lowest: FRAME_THUMBNAIL 130.65). The
corrected-harness result of D1's re-run is independently reproduced: the real
game page costs the engine ~1-2% vs idle, and the only real stress finding
stays the thumbnail channel, which no player load pulls.
