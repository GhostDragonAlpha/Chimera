# checklist-null-config-20260921 preregistration

Banked BEFORE the edit, per Rule 0. Lane: agent/checklist-null-config-20260921,
forked from master 6ea2702c (the live tip, verified against ls-remote).

**STATEMENT:** The null-configuration law (an operational definition must exclude
the trivially-satisfied configuration; evaluate the objective at the null
configuration BEFORE the run, bank the number as the floor) belongs in the
Rule-0/preregistration discipline of docs/THE_CHECKLIST.md §0, and appending it
is a docs-only change that cannot affect any executable code path.

**PREDICTION:** The diff vs master 6ea2702c touches exactly two paths —
docs/THE_CHECKLIST.md (pure insertion, §0, after the Rule-0-banked bullet; zero
deleted or reordered lines) and this evidence directory. The gate batteries
stay at their baselines: creature_graph test_contracts = 19 OK at BOTH
PYTHONPATH roots (tools:tools/creature_graph and .), matter_kernel
test_definition = 9/9, tools/training_gate.py = PASS.

**FALSIFIER:** Any third file path in the diff; any deletion/reorder inside
THE_CHECKLIST.md (a non-append diff); any gate below baseline (fewer than
19 OK at either root, fewer than 9/9, or training_gate not PASS).

Lesson source: the standing-pose lane verification 2026-09-21, lead-verified —
the objective was satisfied by the corpse itself, the numeric battery went
green, and the eyes-on visual falsifier fired (branch
agent/standing-pose-20260921 @ 4ea008cb; successor v2).
