# THE VULKAN FEATURE LIFETIME

> Companion to `docs/THE_VULKAN_RESOURCE_LIFETIME.md` (PR #58: startup / resize /
> capture / demo teardown). That doc closed the ALWAYS-ON families. This one closes
> the LOADED families: joint/strain, water, frost — the ones the private ownership
> audit (2026-09-10, `E:/ChimeraWork/evidence/vulkan_ownership_audit_20260910`)
> listed as omitted because they only exist after a feature upload.
>
> THE LAW (same sentence, wider scope): **every device child a loaded feature
> creates is destroyed exactly once — at replacement, at clear, and at shutdown —
> after the drain, with mapped host memory unmapped before it is freed.**

## The four helpers (engine.cpp / engine.hpp)

| Helper | Owns (destructor order) |
|---|---|
| `destroy_strain_resources()` | unmap `strain_map_`; `strain_buf_`/`strain_mem_` |
| `destroy_joints_resources()` | `joints_desc_pool_`; `joints_pipe_/layout_/dsl_/mod_`; unmap `j_state_map_` + `j_state_buf_/mem_`; `j_assign_/j_w_/j_parent_/j_joint2_` buf/mem; unmap `j_work_map_` + `j_work_buf_/mem_`; `j_csr_buf_/mem_` (M1 pair, moved here from `shutdown`) |
| `destroy_water_resources()` | `w_fence_`; `w_desc_pool_`; `w_{depth,color,occ,vis}_pipe_/layout_/dsl_/mod_`; unmap `w_readback_map_` + readback buf/mem; `w_states_`; the ten solver buffer/memory pairs (`w_V_ w_depth_ w_areas_ w_bed_ w_eij_ w_ke_ w_lij_ w_qe_ w_eactive_ w_occ_`) |
| `destroy_frost_resources()` | `frost_desc_pool_`; `tri_frost_pipeline_`/`tri_frost_frag_mod_`; `frost_frag_pool_`; `frost_render_layout_`; `frost_frag_dsl_`; `frost_pipe_/layout_/dsl_/mod_`; `f_eye_`; unmap `f_dbg_rb_map_`/`f_color_rb_map_` + both readbacks; `f_dbg_/f_color_/f_lut_/f_ab_/f_w_/f_m_/f_lat_` buf/mem |

All four are null-guarded and idempotent (fields nulled as they die), called once
from `Engine::shutdown()` right after `destroy_triangle_resources()`, inside the
drain barrier (`vkDeviceWaitIdle` runs earlier in the same function).

## Replacement ownership

`w_make_pipeline()` owns pipeline-family replacement: the previous generation's
`pipe/layout/dsl/mod` die before the new generation is created. This repairs the
per-reload leak for every compute family that reloads (joints, water ×4, frost;
gait/volp gain the same null-guarded release). The loaders' existing
reload-time releases (`upload_buffer`, `j_state`, `w_states`, `w_readback`,
`make_readback`, `frost_desc_pool_`, `tri_frost_*`) are unchanged.

## Unchanged coverage

- `w_vis_vbuf_`/`w_vis_indirect_buf_` stay in `destroy_triangle_resources()`
  (recorded coverage, not moved).
- Everything PR #58 closed (offscreen, tri_shadow, swapchain/frames, studio UI,
  membrane demo, sort/skin/hinge/volp/gait base buffers) is untouched.

## The measured gate

Preregistered in `docs/evidence/vulkan_feature_lifetime/PREREGISTRATION.md`
(commit `80d3ecf5`, before any run): three owned-window native cases
(F1_JOINTS, F2_WATER, F3_FROST), each loading its family from EXISTING sourced
fixtures, exercising load → replacement → (F1) the B3 mesh clear cycle →
close, with live state gates, KHRONOS validation ON and no suppression.

Result: baseline exe (prereg-commit source, `fa2c7468…`) reported the truncated
leak class (10 × VUID-vkDestroyDevice-device-05137 per run); the corrected exe
(`c3cfe41f…`) reported **zero `[VK ERROR]` lines in all three families**, with
ordered shutdown markers, exit 0, and unchanged state gates. Verbatim logs and
`result.json` per run live in `docs/evidence/vulkan_feature_lifetime/`.

## Known adjacent defect (recorded, NOT fixed here — outside this task's scopes)

`Engine::load_frost` reads the BARE name `shaders/render_tri_frost.spv`
(engine.cpp:4754) while the derived shader build (CMakeLists, 2026-09-03
stale-spv incident) emits `render_tri_frost.frag.spv`. A clean private build
cannot load frost without a hand-staged file; the evidence runner stages a
glslc-derived copy and records the command + hashes. The fix (rename the read
or emit the bare name) belongs to a shader-pipeline lane together with whoever
owns the operator runtime layout.
