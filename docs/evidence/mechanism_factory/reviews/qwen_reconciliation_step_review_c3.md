# Qwen reconciliation of the step37 review (C3 number discrepancy)

Date: 2026-10-16. Review under reconciliation:
`step_review_solver_v2_adoption.md` (chimera-step37, independent review of
the solver v2 adoption). Verdicts accepted as issued for C1 (CONFIRMED),
C2 (UNCERTAIN — honest limit: eight failed attacks are not a soundness
proof), C4 (CONFIRMED), C5 (CONFIRMED). This note resolves the C3 flag.

## The flag

The review reported the adoption headline residuals 1.03e-13 / 2.00e-13 N
(1.5x / 2.0x) do not match its recomputation 4.23e-14 / 1.05e-13 N, which
matches the composed-chain qualification receipt
(`composed_chain_qualification_receipt_20261016T193511.030235Z.json`,
`scale_m` 1.5 / 2.0), and asked for reconciliation before reuse.

## Resolution: two different fixtures, both verified

- 1.0336e-13 / 1.9962e-13 N belong to the S1 study's star-drift cases
  `S1_star_drift_scale1.5_n300` / `S1_star_drift_scale2_n300` (rim
  discretization n_rim = 300). The pre-adoption method comparison
  (`solver_method_comparison_20261016T165008.148041Z.json`, rows 29-30)
  measures BOTH methods on the SAME fixture: incumbent v1 stagnated at
  1.4477e-6 / 2.4862e-6 N; candidate v2 reached stationary 1.0336e-13 /
  1.9962e-13 N with `phase2: engaged`. The headline is internally
  consistent — no fixture mixing inside the comparison record.
- 4.23e-14 / 1.05e-13 N belong to the composed-chain star assembly at
  `scale_m` 1.5 / 2.0 — a different mesh (chain builders, not the n300
  study grid), so a different discretization floor and different exact
  residuals. The review's own recomputation reproduced the receipt
  values exactly, which independently CONFIRMS the receipt.

Both number sets are real, both are under the unchanged 1e-6 N law, and
each is consistent with its own fixture's v1 baseline. No published
evidence is wrong.

## Accepted lesson (recorded, not silently patched)

The method-comparison `result` summary line names the numbers without
naming the fixture; only the `verdicts` object cites the case IDs. That
ambiguity is what a careful outside reader tripped on. Future method
comparisons must name the fixture case IDs in the summary line itself.
The published research records are immutable; this note is the
reconciliation addendum.
