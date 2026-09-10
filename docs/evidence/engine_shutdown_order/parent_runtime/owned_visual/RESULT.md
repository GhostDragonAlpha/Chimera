# Final bounded shutdown visual verification

Task engine-shutdown-order-01, generation 1; native source branch head before this evidence: deae5d2e0c9b0ad554ed3e0a23dcb57e0e3cc403. CPU/native cancellation evidence in the parent directories remains part of the certificate.

## Executed native follow-up

Applied the preregistration correction before running: engine `/glass` before close, own GDI backdrop `PrintWindow(PW_CLIENTONLY)` afterward; no desktop pixels read. Parent corrected two gdi32 calls and reserved-alpha handling before the first run. The seven CPU harness checks passed in 0.038 seconds. These check harness structure/ownership refusal, not engine behavior.

Command (PYTHONIOENCODING=utf-8, PYTHONDONTWRITEBYTECODE=1):

```text
python docs/evidence/engine_shutdown_order/parent_runtime/owned_visual/native_visual_run.py --repo E:/ChimeraWork/slot-02 --exe E:/ChimeraWork/slot-02/.tmp/engine_build/Release/chimera_engine.exe --output E:/ChimeraWork/slot-02/docs/evidence/engine_shutdown_order/parent_runtime/owned_visual/run_01 --runtime-name owned_visual_01 --port 8102
```

Exit 0. Owned engine PID 30060, HWND 13308926, listener PID 30060. WM_CLOSE resulted in normal exit, destroyed HWND, and markers admission_closed -> boot_joined -> http_stopped -> engine_shutdown at log offsets 792/819/841/905. No watchdog termination. Owned backdrop PID 46728, HWND 7474906; reference and after hashes both 9c84a2363350f80ffd0eada74513c1b9956d5b573f5064d3f47cecf8721ccf55. Engine image hash 6a35b36aa889cc5a5715ff04f79d6d8cedd4e9645fd6b3b3ac3ecf2230d64858.

The normal executable hash remains 7abcfacb4dade0a776805350b5db22a5789eaee6b5d14d2b87ce4d89ff1583c5, compiled from main.cpp 5fa2bb1301475e8512907f9ae323a97a54335ffdee70fe99e06e304ef41ad8a0. The observed current source hash e1fa75ef528a6800b794f35517454e89b61567ab3468b77a9c0ba98766d8eba7 differs only by the previously documented trailing-newline cleanup. This follow-up did not rebuild or claim a new binary from final source bytes. Runtime binaries/shaders remain private under .tmp; the record includes their hashes.

## Executed DYAD

Root initialized and operated DYAD on each image separately using `dyad_verify.py --senses-repo E:/ChimeraWork/slot-01 --output <dyad_before_01 or dyad_after_01> --image <run_01/engine_before_glass.png or run_01/backdrop_after.png> --prompt <before_prompt.txt or after_prompt.txt>`.

Both calls exited 0. Each can_see returned True with qwen3.8-27b-nvfp4-mtp; both actual watch responses reported that exact model and finish_reason stop. Each 13-test policy regression invocation passed. Source hashes remained stable before/after. The explicitly identified senses source comes from integrated PR31, not slot02's older senses file. Requests, exact prompts, raw responses and results are retained in the named directories. Inference had no timeout. No model was loaded, unloaded, or reconfigured.

Before: the eye identified THE ENGINE STUDIO, the empty grid and status UI; it reported overlapping/truncated text and no visible foreign application or error dialog. Root visual inspection agrees with the overlapping text observation. Scene emptiness is expected in this --no-restore lifecycle fixture, not proof of gameplay. The eye's frame-time comparison is an observation about differently labeled counters, not a measured performance defect.

After: the eye identified the painted test backdrop and its disclaimer, with no engine UI or error dialog in that surface. Its claimed black vertical margins are contradicted by pixel_check.json: both edge columns contain only the three intended nonblack paint colors. Font/spacing opinions concern the fixture, not engine product acceptance. The model's statement that this resembles earlier occlusion is not accepted as evidence of foreign-window occlusion.

## Acceptance and limits

The visual observation requirement is satisfied for the two declared owned surfaces. It does not certify desktop exposure, universal screen-capture safety, process absence from pictures, or physics. Process/window and ordered teardown claims rest on the independent native measurements. Earlier pending/nested/boot witnesses and CPU actual-helper mutations remain required evidence. Pending HTTP callers may receive a disconnect; logs certify named cancellation, not delivered HTTP error bodies. Direct Ctrl+C was not separately executed. No performance certificate, operator engine swap, or universal concurrency-safety claim.

Resource bundle admitted at revision 359. Native runner and both inference commands completed; child engine/eye released at revisions 361/362 before GPU release 363. The user's model remains loaded. Historical failed captures and dark-eye results remain preserved; this record supersedes their open visual gate without rewriting them.
