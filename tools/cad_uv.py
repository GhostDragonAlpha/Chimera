#!/usr/bin/env python
"""cad_uv.py -- TEST A3 (UV correctness) + TEST B2 (chain proof through the
GLB artifact), pre-registered in docs/THE_UV_METHOD.md RESULTS. Read that
file before touching this one.

  TEST A3: seam-cut (duplicated u=1.0 column) + equal-area v UVs are
           injective off-cut and constant-density per quad.
  TEST B2: TEXCOORD_0 read BACK out of cad_bear_uv.glb reproduces the
           analytic packed UVs, and a per-pixel render through the read-back
           UVs equals the per-pixel reference (the chain proven through the
           actual artifact, before any AI sheet is admitted at link 2).

  .venv-gs/Scripts/python.exe -u tools/cad_uv.py
"""
from __future__ import annotations

import json
import struct
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cad_core import PRIMS
from cad_mesh import SEG, uv_ellipsoid, capsule, build_glb

# ------------------------------------------------------------- material map
def material_of(name: str) -> str:
    if name.startswith(("sweater", "sleeve")):
        return "sweater"
    if name.startswith("eye"):
        return "eye"
    if name == "nose":
        return "nose"
    return "fur"


# ------------------------------------------------------------- TEST A3
NCOLS = SEG + 1    # duplicated seam column (u=0 and u=1 sides of the cut)
QUAD_BOUND = 2.0   # pre-registered per-quad density bound (THE_UV_METHOD A3)


def tessellate(p):
    if p["kind"] == "ell":
        return uv_ellipsoid(p["c"], p["r"], p.get("sole"))
    return capsule(p["a"], p["b"], p["rad"])


def test_a() -> bool:
    print("== TEST A3: seam-cut equal-area UV (bounds: docs/THE_UV_METHOD.md) ==")
    ok_all = True
    for p in PRIMS:
        v, _n, idx, uv = tessellate(p)
        nrows = len(v) // NCOLS
        du = 1.0 / SEG
        uv64 = uv.astype(np.float64)
        v64 = v.astype(np.float64)

        # tears: row neighbors step exactly du in u and share v; column
        # neighbors share u EXACTLY with v strictly increasing down-column.
        # the cut (every row): j=0 and j=SEG share 3D position and v, and
        # differ by exactly 1.0 in u.
        tears, cut_bad = 0, 0
        for i in range(nrows):
            k0, k1 = i * NCOLS, i * NCOLS + SEG
            if (np.abs(v64[k0] - v64[k1]) > 1e-5).any() \
                    or abs(uv64[k0, 1] - uv64[k1, 1]) > 1e-6 \
                    or abs(uv64[k1, 0] - uv64[k0, 0] - 1.0) > 1e-6:
                cut_bad += 1
            for j in range(SEG):
                k = i * NCOLS + j
                if abs(abs(uv64[k, 0] - uv64[k + 1, 0]) - du) > 1e-6 \
                        or abs(uv64[k, 1] - uv64[k + 1, 1]) > 1e-6:
                    tears += 1
                if i < nrows - 1:
                    kd = k + NCOLS
                    if abs(uv64[k, 0] - uv64[kd, 0]) > 1e-6 \
                            or not uv64[kd, 1] > uv64[k, 1]:
                        tears += 1

        # distortion: per-QUAD density (consecutive triangle pairs share a
        # grid cell; the pole fan's half-cell pairs with its degenerate twin)
        t = idx.reshape(-1, 3)
        a3 = 0.5 * np.linalg.norm(
            np.cross(v64[t[:, 1]] - v64[t[:, 0]],
                     v64[t[:, 2]] - v64[t[:, 0]]), axis=1)
        d1 = uv64[t[:, 1]] - uv64[t[:, 0]]
        d2 = uv64[t[:, 2]] - uv64[t[:, 0]]
        auv = 0.5 * np.abs(d1[:, 0] * d2[:, 1] - d1[:, 1] * d2[:, 0])
        deg = a3 < 1e-12
        q3 = a3.reshape(-1, 2).sum(1)
        quv = auv.reshape(-1, 2).sum(1)
        qdeg = q3 < 1e-12
        dens = q3[~qdeg] / quv[~qdeg]
        ratio = float(dens.max() / dens.min())
        dens_t = a3[~deg] / auv[~deg]
        ratio_t = float(dens_t.max() / dens_t.min())
        ok = tears == 0 and cut_bad == 0 and ratio <= QUAD_BOUND
        ok_all &= ok
        print(f"  {p['name']:14s} tears={tears} cut_bad={cut_bad} "
              f"deg={int(deg.sum()):4d}  quad ratio={ratio:6.3f} "
              f"(bound {QUAD_BOUND})  tri ratio={ratio_t:6.3f}  "
              f"{'OK' if ok else 'FAIL'}")
    print(f"TEST A3: {'PASS' if ok_all else 'FAIL'}")
    return ok_all


# ------------------------------------------------------------- TEST B
TILE = 256          # px per atlas tile
COLS, ROWS = 5, 4   # atlas grid (19 parts)
GUT = 0.02          # gutter, matches cad_mesh --uv packing
RENDER = 512        # orthographic render resolution

MAT = {  # base rgb, noise std  (KNOWN statistics -- the placeholder sheet)
    "fur":     ((0.45, 0.30, 0.18), 0.040),
    "sweater": ((0.20, 0.50, 0.25), 0.030),
    "eye":     ((0.05, 0.04, 0.04), 0.010),
    "nose":    ((0.12, 0.08, 0.06), 0.010),
}
CHECKER_PX = 16     # spatial-identity signal period within a tile
CHECKER_AMP = 0.05


def placeholder_sheet(seed: int = 0) -> np.ndarray:
    """The atlas image: one tile per part, per-material known stats + checker."""
    rng = np.random.default_rng(seed)
    img = np.zeros((ROWS * TILE, COLS * TILE, 3))
    yy, xx = np.mgrid[0:ROWS * TILE, 0:COLS * TILE]
    checker = (((xx // CHECKER_PX) + (yy // CHECKER_PX)) % 2) * 2 - 1  # +-1
    for k, p in enumerate(PRIMS):
        base, std = MAT[material_of(p["name"])]
        r0, c0 = (k // COLS) * TILE, (k % COLS) * TILE
        tile = np.array(base) + rng.normal(0, std, (TILE, TILE, 3))
        img[r0:r0 + TILE, c0:c0 + TILE] = tile
    img += (CHECKER_AMP * checker)[..., None]
    return np.clip(img, 0, 1)


def bilinear(img: np.ndarray, u: np.ndarray, vv: np.ndarray) -> np.ndarray:
    """Sample img (H,W,3) at float uv in [0,1] (v down, matching image rows)."""
    h, w = img.shape[:2]
    x = np.clip(u, 0, 1) * (w - 1)
    y = np.clip(vv, 0, 1) * (h - 1)
    x0, y0 = np.floor(x).astype(int), np.floor(y).astype(int)
    x1, y1 = np.minimum(x0 + 1, w - 1), np.minimum(y0 + 1, h - 1)
    fx, fy = (x - x0)[:, None], (y - y0)[:, None]
    return (img[y0, x0] * (1 - fx) * (1 - fy) + img[y0, x1] * fx * (1 - fy)
            + img[y1, x0] * (1 - fx) * fy + img[y1, x1] * fx * fy)


def render_part(v: np.ndarray, uv_atlas: np.ndarray, idx: np.ndarray,
                sheet: np.ndarray, per_pixel: bool) -> tuple[np.ndarray, np.ndarray]:
    """Orthographic z-buffer render of ONE part, camera +Z -> -Z.
    per_pixel=False: vertex colors (the chain: sheet sampled AT VERTICES,
    interpolated). per_pixel=True: sheet sampled per-pixel at interpolated
    UV (the reference mapping). Returns (rgb, mask)."""
    img = np.zeros((RENDER, RENDER, 3))
    zbuf = np.full((RENDER, RENDER), -np.inf)
    m = v.min(0)
    s = (v.max(0) - m)[:2].max()
    c = (v.min(0) + v.max(0))[:2] / 2
    px = (v[:, 0] - c[0]) / s * (RENDER * 0.9) + RENDER / 2
    py = (v[:, 1] - c[1]) / s * (RENDER * 0.9) + RENDER / 2
    vcol = bilinear(sheet, uv_atlas[:, 0], uv_atlas[:, 1]) if not per_pixel else None
    for a, b, d in idx.reshape(-1, 3):
        xa, xb, xd = px[a], px[b], px[d]
        ya, yb, yd = py[a], py[b], py[d]
        x0, x1 = max(int(min(xa, xb, xd)) - 1, 0), min(int(max(xa, xb, xd)) + 2, RENDER)
        y0, y1 = max(int(min(ya, yb, yd)) - 1, 0), min(int(max(ya, yb, yd)) + 2, RENDER)
        if x0 >= x1 or y0 >= y1:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1) + 0.5, np.arange(y0, y1) + 0.5)
        den = (yb - yd) * (xa - xd) + (xd - xb) * (ya - yd)
        if abs(den) < 1e-12:
            continue
        w0 = ((yb - yd) * (gx - xd) + (xd - xb) * (gy - yd)) / den
        w1 = ((yd - ya) * (gx - xd) + (xa - xd) * (gy - yd)) / den
        w2 = 1 - w0 - w1
        inside = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
        if not inside.any():
            continue
        z = w0 * v[a, 2] + w1 * v[b, 2] + w2 * v[d, 2]
        sub = img[y0:y1, x0:x1]
        zsub = zbuf[y0:y1, x0:x1]
        win = inside & (z > zsub)
        if not win.any():
            continue
        if per_pixel:
            uu = w0 * uv_atlas[a, 0] + w1 * uv_atlas[b, 0] + w2 * uv_atlas[d, 0]
            vv2 = w0 * uv_atlas[a, 1] + w1 * uv_atlas[b, 1] + w2 * uv_atlas[d, 1]
            col = bilinear(sheet, uu[win], vv2[win])
        else:
            col = (w0[win, None] * vcol[a] + w1[win, None] * vcol[b]
                   + w2[win, None] * vcol[d])
        zsub[win] = z[win]
        sub[win] = col
    mask = zbuf > -np.inf
    return img, mask


def pack_uv(uv: np.ndarray, k: int) -> np.ndarray:
    """Atlas packing, same formula as cad_mesh.build_glb --uv."""
    uva = uv.copy()
    uva[:, 0] = (k % COLS + GUT + uva[:, 0] * (1 - 2 * GUT)) / COLS
    uva[:, 1] = (k // COLS + GUT + uva[:, 1] * (1 - 2 * GUT)) / ROWS
    return uva


def read_glb_uv(path: Path) -> list[np.ndarray]:
    """TEXCOORD_0 of every primitive, read BACK out of the written GLB."""
    raw = path.read_bytes()
    assert raw[:4] == b"glTF", "not a GLB"
    js, bin_ = None, None
    off = 12
    while off < len(raw):
        clen, ctype = struct.unpack_from("<II", raw, off)
        chunk = raw[off + 8: off + 8 + clen]
        if ctype == 0x4E4F534A:        # JSON
            js = json.loads(chunk)
        elif ctype == 0x004E4942:      # BIN
            bin_ = chunk
        off += 8 + clen
    out = []
    for prim in js["meshes"][0]["primitives"]:
        ad = js["accessors"][prim["attributes"]["TEXCOORD_0"]]
        bv = js["bufferViews"][ad["bufferView"]]
        start = bv.get("byteOffset", 0) + ad.get("byteOffset", 0)
        assert ad["componentType"] == 5126 and ad["type"] == "VEC2"
        out.append(np.frombuffer(bin_, np.float32, ad["count"] * 2,
                                 start).reshape(-1, 2).copy())
    return out


def test_b() -> bool:
    print("== TEST B2: chain proof THROUGH the GLB artifact ==")
    glb = Path("models/cad_bear/cad_bear_uv.glb")
    build_glb(glb, with_uv=True)            # the artifact under test
    readback = read_glb_uv(glb)
    assert len(readback) == len(PRIMS)
    sheet = placeholder_sheet()
    # link 3 EXTRACT: per-tile channel stats (the sheet's own known stats)
    print("  extracted sheet stats (per material, mean/std, x255):")
    seen = {}
    for k, p in enumerate(PRIMS):
        mat = material_of(p["name"])
        if mat in seen:
            continue
        r0, c0 = (k // COLS) * TILE, (k % COLS) * TILE
        t = sheet[r0:r0 + TILE, c0:c0 + TILE].reshape(-1, 3) * 255
        seen[mat] = True
        print(f"    {mat:8s} mean=({t.mean(0)[0]:6.2f},{t.mean(0)[1]:6.2f},"
              f"{t.mean(0)[2]:6.2f})  std=({t.std(0)[0]:5.2f},{t.std(0)[1]:5.2f},"
              f"{t.std(0)[2]:5.2f})")
    # links 1+4+5: analytic UV -> atlas pack -> WRITE GLB -> READ BACK ->
    # per-pixel render == per-pixel reference (both per-pixel: that is what
    # a real rasterizer does; TEST B's vertex-sampled chain fired its
    # falsifier on sub-triangle sheet content)
    tol = 2.0 / 255
    ok_all = True
    worst_mean, worst_corr, worst_uv = 0.0, 1.0, 0.0
    for k, p in enumerate(PRIMS):
        v, _n, idx, uv = tessellate(p)
        uva = pack_uv(uv, k)
        rb = readback[k]
        assert rb.shape == uva.shape, f"{p['name']}: GLB vert count changed"
        duv = float(np.abs(rb.astype(np.float64)
                           - uva.astype(np.float64)).max())
        ref, mask = render_part(v, uva, idx, sheet, per_pixel=True)
        chain, _m2 = render_part(v, rb, idx, sheet, per_pixel=True)
        d = np.abs(chain[mask] - ref[mask]).reshape(-1, 3)
        dmean = d.mean(0)
        la = chain[mask].mean(1)
        lb = ref[mask].mean(1)
        corr = float(np.corrcoef(la, lb)[0, 1])
        ok = duv < 1e-6 and (dmean < tol).all() and corr > 0.99
        ok_all &= ok
        worst_mean = max(worst_mean, float(dmean.max()))
        worst_corr = min(worst_corr, corr)
        worst_uv = max(worst_uv, duv)
        print(f"  {p['name']:14s} |duv|={duv:.2e}  dmean(x255)=({dmean[0] * 255:5.3f},"
              f"{dmean[1] * 255:5.3f},{dmean[2] * 255:5.3f})  "
              f"checker corr={corr:6.4f}  {'OK' if ok else 'FAIL'}")
    print(f"  worst |duv| = {worst_uv:.2e} (tol 1e-6)  "
          f"worst |dmean| x255 = {worst_mean * 255:.3f} (tol 2.000)  "
          f"worst corr = {worst_corr:.4f} (tol 0.9900)")
    print(f"TEST B2: {'PASS' if ok_all else 'FAIL'}")
    return ok_all


def main() -> int:
    a = test_a()
    b = test_b()
    print(f"== cad_uv: TEST A3 {'PASS' if a else 'FAIL'}, "
          f"TEST B2 {'PASS' if b else 'FAIL'} ==")
    return 0 if (a and b) else 1


if __name__ == "__main__":
    sys.exit(main())
