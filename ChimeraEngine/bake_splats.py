"""BAKE a scene's splats into a compact, GPU-ready binary -- the generate-then-bake seam (RENDERER_V2 §2).

Python owns everything upstream (story -> terms -> matter -> splat_appearance -> LOD). This writes the
*phenotype*: a flat record array the renderer uploads ONCE and keeps resident in VRAM. Python is then
out of the frame loop entirely.

Record = 48 bytes, std430-friendly (3x vec4):
    [ pos.x pos.y pos.z  scale ] [ col.r col.g col.b  opacity ] [ nrm.x nrm.y nrm.z  _pad ]

`scale` is the world-space Gaussian sigma with the particle TYPE profile already baked out (v1 applied
it per frame in `_p2s`); `nrm` is the optional back-face-cull normal (0,0,0 = never culled).

Run:  python ChimeraEngine/bake_splats.py aPlanet theSolarSystem
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import splat_appearance as sa

# size multiplier per particle type -- mirrors ParticleEngine.gpu_pipeline._profile
_SM = {0: 0.3, 1: 0.5, 2: 0.3, 3: 1.0, 4: 1.5, 5: 6.0, 6: 0.8, 7: 0.05}
_BASE_SCALE = 0.5                     # FullGPUPipeline(base_scale=)
OUT_DIR = Path(__file__).resolve().parent.parent / "web" / "renderer" / "data"


def bake(term: str, out_dir: Path = OUT_DIR) -> dict:
    buf = sa.scene_buffer(term)
    if buf is None:
        raise SystemExit(f"no scene buffer for {term!r}")
    buf = np.asarray(buf, dtype=np.float32)
    n = int(buf.shape[0])

    tcode = buf[:, 11].astype(np.int32)
    sm = np.vectorize(lambda t: _SM.get(int(t), 0.5))(tcode).astype(np.float32)
    scale = (buf[:, 20] * sm * _BASE_SCALE).astype(np.float32)     # world-space sigma

    rec = np.zeros((n, 12), dtype=np.float32)
    rec[:, 0:3] = buf[:, 0:3]                                       # position
    rec[:, 3] = scale
    rec[:, 4:7] = np.clip(buf[:, 16:19], 0.0, 1.0)                  # colour
    rec[:, 7] = np.clip(buf[:, 19], 0.0, 1.0)                       # opacity
    rec[:, 8:11] = buf[:, 21:24]                                    # normal (0,0,0 => no back-face cull)

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{term}.bin").write_bytes(rec.tobytes())
    radius = float(np.linalg.norm(buf[:, 0:3], axis=1).max())
    cam = sa.scene_cam_distance(term)
    meta = {"term": term, "count": n, "stride": 48, "radius": radius, "cam_distance": float(cam),
            "opaque": int((rec[:, 7] > 0.9).sum()), "bytes": int(rec.nbytes)}
    (out_dir / f"{term}.json").write_text(json.dumps(meta, indent=2))
    print(f"{term}: {n} splats, {rec.nbytes/1e6:.2f} MB, radius {radius:.1f}, cam {cam:.0f} -> {out_dir}")
    return meta


if __name__ == "__main__":
    terms = sys.argv[1:] or ["aPlanet"]
    index = [bake(t) for t in terms]
    (OUT_DIR / "index.json").write_text(json.dumps(index, indent=2))
