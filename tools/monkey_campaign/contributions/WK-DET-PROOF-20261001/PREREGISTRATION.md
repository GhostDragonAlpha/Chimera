# PREREGISTRATION — determinism proof v1 (draft for Lieutenant commit)

- Lane: `wk-proof-det` (worker), 2026-10-01. Direct Captain implementation tasking.
- Deliverable dir: `E:/ChimeraWork/monkey-coordination/determinism-proof/` (sole write scope).
- Status: **DRAFT**. Gated execution starts only after the Lieutenant commits this
  file and returns the pin SHA (prereg law; a package seal is not a substitute
  for the required commit — NO_WORKTREES.md, "Publication and scientific
  precommitment").
- Method documents obeyed: `E:/PythonChimera/tools/monkey_campaign/NO_WORKTREES.md`
  (no worktrees; CPU via task_package runner; GPU only via the existing mailbox
  queue), `E:/ChimeraWork/gpu-queue/PROTOCOL.md`.
- Whole-run precedent: MAT2-W10 whole-run verification
  (`E:/ChimeraWork/monkey-coordination/evidence-store/MAT2-W10/numerical/walking_demo_receipt.json`,
  `determinism_zero_control.r1_vs_r2_state_chains_bit_identical`).

## 0. Pinned environment and hardware (measured, executable-reported)

| Item | Measured value | Measured how (this lane, unless noted) |
|---|---|---|
| GPU | NVIDIA GeForce RTX 4090, 24564 MiB, compute cap 8.9 (sm_89), UUID GPU-2decfc88-729b-6cc5-472b-ad7336073800 | `nvidia-smi --query-gpu=...`, probe file section 1 |
| Driver | 616.92 | `nvidia-smi`, probe section 1 |
| CUDA toolkit (host) | 12.8, nvcc V12.8.61, `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8` | `nvcc --version`, probe section 2 |
| Toolkit-bundled CCCL | CUB/Thrust version macros 200700 (2.7 line); `include/cuda/execution` ABSENT | probe sections 3-4 |
| Interpreter | Python 3.13.5 (MSC v.1943), `E:/ChimeraWork/envs/newton/Scripts/python.exe` | probe section 7 |
| newton | 1.6.0 | importlib.metadata + pip list, probe sections 5/7 |
| warp-lang | 1.17.0 (`wp.config.version` 1.17.0) | probe section 7 |
| numpy | 2.5.3 | probe sections 5/7 |
| warp runtime CUDA report (driver/toolkit tuples, arch) | NOT YET RE-OBSERVED this session — Phase B queue job re-records (wk-newton-install previously recorded driver (13,4), toolkit (12,9), arch 89; that is prior-lane evidence, not claimed here) | Phase B d1/d2 receipts |
| Host | Windows 10.0.26200 x64, i9-13900K-class, 128 GB (runner profile) | NO_WORKTREES.md host profile |

Pins carried from the install lane and re-measured by `pip list`:
newton wheel sha256 `5eedebe17d7261ca39e8f97c2f2f20e22e7264d0aed01782f3cb1dd60180b872`,
warp-lang wheel sha256 `ca35c82242a7553046f09023bbe56750b5c3d9af72625bd1a905a56d3189771d`,
numpy wheel sha256 `71cad2b2a7451ab79d8f5e71b453485b6775963d5cf794179144a7463fe6e8ec`.

## 1. Availability record (Phase A — done, no install performed)

Reference fetched and cited: https://nvidia.github.io/cccl/unstable/cccl/determinism.html —
determinism levels `not_guaranteed ⊆ run_to_run ⊆ gpu_to_gpu` via
`cuda::execution::require(cuda::execution::determinism::run_to_run)`; bitwise-identical
outputs for reductions/scans; guarantee bound to a fixed CCCL + CUDA toolkit version and
identical tuning; consumers are several CUB device algorithms.

| Option | Verdict | Evidence |
|---|---|---|
| CCCL deterministic-collectives C++ API in local toolkit | **ABSENT** (toolkit 12.8 bundles CCCL 2.7; no `cuda/execution` header) | probe sections 3-4 |
| CCCL via pip (`nvidia-cuda-cccl-cu12`) | AVAILABLE up to 12.9.27, **NOT installed** (no named gap requires it; license file not inspected because not installed) | probe section 6 |
| warp 1.17.0 deterministic mode | **PRESENT and usable from Python**: `wp.DeterministicMode` = {NOT_GUARANTEED:0 (default), RUN_TO_RUN:1, GPU_TO_GPU:2}; `wp.config.deterministic`, `wp.config.deterministic_max_records`, `wp.config.deterministic_debug`; implementation `warp/native/deterministic.h`, SPDX Apache-2.0 (NVIDIA), NVRTC-compatible (no nvcc needed); mechanism: supported atomics redirected to temp buffers, 64-bit radix sort by (dest_index, thread_id), fixed-order reduction; counter atomics prefix-scanned | probe sections 7-8; wheel source |
| newton 1.6.0 deterministic contact reduction | PRESENT: `GlobalContactReducer` packing modes fast (default) vs deterministic (geometry fingerprint tiebreaker) in `newton/_src/geometry/contact_reduction_global.py`; not wired into SolverXPBD by source inspection (solver-level determinism is measured, not assumed) | wheel source |

**Verdict: no adoption/install is required.** The named need (deterministic float
accumulation reachable from the pinned Python env) is already filled by warp 1.17.0's
built-in deterministic mode, whose three-level guarantee ladder mirrors CCCL's
`cuda::execution::determinism` semantics. CCCL C++ headers would be adopted only if a
Phase B boundary finding shows a scene op outside warp's supported set AND a C++ path
is named — that would be a prereg amendment committed by the Lieutenant first.

## 2. Harness design

Scripts (sha256, all syntax-checked with `python -m py_compile`; **no arm has been
executed**):

| Script | sha256 | Role |
|---|---|---|
| `scripts/dcommon.py` | `04df6c548479e958cb9b6bfcf05c7ae95e29f98edff086a3ecc6b68d8145a83c` | shared harness, canonical-JSON receipts + sidecars |
| `scripts/d1_microben_determinism.py` | `879d1933a325a5bb399bb8794a796aaf949c47af87b84f22ddde969ca2b7731d` | library-level microbenchmark |
| `scripts/d2_wholerun_determinism.py` | `b76169f32bff32720b07c1fd6e81d537acbcdfac378c4010636d429abf48d1e8` | whole-run verification |
| `scripts/dcompare.py` | `bec7650e1fa14c315deba8a0cfc59fa1881e51637a7438f36409c8cbabf63433` | receipt comparison (local CPU, read-only) |

### 2a. d1 — library-level microbenchmark (per process invocation)

- Mode fixed per invocation; `wp.config.deterministic` set BEFORE kernel module
  creation (warp contract, `warp/config.py` docstring).
- Arms, all on identical deterministic source inputs (65536 values):
  - `atomic_f64`: 65536 threads scatter-add float64 into 4096 shared slots via
    `wp.atomic_add` — the warp/newton accumulation pattern.
  - `atomic_f32`: same in float32 — declared boundary probe; a mode/dtype
    rejection is recorded verbatim as a named finding.
  - `control_fixed_f64`: one thread per slot, fixed index-order sum, no atomics —
    invariance control.
- Per arm, 5 in-process repeats: destination zeroed, 100 accumulation launches,
  sha256 of readback bytes, per-launch wall time. Device memory via warp mempool
  used/high before/after; host peak via GetProcessMemoryInfo (recorded verbatim on
  the known mailbox-runner failure).
- Receipt: canonical JSON + sha256 sidecar in `receipts/`.

### 2b. d2 — whole-run verification (the acceptance-relevant arm)

- Scene: wk-newton-install b2 recipe verbatim (base + 3-link revolute chain,
  SolverXPBD, DT=1/120, 4 substeps x 60 iters; settle 120 frames at 0 rad, drive
  240 frames at 0.5 rad) — proven stable on this host (receipt
  `2-wk-newton-install-b2-articulation`: 0.479/0.474/0.492 rad tracked vs 0.5).
- Per-tick chained digest over resident-state readbacks
  (`body_q`, `body_qd` bytes): `h_t = sha256(h_{t-1} + block_bytes)`, seeded with
  the canonical scene recipe; checkpoints every 60 ticks;
  `whole_run_sha256 = sha256(h_last + final state bytes)`.
- Library-level determinism does NOT replace whole-run verification: d1 proves a
  kernel pattern bit-stable; d2 proves the actual pipeline (newton solver
  internals, module codegen order, allocator behavior, async launches) reproduces
  whole-run bytes. **Only d2 carries the determinism acceptance verdict.**

## 3. Declared predictions and tolerances

Bit-identity is the criterion everywhere; tolerance is 0 (exact bytes), never
epsilon. "Vary" arms have no numeric tolerance; observed divergence is recorded.

| # | Prediction (per device, same binary, same inputs) | Expected | Falsified when |
|---|---|---|---|
| P1 | d1 `control_fixed_f64` repeat hashes (5 in-process repeats, any mode) | bit-identical | any repeat hash differs |
| P2 | d1 `atomic_f64` under `not_guaranteed` (current path): cross-invocation hashes | MAY differ (scheduling-order float add is non-associative); a mismatch is a measurement confirming nondeterminism, not a failure | — (if it is bit-identical, that is recorded as an observation, not claimed as a guarantee) |
| P3 | d1 `atomic_f64` under `run_to_run`: repeats AND cross-invocation hashes | bit-identical (warp RUN_TO_RUN contract, same GPU arch) | any hash differs |
| P4 | d1 `atomic_f32` under `run_to_run`/`gpu_to_gpu` | bit-identical; if the mode/dtype is rejected at module creation/launch, the rejection is a named boundary finding | silent acceptance cannot occur; a recorded rejection only falsifies "f32 supported under this mode" |
| P5 | d2 whole-run under `not_guaranteed`, two separate process invocations (R1, R2) | MAY diverge; first divergent checkpoint tick recorded | — (same note as P2) |
| P6 | d2 whole-run under `run_to_run`, >= 2 separate invocations | bit-identical `whole_run_sha256` AND identical checkpoints | any checkpoint or whole-run hash differs |
| P7 | d2 physics sanity (all modes): joint2 tracks 0.5 rad within b2's 0.15 rad band | inside band | outside band (scene broken; determinism numbers then invalid for acceptance) |
| P8 | d2 `cpu` device vs `cuda:0` hashes | expected to DIFFER (different codegen); cross-device identity is NOT claimed; warp `gpu_to_gpu` cross-ARCH identity is UNTESTABLE here (single 4090) and is declared out of scope | — |

Speed/memory expectations (recorded, not gates): d2 `not_guaranteed` stepping is
expected near b2's 18.66 ms/frame; the deterministic arm pays sort+reduce per
atomic site and is expected slower — if > 5x slower, that is recorded as a
performance finding for the adoption decision. d1 deterministic arms pay extra
device memory for scatter buffers (bounded by records-per-launch x value size,
`deterministic_max_records=0` -> codegen lower bound); mempool delta is recorded.

## 4. Failure preservation

- A hash mismatch is a recorded finding: both hashes, the arm, the mode, and (d2)
  the first divergent checkpoint tick go into the receipt verbatim. **No rerun to
  make it pass.** Any further observation is a separately declared amendment
  committed by the Lieutenant before it runs.
- Kernel/module exceptions (mode or dtype unsupported) are recorded verbatim in a
  FAILED receipt by the run wrapper — that receipt is evidence, not noise.
- The `gpu_to_gpu` level: this host has one GPU, so cross-arch identity is declared
  untestable; nothing may be claimed about it from this lane.

## 5. Phase B execution plan (gated on the Lieutenant's pin SHA)

1. GPU work through the mailbox queue ONLY (`E:/ChimeraWork/gpu-queue/PROTOCOL.md`):
   one job per mode/tag invocation, non-interactive, bounded timeout, outputs to
   `receipts/`, per-output sha256 by the worker.
   Matrix (d1): {cuda:0} x {not_guaranteed, run_to_run, gpu_to_gpu} x 5
   invocations, plus {cpu} x {run_to_run} x 2 (local, CPU-legal).
   Matrix (d2): {cuda:0} x {not_guaranteed (R1, R2), run_to_run (R1, R2)} x 2,
   plus {cpu} x {run_to_run} x 2 (local, CPU-legal).
2. `dcompare.py` over each matrix; comparison outputs appended to
   `EVIDENCE.md` with sha256 of every receipt.
3. Runtime warp/toolchain identity (driver/toolkit tuples, device arch) recorded
   from the d1/d2 receipts into `EVIDENCE.md` (my executables' live report).
4. Refinement checks ONLY as declared here: d1 repeats within process;
   cross-invocation comparisons; nothing else. New probes need an amendment
   commit first.
5. Receipts/evidence anchored through the existing `anchor.py` into the sealed
   evidence store before registry reference.

## 6. Explicitly not yet done (truth inventory)

- No d1 or d2 arm has been executed anywhere (scripts are py_compile-only).
- No GPU job has been submitted by this lane.
- warp's runtime CUDA driver/toolkit report has not been re-observed this session.
- `gpu_to_gpu` bit-identity is untestable on this single-GPU host.
- CCCL pip wheel license content: not inspected (wheel not installed; no named gap).
- The prereg itself is an uncommitted draft; no pin SHA exists yet.
