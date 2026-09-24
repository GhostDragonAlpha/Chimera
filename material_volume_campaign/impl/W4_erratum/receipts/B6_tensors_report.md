# B6 REPORT — analytic tensor checks (symmetry, principal moments, parallel-axis recombination)

Campaign: material-volume 24h · worktree `E:/ChimeraWork/mvc-20260924`
(branch `material-volume-campaign-20260924`)
Target under check (READ-ONLY): `tools/material_volume_body_export.py` — contract v0.9,
per-body full inertia tensor about COM, all 9 entries, off-diagonals preserved.
Prereg (frozen before exporter execution): `prereg.md` · predictions
`prereg_predictions.json` (sha256 `9aa4147c00b2e08d3b43e229ffabae0524524a6a26eed934eeded09247dad64b`).

## 1. What was done

1. **Fixtures** (`fixtures/`, all schema-valid, admission `validation_only_admissible`,
   0 reason codes — `receipts/admission_prevalidation.json`):
   - `b6-body-unit-tetra` — single right tetra (legs 1), ρ=1000, identity authored frame,
     origin (−10,0,0). Fully hand-derived closed form.
   - `b6-body-asym` — asymmetric multi-cell: 3 tetrahedra glued face-to-face, densities
     1000/500/2000, genuinely populated off-diagonals (I_xy=−525/4, I_xz=−675/4, I_yz=−925/24),
     identity authored frame. Hand-derived, exact fractions.
   - `b6-body-rotated` — same assembly translated +100 m in x, authored frame
     `R=[[0,1,0],[0,0,1],[1,0,0]]` (exact cyclic permutation, det +1), origin (100,0,0).
     Exercises `I_body = Rᵀ I_domain R` and `com_body = Rᵀ(com_domain − origin)`.
   All fixture coordinates are integers/dyadic rationals — exact in float64.
2. **Frozen preregistration** (`prereg.md`): three check families with frozen bounds,
   falsifier, stop rule, and exact predicted tensors — written and hashed BEFORE the
   exporter was ever executed on the fixtures.
3. **Independent derivation** (`work/derive_b6.py`, exact `Fraction` arithmetic, never
   reads exporter output): per-tet covariance via two algebraically independent routes
   (barycentric monomials / centroid deviations, asserted exactly equal per cell); body
   assembly via two independent routes (cellwise parallel axis / origin second moments,
   asserted exactly equal); per-cell diag-sum identity and body trace identity asserted.
4. **External quadrature cross-check** (`receipts/quadrature_crosscheck.txt`):
   Gauss–Legendre simplex quadrature (exact for these polynomial integrands) reproduces
   the exact predictions to 7.5e-15 relative (mass 1.9e-15, COM 2.9e-15 m).
5. **Exporter executed once** (`work/material_volume_body_export.py` module copy,
   `PYTHONDONTWRITEBYTECODE=1`) → `receipts/export_report.json`: `export_status=complete`,
   `admission_status=validation_only_admitted`, no reason codes, no unassigned cells.
6. **Checks applied** (`work/verify_b6.py`) → `receipts/check_results.json`.
7. **Fired falsifier investigated and classified** (`work/selfcheck_routeC.py`,
   `receipts/selfcheck_routeC_verdict.json`) — see §4.
8. Shipped gate `tools/material_volume_body_export_checks.py` run as context: 8/8 OK
   (`receipts/official_export_checks.txt`).

## 2. Check × fixture verdict table (measured numbers)

Bounds frozen in `prereg.md` §2.

| check (frozen bound) | b6-body-unit-tetra | b6-body-asym | b6-body-rotated |
|---|---|---|---|
| A max\|I−Iᵀ\| ≤ 1e-15 | 0.0 (bit-exact) PASS | 0.0 (bit-exact) PASS | 0.0 (bit-exact) PASS |
| B max\|Im λ\| ≤ 1e-12 | 0.0 PASS | 0.0 PASS | 0.0 PASS |
| B min λ > 0 | 10.416667 PASS | 136.595676 PASS | 136.595676 PASS |
| B triangle margins λ1+λ2−λ3 / λ1+λ3−λ2 / λ2+λ3−λ1 (≥ −1e-12; >0 for solids) | 4.166667 / 16.666667 / 16.666667 PASS | 103.983405 / 169.207948 / 1997.641981 PASS | 103.983405 / 169.207947 / 1997.641981 PASS |
| B det > 0, \|det−det_pred\|/det_pred ≤ 1e-12 | 1808.449074, 1.13e-15 PASS | 155510995.370370, 2.68e-15 PASS | 155510995.370370, 9.58e-16 PASS |
| B trace rel err vs 2Σ(trJᵢ+mᵢdᵢ²) ≤ 1e-12 | 3.79e-16 PASS | 2.00e-16 PASS | 2.00e-16 PASS |
| B max\|λ_exp − λ_pred\| ≤ 1e-9 | 1.78e-15 PASS | 4.55e-13 PASS | 4.55e-13 PASS |
| B mass rel err ≤ 1e-12 | 0.0 PASS | 0.0 PASS | 0.0 PASS |
| B COM max abs err (m) ≤ 1e-12 | 0.0 PASS | 5.55e-17 PASS | 5.55e-17 PASS |
| C route B (cellwise parallel axis) rel ≤ 1e-12 | 0.0 PASS | 0.0 PASS | 0.0 PASS |
| C route C (origin 2nd moments) rel ≤ 1e-12 | 1.45e-13 PASS | 1.08e-15 PASS | **2.94e-12 FAIL (preserved — see §4)** |
| **body verdict** | **PASS** | **PASS** | **PASS with one preserved instrument-limited FAIL** |

Exporter-computed spot values (body-asym): mass 1333.3333333333333 = 4000/3 kg exact,
COM (1.375, 0.43749999999999994, 0.5625) vs exact (11/8, 7/16, 9/16) — err 5.6e-17;
I₁₁ = 189.58333333333326 vs exact 2275/12 = 189.58333333333334.
(body-rotated) COM body (0.5625, 1.375, 0.43749999999999994) vs exact (9/16, 11/8, 7/16);
frame transform exact to printed precision. (unit-tetra) diag 12.499999999999996 vs 25/2,
off 2.083333333333333 vs 25/12.

## 3. Falsifier score

12 of 13 frozen-bound cells PASS with margins of 10⁰–10⁴ (or exactly 0).
1 cell FAILed its frozen bound (route C on b6-body-rotated) — preserved below.

## 4. Fired falsifier — self-check first, then classification (preserved)

**Failing cell**: `C route_C_origin rel = 2.936e-12 > frozen 1e-12` on `b6-body-rotated`
(absolute diff 3.105e-09 kg·m²). Preserved exactly as measured in
`receipts/check_results.json`; not tuned away.

**Self-check of my derivation** (`work/selfcheck_routeC.py`,
`receipts/selfcheck_routeC_verdict.json`):
- **E1** reproduces the failing measurement (2.936e-12).
- **E2** same algebra, same float64, evaluated from a local origin (t = s0): rel 1.075e-15
  — three orders under the bound. The algebra is fine; the reference point is the problem.
- **E3** exact-Fraction route C at the domain origin matches the exported tensor to
  5.68e-14 absolute (5.4e-17 relative) and the frozen prediction to 2.27e-13. The
  mathematics is exact; `derive_b6.py` had already asserted exact route-C == cellwise
  assembly for every body.
- **E4** analytic cancellation bound for float route C at COM distance L:
  rel_err ≲ eps·3·M·L²/scale(I) = 8.63e-12 at M=1333.3 kg, L=101.378 m, scale 1057.3.
  Measured 2.94e-12 ≤ bound. The error also scales as L² across my fixtures
  (L≈10: 1.45e-13; L≈101: 2.94e-12).

**Classification**:
- B6 derivation error: **NO** (E3 exact; quadrature cross-check on record).
- Exporter defect: **NO** (route B — the actual parallel-axis recombination, an
  algebraically independent float path — matches the exporter to 0.0 relative on all
  three bodies; E3 shows the exact value equals the export; the shipped gate is 8/8 OK).
- Instrument/tolerance defect: **YES** — my prereg §2(c) derived the 1e-12 bound from
  operation count alone and ignored the conditioning of the origin-second-moment route
  for a body whose COM sits ~101 m from the domain origin, where float64 loses
  ~eps·3ML²/scale to catastrophic cancellation (W entries ~1.4e7 cancel to ~1e3).
  The frozen bound was unattainable for that instrument at that distance; the bound's
  derivation was mine, and it was wrong. The FAIL verdict stands on the record; the
  conditioned instrument (E2) and the exact instrument (E3) both PASS, and route B
  (the physically primary recombination check) PASSes bit-exactly everywhere.

## 5. Verdict

Stop rule satisfied: all 3 fixtures × {A, B, C} verdicted (13 bound cells + 3 body
verdicts). Exporter tensor output is symmetric bit-exactly, has real/positive/triangle-
valid/positive-determinant principal moments consistent with per-cell data to ≤4.6e-13
against exact predictions, and recombines independently (parallel-axis) to 0.0 relative.
One preserved instrument-limited FAIL, classified above, with the decisive exact-
arithmetic and conditioned-instrument evidence. No exporter defect found.

## 6. Integrity

```
$ git -C E:/ChimeraWork/mvc-20260924 status --porcelain -- tools Chimera/docs/matter
(empty — clean)
```
(Note: a `tools/__pycache__` created by one pre-check run without
`PYTHONDONTWRITEBYTECODE=1` was deleted; git-ignored, and re-verified empty above.
All B6 computation ran from module copies in `work/`.)

## 7. Files

- `prereg.md` — frozen preregistration (fixtures, derivations, tolerances, falsifier)
- `prereg_predictions.json` — frozen exact predictions (sha256 above)
- `fixtures/{manifest,partition,groups}.json` — inputs (sha256 in prereg §1)
- `work/derive_b6.py`, `work/verify_b6.py`, `work/selfcheck_routeC.py`, `work/material_volume*.py` (module copies)
- `receipts/admission_prevalidation.json`, `receipts/export_report.json`,
  `receipts/check_results.json`, `receipts/quadrature_crosscheck.txt`,
  `receipts/selfcheck_routeC_verdict.json`, `receipts/official_export_checks.txt`
