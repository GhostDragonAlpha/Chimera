# RUN_HISTORY_R3 — G01-R3 (integration-law closure), 2026-09-07

Scope (ASTRA's assignment): Task 1 derive the concrete overdamped update
(mobility, units, acceptance, backtracking, termination, named refusals);
Task 2 preregister and test the law; Task 3 make evidence preservation a
runner LAW with an overwrite regression check; amended GPU handoff.
Big Pickle publishes; this worker does not commit, push, or publish.
Original G01/R2 evidence UNCHANGED (hash-verified at the end of this pass).

## Order of work (record before pivot)

1. **Preregistered D1–D7** (STATEMENT/PREDICTION/FALSIFIER) into report
   §9-R3 BEFORE any R3 code existed.
2. Implemented `tools/overdamped_descent.py`:
   - mobility M = m·I, m [wu²/J], default m = min_edge²/γ_max (derived);
   - Armijo acceptance c₁ = 1e-4 on ⟨F, m·F⟩ + the reference's own
     geometry-validity floor at every trial;
   - backtracking s ← s/2, budget 50 (declared parameter), exhaustion =
     `no_descent_step` with geometry returned unchanged;
   - termination: converged / step_limit_reached / no_descent_step /
     invalid_surface (all named).
3. First smoke run (ad-hoc, not a battery): closed octahedron shrinks
   monotonically 19.9% under the guard — correct physics (no finite
   minimum), which TAUGHT the fixture design: the healthy case must be the
   open pinned-boundary patch.
4. Task 3 first: `tools/evidence_output.py` (the shared law), wired into
   BOTH runners (surface + contract; the contract runner previously wrote
   NO raw record at all — closed by the same law). Early resolution: a
   refused run computes and writes nothing.
5. Wrote the battery. First run 6/7 → two findings, each recorded before
   its fix:
   - **Fixture falsified, not the law (D1):** the FLAT patch is already
     the discrete Plateau minimum — interior forces vanish identically
     (max interior force measured 0.0), so zero steps are accepted.
     This is handoff §6.0 correction 2 DEMONSTRATED IN CODE; registered as
     its own check (`r3_flat_patch_stationary`), and the healthy fixture
     became the BUMPED patch. Fixture amendment recorded in §9-R3 BEFORE
     the second run.
   - **Registry collision (D6 check):** importing surface_energy_checks
     re-fires its import-time `expect(8)` against this battery's
     registrations. The evidence regression now runs the REAL runner as a
     SUBPROCESS (real CLI, real exit codes) — strictly stronger.
6. Second run 6/7 → the bumped fixture needed more than 300 guard-capped
   steps (1e-3·min_edge per step, path ~0.35). Budget is a DECLARED
   parameter (the falsifier names no step count): raised to 5000 with the
   sizing derivation in the source.
7. Third run exposed the tail regime: near the minimum, Armijo accepts
   micro-steps whose decrease is float-rounding-scale; recorded energies
   can tie in the last ulps. The LAW was incomplete, not false:
   **stagnation amendment registered BEFORE implementation** — terminate
   `converged` when actual decrease ≤ 8·e·max(U,1) (derived from
   accumulation depth ~3d, d≤4 → 8× headroom; not tuned).
8. Fourth run: **7/7 PASS.**
9. Re-ran both legacy batteries under the new evidence law: **8/8** and
   **16/16**, raw records stamped-unique. Historical surface results file
   verified byte-identical after all runs (`cfe48cb1…`, both copies).
10. GPU handoff §6.0 amended (D7): the update is a mobility law; descent
    is guaranteed by the acceptance test; the old bound survives only as
    the initial trial-scale guard.

## Self-caught errors (recorded, none shipped)

- First `overdamped_descent.py` draft contained a broken leftover stub
  (`descent_step` raising NotImplementedError above the real def);
  rewritten before any run.
- First battery draft: unsafe-trial arithmetic mirrored the sliver below
  the line instead of landing on it (2h vs h — the vertex force is
  height-independent, so h lands exactly); the `no_descent_step` landing
  height was hand-typed (6e-13 mismatch = valid triangle) and is now
  fixed-point-derived from the guard's own min_edge; dead placeholder
  code removed.
- One doc edit typo'd the path (`Chagiri_G01`); retried on the real file.

## Evidence preservation compliance

- The R2 incident (runner overwrote historical results) is now
  STRUCTURALLY IMPOSSIBLE without `--force-out`: the regression check
  proves a normal run at an existing evidence path exits 2 with
  `evidence_path_exists` and the file byte-identical.
- New raw records (this pass, all under agent_logs/glm_foundation_g01/):
  overdamped_descent_checks_results_20260907T034058.619182Z.json (7/7),
  surface_energy_checks_results_20260907T034115.679194Z.json (8/8),
  material_contract_checks_results_20260907T034115.921497Z.json (16/16).
  Earlier R3 run artifacts from the fixture-debugging iterations are also
  preserved (stamped names) — raw failed runs kept per house law.
