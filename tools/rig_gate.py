"""rig_gate.py — THE GATE A JOINTS PACK MUST PASS BEFORE IT SHIPS. (2026-09-03)

Born from the empty-band defect: 8 of 19 joints shipped with zero assigned
vertices and one (elbow_R) floating off the creature entirely. Six checks,
each with its law:

  1. FULL ASSIGNMENT  — every vertex assigned to exactly one joint.
  2. NO EMPTY BANDS   — every joint owns vertices (else its rotation moves
                        nothing: a dead joint in a live rig).
  3. ON-MESH          — every joint center within EPS of some mesh vertex.
  4. MIRROR LAW       — every L/R pair's midpoint lies on the spine axis
                        (x ~ 0); R limb positions are x-negations of L.
  5. SEGMENT PARITY   — parent->child bone lengths match L/R within 2%.
  6. NO ZIGZAG        — each LIMB chain's rest bend stays under 90 deg
                        (the floating-elbow class). The AXIAL chain is
                        exempt per link bend — a primate neck leaves the
                        torso oblique, and that is anatomy, not defect —
                        but every axial link must have length >= 0.2 wu
                        (a collapsed link hides a swallowed joint).

Usage:  python tools/rig_gate.py [pack.bin] [mesh_blob]
        (defaults: Saved/meshes/monkey_joints.bin + the engine snapshot blob)
Exit 0 = PASS (ship it), exit 1 = FAIL (do not POST it).
"""
import numpy as np, struct, sys, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACK = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'Saved/meshes/monkey_joints.bin')
BLOB = sys.argv[2] if len(sys.argv) > 2 else os.path.join(
    ROOT, 'ChimeraEngine/engine/build/Release/session_snapshot/mesh_bin.blob')
EPS_ONMESH = 0.30      # wu — a center further than this from ANY vertex is off-body
MIRROR_TOL = 0.05      # wu — L/R pair midpoint |x| must be under this
SEG_TOL = 0.02         # relative — L/R bone length mismatch
ZIGZAG_MAX = 90.0      # deg — rest-pose bend angle per chain link

CHAINS = [
    ['shoulder_L', 'elbow_L', 'wrist_L'], ['shoulder_R', 'elbow_R', 'wrist_R'],
    ['hip_L', 'knee_L', 'ankle_L'],       ['hip_R', 'knee_R', 'ankle_R'],
]
AXIAL_CHAIN = ['spine_lower', 'spine_mid', 'spine_upper', 'neck']
AXIAL_MIN_LINK = 0.2   # wu — a shorter axial link means a swallowed joint

raw = open(BLOB, 'rb').read()
N, idx_count = struct.unpack('<II', raw[:8])
V = np.frombuffer(raw, np.float32, N * 9, 24).reshape(-1, 9)[:, :3].astype(np.float64)

b = open(PACK, 'rb').read()
assert b[:4] == b'JNT1', 'not a JNT1 pack'
nv, nj, nl = struct.unpack('<III', b[4:16])
p = 16 + nl
assign = np.frombuffer(b, np.int32, nv, p); p += nv * 4
w = np.frombuffer(b, np.float32, nv, p); p += nv * 4
J = np.frombuffer(b, np.float32, nj * 3, p).reshape(nj, 3); p += nj * 12
ax = np.frombuffer(b, np.float32, nj * 3, p).reshape(nj, 3); p += nj * 12
rom = np.frombuffer(b, np.float32, nj * 2, p)
names = [n.decode() for n in b[16:16 + nl].split(b'\x00')[:nj]]
ix = {n: i for i, n in enumerate(names)}

fails = []
def check(num, label, ok, detail):
    tag = 'PASS' if ok else 'FAIL'
    print(f'  [{num}] {label:<22} {tag}  {detail}')
    if not ok:
        fails.append(f'{num} {label}: {detail}')

print(f'pack: {os.path.basename(PACK)}  ({nv} verts, {nj} joints)  vs canonical blob {os.path.basename(BLOB)}')
print()

# 1 — full assignment
check(1, 'full assignment', bool(((assign >= 0) & (assign < nj)).all()),
      f'min={assign.min()} max={assign.max()}')

# 2 — no empty bands
counts = np.bincount(assign, minlength=nj)
empty = [names[i] for i in range(nj) if counts[i] == 0]
check(2, 'no empty bands', not empty,
      ', '.join(empty) if empty else f'min band = {counts.min()} verts')

# 3 — on-mesh
dmin = np.min(np.linalg.norm(V[:, None, :] - J[None, :, :], axis=2), axis=0)
off = [(names[i], float(dmin[i])) for i in range(nj) if dmin[i] > EPS_ONMESH]
check(3, 'on-mesh centers', not off,
      ', '.join(f'{n} d={d:.3f}' for n, d in off) if off else f'max d = {dmin.max():.3f} wu (eps {EPS_ONMESH})')

# 4 — mirror law
bad_pairs = []
for side in ('L', 'R'):
    for nme in names:
        if not nme.endswith('_L'):
            continue
        iL, iR = ix[nme], ix[nme[:-2] + '_R']
        midx = (J[iL][0] + J[iR][0]) / 2.0
        if abs(midx) > MIRROR_TOL or abs(J[iL][1] - J[iR][1]) > MIRROR_TOL or abs(J[iL][2] - J[iR][2]) > MIRROR_TOL:
            bad_pairs.append(f'{nme[:-2]} mid=({midx:.3f},...)')
check(4, 'mirror law', not bad_pairs,
      ', '.join(bad_pairs) if bad_pairs else f'all {sum(1 for n in names if n.endswith("_L"))} pairs on the spine axis (tol {MIRROR_TOL})')

# 5 — segment parity
bad_seg = []
for ch in CHAINS:
    for a, bnm in zip(ch, ch[1:]):
        if not (a.endswith('_L') and bnm.endswith('_L')):
            continue
        ia, ib = ix[a], ix[bnm]
        ra, rb = ix[a[:-2] + '_R'], ix[bnm[:-2] + '_R']
        lL = float(np.linalg.norm(J[ib] - J[ia]))
        lR = float(np.linalg.norm(J[rb] - J[ra]))
        if abs(lL - lR) > SEG_TOL * max(lL, lR):
            bad_seg.append(f'{a[:-2]} {lL:.3f} vs {lR:.3f}')
check(5, 'segment parity', not bad_seg,
      ', '.join(bad_seg) if bad_seg else 'all paired bone lengths within 2%')

# 6 — no zigzag at rest (LIMB chains; axial bends are anatomy, see docstring)
bad_zz = []
for ch in CHAINS:
    for a, bnm, c in zip(ch, ch[1:], ch[2:]):
        ja, jb, jc = ix[a], ix[bnm], ix[c]
        u, v2 = J[jb] - J[ja], J[jc] - J[jb]
        cosang = float(np.dot(u, v2) / (np.linalg.norm(u) * np.linalg.norm(v2) + 1e-12))
        ang = float(np.degrees(np.arccos(np.clip(cosang, -1, 1))))
        if ang > ZIGZAG_MAX:
            bad_zz.append(f'{bnm} {ang:.0f} deg')
axial_short = []
for a, bnm in zip(AXIAL_CHAIN, AXIAL_CHAIN[1:]):
    ln = float(np.linalg.norm(J[ix[bnm]] - J[ix[a]]))
    if ln < AXIAL_MIN_LINK:
        axial_short.append(f'{bnm} {ln:.3f} wu')
zz_detail = ', '.join(bad_zz + axial_short) if (bad_zz or axial_short) else \
    'limb bends < 90 deg; axial links >= 0.2 wu'
check(6, 'no zigzag at rest', not (bad_zz or axial_short), zz_detail)

print()
if fails:
    print(f'GATE: FAIL — {len(fails)} check(s). DO NOT POST THIS PACK.')
    sys.exit(1)
print('GATE: PASS — the pack may ship to the engine.')
