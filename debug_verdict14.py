#!/usr/bin/env python
"""Debug VERDICT 14 implementation."""
import sys
sys.path.insert(0, "E:/PythonChimera/.tmp")
sys.path.insert(0, "E:/PythonChimera")

from probe_world_floor import make_state
from LightEngine.kinematic import build_spec, transforms
from LightEngine.kinematic.dynamics import step
from LightEngine.kinematic.muscle_controller import MuscleController
import numpy as np

ANKLES = (63, 71)
SETTLE = 10
D_CM = -2.15

spec = build_spec(1.80, 80.0, mass_model="deleva", floor_links=True)
st = make_state(spec)

mass = st["mass"]
M = float(mass.sum())
com3 = (st["pos"] * mass[:, None]).sum(axis=0) / M
contact_links = {int(r["link_idx"]) for r in st["contact_records"]
                 if r.get("side") != "W"}

# ankle pivot line (world)
piv = np.zeros(3)
for ji in ANKLES:
    ci = int(st["joint_child"][ji])
    R = transforms.to_matrix(st["quat"][ci])
    piv += st["pos"][ci] + R @ st["r_joint_child_local"][ji]
piv /= len(ANKLES)

# direction: forward = from COM toward the support centroid
pts = []
for r in st["contact_records"]:
    if r.get("side") == "W":
        continue
    li = r["link_idx"]
    R = transforms.to_matrix(st["quat"][li])
    pts.append(st["pos"][li] + R @ r["offset_local"])
centroid = np.array(pts)[:, :2].mean(axis=0)
fwd = centroid - com3[:2]
fwd /= np.linalg.norm(fwd)
h = float(com3[2])
d = D_CM / 100.0

# Apply shift
import math
theta = math.atan2(d, h)
direction = np.array([fwd[0], fwd[1], 0.0])
axis = np.cross(np.array([0.0, 0.0, 1.0]), direction)
q_shift = transforms.from_axis_angle(axis, theta)
R_shift = transforms.to_matrix(q_shift)
for li in range(len(st["pos"])):
    if li in contact_links:
        continue
    st["pos"][li] = piv + R_shift @ (st["pos"][li] - piv)
    st["quat"][li] = transforms.multiply(q_shift, st["quat"][li])
for ji in range(len(st["joint_q_rel0"])):
    pa = int(st["joint_parent"][ji])
    cb = int(st["joint_child"][ji])
    q0 = transforms.multiply(transforms.conjugate(st["quat"][pa]),
                             st["quat"][cb])
    if q0[0] < 0.0:
        q0 = -q0
    st["joint_q_rel0"][ji] = q0

st["balance_cop"] = 1
ctrl = MuscleController(spec, st)

# Run a few ticks to debug
for tick in range(5):
    print(f"\n=== TICK {tick} ===")
    
    # Calculate COM and COP before controller
    com3_pre = (st["pos"] * mass[:, None]).sum(axis=0) / M
    comv_pre = (st["lin_vel"] * mass[:, None]).sum(axis=0) / M
    h_pre = float(com3_pre[2])
    
    if h_pre > 1e-6:
        omega = float(np.sqrt(9.80665 / h_pre))
        kd = 1.0
        p_star = com3_pre[:2] + (1.0 + kd) * comv_pre[:2] / omega
        
        cop_num = np.zeros(2, dtype=np.float64)
        cop_den = 0.0
        impulses = st.get("contact_impulses")
        print(f"Contact impulses exist: {impulses is not None}")
        
        if impulses is not None:
            for ci, rec in enumerate(st["contact_records"]):
                if rec.get("side") == "W":
                    continue
                lam_n = float(impulses[ci][2])
                if lam_n <= 0.0:
                    continue
                li = int(rec["link_idx"])
                R = transforms.to_matrix(st["quat"][li])
                p = st["pos"][li] + R @ rec["offset_local"]
                cop_num += p[:2] * lam_n
                cop_den += lam_n
        
        p_now = cop_num / cop_den if cop_den > 1e-9 else com3_pre[:2].copy()
        print(f"p_star: {p_star}")
        print(f"p_now: {p_now}")
        print(f"offset_vec (p_star - p_now): {p_star - p_now}")
    
    ctrl.apply(st)
    st["contact_priority"] = 1 if ctrl.enabled else 0
    step(spec, st, 0.001, n_proj_iters=20)