# P05 — Plan and Rule-0 Registration (preregistered, before execution)

Status: PREREGISTERED. Written before any build, harness run, or source edit.

## Scope (bounded, from the P05 assignment)

Replace the engine's two direct Win32 surface sites with a small seam
(`namespace plat`) while preserving observable behavior:

1. `engine.cpp` instance-extension gate (lines ~481-495 at master 51cd7212):
   enumerate instance extensions, require `VK_KHR_win32_surface`, hard-fail if
   absent, then push it plus the unconditional `VK_KHR_surface` literal.
2. `engine.cpp` surface creation (~lines 551-560): build a
   `VkWin32SurfaceCreateInfoKHR` from `g_hwnd` + `GetModuleHandle(nullptr)` with
   null allocation callbacks and call `vkCreateWin32SurfaceKHR(instance_,
   ..., nullptr, &surface_)`, failing init on error with the real VkResult.

What is allowed to change: those two call sites, `engine/CMakeLists.txt`
(source-list selection), and three new files under `engine/platform/`.
The `tools/platform_surface_probe/` harness and `docs/evidence/p05/` docs are
new deliverables.

What must NOT change (per assignment): physics, shaders, device selection,
swapchain behavior, window/input, fonts, networking, shared memory; rule-0
says: if the extraction needs any of those, stop and report the dependency.

## STATEMENT (someone must be able to disagree)

> A slimmable platform seam - two functions `plat::surface_instance_extensions()`
> and `plat::create_surface(...)`, with a tagged Win32 backend and a tagged
> unavailable backend - can encapsulate the engine's Win32 instance-extension
> gate and surface creation **without changing any observable surface behavior,
> error semantics, or destruction order, and without touching physics, shaders,
> swapchain, window, or device code.**

The counter-claim is: any such extraction necessarily alters the created
surface's identity (extension list, instance, creation args) or the ply of the
init path, so even a small seam cannot be behavior-preserving.

## PREDICTIONS (not yet measured)

- **P1** On this Windows host, `plat::surface_instance_extensions()` (Win32
  backend, real loader) returns count==1, name string equal to
  `VK_KHR_WIN32_SURFACE_EXTENSION_NAME`, `required==true`, `blocked==false`;
  a second call returns the same pointer (stable static cache) - the seam is
  not re-enumerating per init.
- **P2** `plat::create_surface()` with a REAL instance (created from the
  returned extensions) and a REAL hidden HWND returns `kCreated` with a
  non-null `VkSurfaceKHR`, and `vkDestroySurfaceKHR` on it succeeds - the
  creation args (sType, hwnd, hinstance, null callbacks, instance) are valid.
- **P3** `plat::create_surface()` with a BOGUS (non-created) instance returns
  `kFailed` and `result ==` the loader's real non-SUCCESS VkResult - the real
  error is carried, not swallowed.
- **P4** The UNAVAILABLE backend returns count==0 / required==false /
  blocked==false and `kUnavailable` from create_surface, leaving the caller's
  output handle byte-for-byte unchanged (sentinel preserved), and contains no
  surface-creation or presentation symbols.
- **P5** Baseline (abdea9a5) and candidate (this patch) builds with the SAME
  toolchain and config (MSVC 14.51.36231, VS generator, Release) compile and
  link with zero errors; the 27 shader sources compile to BYTE-IDENTICAL
  `.spv` in both build dirs; the two executables' SHA-256s differ (recorded).
- **P6** The engine teardown order is untouched by the patch (swapchain, then
  surface, then device, instance, window) - verified by diff, not rebuilt.

## FALSIFIERS (named before any run)

- **F1** Harness: Win32 backend on this host returns count != 1, or name not
  equal to the `VK_KHR_win32_surface` string, or `blocked==true` while the
  loader enumerates it -> seam availability logic is wrong. FAIL.
- **F2** Setion: real instance + real HWND -> anything but `kCreated` +
  non-null surface. FAIL.
- **F3** Bogus instance -> `kFailed` with `result==VK_SUCCESS` (swallowed
  result) or non-`kFailed`. FAIL.
- **F4** Unavailable backend: sentinel changed, or not `kUnavailable`/empty
  extension set. FAIL.
- **F5** Candidate engine fails to compile or link `engine.cpp` +
  `platform/vulkan_surface_win32.cpp` against the REAL SDK headers. FAIL.
- **F6** Baseline vs candidate `.spv` differ (shader-input identity broken, so
  the B comparison would be invalid). FAIL.
- **F7** Any repository path outside the allowed set changes; anything is
  written under `engine/build/`; a protected path (`.githooks`, other agents'
  dirs) is touched. FAIL.
- **F8** Runtime (ONLY if separately authorized): paired baseline/candidate
  captures differ beyond the repeat-baseline variance -> a finding to
  investigate, never grounds for widening a threshold. Without authorization
  the runtime verdict is reported NOT TESTED, which is a truthful non-failure.

## Measured environment (preregistered, from today's probing)

- Windows host; Vulkan SDK `C:/VulkanSDK/1.4.328.1`
  (glslangValidator present at that SDK).
- CMake 4.2.1; MSVC `cl 14.51.36231` under VS 18 Community
  (`...\18\Community\VC\Tools\MSVC\14.51.36231\bin\Hostx64\x64\cl.exe`);
  MinGW g++ 13.13 also present but the B comparison will use ONE toolchain -
  MSVC via the VS generator - for both trees.
- WSL Ubuntu 24.04: python3 3.12.3, g++ 13.3.0, vulkan headers ABSENT
  (matches P01 finding) -> the probe's Linux-native Vulkan leg is NOT
  SUPPORTED there; the unavailable-backend leg is nonetheless exercised on
  Windows inside the harness.
- Repo: `astra/gait-capture` head `abdea9a5` (our P04 commit), remote
  re-verified via ls-remote before starting this plan.
- The engine's custom build commands (audited from engine/CMakeLists.txt)
  write only under CMAKE_BINARY_DIR (shader .spv) and
  $<TARGET_FILE_DIR>/shaders (POST_BUILD copy). A build can therefore be kept
  entirely outside the repo by choosing -B build dirs under the temp scratch
  root. No dependency installs, no driver changes, no `engine/build/` writes.

## Execution order (the bound)

1. (done) Write this preregistration.
2. Create clean baseline worktree at abdea9a5.
3. Implement seam (3 new files), edit engine.cpp (2 sites), edit
   engine/CMakeLists.txt (source selection). Diff must show ONLY those files.
4. Author + build the standalone probe project (same toolchain), run it, save
   report.
5. Build baseline and candidate (MSVC, Release, separate -B dirs under temp),
   hash shaders + executables.
6. Run `tools/platform_probe/check.py` on WSL, record results.
7. Write implementation + correction docs; assemble evidence; verify staged
   set; recheck remote head; commit + push; return the 6-item report.