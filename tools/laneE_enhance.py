"""tools/laneE_enhance.py

Enhance the Lane E view grid with SDXL img2img at low denoise, same seed for every view,
to transfer photographic fur/face detail onto the closed DiffSplat geometry.

Runs in .venv-gs (diffusers + torch CUDA).
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from diffusers import StableDiffusionXLImg2ImgPipeline

PROMPT = (
    "professional studio photograph of a plush teddy bear, individual fur strands, "
    "embroidered fabric nose with visible stitching, glass button eyes, "
    "soft studio lighting, dark background"
)
NEG_PROMPT = "cartoon, plastic, smooth blob, deformed, text, watermark, words, letters, signature, caption"
MODEL_ID = "stabilityai/stable-diffusion-xl-base-1.0"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in-dir", default="capture/genbear3/laneE_views")
    ap.add_argument("--out-dir", default="capture/genbear3/laneE_views_enhanced")
    ap.add_argument("--strength", type=float, default=0.40)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--steps", type=int, default=30)
    ap.add_argument("--guidance", type=float, default=7.5)
    args = ap.parse_args()

    in_dir = Path(args.in_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    meta = json.loads((in_dir / "laneE_views.json").read_text())

    print("loading SDXL img2img pipeline...")
    pipe = StableDiffusionXLImg2ImgPipeline.from_pretrained(
        MODEL_ID,
        torch_dtype=torch.float16,
        variant="fp16",
        use_safetensors=True,
    ).to("cuda")

    print(f"enhancing {len(meta)} views  strength={args.strength}  seed={args.seed}  steps={args.steps}")
    for i, m in enumerate(meta):
        src = in_dir / m["file"]
        dst = out_dir / m["file"]
        img = Image.open(src).convert("RGB")

        generator = torch.Generator(device="cuda").manual_seed(args.seed)
        attempt = 0
        while True:
            try:
                result = pipe(
                    prompt=PROMPT,
                    negative_prompt=NEG_PROMPT,
                    image=img,
                    strength=args.strength,
                    num_inference_steps=args.steps,
                    guidance_scale=args.guidance,
                    generator=generator,
                ).images[0]
                break
            except torch.cuda.OutOfMemoryError as e:
                attempt += 1
                print(f"OOM on view {i} attempt {attempt}; waiting 60s...")
                torch.cuda.empty_cache()
                time.sleep(60)
                if attempt >= 3:
                    raise

        result.save(dst)
        print(f"[{i+1}/{len(meta)}] {dst}")

    (out_dir / "laneE_enhance_params.json").write_text(json.dumps({
        "model": MODEL_ID,
        "prompt": PROMPT,
        "negative_prompt": NEG_PROMPT,
        "strength": args.strength,
        "seed": args.seed,
        "num_inference_steps": args.steps,
        "guidance_scale": args.guidance,
        "n_views": len(meta),
    }, indent=2))
    print(f"params saved to {out_dir / 'laneE_enhance_params.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
