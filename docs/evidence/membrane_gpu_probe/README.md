# Membrane GPU probe verification

This directory records reproducible CPU/GPU numerical verification for the
standalone membrane probe. It is not engine-window, runtime, visual, DYAD, or
Alan acceptance evidence.

## Exact command

Run from the repository root:

```bash
python tools/run_membrane_verification.py
```

The runner creates a unique UTC directory below this directory and never
overwrites an existing run. It records:

- source commit and `git status`;
- Python, CMake, GLSL compiler, and C++ toolchain identity;
- raw `vulkaninfo --summary` output;
- source, executable, and shader SHA-256 hashes;
- separate CPU-reference, build, and GPU-comparison exit codes;
- concise `result.json` and `summary.md`;
- raw stdout/stderr for every command.

The runner builds under `.tmp/membrane_gpu_probe_runner/<UTC-stamp>/`, never
under `ChimeraEngine/engine/build/`. `.tmp` binaries are intentionally not
published.

## Successful local run

`20260908T030158.528749Z`:

| Check | State | Evidence |
|---|---|---|
| Frozen CPU fixture verifier | PASS | `cpu_reference.txt` |
| Probe configure/build + shader compilation | PASS | `build_configure.txt`, `build.txt` |
| Vulkan compute comparison | PASS | `gpu_comparison.txt` |
| Engine-window capture | NOT_TESTED | no scoped engine session was supplied |

Device evidence in this run reports NVIDIA GeForce RTX 4090, Vulkan 1.4.341,
and NVIDIA driver 610.47. Those are observations from the captured
`vulkaninfo` output, not inferred capabilities. The probe itself requests only
ordinary Vulkan compute functionality and does not assume CUDA extensions,
subgroups, atomics, or float64 support.

Observed maximum absolute differences in the successful run:

- face area/normal: approximately `3.94e-8`;
- face-corner force: approximately `7.68e-8`;
- complete vertex force: approximately `1.79e-7`;
- energy and validity checks: PASS;
- B2 degree-six and Fan12 degree-twelve CSR assembly checks: PASS.

Earlier failed runs remain in this directory. They include the GLSL finite-test
compile failure, the Windows MinGW DLL launch failure, and the initial host
comparison failure that incorrectly compared complete GPU force against the
assembly-only reference. Those failures were corrected without widening a
physics budget; the final run uses the separated contracts.

## Linux/WSL verification

The exact Linux command is the same command shown above, run from the
repository root:

```bash
python3 tools/run_membrane_verification.py
```

Fresh WSL2 evidence is recorded at
`20260908T044248.110251Z/`. The captured host has GCC/G++ 13.3, Python 3.12,
the Vulkan loader, Mesa ICDs, and `vulkaninfo`; it enumerates only
`llvmpipe (LLVM 20.1.2, 256 bits)`, a software Vulkan device (Vulkan 1.4.318,
Mesa 25.2.8). It does not have CMake, `glslc`/`glslangValidator`, Vulkan
development headers, or Python NumPy. Therefore the honest result is:

| Check | State |
|---|---|
| Frozen CPU fixture verifier | NOT_TESTED — NumPy missing |
| Linux probe configure/build | NOT_TESTED — CMake and shader compiler missing |
| Vulkan comparison | NOT_TESTED — no Linux executable/shader was produced |
| Engine-window capture | NOT_TESTED — no scoped session supplied |

The runner now captures missing-tool records instead of aborting, selects the
native CMake generator and executable name on Linux, and records loader/ICD
inventory. The minimum non-invasive setup for a future Linux run is a Python
environment containing NumPy, CMake, Vulkan development headers plus loader
dev files, and a GLSL-to-SPIR-V compiler such as `glslc`; an operator must
authorize any installation. No dependencies or system configuration were
changed for this run. The Windows rerun at `20260908T044310.438669Z` remains
CPU PASS, build PASS, and GPU PASS on the RTX 4090.


The shader and host use explicit storage layouts rather than relying on packed
`vec3`/`uvec3` arrays:

| Binding | Logical data | Host type | Stride |
|---:|---|---|---:|
| 0 | positions | `F4 {float x,y,z,w}` | 16 bytes |
| 1 | triangle indices | `U4 {uint x,y,z,w}` | 16 bytes |
| 2 | per-face gamma | scalar `float` | 4 bytes |
| 3 | CSR offsets | scalar `uint` | 4 bytes |
| 4 | CSR corner indices | scalar `uint` | 4 bytes |
| 5 | face records: normal+area and 3 corner forces | four `F4` values | 64 bytes |
| 6 | gathered vertex forces | `F4` | 16 bytes |
| 7 | total energy | scalar `float` | 4 bytes |
| 8 | face validity | scalar `uint` | 4 bytes |

The packed fixture inputs are `float32` positions, `uint32` indices, and
`int64` CSR arrays. The host explicitly promotes the fixture CSR values to
`uint32` and expands positions/indices to the padded 16-byte records before
upload. `static_assert` checks the host sizes; the GLSL declarations mirror the
same bindings and strides.

The force law is exactly `F_corner = -gamma * grad(A)`, with
`grad_a(A) = cross(b-c,n)/2` and cyclic permutations. No extra area or
one-third factor is applied. CSR entries are face-major flat corner IDs
`3*f + slot`, consumed in the frozen vertex-major CSR order. No floating-point
atomic scatter is used.

## Engine-window mode

The runner has an explicit manifest-only mode:

```bash
python tools/run_membrane_verification.py --engine-window path/to/scoped_session_manifest.json
```

The manifest must be created by an operator-controlled, scoped engine session
and may contain camera IDs, state IDs, and ordered capture paths. The runner
only records those fields; it never starts, stops, replaces, or POSTs to the
engine, and it never exposes the engine API publicly.
