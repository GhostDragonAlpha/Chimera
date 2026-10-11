"""Round-08 root-cause probe (consolidated, reproducible).

Parses the shipped JNT3 binding pack (Saved/meshes/monkey_joints.bin) + mesh
(Saved/meshes/monkey_birth.bin), reports foot-region ownership, simulates the
game's exact CPU LBS law (joint_binding.hpp pose_binding) at knee_L=40 deg,
verifies the LIMB_CAP rejection mechanism, and proves the proposed re-bind
offline. Touches NOTHING outside this evidence folder.

Side convention: _L limbs are at x>0 (mirror law negates x for _R).
"""
import struct, numpy as np, collections

ROOT = r"E:/PythonChimera"
mesh = open(ROOT + r"/Saved/meshes/monkey_birth.bin", 'rb').read()
nv, nf = struct.unpack_from('<II', mesh)
xyz = np.frombuffer(mesh, '<f4', 3*nv, 8).reshape(nv, 3).astype(np.float64)
pack = open(ROOT + r"/Saved/meshes/monkey_joints.bin", 'rb').read()
assert pack[:4] == b'JNT3'
pnv, nj, nl = struct.unpack_from('<III', pack, 4)
p = 16; names = []
while len(names) < nj:
    z = pack.index(b'\x00', p); names.append(pack[p:z].decode()); p = z + 1
def ints(n):
    global p
    a = np.frombuffer(pack, '<i4', n, p).copy(); p += 4*n; return a
def floats(n):
    global p
    a = np.frombuffer(pack, '<f4', n, p).copy(); p += 4*n; return a.astype(np.float64)
owner = ints(nv); weight = floats(nv)
pivots = floats(3*nj).reshape(nj, 3); axes = floats(3*nj).reshape(nj, 3)
limits = floats(2*nj).reshape(nj, 2); parents = ints(nj)
secondary = ints(nv); weight2 = floats(nv)
own_names = np.array(names)
knee_L = names.index('knee_L'); ankle_L = names.index('ankle_L')
spine_lower = names.index('spine_lower')

print(f"nv={nv} nj={nj}")
print(f"unassigned verts (owner<0): {(owner<0).sum()}  (JNT3 decoder forbids them)")

def pose(rad, own=owner, w=weight, sec=secondary):
    F = {}
    for j in range(nj):
        chain = []; k = j
        while k >= 0: chain.append(k); k = parents[k]
        M = np.eye(3); T = np.zeros(3)
        for k in reversed(chain):
            ang = rad[k]
            if ang == 0: continue
            a = axes[k]; c, s, dd = np.cos(ang), np.sin(ang), 1-np.cos(ang)
            R = np.array([[c+dd*a[0]*a[0], dd*a[0]*a[1]-s*a[2], dd*a[0]*a[2]+s*a[1]],
                          [dd*a[1]*a[0]+s*a[2], c+dd*a[1]*a[1], dd*a[1]*a[2]-s*a[0]],
                          [dd*a[2]*a[0]-s*a[1], dd*a[2]*a[1]+s*a[0], c+dd*a[2]*a[2]]])
            off = pivots[k] - R @ pivots[k]
            T = T + M @ off; M = M @ R
        F[j] = (M, T)
    out = np.empty_like(xyz)
    for v in range(nv):
        j = int(own[v]); k = int(sec[v])
        if k < 0: k = int(parents[j])
        Ma, Ta = F[j]
        Mz, Tz = F[k] if k >= 0 else (np.eye(3), np.zeros(3))
        out[v] = w[v]*(Ta + Ma@xyz[v]) + (1-w[v])*(Tz + Mz@xyz[v])
    return out

rad = np.zeros(nj); rad[knee_L] = np.radians(40)
d = np.linalg.norm(pose(rad) - xyz, axis=1)

foot = np.where((xyz[:, 1] < 0.16) & (xyz[:, 0] > 0))[0]
sole = np.where((xyz[:, 1] < 0.12) & (xyz[:, 0] > 0.2))[0]
shin = np.where((np.abs(xyz[:, 0] - 0.47) < 0.35) & (xyz[:, 1] > 0.9) & (xyz[:, 1] < 1.8))[0]
ank = np.where(owner == ankle_L)[0]
print(f"\nLEFT FOOT (y<0.16,x>0) n={len(foot)} owner: {dict(collections.Counter(own_names[owner[foot]]))}")
print(f"SOLE      (y<0.12,x>0.2) n={len(sole)} owner: {dict(collections.Counter(own_names[owner[sole]]))}")
sl_sole = sole[owner[sole] == spine_lower]
print(f"sole verts owned by spine_lower (FK ROOT): {len(sl_sole)}/{len(sole)}, "
      f"w mean={weight[sl_sole].mean():.3f} -> follow share (1-w) mean={1-weight[sl_sole].mean():.3f}")
print(f"ankle_L band n={len(ank)} y-range [{xyz[ank,1].min():.2f},{xyz[ank,1].max():.2f}] "
      f"(covers shin ABOVE the ankle pivot y=0.34, never the foot)")

print(f"\nknee_L=40 pure-LBS displacement:")
print(f"  ankle_L band: mean={d[ank].mean():.3f} max={d[ank].max():.3f}")
print(f"  shin region:  mean={d[shin].mean():.3f} max={d[shin].max():.3f}")
print(f"  left foot:    mean={d[foot].mean():.3f} max={d[foot].max():.3f}")
print(f"  sole:         mean={d[sole].mean():.3f} max={d[sole].max():.3f}")

# ── mechanism: foot_tip_L misidentification + LIMB_CAP rejection ────────────
J_ankle, J_knee = pivots[ankle_L], pivots[knee_L]
leg_L = np.linalg.norm(xyz - J_ankle, axis=1)
beyond = np.where((np.linalg.norm(xyz - J_knee, axis=1) < leg_L) & (leg_L < 1.0))[0]
tip_ids = beyond[np.argsort(-leg_L[beyond])][:30]
foot_tip = xyz[tip_ids].mean(axis=0)
print(f"\nfoot_tip_L reproduced = {foot_tip.round(3)}  (ankle pivot {J_ankle.round(3)}; "
      f"a true toe would be y~0.1, z>0.4)")
A = foot_tip - J_ankle
D = xyz[sole] - J_ankle
t = np.clip((D @ A) / (A @ A), 0, 1)
dseg = np.linalg.norm(xyz[sole] - (J_ankle + t[:, None] * A), axis=1)
print(f"sole distance to the ankle->foot_tip segment: min={dseg.min():.2f} "
      f"mean={dseg.mean():.2f} max={dseg.max():.2f}; LIMB_CAP=0.7 rejects {(dseg>0.7).sum()}/{len(sole)}")

# ── offline proof of the fix (scratch arrays only) ──────────────────────────
own2 = owner.copy(); w2 = weight.copy(); sec2 = secondary.copy()
fixm = np.where((owner == spine_lower) & (xyz[:, 1] < 0.35) & (np.abs(xyz[:, 0]) > 0.2))[0]
own2[fixm] = ankle_L; w2[fixm] = 1.0; sec2[fixm] = knee_L
d1 = np.linalg.norm(pose(rad, own2, w2, sec2) - xyz, axis=1)
print(f"\nFIX PROOF (scratch): re-bound {len(fixm)} root-owned foot verts (both feet) -> ankle_L")
print(f"  knee_L=40 sole displacement: BEFORE {d[sole].mean():.3f} -> AFTER {d1[sole].mean():.3f}")
print(f"  knee_L=40 shin displacement: BEFORE {d[shin].mean():.3f} -> AFTER {d1[shin].mean():.3f} (unchanged)")
rest = pose(np.zeros(nj), own2, w2, sec2)
print(f"  rest pose bit-identical to mesh: {np.abs(rest - xyz).max() < 1e-9}")
