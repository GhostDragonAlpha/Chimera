# Owned-backdrop visual follow-up — preregistration correction

Recorded before this follow-up harness is executed.

The earlier instruction to capture the desktop region after the engine window
closed is withdrawn. A desktop-region capture can include unrelated applications;
the initial occluded image demonstrated that risk and is excluded from publication.
This follow-up never reads desktop pixels. The before image is the engine's own
`/glass` swapchain readback after its PID, listener, visible HWND, and presentation
are verified. The after image captures only the backdrop HWND's client surface
with Win32 `PrintWindow(..., PW_CLIENTONLY)`.

**STATEMENT:** The engine's own presented surface before close and an unchanged,
clearly labeled test-owned backdrop after close provide two safe owned-surface
observations at the same declared test layout. `PrintWindow` can render the
backdrop regardless of desktop occlusion, so the pair does not prove what the
desktop exposed. It also does not establish process or window absence; the
process handle, `IsWindow`, listener identity, and shutdown log establish those
facts.

**PREDICTION:** In one ordinary, uninstrumented `--no-restore` run, the before
`/glass` image is bound to the engine PID/HWND and the after capture is bound to the
harness PID/backdrop HWND. `WM_CLOSE` is posted only after rechecking engine HWND
ownership. The native process exits with code 0 before the unchanged ten-second
watchdog, its HWND no longer exists, and the four existing shutdown markers remain
ordered. The backdrop remains owned and its post-close client capture is byte
identical to its pre-engine reference capture.

**FALSIFIERS:** Any ownership mismatch, invalid `/glass` PNG, backdrop capture
failure, capture of an HWND other than the recorded backdrop HWND, changed backdrop
hash, native crash, watchdog action, surviving engine HWND, listener owned by a
different PID, or shutdown-marker inversion is a failure. If the before image
does not visibly identify the engine content, the visual observation is
inconclusive even when the independent shutdown gates pass.

The numeric gates and the ten-second watchdog are unchanged. No executable,
shader, compile flag, model, context, firewall, or unknown window is changed.
The declared UI test rectangle remains `(64, 64, 1280, 720)`, inherited from the
existing parent runtime runner rather than chosen after seeing an image.
