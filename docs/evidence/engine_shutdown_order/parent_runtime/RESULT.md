# Parent native results: numerical lifecycle supported, DYAD open

Current main.cpp SHA256: 5fa2bb1301475e8512907f9ae323a97a54335ffdee70fe99e06e304ef41ad8a0.
Normal MSVC executable: 7abcfacb4dade0a776805350b5db22a5789eaee6b5d14d2b87ce4d89ff1583c5.
Instrumented executable: 554887e4a6d0e0f7ee92c763e3573d24562aa7dcc76da38b913260c4c727f14c.
Every run records per-shader hashes, exact owned PID/HWND, listener identity and executable location.

Configuration used Visual Studio 17 2022 x64, MSVC 19.44.35228, Vulkan SDK 1.4.328.1, private slot02 .tmp build directories. The first test configuration replaced CMAKE_CXX_FLAGS with only the test define and lost /EHsc; its compiler warning and output are preserved in configure_test.log/build_test.log and are NOT accepted runtime evidence. Before any native launch it was corrected to /DWIN32 /D_WINDOWS /W3 /GR /EHsc /DCHIMERA_SHUTDOWN_TEST and rebuilt clean-first (v2 logs). The normal build uses the unchanged default /DWIN32 /D_WINDOWS /EHsc and has no private test macro.

Executed native_run.py with the corresponding --exe, --case, --run and --instrumented flags:

| Retained run | Executed observation | Exit |
|---|---|---|
| pending_01 / pending_02 | Actual membrane-demo wait held, cancelled, all shutdown markers ordered, HWND destroyed | 0 |
| nested_01 / nested_02 | Actual /session restore entered /mesh_bin wait; cancellation produced replayed=0, failed=1, ok=false; ordered teardown | 0 |
| boot_test_01 | Boot wait entered; close cancelled it before any restore invocation; joined before engine shutdown | 0 |
| quiet_normal_01 | Ordinary native build, quiet WM_CLOSE, ordered teardown and HWND destruction | 0 |
| quiet_normal_regression_01 | Ordinary build, existing demo_runtime_verify gamma/reset and step/reset gates passed, then normal close | 0 |

Each close finished before the preregistered ten-second watchdog; no native process termination was needed. Instrumented builds also invoked the actual shared API after Engine::shutdown and observed explicit shutdown cancellation. The native pending client received a transport disconnect: a cancellation response body is not guaranteed after HttpServer::stop. The named API cancellation and nested negative result are independently retained in stdout; this is not claimed as a delivered HTTP error response. Direct Ctrl+C delivery was not separately executed; native WM_CLOSE exercises the common teardown tail.

Initial screen captures were occluded; they are disqualified and preserved privately outside publication, as their adjacent notes explain. The corrected runner raises only its own window, verifies visible point ownership, and captures its client rectangle. Retained engine-only /glass images are separate from actual screen captures. Parent inspected corrected captures: a native Studio window is visible, with an empty/narrow viewport and overlapping status content at the test window size. No polished presentation or visible physical-state linkage is claimed. No screenshot alone proves cancellation or physics correctness.

DYAD can_see returned false with NoModelLoaded. No model was selected, loaded or evicted. No watch_one verdict exists. The DYAD acceptance gate remains OPEN; this candidate may be published for review but is not ready for final task acceptance. GPU, engine and eye reservations were released after owned processes/probes drained (controller revisions307-309). No performance certificate or operator engine swap.

Final formatting-only adjustment removes the trailing blank line reported by git diff --check. Tested source hash above predates this final newline cleanup; final source SHA256 is e1fa75ef528a6800b794f35517454e89b61567ab3468b77a9c0ba98766d8eba7. Byte comparison confirms only trailing CR/LF bytes changed; the C++ program and helper text are unchanged. No fresh runtime run is claimed for the whitespace-only delta.
