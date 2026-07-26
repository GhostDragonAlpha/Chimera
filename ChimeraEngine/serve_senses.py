"""serve_senses.py -- launch the DYAD's SENSES server: the Omni model (eye + ear + movie) on llama-server.

    python ChimeraEngine/serve_senses.py         # serves 127.0.0.1:1235 until Ctrl+C

Why not LM Studio: LM Studio loads an omni model's mmproj for VISION only and never wires the audio tower,
so it can SEE but not HEAR. Running llama.cpp's server directly makes it print `init_audio` and wire the
ear. The model goes on the GPU, the ~5.3 GB projector on CPU (`--no-mmproj-offload`) so it fits alongside
whatever else is loaded. `senses.py` (and thus human_messenger + sound_messenger) read from here.

MEASURED CAVEAT (2026-07-25): llama.cpp audio is "experimental" and the ear is UNRELIABLE -- it hallucinated
a high-pitched component in a signal measured 100% below 170 Hz. It is an ADVISORY second opinion only; the
operator is the authoritative ear. (Vision is solid: it read the marble and scored the dyad ~0.8.)
"""
import glob
import os
import subprocess
import sys
from pathlib import Path

LM = Path.home() / ".lmstudio"


def _newest(pattern: str):
    hits = glob.glob(pattern)
    return max(hits, key=os.path.getmtime) if hits else None


def main() -> int:
    server = _newest(str(LM / "extensions" / "backends" / "llama.cpp-win-*cuda*" / "llama-server.exe"))
    mdir = LM / "models" / "unsloth" / "Qwen2.5-Omni-7B-GGUF"
    model, mmproj = mdir / "Qwen2.5-Omni-7B-Q4_K_M.gguf", mdir / "mmproj-F32.gguf"
    for p, label in [(server, "llama-server.exe"), (model, "omni model GGUF"), (mmproj, "mmproj-F32")]:
        if not p or not Path(p).exists():
            sys.exit(f"[serve_senses] missing {label}: {p}\n  (adjust the paths in this script for your setup)")
    cmd = [str(server), "-m", str(model), "--mmproj", str(mmproj), "--no-mmproj-offload",
           "-ngl", "99", "--host", "127.0.0.1", "--port", "1235", "-c", "4096"]
    print("[serve_senses] launching the Omni senses server (eye + ear + movie):")
    print("  " + " ".join(f'"{c}"' if " " in c else c for c in cmd))
    print("  -> http://127.0.0.1:1235   (CHIMERA_SENSES_URL to point senses.py elsewhere)")
    return subprocess.run(cmd).returncode


if __name__ == "__main__":
    raise SystemExit(main())
