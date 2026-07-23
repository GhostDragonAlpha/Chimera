"""Rung 9.5: spatial voting (the membrane). A lone splat's genome is noisy (82.5%). But a
splat sits IN a neighbourhood of the same material, so smooth its label over its k nearest
spatial neighbours' predictions. That neighbourhood IS the membrane. Does identify sharpen?"""
import sys, numpy as np
sys.path.insert(0, "E:/PythonChimera")
from Construction.ksplat_io import load_ksplat
from scipy.spatial import cKDTree

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
regions = [("GROUND", np.abs(Y) < 2.5), ("MOSS", (grn > 0.06) & (Y > 6)), ("BARK", (grn < -0.02) & (Y > 6) & (r_in < 20))]

ss = np.sort(scale, 1); size = ss[:, 1]; aniso = 1 - ss[:, 0] / (ss[:, 2] + 1e-9)
F = np.stack([np.log(size + 1e-6), aniso, rgb[:, 0], rgb[:, 1], rgb[:, 2], opac, grn], 1)
Fz = (F - F.mean(0)) / (F.std(0) + 1e-9)
lab = np.full(len(pos), -1)
for c, (name, m) in enumerate(regions): lab[m] = c
sel = lab >= 0; Pm = pos[sel]; Fm = Fz[sel]; ym = lab[sel]

istest = np.zeros(len(ym), bool)
for c in range(3):
    ci = np.where(ym == c)[0]; rng.shuffle(ci); istest[ci[int(0.7 * len(ci)):][:4000]] = True
G = []
for c in range(3):
    Xr = Fm[(ym == c) & ~istest]; G.append((Xr.mean(0), np.linalg.inv(np.cov(Xr.T) + 1e-3 * np.eye(7))))
pred = np.stack([((Fm - mu) @ P * (Fm - mu)).sum(1) for mu, P in G], 1).argmin(1)

def pc(p, y): return "  ".join(f"{['GRND', 'MOSS', 'BARK'][c]} {100*(p[y == c] == c).mean():.0f}%" for c in range(3))
print(f"baseline per-splat : {100*(pred[istest]==ym[istest]).mean():.1f}%    [{pc(pred[istest], ym[istest])}]")
tree = cKDTree(Pm); tidx = np.where(istest)[0]
print("\nspatial-voted (membrane = k nearest neighbours):")
for k in (10, 25, 50, 100):
    _, nb = tree.query(Pm[tidx], k=k)
    vp = np.array([np.bincount(pred[nb[i]], minlength=3).argmax() for i in range(len(tidx))])
    print(f"   k={k:>3} : {100*(vp==ym[tidx]).mean():.1f}%    [{pc(vp, ym[tidx])}]")
