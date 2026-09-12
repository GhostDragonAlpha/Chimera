# RESULT — fleet-catalogue-repin-01 (generation 1, slot 3)

Agent: subagent-worker-02 · Branch: astra/tasks/fleet-catalogue-repin-01
Worktree: E:\ChimeraWork\slot-03 · Parent tip: d012b4b1 (tree clean before work)

## What was done (in preregistered order)

1. PREREGISTRATION.md written before any measurement or edit.
2. MEASURED via the real builder (`master_catalogue.build_records()` over the canonical
   sources; see MEASUREMENT.json for full counters + source provenance).
3. Updated ONLY stale count pins in `tools/agent_fleet/test_master_catalogue.py`.
4. Suite runs + perturbation proof + full fleet suite (counts below).

## Measured vs pinned (builder output at tip d012b4b1)

| counter                          | old pin | measured | file:line |
|----------------------------------|---------|----------|-----------|
| coverage.master_row_ids          | 65      | 76       | test_master_catalogue.py:185 |
| coverage.master_row_observations | 68      | 96       | test_master_catalogue.py:186 |
| len(coverage.line_partition)     | 2430    | 2540     | test_master_catalogue.py:668 |

- master_sha256 at measurement: 99d0f3610e56080af08703432e14fa405cf6b00bbc35d5bbf97c66205bb2f6ff
  (2540 lines, 226989 bytes, git_commit d012b4b1...); catalog_sha256
  d9bb441939c0f07ccdbc0e4295353dc08ddb717f3b557f3e23639884d93f5a74. Full counter set in
  MEASUREMENT.json (cards 240, domains 40, unresolved 3, structural_rows 24,
  prose_mentions 13, campaign_prose_refs 24, unkeyed_requirements 278 — all unchanged
  pins in the suite still hold against these).
- The `master_row_observations` pin (68) is a THIRD stale count inside the already-
  failing test, declared in PREREGISTRATION.md ("Prediction" conditional) and repinned
  from the same measurement. unittest stops at the first failing assert, so the packet's
  failure report (65 vs 76) could not show it; with ids repinned to 76 the 68-pin would
  have failed next (96 != 68). Not updating it would have left the suite red.
- The pinned B7b falsifier check (partition line 1825) was RE-MEASURED, not changed:
  line 1825 is still class `prose` and still contains 'B7b' in the grown document.
- All row-content assertions re-verified (L1 '**The corpus**', B2 '**ROM re-sweep',
  demo-studio-state-01 table_row with 'no mesh loaded') — untouched, still valid.

## Suite results

- Before (baseline, no edits): targeted 23 tests, FAILED (failures=2) — exactly the two
  packet failures. Full discover: 166 tests, FAILED (failures=2, skipped=1), same two.
- After repin: targeted `python -m unittest tools.agent_fleet.test_master_catalogue`
  → Ran 23 tests, OK. Full `python -m unittest discover -s tools/agent_fleet -p
  'test_*.py'` → Ran 166 tests, OK (skipped=1 — the pre-existing skip; zero failures).
- Perturbation proof: each new pin at measured-1 FAILS its test (76!=75, 96!=95,
  2540!=2539) — see PERTURBATION.md. Checks remain load-bearing.
- One incident recorded honestly in PERTURBATION.md: stale `__pycache__` bytecode
  (same-size same-mtime edits) produced one false failure during the perturbation
  sequence; all recorded results are from cleared-cache `python -B` runs.

## Falsifier check

No test disabled or skipped; no expectation changed other than the three measured
count pins (+ their comments); no builder change; counts came from measured builder
output (MEASUREMENT.json), never hand-counted. git diff touches only
tools/agent_fleet/test_master_catalogue.py (15 lines) + this evidence directory.

## Acceptance

NOT_CLAIMED (review pending).
