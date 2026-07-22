"""cross.py — THE SYNTHESIS: a template MADE FROM THE PHOTO x photo patterns -> a 3D tree.

The template is authored FROM the reference, not reused: markers are distributed by
the photo's own silhouette (foliage fills the actual crown mask, trunk fills the
actual trunk mask), each lifted into 3D by a morphology prior (the crown is filled
as a volume so it is round from every angle; the trunk as a cylinder) and coloured
from ITS OWN pixel. Then a library of real textured PATCHES cut from the photo is
matched to each marker by colour and stamped in its vicinity.

Because every marker is born on the tree mask, two old bugs are gone by construction:
sky/white is never part of the structure (there are no markers there), and a trunk
marker is bark because it was sampled from the trunk. A best reference is a whole
subject ISOLATED ON WHITE (REFERENCE_TO_NOUN.md, Stage 0).

CLI:  python -m Construction.cross --photo <ref.jpg> --genome <trained.json> [--lod 1.0]
"""
from __future__ import annotations
import argparse, json, math, os
import numpy as np
from PIL import Image, ImageDraw

FW, FH, SC = 680, 900, 1.30
CX = FW * 0.5; GROUNDY = FH * 0.90
WORLD_H = 480.0                      # tree height in world units (fits the frame)


def _masks(photo):
    r, g, b = photo[..., 0], photo[..., 1], photo[..., 2]; mx = photo.max(2); mn = photo.min(2)
    green = (g > r) & (g > b) & (g > 0.18) & ((mx - mn) > 0.04)
    bark = (~green) & (mx < 0.82) & (mx > 0.12) & (r >= b * 0.85)   # brownish, not white, not green
    return green, bark


def build_markers(photo, genome=None, lod=1.0, seed=7):
    """TEMPLATE FROM THE PHOTO. Returns (P Nx4 [x,y,z,size], parts N, src Nx2 [ix,iy]).
    Foliage fills the crown mask as a 3D volume; trunk fills the trunk mask as a
    cylinder. genome lightly scales crown depth."""
    rng = np.random.default_rng(seed)
    Hp, Wp, _ = photo.shape
    green, bark = _masks(photo)
    tys, txs = np.where(green | bark)
    x0, x1, y0, y1 = txs.min(), txs.max(), tys.min(), tys.max()
    tcx = (x0 + x1) / 2.0; boty = float(y1); ws = WORLD_H / max(1, (y1 - y0))
    gy, gx = np.where(green)
    ccx, ccy = gx.mean(), gy.mean(); crx = (gx.max() - gx.min()) / 2.0; cry = (gy.max() - gy.min()) / 2.0
    depth_k = crx * ws * (0.8 + 0.5 * (genome.get("flat", 0.4) if genome else 0.4))
    P, part, src = [], [], []
    # foliage: fill the crown mask, lifted into a 3D volume (round from any angle)
    nf = int(min(len(gx), 6500 * lod))
    for i in rng.integers(0, len(gx), nf):
        ix, iy = int(gx[i]), int(gy[i])
        rr = min(1.0, math.hypot((ix - ccx) / (crx + 1), (iy - ccy) / (cry + 1)))
        Y = rng.uniform(-1, 1) * depth_k * math.sqrt(max(0.0, 1 - rr * rr))
        P.append(((ix - tcx) * ws, Y, (boty - iy) * ws, rng.uniform(6, 10))); part.append(0); src.append((ix, iy))
    # trunk: fill the trunk mask as a cylinder (front silhouette = the photo trunk)
    by, bx = np.where(bark)
    if len(bx):
        # keep only the trunk (bark near the vertical centre-line, below the crown top)
        keep = (np.abs(bx - tcx) < (x1 - x0) * 0.28)
        by, bx = by[keep], bx[keep]
    if len(bx):
        tcx2 = (bx.min() + bx.max()) / 2.0; tw = max(6.0, (bx.max() - bx.min()) / 2.0)
        nb = int(min(len(bx), 2600 * lod))
        for i in rng.integers(0, len(bx), nb):
            ix, iy = int(bx[i]), int(by[i])
            dx = ix - tcx2; Y = float(rng.choice([-1, 1])) * math.sqrt(max(0.0, tw * tw - dx * dx)) * ws
            P.append(((ix - tcx) * ws, Y, (boty - iy) * ws, rng.uniform(4, 7.5))); part.append(1); src.append((ix, iy))
    return np.array(P, np.float32), np.array(part), np.array(src)


def marker_colors(photo, parts, src):
    """Colour each marker from ITS OWN source pixel; enforce material by part and
    drop anything that still reads as background."""
    col = photo[src[:, 1], src[:, 0]].copy()
    smx = col.max(1); smn = col.min(1); sr, sg, sb = col[:, 0], col[:, 1], col[:, 2]
    is_green = (sg > sr) & (sg > sb) & ((smx - smn) > 0.04)
    is_white = smx > 0.82
    green, bark = _masks(photo)
    folpal = photo[green]; barkpal = photo[bark] if bark.any() else np.array([[0.36, 0.30, 0.22]], np.float32)
    rng = np.random.default_rng(3)
    is_bark = parts > 0
    valid = np.ones(len(col), bool)
    fix = is_bark & (is_green | is_white)
    if fix.any(): col[fix] = barkpal[rng.integers(0, len(barkpal), int(fix.sum()))]
    ffix = (~is_bark) & (~is_green) & (~is_white)
    if ffix.any(): col[ffix] = folpal[rng.integers(0, len(folpal), int(ffix.sum()))]
    valid[(~is_bark) & is_white] = False
    return col, valid


def pattern_library(photo, mask, n, ps, seed):
    rng = np.random.default_rng(seed); Hp, Wp, _ = photo.shape
    ys, xs = np.where(mask)
    yy, xx = np.mgrid[0:ps, 0:ps]; al = np.clip(1.25 - np.hypot((xx - ps / 2) / (ps / 2), (yy - ps / 2) / (ps / 2)), 0, 1)
    ims, means = [], []; tries = 0
    while len(ims) < n and tries < n * 8:
        tries += 1
        j = rng.integers(len(xs)); cy, cx = ys[j], xs[j]
        if cy - ps // 2 < 0 or cy + ps // 2 >= Hp or cx - ps // 2 < 0 or cx + ps // 2 >= Wp: continue
        p = photo[cy - ps // 2:cy - ps // 2 + ps, cx - ps // 2:cx - ps // 2 + ps]
        br = p.mean(2)
        if br.mean() > 0.78 or (br > 0.9).mean() > 0.12: continue   # reject white-background bleed at the edge
        ims.append(Image.fromarray((np.dstack([p, al]) * 255).astype(np.uint8), "RGBA")); means.append(p.reshape(-1, 3).mean(0))
    return ims, np.array(means)


def render(P, parts, colors, valid, fol_lib, fol_mu, bark_lib, bark_mu, yaw, path, seed=7):
    rng = np.random.default_rng(seed)
    X, Y, Z, SZ = P[:, 0], P[:, 1], P[:, 2], P[:, 3]
    bg = Image.new("RGB", (FW, FH)); dr = ImageDraw.Draw(bg)
    for yy in range(FH):
        t = yy / FH; dr.line([(0, yy), (FW, yy)], fill=tuple((np.array([150, 183, 216.]) * (1 - t) + np.array([224, 231, 224.]) * t).astype(int)))
    dr.ellipse([CX - 230, GROUNDY - 14, CX + 230, GROUNDY + 46], fill=(70, 88, 60))
    canvas = bg.convert("RGBA")
    c_, s_ = math.cos(yaw), math.sin(yaw)
    xr = X * c_ - Y * s_; dep = X * s_ + Y * c_
    sx = CX + xr * SC; sy = GROUNDY - Z * SC
    is_bark = parts > 0
    def match(col, mu, ims):
        k = np.argsort(((mu - col) ** 2).sum(1))[:6]; return ims[int(rng.choice(k))]
    for k in np.argsort(-dep):
        if not valid[k]: continue
        if is_bark[k] and dep[k] > 0: continue          # back-face cull the trunk cylinder
        t = int(max(9, SZ[k] * 3.0))
        if is_bark[k]:
            patch = match(colors[k], bark_mu, bark_lib).resize((t, t))
        else:
            patch = match(colors[k], fol_mu, fol_lib).rotate(float(rng.uniform(0, 360)), expand=True).resize((t, t))
        canvas.alpha_composite(patch, (int(sx[k] - t / 2), int(sy[k] - t / 2)))
    canvas.convert("RGB").save(path); return path


def synthesize(photo_path, genome_path, out_prefix, lod=1.0, yaws=(0.0, 0.5)):
    photo = np.asarray(Image.open(photo_path).convert("RGB")).astype(np.float32) / 255.0
    genome = json.load(open(genome_path))["genome"] if genome_path and os.path.exists(genome_path) else None
    P, parts, src = build_markers(photo, genome, lod=lod)
    colors, valid = marker_colors(photo, parts, src)
    green, bark = _masks(photo)
    fol_lib, fol_mu = pattern_library(photo, green, int(600 * lod), 24, seed=1)
    bark_lib, bark_mu = pattern_library(photo, bark, int(260 * lod), 22, seed=2)
    outs = []
    for i, yaw in enumerate(yaws):
        outs.append(render(P, parts, colors, valid, fol_lib, fol_mu, bark_lib, bark_mu, yaw, f"{out_prefix}_{i}.png"))
    print(f"markers={len(P)} (valid {int(valid.sum())}, foliage {int((parts==0).sum())}, trunk {int((parts>0).sum())})  patches {len(fol_lib)}/{len(bark_lib)}")
    return outs


def _main():
    ap = argparse.ArgumentParser(prog="python -m Construction.cross")
    ap.add_argument("--photo", required=True)
    ap.add_argument("--genome", default=None)
    ap.add_argument("--out", default="Construction/renders/cross")
    ap.add_argument("--lod", type=float, default=1.0)
    a = ap.parse_args()
    for p in synthesize(a.photo, a.genome, a.out, lod=a.lod):
        print("wrote", p)


if __name__ == "__main__":
    _main()
