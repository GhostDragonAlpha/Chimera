# ENGINE-DEMO-01 final review record

Claim: `engine-demo-01`, generation 1, slot 1. Primary project objective remains
the full evolving Master list. This is one bounded native membrane milestone.

## Final source and executed checks

Native source and strengthened gate are committed at `7cea724d` (full commit
in Git). The final C++ SHA256 is
`8ac34e4bc28af1d008dacceeb39c38f25d8dba85c0887af3db80f3e8cca72020`.
Final executable SHA256 is
`fd9c63e2e07b56c17f994a826ff4b2f06905c5757cb5bca00fa097d66af15ffa`.
Build identity deliberately retains the then-dirty source parent instead of
pretending the later source commit already existed at build time.

Commands executed from `E:/ChimeraWork/slot-01`:

```powershell
cmake --build .tmp/engine_build --config Release --parallel 4 --clean-first
python -B docs/evidence/engine_demo01/test_reset_gate.py -v
python -B tools/demo_runtime_verify.py --base http://127.0.0.1:8101 --identity docs/evidence/engine_demo01/reset_review_identity.json --output docs/evidence/engine_demo01/reset_review_after
python -B tools/membrane_demo_client.py gate --launch E:/ChimeraWork/slot-01/.tmp/engine_runtime/reset_review_01/chimera_engine.exe --port 8101 --base http://localhost:8101 --capture-phi 0.35 --capture-radius 3.0
```

Set `PYTHONIOENCODING=utf-8` and `CHIMERA_MD_EDGE=1` for the native gate. Each
native executable and shaders was copied into a fresh private runtime folder.
No binary in the protected engine build tree was used or modified.

Results: clean-first build exit 0; five fake-request tests pass; two strengthened
reset checks pass; unchanged frozen runtime gate has 20 PASS and 1 INFO, exit 0.
The gate terminates its own launched process; its logged termination return
code is not the numerical gate verdict. Historical pre-repair failures remain
in `reset_before/`. Successful reset does not test injected GPU failure.

## Final profile capture procedure

The derived camera is preregistered in `PROFILE_PREREGISTRATION.md`. On the
owned native process PID 9032, endpoint 8101, save then recall `/cameras`
bookmark `reset_review_profile` with `v=[3,0,0,0,0.5,0,0,0]`. Capture initialized
state using GET `/membrane_demo`, GET `/frame`, GET `/membrane_demo`. Then POST
`/membrane_demo` with `{"op":"run","n_steps":256}` and repeat the capture
sequence. The actual relaxed iteration is 126, terminal `stagnated`.

`profile_review/*_manifest.json` records identities, image hashes and request
times. The shader hash convention is SHA256 over sorted relative shader path
bytes (slash separators), NUL, then each file's bytes. Both validator results
are `consistent_snapshot`, with render submission identity `unbound`.

Run `senses.can_see()` before one-image `senses.watch_one(path,prompt)` calls.
Prompts, raw responses, served model, timestamps and finish reasons are retained
in `profile_review/`. Both completed. The relaxed profile remains visually
ambiguous; no acceptance threshold was lowered to change that outcome.

## Drain and limits

After capture and inference completion, PID 9032's executable path was verified
against its private runtime, its own window closed, and `WaitForExit` returned
true. Engine, DYAD and GPU reservations were released in that order at live
controller revisions 192–194. Operator engine and Security dialog untouched.

See `docs/THE_ENGINE_DEMO.md` for earlier failed UI attempts, source-specific
scheduler checks, sparse-checkout eye prerequisite failure, and remaining
Studio/capture-identity requirements. GPU functional evidence here is not
performance, fluid, elastic-material, physical-time or human certification.
