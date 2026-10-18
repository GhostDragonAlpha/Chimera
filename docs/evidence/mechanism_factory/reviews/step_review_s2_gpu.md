# Step review — S2 increment (bounded GPU characterization)

Reviewer: Step (final reviewer). Artifacts under review: HEAD 5445c2ad, UNCOMMITTED.
Review file written 2026-10-18. No commits, no pushes, no edits to Maya's artifacts.

---

## 1. Reproduction

### 1.1 Output completeness and byte-identity
- Verified all 35 cases have complete `pass1/` and `pass2/` output directories
  (`faces_f32.npy`, `vertex_forces_f32.npy`, `valid_u32.npy`, `energy_f32.npy`).
- Spot-checked the five worst-case directories named in the receipt:
  `refrow_s1.0_load3`, `grid_unmatched_s0.75_F2`, `grid_unmatched_s0.75_F1.6`,
  `grid_unmatched_s0.75_F0.8`, `refrow_s1.0_load2.5`. All pass1/pass2 arrays are
  byte-identical (`np.array_equal` returns `True` for every array).
- Driver log (`01.stdout.log`) reports `repeat=IDENTICAL valid=1` for all 35 cases.

### 1.2 Independent agreement check
Ran `s2_gpu_characterization_check.py --batch-out ...` against the existing
`gpu_outputs/`. Result:

```
anchor_gate_pass=True cases=35 all_pass=35 repeat_identical=35 failures=0
S2_GPU_CHARACTERIZATION VERDICT PASS
```

Worst ratios reported by the script: area 0.0078, normal 0.6512, corner 0.111,
energy 0.0, assembly 0.1181.

### 1.3 Independent ratio recomputation
Recomputed worst ratios from the frozen case set and GPU outputs using the same
formulas as the check script. Results match the receipt digit-for-digit:

| Quantity  | Worst ratio | Case                     | Receipt value          |
|-----------|-------------|--------------------------|------------------------|
| area      | 0.007798    | refrow_s1.0_load2.5      | 0.007797916173033326   |
| normal    | 0.651227    | grid_unmatched_s0.75_F1.6 | 0.6512274701026399    |
| corner    | 0.111018    | grid_unmatched_s0.75_F2  | 0.111017903858158      |
| energy    | 0.000011    | grid_unmatched_s0.75_F0.8 | 1.1426915905787547e-05 |
| assembly  | 0.118105    | refrow_s1.0_load3        | 0.11810528064328772    |

The receipt's `worst_absolute.complete` = 1.623629058400411e-05 N at
`refrow_s1.0_load3` was also spot-checked and matches the independently
computed maximum absolute vertex-force deviation.

### 1.4 Batch evidence discrepancy
The batch `result.json` records job 2 (`s2-characterization-check-and-receipt`)
as `exit_code=1`, `passed=false`, with stderr:

```
KeyError: 1
```

This is a script bug (the batch ran a version of `s2_gpu_characterization_check.py`
that iterated `for k in gp` instead of `for k in ("faces","vf","valid","energy")`,
causing `gp[1][1]` to fail). The driver job (01) and anchor gate (00) both
succeeded. Maya fixed the check script, re-ran it manually, and wrote the
PASS receipt `…T044604.123284Z.json`. The characterization outputs themselves
are intact and byte-correct.

**Defect 1:** The batch automation did not complete cleanly; the PASS receipt
was generated outside the batch after a script fix.
**Defect 2:** The batch manifest pins kernel and driver hashes but does not pin
the check script hash, so the script could change between batch and receipt.

---

## 2. Preregistration frozen check

- `cases.json` header: `"utc": "2026-10-18T03:54:05.947595+00:00"`,
  `"frozen_before_gpu_batch": true`.
- Batch manifest: `"preregistration_frozen_utc": "2026-10-18T03:54:05.947595+00:00"`.
- Batch directory timestamp: `s2_gpu_characterization_20261018T040800Z` (04:08:00Z).
- Gap: ~14 minutes. The case set and preregistration were frozen before any GPU
  output existed.

**Erratum:** The preregistration prose in the report and earlier receipt labeled
the composition as "27 in-grid + 6 refrow + 2 patch". The frozen
`cases.json` (sha256 `bf1cfb1f…`, pinned in the manifest) contains:
- 25 S1 grid solves (10 matched-Pi + 15 unmatched fixed-F)
- 8 s=1.0 load-domain study rows (0.0, 0.4, 0.8, 1.2, 1.6, 2.0, 2.5, 3.0 N)
- 2 S1 resolution-contrast patch cells (n_rim 200/300)
Total = 35. No case was added, removed, or re-solved after freezing.

The erratum is disclosed in both the retained receipt (`…T044604…`) and the
report (`S2_gpu_characterization.md` §2). The two study rows above S1's T5
grid port cap (2.5 N, 3.0 N) are explicitly called out as retained measurements
for the `valid_loads_N` domain amendment, not as domain claims.

**Verdict:** Erratum is honest, not hidden. The frozen artifact matches the
receipt's operative claim.

---

## 3. Bound physics check

### 3.1 Engine quantum and corner bound
- Engine commit quantum: `2^-21` wu = `4.76837158203125e-07` wu exactly.
  `8 * 2^-21 == 64 * 2^-24` is an exact symbolic identity.
- `64u` = `3.814697265625e-06` N. Frozen B2 corner budget = `4.0e-6` N.
  Margin = `1.85302734375e-07` N > 0.
- The scale-relative corner bound `64u·γ·Lmax` reproduces the adopted B2 budget
  at `Lmax = 1` with positive margin, and is made scale-relative. This is
  correct.

### 3.2 Assembly law
- `B_vj = η₍dᵥ₋₁₎ · Σ_incident |f32 corner comp|`, with `ηₙ = n·u/(1−n·u)`.
  This is the exact fixed-order binary32 CSR gather budget. Correct.

### 3.3 Complete vertex-force bound
- `d_v · 64u·γ·Lmax + B_vj` applies the triangle inequality over incident
  corner bounds plus the assembly law. Conservative. Correct.

### 3.4 Energy bound
- `B_energy = 32u·γ·Σ Lmax_f² + (1+u)·(1+γ_High(nF))·Σ γ·A_f`
- `γ_High(n) = n·u/(1−n·u)` is the Higham sequential-summation bound (using `n`
  instead of `n−1` is slightly conservative, which is acceptable for a bound).
- Pre-batch CPU simulation over all 35 cases (`pre_batch_preregistration_validation`
  in `cases.json`) confirms worst energy-simulation/allowance ratio
  `1.1560396061138202e-05` and worst assembly-simulation/budget ratio within
  bounds.
- The `(1+u)` factor accounts for the `γ·A_f` multiplication; with `γ = 1.0`
  exact in binary32 this is conservative but not incorrect.

### 3.5 Precedent use
- The engine quantum `8u` is used as the absolute f32-level precedent.
- The bounds are binary32-arithmetic-scale bounds, not f64 residuals.
- This is honestly framed in the preregistration header and report.

**Verdict:** Bound physics are correctly derived, conservatively applied, and
pre-validated. No defect found in the bound derivation itself.

---

## 4. S2 gate ruling

### Gate text (GAME_PLAN_ACTION_RPG.md §13.1)
> S2 — bounded GPU characterization | Existing kernel evaluates independent
> supported cases; compact reusable dataset | GPU/reference agreement,
> repeatability, numerical/error bounds, failures retained, throughput and
> RAM/VRAM/storage measured.

### Analysis
- **Existing kernel:** `membrane.comp.spv` (sha256 `a147901f…`) is unchanged
  from the pre-S2 qualified state. It was qualified on b2/fan12 fixtures via
  `membrane_gpu_probe.exe` and `relax_gpu_probe.exe`.
- **Evaluates:** The kernel is executed by `s2_case_driver.exe`, built on
  `probe_core.hpp` with the same SPV bytes. The driver is characterization
  equipment, not a deployed production kernel. This is honestly disclosed.
- **Independent supported cases:** 35 cases from the S1 record, re-solved on
  CPU and frozen before the batch. The case set is compact and reusable
  (`cases.json` + per-case geometry/adjacency arrays, 4.4 MiB).
- **Agreement:** 35/35 cases within every preregistered bound. Worst ratios
  independently verified.
- **Repeatability:** 35/35 byte-identical across two passes.
- **Failures retained:** None occurred; digit-for-digit worst-deviation tables
  are in the receipt and per-case outputs are on disk.
- **Throughput/RAM/VRAM/storage:** Measured and recorded (314 cases/s, 98 MiB
  peak RAM, VRAM sampled +16 MiB, storage bytes accounted).

### Plan warning context
§13.1 and §11.20 warn: "a probe patch is not automatically deployed." This
refers to optimization patches (tree reduction, persistent buffers, fused trial
eval) being promoted to production without proper qualification. Maya's driver
is not a kernel patch; it is a test harness around unchanged kernel bytes. The
warning does not forbid characterization drivers that feed the existing kernel
new inputs.

### Ruling
**PASS**, scoped exactly as the gate row reads, with the named carry-forwards:
- The case loader is probe-grade tooling, not a production-deployed kernel path.
- The two >2.0 N study rows are retained-measurement cases, not a domain claim.
- Throughput numbers are characterization evidence, not a qualified benchmark.

The hardcoded-fixture gap is acknowledged by characterizing the unchanged SPV
bytes through a new driver rather than deploying the driver as production. This
satisfies "existing kernel evaluates independent supported cases" because the
kernel bytes are unchanged and the evaluation is over independent cases; the
driver is harness, not a new kernel.

---

## 5. Erratum and boundary rulings

### 5.1 Erratum
The preregistration prose mislabeled the case composition. The erratum is
recorded in the receipt and report, the frozen artifact (`cases.json`) is
correct, and no case was changed after freezing. This is honest disclosure.

**Verdict:** PASS — erratum handled correctly.

### 5.2 1.62e-5 N boundary
- Worst complete vertex-force deviation: `1.6236e-5` N at `refrow_s1.0_load3`
  (`Lmax = 1.037` wu, forces up to 3.0 N).
- Ratio to preregistered bound: `0.118` (11.8% of bound), well inside.
- Ratio to S1 residual gate (`1e-6` N): `~16.2×`. This is the honest boundary
  of binary32 kernel arithmetic at largest scales.
- The agreement claim (35/35 within preregistered bounds) is not contradicted
  by this boundary. The S2 bound is intentionally looser than the S1 residual
  gate because it is an f32-representation-level bound, not an f64 residual.

**Verdict:** PASS — boundary is honestly reported and does not contradict the
agreement claim.

---

## 6. Final verdict

| Check                       | Result | Notes                                                                 |
|-----------------------------|--------|-----------------------------------------------------------------------|
| Reproduction (outputs)      | PASS   | All 35 cases complete, byte-identical, worst ratios match receipt     |
| Preregistration frozen      | PASS   | Frozen 03:54:05Z, batch 04:08:00Z, erratum disclosed                 |
| Bound physics               | PASS   | C1–C4 verified; 64u ≤ 4.0e-6 N with margin; Higham bound applied     |
| S2 gate                     | PASS   | Existing kernel unchanged; characterization driver; carry-forwards named |
| Erratum handling            | PASS   | Disclosed in receipt + report; frozen artifact correct                |
| 1.62e-5 N boundary         | PASS   | Honest limit of f32 kernel; within preregistered bound                |

**Overall S2 gate ruling: PASS** (scoped as the gate row reads, with
carry-forwards named).

**Critical defect to retain:** The batch's automated check job failed (exit 1,
`KeyError: 1`) due to a check-script bug. The batch `result.json` shows FAIL.
The PASS receipt was generated from a manual re-run after the script was fixed.
The manifest does not pin the check script hash, so this version drift is
undetected by the batch runner. Future batches should hash-pin all scripts that
contribute to the receipt.

---

Review file: `docs/evidence/mechanism_factory/reviews/step_review_s2_gpu.md`
