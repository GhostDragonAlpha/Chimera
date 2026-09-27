# MAT2-P04 preregistration addendum — carried-probe source (frozen before re-run)

Addendum to `PREREGISTRATION.md` of this attempt, frozen after the runner's
first recorded run failed on a RUNNER layout defect (preserved:
`first_run_failures/runner_run1_traceback.txt`) and before any probe or
pinned suite has executed. No probe expectation of PREREGISTRATION.md is
weakened; this addendum pins one additional identity expectation.

## Defect and fix (runner only)

The PR #175 tree does not contain `test_p04_contract.py` /
`test_p04_records.py`: they were byte-identical carries of PR #158 (recorded
in the merged runner's `CARRIED_FROM_PRIOR`), so extracting the 20 files of
merge commit `b7c4b797...` left the two carried probes missing. Fix: the
layout additionally extracts the two carried probes from the merged PR #158
head `68290bec4ab84238e00e9190748402177fd55937` (PR state CLOSED =
superseded by #175; blobs observed via `git show` at reconcile/fix time).

## Additional frozen expectation (P3b)

The executed copies of the carried probes hash-match both the PR #158 head
blobs and the merged `run_all_probes.py` `CARRIED_FROM_PRIOR` values:

- `test_p04_contract.py`: `e9b8b62d0af01821b0d6a370b5ddee47eb078e69033734ec0793b862956f77a0`
- `test_p04_records.py`: `153dd91c56f06f2f90b63a2b6cc7faab552a7544e65e0810d5875a2e978e924c`

A violation of P3b is recorded as a failure with disposition; the carried
probes are never edited by this attempt.
