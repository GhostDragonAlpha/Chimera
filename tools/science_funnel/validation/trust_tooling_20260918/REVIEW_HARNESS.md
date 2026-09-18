# REVIEW HARNESS — validation against the Rule-0 prediction

Prediction: `--base a6e6acf2 --candidate e9c7bd5e` reproduces the statically
visible F1–F4 (briefing said F1–F6; the receipt holds F1–F4 only — discrepancy
recorded in WORK_RECORD.md); F1 at most CANNOT-VERIFY.
Falsifier: docs-only range must PASS with zero findings.

## Measured

Friction (`validation/review_e9c7bd5e/verdict.json`):
- frozen_reference PASS (6 frozen/bit-exact markers, incl. mu=0 bit-exactly).
- falsifier_as_test FINDING(MINOR): F2-shape ({0.05,0.8} without mucrit/0.6/
  travel threshold) + F3-shape (friction_cone without impact-cone and J^T
  guards), with embedded F1-shape CANNOT-VERIFY (exact-rest sign needs the
  solver seam, quote at coupled_dynamics.hpp:85).
- scope_honesty FINDING(MINOR): F4-shape (engine adds Coulomb friction, live
  scope line 69 still "No friction").
- receipt_schema PASS (no receipt in the candidate diff itself — honest
  not-applicable, not a false claim).
- evidence_count CANNOT-VERIFY (graph JSONs touched, no receipt in scope to
  pin 11 — honest, not a false MAJOR).
- graph_merge_replay PASS (no merges, no conflict markers).
- Verdict FINDINGS, exit 1.

Docs-only control (`validation/review_4b047609/verdict.json`,
a4eaf574..4b047609, handoff .zcode only):
- All 6 PASS, 0 FINDING, 0 CANNOT-VERIFY, exit 0. No invented findings.

Both locked by `tools/science_funnel/tests/test_review_candidate.py`
(3 tests). Falsifier held: no false PASS on friction, no false FINDING on
docs-only.
