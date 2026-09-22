"""py_fk_full.py -- build M and gv at the defaults pose with the kernels'
math (replica), dump for the C++ inverse probe. Trailer Agent: GLM 5.3."""
import numpy as np, sys
sys.path.insert(0, '.')
mdl = np.loadtxt('host_shim/mdl.txt'); mdi = np.loadtxt('host_shim/mdi.txt', dtype=int)
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
body_inertia = mdl[OF['body_inertia']:OF['body_inertia']+42].reshape(14, 3)
body_fp      = mdl[OF['body_fp']:OF['body_fp']+224].reshape(14, 4, 4)
body_fc      = mdl[OF['body_fc']:OF['body_fc']+224].reshape(14, 4, 4)
chain_off    = mdi[OI['chain_off']:OI['chain_off']+15]
chain_ax     = mdi[OI['chain_ax']:OI['chain_ax']+104]
grav = np.array([0.0, -9.80665, 0.0])
from walker_env_host import load_spec
q = load_spec().defaults.copy()

fr = np.zeros((14,4,4)); fr[0] = np.eye(4)
axw = np.zeros((18,3)); axpiv = np.zeros((18,3)); axdir = np.zeros((18,3))
def rot_axis(axis, ang):
    c,s = np.cos(ang), np.sin(ang); t=1-c; x,y,z=axis
    return np.array([[c+x*x*t,x*y*t-z*s,x*z*t+y*s,0],[y*x*t+z*s,c+y*y*t,y*z*t-x*s,0],[z*x*t-y*s,z*y*t+x*s,c+z*z*t,0],[0,0,0,1.0]])
for b in range(1,14):
    par = body_parent[b]; pfp = fr[par] @ body_fp[b]
    motion = np.eye(4); tv = np.zeros(3)
    for ai in range(body_axoff[b], body_axoff[b+1]):
        slot = ax_slot[ai]; ang = ax_const[ai]
        if slot >= 0: ang = ang + ax_slope[ai]*q[slot]
        if ax_rot[ai] != 0: motion = motion @ rot_axis(ax_axis[ai], ang)
        else: tv = tv + ax_axis[ai]*ang
    m4 = motion.copy(); m4[:3,3] = tv
    fr[b] = pfp @ m4 @ body_fc[b]
    for ai in range(body_axoff[b], body_axoff[b+1]):
        w = pfp[:3,:3] @ ax_axis[ai]
        if ax_rot[ai] != 0:
            axw[ai] = w; axpiv[ai] = pfp[:3,3] + pfp[:3,:3] @ tv
        else: axdir[ai] = w

M = np.zeros((18,18)); gv = np.zeros(18)
for b in range(1,14):
    m = body_mass[b]
    if m <= 0: continue
    Ib = np.diag(body_inertia[b])
    Iw = fr[b][:3,:3] @ Ib @ fr[b][:3,:3].T
    comw = (fr[b] @ np.append(body_com[b],1.0))[:3]
    jv = np.zeros((18,3)); jw = np.zeros((18,3))
    for ai in chain_ax[chain_off[b]:chain_off[b+1]]:
        slot = ax_slot[ai]
        if slot < 0: continue
        if ax_rot[ai] != 0:
            jv[slot] += np.cross(axw[ai], comw - axpiv[ai]); jw[slot] += axw[ai]
        else: jv[slot] += axdir[ai]
    for si in range(18):
        gv[si] += m * jv[si] @ grav
        for sj in range(18):
            M[si,sj] += m * jv[si] @ jv[sj] + jw[si] @ (Iw @ jw[sj])

a = np.linalg.solve(M, gv)
np.savetxt('host_shim/M_probe.txt', M, fmt='%.18e')
np.savetxt('host_shim/gv_probe.txt', gv, fmt='%.18e')
np.savetxt('host_shim/a_true.txt', a, fmt='%.18e')
print('dumped. a[4]=%.17g a[6]=%.17g' % (a[4], a[6]))
