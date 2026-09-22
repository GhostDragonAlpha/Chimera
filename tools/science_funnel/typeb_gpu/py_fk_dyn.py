"""py_fk_dyn.py -- full-dynamics replica (C++ semantics: dt/ddt seed ZERO):
frames + frd + frdd recursion, M/gv/bv, acc = M^-1 (gv - bv - damping*v),
dumped at the walk-reset (capture) pose for comparison with the kernels' rate.
Trailer Agent: GLM 5.3."""
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
drive_damping = mdl[OF['drive_damping']:OF['drive_damping']+12]
grav = np.array([0.0, -9.80665, 0.0])

q = np.loadtxt('host_shim/q.txt')
v = np.loadtxt('host_shim/v.txt')

def rot_axis(axis, ang):
    c,s = np.cos(ang), np.sin(ang); t=1-c; x,y,z=axis
    R = np.eye(4)
    R[0,0]=c+x*x*t; R[0,1]=x*y*t-z*s; R[0,2]=x*z*t+y*s
    R[1,0]=y*x*t+z*s; R[1,1]=c+y*y*t; R[1,2]=y*z*t-x*s
    R[2,0]=z*x*t-y*s; R[2,1]=z*y*t+x*s; R[2,2]=c+z*z*t
    return R
def skew(axis):
    S = np.zeros((4,4)); x,y,z = axis
    S[0,1]=-z; S[0,2]=y; S[1,0]=z; S[1,2]=-x; S[2,0]=-x; S[2,1]=y
    return S
def apply_point(T, p):
    return (T @ np.append(p, 1.0))[:3]
def axial(M4):
    return np.array([M4[2,1]-M4[1,2], M4[0,2]-M4[2,0], M4[1,0]-M4[0,1]]) * 0.5

fr = np.zeros((14,4,4)); fr[0] = np.eye(4)
frd = np.zeros((14,4,4)); frd[0] = np.eye(4)
frdd = np.zeros((14,4,4)); frdd[0] = np.eye(4)
axw = np.zeros((18,3)); axpiv = np.zeros((18,3)); axdir = np.zeros((18,3))

for b in range(1,14):
    par = body_parent[b]
    pfp = fr[par] @ body_fp[b]
    pfpd = frd[par] @ body_fp[b]
    pfpedd = frdd[par] @ body_fp[b]
    motion = np.eye(4); motion_dt = np.zeros((4,4)); motion_ddt = np.zeros((4,4))
    tv = np.zeros(3); vv = np.zeros(3)
    for ai in range(body_axoff[b], body_axoff[b+1]):
        slot = ax_slot[ai]
        ang = ax_const[ai] + (ax_slope[ai]*q[slot] if slot >= 0 else 0.0)
        rate = ax_slope[ai]*v[slot] if slot >= 0 else 0.0
        axis = ax_axis[ai]
        if ax_rot[ai] != 0:
            one = rot_axis(axis, ang)
            dr = skew(axis) @ one
            one_dt = dr * rate
            one_ddt = (skew(axis) @ dr) * rate * rate
            motion = motion @ one
            motion_dt = motion_dt @ one + motion @ one_dt
            motion_ddt = motion_ddt @ one + 2.0*(motion_dt @ one_dt) + motion @ one_ddt
            # careful: the C++ product recursion composes with PRE-update values;
            # replicate exactly:
        else:
            tv = tv + axis*ang; vv = vv + axis*rate
    # C++ composes with PRE-update values; redo strictly:
    # (recompute with temporaries)
    motion = np.eye(4); motion_dt = np.zeros((4,4)); motion_ddt = np.zeros((4,4))
    tv = np.zeros(3); vv = np.zeros(3)
    for ai in range(body_axoff[b], body_axoff[b+1]):
        slot = ax_slot[ai]
        ang = ax_const[ai] + (ax_slope[ai]*q[slot] if slot >= 0 else 0.0)
        rate = ax_slope[ai]*v[slot] if slot >= 0 else 0.0
        axis = ax_axis[ai]
        if ax_rot[ai] != 0:
            one = rot_axis(axis, ang)
            dr = skew(axis) @ one
            one_dt = dr * rate
            one_ddt = (skew(axis) @ dr) * rate * rate
            motion_new = motion @ one
            motion_dt_new = motion_dt @ one + motion @ one_dt
            motion_ddt_new = motion_ddt @ one + 2.0*(motion_dt @ one_dt) + motion @ one_ddt
            motion, motion_dt, motion_ddt = motion_new, motion_dt_new, motion_ddt_new
        else:
            tv = tv + axis*ang; vv = vv + axis*rate
    m4 = motion.copy(); m4[:3,3] = tv
    md4 = motion_dt.copy(); md4[:3,3] = vv
    mdd4 = motion_ddt.copy()  # ddt translation stays 0
    fr[b] = pfp @ m4 @ body_fc[b]
    frd[b] = pfpd @ m4 @ body_fc[b] + pfp @ md4 @ body_fc[b]
    frdd[b] = pfpedd @ m4 @ body_fc[b] + pfp @ mdd4 @ body_fc[b]
    for ai in range(body_axoff[b], body_axoff[b+1]):
        w = pfp[:3,:3] @ ax_axis[ai]
        if ax_rot[ai] != 0:
            axw[ai] = w
            axpiv[ai] = pfp[:3,3] + pfp[:3,:3] @ tv
        else:
            axdir[ai] = w

M = np.zeros((18,18)); gv = np.zeros(18); bv = np.zeros(18)
for b in range(1,14):
    m = body_mass[b]
    if m <= 0: continue
    Ib = np.diag(body_inertia[b])
    R = fr[b][:3,:3]; RT = R.T
    Iw = R @ Ib @ RT
    comw = apply_point(fr[b], body_com[b])
    acc_com = apply_point(frdd[b], body_com[b])
    omega = axial(frd[b][:3,:3] @ RT)
    alpha = axial(frdd[b][:3,:3] @ RT + frd[b][:3,:3] @ frd[b][:3,:3].T)
    moment = Iw @ alpha + np.cross(omega, Iw @ omega)
    jv = np.zeros((18,3)); jw = np.zeros((18,3))
    for ai in chain_ax[chain_off[b]:chain_off[b+1]]:
        slot = ax_slot[ai]
        if slot < 0: continue
        if ax_rot[ai] != 0:
            jv[slot] += np.cross(axw[ai], comw - axpiv[ai]); jw[slot] += axw[ai]
        else: jv[slot] += axdir[ai]
    for si in range(18):
        gv[si] += m * jv[si] @ grav
        bv[si] += m * jv[si] @ acc_com + jw[si] @ moment
        for sj in range(18):
            M[si,sj] += m * jv[si] @ jv[sj] + jw[si] @ (Iw @ jw[sj])

rhs = gv - bv
for d in range(12):
    c = mdi[OI['drive_coord']+d]
    rhs[c] += -drive_damping[d]*v[c]
acc = np.linalg.solve(M, rhs)
names = ['bx','by','bz','x','y','z','Lhip','Lknee','Lank','LMP','Rhip','Rknee','Rank','RMP','Fshl','Fell','Fshr','Felr']
print('replica (C++ semantics) acc at capture pose:')
print(' '.join(f'{names[i]}={acc[i]:+.6e}' for i in range(18)))
np.savetxt('host_shim/acc_true_capture.txt', acc, fmt='%.18e')
print()
print('bv:', ' '.join(f'{x:+.4e}' for x in bv))
