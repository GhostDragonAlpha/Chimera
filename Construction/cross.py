"""cross.py — THE SYNTHESIS: template markers x photo patterns -> a textured 3D tree.

Neither piece alone works: a per-splat pixel fit is a flat, clipped billboard; a
parametric template is complete-3D but generically coloured. CROSS them: the TEMPLATE
distributes MARKERS in complete 3D (trunk cylinder + branch limbs + foliage dome);
each marker is LABELLED by which subpart of the whole it is (trunk/branch/root/
foliage) and coloured by sampling the photo; then a library of real textured PATCHES
cut from the photo is matched to each marker and stamped in its vicinity.

Two rules the subpart label enforces (2026-07-22, from operator review of the
spinning tree):
  - MATERIAL BY PART: a bark part (trunk/branch/root) NEVER takes a green sample,
    a foliage part never takes bark — fixes "the trunk is green".
  - SKY IS NOT STRUCTURE: a foliage marker that projects onto sky is DROPPED (the
    bright-white halo puffs) — the operator's "negative value".
Bark cylinders are back-face culled at render so the trunk stops "fighting for
dominance" as it spins.

CLI:
  python -m Construction.cross --photo <ref.jpg> --genome <trained.json> [--lod 1.0]
"""
from __future__ import annotations
import argparse, json, math, os
import numpy as np
from PIL import Image, ImageDraw

PARTS = {"foliage": 0, "trunk": 1, "branch": 2, "root": 3}
FW, FH, SC = 680, 900, 1.30
CX = FW * 0.5; GROUNDY = FH * 0.90


def build_markers(genome: dict, lod: float = 1.0, seed: int = 7):
    """The TEMPLATE: a complete 3D marker set, each LABELLED by subpart.
    Returns (P Nx4 [x,y,z,size], parts N int).  `lod` scales density."""
    g = genome; rng = np.random.default_rng(seed)
    rx, rz, zc, hf, bw = g["rx"], g["rz"], g["zc"], g["hf"], g["base_w"]
    def hw(z):
        t = z / hf; return (bw * (1 - 0.42 * t)) * (1.0 + 1.05 * math.exp(-t * 6))
    P, part = [], []
    # trunk cylinder
    for _ in range(int(950 * lod)):
        z = rng.uniform(0, hf); a = rng.uniform(0, 2 * math.pi); w = hw(z) * 0.9
        P.append((math.cos(a) * w, math.sin(a) * w, z, rng.uniform(4.5, 8))); part.append(1)
    # root flare (wider, low)
    for _ in range(int(160 * lod)):
        z = rng.uniform(0, hf * 0.12); a = rng.uniform(0, 2 * math.pi); w = hw(z) * 1.15
        P.append((math.cos(a) * w, math.sin(a) * w, z, rng.uniform(5, 9))); part.append(3)
    # branch limbs: from the fork up into the canopy, tapering (the missing skeleton)
    fork = (0.0, 0.0, hf); segs = []
    nmain = 5
    for i in range(nmain):
        ang = i * 2 * math.pi / nmain + rng.uniform(-0.3, 0.3); el = rng.uniform(0.55, 1.05)
        tip = (math.cos(ang) * rx * 0.65 * math.cos(el), math.sin(ang) * rz * 0.65 * math.cos(el),
               zc + rng.uniform(-0.25, 0.35) * rz)
        segs.append((fork, tip, bw * 0.5, bw * 0.14))
    for (a0, b0, r0, r1) in list(segs):                       # one level of sub-branches
        for _ in range(2):
            t = rng.uniform(0.4, 0.8); mid = tuple(a0[k] + (b0[k] - a0[k]) * t for k in range(3))
            tip = (b0[0] + rng.uniform(-70, 70), b0[1] + rng.uniform(-70, 70), b0[2] + rng.uniform(-10, 60))
            segs.append((mid, tip, r1, r1 * 0.5))
    tips = []
    for (a0, b0, r0, r1) in segs:
        L = math.dist(a0, b0); n = int(L / 6 * lod) + 3
        for i in range(n):
            t = i / max(1, n - 1); p = [a0[k] + (b0[k] - a0[k]) * t for k in range(3)]
            w = r0 + (r1 - r0) * t; o = rng.normal(0, w * 0.5, 3)
            P.append((p[0] + o[0], p[1] + o[1], p[2] + o[2], max(2.5, w * 0.7))); part.append(2)
        tips.append(b0)
    # foliage dome, biased onto branch tips (so the crown sits on the limbs)
    for _ in range(26):
        if tips and rng.random() < 0.6:
            b = tips[rng.integers(len(tips))]; X, Y, Z = b[0] + rng.normal(0, 45), b[1] + rng.normal(0, 45), b[2] + rng.normal(0, 40)
        else:
            ang = rng.uniform(0, 2 * math.pi); rad = math.sqrt(rng.uniform(0.04, 1.0))
            X = math.cos(ang) * rx * rad; Y = math.sin(ang) * rz * 1.4 * rad
            Z = min(zc + rng.uniform(-0.35, 0.65) * rz - (rad ** 2) * rz * (0.4 + 0.5 * g["flat"]), zc + rz * 0.6)
        cr = rng.uniform(45, 80)
        for _ in range(int(cr * cr * 0.05 * lod)):
            o = rng.normal(0, cr * 0.62, 3)
            zz = Z + o[2] - g["droop"] * ((math.hypot(X, Y) / max(rx, 1)) ** 2) * rz * 0.5
            P.append((X + o[0], Y + o[1], zz, rng.uniform(6, 11))); part.append(0)
    return np.array(P, np.float32), np.array(part)


def _front(P):
    return CX + P[:, 0] * SC, GROUNDY - P[:, 2] * SC


def target_colors(P, parts, photo):
    """CROSS colour + the two enforcement rules. Returns (colors Nx3, valid N bool).
    Bark parts never green/sky (drawn from the bark palette instead); foliage on sky
    is dropped; foliage on bark is redrawn from the foliage palette."""
    Hp, Wp, _ = photo.shape
    fsx, fsy = _front(P)
    tx0, tx1, ty0, ty1 = fsx.min(), fsx.max(), fsy.min(), fsy.max()
    r, g, b = photo[..., 0], photo[..., 1], photo[..., 2]; mx = photo.max(2); mn = photo.min(2)
    green = (g > r) & (g > b) & (g > 0.2) & ((mx - mn) > 0.05)
    reg = np.zeros((Hp, Wp), bool); reg[int(Hp * 0.30):, int(Wp * 0.30):int(Wp * 0.70)] = True
    barkm = reg & (~green) & (mx < 0.72) & (mx > 0.13)
    tys, txs = np.where(green | barkm); px0, px1, py0, py1 = txs.min(), txs.max(), tys.min(), tys.max()
    folpal = photo[green]; barkpal = photo[barkm] if barkm.any() else np.array([[0.36, 0.30, 0.22]], np.float32)
    px = np.clip((fsx - tx0) / (tx1 - tx0) * (px1 - px0) + px0, 0, Wp - 1).astype(int)
    py = np.clip((fsy - ty0) / (ty1 - ty0) * (py1 - py0) + py0, 0, Hp - 1).astype(int)
    col = photo[py, px].copy()
    sr, sg, sb = col[:, 0], col[:, 1], col[:, 2]; smx = col.max(1); smn = col.min(1)
    is_green = (sg > sr) & (sg > sb) & ((smx - smn) > 0.05)
    is_sky = (smx > 0.72) & ((smx - smn) < 0.12)
    rng = np.random.default_rng(3)
    is_bark_part = parts > 0
    valid = np.ones(len(P), bool)
    # bark part sampled non-bark -> draw a real bark colour
    fix = is_bark_part & (is_green | is_sky)
    col[fix] = barkpal[rng.integers(0, len(barkpal), int(fix.sum()))]
    # foliage on sky -> DROP; foliage on bark -> draw a real foliage colour
    fol = ~is_bark_part
    valid[fol & is_sky] = False
    ffix = fol & (~is_green) & (~is_sky)
    col[ffix] = folpal[rng.integers(0, len(folpal), int(ffix.sum()))]
    return col, valid


def pattern_library(photo, mask, n, ps, seed):
    rng = np.random.default_rng(seed); Hp, Wp, _ = photo.shape
    ys, xs = np.where(mask)
    yy, xx = np.mgrid[0:ps, 0:ps]; al = np.clip(1.25 - np.hypot((xx - ps / 2) / (ps / 2), (yy - ps / 2) / (ps / 2)), 0, 1)
    ims, means = [], []
    for _ in range(n):
        j = rng.integers(len(xs)); cy, cx = ys[j], xs[j]
        if cy - ps // 2 < 0 or cy + ps // 2 >= Hp or cx - ps // 2 < 0 or cx + ps // 2 >= Wp: continue
        p = photo[cy - ps // 2:cy - ps // 2 + ps, cx - ps // 2:cx - ps // 2 + ps]
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
    is_bark_part = parts > 0
    def match(col, mu, ims):
        k = np.argsort(((mu - col) ** 2).sum(1))[:6]; return ims[int(rng.choice(k))]
    for k in np.argsort(-dep):
        if not valid[k]: continue
        if is_bark_part[k] and dep[k] > 0: continue          # back-face cull the bark cylinders
        t = int(max(9, SZ[k] * 3.0))
        if is_bark_part[k]:
            patch = match(colors[k], bark_mu, bark_lib).resize((t, t))
        else:
            patch = match(colors[k], fol_mu, fol_lib).rotate(float(rng.uniform(0, 360)), expand=True).resize((t, t))
        canvas.alpha_composite(patch, (int(sx[k] - t / 2), int(sy[k] - t / 2)))
    canvas.convert("RGB").save(path); return path


def synthesize(photo_path, genome_path, out_prefix, lod=1.0, yaws=(0.0, 0.5)):
    photo = np.asarray(Image.open(photo_path).convert("RGB")).astype(np.float32) / 255.0
    genome = json.load(open(genome_path))["genome"]
    P, parts = build_markers(genome, lod=lod)
    colors, valid = target_colors(P, parts, photo)
    green = (photo[..., 1] > photo[..., 0]) & (photo[..., 1] > photo[..., 2]) & (photo[..., 1] > 0.2) & ((photo.max(2) - photo.min(2)) > 0.05)
    reg = np.zeros(photo.shape[:2], bool); reg[int(photo.shape[0] * 0.30):, int(photo.shape[1] * 0.30):int(photo.shape[1] * 0.70)] = True
    barkm = reg & (~green) & (photo.max(2) < 0.72) & (photo.max(2) > 0.13)
    fol_lib, fol_mu = pattern_library(photo, green, int(600 * lod), 24, seed=1)
    bark_lib, bark_mu = pattern_library(photo, barkm, int(300 * lod), 22, seed=2)
    outs = []
    for i, yaw in enumerate(yaws):
        outs.append(render(P, parts, colors, valid, fol_lib, fol_mu, bark_lib, bark_mu, yaw, f"{out_prefix}_{i}.png"))
    print(f"markers={len(P)} (valid {int(valid.sum())})  foliage_patches={len(fol_lib)} bark_patches={len(bark_lib)}")
    return outs


def _main():
    ap = argparse.ArgumentParser(prog="python -m Construction.cross")
    ap.add_argument("--photo", required=True)
    ap.add_argument("--genome", required=True)
    ap.add_argument("--out", default="Construction/renders/cross")
    ap.add_argument("--lod", type=float, default=1.0)
    a = ap.parse_args()
    for p in synthesize(a.photo, a.genome, a.out, lod=a.lod):
        print("wrote", p)


if __name__ == "__main__":
    _main()
