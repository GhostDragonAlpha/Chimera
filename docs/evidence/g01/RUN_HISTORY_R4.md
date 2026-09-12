# RUN_HISTORY_R4 — G01-R4 (dimensional consistency + honest convergence), 2026-09-07

Scope (ASTRA's assignment): (1) fix the R3 mobility's unit error and derive
the dimensionally consistent update; (2) separate stopping outcomes with
free-DOF stationarity; (3) audit every constant as an algorithm choice;
(4) preregister and pass the six R4 falsifiers; (5) return the handoff.
R3 source and evidence SNAPSHOTTED BEFORE CHANGES
(docs/evidence/g01/r3_snapshot/, 9 files + SHA256SUMS.txt). Big Pickle
publishes; this worker made no commits, pushes, engine control, or
protected-directory writes. Historical evidence untouched
(surface_energy_checks_results.json = cfe48cb1... verified after all runs).

## Order of work (record before pivot)

1. Adopted ASTRA's audit AS A CORRECTION: min_edge^2/gamma_max is wu^4/J,
   not wu^2/J. Noted WHY three green R3 batteries missed it: at unit scale
   min_edge ~ 1 so the numeric value equals 1/gamma_max, and the step-scale
   guard rescales every first trial -- a dimensional error invisible to
   unit-scale fixtures. Preregistered R4-U1..U4 (units, taxonomy, audit,
   falsifiers) in report section 9-R4 BEFORE the rewrite.
2. Rewrote overdamped_descent.py:
   - P = 1/gamma_max [wu^2/J] (dimensionally exact); full units table in
     the docstring; gamma_max = 0 handled BEFORE division (F == 0 exactly
     => stationary, zero steps, no P computed);
   - step parameter alpha DIMENSIONLESS (x+ = x + alpha*P*F); the 'dt'
     notation retired everywhere -- no time variable exists in the module;
   - FIVE stopping states: stationary (free-DOF residual <=
     1e-12*scene_scale) / stagnated (machine-scale decrease WITHOUT
     residual pass) / step_limit / no_descent_step / invalid_surface;
     pinned vertices excluded from the residual BY CONSTRUCTION; reaction
     forces reported for the FINAL geometry;
   - pin-list validation (range/repeat refusals); constants audit dict
     attached to every result ("numerical_algorithm_choices_not_physical_
     constants" + the seven values).
3. Battery results, in order, each failure recorded before its fix:
   - Run 1 (smoke): bumped patch ends STAGNATED with residual 2.05e-7 --
     the honest split working: R3 would have called this 'converged'.
     Flat patch STATIONARY (residual exactly 0.0); dome STATIONARY.
   - Run 2: 9/13. (a) r3_no_descent_step_budget: leftover mobility= kwarg
     (R3 API remnant) -- fixed. (b) r4a FAIL was MY CONVERSION ARITHMETIC:
     U = gamma*A with gamma_cm = gamma_wu/SCALE^2 and A_cm = A_wu*SCALE^2
     CANCELS -- energies are numerically equal across units; the first
     draft multiplied by SCALE^2. Shape agreement was already 6.7e-15.
     (c) r4b: two findings -- the deep-tail re-run honestly ends
     'stagnated' (residual 1.74e-7 > tol 4e-12; the taxonomy REFUSES to
     call it equilibrium), and reaction_forces was an INITIAL-state
     snapshot (real defect; now reported for the FINAL geometry).
     Amendment recorded in the check's registration BEFORE the rerun.
   - Run 3: 11/13. (d) r3_fixed_vertices_bitexact: the NEW pin-repeat
     validation refused the R3 fixture -- boundary[0] == 0 duplicated a
     pin; the R4 validation caught on first use an ambiguity the R3 code
     silently accepted. Fixture de-duplicated. (e) r4b: my 'balance'
     identity was PHYSICALLY WRONG: sum(F_all) + sum(reaction) = 0 reduces
     (via sum(F_all) = 0, the invariance law) to sum(F_pinned) = 0, which
     is false except at true stationarity -- the run measured the tail's
     free-DOF disequilibrium and called it imbalance. Corrected semantics:
     reaction[i] = -F(pinned, final) (the pin's APPLIED force); the
     always-true law is sum(F_all) = 0; at true stationarity NET pin load
     vanishes while individual boundary pins carry local tension.
     Registered correction before the rerun.
   - Run 4: **13/13 PASS**. Legacy batteries re-run under the new law:
     surface 8/8, contract 16/16 (unique stamped outputs; historical file
     byte-identical after ALL runs).
4. GPU handoff amended: preconditioner corrected to 1/gamma_max with the
   dated retraction; dimensionless alpha; five-state taxonomy; free-DOF
   stationarity + reactions. The FALSIFIER battery bullet (7 checks) is
   now stale (13 checks) -- corrected in the same edit pass: see handoff.

## Constants audit (R4-U3 -- stated, not retuned)

ARMIJO_C1 1e-4, BACKTRACK_FACTOR 0.5, MAX_BACKTRACKS 50, GUARD_FRAC 1e-3
(demoted R2/R3 bound, initial trial-scale cap only), RESIDUAL_TOL_FRAC
1e-12, STAGNATION_FRAC 8 (f64-derived), DEFAULT_MAX_STEPS 200. All are
NUMERICAL ALGORITHM CHOICES; none is presented as a physical constant;
none was changed to make a fixture pass (the two failing fixtures were
fixed by correcting the FIXTURE/CHECK, never the constant).

## New raw records (agent_logs/glm_foundation_g01/, unique stamped)

overdamped_descent_checks_results_20260907T041916.988123Z.json (13/13),
surface_energy_checks_results_20260907T041927.107608Z.json (8/8),
material_contract_checks_results_20260907T041927.354618Z.json (16/16).
Earlier R4 iteration artifacts (runs 2 and 3) preserved alongside.
