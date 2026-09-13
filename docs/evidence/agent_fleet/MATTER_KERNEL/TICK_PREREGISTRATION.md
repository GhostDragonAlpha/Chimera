# THE MEMBRANE TICK — preregistration (Appliance 1)

Rule 0: statement, derivation, predictions, falsifier — BEFORE the C++
surgery. The engine is the frozen service; this is a named appliance:
"membrane tick". Rebuild happens in a separate build dir; the swap lands
only after the new binary serves.

## STATEMENT

Membrane triangles are CELLS. The engine ticks them once per frame:
per-cell state (load, damage) updates from certified local rules, driven
only by posted intents (force in newtons, never defaulted). Cells live
in the engine (GPU-resident vertex data, engine-side state) — Python
never per-frames. Cell state is VISIBLE: load and damage tint the cell
color in the render (the law: invisible becomes visible in motion).

## DERIVATION (from measured geometry + sourced constants)

- Cells: the feet scene = 60 triangles (2 feet x 30). Per foot:
  20 cells over a 0.39 x 0.78 sole face -> cell area
  A_c = 0.3024 / 20 = 0.0152 m^2.
- Material: mat.skin, yield 15e6 Pa (Yamada 1970, conservative end).
- Cell capacity: C = yield x A_c = 15e6 x 0.0152 = 2.28e5 N.
- Press law (force known): an intent {force_n, foot} spreads F evenly
  over that foot's cells: per-cell load = F / 20. Standing pressures are
  ~1e3 N (safe by 3 orders); the failure threshold for the foot is
  F_fail = 20 x 2.28e5 = 4.56e6 N.
- Tensile distribution (B3): an overloaded cell sheds its excess,
  half to each edge-neighbor, per tick, until stable or failed.
- Damage (B1 spirit): damage += (load - C) / C per tick while
  load > C; damage >= 1 -> the cell FAILS (recolors, stops carrying).
- Visibility: color = skin color blended toward red by
  min(1, load/C), and a failed cell renders dark grey.

## PREDICTIONS (bars; all read through GET /tick_state + /frame)

P1. Idle: tick advances every frame (counter grows) with zero intents;
    total load 0, damage 0, colors unchanged.
P2. Press 1000 N on the left sole: left cells carry total 1000 N
    (sum of per-cell load), right foot 0, damage 0.
P3. Sustain: the same intent held N frames keeps the total at 1000 N
    (no leak, no growth) — steady state.
P4. Overload: a 6e6 N press (per-cell 3.0e5 > 2.28e5) grows damage per
    tick; loaded cells recolor toward red (visible in /frame pixels);
    at damage >= 1 cells fail (dark grey) and stop carrying.
P5. Distribution: an overloaded cell sheds excess to edge-neighbors —
    after ticks settle, no carrying cell exceeds C while neighbors have
    headroom (the web finds the weakest link, computed not scripted).
P6. Intents only: the harness performs ZERO HTTP during the ticking
    window; /tick_state shows ticks advancing — the tick is the
    engine's own heartbeat (the 22 fps law, enforced).
P7. Refusals: intent without force_n -> refused by name; unknown foot
    -> refused; negative force -> refused.

## MUTATION PROBE

- "scripted failure": any damage growth while total posted force is 0
  must be impossible — P1 catches it.
- "phantom load": total cell load must equal the posted intent (sums
  are checked exactly) — a tick that invents or loses force fails.
- "python tick": the harness counts its own HTTP calls (2: enable +
  intent); a tick dependent on polling fails P6.

## FALSIFIER

Any bar fails, OR the tick stalls without Python, OR load is not
conserved in distribution, OR damage appears without overload. On
failure the successor is named: the cell state moved out of the apply
path (find where the frame loop drops it), fix, re-run.

## OPEN (named)

- Scratch between two membranes: needs two membranes pressing — v2
  after the single-foot contact works.
- Drape is a static rule (not a tick term) — excluded from v1.
- GPU compute migration: v1 ticks engine-side C++ per frame (18.9k
  cells is trivial); the compute-shader migration is its own appliance
  once the semantics are proven.
