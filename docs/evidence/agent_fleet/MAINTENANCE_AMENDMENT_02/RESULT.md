# fleet-maintenance-amendment-02 — RESULT (2026-09-11, lead lane)

All three preregistered predictions HOLD; no falsifier fired.

## Predictions vs measured

- **(a) append-only amendment — HOLD.** `docs/THE_MASTER_LIST.md` +88/-0,
  single dated section ("fourth and fifth waves"), verified byte-identical
  prefix against `HEAD` BEFORE the amendment commit (`git show HEAD:...`
  vs working copy; 2692 → 2780 lines). Commit `750b1beb`.
- **(b) fresh measured repin makes the suite green — HOLD.** Builder at
  amended head `750b1beb`: ids 97, observations 142, partition 2780
  (envelope sha256 `82f95803…bba28a8`, console retained). Pins updated
  89→97 / 127→142 / 2692→2780 at commit `f920ad79`; catalogue suite 23/23
  OK; full fleet suite **Ran 231 tests, OK (skipped=1)**, exit 0 — matching
  the 231-era count measured independently by the PR #68 regression sweep.
  The known intermittent capture-content flake did not fire in this run.
- **(c) perturbation control — HOLD (the pins FAIL as required).**
  Throwaway detached worktree at `f920ad79`, one appended dated pipe-row in
  the Master copy: `AssertionError: 2782 != 2780` and
  `AssertionError: 98 != 97` — FAILED (failures=2), exactly the +1 row / +2
  lines delta. The throwaway worktree was removed after the run; the
  operator checkout was never written.

## Falsifier review

No history rewritten (append verified pre-commit); pins changed ONLY with a
fresh measured run at the amended tip (commands + envelope digest retained);
perturbation demonstrated (above); no test weakened (numstat on
`test_master_catalogue.py` is a 4-value count/comment repin only); **no
stale-record retirement executed before integration** — the seven
`task_abandon` ops remain gated on this PR's pinned-head merge + ack, per
the preregistration and the Master dispositions.

## Scope discipline

Diff touches exactly: `docs/THE_MASTER_LIST.md` (+88/-0),
`tools/agent_fleet/test_master_catalogue.py` (4-line repin), and this
evidence directory. Nothing else.

## Notes for review

- The full-suite console (RUN_FULL_FLEET_SUITE.txt) includes the
  scale-probe stdout and two "stopped pid … (test teardown controlled
  transition)" teardown lines — those are the slot-expansion tests' own
  fixture services being torn down, not fleet actions.
- Suite duration 236s at 231 tests on the co-loaded fleet host.
