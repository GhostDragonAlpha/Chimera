# Master Development Dashboard — TOMBSTONE (gutted 2026-07-16)

> **This dashboard reported percentages against a benchmark that does not exist. It is
> gone. This page exists so nobody rebuilds it.**

## What was here

A table of "player-enjoyment percentile vs AAA benchmark titles" — `Goal: 85%+`, with
rows like `Core Systems 89-91% ✅ EXCEEDS TARGET` and `Player_Character_Model: 97.2%
(A+) ← DEMONSTRATION OF AAA QUALITY`, `Tier 2 (120 pts): 120/120 ✓ PERFECT`, headed
**"Verified via Result Grader"**. Alongside it: `PHASE_1_COMPLETE_SYNTHESIS.md` ("✅
Calibrated against proven AAA benchmarks") and `AAA_DEVELOPMENT_ROADMAP.md`.

## Why it is gone — the verified facts, not an opinion

The numbers came from `core/result_grader_aaa_expanded.py` (754 lines, deleted). Three
things were true of it at once:

1. **The benchmark was never read.** `benchmark_titles` was accepted as an argument
   (`:600`), defaulted to `[]` (`:612`), copied into the output dict (`:674`) — and
   never used again. Not once. No EVE / No Man's Sky / Elite data existed anywhere in
   the repo. "85th percentile vs AAA titles" was computed against **nothing**. The
   title string was a label, and printing it next to a number was false provenance.

2. **The agent graded itself by typing an adjective.** 45 of its scoring branches were
   string-equality checks against the agent's own evidence file:

   ```python
   if immersion.get("moment_to_moment_feel_quality") in ("AAA", "high"):
       pts += 12
   ```

   An agent that wrote `"moment_to_moment_feel_quality": "AAA"` about its own work
   scored 12/12 for "moment-to-moment feel". That is the whole mechanism behind
   `120/120 ✓ PERFECT`. The author was the judge — the exact error the Frame Audit
   (Q2: *"Who judges the judge — is the author grading its own work anywhere?"*) exists
   to catch, and `docs/RESEARCH_ENFORCEMENT.md:36` had already named it in this very
   repo: *"a system that grades its own output ... can report a 2.02 GPA over features
   that don't work."*

3. **Nothing called it.** Zero importers — the only match in the codebase was its own
   docstring example. It was a shadow grader beside the real one, and every number it
   ever produced reached the operator through these docs.

## What is actually true

- **`core/result_grader.py` (180 lines) is THE gate, and it is clean** — no AAA strings,
  no benchmark passthrough, no self-report scoring. It grades measured evidence with
  zero LM dependency. It was never the source of these numbers.
- **There is no measurement of "fun" or "AAA quality" in this studio, and there is not
  going to be one by grading harder.** `docs/TRAINING_PROTOCOL.md` says it plainly:
  *"Nobody has a fitness function for fun — that is the open problem."*

## The rule this cost us

> **No reference, no verdict.**

The system never decides what is good on its own. A human — or an objective that a human
authored — supplies the reference; the machine attunes to it and reports how close it
got. A percentile needs something to be a percentile *of*. If the reference is absent,
the honest output is a **refusal**, never a number.

What CAN be measured is measured, and it looks like this — every figure below is a fact
some physics produced, reproducible by running the tool named:

| claim | measured by |
|---|---|
| `periodicity 0.76`, duty 0.58, suspension 4.3% | `python -m core.gait_mj --trained docs/objectives/brain_gpu.trained.json` |
| a 1-micron start nudge costs 0.53 body lengths | same command, ROBUSTNESS block |
| `punishes_naive = 4.00x` (matching a call costs 4x the energy) | `python -m core.attunement demo` |
| `skill_gap 83.7x`, `learnability 0.98` | `docs/objectives/attunement.trained.json` |

Those are small, unglamorous, and true. The 97.2% was none of those things.

**If you find yourself about to write a percentile against AAA titles: the data still
does not exist. Write down what the physics measured instead.**
