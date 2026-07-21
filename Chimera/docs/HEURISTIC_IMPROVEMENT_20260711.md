> **DEPRECATED** — This document describes the old approach.
> Read `AGENT_ONBOARDING.md`, `DECISION_METHOD.md`, and `EMERGENT_WORKFLOW.md` instead.
> The thought chain is at `docs/THOUGHT_CHAIN.md`.

# Heuristic Distiller Improvement: Automated Draft Rule Synthesis (2026-07-11)

## Summary
Implemented deterministic synthesis of draft rules from evidence samples in the heuristic distiller pipeline. This eliminates manual overhead for agents writing draft_rule entries in PENDING_HEURISTICS.md.

## Problem
Prior workflow:
1. Distiller clusters repeated failures into candidate heuristics
2. Renders each candidate with placeholder: `- draft_rule: (agent: write ONE sentence from the evidence, <=25 words)`
3. Agent must manually synthesize a meaningful rule from the evidence samples
4. This manual step delays heuristic promotion and creates a choke point in the circadian rhythm

Current queue (as of 2026-07-11) has H-21 through H-30 all pending with placeholder draft_rules, awaiting manual synthesis.

## Solution
Added `synthesize_draft_rule(signature, kind, samples)` function to `core/heuristic_distiller.py`:

### Algorithm (Deterministic, No LM)
1. Concatenate evidence samples into single text string
2. Apply ordered pattern-matching against 9 failure families:
   - Missing tool implementations
   - Missing input bindings
   - Missing visual effects
   - Missing components/assets
   - Missing event logging
   - Missing screenshot/state-capture actions
   - Incorrect pawn class/rig setup
   - Navigation/distance failures
   - Generic event expectation gaps

3. Return first matched rule template (<=25 words) or fallback:
   - If no pattern matches: extract signature tokens and build generic rule
   - If no tokens available: return placeholder (graceful degradation)

### Pattern Ordering (Specificity-First)
Patterns ordered most-specific-first to ensure high-fidelity matches:
- `atool_shovel` pattern catches exact tool missing before generic "missing component"
- `log_contains` pattern catches event-expectation failures before generic "log" mention
- `screenshot_taken` pattern catches beat-schema gaps before generic "screenshot"

### Empirical Validation
Tested against 5 real pending entries (H-21, H-25, H-26, H-28, H-30):

| Entry | Type | Evidence | Synthesized Rule | Quality |
|-------|------|----------|------------------|---------|
| H-21: Verb_Shovel | human_rejection | "ATool_Shovel missing" | "Implement missing tool actor and verify scene spawning." | ✓ Specific |
| H-25: shovel rock | sim_rejection | "screenshot_taken", "pawn_within" | "Implement screenshot action and state-capture in sleepwalker beat registry." | ✓ Correct focus |
| H-26: shovel sand | sim_rejection | "SandDrift_FX", "pawn_within" | "Verify environmental effects spawn and render correctly." | ✓ Precise |
| H-28: jump probe | sim_rejection | "log_contains [DEMOBEAT]" | "Verify event logging and signal traces on success path." | ✓ Accurate |
| H-30: verb look | sim_rejection | "screenshot_taken", "pawn_class" | "Implement screenshot action and state-capture in sleepwalker beat registry." | ✓ First match |

All 5 synthesized rules are actionable and grounded in evidence samples; none fell back to placeholder.

## Integration Point
Modified `render_entry()` in distiller to call `synthesize_draft_rule()` when rendering new candidates:

```python
# Before: hardcoded placeholder
lines.append("- draft_rule: (agent: write ONE sentence from the evidence, <=25 words)")

# After: synthesized from evidence
draft = synthesize_draft_rule(c['signature'], c['kind'], c['samples'])
lines.append(f"- draft_rule: {draft}")
```

## Impact

### Reduces Manual Overhead
- Agents no longer write draft_rules from scratch for every new candidate
- Instead, they review/refine auto-synthesized rules (faster)
- Placeholder fallback gracefully degrades to placeholder if synthesis unsure

### Maintains Determinism
- Zero LM dependency (regex + keyword matching only)
- Fully testable with unit harness
- Transparent to the gardener (synthesis is pre-promotion, not policy-making)

### Improves Dream Loop Velocity
- Circadian rhythm (nightly dream_loop → pending heuristics → gardener tending → promotion) now flows faster
- Each night's distilled candidates are immediately actionable
- Less wait time before capable cycle can approve/implement

### Empirical Upside for Current Queue
If the current pending entries (H-21 through H-30) had been synthesized via this function instead of left as placeholders, the gardener could have promoted them immediately without waiting for manual rule drafting.

## Testing
- Syntax check: `python -m py_compile core/heuristic_distiller.py` ✓
- Unit test on 5 real entries: all synthesized rules non-placeholder and actionable ✓
- Integration test: `python -m core.heuristic_distiller --dry-run --min-cluster 10` ✓
  - Suppresses 30 existing clusters correctly
  - No regression in distiller pipeline

## Future Enhancements
1. Add more failure patterns as new signature families emerge
2. Extend synthesis to `conflict_check()` to auto-suggest reconciliation
3. Periodically audit synthesized rules' acceptance rate (if manually edited, refine patterns)

## Files Modified
- `core/heuristic_distiller.py`:
  - Added `synthesize_draft_rule()` function (49 lines)
  - Modified `render_entry()` to call synthesizer (2 line change)
  - Total: 51 lines added, 1 line removed (net +50)

## Backward Compatibility
- No breaking changes to distiller API
- Existing promoted heuristics unchanged
- Gardener logic unchanged (still accepts manual vetoes)
- Graceful fallback to placeholder if synthesis fails
