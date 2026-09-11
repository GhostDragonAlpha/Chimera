# RESULT — fleet-catalogue-repin-02 (generation 1, slot 4)

Agent: subagent-worker-01 · Branch: astra/tasks/fleet-catalogue-repin-02
Base (recorded): f9ef0ebeab10da13b2f134403946063a441833e7 (= integration tip at
claim, post PR #49 + PR #50) · Prereg commit: 77bc1588 · Repin commit: 48e98851

## What was done

1. PREREGISTRATION committed FIRST (77bc1588), before any measured value was
   pinned — statement/prediction/falsifier per the task packet.
2. Baseline at base f9ef0ebe: `python -m unittest
   tools.agent_fleet.test_master_catalogue` → exactly 2 failures, both stale
   count pins, pre-existing (matches the window-capture-02 observation):
   - `master_row_ids`: pinned 76, actual 85
   - `line_partition` length: pinned 2540, actual 2630
   A THIRD stale pin was masked: `master_row_observations` (pinned 96) sits in
   the same test one line below the failing ids assertion, so the baseline run
   aborted before reaching it. Fresh measurement showed actual 119.
3. Fresh measured builder run at the branch head (`python
   tools/agent_fleet/master_catalogue.py`; verbatim output in
   BUILDER_OUTPUT_HEAD.raw; full counters in MEASUREMENT.json):
   - master_row_ids **85**, master_row_observations **119**,
     line_partition length **2630** (cards 240, domains 40 unchanged)
   - the pinned B7b line-1825 falsifier re-measured UNCHANGED: still
     `class: prose`, text still contains `B7b` — no semantic check moved.
4. Repinned ONLY the three stale counts in
   `tools/agent_fleet/test_master_catalogue.py` (76→85, 96→119, 2540→2630) with
   provenance comments. No assertion removed, no check weakened, builder and
   Master list untouched (scopes respected).
5. Perturbation proof: one dated doc line appended in a THROWAWAY detached temp
   worktree at the repin head → measured counts moved to 86 / 120 / 2632 and
   the repinned pins FAILED against perturbed output (86 != 85, 120 != 119,
   2632 != 2630). See PERTURBATION.md; raw outputs retained verbatim. Temp
   worktree removed after capture.
6. Full fleet suite from the worktree root:
   `python -m unittest discover -s tools/agent_fleet -p 'test_*.py'`
   → **Ran 166 tests — OK (skipped=1)**: 0 failures, the 1 expected
   Windows-symlink skip. Prediction 1 confirmed.

## Pins: old → new (each bound to a fresh measured run at THIS revision)

| pin                      | old (PR #47, tip d012b4b1) | new (measured at f9ef0ebe) |
|--------------------------|---------------------------:|---------------------------:|
| master_row_ids           | 76                         | 85                         |
| master_row_observations  | 96                         | 119                        |
| line_partition length    | 2540                       | 2630                       |

## Falsifier check (none fired)

- Pins changed WITH a fresh measured builder run at the revision under test
  (MEASUREMENT.json carries the producing commands; digest
  08d8b6eccabba03806d474c449020b7e09aa3e916047128ed8a4045f26b0db7c).
- Perturbation demonstrated (PERTURBATION.md + two verbatim .raw outputs).
- No test weakened: the diff is 3 count literals + provenance comments only.
- Pins match the CURRENT source revision: the builder's source manifest at head
  binds the measured payload to the live THE_MASTER_LIST.md text (sha256
  recomputed from the retained line partition by validate_payload).

## Effect

The GOV-01 clause-4 full catalogue import is unblocked: the lead can run
`master_catalogue.py` at the integration tip after this PR integrates and the
pinned suite will hold as long as the Master list is unchanged (and will fail,
loudly, the moment it grows — which is the point).
