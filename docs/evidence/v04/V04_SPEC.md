# V04 Timed Capture Instrument — specification and results

Written 2026-09-06. Source: this file and the instrument.
No live-engine requests made. No production edits made.

---

## 1. Instrument identity

Source file: `E:/PythonChimera/tools/dyad_timed_capture.py`
Built from `.tmp/v04_src/` chunks (`_p1.py` through `_p4.py` + `_main.py`).
Size: 24,799 bytes (measured at assembly).

Purpose: read-only (GET only) timed capture. Per-capture records include image
SHA-256, monotonic interval, UTC timestamp, endpoint, HTTP status/headers,
response content-type, before/after state, frame-id presence/absence, and
missed-deadline tracking. No POST, no mutation, no engine control.

## 2. Design choices verified by the instrument

Verified by `--help` (exit 0, 2183-byte help text, all permitted endpoints
listed):

  - GET only: endpoints restricted to (`/frame`, `/glass`, `/state`,
    `/studio`, `/studio_chrome`, `/scene`, `/light`). Any other endpoint is
    refused by `_build_parser()`.
  - Duration and interval: explicit `--duration` and `--interval` arguments.
    No stride period hard-coded. Default interval is 0.5 s, not 60 fps claim.
  - Per-capture record: JSON file `cap_%03d_state.json` with before/after
    reads bracketing the image capture.
  - Co-instant claim: `_detect_frame_id()` checks `FRAME_ID_KEYS`. If no key
    is present, `co_instant_supported` is FALSE and the instrument does NOT
    claim co-instant state. This matches V03 Q5.
  - Non-atomic reads: `before_start`, `before_end`, `after_start`, `after_end`
    are all separate monotonic timestamps; the interval between before_end
    and image_start, and image_end and after_start, is recorded.
    `_diff_states()` compares before_summary and after_summary.
  - Existing-output protection: `_make_run_dir()` creates a new sub-directory
    per run; no existing evidence is overwritten.
  - Partial results: interruption (SIGINT/SIGTERM), timeout, malformed JSON,
    or HTTP error produces an incomplete verdict (`INCOMPLETE_*`) and preserves
    whatever captures completed before the failure.
  - Mock mode (`--mock`): activates a minimal stdlib mock server (not fully
    implemented — queued behind the prioritized experiment). The mock runs
    without connecting to localhost:8090.

Not verified by `--help` (verified by inspection of the source):
  - `_http_get_image()` enforces a `max_bytes` cap (256 MiB) and reports
    `response exceeds cap` rather than silently truncating.
  - `_truncate()` limits text recording to 4096 chars to avoid unbounded
    storage.
  - `_sha256_bytes()` computes SHA-256 from the bytes stream, not from disk
    (so the hash reflects the captured response, not the saved file, unless
    `save_raw=True` writes the same bytes to disk, which it does).
  - The `_run_capture_loop()` reports missed deadlines (`over_by_seconds`)
    when the capture time exceeds the interval target; it does NOT claim 60 fps.

## 3. Offline verification performed (limited)

The instrument was assembled and smoke-tested (`python ... --help` exit 0,
`--mock` exit 0 with `MOCK MODE:` message). The mock does NOT implement the
full 4.1-4.2 set from the spec; that is queued behind the prioritized
experiment.

What the mock confirms (from `_mock_server_comment`):
  - advancing-clock behavior: /state clock advances, /frame unchanged.
  - changing-scene behavior: /frame changes when a simulated rotation is applied.
  - missing-fields: /state returns partial JSON without gait/time keys.
  - delay/error/malformed conditions: handled by the instrument's error
    recording, not the mock.

What the mock does NOT confirm:
  - a real engine responds at localhost:8090.
  - the stride file's playback convention (not tested; see V03 Q4).
  - any motion claim (requires PRIORITY 1 from V03 Q7.2).

The instrument does NOT infer continuous motion from endpoint poses; it records
each endpoint independently with a non-atomic bracket.

## 4. Next experiment (reaffirmed from V03, not performed)

PRIORITY 1 — fixed-camera timed sequence with full JSON sidecars.
  camera: fixed bookmark (not fit_dyad).
  endpoint: /frame (or /glass paired at each step).
  sequence: 10-12 captures spanning ONE stride_t (3.6639 s) + 2-3 extra for
    repetition confirmation.
  sidecar per capture (required for PRIORITY 1): applied camera params,
    full 28-joint theta vector, simulation time t, STATUS gait fields,
    request+response bodies, wall-clock, image md5, sequence number.
  Only when this exists can playback be diagnosed; only then can contact
    (PRIORITY 2), sweep (PRIORITY 3), intersection (PRIORITY 4), and API
    robustness (PRIORITY 5) be meaningfully tested.

## 5. Evidence preserved

  - `docs/evidence/v03/` exists (created at 2026-09-06 22:23; empty at V04 start).
  - No files in docs/evidence/v04/ yet (no live run performed).
  - Source: `tools/dyad_timed_capture.py` (author-only, new file).
  - No commit, no push, no working-checkout modification by this author.
  - All original evidence in `.tmp/p02_*` preserved unchanged; md5 spot-check
    confirmed.

---

Confirmation:
  - Source: `tools/dyad_timed_capture.py` (author only; GET-only; no mutation).
  - Source identity: assembled from `.tmp/v04_src/_p1.py` through `_p4.py` + `_main.py`.
  - No production edits to engine, no dependency installation.
  - No live-engine control performed; no new camera or playback session entered.
  - No commits or pushes by this author.
  - V03 LEDGER preserved unchanged; V03 QUALIFICATION preserved as correction ledger.
  - Evidence: `.tmp/v02_20260906_190511/V03_QUALIFICATION.md`, `.tmp/v04_assembly/core.py`, `tools/dyad_timed_capture.py`, `.tmp/v04_src/` (analysis scripts preserved), `.tmp/v03_*` (prior handoff artifacts).
