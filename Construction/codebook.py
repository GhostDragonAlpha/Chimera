"""Rung 9: the serial-number codebook. Cluster every splat by its CONFIGURATION features
(size, anisotropy, colour, opacity, greenness) into K material genomes on the GPU, assign
each a serial number, report how much of the scene each covers, and paint the scene by
serial number. Scene now = {K genome centroids} + {per-splat serial} -> compress/identify."""
import sys, json, numpy as np, torch
sys.path.insert(0, "E:/PythonChimera")
from Construction.ksplat_io import load_ksplat

dev = "cuda"; K = 8
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

# per-splat CONFIGURATION features
ss = np.sort(scale, 1); log_size = np.log(ss[:, 1] + 1e-6); aniso = 1 - ss[:, 0] / (ss[:, 2] + 1e-9)
grn = rgb[:, 1] - np.maximum(rgb[:, 0], rgb[:, 2])
F = np.stack([log_size, aniso, rgb[:, 0], rgb[:, 1], rgb[:, 2], opac, grn], 1).astype(np.float32)
F = (F - F.mean(0)) / (F.std(0) + 1e-9)
Ft = torch.tensor(F, device=dev)

# k-means on the GPU
g = torch.Generator(device=dev).manual_seed(0)
S = Ft[torch.randperm(len(Ft), generator=g, device=dev)[:200000]]
C = S[torch.randperm(len(S), generator=g, device=dev)[:K]].clone()
for _ in range(60):
    aidx = torch.cdist(S, C).argmin(1)
    for k in range(K):
        m = aidx == k
        if m.any(): C[k] = S[m].mean(0)
serial = torch.empty(len(Ft), dtype=torch.long, device=dev)
for i in range(0, len(Ft), 500000):
    serial[i:i + 500000] = torch.cdist(Ft[i:i + 500000], C).argmin(1)
serial = serial.cpu().numpy()

PAL = np.array([[225, 70, 70], [70, 140, 225], [90, 205, 90], [235, 185, 55], [185, 90, 215], [70, 205, 205], [235, 120, 185], [165, 165, 120]])
print(f"CODEBOOK — {K} material genomes on the RTX 4090\n")
print(f"{'serial':7}{'%scene':>8}{'size':>8}{'aniso':>7}{'opacity':>9}{'green':>7}   mean colour")
print("-" * 62)
order = np.argsort([-(serial == k).mean() for k in range(K)])
for k in order:
    m = serial == k; c = rgb[m].mean(0)
    print(f"  #{k:<4}{100*m.mean():>7.1f}%{ss[m, 1].mean():>8.3f}{aniso[m].mean():>7.2f}{opac[m].mean():>9.2f}{grn[m].mean():>+7.2f}   [{c[0]:.2f} {c[1]:.2f} {c[2]:.2f}]")

Xc = X - np.median(X); Zc = Z - np.median(Z)
sel = np.random.default_rng(1).choice(len(pos), 95000, replace=False)
pts = [{"p": [round(float(Xc[i]), 2), round(float(Y[i]), 2), round(float(Zc[i]), 2)],
        "c": [int(PAL[serial[i]][0]), int(PAL[serial[i]][1]), int(PAL[serial[i]][2])], "o": True} for i in sel]
json.dump({"pts": pts, "nobj": len(pts), "nsoil": 0}, open("E:/PythonChimera/web/object.json", "w"))
print(f"\ncompression: {len(pos):,} splats  ->  {K} genome centroids ({K}x7 numbers) + one serial# per splat")
print("exported scene painted by material serial number -> viewer")
