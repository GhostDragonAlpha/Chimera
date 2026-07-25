# The Chimera Engine (MCP) — the workflow as forcing tooling

> **The AI's Unreal.** Built 2026-07-25. The Chimera *development* engine: an environment the agent
> works THROUGH, whose structure IS the PROVE workflow. Where Unreal keeps a human in the
> game-making workflow (the editor only affords valid moves), this keeps the AI in the method.
>
> This documents the **MCP workflow engine** (`engine_state.py` + `mcp_server.py`). The older
> `README.md` in this folder documents the earlier splat/particle rendering pipeline — a different
> layer, not retired, just separate.

## Why it exists

The workflow lived in documents, and — by this studio's own first law
(`Chimera/docs/THE_COMPLETE_CHIMERA_DEVELOPMENT_CYCLE.md`) — *"the reasoning trace is the code;
prose rots, only mechanism is alive."* Across one session the agent broke every rule that was
prose and obeyed the one rule that was a command (the saturation pre-commit lint — because git
ran it, not because the agent chose to). So the workflow is rebuilt as a **command surface**: an
MCP server whose tools are the only sanctioned way to move a term toward "proven."

## The hinge — the engine owns "proven"

"`term` is proven" is a fact only `engine_state.py` writes, and only after every gate passes. Raw
tools can touch files, but a term cannot **count** as proven without `prove()`. That is what forces
the workflow instead of asking for it — the same way an actor exists in Unreal only if the bridge
spawned it, never because a file claims so.

## dyadAnalysis — "proven" means the DYAD crossed the boundary

Owning "proven" is not enough; the proof must be made in the RIGHT system. A valid proof is a
**dyadAnalysis** — an analysis performed by a **dyad** (a pair interacting as a unit; Greek *dyás*
"two" + *-ad*, the unit-of-N suffix as in *monad*/*triad*), never by a monad measuring itself. Here
the dyad's two halves are two systems:

- **your own system** — a driver/script that imports the `Engine` class and calls `.prove()`
  directly. You control the whole flow. This is *measuring the engine with a copy of yourself.*
- **the engine system** — the MCP tool surface (`mcp__chimera-engine__*`), an INDEPENDENT system you
  reach across a boundary (a separate server process, invoked through the sanctioned interface).

A term counts as proven only when the **dyadAnalysis is complete** — it has crossed the boundary,
been proven through the engine system, not merely in your own. This is the two-messenger law at the
process scale: the prover and the engine are the dyad, and *you cannot measure a system with
itself.* `prove(via='mcp')` (the MCP tool) completes the dyadAnalysis; `prove(via='api')` (a driver)
is a monad — it returns "PROVEN (your own system only)" and `orient` marks the term `[~]`, not
`[x]`. Proving via a driver and declaring it done is the exact failure this engine exists to
prevent, wearing a lab coat.

## Architecture

| File | Role |
|---|---|
| `engine_state.py` | the owned state + the gates — the source of truth (`Engine` class) |
| `appearance.py` | the APPEARANCE MESSENGER — projects each term's physics into a light-view |
| `convergence.py` | the MEASURED CONVERGENCE — predicts a feature from the physics law, measures it from the rendered pixels, checks they agree |
| `mcp_server.py` | 8 bounded FastMCP tools over that state |
| `.mcp.json` (repo root) | registers the server for Claude Code |
| `engine_state.json` | the runtime ledger: hierarchy · per-term records · codebook (gitignored) |

Backed by `Chimera/core/saturation.py` — the real S2b saturation gate (Chao2 completeness + dry tail).

## Activation

Registered in `.mcp.json`; MCP servers load at **session start**. Reload the session, approve
`chimera-engine` when Claude Code prompts, and the `mcp__chimera-engine__*` tools appear in the
toolset. One-time — the "install the bridge" step.

## The tools (the whole surface)

| Tool | Does |
|---|---|
| `orient` | the viewport: current term + gate progress, the hierarchy, the codebook, the ONE next move. **Call first, always.** |
| `next` | advance to the next term, setting-first from the seed. You don't pick — the hierarchy does. |
| `frame(term, claim)` | S0: state the term as exactly one atomic claim. |
| `question(term, question, variables)` | S1: submit a question + the variables it DISCOVERED. Repeat until the engine reports `saturated`. |
| `classify(term, {var: PHYSICS\|THE HUMAN})` | S3: send each variable to its terminal. |
| `render(term)` | generate the **APPEARANCE MESSENGER** and MEASURE its convergence — project the physics into a light-view (`appearance.py`), then check a feature read back from the pixels against what the physics predicts (`convergence.py`); refused with no projector, DIVERGENT if the look leaves the physics. |
| `prove(term)` | **the one door.** Runs every gate; writes the codebook ONLY if all pass; else refuses, naming the blocker. |
| `decide(term, ruling)` | THE HUMAN terminal (taste/meaning) — the one terminal an LLM can never stand in for. |

## The loop

```
orient → next → frame → question × N (until saturated) → classify → render → prove
   ▲                                                                            │
   └────────────────────── prove advances the hierarchy, setting-first ─────────┘
```

## The gates `prove()` enforces (the PROVE formula)

`S0 FRAME` (atomic claim) · `S2a PROVENANCE` (variables born of questions) · `S2b SATURATION`
(measured — over the hump) · `S3 CLASSIFY` (every variable → a terminal) · `APPEARANCE MESSENGER`
(a projection of the physics that MEASURABLY CONVERGES with it) · `S5 WHY-TERMINAL` (PHYSICS or THE
HUMAN). **`prove` refuses until all six pass**, and names the first that fails.

**Two messengers (the proof model).** The gates are two independent readings of one membrane: the
**physics messenger** — the measured interior (frame · provenance · saturation · classify · why) —
and the **appearance messenger** — the emitted surface (`render` projects it from the physics via
`appearance.py`). Gravity and light are one thing measured by two systems; a term is proven when
both agree. The engine *generates* the appearance so it can't be a faked or unrelated picture:
appearance derives from the matter model, never beside it (no aesthetic passes). **The convergence
is MEASURED** (`convergence.py`): the engine reads a feature back out of the rendered pixels — the
star's glow chromaticity, the system's bright centroid, the garden's vegetation cover — and checks
it against what the physics law predicts (Planck's law → the Sun's true color; the barycenter;
chlorophyll). A star recolored blue leaves the Planck locus and is REFUSED. The residual, not a
vibe, decides — and you fix the projector, never the tolerance.

## Honest scope (V1 — what forces now, what's next)

**Forces now:** `prove` cannot be faked — the engine owns "proven" at the state layer; real
saturation; an appearance the engine projects from the physics AND measurably converges with it
(residual < tolerance, or DIVERGENT); the hierarchy advances itself.

**Still to build:**
1. **A projector + convergence law for every term.** Only `theStar`, `theSolarSystem`, `theGarden`,
   `aPlanet` have a light-view today (`appearance.py`/`convergence.py`); a term with none cannot be
   proven by two messengers until one is built. Each new term owes its projected, converging surface.
2. The **pure form** — run the working agent with *only* these tools (Bash/Write removed), so choices
   genuinely *are* the tool list.
3. **Auto-fire** — a pre-commit hook that refuses a "done" claim which didn't go through the engine.
4. A `PHYSICS` terminal that requires a **measurement record**, not just a label.
5. **The story as a filesystem** (next phase) — the term hierarchy becomes a real directory tree
   under `story/` (folder = term, **path = serial**, proof-files inside), replacing `engine_state.json`
   + the DNA graph. The filesystem hierarchy IS the term hierarchy IS the story, readable top-to-bottom
   by a human *and* an AI, no query engine. Build → prove → migrate → retire the graph (never rip out
   the load-bearing thing first).

## The method it enforces

`Chimera/docs/THE_WORKFLOW.md` (the map) · `THE_FORMULA.md` (S0–S7) · `THE_STORY.md` (the seed) ·
`THE_LINE.md` (program/train/decide). The engine is those documents made un-skippable.
Agent onboarding: `ChimeraEngine/ONBOARDING.md`.
