"""station_probe.py — re-derive the flagged landmark stations FROM THE MESH. (2026-09-04)

The operator read the viewport tags and convicted six stations: neck, jaw,
spine_upper, spine_mid, spine_lower, ankle (all "too high"). The current seeds
were eyeballed; this probe measures the body's own anatomy and re-derives each
station from a profile, so the patch is a measurement, not a new guess:

  NECK          — the skull-base flare: scanning up the neck tube, the slice
                  width shrinks to a minimum then jumps where the head begins.
                  neck_y := the minimum-width bin (the skull base joint).
  JAW           — the mouth crease: on the front face (z near max), the
                  x-extent per height has two lobes (muzzle, chin) separated
                  by the mouth valley. jaw_y := the valley bin.
  SPINE_UPPER   — the withers: the widest torso-core slice (the shoulder
                  girdle). spine_upper_y := argmax width.
  SPINE_LOWER   — the pelvis: the widest lower-torso slice (the hip girdle).
                  spine_lower_y := argmax width, y < pelvis band cap.
  SPINE_MIDDLE  — the lumbar midpoint between the two measured girdles.
  ANKLE         — the tarsal break: scanning down the leg tube, the section
                  area jumps where the foot flares. ankle_y := flare onset.

Each law's window parameters are instrumentation; the STATIONS come out of the
profile extrema. Ambiguity (no clear extremum) is reported, never papered over.
"""

import struct
import numpy as np

PACK = 'Saved/meshes/monkey_joints.bin'
BLOB = 'ChimeraEngine/engine/build/Release/session_snapshot/mesh_bin.blob'

b = open(PACK, 'rb').read()
nv, nj, nl = struct.unpack('<III', b[4:16])
p = 16
names = [n for n in b[p:p + nl].decode().split('\x00') if n][:nj]; p += nl
p += nv * 8
J = np.frombuffer(b, np.float32, nj * 3, p).reshape(nj, 3).astype(np.float64)
Jd = {n: J[i] for i, n in enumerate(names)}

raw = open(BLOB, 'rb').read()
N, _ = struct.unpack('<II', raw[:8])
V = np.frombuffer(raw, np.float32, N * 9, 24).reshape(-1, 9)[:, :3].astype(np.float64)
print(f"mesh N={N}   ground ~ -0.02, crown ~ {V[:,1].max():.2f}")

print("\n== CURRENT stations (the convicted six marked *) ==")
for n in ('neck', 'jaw', 'spine_upper', 'spine_mid', 'spine_lower', 'tail_base',
          'shoulder_L', 'hip_L', 'knee_L', 'ankle_L'):
    star = '*' if n in ('neck', 'jaw', 'spine_upper', 'spine_mid', 'spine_lower',
                        'ankle_L') else ' '
    print(f" {star} {n:12s} x={Jd[n][0]:7.3f} y={Jd[n][1]:7.3f} z={Jd[n][2]:7.3f}")

def profile(ylo, yhi, dy, xw=None, zw=None, zref=None):
    """Per-y-bin: count, x-extent, z-extent, x/z centroid of the slice."""
    bins = np.arange(ylo, yhi, dy)
    rows = []
    for y0 in bins:
        m = (np.abs(V[:, 1] - y0) < dy * 0.5)
        if xw is not None: m &= (np.abs(V[:, 0] - (xw[0] if xw[0] else 0)) < xw[1])
        if zw is not None: m &= (np.abs(V[:, 2] - zref) < zw)
        if m.sum() < 4:
            rows.append((y0, 0, 0, 0, 0, 0)); continue
        P = V[m]
        rows.append((y0, len(P), P[:, 0].max() - P[:, 0].min(),
                     P[:, 2].max() - P[:, 2].min(), P[:, 0].mean(), P[:, 2].mean()))
    return rows

def show(rows, tag):
    print(f"\n== {tag} ==")
    print(f"{'y':>7s} {'n':>6s} {'x-ext':>6s} {'z-ext':>6s} {'cx':>6s} {'cz':>6s}")
    for r in rows:
        print(f"{r[0]:7.2f} {r[1]:6d} {r[2]:6.2f} {r[3]:6.2f} {r[4]:6.2f} {r[5]:6.2f}")

# A) TORSO WIDTH PROFILE (withers + pelvis) — full slice first, the arms included,
#    then the core (|x| < 0.90) so the arm tubes don't dominate.
show(profile(3.2, 6.6, 0.08), "TORSO full slice (arms included), y 3.2..6.6")
show(profile(3.2, 6.6, 0.08, xw=(0.0, 0.90)), "TORSO core |x|<0.90")

# B) NECK/HEAD — the skull-base flare: slice width vs height.
show(profile(6.8, 9.6, 0.06, xw=(0.0, 0.75)), "NECK/HEAD core |x|<0.75, y 6.8..9.6")

# C) MOUTH CREASE — front-face band (z near the head's max z), x-extent per y.
hz = V[V[:, 1] > 8.2][:, 2]
zfront = np.percentile(hz, 99)
m_front = V[:, 2] > zfront - 0.22
print(f"\nfront-face band: z > {zfront - 0.22:.2f} (z99={zfront:.2f}), {m_front.sum()} verts")
bins = np.arange(7.8, 9.6, 0.04)
print(f"{'y':>7s} {'n':>6s} {'x-ext':>6s}")
fr = []
for y0 in bins:
    m = m_front & (np.abs(V[:, 1] - y0) < 0.02)
    if m.sum() < 3: continue
    P = V[m]
    fr.append((y0, len(P), P[:, 0].max() - P[:, 0].min()))
for r in fr:
    print(f"{r[0]:7.2f} {r[1]:6d} {r[2]:6.2f}")

# D) LEG TUBE + TARSAL BREAK — around ankle_L's own (x,z), scan down.
ax_, az_ = Jd['ankle_L'][0], Jd['ankle_L'][2]
show(profile(0.1, 1.9, 0.05, xw=(ax_, 0.35), zw=0.55, zref=az_),
     f"LEG tube near x={ax_:.2f} z={az_:.2f}, y 0.1..1.9")

# E) SPINE COLUMN LINE — slice centroid z at the current stations (for the new z's).
print("\n== column-line centroid z at each spine station (|x|<0.90, dy=0.16) ==")
for n in ('spine_upper', 'spine_mid', 'spine_lower', 'neck'):
    y0 = Jd[n][1]
    m = (np.abs(V[:, 1] - y0) < 0.08) & (np.abs(V[:, 0]) < 0.90)
    P = V[m]
    print(f" {n:12s} y={y0:5.2f}  cz={P[:,2].mean():6.3f}  z-ext=[{P[:,2].min():.2f},{P[:,2].max():.2f}]  n={len(P)}")
