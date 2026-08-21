"""preview_corpus.py -- render a contact sheet of corpus patches through the REAL viewer.

The human (and the AI) must SEE the patches before any eye time or training is
spent: a ring/crescent/strip window means the cut is wrong, and no qualification
pass can fix a wrong cut. Native-scale presentation (qualify_corpus' lesson):
the window is shown at ~1 px per splat footprint, then cropped and upscaled.

  .venv-gs/Scripts/python.exe tools/preview_corpus.py \
      --corpus fur=models/littlebear/corpus/fur.npz \
               sweater=models/littlebear/corpus/sweater.npz \
      --half 0.025 --n 8 --out .tmp/preview/patches_sheet.png
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "ChimeraEngine"))

VIEWER_R = 0.2           # viewer.html clamps OrbitControls to >= 0.2 m
NATIVE_AT_HALF_005 = 150.0  # px a 0.05 half-window spans at r=0.2 (eye-verified)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--corpus", nargs="+", required=True,
                    help="label=path.npz pairs, columns laid out in order")
    ap.add_argument("--half", type=float, default=0.05,
                    help="half-window the corpus was cut with (cut_patches --half)")
    ap.add_argument("--n", type=int, default=8, help="samples per corpus")
    ap.add_argument("--workdir", default=".tmp/preview")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    from qualify_corpus import patch_buffer
    import cpp_bridge as cb

    work = Path(a.workdir)
    work.mkdir(parents=True, exist_ok=True)
    qdir = ROOT / "models/triposplat/static/viewer/_qualify"
    qdir.mkdir(parents=True, exist_ok=True)

    names, labels = [], []
    k = 0
    for spec in a.corpus:
        label, _, cpath = spec.partition("=")
        P = np.load(cpath)["patches"]
        for i in np.linspace(0, len(P) - 1, min(a.n, len(P))).astype(int):
            buf = patch_buffer(P[i]).astype(np.float32)
            buf[:, 0:3] -= buf[:, 0:3].mean(0)
            name = f"prev{k:03d}"
            cb.save_splat(str(qdir / f"{name}.splat"), buf)
            names.append(name)
            labels.append(label)
            k += 1
    (work / "manifest.json").write_text(json.dumps(names))

    r = subprocess.run(["node", str(ROOT / "tools/qualify_shots.js"),
                        str(work.resolve()), str(VIEWER_R)], cwd=str(ROOT))
    if r.returncode != 0:
        raise SystemExit("FAILED: qualify_shots.js")

    native_px = NATIVE_AT_HALF_005 * (a.half / 0.05)
    cw = int(native_px / 2 * 1.15)
    tw = th = 320
    cols = 6
    rows = (len(names) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * tw, rows * th), (12, 12, 18))
    dr = ImageDraw.Draw(sheet)
    for k, (name, label) in enumerate(zip(names, labels)):
        img = Image.open(work / f"{name}.png")
        img = img.crop((320 - cw, 180 - cw, 320 + cw, 180 + cw))
        img = img.resize((tw, th), Image.LANCZOS)
        sheet.paste(img, ((k % cols) * tw, (k // cols) * th))
        dr.text(((k % cols) * tw + 4, (k // cols) * th + 4), f"{label} {k}",
                fill=(255, 255, 120))
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    sheet.save(a.out)
    print(f"{len(names)} patches -> {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
