# BASELINE (before any edit) — recorded 2026-09-11, worktree E:\ChimeraWork\slot-03, HEAD d012b4b1

Targeted suite:  python -m unittest tools.agent_fleet.test_master_catalogue
Ran 23 tests — FAILED (failures=2)

FAIL: test_gen5_exhaustive_partition_no_silent_omissions
  File "tools\agent_fleet\test_master_catalogue.py", line 665, in test_gen5_exhaustive_partition_no_silent_omissions
    self.assertEqual(len(part), 2430)
  AssertionError: 2540 != 2430

FAIL: test_import_real_sources_full_coverage
  File "tools\agent_fleet\test_master_catalogue.py", line 183, in test_import_real_sources_full_coverage
    self.assertEqual(built['coverage']['master_row_ids'], 65)
  AssertionError: 76 != 65

Full fleet suite:  python -m unittest discover -s tools/agent_fleet -p 'test_*.py'
Ran 166 tests — FAILED (failures=2, skipped=1)
The only failures are the same two tests (identical tracebacks); 1 pre-existing skip.
