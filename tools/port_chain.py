"""port_chain.py -- THE BRANCHES. One connection at a time, and the truth that flows through it.

THE CORRECTION THAT PRODUCED THIS FILE (operator, 2026-08-02): *"stand is not a port. Stand is the
tree."* `stand_port.py` drew the whole skeleton and called it a port. It is not. A PORT IS A BRANCH
-- the line between two proven points -- and the tree is what you get when every branch carries.

    GROUND --> FOOT --> ANKLE --> KNEE --> HIP --> PELVIS

Six points, five branches. Each branch is proven ALONE, from the root outward, before the next one
is touched. You do not train the tree. You train the connection.

WHAT FLOWS, AND WHY IT IS CHECKABLE. A branch carries FORCE, and Newton makes the check exact at
every instant -- standing, falling, or mid-stride:

    force through the joint  =  m_above * a_com_above     (cacc is gravity-offset)

So for each branch we take the free body ABOVE it, add up its mass, read its measured centre-of-
mass acceleration out of the simulator, and ask whether the force the branch is actually carrying
equals what Newton says it must. THE RESIDUAL IS THE PORT'S ERROR. It needs no equilibrium, no
settling and no assumption that the body is standing -- which matters, because it is not.

    A branch that closes carries the truth. A branch that does not is where the body breaks.

WHAT THE FIRST RUN FOUND, before a line of training:
  * GROUND<->FOOT carries 200.8 N against a body weight of 580.5 N -- 34.6%. At the keyframe the
    body is not standing on the ground, it is FALLING onto it at ~4.6 m/s^2.
  * THE MASSES DISAGREE. theHuman publishes 94.504 kg (668.7 N); the simulated body is 82.041 kg
    (580.5 N). theHuman's figure includes a 9.9 kg suit and 1.9 kg of consumables that
    `myobody.xml` does not wear -- so `stand_port.py`'s derived weight is 15% off the body it is
    supposed to stand up. A tree picture cannot show that. One branch measurement did.

    python tools/port_chain.py               # prove every branch, draw the growing tree
    python tools/port_chain.py --settle 0.5  # let it settle first, then prove
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from world import load_body

MYOBODY = ROOT / "external" / "myo_sim" / "body" / "myobody.xml"
OUTDIR = ROOT / "ChimeraEngine" / "output" / "ports"

# The chain, ROOT FIRST. Each entry is (point, the body whose joint carries it).
# Walked from the model's own parent tree, never typed: toes_r -> calcn_r -> talus_r -> tibia_r
# -> femur_r -> pelvis. `talus_r` is the ankle's own body and weighs 0.021 kg -- it is a hinge,
# not a segment, which is why the ANKLE branch carries almost exactly what the FOOT branch does.
CHAIN = [("GROUND", None), ("FOOT", "toes_r"), ("ANKLE", "talus_r"),
         ("KNEE", "tibia_r"), ("HIP", "femur_r"), ("PELVIS", "pelvis")]


def bodies_above(m, mujoco, body_name):
    """Every body at or above this one in the tree -- the FREE BODY the branch has to carry."""
    root = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, body_name)
    keep, changed = {root}, True
    while changed:                      # everything whose parent chain does NOT pass through root
        changed = False
        for i in range(1, m.nbody):
            if i in keep:
                continue
            j, hit = i, False
            while j > 0:
                if j == root:
                    hit = True
                    break
                j = m.body_parentid[j]
            if not hit:
                keep.add(i)
                changed = True
    return sorted(keep - {root} | {root})


def free_body_above(m, d, ids):
    """Mass, CoM height and CoM vertical acceleration of a set of bodies -- measured, not modelled."""
    mass = float(sum(m.body_mass[i] for i in ids))
    if mass <= 0:
        return 0.0, 0.0, 0.0
    com = sum(m.body_mass[i] * d.xipos[i] for i in ids) / mass
    acc = sum(m.body_mass[i] * d.cacc[i][3:6] for i in ids) / mass
    return mass, float(com[2]), float(acc[2])


def ground_force(m, d, mujoco):
    """What the GROUND branch is actually carrying, summed over every contact with the floor."""
    fz = 0.0
    for c in range(d.ncon):
        f = np.zeros(6)
        mujoco.mj_contactForce(m, d, c, f)
        con = d.contact[c]
        n = con.frame[0:3]
        fz += float(f[0] * n[2])        # normal force projected onto world +Z
    return fz


def prove_chain(settle=0.0):
    import mujoco
    m, g = load_body(MYOBODY, mujoco)
    d = mujoco.MjData(m)
    d.qpos[:] = m.key_qpos[0]
    mujoco.mj_forward(m, d)
    for _ in range(int(settle / m.opt.timestep)):
        mujoco.mj_step(m, d)
    mujoco.mj_forward(m, d)
    # WITHOUT THIS, cacc AND cfrc_int ARE ZERO and every branch reports a_com = 0.00 and the same
    # carried force -- which is what the first run did. mj_forward does not run the post-constraint
    # RNE pass, so the accelerations and the per-joint interaction forces simply are not there yet.
    # Rule 24: the instrument reported a clean 0.00 rather than "I did not measure this."
    mujoco.mj_rnePostConstraint(m, d)

    total = float(sum(m.body_mass))
    rows = []
    for k in range(1, len(CHAIN)):
        lo_name, _ = CHAIN[k - 1]
        hi_name, body = CHAIN[k]
        ids = bodies_above(m, mujoco, body)
        mass, com_z, acc_z = free_body_above(m, d, ids)
        # NEWTON, IN MUJOCO'S CONVENTION -- and the convention is the whole correction.
        # `cacc` is ALREADY gravity-offset: a body in free fall reads 0, a body at rest on the
        # ground reads +g. So `mass * (g + acc_z)` -- which is what this line said for one commit
        # -- COUNTS GRAVITY TWICE and demanded double the weight of every branch.
        # The control caught it: a settled body reads a_com ~ +7.076, and mass * a_com =
        # 82.041 * 7.076 = 580.5 N, which is its weight exactly. That is the known case rule 24
        # says to check by hand before trusting a column across five branches. I published the
        # column first and checked afterwards; this is the correction.
        need = mass * acc_z
        if lo_name == "GROUND":
            have = ground_force(m, d, mujoco)         # measured contact force
            src = "measured contact"
        else:
            # THE FORCE ACTUALLY IN THE JOINT, read from MuJoCo rather than propagated. The first
            # version carried the ground force upward and subtracted segment weights, so every
            # branch reported the SAME number -- a chain of arithmetic wearing five measurements'
            # clothes. cfrc_int is the interaction force between a body and its parent: the
            # truth in the branch, measured at the branch.
            bid = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, body)
            have = -float(d.cfrc_int[bid][5])
            src = "cfrc_int (measured at the joint)"
        rows.append(dict(
            branch=f"{lo_name} -> {hi_name}", mass=mass, com_z=com_z, acc_z=acc_z,
            need=need, have=have, src=src,
            resid_pct=100.0 * (have - need) / max(abs(need), 1e-9),
            mass_below_next=0.0))
    # the mass each branch drops off before the next one (the segment between the two joints)
    for i in range(len(rows) - 1):
        rows[i]["mass_below_next"] = rows[i]["mass"] - rows[i + 1]["mass"]
    return m, d, g, total, rows


def draw(rows, g, total, path, ledger_mass):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig = plt.figure(figsize=(14.5, 7.2))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.05, 1.15], wspace=0.22)

    # ── the tree, growing from the root, one branch at a time ────────────────────────────────
    ax = fig.add_subplot(gs[0, 0])
    ys = [0.0] + [r["com_z"] for r in rows]
    names = ["GROUND"] + [r["branch"].split("->")[1].strip() for r in rows]
    for i, r in enumerate(rows):
        ok = abs(r["resid_pct"]) <= 5.0
        col = "#1a7f37" if ok else "#c0392b"
        ax.annotate("", xy=(0, ys[i + 1]), xytext=(0, ys[i]),
                    arrowprops=dict(arrowstyle="-|>", lw=1.6 if ok else 1.6,
                                    color=col, ls="-" if ok else (0, (3, 3)),
                                    shrinkA=8, shrinkB=8))
        ax.text(0.035, (ys[i] + ys[i + 1]) / 2,
                f"{r['have']:.0f} N carried\nNewton wants {r['need']:.0f} N\n"
                f"{'CLOSES' if ok else 'OPEN'} {r['resid_pct']:+.1f}%",
                fontsize=7.4, color=col, va="center")
    for n, y in zip(names, ys):
        ax.scatter([0], [y], s=150, zorder=5, facecolor="white", edgecolor="#222", lw=1.6)
        ax.text(-0.03, y, n, fontsize=8, ha="right", va="center", weight="bold")
    ax.axhline(0, color="#8b5a2b", lw=3.2)
    ax.set_xlim(-0.16, 0.30); ax.set_ylim(-0.05, max(ys) + 0.10); ax.axis("off")
    ax.set_title("THE BRANCHES — solid = the truth flows through it\n"
                 "dashed = the port is OPEN, the connection does not carry", fontsize=9.5)

    # ── the ledger of the proof ──────────────────────────────────────────────────────────────
    ax = fig.add_subplot(gs[0, 1]); ax.axis("off")
    L = [f"g = {g:.6f} m/s²   simulated body = {total:.3f} kg   weight = {total*g:.1f} N", "",
         f"{'branch':<18}{'mass above':>11}{'a_com':>9}{'needs':>10}{'carries':>10}{'resid':>9}"]
    for r in rows:
        L.append(f"{r['branch']:<18}{r['mass']:>9.2f}kg{r['acc_z']:>8.2f}"
                 f"{r['need']:>9.1f}N{r['have']:>9.1f}N{r['resid_pct']:>8.1f}%")
    L += ["", "PROVEN = the branch carries what Newton says it must, |resid| <= 5%.",
          "The law needs no equilibrium: force_in = m_above * (g + a_com).",
          "It is exact while falling, which is what this body is doing.", "",
          "THE MASS DEFECT, found by this file:",
          f"  theHuman publishes      {ledger_mass:.3f} kg  ({ledger_mass*g:.1f} N)",
          f"  the simulated body is   {total:.3f} kg  ({total*g:.1f} N)",
          f"  -> stand_port.py's derived weight is {100*(ledger_mass/total-1):+.1f}% off the body",
          "     it is meant to stand up. theHuman wears a 9.9 kg suit + 1.9 kg consumables;",
          "     myobody.xml does not. ONE QUANTITY, TWO LANDMARKS (rule 19)."]
    ax.text(0, 1, "\n".join(L), family="monospace", fontsize=8.4, va="top")
    fig.suptitle("PORT CHAIN — one branch at a time, from the root outward", fontsize=11.5)
    fig.savefig(path, dpi=104, bbox_inches="tight"); plt.close(fig)


def main() -> int:
    a = sys.argv
    settle = float(a[a.index("--settle") + 1]) if "--settle" in a else 0.0
    OUTDIR.mkdir(parents=True, exist_ok=True)
    m, d, g, total, rows = prove_chain(settle)

    hits = [p for p in (ROOT / "story").rglob("numbers.json") if p.parent.name == "theHuman"]
    ledger_mass = float(json.loads(hits[0].read_text(encoding="utf8"))["mass_kg"])

    print(f"\nTHE PORT CHAIN — settle {settle}s,  g = {g:.6f},  body {total:.3f} kg\n" + "=" * 92)
    print(f"{'branch':<18}{'mass above':>12}{'a_com m/s²':>12}{'needs':>11}{'carries':>11}"
          f"{'resid':>9}   verdict")
    first_open = None
    for r in rows:
        ok = abs(r["resid_pct"]) <= 5.0
        if not ok and first_open is None:
            first_open = r["branch"]
        print(f"{r['branch']:<18}{r['mass']:>10.2f}kg{r['acc_z']:>12.2f}{r['need']:>10.1f}N"
              f"{r['have']:>10.1f}N{r['resid_pct']:>8.1f}%   {'CLOSES' if ok else 'OPEN'}")
    print("=" * 92)
    print(f"THE ROOT BRANCH IS: {first_open or 'none — every branch carries'}")
    print(f"MASS: theHuman {ledger_mass:.3f} kg vs simulated {total:.3f} kg "
          f"({100*(ledger_mass/total-1):+.1f}%)")

    png = OUTDIR / f"port_chain_settle{settle:g}.png"
    draw(rows, g, total, png, ledger_mass)
    print(f"\nPICTURE: {png}\nA BRANCH YOU HAVE NOT LOOKED AT IS NOT PROVEN.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
