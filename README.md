# Chimera

**A physics-first engine where structure is grown by cellular automata and
every field (gravity, light, charge, heat) is one Barnes-Hut tree traversal.**
Everything is derived, falsified, and measured — no parameter sweeps, no
claims without a number.

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

## Make your own thing

**[ChimeraEngine/docs/HOW_TO_MAKE_A_THING.md](ChimeraEngine/docs/HOW_TO_MAKE_A_THING.md)**
— the full construction method, step by step, with the teddy as the worked
example: reference image (ambient light only) → TRELLIS 3D → voxelize →
shape-train → genome table (data, not code) → run → falsify.

## Layout

| Path | What it is |
|---|---|
| `ChimeraEngine/` | the workflow engine + the native CA core (`native/`) + the browser splat engine (`engine/`) |
| `ChimeraEngine/native/ca_core.cpp` | the C++17 core: CA growth, gravity kernel, rig/IK, gait, learner — genomes are data, this is the reader |
| `ChimeraEngine/engine/` | WebGPU Barnes-Hut + splat renderer, kernel DSL, tests/oracles |
| `docs/` | the method: THE_LAW, THE_WORKFLOW, THE_COMPILER |
| `ChimeraEngine/engine/SPIACE_RPG_PLAN.md` | the phase ledger — every phase with its measured falsifier results |

## License

**GNU AGPL v3** ([LICENSE](LICENSE)). This project is free — forever, for
everyone. If you modify it and let others interact with it over a network,
you must publish your source. Nobody takes this private.
