# elastic-domain-audit-01 result

Base: `0e878758aa5eb4ad8fbd98648d59a8356e41f4fe`

Audit source blob (`git hash-object`):
Historical correction source: `c5b0a3bd2747c47a2b80ee7301e05210048a2fb6`.
Final source blob: `e6049a52a61ae54c5ca1cac258ac432fd3ed79d3`.

Command:

```text
PYTHONDONTWRITEBYTECODE=1 python tools/elastic_foundation/domain_audit.py --json
negative_controls=PASS; rotation_covariance=PASS
PYTHONDONTWRITEBYTECODE=1 python tools/elastic_foundation/domain_audit.py --self-test --assert-clean
adversarial_gate_controls=PASS; exit=0
Reflection inversion-count and finite-output falsifiers, exact refusal names,
and contradictory legacy-gate rejection are included in the adversarial gate;
the stamped output is `audit-integrity.json`.
```

The corrected CPU diagnostic uses the nonzero frozen
`fixtures/v1/run_20260908T231140Z/trisingle_stretch.npz` pose:
the proper cyclic 3D rotation gives full-force covariance max `0.0`; the
`eulerian_frame` mutation breaks covariance by `0.24461757268640794` and is
retained as a known failure. Reflection gets an explicit inversion flag, while
collapsed geometry and nonpositive Young modulus get named refusals.

Compression scales `1`, `1/sqrt(3)`, and `1e-6` match the derived
`2(lambda_bar+mu_bar)e² A0` energy within `2.8e-17`. Equal-pose runs at `h`
and `2h` are unchanged, exposing the documented
`CONTRACT_CONFLICT_NOT_CERTIFIED` between Pa/metre metadata and the law's
implicit unit thickness.

All raw JSON outputs are retained in this evidence directory, including the
superseded first run and each correction run. No byte-identical snapshot of
the superseded Python source was retained; this record does not claim one.

Parent final evaluator evidence is preserved at
`E:\ChimeraWork\evidence\elastic_domain_parent_final_20260910` and reports
all five evaluator mutations rejected plus the direct CLI gate passing. Those
results are independent review evidence; this task adds no runtime claim.

Provenance is limited to the existing `DERIVATION.md` §§2–3, 6, 12 and
`GPU_HANDOFF.md` §§3–4. No law, material, fixture, tolerance, engine, GPU, or
DYAD path was changed or run.
