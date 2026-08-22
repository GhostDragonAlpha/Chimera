"""d3_refine.py -- Lane D refinement round (operator-authorized 2026-08-20): DiffSplat SD1.5
text->3DGS, targeting the ONE flaw the eye named on laneD ("a photograph... except for the
nose") plus the d2 failures (stipple fur, dead eyes).

RULE-0 MEMBRANE (stated before the run, per THE_LAW):
  STATEMENT:  laneD's 20-step sde-dpmsolver++ sampling is draft-quality; 50 steps on
              face-detail-bound prompts yields a photographic face without breaking structure.
  PREDICTION: >=1 candidate earns eye Verdict: YES (photoreal) with structure >= 0.6.
  FALSIFIER:  all candidates Verdict: NO -> SD1.5 latent capacity is the ceiling; escalate
              to the SD3.5m backbone (gsdiff_gobj83k_sd35m) instead of more sd15 sweeps.

LEVERS CHANGED vs laneD/d2: num_inference_steps 20 -> 50; prompts bound to real toy
face materials (amber glass / shoe-button eyes, stitched fabric nose). Everything else
held at the mapped laneD recipe: elevation 10, distance 1.4, guidance 7.5 (one probe at
9.0), eta 1.0, half_precision, opacity_threshold_ply 0.0, then the proven conversion
(orient_splat --alpha-min 0.1 --lum-min 0.10 --no-envelope --density-k 3 --blob-keep).

Every command is logged to capture/genbear3/d3_commands.jsonl -- the original laneD
prompt was lost because the run was never logged; that failure mode ends here.

Usage:  .venv-gs/Scripts/python.exe tools/d3_refine.py
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
LOG = ROOT / "capture" / "genbear3" / "d3_commands.jsonl"

PROMPTS = {
    # r0: reconstruction attempt of the lost original laneD prompt (eye: "vintage, worn fur")
    "r0_vintage": "a vintage teddy bear, worn soft brown plush fur, seated, dark background",
    # r1/r2: the two d2 prompts that held structure 1.0, now at 50 steps
    "r1_tan_glass": ("a seated classic teddy bear, warm tan plush fur, soft bright lighting, "
                     "embroidered nose with stitching, round glass button eyes with white "
                     "highlights, dark background"),
    "r2_golden_emb": ("a seated classic light golden brown teddy bear, soft plush fur, bright "
                      "soft studio lighting, detailed embroidered fabric nose with visible "
                      "stitching, realistic glass button eyes with highlights, dark background"),
    # r3: new -- darker fur + amber glass eyes reads more photographic in sd15 latents
    "r3_choc_amber": ("a seated classic teddy bear, dark chocolate brown plush fur, amber glass "
                      "eyes, stitched brown fabric nose, soft studio lighting, dark background"),
}

SEEDS = [0, 7]
STEPS = 50


def run(tag: str, prompt: str, seed: int, guidance: float = 7.5) -> None:
    ply_path = ROOT / "models" / "genbear3" / f"d3_{tag}_s{seed}.ply"
    cmd = [PYTHON, "infer_sd15_ply_only.py",
           "--config_file", "configs/gsdiff_sd15.yaml",
           "--tag", "gsdiff_gobj83k_sd15__render",
           "--prompt", prompt,
           "--ply_path", str(ply_path),
           "--gpu_id", "0",
           "--seed", str(seed),
           "--num_inference_steps", str(STEPS),
           "--guidance_scale", str(guidance),
           "--half_precision"]
    rec = {"tag": f"d3_{tag}_s{seed}", "prompt": prompt, "seed": seed,
           "steps": STEPS, "guidance": guidance, "cmd": cmd,
           "started": time.strftime("%H:%M:%S")}
    print(f"\n=== d3_{tag}_s{seed} (steps={STEPS}, cfg={guidance}) ===", flush=True)
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
    # one guidance probe on the strongest structure prompt
    run("r1_tan_glass_cfg9", PROMPTS["r1_tan_glass"], 0, guidance=9.0)
    print("\nD3 round complete.", flush=True)


if __name__ == "__main__":
    main()
