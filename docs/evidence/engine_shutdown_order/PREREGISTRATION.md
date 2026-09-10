# Engine shutdown order generation 1 preregistration

Commit under test: `0e878758aa5eb4ad8fbd98648d59a8356e41f4fe`.

## Statement
Once shutdown admission closes, no new shared API operation may begin; all render handoff waits must observe cancellation without converting an unapplied operation into success; the HTTP worker and boot-restore worker must stop and join before `Engine::shutdown()` invalidates console, log, UI, and Vulkan state.

## Prediction
A CPU lifecycle harness with delayed boot/API callbacks and each of the nine render handoff channels will observe the ordered markers `closing → boot_joined → server_stopped → engine_shutdown`. Every wait will wake on closing and return a cancellation result unless its associated applied predicate is already true. Ctrl+C will set the close request and the loop will reach the same ordered tail.

## Falsifier
Any API entry after closing, detached boot callback after engine shutdown, server or boot worker still live when `Engine::shutdown()` starts, a wait that remains blocked after its channel notification, or a cancelled unapplied operation reported as success falsifies this theory. A lost wake caused by notifying without the channel mutex also falsifies it.

## Scope
Implementation is main-only: `ChimeraEngine/engine/main.cpp`, this contract, and CPU evidence. Existing `Engine::shutdown()` console-worker join and Vulkan/UI ownership remain the engine owner. No public debug API, engine header change, GPU launch, or runtime claim is part of this preregistration.

## Optional native witness (preregistered before any instrumented run)

A private `CHIMERA_SHUTDOWN_TEST` build may set `CHIMERA_SHUTDOWN_TEST_HOLD` to withhold membrane-demo pending consumption while the normal Windows message pump continues. The helper emits `shutdown_test: wait_entered` before its real wait. This test-only compile path has no production behavior or public API and does not alter timeout values. The native falsifier is a verified outstanding `/membrane_demo` wait followed by `WM_CLOSE` that lacks cancellation and the ordered shutdown markers.
