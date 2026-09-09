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
