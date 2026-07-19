# Lead Agent Onboarding

Welcome. You are the lead agent. Read this first every session. Then read WORKFLOW.md.
Then check the graph for the current state. Then proceed.

## The Ultimate Goal

Build the most famous educational RPG on Steam. Deep Space Trader is the vehicle.
The proceeds will be used to advance life in the universe.

This is the Mirror of Erised. Every question must trace to it. If a question cannot
answer "how does this serve the ultimate goal?" it is not asked.

## The Three Question Categories

Every feature lives in the graph as answered questions. There are three layers:

```
MIRROR (why does this exist?)
  vision      — Does this serve the ultimate goal?
  tradeoff    — What are we sacrificing to do this?
  evidence    — How do we know this is the right path?
  terminal    — Does this chain reach a human or physics?

NODE (what is this feature?)
  education   — Does it teach real knowledge?
  fame        — Does it make the game more desirable than competitors?
  world       — Does it make the universe feel real and alive?
  shipping    — Does it move toward a playable release?
  foundation  — Does it strengthen the infrastructure?

EDGE (how does it relate to other things?)
  depends_on    — What must exist before this?
  proves        — What existing answer does this validate?
  derived_from  — What question led to this?
  conflicts     — What existing design does this challenge?
  requires      — What skills, tools, or data are needed?
```

A feature is not ready to build until EVERY question has an answer.
The feature status goes: questioning -> designed -> building -> verified.

## Your First Actions Each Session

1. **Read this file** — you're doing it.
2. **Read WORKFLOW.md** — the detailed workflow.
3. **Check the bridge** — `python -c "from worker_client import PiWorker; w=PiWorker('http://127.0.0.1:8895'); print(w.status().get('status'))"`
4. **Check the graph** — `ls Chimera/docs/features/` to see all features. Check their status.
5. **Check MCP** — port 3000 and 8091 must be listening. If not, restart UE5 editor.
6. **Check git** — commit any pending changes before starting new work.

## The Cycle

```
1. HUMAN gives direction
2. LOAD the current feature from graph (docs/features/<name>.json)
3. CHECK existing questions — which are unanswered?
4. RUN internal council (5 node + 4 edge + 4 mirror categories)
5. SEARCH chronicle + knowledge graph for existing answers
6. ANSWER only genuinely new questions
7. RECORD answers back to the feature JSON
8. IF all questions answered -> feature is DESIGNED -> ready to build
9. EXECUTE using tools (fastest first)
10. REPORT verbatim Q&A + what was built + what remains
11. COMMIT to git
```

## Tool Hierarchy (fastest first)

1. **Internal council** — 7 gates in your own context. No API calls.
2. **Direct file tools** — `read`, `edit`, `write`, `readSeek_grep`.
3. **Worker bridge** — `worker_client.py` for design briefs.
4. **Graph tools** — `core/feature_graph.py` for feature management.
5. **Forge** — `forge.py spec.json` for multi-file implementations.
6. **MCP tools** — `mcp_spawn_actor`, `mcp_capture_viewport` for UE5.
7. **Research engine** — `research_engine` for UE5 source.

## Key Files

| File | Purpose |
|------|---------|
| `ONBOARDING.md` | THIS FILE — start here every session |
| `WORKFLOW.md` | Detailed execution workflow |
| `CLAUDE.md` | Project constitution, gates, conventions |
| `AGENTS.md` | Doc pointer file |
| `worker_bridge/main.py` | FastAPI bridge server (port 8895) |
| `worker_bridge/forge.py` | Workshop pipeline |
| `worker_bridge/worker_client.py` | Python SDK for bridge |
| `worker_bridge/graph_before_council.py` | Search chronicle + knowledge graph |
| `Chimera/core/feature_graph.py` | Feature graph management |
| `Chimera/docs/features/*.json` | All features as graph nodes |

## Common Gotchas

- **MCP config**: Section header must be `[/Script/McpAutomationBridge.McpAutomationBridgeSettings]`.
  If MCP fails, check `Chimera/Config/DefaultGame.ini` has this section with `bEnableNativeMCP=True`.
- **UE5 editor path**: `C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe`
- **ProceduralGenerated/**: Never edit directly. Fix `game_code_generator.py` instead.
- **Python encoding**: Use `sys.stdout.reconfigure(encoding='utf-8', errors='replace')`.
- **Windows terminal**: Set `PYTHONIOENCODING=utf-8:replace` for bash commands.
- **Worker bridge port**: Use 8895. Kill stale processes with `taskkill /F /PID <pid>`.
- **bash quoting**: Use `worker_client.py` instead of curl. Write Python scripts for complex commands.
- **The graph lives on disk, not in your head**. Never assume you know the state. Read the JSON.

## Emergency

- Bridge down: `cd E:\PythonChimera\worker_bridge && python -m uvicorn main:app --host 127.0.0.1 --port 8895`
- Editor down: `powershell -Command "Start-Process -FilePath 'C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe' -ArgumentList 'E:\PythonChimera\Chimera\Chimera.uproject -log -mcp'"`
- MCP down: Check DefaultGame.ini has correct section. Restart editor.
- Everything committed: `git push origin master`
