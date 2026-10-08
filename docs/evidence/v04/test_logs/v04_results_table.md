# V04 Offline Verification Results
Mock server reference: .tmp/v04_src/_mock_server_impl.py (minimal; queued behind PRIORITY 1)
Instrument: E:/PythonChimera/tools/dyad_timed_capture.py
No live-engine requests made. No mutation endpoints POSTed.
Results generated: 2026-09-07 19:52:20Z

| case | mode | expected (brief) | exit | PASS/FAIL | log |
|---|---|---|---|---|---|
| repeated_advancing | advancing | Same PNG repeated; clock advances; no scene change dete | 0 | PASS | repeated_advancing.log |
| changing_fixed_camera | changing | Different PNG at each step; scene change detected. | 0 | PASS | changing_fixed_camera.log |
| missing_fields | missing | Partial state; UNKNOWN for missing gait/time fields. | 0 | PASS | missing_fields.log |
| delayed_deadline | delayed | Delayed image response; over_by_seconds > interval. | 0 | PASS | delayed_deadline.log |
| http_error | error3 | Every 3rd /frame HTTP 500; error recorded; partial pres | 0 | PASS | http_error.log |
| malformed_json | malformed | Non-JSON /state body; co-instant claim NOT supported. | 0 | PASS | malformed_json.log |
| state_change_bracket | bracket | Before/after state differ; change detected. | 0 | PASS | state_change_bracket.log |
| existing_output_protected | baseline | Unique new run dir; originals preserved. | 0 | PASS | existing_output_protected.log |

Notes:
- PASS = instrument exits 0 and the expected behavior is met.
- FAIL = timeout, HTTP error, malformed response, or unexpected exit code.
- The full mock (4.1-4.2) is queued behind V03 Q7 PRIORITY 1; these are design-verification tests only.
- Instrument verifies GET-only (READ_ENDPOINTS enforced in parser), non-atomic state bracket, co-instant claim control (FRAME_ID_KEYS), partial preservation, unique-run-dir, missed-deadline tracking.
