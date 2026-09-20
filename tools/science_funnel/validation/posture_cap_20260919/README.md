# The posture-cap provenance: the biped's last hearing (2026-09-19)

Lane `buffy/posture-cap-provenance`, agent Buffy. Worktree of
`origin/buffy/gait-wave10-admissible-vault` (tip 7e0904ec). Pure derivation +
record audit; no engine files touched.

## The question

Wave 10 closed with: no reachable periodic trunk trajectory fits the combined
stance+posture envelope — worst combined ratio 1.3228 (binding node
phi=0.75), posture demand peaking 10.09 N.m under the 11.2125 N.m cap. The
cap's provenance is the softest constant in the walker: the gait-impl lane
keyed the posture drive to the HIP cap ("the same musculature carries the
trunk moment"), never deriving whether the sharing is a cap on EACH drive or
on the SUM.

## Artifacts

- `sweep_posture_cap.py` / `min_admissible_cap.json` — Task 1. Wave 10's own
  SLSQP collocation, re-run by module import with `CAP_POST` re-pinned per
  sweep point; leg demands carried as hard constraints; acceptance = constraint
  satisfaction + kinematic-residual check (not the KKT success flag). Coarse
  grids + 10-step bisections at two bounds, plus a declared downward extension.
- `provenance_receipt.py` / `provenance_receipt.json` — Task 2. Per-side
  muscle capability from the admitted muscle-path record
  (`model.creature.muscle_path_geometry`), side-aware concurrency audit, the
  two verdicts, both falsifiers, and the amendment.

## Findings

1. **The prompt's premise dissolves at ratio <= 1.0**: a stance-feasible
   witness exists DOWN TO 10.334 N.m (bracket [10.3335, 10.334]). The current
   11.2125 N.m cap is admissible; wave 10's failure was its pre-registered
   0.9 margin, not the cap.
2. **The 0.9 margin is unreachable at ANY cap in [11.2, 22.4] N.m** — the
   wall is the KNEE cap, not the posture cap (static minimum combined 0.9112
   at phi=0.85, knee ratio 0.785, posture floor -6.99 N.m). Raising the
   posture cap cannot buy wave-10's margin; raising the knee cap is a
   different (unpinned) hearing.
3. **Provenance defects banked**: (a) a rounding split — the derivation lane
   pins 1.25 x 8.9746 = 11.21825 N.m while the engine/wave 10 pin
   1.25 x 8.97 = 11.2125 N.m; (b) the sharing was never derived.
4. **Verdict (a)**: the engine realizes cap-on-EACH (independent capped PDs,
   separate stores). The records support admissibility on the witness
   architecture: same-side concurrent sums stay inside the supporting group's
   envelope at every node (worst flexion-side ratio 0.932); the theta=0
   baseline's over-nodes are the known quasi-static single-contact
   overestimates, not concurrency effects.
5. **Verdict (b)**: PCSA x sigma x cos(pennation) x moment arm gives the
   trunk-carrying pair (ILI + GMed, Oku's pinned scheme) 10.542-10.837 N.m on
   the flexion+ side — covering the price tag (10.334) and the demand peak
   (8.67, 17.8% headroom). Neither muscle alone suffices (ILI 3.92-4.01,
   GMed 6.62-6.82).
6. **Falsifier 1 (muscle closure) NOT triggered.** **Falsifier 2:
   AMENDMENT_DERIVABLE** — proposed cap 10.54 N.m (the pair's worst-side
   ceiling, rounded down), ending the borrowed hip peak and the rounding
   split. Walker-lane falsifier: re-run the walk with the amended cap and the
   wave-10 reachable table as the posture target; PASS = saturation < 10% of
   ticks and survival past tick 426.

## Boundaries kept

New directory only; derivation-lane files untouched; engine untouched.
Graph tests: `test_contracts.py` 19 passed, `test_class_contracts.py` +
`test_project_spec.py` + `test_contracts.py` 37 passed,
`test_macaque_anatomy.py` 12 passed (the graph-intake test deselected — the
pre-existing >550 s host-contention case documented by the muscle-paths
lane). `test_qs_query_semantics.py::test_query_semantics_recorded` fails on
the base commit too (verified on a throwaway worktree of 7e0904ec);
pre-existing, not this lane's.
