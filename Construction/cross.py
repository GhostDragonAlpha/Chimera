"""cross.py — THE SYNTHESIS: template markers x photo patterns -> a textured 3D tree.

This is the step that made it work (2026-07-22).  Neither piece alone is enough:
  - the per-splat fit reproduces the photo but is a flat, clipped billboard;
  - the parametric template is a complete 3D tree but generic/hand-guessed.
CROSS them:
  1. the TEMPLATE distributes MARKERS in complete 3D (crown dome + trunk cylinder,
     no clipping, holds up when rotated).  Each marker is coloured by sampling the
     photo at its front projection — the marker says WHERE a pattern goes and WHAT
     colour it is.
  2. the PHOTO is decomposed into real textured PATCHES (the recognized sub-
     patterns — bark fissures, leaf clusters).
  3. each marker MATCHES the patch whose colour is nearest and reproduces that real
     patch in its vicinity.  Foliage markers get leaf patches; bark markers get
     bark patches; the completed (unseen) parts wear the nearest photo pattern.

Result: a complete 3D tree wearing the photo's real bark and foliage texture that
holds up from multiple angles.  Refinement dial = template LEVEL OF DETAIL (`lod`,
marker density): more markers -> finer detail.

CLI:
  python -m Construction.cross --photo <ref.jpg> --genome <trained.json> [--lod 1.0]
"""
from __future__ import annotations
import argparse, json, math, os
import numpy as np
from PIL import Image, ImageDraw


def build_markers(genome: dict, lod: float = 1.0, seed: int = 7):
    """The TEMPLATE: a complete 3D distribution of markers (foliage dome + bark
    cylinder).  Returns (positions Nx4 [x,y,z,size], is_bark bool N).  `lod` scales
    marker density — the level-of-detail dial."""
    g = genome; rng = np.random.default_rng(seed)
    rx, rz, zc = g["rx"], g["rz"], g["zc"]
    def hw(z):
        t = z/g["hf"]; return (g["base_w"]*(1-0.42*t))*(1.0+1.05*math.exp(-t*6))
    fol = []
    for _ in range(26):
        ang = rng.uniform(0, 2*math.pi); rad = math.sqrt(rng.uniform(0.04, 1.0))
        X = math.cos(ang)*rx*rad; Y = math.sin(ang)*rz*1.4*rad
        Z = min(zc + rng.uniform(-0.35, 0.65)*rz - (rad**2)*rz*(0.4+0.5*g["flat"]), zc+rz*0.6)
        cr = rng.uniform(48, 82)
        for _ in range(int(cr*cr*0.05*lod)):
            o = rng.normal(0, cr*0.62, 3)
            zz = Z + o[2] - g["droop"]*((math.hypot(X, Y)/max(rx, 1))**2)*rz*0.5
            fol.append((X+o[0], Y+o[1], zz, rng.uniform(6, 11)))
    bark = []
    for _ in range(int(1300*lod)):
        z = rng.uniform(0, g["hf"]); a = rng.uniform(0, 2*math.pi); w = hw(z)*0.92
        bark.append((math.cos(a)*w, math.sin(a)*w, z, rng.uniform(6, 10)))
    P = np.array(fol + bark, np.float32)
    is_bark = np.array([False]*len(fol) + [True]*len(bark))
    return P, is_bark


# fixed template frame the markers project into
FW, FH, SC = 680, 900, 1.30
CX = FW*0.5; GROUNDY = FH*0.90


def _front(P):
    return CX + P[:, 0]*SC, GROUNDY - P[:, 2]*SC


def target_colors(P, is_bark, photo):
    """CROSS step 1: each marker's target colour = the photo at its front projection
    (the template silhouette aligned to the photo tree's bbox)."""
    Hp, Wp, _ = photo.shape
    fsx, fsy = _front(P)
    tx0, tx1, ty0, ty1 = fsx.min(), fsx.max(), fsy.min(), fsy.max()
    r, g, b = photo[..., 0], photo[..., 1], photo[..., 2]; mx = photo.max(2); mn = photo.min(2)
    green = (g > r) & (g > b) & (g > 0.2) & ((mx-mn) > 0.05)
    reg = np.zeros((Hp, Wp), bool); reg[int(Hp*0.30):, int(Wp*0.30):int(Wp*0.70)] = True
    barkm = reg & (~green) & (mx < 0.72) & (mx > 0.13)
    tys, txs = np.where(green | barkm)
    px0, px1, py0, py1 = txs.min(), txs.max(), tys.min(), tys.max()
    px = np.clip((fsx-tx0)/(tx1-tx0)*(px1-px0)+px0, 0, Wp-1).astype(int)
    py = np.clip((fsy-ty0)/(ty1-ty0)*(py1-py0)+py0, 0, Hp-1).astype(int)
    return photo[py, px], green, barkm


def pattern_library(photo, mask, n, ps, seed):
    """The recognized sub-patterns: real textured patches sampled from the photo,
    each with a soft radial alpha so they blend.  Returns (PIL RGBA images, mean-colours)."""
    rng = np.random.default_rng(seed); Hp, Wp, _ = photo.shape
    ys, xs = np.where(mask)
    yy, xx = np.mgrid[0:ps, 0:ps]; al = np.clip(1.25 - np.hypot((xx-ps/2)/(ps/2), (yy-ps/2)/(ps/2)), 0, 1)
    ims, means = [], []
    for _ in range(n):
        j = rng.integers(len(xs)); cy, cx = ys[j], xs[j]
        if cy-ps//2 < 0 or cy+ps//2 >= Hp or cx-ps//2 < 0 or cx+ps//2 >= Wp: continue
        p = photo[cy-ps//2:cy-ps//2+ps, cx-ps//2:cx-ps//2+ps]
        ims.append(Image.fromarray((np.dstack([p, al])*255).astype(np.uint8), "RGBA"))
        means.append(p.reshape(-1, 3).mean(0))
    return ims, np.array(means)


def render(P, is_bark, colors, fol_lib, fol_mu, bark_lib, bark_mu, yaw, path, seed=7):
    """CROSS step 2+3: for each marker (depth-sorted), stamp the nearest-colour photo
    patch in its vicinity, scaled by marker size, rotated (foliage) for variety."""
    rng = np.random.default_rng(seed)
    X, Y, Z, SZ = P[:, 0], P[:, 1], P[:, 2], P[:, 3]
    bg = Image.new("RGB", (FW, FH)); dr = ImageDraw.Draw(bg)
    for yy in range(FH):
        t = yy/FH; dr.line([(0, yy), (FW, yy)], fill=tuple((np.array([150, 183, 216.])*(1-t)+np.array([224, 231, 224.])*t).astype(int)))
    dr.ellipse([CX-230, GROUNDY-14, CX+230, GROUNDY+46], fill=(70, 88, 60))
    canvas = bg.convert("RGBA")
    c_, s_ = math.cos(yaw), math.sin(yaw)
    xr = X*c_ - Y*s_; dep = X*s_ + Y*c_
    sx = CX + xr*SC; sy = GROUNDY - Z*SC
    def match(col, mu, ims):
        k = np.argsort(((mu-col)**2).sum(1))[:6]; return ims[int(rng.choice(k))]
    for k in np.argsort(-dep):
        t = int(max(9, SZ[k]*3.0))
        if is_bark[k]:
            patch = match(colors[k], bark_mu, bark_lib).resize((t, t))
        else:
            patch = match(colors[k], fol_mu, fol_lib).rotate(float(rng.uniform(0, 360)), expand=True).resize((t, t))
        canvas.alpha_composite(patch, (int(sx[k]-t/2), int(sy[k]-t/2)))
    canvas.convert("RGB").save(path); return path


def synthesize(photo_path, genome_path, out_prefix, lod=1.0, yaws=(0.0, 0.5)):
    photo = np.asarray(Image.open(photo_path).convert("RGB")).astype(np.float32)/255.0
    genome = json.load(open(genome_path))["genome"]
    P, is_bark = build_markers(genome, lod=lod)
    colors, green, barkm = target_colors(P, is_bark, photo)
    fol_lib, fol_mu = pattern_library(photo, green, int(600*lod), 24, seed=1)
    bark_lib, bark_mu = pattern_library(photo, barkm, int(300*lod), 22, seed=2)
    outs = []
    for i, yaw in enumerate(yaws):
        outs.append(render(P, is_bark, colors, fol_lib, fol_mu, bark_lib, bark_mu, yaw, f"{out_prefix}_{i}.png"))
    print(f"markers={len(P)}  foliage_patches={len(fol_lib)}  bark_patches={len(bark_lib)}")
    return outs


def _main():
    ap = argparse.ArgumentParser(prog="python -m Construction.cross")
    ap.add_argument("--photo", required=True)
    ap.add_argument("--genome", required=True, help="trained tree_appearance genome json")
    ap.add_argument("--out", default="Construction/renders/cross")
    ap.add_argument("--lod", type=float, default=1.0, help="template level-of-detail (marker density)")
    a = ap.parse_args()
    for p in synthesize(a.photo, a.genome, a.out, lod=a.lod):
        print("wrote", p)


if __name__ == "__main__":
    _main()
