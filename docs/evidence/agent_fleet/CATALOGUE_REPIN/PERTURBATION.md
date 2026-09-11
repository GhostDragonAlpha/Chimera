# PERTURBATION PROOF — each new pin set to measured-1, the owning test still fails

Method: one pin at a time, in a single sequential cycle per pin — apply measured-1,
clear all `tools/**/__pycache__`, run only the owning test, restore, assert the
original pin is back. Final file state re-verified by Select-String + git diff.

## 1. master_row_ids 76 -> 75
    AssertionError: 76 != 75
    Ran 1 test in 0.167s — FAILED (failures=1)
restored to 76, verified.

## 2. master_row_observations 96 -> 95
    AssertionError: 96 != 95
    Ran 1 test in 0.149s — FAILED (failures=1)
restored to 96, verified.

## 3. line_partition length 2540 -> 2539
    AssertionError: 2540 != 2539
    Ran 1 test in 0.142s — FAILED (failures=1)
restored to 2540, verified.

All three checks are load-bearing: a one-off perturbation of any new pin fails its test.

# INCIDENT RECORD (honesty note) — stale __pycache__ false failure

During the first post-repin full-suite runs, discover reported
`AssertionError: 96 != 95` while the on-disk source line (printed in the same
traceback) read `..., 96)`. Root cause: the perturbation helper wrote same-size
("95"/"96", "2539"/"2540") edits within the same coarse mtime granularity, so Python's
bytecode cache validation (mtime+size) kept serving the pre-restore module. The
builder output was never 95; the file on disk was never committed in a perturbed
state. All results above were re-taken with `__pycache__` cleared and `python -B`.
Nothing about the task statement changes: it is a test-RUNNING hygiene artifact of the
perturbation procedure itself, not a suite or builder defect.
