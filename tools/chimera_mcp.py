"""chimera_mcp -- the Kimi Work bridge to the Chimera Engine.

The engine (ChimeraEngine/mcp_server.py, FastMCP over stdio) is a SEPARATE system; this client
exists so every engine call CROSSES THE BOUNDARY (a spawned server process over the sanctioned
MCP tool surface) instead of importing Engine() into our own process -- which would be a monad,
and a monad is never proof (MCP_ENGINE.md, "dyadAnalysis").

Usage:
    python tools/chimera_mcp.py list
    python tools/chimera_mcp.py orient
    python tools/chimera_mcp.py frame --term theSeed --claim "..."
    python tools/chimera_mcp.py question --term theSeed --question "..." --variables '["a","b"]'
    python tools/chimera_mcp.py classify --term theSeed --assignments '{"a":"PHYSICS"}'

Values are parsed as JSON when possible, else passed as strings. The server runs under the
project Python (the one .mcp.json resolves to under Claude Code): override with
CHIMERA_ENGINE_PYTHON. Each invocation spawns a fresh server; engine state persists on disk
(engine_state.json), so per-call processes lose nothing.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SERVER = REPO / "ChimeraEngine" / "mcp_server.py"

ENGINE_PYTHON = (
    os.environ.get("CHIMERA_ENGINE_PYTHON")
    or os.environ.get("DAIMON_USER_PYTHON")
    or sys.executable
)

PROTOCOL_VERSION = "2024-11-05"

# The engine renders on the GPU (Numba CUDA), and Numba finds libNVVM only via CUDA_PATH/PATH.
# Claude Code's shell inherited those; this bridge may not -- so hand the server the toolkit
# explicitly (measured: nvvm64_40_0.dll lives in <toolkit>\nvvm\bin). First toolkit found wins.
def _engine_env() -> dict:
    env = dict(os.environ)
    root = Path(r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA")
    if not env.get("CUDA_PATH") and root.is_dir():
        kits = sorted((p for p in root.iterdir() if p.is_dir()), reverse=True)
        for kit in kits:
            if (kit / "nvvm" / "bin").is_dir():
                env["CUDA_PATH"] = str(kit)
                env["PATH"] = os.pathsep.join(
                    [str(kit / "nvvm" / "bin"), str(kit / "bin"), env.get("PATH", "")]
                )
                break
    return env


class BridgeError(RuntimeError):
    pass


def _send(proc, payload: dict) -> None:
    proc.stdin.write(json.dumps(payload) + "\n")
    proc.stdin.flush()


def _recv(proc, want_id, timeout: float) -> dict:
    import time

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        line = proc.stdout.readline()
        if not line:
            raise BridgeError("engine server closed stdout (crashed?) -- see stderr below")
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue  # not ours; a stray print
        if msg.get("id") == want_id:
            return msg
        # else: a notification/log frame -- skip
    raise BridgeError(f"timed out waiting for response id={want_id}")


def call(tool: str, arguments: dict, timeout: float) -> str:
    proc = subprocess.Popen(
        [ENGINE_PYTHON, str(SERVER)],
        cwd=str(REPO),
        env=_engine_env(),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    try:
        _send(proc, {
            "jsonrpc": "2.0", "id": 0, "method": "initialize",
            "params": {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "kimi-work-bridge", "version": "0.1.0"},
            },
        })
        init = _recv(proc, 0, timeout)
        if "error" in init:
            raise BridgeError(f"initialize refused: {init['error']}")
        _send(proc, {"jsonrpc": "2.0", "method": "notifications/initialized"})

        _send(proc, {
            "jsonrpc": "2.0", "id": 1, "method": "tools/call",
            "params": {"name": tool, "arguments": arguments},
        })
        resp = _recv(proc, 1, timeout)
        if "error" in resp:
            raise BridgeError(f"{tool} error: {resp['error']}")
        result = resp.get("result", {})
        if result.get("isError"):
            texts = [c.get("text", "") for c in result.get("content", [])]
            raise BridgeError(f"{tool} refused:\n" + "\n".join(texts))
        return "\n".join(c.get("text", "") for c in result.get("content", []))
    finally:
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except Exception:
            proc.kill()
        if proc.returncode not in (0, None) and proc.returncode is not None:
            err = proc.stderr.read() if proc.stderr else ""
            if err.strip():
                print(f"[server stderr]\n{err.strip()[-3000:]}", file=sys.stderr)


def list_tools(timeout: float) -> str:
    proc = subprocess.Popen(
        [ENGINE_PYTHON, str(SERVER)],
        cwd=str(REPO),
        env=_engine_env(),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    try:
        _send(proc, {
            "jsonrpc": "2.0", "id": 0, "method": "initialize",
            "params": {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "kimi-work-bridge", "version": "0.1.0"},
            },
        })
        _recv(proc, 0, timeout)
        _send(proc, {"jsonrpc": "2.0", "method": "notifications/initialized"})
        _send(proc, {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
        resp = _recv(proc, 2, timeout)
        tools = resp.get("result", {}).get("tools", [])
        return "\n".join(f"- {t['name']}: {t.get('description', '').splitlines()[0]}" for t in tools)
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    tool = argv[1]
    timeout = 120.0
    args: dict = {}
    it = iter(argv[2:])
    for flag in it:
        if flag == "--timeout":
            timeout = float(next(it))
            continue
        if not flag.startswith("--"):
            print(f"unexpected argument: {flag}", file=sys.stderr)
            return 2
        key = flag[2:]
        raw = next(it)
        try:
            args[key] = json.loads(raw)
        except json.JSONDecodeError:
            args[key] = raw
    try:
        out = list_tools(timeout) if tool == "list" else call(tool, args, timeout)
    except BridgeError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
