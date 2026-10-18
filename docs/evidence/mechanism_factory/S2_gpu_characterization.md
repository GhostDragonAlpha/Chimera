# S2 — Bounded GPU characterization (mechanism factory)

Gate: GAME_PLAN_ACTION_RPG.md §13.1, row **S2 — bounded GPU
characterization** ("Existing kernel evaluates independent supported
cases; compact reusable dataset"). Required evidence: GPU/reference
agreement, repeatability, numerical/error bounds, failures retained,
throughput and RAM/VRAM/storage measured.

Written 2026-10-18 by Maya. One managed exclusive `gpu_batch`
invocation; no engine C++, no published record file touched. Receipt:
`s2_gpu_characterization_receipt_20261018T044604.123284Z.json`
(an earlier same-content receipt `…T043742.241360Z.json` is superseded —
written before the erratum below was recorded). Batch evidence:
`D:/Chimera-Maintenance/Runtime/local-ai/gpu-batches/s2_gpu_characterization_20261018T040800Z/`
(manifest `s2_gpu_characterization_manifest_20261018T040800Z.json`,
copied into the batch dir as `manifest.json`). Recorded CPU bound checks:
`D:/Chimera-Maintenance/Runtime/local-ai/math-tools/results/20261017-235844-38a22dde/result.json`
(script `checks_tmp/s2_bound_derivation_check.py`, **PASS 6/6**).

---

## 1. Kernel inventory (what exists, what is qualified, what was chosen)

- **The kernel of record for the constant-γ current-area law on GPU:**
  `tools/membrane_scale_lab/membrane_gpu_probe/membrane.comp` →
  `membrane.comp.spv` (sha256 `a147901f7e22b50c…`), three stages:
  per-face evaluation, fixed-order CSR binary32 vertex gather,
  single-invocation fixed-face-order binary32 energy reduction; no
  floating-point atomics.
- **Executables that actually run it:** `membrane_gpu_probe.exe`
  (certified single-shot gate, b2 + fan12 fixtures, identity-pinned in
  `gpu-small-checks.json`), `relax_gpu_probe.exe` (GLM-RELAX-GPU-01
  relaxation gate), and — this increment — `s2_case_driver.exe`.
- **Qualification before S2:** the two frozen GLM-FREEZE fixtures (b2,
  fan12; force/energy agreement, stale-buffer detection, bounded B2
  relaxation). That qualification is fixture-scoped: **no pre-S2
  executable could load an arbitrary mesh** — fixture names were
  hardcoded. This is exactly the plan's warning in force: the probe is
  setup evidence; it closed no S gate.
- **Choice:** characterize the unchanged `membrane.comp.spv` bytes
  through a new case driver built on `probe_core.hpp` — which
  GLM-RELAX-GPU-01 extracted verbatim from `probe.cpp` *precisely so a
  second harness can drive the same machinery without touching the
  certified single-shot gate*. The driver is characterization
  equipment, **not a deployed production kernel**. Patch candidates in
  `membrane_gpu_probe_patches/` (tree reduction, persistent buffers,
  fused trial eval) were inspected and left un-deployed.
- **Honest gap named:** between "kernel qualified on two analytic
  fixtures" and "kernel qualified over the mechanism's own meshes"
  there was nothing; S2 is the measurement that fills it, and the
  driver's loader is the new (unqualified-as-production) code around
  otherwise unchanged kernel bytes.

## 2. Case set and preregistration (frozen before the GPU ran)

The compact reusable dataset was not invented: 35 cases, all re-solved
on CPU from the S1 record with the pinned law/solver bytes and each
bound to its retained apex_z within 1e-9 wu (retained n_rim=300 cell
1e-6), then frozen at **2026-10-18T03:54:05.947595+00:00** in
`docs/evidence/mechanism_factory/s2_case_set/` (cases.json
sha256 `bf1cfb1fea7c4fe4…`, pinned in the batch manifest):

- 25 S1 in-grid solves (10 matched-Pi + 15 unmatched fixed-F),
- 8 s=1.0 load-domain study rows (0.0–3.0 N),
- 2 S1 resolution-contrast patch cells (n_rim 200/300).

**ERRATUM (recorded in the receipt):** the preregistration prose
labeled this "27 in-grid solves + 6 s=1.0 rows + 2 patch cells"; the
operative frozen artifact (pinned before the batch) contains the 35
cases above. Two study rows (2.5 N, 3.0 N) sit above S1's T5 grid port
cap of 2.0 N — they are retained rows of `load_domain_study_20261017.json`
whose stated purpose is the additive `valid_loads_N` domain amendment
(residuals in the packet gate), used as-is; no new physics, no case
added or removed after freezing.

**Preregistered agreement model** (full text in the frozen header of
`checks_tmp/s2_gpu_characterization_check.py`): the GPU input geometry
*is* the reference geometry — the f64 reference
(`surface_energy_reference.evaluate_surface`) is evaluated on the exact
binary32-rounded positions stored for the GPU, γ = 1.0 is exact in
binary32, adjacency is integral — so every difference is pure binary32
kernel arithmetic plus fixed-order binary32 assembly rounding. Scale
precedent: the engine's own commit quantum 2⁻²¹ wu = 8u = 4.768e-7 wu
(u = 2⁻²⁴). Per-case bounds: area 32u·Lmax²; normals 32u; corner force
64u·γ·Lmax (= the frozen B2 corner budget 4.0e-6 N at Lmax = 1, made
scale-relative); complete vertex force d_v·64u·γ·Lmax + B_vj with
B_vj = η₍d−1₎·Σ_incident|f32 corner| (the GLM-FREEZE assembly law);
energy 32u·γ·Σ Lmax_f² + (1+u)(1+γ_High(nF))·Σ t_f (Higham sequential
bound for the shader's fixed-order binary32 reduction). **Repeatability:
same input twice, byte-identical outputs.** **Failed-S2:** any validity
flag ≠ 1; any bound exceeded; any pass1/pass2 byte difference; anchor
gate failure; driver crash; reference not regenerating bitwise. The
energy/assembly bounds were validated **pre-batch** by CPU binary32
simulation over all 35 cases (`s2_case_set/cases.json`,
`pre_batch_preregistration_validation`), and the derivation itself is
recorded PASS 6/6 (bounds vs brute-force simulation, engine-quantum
identity, 2e4 random-sign Higham stress) at
`math-tools/results/20261017-235844-38a22dde/result.json`.

## 3. Results (one gpu_batch, 3 jobs, ~10 s wall under reservation)

- **Qualified anchor gate:** `GPU_RESULT PASS`, b2+fan12, RTX 4090 —
  kernel qualification intact inside the same batch.
- **Agreement:** **35/35 cases within every preregistered bound; zero
  failures.** Worst ratios to bound: area 0.008, corner 0.111, assembly
  0.118, normal 0.651 (worst 1.24e-6 in
  `grid_unmatched_s0.75_F1.6`), energy 1.1e-5 (worst 1.63e-4 J on
  energies of 3.2–25.4 J). No case agrees at f64 level and none fails —
  the deviations are uniformly binary32-arithmetic-scale and sit well
  inside the derived bounds everywhere measured.
- **Repeatability:** 35/35 byte-identical across the two passes.
- **Boundary (the honest limit):** worst complete vertex-force
  deviation 1.62e-5 N at `refrow_s1.0_load3` — binary32 kernel
  arithmetic alone is ~16× the packet's 1e-6 N residual gate at the
  largest scales (Lmax up to 2.13 wu, forces to 3.0 N). f32-level
  agreement is real but coarse relative to the physics gate; any future
  force-accuracy claim below ~1e-5 N needs f64 or mixed-precision
  accumulation, not this kernel as-is.
- **Throughput:** 314 cases/s (629 evals/s), per-eval 2.7–4.0 ms
  (601-vertex star: stage0 7.2 μs, stage1 46 μs, stage2 8.2 μs GPU
  time). Driver-measured host wall; not an isolated benchmark.
- **Memory:** peak process RAM 98 MiB; VRAM sampled 963→979 MiB
  (+16 MiB over kernel init; MiB-granularity machine-wide samples, not
  an exact per-process bound — the small-fixture coexistence precedent
  is not generalized to larger jobs).
- **Storage:** case set 4,395,424 B; GPU outputs 3,447,640 B; batch
  evidence 3,468,701 B; receipt 7,231 B.
- **Failures retained:** none occurred; the receipt carries the empty
  `failures` list, both passes of every case on disk, and the full
  digit-for-digit per-case worst-deviation table.

## 4. Verdict

**S2 is recordable as PASS, scoped exactly as the gate row reads:** the
existing kernel — unchanged spv bytes — evaluated 35 independent
supported cases from the compact reusable S1-derived dataset, at
preregistered binary32-level bounds justified from the f32
representation (engine commit-quantum precedent), with byte-identical
repeatability, pre-validated error bounds, measured throughput and
RAM/VRAM/storage, and the agreement boundary (1.6e-5 N complete-force
deviation vs the 1e-6 N packet gate at the largest scales) recorded as
the honest limit rather than hidden. Deferrals, explicitly carried
forward: the case loader is probe-grade tooling, not a
production-deployed kernel path; the two >2.0 N study rows are
retained-measurement cases, not a domain claim; and the throughput
numbers are characterization evidence, not a qualified benchmark.
