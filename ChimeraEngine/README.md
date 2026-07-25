# ChimeraEngine

> **What this folder is — read this first.** One name used to mean four things, so "what is
> ChimeraEngine" had no answer. It now means ONE thing: the **MCP workflow engine** — the AI's
> Unreal, the workflow made into tooling. Three other systems live here as **tenants**, each sealed
> in its own folder (its own membrane = its own attributable identity). This README is the index:
> the boundary that tells them apart.

## The identity — the workflow engine (the root files)

The files at the ChimeraEngine **root** ARE the workflow engine. You work THROUGH it; its structure
is the PROVE workflow, and `prove` **owns "proven"** — it refuses to record a term until every gate
passes. A doc can be ignored; an engine that owns "proven" cannot.

| File | Role |
|---|---|
| `mcp_server.py` | the MCP tool surface (8 tools) — the sanctioned way to move a term toward proven |
| `engine_state.py` | the OWNED state + the gates (`Engine` class) — the source of truth |
| `human_messenger.py` | **the HUMAN side of the dyad** — a vision LLM reads the render (a TERM), cross-referenced to the physics number (0→1); no-model FAIL + CAPCOM summon + operator override |
| `gallery.py` | the shared HTTP view (127.0.0.1) so the physics (agent) and the human see the same render |
| `appearance.py` · `convergence.py` | PLACEHOLDER matplotlib + the self-measured pixel convergence (a **monad**, being replaced by the splat movie + the human dyad) |
| `terms_data.py` · `gen_decl.py` · `gen_terms.py` | the declaration pipeline (STORY → terms → `THE_TERMS.md`) |

**The dyadAnalysis — a NUMBER and a TERM.** A term is proven only when its two independent systems
AGREE: the **PHYSICS** (the agent → a NUMBER from the law) and the **HUMAN** (the operator + LM
Studio's vision model → a TERM, from LOOKING at the render), cross-referenced to an alignment. Two
different KINDS of output are what make them independent — identical outputs are a false dyad (one
system twice). The render they judge is the **Gaussian-splat engine movie** (`ParticleEngine`,
beginning→end), not a diagram. `convergence.py` (physics reading its own pixels) was a monad, being
replaced. The agent is the physics and owns rendering; the human (operator + vision) judges taste.

Read next: **`MCP_ENGINE.md`** (how it works) · **`ONBOARDING.md`** (paste-in for a new agent) ·
**`THE_TERMS.md`** (the term list). The method it enforces: `../Chimera/docs/THE_WORKFLOW.md`.
Run `python -m ChimeraEngine` to print the engine's viewport (current term, gates, next move).

## The three tenants (each its own membrane)

Separate systems that share this roof but not the identity. `import ChimeraEngine` does **not** pull
them in — reach each by its path (`ChimeraEngine.rendering.*`, `ChimeraEngine.dialectic.*`,
`ChimeraEngine.vision.*`). Each folder's `__init__.py` states its own identity.

| Folder | System | Relationship to the engine |
|---|---|---|
| `rendering/` | the splat/particle **rendering pipeline** (GaussianSplatCloud · budgeted-cut LOD · GPU rasterizer · quality gates) | the light-view machinery; does NOT own "proven" |
| `dialectic/` | the older particle-engine **dialectical workflow** (council · helm · beats · gates) | the **pre-MCP precursor** to the workflow engine; kept for reference |
| `vision/` | **vision → membrane** labeling (photo patterns → classified membranes; geology downloaders) | feeds the matter library |

## Why the boundary matters (and what's next)

A boundary is what makes a cause — or a name — attributable; that is the studio's membrane
primitive, the same law the workflow proves with. With no boundary, four systems smeared into one
name. Drawing the folders **is** drawing the membrane: each system now has a local frame, an
inside/outside, and an address (its path).

**Next phase:** the STORY itself becomes a directory tree under `story/` — folder = term, **path =
serial**, proof-files inside — so the whole game is readable top-to-bottom by a human *and* an AI,
with no separate graph to query. The filesystem hierarchy IS the term hierarchy IS the story.
