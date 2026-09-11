# PREREGISTRATION — engine-feature-resource-lifetime-02, generation 1

Written and committed BEFORE the first native build or run of this task.
Branch `astra/tasks/engine-feature-resource-lifetime-02`; base `5199d9c3`
(astra/gait-capture tip; no reconcile needed). Realization of
engine-feature-resource-lifetime-01 with the corrected dependency on
engine-vulkan-cleanup-02 (PR #58, merged at ecc839ab, part of this base).
Replacement task for the unclaimable-by-construction `-01` (its recorded
dependency engine-vulkan-cleanup-01 can never integrate).

## Statement / Prediction / Falsifier (packet verbatim)

STATEMENT: each declared loaded feature releases its explicit device children
once after GPU/host drain, including replacement/clear paths.

PREDICTION: sourced existing feature fixtures and recorded per-feature
create/destroy ledger plus actual native validation exercise
load/clear/reload/close, zero lifetime VUID errors, no validator suppression,
retained accepted state gates unchanged.

FALSIFIER: leaked/double-freed/live-used device child, skipped required
feature called PASS, arbitrary unlabelled physics inputs, changed numerical
tolerance, or certification of unexecuted paths.

## Scope boundary (what this task certifies)

PR #58 (engine-vulkan-cleanup-02) closed the startup/resize/capture/demo
teardown (offscreen MSAA/depth family, tri_shadow family). This task certifies
the four LOADED feature families the private ownership audit
(E:/ChimeraWork/evidence/vulkan_ownership_audit_20260910, READ ONLY) listed as
omitted: **joints (+ the matter CSR/work pair it creates), strain, water,
frost**. Families already covered at base (membrane, sort, skin, hinge base
buffers, VOLP, gait, triangle/floor/edge, swapchain/frame, studio UI,
offscreen) are NOT re-certified here; where a covered helper already destroys
a declared child (water-vis pair via `destroy_triangle_resources`) the
coverage is recorded and NOT moved.

## Fixtures (sourced, existing — no invented inputs)

| Fixture | Path (sha256 recorded at run time) | Prior evidence lane |
|---|---|---|
| D1 monkey mesh | `.tmp/monkey_assets/recon/8955fb5b9c9b4e169456ccbae7c465f7_birth.glb` | C1 joints editor (scratch/_joints_verify.py) |
| eye geometry | `.tmp/eye_build/eye_geom.npz` | same |
| hinge scaffold | `.tmp/skeleton/joints_pack.npz` (J/axis/rom) | same |
| joints pack | `.tmp/skeleton/joints_pack.bin` | same (D1 driver sequence) |
| water payload | `.tmp/water_gpu/water_payload.npz` | H4 water lane (scratch/_chrome_verify.py) |
| frost model blob | `.tmp/frost_gt/frost_engine.bin` (FRO1) | H9/H12 integrated v3 model |

The mesh/hinge/joints POST bodies are built exactly by the recorded D1 driver
recipe (mesh_bin header + verts9 + tris; hinge header "<I13f" + zero weights;
joints pack bytes verbatim). Water/frost POST bodies are byte-assembled from
the fixtures by the same recipes those lanes recorded. No physics input is
authored by this task; no solver step is run; no numerical gate is read or
changed (the state gates are load-state boolean/count gates only).

## Audited per-family create/destroy ledger (base `5199d9c3`, engine.cpp)

JOINTS + MATTER — `Engine::load_joints` (4955):

| Device children | Create | Destroy at base | Verdict |
|---|---|---|---|
| `j_csr_buf_`/`j_csr_mem_` | 5172–5189 (transient map, unmapped 5187) | reload 5172; shutdown 919 | covered |
| `j_work_buf_`/`j_work_mem_`/`j_work_map_` | 5195–5204 (persistent map) | reload 5195–5204 (unmap); shutdown 920 destroys buffer+memory WITHOUT unmap | shutdown: mapped `vkFreeMemory` → VUID-vkFreeMemory-memory-00677 |
| `j_assign_buf_`/`mem_` 5225, `j_w_buf_`/`mem_` 5226, `j_parent_buf_`/`mem_` 5233, `j_joint2_buf_`/`mem_` 5239 | `upload_buffer` (reload-safe) | none at shutdown | leak |
| `j_state_buf_`/`j_state_mem_`/`j_state_map_` | 5243–5271 (persistent map) | reload 5246–5248 only | leak (+mapped free never happens: no free at all) |
| `joints_mod_`/`joints_dsl_`/`joints_layout_`/`joints_pipe_` | `w_make_pipeline` 5272–5273 | `w_make_pipeline` overwrites WITHOUT releasing → replacement leak per reload; no shutdown destroy | leak both paths |
| `joints_desc_pool_` (set rides pool) | 5278–5287 | reload only | leak at shutdown |

STRAIN — `Engine::set_hinge` (1899):

| Device children | Create | Destroy at base | Verdict |
|---|---|---|---|
| `strain_buf_`/`strain_mem_`/`strain_map_` | 1931–1952 (persistent map) | reload 1933–1935 (unmap+destroy+free) | leak at shutdown (mapped memory never freed) |

WATER — `Engine::load_water` (3608):

| Device children | Create | Destroy at base | Verdict |
|---|---|---|---|
| solver buffers `w_V_ w_depth_ w_areas_ w_bed_ w_eij_ w_ke_ w_lij_ w_qe_ w_eactive_ w_occ_` (+mems) | `upload_buffer` 3616–3638 (reload-safe) | none at shutdown | leak |
| `w_states_buf_`/`mem_` | 3643–3659 | reload 3650–3651 only | leak |
| `w_readback_buf_`/`mem_`/`map_` | 3662–3676 (persistent map) | reload 3662 only (unmap) | leak |
| `w_depth_/w_color_/w_occ_/w_vis_` × {`_mod_ _dsl_ _layout_ _pipe_`} | `w_make_pipeline` 3678–3684 | none anywhere (overwrite without release) | leak both paths |
| `w_vis_vbuf_`/`w_vis_indirect_buf_` (+mems) | 3690–3700 | `destroy_triangle_resources` 5508–5509 at shutdown | covered (NOT moved) |
| `w_desc_pool_` | 3711–3717 | reload only | leak at shutdown |
| `w_fence_` | 3745–3750 (created once) | none | leak |

FROST — `Engine::load_frost` (4663):

| Device children | Create | Destroy at base | Verdict |
|---|---|---|---|
| `f_lat_ f_m_ f_w_ f_ab_ f_lut_ f_color_ f_dbg_` (+mems) | `upload_buffer` 4704–4716 (reload-safe) | none at shutdown | leak |
| `f_color_rb_`/`mem_`/`map_`, `f_dbg_rb_`/`mem_`/`map_` | `make_readback` 4718–4744 (persistent maps) | reload only (unmap) | leak |
| `frost_mod_`/`frost_dsl_`/`frost_layout_`/`frost_pipe_` | `w_make_pipeline` 4741–4743 | none anywhere (overwrite without release) | leak both paths |
| `f_eye_buf_`/`f_eye_mem_` | 4750–4753 (created once) | none | leak |
| `tri_frost_frag_mod_` | 4756–4762 (reload destroys first) | no shutdown destroy | leak |
| `frost_frag_dsl_` 4764–4771, `frost_render_layout_` 4773–4776, `frost_frag_pool_` 4777–4787 (created once; set rides pool) | — | none | leak |
| `tri_frost_pipeline_` | create 4855–4858 (reload destroys first) | no shutdown destroy | leak |
| `frost_desc_pool_` | 4863–4870 (reload destroys first) | no shutdown destroy | leak |

Count consistency: a single generation of every family, all loaded once, then
close ⇒ ≥ 23 buffers + 23 memories + 10 shader modules + 10 pipelines + 8
layouts + 8 dsls + 3 pools + 1 fence live at `vkDestroyDevice`, plus 5 mapped
memories freed-while-mapped (j_work, strain, w_readback, f_color_rb, f_dbg_rb)
and 2 more mapped-then-never-freed (j_state, plus w_readback/f_color_rb/f_dbg_rb
in the mapped-free class). The baseline stderr is PREDICTED to report
VUID-vkDestroyDevice-device-05137 (child objects at device destruction) and
VUID-vkFreeMemory-memory-00677 (free of mapped memory), truncated by the
validator's duplicate_message_limit (10). The repair runs are PREDICTED to
report ZERO `[VK ERROR]` lines.

## Planned smallest coherent correction (before runs; single ownership)

1. `w_make_pipeline` (3559): destroy the four previous objects (`mod`, `dsl`,
   `layout`, `pipe`) when non-null before creating the new generation. This is
   the ONE place pipeline-family replacement happens for every compute family
   (gait 3354, volp 3492, water×4 3678–3684, frost 4741, joints 5272); all six
   call sites inside this task's executed set become correct, and the two
   outside it (gait, volp) are untouched in their shutdown coverage and
   unexercised here (their reload gains the same null-guarded release).
2. New null-guarded, idempotent family destroy helpers (declared in
   `engine.hpp`, defined next to the family loaders):
   - `destroy_strain_resources()`: unmap `strain_map_`; destroy `strain_buf_`
     + free `strain_mem_`.
   - `destroy_joints_resources()`: unmap `j_state_map_` + destroy
     `j_state_buf_/mem_`; destroy `j_assign_ j_w_ j_parent_ j_joint2_`
     buf/mem; destroy `joints_pipe_ layout_ dsl_ mod_`; destroy
     `joints_desc_pool_`; unmap `j_work_map_` + destroy `j_work_buf_/mem_`;
     destroy `j_csr_buf_/mem_` (the M1 pair moves here from shutdown 919–920 —
     single ownership, PR-#58 `destroy_offscreen_resources` precedent).
   - `destroy_water_resources()`: destroy `w_fence_`; destroy `w_desc_pool_`;
     destroy `w_depth_/w_color_/w_occ_/w_vis_` pipe/layout/dsl/mod; unmap
     `w_readback_map_` + destroy/free readback; destroy `w_states_`; destroy
     the ten solver buffer/memory pairs.
   - `destroy_frost_resources()`: destroy `frost_desc_pool_`; destroy
     `tri_frost_pipeline_`, `tri_frost_frag_mod_`; destroy `frost_frag_pool_`,
     `frost_render_layout_`, `frost_frag_dsl_`; destroy `frost_pipe_ layout_
     dsl_ mod_`; destroy `f_eye_`; unmap `f_dbg_rb_map_`/`f_color_rb_map_` +
     destroy/free both readbacks; destroy `f_dbg_ f_color_ f_lut_ f_ab_ f_w_
     f_m_ f_lat_` buf/mem.
3. `Engine::shutdown()`: after `destroy_triangle_resources()`, call the four
   helpers; the M1 j_csr/j_work block (919–920) is removed (moved into
   `destroy_joints_resources()`). Position in the ordered teardown is
   unchanged otherwise; `vkDeviceWaitIdle` (the drain) precedes everything.

No numerical path, shader, descriptor binding count, or accepted state gate is
touched. Gates stay byte-identical.

## Preregistered native cases (runner: run_feature_case.py, committed with this file)

Owned-window discipline inherited from the PR-#58 runner (only test-owned
HWNDs moved/closed/captured; engine staged unchanged with shaders into an
isolated runtime dir; stderr retained verbatim; validation layer
engine-enabled when present, no suppression, identical config for baseline and
repair; free port 8105; single static window — resize generations were PR
#58's scope).

- **F1_JOINTS** (exercises joints + matter + strain families, D1 sequence):
  startup → `/mesh_bin` (D1 monkey+eye) → `/hinge_bin` scaffold (strain
  created) → `/joints_bin` pack → `/joints_bin` AGAIN (replacement path) →
  `/mesh_bin` valid header with N=0/idxCount=0 (the B3 clear path; a
  zero-byte body is rejected by the parser) → `/mesh_bin` re-upload → `/strain
  {"on":true}` → gates: GET `/joints` `loaded==true && n_joints==19` (the
  pack's own size), GET `/strain` `on==true`, `/glass` PNG captured → ordered
  WM_CLOSE.
- **F2_WATER**: startup → `/water_bin` payload → `/water_bin` AGAIN
  (replacement) → gate: GET `/water_state` binary header `ns >= 1` → ordered
  WM_CLOSE. (No solver step; no clock; readback mapping exercised by the
  state read only.)
- **F3_FROST**: startup → `/frost_bin` blob → `/frost {"on":true}` →
  `/frost_bin` AGAIN (replacement) → `/frost {"on":true}` → gate: GET `/frost`
  `loaded==true && on==true` → `/glass` PNG captured → ordered WM_CLOSE.

Decision rule (fixed before runs): a family case PASSES only if the family was
actually loaded (its state gate read `true` from the live endpoint) AND the
run ends with exit 0, no watchdog, window destroyed, ordered shutdown markers,
and ZERO `[VK ERROR]` lines in the verbatim stderr. Baseline runs of the same
runner on the unmodified base are retained verbatim; they are EXPECTED to show
the lifetime VUIDs (that is the measured defect, not a pass/fail gate — the
baseline documents the before state). If a baseline run shows ZERO lifetime
VUIDs, the correction premise is falsified and no repair is needed — record
and stop. A repair run with any lifetime VUID, any suppressed validator
config, or a failed state gate is a FAIL and blocks submit_review.

Honest NOT_TESTED list (declared in advance): gait and volp reload replacement
paths (families outside the declared four; their shutdown coverage unchanged);
water solver stepping numerics and frost decode numerics (no step run; no
number read or compared); joints matter `/matter_state` values (CSR pair
lifetime is certified, its values are not this task's gate).

## Resources and safety

rtx4090 + engine_demo acquired through the controller BEFORE any GPU/engine
work, released only after drain evidence. Private slot build under
`.tmp/engine_build` (protected build path untouched); free port 8105; the
operator's engine (ports 8080/8090/8099) and LM Studio are never touched; no
validator suppression anywhere.
