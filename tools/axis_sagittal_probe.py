"""axis_sagittal_probe.py — measure the paired hinge axes before the sagittal law ships. (2026-09-04)

The wing-splay diagnosis (dyad verdict round 1 + Rodrigues arithmetic): the
referee's n = u x v axis derivation is DEGENERATE for near-collinear bones —
the derived axis inherits the rest pose's sideways splay. The candidate cure
is the para-sagittal law: shared +/-x-hat (the spine chain's own axes), sign
per joint from the CLOSING TEST: +theta must swing the distal bone TOWARD
its parent bone (flexion closes the interior angle — a derivation, not a pick).

This probe replicates the factory's exact topology (including the hand/foot
mesh tips) and answers, per joint:
  bend_deg      rest bend between parent and distal bone (0 = straight limb)
  ang_to_x      angle between the OLD derived axis and +/-x-hat
  n_alignment   |old_axis . (u x v)| — 1.0 = old axis was the true plane normal
  old_sign      sign of closing under the OLD axis  (+1 closes, -1 opens)
  sag_sign      sign of closing under SAGITTAL x-hat (sign the law would ship)
  match         do old and sagittal agree? A mismatch on a WELL-BENT joint
                (> 30 deg bend) is the falsifier that shrinks the law's scope.

Falsifiers named before the run: (a) old_sign != sag_sign on a well-bent
joint — the sagittal law contradicts the measured plane there; (b) ambiguous
closing test, |c| tiny relative to scale — the sign is not derivable; (c)
sagittal axis parallel to the bone (|x . v| near 1) — hinge cannot fold.

Run: python tools/axis_sagittal_probe.py
"""
import struct
import numpy as np

PACK = 'Saved/meshes/monkey_joints.bin'

b = open(PACK, 'rb').read()
nv, nj, nl = struct.unpack('<III', b[4:16])
p = 16
names = [n for n in b[p:p + nl].decode().split('\x00') if n][:nj]; p += nl
p += nv * 8                                   # assign + w
J = np.frombuffer(b, np.float32, nj * 3, p).reshape(nj, 3).astype(np.float64); p += nj * 12
AX = np.frombuffer(b, np.float32, nj * 3, p).reshape(nj, 3).astype(np.float64)
ix = {n: i for i, n in enumerate(names)}

# the factory's own topology (tools/rig_factory_fit.py): the tips are MEASURED
# from the engine's canonical vertex list, not constants — replicate verbatim.
BLOB = 'ChimeraEngine/engine/build/Release/session_snapshot/mesh_bin.blob'
raw = open(BLOB, 'rb').read()
N, _ = struct.unpack('<II', raw[:8])
V = np.frombuffer(raw, np.float32, N * 9, 24).reshape(-1, 9)[:, :3].astype(np.float64)
arm_L = np.linalg.norm(V - J[names.index('wrist_L')], axis=1)
beyond_wrist = np.where((np.linalg.norm(V - J[names.index('elbow_L')], axis=1) < arm_L) & (arm_L < 1.2))[0]
tip_ids = beyond_wrist[np.argsort(-arm_L[beyond_wrist])][:30]
hand_tip = V[tip_ids].mean(axis=0)
leg_L = np.linalg.norm(V - J[names.index('ankle_L')], axis=1)
beyond_ankle = np.where((np.linalg.norm(V - J[names.index('knee_L')], axis=1) < leg_L) & (leg_L < 1.0))[0]
tip_ids = beyond_ankle[np.argsort(-leg_L[beyond_ankle])][:30]
foot_tip = V[tip_ids].mean(axis=0)
Jd = {n: J[i] for i, n in enumerate(names)}   # the pack's J IS the factory's post-law dict
print(f"mesh N={N}, hand_tip={np.round(hand_tip,3)}, foot_tip={np.round(foot_tip,3)}")

PARENT = {'shoulder': 'spine_upper', 'elbow': 'shoulder', 'wrist': 'elbow',
          'hip': 'spine_lower', 'knee': 'hip', 'ankle': 'knee'}
CHILD = {'shoulder': 'elbow', 'elbow': 'wrist', 'hip': 'knee', 'knee': 'ankle'}
TIP = {'wrist': hand_tip, 'ankle': foot_tip}

print(f"{'joint':12s} {'bend_deg':>8s} {'ang_to_x':>8s} {'n_align':>8s} "
      f"{'old_sign':>8s} {'sag_sign':>8s} {'match':>8s}  flex_sweep_plane(y-z)")
rows = []
for base in ('shoulder', 'elbow', 'wrist', 'hip', 'knee', 'ankle'):
    side = 'L'
    jk = base + '_' + side
    pk = PARENT[base] + ('_' + side if PARENT[base] + '_' + side in ix else '')
    P = Jd[pk]
    if base in CHILD:
        C = Jd[CHILD[base] + '_' + side]
    else:
        C = TIP[base]  # the factory uses hand_tip_L directly for wrist_L
    u = Jd[jk] - P
    v = C - Jd[jk]
    u /= np.linalg.norm(u)
    v /= np.linalg.norm(v)
    bend = np.degrees(np.arcsin(np.clip(np.linalg.norm(np.cross(u, v)), 0.0, 1.0)))
    old = AX[ix[jk]]
    old = old / np.linalg.norm(old)
    ang_x = np.degrees(np.arccos(min(1.0, abs(old[0]))))
    n_true = np.cross(u, v)
    nt = np.linalg.norm(n_true)
    n_align = abs(np.dot(old, n_true)) if nt > 1e-9 else float('nan')
    # closing test: does +theta about the axis swing v toward u?
    th = np.radians(45.0)
    def swing(vdir, ax):
        return (vdir * np.cos(th) + np.cross(ax, vdir) * np.sin(th)
                + ax * np.dot(ax, vdir) * (1 - np.cos(th)))
    old_sign = 1 if np.dot(swing(v, old), u) > 0 else -1
    sag = np.array([1.0, 0.0, 0.0])
    sw = swing(v, sag)
    c_sag = np.dot(sw, u)
    sag_sign = 1 if c_sag > 0 else -1
    amb = abs(c_sag)  # closing magnitude at 45 deg; near 0 = ambiguous sign
    sag_foldable = abs(sag[0] * v[0] + sag[1] * v[1] + sag[2] * v[2]) < 0.95
    v1 = swing(v, sag * sag_sign)
    plane_yz = abs(v1[0] - v[0]) < 1e-9
    match = 'MISMATCH' if old_sign != sag_sign else 'match'
    rows.append((jk, bend, ang_x, n_align, old_sign, sag_sign, match, amb, sag_foldable, plane_yz))
    print(f"{jk:12s} {bend:8.2f} {ang_x:8.2f} {n_align:8.4f} "
          f"{old_sign:8.0f} {sag_sign:8.0f} {match:>8s}  "
          f"c45={amb:5.2f} foldable={sag_foldable} yz-preserving={plane_yz}")

print()
well_bent = [r for r in rows if r[1] > 30.0]
fals_a = [r for r in well_bent if r[4] != r[5]]
fals_b = [r for r in rows if r[7] < 0.05]
fals_c = [r for r in rows if not r[8]]
print(f"falsifier (a) sign contradiction on well-bent joints: {[r[0] for r in fals_a] or 'NONE'}")
print(f"falsifier (b) ambiguous closing sign:                 {[r[0] for r in fals_b] or 'NONE'}")
print(f"falsifier (c) sagittal axis cannot fold the bone:     {[r[0] for r in fals_c] or 'NONE'}")
