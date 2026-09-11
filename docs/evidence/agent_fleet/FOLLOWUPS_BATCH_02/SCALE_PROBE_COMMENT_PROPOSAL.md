# F2 optional followup: load-context comment for the scale-probe assertion

- Source: PR #63 delta review INFO, recorded in the fleet-followups-batch-02
  packet (2026-09-11). The mandatory half of F2 (the dated load-fragility
  append to `SLOT_EXPANSION/MEASUREMENT.json`,
  key `correction_20260911_followups_batch_02`) LANDED in this task.
- Status: PROPOSAL ONLY. The assertion lives in
  `tools/agent_fleet/test_slot_expansion.py`
  (`test_scale_probe_lock_errors_and_latency`, mixed-load phase,
  `self.assertEqual(lock_err, 0, ...)`), which is NOT in this task's write
  scopes. Nothing was edited there; the assertion is untouched.

## Proposed comment (insert directly above the assertEqual)

```python
        # LOAD CONTEXT (followups-batch-02): this gate is green in module
        # isolation but LOAD-FRAGILE under full-suite contention - two
        # recorded runs under suite load each saw exactly ONE
        # database-locked error at the single-writer SQLite boundary (see
        # SLOT_EXPANSION/MEASUREMENT.json,
        # correction_20260911_followups_batch_02). The assertion is
        # retained deliberately: green gate = module-isolated run; a lock
        # error under external suite load is boundary data, not a
        # regression - rerun the module in isolation and keep both outputs.
```

## Disposition note for the lead

One-comment edit in a file this task cannot write. Recommended: fold into
the same followup that lands F4 (`watchdog-fail-closed-01`) or any future
task scoped to `tools/agent_fleet/test_slot_expansion.py`.
