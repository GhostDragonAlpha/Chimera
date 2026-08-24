#!/usr/bin/env python
"""uv_sheet.py -- TEST C, pre-registered in docs/THE_UV_METHOD.md.

  STATEMENT: SD 3.5 Medium (local, access granted) generates a seamless
  tileable plush-fur sheet at 1024px on the 4090 alongside the training load.
  PREDICTION: no OOM at fp16; edge-wrap mean|delta| < internal local std.
  FALSIFIER: OOM or wrap error above bound -> fp8/sequential, or DreamMat.
  The eye (does it read as fur) is the OPERATOR's call at link 5.

  .venv-gs/Scripts/python.exe -u tools/uv_sheet.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

OUT = Path("models/materials")
SIZE = 1024
PROMPT = ("seamless tileable texture swatch of dark brown teddy bear plush "
          "fur, flat top-down fabric sample, dense short fibers, uniform "
          "diffuse lighting, no shadows, no highlights, no seams, edge-to-edge "
          "repeating pattern, photorealistic material scan")
NEG = ("shadow, highlight, gradient, border, frame, seams, text, watermark, "
       "object, toy, face, perspective")


def tileability(img: np.ndarray) -> tuple[float, float]:
    """wrap_err = mean |delta| across the tile boundary (both axes);
    internal = mean |delta| between adjacent pixels in the interior."""
    f = img.astype(np.float64) / 255.0
    wrap = 0.5 * (np.abs(f[:, 0] - f[:, -1]).mean()
                  + np.abs(f[0, :] - f[-1, :]).mean())
    internal = 0.5 * (np.abs(f[:, 1:] - f[:, :-1]).mean()
                      + np.abs(f[1:, :] - f[:-1, :]).mean())
    return float(wrap), float(internal)


def seamless(img: np.ndarray, band: float = 0.10) -> np.ndarray:
    """TEST C3: offset + cosine cross-fade (make-seamless). Roll by half a
    tile so the cut lands at the image center, then cross-fade the original
    against the rolled copy with a weight that falls to zero at the borders
    -- the output's edges are the rolled image's INTERIOR on both sides, so
    the wrap is continuous by construction."""
    h, w = img.shape[:2]
    f = img.astype(np.float64)
    rolled = np.roll(np.roll(f, h // 2, axis=0), w // 2, axis=1)
    bx, by = int(w * band), int(h * band)
    wx = np.ones(w)
    wx[:bx] = 0.5 - 0.5 * np.cos(np.pi * np.arange(bx) / bx)   # 0 -> 1
    wx[-bx:] = 0.5 + 0.5 * np.cos(np.pi * np.arange(bx) / bx)  # 1 -> 0
    wy = np.ones(h)
    wy[:by] = 0.5 - 0.5 * np.cos(np.pi * np.arange(by) / by)
    wy[-by:] = 0.5 + 0.5 * np.cos(np.pi * np.arange(by) / by)
    w2 = np.outer(wy, wx)[..., None]
    return np.clip(f * w2 + rolled * (1 - w2), 0, 255).astype(np.uint8)


def make_circular(pipe) -> int:
    """TEST C2: flip every Conv2d in the denoiser + VAE decoder to circular
    padding so the sheet wraps by construction, not by prompt luck."""
    import torch.nn as nn
    n = 0
    for root in (pipe.transformer, pipe.vae):
        for m in root.modules():
            if isinstance(m, nn.Conv2d) and m.padding_mode == "zeros" \
                    and m.padding != (0, 0) and m.padding != 0:
                m.padding_mode = "circular"
                n += 1
    return n


def main() -> int:
    if "--seamless" in sys.argv:  # TEST C3: no GPU, deterministic
        from PIL import Image
        src = OUT / "fur_sd35_testc.png"      # the OPERATOR-APPROVED sheet
        a = np.asarray(Image.open(src).convert("RGB"))
        out = seamless(a)
        out_path = OUT / "fur_sd35_testc3.png"
        Image.fromarray(out).save(out_path)
        print(f"WROTE {out_path} (from {src})")
        wrap, internal = tileability(out)
        dm = np.abs(out.astype(np.float64) - a).mean(axis=(0, 1))
        ds = np.abs(out.astype(np.float64).std(axis=(0, 1))
                    - a.astype(np.float64).std(axis=(0, 1)))
        ok = wrap < internal and (dm < 2.0).all() and (ds < 2.0).all()
        print(f"tileability: wrap={wrap * 255:.2f}/255 internal="
              f"{internal * 255:.2f}/255 ratio={wrap / max(internal, 1e-9):.2f}"
              f"  stats drift: dmean=({dm[0]:.2f},{dm[1]:.2f},{dm[2]:.2f}) "
              f"dstd=({ds[0]:.2f},{ds[1]:.2f},{ds[2]:.2f}) (tol 2.00)  "
              f"{'PASS' if ok else 'FAIL (falsifier fired)'}")
        return 0 if ok else 1

    if "--seeds4" in sys.argv:  # TEST C4: parent process, one SUBPROCESS per
        # seed (the in-process loop hung twice at generation end -- under a
        # pegged-RAM machine, re-entering the pipeline in one process stalls;
        # single-shot processes are the proven path: TEST C and C2)
        import subprocess
        from PIL import Image
        sheets, ok_all = [], True
        for seed in (0, 1, 2, 3):
            out_path = OUT / f"fur_sd35_c4_s{seed}.png"
            try:
                subprocess.run(
                    [sys.executable, "-u", str(Path(__file__).resolve()),
                     "--seed", str(seed)],
                    timeout=600, check=False)
            except subprocess.TimeoutExpired:
                print(f"  seed={seed}  SUBPROCESS TIMEOUT (600s) -- killed, "
                      f"continuing with next seed")
            if not out_path.exists():
                print(f"  seed={seed}  no sheet produced")
                ok_all = False
                continue
            a = np.asarray(Image.open(out_path).convert("RGB"))
            wrap, internal = tileability(a)
            ok = wrap < internal
            ok_all &= ok
            sheets.append((seed, Image.open(out_path).resize((512, 512))))
            print(f"  seed={seed}  wrap={wrap * 255:.2f} internal="
                  f"{internal * 255:.2f} ratio={wrap / internal:.2f}  "
                  f"{'OK' if ok else 'FAIL'}  -> {out_path}")
        if sheets:
            contact = Image.new("RGB", (1024, 1024))
            for i, (_seed, s) in enumerate(sheets[:4]):
                contact.paste(s, ((i % 2) * 512, (i // 2) * 512))
            contact_path = OUT / "fur_sd35_c4_contact.png"
            contact.save(contact_path)
            print(f"WROTE {contact_path} (row-major by seed order)")
        print(f"TEST C4: {'PASS' if ok_all and len(sheets) == 4 else 'FAIL (falsifier fired)'}")
        return 0 if ok_all and len(sheets) == 4 else 1

    import torch
    from diffusers import StableDiffusion3Pipeline

    circular = "--circular" in sys.argv  # TEST C2
    seed_arg = None
    if "--seed" in sys.argv:             # TEST C4 worker
        seed_arg = int(sys.argv[sys.argv.index("--seed") + 1])
        circular = True
    print(f"torch {torch.__version__}, cuda={torch.cuda.is_available()}, "
          f"vram free ~{(torch.cuda.mem_get_info()[0] / 2**20):.0f} MiB")
    pipe = StableDiffusion3Pipeline.from_pretrained(
        "stabilityai/stable-diffusion-3.5-medium",
        torch_dtype=torch.float16)
    if circular:
        print(f"circular padding: flipped {make_circular(pipe)} conv layers")
    pipe.to("cuda")
    print(f"loaded; vram used "
          f"{(torch.cuda.memory_allocated() / 2**20):.0f} MiB")

    OUT.mkdir(parents=True, exist_ok=True)
    gen_kw = {}
    if seed_arg is not None:
        gen_kw["generator"] = torch.Generator("cuda").manual_seed(seed_arg)
    img = pipe(PROMPT, negative_prompt=NEG, width=SIZE, height=SIZE,
               num_inference_steps=28, guidance_scale=4.5, **gen_kw).images[0]
    if seed_arg is not None:
        out_path = OUT / f"fur_sd35_c4_s{seed_arg}.png"
    else:
        out_path = OUT / ("fur_sd35_testc2.png" if circular
                          else "fur_sd35_testc.png")
    img.save(out_path)
    print(f"WROTE {out_path}")

    a = np.asarray(img.convert("RGB"))
    wrap, internal = tileability(a)
    ok = wrap < internal
    print(f"tileability: edge-wrap mean|delta|={wrap * 255:.2f}/255  "
          f"internal local mean|delta|={internal * 255:.2f}/255  "
          f"ratio={wrap / max(internal, 1e-9):.2f}  "
          f"{'PASS' if ok else 'FAIL (falsifier fired: not seamless)'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
