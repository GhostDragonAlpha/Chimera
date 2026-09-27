# MAT2-P04 preregistration addendum 2 — extraction convention and fixture layout (frozen before re-run)

Second addendum to `PREREGISTRATION.md`, frozen after the second recorded
runner run (failures preserved: `first_run_failures/run2_probe_run_results.json`,
`first_run_failures/run2_reconciliation_checks.json`,
`first_run_failures/probe_test_correction_records.log`) and before the third
run. No carried probe or pinned file is edited; no probe expectation of
PREREGISTRATION.md / addendum 1 is weakened. Two RUNNER/LAYOUT defects and
their fixes:

## D1: extraction conversion convention (fixes P1 and one carried FAIL)

`git show` writes the raw LF blob, but the legacy manifest
(`pinned_file_hashes.json`, whole-file sha256 `c79f248b...`) records
`git archive` output under this machine's `core.autocrlf=true` +
`text=auto`, i.e. LF->CRLF-converted text files. Proof of identical content:
the CRLF-converted `control.py` blob hashes to exactly the manifest value
`39ff01dc8a4192e04606ee9d87386780739e89c8a1774da48501a9545792f6b3`
(P1.control_py_frozen passed even in run 2; the raw LF hash was
`b540966a...`, which is the same blob). Fix: the pinned tree is re-extracted
with `git archive HEAD -- tools/agent_fleet tools/monkey_campaign` and only
the 51 manifest-keyed members are written, reproducing the legacy INDEX's
documented `git archive` procedure. After this, all 52 manifest entries hash-
match (P1 green).

## D2: legacy-untracked fixture layout elements (fixes one carried FAIL and one carried ERROR)

`test_correction_records.py` reads two legacy-workspace elements that were
deliberately untracked and are therefore absent from the merged PR #175
tree:

- `qualification_receipt.json` at the workspace root (the final
  non-draft receipt whose honesty the probe cross-checks);
- the byte-identical mirror of `gpu_handoff.py` at the attempt-checkout
  sparse path `checkout/tools/monkey_campaign/contributions/ONT-P04/`,
  asserted by `test_machine_module_exists_and_is_byte_identical`.

Fix: both are copied byte-exact with provenance from the final legacy
attempt workspace
`kanban-attempts/ONT-P04/06792d79c3704ac29df519055aabbc57/`:

- `qualification_receipt.json` sha256 `4ca0d18eebdc14d4b1cb8235da806569598740ab134055f82d152e5942f44da0`
  (source and copy equal);
- checkout-mirror `gpu_handoff.py` sha256 `fd664b5f8182ea3466b37f9cdfe217950bcc6e91a4bb72c23c9ac6c33ad78dc0`
  (source, copy, and the merged WS copy all equal — the merged blob
  `fd664b5f...` is the machine of record).

The mirror is placed at the same path relative to the verification workspace
(`reference/ONT-P04/checkout/...`) to satisfy the carried probe's documented
fixture layout; the new-namespace candidate tree is not polluted with a
duplicate machine module.

## Frozen expectation additions (P6)

The runner additionally records P6: both provenance copies hash-equal their
legacy sources, and the checkout-mirror copy hash-equals the merged
`gpu_handoff.py` blob. A P6 violation is recorded as a failure with
disposition.

## Run ledger

- Run 1: runner crash before any probe (runner defect; preserved
  `runner_run1_traceback.txt`). No probe executed.
- Run 2: identity checks P1 FAIL (D1); battery 134/137 OK —
  `probe:test_correction_records` 7/10 with 2 FAIL + 1 ERROR (D1, D2);
  all other 10 suites green (preserved run-2 files above).
- Run 3 (this addendum's re-run): full identity checks + battery; any
  failure is recorded honestly with disposition and preserved output.
