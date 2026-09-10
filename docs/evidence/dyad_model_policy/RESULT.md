# Permanent DYAD model result

The checked-in policy selects `qwen3.8-27b-nvfp4-mtp` and the exact relative
GGUF path specified by Alan. `MODEL_IDENTITY.json` records the absolute file,
SHA-256, local index and loaded instance. `VISION_PROJECTOR.json` separately
records the companion projector. The operator loaded this model; this task
did not load, unload, replace, or change its 30208-token context configuration.

The model id is read from policy afresh. Saved overrides and backend changes
cannot silently replace it. DYAD disables resident retargeting only on its
private fair-gateway instance, requires the intended id to be loaded, and
rejects missing/wrong response identity. Non-DYAD gateway defaults are retained.

## Executed evidence

`LIVE_20260910_02/` contains the exact requests, raw responses, prompt, owned
engine-client image, CPU output and result. Command:

```text
PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1
python docs/evidence/dyad_model_policy/live_verify.py --output docs/evidence/dyad_model_policy/LIVE_20260910_02 --image E:/ChimeraWork/slot-02/docs/evidence/engine_shutdown_order/parent_runtime/quiet_normal_regression_01/window_before.png
```

The driver ran `python -m unittest tools.test_dyad_model_policy -v`: 13 tests
passed. Actual `can_see` returned true with served id
`qwen3.8-27b-nvfp4-mtp`. One `watch_one` call returned a nonempty report from
that same id, with `finish_reason=stop`. Driver exit was 0. Source and policy
SHA-256 values match before/after in the result. Inference waited without a
timeout; controller admission revision 338 held GPU/eye resources, released
after the completed process at revisions 350 and 351.

The first run `LIVE_20260910_01/` failed in this task's recording wrapper:
the gateway returns a buffered response without a `close()` method. That
wrapper and failure are preserved. The corrected wrapper saves response
bytes and calls close only when provided. The failed run did not establish
capability; its raw response bodies were not retained because that wrapper
failed before writing them. No failure was rewritten as a pass.

## Observation boundary

The eye identified an empty Studio dashboard, a small grid, and text overlap.
It did not see clear evidence of an error dialog, but expressed uncertainty
about overlapping UI elements. Its FPS/frametime interpretation is an eye
observation requiring measurement, not a new performance finding. It correctly
stated that one still cannot prove shutdown, cancellation, motion, physics,
or the executable identity. Build/process identity and shutdown ordering
remain the separate numerical/runtime records in PR27. The source image is
the owned client capture from that recorded native run; this task did not
start a new engine process or take an operator-desktop screenshot.

Permanent selection and live served-identity verification pass their bounded
gates. This is not physics certification, presentation acceptance, or proof
that an already-running old client has loaded the new source policy.
