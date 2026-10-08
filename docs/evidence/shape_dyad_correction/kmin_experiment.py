"""k_min experiment — how many px/cell does the eye need to read a voxel body as cubes?

THE_SHAPE_DYAD_CORRECTION.md §3: k_min is measured by the eye itself, one image per call,
blind, fixed non-leading question. Physics emit() is used VERBATIM (no edits); only the
eye-path framing varies (crop around the subject, then the standard 384px eye resize).

Each variant: render through the C++ engine on 8091 -> /frame (1280x720) -> crop variant
-> 384px resize -> senses.see (ONE image, ONE call) -> report archived.
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image

_HERE = Path(__file__).resolve().parent
_CE = _HERE.parents[1]                     # ChimeraEngine/
sys.path.insert(0, str(_CE))

import cpp_bridge
import splat_appearance as sa
import senses

ENGINE_URL = "http://127.0.0.1:8091"
cpp_bridge.ENGINE_URL = ENGINE_URL
OUT = _HERE
EVIDENCE = _CE.parent / "docs" / "evidence" / "shape_dyad_correction"
EVIDENCE.mkdir(parents=True, exist_ok=True)

# The fixed, non-leading question. It never mentions cubes, voxels, blocks or bears.
QUESTION = ("Describe the surface of the object in this image. Is its surface smooth, "
            "or does it show a repeating fine structure? If it shows repeating structure, "
            "name its shape. Answer in 1-3 sentences.")

# Crop margin variants: fraction of subject half-width added around the subject box.
MARGINS = (0.06, 0.14, 0.25)
FRAME_PX = 384                             # the eye's measured token budget format


def subject_box(gray: np.ndarray, thr_frac: float = 0.35):
    """Bounding box of the bright subject against the near-black background."""
    thr = gray.max() * thr_frac
    ys, xs = np.where(gray > thr)
    return xs.min(), ys.min(), xs.max(), ys.max()


def render_t0() -> np.ndarray:
    """The real emit(0) buffer through the engine; returns the full 1280x720 frame."""
    buf = sa.membrane_buffer("theShape", 0.0)
    assert buf is not None, "emit(0) failed"
    ext = float(np.linalg.norm(buf[:, 0:3], axis=1).max()) or 1.0
    cam = (0.0, -2.7 * ext, 0.72 * ext)
    assert cpp_bridge.load_membrane("theShape", buf, cam), "upload failed"
    time.sleep(0.6)                        # let the render loop capture the new scene
    raw = cpp_bridge.fetch_frame()
    (OUT / "engine_t0_full.png").write_bytes(raw)
    return np.asarray(Image.open(OUT / "engine_t0_full.png").convert("RGB"))


def main():
    print("== k_min experiment ==", flush=True)
    rgb = render_t0()
    gray = rgb.mean(axis=2)
    x0, y0, x1, y1 = subject_box(gray)
    w, h = x1 - x0 + 1, y1 - y0 + 1
    print(f"subject box: {w}x{h}px at ({x0},{y0})", flush=True)

    # 96 cells span the subject's height (asset Y -> screen V is upright here: Z-up emit,
    # camera above the plane). px/cell at full res:
    k_full = h / 96.0
    print(f"px/cell at full res: {k_full:.2f}", flush=True)

    records = []
    for mi, margin in enumerate(MARGINS):
        mx, my = int(w * margin), int(h * margin)
        cx0, cy0 = max(0, x0 - mx), max(0, y0 - my)
        cx1, cy1 = min(rgb.shape[1] - 1, x1 + mx), min(rgb.shape[0] - 1, y1 + my)
        crop = Image.fromarray(rgb[cy0:cy1 + 1, cx0:cx1 + 1])
        crop.save(OUT / f"variant_m{mi}_full.png")
        small = crop.resize((FRAME_PX, round(crop.height * FRAME_PX / crop.width)),
                            Image.LANCZOS)
        p = OUT / f"variant_m{mi}_384.png"
        small.save(p)
        k_eye = (h / crop.height) * small.height / 96.0   # px/cell AT the eye
        print(f"variant m{mi}: crop {crop.size}, eye {small.size}, k_eye={k_eye:.2f}", flush=True)

        report = senses.see(str(p), QUESTION)
        rec = {"variant": f"m{mi}", "margin": margin, "k_eye_px_per_cell": round(k_eye, 2),
               "eye_image": str(p), "question": QUESTION, "report": report,
               "served_model": senses._last_served_model()}
        records.append(rec)
        print(f"  eye: {report!r}", flush=True)
        (EVIDENCE / "kmin_experiment.json").write_text(
            json.dumps(records, indent=1), encoding="utf8")
        time.sleep(1.0)

    print("done", flush=True)


if __name__ == "__main__":
    main()
