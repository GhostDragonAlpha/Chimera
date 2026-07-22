"""web_export.py — dump the Construction tree to web/tree.json for the browser dev renderer.

The DOM development backend (web/index.html) fetches this. Markers come from the
trained template (Construction.cross.build_markers) and are colour-sampled from the
reference photo (target_colors) — the same scene the Python renderers use, served to
the browser so the AI can run and iterate in HTTP like web dev.

Run:  python -m Construction.web_export [--photo <ref.jpg>] [--genome <trained.json>] [--lod 1.0]
"""
from __future__ import annotations
import argparse, json, os
import numpy as np
from PIL import Image

from Construction import cross

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB = os.path.join(ROOT, "web")


def export(photo_path, genome_path, lod=1.0, out=None):
    photo = np.asarray(Image.open(photo_path).convert("RGB")).astype(np.float32)/255.0
    genome = json.load(open(genome_path))["genome"]
    P, parts = cross.build_markers(genome, lod=lod)
    colors, valid = cross.target_colors(P, parts, photo)
    markers = [{
        "p": [round(float(P[i, 0]), 1), round(float(P[i, 1]), 1), round(float(P[i, 2]), 1)],
        "s": round(float(P[i, 3]), 1),
        "c": [int(np.clip(colors[i, 0]*255, 0, 255)), int(np.clip(colors[i, 1]*255, 0, 255)), int(np.clip(colors[i, 2]*255, 0, 255))],
        "b": bool(parts[i] > 0),
    } for i in range(len(P)) if valid[i]]
    os.makedirs(WEB, exist_ok=True)
    out = out or os.path.join(WEB, "tree.json")
    json.dump({"markers": markers,
               "view": {"cx": cross.CX, "groundY": cross.GROUNDY, "SC": cross.SC, "W": cross.FW, "H": cross.FH}},
              open(out, "w"))
    print(f"wrote {out}  ({len(markers)} markers, lod={lod})")
    return out


def _main():
    ap = argparse.ArgumentParser(prog="python -m Construction.web_export")
    ap.add_argument("--photo", default=os.path.join(ROOT, "Construction", "renders", "reference_oak.jpg"))
    ap.add_argument("--genome", default=os.path.join(ROOT, "Chimera", "docs", "objectives", "tree_appearance.trained.json"))
    ap.add_argument("--lod", type=float, default=1.0)
    a = ap.parse_args()
    export(a.photo, a.genome, a.lod)


if __name__ == "__main__":
    _main()
