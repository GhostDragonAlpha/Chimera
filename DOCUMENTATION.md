# DOCUMENTATION.md — the map

The repo holds ~100 markdown files accumulated over months of development.
Most are session history. **This is the canon** — the short list that tells
you everything, in the order to read it. Everything not listed here is
archive: kept for provenance, not required reading.

## Read in this order

1. **[README.md](README.md)** — install, build, run, test. Start here.
2. **[docs/THE_LAW.md](docs/THE_LAW.md)** — the method's constitution:
   Rule 0 (every membrane is a theory: statement + prediction + falsifier
   *before* you build), Rule 1 (derive, don't sweep), and the rule index.
3. **[docs/THE_WORKFLOW.md](docs/THE_WORKFLOW.md)** — the daily loop:
   ORIENT → NEXT → PROVE → CHECK → COMMIT.
4. **[ChimeraEngine/docs/HOW_TO_MAKE_A_THING.md](ChimeraEngine/docs/HOW_TO_MAKE_A_THING.md)**
   — the construction pipeline, with the teddy bear as the end-to-end worked
   example. If you want to build something, this is the doc.
5. **[ChimeraEngine/engine/SPIACE_RPG_PLAN.md](ChimeraEngine/engine/SPIACE_RPG_PLAN.md)**
   — the phase ledger: every phase ever shipped, with its measured falsifier
   results. The project's memory of what is proven.
6. **[ChimeraEngine/AGENT_PROTOCOL.md](ChimeraEngine/AGENT_PROTOCOL.md)** —
   the session contract for AI implementation agents (if you use one):
   standing rules, key paths, test scoping, the task template.

## By topic

| Topic | Doc |
|---|---|
| The method's rules (27, with enforcers) | [Chimera/docs/EXPERIMENTAL_METHOD.md](Chimera/docs/EXPERIMENTAL_METHOD.md) |
| The engine model (ports → primitives → programs → parser → runtime) | [docs/THE_COMPILER.md](docs/THE_COMPILER.md) |
| The engine's pieces | [docs/THE_PIECES.md](docs/THE_PIECES.md) |
| The MCP proof engine | [ChimeraEngine/MCP_ENGINE.md](ChimeraEngine/MCP_ENGINE.md) |
| Agent onboarding (the dyad: physics vs human) | [ChimeraEngine/ONBOARDING.md](ChimeraEngine/ONBOARDING.md) |
| The splat renderer (targets, budgets) | [ChimeraEngine/RENDERER_V2.md](ChimeraEngine/RENDERER_V2.md) |
| The kernel DSL (adding a field to the tree) | `ChimeraEngine/engine/kernel_dsl.py` (self-documenting header) |
| The native core (CA + physics + rig + learner) | `ChimeraEngine/native/ca_core.cpp` (documented headers per layer) |
| Relay / viewer plumbing | `ChimeraEngine/native/relay.py` · `native/viewer.cpp` (headers) |
| Voxelizer / shape trainer | `ChimeraEngine/native/voxelize_teddy.py` · `shape_train.py` (headers) |
| Sound | [ChimeraEngine/SOUND_DESIGN.md](ChimeraEngine/SOUND_DESIGN.md) |

## Conventions every doc follows

- **A doc points; it does not duplicate.** Facts live in exactly one place;
  everywhere else links. (Three copies of a rule drift; a pointer cannot.)
- **Numbers in docs are measured.** If a doc states a number, the run that
  produced it is named next to it.
- **Docs are append-only within a phase** (AGENT_PROTOCOL rule 3): new
  findings append new sections; history is not rewritten.
