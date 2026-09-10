# GPU membrane demo controller

## Preregistration

**Statement:** an operator can launch an isolated visible Chimera engine, load
the frozen B2 fixture, and control the accepted state from a persistent
companion window.

**Prediction:** after initialization the companion reports B2 centre `z=0.125`
and gamma `1`; Run advances one accepted request at a time, while Pause stops
future requests and Reset restores the frozen initial state.

**Falsifier:** any launch that targets an occupied port or reused runtime, any
upload that does not receive an applied response, a UI-thread network call, or
a control sequence that sends a step after Pause has taken effect.

## Launch

Build the native engine first. Then run the controller with an explicit
executable and unused port:

```powershell
python tools/engine_demo.py --exe E:\path\to\chimera_engine.exe --port 8106
```

The controller creates a fresh private runtime directory beside the
executable, stages the exact executable and `shaders\` tree, launches with
`--no-restore`, and records ownership in `manifest.json`. It refuses an
occupied port or a reused runtime directory before starting anything. It keeps
the native engine window open until the companion window is closed. Only the
`Popen` it created is terminated; there is no attach mode.

The buttons initialize frozen B2, take one step, run one step per background
request, pause future steps, reset, apply gamma 0/1/2 fixture controls, and
refresh status. The rendered membrane is
visible in the native engine window. The status panel displays iteration,
energy, centre height, terminal state, and the last control response.

Optimization iterations are control steps, not physical time.

The controller uses `tools/membrane_demo_client.py::load_b2` and
`md01_packet`; it does not define geometry, gamma, lift, or optimizer constants.
The engine API is `POST /membrane_demo_bin`, `GET /membrane_demo`, and
`POST /membrane_demo` with `step`, `run` (unused by the scheduler), `pause`,
`reset`, and `gamma` operations.
