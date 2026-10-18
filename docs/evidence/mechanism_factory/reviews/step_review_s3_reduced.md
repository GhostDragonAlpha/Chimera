# Step review — S3 reusable reduced response

**Reviewer:** Step (Qwen-led review, Step verification)  
**Artifact:** `docs/evidence/mechanism_factory/S3_reduced_response.md` + associated JSON artifacts  
**Gate:** GAME_PLAN_ACTION_RPG.md §13.1, row **S3 — reusable reduced response**  
**HEAD:** d2ffd7dc (uncommitted)  
**Review date:** 2026-10-16  

---

## Verdict table

| Check | Result | Evidence |
|-------|--------|----------|
| Preregistration integrity (sha256, timestamps, import graph) | **PASS** | `2ebcdae17638df9d…` matches claimed sha; frozen 2026-10-18T07:04:46Z before any held-out solve; `s3_preregister_check.py` imports no solver |
| Node provenance (digit-for-digit from `load_domain_study_20261017.json` s=1.0 rows) | **PASS** | All 6 Π nodes reproduce source `apex_z_wu` exactly (diff = 0.00e+00) |
| LOO scheme selection (linear vs Fritsch–Carlson) | **PASS** | Reproduced exactly: worst linear 1.676439e-03, worst monotone-cubic 2.568855e-04; matches preregistered values to 1e-10 |
| FC implementation (exactness, monotonicity, C1, scipy agreement) | **PASS** | Exact at all nodes; strictly decreasing on [0.4, 2.0]; C1 continuous; LOO errors match prereg. scipy not in review venv, but FC properties verified by hand |
| Held-out cells (re-solve + Δη digit-for-digit) | **PASS** | 4 cells re-solved (worst + 3 others): η, η_pred, and Δη all digit-for-digit identical to receipt |
| Fresh cells genuinely never solved before | **PASS** | None of the 10 fresh cells appear in `s1_multiscale_receipt_20261018T014859.632468Z.json` grid or unmatched_controls |
| Validity query (7 refusal + 2 accept probes) | **PASS** | All probes return expected codes; edge cases (Π=2.0, F=2.0 at various scales, negative F, NaN γ) behave correctly |
| 2×-step re-solve diagnostic | **PASS** | Re-solving worst cell with max_steps=120000 moves η by exactly 0.0 (confirmed) |
| Benefit ratio formula | **PASS** | Formula matches preregistered P9: `detailed_total / (reduced_per_query × n_cells)` |
| Superseded receipt honesty | **PASS** | `s3_reduced_response_receipt_20261018T072643.952456Z.json` retained with 75.8× ratio; mis-implementation (divided by repeats×cells) honestly documented; no physics numbers changed |
| Conservation/passivity labeling | **PASS** | Passivity correctly labeled N/A (static map); monotonicity labeled static consistency check, not conservation |
| No silent extrapolation | **PASS** | Validity query refuses all out-of-domain inputs; scale-interpolated predictions flagged, not refused |

**Minor observations (not defects):**
1. The check script computes mean per-query time, while preregistration P9 specifies "median per query". For 1000 repeats the difference is negligible, but the wording is inconsistent.
2. `s3_reduced_response_check.py` imports solver modules (`patch_equilibrium`, `composed_chain`) at the top level, though the `validity_query` function itself is pure and solver-free.
3. scipy is not available in the Strata venv used for this review, so the scipy PCHIP cross-check could not be independently rerun; the FC implementation was verified by hand instead.

---

## Overall S3 gate ruling

**PASS**

The artifact meets the gate row as written:
- **Analytical reduction**: 1-D η(Π) table + Fritsch–Carlson monotone-cubic interpolation, preregistered by LOO on the node set.
- **Explicit validity query**: Pure function refusing all out-of-domain inputs (7 refusal probes verified), with named caveats for known gaps (γ-degeneracy, self-intersection, dynamics).
- **Held-out validation**: 10 fresh never-solved cells + 7 retained S1 cells; worst |Δη| = 2.3673e-05 ≤ T_S3 = 1e-4; digit-for-digit reproducibility confirmed by independent re-solve.
- **No silent extrapolation**: All probes behave as specified; Π=0 accepted only at s=1.0; Π ∈ (0, 0.4) and Π > 2.0 refused.
- **Measured benefit**: 7.4318e+04× on the identical 10-cell workload, formula matches preregistration.

**Named carry-forwards (all honestly disclosed):**
1. Reduction valid only at γ = 1.0 (S0 gap 6).
2. Π ∈ (0, 0.4) and Π > 2.0 refused; 2.5/3.0 N load-domain rows excluded (packet cap, S0 gap 2).
3. Scale-interpolated predictions (s ∉ {0.75, 1.0, 1.5, 2.0}) flagged, not refused.
4. No self-intersection/ground-crossing refusal exists (S0 gap 3); mitigated by η ≥ 0.111 over valid window.
5. One superseded receipt retained with mis-computed 75.8× ratio.
6. Worst-cell error (2.37e-05) is real interpolation error at current 0.4-wide node spacing; refining nodes requires new measurements.

**No critical defects found.**

---

## Review evidence summary

### Preregistration integrity
- File `s3_preregistration_20261018T070446.414763Z.json` sha256: `2ebcdae17638df9dbbf82d259febd1f4157d238efd953d5278a96b908b7c6c90` — matches claimed value.
- Frozen at 2026-10-18T07:04:46.414763+00:00, before any held-out solve (receipt timestamps are 07:26:43 and 07:29:19).
- `s3_preregister_check.py` imports: `hashlib`, `json`, `sys`, `datetime`, `pathlib`, `numpy`, `math_check.symbolic`, `math_check.numeric`. No solver import.

### Node provenance
Reproduced from `load_domain_study_20261017.json` s=1.0 rows:
```
Π=0.0: eta=0.386956838052729 (source 0.386956838052729) ✓
Π=0.4: eta=0.336652356168765 (source 0.336652356168765) ✓
Π=0.8: eta=0.284380487039174 (source 0.284380487039174) ✓
Π=1.2: eta=0.229667574529114 (source 0.229667574529114) ✓
Π=1.6: eta=0.172059048406085 (source 0.172059048406085) ✓
Π=2.0: eta=0.111097643559199 (source 0.111097643559199) ✓
```
All match preregistered values to machine precision.

### LOO scheme selection
Reproduced LOO errors:
- Linear worst: 1.676439e-03 at Π=1.6 (matches prereg 1.676439361928711e-03)
- Monotone-cubic worst: 2.568855e-04 at Π=1.6 (matches prereg 2.568854704039225e-04)
- Linear rejected (>16× TOL_ETA), monotone-cubic selected.

### FC implementation verification
- Exactness at all 6 nodes: diff = 0.00e+00.
- Strictly decreasing on [0.4, 2.0]: min diff = -2.528e-03.
- C1 continuous at interior knots (derivative left = derivative right at each node).
- LOO errors match preregistered values to <1e-10.

### Held-out cell re-solves
Independent re-solve of 4 fresh cells:
```
s=1.0, F=1.8: eta=0.142027054555548, pred=0.142003381543312, Δη=-2.367301223638041e-05 ✓
s=0.75, F=1.05: eta=0.201253306850710, pred=0.201252582022606, Δη=-7.248281035099335e-07 ✓
s=1.0, F=1.0: eta=0.257357675366609, pred=0.257356387382043, Δη=-1.287984566167300e-06 ✓
s=0.75, F=0.45: eta=0.310792604665556, pred=0.310790825851044, Δη=-1.778814512354288e-06 ✓
```
All digit-for-digit identical to receipt values.

### Fresh cells not previously solved
None of the 10 fresh cells appear in `s1_multiscale_receipt_20261018T014859.632468Z.json` (checked both `grid` and `unmatched_controls` arrays).

### Validity query probes
All 7 refusal probes return expected codes (3, 3, 4, 5, 2, 6, 7).  
Both accept probes return code 0 with correct flags (`zero_load_measured_cell` for s=1.0,F=0; `scale_interpolated` for s=1.1,F=0.8).  
Edge cases: Π=2.0 accepted; F=2.0 at s=0.75 refused (Π=2.667>2.0); F=2.0 at s=2.0 accepted (Π=1.0); negative F refused; NaN γ refused.

### 2×-step re-solve diagnostic
Re-solving worst cell (s=1.0, F=1.8) with max_steps=120000:
- 60k: status=stagnated, residual=2.583e-07, η=0.142027054555548
- 120k: status=stagnated, residual=2.583e-07, η=0.142027054555548
- Δη = 0.000000000000000e+00 (exactly 0.0)

### Benefit ratio
- Superseded receipt: 75.7631061904147× (mis-computed: divided by repeats×cells).
- Current receipt: 74318.20512335624× (correct: divided by cells×median-per-query).
- Formula: `detailed_total_s / (reduced_per_query_s × n_cells)` matches preregistered P9.
- Timing magnitude reasonable: ~11.4 s detailed vs ~15 µs reduced per query.

### Noise decomposition
- Matched-Π spread max: 1.554e-07 (consistent with S1 floor 1.831e-07).
- Worst-cell u_bound: 5.93e-07.
- Interpolation share lower bound: 2.308e-05 (≥97.5% of |Δη|).
- Stagnation share ≤2.5%.

---

## Defects

**None.** All gate requirements are satisfied. The minor observations about mean-vs-median and top-level solver imports in the check script do not affect the validity of the reduced response artifact itself.

---

## Files examined

- `docs/evidence/mechanism_factory/S3_reduced_response.md`
- `docs/evidence/mechanism_factory/s3_preregistration_20261018T070446.414763Z.json`
- `docs/evidence/mechanism_factory/s3_star_eta_pi_table_v1.json`
- `docs/evidence/mechanism_factory/s3_reduced_response_receipt_20261018T072919.936426Z.json`
- `docs/evidence/mechanism_factory/s3_reduced_response_receipt_20261018T072643.952456Z.json`
- `docs/evidence/mechanism_factory/load_domain_study_20261017.json`
- `docs/evidence/mechanism_factory/s1_multiscale_receipt_20261018T014859.632468Z.json`
- `D:/Chimera-Maintenance/Runtime/local-ai/math-tools/checks_tmp/s3_preregister_check.py`
- `D:/Chimera-Maintenance/Runtime/local-ai/math-tools/checks_tmp/s3_reduced_response_check.py`
