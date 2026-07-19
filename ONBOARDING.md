# Lead Agent Onboarding

Welcome. You are the lead agent. Read this first. Then read WORKFLOW.md. Then proceed.

## The Goal

Build the most famous educational RPG on Steam. Deep Space Trader is the vehicle.
The Foundry engine (worker bridge + forge) is the build system.
The 7-gate internal council is the thinking method.

## Your First Actions Each Session

1. **Read this file** — you're doing it.
2. **Read WORKFLOW.md** — the 7-gate internal council, tool hierarchy, execution steps.
3. **Check the bridge** — `python -c "from worker_client import PiWorker; w=PiWorker('http://127.0.0.1:8895'); print(w.status().get('status'))"`
   - If DOWN: `cd E:\PythonChimera\worker_bridge && python -m uvicorn main:app --host 127.0.0.1 --port 8895`
4. **Check the MCP bridge** — if MCP tools fail, check:
   - DefaultGame.ini has `[/Script/McpAutomationBridge.McpAutomationBridgeSettings]` with `bEnableNativeMCP=True`
   - Port 3000 is listening (Native HTTP MCP)
   - Port 8091 is listening (WebSocket bridge)
   - Editor is running: `C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe`
5. **Check git** — `cd E:\PythonChimera && git status` — commit any pending changes before starting new work.
6. **Run preflight** — `cd E:\PythonChimera\Chimera && python -m core.preflight` — know the project state.

## Tool Hierarchy (fastest first)

1. **Internal council** — 7 gates in your own context. No external calls. Fast.
2. **Direct file tools** — `read`, `edit`, `write`, `readSeek_grep` for Python files.
3. **Worker bridge** — `worker_client.py` for design briefs, research, second opinions.
4. **Forge** — `forge.py spec.json` for multi-file implementations with gates.
5. **MCP tools** — `mcp_spawn_actor`, `mcp_capture_viewport`, `mcp_set_camera` for UE5.
6. **Research engine** — `research_engine` for UE5 source lookups.

## Key Files

| File | Purpose |
|------|---------|
| `WORKFLOW.md` | Master workflow (read this) |
| `CLAUDE.md` | Constitution — project rules, conventions, gates |
| `AGENTS.md` | Doc pointer file |
| `worker_bridge/main.py` | FastAPI bridge server (port 8895) |
| `worker_bridge/forge.py` | Workshop pipeline (Writer->Builder->Reviewer->Beats) |
| `worker_bridge/worker_client.py` | Python SDK for bridge |
| `Chimera/core/geology.py` | Geology/rock type system |
| `Chimera/core/env_education.py` | Environmental education prompts |
| `Chimera/core/splat_gpu.py` | Splat rendering (weather visibility modifier) |
| `Chimera/core/bake.py` | Asset baking pipeline |
| `Chimera/core/matter_gpu.py` | GPU terrain generation |
| `Chimera/core/game_code_generator.py` | UE5 C++ code generator (10,000+ lines) |

## Cycle Pattern

```
1. Human gives direction
2. Run 7-gate internal council (produce 20 Q&A pairs)
3. Build using tools (fastest first)
4. Report verbatim Q&A + what was built + what's open
5. Commit: git add -A && git commit && git push
6. Wait for next direction
```

## Common Gotchas

- **MCP config**: Section header must be `[/Script/McpAutomationBridge.McpAutomationBridgeSettings]`, not `[McpAutomationBridge]`. If MCP tools fail, check DefaultGame.ini.
- **UE5 editor path**: `C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe`
- **ProceduralGenerated/**: Never edit directly — fix `game_code_generator.py` instead.
- **Python encoding**: Use `# -*- coding: utf-8 -*-` at the top of files. Avoid em-dashes in strings.
- **Windows terminal**: Set `PYTHONIOENCODING=utf-8:replace` for bash commands with Unicode.
- **Worker bridge port**: Use 8895. If port conflicts, the old process needs `taskkill /F /PID <pid>`.
- **bash quoting**: Use `worker_client.py` instead of curl for bridge calls. Write Python scripts for complex commands.

## Emergency

- Bridge down: `cd E:\PythonChimera\worker_bridge && python -m uvicorn main:app --host 127.0.0.1 --port 8895`
- Editor down: `powershell -Command "Start-Process -FilePath 'C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe' -ArgumentList 'E:\PythonChimera\Chimera\Chimera.uproject -log -mcp'"`
- MCP down: Check DefaultGame.ini has the correct section, restart editor
- Everything committed: `git push origin master`
