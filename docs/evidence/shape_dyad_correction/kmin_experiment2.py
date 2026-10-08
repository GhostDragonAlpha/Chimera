"""k_min experiment 2 — the splat-size axis.

Experiment 1 falsified the crop-only law: at 3.0 px/cell (sigma = 1 cell pitch) the eye
reads smooth. Mechanism: sigma = pitch merges neighboring cells. Splat extent is NOT
claimed matter (numbers.json: 'splat_extent: point-center convention'), so sigma is a
presentation dial owned by the eye path. Physics emit() stays verbatim; the buffer's
SIZE column is scaled IN THE EYE PATH after emit, and the transform is recorded.

Grid: sigma_frac x crop margin -> one eye call per rendered image.
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image

_HERE = Path(__file__).resolve().parent
_CE = _HERE.parents[1]
sys.path.insert(0, str(_CE))

import cpp_bridge
import splat_appearance as sa
import senses

cpp_bridge.ENGINE_URL = "http://127.0.0.1:8091"
OUT = _HERE
EVIDENCE = _CE.parent / "docs" / "evidence" / "shape_dyad_correction"
EVIDENCE.mkdir(parents=True, exist_ok=True)

QUESTION = ("Describe the surface of the object in this image. Is its surface smooth, "
            "or does it show a repeating fine structure? If it shows repeating structure, "
            "name its shape. Answer in 1-3 sentences.")

CPP_SIZE = 20          # buffer column for splat sigma (28-col grain layout)


def subject_box(gray, thr_frac=0.35):
    thr = gray.max() * thr_frac
    ys, xs = np.where(gray > thr)
    return xs.min(), ys.min(), xs.max(), ys.max()


def render_variant(sigma_frac, margin, tag):
    """emit(0) verbatim, SIZE scaled in the eye path, engine render, crop, 384px."""
    buf = sa.membrane_buffer("theShape", 0.0)
    assert buf is not None
    n_body = None
    # ground grains are the tail (900 rows, TYPE also 3) — scale only sigma globally:
    # the ground is presentation too, but keep its size as emitted (identify by size value)
    s_cell = float(np.median(buf[:, CPP_SIZE]))          # body cells carry sigma = s
    ground_mask = buf[:, CPP_SIZE] > (s_cell * 1.5)      # ground grains: r_xy*0.06 >> s
    buf2 = buf.copy()
    buf2[~ground_mask, CPP_SIZE] = buf2[~ground_mask, CPP_SIZE] * sigma_frac
    ext = float(np.linalg.norm(buf2[:, 0:3], axis=1).max()) or 1.0
    cam = (0.0, -2.7 * ext, 0.72 * ext)
    assert cpp_bridge.load_membrane("theShape", buf2, cam)
    time.sleep(0.6)
    raw = cpp_bridge.fetch_frame()
    full = OUT / f"v2_{tag}_full.png"
    full.write_bytes(raw)
    rgb = np.asarray(Image.open(full).convert("RGB"))
    gray = rgb.mean(axis=2)
    x0, y0, x1, y1 = subject_box(gray)
    w, h = x1 - x0 + 1, y1 - y0 + 1
    mx, my = int(w * margin), int(h * margin)
    cx0, cy0 = max(0, x0 - mx), max(0, y0 - my)
    cx1, cy1 = min(rgb.shape[1] - 1, x1 + mx), min(rgb.shape[0] - 1, y1 + my)
    crop = Image.fromarray(rgb[cy0:cy1 + 1, cx0:cx1 + 1])
    small = crop.resize((384, round(crop.height * 384 / crop.width)), Image.LANCZOS)
    p = OUT / f"v2_{tag}_384.png"
    small.save(p)
    k_eye = (h / crop.height) * small.height / 96.0
    return str(p), k_eye, (w, h)


def main():
    print("== k_min experiment 2 (splat-size axis) ==", flush=True)
    variants = [
        (0.60, 0.14, "s60_m1"),
        (0.60, 0.06, "s60_m0"),
        (0.35, 0.14, "s35_m1"),
        (0.35, 0.06, "s35_m0"),
    ]
    records = []
    for sigma_frac, margin, tag in variants:
        p, k_eye, wh = render_variant(sigma_frac, margin, tag)
        print(f"[{tag}] sigma_frac={sigma_frac} k_eye={k_eye:.2f} subject={wh}", flush=True)
        report = senses.see(p, QUESTION)
        rec = {"tag": tag, "sigma_frac": sigma_frac, "margin": margin,
               "k_eye_px_per_cell": round(k_eye, 2), "eye_image": p,
               "question": QUESTION, "report": report,
               "served_model": senses._last_served_model()}
        records.append(rec)
        print(f"  eye: {report!r}", flush=True)
        (EVIDENCE / "kmin_experiment2.json").write_text(json.dumps(records, indent=1),
                                                        encoding="utf8")
        time.sleep(1.0)
    print("done", flush=True)


if __name__ == "__main__":
    main()
