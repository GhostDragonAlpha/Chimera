# GLM-GPU-DEMO-01 runtime record

## Preregistration

The governing statement, predictions, and falsifiers are in
`docs/THE_GPU_DEMO01_PREREGISTRATION.md`. This record keeps CPU, GPU,
runtime, visual/DYAD, and human verdicts separate.

## Build

- Checkout: `C:/Users/allen/AppData/Local/Temp/opencode/chimera_pub`
- Branch at inspection: `astra/gait-capture`
- Build directory: `C:/Users/allen/AppData/Local/Temp/opencode/chimera_build_gpu_demo_msvc`
- Protected `ChimeraEngine/engine/build/`: not used.
- Generator/toolchain: Visual Studio 17 2022, x64, MSVC 19.44.35228.0.
- Vulkan SDK: `C:/VulkanSDK/1.4.328.1`.
- Build command:
  `cmake -S C:/Users/allen/AppData/Local/Temp/opencode/chimera_pub/ChimeraEngine/engine -B C:/Users/allen/AppData/Local/Temp/opencode/chimera_build_gpu_demo_msvc -G "Visual Studio 17 2022" -A x64 -DVULKAN_SDK=C:/VulkanSDK/1.4.328.1`
  followed by
  `cmake --build C:/Users/allen/AppData/Local/Temp/opencode/chimera_build_gpu_demo_msvc --config Release --parallel 4`.
- Latest executable SHA-256:
  `30982A1C13055BC623D1AE82DFDB9B1EF9ADD3A6D948BBF424D138B49D7C3B82`.
- Latest engine-built shader SHA-256 (`Release/shaders/membrane_demo.spv`):
  `71B5F8D37ACFF921EA249C74ADE6D4074D79EA80D39BF03D66488F1C47C3898F`.
- The first runtime attempt exposed a concrete filename defect: CMake emitted
  `membrane_demo.spv`, while the controller requested
  `membrane_demo.comp.spv`. The source now requests the emitted filename.

## Runtime bring-up

The firewall prompt was allowed. Port 8091 was checked free before each
isolated launch. The only controlled processes were isolated executable PIDs
from the build directory; Alan's engine was not controlled.

Launch command:

`C:/Users/allen/AppData/Local/Temp/opencode/chimera_build_gpu_demo_msvc/Release/chimera_engine.exe 8091 --no-restore 1280 720`

The executable survived initialization, opened its HTTP listener, and
reported stable frame output around 55--56 FPS at 1280x720. The selected
Vulkan device was not printed by this engine path, so RTX identity is NOT
claimed by this record.

A B2 upload through `/membrane_demo_bin` succeeded. Initial status:

- energy `2.625` J;
- centre `[0, 0, 0.125]`;
- centre force approximately `[0, 2.98023224e-08, -0.428571433]`;
- `accepted_state_id=17560123212910228982`;
- material snapshot reported `gamma_admitted_f64=1`,
  `gamma_uploaded_f32=1`, unit `J/m^2`, and `wu_to_m=1.0`.

A single GPU step succeeded: iteration/accepted count became 1, centre z
`0.123999998`, energy `2.62457323` J, and the state ID changed. A frame
capture returned PNG bytes (3,687,468 bytes in one run).

## Runtime findings

The first runtime control sequence found and preserved two defects:

1. The demo shader filename mismatch caused init failure before the fix.
2. Gamma re-admission updated the GPU gamma buffer but did not immediately
   refresh the reported energy/force, and reset did not restore the initial
   material. These were corrected in the source by re-evaluating the accepted
   buffer after admission and restoring the initial gamma/snapshot on reset.

After that correction, a later control attempt caused an access violation in
`VCRUNTIME140.dll` while servicing the demo upload/control request. Windows
Application Error event 1000 recorded exception `0xc0000005` for the isolated
`chimera_engine.exe`; the process was not Alan's engine. The exact faulting
source line has not been established. Therefore the post-correction gamma,
reset, rejection, and fixed-state doubling controls are **NOT TESTED**.

The earlier pre-correction controls are retained only as diagnostic evidence:
positive-gamma single-step passed; the earlier gamma-zero control showed
stationary geometry; however the earlier fixed-state gamma-doubling result was
invalid because admission status did not refresh, so it is not a PASS.

## Verdicts

- CPU reference: PASS (existing `tools/membrane_window_demo.py` rerun;
  gamma 1 reaches 126 accepted steps and `stagnated`; gamma 0 is stationary
  with no accepted steps).
- Standalone Vulkan probe: existing published PASS remains unchanged; this
  record does not rerun or replace it.
- Engine build/shader compilation: PASS.
- Engine startup/listener: PASS for isolated instance on the allowed firewall
  path.
- Engine GPU material demo initialization: PASS once, before the later
  post-correction crash.
- Engine GPU single-step: PASS once, before the later post-correction crash.
- Gamma-zero, fixed-state doubling, reset after gamma change, rejection
  integrity after the correction: NOT TESTED.
- Full matched CPU/GPU relaxation trajectory: NOT TESTED.
- Compute-to-render state-id/capture hash certification: NOT TESTED.
- Visual capture comparison/DYAD: NOT TESTED.
- Human acceptance: NOT CLAIMED.
- GPU-driven engine milestone: NOT COMPLETE.

The remaining blocker is a concrete isolated Windows access violation during
post-correction control/upload handling. Do not infer RTX hardware identity,
full numerical parity, or window/DYAD acceptance from the successful startup,
initialization, or single-step observations.

---

# GLM-GPU-DEMO-02 — crash resolved, full runtime gate PASS (2026-09-09)

## Crash diagnosis (marker ladder, all evidence preserved)

Nine WER records (2026-09-08 22:39 through 23:59) showed the IDENTICAL fault:
`0xc0000005` at VCRUNTIME140.dll offset `0x1ddea` (inside `memcpy`), across
rebuilds — deterministic, hence logic/toolchain-state, not random. A
stderr marker ladder through `membrane_demo_init` bound the crash to the
statement after "[md] initial position copy ready": the valid-sized
`md_idx_host_.assign(...)` — whose inputs were independently valid. A
valid-size memcpy crashing there means corrupted CRT vector internals.

**Root cause: a stale translation unit.** The build directory sits under the
user Temp dir (CMake warning MSB8029: "Intermediate/Output directory cannot
reside under the Temporary directory as it could lead to issues with
incremental build"); earlier `engine.hpp` member-layout changes had left a
stale object compiled against the old header. A `--clean-first` rebuild of
the SAME source eliminated the crash entirely. No source change fixes this
crash; the fix is the clean build, recorded here.

Falsifier check: the crash reproduced exactly (single `/membrane_demo_bin`
request, exit 0xC0000005) before the clean rebuild and never after — across
four subsequent builds including two more `--clean-first` passes.

## Second, independent defect: JSON value-shadowing (source fix)

With the crash gone the gate exposed: after any `/membrane_demo` gamma
request, energy and force read EXACTLY 0 (validity stayed 1; the kernel ran
and wrote the energy buffer). Root cause in `main.cpp::find_colon_after`:
it returned the FIRST textual occurrence of the key, which in
`{"op":"gamma","gamma":2.0}` is the VALUE of `op`; no colon follows, so
`get_double("gamma", 0.0)` silently returned its DEFAULT 0.0, which
`md_admit_gamma(0.0)` legally admitted as a zero material — every observed
symptom, including the never-recovering status refresh (each subsequent
admission parsed 0.0 again).

Fix: scan ALL occurrences of the key; accept the first followed by ':';
skip value occurrences and longer names sharing the prefix (closing-quote
guard). No tolerance, fixture, shader or physics change.

## New runtime gate (option-b per Astra; Astra review answered)

Astra's review items were resolved: no prior symbolized record of this
crash; the source-publication discrepancy was real — commit `35f97e34` had
never been pushed (the crash session died before `git push`); pushed as a
fast-forward, remote head now `35f97e346abb7cb3f703d5af0e1d7edfe5313680`.
The runtime numerical gate is option (b): a separate engine-runtime gate
reusing the frozen fixtures/references — `tools/membrane_demo_client.py`
(separated requests; launch discipline: refuses occupied ports, terminates
only the PID it launched; archives engine stdout/stderr per run).

Preregistered: STATEMENT — the demo executes the declared law through its
actual runtime path. PREDICTION — comparisons and state-transition controls
meet their preregistered bounds. FALSIFIER — any bound breach,
accepted-state corruption, incomplete readback, or unverifiable state
association.

## Results (two consecutive clean-build gates, 20 PASS + 1 INFO each)

- init: E=2.625 vs frozen ref 2.6249999533666486 (f32 readback); centre
  [0,0,0.125]; material snapshot gamma f64=1/f32=1, J/m^2, wu_to_m=1.0.
- Fixed-state gamma doubling: E2=5.25=2×E0 EXACT; centre force
  -0.857142866 = 2×F0 EXACT.
- gamma back to 1: E=2.625 restored.
- step1: it=1, E=2.62457323 (CPU law first step 2.6245730615, f32-consistent).
- Full run: terminal `stagnated` at iteration 126, E=2.59807611 vs CPU
  2.5980761647224426 — SAME terminal state as the CPU law, not just an
  iteration-count match.
- reset: E=2.625, it=0, z=0.125 restored.
- rejection integrity: `invalid_trial_REFUSED`, accepted_state_id unchanged.
- gamma=0: `stationary`, it=0, no accepted step.
- Captures `final_relaxed.png` / `raised_gamma0.png` with status sidecars
  and accepted_state_id linkage (render-side certification remains
  conditional per GLM-WINDOW-02; not upgraded here).
- CPU regression rerun (shared-code rule): gamma=1 `stagnated`, 126
  accepted, 2.6245730615178493 → 2.5980761647224426; gamma=0 `stationary`.
- The leftover single-request CRASH in evidence 20260909T135116 was the
  client probing a port after its own gate had terminated the engine; the
  engine was not running; no engine defect.

## Verdicts after GLM-GPU-DEMO-02
- Engine runtime numerical gate (frozen B2, actual 11-binding/32-byte ABI,
  GPU readback): PASS.
- CPU: PASS. Engine build/shader: PASS. Startup/listener: PASS.
- Full matched CPU/GPU relaxation: PASS at terminal state and endpoints;
  per-iteration trajectory dump remains NOT TESTED.
- Gamma-zero, fixed-state doubling, reset, rejection integrity: PASS.
- Visual/DYAD review of the GPU-driven demo: NOT TESTED (next task).
- Human acceptance: NOT CLAIMED. GPU-driven engine milestone: implementation
  and numerical runtime gate complete; DYAD/human verdicts pending.

