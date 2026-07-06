# Result Grading Rubric — Industry-Standard Criteria

The grade for a feature comes from **measuring the built result**, judged by the driving
agent against this rubric. **No runtime model dependency**: no LM Studio, no local LLM in
the gate path. Where judgment is required, the agent applies the written criteria below
and records its reasoning with the grade (`record_grade`).

## Score composition (100 points → letter)

| Weight | Category | Source of truth |
|---|---|---|
| 40 | **Correctness** — acceptance tests pass | UE Automation test results (`Automation RunTests ChimeraTests`). Headless skip ≠ pass: cap Correctness at 20/40 until tests actually run in-editor. |
| 25 | **Stability & performance budgets** | Telemetry via MCP `inspect`: no crashes/asserts in log, frame rate ≥ DSL `target_fps` (60), no unbounded actor/memory growth across a 60s soak. |
| 20 | **Design-standard conformance** (agent-judged checklist below) | Engine state + feature parameters vs. the checklist — each item is a concrete yes/no. |
| 15 | **Spec fidelity** | Built result matches the DSL block and researched parameters (names, counts, values, placements verified via telemetry queries). |

**Letters**: A ≥ 90 · B ≥ 75 · C ≥ 60 · F < 60. Gate: A/B proceed; C/F → back to research
with the grader's per-category breakdown as the study guide.

## Design-standard checklist (the 20 judged points)

Grounded in established game-development practice (MDA framework; Nielsen/Federoff game
usability heuristics; standard live-balance practice). Each item is concrete and evidenced:

1. **Feedback** (4 pts) — every player-facing action produces an observable response
   (event broadcast, log, UI hook, or state change reachable by tests).
2. **Consistency** (4 pts) — same inputs → same rules everywhere (e.g., one pricing formula,
   one standing ladder; no duplicate competing systems).
3. **Meaningful parameters** (4 pts) — every exposed tunable actually changes behavior
   (no dead fields — the CommodityData elasticity bug is the canonical fail).
4. **Fail-safety** (4 pts) — invalid input degrades gracefully, never crashes or corrupts
   (bounds-checked, clamped, FindOrAdd-not-operator[], atomic transactions).
5. **Balance sanity** (4 pts) — numbers land in playable ranges: profit routes exist but are
   bounded (price clamp 0.25x–4x), rewards exceed free-trade baseline for equivalent risk,
   no degenerate infinite-money loop reachable by tests.

## What this replaces

- LM-model research grading as the gate (research review is now an advisory pre-gate the
  agent performs itself against the Research Depth Protocol).
- Screenshot/vision as the primary verdict (now tertiary evidence at most; the
  `gate_lm_available` blocker applies only if a vision layer is explicitly requested).

## Recording

`record_grade(feature, letter, reasoning)` where reasoning = the per-category point
breakdown. The C/F retry MUST quote the lowest-scoring categories in the next research
prompt so the re-research is targeted.
