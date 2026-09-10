# MANIFEST.md — BP-ELASTIC-FOUNDATION, delivered 2026-09-08

Everything in this manifest is owned by `tools/elastic_foundation/` and
`docs/evidence/elastic_foundation/`. Git head at the time the battery went green:
`51cd7212fd6ef2cfda95c330abcc2ff154cc6141` (dirty worktree — expected).

## What was built

`X` = done + verified, `O` = reference-only, untouched by this task
- CPU reference membrane law (isotropic STVK, plane-stress, energy per reference area,
  rest-shape memory, sheet-level rest-derived co-rotating pullback frame): X
- falsification battery, 19/19 green: X   (`run_falsify --suffix final`, see §Battery)
- D1 material-response demo, 3 phases green: X
- frozen GPU fixtures + self-verification: X
- GPU acceptance contract: X   (`GPU_HANDOFF.md`)
- roadmap: X   (`WHAT_COMES_NEXT.md`)
- docs amendments recorded (append-only): X   (`PREREGISTRATION.md` A1–A4b, `DERIVATION.md`
  §11–§12, `AUDIT.md` §7)
- surface-energy reference (exists for calibration only): O

## Key files

    tools/elastic_foundation/
      geometry.py      rest build: sheet frame (SVD principal normal, sign-oriented to majority,
                       rest-t1 co-rotating), pullback B, CSR layout, refusals (incl.
                       NONFLAT_REST_SHEET), unit_make_grid (indexing="xy")
      materials.py     ElasticMaterial2D (E, nu, h plane-stress), library loader
      law.py           evaluate_elastic: energy, corner + vertex forces (CSR gather), refusals
      battery.py       F0–F12 + M1–M6 checks (floating placements, budgets)
      run_falsify.py   CLI: runs battery to timestamped evidence dir, exit 0 iff all green
      demo_sheet.py    D1 demo: A pinned-shear reaction, B release (conjugate-gradient,
                       optimization steps, not time), C law-contrast at the same pose
      optimizers.py    gradient_descent + conjugate_gradient (Fletcher–Reeves, Armijo)
      make_fixtures.py freeze float32 GPU fixtures (immutable, SHA-256 manifest)
      verify_fixtures.py self-check the fixtures, exit 0 iff all legs pass
      __init__.py

    docs/evidence/elastic_foundation/
      DERIVATION.md    law derivation + amendments (§11 sheet frame, §12 units)
      PREREGISTRATION.md falsifier registry F0–F12, M1–M6, D1; amendments A1–A4b
      AUDIT.md         methodology audit + §7 (stage conventions)
      GPU_HANDOFF.md   acceptance contract for the GPU stages (ONLY way to claim done)
      WHAT_COMES_NEXT.md roadmap
      fixtures/v1/…    latest run: trisingle_stretch.npz + patch_8x4_shear.npz (20 arrays
                       each), manifest.json (SHA-256 of each .npz), .verified.json
      run_*/          historical battery evidence dirs (smoke…smoke5) + demo_* dirs
                       (v1 failed on the old optimizer = real recorded history; v2/v3 green)

## How to run (verify it yourself)

    python -m tools.elastic_foundation.run_falsify --suffix final     # full battery 19/19
    python -m tools.elastic_foundation.demo_sheet --suffix check      # D1 demo, 3 phases
    python -m tools.elastic_foundation.verify_fixtures                # fixtures self-check
    python -m tools.elastic_foundation.make_fixtures                  # new fixture run (v1+)

## Named constants a GPU or future agent must NOT invent

- `ALG  = 512 · ε64` ≈ 1.137e-13 (analytic/patch budgets)
- `FD_LIMIT = 256 · ε64^(2/3)` ≈ 9.387e-9, `FD_H = ε64^(1/3)`
- `FLAT_SHEET_TOL = 1e-9`, refusal `NONFLAT_REST_SHEET`
- `EPS64 = 2.220446049250313e-16`; degeneracy floor `DEGENERACY_FLOOR_FACTOR · EPS64 · max_edge²`
- GPU float32 acceptance `TOL = 2 u1p f32` ≈ 2.384e-7 (GPU_HANDOFF.md §5)

## History / audit trail

- 2026-09-08 battery went green 16/19 → frame re-derived (sheet-level) → 19/19.
- 2026-09-08 `unit_make_grid` index bug (ij vs xy) found and fixed; patch tests now conform.
- 2026-09-08 demo phase B was slow: steepest-descent max_iter; replaced with
  conjugate-gradient (1130 iters to stationary).
- 2026-09-08 fixtures: float32 nu round-trip in the verifier was the only mismatch found;
  fixed by carrying authored doubles (`E_f64`/`nu_f64`/`h_f64`) alongside the float32 stream.

## Boundary of this delivery

- The GPU kernel itself is NOT implemented, per scope (handoff-only). GLM remains the
  publisher; no commits were pushed. The demo energy/forces play in m·Pa-style units
  (implicit unit thickness — DERIVATION.md §12).

## Worktree compensation

Everything above lives in owned dirs; nothing else in the repo was modified except through the
evidence docs listed here.