# B4 gate-validation log (append-only)

Known-good: radius + radius_l (the artifact's own accepted case). Rule: any test the
known-good fails is a TEST defect — fix the test, not the case, record the iteration.
All iterations below occurred BEFORE any candidate ulna/ulna_l/hand_r/hand_l mapping
existed.

## Iteration 0 — protocol frozen (2026-09-24)
challenge_protocol.md written (T1–T6, tolerances, falsifiers, architect laws quoted,
amendments A1–A3 from derivation-time findings: epsilon location, two-tier
orthonormality, degenerate residual-ratio metric rejected pre-run).

## Iteration 1 — T4 failed the known-good (6.56e-01) → TEST defect, fixed (A4)
- Symptom: rebuilt L = B'·diag(S)·Bᵀ vs packet `rotation` max-abs diff 6.56e-01 on
  both radii; frame_basis and scale matched at 0.00e+00.
- Cause: the packet records the DERIVATION §5 SPLIT — `rotation` is the rigid part
  G = B'·Bᵀ, scale is S — while the preregistered body map is the full L. The test
  compared L to G (category error), the protocol text was ambiguous enough to allow it.
- Fix (A4): compare G vs `rotation`, S vs `scale`, and the landmark reconstruction
  x' = P + L(x−A) vs the packet's recorded fitted site positions (1e-6 m bound).
- Re-run: G matched at 0.00e+00 (packet tier); reconstruction error 5.6e-17 m
  (radius, 16 sites) and 1.7e-18 m (radius_l, 16 sites). T4 PASS.

## Iteration 2 — T5 failed the known-good (9 competitors) → TEST defect, fixed (A5)
- Symptom: the preregistered metric (competing owner = implied axial scale within a
  factor-2 band on the same target edge) flagged femur_r/l, tibia_r/l, humerus_r/l,
  radius_l, thorax, thorax_dummy — the known-good FAILED its own gate.
- Cause: bilateral source symmetry makes the contralateral bone's implied scale
  identical to 12 digits (s(radius_l) = 0.221706795665… == s(radius)); every body
  with a similar-length bone lands in the band. Scale similarity is not ownership
  support — the metric measured bone length, not evidence support.
- Fix (A5): PRIMARY metric = resolution-consistency count (bodies whose own
  XML-consistent resolution coincides with the DECLARED source resolutions; unique
  ownership ⇔ count == 1). FALLBACK for under-declared candidates: the factor-2
  implied-scale band, firing on ANY in-band alternative (strictly stricter than the
  old metric). Scale table retained as recorded context.
- Re-run: resolution-consistency count = 1 (radius only; radius:16==16,
  radius_l:16==16 site ownership separately verified in T1). T5 PASS.

## Iteration 3 — T6 scanner self-match + dead line (tooling, not gate substance)
- The utility-ban scanner matched its own token literals; tokens are now assembled
  from fragments so the scanner cannot self-match, and a dead line that crashed the
  script was removed. Scan result: 0 banned-evidence occurrences across scripts/.

## Final state — all six tests PASS on the known-good (see receipts/)
T1 PASS · T2 PASS · T3 PASS · T4 PASS · T5 PASS · T6 PASS
