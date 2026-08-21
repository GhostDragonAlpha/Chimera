"""lasso_label.py -- tailor's chalk for splat sectioning, photogrammetry-style.

The labeler (me) cannot hold a pen, so this tool is the pen. v2: the donor is
rendered as TRUE anisotropic ellipse splats (projected 3D covariance per
splat) so the chalk is drawn on the real object, not on dot placeholders.
A contact SHEET packs front/right/back/left/top/bottom into one image; the
labeler circles a part in several tiles and the view cylinders INTERSECT --
exactly how SfM rejects noise that doesn't triangulate, so floaters and
static contamination (e.g. the cloud beside bear-34's right ear) never
survive a multi-view op. Regions carry a HIERARCHY (head contains eyes/ears/
nose/snout; torso carries the limbs) recorded in the labels JSON -- the tree
the CAD body's standardized shape will hang from.

Ops JSON:
{"ops": [
  {"label": "ear_R", "op": "set", "parent": "head",
   "surface_only": true, "thick": 0.02,
   "views": [{"tile": "front", "poly": [[x, y], ...]},   # tile-pixel coords
             {"tile": "right", "poly": [[x, y], ...]}]}  # intersected
]}
(view entries may instead be {"az","el","r","poly"} in full-frame 1280x720;
 op = set | replace | sub, applied in order on the ellipsoid-spec base.)

Subcommands:
  render  -- per-view PNGs (chalk overlaid) for inspection BEFORE applying
  sheet   -- one contact-sheet PNG of all six views (+ chalk if --ops given)
  apply   -- apply ops, re-derive membrane + core labels, write viz splats

Usage:
  .venv-gs/Scripts/python.exe tools/lasso_label.py sheet --splat X --out .tmp/sheet [--ops O]
  .venv-gs/Scripts/python.exe tools/lasso_label.py apply --splat X --shells Y \
      --spec tools/specs/bear34_regions.json --ops O --out models/co3d/bear34 [--denoise 0.02]
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
TILE_W, TILE_H = 640, 360
SHEET_TILES = [  # name, az, el -- layout is 3 wide x 2 tall, row-major
    ("front", 0.0, 0.15), ("right", np.pi / 2, 0.15), ("back", np.pi, 0.15),
    ("left", 3 * np.pi / 2, 0.15), ("top", 0.0, 0.95), ("bottom", 0.0, -0.95),
]

CHALK = {  # per-label outline colors on the sheet
    "head": (255, 255, 80), "snout": (255, 180, 80), "nose": (255, 255, 255),
    "eye_L": (0, 255, 255), "eye_R": (0, 255, 255),
    "ear_L": (255, 60, 60), "ear_R": (60, 120, 255),
    "arm_L": (255, 0, 255), "arm_R": (80, 255, 255),
    "leg_L": (255, 140, 0), "leg_R": (170, 110, 255), "torso": (120, 255, 120),
}


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


def project(pts: np.ndarray, cam, w: int = W, h: int = H):
    """World -> (u, v, depth). depth <= 0 is behind the camera."""
    pos, right, up, fwd = cam
    rel = pts - pos
    x = rel @ right
    y = rel @ up
    z = rel @ fwd
    f = (h / 2.0) / np.tan(np.radians(FOV_DEG) / 2.0)
    with np.errstate(divide="ignore", invalid="ignore"):
        u = f * x / z + w / 2.0
        v = -f * y / z + h / 2.0
    return u, v, z


def quat_to_R(q: np.ndarray) -> np.ndarray:
    """(N,4) wxyz -> (N,3,3)."""
    w, x, y, z = q[:, 0], q[:, 1], q[:, 2], q[:, 3]
    R = np.empty((len(q), 3, 3))
    R[:, 0, 0] = 1 - 2 * (y * y + z * z); R[:, 0, 1] = 2 * (x * y - w * z); R[:, 0, 2] = 2 * (x * z + w * y)
    R[:, 1, 0] = 2 * (x * y + w * z); R[:, 1, 1] = 1 - 2 * (x * x + z * z); R[:, 1, 2] = 2 * (y * z - w * x)
    R[:, 2, 0] = 2 * (x * z - w * y); R[:, 2, 1] = 2 * (y * z + w * x); R[:, 2, 2] = 1 - 2 * (x * x + y * y)
    return R


def ellipses_2d(buf: np.ndarray, cam, w: int, h: int, k: float = 2.5):
    """Project each splat's 3D covariance to a 2D ellipse.
    Returns (u, v, z, ax, ay, theta) for splats in front of the camera."""
    pos = buf[:, 0:3]
    pos3, right, up, fwd = cam
    rel = pos - pos3
    x = rel @ right; y = rel @ up; z = rel @ fwd
    f = (h / 2.0) / np.tan(np.radians(FOV_DEG) / 2.0)
    R = quat_to_R(buf[:, 10:14])
    S2 = buf[:, 7:10] ** 2
    RS = R * np.sqrt(S2)[:, None, :]
    cov3 = np.einsum("nij,nkj->nik", RS, RS)
    with np.errstate(divide="ignore", invalid="ignore"):
        J = np.zeros((len(buf), 2, 3))
        J[:, 0, 0] = f / z; J[:, 0, 2] = -f * x / z ** 2
        J[:, 1, 1] = f / z; J[:, 1, 2] = -f * y / z ** 2
    cov2 = np.einsum("nij,njk,nlk->nil", J, cov3, J)
    tr = cov2[:, 0, 0] + cov2[:, 1, 1]
    det = cov2[:, 0, 0] * cov2[:, 1, 1] - cov2[:, 0, 1] ** 2
    disc = np.sqrt(np.maximum(tr * tr / 4 - det, 1e-12))
    l1 = np.maximum(tr / 2 + disc, 1e-12)
    l2 = np.maximum(tr / 2 - disc, 1e-12)
    theta = np.arctan2(l1 - cov2[:, 0, 0], cov2[:, 0, 1] + 1e-12)
    ok = (z > 0.02) & np.isfinite(cov2[:, 0, 0])
    u = f * x / z + w / 2.0
    v = -f * y / z + h / 2.0
    return u[ok], v[ok], z[ok], k * np.sqrt(l1[ok]), k * np.sqrt(l2[ok]), theta[ok], ok


def render_view(buf: np.ndarray, cam, out_png: str, polys=None, tint=None,
                w: int = W, h: int = H, base_img=None):
    """Anisotropic-ellipse splat render -- the real object, chalkable."""
    from PIL import Image, ImageDraw

    u, v, z, ax, ay, th, ok = ellipses_2d(buf, cam, w, h)
    rgb = buf[ok, 3:6] if tint is None else tint[ok]
    alpha = buf[ok, 6]
    order = np.argsort(-z)
    img = base_img or Image.new("RGB", (w, h), (10, 10, 16))
    dr = ImageDraw.Draw(img, "RGBA")
    t = np.linspace(0, 2 * np.pi, 10)
    ct, st = np.cos(t), np.sin(t)
    for i in order:
        if ax[i] > 60 or ax[i] < 0.3:  # screen-space degenerate: skip
            continue
        c, s = np.cos(th[i]), np.sin(th[i])
        ex = ax[i] * ct; ey = ay[i] * st
        px = u[i] + ex * c - ey * s
        py = v[i] + ex * s + ey * c
        col = rgb[i]
        dr.polygon(list(zip(px, py)),
                   fill=(int(col[0] * 255), int(col[1] * 255), int(col[2] * 255),
                         int(255 * min(1.0, alpha[i]))))
    if polys:
        for poly, col, name in polys:
            p = [(float(x), float(y)) for x, y in poly]
            dr.line(p + [p[0]], fill=col + (255,), width=2)
            dr.text((p[0][0] + 3, p[0][1] - 12), name, fill=col + (255,))
    if out_png is not None:
        img.save(out_png)
    return img


def render_sheet(buf, target, r, out_png, ops=None):
    from PIL import Image, ImageDraw

    sheet = Image.new("RGB", (TILE_W * 3, TILE_H * 2), (10, 10, 16))
    dr = ImageDraw.Draw(sheet)
    for ti, (name, az, el) in enumerate(SHEET_TILES):
        ox, oy = (ti % 3) * TILE_W, (ti // 3) * TILE_H
        cam = camera(az, el, r, target)
        tile = render_view(buf, cam, None, w=TILE_W, h=TILE_H)
        sheet.paste(tile, (ox, oy))
        dr.text((ox + 6, oy + 4), name, fill=(255, 255, 255))
    if ops:
        dr = ImageDraw.Draw(sheet)
        for op in ops:
            col = CHALK.get(op["label"], (255, 0, 255))
            for vw in op["views"]:
                if "tile" not in vw:
                    continue
                ti = [i for i, (n, _, _) in enumerate(SHEET_TILES) if n == vw["tile"]][0]
                ox, oy = (ti % 3) * TILE_W, (ti // 3) * TILE_H
                p = [(x + ox, y + oy) for x, y in vw["poly"]]
                dr.line(p + [p[0]], fill=col, width=2)
                dr.text((p[0][0] + 3, p[0][1] - 10), op["label"], fill=col)
    sheet.save(out_png)
    print(out_png)


# ---------------------------------------------------------------- skeleton --

def mark_ray(mark, target, sheet_r: float):
    """One pixel mark -> (origin, unit direction) ray in world space."""
    if "tile" in mark:
        ti = [i for i, (n, _, _) in enumerate(SHEET_TILES) if n == mark["tile"]][0]
        _, az, el = SHEET_TILES[ti]
        cam = camera(az, el, mark.get("r", sheet_r), target)
        w, h = TILE_W, TILE_H
    else:
        cam = camera(mark.get("az", 0), mark.get("el", 0.15), mark.get("r", sheet_r), target)
        w, h = W, H
    u, v = mark["px"]
    pos, right, up, fwd = cam
    f = (h / 2.0) / np.tan(np.radians(FOV_DEG) / 2.0)
    d = fwd + ((u - w / 2.0) / f) * right + ((h / 2.0 - v) / f) * up
    return pos, d / np.linalg.norm(d)


def triangulate(marks, target, sheet_r: float):
    """Least-squares closest point of >=2 pixel rays -> (point, rms reprojection px)."""
    A = np.zeros((3, 3)); b = np.zeros(3)
    rays = [mark_ray(m, target, sheet_r) for m in marks]
    for o, d in rays:
        P = np.eye(3) - np.outer(d, d)
        A += P; b += P @ o
    p = np.linalg.solve(A, b)
    errs = []
    for (o, d), m in zip(rays, marks):
        t = max(np.dot(p - o, d), 1e-6)
        q = o + t * d
        if "tile" in m:
            w, h = TILE_W, TILE_H
        else:
            w, h = W, H
        f = (h / 2.0) / np.tan(np.radians(FOV_DEG) / 2.0)
        rel = q - o  # project q back onto the mark's image plane
        # reproject via the same camera basis: rebuild from ray origin is fine
        errs.append(float(np.linalg.norm(p - q) * f / t))
    return p, float(np.sqrt(np.mean(np.square(errs)))) if errs else 0.0


def load_solved_skel(path, target, sheet_r: float):
    """Marks file -> solved skeleton dict {name: {"pos": [x,y,z], "parent": str}}."""
    data = json.loads(Path(path).read_text())
    solved = {}
    for j in data["joints"]:
        p, rms = triangulate(j["marks"], target, sheet_r)
        solved[j["name"]] = {"pos": p.tolist(), "parent": j.get("parent"), "rms_px": rms}
    return solved


def overlay_skeleton(sheet, solved, target, r, tile_of_interest=None):
    """Draw bones + joint dots on a contact sheet (in place)."""
    from PIL import ImageDraw

    dr = ImageDraw.Draw(sheet)
    names = list(solved)
    for ti, (tname, az, el) in enumerate(SHEET_TILES):
        ox, oy = (ti % 3) * TILE_W, (ti // 3) * TILE_H
        cam = camera(az, el, r, target)
        uv = {}
        for n in names:
            u, v, z = project(np.array([solved[n]["pos"]]), cam, TILE_W, TILE_H)
            if z[0] > 0.02:
                uv[n] = (float(u[0]) + ox, float(v[0]) + oy)
        for n in names:
            par = solved[n].get("parent")
            if par and n in uv and par in uv:
                dr.line([uv[par], uv[n]], fill=(255, 255, 255), width=2)
        for n, (x, y) in uv.items():
            dr.ellipse([x - 3, y - 3, x + 3, y + 3], outline=(0, 255, 128), width=2)
            dr.text((x + 5, y - 5), n, fill=(0, 255, 128))
    return sheet


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


def view_sel(spos, target, vw, surface_only, thick):
    """Boolean mask of splats inside one view's polygon."""
    if "tile" in vw:
        ti = [i for i, (n, _, _) in enumerate(SHEET_TILES) if n == vw["tile"]][0]
        _, az, el = SHEET_TILES[ti]
        cam = camera(az, el, vw.get("r", 0.8), target)
        w, h = TILE_W, TILE_H
    else:
        cam = camera(vw.get("az", 0), vw.get("el", 0.15), vw.get("r", 0.8), target)
        w, h = W, H
    u, v, z = project(spos, cam, w, h)
    m = (z > 0.02) & in_poly(u, v, vw["poly"])
    if surface_only:
        px = (np.clip(u, 0, w - 1).astype(int), np.clip(v, 0, h - 1).astype(int))
        zbuf = np.full((w, h), np.inf)
        np.minimum.at(zbuf, (px[0][m], px[1][m]), z[m])
        m &= z <= zbuf[px[0], px[1]] + thick
    return m


def cmd_render(a):
    buf = cb.load_splat(a.splat).astype(np.float64)
    buf = buf[buf[:, 6] >= a.alpha_min]
    target = (buf[:, 0:3].min(0) + buf[:, 0:3].max(0)) / 2.0
    ops = json.loads(Path(a.ops).read_text())["ops"] if a.ops else []
    views = a.view or []
    for op in ops:
        for k, vw in enumerate(op["views"]):
            if "tile" not in vw:
                views.append((f"{op['label']}_{k}", vw, [vw["poly"]]))
    if not views:
        views = [(n, {"az": az, "el": el, "r": a.r}, None)
                 for n, az, el in [("front", 0, 0.15), ("right", np.pi / 2, 0.15),
                                   ("back", np.pi, 0.15), ("left", 3 * np.pi / 2, 0.15),
                                   ("top", 0, 0.95), ("bottom", 0, -0.95)]]
    outdir = Path(a.out)
    outdir.mkdir(parents=True, exist_ok=True)
    for name, vw, polys in views:
        cam = camera(vw.get("az", 0), vw.get("el", 0.15), vw.get("r", a.r), target)
        png = str(outdir / f"{name}.png")
        render_view(buf, cam, png)
        if polys:
            img = render_view(buf, cam, png, polys=[(p, (255, 64, 64), "") for p in polys])
            img.save(png)
        print(png)


def cmd_sheet(a):
    buf = cb.load_splat(a.splat).astype(np.float64)
    buf = buf[buf[:, 6] >= a.alpha_min]
    target = (buf[:, 0:3].min(0) + buf[:, 0:3].max(0)) / 2.0
    ops = json.loads(Path(a.ops).read_text())["ops"] if a.ops else None
    Path(a.out).mkdir(parents=True, exist_ok=True)
    render_sheet(buf, target, a.r, str(Path(a.out) / "sheet.png"), ops=ops)
    if a.skel:
        from PIL import Image
        solved = load_solved_skel(a.skel, target, a.r)
        img = Image.open(str(Path(a.out) / "sheet.png"))
        overlay_skeleton(img, solved, target, a.r)
        img.save(str(Path(a.out) / "sheet.png"))
        for n, j in solved.items():
            print(f"  {n}: pos=({j['pos'][0]:.3f},{j['pos'][1]:.3f},{j['pos'][2]:.3f}) rms={j['rms_px']:.1f}px")
        print("skeleton overlaid ->", str(Path(a.out) / "sheet.png"))


def cmd_skel(a):
    buf = cb.load_splat(a.splat).astype(np.float64)
    buf = buf[buf[:, 6] >= 0.5]
    spos = buf[:, 0:3]
    target = (spos.min(0) + spos.max(0)) / 2.0
    solved = load_solved_skel(a.skel, target, a.r)
    # containment check: every joint must sit inside the blob (near membrane core)
    from scipy.spatial import cKDTree
    shells = np.load(a.shells) if a.shells else None
    out = {"splat": a.splat, "joints": solved}
    for n, j in solved.items():
        p = np.array(j["pos"])
        inside = ""
        if shells is not None:
            d_core = cKDTree(shells["inner"]).query(p)[0]
            d_out = cKDTree(shells["outer"]).query(p)[0]
            inside = f" core_dist={d_core*1000:.0f}mm membrane_dist={d_out*1000:.0f}mm"
        print(f"{n}: ({p[0]:.3f},{p[1]:.3f},{p[2]:.3f}) rms={j['rms_px']:.1f}px{inside}")
    Path(a.out).write_text(json.dumps(out, indent=2))
    print("->", a.out)


def cmd_apply(a):
    from scipy.spatial import cKDTree

    sys.path.insert(0, str(ROOT / "tools"))
    import label_regions as lr

    regions = json.loads(Path(a.spec).read_text())["regions"]
    names = [r["name"] for r in regions]
    hierarchy = {r["name"]: r.get("parent") for r in regions if r.get("parent")}
    ops = json.loads(Path(a.ops).read_text())["ops"]
    for op in ops:
        if op["label"] not in names:
            names.append(op["label"])
        if op.get("parent"):
            hierarchy[op["label"]] = op["parent"]

    buf = cb.load_splat(a.splat).astype(np.float64)
    buf = buf[buf[:, 6] >= 0.5]
    shells = np.load(a.shells)
    outer, core = shells["outer"], shells["inner"]

    if a.denoise:
        # floaters/static never reach the labels: drop splats far from the membrane
        d = cKDTree(outer).query(buf[:, 0:3])[0]
        keep = d <= a.denoise
        print(f"denoise: dropped {int((~keep).sum())} splats > {a.denoise} m from membrane")
        buf = buf[keep]

    spos = buf[:, 0:3]
    target = (spos.min(0) + spos.max(0)) / 2.0

    outer_lab = lr.assign(outer, regions)
    otree = cKDTree(outer)
    splat_lab = outer_lab[otree.query(spos)[1]]
    name_to_i = {n: i for i, n in enumerate(names)}

    for op in ops:
        li = name_to_i[op["label"]]
        sel = np.ones(len(spos), dtype=bool)
        for vw in op["views"]:
            sel &= view_sel(spos, target, vw, op.get("surface_only"), op.get("thick", 0.02))
        if op["op"] == "set":
            splat_lab[sel] = li
        elif op["op"] == "replace":
            splat_lab[(splat_lab == li) & ~sel] = -1
            splat_lab[sel] = li
        elif op["op"] == "sub":
            splat_lab[sel] = -1
        print(f"{op['op']} {op['label']}: {int(sel.sum())} splats")

    if (splat_lab < 0).any():
        claimed = splat_lab >= 0
        _, nn = cKDTree(spos[claimed]).query(spos[~claimed])
        splat_lab[~claimed] = splat_lab[claimed][nn]

    stree = cKDTree(spos)
    outer_lab = splat_lab[stree.query(outer)[1]]
    core_lab = outer_lab[otree.query(core)[1]]

    counts = {names[i]: int((splat_lab == i).sum()) for i in range(len(names))}
    print("splat counts:", counts)

    Path(a.out + "_labels.json").write_text(json.dumps({
        "splat": a.splat, "shells": a.shells, "spec": a.spec, "ops": a.ops,
        "regions": names, "hierarchy": hierarchy,
        "outer_labels": outer_lab.tolist(),
        "core_labels": core_lab.tolist(),
        "splat_labels": splat_lab.tolist(),
        "denoise": a.denoise,
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
    don[:, 6] = np.maximum(don[:, 6], 0.6)
    cb.save_splat(a.out + "_donor_labeled.splat", don)
    print(f"viz -> {a.out}_core_labeled.splat / {a.out}_donor_labeled.splat")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("render", "sheet", "skel", "apply"):
        p = sub.add_parser(name)
        p.add_argument("--splat", required=True)
        p.add_argument("--out", required=True)
        p.add_argument("--ops")
        p.add_argument("--alpha-min", type=float, default=0.3)
        p.add_argument("--r", type=float, default=0.8)
        if name == "render":
            p.add_argument("--view", action="append",
                           help='name,az,el,r (repeatable); default: six sides')
        if name in ("sheet", "skel"):
            p.add_argument("--skel", help="skeleton marks JSON (triangulated + overlaid)")
        if name == "skel":
            p.add_argument("--shells", help="shells npz for the inside-the-body check")
        if name == "apply":
            p.add_argument("--shells", required=True)
            p.add_argument("--spec", required=True)
            p.add_argument("--denoise", type=float, default=0.0)
    a = ap.parse_args()
    if getattr(a, "view", None):
        a.view = [(v.split(",")[0], dict(zip(("az", "el", "r"), map(float, v.split(",")[1:]))), None)
                  for v in a.view]
    return {"render": cmd_render, "sheet": cmd_sheet, "skel": cmd_skel, "apply": cmd_apply}[a.cmd](a)


if __name__ == "__main__":
    raise SystemExit(main())
