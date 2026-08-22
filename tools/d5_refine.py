"""d5_refine.py -- Lane D5: DiffSplat SD3.5-medium sweep (operator-unlocked 2026-08-20).

RULE-0 MEMBRANE:
  STATEMENT:  SD1.5's CLIP encoder could not bind face-detail prompts (D3 falsifier);
              SD3.5m's T5-XXL encoder can, and its transformer renders finer latents.
  PREDICTION: >=1 candidate earns eye Verdict: YES (photoreal) with structure >= 0.6.
  FALSIFIER:  all candidates Verdict: NO -> the 256px 4-view DiffSplat architecture
              itself is the ceiling, not the backbone; stop DiffSplat entirely.

Held at official SD3.5m defaults (infer_gsdiff_sd3.py): flow scheduler, 28 steps,
guidance 5.0, elevation 10, distance 1.4, half precision. Same prompts as D3 for
comparability, seeds {0,7}. Every command logged to capture/genbear3/d5_commands.jsonl.

Usage:  .venv-gs/Scripts/python.exe tools/d5_refine.py
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path("E:/PythonChimera")
DIFFSPLAT = ROOT / "external" / "diffsplat"
PYTHON = str(ROOT / ".venv-gs" / "Scripts" / "python.exe")
LOG = ROOT / "capture" / "genbear3" / "d5_commands.jsonl"

PROMPTS = {
    "r0_vintage": "a vintage teddy bear, worn soft brown plush fur, seated, dark background",
    "r1_tan_glass": ("a seated classic teddy bear, warm tan plush fur, soft bright lighting, "
                     "embroidered nose with stitching, round glass button eyes with white "
                     "highlights, dark background"),
    "r2_golden_emb": ("a seated classic light golden brown teddy bear, soft plush fur, bright "
                      "soft studio lighting, detailed embroidered fabric nose with visible "
                      "stitching, realistic glass button eyes with highlights, dark background"),
    "r3_choc_amber": ("a seated classic teddy bear, dark chocolate brown plush fur, amber glass "
                      "eyes, stitched brown fabric nose, soft studio lighting, dark background"),
}

SEEDS = [0, 7]


def run(tag: str, prompt: str, seed: int) -> None:
    ply_path = ROOT / "models" / "genbear3" / f"d5_{tag}_s{seed}.ply"
    cmd = [PYTHON, "infer_sd35m_ply_only.py",
           "--config_file", "configs/gsdiff_sd35m_80g.yaml",
           "--tag", "gsdiff_gobj83k_sd35m__render",
           "--prompt", prompt,
           "--ply_path", str(ply_path),
           "--gpu_id", "0",
           "--seed", str(seed),
           "--half_precision"]
    rec = {"tag": f"d5_{tag}_s{seed}", "prompt": prompt, "seed": seed,
           "steps": 28, "guidance": 5.0, "cmd": cmd,
           "started": time.strftime("%H:%M:%S")}
    print(f"\n=== d5_{tag}_s{seed} ===", flush=True)
    t0 = time.time()
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=DIFFSPLAT)
    rec["elapsed_s"] = round(time.time() - t0, 1)
    rec["returncode"] = r.returncode
    rec["stdout_tail"] = r.stdout[-600:]
    if r.returncode != 0:
        rec["stderr_tail"] = r.stderr[-900:]
        print(f"FAILED: {r.stderr[-300:]}", flush=True)
    else:
        print(f"ok ({rec['elapsed_s']}s) -> {ply_path.name}", flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")


def main() -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    for tag, prompt in PROMPTS.items():
        for seed in SEEDS:
            run(tag, prompt, seed)
    print("\nD5 round complete.", flush=True)


if __name__ == "__main__":
    main()
