# PERTURBATION PROOF — fleet-catalogue-repin-02

Question the perturbation answers: do the repinned pins bind to MEASURED builder
output at the revision under test, or to taste? If they bind to measurement, any
deliberate perturbation of the source corpus MUST move the measured counts and the
pins MUST fail against perturbed output.

## Setup (throwaway; removed after capture)

```bash
git -C E:/ChimeraWork/slot-04 worktree add --detach /tmp/repin-perturb-02 HEAD
# HEAD = 48e9885130ed04386d440eeff603b529f3622aa6 (repin commit)
printf '\n| repin-02-perturbation-probe-01 | perturbation: one dated line appended 2026-09-11 (throwaway probe, fleet-catalogue-repin-02) | PERTURBATION |\n' \
  >> /tmp/repin-perturb-02/docs/THE_MASTER_LIST.md
```

The appended perturbation is one dated pipe-table row with a fresh task ID
(plus the blank separator line the printf emits). The canonical Master list in
the real worktree was NEVER touched (`git status` clean throughout; scopes
respected — the perturbation lived only in the throwaway checkout, now removed).

## Measured counts move

Builder at the perturbed checkout (`BUILDER_OUTPUT_PERTURBED.raw`, verbatim):

| counter                | pinned (head 48e98851) | measured perturbed | delta |
|------------------------|-----------------------:|-------------------:|------:|
| master_row_ids         | 85                     | 86                 | +1    |
| master_row_observations| 119                    | 120                | +1    |
| line_partition length  | 2630                   | 2632               | +2    |

## Pins FAIL against perturbed output (load-bearing)

`python -m unittest tools.agent_fleet.test_master_catalogue` in the perturbed
checkout (`TEST_OUTPUT_PERTURBED.raw`, verbatim):

```
FAIL: test_gen5_exhaustive_partition_no_silent_omissions
AssertionError: 2632 != 2630
FAIL: test_import_real_sources_full_coverage
AssertionError: 86 != 85
Ran 23 tests in 2.033s
FAILED (failures=2)
```

The observations pin (119) is again masked inside the failing
`test_import_real_sources_full_coverage` (the test aborts at the ids assertion
in the same test), so it was demonstrated directly in the perturbed checkout:

```
AssertionError: observations pin 120 != 119
```

## Verdict

A one-line dated doc append moves all three measured counters and all three
repinned pins fail against the perturbed output. The pins bind to measurement,
not to taste. Cleanup:

```bash
git -C E:/ChimeraWork/slot-04 worktree remove --force /tmp/repin-perturb-02
```
