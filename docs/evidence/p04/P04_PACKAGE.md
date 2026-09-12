# P04 — Pre-S1 Reconciliation and Regression-Gate Specification

**Agent:** Big Pickle (platform-audit, P04 continuation)
**Date:** 2026-09-06 21:5x CDT (packet assembled read-only; publication step deferred per handoff protocol)
**Evidence directory:** `.tmp/p04_20260906_1904/` (this packet; `pr8_retrieved/` inside)
**Mode:** Read-only against production. No commits, no pushes, no branch switches, no installs, no live-engine control, no writes under `ChimeraEngine/engine/build/`. S1 is specified, not implemented.

---

## 0. Change to the handoff channel (operative)

The ZIP/upload return path was replaced: **Big Pickle is the designated local publisher**.
Workers return exact paths + source commit + SHA-256 hashes + changed-file list only; the
publisher collects the three completed handoffs (G01, P04, V03), stages them into
`docs/evidence/{g01,p04,v03}/` on an **isolated checkout** of `astra/gait-capture`, verifies
the diff and blob hashes (accounting for line-ending normalization), commits, and pushes
normally. Never touch Alan's checkout; never push master; never force-push; never write
under `ChimeraEngine/engine/build/`. If the remote branch advanced before publish → STOP
and report. See §7.

---

## 1. Architecture-version reconciliation (PR #8 vs P03 proposal)

### 1.1 Exact retrieval identity

Retrieved read-only (no git mutation of Alan's checkout) from the public repo
`GhostDragonAlpha/Chimera` via GitHub REST + `raw.githubusercontent.com`:

| Field | Value |
|---|---|
| PR | **#8** — "Define material foundation, DYAD contracts, and GLM worker assignment" |
| State | **open**, not merged (checked at retrieval) |
| Head commit | `037b7a1ae1652a1752ad1008d47f5bd5cce616d0` (branch `astra/gait-capture`) |
| Base commit | `7cafb33297e8c35c2bb32d09f812e3dafde34df3` (master, **two commits behind** engine `51cd7212`) |
| `docs/THE_PLATFORM_BOUNDARY.md` blob | `3ab6cb68c1820ac1ae2e1bf27fe19ba0c1233ac7` |
| Isolated-checkout recheck | `git ls-remote origin astra/gait-capture` → `037b7a1a…` (identical, 2026-09-06 21:5x) |

Files retrieved (10, all in `pr8_retrieved/`):
`THE_PLATFORM_BOUNDARY.md`, `FOUNDATION_P01_REPORT.md`, `FOUNDATION_CONTEXT.md`,
`FOUNDATION_AGENT_TASKS.md`, `THE_MATERIAL_FOUNDATION.md`,
`THE_SURFACE_ENERGY_TRANSLATION.md`, and `tools/platform_probe/{README.md,check.py,CMakeLists.txt,capture_fixture.cpp}`.

**Retrieval verified byte-exact (2026-09-06):** `git hash-object` of each `pr8_retrieved/`
file equals the branch blob at `037b7a1a` — all 10/10 (e.g. `docs/THE_PLATFORM_BOUNDARY.md` =
`3ab6cb68c1820ac1ae2e1bf27fe19ba0c1233ac7`, matching the PR #8 file listing; sizes 2357–13,427).
These 10 are the committed blobs, byte-for-byte (LF; no line-ending drift).

Note the skew: the boundary doc's coupling table is audited at base `7cafb332`; this packet's
anchors are audited at `51cd7212`. Symbols and block boundaries are identical in both; only a
few line numbers differ (cosmetic, recorded below where relevant). No conflict of types.

### 1.2 What THE_PLATFORM_BOUNDARY.md actually decides

- **Keep one C++/Vulkan engine; extract OS services behind a narrow interface; add Linux.** The
  split lives at **platform services and presentation**, not at materials/membranes/physics/
  shaders/authoritative state. Dependency direction:
  `shared application/engine → platform interface → selected platform backend`.
- **Windows is a backend**, not the center. **GLFW is the named candidate** for the Linux
  window/input/surface backend.
- Coupling inventory (at `7cafb332`): engine.cpp (HWND/WndProc/CreateWindowEx, Win32 Vulkan
  extension+surface), main.cpp (Winsock, message pump, Sleep, timer), http_server.cpp
  (Windows network, `SOCKET` leak), ui.cpp (GDI font raster), engine/CMakeLists.txt (fixed
  `C:/VulkanSDK`, `.exe` shader-tool search, Windows libs), offscreen/capture (requires Win32
  surface today).
- Contracts named: Window/input (create/destroy, framebuffer extent, event queue, key/mouse
  semantics, pointer capture, **required instance extensions, surface creation**); Presentation
  (window/swapchain **or** offscreen image target; **headless must not call acquire/present**);
  Network; Time/files/process; Fonts (portable provider, **GDI preserved for parity, not silent
  removal**); Build (imported Vulkan target, shader-compiler discovery, validation builds fail
  on stale binaries).
- Sequence: 1) inventory+baseline → 2) extract Win32 backend **preserving behavior**, re-run
  baseline → 3) Linux backend (+ conditional build) → 4) headless init + offscreen target
  selection → 5) software Vulkan optional (enumerate features first, e.g. `shaderFloat64`) →
  6) numerical + DYAD certification on both.
- Rule-0 STATEMENT/PREDICTIONS/FALSIFIERS recorded in the doc; P01's worker packet reserved.

### 1.3 Comparison to the P03 proposal — conflicts and resolutions

| # | Area | P03 proposal | THE_PLATFORM_BOUNDARY.md / PR #8 | Verdict |
|---|---|---|---|---|
| C1 | Boundary doc | "absent at checkout — author it first" (P03 §13.0) | EXISTS at `astra/gait-capture` 037b7a1a | **Superseded**: don't re-author; S1 aligns to the PR doc. Still *absent at master* — fact unchanged |
| C2 | First-patch shape | S1 = Vulkan-surface seam, Win32 verbatim move + Linux `kUnavailable` stub first (P03 §13.2/13.3) | Stage 2 = extract Win32 backend **preserving behavior**, baseline re-run; Linux backend = stage 3 | **Mostly aligned.** S1 is the surface subset (2 of the 6 WindowBackend members) of stage 2. Keep Windows-preservation-as-gate; stub is the stage-2 first-cut, not a working Linux engine |
| C3 | Linux backend name | unnamed stub, "returns unavailable" | GLFW named candidate | **Agree in interim**: stub is a boundary test until GLFW stage 3 |
| C4 | Headless ordering | first-cut folds "deferred-present (headless)" into the Linux unavailable path (P03 §13.3) | headless/offscreen = separate **stage 4**, after the Linux window backend | **Conflict, resolve by scoping**: `kUnavailable` must never create a swapchain or call acquire/present (matches doc), but genuine headless *boot/offscreen-target* work is stage 4, **not** an S1 acceptance claim |
| C5 | Dependency order | S1→S4→S2→S3→S5/S6 (P03 §13.5) | doc stages 1→2→3→4→5→6 | **Restate** in doc terms: stage-1 baseline (§3) → S1(surface⊂WindowBackend) → full WindowBackend/GLFW → S4 socket → S3 fonts(GDI first) → S5 shared region (its own sync audit) → S6 timing → stage-4 headless → stage-5 software-Vulkan features → stage-6 certification. S1 unchanged as the first increment |
| C6 | Shared region (S5) | "dormant, can be deleted/guarded for free later; not a blocker" (P03 §13.2/13.5) | P01 = "new inventory finding"; **don't silently drop on Linux**; concurrency semantics need *their own test* (mapping same bytes ≠ synchronized access) | **Conflict**: fine that S5 is not in S1, but deletion is NOT sanctioned without its sync audit; S5's audit is a required later item (baseline admission "shared-memory producer/consumer if active") |
| C7 | Probe tool | "missing; to be authored in the S1 patch" (P03 §13.7/§14) | already authored + measured in PR #8 (P01: 9/9, 8/8 on Linux) | **Superseded**: S1 runs the existing `tools/platform_probe/check.py` once merged; do not re-author |

**Bottom line:** no unresolvable conflict. P03 correctly derived the seams from source; the PR
#8 boundary doc names the same seams, re-orders headless to stage 4, names GLFW, and already
carries an executed P01 + the probe. S1 = stage-2's surface-creation increment of
`WindowBackend`, gated by the corrected Windows regression (§3).

### 1.4 Cross-verification: encoder bytes are identical across branches

P01's checked-out header SHA-256 `924e4da9876ed043d3e572b7467aabd830288d10124a71d047670ab036f8b30a`
(P01 report) **equals** this checkout's `ChimeraEngine/engine/png_encoder.hpp` SHA-256
`924E4DA9876ED043D3E572B7467AABD830288D10124A71D047670AB036F8B30A`. So the PNG encoder the
Windows engine uses is byte-identical to the one P01 proved lossless on Linux → the S1
bit-identical `/frame` gate (§3) is well-founded by construction.

---

## 2. Complete S1 specification (surface subset of the WindowBackend contract)

**STATEMENT:** The engine's only hard Linux blocker is the instance/surface gate: instance
creation demands `VK_KHR_win32_surface` before device selection (`engine.cpp:481–495`, hard
fail at `:495`), and surface creation is hard-wired to Win32 (`:551–560`). Moving exactly the
two surface members of the doc's `WindowBackend` contract behind a narrow `plat::` seam — with
a Win32 implementation that is a verbatim move and a Linux/unavailable stub — makes WSL2
compilation reach `pick_physical_device`/`find_queue_families`, while the Windows build
produces a call-for-call identical surface path (measured bit-identical `/frame`, §3). No
change to swapchain, device selection, pipelines, compute, physics, shaders, authoritative
state, fonts, network, shared memory, timing, or the offscreen `/frame` path.

**PREDICTION:** (a) Windows same-env `/frame` at `fit_dyad` = `2D4A9F93E0…`; (b) WSL2 g++
build compiles S1 and reaches device enumeration (llvmpipe) with the `kUnavailable` path
logged, no acquire/present call, no crash; (c) engine.cpp diff = the two call-site substitutions
plus a same-condition `plat::` switch; `platform/` = 3 new files; CMake edit additive.

**FALSIFIERS (named before the run):**
1. Windows `/frame` ≠ `2D4A9F93E070C5CBCE2217213592357CADE70C5ECC9F96470AC403BD3B0DA20F` at the
   same-env baseline cell → behavior changed → STOP, revert.
2. `create_swapchain`, `pick_physical_device`, `find_queue_families`, any pipeline, compute,
   physics, shader, or `/frame`-capture code must be *edited*, not merely repositioned, to make
   S1 compile → seam too deep → STOP, narrow.
3. Linux first-cut: crash before device enumeration, `kUnavailable` path calls acquire/present,
   or no "surface unavailable (headless)" log → fix or revert.
4. Any production file outside `{engine.cpp` (the two sites), `engine/CMakeLists.txt` (additive),
   `platform/` (new)` changes → revert all.

### 2.1 Exact files and symbols

| File | Content |
|---|---|
| `ChimeraEngine/engine/platform/vulkan_surface.h` (new) | Pure interface. Vulkan types (VkInstance/VkSurfaceKHR) only; **zero Win32/Posix/GLFW headers** |
| `ChimeraEngine/engine/platform/vulkan_surface_win32.cpp` (new) | Win32 impl: verbatim move of `engine.cpp:481–495` (extension gate) and `:551–560` (surface build) |
| `ChimeraEngine/engine/platform/vulkan_surface_unavailable.cpp` (new) | Non-Win32 first cut: reports unavailable; no OS headers beyond what CMake picks |
| `ChimeraEngine/engine/CMakeLists.txt` (edit, additive) | add `platform/` sources; per-OS selection `if(WIN32)…else()…`; existing Windows libs/defaults unchanged |

Interface (nominal, final):

```cpp
namespace plat {
  enum class SurfaceResult : uint8_t { kCreated, kUnavailable, kError };

  struct SurfaceRequirements {
    std::vector<char const*> instance_extensions;  // extension-name C strings (static storage)
    bool required;                                 // instance creation must abort if unmet
  };

  // Called BEFORE vkCreateInstance. Pure query; no state. Replaces engine.cpp:477–495.
  SurfaceRequirements instance_surface_requirements() noexcept;

  // Called AFTER vkCreateInstance, only when the caller is ready to present.
  // native_window is BORROWED (HWND on Win32). Caller owns the window and the VkSurfaceKHR.
  // out is left untouched on kUnavailable/kError; caller pre-inits out = VK_NULL_HANDLE.
  SurfaceResult create_surface(VkInstance instance, void* native_window, VkSurfaceKHR& out) noexcept;
}
```

### 2.2 Behavior contracts

- **Instance-extension discovery — before instance creation.** At `engine.cpp:469`+
  (`app.apiVersion = VK_API_VERSION_1_2`), the engine asks
  `plat::instance_surface_requirements()` before `vkCreateInstance`. The engine's existing
  instance-extension enumeration loop (:481–493) appends any required name it finds present;
  if `req.required == true` and it is missing → the **same** hard fail as today (`:495`).
  Win32 impl returns `{ {VK_KHR_WIN32_SURFACE_EXTENSION_NAME}, required=true }`; unavailable
  impl returns `{ {}, required=false }` → instance builds without the surface extension,
  exactly the doc's "device/queue feature selection works without a presentation surface".
  Debug-utils extension and all other instance additions stay exactly as today.
- **Surface creation.** After `vkCreateInstance`, the engine calls
  `plat::create_surface(instance_, g_hwnd, surface_)`, replacing inline `:551–560`.
  Win32 impl performs the identical `VkWin32SurfaceCreateInfoKHR` build in the identical order
  (`sType :553`, `hwnd=g_hwnd :554`, `hinstance=GetModuleHandle :555`, `vkCreateWin32SurfaceKHR
  :556`, null allocator) — call-for-call identical.
- **Ownership / destruction.** `instance_surface_requirements()` = pure query, no state.
  `create_surface` borrows `native_window`; the engine owns HWND lifetime and must not destroy
  the window before `vkDestroySurfaceKHR` (existing teardown `:936`, `DestroyWindow :947`,
  unchanged). The returned `VkSurfaceKHR` is caller-owned; engine destroys it exactly as today.
  The seam owns nothing at rest.
- **Failure reporting.** `kCreated` → proceed to the existing `create_swapchain()` flow
  (`:621`–`:646` gate unchanged). `kUnavailable` → engine skips swapchain/present entirely,
  logs `"surface unavailable (headless)"`, and continues to device selection; **no acquire or
  present call is ever issued** (doc: headless must not call acquire/present). `kError` → engine
  logs the VkResult and hard-stops as today. No fake success, no silent no-op.
- **Win32 behavior preserved exactly.** Same required-extension list, same fail condition, same
  create call sequence/order/arguments → the instance+surface path is bit-for-bit today's path.
- **Linux/unavailable stub (first cut).** Returns `{ {}, false }` / `kUnavailable`. This is a
  **boundary test, not a working Linux engine**. No window, no present device, no GLFW yet.

### 2.3 What S1 makes testable — and not

Testable now:
1. WSL2 g++ compile of the seam + engine to device selection with some device enumerated (llvmpipe).
2. The `kUnavailable` path: explicit failure log, deferred present, no acquire/present, offscreen
   `/frame` independence (existing `rt_image_`-based capture stays window-independent).
3. Windows bit-identical `/frame` at `fit_dyad` (§3) + live `/glass` HUD.
4. The "no pipeline edit" falsifier (2.0#2).

Explicitly **not** testable by S1 (out of scope, stated so reviewers don't read success where
none exists):
- Linux present/swapchain (needs full WindowBackend window+pump → GLFW stage 3 + a compositor).
- GDI font parity / UI text (S3).
- Normalized input semantics, pointer capture, resize/minimize/restore.
- Genuine headless *boot/offscreen-target selection* (doc stage 4).
- Software-Vulkan feature matrix incl. `shaderFloat64` (doc stage 5; preregistered checks).
- Numerical + DYAD certification on both platforms (doc stage 6).
- A whole-engine WSL **run** (ladder rung 6) — needs the window backend.

### 2.4 How the later Linux window backend fits without touching core files

`vulkan_surface_glfw.cpp` later implements the **same** `plat::` surface interface (lists the
GLFW-negotiated instance extensions, creates the surface via `glfwCreateWindowSurface`) and
replaces the unavailable stub at doc stage 3; the engine driver code, `create_swapchain`
(already portable `VK_KHR_swapchain`, engine.cpp:619/1038), `pick_physical_device`,
`find_queue_families`, pipelines, physics, shaders, and authoritative state are **untouched**.
Stage 4 adds a distinct `PresentationTarget` offscreen-image path alongside the window present
path; stages 5–6 add feature probing and certification. Every later stage extends the seam's
backend set or adds new seams; none re-edits S1's extraction-driver code.

---

## 3. Corrected Windows regression gate

A reproducible same-environment baseline cell, per item, no invented tolerances.

### 3.1 The baseline cell (identity, reproducible)

| Item | Value |
|---|---|
| Source commit | `51cd7212fd6ef2cfda95c330abcc2ff154cc6141` |
| Executable | `ChimeraEngine/engine/build/Release/chimera_engine.exe` — SHA-256 `79BFBE967401A8697364BAD950E8634FEB5669839C7F4A53129ED4BD6CD6C45F`, 681,984 B, mtime 2026-09-06 12:04:43 (P02's running binary; PID 14268, started 12:04:44) |
| Video encoder | `png_encoder.hpp` SHA-256 `924E4DA9876ED043D3E572B7467AABD830288D10124A71D047670AB036F8B30A` |
| Shaders | **Release SPV set to be enumerated + hashed at packaging time.** (Recursive search surfaced only `build/build-asan/Release/shaders/*.spv`, mtime 09-05 22:50; the Release-set shader location loaded by the gated binary is confirmed **pending** — the gate records it, never assumes it) |
| GPU / driver | NVIDIA GeForce RTX 4090 (read out via `/glass`), driver 610.43.02 (nvidia-smi) |
| Camera | recall `fit_dyad` — bookmark `[20.2905617, 0.5, 0.349999994, 0.284010023, 3.35295677, -1.73747635, 0, 0]`; camera at `fit_dyad` (seq 42 reel) |
| Joints | owner `"show"`, all 28 `theta=0.0`, `on:false` (no edit pose) |
| Playback | show **playing** (live clock; `/frame` is `2D4A9F93…` in the tested config *while the clock advances* — scoped finding V4, not a general claim) |
| Scene flags | show/volp/chrome **ON**; joints/gait/water/frost/matter/strain **OFF** |
| Viewport / window | 2560×1440, window "Chimera Engine", port 8090 |

### 3.2 Capture protocol and assertions

1. `GET http://localhost:8090/frame` → hash the PNG bytes.
2. **Same-environment exact check (zero tolerance):** must equal
   `2D4A9F93E070C5CBCE2217213592357CADE70C5ECC9F96470AC403BD3B0DA20F`
   (byte-identical to `cam_pre_orbit.png`/`frame_000..004`/`verifyA/B`, 12:28:31, P02 corpus).
   Justification: lossless encoder (byte transport, P01: 66,992 bytes exact), deterministic in
   tested config → same environment ⇒ same bytes. Same-env is the ONLY place byte-equality is
   the standard.
3. `GET /glass` twice ~1 s apart → **different** (HUD lives above the 3D surface; time-dependent).
   `/glass` is a liveness sanity check, never an equality assertion. Sample id `538CE59B…` is
   informational only.
4. `POST /cameras {"op":"recall","name":"fit_dyad"}` → `ok`, applied values == the bookmark above.

### 3.3 Same-environment vs cross-device — the rule

- **Same environment** (same exe + shader set + device + driver + scene + camera + viewport):
  byte-identical PNG required. Zero tolerance. No "allowed difference" exists here.
- **Cross-device / cross-build / cross-branch**: **not** a baseline gate. No allowed-image-
  difference number is invented in this packet (per instruction). Any future cross-device
  comparison (doc stage 6 certification) must preregister its metric and tolerance **before**
  the run (Rule 0) — e.g. per-channel statistics, structural similarity — and pair every
  numerical metric with a DYAD visual read carrying its own falsifier. A number is a
  measurement, never an assumption smuggled into a gate.
- The gate asserts same-env byte-identity; it never claims cross-device hash equality, and it
  does not "restore" the show clock (a live marching clock cannot be rewound; `/frame`
  identity holds in the tested config regardless).

---

## 4. WSL acceptance ladder — reconciled (commands/errors as recorded)

No raw WSL transcript was preserved; P02 §3/§4 tables are the recorded evidence. Cited findings:
`wsl --version` 2.6.3.0; kernel 6.6.87.2; Ubuntu 24.04.3; g++ 13.3.0 PASS; python3 3.12.3 PASS;
CMake FAIL (not installed); glslangValidator/glslc FAIL; DISPLAY/WAYLAND_DISPLAY empty;
nvidia-smi driver 610.43.02 (KMD 610.47, CUDA UMD 13.3); vulkaninfo 1.3.275 → **only**
`GPU0: llvmpipe (LLVM 20.1.2)`, `deviceType = PHYSICAL_DEVICE_TYPE_CPU`, API 1.4.318,
queueFlags GRAPHICS|COMPUTE|TRANSFER.

Corrected verdicts (tier per claim: **M** = measured, **S** = source-predicted,
**N** = not attempted):

| Rung | P03 label | Corrected label | Basis |
|---|---|---|---|
| 1. Compiler works | PASS (toolchain) | **M-PASS** (toolchain); engine build in WSL **N** (never attempted 51cd7212) | g++/python presence verified; engine build was read-only-skipped, not failed |
| 2. Probe passes | NOT TESTED (tool missing) | **N** at master (tool absent) — but tool **exists and measured** at `astra/gait-capture` 037b7a1a (P01: 9/9 compiled route, 8/8 supplied-exe route; runs `run_m4nsbxlx`/`run_e6ib3721`); `png_encoder.hpp` bytes identical → result transfers to master's encoder | glob: no `tools/platform_probe/` at 51cd7212; P01 report |
| 3. Device enumerates | PASS (some)/FAIL (discrete) | **M**: llvmpipe enumerated (software, CPU, API 1.4.318). RTX 4090 **not** enumerated for Vulkan. No name-based inference: llvmpipe = Mesa/Lavapipe CPU rasterizer from raw enum + type field; nvidia-smi ≠ Vulkan ICD | vulkaninfo raw output |
| 4. Features available | NOT TESTED | **N**: feature matrix (float64/int64/geometry/non-solid fill, engine.cpp:601–609) unmeasured in WSL; software-Vulkan feature probing deferred to doc stage 5 with preregistered checks | no in-WSL feature probe run |
| 5. Presentation | FAIL | **NOT ATTEMPTED**: no DISPLAY/WAYLAND_DISPLAY, no compositor; no presentation attempt occurred. No-compositor does **not** block headless compute — headless compute also **N** (stage 4 material) | recorder: absent compositor; no attempt |
| 6. Chimera runs | FAIL | **N (source-predicted fail)**: no actual WSL run occurred; today the engine would hard-fail at `engine.cpp:495` (source-determined, not measured). Real measurement requires the S1 patch; predicted outcome after S1 = compiles → device enumeration (llvmpipe) → present unavailable → logs headless → would then MEASURE `/frame` offscreen, not assume | P02 recorded engine exit-before-instance-complete + source inspection |

Disclaimers retained: CUDA access (nvidia-smi) ≠ Vulkan support; a WSL success would be one
distro/kernel/driver combination, not native-Linux certification; every rung states measured
(or explicitly not-attempted) evidence.

---

## 5. Evidence accounting — the "4" was a miscount, the state was always 5

- Three independent read-only checkpoints (P02 session-report, P03 verified, P04 verified) each
  show **the same five** modified tracked files vs `51cd7212`:
  `Chimera/docs/DREAM_REPORT.md`, `Chimera/docs/HERALD.md`, `Chimera/docs/HISTORY_BOOK.md`,
  `ChimeraEngine/engine/_native_end.png`, `ChimeraEngine/engine/_native_start.png`.
- `P02_PLATFORM_AUDIT.md` line 17 reads "Tracked modifications | 4 files:" then **lists five
  filenames**. The prose count was wrong; the list was right. There was no hidden fifth, no
  concurrent change; the discrepancy is inside P02's own line.
- Blob IDs (index) and diffstat vs HEAD: `DREAM_REPORT.md fe2dff60…` (18 lines changed),
  `HERALD.md 07c2e79d…` (2), `HISTORY_BOOK.md 71b7a3fb…` (4),
  `_native_end.png ea061dad…` (235,338→274,061 B), `_native_start.png 408f8091…`
  (235,350→273,757 B); 5 files, +12/−12.
- Attribution: the P02 session-start snapshot already contained these changes, before any P02
  action → **pre-existing** for the whole P02/P03/P04 chain. Unattributed drift; no basis to
  attribute to any agent (including G01/GLM), so none is assigned.
- Corollary: P04 (and P03) produced **zero** new tracked modifications (git status verified at
  both checkpoints); nothing was written under `ChimeraEngine/engine/build/`.

---

## 6. S1 patch handoff spec (for the implementing worker)

### 6.1 Dependency order (doc-stage aligned)

1. **Stage 1 — baseline**: record + gate from §3 (evidence exists, P02/P03/P04 corpus).
2. **S1**: surface subset of `WindowBackend` per §2 — Windows-preserving, gated by §3.
3. Probe: use the **existing** `tools/platform_probe/check.py` (P01 protocol; runs on the
   foundation branch) — run on WSL2 after the first-cut; do not re-author.
4. Full `WindowBackend` window+pump+input via GLFW (doc stage 3); **then** rung-6 WSL run.
5. S4 socket transport; S3 fonts (GDI first, not silent removal); S5 shared region — **own
   concurrency audit** (do not silently drop or delete); S6 timing (trivial ride-along).
6. Headless init + offscreen `PresentationTarget` selection (doc stage 4).
7. Software-Vulkan optional — enumerate features first (doc stage 5).
8. Numerical + DYAD certification on both platforms (doc stage 6) — cross-device tolerances
   preregistered before that run, per §3.3.

### 6.2 Acceptance commands

**Windows (this audited box; schedule when PID 14268 or the current live engine no longer holds
port 8090 — do not kill a running engine):**
- Build out-of-source, outside `engine/build/`: configure + build `ChimeraEngine/build-split-win`
  (gitignored scratch) from `ChimeraEngine/engine/CMakeLists.txt`.
- Run the produced `chimera_engine.exe`; then:
  - `GET http://localhost:8090/frame` → SHA-256 must equal `2D4A9F93E070C5CBCE2217213592357CADE70C5ECC9F96470AC403BD3B0DA20F`.
  - `GET /glass` twice, ~1 s apart → hashes differ.
  - `POST /cameras {"op":"recall","name":"fit_dyad"}` → ok, applied values == §3.1 bookmark.
  - `GET /show` → playing.
- Verify with: `(Get-FileHash frame.png -Algorithm SHA256).Hash`.

**Linux first cut (WSL2):**
- `python tools/platform_probe/check.py` → P01-equivalent route (2 = supplied-executable ok).
- Build to `build-split-linux` with Vulkan headers; run:
  - device enumeration appears (llvmpipe expected) — no crash;
  - log contains `"surface unavailable (headless)"`;
  - no acquire/present call issues (instrument log/assert);
  - capture raw `vulkaninfo` output verbatim for the record; attempt `/frame` offscreen **as a
    measurement** and report the result either way (do not assert).

### 6.3 Remaining Windows interaction tests (NOT TESTED, carried open per P01 baseline admission)

Console/keyboard input while console open; mouse-drag orbit/pan/zoom (only HTTP orbit tested);
resize/minimize/restore; HTTP responsiveness under live input; human acceptance (Alan). These
are WindowBackend-completion admission items, **not** S1 acceptance (S1 is byte-preserving by
the §3 gate; no new capability is claimed).

### 6.4 Rollback

Delete `ChimeraEngine/engine/platform/` (3 new files); revert the two `engine.cpp` call sites to
their verbatim original blocks; revert the additive `engine/CMakeLists.txt` edit. `engine/build/`
is never touched → rollback restores the exact pre-patch tree. `build-split-*` are gitignored
out-of-tree scratch.

### 6.5 Worker-return line for P04

- Packet paths: `.tmp/p04_20260906_1904/` (`P04_PACKAGE.md`, `P04_EVIDENCE_MANIFEST.sha256`, `pr8_retrieved/*` ×10).
- Source commits: engine audited at `51cd7212` (master); anchor doc at `037b7a1a` (`astra/gait-capture`, PR #8).
- Changed tracked files: **none** in Alan's checkout.
- Manifest: `P04_EVIDENCE_MANIFEST.sha256` (below); reference hashes in §1.4/§3.

---

## 7. Publication state (designated publisher — blocked on inputs)

- **Isolated checkout ready** (never touches Alan's checkout): `C:\Users\allen\AppData\Local\Temp\opencode\chimera_pub`
  — `git clone --no-checkout --filter=blob:none --single-branch`, then `fetch` + local branch
  `astra/gait-capture` from `FETCH_HEAD`; HEAD = `037b7a1ae1652a1752ad1008d47f5bd5cce616d0`;
  worktree matches PR #8 (verified `THE_PLATFORM_BOUNDARY.md`, `FOUNDATION_P01_REPORT.md`,
  `tools/platform_probe/check.py` present). `git ls-remote` at setup showed remote
  `astra/gait-capture` **unchanged** → no conflict so far.
- **Line-ending accounting:** repo `.gitattributes` = `* text=auto`, `*.bat/*.ps1 eol=crlf`,
  `*.uasset/*.umap/*.png/*.jar/*.exe binary`; `core.autocrlf=true` in both Alan's checkout and
  the pub clone. Consequences: text files are LF in-repo (normalized at `git add`); worktree
  copies are CRLF on Windows. Publication verifies **staged blob** identity via `git hash-object`
  /`git ls-files -s` vs the pre-commit tree, plus an explicit line-ending note in the commit
  message; binaries (PNG) are exact bytes, no normalization.
- **Blocker (reported, not resolved):** G01 and V03 packets are **not present on this machine** —
  `docs/evidence/` does not exist; no `FOUNDATION_G01*`/`FOUNDATION_V0*` files anywhere; no
  `tools/material_contract*.py` / `surface_energy*.py`; no g01/v03 dirs under `.tmp/`;
  `agent_logs/` holds only older phase0 logs. Publication executes **only** once all three
  handoffs (G01, P04, V03) are collected and verified against their own deliverable lists + manifests.
- **On collection:** copy only the listed deliverables into `docs/evidence/{g01,p04,v03}/`. The
  **P04 publish set** (new files only; the 10 `pr8_retrieved/` files stay local — they are the
  repo's own committed blobs, referenced by ID) is exactly:
  `docs/evidence/p04/P04_PACKAGE.md`, `docs/evidence/p04/P04_EVIDENCE_MANIFEST.sha256`,
  `docs/evidence/p04/P02_PLATFORM_AUDIT.md`, and the 6 representative P02/P03 PNGs as
  byte-identical copies under `docs/evidence/p04/p02_representative/`
  (`final_baseline 3D538F1C…`, `orbitOK_00 1E237962…`, `orbitOK_05 0FFA1C91…`,
  `joint_pose_base 79918E0E…`, `joint_pose_kneeL_100 4275EBDC…`, `glass_001 538CE59B…`).
  Then verify the staged diff + blob hashes (`git hash-object` worktree == `git ls-files -s`
  index, accounting for `* text=auto` LF normalization and `.png binary`); re-check remote
  head; commit; push `astra/gait-capture` normally (no master, no force-push, nothing under
  `engine/build/`); report full commit SHA + file list + results. If the remote advanced →
  STOP and report the conflict.

---

## Confirmation

| Item | Status |
|---|---|
| Files written (new) | `.tmp/p04_20260906_1904/` packet (this doc + manifest + `pr8_retrieved/` ×10) |
| Live engine mutation | **None** (read-only; the active `engine_fit6.out` engine run observed, not touched) |
| Alan's checkout | Untouched; branch `master` @ `51cd7212`; git status = same 5 pre-existing files |
| Commits / pushes / branches / installs / production edits | **None** (isolated pub clone local-only; nothing pushed) |
| `ChimeraEngine/engine/build/` | **Untouched** |
| Publication | **Prepared, blocked** pending G01 + V03 packets (no partial publish) |