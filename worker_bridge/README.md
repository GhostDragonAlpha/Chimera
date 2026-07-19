# PI Worker Bridge

Spawns a second PI agent via `pi --mode rpc` and wraps it in a **FastAPI** server with REST + WebSocket endpoints so the main AI can control it and read its output in real-time.

## How it works

```
┌────────────────┐   HTTP/WS     ┌─────────────────┐   stdin/stdout JSONL    ┌─────────────┐
│  Main Session  │ ──────────►   │  FastAPI Server  │ ◄────────────────────   │ pi --mode   │
│  (this AI)     │ ◄──────────   │  127.0.0.1:8890  │ ────────────────────►  │ rpc (worker)│
└────────────────┘               └────────┬────────┘                        └─────────────┘
                                           │
                                    ┌──────┴──────┐
                                    │  WebSocket   │
                                    │  /ws         │
                                    │ (real-time   │
                                    │  event stream)│
                                    └─────────────┘
```

**Architecture** (single-threaded async dispatcher, no race conditions):

1. `stdout_reader` reads JSONL lines from the worker PI's stdout into an `asyncio.Queue`
2. `line_dispatcher` consumes the queue — resolves pending RPC request futures, then broadcasts to WebSocket clients
3. `send_rpc_command` puts a future into `pending_requests`, writes JSON to the worker's stdin, and `await`s the future

## Running

```powershell
cd E:\PythonChimera\worker_bridge

# Option A: uvicorn directly
python -m uvicorn main:app --host 127.0.0.1 --port 8890 --reload

# Option B: PowerShell script
.\launch.ps1

# Option C: Python launcher
python launch.py
```

## REST API Reference

| Method | Endpoint | Body | Description |
|--------|----------|------|-------------|
| GET | `/api/status` | — | Check if worker PI process is alive |
| POST | `/api/prompt` | `{"message":"..."}` | Send prompt to worker PI (returns after preflight) |
| POST | `/api/bash` | `{"command":"..."}` | Execute bash command in worker's shell |
| POST | `/api/steer` | `{"message":"..."}` | Interrupt worker mid-run with redirect |
| POST | `/api/follow_up` | `{"message":"..."}` | Queue message for after worker finishes |
| POST | `/api/abort` | — | Abort current operation |
| POST | `/api/abort_bash` | — | Abort running bash command |
| GET | `/api/get_state` | — | Full session state (model, streaming, messages count) |
| GET | `/api/get_messages` | — | All session messages |
| GET | `/api/get_entries` | `?since=...` | Session entries in append order |
| GET | `/api/get_tree` | — | Session entry tree |
| GET | `/api/get_commands` | — | Available extension/prompt/skill commands |
| GET | `/api/get_available_models` | — | All models available to the worker |
| GET | `/api/get_session_stats` | — | Session statistics |
| POST | `/api/cycle_model` | — | Cycle to next model |
| POST | `/api/set_thinking_level` | `{"level":"high"}` | Set thinking level |
| POST | `/api/compact` | `{"customInstructions":"..."}` | Compact session context |

## WebSocket

Connect to `ws://127.0.0.1:8890/ws` to receive **all events** from the worker PI
in real-time (prompt responses, tool calls, agent messages, etc.).

The WebSocket also accepts `"ping"` messages and responds with `{"type":"pong"}`.

## Python Client

```python
from worker_client import PiWorker

worker = PiWorker("http://127.0.0.1:8890")

# Check alive
print(worker.status())

# Send a prompt (fire-and-forget — returns immediately on preflight success)
worker.prompt("List the files in the current directory")

# Execute bash and get results
result = worker.bash("dir /s /b | head -10")
print(result["data"]["output"])

# Interrupt the agent mid-stream
worker.steer("Stop and redirect")

# Get the worker's current state
state = worker.get_state()
print(state["data"]["model"]["id"])
print(state["data"]["messageCount"])
