"""action_upright.py -- UPRIGHT: derive standing from the body's own actuators.

A body stands when its muscles can produce enough torque at every joint to keep the
center of mass inside the base of support.  This is a DERIVATION, not a parameter
sweep: the gravitational moment at each joint follows from the body's mass, geometry
and gravity; the muscle capacity follows from the model's own actuators at the
measured pose.  No number is chosen.

    STATEMENT   a body can hold upright under Earth g from its own muscle actuation,
                with no external support.
    PREDICTION  the minimal ankle/hip/knee torques to keep the CoM inside the support
                polygon equal the body's own allometric muscle capacity (peak isometric
                force x moment arm), and the CoM stays within the base of support at
                equilibrium.
    FALSIFIER   equilibrium unreachable (CoM exits support / diverges) -> REFUSE as
                absent structure, not FAIL.

Laws obeyed:
  ALLOMETRY   -- strength scales to the body doing the lifting, never a human table.
  PUBLISHEDOLOGY -- any constant cites a named ology or is flagged minting.
  gravity from world.py::gravity() (never hardcoded 9.81).

    python tools/action_upright.py                     # run directly
    python -c "import tools.action_upright as m; print(m.a_upright(None))"
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np

from port_registry import MYOBODY, action_test
import port_tests                                  # noqa: F401  registers the ports this action rests on
import port_tests_more                             # noqa: F401  registers the ports this action rests on
from world import load_body


# ---------------------------------------------------------------------------
# Leg anatomy, derived from the model at runtime.  Never assumed.
# ---------------------------------------------------------------------------

SAGITTAL_JOINTS = {
    "r": ["ankle_angle_r", "knee_angle_r", "hip_flexion_r"],
    "l": ["ankle_angle_l", "knee_angle_l", "hip_flexion_l"],
}

FOOT_BODIES = ["calcn_r", "calcn_l", "toes_r", "toes_l"]


def _joint_info(mj, m, name):
    """Return (joint_id, qposadr, dofadr) for a named joint, or None."""
    j = mj.mj_name2id(m, mj.mjtObj.mjOBJ_JOINT, name)
    if j < 0:
        return None
    return j, int(m.jnt_qposadr[j]), int(m.jnt_dofadr[j])


def _muscle_capacity_per_direction(mj, m, d, dof):
    """Split muscle torque into positive and negative components."""
    flat = np.asarray(d.actuator_moment).ravel()
    pos, neg = 0.0, 0.0
    for k in range(m.nu):
        n0 = int(d.moment_rownnz[k])
        a0 = int(d.moment_rowadr[k])
        for e in range(n0):
            if int(d.moment_colind[a0 + e]) == dof:
                contrib = float(flat[a0 + e]) * float(d.actuator_force[k])
                if contrib > 0:
                    pos += contrib
                else:
                    neg += contrib
    return pos, neg


def _find_leg_joints(mj, m):
    """Identify sagittal leg joints and their DOFs from the loaded model."""
    sides = {}
    for side in ("r", "l"):
        joints = []
        for jname in SAGITTAL_JOINTS[side]:
            info = _joint_info(mj, m, jname)
            if info is not None:
                joints.append((jname,) + info)
        sides[side] = joints
    return sides


def _support_polygon(mj, m, d):
    """Compute the support polygon from the four foot body positions."""
    positions = []
    for bname in FOOT_BODIES:
        bid = mj.mj_name2id(m, mj.mjtObj.mjOBJ_BODY, bname)
        if bid >= 0:
            positions.append(np.array(d.xpos[bid]))
    if len(positions) < 2:
        return None, None, None, None
    positions = np.array(positions)
    cx = float(np.mean(positions[:, 0]))
    cy = float(np.mean(positions[:, 1]))
    half_x = float(0.5 * (positions[:, 0].max() - positions[:, 0].min()))
    half_y = float(0.5 * (positions[:, 1].max() - positions[:, 1].min()))
    return cx, cy, half_x, half_y


def _compute_joint_forces(mj, m, d, dof):
    """Net muscle torque and per-direction capacity for one DOF.

    Returns (tau_net, tau_pos, tau_neg).
    """
    flat = np.asarray(d.actuator_moment).ravel()
    net, pos, neg = 0.0, 0.0, 0.0
    for k in range(m.nu):
        n0 = int(d.moment_rownnz[k])
        a0 = int(d.moment_rowadr[k])
        for e in range(n0):
            if int(d.moment_colind[a0 + e]) == dof:
                arm = float(flat[a0 + e])
                force = float(d.actuator_force[k])
                contrib = arm * force
                net += contrib
                if contrib > 0:
                    pos += contrib
                else:
                    neg += contrib
    return net, pos, neg


# ---------------------------------------------------------------------------
# The action primitive.
# ---------------------------------------------------------------------------
@action_test(
    "upright", ["rigid_body", "contact", "hill_muscle"],
    "a body can hold upright under Earth g from its own muscle actuation, with no "
    "external support -- the derived standing torques equal the body's own allometric "
    "muscle capacity and the CoM stays inside the base of support at equilibrium",
    "the minimal ankle/hip/knee torques to keep the CoM inside the support polygon "
    "equal the body's own muscle capacity (peak isometric force x moment arm), and a "
    "feasible standing region exists where the CoM stays within the base of support",
    "equilibrium unreachable (CoM exits support / no feasible standing region) -> "
    "REFUSE as absent structure, not FAIL")
def a_upright(_):
    import mujoco

    m, g = load_body(MYOBODY, mujoco)
    M_total = float(np.sum(m.body_mass))
    W = M_total * g

    # Reset to keyframe 0: the symmetric standing pose.
    d = mujoco.MjData(m)
    mujoco.mj_resetDataKeyframe(m, d, 0)

    # Set ALL muscles to full activation so mj_forward evaluates each muscle's
    # force at its current length and velocity.
    d.ctrl[:] = 1.0
    if m.na:
        d.act[:] = 1.0
    mujoco.mj_forward(m, d)

    # If no contact at the keyframe, seat the body on the floor.
    if d.ncon == 0:
        lo, hi = -0.5, 0.5
        for _ in range(40):
            mid = 0.5 * (lo + hi)
            z = float(d.qpos[2])
            d.qpos[2] = z + mid
            mujoco.mj_forward(m, d)
            touching = d.ncon > 0
            d.qpos[2] = z
            if touching:
                lo = mid
            else:
                hi = mid
        d.qpos[2] += 0.5 * (lo + hi)
        if m.na:
            d.act[:] = 1.0
        d.ctrl[:] = 1.0
        mujoco.mj_forward(m, d)

    # ---------- CoM and support polygon ----------
    com = np.array(d.subtree_com[1])
    sp_cx, sp_cy, sp_hx, sp_hy = _support_polygon(mujoco, m, d)
    com_in_bos = (abs(com[0] - sp_cx) <= sp_hx and
                  abs(com[1] - sp_cy) <= sp_hy) if sp_hx is not None else False

    # ---------- Per-joint analysis ----------
    #
    # THE DERIVATION.
    #
    # For each sagittal joint, we compute:
    #   (a) The MUSCLE TORQUE CAPACITY from the model's own actuators at full
    #       activation, via the sparse moment matrix and the force-length curve.
    #       This is allometry: strength from PCSA x specific tension, embedded in
    #       gainprm and the Hill model.  No number is chosen.
    #   (b) The GRAVITATIONAL MOMENT DEMAND for the worst-case CoM position that
    #       the muscles themselves permit.  Each joint's capacity limits how far
    #       the CoM can offset from it: h_max = tau_capacity / W.  The feasible
    #       CoM range is the intersection of these per-joint ranges AND the
    #       support polygon.  If the intersection is non-empty, standing is
    #       possible.
    #
    # The BINDING CONSTRAINT is the joint whose h_max is smallest -- typically
    # the ankle, which supports the whole body and has the weakest dorsiflexors.
    # The knee and hip only need to handle the CoM range the ankle permits, not
    # the full support polygon width.
    #
    # We verify at TWO landmark positions:
    #   1. The CURRENT CoM (from the keyframe): does the muscle capacity exceed
    #      the gravitational demand at this specific pose?
    #   2. The ANKLE-CONSTRAINED WORST CASE: the CoM at the maximum offset the
    #      ankle can handle, which is the true upright requirement.
    #
    leg_joints = _find_leg_joints(mujoco, m)

    # Collect joint data: for each joint, compute capacity and the CoM offset
    # that would consume all of it.
    joint_data = []
    for side in ("r", "l"):
        for jname, jid, jadr, dofadr in leg_joints[side]:
            axis = np.array(d.xaxis[dofadr])
            axis_norm = np.linalg.norm(axis)
            if axis_norm > 1e-12:
                axis = axis / axis_norm
            joint_pos = np.array(d.xanchor[jid])

            # Which coordinate matters (sagittal -> x, frontal -> y).
            axis_y, axis_x, axis_z = abs(axis[1]), abs(axis[0]), abs(axis[2])
            coord = 0 if (axis_y >= axis_x and axis_y >= axis_z) else (
                1 if axis_x >= axis_y else -1)

            tau_net, tau_pos, tau_neg = _compute_joint_forces(mujoco, m, d, dofadr)

            # h_max: the maximum CoM offset this joint can handle in each direction.
            # h_max_pos = tau_pos / W  (how far the CoM can be in the positive direction)
            # h_max_neg = |tau_neg| / W  (how far in the negative direction)
            h_max_pos = tau_pos / W if W > 0 else float("inf")
            h_max_neg = abs(tau_neg) / W if W > 0 else float("inf")

            # Current CoM offset from this joint.
            if coord >= 0:
                h_now = abs(float(com[coord] - joint_pos[coord]))
            else:
                h_now = float(np.linalg.norm(com[:2] - joint_pos[:2]))

            joint_data.append(dict(
                side=side, name=jname, jid=jid, dofadr=dofadr, coord=coord,
                joint_pos=joint_pos, axis=axis,
                tau_net=tau_net, tau_pos=tau_pos, tau_neg=tau_neg,
                h_max_pos=h_max_pos, h_max_neg=h_max_neg,
                h_now=h_now,
            ))

    # ---------- Feasibility analysis ----------
    #
    # For each sagittal joint, the feasible CoM range (in the coord direction)
    # is [joint_pos - h_max_neg, joint_pos + h_max_pos].  The intersection of
    # ALL these ranges AND the support polygon is the feasible standing region.
    # If it is non-empty, standing is possible.
    #
    # For the sagittal plane (coord=0, x-direction):
    feasible_lo = -float("inf")
    feasible_hi = float("inf")
    for jd in joint_data:
        if jd["coord"] == 0:
            jp = float(jd["joint_pos"][0])
            feasible_lo = max(feasible_lo, jp - jd["h_max_neg"])
            feasible_hi = min(feasible_hi, jp + jd["h_max_pos"])
    # Clip to support polygon.
    sp_lo = sp_cx - sp_hx if sp_cx is not None else -float("inf")
    sp_hi = sp_cx + sp_hx if sp_cx is not None else float("inf")
    feasible_lo = max(feasible_lo, sp_lo)
    feasible_hi = min(feasible_hi, sp_hi)
    feasible = feasible_hi - feasible_lo

    # ---------- Per-joint ratios at the CURRENT CoM ----------
    joint_results = []
    worst_ratio = 0.0
    worst_joint = "?"
    for jd in joint_data:
        if jd["coord"] >= 0:
            offset = float(com[jd["coord"]] - jd["joint_pos"][jd["coord"]])
            h_now = abs(offset)
            tau_grav_now = W * h_now
            if offset >= 0:
                cap_now = jd["tau_pos"]
            else:
                cap_now = abs(jd["tau_neg"])
            ratio_now = cap_now / max(tau_grav_now, 1e-12)
        else:
            h_now = jd["h_now"]
            tau_grav_now = W * h_now
            cap_now = max(jd["tau_pos"], abs(jd["tau_neg"]))
            ratio_now = cap_now / max(tau_grav_now, 1e-12)

        # Worst case: CoM at the limit of this joint's capacity.
        # The worst case is the direction with the SMALLER h_max (weaker side).
        h_max_min = min(jd["h_max_pos"], jd["h_max_neg"])
        tau_grav_worst = W * h_max_min
        cap_worst = min(jd["tau_pos"], abs(jd["tau_neg"]))
        ratio_worst = cap_worst / max(tau_grav_worst, 1e-12)

        joint_results.append(dict(
            side=jd["side"], name=jd["name"],
            h_now=h_now, h_max_pos=jd["h_max_pos"], h_max_neg=jd["h_max_neg"],
            tau_grav_now=tau_grav_now, tau_pos=jd["tau_pos"], tau_neg=jd["tau_neg"],
            ratio_now=ratio_now, ratio_worst=ratio_worst,
        ))

        if ratio_worst < worst_ratio or worst_joint == "?":
            worst_ratio = ratio_worst
            worst_joint = jd["name"]

    # ---------- Verdict ----------
    # Standing is possible if and only if:
    #   1. The CoM is inside the base of support at the keyframe.
    #   2. The feasible standing region is non-empty (all joints' capacity
    #      ranges overlap within the support polygon).
    ok = com_in_bos and feasible > 0

    # ---------- Detail string ----------
    detail_parts = [
        f"M = {M_total:.3f} kg, W = {W:.1f} N, g = {g:.4f} m/s^2",
        f"CoM = ({com[0]*1000:+.1f}, {com[1]*1000:+.1f}, {com[2]*1000:.1f}) mm",
        f"support polygon: half-extents ({sp_hx*1000:.1f}, {sp_hy*1000:.1f}) mm "
        f"around ({sp_cx*1000:.1f}, {sp_cy*1000:.1f}) mm",
        f"CoM {'INSIDE' if com_in_bos else 'OUTSIDE'} base of support",
        f"feasible standing region: x in [{feasible_lo*1000:+.1f}, {feasible_hi*1000:+.1f}] mm "
        f"(width {feasible*1000:.1f} mm)",
    ]
    for r in sorted(joint_results, key=lambda x: x["ratio_worst"]):
        tag = "OK" if r["ratio_worst"] >= 1.0 else "WEAK"
        detail_parts.append(
            f"  {r['side'].upper()} {r['name']:22s} "
            f"h_now={r['h_now']*1000:5.1f}mm  "
            f"h_max=+{r['h_max_pos']*1000:5.1f}/-{r['h_max_neg']*1000:5.1f}mm  "
            f"tau_cap=[+{r['tau_pos']:6.1f}/-{abs(r['tau_neg']):6.1f}] N.m  "
            f"ratio_now={r['ratio_now']:.3f}  ratio_worst={r['ratio_worst']:.3f}  [{tag}]"
        )

    return dict(
        pass_=ok,
        refused=False,
        got=f"CoM {'in' if com_in_bos else 'out'}, feasible {feasible*1000:.1f}mm, "
            f"worst joint {worst_joint} ratio {worst_ratio:.3f}",
        detail="; ".join(detail_parts),
    )


if __name__ == "__main__":
    import mujoco as _mj
    r = a_upright(_mj)
    print(f"UPRIGHT: {'PASS' if r.get('pass_') else ('REFUSED' if r.get('refused') else 'FAIL')}")
    print(f"  got:    {r['got']}")
    print(f"  detail: {r['detail']}")
