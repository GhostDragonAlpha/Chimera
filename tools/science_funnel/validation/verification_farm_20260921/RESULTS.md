# RESULTS — Verification Farm pilot (Astra P1), 2026-09-21

Lane `agent/verification-farm-20260921` · Trailer Agent: GLM 5.3
Prereg: `PREREG.md` in this directory (banked before any run; batch order [4,1,8,2] fixed there).
Runner: `tools/agent_fleet/verify_farm.py` · Pinned baseline: canonical `agent/gait-wave38-calendar-guard` @ `30821ef7`.

## Measured workload note

The Astra upper-bound arithmetic ("N ten-minute runs in one ~ten-minute batch")
assumed a 10-minute verification. The pinned walk-baseline workload MEASURES
30.7 s run + ~10-18 s cold build per job on this machine. The claim shape
(N jobs, one batch, unchanged bytes) is tested exactly; the numbers below are the
measured reality and supersede the 10-minute idealization.

## Throughput curve (R1_run = 30.6885 s = median{setup 30.8, c1 30.577})

| c | N | batch wall (s) | gain = N x R1_total / wall | run p50 (s) | inflation p50 | run p95 (s) | build p50 (s) | RAM peak (GB) |
|---|---|----------------|----------------------------|-------------|---------------|-------------|---------------|---------------|
| 1 | 1 | 47.6 | 1.00 (reference) | 30.58 | -0.4% | 30.58 | 10.2 | 40.3 |
| 2 | 2 | 52.0 | 1.83 | 33.55 | +9.3% | 33.55 | 11.2 | 42.5 |
| 4 | 4 | 49.7 | 3.83 | 30.88 | +0.6% | 30.94 | 12.4 | 44.2 |
| 8 | 8 | 68.0 | 5.60 | 39.84 | +29.8% | 40.40 | 17.7 | 46.0 |

Spine-first confirmation (c=4 shape: 1 spine + 3 exploratory, spine admitted first):
spine run 30.527 s (limit 41.43 s = 1.35 x R1_run — green), exploratory p50 35.41 s
(+15.4%). The spine slot measurably runs at isolated speed while siblings absorb the
contention.

The c=4 batch ran FIRST in the banked order (coldest caches) and still shows the
lowest inflation; the c=2 batch ran LAST (warmest) and is slower than c=4. Warm-cache
and thermal bias do not explain the curve; c=2 is a single-sample batch (n=2), so its
+9.3% should be read with that error bar.

## Falsifier verdicts

- **F-FARM-BYTES: GREEN (not fired).** All 19 jobs across 5 batches (15 benchmark +
  4 spine-confirmation): exit 0, stdout sha256 = `71065ac54fa988704ce29cd79cfb5cdbe0d4e2eab3f7db69b10d4b8d94517592`
  (22184 bytes), scene sha256 = `f6844eeae3dc87170a572ccdeedf326a6cac4f73d1448941808bd8b25a8db342`.
  Byte identity holds under parallel load — the determinism-under-concurrency proof.
- **F-FARM-NO-GAIN: GREEN (not fired).** Every measured c in {2,4,8} improves
  completion time after scheduling overhead (gains 1.83 / 3.83 / 5.60).
- **F-FARM-TAIL: GREEN (not fired).** Spine job 30.527 s vs registered limit 41.43 s.

Setup finding (recorded honestly): building/running from the master checkout of this
lane produced a DIFFERENT stdout sha (`cf382756...`, 15794 bytes) on the SAME scene —
the pin is load-bearing; the farm must build from the pinned worktree, which is what
the runner enforces.

## Resource policy (measured, recommended)

- **Recommended production concurrency: c=4** — the largest measured level with
  run-phase inflation < 10% (banked rule); it delivers 3.83x serial throughput at
  isolated-speed verification latency.
- c=8 is a legal backlog-drain level (bytes exact, gain 5.60x) but its +29.8%
  run inflation exceeds the banked tail rule; do not use it for spine-adjacent work.
- Runner-enforced policy: exploratory WIP bounded at 8 and at floor(cores) - 4;
  4 logical cores reserved for the serial spine; spine-priority jobs bypass the WIP
  bound and block exploratory admission until placed.
- Peak system RAM observed 46.0 GB of 128 GB at c=8 — no memory pressure; the
  binding constraint is run-phase inflation, not RAM.

## Artifacts

- `batch_c4.json`, `batch_c1.json`, `batch_c8.json`, `batch_c2.json`, `batch_c4_spine.json`
  — full per-job records (run/build/queue timings, exit codes, shas, RSS peaks, RAM curves).
- Mechanics scripts (ephemeral, outside the repo): `E:/ChimeraWork/farm_setup.ps1`,
  `farm_setup_verify.ps1`, `farm_ref_pinned.ps1`, `farm_batches.ps1`.
