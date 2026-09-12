# Engine shutdown order contract

Generation 1, source commit `0e878758aa5eb4ad8fbd98648d59a8356e41f4fe`.

The main process owns the cross-component shutdown order. `main.cpp` closes API admission, wakes every render handoff channel under its mutex, cancels and joins boot restore, explicitly stops HTTP, and only then calls `Engine::shutdown()`. The engine remains the owner of its console-worker join and Vulkan/UI destruction.

`wait_for_shutdown()` preserves an already-applied result by checking the predicate under the channel lock before throwing the named cancellation marker. The API wrapper catches only that marker and returns a JSON failure; recursive `/session` replay therefore counts a cancelled child as failed rather than reporting restore success. Ordinary endpoint exceptions remain visible to existing process behavior.

The CPU harness is a standalone extraction of the main lifecycle helper and channel protocol. It has no engine header, public debug API, Vulkan, or native runtime dependency. Native validation of the actual executable belongs to the parent runtime evidence.

## Parent correction and acceptance boundary

The initial CPU harness/results are historical and superseded: its helper was a handwritten twin, marker order was a tautology, boot cancellation began with closing already true, and a mutation wrote applied without its mutex. Parent CPU evidence now compiles verbatim production helpers and rejects three injected faults. The boot notification uses its matching mutex. All original failed/superseded evidence remains retained.

Fresh MSVC native tests support quiet, boot-delay, outstanding-request and nested-restore cancellation ordering. The existing membrane reset regression also passed in the ordinary build. See docs/evidence/engine_shutdown_order/parent_runtime/RESULT.md for exact source/artifact identities, transport-disconnect limitations, capture exclusions and executed commands. DYAD could not run because no model was loaded; its gate remains OPEN. No final acceptance or performance claim.

## Final visual follow-up (2026-09-10)

The historical dark-eye gate above is superseded by parent_runtime/owned_visual/RESULT.md. An unchanged ordinary executable passed owned-window shutdown with ordered markers and no watchdog. Root operated two separate one-image DYAD calls using the integrated permanent-model policy: both returned qwen3.8-27b-nvfp4-mtp with finish_reason stop. The before image is engine swapchain readback; the after image is a separately owned GDI backdrop. Those observations satisfy the corrected visual contract and do not establish desktop exposure or numerical correctness. Earlier CPU/pending/nested/boot evidence remains required; pending transport may disconnect and direct Ctrl+C remains untested. No performance certification.
