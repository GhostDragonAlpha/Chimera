"""rig_factory_fit.py — THE RIG FITS THE MESH, IN THE ENGINE'S OWN FRAME. (2026-09-03)

The defect this retires: the old pack was built offline (npz/GLB vertex order
≠ engine order), so 8 of 19 joints had EMPTY bands (their rotations moved
nothing) and elbow_R floated in free space off the creature. This factory
reads the ENGINE's canonical vertex list — session_snapshot/mesh_bin.blob,
the exact bytes the engine holds — and derives everything from the mesh:

  1. MEASURED L-CHAIN LANDMARKS (the on-mesh L anchors that survived every
     audit) are medoid-snapped onto their nearest vertex patch: J := the
     patch's medoid, so every center is ON the creature by construction.
  2. THE MIRROR LAW builds every R limb: J_R := (-J_L.x, J_L.y, J_L.z).
     R is never independently fitted — the elbow-bug class is structurally
     impossible. Hinge axes follow the SAGITTAL LAW (2026-09-04): paired
     joints share the identical signed x-hat, sign per joint from the
     closing test (flexion closes the interior angle). The earlier u x v
     derivation is degenerate for near-collinear bones (every limb bends
     < 26 deg at rest) and inherited the rest pose's sideways splay — the
     wing-splay defect the dyad convicted at verdict round 1.
  3. ROM LAW: paired joints take the L stop on both sides. The asymmetric R
     stops (elbow_R 166.78, hip_R -104.74, ...) were measured by folding
     from OFF-FRAME anchors — retired with a referee note, re-measurable
     on this frame later. Central joints (neck/spine/tail/jaw) keep their
     measured stops: their anchors were on the body axis, on-mesh.
  4. ASSIGNMENT: every vertex -> nearest bone SEGMENT (point-to-segment),
     owner = the segment's driving joint. w = d2/(d1+d2): 1 deep in a band,
     0.5 at boundaries — bends blend across the crease instead of tearing.
     NO vertex is unassigned; NO band is empty. Falsifier of record.
  5. Outputs: JNT2 pack (engine wire format: JNT1 record PLUS the FK parent
     map), .npz source, MJCF primate template (mirror law in the tree
     itself, for the B6 referee), and a refit report.

Run:  python tools/rig_factory_fit.py
"""
import numpy as np, struct, json, os, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLOB = os.path.join(ROOT, 'ChimeraEngine/engine/build/Release/session_snapshot/mesh_bin.blob')
PACK_OUT = os.path.join(ROOT, 'Saved/meshes/monkey_joints.bin')
NPZ_OUT = os.path.join(ROOT, '.tmp/skeleton/joints_pack.npz')
MJCF_OUT = os.path.join(ROOT, '.tmp/skeleton/chimera_primate.xml')
ROM_OUT = os.path.join(ROOT, '.tmp/skeleton/factory_rom_r2.json')
REPORT = os.path.join(ROOT, '.tmp/skeleton/rig_fit_report.txt')

# ── 1. THE CANONICAL FRAME: the engine's own vertices ────────────────────────
raw = open(BLOB, 'rb').read()
N, idx_count = struct.unpack('<II', raw[:8])
V = np.frombuffer(raw, np.float32, N * 9, 24).reshape(-1, 9)[:, :3].astype(np.float64)
assert N == 18459, f'canonical frame expects 18459 verts, blob says {N}'
print(f'canonical frame: {N} verts (engine order, mesh_bin.blob)')

# ── 2. MEASURED L-CHAIN LANDMARKS (on-mesh survivors of every audit) ─────────
# THE SIDE LAW (2026-09-04, the operator caught it on the viewport tags):
# anatomical LEFT := up x forward. The creature's forward is +z (the tail
# extends to -z, the jaw to +z — measured from this very table), so
# left = y-hat x z-hat = +x. The original anchors were stamped under the
# DEFAULT CAMERA's left, which mirrored the creature's own — every _L/_R tag
# was on the wrong limb. The anchors below are the SAME measured points,
# renamed to the creature's perspective: _L anchors now sit at +x, and the
# mirror law (J_R := -J_L.x, ...) builds the other side as always. Rotation
# about x-hat acts only in y-z, so the sagittal AXIS table and the ROM stops
# are mirror-invariant — no re-derivation, the same numbers serve both sides.
L_landmarks = {
    'neck':        (0.0260, 8.3711, 0.6614),
    'jaw':         (0.1843, 9.0493, 0.3625),
    'spine_upper': (0.0260, 7.7121, 0.0140),
    'spine_mid':   (0.0260, 6.8580, -0.1195),
    'spine_lower': (0.0260, 5.6824, 0.0874),
    'tail_base':   (0.0260, 3.9607, -0.7033),
    'tail_mid':    (0.0260, 3.9497, -1.8190),
    'shoulder_L':  (0.9975, 6.0733, -0.0677),
    'elbow_L':     (1.8279, 5.0633, -0.0892),
    'wrist_L':     (2.3269, 4.1482, -0.1016),
    'hip_L':       (0.4727, 3.1696, 0.1627),
    'knee_L':      (0.4937, 1.7670, 0.1299),
    'ankle_L':     (0.5132, 1.1693, 0.0325),
}
# ROMs: central = measured stops (anchors were on the axis); pairs take L on
# both sides (the R stops were folded from off-frame anchors — retired).
ROM_central = {  # ext, flex (deg)
    'neck': (-35.84, 130.23), 'jaw': (-30.0, 60.0),
    'spine_upper': (-169.73, 119.16), 'spine_mid': (-124.51, 126.17),
    'spine_lower': (-117.87, 152.51), 'tail_base': (-30.0, 87.14),
    'tail_mid': (-139.06, 138.73),
}
ROM_L = {
    # Fallbacks for joints the referee measures as ligament-limited (no
    # separable bone stop in the sagittal plane — the referee's own finding,
    # round 3). "Kept" echoes THESE, so they must be the working values the
    # operator has been living with, never round-1 placeholders: the elbow's
    # 125 is the round-2 shipped stop (now understood as a soft/anatomical
    # limit, the 130 contact it came from having been a splay artifact).
    'shoulder_L': (-30.0, 60.0), 'elbow_L': (-30.0, 125.0), 'wrist_L': (-30.0, 60.0),
    'hip_L': (-150.23, 60.0), 'knee_L': (-147.89, 140.15), 'ankle_L': (-159.21, 131.44),
}
AXIS_L = {  # PAIRED joints: the SAGITTAL LAW (2026-09-04, see the EMIT block).
    # Sign per joint from the closing test (tools/axis_sagittal_probe.py):
    # +theta must swing the distal bone TOWARD its parent — shoulder/elbow/hip/
    # knee close under +x, wrist/ankle under -x. Central joints keep their
    # measured sweep axes (x-hat for the spine chain, unchanged).
    'neck': (1.0, 0.0, 0.0), 'jaw': (1.0, 0.0, 0.0),
    'spine_upper': (1.0, 0.0, 0.0), 'spine_mid': (1.0, 0.0, 0.0),
    'spine_lower': (1.0, 0.0, 0.0), 'tail_base': (1.0, 0.0, 0.0), 'tail_mid': (1.0, 0.0, 0.0),
    'shoulder_L': (1.0, 0.0, 0.0), 'elbow_L': (1.0, 0.0, 0.0),
    'wrist_L': (-1.0, 0.0, 0.0), 'hip_L': (1.0, 0.0, 0.0),
    'knee_L': (1.0, 0.0, 0.0), 'ankle_L': (-1.0, 0.0, 0.0),
}

def medoid_snap(landmark, k=8, r_cap=0.8):
    """J := medoid of the vertex patch around the landmark. Returns (J, snap_d).
    The old anchors were measured INSIDE the mesh volume (rod-folding), so the
    radius grows until it owns k verts; the nearest-k fallback guarantees a
    non-empty patch. A LARGE snap_d is itself a finding: an anchor far from
    the surface — reported, never hidden."""
    d = np.linalg.norm(V - np.array(landmark), axis=1)
    order = np.argsort(d)
    r = float(min(max(2.5 * d[order[k]], 0.12), r_cap))
    patch = order[d[order] <= r]
    if len(patch) == 0:
        patch = order[:k]
    if len(patch) > 400:
        patch = patch[:400]          # nearest 400 — medoid is O(p^2)
    P = V[patch]
    dm = np.linalg.norm(P[:, None, :] - P[None, :, :], axis=2)
    J = P[int(np.argmin(dm.sum(axis=1)))]
    return J, float(np.linalg.norm(J - np.array(landmark)))

J = {}
snap = {}
for name, lm in L_landmarks.items():
    J[name], snap[name] = medoid_snap(lm)
# THE AXIS LAW: CENTRAL joints ride the mirror axis (x := 0). The medoid
# snaps drift off-axis because the mesh itself is asymmetric (x up to 0.20);
# a spine that is not on the axis breaks the mirror conjugation for every
# limb hung off it (the referee's M check convicted exactly this).
for _cn in ('neck', 'jaw', 'spine_upper', 'spine_mid', 'spine_lower',
            'tail_base', 'tail_mid'):
    J[_cn] = J[_cn] * np.array([0.0, 1.0, 1.0])

# ── 3. THE MIRROR LAW: R limbs are x-negated copies, never fitted ────────────
for name in list(L_landmarks):
    if name.endswith('_L'):
        J[name[:-2] + '_R'] = np.array([-J[name][0], J[name][1], J[name][2]])
        snap[name[:-2] + '_R'] = 0.0   # exact by construction

# extremity tips: measured from the mesh, mirrored for R
arm_L = np.linalg.norm(V - J['wrist_L'], axis=1)
beyond_wrist = np.where((np.linalg.norm(V - J['elbow_L'], axis=1) < arm_L) & (arm_L < 1.2))[0]
tip_ids = beyond_wrist[np.argsort(-arm_L[beyond_wrist])][:30]
hand_tip_L = V[tip_ids].mean(axis=0)
leg_L = np.linalg.norm(V - J['ankle_L'], axis=1)
beyond_ankle = np.where((np.linalg.norm(V - J['knee_L'], axis=1) < leg_L) & (leg_L < 1.0))[0]
tip_ids = beyond_ankle[np.argsort(-leg_L[beyond_ankle])][:30]
foot_tip_L = V[tip_ids].mean(axis=0)
tail_ids = np.where(V[:, 2] < J['tail_mid'][2] - 0.3)[0]
tail_d = np.linalg.norm(V[tail_ids] - J['tail_mid'], axis=1)
tip_ids = tail_ids[np.argsort(-tail_d)][:50]
tail_tip = V[tip_ids].mean(axis=0)
head_top = V[np.argsort(-V[:, 1])][:60].mean(axis=0)

# ── 4. SEGMENTS (owner <- verts nearest this segment) ────────────────────────
def seg(a, b, owner): return (np.asarray(a, float), np.asarray(b, float), owner)
segments = [
    seg(J['neck'], head_top, 'neck'),
    seg(J['spine_upper'], J['neck'], 'spine_upper'),
    seg(J['spine_mid'], J['spine_upper'], 'spine_mid'),
    seg(J['spine_lower'], J['spine_mid'], 'spine_lower'),
    seg(J['tail_base'], J['spine_lower'], 'tail_base'),
    seg(J['tail_mid'], J['tail_base'], 'tail_mid'),
    seg(tail_tip, J['tail_mid'], 'tail_mid'),
    seg(J['shoulder_L'], J['elbow_L'], 'shoulder_L'),
    seg(J['elbow_L'], J['wrist_L'], 'elbow_L'),
    seg(hand_tip_L, J['wrist_L'], 'wrist_L'),
    seg(J['hip_L'], J['knee_L'], 'hip_L'),
    seg(J['knee_L'], J['ankle_L'], 'knee_L'),
    seg(foot_tip_L, J['ankle_L'], 'ankle_L'),
]
# the mirror law, applied to the segment table itself
for a, b, owner in list(segments):
    if owner.endswith('_L'):
        segments.append(seg(np.array([-a[0], a[1], a[2]]),
                            np.array([-b[0], b[1], b[2]]),
                            owner[:-2] + '_R'))

A = np.stack([np.array(s[1]) - np.array(s[0]) for s in segments])       # (S,3)
B0 = np.stack([np.array(s[0]) for s in segments])
L2 = (A * A).sum(axis=1)
L2[L2 == 0] = 1e-12
D = V[:, None, :] - B0[None, :, :]                                      # (N,S,3)
t = np.clip(np.einsum('nsc,sc->ns', D, A) / L2[None, :], 0.0, 1.0)      # (N,S)
closest = B0[None, :, :] + t[:, :, None] * A[None, :, :]
dseg = np.linalg.norm(V[:, None, :] - closest, axis=2)                  # (N,S)
owners = [s[2] for s in segments]
owner_idx = np.array([owners.index(o) for o in owners])
best = np.argmin(dseg, axis=1)
assign_name = np.array([owners[b] for b in best])
# OWNERSHIP SHELLS (the rigger's law): a LIMB may only claim verts within
# LIMB_CAP of its own segment — on a primate the belly flank is euclidean-
# closer to an arm segment than to the spine line, but it belongs to the
# torso. Rejected claims fall to the nearest AXIAL segment (neck/spine/tail).
LIMB_CAP = 0.7
limb_mask = np.array([not (o.startswith(('neck', 'jaw', 'spine', 'tail'))) for o in owners])
axial_idx = np.where(~limb_mask)[0]
claim_rejected = limb_mask[best] & (dseg[np.arange(N), best] > LIMB_CAP)
if claim_rejected.any():
    ri = np.where(claim_rejected)[0]
    best[ri] = axial_idx[np.argmin(dseg[ri][:, axial_idx], axis=1)]
    assign_name[ri] = np.array([owners[b] for b in best[ri]])
# second-best distance among DIFFERENT-owner segments -> blended weight
d2 = dseg.copy()
owner_of_best = owner_idx[best][:, None]                 # (N,1)
d2[owner_idx[None, :] == owner_of_best] = np.inf
second = np.argmin(d2, axis=1)
d1v = dseg[np.arange(N), best]
d2v = d2[np.arange(N), second]
w = d2v / (d1v + d2v + 1e-9)
# JAW: its medoid sits inside the skull (no verts within reach), so it takes
# its band from the neck-owned face region — the nearest verts to J_jaw.
djaw = np.linalg.norm(V - J['jaw'], axis=1)
face = np.where((assign_name == 'neck') & (djaw < 0.8))[0]
face = face[np.argsort(djaw[face])][:150]
assign_name[face] = 'jaw'

# ENVELOPE WEIGHTS (the rigger's law, JNT2 — 2026-09-03): w fades from 0.5 at
# the segment's OWN crease (t=0, blending with the PARENT bone — exactly the
# kernel's second influence) to 1.0 mid-segment. The measured tear lived in
# the old w cliff: hard segmentation put w=1 within one edge of w=0, so 125
# deg of rotation concentrated on a single-edge transition (62.9x edge
# stretch at the elbow, skin torn open). The envelope spreads the transition
# over the proximal half of every segment; LBS then bounds the stretch.
t_own = t[np.arange(N), best]                   # projection along OWN segment
smooth = t_own * t_own * (3.0 - 2.0 * t_own)    # C1 smoothstep
w = 0.5 + 0.5 * smooth
w[face] = 0.85                                  # jaw keeps its dedicated weight

# ── 5. EMIT: names fixed to the legacy order (D7 keys reference indices) ─────
names = ['neck', 'jaw', 'spine_upper', 'spine_mid', 'spine_lower', 'tail_base',
         'tail_mid', 'shoulder_L', 'shoulder_R', 'elbow_L', 'elbow_R',
         'wrist_L', 'wrist_R', 'hip_L', 'hip_R', 'knee_L', 'knee_R',
         'ankle_L', 'ankle_R']
nj = len(names)
Jf = np.zeros((nj, 3), np.float32)
AXf = np.zeros((nj, 3), np.float32)
ROMf = np.zeros((nj, 2), np.float32)
for i, nme in enumerate(names):
    Jf[i] = J[nme]
    src = nme if not nme.endswith('_R') else nme[:-2] + '_L'
    axl = AXIS_L[src]
    # THE HINGE AXIS IS THE BODY'S SAGITTAL LAW (2026-09-04, successor to the
    # u x v derivation the referee shipped in round 2): n = (J-parent) x
    # (child-J) is DEGENERATE for near-collinear bones — every limb bends
    # < 26 deg at rest (tools/axis_sagittal_probe.py, alignment with the true
    # plane normal as low as 0.10), so the derived axis inherited the rest
    # pose's sideways splay: the elbow's axis pointed mostly world-forward
    # (z), and 125 deg of flexion swung the forearm 1.40 in x vs 0.29 in z —
    # the wing splay the dyad caught at verdict round 1. A primate limb hinge
    # folds in the PARA-SAGITTAL plane: shared +/-x-hat, the spine chain's
    # own axis. x-hat is invariant under the y/z-negation mirror, so L and R
    # share the identical axis by construction (the mirror law for axes
    # survives); Rodrigues about x-hat preserves v.x exactly, so flexion
    # moves the distal bone strictly in y-z — a splay is geometrically
    # impossible. Central joints keep their measured sweep axes.
    AXf[i] = axl
    ROMf[i] = ROM_central.get(nme, ROM_L.get(src, (-30.0, 60.0)))
# THE REFEREE OWNS THE PAIRED STOPS (2026-09-04): the tables above are only the
# factory's fallback — the B5 referee's measured bone stops are the authority,
# so its verdicts are OVERLAID here from the verdict file. A missing file is a
# loud warning, never a silent fall-back to round-1 numbers (the regression
# this retires: the envelope re-emit shipped elbow flex 60 where the referee
# shipped 125).
_ref_path = os.path.join(ROOT, '.tmp/skeleton/rom_referee_r2.json')
if os.path.exists(_ref_path):
    _ref = json.load(open(_ref_path))
    _shipped = _ref.get('shipped', {})
    for _pair, _tab in _shipped.items():
        for _s in ('_L', '_R'):
            ROMf[names.index(_pair + _s)] = (_tab['ext_stop_deg'], _tab['flex_stop_deg'])
    print(f"ROM overlay: {len(_shipped)} referee verdicts applied to the pack")
else:
    print("WARNING: no referee verdict file .tmp/skeleton/rom_referee_r2.json — "
          "pack carries factory fallback ROMs; run tools/rom_referee_r2.py")
assign_i32 = np.array([names.index(a) for a in assign_name], np.int32)
w_f32 = w.astype(np.float32)

os.makedirs(os.path.dirname(PACK_OUT), exist_ok=True)
if os.path.exists(PACK_OUT) and not os.path.exists(PACK_OUT + '.pre_refit.bak'):
    shutil.copyfile(PACK_OUT, PACK_OUT + '.pre_refit.bak')   # keep the ORIGINAL convict
names_blob = b''.join(n.encode() + b'\x00' for n in names)
# JNT2: the FK parent map — the SECOND BONE of every crease. Authority is the
# engine's own overlay FK table (Engine::push_rig_overlay); the LBS kernel
# blends each vertex between its joint and this parent. -1 = root/central.
JNT2_PARENTS = {
    'neck': -1, 'jaw': 'neck',
    'spine_upper': 'neck', 'spine_mid': 'spine_upper',
    'spine_lower': 'spine_mid', 'tail_base': 'spine_lower', 'tail_mid': 'tail_base',
    'shoulder_L': 'spine_upper', 'elbow_L': 'shoulder_L', 'wrist_L': 'elbow_L',
    'shoulder_R': 'spine_upper', 'elbow_R': 'shoulder_R', 'wrist_R': 'elbow_R',
    'hip_L': 'spine_lower', 'knee_L': 'hip_L', 'ankle_L': 'knee_L',
    'hip_R': 'spine_lower', 'knee_R': 'hip_R', 'ankle_R': 'knee_R',
}
parents_i32 = np.array([-1 if JNT2_PARENTS[nme] == -1 else names.index(JNT2_PARENTS[nme])
                        for nme in names], np.int32)
pack = (b'JNT2' + struct.pack('<III', N, nj, len(names_blob)) + names_blob
        + assign_i32.tobytes() + w_f32.tobytes() + Jf.tobytes() + AXf.tobytes() + ROMf.tobytes()
        + parents_i32.tobytes())
open(PACK_OUT, 'wb').write(pack)
np.savez(NPZ_OUT, vert_joint=assign_i32, vert_w=w_f32, J=Jf, axis=AXf, rom=ROMf,
         parents=parents_i32,
         names=np.array(names, dtype='<U11'))

# ── 6. MJCF TEMPLATE — the mirror law lives in the tree itself ───────────────
# Built by concatenation (f-string brace nesting is a syntax trap).
def body_xml(name, pos, axis, rom, children=''):
    ext, flex = rom
    rng = f'{min(ext, flex)} {max(ext, flex)}'
    return (f'  <body name="{name}" pos="{pos[0]:.4f} {pos[1]:.4f} {pos[2]:.4f}">\n'
            f'   <joint name="{name}_hinge" type="hinge" axis="{axis[0]:.4f} {axis[1]:.4f} {axis[2]:.4f}" '
            f'range="{rng}" limited="true"/>\n{children}  </body>\n')

def chain_L():
    return body_xml('shoulder_L', J['shoulder_L'] - J['spine_upper'], AXIS_L['shoulder_L'], ROM_L['shoulder_L'],
           body_xml('elbow_L', J['elbow_L'] - J['shoulder_L'], AXIS_L['elbow_L'], ROM_L['elbow_L'],
           body_xml('wrist_L', J['wrist_L'] - J['elbow_L'], AXIS_L['wrist_L'], ROM_L['wrist_L'])))

def chain_R():
    neg = lambda p: np.array([-p[0], p[1], p[2]])
    afl = lambda a: np.array([a[0], -a[1], -a[2]])   # the axis mirror law
    # MIRRORED axes and SAME ROMs as L: +theta flexes both sides identically
    return body_xml('shoulder_R', neg(J['shoulder_L']) - J['spine_upper'], afl(AXIS_L['shoulder_L']), ROM_L['shoulder_L'],
           body_xml('elbow_R', neg(J['elbow_L']) - neg(J['shoulder_L']), afl(AXIS_L['elbow_L']), ROM_L['elbow_L'],
           body_xml('wrist_R', neg(J['wrist_L']) - neg(J['elbow_L']), afl(AXIS_L['wrist_L']), ROM_L['wrist_L'])))

def leg_chain(side):
    if side == 'L':
        return body_xml('hip_L', J['hip_L'] - J['spine_lower'], AXIS_L['hip_L'], ROM_L['hip_L'],
               body_xml('knee_L', J['knee_L'] - J['hip_L'], AXIS_L['knee_L'], ROM_L['knee_L'],
               body_xml('ankle_L', J['ankle_L'] - J['knee_L'], AXIS_L['ankle_L'], ROM_L['ankle_L'])))
    neg = lambda p: np.array([-p[0], p[1], p[2]])
    afl = lambda a: np.array([a[0], -a[1], -a[2]])   # the axis mirror law
    return body_xml('hip_R', neg(J['hip_L']) - J['spine_lower'], afl(AXIS_L['hip_L']), ROM_L['hip_L'],
           body_xml('knee_R', neg(J['knee_L']) - neg(J['hip_L']), afl(AXIS_L['knee_L']), ROM_L['knee_L'],
           body_xml('ankle_R', neg(J['ankle_L']) - neg(J['knee_L']), afl(AXIS_L['ankle_L']), ROM_L['ankle_L'])))

axial = body_xml('neck', J['neck'] - J['spine_upper'], AXIS_L['neck'], ROM_central['neck'],
         body_xml('jaw', J['jaw'] - J['neck'], AXIS_L['jaw'], ROM_central['jaw']))
spine_chain = body_xml('spine_upper', J['spine_upper'] - J['spine_mid'], AXIS_L['spine_upper'], ROM_central['spine_upper'],
              axial + chain_L() + chain_R())
spine_chain = body_xml('spine_mid', J['spine_mid'] - J['spine_lower'], AXIS_L['spine_mid'], ROM_central['spine_mid'],
              spine_chain)
tail_chain = body_xml('tail_base', J['tail_base'] - J['spine_lower'], AXIS_L['tail_base'], ROM_central['tail_base'],
             body_xml('tail_mid', J['tail_mid'] - J['tail_base'], AXIS_L['tail_mid'], ROM_central['tail_mid']))

mjcf = ('<mujoco model="chimera_primate_r2">\n'
        '<!-- GENERATED by tools/rig_factory_fit.py - the mirror law is IN THE TREE:\n'
        '     every R body pos is the x-negation of its L sibling, by construction. -->\n'
        '<option timestep="0.002" integrator="implicitfast"/>\n'
        '<worldbody>\n'
        '  <geom name="floor" type="plane" size="5 5 0.1" pos="0 0 0"/>\n'
        + body_xml('spine_lower', np.array([0.0, J['spine_lower'][1], J['spine_lower'][2]]),
                   AXIS_L['spine_lower'], ROM_central['spine_lower'], spine_chain)
        + tail_chain + leg_chain('L') + leg_chain('R')
        + '</worldbody>\n</mujoco>\n')
# NOTE: spine_lower/tail/legs hang off worldbody in this template (root bodies
# with 0-offset hinges) - the B6 referee welds them via its own harness; the
# ENGINE pack above is the authority for the render rig.
open(MJCF_OUT, 'w').write(mjcf)

# ── 7. REFEREE RECORD R2 + REPORT ────────────────────────────────────────────
retired = {
    'law': 'ROM_R asymmetric stops retired 2026-09-03: measured by folding from OFF-FRAME anchors '
           '(the empty-band defect). Pairs now carry the L stop on both sides. Re-measure on this frame.',
    'retired': {'elbow_R': 166.78, 'hip_R': [-104.74, 152.23], 'knee_R': [-160.87, 151.33], 'ankle_R': [-143.62, 143.61]},
}
json.dump(retired, open(ROM_OUT, 'w'), indent=1)

lines = ['RIG FIT REPORT — canonical frame = engine mesh_bin.blob order',
         f'verts: {N}   joints: {nj}   pack bytes: {len(pack)}', '',
         f'{"joint":<13}{"J (refit)":<30}{"snap_d":>7}{"band":>7}{"w_min":>7}{"w_mean":>8}', '-' * 74]
for i, nme in enumerate(names):
    sel = assign_i32 == i
    nb = int(sel.sum())
    lines.append(f'{nme:<13}{str(np.round(Jf[i], 4)):<30}{snap[nme]:7.3f}{nb:7d}{w[sel].min() if nb else 0:7.2f}{w[sel].mean() if nb else 0:8.2f}')
empty = [n for i, n in enumerate(names) if not (assign_i32 == i).any()]
lines += ['', 'EMPTY BANDS: ' + (', '.join(empty) if empty else 'NONE — every joint owns vertices')]
unassigned = int((assign_i32 < 0).sum())
lines.append(f'unassigned verts: {unassigned}')
open(REPORT, 'w').write('\n'.join(lines))
print('\n'.join(lines))
print(f'\nwritten: {PACK_OUT}\n         {MJCF_OUT}\n         {ROM_OUT}\n         {REPORT}')
