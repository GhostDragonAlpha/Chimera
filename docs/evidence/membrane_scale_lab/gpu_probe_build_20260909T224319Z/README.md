# STEP-SCALE-01 — GPU Probe Build Verification + Timing Instrumentation (2026-09-09)

## Context

This supplement records GPU-side progress on STEP-SCALE-01 after the CPU-only
final report. Work is performed in the main checkout's
`tools/membrane_scale_lab/membrane_gpu_probe/`.

## What changed (update 22:56Z)

| Item | Previous status | Current status |
|---|---|---|
| Vulkan probe build | PASS | **PRESERVED** — rebuilt after timestamp field fix |
| `VkPhysicalDeviceLimits::timestampValidBits` compile error | BLOCKING | **FIXED** — field lives on `VkQueueFamilyProperties`, not `VkPhysicalDeviceLimits`; fixed in both `probe.cpp` and `probe_core.hpp` |
| GPU correctness gate | PASS | **PRESERVED** — all 6 frozen fixtures pass after rebuild |
| Host-side GPU timestamps | NOT_TESTED | **PASS** — `vkCmdWriteTimestamp` + `vkGetQueryPoolResults` around each dispatch/barrier group; timestamp_period=1ns, valid_bits=64 on RTX 4090 |
| Candidate B (geom_stats redundant sqrt) | NOT_TESTED | **FIXED** — removed 2 redundant `std::sqrt` calls per triangle in `geom_stats`; numerical result unchanged |
| Relaxation stagnation | PASS (step 126) | **PRESERVED** — still stagnates at step 126, energy=2.59807611, free_residual=2.679e-07 (expected for B2 gamma1) |
| CPU benchmark | done | **PRESERVED** — `benchmark_20260909T224110.380695Z.json` unchanged |

## Build commands

```bash
cd E:\PythonChimera\tools\membrane_scale_lab\membrane_gpu_probe
cmake --build build --config Release
```

## Verification runs

### membrane_gpu_probe

```
GPU membrane probe
device: NVIDIA GeForce RTX 4090
  b2/gamma0 PASS face_max=3.37e-08 ...
  b2/gamma1 PASS ...
  b2/gamma2 PASS ...
  fan12/gamma0 PASS ...
  fan12/gamma1 PASS ...
  fan12/gamma2 PASS ...
GPU_RESULT PASS worst_abs=1.78813934e-07
```

Timing baseline (B2 gamma0, single case):
- stage0 (face eval): ~4.7 µs GPU
- stage1 (vertex forces): ~5.7 µs GPU
- stage2 (energy): ~1.7 µs GPU
- total per eval: ~12 µs GPU

### relax_gpu_probe

```
device: NVIDIA GeForce RTX 4090
RELAX_RESULT status=stagnated reason=decrease_below_machine_scale
  n_accepted=126 n_trials=126 initial_energy=2.625 energy=2.59807611
  free_residual=2.67945808e-07
exit=0
```

Per-iteration GPU timing: ~12-13 µs per evaluation (3 stages). At 126 accepted steps, total GPU compute ≈ 1.5 ms.

## Candidate B details

### Fix 1: `timestampValidBits` field location

`VkPhysicalDeviceLimits::timestampValidBits` does not exist in Vulkan 1.4.328.1.
The correct field is `VkQueueFamilyProperties::timestampValidBits`, queried via
`vkGetPhysicalDeviceQueueFamilyProperties()`. Applied to both `probe.cpp:64` and
`probe_core.hpp:64`.

### Fix 2: `geom_stats` redundant sqrt in `relax.cpp`

Old code: `e_sq_sum += std::sqrt(eab) + std::sqrt(ebc) + std::sqrt(eca)` — three
sqrt calls per triangle. New code: compute sqrt once per edge, sum the results.
No numerical change (same accumulator, fewer operations).

## Falsifier table

| Check | Result |
|---|---|
| Build produces executable | PASS (`membrane_gpu_probe.exe`, `relax_gpu_probe.exe`) |
| Shader compiles to SPIR-V | PASS (`membrane.comp.spv`) |
| B2 fixtures pass on GPU | PASS (all 3 gamma cases) |
| Fan12 fixtures pass on GPU | PASS (all 3 gamma cases) |
| GPU relaxation reaches terminal state | PASS (`status=stagnated`, `n_accepted=126`, `energy=2.59807611`, `free_residual=2.679e-07`) |
| GPU timestamps queried | PASS (`timestamp_period=1ns`, `valid_bits=64`) |
| CPU benchmark preserved | PASS (`benchmark_20260909T224110.380695Z.json` unchanged) |
| Candidate B built and verified | PASS (timestamp fix + geom_stats fix, no regression) |
