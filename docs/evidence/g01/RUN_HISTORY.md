# G01 RUN HISTORY — falsifier batteries

## surface_energy_checks.py (F1..F8)

| Run | Result | Evidence preserved |
|---|---|---|
| 1 (2026-09-06, first) | **0/8 PASS** | console tail in the session record; JSON overwritten by run 3 — payload maxima quoted in REPORT §5 are from this run's JSON |
| 2 (after gather fix) | **6/8 PASS** | console tail in session record (F4 sliver accepted, F6 frame mismatch remained); JSON overwritten |
| 3 (final) | **8/8 PASS** | `surface_energy_checks_results.json` (this state) |

Failures run 1 → fixes, all documented at their code sites:
- F1/F2/F5/F7/F8: gather order bug — face-major rows reduced with
  vertex-major offsets; fixed by `flat[corner_idx]` reorder in
  `evaluate_surface` (reference, with the 2026-09-06 comment).
- F4: fixture `near_degenerate_sliver` h=1e-13 sat 5.6× ABOVE the derived
  floor (64·e·max_edge² ≈ 1.42e-14) — fixture lowered to h=1e-15. The
  reference's floor law was NOT touched.
- F3: payload-truth inversion in the summary plumbing (all four sabotages
  were detected); corrected with the payload.
- F6: check compared per-triangle-frame C against world-axes diag(4,¼);
  replaced by the frame-free law det(C) = (A_cur/A_rest)² + the
  frame-agreeing tri-0 control. No tolerance widened anywhere (limits in
  the JSON are the preregistered ones).

## material_contract_checks.py (P8a..P8j)

| Run | Result | Note |
|---|---|---|
| 1 | 8/10 | P8c/d/e: bare `MaterialProperty` bypassed validation (gate lived in `add()` only) |
| 2 (final) | **10/10** | gate moved into `MaterialProperty.__post_init__` — validation at construction |

No tolerances exist in this battery except the algebraic 512·e; none changed.
