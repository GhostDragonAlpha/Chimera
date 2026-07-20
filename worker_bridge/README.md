# PI Worker Bridge + Gaussian Foundry

A multi-agent game development system. Spawns a second PI agent via `pi --mode rpc`,
wraps it in a FastAPI server, and runs a build pipeline.

## Architecture (Simplified)

```
Main Session ──HTTP/WS──► FastAPI Server ──stdin/stdout JSONL──► pi --mode rpc (worker)
                                │
                                ▼
                     Workshop: Writer → Builder → Reviewer → Beats
```

**The Council (dialogos.py) is retired.** The exploratory Q&A phase completed after 10 cycles.
The system now operates in BUILD mode: direct design briefs to the worker, implementation
via the Workshop (forge.py), results reported to the human.

## Files

| File | Status | Purpose |
|------|--------|---------|
| `main.py` | ACTIVE | FastAPI server wrapping `pi --mode rpc` |
| `forge.py` | ACTIVE | Workshop: Writer→Builder→Reviewer→Beats pipeline |
| `worker_client.py` | ACTIVE | Python SDK for bridge API |
| `dashboard.html` | ACTIVE | Live monitoring UI at `/` |
| `monitor.ps1` | ACTIVE | PowerShell live monitor |
| `launch_visible.bat` | ACTIVE | Opens visible bridge + monitor windows |
| `run_bridge_visible.bat` | ACTIVE | Opens bridge in visible window |
| `open_windows.bat` | ACTIVE | Opens both bridge and chronicle watcher |
| `watch_chronicle.bat` | ACTIVE | Tails chronicle files in real-time |
| `README.md` | ACTIVE | This file |
| `FOUNDRY_DESIGN.md` | ACTIVE | Architecture design doc |
| `dialogos.py` | DELETED | Council format retired |
| `council_to_forge.py` | DELETED | Depended on Council |
| `run.py` | DELETED | Replaced by direct forge invocation |

## Running

```powershell
cd E:\PythonChimera\worker_bridge

# Start the bridge
python -m uvicorn main:app --host 127.0.0.1 --port 8888

# Or with a visible window
.\run_bridge_visible.bat

# Send a design brief and run the forge:
python -c "
from worker_client import PiWorker
w = PiWorker('http://127.0.0.1:8888')
w.prompt('Design an educational mechanic...')
"
```

## Workflow

1. Human gives direction
2. Agent sends design brief to worker via bridge
3. Worker responds with design/code
4. Forge implements if spec is produced
5. Agent reports results to human
6. Commit
