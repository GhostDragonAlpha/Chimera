"""gap_track.py -- track the 8 pad gaps per tick from FULL q-dumps (host/cpp),
using the frames recursion (post-fix semantics). Locates the CoP-flip and
touch-band crossing differences between the implementations.
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
body_fp      = mdl[OF['body_fp']:OF['body_fp']+224].reshape(14, 4, 4)
body_fc      = mdl[OF['body_fc']:OF['body_fc']+224].reshape(14, 4, 4)
pt_body = mdi[OI['pt_body']:OI['pt_body']+8]
pt_local = mdl[OF['pt_local']:OF['pt_local']+24].reshape(8, 3)
pt_radius = mdl[OF['pt_radius']:OF['pt_radius']+8]
plane_y = mdl[OF['pt_local']+0]  # placeholder, overwritten below
cst = np.loadtxt('host_shim/cst.txt')
plane_y = cst[0]

def rot_axis(axis, ang):
    c,s = np.cos(ang), np.sin(ang); t=1-c; x,y,z=axis
    R = np.eye(4)
    R[0,0]=c+x*x*t; R[0,1]=x*y*t-z*s; R[0,2]=x*z*t+y*s
    R[1,0]=y*x*t+z*s; R[1,1]=c+y*y*t; R[1,2]=y*z*t-x*s
    R[2,0]=z*x*t-y*s; R[2,1]=z*y*t+x*s; R[2,2]=c+z*z*t
    return R

def gaps(q):
    fr = np.zeros((14,4,4)); fr[0] = np.eye(4)
    for b in range(1,14):
        pfp = fr[body_parent[b]] @ body_fp[b]
        motion = np.eye(4); tv = np.zeros(3)
        for ai in range(body_axoff[b], body_axoff[b+1]):
            slot = ax_slot[ai]
            ang = ax_const[ai] + (ax_slope[ai]*q[slot] if slot >= 0 else 0.0)
            if ax_rot[ai] != 0: motion = motion @ rot_axis(ax_axis[ai], ang)
            else: tv = tv + ax_axis[ai]*ang
        m4 = motion.copy(); m4[:3,3] = tv
        fr[b] = pfp @ m4 @ body_fc[b]
    out = []
    for k in range(8):
        p = (fr[pt_body[k]] @ np.append(pt_local[k], 1.0))[:3]
        out.append(p[1] + pt_radius[k] - plane_y)
    return np.array(out)

def load(path):
    rows = {}
    for line in open(path):
        if not line.startswith('FULL'):
            continue
        kv = dict(p.split('=') for p in line.split()[1:])
        t = int(kv['t'])
        rows[t] = np.array([float(v) for k, v in kv.items() if k != 't'])
    return rows

hl = load('hl_base.txt'); cp = load('cp_base.txt')
names = ['Lheel','LMPf','Rheel','RMPf','LFheel','LFMP','RFheel','RFMP']
print('tick  L_heel  L_MP   (host) | L_heel  L_MP   (cpp)  || R fore heel/MP host | cpp')
for t in range(1, 9):
    ct = t - 1
    gh = gaps(hl[t][:18]); gc = gaps(cp[ct][:18])
    print(f'{t:3d}  {gh[0]:+.6f} {gh[1]:+.6f} | {gc[0]:+.6f} {gc[1]:+.6f}  || {gh[4]:+.7f} {gh[5]:+.7f} | {gc[4]:+.7f} {gc[5]:+.7f}')
