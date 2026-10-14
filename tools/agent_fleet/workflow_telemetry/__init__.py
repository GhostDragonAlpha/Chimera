"""workflow_telemetry -- the Astra P0 pilot lane (agent/workflow-telemetry-20260921).

An incident ledger is not enough: it records failures without DENOMINATORS. The
MAPE-K Observe step needs an EVENT LEDGER OF EVERY ATTEMPT -- the uneventful
runs, the queue delays, the abandoned candidates, the waiting time.

This package:
  schema.py      -- the append-only JSONL event schema + writer
  collectors.py  -- retroactive collectors over EXISTING evidence only
                    (wave receipts, git history, janitor JSONL, lane artifacts)
  reconstruct.py -- attempt graph (waves 28-38), serial-path analysis (35-38),
                    F-EVENT-GAP / F-TIME-ACCOUNTING reconciliation

NO lane is touched. Read-only over the worktrees; writes only to this repo's
validation receipt dir. Preregistration (Rule 0) lives at
tools/science_funnel/validation/workflow_telemetry_20260921/PREREGISTER_F_EVENT_GAP.md
and was frozen BEFORE this code existed.
"""
