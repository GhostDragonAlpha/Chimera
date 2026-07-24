"""Take DNA samples of KNOWN splat regions and characterize each one's CONFIGURATION
(not its average): the distribution of splat size, shape (anisotropy), orientation
(how aligned the splats are), opacity, and colour. If bark / moss / ground come out as
different signatures, the material DNA is in the splat configuration."""
import sys, numpy as np
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from Construction.ksplat_io import load_ksplat

pos, rgb, opac, scale, quat = load_ksplat("E:/PythonChimera/WorldModel/training_data/real_data/stump/stump.ksplat", full=True)
rng = np.random.default_rng(0); EXT = (pos.max(0) - pos.min(0)).max()
sub = pos[rng.choice(len(pos), 120000, replace=False)]; t = 0.01 * EXT
best, bi = None, 0
for _ in range(600):
    i = rng.choice(len(sub), 3, replace=False); a, b, d = sub[i]
    nr = np.cross(b - a, d - a); L = np.linalg.norm(nr)
    if L < 1e-6: continue
    nr /= L; k = int((np.abs((sub - a) @ nr) < t).sum())
    if k > bi: bi, best = k, (a.copy(), nr.copy())
a, nr = best; inl = sub[np.abs((sub - a) @ nr) < t]; ctr = inl.mean(0)
up = np.linalg.svd(inl - inl.mean(0), full_matrices=False)[2][-1]
h = (pos - ctr) @ up
if np.median(h) < 0: up, h = -up, -h
e1 = np.cross(up, [1, 0, 0.]); e1 /= np.linalg.norm(e1) + 1e-9; e2 = np.cross(up, e1)
X = (pos - ctr) @ e1 - np.median((pos - ctr) @ e1); Z = (pos - ctr) @ e2 - np.median((pos - ctr) @ e2); Y = h
grn = rgb[:, 1] - np.maximum(rgb[:, 0], rgb[:, 2]); r_in = np.hypot(X - 7, Z - 2)

regions = {
    "GROUND": np.abs(Y) < 2.5,
    "MOSS/LEAF": (grn > 0.06) & (Y > 6),
    "BARK/WOOD": (grn < -0.02) & (Y > 6) & (r_in < 20),
}

def qR(q):
    q = q / (np.linalg.norm(q, axis=1, keepdims=True) + 1e-9)
    w, x, y, z = q[:, 0], q[:, 1], q[:, 2], q[:, 3]; R = np.empty((len(q), 3, 3), np.float32)
    R[:, 0, 0] = 1 - 2 * (y * y + z * z); R[:, 0, 1] = 2 * (x * y - w * z); R[:, 0, 2] = 2 * (x * z + w * y)
    R[:, 1, 0] = 2 * (x * y + w * z); R[:, 1, 1] = 1 - 2 * (x * x + z * z); R[:, 1, 2] = 2 * (y * z - w * x)
    R[:, 2, 0] = 2 * (x * z - w * y); R[:, 2, 1] = 2 * (y * z + w * x); R[:, 2, 2] = 1 - 2 * (x * x + y * y)
    return R

def coh(v):                                          # 1.0 = all aligned, 0.33 = random
    return float(np.linalg.eigvalsh((v[:, :, None] * v[:, None, :]).mean(0))[-1])

def dna(m):
    n = int(m.sum()); s = scale[m]; ss = np.sort(s, 1)
    R = qR(quat[m]); ax = np.arange(n)
    nd = R[ax, :, s.argmin(1)]; gd = R[ax, :, s.argmax(1)]         # normal axis / long ("grain") axis
    return dict(n=n, size=float(ss[:, 1].mean()), aniso=float((1 - ss[:, 0] / (ss[:, 2] + 1e-9)).mean()),
                ncoh=coh(nd), gcoh=coh(gd), op=float(opac[m].mean()), grn=float(grn[m].mean()), col=rgb[m].mean(0))

print(f"{'region':12}{'n':>9}{'size':>8}{'aniso':>7}{'norm_coh':>9}{'grain_coh':>10}{'opacity':>9}{'green':>7}  colour")
print("-" * 88)
for name, m in regions.items():
    d = dna(m); c = d["col"]
    print(f"{name:12}{d['n']:>9,}{d['size']:>8.3f}{d['aniso']:>7.2f}{d['ncoh']:>9.2f}{d['gcoh']:>10.2f}"
          f"{d['op']:>9.2f}{d['grn']:>+7.2f}  [{c[0]:.2f} {c[1]:.2f} {c[2]:.2f}]")
