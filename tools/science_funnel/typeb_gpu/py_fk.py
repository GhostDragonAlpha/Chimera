"""py_fk.py -- python transliteration of fk_eval's frame recursion + gravity
reduction, run on the EXACT shim arrays (host_shim/mdl.txt + mdi.txt), to
localize which axis/pivot/body produces the spurious joint-row gravity at the
defaults pose (where the C++ reference measures EXACTLY zero joint gravity and
a ballistic base). Trailer Agent: GLM 5.3.
"""
import numpy as np

mdl = np.loadtxt('host_shim/mdl.txt')
mdi = np.loadtxt('host_shim/mdi.txt', dtype=int)

def mm(a, b):
    return a @ b

def rot_axis(axis, ang):
    c, s = np.cos(ang), np.sin(ang)
    t = 1.0 - c
    x, y, z = axis
    return np.array([
        [c + x*x*t, x*y*t - z*s, x*z*t + y*s, 0],
        [y*x*t + z*s, c + y*y*t, y*z*t - x*s, 0],
        [z*x*t - y*s, z*y*t + x*s, c + z*z*t, 0],
        [0, 0, 0, 1]], float)

ax_rot   = mdi[mdi[13+0]:mdi[13+0]+18] if False else None
# offsets: OI/OA constants come from walker_numba; hard-read via its module
import sys
sys.path.insert(0, '.')
from walker_numba import OF, OI

ax_rot   = mdi[OI['ax_rot']:OI['ax_rot']+18]
ax_axis  = mdl[OF['ax_axis']:OF['ax_axis']+54].reshape(18, 3)
ax_slot  = mdi[OI['ax_slot']:OI['ax_slot']+18]
ax_slope = mdl[OF['ax_slope']:OF['ax_slope']+18]
ax_const = mdl[OF['ax_const']:OF['ax_const']+18]
body_axoff   = mdi[OI['body_axoff']:OI['body_axoff']+15]
body_parent  = mdi[OI['body_parent']:OI['body_parent']+14]
body_mass    = mdl[OF['body_mass']:OF['body_mass']+14]
body_com     = mdl[OF['body_com']:OF['body_com']+42].reshape(14, 3)
body_fp      = mdl[OF['body_fp']:OF['body_fp']+224].reshape(14, 4, 4)
body_fc      = mdl[OF['body_fc']:OF['body_fc']+224].reshape(14, 4, 4)
chain_off    = mdi[OI['chain_off']:OI['chain_off']+15]
chain_ax     = mdi[OI['chain_ax']:OI['chain_ax']+104]
nbod = 14
grav = np.array([0.0, -9.80665, 0.0])

q = np.loadtxt('host_shim/q.txt') * 0.0   # the DEFAULTS pose = all joint zeros
# base coords 0..5 default to 0 as well (the C++ freefall start); fore entry
# pose is the scene default for coords 14..17 -- read the real defaults:
from walker_env_host import load_spec
spec = load_spec()
q = spec.defaults.copy()

fr = np.zeros((nbod, 4, 4)); fr[0] = np.eye(4)
axw = np.zeros((18, 3)); axpiv = np.zeros((18, 3)); axdir = np.zeros((18, 3))
gv = np.zeros(18)

for b in range(1, nbod):
    par = body_parent[b]
    pfp = fr[par] @ body_fp[b]
    motion = np.eye(4); tv = np.zeros(3)
    for ai in range(body_axoff[b], body_axoff[b+1]):
        slot = ax_slot[ai]
        ang = ax_const[ai]; rate = 0.0
        if slot >= 0:
            ang = ang + ax_slope[ai] * q[slot]
        axis = ax_axis[ai]
        if ax_rot[ai] != 0:
            one = rot_axis(axis, ang)
            motion = motion @ one
        else:
            tv = tv + axis * ang
    m4 = motion.copy(); m4[:3, 3] = 0.0
    m4[:3, 3] = tv
    fr[b] = pfp @ m4 @ body_fc[b]
    for ai in range(body_axoff[b], body_axoff[b+1]):
        axis = ax_axis[ai]
        w = pfp[:3, :3] @ axis
        if ax_rot[ai] != 0:
            axw[ai] = w
            piv = pfp[:3, 3] + pfp[:3, :3] @ tv
            axpiv[ai] = piv
        else:
            axdir[ai] = w

gv_report = []
for b in range(1, nbod):
    m = body_mass[b]
    if m <= 0:
        continue
    comw = (fr[b] @ np.append(body_com[b], 1.0))[:3]
    jv = np.zeros((18, 3))
    for ai in chain_ax[chain_off[b]:chain_off[b+1]]:
        slot = ax_slot[ai]
        if slot < 0:
            continue
        if ax_rot[ai] != 0:
            r = comw - axpiv[ai]
            jv[slot] += np.cross(axw[ai], r)
        else:
            jv[slot] += axdir[ai]
    g = m * (jv @ grav)
    if np.any(np.abs(g) > 1e-12):
        gv_report.append((b, m, comw, g))
    gv += g

print('bodies with nonzero joint-row gravity at defaults pose:')
for b, m, comw, g in gv_report:
    names = ['b0','pelvis?','b2','b3','b4','b5','b6','b7','b8','b9','b10','b11','b12','b13']
    print(f'  body {b} (m={m:.4f}) comw={comw}  gv_contrib={g}')
print('total gv:', ' '.join(f'{v:+.6e}' for v in gv))
print()
print('per-axis world data at defaults pose:')
coord_names = ['bx','by','bz','x','y','z','Lhip','Lknee','Lank','LMP','Rhip','Rknee','Rank','RMP','Fshl','Fell','Fshr','Felr']
for ai in range(18):
    s = ax_slot[ai]
    kind = 'rot' if ax_rot[ai] != 0 else 'prj'
    owner = [b for b in range(1, nbod) if body_axoff[b] <= ai < body_axoff[b+1]]
    sn = coord_names[s] if s >= 0 else 'fix'
    print(f'  ax{ai:2d} slot={sn:5s} {kind} owner={owner} '
          f'w={axw[ai] if ax_rot[ai]!=0 else axdir[ai]} piv={axpiv[ai]}')
