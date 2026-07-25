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

## Architecture

| File | Role |
|---|---|
| `engine_state.py` | the owned state + the gates — the source of truth (`Engine` class) |
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
| `render(term, path)` | record the REAL rendered visual — refuses a file that doesn't exist. |
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
(measured — over the hump) · `S3 CLASSIFY` (every variable → a terminal) · `VISUAL` (a real on-disk
image) · `S5 WHY-TERMINAL` (PHYSICS or THE HUMAN). **`prove` refuses until all six pass**, and names
the first that fails.

## Honest scope (V1 — what forces now, what's next)

**Forces now:** `prove` cannot be faked — the engine owns "proven" at the state layer; real
saturation; a real on-disk visual; the hierarchy advances itself.

**Still to build:**
1. `render` should **produce** the image via `renderers/gpu_rasterizer.py`, not just record a path.
2. The **pure form** — run the working agent with *only* these tools (Bash/Write removed), so choices
   genuinely *are* the tool list.
3. **Auto-fire** — a pre-commit hook that refuses a "done" claim which didn't go through the engine.
4. A `PHYSICS` terminal that requires a **measurement record**, not just a label.

## The method it enforces

`Chimera/docs/THE_WORKFLOW.md` (the map) · `THE_FORMULA.md` (S0–S7) · `THE_STORY.md` (the seed) ·
`THE_LINE.md` (program/train/decide). The engine is those documents made un-skippable.
Agent onboarding: `ChimeraEngine/ONBOARDING.md`.
