"""GPU render of the locked-on stump with gsplat (real 3DGS rasterization on the 4090).
Loads full splat params, orients, crops the stump sphere, orbits N cameras, rasterizes
all views in one GPU batch, mashes them into a montage."""
import sys, time, numpy as np, torch, gsplat
from PIL import Image
sys.path.insert(0, "E:/PythonChimera")
from Construction.ksplat_io import load_ksplat

SCALE_MULT = float(sys.argv[1]) if len(sys.argv) > 1 else 1.0
dev = "cuda"
pos, rgb, opac, scale, quat = load_ksplat("E:/PythonChimera/WorldModel/training_data/real_data/stump/stump.ksplat", full=True)
rng = np.random.default_rng(0); EXT = (pos.max(0) - pos.min(0)).max()
sub = pos[rng.choice(len(pos), 80000, replace=False)]; t = 0.01 * EXT
best, bi = None, 0
for _ in range(400):
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
m = np.linalg.norm(np.stack([X, Y, Z], 1) - np.array([7., 16, 2]), axis=1) < 15.0
print(f"stump crop: {int(m.sum()):,} splats   scale median={np.median(scale[m]):.3f} (x{SCALE_MULT})")

means = torch.tensor(pos[m], device=dev)
quats = torch.tensor(quat[m], device=dev); quats = quats / quats.norm(dim=1, keepdim=True)
scales = torch.tensor(scale[m] * SCALE_MULT, device=dev)
opac_t = torch.tensor(np.clip(opac[m], 0, 1), device=dev)
colors = torch.tensor(np.clip(rgb[m], 0, 1), device=dev)
target = pos[m].mean(0)

W = H = 380; fov = np.radians(35); f = 0.5 * W / np.tan(fov / 2); dist = 15 / np.tan(fov / 2) * 1.25
K = np.array([[f, 0, W / 2], [0, f, H / 2], [0, 0, 1]], np.float32)
VIEWS = 9; viewmats = []
for k in range(VIEWS):
    th = 2 * np.pi * k / VIEWS
    off = np.cos(np.radians(18)) * (np.cos(th) * e1 + np.sin(th) * e2) + np.sin(np.radians(18)) * up
    eye = target + dist * off
    fwd = (target - eye); fwd /= np.linalg.norm(fwd)
    right = np.cross(up, fwd); right /= np.linalg.norm(right); down = np.cross(fwd, right)
    R = np.stack([right, down, fwd], 0); tt = -R @ eye
    vm = np.eye(4, dtype=np.float32); vm[:3, :3] = R; vm[:3, 3] = tt; viewmats.append(vm)
viewmats = torch.tensor(np.stack(viewmats), device=dev)
Ks = torch.tensor(np.stack([K] * VIEWS), device=dev)

torch.cuda.synchronize(); t0 = time.time()
out, alpha, meta = gsplat.rasterization(means, quats, scales, opac_t, colors, viewmats, Ks, W, H,
                                        near_plane=0.01, far_plane=1e6, render_mode="RGB")
torch.cuda.synchronize(); dt = time.time() - t0
print(f"gsplat rasterized {VIEWS} views of {int(m.sum()):,} splats in {dt*1000:.0f} ms on {torch.cuda.get_device_name(0)}")

imgs = (out.clamp(0, 1).cpu().numpy() * 255).astype(np.uint8)   # (C,H,W,3)
g = 3; pad = 4; M = Image.new("RGB", (g * W + (g + 1) * pad, g * H + (g + 1) * pad), (14, 16, 24))
for k in range(VIEWS):
    r, c = divmod(k, g); M.paste(Image.fromarray(imgs[k]), (pad + c * (W + pad), pad + r * (H + pad)))
M.save("E:/PythonChimera/web/stump_gpu.png")
print("wrote web/stump_gpu.png")
