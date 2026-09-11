# RESULT — engine-feature-resource-lifetime-02, generation 1

Worker: subagent-worker-03 · slot 2 (`E:/ChimeraWork/slot-02`) · base `5199d9c3`
(astra/gait-capture tip; task-record base, used verbatim) · PR base `astra/gait-capture`.

## Verdict

**PASS.** Each declared loaded feature (joints + the matter CSR/work pair,
strain, water, frost) now releases its explicit device children exactly once —
at shutdown via four new null-guarded family helpers, and at replacement via
`w_make_pipeline` — after the drain, with mapped host memory unmapped before
free. Native validation (KHRONOS, ON, no suppression, identical config for
baseline and repair) reports **zero `[VK ERROR]` lines** in all three
preregistered family cases, where the unmodified base reported the truncated
leak class (10 × VUID-vkDestroyDevice-device-05137 per run). Retained accepted
state gates are unchanged and green.

## Commit chain (base 5199d9c3 → head)

| Commit | Content |
|---|---|
| `80d3ecf5` | PREREGISTRATION (ledger + cases + decision rule, zero measured actuals) + runner — committed BEFORE any build/run |
| `d7173e1e` | runner fix (bytes step-detail JSON-serializable) + retained runner-bug failed attempt 01 |
| `f0129181` | force-add failed-attempt logs past the `*.log` ignore |
| `e21afdca` | baseline runs (F1/F2/F3) + F3 failed attempt 01 (bare `render_tri_frost.spv` missing from derived build) + staging fix |
| `9d6144d7` | the correction: `destroy_{strain,joints,water,frost}_resources()` + `w_make_pipeline` replacement ownership + shutdown wiring + M1 pair moved (engine.cpp +113/−4, engine.hpp +5) |
| `234973d4` | repair runs (F1/F2/F3, zero errors) + retained sType-regression failed attempts 01 |
| head | docs: `THE_VULKAN_FEATURE_LIFETIME.md`, `MEASUREMENT.json`, `RESULT.md` |

## Validation table (family → load/clear/reload/close → baseline → after)

| Case | Paths executed | State gates (live endpoints) | [VK ERROR] baseline → repair | 05137 baseline → repair | Ordered close |
|---|---|---|---|---|---|
| F1_JOINTS | mesh(D1) → hinge scaffold (strain created) → joints load → **joints reload** → **mesh B3 clear** → mesh re-upload → strain on → capture → close | `/joints loaded && n_joints==19` (before reload, after reload, after clear cycle); `/strain on && hinge` | 10 → **0** | 10 → **0** | exit 0, markers ordered, no watchdog, HWND destroyed, backdrop unchanged |
| F2_WATER | water load → **water reload** → readback state read → capture → close | `/water_state` binary header `ns >= 1` | 10 → **0** | 10 → **0** | same |
| F3_FROST | frost load → `/frost on` → **frost reload** → `/frost on` → capture → close | `/frost loaded && on` | 10 → **0** | 10 → **0** | same |

Baselines retain the measured defect verbatim (leak class: 6+ VkBuffer and
3–4 VkDeviceMemory reported before the validator's duplicate_message_limit
truncates; the full predicted surface is in the PREREGISTRATION ledger).
Repairs report zero, so no truncation applies. Full per-run records:
`baseline_*/result.json`, `repair_*/result.json`, `engine.stderr.log`,
`engine.stdout.log` (force-added past the `*.log` ignore).

## Fixtures (sourced, existing; sha256 per run in each result.json)

D1 monkey mesh + eye geometry + hinge scaffold + joints pack (C1/D1 lane
recipes), `water_gpu/water_payload.npz` (H4 lane recipe),
`frost_gt/frost_engine.bin` (H9/H12 integrated v3 model). No physics input was
authored by this task; no solver step was run; no numerical gate was read or
changed.

## Suites

- `test_field_physics.py`: 24 passed.
- `test_engine_gates.py`: 6/9 — **identical at base `5199d9c3` and at this
  head** (same 3 pre-existing failures). The gates-preservation requirement
  holds (unchanged); the failures are a base defect in the Python state gates,
  outside this task's scopes and untouched by a C++ teardown change.
- Fleet suite (`tools/agent_fleet`): Ran 198 tests — **OK (skipped=1)**,
  twice consecutively. One earlier run that day FAILED (failures=1; a
  transient 409 ResourceWarning is visible in its tail and the failing test's
  identity was not captured before the clean re-runs); both clean runs are the
  recorded verdict.

## Falsifier check

- Leaked device child: ELIMINATED on the declared cases (0 reports ×3 repairs,
  against 10 ×3 baselines), identical validation configuration — not suppressed
  anywhere.
- Double-free / invalid use: none (repairs clean; the loader-side
  reload releases were not modified).
- Skipped required feature called PASS: every case's family gate read the live
  engine state (`/joints`, `/strain`, `/water_state`, `/frost`) AND a presented
  `/glass` frame was captured with the family loaded.
- Arbitrary unlabelled physics inputs: none — fixture recipes are the prior
  lanes' recorded ones; every fixture sha256 recorded.
- Changed numerical tolerance: no numeric gate read or modified anywhere.
- Certification of unexecuted paths: NOT_TESTED (declared in the
  PREREGISTRATION and restated here): gait/volp reload replacement (their
  shutdown coverage unchanged; the shared helper's release is null-guarded),
  water solver stepping and frost decode numerics (no steps run),
  `/matter_state` values (CSR pair lifetime certified, values not gated),
  membrane-demo path (PR #58's V3, not re-run here).

## Retained failed attempts (all verbatim)

1. `baseline_F1_JOINTS_failed_attempt_01/` — runner bug (bytes step detail not
   JSON-serializable) after the engine had already exited cleanly; no
   measurement landed; fixed in `d7173e1e`.
2. `baseline_F3_FROST_failed_attempt_01/` — `frost: render_tri_frost.spv
   missing`: the derived shader build emits `render_tri_frost.frag.spv` while
   `load_frost` reads the bare name (recorded ADJACENT DEFECT, not fixed here —
   outside this task's scopes; see THE_VULKAN_FEATURE_LIFETIME.md). The runner
   now stages a glslc-derived copy of the repo's own frag source, command and
   hashes recorded in the run's `result.json`.
3. `repair_{F1,F2,F3}_JOINTS|WATER|FROST_failed_attempt_01/` — a
   worker-introduced regression: the first correction edit dropped the
   pre-existing `smci.sType` assignment in `w_make_pipeline`. Validation caught
   it on every call (VUID-VkShaderModuleCreateInfo-sType-sType); fixed at
   source before the clean repair generation. Lesson: the anchor-and-replace
   must carry the FULL replaced block — recorded here so the next lane inherits
   the pathway.

## Resource record

- rtx4090 acquired (rev 774) and engine_demo chained (rev 775) BEFORE any build
  or run; released after drain with process evidence (submit_review refuses
  first). No other process, port, or engine was touched; the operator's engine
  (ports 8080/8090) was never approached; all writes stayed in
  `E:/ChimeraWork/slot-02` (+ `%TEMP%`).
