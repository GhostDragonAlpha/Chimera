# KNOWN_SKIPS — MAT2-G02 named-check suite

- `test_C6_camera_record_and_clean_pairs` (CaptureChecks): SKIPPED until the
  visual capture is built. Reason: the check asserts the capture manifest's
  camera records and clean/diagnostic pair identity; the capture is the NEXT
  artifact in the chain (render_run -> make_capture per CODEC_STANDARD), and
  the suite must already run green at batch_gates time BEFORE the capture
  exists (the named-check gate runs on every batch). The check unskips
  itself once capture_validation_receipt.json exists and MUST be green
  before submission.
- `test_C6_clean_diagnostic_state_hash` (CaptureChecks): same reason and
  same unskip condition; asserts the state-hash preservation across view
  toggles recorded in the capture validation receipt.

Both checks are part of the done_when evidence (profile falsifier: mismatched
clean/diagnostic state fails) and are verified green in the final submitted
state.
