# Result Grading Rubric — Industry-Standard Criteria

<!-- CHIMERA-LAW -->
> **RULE 1 — DERIVE IT BEFORE YOU TRAIN IT.** A parameter sweep is an admission the derivation was
> not done. Before any run, any sweep, any "let's try N variants": trace the variables and show the
> equations close. If you are choosing a number, you broke the chain and substituted taste for a
> law. Ask what QUESTION each variant answers — if the answer is "which number is best", STOP.
> **[docs/THE_LAW.md](../../docs/THE_LAW.md)** · full method: `Chimera/docs/EXPERIMENTAL_METHOD.md`
> · enforced by `python tools/training_gate.py`
<!-- CHIMERA-LAW -->

**Principle: research writes the exam; the built game takes it.** Research output = the
declared acceptance criteria (the coverage denominator). The grading agent never declares
or shrinks the exam at grading time.

**The grade is the system's preliminary measurement — automated observation (sleepwalker simulations + telemetry + result grading) is the
true collapse** (Generation Protocol). A/B advances a feature to `verified` and stages it
in the Observation queue; automated observation evidence (a simtest attribution) makes it `observed` (truly
done), and an automated `rejected` reopens it regardless of the grade (a human sentence may still redirect it), with that evidence
as first-priority study material. Canonical example: Ground_Sand_Particles scored an
honest B 79.3 on its declared criteria while visibly being a white fountain, not sand —
exactly the gap automated observation exists to catch.

The grade for a feature comes from **measuring the built result**, judged by the driving
agent against this rubric. **No runtime model dependency**: no LM Studio, no local LLM in
the gate path. Where judgment is required, the agent applies the written criteria below
and records its reasoning with the grade (`record_grade`).

## Score composition (100 points → letter)

| Weight | Category | Source of truth |
|---|---|---|
| 40 | **Correctness** — acceptance tests pass | UE Automation test results (`Automation RunTests ChimeraTests`). Score = pass_rate × **coverage** (tests executed ÷ declared acceptance criteria) × 40 — one passing test of three declared criteria earns 13/40, never 40/40. Headless skip ≠ pass (cap 20/40). Every feature MUST declare its acceptance criteria count. |
| 25 | **Stability & performance budgets** | Telemetry via MCP `inspect`: crash-free log (12 pts), frame rate ≥ DSL `target_fps` 60 (5 pts), no unbounded actor growth (4 pts, via get_performance_stats), no unbounded memory growth (4 pts, via get_memory_stats <10% delta). |
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

## Frame Audit (mandatory before declaring any phase/design complete)

History shows agents optimize inside the handed frame; every frame-level error in this
project was caught by the human. Before claiming done, answer these OUT LOUD in the
Post-Flight record:
1. What is being measured vs. what actually matters? (proxy vs. target)
2. Who judges the judge — is the author grading its own work anywhere?
3. Are we fixing the artifact, or the machine that generates the artifact?
4. What would look good while being wrong?

## Recording

`record_grade(feature, letter, reasoning)` where reasoning = the per-category point
breakdown. The C/F retry MUST quote the lowest-scoring categories in the next research
prompt so the re-research is targeted.
