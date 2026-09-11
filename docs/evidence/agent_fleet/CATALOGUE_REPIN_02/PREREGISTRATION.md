# PREREGISTRATION — fleet-catalogue-repin-02 (generation 1, slot 4)

Agent: subagent-worker-01 · Worktree: E:\ChimeraWork\slot-04 · Base: f9ef0ebe
(= integration tip at claim, post PR #49 + PR #50 second-wave doc merges)
Branch: astra/tasks/fleet-catalogue-repin-02 · Registered BEFORE any measurement,
before any edit to the test, and before any builder run is used to set a pin.

## STATEMENT

The count pins in `tools/agent_fleet/test_master_catalogue.py` equal the canonical
builder output for the exact source files at the revision under test. The pins left
by fleet-catalogue-repin-01 (PR #47, tip d012b4b1) no longer satisfy this: the
2026-09-11 second-wave doc merges (PR #49 Master maintenance amendment + PR #50
evidence) grew the canonical Master list beyond them, so `test_master_catalogue`
fails 2 pins at tip (observed by the window-capture-02 lane; provenance proven
pre-existing at base). They are STALE COUNT PINS, not lost documents; repinning to
MEASURED builder output restores the suite without weakening any check.

## PREDICTION

1. Running `python tools/agent_fleet/master_catalogue.py` at this branch head yields
   coverage counts that, when pinned, make the full fleet suite pass
   (0 failures, 1 Windows-symlink skip).
2. A deliberate perturbation — appending one dated doc line in a THROWAWAY temp
   checkout of this head — changes the measured counts, and the pins FAIL against
   that perturbed output (proof the pins bind to measurement, not to taste).
3. Only count pins move. Every other assertion in the test keeps its exact
   semantics: content checks (required IDs, B7b line-1825 retention class),
   validator refusals, and import behavior are untouched.

If a NON-count assertion fails at this revision for a semantic reason, that is a
FINDING, not a repin: it will be reported without touching it.

## FALSIFIER

- Pins changed without a fresh measured builder run at this revision.
- Perturbation not demonstrated.
- Any test weakened or expectation removed instead of re-measured.
- Pins matching a non-current source revision (e.g. values taken from repin-01's
  evidence instead of re-measured here).

Any of these falsifies the statement and blocks the PR.

## EXACT COMMANDS (in execution order)

```bash
# 0. ownership + baseline (this file committed FIRST, own commit)
git -C E:\ChimeraWork\slot-04 rev-parse HEAD      # expect f9ef0ebe...
python -m unittest tools.agent_fleet.test_master_catalogue        # baseline: 2 failures expected
python -m unittest discover -s tools/agent_fleet -p 'test_*.py'   # baseline full suite

# 1. MEASURE via the builder at head (never hand-count, never inherit repin-01 values)
python tools\agent_fleet\master_catalogue.py
# + a build_records() dump of every coverage counter into MEASUREMENT.json

# 2. EDIT: only the stale count pins in tools/agent_fleet/test_master_catalogue.py
# 3. RUN targeted: python -m unittest tools.agent_fleet.test_master_catalogue
# 4. PERTURBATION PROOF (throwaway):
#    git -C E:\ChimeraWork\slot-04 worktree add --detach "$TEMP/repin-perturb-02" HEAD
#    append one dated line to THE_MASTER_LIST.md in the temp checkout,
#    run the builder + pinned tests there -> pins must FAIL; remove the worktree.
#    (builder argparse supports --master; a scratch-copy variant is equivalent)
# 5. FULL SUITE: python -m unittest discover -s tools/agent_fleet -p 'test_*.py'
#    expect 0 failures, 1 Windows-symlink skip
# 6. COMMIT + PUSH (no force) + PR against astra/gait-capture + submit_review
```

## SCOPE

- `tools/agent_fleet/test_master_catalogue.py` — ONLY the stale count pins, each
  justified by measured builder output recorded in this directory.
- `docs/evidence/agent_fleet/CATALOGUE_REPIN_02/` — evidence only.
- NOT touched: `docs/THE_MASTER_LIST.md`, `tools/agent_fleet/master_catalogue.py`,
  any other test, any live registry.
