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

## Certified-world hero disclosure record

**What:** the hero still `hero_tick150` (sha256
`9efd86ce3054e9eccb1c1996768e8a00c447186701ff6a5beb49777a72375e2b`) contains a
known render anomaly: the small sharp-edged white disc upper-right of the sky
is an AUTHORED decorative cloud cluster (`sky-sun/sky_sun.py` `build_clouds`,
layer 6, one 12-blob cluster at 6.3-6.6 km, az ~200 deg el ~28 deg) whose
stacked alpha Gaussians read as a "second sun" beside the single authored sun.
Diagnosis (pinned root cause, HIGH confidence): DEFECT 1 in the Sergeant lane
report `world-build-20260928/visual-defects/VISUAL_DEFECTS.md` (2026-09-29);
not a duplicate sun, flare, bloom pass, or blending double. Both later
records that touch the region (`composition3-trunk/RESEAT_RECEIPT.md`,
`game-loop-design/GAME_LOOP_R3_STUDY.md` section 5) defer to that diagnosis
and record the Captain question as open.

**Where:** the demo page's certified-world sealed-captures surface. The
disclosure is a `"disclosure"` field on the `hero_tick150` entry in
`tools/product_viewer/certified_world.json`, rendered by
`certified_world_section()` in `tools/product_viewer/server.py` as one
amber line between the hero image and its caption (server-built HTML, zero
page JS). It passes through `load_certified_world()` untouched and appears in
`/api/world/certified` like the other entry fields.

**Why:** Captain decision, docket 2026-09-30 (decision #1): the anomaly is
DISCLOSED, not re-authored — VISUAL_DEFECTS.md Option A (disclosure-only, no
pixels change) was selected over Option B (re-author `build_clouds`, which
would invalidate every downstream composed buffer) and Option C (scene-scoped
re-framing, ineffective for the hero). The hero is not re-authored; no
re-render, no sha re-pin, and the sealed-capture contract (served bytes equal
the pinned file bytes) is unchanged. The disclosure is declared page copy for
a known anomaly; it is not a refusal and does not alter the verification
state of the entry.
