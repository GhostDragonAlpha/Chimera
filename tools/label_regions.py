"""label_regions.py -- trace anatomical regions onto a donor: same labels on the
inner core, the outer membrane, and every splat in the margin.

Regions are oriented ellipsoids (center, euler-deg rotation, radii) listed in a
JSON spec IN PRIORITY ORDER: a point inside several ellipsoids takes the FIRST
region containing it (so "snout" carved out of "head" just comes first).
Unclaimed core points inherit the nearest claimed core point's label; splats
inherit from their nearest core point. Output viz splats let the labeler (me)
eye-check boundaries against the real bear and iterate the spec.

Spec JSON: {"regions": [{"name": "head", "c": [x,y,z], "rot": [rx,ry,rz],
                         "r": [rx,ry,rz]}, ...]}

Usage:
  .venv-gs/Scripts/python.exe tools/label_regions.py --splat models/co3d/co3d_34.splat \
      --shells models/co3d/bear34_shells.npz --spec tools/specs/bear34_regions.json \
      --out models/co3d/bear34
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "ChimeraEngine"))
import cpp_bridge as cb  # noqa: E402

PALETTE = [
    (0.90, 0.10, 0.10), (0.10, 0.80, 0.10), (0.10, 0.30, 0.95), (0.95, 0.85, 0.10),
    (0.90, 0.10, 0.90), (0.10, 0.90, 0.90), (0.95, 0.55, 0.10), (0.55, 0.30, 0.90),
    (0.40, 0.90, 0.40), (0.90, 0.40, 0.60), (0.30, 0.60, 0.30), (0.60, 0.60, 0.95),
    (0.95, 0.95, 0.60),
]

# Stable colors by region NAME — spec edits must never reshuffle the map.
# L = warm, R = cool.
NAME_COLORS = {
    "eye_L": (0.95, 0.95, 0.95), "eye_R": (0.95, 0.95, 0.95),
    "snout": (0.80, 0.62, 0.42),
    "nose": (0.12, 0.08, 0.08),
    "ear_L": (0.90, 0.10, 0.10), "ear_R": (0.10, 0.30, 0.95),
    "head": (0.95, 0.85, 0.10),
    "arm_L": (0.90, 0.10, 0.90), "arm_R": (0.10, 0.90, 0.90),
    "leg_L": (0.95, 0.55, 0.10), "leg_R": (0.55, 0.30, 0.90),
    "torso": (0.40, 0.90, 0.40),
}


def region_color(name: str, idx: int):
    return NAME_COLORS.get(name, PALETTE[idx % len(PALETTE)])


def euler_to_R(deg) -> np.ndarray:
    rx, ry, rz = [np.radians(v) for v in deg]
    Rx = np.array([[1, 0, 0], [0, np.cos(rx), -np.sin(rx)], [0, np.sin(rx), np.cos(rx)]])
    Ry = np.array([[np.cos(ry), 0, np.sin(ry)], [0, 1, 0], [-np.sin(ry), 0, np.cos(ry)]])
    Rz = np.array([[np.cos(rz), -np.sin(rz), 0], [np.sin(rz), np.cos(rz), 0], [0, 0, 1]])
    return Rz @ Ry @ Rx


def assign(pts: np.ndarray, regions) -> np.ndarray:
    """Priority-order ellipsoid containment, then nearest-claimed fill."""
    labels = np.full(len(pts), -1, dtype=np.int64)
    for i, reg in enumerate(regions):
        R = euler_to_R(reg.get("rot", [0, 0, 0]))
        c = np.array(reg["c"]); r = np.array(reg["r"])
        local = (pts - c) @ R.T  # world -> ellipsoid frame
        inside = ((local / r) ** 2).sum(1) <= 1.0
        labels[(labels < 0) & inside] = i
    if (labels < 0).any():
        from scipy.spatial import cKDTree
        claimed = labels >= 0
        if claimed.any():
            _, nn = cKDTree(pts[claimed]).query(pts[~claimed])
            labels[~claimed] = labels[claimed][nn]
    return labels


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--splat", required=True)
    ap.add_argument("--shells", required=True)
    ap.add_argument("--spec", required=True)
    ap.add_argument("--out", required=True, help="prefix for <out>_labels.json / <out>_core_labeled.splat / <out>_donor_labeled.splat")
    a = ap.parse_args()

    regions = json.loads(Path(a.spec).read_text())["regions"]
    names = [r["name"] for r in regions]
    shells = np.load(a.shells)
    core = shells["inner"]
    outer = shells["outer"]

    # Labels are traced on the OUTER membrane: thin limbs have no eroded core
    # inside them (measured: arm_R claimed 0 core points), so the membrane is
    # the authoritative labeled surface; core points and splats both inherit
    # from their nearest membrane point.
    outer_lab = assign(outer, regions)
    from scipy.spatial import cKDTree
    tree = cKDTree(outer)
    core_lab = outer_lab[tree.query(core)[1]]

    buf = cb.load_splat(a.splat).astype(np.float64)
    buf = buf[buf[:, 6] >= 0.5]
    spos = buf[:, 0:3]
    splat_lab = outer_lab[tree.query(spos)[1]]

    counts = {names[i]: int((outer_lab == i).sum()) for i in range(len(names))}
    print("membrane points per region:", counts)

    Path(a.out + "_labels.json").write_text(json.dumps({
        "splat": a.splat, "shells": a.shells, "spec": a.spec,
        "regions": names,
        "outer_labels": outer_lab.tolist(),
        "core_labels": core_lab.tolist(),
    }))

    def colored(pts, labs, alpha, scale, keep_alpha=None):
        n = len(pts)
        out = np.zeros((n, 14), dtype=np.float32)
        out[:, 0:3] = pts
        for i in range(len(names)):
            out[labs == i, 3:6] = region_color(names[i], i)
        out[:, 6] = alpha
        out[:, 7:10] = scale
        out[:, 10] = 1.0
        return out

    cb.save_splat(a.out + "_core_labeled.splat",
                  colored(outer, outer_lab, 1.0, 0.0025))
    don = buf.copy().astype(np.float32)
    for i in range(len(names)):
        don[splat_lab == i, 3:6] = region_color(names[i], i)
    don[:, 6] = np.maximum(don[:, 6], 0.6)
    cb.save_splat(a.out + "_donor_labeled.splat", don)
    print(f"viz -> {a.out}_core_labeled.splat / {a.out}_donor_labeled.splat (orient=1)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
