# Independent Review: patch_equilibrium v2 Adoption Claims

Reviewer: Step (independent, read-only except this file)
Date: 2026-10-16
Target: D:/Chimera-Maintenance/PythonChimera/tools/mechanism_factory/patch_equilibrium.py (commit 912f688f adoption)

## Verdict Summary

| Claim | Verdict | Evidence |
|-------|---------|----------|
| C1: Phase 1 bit-identical on law-passing cases | CONFIRMED | Max shift 0.0 N on 4/4 tested cases (composed_patch scales 0.5/1.0/2.0, single triangle); diff shows phase 1 extracted verbatim |
| C2: Phase 2 soundness (no fake convergence, energy guard works) | UNCERTAIN | All 8 adversarial attacks failed to break phase 2 (degenerate meshes, mixed pins, horizontal loads, strong coupling, stiff systems, manufactured convergence). Attack space is large; absence of breaks is not proof of soundness |
| C3: Headline star numbers (1.5x/2.0x) | PARTIALLY CONFIRMED / PARTIALLY REFUTED | Recomputed: 4.23e-14 N (1.5x) and 1.05e-13 N (2.0x), both well below 1e-6 N law — confirming the general claim. Exact claimed values (1.03e-13 / 2.00e-13) do NOT match my recomputation; discrepancy ~2-2.5x suggests either different run conditions or claim typo |
| C4: No-equilibrium honesty (overload stays over law) | CONFIRMED | Overloaded star (10 N load): residual 4.74 N, status step_limit. Simple cantilever (100 N load): residual 100.5 N, status step_limit. Both honestly over 1e-6 N law |
| C5: Resolution ladder gap is discretization | CONFIRMED | Resolution study shows finest dz ~1.16e-5 wu = 11.6x tol_u (1e-6 wu). Ladder does NOT reach tol_u at any refinement. The "forced continuation reaches ~1e-15 N while apex_z shifts ~1e-8 wu" detail was not directly located in the evidence files examined, but the discretization conclusion is well-supported |

## Detailed Findings

### C1: Bit-identical Phase 1
- `git diff 912f688f HEAD` shows the new file extracts `_solve_v1_machinery` verbatim from the old `solve_equilibrium` body; only the phase-2 continuation is new.
- Tested 4 law-passing cases (composed_patch at 0.5x, 1.0x, 2.0x; single triangle all-pinned; single triangle loaded). All show max shift 0.0 N, status match, energy match, position match, reaction match.
- One additional case (single triangle with insufficient pins) did not pass the law under the old solver either; both versions bit-identical on it.
- Verdict: CONFIRMED. The regression guard claim (0.0 shift on 29/29 law-passing cases) is plausible; my sample is smaller but consistent.

### C2: Phase 2 Soundness Attacks
Attempted 8 adversarial attacks:
1. Near-degenerate (nearly collinear) triangle — phase 1 returns no_descent_step, residual 0.41 N, honest.
2. Mixed pins with load on vertex adjacent to pin — step_limit, residual 9.18 N, honest.
3. Horizontal load on vertically symmetric structure (moment the pins cannot resist) — step_limit, residual ~100 N, honest.
4. Strongly coupled mesh where FD-diagonal Jacobian is a poor approximation — phase 2 not engaged (budget exhausted), honest.
5. Energy guard test (load creating instability) — no energy increases observed in the step trail.
6. Residual non-increase acceptance test — no residual increases observed in the step trail.
7. Stiff system (gamma = 1e6) — step_limit, residual 0.5 N, honest.
8. Manufactured convergence test (star with 2 N load) — phase 2 not engaged (phase 1 residual 2.7e-7 N already under law), honest.

No attack produced fake convergence, energy increase beyond guard, or residual-violating "stationary" report. Verdict: UNCERTAIN (attacks failed, but the space of possible breaks is large; this is not a proof of soundness).

### C3: Headline Star Numbers
- Claimed: 1.5x → 1.03e-13 N, 2.0x → 2.00e-13 N.
- Recomputed via `composed_chain.solve_star(composed_chain.build_star(scale=s))`:
  - 1.5x: 4.229950e-14 N, status stationary
  - 2.0x: 1.053602e-13 N, status stationary
- The actual qualification receipt (`composed_chain_qualification_receipt_20261016T193511.030235Z.json`) records 4.23e-14 N and 1.05e-13 N, matching my recomputation exactly.
- The method_comparison research files claim 1.03e-13 / 2.00e-13 N, which do NOT match the receipt.
- Scientific claim (phase 2 brings these cases from ~1e-6 N to ~1e-13 N, well under law) is CONFIRMED.
- Exact numerical claim as written in the task is REFUTED by the actual evidence files.

### C4: No-Equilibrium Honesty
- Overloaded star (10 N vertical load at seam): residual 4.74 N, status step_limit — honestly over 1e-6 N law.
- Simple cantilever (100 N load at apex): residual 100.5 N, status step_limit — honestly over law.
- Both cases exhaust budget without faking convergence. Verdict: CONFIRMED.

### C5: Discretization vs Solver Slack
- Resolution study (`scale_resolution_study_20261016T142319.584Z.json`) states: "the n_rim<=300 ladder does NOT reach tol_u (finest dz ~1.16e-5 wu = 11.6x tol_u)".
- Apex ladder data shows dz_wu ~1.16e-5 wu between 200 and 300 rim rungs, confirming 11.6x gap.
- All ladder rungs stagnate at residuals 1e-9 to 1e-7, well above machine floor (~1e-15) but below the solver's stagnation trigger — the solver is not stuck at machine precision; the mesh is too coarse to represent tol_u shifts.
- The specific claim "forced continuation reaches ~1e-15 N while apex_z shifts ~1e-8 wu" was not directly located in the evidence files examined; the discretization conclusion is CONFIRMED, but that exact numeric witness is unverified here.

## Attacks Attempted (C2)
- Near-degenerate triangle (collinear vertices)
- Mixed pin sets with load adjacent to pin
- Horizontal load creating unresolvable moment
- Strongly coupled mesh (FD-diagonal Jacobian pathological)
- Energy guard stress test (unstable load)
- Residual non-increase acceptance probe
- Stiff system (gamma span 1e6)
- Manufactured convergence probe (star at 2 N load)

All failed to break phase 2. No breaks found in this session.

## Files Examined
- D:/Chimera-Maintenance/PythonChimera/tools/mechanism_factory/patch_equilibrium.py
- D:/Chimera-Maintenance/PythonChimera/tools/mechanism_factory/old_patch_equilibrium.py (git show 912f688f)
- D:/Chimera-Maintenance/PythonChimera/tools/mechanism_factory/solver_candidate.py
- D:/Chimera-Maintenance/PythonChimera/tools/mechanism_factory/composed_chain.py
- D:/Chimera-Maintenance/PythonChimera/tools/mechanism_factory/composed_patch.py
- D:/Chimera-Maintenance/PythonChimera/docs/evidence/mechanism_factory/composed_chain_qualification_receipt_20261016T193511.030235Z.json
- D:/Chimera-Maintenance/PythonChimera/docs/evidence/mechanism_factory/scale_resolution_study_20261016T142319.584Z.json
- D:/Chimera-Maintenance/PythonChimera/docs/evidence/mechanism_factory/research/method_comparison.incumbent-vs-v2-candidate.20261016T191459.083Z.json
