# Research: Regression Curator (tb-0006)

## Task Anchor
**tb-0006** Hire_Regression_Curator (DREAM_ROSTER #6)
- Footprint: `core/regression.py`, `docs/beats/**`
- Objective: Build a module that mines rejection observations from the DNA graph and converts them to permanent regression beat scripts.

## Research Sources (Disk-Based)

### Source 1: `docs/RESULT_GRADING_RUBRIC.md`
The grading rubric defines the criteria by which features are evaluated. Each rejected observation carries a context (what failed, under what conditions, which subsystem). A regression curator must preserve these rejection contexts as playable beats.

**Key fact:** The rubric's evidence schema distinguishes `tests`, `telemetry`, `checklist`, and `spec_fidelity`. Regressions must exercise at least ONE of these.

### Source 2: `core/result_grader.py`
The result_grader scores measured evidence (lines 15-22, evidence schema). When a feature grades F or C, it enters a retry loop with a study guide. The regression curator must extract the failure mode from that evidence and make it reproducible.

**Key fact:** The module records through `graphify_interface.record_grade`, tying the grade to the DNA graph. Regressions must therefore be indexable via graphify queries.

### Source 3: `docs/beats/` directory
Beat scripts (e.g., `regolith_yard.beats.json`) are the machine-playable test format. Each beat is a JSON object with `actions` (input) and `expects` (output assertion). The regression curator must emit beat JSON in this format.

**Key fact:** Beats are dispatched via `core.sleepwalker --beats <file>.beats.json`. The regression format must be dispatch-compatible.

## Acceptance Criteria (Numeric)

1. **Regression Beat Recall:** >= 95% of rejection-type observations (verdict=rejected) in the DNA graph are converted to regression beats within the curator's lifetime.
   - Measurement: `mine()` output count vs. `graphify query --kind Observation --filter verdict=rejected | wc -l`

2. **Beat Schema Validity:** 100% of emitted beat JSON must pass Sleepwalker schema validation.
   - Measurement: `python -m core.sleepwalker --validate-only <beat>.beats.json` returns exit code 0 for every generated beat.

3. **Stale Entry Pruning:** Regression beats older than 180 days are either confirmed/updated or archived.
   - Measurement: `prune(max_age_days=180)` removes or flags beats where `created_at < (now - 180d)` and no supporting evidence exists.

## Implementation Strategy
The curator must:
- Parse DNA graph nodes of kind `Observation` where `verdict == "rejected"`
- Extract failure context (subsystem, error message, conditions)
- Generate a `.beats.json` entry that reproduces the failure mode
- Index the new beat with a back-reference to the originating Observation node
- Periodically prune stale entries per a freshness law

