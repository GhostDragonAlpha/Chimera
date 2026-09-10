# GPU membrane demo controller

## Preregistration

**Statement:** an operator can launch an isolated visible Chimera engine, load
the frozen B2 fixture, and control the accepted state from a persistent
companion window.

**Prediction:** after initialization the companion reports B2 centre `z=0.125`
and gamma `1`; Run advances one accepted request at a time, while Pause stops
future requests and Reset restores the frozen initial state.

**Falsifier:** any launch that attaches to an unowned process, any upload that
does not receive an applied response, a UI-thread network call, or a control
sequence that sends a step after Pause has taken effect.

## Launch

Build the native engine first. Then run the controller with an explicit
executable and unused port:

```powershell
python tools/engine_demo.py --exe E:\path\to\chimera_engine.exe --port 8106
```

The controller creates a sibling `demo_runtime\` directory beside the
executable, launches with `--no-restore`, and records ownership in
`demo_runtime\manifest.json`. It keeps the native engine window open until the
companion window is closed. Only the `Popen` it created is terminated.

To connect the companion to an already-running, explicitly supplied runtime,
use its manifest:

```powershell
python tools/engine_demo.py --attach E:\path\to\demo_runtime\manifest.json
```

Attach mode never terminates the process. The manifest must name the loopback
base URL and a live runtime; a stale or malformed manifest is refused.

The buttons initialize frozen B2, run one step per background request, pause
future steps, reset, change gamma, and refresh status. The rendered membrane is
visible in the native engine window. The status panel displays iteration,
energy, centre height, terminal state, and the last control response.

The controller uses `tools/membrane_demo_client.py::load_b2` and
`md01_packet`; it does not define geometry, gamma, lift, or optimizer constants.
The engine API is `POST /membrane_demo_bin`, `GET /membrane_demo`, and
`POST /membrane_demo` with `step`, `run` (unused by the scheduler), `pause`,
`reset`, and `gamma` operations.
