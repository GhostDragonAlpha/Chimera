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
