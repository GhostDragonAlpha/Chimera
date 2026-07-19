"""
PI Worker Bridge — FastAPI wrapper around `pi --mode rpc`.

Architecture (single-line dispatcher to avoid races):
    stdout_reader ──> stdout_queue ──> dispatcher ──> pending_req futures
                                                      └─> WebSocket clients
"""

import asyncio
import json
import subprocess
import sys
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Optional, List, Set

# ─── Globals ────────────────────────────────────────────────────────────────
pi_process: subprocess.Popen = None
stdout_queue: asyncio.Queue = None
stderr_lines: list = []
ws_clients: Set[WebSocket] = set()
pending_requests: dict[str, asyncio.Future] = {}

# ─── Subprocess helpers ─────────────────────────────────────────────────────

def start_pi_rpc():
    global pi_process
    cli_path = (
        r"C:\Users\allen\node-portable\node-v22.23.1-win-x64"
        r"\node_modules\@earendil-works\pi-coding-agent\dist\rpc-entry.js"
    )
    pi_process = subprocess.Popen(
        ["node", cli_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=False,
        bufsize=1,
    )


async def stdout_reader():
    """Read lines from PI stdout into a queue."""
    global pi_process, stdout_queue
    if not pi_process or not pi_process.stdout:
        return
    try:
        while True:
            line = await asyncio.get_event_loop().run_in_executor(
                None, pi_process.stdout.readline
            )
            if not line:
                break
            line_str = line.decode("utf-8").strip()
            if line_str:
                await stdout_queue.put(line_str)
    except Exception as e:
        print(f"[stdout_reader error] {e}", file=sys.stderr)


async def stderr_reader():
    """Collect PI stderr for debugging."""
    global pi_process, stderr_lines
    if not pi_process or not pi_process.stderr:
        return
    try:
        while True:
            line = await asyncio.get_event_loop().run_in_executor(
                None, pi_process.stderr.readline
            )
            if not line:
                break
            line_str = line.decode("utf-8").strip()
            if line_str:
                stderr_lines.append(line_str)
    except Exception as e:
        print(f"[stderr_reader error] {e}", file=sys.stderr)


async def line_dispatcher():
    """
    Single consumer of stdout_queue.

    - If line is a RPC response with a matching pending future → resolve it.
    - All lines (including responses) are forwarded to WebSocket clients.
    """
    global stdout_queue, ws_clients, pending_requests
    while True:
        line = await stdout_queue.get()
        try:
            parsed = json.loads(line)
        except Exception:
            parsed = None

        # 1. Resolve pending RPC requests
        if (
            parsed
            and isinstance(parsed, dict)
            and parsed.get("type") == "response"
        ):
            req_id = parsed.get("id")
            if req_id and req_id in pending_requests:
                fut = pending_requests.pop(req_id)
                if not fut.done():
                    fut.set_result(parsed)

        # 2. Broadcast to all WebSocket clients
        dead: list[WebSocket] = []
        for ws in ws_clients:
            try:
                await ws.send_text(line)
            except Exception:
                dead.append(ws)
        for ws in dead:
            ws_clients.discard(ws)


# ─── Lifespan ──────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    global pi_process, stdout_queue
    start_pi_rpc()
    await asyncio.sleep(1.0)
    stdout_queue = asyncio.Queue()
    asyncio.create_task(stdout_reader())
    asyncio.create_task(stderr_reader())
    asyncio.create_task(line_dispatcher())
    yield
    if pi_process and pi_process.poll() is None:
        pi_process.terminate()


app = FastAPI(title="PI Worker Bridge", lifespan=lifespan)

# ─── WebSocket ──────────────────────────────────────────────────────────────

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    ws_clients.add(ws)
    try:
        while True:
            data = await ws.receive_text()
            if data == "ping":
                await ws.send_text('{"type":"pong"}')
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        ws_clients.discard(ws)


# ─── Internal RPC helper ───────────────────────────────────────────────────

async def send_rpc_command(command_type: str, data: dict = None) -> dict:
    """Send a JSON-RPC command to the PI process and await its response."""
    global pi_process, pending_requests

    if not pi_process or pi_process.poll() is not None:
        raise HTTPException(status_code=503, detail="PI RPC process not running")

    req_id = f"req_{uuid.uuid4()}"
    cmd_dict = {"type": command_type, "id": req_id}
    if data:
        cmd_dict.update(data)

    # Create a future that line_dispatcher will resolve
    fut = asyncio.get_event_loop().create_future()
    pending_requests[req_id] = fut

    # Write command to PI's stdin
    pi_process.stdin.write((json.dumps(cmd_dict) + "\n").encode("utf-8"))
    pi_process.stdin.flush()

    # Wait for the response (with timeout)
    try:
        result = await asyncio.wait_for(fut, timeout=300.0)
        return result
    except asyncio.TimeoutError:
        pending_requests.pop(req_id, None)
        raise HTTPException(status_code=504, detail=f"RPC command '{command_type}' timed out")


# ─── REST endpoints ────────────────────────────────────────────────────────

class PromptCommand(BaseModel):
    message: str
    images: Optional[List[str]] = None

class BashCommand(BaseModel):
    command: str
    excludeFromContext: Optional[bool] = None


@app.post("/api/prompt")
async def prompt(cmd: PromptCommand):
    return await send_rpc_command("prompt", {"message": cmd.message, "images": cmd.images})

@app.post("/api/steer")
async def steer(cmd: PromptCommand):
    return await send_rpc_command("steer", {"message": cmd.message, "images": cmd.images})

@app.post("/api/follow_up")
async def follow_up(cmd: PromptCommand):
    return await send_rpc_command("follow_up", {"message": cmd.message, "images": cmd.images})

@app.post("/api/bash")
async def bash_cmd(cmd: BashCommand):
    return await send_rpc_command("bash", {
        "command": cmd.command,
        "excludeFromContext": cmd.excludeFromContext,
    })

@app.post("/api/abort")
async def abort_cmd():
    return await send_rpc_command("abort", {})

@app.post("/api/abort_bash")
async def abort_bash():
    return await send_rpc_command("abort_bash", {})

@app.get("/api/get_state")
async def get_state():
    return await send_rpc_command("get_state", {})

@app.get("/api/get_available_models")
async def get_available_models():
    return await send_rpc_command("get_available_models", {})

@app.post("/api/cycle_model")
async def cycle_model():
    return await send_rpc_command("cycle_model", {})

@app.post("/api/set_thinking_level")
class ThinkingLevelCmd(BaseModel):
    level: str

@app.post("/api/set_thinking_level")
async def set_thinking_level(cmd: ThinkingLevelCmd):
    return await send_rpc_command("set_thinking_level", {"level": cmd.level})

@app.post("/api/compact")
class CompactCmd(BaseModel):
    customInstructions: Optional[str] = None

@app.post("/api/compact")
async def compact(cmd: CompactCmd):
    data = {}
    if cmd.customInstructions:
        data["customInstructions"] = cmd.customInstructions
    return await send_rpc_command("compact", data)

@app.get("/api/get_session_stats")
async def get_session_stats():
    return await send_rpc_command("get_session_stats", {})

@app.get("/api/get_messages")
async def get_messages():
    return await send_rpc_command("get_messages", {})

@app.get("/api/get_entries")
async def get_entries(since: str = None):
    data = {}
    if since:
        data["since"] = since
    return await send_rpc_command("get_entries", data)

@app.get("/api/get_fork_messages")
async def get_fork_messages():
    return await send_rpc_command("get_fork_messages", {})

@app.post("/api/new_session")
async def new_session():
    return await send_rpc_command("new_session", {})

@app.get("/api/get_tree")
async def get_tree():
    return await send_rpc_command("get_tree", {})

@app.get("/api/get_commands")
async def get_commands():
    return await send_rpc_command("get_commands", {})

@app.get("/api/status")
async def status():
    alive = pi_process is not None and pi_process.poll() is None
    return {
        "status": "running" if alive else "stopped",
        "pid": pi_process.pid if alive else None,
        "ws_clients": len(ws_clients),
        "stderr_lines": len(stderr_lines),
        "stderr_tail": stderr_lines[-10:] if stderr_lines else [],
    }


# ─── Direct execution ──────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8888, reload=True)
