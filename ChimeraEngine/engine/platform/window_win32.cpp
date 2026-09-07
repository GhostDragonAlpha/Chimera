// P06 — window/input backend A: Win32 (DECLARED, NOT IMPLEMENTED).
// This file is the P06 contract for the Win32 window backend; its body lands
// in the Inc-3 increment (engine.cpp creation/pump migration) so the engine's
// source is not touched by P06. What it MUST do when implemented (verbatim
// from the current engine.cpp, see P06 spec §4.3):
//   create_window  — RegisterClassEx("ChimeraEngine") / AdjustWindowRect /
//                    CreateWindowEx(WS_OVERLAPPEDWINDOW…) / bar-off-screen
//                    clamp (MonitorFromWindow+GetMonitorInfoA+SetWindowPos) /
//                    ShowWindow / UpdateWindow (engine.cpp:249-299);
//                    `native` = HWND, client_w/h = actual client extent.
//   destroy_window — DestroyWindow + null `native`; idempotent (engine.cpp:932).
//   native_handle  — the HWND as void*, forged for plat::create_surface's
//                    void* parameter (the surface seam owns nothing).
//   pump_events    — PeekMessage drain (one call = one drained batch, FIFO),
//                    Translate + Dispatch, WM_QUIT/WM_CLOSE -> exit_now=true
//                    and NOT emitted as InputEvents (main.cpp:2510-2522);
//                    WM_SIZE -> kResize; WM_(SYS)KEYDOWN/UP + bit-30 -> repeat;
//                    WM_CHAR -> kChar; mouse arms -> client coords; wheel ->
//                    ScreenToClient applied BEFORE kWheel emission; WM_DESTROY
//                    keeps PostQuitMessage via the WndProc tail.
#include "platform/window.h"

namespace plat {
// P06: compilation unit walls only — see the contract above.
} // namespace plat