"""Reverse photogrammetry, step 1: orbit a camera around a splat scene, render N views,
and mash them into one montage (the user's 'all photos in one photo'). Each view also
writes an ID BUFFER (pixel -> 3D splat index) so any 2D label back-projects exactly to
3D. The montage is for segmenting all views at once; the per-view maps do the lifting.
"""
import sys, numpy as np
from pathlib import Path
from PIL import Image, ImageDraw
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from Construction.ksplat_io import load_ksplat

VIEWS, IMG = 9, 240                       # 9 views -> 3x3 montage, 240px each
pos, rgb = load_ksplat("E:/PythonChimera/WorldModel/training_data/real_data/stump/stump.ksplat")
rng = np.random.default_rng(0); EXT = (pos.max(0) - pos.min(0)).max()

# robust 'up' from the dominant ground plane
sub = pos[rng.choice(len(pos), 120000, replace=False)]; t = 0.01 * EXT
best, bi = None, 0
for _ in range(600):
    i = rng.choice(len(sub), 3, replace=False); a, b, d = sub[i]
    nr = np.cross(b - a, d - a); L = np.linalg.norm(nr)
    if L < 1e-6: continue
    nr /= L; k = int((np.abs((sub - a) @ nr) < t).sum())
    if k > bi: bi, best = k, (a.copy(), nr.copy())
a, nr = best; inl = sub[np.abs((sub - a) @ nr) < t]; up = np.linalg.svd(inl - inl.mean(0), full_matrices=False)[2][-1]
h = (pos - inl.mean(0)) @ up
if np.median(h) < 0: up = -up
e1 = np.cross(up, [1, 0, 0.]); e1 = e1 / np.linalg.norm(e1) if np.linalg.norm(e1) > 1e-6 else np.cross(up, [0, 1, 0.]); e1 /= np.linalg.norm(e1)
e2 = np.cross(up, e1)
center = pos.mean(0); R = np.percentile(np.linalg.norm(pos - center, axis=1), 98)
SC = IMG * 0.46 / R

id_buffers = []
tiles = []
for k in range(VIEWS):
    th = 2 * np.pi * k / VIEWS
    vd = np.cos(th) * e1 + np.sin(th) * e2 - 0.35 * up; vd /= np.linalg.norm(vd)   # slight downward tilt
    right = np.cross(up, vd); right /= np.linalg.norm(right); camup = np.cross(vd, right)
    d = pos - center
    sx = (d @ right) * SC + IMG / 2; sy = IMG / 2 - (d @ camup) * SC; dep = d @ vd
    px = sx.astype(np.int32); py = sy.astype(np.int32)
    ok = (px >= 0) & (px < IMG) & (py >= 0) & (py < IMG)
    order = np.argsort(-dep[ok])                       # far first, near overwrites
    pk = px[ok][order]; pyk = py[ok][order]; idxs = np.where(ok)[0][order]
    colimg = np.zeros((IMG, IMG, 3), np.uint8); idbuf = np.full((IMG, IMG), -1, np.int64)
    colimg[pyk, pk] = (np.clip(rgb[idxs], 0, 1) * 255).astype(np.uint8)
    idbuf[pyk, pk] = idxs
    id_buffers.append((idbuf, th))
    tiles.append(colimg)

# mash into one montage (3x3)
g = int(np.ceil(np.sqrt(VIEWS))); pad = 4
M = Image.new("RGB", (g * IMG + (g + 1) * pad, g * IMG + (g + 1) * pad), (16, 18, 26))
dr = ImageDraw.Draw(M)
for k, tile in enumerate(tiles):
    r, c = divmod(k, g); x = pad + c * (IMG + pad); y = pad + r * (IMG + pad)
    M.paste(Image.fromarray(tile), (x, y))
    dr.text((x + 4, y + 3), f"{int(np.degrees(2*np.pi*k/VIEWS))}deg", fill=(200, 210, 160))
M.save("E:/PythonChimera/web/montage.png")
np.savez("C:/Users/allen/AppData/Local/Temp/claude/E--PythonChimera/ad56e64f-dbc3-4842-b124-5eac10776728/scratchpad/id_buffers.npz",
         **{f"v{k}": b for k, (b, _) in enumerate(id_buffers)}, n_splats=len(pos))
print(f"rendered {VIEWS} views ({IMG}px) -> web/montage.png   ID buffers saved ({len(pos):,} splats indexed)")
print(f"up={up.round(3)}  scene radius={R:.1f}")
