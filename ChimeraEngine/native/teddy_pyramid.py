# SPIACE T2 — teddy render pyramid: multi-density splat shells from the
# TRELLIS mesh (teddy.ply, 2.4M verts, per-vertex RGB). Render-side DATA ONLY:
# the CA sim keeps running on genomes/teddy.cells (370 cells); this file is
# the skin the viewer draws, with the level picked by the camera LOD law
# (3DGS invariant: splat footprint ~2.5 px at current depth).
#
#   python teddy_pyramid.py
#
# Emits genomes/teddy_shell.json:
#   { "levels": [ { "h": <grid height in cells>, "cell": <world units>,
#                   "n": N, "pos": [[x,y,z]...], "col": [[r,g,b]...] } ... ] }
# Positions are in CA cell space (same axes as teddy.cells: y up = model z)
# but FRACTIONAL — sub-cell placement is the whole point of the shell.

import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
GENOMES = HERE / "genomes"
PLY = HERE.parent.parent / "models" / "trellis" / "teddy.ply"

BEAR_BODYH = 8          # the sim's teddy stands 8 sim-cells tall (voxelize_teddy)
CELL = 0.06             # sim cell world size
LEVELS = [16, 24, 32, 48, 64]      # pyramid: grid heights in shell cells


def read_ply_verts(path):
    """binary_little_endian PLY -> x, y, z (f64) + r, g, b (f64 0..1).
    Reads exactly the vertex element (faces follow it in the file)."""
    with open(path, "rb") as f:
        vcount = 0
        while True:
            line = f.readline()
            t = line.strip()
            if t.startswith(b"element vertex"):
                vcount = int(t.split()[2])
            if t == b"end_header":
                break
        off = f.tell()
    dt = np.dtype([("x", "<f4"), ("y", "<f4"), ("z", "<f4"),
                   ("red", "u1"), ("green", "u1"), ("blue", "u1")])
    with open(path, "rb") as f:
        f.seek(off)
        v = np.fromfile(f, dtype=dt, count=vcount)
    return (v["x"].astype(np.float64), v["y"].astype(np.float64),
            v["z"].astype(np.float64), v["red"].astype(np.float64) / 255,
            v["green"].astype(np.float64) / 255, v["blue"].astype(np.float64) / 255)


def main():
    x, y, z, r, g, b = read_ply_verts(PLY)
    print(f"loaded {len(x)} verts from {PLY.name}")
    H = float(z.max() - z.min())

    levels = []
    for h in LEVELS:
        # shell cells per model unit so the shell stands h cells tall;
        # shell cell world size keeps the teddy 8 sim cells = 0.48 units tall.
        s = h / H
        cell_world = (BEAR_BODYH * CELL) / h
        # CA axes: x = model x, y(up) = model z, z = model y — same mapping
        # as voxelize_teddy.py, but keeping the fractional remainder.
        fx, fy, fz = x * s, z * s, y * s
        ix = np.floor(fx).astype(np.int32)
        iy = np.floor(fy).astype(np.int32)
        iz = np.floor(fz).astype(np.int32)
        # shift to non-negative before key packing (model coords go negative)
        ix -= ix.min(); iy -= iy.min(); iz -= iz.min()
        key = (ix.astype(np.int64) * 100000 + iy) * 100000 + iz
        uniq, inv = np.unique(key, return_inverse=True)
        n = len(uniq)
        # voxel center = mean of its verts (sub-cell position + mean color).
        # Positions must be reported in the UNSHIFTED frame the sim uses:
        # fx/fy/fz are model-units x s, so subtracting the shift restores it.
        cx = np.bincount(inv, weights=fx) / np.bincount(inv)
        cy = np.bincount(inv, weights=fy) / np.bincount(inv)
        cz = np.bincount(inv, weights=fz) / np.bincount(inv)
        cr = np.bincount(inv, weights=r) / np.bincount(inv)
        cg = np.bincount(inv, weights=g) / np.bincount(inv)
        cb = np.bincount(inv, weights=b) / np.bincount(inv)
        # spatial low-pass: TRELLIS vertex colors carry ~1.5% saturated
        # outlier speckle (measured) — one 26-neighbor smoothing pass,
        # 50% self + 50% neighborhood mean, kills the sparkle without
        # washing the brown (mean RGB 0.43/0.31/0.20, measured)
        idx = {}
        kx = uniq // 100000 // 100000
        ky = (uniq // 100000) % 100000
        kz = uniq % 100000
        for i in range(n):
            idx[(int(kx[i]), int(ky[i]), int(kz[i]))] = i
        for _pass in range(2):                   # two 50/50 smoothing passes
            sr = np.zeros(n); sg = np.zeros(n); sb = np.zeros(n); sc = np.zeros(n)
            for i in range(n):
                bx0, by0, bz0 = int(kx[i]), int(ky[i]), int(kz[i])
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        for dz in (-1, 0, 1):
                            if dx == 0 and dy == 0 and dz == 0:
                                continue
                            j = idx.get((bx0 + dx, by0 + dy, bz0 + dz))
                            if j is not None:
                                sr[i] += cr[j]; sg[i] += cg[j]; sb[i] += cb[j]
                                sc[i] += 1
            has = sc > 0
            cr = np.where(has, 0.5 * cr + 0.5 * sr / np.maximum(sc, 1), cr)
            cg = np.where(has, 0.5 * cg + 0.5 * sg / np.maximum(sc, 1), cg)
            cb = np.where(has, 0.5 * cb + 0.5 * sb / np.maximum(sc, 1), cb)
        # deviation clamp: a splat may differ from its neighborhood mean by at
        # most 0.15/channel — regional features (ribbon, muzzle) survive
        # because their neighborhood shares them; isolated specks get reeled in
        sr = np.zeros(n); sg = np.zeros(n); sb = np.zeros(n)
        for i in range(n):
            bx0, by0, bz0 = int(kx[i]), int(ky[i]), int(kz[i])
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    for dz in (-1, 0, 1):
                        if dx == 0 and dy == 0 and dz == 0:
                            continue
                        j = idx.get((bx0 + dx, by0 + dy, bz0 + dz))
                        if j is not None:
                            sr[i] += cr[j]; sg[i] += cg[j]; sb[i] += cb[j]
        has = sc > 0
        mr = np.where(has, sr / np.maximum(sc, 1), cr)
        mg = np.where(has, sg / np.maximum(sc, 1), cg)
        mb = np.where(has, sb / np.maximum(sc, 1), cb)
        D = 0.15
        cr = mr + np.clip(cr - mr, -D, D)
        cg = mg + np.clip(cg - mg, -D, D)
        cb = mb + np.clip(cb - mb, -D, D)
        # luminance floor + gain: TRELLIS bakes crevice shadow into the vertex
        # colors (measured: dark tail renders as holes). Lift hue-preservingly
        # to L>=0.20, then global gain 1.22 toward the flat-debug tan that
        # read correctly on screen (0.55/0.42/0.30 pre-shading).
        lum = 0.299 * cr + 0.587 * cg + 0.114 * cb
        lift = np.maximum(1.0, 0.20 / np.maximum(lum, 1e-3))
        cr = np.clip(cr * lift * 1.22, 0, 1)
        cg = np.clip(cg * lift * 1.22, 0, 1)
        cb = np.clip(cb * lift * 1.22, 0, 1)
        pos = np.stack([cx, cy, cz], axis=1).round(3)
        col = np.stack([cr, cg, cb], axis=1).round(3)
        levels.append({"h": h, "cell": round(cell_world, 5), "n": n,
                       "pos": pos.tolist(), "col": col.tolist()})
        print(f"level h={h:3d}  cell={cell_world:.4f} units  splats={n}")

    out = GENOMES / "teddy_shell.json"
    out.write_text(json.dumps({"levels": levels}, separators=(",", ":")),
                   encoding="utf-8")
    print(f"wrote {out} ({out.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
