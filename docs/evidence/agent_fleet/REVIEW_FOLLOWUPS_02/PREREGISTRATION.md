# fleet-review-followups-02 preregistration (2026-09-11, subagent-worker-02)

Task `fleet-review-followups-02` generation 1, slot 2, worktree
`E:\ChimeraWork\slot-02`, base
`c1a1ec5a5a166d8f32816cdacc9569e03857fa0e` (= remote tip of
`astra/gait-capture`; no merge needed). Bundles the four recorded
non-blocking review followups from wave 2 (PR #51 review findings 1-2;
feedback `97b871b5` on PR #55). This file is committed BEFORE any fix,
measurement, or test run and names no measured actuals.

## STATEMENT

Each recorded followup is landable as a smallest coherent correction
without weakening any gate.

## PREDICTION

- **F1** (capture_window.py `capture_client_pixels`): a failed
  `CreateCompatibleDC` currently flows NULL into `SelectObject` /
  `PrintWindow` and mislabels the refusal as
  `capture_refused:printwindow_refused`. After the fix, forcing the failure
  path (monkeypatched ctypes prototype, self-created fixture window only)
  yields the NAMED fail-closed verdict
  `capture_refused:memory_dc_unavailable`, the new name joins
  `verdict_verdicts()`, and no existing assertion is removed or weakened.
- **F2** (`verify_hwnd_capture(pinned_size=None)`): the None semantics
  (the measured client size is silently adopted as the pin, which makes the
  `window_resized` gate inert for a non-pinning caller) are documented in
  the function docstring AND `docs/THE_WINDOW_CAPTURE_OWNERSHIP.md`; a new
  test asserts the documented adoption behavior on a self-created fixture;
  every in-repo caller keeps pinning (no caller behavior changes).
- **F3** (`docs/evidence/agent_fleet/TRANSPORT_BODY_LIMIT/MEASUREMENT.json`):
  the evidence gains an APPENDED dated correction section
  (`correction_20260911`) embedding the exact payload-measurement one-liner
  and its re-measured output from this worktree; the original block is never
  rewritten; the recorded 1,518,593 B is noted as discovery-context and the
  reproducible variants (transport envelope with `json.dumps` defaults, the
  `--out` artifact) are recorded. `RESULT.md` gains a short appended note
  pointing at the correction.
- **F4** (`tools/agent_fleet/test_controller_transition.py` test_4): the
  `post()` helper closes the `HTTPError` (no ResourceWarning in retained
  output) and the docstring states the actual probe size (+2 KiB above the
  cap, matching `sized(2**24 + 2048)`).
- The full fleet suite from the repo root is green: 0 failures, 1
  expected Windows-symlink skip (187 tests at base tip; the observed count
  is reported with provenance whatever it is), and the transition suite is
  4/4.

## FALSIFIER

Any existing assertion removed or weakened; evidence rewritten instead of
appended; a followup "fixed" by deleting the behavior it describes; or
suite failures.

## Method notes (binding on the run)

- F1 regression forces the failure by monkeypatching the
  `gdi32.CreateCompatibleDC` ctypes prototype/return in the test process
  only (the module's declared argtypes are the window-capture-ownership-02
  fix and stay untouched); fixture windows are SELF-CREATED
  (`ChimeraFixture`) only.
- F2 documents existing semantics; it does NOT change the decision order or
  make pinning mandatory — the recorded finding is documentation, not
  behavior change.
- F3 appends a dated key to the JSON (original bytes untouched otherwise);
  re-measurement runs `python tools/agent_fleet/master_catalogue.py --out
  <temp>` from THIS worktree and an exact in-process one-liner mirroring the
  transport serialization (`client.call` sends
  `json.dumps({'operation': ..., 'arguments': ...}).encode()` with
  `json.dumps` defaults, UTF-8).
- Evidence rule: raw outputs verbatim under this directory; failures are
  retained, never tolerated away. Commit trailer `Agent: subagent-worker-02`
  on every commit. Acceptance stays NOT_CLAIMED until lead review and
  authorized integration.
