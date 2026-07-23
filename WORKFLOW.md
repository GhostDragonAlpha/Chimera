# GAUSSIAN FOUNDRY — AGENT WORKFLOW

> **THE FOUNDRY is the dialectical design engine.** When you need to design a feature from
> scratch — saturate it with questions, run the internal council, debate every angle — this
> is the method. It operates WITHIN the broader operational infrastructure (task board,
> sleepwalker, trainer, automation) described in `CLAUDE.md`. The Foundry designs; the
> Spiral executes, verifies, and trains.
>
> **Relationship**: the helm (`core/helm.py`) reads the seed and decides WHAT to build.
> The Foundry (this file) describes HOW to think through a design. The Spiral
> (`CLAUDE.md` + `task_board`) provides the operational machinery that claims, tunnels,
> witnesses, and collapses the result. The Foundry council is a tool you reach for inside
> a task-board tunnel when the work packet says "design X."
>
> **THE RHYTHM (proven 2026-07-20 — 25+ features observed in one session):**
> The Foundry is not a checklist. It is a continuous question loop:
>
>   1. **Ask** a concrete question about the current state
>   2. **Answer** it with evidence — read code, run beats, query MCP, spawn actors
>   3. **Ask** the next question based on what you learned
>   4. **Repeat** until the human stops you
>
> Never stop at "task done." A task is just one answer — the session ends when the
> human stops you, not when you've checked a box. Record evidence immediately.
> Verify everything with sleepwalker beats. Use the council for design decisions
> you cannot answer from the graph or code alone. The rhythm:
> **ask → answer → ask → answer → ask** until the ultimate goal is reached.

## PHASES

The system has two modes that alternate:

### DESIGN MODE — "What do we need to ask?"

Purpose: Saturate a feature with questions until every angle is covered.

1. RECEIVE DIRECTION — Human gives a goal, problem, or question.
2. QUERY THE GRAPH — Search chronicle + knowledge graph for existing answers.
3. INTERNAL COUNCIL — Run 7 gates: Frame → 10Q → Answer → 10Q → Answer → Saturate → Spec.
4. RECORD — Write all Q&A pairs to the feature JSON in `Chimera/docs/features/`.
5. REPEAT — If META questions say "needs deeper zoom," create sub-features and repeat.

A feature transitions from `questioning` -> `designed` when ALL questions are answered.

### BUILD MODE — "Construct what we know."

Purpose: Take a designed feature and construct it from the graph answers.

1. LOAD FEATURE — Read the designed feature JSON (all questions answered = spec).
2. READ SUB-FEATURES — Load all sub-features for full context.
3. CONSTRUCT IN UE5 — Use `mcp_builder.py` to:
   - Spawn actors (TriggerBox, StaticMesh, VolumetricCloud)
   - Set component properties (density, color, shadow, rotation)
   - Position cameras and lights
   - Apply materials
4. VERIFY — Capture viewport screenshots via MCP to confirm construction.
5. REPORT — Show what was built with screenshot evidence.

Python abstractions are built first, then MCP constructs them in UE5.
The Python layer is DATA. The MCP layer is CONSTRUCTION.

## THE COMPLETE CYCLE

```
HUMAN DIRECTION
    │
    ▼
DESIGN MODE (feature_graph.py)
    │  Create feature node
    │  Ask 21 category questions + 5 META
    │  Answer from existing knowledge
    │  Zoom deeper if META says so
    │
    ▼
SATURATION (all questions answered -> feature = 'designed')
    │
    ▼
BUILD MODE (mcp_builder.py)
    │  Read designed feature JSON
    │  Construct in UE5 via MCP calls
    │  Verify with screenshots
    │
    ▼
REPORT (verbatim Q&A + build evidence)
    │
    ▼
COMMIT
    │
    ▼
(repeat)
```

## QUESTION CATEGORIES

Every question belongs to one of 22 categories across 4 groups:

### NODE (12) — what IS this feature?
education, fame, world, testing, shipping, foundation, foundry, platform, performance,
  economy, narrative, UX, save_load, physics,
accessibility, audio, multiplayer, modding, localization

### EDGE (5) — how does it RELATE?
depends_on, proves, derived_from, conflicts, requires

### MIRROR (4) — why does it EXIST?
vision, tradeoff, evidence, terminal

### META (5) — where does it FIT in the tree?
depth, breadth, parent, priority, dependency

## TOOL HIERARCHY (fastest first)

1. **Internal council** — 7 gates in your own context. No API calls.
2. **Direct file tools** — `read`, `edit`, `write`, `readSeek_grep`.
3. **Worker bridge** — `worker_client.py` for design briefs.
4. **Graph tools** — `core/feature_graph.py` for feature management.
5. **MCP builder** — `worker_bridge/mcp_builder.py` for UE5 construction.
6. **Forge** — `worker_bridge/forge.py` for multi-file implementations.
7. **Research engine** — `research_engine` for UE5 source.

## KEY FILES

| File | Purpose |
|------|---------|
| `WORKFLOW.md` | THIS FILE — the Foundry design workflow |
| `CLAUDE.md` | Project constitution, gates, operational infrastructure |
| `SUCCESSOR_RUNBOOK.md` | Recipes for the full system (Foundry + Spiral) |
| `ONBOARDING.md` | Quick-reference Foundry onboarding (superseded by this file + CLAUDE.md for procedure) |
| `Chimera/core/feature_graph.py` | Feature graph management (create, ask, answer) |
| `worker_bridge/main.py` | FastAPI bridge to pi --mode rpc (port 8888) |
| `worker_bridge/mcp_builder.py` | MCP client for UE5 construction |
| `worker_bridge/worker_client.py` | Worker bridge SDK |
| `worker_bridge/forge.py` | Writer→Builder→Reviewer→Beats pipeline |
| `Chimera/docs/features/*.json` | All features as graph nodes |

## COMMON GOTCHAS

- **MCP config**: Section header must be `[/Script/McpAutomationBridge.McpAutomationBridgeSettings]`.
- **MCP session**: Call `initialize` first to get a `Mcp-Session-Id` header. Sessions expire.
- **MCP responses**: Are SSE format (`event: message\ndata: {...}`). Parse the `data:` line.
- **MCP port 3000**: HTTP/JSON-RPC server. Port 8091 is WebSocket-only.
- **UE5 editor path**: `C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe`
- **ProceduralGenerated/**: Never edit directly. Fix `game_code_generator.py` instead.
- **The graph lives on disk, not in your head**. Never assume state — read the JSON.
- **Build from answers, not from scratch**. The graph IS the design. Implement literally.
