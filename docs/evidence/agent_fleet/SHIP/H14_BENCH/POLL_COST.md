# H14 — THE PAGE POLL COST (measured, not claimed)

Feeds C3 (delta compression) verification. Tool: `measure_poll_cost.js`
(self-contained: boots its own scratch engine + scratch shell on private ports
8141/8241, opens ONE headless-Chrome player, samples the engine tick counter
per the G8 method, and reads per-poll bytes from the page's OWN
PerformanceResourceTiming so the one-delta-client chain is never contended).
Raw: `poll_cost_raw.json`. Date: 2026-09-14, binary sha256
`3854de55...` (pre-build-window).

## Engine-side cost of one open page (ticks/min, G8 true-rate method)

| phase                          | ticks/min | t/s    |
|---|---|---|
| no page (settled 30 s first)   | 17,941.4  | 299.02 |
| page open, idle                | 17,937.3  | 298.96 |
| page open, knee pose oscillating | 17,945.1 | 299.09 |
| page closed again              | 17,942.0  | 299.03 |

**One open page costs the engine nothing measurable on this build** — all four
phases within 0.1 % of each other. The page's 3 Hz + 1.4 Hz poll streams are
noise against a 300 t/s loop. (First run's "no page = 271 t/s" was a boot
transient: the cold scratch engine settles onto 300 t/s over its first minute —
hence the 30 s settle now built into the tool and into `bench.py --scratch`.)

## Bytes per poll (the page's own resource timings)

- `/api/verts?delta=1` steady state: **p50 = 316 B**, active-phase mean 4,481 B,
  active-phase max 89,856 B (runs payloads; 16 B of those polls are the empty
  header). Full frame on the same engine: **664,528 B** — the idle steady-state
  per-poll ratio is **2,103x**.
- `/api/state` (-> `/tick_state`): **1,658–1,706 B** at ~1.4 Hz (the payload
  grew with the gait fields; still ~0.15 MB/min).
- Session keyframes: the FIRST delta pull of a session is a keyframe
  (16 + n*36 B), by design.

## Bytes per minute per player (the C3 baseline)

| player                          | verts      | state      | total        |
|---|---|---|---|
| ONE IDLE player (45 s window)   | 2.72 MB/min| 0.15 MB/min| **2.87 MB/min** |
| ONE ACTIVE player (45 s window; knee_L oscillated 25<->0 deg every 2 s) | 75.1 MB/min | 0.14 MB/min | **75.2 MB/min** |

C3's bar: >10x byte drop vs the pre-C3 page (full frame at 3 Hz ≈ 119.6 MB/min
idle, ≈ 126 MB/min at the same active motion).

- IDLE: 2.87 vs 119.6 MB/min = **41.7x drop — PASS**.
- ACTIVE (sustained whole-mesh pose motion): 75.2 vs 126 MB/min = only **1.7x**
  — the delta honestly degrades to keyframes under big changes (83/207 pulls
  were keyframes). The engine REFUSES to send a delta that would not beat the
  full frame, so this is correct behavior, but the >10x bar does NOT hold for
  this pathological motion pattern. Named for C3, not hidden.

## Named findings for C3 (not H14's files to fix)

1. **Resync amplification through the python shell proxy**: the IDLE player
   pulled ~4 unexpected keyframes/min (each 664 KB). Every page-side transport
   hiccup (fetch error / seq gap / 429) costs a full keyframe via the page's
   `pullKey()` resync. The R9 funnel already flagged the per-IP 429 flood;
   combined with resync amplification a starved client is also an expensive
   one. Candidate fixes live in server.py/page, not the engine.
2. **Direct unchained pull answers a keyframe, then 16 B**: after the page
   closed, a direct `?delta=1` returned a 664,540 B keyframe; 3 s later, 16 B
   (flags=1, runs=0). Idle-world "unchanged" is the 16 B header — the bit-map
   memcmp path works as documented.
