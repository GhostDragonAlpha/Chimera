"""lasso_label.py -- tailor's chalk for splat sectioning.

The labeler (me) cannot hold a pen, so this tool is the pen: it renders the
donor through a pinhole camera it owns, the labeler looks at the PNG and
writes polygon(s) in PIXEL coordinates into an ops file, and every splat
projecting inside the polygon takes the label. Multiple views in one op are
INTERSECTED (circle the ear from the front AND the side -> pinned in 3D).
Ops apply in order on top of the ellipsoid-spec base labels.

Ops JSON:
{"ops": [
  {"label": "eye_L", "op": "set",            # set | sub (sub -> unlabeled)
   "surface_only": true,                      # only the front layer per pixel
   "thick": 0.02,                             # surface layer thickness (m)
   "views": [{"az": 0.0, "el": 0.15, "r": 0.8,
              "poly": [[x, y], ...]}]}        # pixel coords in a W x H image
]}

Subcommands:
  render  -- write view PNGs (with op polygons overlaid as chalk) for the
             labeler to look at BEFORE applying anything
  apply   -- apply ops, re-derive membrane + core labels, write viz splats

Usage:
  .venv-gs/Scripts/python.exe tools/lasso_label.py render --splat X --ops ops.json --out .tmp/lasso
  .venv-gs/Scripts/python.exe tools/lasso_label.py apply  --splat X --shells Y \
      --spec tools/specs/bear34_regions.json --ops ops.json --out models/co3d/bear34
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

W, H = 1280, 720
FOV_DEG = 45.0


def camera(az: float, el: float, r: float, target: np.ndarray):
    """az=0 -> camera at +Z looking at target (the viewer's front view)."""
    pos = target + r * np.array(
        [np.cos(el) * np.sin(az), np.sin(el), np.cos(el) * np.cos(az)]
    )
    fwd = target - pos
    fwd /= np.linalg.norm(fwd)
    right = np.cross(fwd, [0.0, 1.0, 0.0])
    right /= np.linalg.norm(right)
    up = np.cross(right, fwd)
    return pos, right, up, fwd


def project(pts: np.ndarray, cam):
    """World -> (u, v, depth). depth <= 0 is behind the camera."""
    pos, right, up, fwd = cam
    rel = pts - pos
    x = rel @ right
    y = rel @ up
    z = rel @ fwd
    f = (H / 2.0) / np.tan(np.radians(FOV_DEG) / 2.0)
    with np.errstate(divide="ignore", invalid="ignore"):
        u = f * x / z + W / 2.0
        v = -f * y / z + H / 2.0
    return u, v, z


def render_view(buf: np.ndarray, cam, out_png: str, polys=None, tint=None):
    """Alpha-blended gaussian-dot render; good enough to draw chalk on."""
    from PIL import Image, ImageDraw

    pos = buf[:, 0:3]
    rgb = buf[:, 3:6] if tint is None else tint
    alpha = buf[:, 6]
    size = buf[:, 7:10].max(1)
    u, v, z = project(pos, cam)
    ok = z > 0.02
    u, v, z = u[ok], v[ok], z[ok]
    rgb, alpha, size = rgb[ok], alpha[ok], size[ok]
    order = np.argsort(-z)  # far first
    img = Image.new("RGB", (W, H), (10, 10, 16))
    dr = ImageDraw.Draw(img, "RGBA")
    f = (H / 2.0) / np.tan(np.radians(FOV_DEG) / 2.0)
    for i in order:
        r_px = max(1.0, f * size[i] * 2.0 / z[i])
        c = rgb[i]
        a = int(255 * min(1.0, alpha[i]))
        dr.ellipse(
            [u[i] - r_px, v[i] - r_px, u[i] + r_px, v[i] + r_px],
            fill=(int(c[0] * 255), int(c[1] * 255), int(c[2] * 255), a),
        )
    if polys:
        for poly in polys:
            p = [(float(x), float(y)) for x, y in poly]
            dr.polygon(p, outline=(255, 64, 64, 255))
    img.save(out_png)


def in_poly(u: np.ndarray, v: np.ndarray, poly) -> np.ndarray:
    """Ray-casting point-in-polygon, vectorized."""
    px = np.array([p[0] for p in poly])
    py = np.array([p[1] for p in poly])
    inside = np.zeros(len(u), dtype=bool)
    j = len(px) - 1
    for i in range(len(px)):
        cond = ((py[i] > v) != (py[j] > v)) & (
            u < (px[j] - px[i]) * (v - py[i]) / (py[j] - py[i] + 1e-12) + px[i]
        )
        inside ^= cond
        j = i
    return inside


def cmd_render(a):
    buf = cb.load_splat(a.splat).astype(np.float64)
    buf = buf[buf[:, 6] >= a.alpha_min]
    target = (buf[:, 0:3].min(0) + buf[:, 0:3].max(0)) / 2.0
    views = a.view or []
    ops = json.loads(Path(a.ops).read_text())["ops"] if a.ops else []
    for op in ops:
        for k, vw in enumerate(op["views"]):
            views.append((f"{op['label']}_{k}", vw, [vw["poly"]]))
    if not views:  # default six-side inspection
        views = [(n, {"az": az, "el": el, "r": a.r}, None)
                 for n, az, el in [("front", 0, 0.15), ("right", np.pi / 2, 0.15),
                                   ("back", np.pi, 0.15), ("left", 3 * np.pi / 2, 0.15),
                                   ("top", 0, 0.95), ("bottom", 0, -0.95)]]
    outdir = Path(a.out)
    outdir.mkdir(parents=True, exist_ok=True)
    for name, vw, polys in views:
        cam = camera(vw.get("az", 0), vw.get("el", 0.15), vw.get("r", a.r), target)
        png = str(outdir / f"{name}.png")
        render_view(buf, cam, png, polys=polys)
        print(png)


def cmd_apply(a):
    from scipy.spatial import cKDTree

    sys.path.insert(0, str(ROOT / "tools"))
    import label_regions as lr

    regions = json.loads(Path(a.spec).read_text())["regions"]
    names = [r["name"] for r in regions]
    ops = json.loads(Path(a.ops).read_text())["ops"]
    for op in ops:
        if op["label"] not in names:
            names.append(op["label"])

    buf = cb.load_splat(a.splat).astype(np.float64)
    buf = buf[buf[:, 6] >= 0.5]
    spos = buf[:, 0:3]
    target = (spos.min(0) + spos.max(0)) / 2.0

    shells = np.load(a.shells)
    outer, core = shells["outer"], shells["inner"]

    # base: ellipsoid spec on the membrane, splats inherit nearest membrane
    outer_lab = lr.assign(outer, regions)
    otree = cKDTree(outer)
    splat_lab = outer_lab[otree.query(spos)[1]]
    name_to_i = {n: i for i, n in enumerate(names)}

    for op in ops:
        li = name_to_i[op["label"]]
        sel = np.ones(len(spos), dtype=bool)
        for vw in op["views"]:
            cam = camera(vw.get("az", 0), vw.get("el", 0.15), vw.get("r", 0.8), target)
            u, v, z = project(spos, cam)
            m = (z > 0.02) & in_poly(u, v, vw["poly"])
            if op.get("surface_only"):
                # keep only splats within `thick` of the front surface of their pixel
                thick = op.get("thick", 0.02)
                px = (np.clip(u, 0, W - 1).astype(int),
                      np.clip(v, 0, H - 1).astype(int))
                zbuf = np.full((W, H), np.inf)
                np.minimum.at(zbuf, (px[0][m], px[1][m]), z[m])
                front = zbuf[px[0], px[1]]
                m &= z <= front + thick
            sel &= m
        if op["op"] == "set":
            splat_lab[sel] = li
        elif op["op"] == "replace":
            # redraw a region: old members outside the chalk go unlabeled
            splat_lab[(splat_lab == li) & ~sel] = -1
            splat_lab[sel] = li
        elif op["op"] == "sub":
            splat_lab[sel] = -1
        print(f"{op['op']} {op['label']}: {int(sel.sum())} splats")

    # splats are now authoritative; refill anything the ops unlabeled
    if (splat_lab < 0).any():
        claimed = splat_lab >= 0
        _, nn = cKDTree(spos[claimed]).query(spos[~claimed])
        splat_lab[~claimed] = splat_lab[claimed][nn]

    # splats are now authoritative; membrane + core inherit nearest splat
    stree = cKDTree(spos)
    outer_lab = splat_lab[stree.query(outer)[1]]
    core_lab = outer_lab[otree.query(core)[1]]

    counts = {names[i]: int((splat_lab == i).sum()) for i in range(len(names))}
    print("splat counts:", counts)
    print("unlabeled splats:", int((splat_lab < 0).sum()))

    Path(a.out + "_labels.json").write_text(json.dumps({
        "splat": a.splat, "shells": a.shells, "spec": a.spec, "ops": a.ops,
        "regions": names,
        "outer_labels": outer_lab.tolist(),
        "core_labels": core_lab.tolist(),
    }))

    def colored(pts, labs, alpha, scale):
        out = np.zeros((len(pts), 14), dtype=np.float32)
        out[:, 0:3] = pts
        for i in range(len(names)):
            out[labs == i, 3:6] = lr.region_color(names[i], i)
        out[:, 6] = alpha
        out[:, 7:10] = scale
        out[:, 10] = 1.0
        return out

    cb.save_splat(a.out + "_core_labeled.splat", colored(outer, outer_lab, 1.0, 0.0025))
    don = buf.copy().astype(np.float32)
    for i in range(len(names)):
        don[splat_lab == i, 3:6] = lr.region_color(names[i], i)
    don[splat_lab < 0, 3:6] = (0.5, 0.5, 0.5)  # unlabeled = grey, must be zero
    don[:, 6] = np.maximum(don[:, 6], 0.6)
    cb.save_splat(a.out + "_donor_labeled.splat", don)
    print(f"viz -> {a.out}_core_labeled.splat / {a.out}_donor_labeled.splat")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("render", "apply"):
        p = sub.add_parser(name)
        p.add_argument("--splat", required=True)
        p.add_argument("--out", required=True)
        p.add_argument("--ops")
        p.add_argument("--alpha-min", type=float, default=0.3)
        p.add_argument("--r", type=float, default=0.8)
        p.add_argument("--view", action="append",
                       help='name,az,el,r (repeatable); default: six sides')
        if name == "apply":
            p.add_argument("--shells", required=True)
            p.add_argument("--spec", required=True)
    a = ap.parse_args()
    if a.view:
        a.view = [(v.split(",")[0], dict(zip(("az", "el", "r"), map(float, v.split(",")[1:]))), None)
                  for v in a.view]
    return cmd_render(a) if a.cmd == "render" else cmd_apply(a)


if __name__ == "__main__":
    raise SystemExit(main())
