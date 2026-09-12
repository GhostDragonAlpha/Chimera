# CHIMERA — the membrane game

**A world built from membranes — cosmic down to molecular — where the physics cannot lie.**

Chimera is a real-time physics teaching game built on one idea: every
material's outer surface — every triangle — carries real physical
properties. Bones are membranes. Joints are membranes. Water, cloth,
terrain, heat: membranes. Compose them and you get a creature that cannot
lie about its own body, in a world built the same way. **Minecraft's
accessibility, Star Citizen's scope, Space Engineers' material depth —
and behind it, a real physics engine that never fakes a number.**

[docs/THE_GAME.md](docs/THE_GAME.md) is the constitution: the vision, the
build order, and the laws this project runs under.

## What's running today

- **The creature** — a 28-joint rigged body you can pose, march, and
  pour water on; every on-screen readout tracks the real simulation
  (blind-judged: independent reviewers who don't know what they're
  looking at confirm what the body does).
- **The engine** — a C++ Vulkan renderer + physics service speaking ~45
  HTTP routes (membrane/strain, water, gait, frost, stride). Frozen as a
  service; extended only by named, reviewed exceptions.
- **The brain** — all product logic is Python driving the engine over
  its HTTP contract: scripted takes, choreography, and the HTTP viewer
  with live view, byte-identical snapshots, and on-demand movies.
- **The fleet** — AI agents build every feature through preregistered
  falsifiable experiments, independent adversarial review, and blind
  visual judges. Nothing merges unaudited. Every claim traces to a
  picture.

## Run it

```bash
# engine (Windows, VS Build Tools + Vulkan SDK)
cmake -B .tmp/engine_build -S ChimeraEngine
cmake --build .tmp/engine_build --config Release
.tmp/engine_build/Release/chimera_engine.exe 8080

# viewer (Python 3.10+, stdlib only)
python -m tools.product_viewer
# → open the printed URL: live view, frame gallery, camera presets
```

## The laws (short form)

1. One feature at a time; a feature is a **visually provable concept**.
2. Passing the human and the blind judge = **frozen**; polish comes later.
3. Proofs wait for visuals — never gold-plate what the eye hasn't judged.
4. The C++ engine is a frozen service; Python does everything else.
5. **All invisible elements shall be seen when put in motion** — and seen
   no more once proven (toggleable: making the invisible visible IS the
   lesson).

Full laws, protocol, and the feature inventory: [docs/THE_GAME.md](docs/THE_GAME.md)

## Repository map

| Path | What it is |
|---|---|
| `docs/THE_GAME.md` | the product constitution |
| `ChimeraEngine/engine/` | the frozen Vulkan+physics service |
| `tools/product_viewer/` | the Python viewer (live view, snapshots, movies) |
| `tools/product_features*` | product feature drivers (walk, water, …) |
| `tools/agent_fleet/` | the fleet: controller, gates, catalogue |
| `docs/evidence/agent_fleet/` | every feature's proof, verbatim |
| `docs/roadmap/holodeck_tasks.json` | the 240-card physics curriculum |
| `docs/THE_AGENT_FLEET.md` | fleet operating model (agents start here) |

## For contributors and agents

Agents: [AGENT_START.md](docs/AGENT_START.md) → live controller →
[Master task list](docs/THE_MASTER_LIST.md); follow [AGENTS.md](AGENTS.md).
The method: [docs/THE_LAW.md](docs/THE_LAW.md); the dyad:
[docs/THE_DYAD_PROTOCOL.md](docs/THE_DYAD_PROTOCOL.md); the fleet:
[docs/THE_AGENT_FLEET.md](docs/THE_AGENT_FLEET.md).

## Status

Tier 0 (the body) frozen and proven; Tier 1 (locomotion — the creature
learns to walk) in flight; 23 features queued, one at a time, ~1 visible
feature per day. Multiplayer is native: the engine is already a server.

License: [LICENSE](LICENSE). Built in the open, one verified membrane at
a time.
