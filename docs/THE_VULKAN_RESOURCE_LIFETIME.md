# THE_VULKAN_RESOURCE_LIFETIME.md — offscreen family ownership

Task lane: `engine-vulkan-cleanup-02` (generation 1, slot 4). Source binding:
`ChimeraEngine/engine/engine.cpp` blob `3892217f821fc3e0c0868bbe966f88c9a6068997`
at base `265dad98`, correction in commit `527bde2f`.

## The law

Every device child created on the startup/resize/capture/membrane-demo paths has ONE
explicit owner and is destroyed exactly once, before `vkDestroyDevice`, after
`vkDeviceWaitIdle` and worker drain (VUID-vkDestroyDevice-device-05137). Split or
implicit ownership is how the leak happened: three families, three different destroy
arrangements, two of them wrong.

## The ownership map (post-correction)

- `Engine::destroy_offscreen_resources()` is the SINGLE owner of the offscreen family
  created by `create_offscreen()`: framebuffer, render pass, MSAA view/image/mem, depth
  view/image/mem, color view/image/mem. `resize()` calls it to release a replaced
  generation; `shutdown()` calls it for the final one. Null-guarded, nulling handles —
  each object destroyed once, a second call destroys nothing.
- `create_offscreen()` keeps its own previous-MSAA release (idempotent after the above;
  it sees null handles on the resize path).
- `destroy_triangle_resources()` owns the triangle/floor/edge family INCLUDING the
  contact-shadow instruments (`tri_shadow_pipeline_`, `tri_shadow_frag_mod_`,
  `tri_shadow_vert_mod_`) and NO LONGER owns any offscreen object (the rt_depth rows
  moved to the offscreen helper — offscreen lifetime must not depend on a feature
  helper's call graph).
- `destroy_depth_resources()` keeps owning the swapchain depth trio (its own family,
  called by `resize()` and `shutdown()`).
- Feature families (joints/strain/water/frost) are OUT OF SCOPE here — unexecuted at
  this lane's runtime cases and therefore unclaimed; their loaded/cleared lifetimes are
  the declared scope of `engine-feature-resource-lifetime-01`.

## Evidence (proof lives in files, not here)

- Method + preregistered cases + validation config:
  `docs/evidence/vulkan_resource_lifetime/PREREGISTRATION.md`
- Baseline failure retained verbatim (10 truncated VUID reports) and repair runs
  (0 validation errors, ordered close, rendering retained): `baseline_run_01/`,
  `repair_run_01/`, `repair_run_02/` in the same directory; commands and exe sha256 in
  `MEASUREMENT.json`; full matrix + falsifier check + NOT_CLAIMED list in `RESULT.md`.
- Frozen membrane reset/step gate (B2 fixture, 21 checks PASS): `b2_gate_repair_01/`.
- Original failing lane (PR27, unchanged executable):
  `docs/evidence/engine_shutdown_order/parent_runtime/owned_visual/run_01/`.
