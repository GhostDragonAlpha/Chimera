# platform_surface_probe — P05-R1 seam harness

Standalone probe for the `plat::` surface seam in
`ChimeraEngine/engine/platform/`. It exercises both backends against the REAL
Vulkan loader (and, for controlled-failure experiments, an injected substitute
with the real PFN signature) — it does NOT build the engine, compile shaders,
or render anything.

## Legs

- `[A] UnavailableBackend` (portable) — extension set empty/not-required/
  not-blocked; `create_surface` -> `kUnavailable` with `result` and `surface`
  byte-for-byte untouched (the "no headless fiction" contract).
- `[B] extension-name lifetime` (portable) — the enumeration helper returns
  OWNED `VkExtensionProperties`; the leg copies names out and re-reads them
  AFTER the helper (and its buffers) have gone out of scope. This is the R1
  regression for the R0 dangling-pointer defect.
- `[C] Win32Backend real loader` (Windows) — reported extension really present
  in the loader list; `blocked` agrees; pointers stable (fixed static
  storage); a real instance + real hidden HWND -> `kCreated`, destroyed
  fault-free in engine teardown order. Purely real-loader; no injection.
- `[D] controlled failure` (Windows) — a substitute carrying the REAL
  `PFN_vkCreateWin32SurfaceKHR` signature is injected and returns
  `VK_ERROR_DEVICE_LOST`; the harness asserts the substitute ran, status is
  `kFailed`, the EXACT VkResult propagated, and the output handle is untouched.
  Reset restores the real loader path (verified by a second real create).
  This replaces the R0 experiment that deliberately violated Vulkan usage
  requirements.
- `[E] zero-arg entry` (portable) — agrees with the compile-time-selected
  backend.

Exit code 0 iff every check passes. Rule-0 registration and coverage notes:
`docs/evidence/p05/P05_PLAN_RULE0.md` and `docs/evidence/p05/P05_REPAIR_R1.md`.

## Build + run (Windows host)

```bat
cmake -S tools\platform_surface_probe -B %TEMP%\p05_builds\probe -G "Visual Studio 18 2026" -A x64
cmake --build %TEMP%\p05_builds\probe --config Release
%TEMP%\p05_builds\probe\Release\platform_surface_probe.exe
```

ASan variant (dangling-pointer regression under the sanitizer — MSVC):

```bat
cmake -S tools\platform_surface_probe -B %TEMP%\p05_builds\probe_asan -G "Visual Studio 18 2026" -A x64 -DCMAKE_CXX_FLAGS="/fsanitize=address /Zi"
cmake --build %TEMP%\p05_builds\probe_asan --config Release
%TEMP%\p05_builds\probe_asan\Release\platform_surface_probe.exe
```

## Requirements + limitations (R1-corrected)

- The standalone target REQUIRES Vulkan headers/discovery (`find_package
  Vulkan`) — it does NOT build without them. On a Vulkan-enabled non-Windows
  host it compiles the UnavailableBackend-half (legs A, B, E) only.
- Non-Windows build status here: NOT TESTED (the WSL image has no Vulkan
  headers; installing them is out of scope).
- Enumeration failure / VK_INCOMPLETE / allocation-failure handling inside the
  seam is implemented (folds to `blocked`) but not black-box tested here: the
  real loader cannot be forced into those states and the injection seam covers
  the create call, not the enumeration calls. Verified by code audit.
- Runtime pixel parity is governed by a separate paired-session procedure and
  remains NOT TESTED until that session occurs.