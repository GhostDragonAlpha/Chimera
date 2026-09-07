# P05 — Vulkan surface seam: implementation + evidence

Status: PUBLISHED. Commit supersedes in: `docs/evidence/p04/P04_SUPERSEDED_BY_P05.md`.
Preregistration (Rule 0, written before any build): `docs/evidence/p05/P05_PLAN_RULE0.md`.

## What changed (the bound, verified by git diff)

| File | Change |
|---|---|
| `ChimeraEngine/engine/platform/vulkan_surface.h` | new — the seam contract (see below) |
| `ChimeraEngine/engine/platform/vulkan_surface_win32.cpp` | new — Win32 backend |
| `ChimeraEngine/engine/platform/vulkan_surface_unavailable.cpp` | new — unavailable backend |
| `ChimeraEngine/engine/engine.cpp` | 2 call sites only (+1 include) |
| `ChimeraEngine/engine/CMakeLists.txt` | per-OS source selection, additive |
| `tools/platform_surface_probe/CMakeLists.txt` | new — standalone harness project |
| `tools/platform_surface_probe/probe_surface.cpp` | new — harness (27 checks) |
| `docs/evidence/p05/*` | this report + prereg + run logs |

`git diff abdea9a5..worktree`-equivalent shows exactly three hunks in tracked
production files (include; instance-extension gate; surface creation) plus the
new files. Physics, shaders, device selection, swapchain, window/input, fonts,
networking and shared-memory paths are unmodified. Teardown order in
`Engine::shutdown` is untouched (its hunks do not appear in the diff) — the
surface is still destroyed before device, instance and window, exactly as at
`abdea9a5`.

## The seam

```cpp
namespace plat {
struct SurfaceExtensionSet { const char* const* names; uint32_t count;
                             bool required; bool blocked; };
enum class SurfaceStatus : uint8_t { kCreated, kUnavailable, kFailed };
struct SurfaceCreateOutcome { SurfaceStatus status; VkResult result; VkSurfaceKHR surface; };

SurfaceExtensionSet surface_instance_extensions(Win32Backend)      noexcept;
SurfaceExtensionSet surface_instance_extensions(UnavailableBackend) noexcept;
void create_surface(VkInstance, void* /*HWND as void* */, SurfaceCreateOutcome&, Win32Backend)      noexcept;
void create_surface(VkInstance, void*, SurfaceCreateOutcome&, UnavailableBackend) noexcept;
}
```

- Win32 backend preserves byte-behavior of the replaced code: enumerates,
  requires `VK_KHR_win32_surface`, folds absence into `blocked=true` so the
  engine hard-fails with the identical message; creation arguments identical
  (`VkWin32SurfaceCreateInfoKHR` with sType, hwnd, `GetModuleHandle(nullptr)`,
  no alloc callbacks); the loader's REAL `VkResult` is carried out; the caller's
  `surface` field is written only on `kCreated`.
- OS types (`HWND`) stay out of the shared header; `native_window` is `void*`.
- The seam is `noexcept`; allocation failure inside the one-time enumeration is
  folded into `blocked=true` by explicit policy (documented in the sources).
- `kUnavailable` means the engine logs "no headless engine path" and fails
  init — there is deliberately NO headless/offscreen engine mode (S1 corrected).

## Rule-0 outcome (STATEMENT/PREDICTION/FALSIFIER)

STATEMENT: the seam can be inserted without changing observable surface
behavior, error semantics or destruction order, without touching physics /
shaders / swapchain / window / device code. **Survived.**

| P | Prediction | Result |
|---|---|---|
| P1 | Win32 ext set: count 1, name `VK_KHR_win32_surface`, required, not blocked, pointer-stable | PASS (probe) |
| P2 | real instance + real HWND -> kCreated, non-null, clean destroy | PASS (probe) |
| P3 | instance without the ext -> kFailed with REAL non-SUCCESS VkResult, handle untouched | PASS (probe) |
| P4 | unavailable backend: empty/not-required set; kUnavailable; sentinel unchanged; no loader symbols | PASS (probe + objdump) |
| P5 | same toolchain: both builds link 0 errors; 23/23 SPV byte-identical; exe hashes differ | PASS |
| P6 | teardown untouched | PASS (diff) |

F1..F8: none triggered. Exit code 0.

## Harness results (real loader, real VulkanSDK headers)

`probe_run_windows.txt` (in this directory) records the full transcript:
**27 checks, 0 failed.** Highlights:
- unavailable backend never touches the caller's `result`/`surface`;
- the reported win32 extension is genuinely present in the loader list and
  `blocked` agrees with reality;
- a real VkSurfaceKHR is created from a real hidden HWND and destroyed cleanly
  (`vkDestroySurfaceKHR` returns void; the teardown leg runs fault-free in
  engine order);
- the error leg returns the loader's real non-`VK_SUCCESS` VkResult.

Symbol audit: `objdump -t vulkan_surface_unavailable.obj` references no
`vkCreate*` / `vkAcquire*` / `vkQueuePresent*` symbols (the only `Vk*` text is
the seam's own `create_surface` mangled signature).

## Device-selection / extension notes

Unchanged from baseline. This extraction did not touch device selection,
device extension lists, queue family logic, swapchain creation or surface
capability queries. (P04's S1 overclaim - those became touch-listed in P05
rather than being performed.)

## Build comparison (P05 §B), Windows host

Same toolchain + configuration applied to both trees from clean directories:

- Working trees: **baseline** `abdea9a5` (clean git worktree), **candidate**
  (this patch, uncommitted working tree).
- Commands: `cmake -S <tree>/ChimeraEngine/engine -B <scratch>/<side> -G
  "Visual Studio 18 2026" -A x64`, then `cmake --build <scratch>/<side>
  --config Release`.
- Scratch dirs: `%TEMP%\opencode\p05_builds\base` and `...\cand` (OUTSIDE the
  repo; nothing written under `engine/build/`; `engine/build` mtime of Alan's
  checkout verified unchanged).
- Identities:
  - CMake 4.2.1; MSVC cl 19.51.36256.0 (MSVC 14.51.x, VS 18 Community); SDK
    `C:/VulkanSDK/1.4.328.1`; glslangValidator 11:15.4.0; Win SDK 10.0.26100.
  - custom commands audited (engine/CMakeLists.txt): shader .spv -> build dir,
    POST_BUILD copy -> `$<TARGET_FILE_DIR>/shaders`. No hidden writes.
  - shader inputs: all 27 GLSL sources byte-identical across trees (SHA-256
    compared); 23 compiled `.spv` in each `Release/shaders`: byte-identical
    per file (0 mismatches).
  - executables (`Release/chimera_engine.exe`):
    - baseline  `9B7C547DC0D56A463297C0D87C17E9E1E8B058BA34D52748A52398905493A37C` (688 640 B)
    - candidate `D74A0672F7AB43A76182012A6DFB7785F567513F17E08D6E7077153EE1BFAB24` (691 200 B)
  - hashes differ as expected (compiler metadata + the seam's object). Hash
    equality was never a parity signal; parity rests on shader identity,
    harness behavior and the preserved-by-diff code paths.

## Existing probe (P05 §C), WSL

`tools/platform_probe/check.py` (encoder byte-transport instrument; NOT a
renderer/DYAD verdict) on WSL Ubuntu 24.04 (g++ 13.3.0, python 3.12.3):
**PASS**, 9/9 checks, JSON in `platform_probe_wsl.txt`. This validates the PNG
encoder's byte transport, which is not a claim about rendered pixels.

## Runtime / visual (P05 §D): **NOT TESTED**

This report does NOT certify, by publication, that the candidate's rendered
pixels match the baseline. That decision belongs to a paired capture, which was
NOT executed because it requires an explicit current-window-session +
isolated-launch arrangement (Alan's engine was live; we were instructed to
prepare, never to run, the paired procedure).

Paired procedure (prepared, unexecuted):
- Scene/camera/viewport/shader inputs identical on both executables: `fit_dyad`
  bookmark `[20.2905617, 0.5, 0.349999994, 0.284010023, 3.35295677,
  -1.73747635, 0, 0]`; joints owner `show` theta 0.0; show playing; scene flags
  show/volp/chrome ON, joints/gait/water/frost/matter/strain OFF; 2560x1440;
  port 8090.
- Repeat baseline captures first to measure stability; then capture candidate
  under the same inputs; a pixel difference is a finding to investigate, NOT a
  threshold to widen.
- Any captured difference lands here as a real result before the next cycle.

## What P04's S1 claimed vs. what P05 establishes (correction summary)

| P04 S1 claim | P05 correction |
|---|---|
| swapchain/surface was the engine's only Linux blocker | NOT established; the remaining windows (Win32 window creation + message loop in `main.cpp`, and WSI feature queries) still block a Linux build. This extraction touched neither (by design). |
| S1 authorized headless init / skipped presentation / offscreen runtime | does NOT exist and was NOT authorized. `kUnavailable` fails init. The seam's unavailable backend exists solely for the harness. |
| portable seam harness == compiled Linux engine | no; the probe is a standalone boundary probe running the real loader on Windows; a Linux ENGINE compile was not attempted (no Vulkan headers on this WSL; recorded NOT TESTED). |
| unchanged PNG encoder proves unchanged rendered pixels | no; the encoder check validates byte transport only (see §C). |
| (implicit) exe parity signal | exe hashes differ by construction; recorded both. |

## Remaining blockers + recommended next extraction

Blockers today:
1. Runtime/visual parity: NOT TESTED (needs the paired-session arrangement above).
2. Linux native engine build: no Vulkan headers in this WSL; the unavailable
   backend proves the harness contract, not a Linux engine.
3. Release shader set claimed by the running binary vs. build-dir set: the
   build regenerates deterministically (proven: 23/23 identical), but the
   pre-existing deployed binary's actual set was not under our control.

Recommended next extraction (lowest risk, highest value for a Linux engine):
**window/input abstraction** — `main.cpp` owns class registration, `g_hwnd`
creation, the message loop, and destroy order that shuts down the Vulkan
surface via the already-seam'd path. Abstracting it (like the surface seam:
tagged backends, unavailable = no input surface, no headless fiction) is the
true successor to P04's "only blocker" claim and would let a real Linux build
exercise this seam's unavailable/real paths under a different WSI stack.
Second choice: an explicit device-extension/feature selection seam.

## Evidence manifest

| File | Kind |
|---|---|
| `P05_PLAN_RULE0.md` | preregistration (STATEMENT/P/F) |
| `P05_IMPLEMENTATION.md` | this report |
| `probe_run_windows.txt` | harness transcript, exit 0, 27/27 |
| `platform_probe_wsl.txt` | existing probe JSON, PASS 9/9 |
| `tools/platform_surface_probe/README.md` | harness usage |
| commit | see latest publish on `astra/gait-capture` |