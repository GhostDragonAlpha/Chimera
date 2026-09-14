# A4_READBACK — RESULTS (relay to Astra)

2026-09-14 · RTX 4090 (24 GB, ReBAR on, tsPeriod 1 ns) · Windows WDDM ·
headless standalone Vulkan 1.1, per Astra's Q3 spec (see README.md) ·
N=40 warm + cold iter0 per cell unless noted.

## THE FINDING (one paragraph)

**The ~900 ms does NOT reproduce in the spec-compliant standalone — and every
one of Astra's candidate mechanisms was individually exercised and measured.**
The real IMAGE→BUFFER pull (8.3 MB) with a valid fence dependency, noncoherent-
safe ordering, persistently-mapped cached staging costs **2.16 ms median /
2.56 ms max** request→data-in-RAM (copy itself 0.31 ms ≈ 26.5 GB/s; mapped
first read 0.3 µs; publication into ordinary RAM 1.4 ms). Across 21 regimes ×
40 iterations, the ONLY segment that ever grows past ~2 ms is **fence_wait,
and it grows exactly in proportion to PRIOR WORK QUEUED AHEAD of the copy on
the same queue** — 4-byte cells wait out a 4 GB backlog identically to 8 MB
cells (6.9 ms), a 19 GB re-fill under 80 %-of-VRAM commit costs ~101 ms of
fence_wait while the readback copy itself still executes in 0.32 ms — and the
worst standalone observation anywhere is **104 ms** (pressure, cold iter0),
vs the engine's ~940–965 ms steady and ~1.07 s first pull. Paging under VRAM
oversubscription, driver-implicit sync at map/first-touch (omitted fence),
idle wake (3 s sleeps), invalidate, mapped access, and RAM publication are all
ruled out as the 900 ms home. By elimination with Astra's signature list, the
engine's stall is **queue serialization whose "prior work" the standalone does
not have: the swapchain/present flip chain** (or whatever the engine queues
behind/around it) — the standalone's row-5 mechanics scaled up to frame level.
The engine's own numbers (fence 3 µs, collect 2 µs, present 109–161 µs,
frame() ~940 ms) agree: the wait lives in a segment the engine does not
instrument yet; the harness timeline schema ports 1:1 into the engine's pull
and will name it.

(Shape per THE_LAW: STATEMENT — the 900 ms is not an intrinsic cost of
copy→map→read on this hardware/driver, it is inherited queued work.
PREDICTION (untested, falsifiable) — in the engine, pull latency will be
(1) size-independent (8.3 MB ≈ 4 bytes pulled) and (2) collapse when the
readback is submitted BEFORE the frame's present/flip work or on a separate
queue with a semaphore dependency instead of queue order.
FALSIFIER — port these timeline segments into the engine's pull: if the 900 ms
lands in `submit` (CPU-side) or scales with pulled bytes, this statement is
wrong and the mechanism is CPU/publication-side instead.)

## Signature verdicts (Astra's decisive list)

| Signature | Verdict on this machine (standalone) | Decisive numbers |
|---|---|---|
| **paging** (residency/page-table op spanning the delay) | **RULED OUT** at standalone level | 19 GB committed + re-filled every iteration: fence_wait 101 ms = the deliberate fill time; readback gpu_copy stays 0.32 ms, first_read 0.4 µs, memcpy 0.38 ms. No delay appears inside the readback path. |
| **scheduling** (runnable work waiting while other contexts execute) | not observed | witness job (independent resources, second queue) completed +114 µs after the readback fence, 0 device-wide stalls in 19 warm iters. |
| **queue serialization** (copy follows earlier work / identifiable dependency) | **REPRODUCED — the only mechanism that grows the delay** | 4 GB backlog: fence_wait 7.26 ms (8 MB pull) vs 6.85–6.93 ms (4-BYTE pulls) — delay tracks prior work, independent of pull size; with no backlog fence_wait is 0.03–0.76 ms. |
| **CPU-side blocking** (delayed submit, worker wakeup, lock, first-touch fault, publication) | **RULED OUT** for every CPU segment | submit 5–34 µs; first_read 0.3 µs; memcpy 0.38 ms; swizzle 0.98 ms; invalidate = no-op (driver has no noncoherent cached type — see README caveat 2); nofence cell (dependency omitted): memcpy 401 µs vs 376 µs baseline — NVIDIA injects no big implicit sync at first-touch for 8.3 MB. |
| **true device-wide stall** (independent resource-independent work also stops) | **NOT OBSERVED** | witness cell: independent job always completed within ~0.1–0.6 ms of the readback fence, never blocked behind it. |
| **initialization / first-touch / residency (row 1 cold-only)** | once-per-process only, ~80 ms, NOT per-pull | process-cold iter0: 79.8 ms (78.5 ms of it fence_wait = first-submission/context/WDDM bring-up); the NEXT regime's cold iter0: 1.8 ms; all warm: 2.2 ms. Engine's "first pull ~1.07 s EVERY boot" is 13x this. |
| **fixed overhead vs transfer work (row 2)** | scaling confirmed, all sub-3 ms | 4 B: 39 µs e2e_read (30 µs fence_wait) vs 8.3 MB: 2.16 ms — the standalone's cost is transfer/access work, no constant ~900 ms term exists. |
| **copy+completion with NO CPU access (row 3)** | no stall without CPU access — and none with it either | noread request→fence_return: 0.38 ms (8 MB), 39 µs (4 B). |
| **read / memcpy / swizzle split (row 4)** | publication is µs-to-ms scale, never ~900 ms | first_read 0.3 µs · memcpy 0.38 ms · swizzle 0.98 ms (8.3 MB). |
| **idle vs queued (row 5)** | idle wake is innocent; queued work dominates | idlesleep (3 s GPU idle before each pull): cold 1.94 ms, warm median 2.25 ms — indistinguishable from warm idle cells. |

## Key table — the 8.3 MB real pull across regimes (median/max, ms)

| regime (img8M full read) | e2e_read med | e2e_read max | fence_wait med | gpu copy med |
|---|---:|---:|---:|---:|
| idle (warm, N=39) | 2.16 | 2.56 | 0.75 | 0.31 |
| idle after 3 s sleep (N=10) | 2.25 | 2.60 | 0.87 | 0.31 |
| behind 4 GB backlog (N=39) | 8.64 | 9.47 | 7.26 | 0.31 |
| 19 GB VRAM pressure + re-fill (N=39) | 102.5 | 109.5 | 101.1 | 0.32 |
| nofence (dependency omitted, warm) | 1.41 | 2.63 | (0) | 0.31 |
| nofence + 4 GB backlog (warm) | 1.35 | 1.53 | (0) | 0.42 |
| cold, first submission of process | 79.8 | — | 78.5 | 0.31 |

**Read the pressure row carefully**: the 101 ms of fence_wait is the queue
draining the deliberately-queued 19 GB fill submitted ahead of the readback
(measured separately: the pin pass alone costs ~105 ms). The readback copy,
map, and read stay at µs–0.3 ms even at 80 % VRAM commit. Delay tracks PRIOR
WORK, never the readback. The same law at frame scale, with present/flip work
as the prior queue, is the surviving hypothesis for the engine's ~900 ms.

## Engine vs standalone (the discriminating delta)

| quantity | engine (our rounds) | standalone (this harness) |
|---|---:|---:|
| steady pull | ~940–965 ms | 2.16 ms (8.3 MB, full path) |
| effective throughput | 9.2 MB/s | ~3.9 GB/s (e2e_read, 8.3 MB) |
| first pull after boot | ~1.07 s | 79.8 ms |
| fence wait | 3 µs (reported) | 0.03–0.76 ms idle; grows only with queued work |
| present | 109–161 µs | absent (no swapchain — by spec) |

The standalone differs from the engine exactly by: swapchain/present/DWM flip
queue, the engine's other per-frame allocations and queue traffic, and
whatever ordering the engine uses between pull and present. Those are the
follow-up rows in README.md.

## Raw numbers

- `raw_timeline_matrix.csv` — every iteration, 20 regimes, full continuous
  timeline (ns) + GPU timestamps.
- `raw_timeline_pressure.csv` — same + `img8M_full_pressure` regime.
- `summary_matrix.md`, `summary_pressure.md` — per-regime segment tables
  (median/max) as generated by the exe.
- Harness: `tools/readback_probe/` (build: see README.md).
