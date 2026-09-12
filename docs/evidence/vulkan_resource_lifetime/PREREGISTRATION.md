# PREREGISTRATION — engine-vulkan-cleanup-02, generation 1

Written and committed BEFORE the first native build or run of this task.
Branch `astra/tasks/engine-vulkan-cleanup-02`; source base `265dad98` (integrated PR27)
reconciled with `origin/astra/gait-capture` at `c1a1ec5a` (merge, no force).
Replacement task for the unclaimable-by-construction `engine-vulkan-cleanup-01`
(disposition recorded by lead glm53-lead-02, epoch 5): identical theory and gates.

## Statement / Prediction / Falsifier (packet verbatim)

STATEMENT: each resource created on declared startup/resize/capture/membrane-demo paths
has explicit ownership and is destroyed once before its device, after GPU work and host
workers drain.

PREDICTION: audited create/destroy ledger and smallest coherent cleanup correction remove
actual Vulkan validation errors in these native cases, retain ordinary visible rendering
and frozen membrane reset/step gates, with ordered normal shutdown.

FALSIFIER: live-child validation error, invalid destruction/double free, suppressed
validation, crashed/hung close, changed accepted geometry/numerical gate, foreign process
action, or certification of unexecuted water/gait/frost paths.

## Source binding of the audit

- `ChimeraEngine/engine/engine.cpp` at `265dad98`
  (git blob `3892217f821fc3e0c0868bbe966f88c9a6068997`, 473437 bytes,
  sha256 `1325676ded0e64cb0614e851d8bf559709a79b157795ff8d36bb8f65be87a8b2`).
- Prior read-only audit retained at `E:/ChimeraWork/evidence/vulkan_ownership_audit_20260910`
  (LEDGER.json + REPORT.md); every load-bearing row below was re-verified against the base
  source by this task before this file was written.
- Original failing evidence retained at tip
  `docs/evidence/engine_shutdown_order/parent_runtime/owned_visual/run_01/engine.stderr.log`
  (PR27 lane, unchanged executable): 10 VUID-vkDestroyDevice-device-05137 reports before the
  validator's duplicate_message_limit (10) truncates further reporting — 3 VkImage,
  3 VkDeviceMemory, 3 VkImageView, 1 VkShaderModule. Numeric handle values are dispatch
  magic and are NOT mapped to fields; the mapping below is source-derived.

## Audited create/destroy ledger (declared paths, base source)

| Device children | Create site (engine.cpp) | Destroy site | Verdict |
|---|---|---|---|
| `rt_msaa_image_` / `rt_msaa_mem_` / `rt_msaa_view_` | 8748 / 8754 / 8764 (`create_offscreen`) | previous generation only, 8666–8668; NO destroy in `Engine::shutdown` (797–967) | live at vkDestroyDevice — leak |
| `rt_depth_image_` / `rt_depth_mem_` / `rt_depth_view_` | 8809 / 8815 / 8824 (`create_offscreen`) | latest generation only, via `destroy_triangle_resources` 5512–5514 at shutdown:889; `resize` 8593–8598 releases fb/pass/color but NOT depth | every replaced generation leaks |
| `tri_shadow_frag_mod_` / `tri_shadow_vert_mod_` | 1184–1189 (init, when SPIR-V present) | none anywhere | live at vkDestroyDevice — leak |
| `tri_shadow_pipeline_` | 1577 (init, when both modules exist) | none anywhere | live at vkDestroyDevice — leak |
| swapchain `depth_image_`/`mem_`/`view_` | `create_depth_resources` | `destroy_depth_resources` at shutdown:830 and resize:8582 | covered |
| `rt_image_`/`rt_mem_`/`rt_view_`, `rt_framebuffer_`, `rt_render_pass_` | `create_offscreen` | shutdown 831–837 and resize 8593–8597 | covered |
| membrane demo `md_*` buffers/memories/pipeline/layout/dsl/pool/module | `membrane_demo_init` 3994+ | `Engine::shutdown` (unmap + `md_destroy_buf` rows, `md_pipe_`…`md_mod_`) | covered |
| capture/glass staging | `ensure_*_staging` 6002/6031 | shutdown 885–886 (+size-change rebuild) | covered |
| Studio UI (`ui.cpp`) fbs_, vbuf_, pipe_, layout_, dpool_, dsl_, font family, thumb stage, rp_ | init / `create_swap_resources` | `StudioUI::shutdown` (ui.cpp 3257–3279) | covered |
| compute/hinge/volp/gait/sort/skin/triangle-floor-edge families, semaphores, fences, pools | init | shutdown 887–955 | covered |

Count consistency with the retained stderr: two `WM_SIZE` resize generations occurred in the
PR27 run (window placed via `SetWindowPos`, engine handles WM_SIZE at engine.cpp:109), so at
`vkDestroyDevice`: 2 leaked offscreen-depth trios + 1 never-destroyed MSAA trio = exactly
3 VkImage + 3 VkDeviceMemory + 3 VkImageView, then the duplicate limit cut the report after
the first leaked VkShaderModule (2 shadow modules + 1 shadow pipeline actually live).

## Planned smallest coherent correction (source-derived before runs)

1. New `Engine::destroy_offscreen_resources()` (declared in `engine.hpp`, defined next to
   `create_offscreen`): destroys, in dependency order with null-guarded single ownership —
   `rt_framebuffer_`, `rt_render_pass_`, `rt_msaa_view_`, `rt_msaa_image_`, `rt_msaa_mem_`,
   `rt_depth_view_`, `rt_depth_image_`, `rt_depth_mem_`, `rt_view_`, `rt_mem_`, `rt_image_`.
2. `resize()` replaces its 5-line rt release block with a call to the helper before
   `create_offscreen()` — every replaced generation is destroyed exactly once.
3. `Engine::shutdown()` replaces the rt block with the same helper call (same position in
   the ordered teardown, before `vkDestroyDevice`) — the final MSAA and depth trios die
   before the device.
4. `destroy_triangle_resources()` loses the rt_depth rows (depth ownership moves to the
   offscreen helper; no dependence of offscreen ownership on a feature helper) and gains
   `tri_shadow_pipeline_`, `tri_shadow_frag_mod_`, `tri_shadow_vert_mod_` destroys
   (triangle-family instruments die with the triangle family).
5. `create_offscreen()`'s own previous-generation MSAA release stays (idempotent guards;
   after (2) it sees null handles and destroys nothing).

No change to geometry, numerics, shaders, gates, validation configuration, or any
non-declared path. Feature families (joints/strain/water/frost loads) are NOT touched —
they are the declared scope of the follow-up task `engine-feature-resource-lifetime-01`
and remain unexecuted/unclaimed here.

## Preregistered observable cases (identical for baseline and repair binaries)

Launch: private build from this slot's source, staged with its `shaders/` into an isolated
runtime dir; invoked as `chimera_engine.exe <port> --no-restore`, CWD = runtime dir, own
process, own visible window, stderr+stdout captured to files. Validation layers ON.

- V0 startup: owned window appears; `GET /state` returns JSON; listener PID == engine PID.
- V1 resize: two `SetWindowPos` size changes on the verified engine HWND (1280x720 →
  1000x640 → 1180x680) → two `WM_SIZE` → two `Engine::resize` generations.
- V2 capture: `GET /glass` returns bytes starting with the PNG magic (ordinary rendering
  retained; swapchain readback produced by the engine PID).
- V3 membrane-demo: `POST /membrane_demo_bin` with a synthetic tetrahedron
  (magic `0x3130444D`, nv=4, nf=4, centre=0, valid CSR) → `ok:true`;
  `POST /membrane_demo {"op":"reset"}` → `ok:true`; `POST /membrane_demo {"op":"step"}` →
  `ok:true`; `GET /membrane_demo` status returns without error.
- V4 ordered shutdown: `WM_CLOSE` posted to the owned HWND only; process exits 0 within a
  10 s watchdog (no kill); stdout markers in order `shutdown: admission_closed` →
  `shutdown: boot_joined` → `shutdown: http_stopped` → `shutdown: engine_shutdown`;
  HWND gone after exit; owned test backdrop unchanged between reference and after captures.

DECISIVE GATE (repair): with the identical validation configuration, stderr contains ZERO
`VUID-vkDestroyDevice-device-05137` (and zero new validation errors of any VUID) across
V0–V4, the close is ordered and unforced (exit 0), and ordinary rendering is retained
(V2 PNG + window alive through V3). BASELINE (expected fail, retained verbatim): the same
cases on the pre-repair binary report the live-child VUID at V4.

## Validation configuration (identical both runs, no suppression)

- `VK_LAYER_KHRONOS_validation` enabled by the engine itself when present
  (engine.cpp:474–500); debug-utils messenger routes `[VK ERROR]` to stderr
  (engine.cpp:397–523). Validator duplicate_message_limit is the default 10 (explains the
  truncated retained baseline report). SDK 1.4.328.1. No env suppression, no disabled
  checks, no message-ID filters anywhere in the build or launch.

## Frozen gates / honest limits

- Existing membrane reset/step CPU regression gates must keep their accepted results
  (changed numerical gate = falsifier). Full fleet suite from repo root expected 0 failures
  (1 Windows-symlink skip).
- Water/gait/frost/joints/strain load paths are NOT executed and NOT claimed. CPU
  ownership coverage is acceptable only for the offscreen/shadow ownership unit; the
  decisive evidence is the native validation run.
- DYAD review of the final visible window via the subagent template if available;
  otherwise recorded NOT_TESTED.
- Never touched: operator checkout, protected build paths, ports 8090/8099/8080, other
  processes' windows.
