# Parent native shutdown verification preregistration

Task engine-shutdown-order-01 generation 1, registered slot02; integrated base 0e878758.

STATEMENT: native window close closes API admission, cancels unapplied render requests with a named negative result, and joins boot/HTTP workers before Engine::shutdown destroys resources. Already applied commands retain their truthful completion state.

PREDICTION: after CPU lifecycle tests pass, a fresh private MSVC build has an identifiable visible native window and loopback listener. Quiet close and close with a witnessed outstanding request exit normally. A test-only build may withhold render consumption while continuing message pumping to witness an outstanding real request deterministically; this instrumentation must be absent from the ordinary build and separately identified. The normal build must also close correctly during the existing boot delay.

FALSIFIERS: exit crash or watchdog termination, no cancellation witness in the pending case, success reported for unapplied work, shutdown-order marker inversion, outstanding owned thread/process after teardown, wrong source/executable/shader/window identity, unrelated process action, or unrecorded test instrumentation. An outstanding case without an observed pending witness is INCONCLUSIVE, never PASS. Existing physical numerical gates and tolerances remain unchanged.

The ten-second process watchdog is a declared test-run safety policy, not a performance threshold or simulation tolerance; it is not widened after observing a failure. Only the exact owned process handle may be terminated after retaining its failure evidence. Native close uses the verified process-owned HWND. No firewall changes, model unloading, or operator engine restart.

Runtime admission: request GPU functionality, engine and DYAD resources as one bundle through the live controller; inspect actual process/device load without claiming a benchmark. Keep each native session, executable, shaders, endpoint and evidence under this slot. No runtime until admission.

DYAD: initialize senses.can_see under reservation; retain served identity. Capture and inspect the real restored engine window before close and the desktop region after owned-window destruction. One image per watch_one call, UTF-8, no inference timeout, numbered non-leading questions about visible windows/content and uncertainty. Record prompts, raw responses/finish reasons and image hashes. Numerical lifecycle results come from ordering/cancellation/process evidence; images establish only visible behavior, not physics correctness or general engine safety.

The baseline CPU source and historical HTTP failure records remain separate. Final runtime outputs bind main.cpp diff/hash, executable and shaders. Broader physical-state behavior is outside this lifecycle certificate.
