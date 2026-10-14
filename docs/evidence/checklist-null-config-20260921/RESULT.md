# checklist-null-config-20260921 result

Amendment shipped: docs/THE_CHECKLIST.md §0, one new bullet inserted directly
after the Rule-0-banked bullet — "Rule 0 — the null configuration (the floor)".
Diff vs master 6ea2702c: `9 0 docs/THE_CHECKLIST.md` (insertions only, zero
deletions, zero reorder) + this evidence directory. Two paths, as predicted.

Gates (logs in this directory):

- graph suite, canonical script mode per CONTRACTS.md
  (`python -B tools/creature_graph/tests/test_contracts.py`, the form
  tools/science_funnel/qualify.py runs): **19 OK at BOTH PYTHONPATH roots**
  (tools:tools/creature_graph and .). graph_root1_scriptmode.txt,
  graph_root2_scriptmode.txt.
- matter_kernel test_definition (PYTHONPATH=tools): **9/9 OK**.
- tools/training_gate.py: **PASS** (Froude-consistent).

The `-m unittest tools.creature_graph.tests.test_contracts` form with the
literal colon PYTHONPATH (tools:tools/creature_graph) shows 4 fixture-import
errors (test_d7/d8/d9 need the tests dir itself on sys.path; native Windows
python's os.pathsep is ';', so the colon form is one bogus entry). Diagnosis,
graph_moduleform_diagnosis.txt: the ';' split plus the tests dir gives 19 OK,
and the identical 4 errors reproduce on PRISTINE master (diff stashed) —
pre-existing environment mechanics, not this lane's change. The suite's two
import identities both green: module form 19 OK with the tests dir banked;
script form 19 OK at both roots.

No falsifier fired: no third file in the diff, the checklist diff is pure
insertion, every gate at baseline. Successor for the cited lane: v2
(agent/standing-pose-20260921 @ 4ea008cb, its visual falsifier fired and
documented downstream; this amendment banks the lesson fleet-wide).
