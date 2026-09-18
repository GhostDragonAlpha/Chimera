# SEVEN-COORDINATE-IMPLEMENTATION — Rule-0 work record (lane/seven-coord-20260918, 2026-09-18)
Agent: GLM 5.3. Base: origin/master @ 32105f18.

## STATEMENT (theory before build — RULE 0)
The qualified `coupled_dynamics.hpp` (2-coordinate: shoulder_flexion + elbow_flexion) is frozen. The `coupled_articulation.hpp` base supports up to 7 dynamic coordinates (`names.size()<=7`). The staged ladder (2→3→5→7) requires a new `coupled_multidynamics.hpp` class that:
- Keeps stage 0 bit-exact (zero-diff on the qualified 2-coordinate path; frozen references: worst_gap 4.147475858029548e-07, drop_heat 0.06656390658451124).
- Generalizes the solver for N=3,5,7: the mass matrix, point Jacobian, joint-stop cascade (earliest-crossing / lowest-index tie), per-drive actuator stores, per-drive bisections, energy closure global.
- Compares ≤1e-12 relative to the Python oracle (`coupled_arm.py`) at packet fixture poses.

## PREDICTION (not yet measured)
- Stage 0 (frozen): passes existing native suite with zero diff on frozen references.
- Stage 1 (3): generalized 3-row solver; oracle deltas ≤1e-12 relative.
- Stage 2 (5): 5-row with joint-stop cascade; same oracle bar.
- Stage 3 (7): full lift; 7-row point Jacobian; per-drive stores; global energy closure.

## FALSIFIER (F1–F9, preregistered)
F1 — frozen path changes (bit-exact lost). F2 — stage-1 relative delta >1e-12. F3 — stage-2 joint-stop tie law wrong (lowest-index violated). F4 — stage-3 point Jacobian dimension/shape wrong. F5 — per-drive bisection does not stay within global energy closure (<1e-12). F6 — per-drive actuator store grows unbounded (battery logic broken). F7 — graph-JSON merge replay fails. F8 — evidence count deviates from 11. F9 — funnel suite fails.
All falsifiers must be named as tests before any claim; any failure kills the claim.

## MISSING ARTIFACTS (honest not-qualified list)
- Packet spec file: `docs/packets/seven_coordinate_lift_v1.md` (absent — user's instructions serve as spec).
- Packet checker: `tools/science_funnel/check_packet.py` (absent).
- Graph record: `work.dynamics.seven_coordinate_lift_packet` (absent).
- Native test suite: `tests_coupled_arm/` directory (absent — qualification uses existing `coupled_arm.py` oracle + manual native test).
- The `coupled_multidynamics.hpp` file (to be created — new, does not modify qualified `coupled_dynamics.hpp`).

## FILE PLAN (packet's plan, executed here)
- NEW: `ChimeraEngine/engine/coupled_multidynamics.hpp` (generalized N-coord solver extending the qualified 2-coord logic).
- ZERO-DIFF: `coupled_dynamics.hpp` (frozen stage-0 path untouched).
- ZERO-DIFF: `coupled_articulation.hpp` base class (capacity ≤7 already present; no change required).
- NEW: `tools/science_funnel/validation/seven_coord_20260918/receipt.json` (per-stage deltas, frozen references, falsifier outcomes, replay commands, not-qualified list).
- NEW: `tools/science_funnel/validation/seven_coord_20260918/WORK_RECORD.md` (this file).
- NEW: `reference_cases.json` extension (7-coordinate format alongside existing 2-coordinate).

## SCOPE HONESTY
No free root, no muscles, no biological claim, no GPU qualification, no engine-release claim. Only: staged ladder verification (static + native reference against Python oracle), frozen-reference preservation, falsifier tests, graph-JSON replay, evidence count pinned at 11.
