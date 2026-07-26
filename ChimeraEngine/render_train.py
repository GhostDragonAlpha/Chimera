"""Train the render 'elements' (grain opacity / size / count) against what the OPERATOR actually sees:
DANCING while it spins (temporal instability) and SPEED (ms/frame) -- measured together, not by taste.

The dancing dots are TEMPORAL ALIASING: as the planet rotates, discrete grains cross pixel boundaries and
coverage gaps pop in and out. The measure renders the planet across a few rotation steps and scores:
  - flicker : fraction of surface pixels that JUMP hard between consecutive frames (a dot popping) -- MINIMIZE
  - ms      : render time per frame                                                                 -- MINIMIZE
  - fidelity: mean colour on target + no persistent holes (guards against the degenerate 'huge blurry grain')

Run:  python ChimeraEngine/render_train.py
"""
import sys, math, json, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
from ParticleEngine.gpu_pipeline import FullGPUPipeline
from ParticleEngine.camera import FirstPersonCamera
import splat_appearance as sa
from splat_appearance import PX, PZ, TYPE, ALPHA, SIZE, NX, NZ, CR, CG, CB, NCOLS

R = 88.0
W = H = 900
TARGET = np.array([43.0, 81.0, 102.0])
DIST = 250.0                      # close-up (live-viewer-ish) framing
DTHETA = math.radians(1.5)        # per-frame spin -- small, like the auto-spin
NFRAMES = 5

# fixed per-grain surface recipe (colours), so only the trained knobs change between genomes
_rng = np.random.default_rng(sa._seed('aPlanet'))
_dirs = sa._fibonacci_sphere(40000)
_z = _dirs[:, 2]; _ln = sa._fbm(_dirs, _rng); _th = np.quantile(_ln, 0.66)
_land = _ln > _th; _ice = np.abs(_z) > 0.88; _land &= ~_ice; _ocean = ~_land & ~_ice
_d = 0.5 + 0.5*sa._fbm(_dirs, _rng)
_col = np.zeros((40000, 3), np.float32)
_col[_ocean] = np.stack([0.02+0.04*_d[_ocean], 0.08+0.12*_d[_ocean], 0.30+0.22*_d[_ocean]], 1)
_ar = np.clip(np.abs(_z)*0.9 + 0.30*sa._fbm(_dirs, _rng), 0, 1)
_col[_land] = np.stack([0.13+0.34*_ar[_land], 0.44-0.12*_ar[_land], 0.12+0.05*_ar[_land]], 1)
_col[_ice] = [0.90, 0.93, 0.97]


def build(n, size, opac, gain):
    idx = np.linspace(0, 39999, n).astype(int)
    d = _dirs[idx]
    b = np.zeros((n, NCOLS), np.float32)
    b[:, PX:PZ+1] = d*R; b[:, NX:NZ+1] = d
    b[:, TYPE] = 3.0; b[:, ALPHA] = opac; b[:, SIZE] = size
    b[:, CR:CB+1] = _col[idx] * gain
    return b


def _frame(pipe, cam, az):
    ce = math.cos(0.0)
    pos = (DIST*ce*math.sin(az), -DIST*ce*math.cos(az), 0.0)
    n = math.sqrt(sum(x*x for x in pos)) or 1.0
    cam.position = np.array(pos, np.float32)
    cam.yaw = math.atan2(-pos[1]/n, -pos[0]/n); cam.pitch = 0.0
    return pipe.render_from_gpu(cam, cam.params(W, H)).astype(np.float32)


def measure(n, size, opac, gain):
    pipe = FullGPUPipeline(bg=(0.0, 0.0, 0.0)); pipe.upload(build(n, size, opac, gain))
    cam = FirstPersonCamera((0.0, -DIST, 0.0))
    frames = [_frame(pipe, cam, i*DTHETA) for i in range(NFRAMES)]
    # timing (steady state)
    t0 = time.time()
    for _ in range(6): _frame(pipe, cam, 0.0)
    ms = (time.time()-t0)/6*1000
    F = np.stack(frames)                                   # (K,H,W,3)
    disk = (F.mean(0).sum(2) > 25)                          # surface pixels (avg lit)
    # FLICKER: consecutive-frame hard jumps localised on the surface (a dot popping in/out)
    jumps = np.abs(np.diff(F, axis=0)).max(3)              # (K-1,H,W) max channel change
    flicker = float((jumps[:, disk] > 45).mean()) * 100.0  # % of surface-pixel-frames that pop
    # fidelity: mean colour distance + persistent dark holes inside the disk
    mean = F.mean(0)[disk].mean(0)
    coldist = float(np.abs(mean - TARGET).mean())
    holes = float((F.mean(0)[disk].sum(1) < 25).mean())*100
    return dict(n=n, size=size, opac=opac, ms=round(ms,1), fps=round(1000/ms,1),
                flicker=round(flicker,2), coldist=round(coldist,1), holes=round(holes,2),
                mean=mean.round(0).tolist())


if __name__ == "__main__":
    GAIN = 0.40
    print("%-26s %-7s %-7s %-9s %-9s %-7s" % ("config", "fps", "ms", "flicker%", "coldist", "holes%"))
    rows = []
    for n in [40000, 60000]:
        for size in [3.5, 5.0, 7.0]:
            for opac in [0.6, 0.85, 1.0]:
                r = measure(n, size, opac, GAIN)
                rows.append(r)
                print("%-26s %-7.1f %-7.1f %-9.2f %-9.1f %-7.2f" %
                      ("n%d s%.1f a%.2f" % (n, size, opac), r['fps'], r['ms'], r['flicker'], r['coldist'], r['holes']))
    Path(Path(__file__).resolve().parent / "render_train.log.json").write_text(json.dumps(rows, indent=2))
    # current live config for reference is n40000 s3.5 a1.0
    print("\n(current live config = n40000 s3.5 a1.00)")
