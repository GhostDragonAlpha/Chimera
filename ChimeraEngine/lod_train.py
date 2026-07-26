"""Train the LOD law (rho, beta) -- the fewest grains that reproduce the CORRECT appearance at every
on-screen scale. MEASURE first: the ground truth for a body of radius r_px is the known-correct large
render DOWNSAMPLED to r_px (a big blue marble shrunk = a small blue marble -- never the over-accumulated
small render). Progression from 1px up (the operator's "start at 1 pixel, zoom out by ratio"): at 1px a
planet IS one average-coloured grain; N = rho*r_px^2 fills grains in by screen area as it grows.

Run:  python ChimeraEngine/lod_train.py            (writes ChimeraEngine/lod.trained.json)
"""
import sys, math, json, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))   # repo root -> ParticleEngine
sys.path.insert(0, str(Path(__file__).resolve().parent))           # ChimeraEngine -> splat_appearance, lod
import numpy as np
from PIL import Image
from ParticleEngine.gpu_pipeline import FullGPUPipeline
from ParticleEngine.camera import FirstPersonCamera
import splat_appearance as sa
import lod as LOD
from splat_appearance import SIZE

R = 88.0
BASE_N = 40000
# geometric progression of projected RADII, 1px -> 512px (each ~2x the last: the operator's zoom-by-ratio)
SCALES = [1, 2, 4, 8, 16, 32, 64, 128, 256, 512]
GAIN = 0.40
_BASE = np.ascontiguousarray(sa.scene_buffer('aPlanet')[:BASE_N].copy())


def _render(buf, r_px, ss=1):
    W = H = max(6, int(r_px * ss * 3))
    cam = FirstPersonCamera((0.0, -400.0, 0.0)); cam.yaw = math.atan2(1.0, 0.0); cam.pitch = 0.0
    focal = H / (2 * math.tan(cam.fov / 2))
    cam.position = np.array([0.0, -R * focal / (r_px * ss), 0.0], np.float32)
    p = FullGPUPipeline(bg=(0.0, 0.0, 0.0)); p.upload(buf)
    img = p.render_from_gpu(cam, cam.params(W, H)).astype(np.float32)
    if ss > 1:
        img = np.asarray(Image.fromarray(img.astype(np.uint8)).resize((W // ss, H // ss), Image.BOX)).astype(np.float32)
    return img

# CORRECT ground truth: render the full body at a LARGE size (clean exposure), then DOWNSAMPLE to each r_px.
print("building correct references (downsample-from-large)..."); t0 = time.time()
_BIG = _render(_BASE, 256, ss=2)                 # 256px full-detail marble, supersampled -> clean, correct colour
_REF = {}
for r in SCALES:
    tgt = max(3, r * 2)                            # reference kept at 2x r_px for a fair AA compare
    _REF[r] = np.asarray(Image.fromarray(_BIG.astype(np.uint8)).resize((tgt, tgt), Image.BOX)).astype(np.float32)
print("  done in %.1fs (big-marble mean RGB %s)" % (time.time() - t0, _BIG.reshape(-1,3)[_BIG.reshape(-1,3).sum(1)>20].mean(0).round(1)))


def _err(cand_img, ref_img):
    # bring candidate to the reference's size, then AUTO-EXPOSE (match means per channel) so the error measures
    # STRUCTURE -- coverage/detail/continents -- not overall brightness (brightness is one global gain, trained
    # separately). White blow-out still scores badly: clipped-at-255 pixels can't be exposure-corrected back down.
    ci = np.asarray(Image.fromarray(cand_img.astype(np.uint8)).resize(ref_img.shape[1::-1], Image.BOX)).astype(np.float32)
    m = (ref_img.sum(2) > 20) | (ci.sum(2) > 20)
    if m.sum() <= 4:
        return 1e9
    cm = ci[m].mean(0); rm = ref_img[m].mean(0)
    ci = ci * (rm / (cm + 1e-3))                      # per-channel exposure match
    return float(np.abs(np.clip(ci, 0, 255)[m] - ref_img[m]).mean())


def measure(rho, beta):
    p = {"rho": rho, "beta": beta, "n_min": 1}
    worst = 0.0; total = 0; per = []
    for r in SCALES:
        N = LOD.lod_count(r, BASE_N, p)
        cand = _render(LOD.resample(_BASE, N, R, p, SIZE=SIZE), r, ss=1)
        e = _err(cand, _REF[r]); worst = max(worst, e); total += N; per.append((r, N, round(e, 1)))
    return worst, total, per


TOL = 14.0
print("%-7s %-7s %-9s %-9s" % ("rho", "beta", "worst_err", "grains"))
best = None
for rho in [0.20, 0.35, 0.55, 0.80]:
    for beta in [2.5, 3.5, 4.5, 5.5]:
        werr, tot, per = measure(rho, beta)
        ok = werr <= TOL
        print("%-7.2f %-7.2f %-9.2f %-9d %s" % (rho, beta, werr, tot, "OK" if ok else ""))
        key = (0 if ok else 1, tot if ok else werr)
        if best is None or key < best[0]:
            best = (key, rho, beta, werr, tot, per)

_, rho, beta, werr, tot, per = best
out = {"rho": rho, "beta": beta, "n_min": 1, "worst_err": round(werr, 2),
       "scales_px": SCALES, "per_scale_[r,N,err]": per, "tol": TOL, "gain": GAIN}
dst = Path(__file__).resolve().parent / "lod.trained.json"
dst.write_text(json.dumps(out, indent=2))
print("\nWINNER rho=%.2f beta=%.2f worst_err=%.2f grains=%d" % (rho, beta, werr, tot))
print("per-scale [r_px, N, err]:", per)
print("wrote", dst)
