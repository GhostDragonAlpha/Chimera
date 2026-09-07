# P05-R1 — Seam + harness repair (post-publish review corrections)

Status: THIS DOCUMENT CORRECTS `docs/evidence/p05/P05_IMPLEMENTATION.md` where they
disagree. It commutes the review's seven points into behavior; every changed
measurement in this document was re-taken after the repair and is recorded
below. The R0 reports, logs and preregistration are preserved byte-for-byte;
this is an **append**, not an edit: `probe_run_windows.txt`,
`probe_run_windows_r1.txt`, `probe_run_windows_asan.txt` and
`platform_probe_wsl.txt` all coexist as distinct historical evidence.

Timestamped run conditions are identical to R0: CMake 4.2.1, MSVC cl
19.51.36256.0 (VS 18 Community), Vulkan SDK `C:/VulkanSDK/1.4.328.1`,
Win SDK 10.0.26100.

## Review points → repairs (the seven)

| # | Review point | Repair in this commit |
|---|---|---|
| 1 | Harness returned `const char*` pointers into a destroyed `std::vector<VkExtensionProperties>` (dangling after return). | `enumerate_instance_extensions()` now returns **owned** `std::vector<VkExtensionProperties>`; leg B re-reads every name **after** the helper returned and PASSes only if no name is dangling/wrong. |
| 2 | Mutable production cache held extension data in file-scope storage written on every query. | Cache removed. The fixed extension-name array is `static` storage (constant content); **enumeration results are local to each query**; every potentially-throwing allocation inside the `noexcept` seam is covered by the declared policy (below). |
| 3 | Docs claimed the enumeration "preserves byte-behavior of the replaced code". | Corrected: the **happy path is byte-identical**; the **error path is STRICTER** — the original gate ignored `vkEnumerateInstanceExtensionProperties` VkResults; the seam now checks the count/query VkResults, folds `VK_INCOMPLETE` and first-call failure into `blocked=true`, and folds `std::bad_alloc` into `blocked=true`. |
| 4 | Harness referenced Windows types/includes unguarded and the standalone target hard-coded the SDK path; one comment claimed it "builds without Vulkan headers". | All Windows-specific code in `probe_surface.cpp` is behind `#if defined(_WIN32)`; a new Windows-only header `engine/platform/vulkan_surface_win32.h` carries the injection seam and is included only under `_WIN32`; `CMakeLists.txt` uses discovered `find_package(Vulkan REQUIRED)` / `Vulkan::Vulkan` (no SDK hard-code); the false comment is corrected (the target explicitly REQUIRES Vulkan headers). |
| 5 | Error path was tested by creating a bare instance WITHOUT the surface extension — a deliberate violation of the loader's usage requirements. | Deleted. Replaced by leg D: a **narrowly scoped injected substitute** — a real `PFN_vkCreateWin32SurfaceKHR` (real SDK types) that returns `VK_ERROR_DEVICE_LOST`; the test asserts the substitute was actually invoked, status `kFailed`, the **EXACT injected VkResult** propagated, the output handle byte-for-byte untouched, and the real-loader path restored after the override is reset. The real-loader success path remains leg C. |
| 6 | Rerun meaningful checks; record coverage + limitations; compile non-Windows if headers exist else NOT TESTED. | Rerun below (31/31 twice: Release + AddressSanitizer). Non-Windows: NOT TESTED — this WSL has no Vulkan headers. Enumeration-failure / `VK_INCOMPLETE` / OOM paths: implemented + documented, verified by code audit only (no injection point exists for the *enumeration* calls, only for the create call; recorded limitation). |
| 7 | Preserve previous logs; append correction history; runtime parity stays NOT TESTED; do not attribute exe-size differences to compiler metadata. | R0 files untouched. Exe sizes are reported as measurements only (below). Runtime/visual parity remains NOT TESTED — see the paired-session procedure in `P05_IMPLEMENTATION.md`, still unexecuted. |

## Allocation-failure / error policy (declared, no longer implicit)

Inside the `noexcept` seam, the fixed extension-name array is `static`
storage (no allocation). Each enumeration query allocates only
transiently; `std::bad_alloc` is caught and folded into `blocked=true`.
The create path performs no allocation. `VK_INCOMPLETE` from the count
query or the fill query is treated as "the loader did not give us the
contractual extension list" → `blocked=true`.
`SurfaceCreateOutcome.result` now ALWAYS receives the loader's real
VkResult (success or failure); `.surface` is written only on `kCreated`
and left byte-for-byte untouched on every other status.

## Re-measured evidence (after repair)

- **Harness Release:** `probe_run_windows_r1.txt` in this directory —
  **31 checks, 0 failed, exit 0** (real loader + controlled injection).
  Legs: A unavailable backend; B owned-lifetime regression; C real-loader
  success + teardown; D injected-substitute exact-result propagation;
  E zero-arg entry point.
- **Harness + AddressSanitizer:** `probe_run_windows_asan.txt` —
  **31 checks, 0 failed, exit 0** (MSVC `/fsanitize=address /Zi`; ASan
  runtime `clang_rt.asan_dynamic-x86_64.dll` from the build's toolchain
  PATH). The ASan build instrumented the R0 dangling-pointer pattern; this
  run is direct evidence that the result is owned after the helper returns.
- **Shader identity:** baseline `abdea9a5` (worktree
  `chimera_pub_base`) vs candidate (R1 worktree), same commands as R0:
  **23/23 `.spv` byte-identical, 0 mismatches** (27 GLSL inputs unchanged;
  `engine.cpp` and `engine/CMakeLists.txt` were NOT modified in R1 — see
  diff scope below).
- **Executables** (`Release/chimera_engine.exe`), measurements only:
  - baseline  `9B7C547DC0D56A463297C0D87C17E9E1E8B058BA34D52748A52398905493A37C` (688 640 B)
  - R0 candidate `D74A0672F7AB43A76182012A6DFB7785F567513F17E08D6E7077153EE1BFAB24` (691 200 B)
  - R1 candidate `69C520F667D3AB035956B5F9BD2B5E291BB4C148B39DE1E3FFD08A8D1A7AAA1E` (690 176 B)
  These sizes are **not attributed to any cause** (no compiler-metadata
  claim, no size-parity claim). Hash equality was never a parity signal.

## Diff scope of this commit

| File | Change |
|---|---|
| `ChimeraEngine/engine/platform/vulkan_surface.h` | corrected contract docs; enumeration-error policy now explicit |
| `ChimeraEngine/engine/platform/vulkan_surface_win32.h` | NEW — Windows-only injection seam (`win32_set_create_surface_override(PFN_vkCreateWin32SurfaceKHR) noexcept`) |
| `ChimeraEngine/engine/platform/vulkan_surface_win32.cpp` | cache removed; per-query enumeration with checked VkResults; `VK_INCOMPLETE` → blocked; `bad_alloc` → blocked; injected-substitute create path |
| `tools/platform_surface_probe/probe_surface.cpp` | owned-lifetime regression; controlled-failure leg D; portability guards |
| `tools/platform_surface_probe/CMakeLists.txt` | discovered `Vulkan::Vulkan`; SDK hard-code removed; comment corrected |
| `tools/platform_surface_probe/README.md` | legs A–E, ASan variant, corrected requirements/limitations |
| `docs/evidence/p05/P05_REPAIR_R1.md` | this correction |
| `docs/evidence/p05/probe_run_windows_r1.txt` | Release transcript (31/31) |
| `docs/evidence/p05/probe_run_windows_asan.txt` | ASan transcript (31/31) |

`engine.cpp`, `engine/CMakeLists.txt`, `vulkan_surface_unavailable.cpp`
and the shaders are **identical to the R0 publish** (`53f37456`).
Teardown order remains untouched.

## Corrected statements (replacing the R0 report's, where they conflict)

1. The seam does NOT "preserve byte-behavior" on the error path. Happy path:
   identical. Error path: **stricter** (checked VkResults, documented
   `blocked=true` folds).
2. Exe-size differences are reported, not explained.
3. The R0 bare-instance error test violated loader usage requirements; it is
   gone, replaced by the injection test (no usage requirement is violated:
   the substitute is a real-function-pointer override, not a malformed
   instance).

## Still NOT TESTED (unchanged from R0)

- Runtime/visual parity (paired capture; procedure prepared, unexecuted).
- Non-Windows harness build (no Vulkan headers on this WSL).
- Enumeration-failure / `VK_INCOMPLETE` / OOM paths at runtime (code-audit
  only; no injection seam for enumeration calls).
- Pre-existing deployed binary's actual shader set (build-dir set regenerates
  deterministically; 23/23 proven).

## P06 append (2026-09-07): command-record correction

This document's build-`-S`/`-B`<span></span> placeholders and the run
evidence's missing probe half are corrected by a dedicated record appended in
the P06 evidence commit: `docs/evidence/p06/P06_COMMAND_RECORD_CORRECTION.md`
holds the ACTUAL commands as run (three distinct configure sources, absolute
paths, verified against each build dir's `CMakeCache.txt`). The correction is
a NEW file + this pointer; nothing above was edited.

Short form of what changed: the probe configures from
`tools/platform_surface_probe`; the engine (both trees) configures from
`ChimeraEngine/engine`; these are three `-S` targets, not one shorthand.

## Evidence manifest (this commit)

| File | Kind |
|---|---|
| `P05_REPAIR_R1.md` | this correction (supersedes statements above) |
| `probe_run_windows_r1.txt` | Release harness, exit 0, 31/31 |
| `probe_run_windows_asan.txt` | ASan harness, exit 0, 31/31 |
| existing `P05_PLAN_RULE0.md`, `P05_IMPLEMENTATION.md`, `probe_run_windows.txt`, `platform_probe_wsl.txt` | preserved R0 evidence, byte-for-byte |