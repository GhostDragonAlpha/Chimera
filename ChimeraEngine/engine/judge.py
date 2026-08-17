# Chimera JUDGE — the visual/physics critique endpoint, one shared module.
#
# The project's two-score system (P physics / V visual, 0-100 each) is judged
# by a LOCAL vision model — never a cloud API. Backend order:
#   1. Ollama   http://localhost:11434/v1  model qwen3.8  (default; also the
#      VS Code Copilot "Ollama" provider — one install serves both)
#   2. LM Studio http://localhost:1234/v1  (legacy fallback)
# Override with env CHIMERA_JUDGE_API / CHIMERA_JUDGE_MODEL.
#
# Usage:
#   from judge import judge
#   verdict = judge("Is this recognizably a teddy bear? Score 0-100.",
#                   ["render_a.png", "render_b.png"])
# CLI:
#   python judge.py "question" img1.png [img2.png ...]
#
# Both backends speak the OpenAI chat-completions wire format; images ride as
# base64 data URLs. Stdlib only. Stdout is UTF-8 safe on Windows.
import base64
import json
import os
import sys
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BACKENDS = [
    ("ollama", "http://localhost:11434/v1/chat/completions", "qwen3.8"),
    ("lmstudio", "http://localhost:1234/v1/chat/completions",
     "bartowski/qwen3.8-27b"),
]
TIMEOUT = 900  # local 17-27B vision models on one GPU: minutes, not seconds


def _alive(url: str) -> bool:
    base = url.split("/v1/")[0]
    try:
        urllib.request.urlopen(base + "/api/version"
                               if "11434" in base else base + "/v1/models",
                               timeout=3)
        return True
    except Exception:
        return False


def pick_backend():
    api = os.environ.get("CHIMERA_JUDGE_API")
    model = os.environ.get("CHIMERA_JUDGE_MODEL")
    if api and model:
        return "env", api, model
    for name, url, m in BACKENDS:
        if _alive(url):
            return name, url, m
    raise RuntimeError(
        "JUDGE OFFLINE: neither Ollama (:11434) nor LM Studio (:1234) "
        "answers. Start one: `ollama serve` (or the Ollama tray app).")


def judge(question: str, images=(), model=None, temperature=0.2,
          max_tokens=4096) -> str:
    name, api, default_model = pick_backend()
    parts = [{"type": "text", "text": question}]
    for f in images:
        b = base64.b64encode(Path(f).read_bytes()).decode()
        parts.append({"type": "image_url",
                      "image_url": {"url": f"data:image/png;base64,{b}"}})
    body = {"model": model or default_model,
            "messages": [{"role": "user", "content": parts}],
            "temperature": temperature, "max_tokens": max_tokens}
    req = urllib.request.Request(api, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=TIMEOUT))
    msg = r["choices"][0]["message"]
    out = msg.get("content") or msg.get("reasoning_content") or ""
    return f"[judge:{name}] {out}"


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    print(judge(sys.argv[1], sys.argv[2:]))
