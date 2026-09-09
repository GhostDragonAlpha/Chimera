# GPU demo runtime evidence

This directory records the isolated Windows runtime attempt for GLM-GPU-DEMO-01.

- Branch: `astra/gait-capture`
- Executable: `C:/Users/allen/AppData/Local/Temp/opencode/chimera_build_gpu_demo_msvc/Release/chimera_engine.exe`
- Executable SHA-256: `30982A1C13055BC623D1AE82DFDB9B1EF9ADD3A6D948BBF424D138B49D7C3B82`
- SPIR-V: `Release/shaders/membrane_demo.spv`
- SPIR-V SHA-256: `71B5F8D37ACFF921EA249C74ADE6D4074D79EA80D39BF03D66488F1C47C3898F`
- Launch: `chimera_engine.exe 8091 --no-restore 1280 720`
- Port 8091 was verified free before isolated launches.
- Firewall access was allowed by the operator.

Observed successful bring-up:

- engine initialized and listened on 8091;
- B2 `/membrane_demo_bin` initialization succeeded once;
- initial f32 energy was `2.625` J and centre was `[0,0,0.125]`;
- one `/membrane_demo {"op":"step"}` succeeded, reaching centre z
  `0.123999998` and energy `2.62457323` J;
- `/frame` returned a PNG in the successful run.

Source corrections made after the first runtime attempt:

- controller now loads the CMake-emitted `membrane_demo.spv` name;
- gamma admission re-evaluates accepted geometry before reporting energy/force;
- reset restores initial gamma, f32 gamma, and material snapshot;
- MSVC `std::min`/`std::max` macro collisions were repaired without changing
  physical constants or numerical tolerances.

Post-correction re-run:

- the isolated process terminated with Windows Application Error 1000,
  `VCRUNTIME140.dll`, exception `0xc0000005`, while servicing the demo upload;
- no Alan process was controlled;
- gamma-zero, fixed-state doubling, reset-after-gamma, rejection integrity,
  full relaxation, state-linked capture, and DYAD are **NOT TESTED** after the
  correction.

The earlier successful initialization and one-step observations are retained
as partial runtime evidence only; they do not close the GPU-driven milestone.
