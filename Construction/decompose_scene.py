"""Decompose a whole scene into its elements by morphological signature (the user's method).
  1. Iterative RANSAC pulls out PLANES (wall / ground / path) — their signature is planarity.
  2. What's left is clustered into BLOBS — each an element.
  3. Every element gets a DNA signature: PCA shape (linearity/planarity/scatter),
     orientation-to-gravity, size, colour, height. A label is read from the signature.
Output: the scene painted by element, so you can SEE it decomposed. Legend printed."""
import sys, json, numpy as np
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from WorldModel.splat_io import load_ply
from scipy import ndimage

c = load_ply("E:/PythonChimera/WorldModel/training_data/garden_tree.ply")
P = c.positions; C = np.clip(np.nan_to_num(c.colors), 0, 1)
rng = np.random.default_rng(0); EXT = (P.max(0) - P.min(0)).max(); T = 0.006 * EXT

# ground normal (for 'up' / gravity orientation)
up0 = int(np.argmin(P.max(0) - P.min(0)))
g = P[P[:, up0] < np.percentile(P[:, up0], 30)]
def plane_of(pts, it=400, t=T):
    sub = pts[rng.choice(len(pts), min(60000, len(pts)), replace=False)]
    best, bi = None, 0
    for _ in range(it):
        i = rng.choice(len(sub), 3, replace=False); a, b, d = sub[i]
        nr = np.cross(b - a, d - a); L = np.linalg.norm(nr)
        if L < 1e-6: continue
        nr /= L; k = int((np.abs((sub - a) @ nr) < t).sum())
        if k > bi: bi, best = k, (a.copy(), nr.copy())
    a, nr = best; inl = pts[np.abs((pts - a) @ nr) < t]; ct = inl.mean(0)
    _, _, vt = np.linalg.svd(inl - ct, full_matrices=False); return ct, vt[-1]
gc, UP = plane_of(g);
h = (P - gc) @ UP
if np.median(h) < 0: UP, h = -UP, -h

# 1. iterative plane extraction
elem = np.full(len(P), -1); rem = np.arange(len(P)); labels = []
for pi in range(6):
    if len(rem) < 0.03 * len(P): break
    ct, nr = plane_of(P[rem])
    dist = np.abs((P[rem] - ct) @ nr); inl = rem[dist < T]
    if len(inl) < 0.03 * len(P): break
    eid = len(labels); elem[inl] = eid
    vert = abs(nr @ UP)
    lab = "ground/floor" if vert > 0.7 else ("wall" if vert < 0.4 else "slope")
    labels.append((lab, len(inl), C[inl].mean(0)))
    rem = rem[dist >= T]

# 2. cluster the non-planar remainder into blobs
Pr = P[rem]; loc = Pr.min(0); vs = (Pr.max(0) - loc).max() / 150
dims = np.ceil((Pr.max(0) - loc) / vs).astype(int) + 1
vi = np.clip(((Pr - loc) / vs).astype(int), 0, dims - 1)
flat = (vi[:, 0] * dims[1] + vi[:, 1]) * dims[2] + vi[:, 2]
cnt = np.bincount(flat, minlength=int(dims.prod()))
lab3, nl = ndimage.label((cnt >= 2).reshape(dims), np.ones((3, 3, 3), int))
comp = lab3[vi[:, 0], vi[:, 1], vi[:, 2]]
for cid in range(1, nl + 1):
    m = comp == cid
    if m.sum() < 0.01 * len(P): continue
    idx = rem[m]; Q = P[idx]; eid = len(labels); elem[idx] = eid
    d = Q - Q.mean(0); _, s, vt = np.linalg.svd(d[rng.choice(len(d), min(20000, len(d)), replace=False)], full_matrices=False)
    lam = s ** 2 / (s ** 2).sum()
    lin = (lam[0] - lam[1]) / lam[0]; plan = (lam[1] - lam[2]) / lam[0]; scat = lam[2] / lam[0]
    vertax = abs(vt[0] @ UP); grn = (C[idx][:, 1] - np.maximum(C[idx][:, 0], C[idx][:, 2])).mean()
    if lin > 0.55 and vertax > 0.5: lab = "column (trunk? post?)"
    elif scat > 0.25: lab = "foliage" if grn > 0.03 else "blob/object"
    elif plan > 0.5: lab = "sheet"
    else: lab = "foliage" if grn > 0.03 else "object"
    labels.append((f"{lab}  [lin{lin:.2f} plan{plan:.2f} scat{scat:.2f} vert{vertax:.2f} grn{grn:+.2f}]", len(idx), C[idx].mean(0)))

PAL = np.array([[220,70,70],[70,140,220],[90,200,90],[230,180,60],[180,90,210],[70,200,200],
                [230,120,180],[150,110,70],[120,200,140],[200,200,120],[160,160,200],[90,160,90]])
print(f"\nSCENE DECOMPOSED INTO {len(labels)} ELEMENTS:")
for k, (lab, nn, mc) in enumerate(labels):
    col = PAL[k % len(PAL)]
    print(f"  [{k:2}] color({col[0]:3},{col[1]:3},{col[2]:3})  {nn:>9,} splats  {lab}")

# 3. export scene painted by element (upright)
a2 = np.array([1., 0, 0]) if abs(UP[0]) < 0.9 else np.array([0., 1, 0])
u = np.cross(UP, a2); u /= np.linalg.norm(u); w = np.cross(UP, u)
base = P[h < np.percentile(h, 5)].mean(0); d = P - base
X, Y, Z = d @ u, h, d @ w
sel = rng.choice(len(P), 90000, replace=False)
def ecol(e): return PAL[e % len(PAL)] if e >= 0 else np.array([40, 40, 46])
pts = [{"p": [round(float(X[i]), 2), round(float(Y[i]), 2), round(float(Z[i]), 2)],
        "c": [int(ecol(elem[i])[0]), int(ecol(elem[i])[1]), int(ecol(elem[i])[2])], "o": True} for i in sel]
json.dump({"pts": pts, "nobj": len(pts), "nsoil": 0}, open("E:/PythonChimera/web/object.json", "w"))
print(f"\nexported {len(pts)} pts, painted by element -> reload the viewer")
