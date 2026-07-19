<#
.SYNOPSIS
    Launch the PI Worker Bridge – a FastAPI server that wraps `pi --mode rpc`
    and exposes REST + WebSocket endpoints so the main AI can send commands
    to a second PI agent and read its output.

.DESCRIPTION
    Starts uvicorn on 127.0.0.1:8888.  Use the REST API to send prompts,
    bash commands, etc. to the worker PI.  Connect to /ws via WebSocket
    to stream ALL events the worker PI emits in real time.

    Available endpoints (curl examples):
      GET  http://127.0.0.1:8888/api/status
      POST http://127.0.0.1:8888/api/prompt       {"message":"..."}
      POST http://127.0.0.1:8888/api/bash          {"command":"..."}
      POST http://127.0.0.1:8888/api/steer         {"message":"..."}
      POST http://127.0.0.1:8888/api/follow_up     {"message":"..."}
      POST http://127.0.0.1:8888/api/abort
      GET  http://127.0.0.1:8888/api/get_state
      GET  http://127.0.0.1:8888/api/get_messages
      GET  http://127.0.0.1:8888/api/get_entries
      GET  http://127.0.0.1:8888/api/get_tree
      GET  http://127.0.0.1:8888/api/get_commands

.EXAMPLE
    .\launch.ps1                        # default port 8888
    .\launch.ps1 -Port 9999              # custom port
#>

param(
    [int]$Port = 8888
)

Write-Host "╔════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║      PI Worker Bridge Launcher                 ║" -ForegroundColor Cyan
Write-Host "║  Spawns pi --mode rpc + FastAPI on port $Port    ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════╝" -ForegroundColor Cyan

cd $PSScriptRoot
python -m uvicorn main:app --host 127.0.0.1 --port $Port --reload
