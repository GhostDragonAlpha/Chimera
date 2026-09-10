# HTTP lifecycle generation 2 review results

Prior `docs/evidence/engine_http_lifecycle/gen2/` records are unchanged. This review uses the current dirty source in `ChimeraEngine/engine/http_server.cpp` and `.hpp`, compiled by the durable `gen2_review/CMakeLists.txt`, whose engine path is relative to the evidence directory.

## Fresh CPU matrix

The executable was built with CMake MinGW Makefiles in private `.tmp/engine_http_lifecycle_gen2_review_v2` and run once per mode. Every mode returned exit code 0; raw stdout/stderr are in `runs/`:

- `quiet`: stop returned (`STOP_RETURN quiet ms=15`).
- `partial_header`: stop returned (`STOP_RETURN partial_header ms=16`).
- `partial_body`: stop returned (`STOP_RETURN partial_body ms=16`).
- `local`: GET and POST passed.
- `blocked_send`: handler entered and stop returned after cancellation (`entered=yes stop_ms=31`).
- `finite_callback`: `entered=yes held_before_release=yes callback_exited=yes stop_returned=yes`.
- `cycles`: five `SAME_OBJECT_CYCLE n PASS` lines. Each cycle starts/stops the same object, calls stop twice, and checks a second start is refused.
- `mutation_gate`: `early_return_rejected=yes callback_exited_after_join=yes`. The test double's worker is joined only after release, so the live object is never destroyed unsafely.
- `start_failure`: occupied second start failed and restart passed.
- `destructor`: destructor returned cleanly.

The finite callback assertion now observes `stop_returned` directly; `thread.joinable()` is not used as a proxy for completion.

## Scope

These controls verify the socket worker lifecycle and the finite callback caller contract. They do not prove cancellation of an arbitrary callback or whole-engine shutdown ordering.
