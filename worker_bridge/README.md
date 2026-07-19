# PI Worker Bridge + Gaussian Foundry

A multi-agent autonomous game development system. Spawns a second PI agent via `pi --mode rpc`, wraps it in a **FastAPI** server, and orchestrates a dialectical development loop:

```
Council (Q&A debate) → Bridge (spec extraction) → Workshop (code → build → review → test) → Commit
```

## Architecture

```
┌────────────────┐   HTTP/WS     ┌─────────────────┐   stdin/stdout JSONL    ┌─────────────┐
│  Main Session  │ ──────────►   │  FastAPI Server  │ ◄────────────────────   │ pi --mode   │
│  (this AI)     │ ◄──────────   │  127.0.0.1:8891  │ ────────────────────►  │ rpc (worker)│
└────────────────┘               └────────┬────────┘                        └─────────────┘
                                           │
                                    ┌──────┴──────┐
                                    │  Gaussian    │
                                    │  Foundry     │
                                    │  Pipeline    │
                                    └──────┬──────┘
                                           │
              ┌────────────────────────────┼────────────────────────────┐
              ▼                            ▼                            ▼
     ┌─────────────────┐       ┌─────────────────────┐       ┌──────────────────┐
     │  COUNCIL         │       │  WORKSHOP            │       │  PROVING GROUND   │
     │  dialogos.py     │       │  forge.py            │       │  (status checks)  │
     │  Q&A dialectic   │ ──►   │  Writer→Builder→     │ ──►   │  Build, Model,    │
     │  10 per turn     │       │  Reviewer→Beats      │       │  Visual verify    │
     └─────────────────┘       └─────────────────────┘       └──────────────────┘
```

## How it works

**The Council (dialogos.py):** Two simulated roles (Worker and Main) take turns asking and answering 10 technical questions each, building on the entire prior conversation. Each turn produces 4 chronicle files (worker_questions, main_answers, main_questions, worker_answers).

**The Bridge (council_to_forge.py):** Reads the chronicle and extracts a `spec_manifest.json` identifying target files, edit plans, and test strategies from the dialectical discussion.

**The Workshop (forge.py):** Four-stage gated pipeline:
1. **Writer** — Reads the spec and makes file edits via the worker PI
2. **Builder** — Compiles (full pipeline or Python syntax check)
3. **Reviewer** — Checks diff against project conventions
4. **Beats** — Runs sleepwalker beat tests in Unreal Engine PIE

**The Orchestrator (run.py):** Single entry point for the full pipeline or individual stages.

## Running

```powershell
cd E:\PythonChimera\worker_bridge

# Start the worker bridge (port 8891)
python -m uvicorn main:app --host 127.0.0.1 --port 8891

# Full pipeline: 2 turns of Council + Bridge + Workshop
python run.py --turns 2

# Individual stages:
python run.py --council-only --turns 2   # just the Q&A cycle
python run.py --bridge-only               # extract spec from chronicle
python run.py --forge-only specs/spec.json # implement from spec
```

## REST API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/status` | Worker bridge health check |
| POST | `/api/prompt` | Send prompt to worker PI |
| POST | `/api/bash` | Execute bash command on worker |
| POST | `/api/steer` | Interrupt worker mid-run |
| POST | `/api/follow_up` | Queue message for after finish |
| GET | `/api/get_state` | Full session state |
| GET | `/api/get_messages` | All session messages |
| GET | `/api/get_entries` | Session entries |
| GET | `/api/get_tree` | Session entry tree |
| GET | `/api/get_commands` | Available commands |
| GET | `/api/get_available_models` | All models |
| GET | `/api/get_session_stats` | Session statistics |
| POST | `/api/cycle_model` | Cycle to next model |
| WS | `/ws` | Real-time event stream |

## Files

| File | Purpose |
|------|---------|
| `main.py` | FastAPI server wrapping `pi --mode rpc` |
| `dialogos.py` | Council: automated dialectical Q&A loop |
| `council_to_forge.py` | Bridge: extract spec from chronicle |
| `forge.py` | Workshop: Writer→Builder→Reviewer→Beats |
| `run.py` | Unified entry point |
| `worker_client.py` | Python SDK for REST API |
| `launch.ps1` / `launch.py` | Launcher scripts |

## Chronicle

All Q&A cycles are saved to `chronicle/turn_NNN_phase.txt`. Spec files go to `specs/spec_turn_NNN.json`. Forge results go to `chronicle/forge_result_*.json`.
