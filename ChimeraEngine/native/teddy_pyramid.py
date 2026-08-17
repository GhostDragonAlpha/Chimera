# SPIACE T2 — teddy render pyramid: multi-density splat shells from the
# TRELLIS mesh (teddy.ply, 2.4M verts, per-vertex RGB). Render-side DATA ONLY:
# the CA sim keeps running on genomes/teddy.cells (370 cells); this file is
# the skin the viewer draws, with the level picked by the camera LOD law
# (3DGS invariant: splat footprint ~2.5 px at current depth).
#
#   python teddy_pyramid.py [ply] [sim_body_h] [out_stem]
#
# T9: parametrized — sim_body_h defaults to 8 (T1 teddy); the canonical honey
# bear stands 28 sim cells (voxelize_teddy's derived H), and the pyramid
# levels scale with it so the LOD law sees the same per-level footprint.
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
import sys
PLY = Path(sys.argv[1]) if len(sys.argv) > 1 else (
    HERE.parent.parent / "models" / "trellis" / "teddy.ply")

BEAR_BODYH = int(sys.argv[2]) if len(sys.argv) > 2 else 8
                          # sim cells tall (voxelize_teddy); T9 honey = 28
OUT_STEM = sys.argv[3] if len(sys.argv) > 3 else "teddy_shell"
CELL = 0.06             # sim cell world size
LEVELS = [round(h * BEAR_BODYH / 8) for h in [16, 24, 32, 48, 64]]
                          # pyramid heights scale with the body's sim height


def read_ply_verts(path):
    """binary_little_endian PLY -> x, y, z (f64) + r, g, b (f64 0..1).
    Reads exactly the vertex element (faces follow it in the file).
    T10 NOTE: mesh face normals were tried first and FALSIFIED as a normal
    source — winding was inward (radial alignment -0.06) and, worse, the
    per-voxel mean of mixed-winding normals cancels to a random direction
    (alignment 0.02 — the light sweep stayed flat, CV ratio 1.40 < 1.5).
    The derived replacement is the occupancy-gradient normal computed on the
    voxel grid itself (below) — winding-free by construction."""
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
        # T10: per-splat normal. First attempt (occupancy gradient of the raw
        # shell) was FALSIFIED: the shell is one voxel thick, so a surface
        # voxel's occupied 26-neighbors lie mostly ALONG the sheet — the
        # offset sum points tangentially, normals came out near-random
        # (radial alignment 0.05-0.09 across two variants, light-sweep CV
        # ratio 1.17-1.40, bound 1.5). The derived fix: FILL the volume
        # first. Close pinholes with one 6-connected dilation, flood the
        # exterior by repeated dilation from the grid boundary, interior =
        # not exterior; then the occupancy gradient on the FILLED volume has
        # interior voxels on the inside of every surface cell and the negated
        # sum points cleanly outward.
        nxg = int(kx.max()) + 1; nyg = int(ky.max()) + 1; nzg = int(kz.max()) + 1
        occ = np.zeros((nxg, nyg, nzg), dtype=bool)
        occ[kx, ky, kz] = True
        dil = occ.copy()
        for ax in range(3):
            for sh in (1, -1):
                dil |= np.roll(occ, sh, axis=ax)
        # np.roll wraps; the bear never touches the wrap boundary (shifted
        # non-negative with a margin from floor()), so wrap fill is harmless.
        ext = np.zeros_like(dil)
        ext[0, :, :] = ext[-1, :, :] = True
        ext[:, 0, :] = ext[:, -1, :] = True
        ext[:, :, 0] = ext[:, :, -1] = True
        ext &= ~dil
        while True:
            grown = ext.copy()
            for ax in range(3):
                for sh in (1, -1):
                    grown |= np.roll(ext, sh, axis=ax)
            grown &= ~dil
            if (grown == ext).all():
                break
            ext = grown
        filled = dil | ~ext
        print(f"  fill: surface {n}, interior {int((~ext & ~dil).sum())}, "
              f"grid {nxg}x{nyg}x{nzg}")
        # gradient of the FILLED occupancy per surface voxel, via the idx map
        # plus a filled-grid probe for neighbors outside the surface set
        snx = np.zeros(n); sny = np.zeros(n); snz = np.zeros(n)
        for i in range(n):
            bx0, by0, bz0 = int(kx[i]), int(ky[i]), int(kz[i])
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    for dz in (-1, 0, 1):
                        if dx == 0 and dy == 0 and dz == 0:
                            continue
                        if 0 <= bx0+dx < nxg and 0 <= by0+dy < nyg \
                                and 0 <= bz0+dz < nzg \
                                and filled[bx0+dx, by0+dy, bz0+dz]:
                            snx[i] += dx; sny[i] += dy; snz[i] += dz
        ln = np.sqrt(snx * snx + sny * sny + snz * snz)
        ok = ln > 1e-9
        nnx = np.where(ok, -snx / np.maximum(ln, 1e-9), 0.0)
        nny = np.where(ok, -sny / np.maximum(ln, 1e-9), 1.0)
        nnz = np.where(ok, -snz / np.maximum(ln, 1e-9), 0.0)
        # thin-shell gradient normals are noisy (measured: radial alignment
        # 0.05 — each surface voxel sees few occupied neighbors). Two 50/50
        # neighbor-mean smoothing passes, same schedule as the color low-pass
        # above, then re-unit. Measured after the fix: alignment ~0.5+.
        for _pass in range(2):
            tx = np.zeros(n); ty = np.zeros(n); tz = np.zeros(n); tc = np.zeros(n)
            for i in range(n):
                bx0, by0, bz0 = int(kx[i]), int(ky[i]), int(kz[i])
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        for dz in (-1, 0, 1):
                            if dx == 0 and dy == 0 and dz == 0:
                                continue
                            j = idx.get((bx0 + dx, by0 + dy, bz0 + dz))
                            if j is not None:
                                tx[i] += nnx[j]; ty[i] += nny[j]; tz[i] += nnz[j]
                                tc[i] += 1
            has = tc > 0
            nnx = np.where(has, 0.5 * nnx + 0.5 * tx / np.maximum(tc, 1), nnx)
            nny = np.where(has, 0.5 * nny + 0.5 * ty / np.maximum(tc, 1), nny)
            nnz = np.where(has, 0.5 * nnz + 0.5 * tz / np.maximum(tc, 1), nnz)
            ln = np.sqrt(nnx * nnx + nny * nny + nnz * nnz)
            ok = ln > 1e-9
            nnx = np.where(ok, nnx / np.maximum(ln, 1e-9), 0.0)
            nny = np.where(ok, nny / np.maximum(ln, 1e-9), 1.0)
            nnz = np.where(ok, nnz / np.maximum(ln, 1e-9), 0.0)
        nor = np.stack([nnx, nny, nnz], axis=1).round(3)
        # measured sanity: outward alignment vs centroid-radial
        rad = pos - pos.mean(axis=0)
        rad /= np.linalg.norm(rad, axis=1, keepdims=True)
        align = float((nor * rad).sum(axis=1).mean())
        levels.append({"h": h, "cell": round(cell_world, 5), "n": n,
                       "pos": pos.tolist(), "col": col.tolist(),
                       "nor": nor.tolist()})
        print(f"level h={h:3d}  cell={cell_world:.4f} units  splats={n}  "
              f"normal-radial alignment {align:.3f}")

    out = GENOMES / f"{OUT_STEM}.json"
    out.write_text(json.dumps({"levels": levels}, separators=(",", ":")),
                   encoding="utf-8")
    print(f"wrote {out} ({out.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
