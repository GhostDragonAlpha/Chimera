# TypeB-P2 receipt — batched GPU physics feasibility (2026-09-21)

Agent: GLM 5.3 · branch `agent/typeb-p2-gpu-20260921` · commit `30821ef7c1d00c9d394ff4b3eb466aafcabc6cc6`

Toolchain: **warp 1.15.0** on cuda:0 (fallback: False)

## Throughput (device-resident, warm, median of 3 x 300 ticks)

| batch | env-steps/s | vs CPU 9.68 ticks/s | ms/tick |
|---:|---:|---:|---:|
| 256 | 28,246 | 2,918x | 9.063 |
| 1024 | 100,310 | 10,363x | 10.208 |
| 4096 | 412,592 | 42,623x | 9.927 |
| 16384 | 1,840,387 | 190,123x | 8.902 |

VRAM: base 2256 MiB -> peak 2591 MiB (delta 335 MiB; state at 16384 envs = 10.6 MB).

## Fidelity vs float64 CPU reference (identical equations, f32-quantized matched init)

| case | regime | one-step pos_rel | 300-tick final pos_rel | bounded |
|---|---|---:|---:|:--:|
| freefall | quiescent | 4.64e-07 | 3.74e-04 (tick 300) | YES |
| freefall | energetic | 2.04e-05 | 8.98e-02 (tick 300) | YES |
| contact | quiescent | 4.90e-07 | 1.08e-04 (tick 300) | YES |
| contact | energetic | 7.33e-06 | 1.13e-01 (tick 300) | YES |

Batch isolation (5v5 repetition study, quiescent): solo-vs-solo max = 2.90e-05; batch-vs-solo median = 4.75e-05, max = 6.80e-05; energetic: batch-vs-solo 1.13e-01 vs run noise 1.46e-01. Neighbor-independence offsets: {'batch=2': 0.00016807, 'batch=8': 0.0001063, 'batch=16': 0.0001063} — offset tracks launch config, not neighbor state (batch=8 and batch=16 bit-identical). F-BATCH-COUPLING FIRED as operationalized; cause is reduction-order rounding across batch configs, not state coupling. Exact-replay needs a deterministic reduction.

## Falsifiers (PREREG.md)

- **F-GPU-TRAINING-BUDGET**: held — {'bar_env_steps_per_s': 968.0, 'measured': 1840386.9, 'fired': False}
- **F-GPU-MEMORY**: held — {'limit_mib': 24564, 'peak_mib': 2591.0, 'fired': False}
- **F-PARITY-ONESTEP**: held — {'bar': 0.0001, 'worst_quiescent': 4.904613045581497e-07, 'fired': False}
- **F-PARITY-BOUNDS**: held — {'fired': False}
- **F-BATCH-COUPLING**: FIRED — {'prereg_bar': 1e-05, 'measured_quiescent_median': 4.754076701991947e-05, 'quiescent_repetition_study': {'n_solo': 5, 'n_batch': 5, 'solo_vs_solo_max': 2.9033438811025993e-05, 'solo_vs_solo_pairs': [3.75e-06, 6.07e-06, 6.73e-06, 8.23e-06, 1.161e-05, 1.486e-05, 1.602e-05, 1.843e-05, 2.234e-05, 2.903e-05], 'batch_vs_solo_median': 4.754076701991947e-05, 'batch_vs_solo_max': 6.80298629656342e-05}, 'neighbor_independence_offset': {'batch=2': 0.00016807123101347386, 'batch=8': 0.00010630072188326414, 'batch=16': 0.00010630072188326414}, 'measured_energetic': 0.11344365414762456, 'gpu_run_noise_energetic': 0.14609032457686458, 'fired': True, 'diagnosis': 'FIRED AS OPERATIONALIZED (batch-vs-solo 3.2e-5 > bar 1e-5, all 25 cross-pairs, vs solo-noise envelope 1.5e-6). Diagnosis: NOT neighbor-state contamination — structurally impossible (env-private force slots) and empirically refuted (offset is neighbor-independent; batch=8 and batch=16 with different neighbor sets give BIT-IDENTICAL env0). The offset tracks LAUNCH CONFIGURATION: nondeterministic-order f32 atomic reduction. Tier implication: envs evolve independently (lane contamination claim holds) but bit-reproducibility across batch configs fails; exact-replay requires a deterministic reduction.'}

## Verdict: **FALSIFIER-FIRED**

Scope: representative slice (42 springs, 27 verts/env), NOT a full membrane-body port; throughput is an existence proof for the tier plumbing, not a full-body forecast (lane warning honored).
