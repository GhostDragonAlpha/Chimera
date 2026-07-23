# archive/unreal-era — RETIRED 2026-07-23

> **Nothing in this folder is current. Do not follow it as instructions.**
> Preserved for history and for the occasional genuinely reusable technique.
> If anything here contradicts the root `CLAUDE.md`, the root file wins.

## What this was

A **DSL-driven Unreal Engine 5 game-generation orchestrator**: a formal spec went in, and
a seven-stage pipeline with hard gates emitted compilable UE5 C++ and assets. Around it
grew a large apparatus — a DNA knowledge graph, a task board with resource-conflict-aware
claims, an agent gauntlet, a feature curriculum, an AI playtester driving Play-In-Editor
beat scripts, circadian dream loops, and roughly a dozen enforcement gates.

It is retired because the project's goal changed. The current work is a **space game fed
by a 3D-scan → object-genome pipeline** (see the root `README.md`), which shares none of
this machinery.

## Why it is archived rather than deleted

Two reasons. First, several hard-won findings in here are about *Unreal and MCP*, not
about the retired architecture, and could matter again:

- `chimera-docs/MCP_PATHWAYS.md` — proven MCP pathways and a long list of traps found by
  hitting them, e.g. `delete_actor` being a silent no-op, `spawn_actor` during PIE landing
  in the persistent editor level instead of the PIE world, and `set_collision` evaporating
  because PIE duplicates serialised state.
- `chimera-docs/THE_MATTER_MODEL.md`, `TERRARIUM_DESIGN.md`, `THE_EVOLUTION_ENGINE.md` —
  the trained-content work (differential adhesion, L-system growth, GPU-batched evolution
  against machine-checkable objectives). The substrate ideas outlived the engine.

Second, the **methodology** survived the architecture. Several principles now in
`docs/EXPERIMENTAL_METHOD.md` were learned here — score from N randomised starts and keep
the worst, an exploit is the optimiser auditing your spec, a compile is not proof, and a
field can lie where an edge cannot.

## Layout

| Folder | Contents |
|---|---|
| `root-docs/` | The old top-level docs — onboarding, runbook, workflow, deployment, the session handoff log (`task_progress.md`), the previous `README.md` |
| `chimera-docs/` | 78 files from `Chimera/docs/` — MCP pathways, training and generation protocols, gauntlet, heuristics, verdicts, design docs |
| `docs/` | The old root `docs/` — DNA graph snapshot, handoffs, Steam page, educational material, research |

The **code** (`Chimera/`, including `core/` and the UE5 project) has not been moved — only
the documentation. It is inert: nothing in the current pipeline imports it.

## One thing worth carrying forward

The retired manual opened with a line that stayed honest to the end, and it applies just
as much to the new pipeline:

> **NO REFERENCE, NO VERDICT.** The system never decides what is good on its own. A human —
> or an objective a human authored — supplies the reference; the machine attunes to it and
> reports how close it got.
