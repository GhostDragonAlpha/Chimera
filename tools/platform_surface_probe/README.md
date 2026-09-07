# platform_surface_probe — P05 seam harness

Standalone probe for the `plat::` surface seam in
`ChimeraEngine/engine/platform/`. It exercises BOTH backends against the REAL
Vulkan loader and headers — it does NOT build the engine, compile shaders, or
render anything.

## What each leg proves

- `[A] UnavailableBackend` — extension set empty/not-required/not-blocked;
  `create_surface` -> `kUnavailable` with the caller's `result` and `surface`
  byte-for-byte untouched (guards the "no headless fiction" contract).
- `[B] Win32Backend` (Windows only) — the reported extension is really present
  in the loader list; `blocked` agrees; pointers are stable across calls; a
  real instance + real hidden HWND -> `kCreated`, destroyed fault-free in
  engine teardown order; an instance created without the extension ->
  `kFailed` carrying the loader's REAL non-success VkResult, handle untouched.
- `[C] zero-arg entry` — the engine's platform entry agrees with the
  compile-time-selected backend.

Exit code 0 iff every check passes. Rule-0 registration for the checks lives
in `docs/evidence/p05/P05_PLAN_RULE0.md`.

## Build + run (Windows host)

```bat
cmake -S tools\platform_surface_probe -B %TEMP%\p05_probe_build -G "Visual Studio 18 2026" -A x64
cmake --build %TEMP%\p05_probe_build --config Release
%TEMP%\p05_probe_build\Release\platform_surface_probe.exe
```

On a host without Vulkan headers the project still builds and runs: only the
UnavailableBackend leg is compiled in (see the `WIN32` guard in its
CMakeLists.txt).

## Notes

- The harness is additive and standalone: `engine.cpp` and the engine build are
  not involved. It shares nothing with `tools/platform_probe` (the engine PNG
  byte-transport check) — those are two different probes with two different
  scopes.
- Determinism of the compile: MSVC ignores the "under TEMP" warning here; the
  probe writes only inside its own build directory.