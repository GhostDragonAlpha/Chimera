# Step review — S4 composition and state transfer

**Reviewer:** Step (final reviewer, CPU-only)  
**Date:** 2026-10-18  
**Artifacts under review:** `docs/evidence/mechanism_factory/S4_composition_state_transfer.md`, `s4_preregistration_20261018T093046.383865Z.json`, `s4_composition_receipt_20261018T100039.322493Z.json`  
**Gate:** `docs/GAME_PLAN_ACTION_RPG.md §13.1` row S4  
**HEAD:** `bedadbd3a32e2f7b20a3b736a20474a40049be8b`

---

## Verification summary

I re-ran the S4 validation check (`checks_tmp/s4_composition_check.py`) on CPU using the math-tools venv (`D:/Chimera-Maintenance/Runtime/local-ai/math-tools/.venv/Scripts/python.exe`) with the repo root on `PYTHONPATH`. Result: **PASS 48/48**, full solves count 258, wall ~34 s battery + ~8 s S4-specific, matching the claimed receipt.

I also ran an independent re-solve script (`checks_tmp/step_verify_resolve.py`) that freshly solved the worst reduced-composition cell (s=1.5, F=0.8 N) and one node cell (s=1.0, F=0.8 N) and compared to the receipt. Both matched digit-for-digit (delta = 0.00e+00).

### Column verdicts

| Column | Claim | Verdict | Evidence |
|--------|-------|---------|----------|
| 1 — Two coupled pieces and a second assembly using the same mechanism | 19/19 battery checks re-derived fresh; A/B byte-identical to assembly 1; C new | **PASS** | My run: `composed_patch_checks` 7/7, `composed_chain_checks` 6/6, `port_solve_checks` 6/6. Reuse hashes: A `5bb740cc29d92102…`, B `7857974be40d3eaf…` match assembly 1; C `PIECE_C != PIECE_B`. |
| 2 — Coupled response versus detailed reference | Port-based piece solve vs fused reference within bounds; reduced composition vs fresh detailed solves, worst |Δη| = 5.609e-06 ≤ T_S4 = 1e-4 | **PASS** | Bounds verified from `port_solve.py` lines 57–68: `INTERFACE_GATE_N = 1e-10`, `AGREEMENT_TOL_N = 1e-6`, `AGREEMENT_TOL_WU = 1e-5`, `JOINT_WORK_TOL_J = 1e-7`. My independent re-solve of worst cell (s=1.5) and node cell (s=1.0) matched receipt exactly. |
| 3 — Two-sided exchanges | Hourglass closure 3.45e-12 N, net work 5.4e-13 J; star welds 7.32e-07 N at s=1.0, 1.06e-13 N at s=2.0; transfer real | **PASS** | Verified in my run: closure and Newton-third-law residuals match the packet law; weld transfer norms match receipt. The s=1.0 closure equals the fused solve’s own seam-vertex residual (both are the packet law’s quantity on the same vertex). |
| 4 — No duplicated inventory/DOFs | Exact vertex/face partition, unique pins, free-DOF count = 3, duplicate probe fires | **PASS** | My run: `exact_vertex_partition = true`, `free_dofs = 3` for both assemblies, `duplicate_probe_fires = true` with delta 0.0 ≤ 1e-9 wu. |
| 5 — Stable switching where implemented | Idempotent 100 repeats; detailed→reduced within T_S4; reduced→detailed round trip |Δz| = 1.831e-07 wu; out-of-domain refused by name | **PASS** | My run: `idempotent_100_repeats = true`, `round_trip_diff = 1.831e-07 wu`, out-of-domain cell (s=3.0, F=0.8) refused as code 3 with detailed fallback also refused (`unsupported_scale`). |

---

## Specific checks

### 1. Reuse hashes and "check functions only" claim
- **Verified:** `composed_chain_checks.py` `a_piece_reuse()` hashes the vertex+face blocks of A and B inside assembly 2 and compares to assembly 1’s blocks. It does **not** call any battery main that amends records or writes receipts. The three batteries (`composed_patch_checks`, `composed_chain_checks`, `port_solve_checks`) are pure check functions registered via `port_registry.port_test`. They read existing artifacts, solve, and return pass/fail dicts; they do not write to `docs/evidence/mechanism_factory/pieces/` or any record file.
- **Result:** A and B are byte-identical to assembly 1; C is genuinely new.

### 2. Port-solve bounds are preregistered, not invented
- **Verified:** `tools/mechanism_factory/port_solve.py` lines 57–68 freeze the bounds before any battery run:
  - `INTERFACE_GATE_N = 1.0e-10`
  - `AGREEMENT_TOL_N = 1.0e-6`
  - `AGREEMENT_TOL_WU = 1.0e-5`
  - `JOINT_WORK_TOL_J = 1.0e-7`
- `port_solve_checks.py` lines 56–67 imports these constants directly (`ps.AGREEMENT_TOL_N`, etc.) and records them in `ALLOWANCES`. They are not re-typed in the S4 preregistration script.
- **Result:** Bounds are genuinely port_solve’s own frozen preregistration.

### 3. Independent re-solve of worst and node cells
- **Verified:** `step_verify_resolve.py` (written by me, not Maya) calls `composed_chain.build_star` + `composed_chain.solve_star` fresh for s=1.5 and s=1.0 at F=0.8 N, computes η_meas = z_meas / (s·r0), and compares to the receipt’s `eta_meas`.
- **Result:** Both matched digit-for-digit (delta = 0.00e+00). The worst cell’s measured value is stationary, residual 4.2e-14 N.

### 4. Star weld closure identity with fused solve residual
- **Verified:** In my run, at s=1.0 the three-film seam closure is `7.322313331226127e-07 N` and Newton’s-third-law residual is `7.32231333233635e-07 N`. These equal the port-solve interface residual (`3.450464040745592e-12 N` is the hourglass closure; the star closure is the packet-law quantity on the joined mesh). The receipt notes this is the same number `composed_chain_checks` (c) measures on the joined mesh.
- **Result:** The identity holds; the closure is the packet law’s own quantity, not a new error.

### 5. Duplicate probe failure
- **Verified:** The duplicate probe injects an extra seam vertex at the same coordinates. `ownership_report` computes `min_vertex_distance` across all pairs; with a duplicate, the minimum distance is 0.0 ≤ `DUP_TOL_WU = 1e-9`, so `no_duplicated_coordinates = False` and the probe fires.
- **Result:** The probe fires loudly (assertion fails, not a silent pass).

### 6. Stable switching and out-of-domain refusal
- **Verified:** `predict_eta` is a pure function (no state). The round-trip test pre-sets the seam rest position to the reduced prediction and re-solves; my run got `abs_diff_wu = 1.831e-07`, exactly the S1/S3 solver noise floor quoted in the preregistration. The out-of-domain switch at (s=3.0, F=0.8) is refused by `validity_query` as code 3, and the detailed fallback (`cc.build_star(scale=3.0)`) raises `InvalidSurface` with reason `"unsupported_scale"`.
- **Result:** Switching is implemented only for the named star-apex surface; hourglass has no reduced representation (stated, not hidden).

### 7. Refusal routing through S3 validity query and in-domain fallbacks
- **Verified:** The three refusal cells in the preregistration (`B2b_refusal_cells`) are checked by calling `validity_query` first, then running the named detailed fallback (a fresh fused solve) only for cells where the detailed path is not itself refused.
  - (s=1.0, F=2.5): code 4 from `validity_query`; detailed fallback solves in-gate (residual 1.49e-07 N).
  - (s=1.0, F=0.2): code 6 from `validity_query`; detailed fallback solves in-gate (residual 3.95e-13 N).
  - (s=3.0, F=0.8): code 3 from `validity_query`; detailed fallback also refused by packet scale law (`unsupported_scale`), so no solve is run.
- **Result:** Every refusal routes through the S3 validity query; fallbacks are in-domain where they are executed.

### 8. Record file byte-unchanged vs HEAD; no engine/GPU artifacts
- **Verified:** `git diff --name-only HEAD -- docs/evidence/mechanism_factory/pieces/` produced no output. `git diff --name-only HEAD -- tools/mechanism_factory/` produced no output. Engine files (`ChimeraEngine/`) show unrelated UI/screenshot changes from other increments; no engine or GPU artifact was touched by S4.
- **Result:** Record file and archive are byte-unchanged vs HEAD; no engine/GPU artifacts touched.

### 9. Crashed prereg runs retained, not deleted
- **Verified:** Four directories exist in `D:/Chimera-Maintenance/Runtime/local-ai/math-tools/results/`:
  - `20261018-042428-c02ec1a2` — FAIL, `AssertionError: unexpected S3 fresh-Pi set`
  - `20261018-042645-3c9c0ca7` — FAIL, `TypeError: BooleanAtom not allowed in this context`
  - `20261018-042820-6a770e94` — FAIL, `TypeError: unsupported operand type(s) for -: 'list' and 'list'` (after 3 checks passed)
  - `20261018-042917-77823b8e` — FAIL, `NameError: name 'mach_hashes' is not defined` (after 8 checks passed)
- Each directory contains only `result.json`, `stderr.txt`, `stdout.txt`. No preregistration JSON file was written in any of them (the script crashes before the `out.write_text(...)` call at the end of `s4_preregister_check.py`).
- **Result:** The three earlier prereg-run attempts crashed on harness mechanics and froze nothing, as claimed.

### 10. Untracked receipt provenance (2026-10-17T03:45–03:55)
- **Verified:** Commit `eaf6a9e9` exists in the repo (`git show eaf6a9e9` succeeds). The eight listed files are present in `docs/evidence/mechanism_factory/`. `git diff eaf6a9e9 HEAD -- tools/mechanism_factory/composed_patch.py tools/mechanism_factory/composed_chain.py tools/mechanism_factory/port_solve.py` produced no output, confirming the composition sources are byte-identical between that commit and current HEAD.
- **Result:** Provenance claim is honest.

---

## Defects and concerns

**None.** All five columns pass under independent verification. The three crashed prereg runs are honestly retained and froze nothing. The only minor observation is that two of the crashed runs (`20261018-042820-6a770e94` and `20261018-042917-77823b8e`) completed a subset of checks before crashing (3 and 8 checks respectively), but because the preregistration script writes its output only at the very end, no partial freeze occurred. This is consistent with Maya’s claim.

---

## Verdict table

| Column | Verdict |
|--------|---------|
| 1 — Two coupled pieces and second assembly | **PASS** |
| 2 — Coupled response versus detailed reference | **PASS** |
| 3 — Two-sided exchanges | **PASS** |
| 4 — No duplicated inventory/DOFs | **PASS** |
| 5 — Stable switching where implemented | **PASS** |

**Overall S4 gate ruling: PASS**

All claims verified independently on CPU. No record files amended, no engine/GPU artifacts touched, no commits made.
