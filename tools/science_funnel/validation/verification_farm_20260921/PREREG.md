# PREREG — Verification Farm pilot (Astra P1), 2026-09-21

Lane: `agent/verification-farm-20260921` · Trailer Agent: GLM 5.3
Parent protocol: `E:/ChimeraWork/lane-archive/astra-acceleration-pilots-20260921.md` §P1
Pinned baseline: canonical `agent/gait-wave38-calendar-guard` @ `30821ef7` (WAVE 38 SHIP).

## Rule 0 membrane (STATEMENT · PREDICTION · FALSIFIER)

**STATEMENT** (disagreeable): the wave-38 walk verification workload is
concurrency-invariant on this machine — N independent copies of the same pinned
commit, built and run simultaneously in private directories, produce byte-identical
stdout and identical scene bytes to the isolated execution.

**PREDICTION** (not yet measured): at c=8 on the 24-core i9-13900K, one batch of 8
jobs completes in less than 4x the c=1 batch wall-clock; per-job run-phase inflation
stays below 25%; every job's stdout sha equals the banked baseline sha.

**FALSIFIERS** (named before any run):

- **F-FARM-BYTES** — fires if ANY job in ANY batch has: stdout sha256 !=
  `71065ac54fa988704ce29cd79cfb5cdbe0d4e2eab3f7db69b10d4b8d94517592`, OR scene
  sha256 != `f6844eeae3dc87170a572ccdeedf326a6cac4f73d1448941808bd8b25a8db342`,
  OR exit code != 0, OR stdout byte count != 22184. This is the
  determinism-under-parallel-load proof. If it fires: STOP, report the divergent
  bytes, do not tune.
- **F-FARM-NO-GAIN** — fires if no measured c in {2,4,8} achieves batch
  throughput gain > 1.0, where gain = (N x R1_total) / T_batch(c) and R1_total is
  the banked per-job build+run time at c=1 (scheduling overhead included).
- **F-FARM-TAIL** — banked spine-candidate latency limit: 1.35x R1_run. Fires if
  any spine-slot job's run-phase time at any measured c exceeds that limit.

## Frozen scope

- Workload: `gait_unit.exe <scene.json>`, stdout raw-redirected via `cmd /c`
  (no shell re-encoding). Intra-run arithmetic and thread policy fixed: the
  binary runs with its default policy; per-job compile is a single TU with no
  `/MP`, per-batch build parallelism `/m:2` — identical in every batch.
- Machine: i9-13900K (24C/32T), run-as-found thermals and cache state.
- Builds in the benchmark are COLD (fresh private build dir per job, removed
  after hashing). The setup verification run is the only cached-build
  observation and is labeled as such.
- RAM: system-wide available-bytes sampled every 500 ms per batch
  (peak used = total - min available); per-job peak RSS via psutil on the
  `gait_unit.exe` child.

## Banked measurement order (fixed before first batch, anti warm/thermal bias)

`[c=4, c=1, c=8, c=2]`

## Reference and decision rule

- R1_run = median run-phase seconds of {setup verification run, c=1 batch run}.
  R1_total = same median over build+run seconds.
- Production concurrency = largest c in {2,4,8} with median job run-phase
  inflation < 10% AND F-FARM-BYTES green AND T_batch(c) < N x R1_total.
  If none qualifies, recommendation is c=1 and F-FARM-NO-GAIN is adjudicated.
- Resource policy (banked, spine-first): exploratory WIP is bounded at 8 jobs;
  the runner never admits more than floor((logical_cores - 4)) exploratory
  slots; 4 logical cores stay reserved. A spine-priority job bypasses the WIP
  bound, is admitted immediately, and blocks further exploratory admissions
  until it is placed. The serial spine's blocking verification always has
  capacity.

## Stop conditions

F-FARM-BYTES firing, a job exceeding 3x (R1_run + R1_build), or batch wall-clock
exceeding 40 minutes → halt the benchmark, record the finding, report.
