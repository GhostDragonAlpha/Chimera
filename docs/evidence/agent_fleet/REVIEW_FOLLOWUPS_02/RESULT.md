# fleet-review-followups-02 result (2026-09-11, subagent-worker-02, slot 2)

Preregistration commit `c4fdb9d7` precedes all results here (statement,
prediction, falsifier; no measured actuals). Branch
`astra/tasks/fleet-review-followups-02`, base
`c1a1ec5a5a166d8f32816cdacc9569e03857fa0e` (= remote tip of
`astra/gait-capture`; no merge needed).

## Followup -> fix -> test

| # | Recorded finding | Fix (commit) | Test / evidence |
|---|------------------|--------------|-----------------|
| F1 | PR #51 review finding 1: `capture_client_pixels` did not null-check `mem_dc`; a failed `CreateCompatibleDC` flowed NULL into `SelectObject`/`PrintWindow` and mislabeled as `capture_refused:printwindow_refused` | `163df151`: explicit null-check returning the NAMED fail-closed verdict `capture_refused:memory_dc_unavailable` (window DC released; refusal fires before DIB allocation and any pixel path); name added to `verdict_verdicts()` | `test_capture_window.py::test_failed_memory_dc_is_named_refusal` — forces the failure path by patching the ctypes prototype on a SELF-CREATED fixture window (restore inline + addCleanup backstop; positive control capture after the patch window). capture suite 19/19 |
| F2 | PR #51 review finding 2: `verify_hwnd_capture(pinned_size=None)` silently adopts the measured size, making the `window_resized` gate inert for non-pinning callers | `163df151`: adoption semantics documented in the function docstring AND `docs/THE_WINDOW_CAPTURE_OWNERSHIP.md` (new appended dated section). No behavior change; every in-repo caller still pins | `test_capture_window.py::test_verify_hwnd_capture_none_pin_adopts_measured_size` — asserts the documented adoption on a self-created fixture: without a pin `pinned_size == client_size` and the resized gate never fires on a really-resized window; contrast control: the same window with the original pin still yields `window_resized` |
| F3 | feedback `97b871b5`: TRANSPORT_BODY_LIMIT/MEASUREMENT.json did not embed the exact payload-measurement command/serializer | `14013a0f`: appended dated `correction_20260911` member embedding the exact one-liner (in-process builder + the exact `client.call` transport serialization, `json.dumps` defaults, UTF-8) and its re-measured output; original block untouched (git diff: 20 insertions, 0 deletions); 1,518,593 B noted as discovery-context; reproducible variants recorded (transport envelope + `--out` artifact). `RESULT.md` gained a pointing note | `RUN_PAYLOAD_MEASUREMENT.txt` (verbatim: envelope **1,519,534 B**, digest `67c89fd5...`), `RUN_MASTER_CATALOGUE_OUT.txt` (verbatim: artifact **1,511,333 B**, sha256 `0223f5b4...`); both inside the recorded variant span 1,518,018-1,526,171 B |
| F4 | feedback `97b871b5` trivials: test_4 `post()` left the `HTTPError` unclosed (ResourceWarning in retained output); docstring said "one byte" while the probe is +2 KiB | `95cbb2bd`: `post()` reads then CLOSES the error response (`try/finally: exc.close()`); docstring corrected to "2 KiB above the cap" | transition suite run with `-W always::ResourceWarning`: 4/4 OK, **0** ResourceWarning occurrences (`RUN_TRANSITION_SUITE.txt`) |

## Suite results (from REPO ROOT, verbatim raw outputs in this directory)

- capture suite: `Ran 19 tests ... OK` (`RUN_CAPTURE_WINDOW_SUITE.txt`)
- transition suite: `Ran 4 tests ... OK` with `-W always::ResourceWarning`
  (`RUN_TRANSITION_SUITE.txt`)
- full fleet suite: `Ran 189 tests ... OK (skipped=1)` — the one skip is
  the expected Windows-symlink skip
  (`test_worktree_reconcile.WorktreeReconcileTests.test_unsafe_arguments_and_symlink_escape_refuse ...
  skipped 'symlink creation unavailable'`) (`RUN_FULL_SUITE.txt`). 187
  tests at base tip + the 2 new capture-contract tests; no assertion
  removed or weakened anywhere.

## Falsifier check

- No existing assertion removed or weakened: diff is purely additive on
  test files (new tests + F4's close/docstring; the F4 docstring fix
  corrects prose, no assertion touched).
- Evidence appended, never rewritten: MEASUREMENT.json diff = 20 insertions,
  0 deletions; THE_WINDOW_CAPTURE_OWNERSHIP.md and TRANSPORT_BODY_LIMIT/
  RESULT.md received appended dated sections only.
- No followup "fixed" by deleting the behavior it describes: F2 keeps the
  adoption behavior and documents it; F1 keeps every existing refusal name
  and adds one; F3 keeps the original measurement block verbatim.
- Suite failures: none.

## Acceptance

NOT_CLAIMED — pending lead review and authorized integration.
