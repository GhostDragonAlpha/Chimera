"""GPU splat render in pure torch (CUDA) — no gsplat JIT needed. Loads the stump,
orients, crops the locked sphere, and rasterizes N orbit views on the 4090 by scattering
soft Gaussian footprints (normalized accumulation). All rasterization runs on the GPU."""
import sys, time, numpy as np, torch
from PIL import Image
sys.path.insert(0, "E:/PythonChimera")
from Construction.ksplat_io import load_ksplat

dev = "cuda"; sigma = float(sys.argv[1]) if len(sys.argv) > 1 else 1.2; K = int(np.ceil(3 * sigma))
pos, rgb, opac, scale, quat = load_ksplat("E:/PythonChimera/WorldModel/training_data/real_data/stump/stump.ksplat", full=True)
rng = np.random.default_rng(0); EXT = (pos.max(0) - pos.min(0)).max()
sub = pos[rng.choice(len(pos), 120000, replace=False)]; t = 0.01 * EXT   # SAME params as the framing run -> same 'up' -> same crop
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
m = np.linalg.norm(np.stack([X, Y, Z], 1) - np.array([7., 16, 2]), axis=1) < 15.0
print(f"stump crop: {int(m.sum()):,} splats")

means = torch.tensor(pos[m], device=dev); col = torch.tensor(np.clip(rgb[m], 0, 1), device=dev, dtype=torch.float32)
op = torch.tensor(np.clip(opac[m], 0, 1), device=dev, dtype=torch.float32)
target = pos[m].mean(0)
W = H = 380; fov = np.radians(35); f = 0.5 * W / np.tan(fov / 2); dist = 15 / np.tan(fov / 2) * 1.25
dxo, dyo = torch.meshgrid(torch.arange(-K, K + 1), torch.arange(-K, K + 1), indexing="ij")
off = torch.stack([dxo.flatten(), dyo.flatten()], 1).to(dev)
gw = torch.exp(-(off[:, 0] ** 2 + off[:, 1] ** 2).float() / (2 * sigma ** 2))

def render(theta):
    o = np.cos(np.radians(18)) * (np.cos(theta) * e1 + np.sin(theta) * e2) + np.sin(np.radians(18)) * up
    eye = target + dist * o; fwd = target - eye; fwd /= np.linalg.norm(fwd)
    right = np.cross(up, fwd); right /= np.linalg.norm(right); down = np.cross(fwd, right)
    R = torch.tensor(np.stack([right, down, fwd], 0), device=dev, dtype=torch.float32); et = torch.tensor(eye, device=dev, dtype=torch.float32)
    pc = (means - et) @ R.T; z = pc[:, 2].clamp(min=1e-3)
    u = (f * pc[:, 0] / z + W / 2); v = (f * pc[:, 1] / z + H / 2); front = pc[:, 2] > 0.05
    U = u.round().long()[:, None] + off[:, 0][None, :]; V = v.round().long()[:, None] + off[:, 1][None, :]
    ok = front[:, None] & (U >= 0) & (U < W) & (V >= 0) & (V < H)
    wt = (op[:, None] * gw[None, :]) * ok
    idx = (V.clamp(0, H - 1) * W + U.clamp(0, W - 1))
    cbuf = torch.zeros(W * H, 3, device=dev); wbuf = torch.zeros(W * H, device=dev)
    fi = idx.reshape(-1); fw = wt.reshape(-1)
    cbuf.index_add_(0, fi, (col[:, None, :].expand(-1, off.shape[0], -1).reshape(-1, 3)) * fw[:, None])
    wbuf.index_add_(0, fi, fw)
    return (cbuf / (wbuf[:, None] + 1e-6)).reshape(H, W, 3)

torch.cuda.synchronize(); t0 = time.time()
imgs = [render(2 * np.pi * k / 9) for k in range(9)]
torch.cuda.synchronize(); dt = time.time() - t0
print(f"rasterized 9 views of {int(m.sum()):,} splats in {dt*1000:.0f} ms on {torch.cuda.get_device_name(0)}")
g = 3; pad = 4; M = Image.new("RGB", (g * W + (g + 1) * pad, g * H + (g + 1) * pad), (14, 16, 24))
for k, im in enumerate(imgs):
    a8 = (im.clamp(0, 1).cpu().numpy() * 255).astype(np.uint8); r, c = divmod(k, g)
    M.paste(Image.fromarray(a8), (pad + c * (W + pad), pad + r * (H + pad)))
M.save("E:/PythonChimera/web/stump_gpu.png"); print("wrote web/stump_gpu.png")
