"""Build a SPACE-GAME material library from the metal-bearing scans.
truck / train / bicycle are painted steel, chrome, rust, rubber and glass -- the exact
vocabulary a spaceship hull needs. Joint codebook across all three so one genome ID means
the same material regardless of which scan it came from."""
import sys, numpy as np, torch
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from Construction.ksplat_io import load_any

dev = "cuda"; K = 10; PER = 400_000
D = "E:/PythonChimera/WorldModel/training_data/downloads"
SRC = [("truck", f"{D}/truck.splat"), ("train", f"{D}/train.splat"), ("bicycle", f"{D}/bicycle.splat")]

rng = np.random.default_rng(0)
F_all, src_all = [], []
for name, p in SRC:
    pos, rgb, op, sc, q = load_any(p, full=True)
    solid = np.where(op > 0.5)[0]          # only OPAQUE surface splats -- haze is not a material
    idx = rng.choice(solid, min(PER, len(solid)), replace=False)
    ss = np.sort(sc[idx], 1)
    f = np.stack([np.log(ss[:, 1] + 1e-6), 1 - ss[:, 0] / (ss[:, 2] + 1e-9),
                  rgb[idx][:, 0], rgb[idx][:, 1], rgb[idx][:, 2], op[idx],
                  rgb[idx][:, 1] - np.maximum(rgb[idx][:, 0], rgb[idx][:, 2])], 1)
    F_all.append(f.astype(np.float32)); src_all.append(np.full(len(idx), len(src_all)))
    print(f"  {name:9}{len(pos):>10,} splats -> sampled {len(idx):,}")
F = np.concatenate(F_all); S = np.concatenate(src_all)
raw = F.copy()
Fz = (F - F.mean(0)) / (F.std(0) + 1e-9)
X = torch.tensor(Fz, device=dev)

g = torch.Generator(device=dev).manual_seed(0)
C = X[torch.randperm(len(X), generator=g, device=dev)[:K]].clone()
for _ in range(60):
    a = torch.cdist(X, C).argmin(1)
    for k in range(K):
        m = a == k
        if m.any(): C[k] = X[m].mean(0)
lab = torch.cdist(X, C).argmin(1).cpu().numpy()

names = ["truck", "train", "bicycle"]
print(f"\nSPACE-GAME MATERIAL LIBRARY — {K} genomes across {len(SRC)} metal-bearing scans\n")
print(f"{'id':4}{'%':>7}{'size':>8}{'aniso':>7}{'opacity':>9}{'colour':>22}   dominant source")
print("-" * 72)
for k in np.argsort([-(lab == k).mean() for k in range(K)]):
    m = lab == k
    r = raw[m]; c = r[:, 2:5].mean(0)
    mix = np.bincount(S[m], minlength=3) / max(1, m.sum())
    dom = " ".join(f"{names[i]} {100*mix[i]:.0f}%" for i in np.argsort(-mix)[:2] if mix[i] > 0.12)
    print(f"#{k:<3}{100*m.mean():>6.1f}%{np.exp(r[:,0]).mean():>8.3f}{r[:,1].mean():>7.2f}{r[:,5].mean():>9.2f}"
          f"   [{c[0]:.2f} {c[1]:.2f} {c[2]:.2f}]{'':>4}   {dom}")
