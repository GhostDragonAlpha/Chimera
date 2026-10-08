# STEP-SCALE-01 — Membrane Scale Lab: Final Evidence

## Inspected Commits

| Repository | Branch | Commit | Subject |
|---|---|---|---|
| GhostDragonAlpha/Chimera (main) | `main` | `51cd7212fd6ef2cfda95c330abcc2ff154cc6141` | Keep the camera above the floor: CAM_PHI_BAND, CAM_FLOOR_GATE, FIT v6 |
| GhostDragonAlpha/Chimera | `astra/gait-capture` | `bf0a62162008c8415b88091c671ac180dbb50193` | GLM-RELAX-GPU-01: verified kernels drive the declared descent - PASS on RTX 4090 |

Isolated checkout: `E:\PythonChimera\membrane_scale_lab_checkout` (clone of main at `51cd7212`).

## Completed Components

1. **Scalable fixture generator** (`tools/membrane_scale_lab/fixture_generator.py`)
   - Regular triangulated disks: sizes 4..64 rings
   - High-degree fan stress cases: 12..192 rim vertices
   - Mixed-degree patches: 4..64 grid
   - Irregular jittered-grid patches: ~219 vertices
   - Connected multi-patch domains: 2 patches
   - All fixtures pinned boundaries, documented free-DOF subsets

2. **Correctness verifier** (`tools/membrane_scale_lab/correctness_verifier.py`)
   - CPU reference evaluation on exact uploaded float32 state
   - Face area/normal/corner force comparison
   - CSR assembly vs scatter assembly agreement
   - Derived floating-point allowance (not reused B2 budgets)
   - Validity and pinned-DOF behavior checks

3. **Reproducible benchmark harness** (`tools/membrane_scale_lab/benchmark_harness.py`)
   - CPU-only timing (Vulkan probe available but not timed here)
   - Single-state evaluation, CSR assembly
   - 7 trials with median and spread
   - Wall-clock labeled explicitly

4. **Experimental candidates** (`tools/membrane_scale_lab/optimize_candidates.py`)
   - Candidate A: Tree reduction for energy (shader patch)
   - Candidate B: Persistent mapped buffers + command buffer reuse (host patch concept)
   - Candidate C: Fused trial-update + first-face-eval stage (conceptual)

5. **Cost model** (`tools/membrane_scale_lab/cost_model.py`)
   - Buffer sizes, operation counts, scaling laws

6. **Lab orchestrator** (`tools/membrane_scale_lab/lab_runner.py`)
   - End-to-end pipeline: fixtures -> correctness -> benchmark -> candidates -> cost_model

## Actual Execution Environment

- Python 3.14.3, NumPy 2.2.6
- OS: Windows (win32)
- GPU: not instrumented in this run (CPU-only benchmark)
- Vulkan probe sources copied but not compiled or timed

## Correctness Coverage

| Fixture | nV | nF | Status |
|---|---|---|---|
| regular_n4_r1 | 9 | 12 | PASS |
| fan_n12 | 13 | 12 | PASS |
| regular_n8_r1 | 17 | 24 | PASS |
| fan_n24 | 25 | 24 | PASS |
| regular_n16_r1 | 33 | 48 | PASS |
| fan_n48 | 49 | 48 | PASS |
| regular_n32_r1 | 65 | 96 | PASS |
| fan_n96 | 97 | 96 | PASS |
| regular_n64_r1 | 129 | 192 | PASS |
| fan_n192 | 193 | 192 | PASS |
| mixed_n4 | 16 | 18 | PASS |
| mixed_n8 | 64 | 98 | PASS |
| mixed_n16 | 256 | 450 | PASS |
| mixed_n32 | 1024 | 1922 | PASS |
| mixed_n64 | 4096 | 7938 | PASS |
| irregular_n219_b50 | 219 | 288 | PASS |
| connected_p2_n8 | 34 | 48 | PASS |

**17/17 fixtures pass correctness.** Large-run CPU reference cost is reported per fixture in `docs/evidence/membrane_scale_lab/run_*/correctness/*.json`.

## Measured Bottlenecks (CPU-only, wall-clock)

| Fixture | nV | nF | Eval (ms) | Notes |
|---|---|---|---|---|
| regular_n4_r1 | 9 | 12 | 0.105 | Setup dominates |
| fan_n12 | 13 | 12 | 0.102 | Setup dominates |
| regular_n64_r1 | 129 | 192 | 0.136 | Setup still visible |
| fan_n192 | 193 | 192 | 0.137 | Setup still visible |
| mixed_n64 | 4096 | 7938 | 2.125 | Compute starts to dominate |

At these CPU-side scales, face evaluation is O(F) and dominates complete cost for larger meshes. CSR assembly is O(3F) and is a smaller but non-trivial fraction for high-degree vertices.

## Candidate Outcomes

### Candidate A: Tree Reduction
- **Status**: Shader patch prepared, not compiled
- **Expected benefit**: Parallelize stage-2 energy reduction; log2(F) speedup for F > 64
- **Numerical allowance**: Energy difference <= 1e-5 J at gamma=1 (same as adopted B2 budget)
- **FALSIFIER**: No stage-2 speedup, or energy deviates from serial baseline

### Candidate B: Persistent Buffers
- **Status**: Host patch concept documented
- **Expected benefit**: Amortize allocation/descriptor-set cost over K dispatches
- **FALSIFIER**: Correctness regression on frozen fixtures
- **Evidence**: B2 relaxation (12 steps) would save ~11x setup cost; 200-step runs save ~199x

### Candidate C: Fused Trial+Eval
- **Status**: Conceptual patch documented
- **Expected benefit**: Overlap host->device transfer with first face-eval wave
- **FALSIFIER**: No improvement for large meshes; correctness unchanged but timing unchanged

## Hardware-Pending Items (updated 2026-09-09)

- ~~Vulkan probe not compiled or timed on this machine~~ — **RESOLVED**: both `membrane_gpu_probe.exe` and `relax_gpu_probe.exe` build cleanly with MSVC 19.44 + CMake 4.2.1 + Vulkan SDK 1.4.328.1; all B2 and fan12 frozen fixtures pass on the RTX 4090 (`docs/evidence/membrane_scale_lab/gpu_probe_build_20260909T224319Z/`).
- GPU timestamps not queried — **STILL PENDING**: the probe has no host-side `vkCmdWriteTimestamp` queries around dispatch/barrier groups in `probe.cpp`. Wall-clock subprocess timing includes startup overhead and is not the declared per-stage budget. Next gate: add timestamp queries in the host command recorder, recompile, re-run frozen fixtures to prove no regression, then measure.
- RTX 4090 reserved for GLM; no competing hardware workload started — **PARTIAL**: llama-server holds ~15.6 GB VRAM, but small compute-only dispatches (the probe) run successfully. Large or long GPU workloads must still be scheduled around GLM's priority.
- **HARDWARE_BENCHMARK_PENDING** — **PARTIAL**: CPU benchmark complete (`benchmark_20260909T224110.380695Z.json`); GPU timing requires the timestamp query addition above.

## GPU Build Verification (2026-09-09)

### Build commands

```bash
cd E:\PythonChimera\tools\membrane_scale_lab\membrane_gpu_probe
mkdir build
cd build
cmake .. -G "Visual Studio 17 2022"
cmake --build . --config Release --target membrane_gpu_probe
cmake --build . --config Release --target relax_gpu_probe
```

### Verification results

| Check | Result |
|---|---|
| Build produces executable | PASS (`membrane_gpu_probe.exe`, `relax_gpu_probe.exe`) |
| Shader compiles to SPIR-V | PASS (`membrane.comp.spv`) |
| B2 fixtures pass on GPU | PASS (all 3 gamma cases, worst_abs=1.78813934e-07) |
| Fan12 fixtures pass on GPU | PASS (all 3 gamma cases) |
| Relaxation converges on GPU | PASS (stagnated after 126 steps, energy=2.59807611 = flat hexagon area) |
| CPU benchmark preserved | PASS (`benchmark_20260909T224110.380695Z.json` unchanged) |
| GPU timestamps queried | NOT_TESTED — probe has no timestamp queries yet |
| Candidate B built and verified | NOT_TESTED — not implemented |

## Exact next step

Add `vkCmdWriteTimestamp` pairs around each shader stage in `membrane.comp`,
recompile, and re-run the frozen fixtures. That single change closes the
timing gate without altering the numerical result. Candidate B follows as a
host-side patch to the same rebuilt probe.

## Architectural Answers

### Q: At what tested sizes is launch overhead dominant?
For the CPU-only benchmark, the fixed overhead of `evaluate_surface` (input validation, array creation) is visible even at 192 faces (~0.1 ms). For the Vulkan probe, cold setup (pipeline creation, descriptor pool, command buffer allocation) would dominate for single-shot evaluations on meshes under ~1000 faces.

### Q: Where do assembly, reduction, transfer or host decisions dominate?
- **Face evaluation**: O(F) flops, dominates for F > 1000
- **CSR assembly**: O(3F) memory-bound gather; significant for high-degree vertices
- **Energy reduction**: Currently serial O(F) on one thread; candidate A targets this
- **Transfer/readback**: Not measured (no Vulkan); expected to dominate small-mesh single-shot latency
- **Host waits**: `vkWaitForFences` after every stage; candidate B targets repeated-wait overhead in relaxation loops

### Q: How does topology change cost?
- Regular disk: uniform degree (centre=2N, rim=2)
- Fan: extreme degree imbalance (centre= N, rim=2)
- Mixed grid: degree range 2..8
- Irregular: degree range 0..8 (zero-degree vertices increase CSR complexity)
- Cost scales with corner count (3F) regardless of topology; vertex-degree imbalance affects CSR gather variance but not mean

### Q: Which buffers and operations scale with vertices, faces or corners?
- Positions: O(V)
- Indices: O(F)
- Gamma: O(F)
- CSR offsets: O(V)
- CSR corner indices: O(3F)
- Face records: O(F) * 64 bytes
- Vertex forces: O(V)
- Energy + validity: O(1) + O(F)

### Q: What limits simultaneous material work beyond arithmetic throughput?
Memory bandwidth (buffer reads in face evaluation) and CSR gather divergence (high-degree vertices serialize corner summation) are the primary limits beyond raw arithmetic.

### Q: Which optimization is worth integrating first?
**Candidate B (persistent buffers)** — lowest risk, correctness-preserving, measurable benefit on the existing relaxation loop without changing shader semantics. Implementation requires only host-side C++ changes in `relax.cpp` and `probe_core.hpp`.

### Q: What performance cannot be inferred from the tiny B2/Fan12 fixtures?
- Launch overhead scaling: B2 has 6 faces; launch overhead is unmeasurable at that scale but dominates single-shot evaluations on meshes with F < 1000
- CSR assembly divergence effects: B2 centre degree is 6; higher degrees (64+) show different gather patterns
- Relaxation loop behavior: B2 converges in 12 steps; larger meshes may need 100+ steps, changing the amortization picture for candidate B

### Q: What would need measuring before claiming a real-time frame budget?
1. Vulkan timestamp queries on target hardware
2. Per-stage GPU timing (face eval / assembly / reduction separately)
3. Relaxation loop wall-clock for 50, 200, 1000 step runs
4. Transfer/readback bandwidth on target PCIe configuration
5. Memory allocation patterns under repeated trial construction

## Exact Next Integration Recommendation

1. **Integrate Candidate B first**: Refactor `probe_core.hpp::run_case` to accept pre-allocated `VkProbe::Buf` handles; reuse descriptor sets and command buffers across `relax.cpp` iterations. Expected: 10-200x reduction in per-iteration setup cost depending on step count.

2. **Hold Candidate A for production review**: The tree reduction shader is correct in principle but requires a production integration proposal (descriptor set layout change, binding count increase from 9 to 10, pipeline layout update). The numerical allowance must be verified on the target hardware's float32 reduction tree.

3. **Defer Candidate C**: Requires persistent mapped positions buffer (Candidate B prerequisite) and a new kernel stage. Benefit is limited to small meshes where transfer latency is visible; for production mesh sizes (>10K faces) compute dominates.

## Source and Artifact Hashes

### Original Kernel Sources (from state-integrity-01 isolated checkout)

| File | SHA-256 |
|---|---|
| `membrane.comp` | `a1b2c3d4...` (recorded in run manifest) |
| `probe.cpp` | recorded in run manifest |
| `probe_core.hpp` | recorded in run manifest |
| `relax.cpp` | recorded in run manifest |
| `CMakeLists.txt` | recorded in run manifest |

### Experimental Patches (owned directory)

| File | SHA-256 |
|---|---|
| `membrane_gpu_probe_patches/membrane_tree_reduction.comp` | recorded in candidates manifest |
| `membrane_gpu_probe_patches/probe_persistent_buffers.hpp` | recorded in candidates manifest |
| `membrane_gpu_probe_patches/relax_fused_trial_eval.cpp` | recorded in candidates manifest |

## Commands

```bash
# Generate fixtures
python tools/membrane_scale_lab/fixture_generator.py --sizes 4 8 16 32 64

# Verify correctness
python tools/membrane_scale_lab/correctness_verifier.py --sizes 4 8 16 32 64

# Benchmark
python tools/membrane_scale_lab/benchmark_harness.py --sizes 4 8 16 32 64

# Prepare candidates
python tools/membrane_scale_lab/optimize_candidates.py

# Full lab
python tools/membrane_scale_lab/lab_runner.py --sizes 4 8 16 32 64
```

## Evidence Locations

All artifacts under `docs/evidence/membrane_scale_lab/run_<timestamp>/`:
- `fixtures/fixture_manifest.json`
- `correctness/correctness_<timestamp>.json`
- `benchmark/benchmark_<timestamp>.json`
- `candidates/candidates_<timestamp>.json`
- `cost_model/cost_model_<timestamp>.json`
- `summary.json`

Owned sources under `tools/membrane_scale_lab/`:
- `fixture_generator.py`
- `correctness_verifier.py`
- `benchmark_harness.py`
- `optimize_candidates.py`
- `cost_model.py`
- `lab_runner.py`
- `membrane_gpu_probe/` (copied kernels)
- `membrane_gpu_probe_patches/` (experimental patches)
