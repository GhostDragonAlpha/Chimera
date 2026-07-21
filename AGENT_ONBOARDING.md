# Chimera Agent Onboarding Prompt

> Paste this into a new agent session. It gets you into the rhythm in under 2 minutes.

## THE RHYTHM

This is not a task-list project. It is a continuous question loop:

**ask → answer → ask → answer → ask**

A task is one answer, not the destination. The session ends when the human ends it.

## THE PIPELINE — from meta-constraint to decoded level

Everything in this project follows the same pipeline. No exceptions:

```
META-CONSTRAINT → CATALOG → DOMAIN → TRAIN → DECODE → LEVEL
(The Mirror)      (69,749     (seed/    (walls    (MCP        (emergent_
                   UE5 vars)   mutate/   only)     spawn)      world)
                                measure)
```

Every step is data. Nothing is hand-authored. The Mirror of Erised is a hard constraint at every level: a costless life produces a dim signal, a generous life produces a strong one.

## THE 40-QUESTION DOCUMENT — how the Mirror reflects

Every feature and sub-feature created gets a 40-question document. Generating it is not a command you run silently — you TYPE the 40 questions and their answers in chat first. The typing IS the reflection. It passes through you before it reaches the filesystem.

The questions define the feature's scope, depth, and Mirror connection. They persist forever, even before the feature exists. Answers are filled in over time. The depth_verdict tells you whether to go deeper:

| Answered | Verdict | Meaning |
|----------|---------|---------|
| 0-9 | unexplored | Feature is barely understood. Needs investigation. |
| 10-19 | explored | Basic understanding exists. |
| 20-29 | adequate | Feature is well-understood. May be deep enough. |
| 30-40 | deep | Feature is fully understood. Decomposition is complete. |

The 40-question document lives in two places:
1. `docs/forty_questions/<name>.json` — the full document
2. The DNA graph (Graphify MCP server) — queryable via MCP tools

**The rule: type the 40 questions and answers in chat first. Save to file second. The chat IS the reflection.**

## THE MIRROR — the steering wheel

The Mirror of Erised is not a document — it is the central node in the DNA graph. Every feature connects to it. Before building anything, check: does this feature serve the Mirror?

- **Direct Mirror features** — giving mechanics, sacrifice, beacon signal, ending
- **Enabling Mirror features** — survival pressure, resource scarcity, NPC needs
- **Orthogonal features** — cosmetic, technical infrastructure, non-interactive

The auto-decomposer prioritizes Mirror-connected features over orthogonal ones.

## THE GRAPH (Graphify MCP server) — the system's memory

The DNA graph stores everything: features, training runs, 40-question depth, Mirror connections, gap analysis. It's served over MCP by `graphify-mcp.exe` (configured in `.mcp.json`).

**MCP tools available:** `query_graph`, `get_node`, `get_neighbors`

The graph feeds back into training. Measure functions can call `forty_questions.graph_context()` to get the current graph state — feature count, Mirror connections, depth distribution, gaps — and use it to seed or inform training.

**Key graph queries:**
```
# Get all 40-question records
graphify_query('feature', '40q_')

# Get unexplored features  
[f for f in all_features if f.get('status') == 'unexplored']

# Get Mirror-connected features
[f for f in all_features if 'mirror' in str(f).lower()]
```

## THE AUTO-DECOMPOSER — fills the gaps automatically

`core/auto_decomposer.py` reads the DNA graph, finds gaps (parent rungs with few sub-rungs), prioritizes by Mirror weight, generates sub-rung constraints + domains + 40-question documents, and trains all sub-rungs in parallel.

```powershell
# Auto-decompose a specific parent
python -m core.auto_decomposer ground_terrain 4

# Auto-select the highest-Mirror-weighted gap
python -m core.auto_decomposer
```

The auto-decomposer skips any feature that already exists in the graph (prevents duplicates). It records all new features to the graph with their Mirror connections.

## THE COMPOSITIONAL LADDER — 10 rungs, all trained

```
cosmic rung → planetary rung → ground rung → body rung → biome rung → shelter rung
(big bang)   (climate)        (terrain)    (survival)  (resources) (threshold)
                                                                          ↓
                              narrative rung ← economy rung ← social rung ← form rung
                              (beacon)       (fabricator)   (NPC needs)  (geometry)
```

Each rung trained independently. All 12 inter-rung seams verified by composition pass. The Mirror is a hard constraint at every level.

## FIRST ACTIONS (every session)

> **D3D12 will crash.** Launch the editor with `-d3d11` or it will
> `EXCEPTION_PRIV_INSTRUCTION` in D3D12RHI (see CAVEATS.md §1).

```powershell
cd E:\PythonChimera\Chimera
python -m core.preflight              # Live state: GPA, loops, CAPCOM
python -m core.capcom brief            # Operator signals
python -m core.helm targets            # Seed-vs-reality gaps
python -m core.forty_questions show <name>  # Check a feature's 40Q depth
```

Read `task_progress.md` for the handoff. Read `EMERGENCE_ROADMAP.md` for the build sequence.

**Opening the game in UE5:**
```powershell
"/c/Program Files/Epic Games/UE_5.8/Engine/Binaries/Win64/UnrealEditor.exe" ^
  "E:/PythonChimera/Chimera/Chimera.uproject" -d3d11
```
Do NOT use `-ExecutePythonScript` — the editor will exit after the script runs.

**Building the level from decoded parameters:**
1. Open the editor (command above)
2. Open Python Console: Window → Developer Tools → Python
3. Run: `exec(open("E:/PythonChimera/Chimera/build_level.py").read())`
4. The SkySphere may fail to spawn — place it manually from the Place Actors panel.

For the full caveat list, read `docs/CAVEATS.md` first.

Read `task_progress.md` for the handoff. Read `EMERGENCE_ROADMAP.md` for the build sequence.

## YOUR TOOLS (in order of power)

1. **40-question engine** — diagnose any feature:
   ```powershell
   python -m core.forty_questions generate <name> <parent>
   python -m core.forty_questions answer <name> 1 "Answer text"
   python -m core.forty_questions show <name>
   ```

2. **Auto-decomposer** — fill gaps automatically:
   ```powershell
   python -m core.auto_decomposer <parent> <n_clusters>
   ```

3. **Graph context** — feed graph state into training:
   ```python
   from core.forty_questions import graph_context
   ctx = graph_context()
   ```

4. **Sleepwalker beats** — verify ANYTHING:
   ```powershell
   python -m core.beat_lint --beats docs/beats/<file>.beats.json
   python -m core.sleepwalker --beats docs/beats/<file>.beats.json --session <name>
   ```

5. **MCP bridge** — query UE5 editor:
   ```python
   from core.telemetry_probe import MCPStdioClient; c = MCPStdioClient()
   ```

6. **DNA graph** — query all system state:
   ```python
   from core.graphify_interface import graphify_query
   ```

7. **Training loop** — train any domain:
   ```powershell
   python -m core.trainer --domain core.trainables.generated.<name> --objective docs/objectives/<name>.json
   ```

8. **Decoder** — place trained winners in the level:
   ```powershell
   python -m core.decoder
   ```

## NEVER DO

> **D3D12 will crash the editor.** Always launch with `-d3d11`. Read `docs/CAVEATS.md` before any editor work.
> **-ExecutePythonScript auto-exits the editor.** Use the Python Console instead.
> **SkySphere fails from Python.** Place it manually via Place Actors panel.
> **MCP bridge port 3000 is not auto-started.** Use the Python Console instead.
> **The build script places placeholder geometry.** Spheres, cylinders, cubes — no game art.

- **Never place a cube.** If you find yourself authoring a form, stop. The form emerges from training.
- **Never trust a scale.** Every metric gets cheated. Walls only, no maximize/minimize.
- **Never decompose in advance.** Sub-features emerge when a season fails. Pre-splitting is guessing.
- **Never generate 40 questions silently.** Type them in chat first. The typing is the reflection. The file is the record.
- **Never skip the 40 questions.** Every feature gets a 40Q document at creation. Answers fill over time.
- **Never write to the level without the decoder.** The decoder reads trained winners. MCP spawn is only for the decoder.
- **Never trust `success: true`** — read the value back.
- **Never skip the formula.** CONSTRAINT → EXISTING → WALLS → WORK → JUDGE.

## CURRENT GAME STATE

- **Level**: emergent_world.umap (160KB) - PlayerStart + warm sun + fog + ground plane
- **Sun**: Warm directional light at (0,0,2000), angled 330/-45
- **Sky**: Atmospheric fog present. SkySphere NOT placed (Blueprint spawn fails - place manually)
- **Terrain**: Large ground plane at origin
- **Resources**: 7 spheres scattered on ring pattern
- **Shelter**: Cylinder disk at (0,-800,0) with blue PointLight
- **NPCs**: 3 cylinder markers around shelter
- **Beacon**: Tower + red PointLight + sphere at (2000,0,50)
- **Graph**: 3,660+ nodes, 392 features, 8 Mirror connections
- **Domains**: 41+ generated, all trained, all passing
- **Auto-decomposer**: Decomposes parent rungs into sub-rungs, trains in parallel

## DOCS TO KNOW

| File | What it is |
|---|---|
| **`AGENT_ONBOARDING.md`** | **THIS FILE — start here** |
| `DECISION_METHOD.md` | 7-step fallthrough tree — never asks |
| `EMERGENT_WORKFLOW.md` | The emergent pipeline |
| `EMERGENCE_ROADMAP.md` | The 9-rung compositional ladder |
| `docs/THOUGHT_CHAIN.md` | Complete reasoning, next steps A-G |
| `docs/CAVEATS.md` | Things that broke and why — read before building |
| `core/auto_decomposer.py` | Automatic sub-rung decomposition + training |
| `core/forty_questions.py` | 40-question engine — every feature's spec |
| `core/decoder.py` | Generic decoder — reads ANY trained genome |
| `core/domain_generator.py` | Generates domains from constraints + catalog |
| `core/research_bridge.py` | Research fills 40Q knowledge gaps |
| `CLAUDE.md` | Constitution, gates, core systems |
| `.mcp.json` | MCP server config (graphify, unreal-engine) |

All other `.md` files in `Chimera/docs/` are marked **DEPRECATED** — they describe the old approach. Do not read them.
