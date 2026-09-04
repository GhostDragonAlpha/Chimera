"""kernel_axis_probe.py — WHICH AXIS DOES THE GPU KERNEL ACTUALLY ROTATE ABOUT? (2026-09-04)

The evidence conflict: the pack + CPU state say the elbow axis is the sagittal
x-hat; the dyad reads the posed arm as straight; a side-view differential
showed a thin HORIZONTAL band (the signature of a twist about the vertical).
This probe settles it with zero assumptions about camera conventions:

  1. Load the pack (J, axis) and the mesh (rest positions).
  2. Pose elbow_L 0 -> 90 deg via /joint (captured live through the engine).
  3. For each candidate law — the PACK's axis, the OLD u x v axis, and the
     vertical y twist — compute the exact set of forearm vertices that would
     MOVE (displacement > 8 world units are far; threshold tuned to the
     pixel test's 8/255 sensitivity), project each set's world bbox through
     the engine's OWN /project endpoint (its current VP), and compare the
     predicted screen bbox with the observed changed-pixel bbox.

The law whose predicted bbox matches the observation IS the law the GPU runs.
No camera conventions assumed: the engine projects the candidates itself.

Run: python tools/kernel_axis_probe.py
"""
import json
import struct
import urllib.request

import numpy as np

ENG = "http://127.0.0.1:8090"
THRESH_PX = 8          # matches the differential's >8/255 changed-pixel rule


def post(p, o, timeout=8):
    r = urllib.request.Request(ENG + p, data=json.dumps(o).encode(),
                               headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(r, timeout=timeout).read())


def get(p, timeout=8):
    with urllib.request.urlopen(ENG + p, timeout=timeout) as r:
        return r.read()


# ── pack + mesh ──────────────────────────────────────────────────────────────
b = open("Saved/meshes/monkey_joints.bin", "rb").read()
nv, nj, nl = struct.unpack("<III", b[4:16]); p = 16
names = [n for n in b[p:p + nl].decode().split("\x00") if n][:nj]; p += nl
p += nv * 8
J = np.frombuffer(b, np.float32, nj * 3, p).reshape(nj, 3).astype(np.float64); p += nj * 12
AX = np.frombuffer(b, np.float32, nj * 3, p).reshape(nj, 3).astype(np.float64)
ix = {n: i for i, n in enumerate(names)}

raw = open("ChimeraEngine/engine/build/Release/session_snapshot/mesh_bin.blob", "rb").read()
N, _ = struct.unpack("<II", raw[:8])
V = np.frombuffer(raw, np.float32, N * 9, 24).reshape(-1, 9)[:, :3].astype(np.float64)

# ── capture the observed differential LIVE (pose is set here, camera untouched) ──
post("/joint", {"joint": "elbow_L", "theta": 0.0})
post("/joint", {"joint": "elbow_R", "theta": 0.0})
import time
time.sleep(1.0)
rest_png = get("/frame")
time.sleep(0.5)
post("/joint", {"joint": "elbow_L", "theta": 90.0})
time.sleep(1.0)
flex_png = get("/frame")

import io
from PIL import Image


def to_img(buf):
    return np.asarray(Image.open(io.BytesIO(buf)).convert("RGB")).astype(np.int16)


a, bb = to_img(rest_png), to_img(flex_png)
d = (np.abs(a - bb).max(axis=2) > THRESH_PX)
ys, xs = np.where(d)
obs = (xs.min(), xs.max(), ys.min(), ys.max(), int(d.sum()))
print(f"observed changed px: {obs[4]}, bbox x[{obs[0]},{obs[1]}] y[{obs[2]},{obs[3]}]")

# ── candidate laws: forearm verts = band of elbow_L (assign==joint), L only ──
# (the live capture posed ONLY elbow_L; R stayed at 0)
assign = np.frombuffer(b, np.int32, nv, 16 + nl)[:nv]
el_idx = ix["elbow_L"]
band = np.where(assign == el_idx)[0]
P0 = V[band]                       # rest positions of the elbow's own band
print(f"elbow_L band: {len(band)} verts")


def rodrigues(P, J0, ax, th):
    v = P - J0
    c, s = np.cos(th), np.sin(th)
    return J0 + v * c + np.cross(ax, v) * s + np.outer(v @ ax, ax) * (1 - c)


J0 = J[el_idx]
pack_ax = AX[el_idx] / np.linalg.norm(AX[el_idx])
old_ax = np.array([0.0, 0.0, 0.9363])   # the convicted round-1 elbow axis (z-ish)
old_ax = old_ax / np.linalg.norm(old_ax)
y_ax = np.array([0.0, 1.0, 0.0])

th = np.radians(90.0)
for lbl, ax in [("PACK x-hat", pack_ax), ("OLD z-ish", old_ax), ("Y twist", y_ax)]:
    P1 = rodrigues(P0, J0, ax, th)
    moved = np.linalg.norm(P1 - P0, axis=1)
    sel = P0[moved > 0.15]           # verts that visibly move
    if len(sel) == 0:
        print(f"{lbl:12s}: no verts move > 0.15 wu — cannot match a 34k-px diff")
        continue
    # project the world bbox of the MOVED verts' DESTINATIONS (the new pixels)
    lo, hi = P1[moved > 0.15].min(axis=0), P1[moved > 0.15].max(axis=0)
    corners = np.array([[lo[0], lo[1], lo[2]], [hi[0], lo[1], lo[2]], [lo[0], hi[1], lo[2]],
                        [lo[0], lo[1], hi[2]], [hi[0], hi[1], lo[2]], [hi[0], lo[1], hi[2]],
                        [lo[0], hi[1], hi[2]], [hi[0], hi[1], hi[2]]])
    sxs, sys_ = [], []
    for c in corners:
        r = post("/project", {"x": c[0], "y": c[1], "z": c[2]})
        sxs.append(r["sx"]); sys_.append(r["sy"])
    print(f"{lbl:12s}: predicted bbox x[{min(sxs):6.0f},{max(sxs):6.0f}] "
          f"y[{min(sys_):6.0f},{max(sys_):6.0f}]   (moved verts: {len(sel)})")
print(f"{'OBSERVED':12s}: predicted bbox x[{obs[0]:6d},{obs[1]:6d}] y[{obs[2]:6d},{obs[3]:6d}]")
