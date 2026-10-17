# Experimental Python control layer

This prototype makes matter experiments and construction tools scriptable around the existing C++/Vulkan renderer. Python issues small intent/configuration messages. Native code retains geometry, material admission, physical state, stepping, contact, independent simulation clocks and drawing. It does not animate substitute vertices or perform a mesh upload on every frame.

## Run a private building world

From the current D:\Chimera-Maintenance\PythonChimera checkout in PowerShell:

```powershell
& "D:\Chimera-Maintenance\Runtime\local-ai\Strata\.venv\Scripts\python.exe" -B -m tools.python_control.demo
```

This launches a private native engine on port 8813, creates the existing granite/steel/timber stack and a reusable fourth timber block, and verifies that native rendering/picking identifies that block. Open the printed `/frame` URL for its native image. `--visible` opens the native window. Ctrl+C stops only the engine this command owns. `--duration 2` runs a bounded smoke test. The launcher refuses occupied ports and keeps runtime files under a new `.tmp/python-control-demo` directory.

The Python layer can attach to an explicitly chosen existing engine instead:

```python
from tools.python_control import EngineControl
from tools.construction_packet.b2_scene_gen import make_stack, box_document

with EngineControl("http://127.0.0.1:8813") as world:
    world.assembly.admit(make_stack())
    world.assembly.pause()
    world.assembly.place(box_document("timber_block", .34, .40, -.01, .03, .12, .18, 600, .3))
    world.assembly.patch(id="timber_block", mu=.4)
    world.assembly.pause(False)
    print(world.assembly.clock())
```

Only run mutating examples in a world you intend to change. The client has no default endpoint. Assembly supports native part admission, placement, removal, material patching, welds, loads, gravity/support, render LOD, state hashes and clock telemetry. Native transaction refusals stop the script, including refusals returned with HTTP 200. Mutations are not retried after a timeout because they may already have applied.

## Membrane scenarios and physics adapters

```powershell
& "D:\Chimera-Maintenance\Runtime\local-ai\Strata\.venv\Scripts\python.exe" -B -m tools.python_control --base http://127.0.0.1:8813 --scenario tools/python_control/membrane_experiment.json --output .tmp/membrane-experiment.json --capture .tmp/membrane-experiment.png
```

Use this scenario in a fresh/private membrane world; it loads the project's pinned B2 MD01 fixture once, changes tension and requests native relaxation. `world.membrane.step(12)` uses native `run`, since native `step` performs exactly one step even if supplied a larger count. Batching defers intermediate rendered feedback; it is appropriate for offline experiments and tool transactions, not a promise of faster interactive animation.

`world.matter.configure()` wraps legacy M1 relaxation; `readback()` requires its native JNT2 prerequisites. `world.physics.intent()` and `surface()` wrap graph-derived coupled-arm and science-surface scenes, which must already be loaded. Those alternate-scene adapters are present but not independently qualified by this prototype's B2 tests.

## Measurements

The full comparison is in `.tmp/python-control-prototype/run-04/receipt.json`; prediction/falsifiers were saved beforehand in `preregistration.json`. Six paired rounds produced identical native accepted-geometry hashes, iteration counts, energy, force and centre positions. The prototype also placed, edited and removed native parts, preserved state on a duplicate-part refusal, and observed the independent physics clock advancing without Python stepping.

| Measurement | Existing direct client | Python layer |
|---|---:|---:|
| Read-only request median (200 samples each) | 0.847 ms | 0.813 ms |
| 12 individually requested native steps | 118.76 ms | 128.52 ms |
| 12 steps in one native batch | — | 43.05 ms |
| Native frame-work median, same paused assembly and polling load | 0.5345 ms | 0.5335 ms |

Batching reduced orchestration time by 2.76x in the expanded run (5.38x in an earlier smaller run). Individual Python steps were about 8% slower in this run; do not hide that result. The frame difference is within noise, not an FPS improvement. Native frame work excludes frame pacing/sleep and is not a GPU timestamp measurement. This is a seven-vertex membrane and three/four-part construction prototype; it does not qualify a whole creature or large asymmetric membrane stacks. The existing renderer/model/download were not stopped, so these are shared-system measurements.

The initial transport experiment failed the overhead target, and a subsequent shorter run showed timing variability. Failed receipts in run-01/run-03 are preserved alongside the expanded result; matching the existing urllib request path and headers avoided changing native server behavior. No C++, shaders, Qwen settings or Kimi transfer settings were modified.

## Reproduce checks

```powershell
& "D:\Chimera-Maintenance\Runtime\local-ai\Strata\.venv\Scripts\python.exe" -B -m unittest tools.python_control.test_client -v
& "D:\Chimera-Maintenance\Runtime\local-ai\Strata\.venv\Scripts\python.exe" -B -m tools.python_control.benchmark --launch .tmp/body-engine/Release/chimera_engine.exe --output .tmp/python-control-new-run
```

Output directories must be new. Benchmark launch uses a copied executable and shaders with `--no-restore` and a private port, and always stops its own process. Six control-contract tests and 25 live checks passed in the expanded run. Repository base was a2155794aa70d290136126e25b582f2b0fb348f2; source/native/fixture identities belong with each receipt. Graph bootstrap check passed. No provisioned controller admission or publication is claimed. This README is experimental usage material, not a replacement for the project graph.

Development value: one API for reproducible material/assembly experiments, quick parameter sweeps, scripted regression scenarios and later editor tools. It preserves the existing native simulation/rendering boundary. Large-scene qualification and an interactive building UI remain separate work.
