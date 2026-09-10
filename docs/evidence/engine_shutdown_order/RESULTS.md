# Engine shutdown order generation 1 results

Source base verified at `0e878758aa5eb4ad8fbd98648d59a8356e41f4fe`; only `ChimeraEngine/engine/main.cpp` is modified. The pre-existing untracked elastic evidence directory was preserved.

## Source changes

- Added `ShutdownCancellation` and `g_shutdown_closing` admission state.
- Replaced all 27 render handoff `condition_variable::wait_for` calls across the nine channels (`mem`, `md`, `mesh`, `hinge`, `water`, `gait`, `volp`, `frost`, `skin`) with the cancellation helper.
- Added mutex-held notifications for all nine channels at shutdown. The helper rechecks the applied predicate under the channel lock, preserving already-applied success.
- Wrapped the shared API in a specific cancellation catch. Recursive `/session` calls return child failure and cannot produce restore success after cancellation.
- Replaced detached boot restore with an owned, cancellation-aware thread and explicit join.
- Added Ctrl+C admission closure polling in the main loop; the handler only sets the atomic and returns `TRUE`.
- Added flushed shutdown markers and orders them as `admission_closed`, `boot_joined`, `http_stopped`, `engine_shutdown`.
- Added an optional `CHIMERA_SHUTDOWN_TEST` private build witness: `CHIMERA_SHUTDOWN_TEST_HOLD` holds membrane-demo pending consumption while message pumping continues, and emits `shutdown_test: wait_entered` / `md_pending_held`.

## CPU evidence

The standalone extracted lifecycle helper harness (`harness.cpp`) compiled with MinGW CMake and exited 0. Output is retained in `cpu_run.txt`:

- `channels: cancelled=9/9`
- `already_applied: result=success`
- `late_admission: rejected`
- `boot: joined=yes cancel_ms=0`
- `api: waiting=yes` followed by `api: cancelled=yes`
- `mutation: early_return_rejected=yes joined_after_release=yes`
- ordered shutdown markers in the registered order

This harness has no engine header, public debug API, Vulkan, native runtime, or GPU dependency. Parent-owned native runtime evidence is required for actual executable teardown.

## Limits

The cancellation helper only changes waits that have not already applied their operation. Existing non-CV polling loops and arbitrary user callback cancellation remain bounded by their existing behavior; no timeout values were changed. Native proof must ensure an actual API wait is outstanding before closing the window and must preserve the ordered markers.
