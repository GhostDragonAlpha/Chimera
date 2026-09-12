# PREREGISTRATION — fleet-catalogue-repin-01 (generation 1, slot 3)

Agent: subagent-worker-02 · Worktree: E:\ChimeraWork\slot-03 · Tip: d012b4b1
Branch: astra/tasks/fleet-catalogue-repin-01 · Registered BEFORE any measurement or edit.

## STATEMENT

The fleet suite's two pre-existing failures are STALE COUNT PINS, not lost documents:
later merged lanes grew `docs/THE_MASTER_LIST.md` past the counts pinned in
`tools/agent_fleet/test_master_catalogue.py` (`master_row_ids` pinned 65, actual 76;
`line_partition` length pinned 2430, actual 2540). Updating the pins to values
MEASURED from the real builder output restores the suite without weakening any check.

## PREDICTION

1. After repinning the two counts to measured values, both failing tests pass AND the
   rest of `test_master_catalogue` (all 23 tests) stays green.
2. A deliberate -1 perturbation of each new pin still fails (the checks remain
   load-bearing).
3. The rest of the fleet suite passes (zero failures; skips allowed).

If any OTHER assertion inside these two tests is stale because the document grew
(e.g. the sibling `master_row_observations` pin at the same call site, or the pinned
B7b line number 1825 if the continuation moved), it will be repinned ONLY from
measured builder output, with the measured provenance recorded — never to make a
semantic check pass dishonestly. A semantic check (row content, B7b retention class)
that fails for a NON-count reason is a finding, not a repin, and will be reported
without touching it.

## FALSIFIER

Any other suite expectation changed beyond measured-count repins inside the two named
tests; counts hardcoded without measuring the actual builder output; or a test
disabled/skipped to go green. Any of these falsifies the statement and blocks the PR.

## EXACT COMMANDS (in execution order)

```bash
# 0. ownership + baseline (before any edit)
python -c "...controller snapshot..."          # verify task/gen/slot
git -C E:\ChimeraWork\slot-03 rev-parse HEAD
cd E:\ChimeraWork\slot-03
python -m unittest tools.agent_fleet.test_master_catalogue        # baseline: 2 failures expected
python -m unittest discover -s tools/agent_fleet -p 'test_*.py'   # baseline full suite

# 1. MEASURE via the builder (never hand-count); dump every coverage counter
python -c "import sys,json; sys.path.insert(0,'tools/agent_fleet');
from master_catalogue import build_records
b=build_records(); c=b['coverage']
print(json.dumps({k:c[k] for k in ('cards','domains','master_row_ids',
 'master_row_observations','unresolved','structural_rows','prose_mentions',
 'campaign_prose_refs','unkeyed_requirements')}, indent=1))
p=c['line_partition']; print('partition_len', len(p))
print('line1825', json.dumps(p[1825], ensure_ascii=True))"
# measurement is written to evidence/MEASUREMENT.json by the same script variant

# 2. EDIT: only the stale count pins inside the two named tests
# 3. RUN
python -m unittest tools.agent_fleet.test_master_catalogue        # expect 23/23 OK
# 4. PERTURBATION PROOF: each new pin set to measured-1 -> capture FAIL output -> restore
# 5. FULL SUITE
python -m unittest discover -s tools/agent_fleet -p 'test_*.py'   # expect 0 failures
# 6. COMMIT + PUSH (no force) + PR against astra/gait-capture
```

## SCOPE

- `tools/agent_fleet/test_master_catalogue.py` — ONLY stale count pins, each justified
  by measured builder output recorded in this directory.
- `docs/evidence/agent_fleet/CATALOGUE_REPIN/` — evidence only.
- No test disabled/skipped; no `master_catalogue.py` change; no live registry touched
  (the suite is isolated temp-registry by construction).
