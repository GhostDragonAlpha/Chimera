# P02 Platform Audit — Windows Baseline & WSL2 Readiness

**Agent:** Big Pickle (platform-audit)
**Date:** 2026-09-06 12:22 CDT (visual/DYAD phase completed same day)
**Checkout:** 51cd7212 (master) — "Keep the camera above the floor: CAM_PHI_BAND, CAM_FLOOR_GATE, FIT v6"
**Author:** GhostDragonAlpha, 2026-09-06 12:05:35 -0500

---

## 1. Checkout Identity

| Field | Value |
|---|---|
| Commit | `51cd7212fd6ef2cfda95c330abcc2ff154cc6141` |
| Branch | `master` (checked out) |
| Other branches | `agent/local`, `rogue-backup`, `remotes/origin/astra/gait-capture` |
| Tracked modifications | 4 files: `Chimera/docs/DREAM_REPORT.md`, `Chimera/docs/HERALD.md`, `Chimera/docs/HISTORY_BOOK.md`, `ChimeraEngine/engine/_native_end.png`, `ChimeraEngine/engine/_native_start.png` |
| Untracked (notable) | `Saved/dyad/` (many session dirs), `ChimeraEngine/engine/engine_launch.{err,out}`, `docs/PHYSICS_NOTES.md`, `docs/THE_CONTACT_SHADOW.md`, `docs/THE_WALK_DERIVATION.md` |
| GLM ownership | No `docs/THE_MATERIAL_FOUNDATION.md` exists. No files matching `THE_MATERIAL_FOUNDATION` in the repo. GLM's G01 material work is not represented in tracked docs at this checkout. |

### Missing required documents

| Document | Status |
|---|---|
| `docs/THE_PLATFORM_BOUNDARY.md` | **MISSING** |
| `docs/FOUNDATION_P01_REPORT.md` | **MISSING** |
| `docs/FOUNDATION_CONTEXT.md` | **MISSING** |
| `docs/THE_MATERIAL_FOUNDATION.md` | **MISSING** |
| `tools/platform_probe/README.md` | **MISSING** (entire `tools/platform_probe/` directory absent) |

---

## 2. Windows & WSL Inventory

### Windows

| Field | Value |
|---|---|
| OS | Microsoft Windows 11 Pro |
| Build | 10.0.26200 (Build 26200) |
| Architecture | x64-based PC |
| BIOS | American Megatrends A.60, 10/27/2023 |

### WSL

| Field | Value |
|---|---|
| WSL version | 2.6.3.0 |
| WSL kernel | 6.6.87.2-microsoft-standard-WSL2 |
| WSLg version | 1.0.71 |
| Default distribution | Ubuntu (WSL2) |
| Distribution state | **Stopped** (must be explicitly started) |
| Ubuntu version | 24.04.3 LTS (Noble Numbat) |

---

## 3. Linux Development Capabilities (WSL2 Ubuntu)

| Capability | Status | Detail |
|---|---|---|
| **C++ compiler** | PASS | g++ 13.3.0 (Ubuntu 13.3.0-6ubuntu2~24.04.1) |
| **Python** | PASS | Python 3.12.3 |
| **CMake** | **FAIL** | Not installed |
| **Vulkan loader** | PASS | libvulkan1 1.3.275.0 |
| **Vulkan tools** | PASS | vulkaninfo 1.3.275.0 |
| **Shader compiler (glslangValidator)** | **FAIL** | Not installed (glslc also missing) |
| **DISPLAY** | **FAIL** | Empty — no X11 or Wayland session |
| **WAYLAND_DISPLAY** | **FAIL** | Empty |
| **GPU passthrough** | PARTIAL | NVIDIA RTX 4090 visible via nvidia-smi 610.43.02, but Vulkan enumerates llvmpipe only |
| **CUDA toolkit** | **FAIL** | nvcc not installed (nvidia-smi shows driver only) |

---

## 4. Vulkan Verification (WSL2)

### Honest assessment

| Claim | Evidence | Verdict |
|---|---|---|
| Vulkan loader exists | `libvulkan1:amd64 1.3.275.0` installed | **PASS** |
| Vulkan enumerates a device | `GPU0: llvmpipe (LLVM 20.1.2, 256 bits)` — `PHYSICAL_DEVICE_TYPE_CPU` | **PASS** (software only) |
| Physical device is discrete GPU | Device type is CPU (llvmpipe), not GPU | **FAIL** |
| Compute queue exists | `queueFlags = QUEUE_GRAPHICS_BIT \| QUEUE_COMPUTE_BIT \| QUEUE_TRANSFER_BIT` | **PASS** (on llvmpipe) |
| Required compute features exist | Unknown — no Vulkan feature probe run; llvmpipe API 1.4.318 | **NOT TESTED** |
| Window presentation works | No DISPLAY/WAYLAND_DISPLAY set; `VK_KHR_wayland_surface` available but no compositor | **FAIL** |
| Chimera actually runs | Engine requires `VK_KHR_win32_surface` (engine.cpp:495 hard-fails without it) | **FAIL** — Win32 surface extension absent in WSL |

### NVIDIA GPU visibility

nvidia-smi shows RTX 4090 with driver 610.43.02 (KMD 610.47) and CUDA UMD 13.3. However:
- The GPU is **not** enumerated by the Vulkan loader in WSL (llvmpipe is the only device)
- nvidia-smi presence does **not** prove Vulkan compatibility
- No CUDA toolkit (nvcc) is installed, so CUDA compute paths cannot be tested
- The 21744 MiB memory usage suggests the Windows host is actively using the GPU

### Key limitation

The engine hard-requires `VK_KHR_win32_surface` (engine.cpp:495: `return false` if absent). WSL2 has `VK_KHR_wayland_surface`, `VK_KHR_xcb_surface`, and `VK_KHR_xlib_surface` but **not** `VK_KHR_win32_surface`. The engine **cannot initialize its Vulkan instance** under WSL2 as currently written.

---

## 5. Portable Capture Probe

**Result: NOT RUN** — `tools/platform_probe/` directory does not exist in the repository.

The assignment referenced `tools/platform_probe/check.py` and `tools/platform_probe/README.md`. Neither is present at commit 51cd7212. This is a finding: the probe tool was either never committed, removed before this checkout, or lives in a different branch/worktree.

---

## 6. Platform Split Audit

### Source files

| File | Lines | Win32 Dependencies |
|---|---|---|
| `engine.cpp` | 8202 | `<windows.h>`, `<vulkan/vulkan_win32.h>`, `CreateWindowEx`, `RegisterClassEx`, `WndProc` (HWND, message handling), `VK_KHR_win32_surface` |
| `main.cpp` | 2841 | `<winsock2.h>`, `<ws2tcpip.h>`, `<windows.h>`, `<mmsystem.h>`, `WSAStartup`, `PeekMessage/DispatchMessage`, `Sleep()`, `timeBeginPeriod(1)` |
| `http_server.cpp` | 132 | `<winsock2.h>`, `<ws2tcpip.h>`, `WSAStartup/closesocket`, `SOCKET`, `#pragma comment(lib, "ws2_32.lib")` |
| `ui.cpp` | 3273 | `<windows.h>`, GDI: `CreateCompatibleDC`, `CreateFontW`, `CreateDIBSection`, `TextOutW`, `SelectObject`, `GetTextMetricsW` |
| `physics.cpp` | 131 | **None** (pure C++ math) |
| `physics.hpp` | 32 | Includes `shared_mem.hpp` (which is Win32) |
| `shared_mem.hpp` | 96 | `<windows.h>`, `CreateFileMappingA`, `MapViewOfFile`, `OpenFileMappingA`, `HANDLE` |
| `engine.hpp` | 1007 | **None** directly (Vulkan API only, no Win32 headers) |
| `ui.hpp` | 710 | **None** directly (Vulkan API only) |
| `http_server.hpp` | 27 | `<winsock2.h>`, `SOCKET` type |
| `png_encoder.hpp` | 103 | **None** (pure C++ math) |

### Dependency map

| System dependency | Owning file(s) | Shared-core? | OS-specific? | Proposed boundary |
|---|---|---|---|---|
| **Win32 window & input** | `engine.cpp` (WndProc, CreateWindowEx, WASD/polling) | Camera logic, key mapping | HWND creation, message dispatch | `platform/window_win32.{cpp,hpp}` → abstract `Window` interface |
| **Vulkan surface creation** | `engine.cpp` (vkCreateWin32SurfaceKHR) | Instance/device selection | Surface creation | `platform/surface_win32.{cpp,hpp}` → `create_surface(instance, window)` |
| **GDI font rendering** | `ui.cpp` (create_font_atlas) | Atlas packing, Vulkan upload | DC/font/bitmap/textout | `platform/font_gdi.{cpp,hpp}` → abstract `rasterize_fontAtlas()` |
| **Filesystem/process paths** | `CMakeLists.txt` (hardcoded `C:/VulkanSDK/`) | Shader compilation | SDK paths | CMake toolchain file or env var |
| **Timing & message pump** | `main.cpp` (timeBeginPeriod, Sleep, PeekMessage) | Frame pacing logic | Win32 sleep resolution, message loop | `platform/timing_win32.{cpp,hpp}` → `platform_sleep(ms)` + `platform_poll_messages()` |
| **Winsock HTTP** | `http_server.cpp/.hpp` | HTTP parsing, routing | Socket API (WSAStartup, SOCKET, closesocket) | `platform/net_winsock.{cpp,hpp}` → abstract `TcpListener` |
| **Named shared memory** | `shared_mem.hpp` | Ring buffer protocol (magic, push/pop) | CreateFileMapping/MapViewOfFile | `platform/shmem_win32.{cpp,hpp}` → abstract `SharedMemory` |

### Files that are already portable (zero Win32 deps)

- `physics.cpp` / `physics.hpp` — pure C++ math (but includes `shared_mem.hpp`)
- `png_encoder.hpp` — pure C++ (no OS deps)
- All GLSL shaders in `engine/shaders/` — cross-platform SPIR-V
- `cpp_bridge.py` — pure Python HTTP client

### Files requiring the most extraction work

1. **`engine.cpp`** (8202 lines) — deepest Win32 coupling: WndProc callback, HWND lifecycle, VK_KHR_win32_surface. This is the critical path.
2. **`ui.cpp`** (3273 lines) — GDI font rasterization is Windows-only but the Vulkan rendering pipeline it feeds is portable.
3. **`main.cpp`** (2841 lines) — Winsock init, message pump, `Sleep()` timing. High line count but the platform-specific surface is thin.

---

## 7. Windows Visual Baseline

**Status: COMPLETE (2026-09-06) — captured live under Alan's granted window/camera session.**

The live engine (PID 14268, window "Chimera Engine", port 8090, 2560x1440, RTX 4090 ~103-300 fps) was already running; no launch was performed. All captures are 2560x1440 PNG under `.tmp/p02_visual_20260906_122824/`.

### 7.1 What was exercised (read-only HTTP, session window only)

| Step | Endpoint | Result |
|---|---|---|
| Registry/state | `/state`, `/studio`, `/studio_chrome`, `/scene`, `/light` | body 36424 tris / 18459 verts; show, volp, chrome ON; joints/gait/water/frost/matter OFF |
| SHOW loop | `/show` | time advanced 1660 → 1675 while `/frame` stayed byte-identical |
| Camera orbit | `/camera` POST with `cam_radius/cam_theta/cam_phi` | 10 distinct frames for 10 theta steps (0.5 → 6.15 rad) |
| Joint pose | `/joints` POST `{"joint":"knee_L","theta":100}` | `ok:true, owner=edit, theta_applied=100`; frame changed |
| Camera restore | `/cameras` POST `{"op":"recall","name":"fit_dyad"}` | restored; show still playing (t≈1698.06) |

> **HTTP trap (recorded):** `/camera` requires keys `cam_radius`,`cam_theta`,`cam_phi`. Posting `radius/theta/phi` silently falls back to defaults and produced one misleading earlier result. `/cameras` POST `{"op":"recall","name":"fit_dyad"}` restores a bookmark.

### 7.2 Numerical evidence (md5, independent of the eye)

| Capture | md5 | Reading |
|---|---|---|
| `frame_000/001/003/004` | all `F4355D89…` | `/frame` byte-identical while show plays |
| `orbitOK_00` / `_05` / `_09` | `48E1A0E1…` / `411F9DD3…` / `67CD3E7A…` | 3 of 10 distinct — all 10 distinct over full sweep |
| `orbitOK_00` vs `showfix_frame_00` | both `48E1A0E1…` | identical start state |
| `showfix_frame_00` vs `_04` | both `48E1A0E1…` | `/frame` static while `/glass` changes |
| `showfix_glass_00` vs `_04` | `0772563C…` / `83EDD2DF…` | `/glass` (composited window) changes each capture |
| `joint_pose_base` vs `kneeL_100` | `3C1E06EA…` / `0464E3EA…` | joint pose changed the mesh |
| `final_baseline` | `B8672C12…` | composited end state (distinct) |

### 7.3 Verdicts

1. **PASS — renderer is camera-responsive.** 10 distinct `/frame` outputs for the 10-step `cam_theta` orbit (0.5→6.15 rad). The renderer genuinely re-projects on camera change.
2. **PASS — joint rig CAN move the mesh.** A single `knee_L:100` POST produced a real, DYAD-visible knee bend.
3. **FINDING — the automated SHOW sweep drives ZERO on-mesh motion in the current state.** `/show` clock advances (`1660→1675`, then `t≈1698`) and `current` joint rotates in the reel, but `/frame` stays byte-identical for 15+ s and `theta=0.0` at every capture. The show is playing but not deforming the mesh (no gait pack, `joints_show` present but theta stays 0; see 7.4).
4. **FINDING — `/frame` is raw 3D viewport (no UI); `/glass` is the live composited window.** Dyad read of `frame_000`: "no UI". Dyad read of `glass_001`: full studio — stage tabs, DOCS dock, STATUS(live), REEL, TIMELINE, running clocks. This is exactly why `/frame` is byte-stable while `/glass` changes: the HUD lives above the 3D surface.

### 7.4 Why SHOW is static (DYAD-informed, evidence-based)

The live UI (`glass_001`) shows: `hinge: off`, `gait CPG: no pack | steps 0`, `show t=1430s…`, `PLAYING`, `SHOW ear_R theta 0.00 deg`. The show clock and reel advance but every joint theta readout is `+0`/`0.00`. With no gait pack and `steps 0`, the automated show has no motion source feeding the mesh — it only advances bookkeeping. This is not a rendering bug; it is the current data state (gait/water stages off at this audit).

---

## 8. DYAD Application

**Status: COMPLETE (2026-09-06) — resident eye `qwen3.8-27b-nvfp4-mtp`, can_see TRUE.**

The resident LM Studio vision model judged the captured frames (one image per call, structured non-leading prompts, `PYTHONIOENCODING=utf-8`). Runs in `Saved/dyad/dyad_log.jsonl`; notes in `.tmp/p02_visual_20260906_122824/_dyad_reads.py`.

### 8.1 Reads (aggregated)

| Frame | Dyad read (condensed) | Consistent with md5? |
|---|---|---|
| `final_baseline` | Tan/clay humanoid, rear/back, arms down, tail out, flat gray floor, **no UI** | — |
| `frame_000` | Same figure rear view, symmetric, **no UI** | Yes (identifier) |
| `orbitOK_00` | Tail sweeps to **viewer's right**, rear view | distinct md5 |
| `orbitOK_05` | Tail sweeps to **viewer's left**, rear view | distinct md5 |
| `joint_pose_base` | **Both legs straight**, symmetric, **no UI** | Yes (identifier) |
| `joint_pose_kneeL_100` | **LEFT knee bent forward ~30-45°**, right leg straight, **asymmetric** | Yes (change) |
| `glass_001` | **Full studio UI**: stage tabs B0-B10, DOCS dock, STATUS(live) FPS 103, REEL[2/12], TIMELINE "PLAYING", running clocks | changes (live) |

### 8.2 DYAD conclusion

- **Mesh motion is real and controllable** when driven directly: the `knee_L:100` joint pose produced a clearly asymmetric, forward knee bend that the eye read without any leading hint — and the orbit frames flip the tail side as the mesh rotates.
- **The automated SHOW currently produces no mesh deformation** — the eye reads a static symmetric pose across `/frame` captures, matching byte-identical md5, because no gait/steps are feeding the mesh despite the show clock advancing.
- **Machine + eye agree** on the two core findings (SHOW-static, joint-pose-moves). Where the eye is ambiguous (exact camera azimuth between orbit frames), the numerical md5 is authoritative (10 distinct frames).
- **Human acceptance required (not a terminal):** the visual "reads as fine" judgment and the final handoff disposition are Alan's; this audit only reduces the decision space.

---


## 9. Proposed Next Bounded Patch

### Recommendation: Platform abstraction layer (first cut)

**STATEMENT:** The engine's Win32 coupling is concentrated in 6 API surfaces across 4 files; extracting them behind thin abstract interfaces preserves Windows behavior while enabling Linux compilation.

**PREDICTION:** A platform abstraction that replaces the 6 OS-specific interfaces will allow the engine to compile on Linux (WSL2 + g++ + Vulkan SDK) with fewer than 500 lines of new header code and zero changes to the rendering/compute logic.

**FALSIFIER:** If any of the 6 interfaces cannot be abstracted without modifying the Vulkan pipeline, physics, or shader code, the patch is too deep for a first cut.

### Proposed files

| New file | Replaces | Content |
|---|---|---|
| `platform/window.hpp` | Win32 HWND/WndProc in `engine.cpp` | Abstract `Window` class: `create()`, `poll_events()`, `on_key()`, `on_resize()` |
| `platform/surface.hpp` | `vkCreateWin32SurfaceKHR` in `engine.cpp` | `create_vulkan_surface(instance, window)` — platform dispatch |
| `platform/font.hpp` | GDI in `ui.cpp` | `rasterize_fontAtlas(scale)` → RGBA bitmap + metrics |
| `platform/net.hpp` | Winsock in `http_server.cpp` | Abstract `TcpListener` class |
| `platform/shmem.hpp` | `CreateFileMapping` in `shared_mem.hpp` | Abstract `SharedMemory` class |
| `platform/timing.hpp` | `Sleep`/`timeBeginPeriod` in `main.cpp` | `platform_sleep(ms)`, `platform_set_timer_resolution()` |

### Dependencies

- Vulkan SDK 1.4.x installed in WSL2 (`apt install libvulkan-dev`)
- CMake installed in WSL2 (`apt install cmake`)
- glslangValidator or glslc installed (`apt install glslang-tools`)
- No GPU passthrough needed for compilation; llvmpipe suffices for headless test

### Rollback

Each platform file is additive — no existing file is modified in a way that breaks Windows. Rollback is deleting the `platform/` directory and reverting `CMakeLists.txt`.

### Acceptance tests

1. Engine compiles on Windows (MSVC) with zero warnings
2. Engine compiles on Linux (g++ + CMake) with zero errors
3. Engine launches on Windows and renders the same frame as before (screenshot delta = 0)
4. `vulkaninfo` in WSL2 shows the instance extensions the engine needs

---

## 10. Blockers

| Blocker | Status at close |
|---|---|
| Engine visual baseline (Task 7/8) | **RESOLVED** — granted session; Tasks 7 & 8 complete with evidence |
| CMake not installed in WSL2 | Open — `apt install cmake` (read-only report; no install) |
| glslangValidator not installed in WSL2 | Open — `apt install glslang-tools` (read-only report; no install) |
| No GPU Vulkan device in WSL2 | Open — llvmpipe only; NVIDIA may need `nvidia-wayland-egl`/ICD or updated drivers |
| `tools/platform_probe/` absent | Open — cannot run `check.py`; tool not at this checkout |

---

## 11. Incidental Findings

1. **The Vulkan SDK path is hardcoded** in `CMakeLists.txt` line 8: `set(VULKAN_SDK "C:/VulkanSDK/1.4.328.1")`. This must become a CMake variable or env lookup for Linux builds.

2. **CMakeLists.txt has duplicate shader rules.** Lines 36-78 use a derived `file(GLOB)` list, then lines 80-134 manually re-declare 7 of those same shaders. This is harmless but confusing — the manual rules win for those 7 files.

3. **physics.cpp is already portable** but includes `shared_mem.hpp` which is Win32-only. The fix: `physics.hpp` forward-declares `SharedRing` and only `main.cpp` (which calls `push_state_to_ring`) needs the Win32 include.

4. **WSL2 has nvidia-smi but not the Vulkan ICD for NVIDIA.** The Mesa/lvmpipe Vulkan driver is the only ICD. Enabling `nvidia_layers.json` or installing `nvidia-utils` inside WSL2 might expose the RTX 4090 as a Vulkan device — but that is an installation action outside this audit's scope.

5. **The engine's `VK_API_VERSION_1_2` requirement** (engine.cpp:469) is satisfied by WSL2's Vulkan 1.4.318. The API version is not a blocker; the surface extension and GPU device are.

---

## Confirmation

| Item | Status |
|---|---|
| Files written | `.tmp/p02_20260906_122252/P02_PLATFORM_AUDIT.md` (this file) + `.tmp/p02_visual_20260906_122824/` (59 evidence PNGs, 2560x1440) |
| Live engine controlled | **Yes** — only within Alan's granted window/camera session (PID 14268, port 8090); end state: camera restored to `fit_dyad`, show playing |
| Commits made | **None** |
| Branches switched | **None** |
| GLM work modified | **None** |
| Protected paths touched | **None** (`engine/build/` untouched) |
