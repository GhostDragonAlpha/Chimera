# RESULT — engine-vulkan-cleanup-02, generation 1

Worker subagent-worker-03, slot 4, port 8104. Preregistration committed (499f3902)
BEFORE the first build or run; implementation commit 527bde2f; this evidence committed
afterwards. Replacement task for unclaimable-by-construction engine-vulkan-cleanup-01
(master-list scope made it lead-only while the lead lacks the lane capabilities —
verified live; disposition by lead glm53-lead-02, epoch 5). Theory and gates identical.

## What was wrong (audited ledger, base 265dad98, blob 3892217f)

`create_offscreen()` builds three device-child families — the offscreen color trio
(`rt_image_/rt_mem_/rt_view_`), the MSAA trio (`rt_msaa_image_/mem_/view_`), and the
offscreen depth trio (`rt_depth_image_/mem_/view_`) plus `rt_render_pass_` and
`rt_framebuffer_`. Ownership was split three ways and incomplete:

1. `Engine::shutdown()` destroyed the color trio, pass and framebuffer — but had NO
   destroy for the final MSAA trio.
2. `resize()` released fb/pass/color before rebuilding, but NOT the old depth trio:
   every replaced resize generation leaked (only the latest generation was destroyed,
   indirectly, by `destroy_triangle_resources()` at shutdown).
3. `tri_shadow_pipeline_`, `tri_shadow_frag_mod_`, `tri_shadow_vert_mod_` (the contact
   shadow instruments, created at init when their SPIR-V is present) had no destroy
   anywhere.

This explains the retained PR27 stderr exactly: 3 VkImage + 3 VkDeviceMemory +
3 VkImageView (2 leaked depth trios + 1 MSAA trio) and a VkShaderModule report cut off
by the validator's duplicate_message_limit (10). Numeric handles were not mapped to
fields anywhere; the mapping is source-derived.

## The correction (smallest coherent)

New `Engine::destroy_offscreen_resources()` — single explicit owner of the whole
offscreen family, destroying framebuffer → pass → MSAA view/image/mem → depth
view/image/mem → color view/image/mem, null-guarded and nulling every handle (each
object destroyed exactly once; a second call destroys nothing; partial generations
handled). `resize()` calls it before `create_offscreen()`; `shutdown()` calls it in the
ordered teardown before `vkDestroyDevice`. `destroy_triangle_resources()` keeps the
triangle family but loses the rt_depth rows (offscreen ownership no longer depends on a
feature helper) and gains the three tri_shadow destroys. No geometry, numeric, shader,
gate, or validation-configuration change. engine.hpp: one added declaration.

## Measurement (decisive gate: actual native validation)

Identical preregistered cases V0–V4 on both binaries, validation layers ON
(VK_LAYER_KHRONOS_validation, SDK 1.4.328.1, no suppression), own process/window,
runtime dir `.tmp/engine_runtime/<name>`, port 8104:

| Case | Baseline (exe 3a6cab51…) | Repair (exe 68079001…) |
|---|---|---|
| V0 startup (owned window + /state) | PASS | PASS |
| V1 resize, 3 placements → ≥3 resize generations | PASS | PASS |
| V2 `/glass` capture | PASS, PNG 2,985,430 B | PASS, PNG 2,985,430 B |
| V3 membrane demo (bin upload nv=4 nf=4, reset, step, status) | PASS | PASS |
| V4 WM_CLOSE → ordered shutdown | PASS (exit 0, markers in order) | PASS ×2 |
| VUID-vkDestroyDevice-device-05137 reports | **10** (truncated at limit) | **0** |
| Total `[VK ERROR]` lines | 10 | 0 |
| engine.stderr.log | 4,305 B retained verbatim | 0 B |

Baseline stderr retained verbatim in `baseline_run_01/engine.stderr.log` (5 VkImage +
5 VkDeviceMemory reported before the limit; the view/shader/pipeline children were live
but unreported because the duplicate limit had been reached). Repair runs repeated
(`repair_run_02`): zero validation output again, same ordered close.

Repeatability + frozen gates:

- B2 membrane reset/step gate (`tools/membrane_demo_client.py gate`, frozen fixture
  3e264f49…): 21 checks, PASS/INFO only, summary rc 0 — E0 2.625 vs fixture
  2.6249999533666486, doubling, gamma-back, step descent, stagnation at it=126, reset
  restore, reject refused, gamma0 stationary. Its engine stderr: 0 bytes (a second full
  engine+membrane lifecycle, validation-clean). Evidence in `b2_gate_repair_01/`.
  A first gate attempt failed for a worker command error (`--port` without `--base`);
  retained verbatim in `b2_gate_failed_attempt_01/` — not an engine defect.
- Full fleet suite: `python -m unittest discover -s tools/agent_fleet -p 'test_*.py' -v`
  → OK (skipped=1): 0 failures, 1 expected Windows-symlink skip.

## Falsifier check

- Live-child validation error: ELIMINATED on the declared cases (0 reports, twice, plus
  the B2 lifecycle), with identical validation configuration — not suppressed anywhere.
- Invalid destruction/double free: none — no validation error of any kind in the repair
  runs; guards null handles, so the pre-existing MSAA release in `create_offscreen()`
  and the moved depth ownership cannot double-destroy.
- Suppressed validation: none (same layer/messenger config both sides; baseline errors
  retained verbatim).
- Crashed/hung close: none — exit 0 within watchdog, markers ordered, HWND destroyed,
  no kill.
- Changed accepted geometry/numerical gate: none — B2 frozen values identical; no
  numeric or shader file touched (shader manifest hashes recorded per run).
- Foreign process action: none — only test-owned HWNDs were queried/moved/closed;
  owned backdrop byte-identical before/after in every run.
- Certification of unexecuted water/gait/frost paths: NOT CLAIMED. Those feature
  families (plus joints/strain) were never loaded in these runs; their ownership is the
  declared scope of the follow-up task `engine-feature-resource-lifetime-01`.

## Not claimed / limits

- DYAD NOT_TESTED: the SUBAGENT reviewer class needs a spawned reviewer subagent
  (lead-side Agent call); this worker cannot spawn one, and the local LM Studio eye is
  operator-owned and off-limits. Rendering retention rests on the engine-produced
  swapchain readbacks (PNG sha256 recorded per run) with the owned window visible at
  capture, plus the B2 gate's two PNG captures.
- CPU ownership unit test NOT_APPLICABLE: engine internals are not CPU-unit-testable
  without restructuring; the preregistered decisive gate was native validation.
- The claims cover the declared startup/resize/capture/membrane-demo paths on this
  machine (RTX 4090, Windows, SDK 1.4.328.1) — not universal driver behavior, not
  performance, not restore/water/gait/frost lifetimes.
- `repair_run_02`'s two `/glass` PNGs are not committed (repeat of repair_run_01's
  image; sha256 + byte size recorded in its result.json); all logs and result.json are
  committed. Every other artifact is committed raw.

## Resource and scope record

rtx4090 + engine_demo acquired through the controller before the first build/run and
released only after every launched process had exited (verified: engine processes
exited with observed exit codes; ports 8104/8094 free). Protected build path never
written; operator checkout untouched; the B2 tool's auto-evidence dir was relocated
into this task's scope immediately after each run.
