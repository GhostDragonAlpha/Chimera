# CPU-RATE DISPOSITION — no CPU hard caps on this host; what IS enforced, measured

Lane: gpu_broker2_20260922 (`Agent: broker2`), 2026-09-22. Governing spec:
Astra round 6 section 2 ("Fleet CPU: 50% aggregate ceiling ... Windows Job
Objects provide CPU hard caps ... without requiring WSRM") and the nested-job
warning: "a nested job's CPU quota is relative to its capped parent. A child at
50% under a fleet parent at 50% gets approximately 25% of machine CPU."

## 1. The policy: CPU hard caps are REFUSED, not pretended

Carried forward unchanged from phase 1 (measured finding F-CPURATE,
`tools/science_funnel/validation/fleet_supervisor_20260922/`, Win11 build 26200):

- The CPU-rate control primitive could not be pinned: SET at information class 7
  "succeeds" and is a measured NO-OP (a spinner ran 0.955 of one core under a
  claimed 10% hard cap); class 14 rejects every rate value with
  ERROR_INVALID_PARAMETER (both the 8- and 16-byte struct); no other class caps
  a measured spinner (0.962 baseline, all candidates > 0.9).
- Per Rule 0, `broker.admit` therefore REFUSES any spec that declares
  `resources.cpu_pct`, and `jobobject.create_job` refuses to set one. A cap that
  cannot be enforced must never be reported as enforced.

Astra's nested-CPU multiplication is thereby carried as a DOCUMENTED hazard, not
a measured effect: since no CPU-rate quota can be set on this build at any job
level, there is nothing to multiply — but if a future build makes the primitive
pinnable, configure the fleet parent and the child quotas TOGETHER (child % is
relative to the parent's %; 50-in-50 ≈ 25 of machine). The trap is pinned in
`jobobject.py` header comments.

## 2. The measured working alternative: job-object AFFINITY (P-CPUAFFINITY)

Where a rate cap cannot be enforced, a HARD PARTITION of logical processors can.
Phase 2 added `affinity_mask` to `jobobject.create_job` (verified by READBACK of
the limit flags and the mask before the job is used — the phase-1 wrong-class
trap taught: effects and readbacks, never API return values).

Measured today (this suite, `tests_gpu_broker.py` check
`CPUAFFINITY_measured_alternative`; 8 spinner PROCESSES for 1.0 s at
below-normal priority; python THREADS cannot show this — the GIL makes 8 threads
draw ~1 core, which the first draft of the check measured on itself):

| Configuration | wall s | CPU s | effective cores (of 32 LPs) |
|---|---|---|---|
| job pinned to 2 of 32 LPs | 4.21 (machine under gaming load) | 6.91 | **1.79** |
| job unpinned, 8 spinners | 1.20 | 8.20 | **9.64** |

The partition held: identical CPU DEMAND, ~5.4x less CPU consumed under the
affinity job. (Earlier runs with a quiet machine measured 1.9-2.0 effective
cores pinned — the bound is exactly the mask size; today's 1.79 is the same
effect measured while the operator was gaming.)

### What affinity IS and IS NOT (honest limits)

- IS: an enforceable ceiling on CPU consumed by a job (a hard partition),
  readback-verifiable, inherited by the whole process tree.
- IS NOT: a utilization percentage. A single-threaded job pinned to 2 LPs still
  only ever uses 1 core; an 8-thread job pinned to 2 LPs uses at most 2.0 —
  the mask bounds the ENVELOPE, and multi-threaded demand fills it.
- IS NOT: isolation of memory bandwidth, disk latency, thermals, or driver
  activity (Astra's warning stands verbatim). Throughput measurements still
  require the exclusive quiet windows of scheduling rule 4.

## 3. What this fleet enforces instead (and it IS enforced)

- `mem_gib` (job + process committed memory) and `max_procs` (active-process
  limit) — pinned by phase-1 `tests_primitives.py` against measured effects
  (allocation failure inside the job, no machine RAM dip), 15/15.
- Priority classes: builds run BELOW_NORMAL (`KIND_PRIORITY`); the affinity
  spinner above also ran below-normal.
- Affinity masks: available per job from phase 2 (above).
- The gaming-mode gate (admit no fleet GPU work / no new builds) and the
  reservation state machine (active / expired_pending / uncertain / released,
  never auto-free) are the primary protection for the operator's session; CPU
  caps were always secondary to "do not run fleet work while he games".

## 4. Decision

Keep `cpu_pct` REFUSED. Document affinity as the enforceable substitute where a
job's CPU envelope must be bounded, and re-test the CPU-rate primitive only on a
future OS build (the class-numbering trap and the no-op-at-class-7 behavior are
build-specific measurements, pinned in `jobobject.py`, to be re-derived, not
assumed, on any new build).
