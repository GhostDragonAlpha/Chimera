"""tissue_witness.py -- LOOK AT THE LIGAMENTS. One variable: passive tissue on vs off.

Port test 6 says passive force exists and grows toward the stop. That is a PASS, not a picture,
and a pass tells you the sign of a thing rather than its shape. This draws the shape:

  LEFT   the derived moment-angle curve for every ligament, with the band the body actually walks
         through shaded. A ligament that is not flat across the shaded band is resisting normal
         motion, which no amount of end-range correctness would excuse.

  RIGHT  the same body dropped twice with every actuator silent, ligaments ON and OFF, nothing
         else changed. Passive tissue cannot make a body stand -- nothing is driving it -- so the
         honest claim is narrow: it should change HOW it collapses, and if it does not, the
         tendons are in the model doing nothing and port 6 was reading a number I put there.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mujoco
import numpy as np

from port_registry import MYOBODY
from world import LIGAMENT_JOINTS, derive_ligaments, load_body, _ledger

OUT = Path(__file__).resolve().parent.parent / "ChimeraEngine" / "output" / "ports"
SHOW = ["hip_flexion_r", "knee_angle_r", "ankle_angle_r"]


def sweep(m, d, jname):
    """Passive joint torque across the joint's whole published range, everything else silent."""
    j = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, jname)
    adr, dof = int(m.jnt_qposadr[j]), int(m.jnt_dofadr[j])
    lo, hi = float(m.jnt_range[j][0]), float(m.jnt_range[j][1])
    qs = np.linspace(lo, hi, 181)
    tq = []
    for q in qs:
        mujoco.mj_resetData(m, d)
        d.qpos[adr] = q
        d.qvel[:] = 0.0
        d.ctrl[:] = 0.0
        if m.na:
            d.act[:] = 0.0
        mujoco.mj_forward(m, d)
        # BOTH ARRAYS: qfrc_passive carries joint/tendon springs, qfrc_actuator carries the
        # MUSCLE's passive force. Reading one is how port 6 missed the tissue the body had.
        tq.append(float(d.qfrc_passive[dof]) + float(d.qfrc_actuator[dof]))
    return np.degrees(qs), np.array(tq), (math.degrees(lo), math.degrees(hi))


def drop(tissue):
    m, g = load_body(MYOBODY, mujoco, tissue=tissue)
    d = mujoco.MjData(m)
    mujoco.mj_resetDataKeyframe(m, d, 0)
    mujoco.mj_forward(m, d)
    t, z = [], []
    for i in range(3000):
        d.ctrl[:] = 0.0
        mujoco.mj_step(m, d)
        t.append(d.time)
        z.append(float(d.qpos[2]))
    return np.array(t), np.array(z), g


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    env = _ledger()["gait_envelope_deg"]
    m_on, g = load_body(MYOBODY, mujoco, tissue=True, verbose=True)
    m_off, _ = load_body(MYOBODY, mujoco, tissue=False)
    d_on, d_off = mujoco.MjData(m_on), mujoco.MjData(m_off)
    emit, refused = derive_ligaments(mujoco.MjModel.from_xml_path(str(MYOBODY)), mujoco)

    fig = plt.figure(figsize=(15.5, 8.6), facecolor="white")
    gs = fig.add_gridspec(3, 2, width_ratios=[1.25, 1.0], hspace=0.55, wspace=0.24)

    for row, jn in enumerate(SHOW):
        ax = fig.add_subplot(gs[row, 0])
        qa, ta, (lo, hi) = sweep(m_on, d_on, jn)
        qb, tb, _ = sweep(m_off, d_off, jn)
        ek = LIGAMENT_JOINTS[jn]
        e_lo, e_hi = min(env[ek]), max(env[ek])
        ax.axvspan(e_lo, e_hi, color="#cfe8cf", alpha=0.75, zorder=0,
                   label="walked through (slack)" if row == 0 else None)
        ax.plot(qb, tb, color="#b0b0b0", lw=1.6, ls="--",
                label="muscle passive only (before)" if row == 0 else None)
        ax.plot(qa, ta, color="#8c1d1d", lw=2.4,
                label="with ligaments" if row == 0 else None)
        ax.axhline(0, color="#555", lw=0.7)
        for x in (lo, hi):
            ax.axvline(x, color="#333", lw=1.1, ls=":")
        mine = [e for e in emit if e["joint"] == jn]
        tag = " + ".join(f"{e['side']} k={e['k']:.0f}" for e in mine) or "no ligament derived"
        ax.set_title(f"{jn}    {tag} N.m/rad", fontsize=10, loc="left")
        ax.set_ylabel("passive torque (N.m)", fontsize=8)
        ax.tick_params(labelsize=7)
        if row == 0:
            ax.legend(fontsize=7.5, loc="upper left", framealpha=0.95)
        if row == len(SHOW) - 1:
            ax.set_xlabel("joint angle (deg)   dotted = published range", fontsize=8)

    ax = fig.add_subplot(gs[:, 1])
    ta, za, _ = drop(True)
    tb, zb, _ = drop(False)
    ax.plot(tb, zb, color="#b0b0b0", lw=2.0, ls="--", label="no passive tissue")
    ax.plot(ta, za, color="#8c1d1d", lw=2.4, label="with ligaments")
    ax.set_xlabel("time (s)", fontsize=9)
    ax.set_ylabel("pelvis height (m)", fontsize=9)
    ax.set_title("SAME BODY, DROPPED TWICE, EVERY ACTUATOR SILENT\n"
                 "one variable: the ligaments", fontsize=10, loc="left")
    ax.legend(fontsize=8.5)
    ax.tick_params(labelsize=8)
    ax.grid(alpha=0.25)
    ax.text(0.02, 0.03,
            f"g = {g:.4f} m/s2 (this world, not Earth)\n"
            f"final pelvis z:  ligaments {za[-1]:.3f} m   none {zb[-1]:.3f} m\n"
            f"{len(emit)} ligaments derived, {len(refused)} refused by name",
            transform=ax.transAxes, fontsize=8, va="bottom",
            bbox=dict(fc="#f4f4f4", ec="#999", boxstyle="round,pad=0.45"))

    fig.suptitle("PASSIVE TISSUE -- derived from theHuman's own gait envelope and this body's "
                 "own muscle torque, never chosen", fontsize=12.5, y=0.975)
    p = OUT / "tissue_witness.png"
    fig.savefig(p, dpi=115, bbox_inches="tight", facecolor="white")
    print(f"\nPICTURE: {p}")
    for e in emit:
        print(f"  {e['name']:28} slack to {math.degrees(e['edge']):+7.2f} deg, "
              f"{e['tau']:6.1f} N.m at {math.degrees(e['limit']):+7.2f} deg")
    for jn, side, why in refused:
        print(f"  REFUSED {jn}/{side}: {why}")


if __name__ == "__main__":
    main()
