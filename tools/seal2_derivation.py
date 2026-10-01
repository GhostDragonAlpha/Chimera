# Cut-and-weld prototype: cut the monkey at plane y, split straddling
# triangles, chain cross-section loops, cap both ways, check volumes.
# Pure derivation check against monkey_full.bin -- no engine involved.
import json
import struct
import numpy as np

BIN = r"E:\ChimeraWork\slot-01\.tmp\monkey_full.bin"
PLANE = 2.6

with open(BIN, "rb") as f:
    data = f.read()
n, idx_count = struct.unpack_from("<II", data, 0)
off = 8 + 16   # skip [f32 cam*4]
verts = np.frombuffer(data, dtype="<f4", count=n * 9, offset=off).reshape(n, 9).copy()
off += n * 9 * 4
indices = np.frombuffer(data, dtype="<u4", count=idx_count, offset=off).copy()
P = verts[:, 0:3]
tris = indices.reshape(-1, 3)
print(f"verts={n} tris={len(tris)}")

# orientation check: whole-mesh divergence volume
a, b, c = P[tris[:, 0]], P[tris[:, 1]], P[tris[:, 2]]
det = np.einsum("ij,ij->i", a, np.cross(b, c))
V_whole = det.sum() / 6.0
print(f"y range: {P[:,1].min():.4f} .. {P[:,1].max():.4f}")
print(f"V_whole signed = {V_whole:.6f} m^3  (target 13.8245)")

# --- classify triangles vs plane
yv = P[tris, 1]                      # (T,3)
below = yv < PLANE                   # strict below
nbelow = below.sum(axis=1)
pure_lower = np.nonzero(nbelow == 3)[0]
pure_upper = np.nonzero(nbelow == 0)[0]
strad = np.nonzero((nbelow == 1) | (nbelow == 2))[0]
print(f"pure_lower={len(pure_lower)} pure_upper={len(pure_upper)} "
      f"straddling={len(strad)} ({len(strad)/len(tris)*100:.2f}%)")

# --- cut each straddling triangle: two cut points on crossing edges
# key: undirected edge (min,max) -> cut point id
cut_id = {}
cut_src = []          # (va, vb, t) position = P[va]*(1-t) + P[vb]*t


def edge_cut(va, vb):
    ya, yb = P[va, 1], P[vb, 1]
    if ya >= yb:
        va, vb = vb, va
        ya, yb = yb, ya
    # ya < yb now; crossing if ya < PLANE <= yb
    if not (ya < PLANE <= yb):
        return None
    t = (PLANE - ya) / (yb - ya)
    key = (min(va, vb), max(va, vb))
    if key not in cut_id:
        cut_id[key] = N + len(cut_src)   # slot id: N..N+n_cut-1
        cut_src.append((va, vb, t))
    return cut_id[key]


segs = []             # (p0, p1) directed: walked as boundary of the BELOW piece
lower_pieces = []     # triangles (slots) for the lower daughter
upper_pieces = []     # triangles (slots) for the upper daughter
N = n                 # slots < N are original vertices; >= N are cut points

for t_i in strad:
    v0, v1, v2 = tris[t_i]
    nb = [bool(below[t_i, 0]), bool(below[t_i, 1]), bool(below[t_i, 2])]
    vs = [v0, v1, v2]
    if sum(nb) == 1:
        # one below: A below, B,C above. below piece (A, Pab, Pca); above quad
        i = nb.index(True)
        A = vs[i]
        B = vs[(i + 1) % 3]
        C = vs[(i + 2) % 3]
        pab = edge_cut(A, B)
        pca = edge_cut(C, A)
        lower_pieces.append((A, pab, pca))
        upper_pieces.append((pab, B, C))
        upper_pieces.append((pab, C, pca))
        segs.append((pab, pca))      # below-piece boundary direction
    else:
        # two below: A,B below, C above. below quad (A,B,Pbc,Pca); above tri
        i = nb.index(False)
        C = vs[i]
        A = vs[(i + 1) % 3]
        B = vs[(i + 2) % 3]
        pbc = edge_cut(B, C)
        pca = edge_cut(C, A)
        lower_pieces.append((A, B, pbc))
        lower_pieces.append((A, pbc, pca))
        upper_pieces.append((pbc, C, pca))
        segs.append((pbc, pca))      # below-piece boundary direction

print(f"cut points={len(cut_src)} segments={len(segs)}")

# --- chain segments into closed loops
out_edges = {}
for p0, p1 in segs:
    out_edges.setdefault(p0, []).append(p1)
bad = [k for k, v in out_edges.items() if len(v) != 1]
loops = []
visited = set()
for start in sorted(out_edges):
    if start in visited:
        continue
    loop = [start]
    visited.add(start)
    cur = start
    while True:
        nxt = out_edges[cur][0]
        loop.append(nxt)
        if nxt == start:
            break
        if nxt in visited:
            print(f"CHAIN ANOMALY at {nxt} (deg={len(out_edges.get(nxt, []))})")
            break
        visited.add(nxt)
        cur = nxt
    loops.append(loop)
print(f"loops: {len(loops)}  sizes: {[len(l)-1 for l in loops]}")
print(f"nodes with out-degree != 1: {len(bad)}")

# --- resolve cut-point positions
cutP = np.zeros((len(cut_src), 3))
for i, (va, vb, t) in enumerate(cut_src):
    cutP[i] = P[va] * (1 - t) + P[vb] * t
    assert abs(cutP[i, 1] - PLANE) < 1e-5


def slot_pos(s):
    return P[s] if s < N else cutP[s - N]


for i, loop in enumerate(loops):
    ring = loop[:-1] if loop[-1] == loop[0] else loop
    pts = np.array([slot_pos(s) for s in ring])
    cen = pts.mean(axis=0)
    print(f"  loop {i}: n={len(ring)} centroid=({cen[0]:+.3f},{cen[1]:+.3f},{cen[2]:+.3f}) "
          f"x[{pts[:,0].min():+.3f},{pts[:,0].max():+.3f}] z[{pts[:,2].min():+.3f},{pts[:,2].max():+.3f}]")


def div_sum(pieces):
    tot = 0.0
    for (s0, s1, s2) in pieces:
        pa, pb, pc = slot_pos(s0), slot_pos(s1), slot_pos(s2)
        tot += np.dot(pa, np.cross(pb, pc)) / 6.0
    return tot


# --- caps: fan from loop[0], two windings
cap_lower = []         # winding as chained (below-piece boundary direction)
cap_upper = []
for loop in loops:
    ring = loop[:-1] if loop[-1] == loop[0] else loop
    for i in range(1, len(ring) - 1):
        cap_lower.append((ring[0], ring[i], ring[i + 1]))
        cap_upper.append((ring[0], ring[i + 1], ring[i]))

# --- assemble daughters: pure triangles + split pieces + cap
all_lower = [(int(a), int(b), int(c)) for a, b, c in tris[pure_lower]] + lower_pieces + cap_lower
all_upper = [(int(a), int(b), int(c)) for a, b, c in tris[pure_upper]] + upper_pieces + cap_upper

V_l = div_sum(all_lower)
V_u = div_sum(all_upper)
print(f"V_lower = {V_l:.6f}  V_upper = {V_u:.6f}  sum = {V_l + V_u:.6f}")
print(f"sum error vs whole: {(V_l + V_u - V_whole) / V_whole * 100:.6e} %")
print(f"daughters both positive-sign: {V_l > 0 and V_u > 0}")

# cap planarity + boundary weld check: every cut point used by >=1 lower
# piece, >=1 upper piece, and the caps use exactly the cut points
used_lower = set()
for p in all_lower:
    used_lower.update(p)
used_upper = set()
for p in all_upper:
    used_upper.update(p)
cutset = set(range(N, N + len(cut_src)))
print(f"cut pts in lower boundary: {len(cutset & used_lower)}/{len(cutset)}")
print(f"cut pts in upper boundary: {len(cutset & used_upper)}/{len(cutset)}")

# triangle count accounting
print(f"lower pieces: {len(all_lower)}  upper pieces: {len(all_upper)}  "
      f"total = {len(all_lower) + len(all_upper)} "
      f"(orig {len(tris)} + split-extra {len(strad)} + caps {len(cap_lower) + len(cap_upper)})")

json.dump({
    "plane": PLANE,
    "V_whole": float(V_whole),
    "V_lower": float(V_l),
    "V_upper": float(V_u),
    "straddling": int(len(strad)),
    "cut_points": int(len(cut_src)),
    "loops": [len(l) - 1 for l in loops],
    "pure_lower": int(len(pure_lower)),
    "pure_upper": int(len(pure_upper)),
}, open(r"E:\ChimeraWork\slot-01\.tmp\cutweld_proto.json", "w"), indent=1)
print("wrote cutweld_proto.json")

# --- conservation under an arbitrary smooth warp (stand-in for a pose):
# cut slots ride their edges at fixed t, daughters re-partition exactly.
rng = np.random.default_rng(7)
warp = np.zeros_like(P)
warp[:, 0] += 0.15 * np.sin(2.1 * P[:, 1] + 0.7)          # x shear by height
warp[:, 1] += -0.06 * np.cos(1.3 * P[:, 0]) * np.cos(1.7 * P[:, 2])  # squash
warp[:, 2] += 0.10 * np.sin(0.9 * P[:, 0] + 1.1)
P2 = P + warp
cutP2 = np.zeros_like(cutP)
for i, (va, vb, t) in enumerate(cut_src):
    cutP2[i] = P2[va] * (1 - t) + P2[vb] * t


def slot_pos2(s):
    return P2[s] if s < N else cutP2[s - N]


def div_sum2(pieces):
    tot = 0.0
    for (s0, s1, s2) in pieces:
        pa, pb, pc = slot_pos2(s0), slot_pos2(s1), slot_pos2(s2)
        tot += np.dot(pa, np.cross(pb, pc)) / 6.0
    return tot


a2, b2, c2 = P2[tris[:, 0]], P2[tris[:, 1]], P2[tris[:, 2]]
V_whole2 = np.einsum("ij,ij->i", a2, np.cross(b2, c2)).sum() / 6.0
V_l2 = div_sum2(all_lower)
V_u2 = div_sum2(all_upper)
print(f"WARP: V_whole={V_whole2:.6f} V_lower={V_l2:.6f} V_upper={V_u2:.6f} "
      f"sum={V_l2 + V_u2:.6f} err={(V_l2 + V_u2 - V_whole2) / V_whole2 * 100:.3e}%")
print(f"WARP: dV_lower={V_l2 - V_l:+.6f} m^3 -> P_lower={(V_l - V_l2) / (4.6e-10 * V_l) / 1e6:+.3f} MPa")
