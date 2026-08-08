"""
theStandingHuman v2-rigid: the muscle actuator table (Lane M1).

RULE 0 -- STATEMENT: the frame stands when and only when derived muscle
torques close the free dofs of the kinematic tree; standing is controlled
actuation, not geometry (the K3 battery measured the unactuated frame
crumpling from t=0, ropes or no ropes).  PREDICTION: with this table driving
a PD loop at derived gains, the v2 battery passes STAND/LIMIT/CAPTURE/FRAME/
LIGAMENT in the MAIN run and the CONTROL (muscles relaxed at tick 1200) falls
with extra COM drop > L_leg*sin(12 deg).  FALSIFIERS: the six meters of
LightEngine/demo_kinematic.py, unchanged.

This module holds NO controller.  It turns the spec + a bind-pose state into
one actuator record per free rotational dof, with every number either
ANATOMY-DATUM (muscle physiology) or DERIVED (gains from the body's own
inverted-pendulum dynamics).  Nothing is tuned.

Muscle physiology (ANATOMY-DATUM):
  - Specific tension 30 N/cm^2: the textbook isometric plateau of vertebrate
    skeletal muscle (measured range 20-40 N/cm^2 across species and methods).
  - PCSA (physiological cross-sectional area, cm^2) per joint group: the sum
    of the agonist group crossing that joint for the 80 kg / 1.80 m reference
    body (Winter's anthropometric tables and the Visible Human dissections
    are the canonical sources; values below are group sums, not per-muscle).
  - Moment arm (m) per joint group: tendon-line to joint-center distance at
    the anatomical position, reference stature 1.80 m.
  PCSA scales with (mass/80 kg)^(2/3) (cross-sectional area scaling);
  moment arms scale with (height/1.80 m) (linear scaling).

Gain derivation (DERIVED -- the law, not a sweep):
  A joint whose subtree COM sits d meters above the joint center is an
  inverted pendulum: gravity supplies a destabilizing stiffness m*g*d (torque
  per radian, small-angle) about the joint center.  The actuator is a PURE
  COUPLE: equal-and-opposite torques on the child and parent links, applied
  at their COMs (net external wrench zero).  Three inertias therefore matter:
    I_red  -- reduced inertia of the pair about the joint axis through the
              JOINT CENTER (child subtree vs parent link, parallel axis
              included): the inertia of the pendulum mode the controller is
              trying to govern.
    I_eff  -- reduced inertia of the pair about the two COM frames,
              1/I_eff = axis.I_c^-1.axis + axis.I_p^-1.axis: the inertia the
              couple actually accelerates in one tick of explicit integration.
  The continuous-time law targets the pendulum mode:
    kp  = 2*m*g*d            (closed-loop natural frequency = open-loop fall
                              rate omega_n = sqrt(m*g*d/I_red); stable iff
                              kp > m*g*d; inertia cancels)
    kd  = 2*zeta*I_red*omega_n,  zeta = 1 (critical, the no-overshoot bound).
  The discrete-time law bounds both gains by what one explicit tick can
  absorb (measured 2026-08-08: kd sized on I_red diverged in <25 ticks on
  links with near-zero long-axis inertia -- humerus I_long 7e-6 kg m^2,
  dt*kd/I_eff ~ 10 >> 1, wmax 2000 rad/s; kp-only rang but stayed bounded):
    kd <= I_eff/dt           (discrete-critical damping: one tick kills a
                              velocity error without oscillation)
    kp <= I_eff*(2/dt)^2     (symplectic-Euler spring stability boundary)
  Final gains: kp = min(2*m*g*d, I_eff*(2/dt)^2),
               kd = min(2*I_red*omega_n, I_eff/dt).  Both bounds are derived
  from the integration scheme at the build-time tick dt; nothing is tuned.
  For hanging subtrees (COM below the joint) gravity already restores; the
  same magnitude law is used so the pose is held at the same rate.  When the
  subtree COM is level with the joint center (d ~ 0) the smallest resolved
  displacement is the joint capture band d_eq, which is used as the floor.
  When the parent link is massless (a rig base) I_red = I_c and
  1/I_p = 0 by convention.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from LightEngine.kinematic import transforms
from LightEngine.kinematic.skeleton_spec import D_EQ_LU

GRAVITY = 9.80665  # ANATOMY-DATUM: standard gravity (matches dynamics.py).

# ANATOMY-DATUM: isometric specific tension of vertebrate skeletal muscle.
SPECIFIC_TENSION_N_PER_CM2 = 30.0

# ANATOMY-DATUM: reference body for the physiology tables below.
REF_HEIGHT_M = 1.80
REF_MASS_KG = 80.0

# ANATOMY-DATUM: per joint group (agonist group sums, 80 kg / 1.80 m body):
#   group key -> (pcsa_cm2, moment_arm_m).
# Sources by group: ankle = soleus+gastrocnemius; knee = quadriceps/hamstrings;
# hip = gluteals+iliopsoas+adductors; spine = erector spinae+abdominals per
# level (lumbar/thoracic/cervical scaling); shoulder = deltoid+rotator cuff;
# elbow = biceps+brachialis+triceps; wrist/hand = forearm flexor+extensor mass;
# ribs/sternum/clavicle = intercostals+pectoral sheet; scapula = trapezius+
# rhomboids+serratus; SI = pelvic floor+deep ligamentous cuff; forefoot/MTP =
# intrinsic+long toe flexors.
_GROUP_PHYSIOLOGY: dict[str, tuple[float, float]] = {
    "tarsals":     (50.0, 0.050),   # ankle plantar/dorsiflexion
    "tibia":       (90.0, 0.040),   # knee (extensors+flexors)
    "fibula":      (90.0, 0.040),   # shares the knee line
    "patella":     (90.0, 0.040),   # rides the knee
    "femur":       (110.0, 0.060),  # hip
    "pelvis":      (30.0, 0.050),   # SI cuff (spec calls it saddle)
    "vertebra_L":  (40.0, 0.045),   # lumbar
    "vertebra_T":  (25.0, 0.035),   # thoracic
    "vertebra_C":  (10.0, 0.030),   # cervical (C2-C7)
    "vertebra_C1": (6.0, 0.030),    # atlanto-axial (ball-cup)
    "skull":       (6.0, 0.030),    # head balance (unused: suture)
    "rib":         (3.0, 0.020),    # intercostals per rib
    "sternum":     (5.0, 0.020),    # manubrium sheet
    "clavicle":    (8.0, 0.030),    # sternoclavicular
    "scapula":     (15.0, 0.040),   # scapulothoracic musculature
    "humerus":     (25.0, 0.040),   # glenohumeral
    "radius_ulna": (15.0, 0.030),   # elbow
    "hand":        (8.0, 0.020),    # wrist
    "metatarsals": (5.0, 0.015),    # tarsometatarsal
    "forefoot":    (6.0, 0.020),    # MTP (toe flexors)
}

# DERIVED-CONTROL: the two law constants of the gain derivation above.
_CLOSED_LOOP_OVER_FALL_RATE = 2.0   # kp = 2 * I * omega_n^2
_ZETA = 1.0                         # critical damping (no-overshoot boundary)


def _group_key(child_link: str) -> str | None:
    """Map a child link name to its physiology group key."""
    if child_link.startswith("vertebra_C1"):
        return "vertebra_C1"
    if child_link.startswith("vertebra_L"):
        return "vertebra_L"
    if child_link.startswith("vertebra_T"):
        return "vertebra_T"
    if child_link.startswith("vertebra_C"):
        return "vertebra_C"
    if child_link.startswith("rib_"):
        return "rib"
    for prefix in ("tarsals", "tibia", "fibula", "patella", "femur", "pelvis",
                   "skull", "sternum", "clavicle", "scapula", "humerus",
                   "radius_ulna", "hand", "metatarsals", "forefoot"):
        if child_link.startswith(prefix):
            return prefix
    return None


def _subtree_links(joints: dict[str, dict[str, Any]], root_child: str) -> list[str]:
    """Return root_child plus every link descended from it (child->parent map)."""
    children: dict[str, list[str]] = {}
    for j in joints.values():
        children.setdefault(j["parent_link"], []).append(j["child_link"])
    out: list[str] = []
    stack = [root_child]
    while stack:
        name = stack.pop()
        out.append(name)
        stack.extend(children.get(name, ()))
    return out


def build_actuator_table(spec: dict[str, Any], state: dict[str, Any],
                         physiology: dict[str, tuple[float, float]] | None = None,
                         dt: float = 1e-3
                         ) -> list[dict[str, Any]]:
    """Return one actuator record per free rotational dof, in joint order.

    Each record:
      joint / joint_index -- name and row in the state's joint arrays.
      parent_idx / child_idx -- rows in the state's link arrays.
      axis_local_parent -- the free axis in the PARENT local frame (unit).
      dof_index -- which free axis of the joint this is.
      torque_limit_Nm -- specific_tension x PCSA x moment arm (physiology cap).
      moment_arm_m -- the group moment arm, scaled to this body.
      kp / kd -- DERIVED PD gains (module docstring: the law, not a sweep).
      subtree_mass / subtree_inertia / omega_n -- the derivation's intermediates.

    `physiology` lets test rigs register group entries for their non-anatomical
    link names; the real skeleton never needs it (the anatomy table is complete).
    """
    physio = dict(_GROUP_PHYSIOLOGY)
    if physiology:
        physio.update(physiology)
    links = spec["links"]
    joints = spec["joints"]
    lam = float(spec.get("lam", 1.0))
    # Test rigs (no body scaling) get a plain 1 mm floor; the real skeleton
    # uses its capture band d_eq.
    d_eq_m = lam * D_EQ_LU if "height_m" in spec else 1e-3
    height_m = float(spec.get("height_m", REF_HEIGHT_M))
    mass_kg = float(spec.get("mass_kg", REF_MASS_KG))
    arm_scale = height_m / REF_HEIGHT_M
    pcsa_scale = (mass_kg / REF_MASS_KG) ** (2.0 / 3.0)

    pos = state["pos"]
    quat = state["quat"]
    mass = state["mass"]
    inertia_diag = state["inertia_diag_local"]

    table: list[dict[str, Any]] = []
    for ji, joint_name in enumerate(state["joint_names"]):
        j = joints[joint_name]
        dof = int(state["joint_dof"][ji])
        if dof <= 0:
            continue
        parent_name = j["parent_link"]
        child_name = j["child_link"]
        parent_idx = int(state["joint_parent"][ji])
        child_idx = int(state["joint_child"][ji])

        # Free axes in the parent local frame.  Hinge/saddle carry them in the
        # spec; ball-cup is free about the parent's full basis.
        if dof == 3:
            pl = links[parent_name]
            axes = [np.asarray(pl["basis_x"], dtype=np.float64).reshape(3),
                    np.asarray(pl["basis_y"], dtype=np.float64).reshape(3),
                    np.asarray(pl["basis_z"], dtype=np.float64).reshape(3)]
        else:
            axes = [np.asarray(ax, dtype=np.float64).reshape(3) for ax in j["axes"]]

        key = _group_key(child_name)
        if key is None and physiology and child_name in physiology:
            key = child_name
        if key is None:
            raise RuntimeError(f"No muscle physiology group for link {child_name!r}")
        pcsa_ref, arm_ref = physio[key]
        arm_m = arm_ref * arm_scale
        torque_limit = SPECIFIC_TENSION_N_PER_CM2 * (pcsa_ref * pcsa_scale) * arm_m

        # The SUPPORTED side of the joint (DERIVED from the tree and the
        # contact set): cutting the joint splits the tree into the child's
        # component and the parent's component; the side with FEWER foot
        # contacts cannot stand on its own and must be held by the muscle.
        # Ties (both sides grounded, or neither) go to the heavier side: the
        # light grounded side stands, the heavy side must be actively held.
        # (Measured 2026-08-08: sizing gains on the child subtree alone left
        # the knee holding the 8 kg shank while the 60 kg trunk buckled it --
        # the load that matters is the side the joint holds UP, not the side
        # the tree hangs DOWN.)
        subtree = _subtree_links(joints, child_name)
        idxs = [state["name_to_idx"][n] for n in subtree]
        idx_set = set(idxs)
        comp_p = [i for i in range(len(state["link_names"])) if i not in idx_set]
        contact_idxs = {int(r["link_idx"]) for r in state["contact_records"]}
        n_cont_c = sum(1 for i in idxs if i in contact_idxs)
        n_cont_p = sum(1 for i in comp_p if i in contact_idxs)
        m_c = float(sum(mass[i] for i in idxs))
        m_p = float(sum(mass[i] for i in comp_p))
        if n_cont_c < n_cont_p:
            sup_idxs = idxs
        elif n_cont_p < n_cont_c:
            sup_idxs = comp_p
        else:
            sup_idxs = idxs if m_c >= m_p else comp_p
        m_sub = float(sum(mass[i] for i in sup_idxs))

        # Joint center in world at the bind pose (child attachment point).
        R_c = transforms.to_matrix(quat[child_idx])
        jc = pos[child_idx] + R_c @ state["r_joint_child_local"][ji]
        if m_sub > 0.0:
            com_sub = sum(mass[i] * pos[i] for i in sup_idxs) / m_sub
        else:
            com_sub = jc.copy()
        # Signed: above the joint is the destabilizing (inverted) side.
        d_z = float(com_sub[2] - jc[2])
        # Floor: the smallest displacement the joint resolves is the capture
        # band; below it no gravity moment is measurable.
        d_eff = d_z if d_z > d_eq_m else d_eq_m

        for k, axis_local in enumerate(axes[:dof]):
            R_p = transforms.to_matrix(quat[parent_idx])
            axis_w = R_p @ axis_local
            axis_w = axis_w / max(float(np.linalg.norm(axis_w)), 1e-15)

            # Inertia of one side of the pair about the joint axis through
            # the joint center:  parallel axis  m*|d - (d.axis)axis|^2 +
            # body term axis^T I_w axis.
            def _side_inertia(link_idxs) -> float:
                total = 0.0
                for i in link_idxs:
                    if mass[i] <= 0.0:
                        continue
                    d = pos[i] - jc
                    d_perp = d - float(np.dot(d, axis_w)) * axis_w
                    R_i = transforms.to_matrix(quat[i])
                    I_w = R_i @ np.diag(inertia_diag[i]) @ R_i.T
                    total += float(axis_w @ (I_w @ axis_w)) \
                        + mass[i] * float(d_perp @ d_perp)
                return total

            inertia_child = _side_inertia(sup_idxs)
            inertia_parent = _side_inertia([parent_idx])
            # Reduced inertia of the pair: the muscle drives the RELATIVE
            # angle, and the reaction torque lands on the parent LINK first.
            if inertia_child > 1e-15 and inertia_parent > 1e-15:
                inertia_red = (inertia_child * inertia_parent
                               / (inertia_child + inertia_parent))
            elif inertia_child > 1e-15:
                inertia_red = inertia_child  # massless parent (rig base)
            else:
                inertia_red = 0.0

            # I_eff: what one explicit tick of the couple actually
            # accelerates -- the COM-frame response 1/I = axis.I^-1.axis
            # summed over the two links (a pure torque rotates a body about
            # its COM, not about the joint center).
            def _com_inv_inertia(link_idx) -> float:
                if mass[link_idx] <= 0.0:
                    return 0.0
                I_inv_diag = state["inv_inertia_diag_local"][link_idx]
                R_i = transforms.to_matrix(quat[link_idx])
                I_inv_w = R_i @ np.diag(I_inv_diag) @ R_i.T
                return float(axis_w @ (I_inv_w @ axis_w))

            inv_i_eff = _com_inv_inertia(child_idx) + _com_inv_inertia(parent_idx)
            i_eff = 1.0 / inv_i_eff if inv_i_eff > 1e-15 else 0.0

            if m_sub > 0.0 and inertia_child > 1e-15:
                # The SERVO bandwidth: the supported side's own fall rate,
                # sqrt(K_g / I_supported).  (Not the pair's relative-mode
                # rate: that one is set by the light local bone -- measured
                # 2026-08-08, bandwidth 260 rad/s at the knee, NaN in 200
                # ticks.  The trunk falls at 4.5 rad/s; respond to THAT.)
                omega_n = math.sqrt(m_sub * GRAVITY * d_eff / inertia_child)
            else:
                omega_n = 0.0
            # Continuous-time targets capped by the discrete-time stability
            # bounds of the integration scheme (module docstring: the law).
            kp = _CLOSED_LOOP_OVER_FALL_RATE * m_sub * GRAVITY * d_eff
            kd = 2.0 * _ZETA * inertia_red * omega_n
            if i_eff > 0.0:
                kp = min(kp, i_eff * (2.0 / dt) ** 2)
                kd = min(kd, i_eff / dt)
            else:
                kp = 0.0
                kd = 0.0

            table.append({
                "joint": joint_name,
                "joint_index": ji,
                "parent_idx": parent_idx,
                "child_idx": child_idx,
                "axis_local_parent": axis_local,
                "dof_index": k,
                "torque_limit_Nm": float(torque_limit),
                "moment_arm_m": float(arm_m),
                "kp": float(kp),
                "kd": float(kd),
                "subtree_mass": m_sub,
                "subtree_inertia": float(inertia_child),
                "parent_inertia": float(inertia_parent),
                "reduced_inertia": float(inertia_red),
                "couple_inertia": float(i_eff),
                "omega_n": float(omega_n),
            })

    return table
