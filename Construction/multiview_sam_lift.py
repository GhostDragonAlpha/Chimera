"""Multi-view SAM2 lift (proven pipeline) with caching + CONTEXT export.
Orbits N cameras around the lock-on point, renders each view (colour for SAM + an ID
buffer = nearest 3D splat per pixel), prompts SAM2 at the projected centre, back-projects
the mask through the ID buffer, and VOTES across views. Result is cached; the export shows
the lifted object in TRUE COLOUR against the removed candidate splats dimmed to gray."""
import sys, os, json, numpy as np, torch
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from Construction.ksplat_io import load_ksplat

dev = "cuda"; NV = 10; W = H = 600
CACHE = "E:/PythonChimera/web/sam_lift_cache.npz"
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
medX = np.median((pos - ctr) @ e1); medZ = np.median((pos - ctr) @ e2)
X = (pos - ctr) @ e1 - medX; Z = (pos - ctr) @ e2 - medZ; Y = h
Cw = ctr + (7 + medX) * e1 + (2 + medZ) * e2 + 16 * up
crop = np.linalg.norm(np.stack([X, Y, Z], 1) - np.array([7., 16, 2]), axis=1) < 40
cidx = np.where(crop)[0]; Nc = len(cidx)
print(f"candidate crop: {Nc:,} splats")

if os.path.exists(CACHE) and np.load(CACHE)["cidx"].shape[0] == Nc:
    keep = np.load(CACHE)["keep"]; print("loaded SAM-lift cache (skipped SAM)")
else:
    from ultralytics import SAM
    means = torch.tensor(pos[crop], device=dev); col = torch.tensor(np.clip(rgb[crop], 0, 1), device=dev, dtype=torch.float32)
    op = torch.tensor(np.clip(opac[crop], 0, 1), device=dev, dtype=torch.float32)
    fov = np.radians(42); f = 0.5 * W / np.tan(fov / 2); dist = 40 / np.tan(fov / 2) * 1.15
    sig = 1.6; K = 3
    dxo, dyo = torch.meshgrid(torch.arange(-K, K + 1), torch.arange(-K, K + 1), indexing="ij")
    off = torch.stack([dxo.flatten(), dyo.flatten()], 1).to(dev); gw = torch.exp(-(off[:, 0] ** 2 + off[:, 1] ** 2).float() / (2 * sig ** 2))
    oid = torch.tensor([[0, 0], [1, 0], [0, 1], [-1, 0], [0, -1]], device=dev)
    model = SAM("sam2_b.pt"); votes = torch.zeros(Nc, device=dev); visible = torch.zeros(Nc, device=dev)
    for k in range(NV):
        th = 2 * np.pi * k / NV
        o = np.cos(np.radians(20)) * (np.cos(th) * e1 + np.sin(th) * e2) + np.sin(np.radians(20)) * up
        eye = Cw + dist * o; fwd = Cw - eye; fwd /= np.linalg.norm(fwd)
        right = np.cross(up, fwd); right /= np.linalg.norm(right); down = np.cross(fwd, right)
        R = torch.tensor(np.stack([right, down, fwd], 0), device=dev, dtype=torch.float32); et = torch.tensor(eye, device=dev, dtype=torch.float32)
        pc = (means - et) @ R.T; z = pc[:, 2].clamp(min=1e-3); front = pc[:, 2] > 0.05
        u = f * pc[:, 0] / z + W / 2; v = f * pc[:, 1] / z + H / 2
        U = u.round().long()[:, None] + off[:, 0][None, :]; V = v.round().long()[:, None] + off[:, 1][None, :]
        ok = front[:, None] & (U >= 0) & (U < W) & (V >= 0) & (V < H); wt = (op[:, None] * gw[None, :]) * ok
        pix = (V.clamp(0, H - 1) * W + U.clamp(0, W - 1)).reshape(-1); fw = wt.reshape(-1)
        cbuf = torch.zeros(W * H, 3, device=dev); wbuf = torch.zeros(W * H, device=dev)
        cbuf.index_add_(0, pix, col[:, None, :].expand(-1, off.shape[0], -1).reshape(-1, 3) * fw[:, None]); wbuf.index_add_(0, pix, fw)
        img8 = ((cbuf / (wbuf[:, None] + 1e-6)).reshape(H, W, 3).clamp(0, 1).cpu().numpy() * 255).astype(np.uint8)
        Ui = u.round().long()[:, None] + oid[:, 0][None, :]; Vi = v.round().long()[:, None] + oid[:, 1][None, :]
        oki = front[:, None] & (Ui >= 0) & (Ui < W) & (Vi >= 0) & (Vi < H)
        pixi = (Vi.clamp(0, H - 1) * W + Ui.clamp(0, W - 1)); zz = z[:, None].expand(-1, oid.shape[0]); ids = torch.arange(Nc, device=dev)[:, None].expand(-1, oid.shape[0])
        pf = pixi[oki]; zf = zz[oki]; idf = ids[oki]
        zbuf = torch.full((W * H,), 1e9, device=dev); zbuf.scatter_reduce_(0, pf, zf, reduce="amin", include_self=True)
        idbuf = torch.full((W * H,), -1, dtype=torch.long, device=dev); near = zf <= zbuf[pf] + 1e-3; idbuf[pf[near]] = idf[near]
        pcc = (torch.tensor(Cw, device=dev, dtype=torch.float32) - et) @ R.T; ptx = float(f * pcc[0] / pcc[2] + W / 2); pty = float(f * pcc[1] / pcc[2] + H / 2)
        res = model(img8, points=[[ptx, pty]], labels=[1], device=0, verbose=False)
        mask = torch.tensor(res[0].masks.data[0].cpu().numpy().astype(bool).reshape(-1), device=dev)
        vis_ids = idbuf[idbuf >= 0]; visible.index_add_(0, vis_ids, torch.ones(len(vis_ids), device=dev))
        sel_ids = idbuf[mask & (idbuf >= 0)]; votes.index_add_(0, sel_ids, torch.ones(len(sel_ids), device=dev))
        print(f"  view {k}: SAM mask {100*mask.float().mean():.0f}% frame")
    ratio = votes / visible.clamp(min=1); keep = ((visible >= 3) & (ratio >= 0.5)).cpu().numpy()
    np.savez(CACHE, cidx=cidx, keep=keep)

kidx = cidx[keep]; rem = cidx[~keep]
print(f"\nlifted object: {len(kidx):,} of {Nc:,} candidate splats  |  removed: {len(rem):,}")
cx0 = X[kidx].mean(); cz0 = Z[kidx].mean()
rng2 = np.random.default_rng(1)
rem_s = rem if len(rem) <= 55000 else rem[rng2.choice(len(rem), 55000, replace=False)]
keep_s = kidx if len(kidx) <= 80000 else kidx[rng2.choice(len(kidx), 80000, replace=False)]
def emit(i, dim):
    c = np.array([120, 125, 135]) if dim else (np.clip(rgb[i], 0, 1) * 255).astype(int)
    return {"p": [round(float(X[i] - cx0), 2), round(float(Y[i]), 2), round(float(Z[i] - cz0), 2)], "c": [int(c[0]), int(c[1]), int(c[2])], "o": (not dim)}
pts = [emit(i, False) for i in keep_s] + [emit(i, True) for i in rem_s]
json.dump({"pts": pts, "nobj": len(keep_s), "nsoil": len(rem_s)}, open("E:/PythonChimera/web/object.json", "w"))
print(f"context export: {len(keep_s):,} lifted (true colour) + {len(rem_s):,} removed (dimmed gray) -> viewer")
