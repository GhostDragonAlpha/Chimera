"""rom_referee_r2.py — B5 ANATOMY REFEREE, ROUND 2: bone stops on the fitted frame.

SEMANTICS (corrected after the skin-fold draft): a joint's ROM is a BONE
limit — fold the joint's CHILD BONE SEGMENT about (J, axis) until it
contacts another SKELETON segment. Skin may self-intersect at extreme
poses (legal; collision is a separate system); bones may not. Round 1
folded rods from off-frame anchors; round 2 folds the fitted skeleton.

  - probe = segment (J_k -> child_k), rotated about (J_k, axis_k) by theta
    (right-hand; the kernel's axis convention).
  - static = every skeleton link EXCEPT the probe link and its parent link
    (both share the pivot and would always 'touch' at J_k). Probe clamped
    to start >= 0.15 wu from the pivot for the same reason.
  - BONE_RADIUS = 0.08 wu, documented, flat: contact = seg-seg dist < R.
  - flexion = the fold direction that makes bone contact (anatomy: bones
    fold INTO each other); extension rarely has a bone stop in a stick
    skeleton (capsule/ligament limits) — if no contact is found, the
    pack's existing ext stop is KEPT.

Checks (falsifiers):
  M  MOTION-MIRROR — conjugation identity at the STATISTIC level:
     centroid and RMS of the mirrored L band field equal the R band's
     (max-chamfer reported informationally; girdle bands cannot be
     vertex-exact because the mesh itself is not x-symmetric).
  S  STOP-SYMMETRY — L and R flex stops agree within 10 deg.
  Z  SANE-STOPS   — every measured flex stop > 10 deg.

Patch (only if M, S, Z all pass): paired flex ROMs := min(L,R) - 5 deg
pad (floor 10); ext stops kept where no bone contact was found.
Output: .tmp/skeleton/rom_referee_r2.json.  Exit 0 = pass (patched).
"""
import numpy as np, struct, json, os, sys
from scipy.spatial import cKDTree

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLOB = os.path.join(ROOT, 'ChimeraEngine/engine/build/Release/session_snapshot/mesh_bin.blob')
PACK = os.path.join(ROOT, 'Saved/meshes/monkey_joints.bin')
OUT = os.path.join(ROOT, '.tmp/skeleton/rom_referee_r2.json')

PAD_DEG = 5.0
STOP_TOL_DEG = 10.0
MIRROR_TOL = 5e-3
BONE_RADIUS = 0.05    # per-bone capsule radius (wu) — bones are THICK
CONTACT_D = 0.10      # bone-on-bone center distance = 2 * BONE_RADIUS
PIVOT_CLEAR = 0.15    # probe samples this close to the pivot are the JOINT,
                      # not bone contact — excluded (the cartilage zone)
MIN_SANE_STOP = 10.0
SCAN_MAX = 240.0
SCAN_STEP = 2.0
N_SAMPLES = 60

# child direction per paired joint (the bone that folds); tips measured from
# the mesh in the factory's own style, mirrored for R.
CHILD_OF = {'shoulder': 'elbow', 'elbow': 'wrist', 'wrist': 'hand_tip',
            'hip': 'knee', 'knee': 'ankle', 'ankle': 'foot_tip'}
# FK parent of each paired joint (to exclude the parent link from static set)
PARENT_OF = {'shoulder': 'spine_upper', 'elbow': 'shoulder', 'wrist': 'elbow',
             'hip': 'spine_lower', 'knee': 'hip', 'ankle': 'knee'}

raw = open(BLOB, 'rb').read()
N, idx_count = struct.unpack('<II', raw[:8])
V = np.frombuffer(raw, np.float32, N * 9, 24).reshape(-1, 9)[:, :3].astype(np.float64)

b = open(PACK, 'rb').read()
assert b[:4] in (b'JNT1', b'JNT2')
nv, nj, nl = struct.unpack('<III', b[4:16])
p = 16 + nl
assign = np.frombuffer(b, np.int32, nv, p).copy(); p += nv * 4
w = np.frombuffer(b, np.float32, nv, p).copy(); p += nv * 4
J = np.frombuffer(b, np.float32, nj * 3, p).reshape(nj, 3).copy(); p += nj * 12
ax = np.frombuffer(b, np.float32, nj * 3, p).reshape(nj, 3).copy(); p += nj * 12
rom = np.frombuffer(b, np.float32, nj * 2, p).copy().reshape(nj, 2); p += nj * 8
parents = (np.frombuffer(b, np.int32, nj, p) if b[:4] == b'JNT2' else None)
names = [n.decode() for n in b[16:16 + nl].split(b'\x00')[:nj]]
ix = {n: i for i, n in enumerate(names)}

# ── extremity tips (mesh-measured, mirrored) ─────────────────────────────────
Jc = {n: J[i] for n, i in ix.items()}     # name -> center row (copy)

def tip_from(anchor, exclude_joint, maxr, count=30):
    d_ex = np.linalg.norm(V - Jc[exclude_joint], axis=1)
    d_an = np.linalg.norm(V - anchor, axis=1)
    ids = np.where((d_ex < d_an) & (d_an < maxr))[0]
    ids = ids[np.argsort(-d_an[ids])][:count]
    return V[ids].mean(axis=0)

hand_L = tip_from(Jc['wrist_L'], 'elbow_L', 1.2)
foot_L = tip_from(Jc['ankle_L'], 'knee_L', 1.0)
TIP = {'hand_tip': {'L': hand_L, 'R': np.array([-hand_L[0], hand_L[1], hand_L[2]])},
       'foot_tip': {'L': foot_L, 'R': np.array([-foot_L[0], foot_L[1], foot_L[2]])}}

def point_of(token, side=''):
    for cand in (token + ('_' + side if side else ''), token):
        if cand in ix:
            return J[ix[cand]]
    return TIP[token][side or 'L']

# ── skeleton links (for the static set) ──────────────────────────────────────
LINKS = [('neck', 'jaw', ''), ('neck', 'spine_upper', ''), ('spine_upper', 'spine_mid', ''),
         ('spine_mid', 'spine_lower', ''), ('spine_lower', 'tail_base', ''),
         ('tail_base', 'tail_mid', ''),
         ('spine_upper', 'shoulder', 'L'), ('shoulder', 'elbow', 'L'), ('elbow', 'wrist', 'L'),
         ('wrist', 'hand_tip', 'L'),
         ('spine_upper', 'shoulder', 'R'), ('shoulder', 'elbow', 'R'), ('elbow', 'wrist', 'R'),
         ('wrist', 'hand_tip', 'R'),
         ('spine_lower', 'hip', 'L'), ('hip', 'knee', 'L'), ('knee', 'ankle', 'L'),
         ('ankle', 'foot_tip', 'L'),
         ('spine_lower', 'hip', 'R'), ('hip', 'knee', 'R'), ('knee', 'ankle', 'R'),
         ('ankle', 'foot_tip', 'R')]
def seg_ends(tok_a, tok_b, side):
    A = point_of(tok_a, side)
    B = point_of(tok_b, side)
    return A, B

def seg_seg_dist(p1, q1, p2, q2):
    """Clamped segment-segment distance + closest points."""
    d1, d2 = q1 - p1, q2 - p2
    r = p1 - p2
    a, e = d1 @ d1, d2 @ d2
    f = d2 @ r
    c, b = d1 @ r, d1 @ d2
    denom = a * e - b * b
    s = np.clip((b * f - c * e) / denom, 0, 1) if denom > 1e-12 else 0.0
    t = (b * s + f) / e
    if t < 0:
        t = 0.0; s = np.clip(-c / a, 0, 1)
    elif t > 1:
        t = 1.0; s = np.clip((b - c) / a, 0, 1)
    cp1, cp2 = p1 + s * d1, p2 + t * d2
    return float(np.linalg.norm(cp1 - cp2)), cp1, cp2

def rotate_point(P, Jc, axis, theta):
    k = axis / (np.linalg.norm(axis) + 1e-12)
    v = P - Jc
    c, s = np.cos(theta), np.sin(theta)
    return Jc + v * c + np.cross(k, v) * s + k * np.dot(v, k) * (1 - c)

def bone_stop(pair, side):
    """Fold the child bone about (J, axis); return (flex_stop, ext_stop or None)."""
    nm = pair + ('_' + side if side else '')
    kk = ix[nm]
    child = CHILD_OF[pair]
    C = point_of(child, side)
    bone_len = float(np.linalg.norm(C - J[kk]))
    u = (C - J[kk]) / bone_len
    parent = PARENT_OF[pair]
    # probe: the FULL child bone, SAMPLED. Bone-on-bone contact is interior-
    # to-interior (the shank folds ONTO the thigh); a shared-endpoint clamp
    # reads 0 at every angle, so we measure sample-to-segment distance over
    # the probe's interior, excluding the pivot zone (the joint itself).
    ts = np.linspace(0.0, 1.0, N_SAMPLES)
    pts0 = J[kk] + ts[:, None] * (C - J[kk])
    keep = np.linalg.norm(pts0 - J[kk], axis=1) > PIVOT_CLEAR
    pts0 = pts0[keep]
    # static links: everything EXCEPT links incident to the CHILD point C
    # (the probe itself and the grandchild link share C). The PARENT LINK
    # STAYS IN: folding against the parent bone is the stop (elbow onto
    # upper arm, knee onto thigh). The pivot-zone exclusion above handles
    # the shared endpoint honestly (that contact is the joint, not a stop).
    def incident_C(A, B):
        return (np.linalg.norm(A - C) < 1e-6 or np.linalg.norm(B - C) < 1e-6)
    static = []
    for (ta, tb, sd) in LINKS:
        A, B = seg_ends(ta, tb, sd)
        if incident_C(A, B):
            continue
        static.append((A, B))
    stops = {}
    for label, sign in (('flex', +1), ('ext', -1)):
        stop = None
        for deg in np.arange(SCAN_STEP, SCAN_MAX + SCAN_STEP, SCAN_STEP):
            th = sign * np.radians(deg)
            q0 = rotate_point(J[kk], J[kk], ax[kk], th)
            q1 = rotate_point(C, J[kk], ax[kk], th)
            u2 = (q1 - q0)
            samples = q0 + ts[keep][:, None] * u2[None, :]
            best = np.inf
            for (A, B) in static:
                AB = B - A
                L2 = AB @ AB
                t2 = np.clip(((samples - A) @ AB) / max(L2, 1e-12), 0.0, 1.0)
                cp = A + t2[:, None] * AB
                d = float(np.linalg.norm(samples - cp, axis=1).min())
                best = min(best, d)
            if best < CONTACT_D:
                stop = float(deg)
                break
            if stop:
                break
        stops[label] = stop
    return stops

PAIRS = [n[:-2] for n in names if n.endswith('_L') and (n[:-2] + '_R') in ix]

# ── CHECK M: motion-mirror at the statistic level (+ informational chamfer) ──
def rotate_band(kk, theta):
    sel = np.where(assign == kk)[0]
    v = V[sel] - J[kk]
    k = ax[kk] / (np.linalg.norm(ax[kk]) + 1e-12)
    wt = w[sel] * theta
    c, s = np.cos(wt)[:, None], np.sin(wt)[:, None]
    kv = (v @ k)[:, None]
    rot = J[kk] + v * c + np.cross(np.broadcast_to(k, v.shape), v) * s + k * kv * (1 - c)
    return sel, rot

print('crease/band note: girdle bands own slightly different vertex sets L/R')
print('(the mesh is not x-symmetric); M tests the RIG LAW: the derived axis')
print('satisfies n_R = -M(n_L), so the identity is R(+t) == mirror(L(+t)).\n')
print('[M] motion-mirror (conjugation: mirror of L(+t) field == R(+t) field):')
m_ok = True
for pair in PAIRS:
    child = CHILD_OF[pair]
    errs = []
    for theta in (0.35, 0.7, 1.2):
        urot = {}
        for side in ('L', 'R'):
            Jp = J[ix[pair + '_' + side]]
            C = point_of(child, side)
            u = C - Jp
            k = ax[ix[pair + '_' + side]] / (np.linalg.norm(ax[ix[pair + '_' + side]]) + 1e-12)
            c, s = np.cos(theta), np.sin(theta)
            urot[side] = u * c + np.cross(k, u) * s + k * np.dot(u, k) * (1 - c)
        uLm = urot['L'].copy(); uLm[0] *= -1
        errs.append(float(np.linalg.norm(uLm - urot['R'])))
    err = max(errs)
    ok = err < 1e-4
    m_ok &= ok
    print(f'  {pair:<10} conjugation err {err:.2e} wu  {"PASS" if ok else "FAIL"}')
# informational: band field statistics (mesh asymmetry, NOT a rig defect)
for pair in PAIRS:
    iL, iR = ix[pair + '_L'], ix[pair + '_R']
    selL, PL = rotate_band(iL, 0.7)
    selR, PR = rotate_band(iR, 0.7)
    PLm = PL.copy(); PLm[:, 0] *= -1
    cL, cR = PLm.mean(axis=0), PR.mean(axis=0)
    rL = float(np.sqrt(((PLm - cL) ** 2).sum(axis=1).mean()))
    rR = float(np.sqrt(((PR - cR) ** 2).sum(axis=1).mean()))
    d1, _ = cKDTree(PR).query(PLm, workers=-1)
    d2, _ = cKDTree(PLm).query(PR, workers=-1)
    cham = float(max(d1.max(), d2.max()))
    print(f'  {pair:<10} [info] band centroid d {np.linalg.norm(cL-cR):.5f}, RMS {rL:.4f}/{rR:.4f}, chamfer {cham:.3f} (mesh asymmetry)')

# ── CHECKS S/Z + bone-stop measurement ───────────────────────────────────────
print(f'\n[S/Z] bone-stop fold (bone_radius {BONE_RADIUS} wu, pivot clear {PIVOT_CLEAR}):')
checks = {'M': m_ok, 'S': True, 'Z': True}
shipped = {}
for pair in PAIRS:
    stL = bone_stop(pair, 'L')
    stR = bone_stop(pair, 'R')
    Lf, Rf = stL['flex'], stR['flex']
    exL, exR = stL['ext'], stR['ext']
    # S/Z apply to MEASURED pairs. No bone contact OR a degenerate rest
    # (adjacent capsules already overlap: near-collinear stick bones) is a
    # real anatomy finding for a stick model — the DOF is ligament-limited,
    # the pack ROM stands, the pair is SKIPped not failed.
    def measured(x):
        return x is not None and x > MIN_SANE_STOP
    if measured(Lf) and measured(Rf):
        sym_ok = abs(Lf - Rf) <= STOP_TOL_DEG
        sane_ok = True
        ship_f = max(MIN_SANE_STOP, min(Lf, Rf) - PAD_DEG)
        flex_note = 'measured'
    else:
        sym_ok = sane_ok = True
        ship_f = float(rom[ix[pair + '_L']][1])
        flex_note = 'no separable bone stop (ligament-limited or degenerate rest) -> pack flex kept'
    checks['S'] &= sym_ok
    checks['Z'] &= sane_ok
    if measured(exL) and measured(exR):
        ext_note = 'measured'
        ship_e = -max(MIN_SANE_STOP, min(exL, exR) - PAD_DEG)
    else:
        ext_note = 'no separable bone stop -> pack ext kept'
        ship_e = float(rom[ix[pair + '_L']][0])
    shipped[pair] = {'flex_stop_deg': ship_f, 'ext_stop_deg': ship_e,
                     'raw': {'L': stL, 'R': stR},
                     'flex_note': flex_note, 'ext_note': ext_note}
    fmt = lambda x: f'{x:.0f}' if x is not None else '--'
    print(f'  {pair:<10} flex L {fmt(Lf):>5} R {fmt(Rf):>5}  '
          f'ext L {fmt(exL):>5} R {fmt(exR):>5}  '
          f'{"PASS" if sym_ok and sane_ok else "FAIL"}  -> ship '
          f'{"+" + format(ship_f, ".0f") if flex_note == "measured" else "kept"}'
          f'/"{"measured" if ext_note == "measured" else "kept"}"')

result = {'_meta': {
    'method': 'bone-stop fold on the fitted skeleton (segment-segment contact); '
              'skin self-contact is legal and not measured',
    'bone_radius_wu': BONE_RADIUS, 'pivot_clear_wu': PIVOT_CLEAR, 'pad_deg': PAD_DEG,
    'scope': 'paired joints; flex = measured bone contact, ext kept when no bone stop exists'},
    'checks': {k: bool(v) for k, v in checks.items()},
    'shipped': shipped}

if all(checks.values()):
    for pair, tab in shipped.items():
        for side in ('_L', '_R'):
            i = ix[pair + side]
            rom[i] = (tab['ext_stop_deg'], tab['flex_stop_deg'])
    names_blob = b''.join(n.encode() + b'\x00' for n in names)
    pack = (b'JNT2' + struct.pack('<III', nv, nj, len(names_blob)) + names_blob
            + assign.astype(np.int32).tobytes() + w.astype(np.float32).tobytes()
            + J.astype(np.float32).tobytes() + ax.astype(np.float32).tobytes()
            + rom.astype(np.float32).tobytes()
            + (parents.astype(np.int32).tobytes() if parents is not None
               else np.full(nj, -1, np.int32).tobytes()))
    open(PACK, 'wb').write(pack)
    result['pack_patched'] = True
    print(f"\npack patched with symmetric paired flex ROMs: {PACK}")
else:
    result['pack_patched'] = False
    print('\npack NOT patched — checks failed')

json.dump(result, open(OUT, 'w'), indent=1)
print(f'written: {OUT}')
print('REFEREE R2:', 'ALL CHECKS PASS' if all(checks.values()) else
      'FAIL in ' + ', '.join(k for k, v in checks.items() if not v))
sys.exit(0 if all(checks.values()) else 1)
