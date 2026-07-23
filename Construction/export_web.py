"""Honest test: how much of garden_tree is actually PLANT? Isolate the green (foliage)
splats by color, trace the largest connected green mass, and report its size + shape
so we can SEE whether there's a real tree in this file."""
import sys, json, numpy as np
sys.path.insert(0, "E:/PythonChimera")
from WorldModel.splat_io import load_ply
from scipy import ndimage

c = load_ply("E:/PythonChimera/WorldModel/training_data/garden_tree.ply")
P = c.positions; C = np.clip(np.nan_to_num(c.colors), 0, 1)
rng = np.random.default_rng(0); EXT = (P.max(0) - P.min(0)).max(); GT = 0.02 * EXT
up = int(np.argmin(P.max(0) - P.min(0)))
cand = P[P[:, up] < np.percentile(P[:, up], 30)]
def ransac(pts, it=500, t=GT):
    best, bi = None, 0
    for _ in range(it):
        i = rng.choice(len(pts), 3, replace=False); a, b, d = pts[i]
        nr = np.cross(b - a, d - a); L = np.linalg.norm(nr)
        if L < 1e-6: continue
        nr /= L; k = int((np.abs((pts - a) @ nr) < t).sum())
        if k > bi: bi, best = k, (a.copy(), nr.copy())
    a, nr = best; ip = pts[np.abs((pts - a) @ nr) < t]; ct = ip.mean(0)
    _, _, vt = np.linalg.svd(ip - ct, full_matrices=False); return ct, vt[-1]
ctr, n = ransac(cand); h = (P - ctr) @ n
if np.median(h) < 0: n, h = -n, -h
ab = h > 0.5 * GT
Pab, Cab, hab = P[ab], C[ab], h[ab]

greenness = Cab[:, 1] - np.maximum(Cab[:, 0], Cab[:, 2])
for thr in (0.02, 0.05, 0.10):
    print(f"  greenness>{thr:.2f}: {100*(greenness>thr).mean():5.1f}% of above-ground splats")
gmask = greenness > 0.05
print(f"clearly-green splats: {int(gmask.sum()):,} of {len(Pab):,} ({100*gmask.mean():.1f}%)")

Pg, Cg, hg = Pab[gmask], Cab[gmask], hab[gmask]
loc = Pg.min(0); RES = 160; vs = (Pg.max(0) - loc).max() / RES
dims = np.ceil((Pg.max(0) - loc) / vs).astype(int) + 1
vi = np.clip(((Pg - loc) / vs).astype(int), 0, dims - 1)
flat = (vi[:, 0] * dims[1] + vi[:, 1]) * dims[2] + vi[:, 2]
cnt = np.bincount(flat, minlength=int(dims.prod()))
lab, nl = ndimage.label((cnt >= 2).reshape(dims), np.ones((3, 3, 3), int))
w = np.bincount(lab.reshape(-1), weights=cnt, minlength=nl + 1); w[0] = 0
keep = lab[vi[:, 0], vi[:, 1], vi[:, 2]] == int(w.argmax())
gh = hg[keep]
print(f"largest green mass = {int(keep.sum()):,} splats  height=[{gh.min():.1f},{gh.max():.1f}] (span {gh.max()-gh.min():.1f})")

a2 = np.array([1., 0, 0]) if abs(n[0]) < 0.9 else np.array([0., 1, 0])
u = np.cross(n, a2); u /= np.linalg.norm(u); ww = np.cross(n, u)
Pk = Pg[keep]; base = Pk[gh < np.percentile(gh, 12)].mean(0)
d = Pk - base; Xc, Yc, Zc = d @ u, gh, d @ ww
sel = rng.choice(len(Xc), min(65000, len(Xc)), replace=False)
cols = (Cg[keep][sel] * 255).astype(int)
pts = [{"p": [round(float(Xc[i]), 2), round(float(Yc[i]), 2), round(float(Zc[i]), 2)],
        "c": [int(cols[j, 0]), int(cols[j, 1]), int(cols[j, 2])], "o": True} for j, i in enumerate(sel)]
json.dump({"pts": pts, "nobj": len(pts), "nsoil": 0}, open("E:/PythonChimera/web/object.json", "w"))
print(f"exported {len(pts)} green pts.  width~{np.hypot(Xc,Zc).max()*2:.1f}  height~{Yc.max()-Yc.min():.1f}")
