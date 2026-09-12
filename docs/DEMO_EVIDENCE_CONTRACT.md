# Native demo capture correspondence

## Preregistration

**Statement:** a capture manifest can establish a bounded correspondence
between one native demo control interval and the bytes saved by its caller,
provided the source, process, request interval, status IDs, and image hash all
agree.

**Prediction:** an unchanged valid before/after status with matching capture
bytes returns `consistent_snapshot`; changed accepted state returns
`changed_during_capture`; missing IDs, nonfinite values, source mismatch, or a
swapped image returns `insufficient_evidence`.

**Falsifier:** a deliberately changed accepted-state ID, swapped image, stale
or missing identity, malformed/nonfinite status, or reversed timestamp is
accepted as a consistent snapshot.

## Scope and schema

`tools/demo_evidence.py` validates a JSON record containing:

```json
{
  "source": {"commit": "…", "executable_sha256": "…", "shader_sha256": "…"},
  "endpoint": "http://127.0.0.1:8103",
  "process": {"pid": 1234, "exe": "…"},
  "before": {"accepted_state_id": 1, "render_state_id": 0, "iteration": 0,
              "energy": 2.625, "centre": [0, 0, 0.125]},
  "after": {"accepted_state_id": 1, "render_state_id": 0, "iteration": 0,
             "energy": 2.625, "centre": [0, 0, 0.125]},
  "capture": {"path": "frame.png", "sha256": "…"},
  "request": {"started_utc": "…", "finished_utc": "…"}
}
```

The validator checks the capture bytes, exact source/process/endpoint identity,
status shape and finite numeric values, nonzero accepted-state IDs, and ordered
timestamps. An optional expected-identity object must match the record exactly.
It reports `consistent_snapshot` only when the accepted IDs are equal and all
checks pass, or `changed_during_capture` when the IDs differ. Missing or
contradictory evidence reports `insufficient_evidence` with named reasons.

`render_submission_identity` is always `"unbound"` in this schema. The optional
`render_state_id` values are reported as presence data only; even nonzero IDs do
not prove submission, completion, or frame linkage. The result is a bounded
before/after snapshot correspondence; it does not claim that the captured PNG
was the exact GPU submission or physics certification.

The writer CLI refuses to overwrite an existing output path and creates parent
directories only under the requested output directory. Failed validations are
preserved in their output record.
