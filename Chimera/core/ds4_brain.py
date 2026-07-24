"""
ds4_brain — SUPERSEDED (2026-07-19). Replaced by dynamic model swapping
through LM Studio. See core/council.py.

Kept as a backwards-compatible stub; features merged into `core.council`.
The Council now swaps between fast (MoE, 3.6B active) and deep (dense 27B)
models on-demand on the GPU — no more 80GB RAM overhead.

This module still works if you need the old server.
"""
import json
import os
import subprocess
import sys
import time
import urllib.request

ENDPOINT = os.environ.get("CHIMERA_DS4_URL", "http://localhost:8000/v1").rstrip("/")
WSL_DISTRO = os.environ.get("CHIMERA_DS4_WSL_DISTRO", "Ubuntu")
_CTX = os.environ.get("CHIMERA_DS4_CTX", "32768")
# Thread count: measured sweep on the i9-13900K (8 P + 16 E = 24 physical cores)
# 2026-07-15 — gen 8t=1.64, 16t=2.04, 24t=2.08, 32t=2.02 t/s; prefill 24t=2.83
# (2.4x the default). 24 (all physical cores) wins; 32 regresses (the 8 HT siblings
# contend on the P-cores). Without --threads ds4 used only ~4-8 cores (82% idle).
_THREADS = os.environ.get("CHIMERA_DS4_THREADS", "24")
# NB: `pkill -x ds4-server` matches the binary's exact process NAME, not the full
# command line — `pkill -f ds4-server` would also match THIS launcher bash (its
# argv contains "ds4-server") and kill itself before the server starts.
_START = (f"pkill -x ds4-server 2>/dev/null; sleep 1; cd ~/ds4 && "
          f"./ds4-server --cpu --threads {_THREADS} --ctx {_CTX} "
          # bind-public: this runs INSIDE WSL2, which has its own network namespace, so
          # 0.0.0.0 is how the Windows side reaches it at all. The exposure is bounded by
          # WSL2's virtual switch rather than by the LAN. Flagged rather than silently
          # allowed, per core/bind_guard.py -- and note this whole module is SUPERSEDED by
          # core/council.py and kept only as a backwards-compatible stub.
          f"--host 0.0.0.0 --port 8000 --kv-disk-dir /tmp/ds4-kv "
          f"> ~/ds4-server.log 2>&1")


def _content(data) -> str:
    """Prefer a clean final `content`; fall back to `reasoning_content`/`reasoning`
    — DeepSeek-V4 (like qwen-agentworld) keeps its real output in the reasoning
    channel and can leave `content` empty under a tight token budget."""
    msg = data["choices"][0]["message"]
    for k in ("content", "reasoning_content", "reasoning"):
        v = (msg.get(k) or "").strip()
        if v:
            return v
    return ""


def health(timeout: float = 6.0) -> dict:
    """(up?, model, latency). Never raises — a down brain is a normal state."""
    t0 = time.time()
    try:
        with urllib.request.urlopen(ENDPOINT + "/models", timeout=timeout) as r:
            data = json.loads(r.read().decode("utf-8", "replace"))
        model = (data.get("data") or [{}])[0].get("id", "?")
        return {"up": True, "model": model,
                "latency_ms": int((time.time() - t0) * 1000), "endpoint": ENDPOINT}
    except Exception as e:
        return {"up": False, "error": str(e)[:120], "endpoint": ENDPOINT}


def ask(prompt: str, system: str = None, max_tokens: int = 512,
        temperature: float = 0.0, timeout: float = 1800.0) -> str:
    """One deep completion. SLOW (~1.6 t/s) — for non-interactive reasoning only."""
    msgs = ([{"role": "system", "content": system}] if system else []) + \
           [{"role": "user", "content": prompt}]
    body = {"messages": msgs, "max_tokens": max_tokens,
            "temperature": temperature, "stream": False}
    req = urllib.request.Request(
        ENDPOINT + "/chat/completions", data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = json.loads(r.read().decode("utf-8", "replace"))
    return _content(data)


def chat(messages: list, max_tokens: int = 512, temperature: float = 0.3,
         timeout: float = 3600.0) -> str:
    """Like ask() but takes a full OpenAI messages list — for multi-turn dialogue
    (e.g. core.council). SLOW (~1.6 t/s); give reasoning room via max_tokens."""
    body = {"messages": messages, "max_tokens": max_tokens,
            "temperature": temperature, "stream": False}
    req = urllib.request.Request(
        ENDPOINT + "/chat/completions", data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = json.loads(r.read().decode("utf-8", "replace"))
    return _content(data)


def serve() -> str:
    """Start the CPU server in WSL if it isn't already up (detached, survives us)."""
    h = health(timeout=3)
    if h["up"]:
        return f"already up ({h['model']}, {h['latency_ms']}ms) at {ENDPOINT}"
    flags = 0
    if os.name == "nt":
        flags = getattr(subprocess, "DETACHED_PROCESS", 0x08) | \
                getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0x200)
    subprocess.Popen(["wsl", "-d", WSL_DISTRO, "--", "bash", "-lc", _START],
                     creationflags=flags, stdin=subprocess.DEVNULL,
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return ("starting ds4-server --cpu (loading ~80GB into RAM, ~30-60s). "
            "check: python -m core.ds4_brain status")


def stop() -> str:
    subprocess.run(["wsl", "-d", WSL_DISTRO, "--", "bash", "-lc", "pkill -x ds4-server"],
                   stdin=subprocess.DEVNULL,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return "stop signal sent to ds4-server (RAM freed once it exits)"


def pulse() -> str:
    """One-line status for preflight / CAPCOM."""
    h = health(timeout=4)
    if h["up"]:
        return (f"[ds4] deep brain ONLINE — {h['model']} on CPU (~1.6 t/s, 0 VRAM) "
                f"at {ENDPOINT}; slow/deep/non-vision only, LM Studio stays default")
    return ("[ds4] deep brain offline (start: python -m core.ds4_brain serve; "
            "optional heavy brain, LM Studio is the default)")


def main(argv=None):
    import argparse
    p = argparse.ArgumentParser(prog="ds4_brain", description=__doc__.split("\n")[1])
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("serve"); sub.add_parser("stop")
    sub.add_parser("status"); sub.add_parser("pulse")
    pa = sub.add_parser("ask"); pa.add_argument("prompt")
    pa.add_argument("--system", default=None)
    pa.add_argument("--max-tokens", type=int, default=512)
    a = p.parse_args(argv)
    if a.cmd == "serve":
        print(serve())
    elif a.cmd == "stop":
        print(stop())
    elif a.cmd == "pulse":
        print(pulse())
    elif a.cmd == "status":
        h = health()
        print(json.dumps(h, indent=2))
        if h["up"]:
            print("role: OPTIONAL deep/slow/non-vision brain; LM Studio (lm_gateway) is the default.")
    elif a.cmd == "ask":
        t0 = time.time()
        out = ask(a.prompt, system=a.system, max_tokens=a.max_tokens)
        print(out)
        print(f"\n[{time.time()-t0:.0f}s]", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
