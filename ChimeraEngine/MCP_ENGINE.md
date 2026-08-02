# The Chimera Engine (MCP) — the workflow as forcing tooling

<!-- CHIMERA-LAW -->
> **RULE 0 — EVERY MEMBRANE IS A THEORY. STATE IT BEFORE YOU BUILD IT.** Three parts, all three
> required: a **STATEMENT** someone could disagree with · a **PREDICTION** you have not measured
> yet · a **FALSIFIER** named *before* the run. **A description survives any result; a theory can
> lose.** No falsifier, no build.
>
> **RULE 1 — DERIVE IT BEFORE YOU TRAIN IT.** A parameter sweep is an admission the derivation was
> not done. Before any run, any sweep, any "let's try N variants": trace the variables and show the
> equations close. If you are choosing a number, you broke the chain and substituted taste for a
> law. Ask what QUESTION each variant answers — if the answer is "which number is best", STOP.
>
> **[docs/THE_LAW.md](../docs/THE_LAW.md)** · the method: `docs/THE_WORKFLOW.md` §0
> · 25 rules: `Chimera/docs/EXPERIMENTAL_METHOD.md` · gate: `python tools/training_gate.py`
<!-- CHIMERA-LAW -->

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
| `human_messenger.py` | **the HUMAN side of the dyad** — a vision LLM reads the render (a TERM), cross-referenced to the physics number (0→1 alignment); no-model FAIL + CAPCOM summon + operator override |
| `appearance.py` · `convergence.py` | PLACEHOLDER matplotlib projectors + a self-measured pixel convergence (a **monad**) — being replaced by the splat-movie render (`ParticleEngine`) + the human dyad |
| `gallery.py` | the shared HTTP view (127.0.0.1) so the physics (agent) and the human (operator + vision model) see the same render |
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
(the splat render + the human DYAD: a vision reading that aligns with the physics) · `S5 WHY-TERMINAL`
(PHYSICS or THE HUMAN). **`prove` refuses until all six pass**, and names the first that fails.

**The dyadAnalysis (the proof model — CORRECTED 2026-07-25).** A proof is a **dyad**: two DIFFERENT
kinds of output, from two independent systems, that must AGREE.
- **PHYSICS (the agent) → a NUMBER** — from the law (the star's blackbody temperature; a world's
  ocean/land fractions). This is *your* side; rendering is physics, so the render is yours too.
- **HUMAN (the operator + LM Studio's vision model) → a TERM** — a separate vision model LOOKS at the
  render, BLIND to the number, and says what it sees; a cross-reference scores their ALIGNMENT 0→1
  (`ChimeraEngine/human_messenger.py`).

The earlier `convergence.py` (predict a feature from the law, MEASURE the same feature back out of the
pixels, compare) is **NOT** this dyad — it is physics measuring its OWN pixels, a **monad**. The tell:
run it in two places and it returns the byte-identical number, because it is one system twice.
Identical outputs are the signature of a false dyad. The real second messenger is a MIND (the vision
model + the operator) producing a TERM, not a second machine producing the same number.

Hard rules (operator): no vision model = **FAIL** (the operator is summoned via CAPCOM); the human
disagreeing means the **physics is wrong — start over**; only the operator's own analysis overrides a
dark eye. And the render the human judges is the **Gaussian-splat engine** movie (`ParticleEngine`,
beginning→end frames as a timeline slice unfolds), NOT a matplotlib diagram — those were placeholders.

## Honest scope (V1 — what forces now, what's next)

**Forces now:** `prove` cannot be faked — the engine owns "proven" at the state layer; real
saturation; the hierarchy advances itself. (The appearance gate currently runs the self-measured
`convergence.py` **monad** — see "still to build" #1; the real human dyad is built but not yet wired
as the gate.)

**Still to build:**
1. **Wire the human dyad into `render`/`prove`.** `human_messenger.py` (vision proxy + cross-reference
   + summon + override) is BUILT and runs, but `prove` still gates on the self-measured `convergence.py`
   monad. The gate must become: the render's human ALIGNMENT ≥ threshold.
2. **Rewire the appearance to the splat MOVIE.** Replace the matplotlib `appearance.py` projectors with
   the Gaussian-splat engine (`ParticleEngine`) rendering each term as a beginning→end movie — the
   mandatory visual test.
3. The **pure form** — run the agent with *only* these tools (Bash/Write removed), so choices genuinely
   *are* the tool list.
4. **Auto-fire** — a pre-commit hook that refuses a "done" claim which didn't go through the engine.
5. A `PHYSICS` terminal that requires a **measurement record**, not just a label.
6. **The story as a filesystem** (next phase) — the term hierarchy becomes a real directory tree
   under `story/` (folder = term, **path = serial**, proof-files inside), replacing `engine_state.json`
   + the DNA graph. The filesystem hierarchy IS the term hierarchy IS the story, readable top-to-bottom
   by a human *and* an AI, no query engine. Build → prove → migrate → retire the graph (never rip out
   the load-bearing thing first).

## The method it enforces

`docs/THE_WORKFLOW.md` (the one sequence) · `THE_FORMULA.md` (S0–S7) · `THE_STORY.md` (the seed) ·
`THE_LINE.md` (program/train/decide). The engine is those documents made un-skippable.
Agent onboarding: `ChimeraEngine/ONBOARDING.md`.
