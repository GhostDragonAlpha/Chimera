"""BAKE a scene's splats into a compact, GPU-ready binary -- the generate-then-bake seam (RENDERER_V2 §2).

Python owns everything upstream (story -> terms -> matter -> splat_appearance -> LOD). This writes the
*phenotype*: a flat record array the renderer uploads ONCE and keeps resident in VRAM. Python is then
out of the frame loop entirely.

ANISOTROPIC, SURFACE-ALIGNED. A splat is an ellipsoid (scale + rotation), not a sphere -- the standard
3DGS parameterisation, and the same shape the scan-DNA pipeline recovers. This matters geometrically:
an isotropic sphere projects to a CIRCLE at every viewing angle, but the SPACING between splats on a
curved surface is foreshortened by cos(phi) (phi = angle between surface normal and view ray). So sphere
splats overlap heavily at the limb and least at the sub-camera point -- an extremum that shows up as a
visible "spot" exactly where the surface faces the camera. A disc tangent to the surface foreshortens by
the same cos(phi) as the spacing does, so screen-space overlap is UNIFORM and the special point vanishes.

Record = 64 bytes, std430-friendly (4x vec4):
    [ pos.xyz  opacity ] [ col.rgb  _pad ] [ scale.xyz  _pad ] [ quat.xyzw ]
`scale` is the world-space Gaussian sigma along each local axis (tangent, tangent, normal); the rotation's
third axis IS the surface normal, so the renderer gets back-face culling for free with no extra field.

Run:  python ChimeraEngine/bake_splats.py aPlanet theSolarSystem
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import splat_appearance as sa

_SM = {0: 0.3, 1: 0.5, 2: 0.3, 3: 1.0, 4: 1.5, 5: 6.0, 6: 0.8, 7: 0.05}
_BASE_SCALE = 0.5
_FLATNESS = 0.22        # normal-axis sigma as a fraction of the tangential sigma (a disc, not a sphere)
OUT_DIR = Path(__file__).resolve().parent.parent / "web" / "renderer" / "data"


def _frames_from_normals(nrm: np.ndarray):
    """Orthonormal (t1, t2, n) per splat; for a zero normal returns the identity frame (isotropic splat)."""
    n = nrm.astype(np.float64)
    ln = np.linalg.norm(n, axis=1, keepdims=True)
    has = (ln[:, 0] > 1e-6)
    n = np.where(ln > 1e-6, n / np.maximum(ln, 1e-12), np.array([0.0, 0.0, 1.0]))
    # pick the world axis least aligned with n, so the cross product is well conditioned
    a = np.zeros_like(n)
    idx = np.argmin(np.abs(n), axis=1)
    a[np.arange(len(n)), idx] = 1.0
    t1 = np.cross(n, a); t1 /= np.maximum(np.linalg.norm(t1, axis=1, keepdims=True), 1e-12)
    t2 = np.cross(n, t1)
    return t1, t2, n, has


def _quat_from_frame(t1, t2, n):
    """Quaternion (x,y,z,w) for the rotation whose COLUMNS are (t1, t2, n)."""
    m00, m10, m20 = t1[:, 0], t1[:, 1], t1[:, 2]
    m01, m11, m21 = t2[:, 0], t2[:, 1], t2[:, 2]
    m02, m12, m22 = n[:, 0], n[:, 1], n[:, 2]
    tr = m00 + m11 + m22
    q = np.zeros((len(t1), 4), np.float64)
    s0 = tr > 0
    s = np.sqrt(np.maximum(tr + 1.0, 1e-12)) * 2.0
    q[s0] = np.stack([(m21 - m12) / s, (m02 - m20) / s, (m10 - m01) / s, 0.25 * s], 1)[s0]
    c1 = (~s0) & (m00 > m11) & (m00 > m22)
    s = np.sqrt(np.maximum(1.0 + m00 - m11 - m22, 1e-12)) * 2.0
    q[c1] = np.stack([0.25 * s, (m01 + m10) / s, (m02 + m20) / s, (m21 - m12) / s], 1)[c1]
    c2 = (~s0) & (~c1) & (m11 > m22)
    s = np.sqrt(np.maximum(1.0 + m11 - m00 - m22, 1e-12)) * 2.0
    q[c2] = np.stack([(m01 + m10) / s, 0.25 * s, (m12 + m21) / s, (m02 - m20) / s], 1)[c2]
    c3 = (~s0) & (~c1) & (~c2)
    s = np.sqrt(np.maximum(1.0 + m22 - m00 - m11, 1e-12)) * 2.0
    q[c3] = np.stack([(m02 + m20) / s, (m12 + m21) / s, 0.25 * s, (m10 - m01) / s], 1)[c3]
    return q / np.maximum(np.linalg.norm(q, axis=1, keepdims=True), 1e-12)


def bake(term: str, out_dir: Path = OUT_DIR) -> dict:
    buf = sa.scene_buffer(term)
    if buf is None:
        raise SystemExit(f"no scene buffer for {term!r}")
    buf = np.asarray(buf, dtype=np.float32)
    n = int(buf.shape[0])

    tcode = buf[:, 11].astype(np.int32)
    sm = np.vectorize(lambda t: _SM.get(int(t), 0.5))(tcode).astype(np.float64)
    sigma = (buf[:, 20].astype(np.float64) * sm * _BASE_SCALE)          # world-space sigma

    t1, t2, nn, has_nrm = _frames_from_normals(buf[:, 21:24])
    quat = _quat_from_frame(t1, t2, nn)
    scale = np.stack([sigma, sigma, sigma], axis=1)
    scale[has_nrm, 2] = sigma[has_nrm] * _FLATNESS                       # surface splats are flat DISCS

    rec = np.zeros((n, 16), dtype=np.float32)
    rec[:, 0:3] = buf[:, 0:3]                                            # position
    rec[:, 3] = np.clip(buf[:, 19], 0.0, 1.0)                            # opacity
    rec[:, 4:7] = np.clip(buf[:, 16:19], 0.0, 1.0)                       # colour
    rec[:, 8:11] = scale                                                 # sigma along (t1, t2, n)
    rec[:, 12:16] = quat                                                 # rotation (x, y, z, w)

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{term}.bin").write_bytes(rec.tobytes())
    radius = float(np.linalg.norm(buf[:, 0:3], axis=1).max())
    cam = sa.scene_cam_distance(term)
    meta = {"term": term, "count": n, "stride": 64, "radius": radius, "cam_distance": float(cam),
            "surface_aligned": int(has_nrm.sum()), "bytes": int(rec.nbytes)}
    (out_dir / f"{term}.json").write_text(json.dumps(meta, indent=2))
    print(f"{term}: {n} splats ({int(has_nrm.sum())} surface-aligned discs), "
          f"{rec.nbytes/1e6:.2f} MB, radius {radius:.1f} -> {out_dir}")
    return meta


if __name__ == "__main__":
    terms = sys.argv[1:] or ["aPlanet"]
    index = [bake(t) for t in terms]
    (OUT_DIR / "index.json").write_text(json.dumps(index, indent=2))
