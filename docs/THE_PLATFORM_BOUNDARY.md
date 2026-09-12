# Platform boundary decision and reserved P01 assignment

ASTRA, 2026-09-06. Alan delegated this architectural decision. Status: source-audited
design; no platform port, build, software Vulkan run, or live visual test performed.

## Decision

Keep one C++/Vulkan engine and the Windows implementation working. Extract OS services
behind a narrow interface, then add Linux. The split is at platform services and
presentation, not at materials, membranes, physics, shaders, or authoritative state.
Windows is a backend, not a server Linux must depend on. A remote Windows worker remains
a useful Windows/GPU test target, not a required production host for Linux.

Logical dependency direction:

    application and shared engine -> platform interface -> selected platform backend

Engine laws never depend on a Windows-versus-Linux material switch. Build one native
executable per OS from shared sources. Keep platform headers inside backend files.

## Evidence: audited source based on master 7cafb332

| Location | Coupling requiring extraction |
|---|---|
| engine/engine.cpp | windows.h, WndProc, HWND, CreateWindowEx, key codes, Win32 Vulkan extension and surface creation; resize and input tied into shared camera/state |
| engine/main.cpp | Winsock/Windows includes, message pumping, Sleep/timer setup, application OS services |
| engine/http_server.cpp | Windows-dependent network implementation |
| engine/ui.cpp | GDI font rasterization: CreateFontW, CreateDIBSection, TextOutW; portable window creation alone does not port the UI |
| engine/CMakeLists.txt | Fixed C:/VulkanSDK default, .exe shader-tool lookup, vulkan-1.lib and Windows libraries |
| engine offscreen/capture paths | Offscreen targets exist, but initialization requires a Win32 surface and capture/pacing paths remain swapchain-dependent |

Paths in this table are relative to ChimeraEngine. Source comments mentioning headless
or minimized operation do not establish initialization without a window or surface.

## Contracts to extract

- Window/input: create/destroy, framebuffer extent, event queue, text/key/mouse events,
  pointer capture, required Vulkan instance extensions, and surface creation. Shared
  code retains camera semantics, console capture, and simulation controls.
- Presentation: window/swapchain target or offscreen image target. Shared draw/compute
  passes consume the same state. Headless mode has no OS window or presentation queue
  requirement and must not call acquire/present. Audit device selection accordingly.
- Network: narrow socket lifecycle/send/receive/error abstraction, preserving loopback
  binding, API semantics, body framing, and request ordering. Do not rewrite HTTP and
  the platform boundary together unless the existing implementation demands it.
- Time/files/process services: use portable C++ where suitable, backend functions where
  required. Simulation tick time remains separate from display pacing. OS process
  launching is optional tooling; it cannot become necessary for core physics.
- Fonts: portable font-atlas provider with an explicitly licensed font and measured glyph
  metrics. Preserve the existing GDI provider for initial Windows parity. Do not make
  Linux pass by silently removing the Studio UI or substituting blank glyphs.
- Build: imported Vulkan target and platform-conditional OS dependencies; discover the
  shader compiler. Validation builds compile source shaders and fail if the compiler is
  absent, instead of treating stale binaries as current evidence. Preserve shader naming.

GLFW is the selected candidate for the Linux window/input/surface backend, behind the
interface. It supports Windows and Linux (X11/Wayland) and Vulkan surfaces. Existing
Win32 stays the default Windows backend through the initial extraction. Migration of
Windows to GLFW is optional later, only after behavior parity; no immediate rewrite.
References: [GLFW](https://www.glfw.org/),
[Vulkan surface API](https://www.glfw.org/docs/latest/group__vulkan.html).
Pin/review the dependency in P01; do not assume a library handles fonts or networking.

## Sequence and admission gates

1. Inventory active OS calls and capture a Windows baseline: window, input, text/console,
   camera, resize/minimize/restore, HTTP, frame capture, and a known scene timeline.
2. Extract the existing Windows backend without changing laws or default behavior.
   Re-run that baseline before replacing anything. Missing Windows runner means Windows
   regression status is NOT RUN and prevents release, not a guessed PASS.
3. Add the Linux backend and conditional build. Test actual desktop/window interaction.
   Record X11/Wayland coverage separately; a build on one is not proof of both.
4. Add genuine headless initialization and offscreen target selection. Run the same
   small scene and compute/graphics pipelines where device features permit.
5. Evaluate software Vulkan as an optional CPU test runner. Mesa documents Lavapipe as
   its software Vulkan frontend ([source-tree documentation](https://docs.mesa3d.org/sourcetree.html)).
   Enumerate required features first, including shaderFloat64, limits, image formats and
   extensions. Unsupported means unavailable coverage; do not disable physics silently.
6. Certify numerical comparison and real-window DYAD behavior on Windows and Linux.
   GPU performance remains hardware-specific; software Vulkan supplies no RTX timing claim.

This cloud workspace currently exposes Linux with no GPU device nodes, no nvidia-smi,
and no DISPLAY/WAYLAND_DISPLAY. Portability would enable more compilation and numerical
testing; software rendering here remains untested and requires suitable installed tools.

## Rule 0

STATEMENT: isolating OS/presentation services permits native Linux testing while preserving
Windows behavior and one shared physical state/law implementation.

PREDICTIONS: after extraction, Windows reproduces the declared baseline; Linux builds
without Windows headers/libraries; headless starts without a display and emits current
frames/diagnostics; equal inputs at equal simulation ticks agree within a preregistered
backend numerical tolerance. No universal bitwise cross-driver claim.

FALSIFIERS: Windows loses a baseline feature; a platform branch changes material laws;
headless requires a window/swapchain; capture is stale or from a different state; Linux
silently omits a required physics/UI feature; simulation advances differently solely
because presentation FPS changed. Each stage names exact controls/tolerances before run.

Offscreen evidence is diagnostic. It does not impersonate Alan's actual window or complete
the human DYAD verdict. A window screenshot can include UI that an offscreen scene image
does not; captures must declare viewport-only versus composited-window scope.

## P01 — reserved worker packet, separate from G01

Not yet dispatched. Objective: implement stage 1 inventory and stage 2 Windows-preserving
extraction proposal/prototype; stop for ASTRA review before stage 3. Read this file,
THE_MATERIAL_FOUNDATION, FOUNDATION_CONTEXT, and current engine source/instructions.

Initial owned deliverable: docs/FOUNDATION_P01_REPORT.md. Prototype only in
.tmp/foundation_p01/ until ASTRA names reviewed production seams. Proposed backend files
are NEW deliverables, not existing APIs. No material/gait/shader-law edits, master push,
force-push, protected-build writes, process restart or active camera takeover.

Return: exhaustive OS-call ownership table; proposed exact interfaces and dependency
direction; CMake/dependency plan; Windows baseline evidence or explicit missing access;
headless initialization graph; feature-capability matrix; staged patch proposal; falsifier
table and commands; new ideas. Build output must be outside ChimeraEngine/engine/build/.
Read-only inventory can run alongside G01. Do not divert GLM from its material assignment.

ASTRA must issue the production edit scope and single window/camera lease before an agent
changes or exercises the live platform backend. Alan's Windows workflow remains protected.

P01 supporting work is now recorded in [FOUNDATION_P01_REPORT.md](FOUNDATION_P01_REPORT.md).
The native Linux capture-encoder probe passes; it is not a Linux renderer or headless
engine. Production extraction remains gated on the Windows baseline. The inventory also
identifies named shared-memory transport as an OS seam with a packet-layout and
synchronization contract. See `tools/platform_probe/README.md` for reproducible checks.
