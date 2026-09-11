# fleet-transport-body-limit-01 result (2026-09-11, lead lane)

Preregistration commit `a539f2b9` precedes all results here (statement,
derivation, prediction, falsifier; no measured actuals).

## Outcome

- `tools/agent_fleet/service.py`: `MAX_BODY` 65,536 → 2**24 (16,777,216 B)
  with the derivation comment (measured canonical payload 1,518,593 B at tip
  `95f25b33`; corpus-doubling headroom x8; power-of-two convention).
- `tools/agent_fleet/test_controller_transition.py`: new
  `test_4_transport_body_limit_boundary` — under-cap body (2**24 − 1 KiB) is
  served (200 + revision); over-cap body (2**24 + 2 KiB) is refused
  (`request_size` 409, or the early-close abort the refusal causes
  mid-upload); listener alive after both; module constant pinned to 2**24.
  Landed in the same file, per recorded feedback `b6eab9ea`: the PR #53
  followup — test_3 now also scans the second live session token (`op`).
- `docs/THE_CONTROLLER_TRANSITION.md`: dated note (below).

## Verification

- Transition suite 4/4 (exit 0; raw `RUN_TRANSITION_SUITE.txt`).
- Full fleet suite 187 tests, 0 failures, 1 Windows-symlink skip (exit 0;
  raw `RUN_FULL_SUITE.txt`).

## Retained corrections (failures kept, not hidden)

1. First draft of the cap comment lost `#` prefixes on continuation lines →
   `SyntaxError` (leading zeros in `2026-09-11`); fixed before any test ran
   green; caught by `py_compile`.
2. test_4 initially appended after the `__main__` guard (dead code, silently
   not collected — "Ran 3 tests"); restructured into the class; the
   collection count (4) is now asserted by the run itself.
3. The size-scaffold's fixed overhead estimate was wrong (off by ~1 KiB);
   replaced with exact byte arithmetic from the measured empty-pad envelope.
4. The over-limit POST surfaces client-side as a connection abort (the
   server refuses from the Content-Length header before reading the body);
   the test accepts the readable 409 OR the abort, then proves the listener
   survived and no op executed.

## NOT_CLAIMED

- The live import through the raised cap — executed only AFTER the
  documented controlled transition to a deployment built from this reviewed
  source (backup, quiescence, authorized stop/start, post-comparison).
- Any deployment-identity claim beyond the one already-evidenced live
  transition.

## Correction appended 2026-09-11 (fleet-review-followups-02, feedback 97b871b5)

Review followup (LOW): this file's recorded canonical payload of 1,518,593 B
was discovery-context (the size measured during the first live import
refusal at tip `95f25b33`) and MEASUREMENT.json did not embed the exact
payload-measurement command/serializer, so it was not byte-reproducible from
committed evidence (rebuild variants span 1,518,018-1,526,171 B). The
appended `correction_20260911` member of MEASUREMENT.json closes that gap:
it embeds the exact one-liner (repo root; in-process builder + the exact
`client.call` transport serialization) and its re-measured output at this
evidence's worktree - transport envelope **1,519,534 B**, payload digest
`67c89fd5...`, plus the `--out` artifact variant (**1,511,333 B**,
ensure_ascii=False serializer). Both reproducible variants sit inside the
recorded discovery-context span; the derivation (x8 headroom, power-of-two
2**24) is unchanged and the boundary regression (`test_4`) pins the deployed
limit empirically. The original measurement block was not rewritten
(git diff: 20 insertions, 0 deletions). Raw outputs:
`docs/evidence/agent_fleet/REVIEW_FOLLOWUPS_02/RUN_PAYLOAD_MEASUREMENT.txt`
and `RUN_MASTER_CATALOGUE_OUT.txt`.

The same followup's trivials are fixed in
`tools/agent_fleet/test_controller_transition.py` test_4: the `post()`
helper now closes the caught `HTTPError` (no ResourceWarning in retained
output) and the docstring states the actual probe size (2 KiB above the
cap), replacing "one byte".
