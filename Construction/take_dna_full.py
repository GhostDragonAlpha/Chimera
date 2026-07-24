"""Rung 1: the genome is a DISTRIBUTION, not a value. For each known region, report every
configuration feature as mean + [p10..p90] RANGE, then prove the distribution identifies
the material: fit a Gaussian genome (mean + covariance = the range) per region and classify
held-out splats by which distribution they fall inside."""
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
regions = {"GROUND": np.abs(Y) < 2.5, "MOSS/LEAF": (grn > 0.06) & (Y > 6), "BARK/WOOD": (grn < -0.02) & (Y > 6) & (r_in < 20)}

ss = np.sort(scale, 1); size = ss[:, 1]; aniso = 1 - ss[:, 0] / (ss[:, 2] + 1e-9)
names = ["size", "aniso", "R", "G", "B", "opacity", "green"]
raw = {"size": size, "aniso": aniso, "R": rgb[:, 0], "G": rgb[:, 1], "B": rgb[:, 2], "opacity": opac, "green": grn}
F = np.stack([np.log(size + 1e-6), aniso, rgb[:, 0], rgb[:, 1], rgb[:, 2], opac, grn], 1)
Fz = (F - F.mean(0)) / (F.std(0) + 1e-9)

print("=== the genome is a DISTRIBUTION — each feature as  mean [p10 .. p90] range ===")
for name, m in regions.items():
    print(f"\n{name}  ({int(m.sum()):,} splats)")
    for f in names:
        v = raw[f][m]; print(f"   {f:8} {v.mean():+.3f}   [{np.percentile(v, 10):+.3f} .. {np.percentile(v, 90):+.3f}]")

# identify: fit a Gaussian genome (mean + covariance) per region, classify held-out splats
gauss, Xt, yt = [], [], []
for lab, (name, m) in enumerate(regions.items()):
    idx = np.where(m)[0]; rng.shuffle(idx); cut = int(0.7 * len(idx)); tr, te = idx[:cut], idx[cut:]
    Xr = Fz[tr]; mu = Xr.mean(0); P = np.linalg.inv(np.cov(Xr.T) + 1e-3 * np.eye(7))
    gauss.append((mu, P)); te = te[:4000]; Xt.append(Fz[te]); yt.append(np.full(len(te), lab))
Xt = np.concatenate(Xt); yt = np.concatenate(yt)
D = np.stack([((Xt - mu) @ P * (Xt - mu)).sum(1) for mu, P in gauss], 1)   # Mahalanobis to each genome
acc = (D.argmin(1) == yt).mean()
print(f"\n=== identify: classify {len(yt):,} held-out splats by which genome DISTRIBUTION they fall inside ===")
print(f"   accuracy = {100 * acc:.1f}%   (chance = {100/len(gauss):.0f}%)   -> the range, not the mean, is what names it")
