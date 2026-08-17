# Chimera

**A physics-first engine where structure is grown by cellular automata and
every field (gravity, light, charge, heat) is one Barnes-Hut tree traversal.**
Everything is derived, falsified, and measured — no parameter sweeps, no
claims without a number.

## Prerequisites

- **Windows** (the native viewer is Win32; the core itself is portable C++17)
- **Python 3.14+** — relay, oracles, pipeline tools (stdlib only; no pip
  install needed for the native stack)
- **MinGW-w64 g++ 15+** — builds the C++ core and the native viewer
- Optional: a **WebGPU browser** for the HTML engine (`engine/spiace_*.html`)
- Optional: **LM Studio** (or any local VLM) for the vision-judge side of the
  scoring dyad

## Quickstart — watch the teddy bear walk (2 commands)

```
cd ChimeraEngine
python native/relay.py 30 8799 native/genomes/teddystandmuscle.chimera
```

Open http://127.0.0.1:8799/ — press **2** (WALK). The bear walks with a
voxel-muscle gait: legs shorten/lengthen by adding and removing cells, and
every shift of the body is *earned* (gated on ground contact — airborne legs
cycling move the body exactly 0.0 cells, bit-exact, and there is a falsifier
that proves it).

Unified human window: http://127.0.0.1:8799/hub — live viewer + scoreboard
+ proof images in one page.

### Prefer a native window (no browser)

```
cd ChimeraEngine/native
g++ -O2 -std=c++17 -static -static-libgcc -static-libstdc++ viewer.cpp \
    -I viewer3rd -o viewer.exe viewer3rd/wgpu_native.dll \
    -lws2_32 -luser32 -lgdi32 -lcomctl32
./viewer.exe          # auto-starts the relay on :8799 if it isn't running
```

Mouse drag = orbit, wheel = zoom, keys 1/2/3 = wave/walk/rest, Esc = quit.
Static linking is **mandatory** on Windows: the system `libstdc++-6.dll`
ABI-mismatches MinGW g++ 15 and segfaults at `-O2`.

## Build the core

```
cd ChimeraEngine/native
g++ -O2 -std=c++17 -Wall -o ca_core.exe ca_core.cpp     # zero warnings is the bar
```

Genomes are **data** (`native/genomes/*.chimera`, key=value). You never edit
C++ to add a creature — you write a new genome file.

## Test

Fast probe (seconds, no browser — drop law, energy ledger, 400-tick walk,
airwalk falsifier in one shot):

```
cd ChimeraEngine/native
./ca_core.exe 30 genomes/teddystandmuscle.chimera selftest
```

The targeted net (wire oracles recompute the world from the relay log
independently of the page's belief):

```
cd ChimeraEngine/engine
python test_native.py
```

Run only the tests your change touches. The browser-based suites
(`test_phase6.py`) need a WebGPU browser and headed mode; gate them behind
`T_HEADED`-style flags when the machine's browser stack is wedged — pixel
proof without a browser goes through wgpu-py offscreen
(`engine/scratch/_render_t12.py` pattern).

## Make your own thing

**[ChimeraEngine/docs/HOW_TO_MAKE_A_THING.md](ChimeraEngine/docs/HOW_TO_MAKE_A_THING.md)**
— the full construction method, step by step, with the teddy as the worked
example: reference image (ambient light only) → TRELLIS 3D → voxelize →
shape-train → genome table (data, not code) → run → falsify.

## Documentation

**[DOCUMENTATION.md](DOCUMENTATION.md)** — the map of every doc in the repo
and the order to read them.

## License

**GNU AGPL v3** ([LICENSE](LICENSE)). This project is free — forever, for
everyone. If you modify it and let others interact with it over a network,
you must publish your source. Nobody takes this private.
