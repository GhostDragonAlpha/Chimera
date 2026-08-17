# THE RENDERER — a decision membrane

> **RULE 0 — every membrane is a theory.** This is a *decision* membrane: it is stated as
> exactly one claim (STATEMENT), a prediction not yet measured (PREDICTION), and the
> measurement that would kill it (FALSIFIER). No falsifier, no build. Settle this before
> proving the playable verbs (`thePlayer`, `theLoop`, `theDig`, `theGrow` …) — they hang on it.

## STATEMENT

The C++ Vulkan engine (`ChimeraEngine/engine/engine.cpp` — N-body gravity, point-splat
renderer, camera, `/frame` HTTP server) is the **emission target** for proven membranes.
`ChimeraEngine/splat_appearance.py` (the Python Gaussian-splat "movie") is the renderer
**only until** the C++ engine can stream a membrane's scene from `engine_state.json` and
serve it through its existing `/frame` endpoint.

## PREDICTION (not yet measured)

Wiring the C++ engine to render `engine_state` membranes — world-streaming the proven
hierarchy + pointing the dyad at its `/frame` — yields a `dyadAnalysis` that passes at
**equal or lower cost** than `splat_appearance`, and **unlocks the playable verbs**
(`thePlayer`/`theLoop`/`theDig`/`theGrow`) that a static splat movie cannot show.

## FALSIFIER

If, after wiring, the C++ engine **cannot render a proven membrane's scene from
`engine_state`** within a small number of sessions, **OR** its `/frame` dyad fails to reach
alignment ≥ 0.6 for membranes `splat_appearance` already passed, then the C++ engine is
**NOT** the renderer: keep `splat_appearance` and treat `engine.cpp` as a separate
experiment, not the method's emission target.

### Counter-hypothesis (B): the C++ engine is a separate experiment

FALSIFIER for B: if a playable verb (`thePlayer`/`theLoop`) **cannot be shown at all**
through `splat_appearance`, then B is false and A is forced — the method needs the C++
engine regardless of cost.

## DECISION TO RECORD

Pick A or B and write the `forbids`/measurement that enforces it as a NIGHT rule. Until
this membrane is framed-and-proven, the two render paths drift and the verbs cannot be
proven through the loop.
