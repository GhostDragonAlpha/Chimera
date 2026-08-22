#!/usr/bin/env python3
"""Lane C: local LTX-Video I2V orbit generation for genbear3 anchor."""
import os
import sys
import argparse
import numpy as np
import torch
from PIL import Image
from diffusers import LTXImageToVideoPipeline

PROMPT = (
    "locked camera orbits slowly and smoothly around a frozen teddy bear, 360 degrees, "
    "camera rises over the top and dips below, fixed studio lighting, no object motion, "
    "single continuous shot, dark background"
)
NEGATIVE_PROMPT = (
    "object moving, deforming, morphing, multiple shots, cuts, zoom, pan, background change, "
    "flickering light, blurry, noisy"
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", default="capture/genbear3/anchor_03.png")
    parser.add_argument("--out", default="capture/genbear3/laneC_ltx.mp4")
    parser.add_argument("--width", type=int, default=768)
    parser.add_argument("--height", type=int, default=512)
    parser.add_argument("--num-frames", type=int, default=241)
    parser.add_argument("--frame-rate", type=int, default=24)
    parser.add_argument("--steps", type=int, default=30)
    parser.add_argument("--guidance", type=float, default=3.0)
    parser.add_argument("--model", default="Lightricks/LTX-Video")
    parser.add_argument("--dtype", default="fp16")
    args = parser.parse_args()

    dtype = torch.float16 if args.dtype == "fp16" else torch.bfloat16
    print(f"Loading {args.model} on cuda with {dtype} ...", flush=True)
    pipe = LTXImageToVideoPipeline.from_pretrained(
        args.model,
        torch_dtype=dtype,
    )
    pipe = pipe.to("cuda")
    # Memory mitigations: model CPU offload + attention slicing if available
    if hasattr(pipe, "enable_model_cpu_offload"):
        pipe.enable_model_cpu_offload()
    if hasattr(pipe, "set_attention_slice"):
        pipe.set_attention_slice(1)
    print("Pipeline ready.", flush=True)

    img = Image.open(args.image).convert("RGB")
    # Resize preserving aspect by center crop to the target aspect, then resize
    target_aspect = args.width / args.height
    src_w, src_h = img.size
    src_aspect = src_w / src_h
    if src_aspect > target_aspect:
        new_w = int(src_h * target_aspect)
        left = (src_w - new_w) // 2
        img = img.crop((left, 0, left + new_w, src_h))
    else:
        new_h = int(src_w / target_aspect)
        top = (src_h - new_h) // 2
        img = img.crop((0, top, src_w, top + new_h))
    img = img.resize((args.width, args.height), Image.LANCZOS)
    print(f"Input image resized to {img.size}", flush=True)

    print(f"Generating {args.num_frames} frames @ {args.frame_rate} fps ({args.num_frames/args.frame_rate:.2f}s) ...", flush=True)
    generator = torch.Generator("cuda").manual_seed(42)
    result = pipe(
        image=img,
        prompt=PROMPT,
        negative_prompt=NEGATIVE_PROMPT,
        width=args.width,
        height=args.height,
        num_frames=args.num_frames,
        frame_rate=args.frame_rate,
        num_inference_steps=args.steps,
        guidance_scale=args.guidance,
        generator=generator,
        output_type="pil",
    ).frames[0]

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    print(f"Saving {len(result)} frames to {args.out} ...", flush=True)
    import imageio
    writer = imageio.get_writer(args.out, fps=args.frame_rate, codec="libx264", quality=8.0)
    for frame in result:
        writer.append_data(np.asarray(frame))
    writer.close()
    print(f"Done: {args.out}", flush=True)


if __name__ == "__main__":
    main()
