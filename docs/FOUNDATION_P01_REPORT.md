# P01: portable test boundary and extraction inventory

ASTRA, 2026-09-06. Alan authorized proceeding with the portability plan.
Scope selected by architecture review: inventory plus a native portable capture-code
test target. No window/backend replacement before the Windows baseline is available.

## Rule 0 — recorded before implementation/run

STATEMENT: the engine's existing RGBA-to-PNG encoder can be built and tested as shared
C++ on Linux without importing Windows, Vulkan or Studio window dependencies. Separating
this test target leaves the Windows executable and its CMake default behavior unchanged.

PREDICTION: an independently decoded PNG reproduces every channel of the supplied bytes
exactly for (1,1), (7,3), and (257,65) fixtures. The large fixture crosses the encoder's
65,535-byte stored-deflate-block boundary. Consecutive fixture images are distinguishable.
PNG CRC/Adler verification and channel/orientation checks catch corruption, wrong pixels
and swapped frames. Header inclusion must work as the first include in a C++17 TU.

FALSIFIERS: compile failure due to hidden platform/include dependencies; any pixel differs;
invalid chunk CRC/size/format; a corrupt, swapped-frame or channel-swapped negative control
passes; Windows production build configuration is changed; protected build files change.
All pixel differences have a zero tolerance because this is lossless byte transport.
This is not a force/physics test, renderer run, frame-timestamp certificate or DYAD verdict.

The fixture dimensions and channel patterns are declared synthetic instrument controls.
They are not material constants, render resolutions, or pictures of a simulated object.

## Dependency inventory and proposed ownership

Sources under ChimeraEngine/engine, audited at the current architecture branch containing
master 7cafb332. This is a source inventory, not a claim every legacy path executes.

| Service | Current evidence | Proposed ownership |
|---|---|---|
| Window/event dispatch | engine.cpp: WndProc, HWND, CreateWindowEx; main.cpp: PeekMessage/TranslateMessage/DispatchMessage | Win32 backend; platform-neutral event representation handed to shared application |
| Input semantics | camera/console/mode toggles mixed inside WndProc; g_keys stores Win32 virtual keys | Preserve shared behavior; translate native keys/text/mouse before processing |
| Surface/presentation | Win32 instance extension mandatory; VkWin32SurfaceCreateInfoKHR; swapchain initialization and resize | Backend extension/surface provider; shared presentation target policy |
| Capture | offscreen /frame and composited /glass differ; PNG encoder has no OS include | Keep both scopes explicit; shared encoding/metadata; platform window capture only if needed |
| Fonts | ui.cpp GDI font/bitmap/text functions | Font atlas provider, keeping GDI first; metrics are part of UI baseline |
| Files/path lookup | main.cpp shader path fallback, module path, directories, delete operations; UI file metadata | Portable filesystem helpers where semantics match; backend executable-path query |
| Socket transport | http_server.hpp leaks SOCKET; cpp uses WSAStartup/closesocket/WSACleanup; main includes Winsock | Platform socket ownership behind narrow transport seam; retain API behavior |
| Shared memory (new inventory finding) | shared_mem.hpp uses HANDLE, Create/OpenFileMapping, MapViewOfFile, UnmapViewOfFile | Named shared-region backend; preserve packet layout and explicitly audit synchronization before POSIX port |
| Timing/shutdown | Sleep, timeBeginPeriod and console handler in main; Sleep in engine idle path | Portable pacing/monotonic time plus Windows-specific timer lifetime; separate simulation time |
| Build/tool discovery | fixed Vulkan SDK, .exe compiler search, Windows libraries | Portable imported dependencies plus platform-specific link selection in later stage |

The shared-memory ring is an additional boundary missing from the initial platform
decision. Do not silently drop it on Linux or claim that swapping the window library
alone ports the application. The ring's concurrency semantics need their own test;
mapping the same bytes does not establish synchronized access.

## Exact first extraction interfaces (proposed, not implemented)

1. `WindowBackend`: create/destroy, poll normalized events, framebuffer extent, pointer
   capture, required instance extensions, create Vulkan surface. No material state.
2. `ApplicationInput`: consumes events and owns existing camera/console/action semantics.
   Preserve autorepeat, keyboard focus, text entry, mouse capture and resize behavior.
3. `PresentationTarget`: acquire/current image/submit/present for window mode; explicit
   offscreen image path for headless mode. No acquire/present call in headless mode.
4. `FontAtlasProvider`: returns pixels plus measured glyph metrics for one declared font.
5. `SocketTransport` and `SharedRegion`: OS resource lifetimes without Windows handle types
   in shared headers. Keep protocol parsing and packet definitions shared.
6. Filesystem/clock calls use standard C++ where adequate; do not wrap standard facilities
   gratuitously. Executable path and console/signal lifetime remain platform-specific.

Dependency direction: shared application/engine -> interfaces -> selected backend.
Vulkan device/queue feature selection must work without a presentation surface for the
eventual headless path. Existing offscreen rendering currently follows surface setup;
it is not a standalone headless boot sequence.

## Windows baseline admission checklist

All NOT RUN here: launch/current scene; viewport rendering; Studio text; keyboard input
while console open; camera orbit/pan/zoom; resize/minimize/restore; HTTP responsiveness;
shared-memory producer/consumer if active; /frame versus /glass; ordered motion captures;
human interaction and DYAD assessment. Obtain original captures, input sequence, build and
scene identities before window extraction. No backend change is certified in their absence.

## Measurements

Preregistered before execution; results appended 2026-09-06.

`python tools/platform_probe/check.py` exited 0: **9/9 checks passed**. The native
C++17 fixture compiled on Linux and used the existing engine PNG header without edits.
Four synthetic fixtures reproduced **66,992 channel bytes exactly** (zero byte error),
including a 257-by-65 image crossing the 65,535-byte DEFLATE block boundary.
Independent checks rejected an invalid CRC, a substituted frame phase, and swapped
color channels. These are instrument checks, not rendered engine frames.

The supplied-executable route also exited 0 with **8/8 checks passed**; it does not
count compilation as a check and explicitly records that the executable was not rebuilt
in that invocation. Both routes preserve their reports in unique `.tmp/platform_probe/`
directories. Initial run: `run_m4nsbxlx`; supplied-executable run: `run_e6ib3721`.

Checked-out header SHA-256:
`924e4da9876ed043d3e572b7467aabd830288d10124a71d047670ab036f8b30a`.
Fixture executable SHA-256:
`880023c628251e1dd878011e5dc790564cdc35b972d8c4f8b65d6891c7c50cbb`.
The checker records separate source and executable identities; a supplied binary's
identity alone does not establish its source provenance.

**Evidence limits:** Windows/MSVC, the optional standalone CMake route, Vulkan rendering,
live engine execution, DYAD visual review, and human acceptance are NOT RUN here.
CMake, Vulkan headers/shader compilers, a usable display and GPU device were unavailable.
The Vulkan loader's presence does not establish a usable Vulkan implementation.
No production source, production build configuration, or protected build file changed.

**Next extraction gate:** obtain the Windows baseline listed above, then implement the
first scoped OS boundary while preserving that behavior. Include named shared memory
alongside window/input, clocks, filesystem, sockets and font rasterization; preserve its
packet layout and audit synchronization separately. A GLFW window alone cannot replace
the existing GDI text or Windows shared-memory services.
