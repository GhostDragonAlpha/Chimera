# Chimera

Chimera is a C++/Vulkan engine and physical-world simulation project with Python
reference laws, numerical falsifiers, runtime verification, and a creature/game
layer. The long-term direction is for accepted physical state to supply rendered
geometry, with the CPU providing derivations and reference tests before GPU ports.

The engine and its verification workflow are under active development. A passing
fixture or a completed local term hierarchy is not a completed game engine.

## Start here

- **Agents:** [universal entry](docs/AGENT_START.md), then the live controller and
  [Master task list](docs/THE_MASTER_LIST.md). Follow the repository
  [operating instructions](AGENTS.md) and your actual task claim.
- **Project direction and open work:** the [Master task list](docs/THE_MASTER_LIST.md)
  owns task IDs, dependencies and evidence. It evolves as new requirements emerge.
- **Runtime demo:** [native membrane demo and evidence](docs/THE_ENGINE_DEMO.md)
  and [launcher instructions](docs/ENGINE_DEMO_QUICKSTART.md).
- **Verification:** [the method](docs/THE_LAW.md) and
  [current DYAD protocol](docs/THE_DYAD_PROTOCOL.md).

## Current renderer and demo

The renderer is the [C++ Vulkan engine](ChimeraEngine/engine/engine.cpp), as recorded
in the [renderer decision](docs/THE_RENDERER_DECISION.md). Its Windows build uses
C++17, CMake, a C++ toolchain and the Vulkan SDK/shader compiler; see the actual
[CMake configuration](ChimeraEngine/engine/CMakeLists.txt). Python numerical lanes
have their own dependencies; the entire project is not standard-library-only.

The current membrane demo exercises a frozen constant-gamma surface-energy
fixture with initialization, stepping, relaxation, reset and parameter controls.
Optimization iterations are not physical time. The recorded demo does not certify
water containment, general elastic materials, creature walking, or performance.
The [runtime record](docs/THE_ENGINE_DEMO.md) distinguishes executed numerical gates,
visual observations and remaining requirements.

Agents build and launch only from their provisioned slot, using its private build,
runtime and endpoint with the required resource reservations. Never write the
protected engine build directory or reuse another worker's runtime.

## Continuous agent workflow

Develop, test, debug, refactor and review against a declared requirement and
falsifier. Workers push task branches and open PRs targeting `astra/gait-capture`;
slot 1 reviews the queue and handles authorized integration.

A verified, preserved PR handoff frees the execution slot and worker capacity
while the task remains REVIEW. Corrections return to the controller for a new
claim and provisioning at the submitted head. Do not mark a task integrated just
to free capacity. The [handoff contract](docs/THE_REVIEW_SLOT_HANDOFF.md) defines the
client operations and evidence requirements.

When a local codebook or hierarchy has no remaining terms, return to the live
Master/controller workflow: continue an owned milestone or claim eligible READY
work. Do not ask the operator to select the next task merely because that local
hierarchy is complete. A missing qualification, dependency or admission is a
specific condition to report to the lead while other authorized work continues.

## Reference work and evidence

- [Surface-energy CPU reference](tools/surface_energy_reference.py).
- [Elastic physical fixture contract](docs/THE_ELASTIC_PHYSICAL_HANDOFF.md).
- [Creature continuity law](docs/THE_CONTINUITY_LAW.md).
- [Engine shutdown ordering](docs/THE_ENGINE_SHUTDOWN_ORDER.md), including the
  separately tracked Vulkan lifetime defects.

Historical claims remain tied to their source revision, device and evidence.
Operator overrides, model observations and actual numerical/runtime tests are
separate records. A one-image observation is not a movie verification result.

## Historical prototype and license

The previous native/WebGPU quickstart is retained as a
[historical prototype README](docs/archive/README_NATIVE_PROTOTYPE_20260910.md).
It is not the current Vulkan entry point or a current walking certificate.

Chimera is licensed under [GNU AGPL v3](LICENSE).
