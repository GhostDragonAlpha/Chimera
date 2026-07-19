# Lead Agent Onboarding

Welcome. You are the lead agent. Read this first every session. Then read WORKFLOW.md.
Then check the graph for the current state. Then proceed.

## The Ultimate Goal

Build the most famous educational RPG on Steam. Deep Space Trader is the vehicle.
The proceeds will be used to advance life in the universe.

This is the Mirror of Erised. Every question must trace to it. If a question cannot
answer "how does this serve the ultimate goal?" it is not asked.

## The Three Question Categories

Every feature lives in the graph as answered questions. Four groups, 27 total categories:

```
MIRROR (why does this exist? — 4)
  vision, tradeoff, evidence, terminal

NODE (what is this feature? — 13)
  education, fame, world, testing, shipping, foundation, foundry,
  platform, performance, accessibility, audio, multiplayer,
  modding, localization, economy, narrative, UX,
  save_load, physics

EDGE (how does it relate? — 5)
  depends_on, proves, derived_from, conflicts, requires

META (where does it fit in the tree? — 5)
  depth, breadth, parent, priority, dependency
```

A feature transitions: `questioning` -> `designed` -> `building` -> `verified`.
It stays in questioning until ALL questions have answers in the graph.

## Your First Actions Each Session

1. **Read this file**
2. **Check the bridge** — `cd worker_bridge && python -c "from worker_client import PiWorker; w=PiWorker('http://127.0.0.1:8895'); print(w.status().get('status'))"`
3. **Check the graph** — `ls Chimera/docs/features/` to see all features and their saturation
4. **Check MCP** — `cd worker_bridge && timeout 10 python -c "from mcp_builder import MCP; mcp=MCP(); r=mcp.call('tools/list',{}); print(len(r['result']['tools']),'tools')"`
5. **Check git** — commit any pending changes before starting new work

## The Cycle

```
1. Human gives direction
2. Load the current feature from graph
3. Check unanswered questions
4. Run internal council (7 gates)
5. Answer from existing knowledge
6. Record back to graph
7. If saturated -> BUILD: construct in UE5 via MCP
8. Verify with MCP screenshots / tests
9. Report verbatim Q&A + build results
10. Commit
```

## Tool Hierarchy (fastest first)

1. **Internal council** — 7 gates in your own context
2. **Direct file tools** — `read`, `edit`, `write`, `readSeek_grep`
3. **Worker bridge** — `worker_client.py` for design briefs
4. **Graph tools** — `core/feature_graph.py` for feature management
5. **MCP builder** — `worker_bridge/mcp_builder.py` for UE5 construction (session management, SSE parsing, actor spawn)
6. **Forge** — `worker_bridge/forge.py` for multi-file implementations
7. **Research engine** — `research_engine` for UE5 source

## Key Files

| File | Purpose |
|------|---------|
| `ONBOARDING.md` | THIS FILE |
| `WORKFLOW.md` | Detailed execution workflow |
| `CLAUDE.md` | Project constitution, gates, conventions |
| `Chimera/core/feature_graph.py` | Feature graph management |
| `worker_bridge/mcp_builder.py` | MCP client for UE5 construction |
| `worker_bridge/worker_client.py` | Worker bridge SDK |
| `Chimera/docs/features/*.json` | All features as graph nodes |
| `Chimera/core/geology.py` | Rock type / strata system |
| `Chimera/core/env_education.py` | Environmental education prompts |
| `Chimera/core/cloud_education.py` | Cloud type education |
| `Chimera/core/cloud_weather.py` | Weather state machine |
| `Chimera/core/day_night_orchestrator.py` | Day/night cycle orchestrator |

## Common Gotchas

- **MCP config**: Section header must be `[/Script/McpAutomationBridge.McpAutomationBridgeSettings]` in DefaultGame.ini.
- **MCP session**: Call `initialize` first to get a `Mcp-Session-Id`. Sessions expire after inactivity.
- **MCP responses**: SSE format (`event: message\ndata: {...}`). Parse the `data:` line, not the raw body.
- **MCP port 3000**: HTTP/JSON-RPC. Port 8091 is WebSocket-only (chiR24).
- **UE5 editor path**: `C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe`
- **ProceduralGenerated/**: Never edit directly. Fix `game_code_generator.py`.
- **Graph lives on disk**: Never assume state. Read the JSON before writing.
- **Build from answers**: The graph IS the design. Implement literally from the Q&A.

## Emergency

- Bridge down: `cd E:\PythonChimera\worker_bridge && python -m uvicorn main:app --host 127.0.0.1 --port 8895`
- Editor down: `powershell -Command "Start-Process -FilePath 'C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe' -ArgumentList 'E:\PythonChimera\Chimera\Chimera.uproject -log -mcp'"`
- MCP down: Check DefaultGame.ini has correct section. Restart editor.
- Everything committed: `git push origin master`
