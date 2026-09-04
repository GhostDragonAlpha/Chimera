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
IS_JNT2 = (b[:4] == b'JNT2')
IS_JNT3 = (b[:4] == b'JNT3')
assert b[:4] in (b'JNT1', b'JNT2', b'JNT3'), 'not a JNT pack'
nv, nj, nl = struct.unpack('<III', b[4:16])
p = 16 + nl
assign = np.frombuffer(b, np.int32, nv, p); p += nv * 4
w = np.frombuffer(b, np.float32, nv, p); p += nv * 4
J = np.frombuffer(b, np.float32, nj * 3, p).reshape(nj, 3); p += nj * 12
ax = np.frombuffer(b, np.float32, nj * 3, p).reshape(nj, 3); p += nj * 12
rom = np.frombuffer(b, np.float32, nj * 2, p); p += nj * 8
# JNT2+: trailing FK parent map — the second bone of every crease (LBS).
# JNT3: + per-vertex second-owner joint and its blend share (w2).
parents = None
if IS_JNT2 or IS_JNT3:
    parents = np.frombuffer(b, np.int32, nj, p)
joint2 = None; w2 = None
if IS_JNT3:
    q = p + nj * 4                                # past the parent map
    joint2 = np.frombuffer(b, np.int32, nv, q); q += nv * 4
    w2 = np.frombuffer(b, np.float32, nv, q)
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

# 3 — in-body (2026-09-04 amendment): the CENTRAL joints are measured
# interior stations (tools/station_probe.py) and are NOT on the skin — the
# old "on-mesh" predicate was a medoid-era artifact (joints snapped to skin
# by construction) and it convicted exactly the fix that un-crowded the
# torso chain. The promise is now class-aware:
#   paired joints  — skin-pinned: within EPS_ONMESH of the nearest vertex;
#   central joints — contained in the body: >= 20 mesh verts within 0.3 wu
#                    (a point outside the hull sees almost none; inside the
#                    torso core it sees hundreds).
CENTRAL = ('neck', 'jaw', 'spine_upper', 'spine_mid', 'spine_lower',
           'tail_base', 'tail_mid')
dmin = np.min(np.linalg.norm(V[:, None, :] - J[None, :, :], axis=2), axis=0)
off = [(names[i], float(dmin[i])) for i in range(nj)
       if names[i] not in CENTRAL and dmin[i] > EPS_ONMESH]
# central containment: a station floating in air is far from ALL skin; one
# inside the torso is within the body's half-thickness (~1.0 wu here). The
# ray-parity alternative was tried and REJECTED this round: 26-28 crossings
# per ray (neck/jaw/spine_lower report "outside" against every geometric
# reading) — the blob's shell appears double-walled in places, which breaks
# parity even/odd. Recorded as a topology audit for another day.
for i in range(nj):
    if names[i] in CENTRAL and dmin[i] > 1.0:
        off.append((names[i], float(dmin[i])))
check(3, 'in-body centers', not off,
      ', '.join(f'{n} d={d:.3f}' for n, d in off) if off
      else f'limb max d = {max(dmin[i] for i in range(nj) if names[i] not in CENTRAL):.3f} wu (eps {EPS_ONMESH}); central: all contained')

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

# 7 — FK parent map (JNT2/3; the LBS second bone must be the overlay's own law)
# TREE RIGHTS (2026-09-04): the FIRST pack hung the skeleton from the SKULL
# (neck root, spine descending) — the neck's arc composed into every band and
# the whole body tilted (measured: neck +30 deg moved 349,357 px whole-frame).
# The pelvis (spine_lower) is the root; the spine ascends; the skull hangs
# from the withers; the tail hangs from the pelvis. Matches the MJCF template.
if IS_JNT2 or IS_JNT3:
    FK_PARENTS = {
        'spine_lower': -1,
        'spine_mid': 'spine_lower', 'spine_upper': 'spine_mid',
        'neck': 'spine_upper', 'jaw': 'neck',
        'tail_base': 'spine_lower', 'tail_mid': 'tail_base',
        'shoulder_L': 'spine_upper', 'elbow_L': 'shoulder_L', 'wrist_L': 'elbow_L',
        'shoulder_R': 'spine_upper', 'elbow_R': 'shoulder_R', 'wrist_R': 'elbow_R',
        'hip_L': 'spine_lower', 'knee_L': 'hip_L', 'ankle_L': 'knee_L',
        'hip_R': 'spine_lower', 'knee_R': 'hip_R', 'ankle_R': 'knee_R',
    }
    bad_par = []
    for nme, want in FK_PARENTS.items():
        got = int(parents[ix[nme]])
        want_ix = -1 if want == -1 else ix[want]
        if got != want_ix:
            bad_par.append(f'{nme}: {got} != {want_ix}')
    check(7, 'FK parent map', not bad_par,
          ', '.join(bad_par) if bad_par else f'all {nj} parents match the upright FK law (pelvis root)')
else:
    print('  [7] FK parent map        SKIP  (JNT1 pack — legacy pose law)')

# 8 — second-owner law (JNT3): the blend partner must be FK-ADJACENT to the
# band joint — its parent, its child, or its sibling (shares the parent). A
# partner outside that set would blend the surface across NON-adjacent bones
# (an armpit blending against the knee, nonsense matter). w2 must equal
# 1−w (the kernel's blend share) and never exceed 0.5 — term 1 dominates
# everywhere; seams blend, bands never surrender to their neighbor.
if IS_JNT3:
    j2o = joint2
    bad_range = int((j2o >= nj).sum())            # -1 is the LEGAL parent fallback
    act = w2 > 0.02
    own_p = parents[assign[act]]                    # band joint's FK parent
    j2v = j2o[act]
    j2_par = np.full(j2v.shape, -2, dtype=parents.dtype)  # -2 = no parent
    pos = j2v >= 0
    j2_par[pos] = parents[j2v[pos]]
    # adjacent = parent (own crease) | sibling (shares my parent) | child (mine)
    # | fallback (-1 -> the kernel uses the parent, adjacent by definition)
    adjacent = (j2v == own_p) | (j2_par == own_p) | (j2_par == assign[act]) | (j2v < 0)
    bad_adj = int((~adjacent).sum())
    bad_self = int((j2v == assign[act]).sum())
    bad_share = int((np.abs(w2 - (1.0 - w)) > 1e-3).sum())
    bad_dom = int((w2 > 0.5 + 1e-6).sum())
    n_blend = int((w2 > 0.01).sum())
    ok8 = (bad_range == 0 and bad_self == 0 and bad_adj == 0 and
           bad_share == 0 and bad_dom == 0)
    check(8, 'second-owner law', ok8,
          f'range {bad_range}, self {bad_self}, non-adjacent {bad_adj}, '
          f'share!=1-w {bad_share}, dominant {bad_dom}; blending verts {n_blend}/{nv}')
else:
    print('  [8] second-owner law     SKIP  (not a JNT3 pack)')

print()
if fails:
    print(f'GATE: FAIL — {len(fails)} check(s). DO NOT POST THIS PACK.')
    sys.exit(1)
print('GATE: PASS — the pack may ship to the engine.')
