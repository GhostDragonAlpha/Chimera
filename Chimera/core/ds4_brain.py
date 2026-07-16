"""
ds4_brain — THE DEEP BACKGROUND BRAIN (DwarfStar / DeepSeek-V4-Flash, CPU).

Why (2026-07-15, measured live): the 4090 (24 GB) is too small to run the 80 GB
DeepSeek-V4 model fast, and WSL2 cannot page-lock host memory — so the CUDA path
crawls at ~0.8 t/s AND monopolizes VRAM (it OOM'd and crashed next to Unreal).
The CPU path keeps the whole model in the 128 GB of RAM, touches ZERO VRAM (so it
coexists with Unreal on the GPU + LM Studio floating GPU/RAM), and is ~2x FASTER
(1.64 t/s). Counter-intuitive but correct for this exact hardware: when the GPU is
smaller than the model and a virtualization layer throttles PCIe, everything-in-RAM
on the CPU wins.

ROLE IN THE WORKFLOW: ds4 is the studio's OPTIONAL, slow, DEEP, non-vision brain —
for reasoning where quality matters more than latency (nightly distillation,
research briefs, a heavy second opinion). LM Studio (fast, vision-capable) stays
the DEFAULT via `core.lm_gateway`, which is UNTOUCHED. This module is only the
studio-side control + client; nothing here changes the gateway or the gates.

  python -m core.ds4_brain serve    # start ds4-server --cpu in WSL (idempotent; ~80GB RAM while up)
  python -m core.ds4_brain stop     # kill it (frees the RAM)
  python -m core.ds4_brain status   # health: up? which model? latency?
  python -m core.ds4_brain ask "…"  # send one deep (slow) prompt, print the reply

Endpoint: CHIMERA_DS4_URL (default http://localhost:8000/v1 — WSL2 forwards the
WSL server's port to Windows localhost). RAM budget: ds4-CPU ~80 GB + LM Studio +
Unreal + Windows — stop ds4 when you need the RAM back.
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
# NB: `pkill -x ds4-server` matches the binary's exact process NAME, not the full
# command line — `pkill -f ds4-server` would also match THIS launcher bash (its
# argv contains "ds4-server") and kill itself before the server starts.
_START = (f"pkill -x ds4-server 2>/dev/null; sleep 1; cd ~/ds4 && "
          f"./ds4-server --cpu --ctx {_CTX} --host 0.0.0.0 --port 8000 "
          f"--kv-disk-dir /tmp/ds4-kv > ~/ds4-server.log 2>&1")


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
