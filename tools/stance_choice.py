"""stance_choice.py -- WHICH BASE OF SUPPORT SHOULD F3 JUDGE AGAINST? A measurement, for the
operator to sign.

`stand_port.py` picks `together_half_width_m` (0.1020 m) and theStance also publishes
`natural_half_width_m` (0.1565) and `braced_half_width_m` (0.3932). Nothing states why. F3 has
been printing that disagreement as an open question for two sessions; this file measures it.

RULE 0, stated before the run:

    STATEMENT   The three published stances are descriptions of postures a PERSON can adopt.
                The base of support is not a posture -- it is the convex hull of the points
                actually carrying load, and outside it the body IS a falling inverted pendulum.
                So exactly one of the four candidate landmarks is a physical fact about this
                rollout and three are descriptions of other rollouts.

    PREDICTION  The measured contact polygon does not coincide with any published stance, and
                the CoM's excursion relative to it disagrees with at least one published stance
                about whether the body left its base at all.

    FALSIFIER   If the contact polygon matches one published stance to within its own sampling
                grain, then the published number IS the measurement and the pick is a naming
                question rather than a physics one. Record it and let the operator pick on
                whatever grounds they like, because nothing measurable is at stake.

THE STANCE CHANGES NOTHING IN THE PLANT. It is a JUDGING landmark: the policy, the body and the
gravity are identical whichever one is read, so all four rows are scored from THE SAME TEN
ROLLOUTS. Running four sets of rollouts would let the seeds differ between rows and turn a
landmark comparison into a noise comparison.

    python tools/stance_choice.py [--theta <path>] [--seeds 10] [--secs 20]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from world import load_body                                       # noqa: E402
from stand_port import derive_stand_port, MYOBODY, read           # noqa: E402
from train_stand import (joint_ids, seat_in_limits,               # noqa: E402
                         CTRL_EVERY, NUDGE)
from parser import Parser, default_registry                       # noqa: E402
from classify_fall import classify_trace                          # noqa: E402

OUTDIR = ROOT / "ChimeraEngine" / "output" / "ports"
LOGDIR = ROOT / "agent_logs"
THETA = OUTDIR / "stand_theta.npy"
FOOT_BODIES = ("calcn_r", "calcn_l", "toes_r", "toes_l")


def rollout(m, d, mujoco, theta, P, jids, secs, seed):
    """One life through the parser, recording the CoM AND every candidate base beside it."""
    tgt, nu = P["OUT pelvis_target_m"], m.nu
    PARSER = Parser(default_registry(theta, tgt, nu))
    PARSER.set_verb("STAND", True)
    mujoco.mj_resetDataKeyframe(m, d, 0)
    mujoco.mj_forward(m, d)
    seat_in_limits(m, d, mujoco, jids)
    if seed:
        d.qpos[:] = d.qpos + np.random.default_rng(seed).normal(0.0, NUDGE, size=d.qpos.shape)
        mujoco.mj_forward(m, d)
    fb = [mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, n) for n in FOOT_BODIES]
    # THE GEOMS THAT CAN CARRY LOAD, so a contact can be attributed to a foot rather than to
    # any body part that happens to touch the floor. Read from the model, not name-matched.
    foot_geoms = {gi for gi in range(m.ngeom) if int(m.geom_bodyid[gi]) in fb}
    tr = {k: [] for k in ("t", "z", "comx", "comy", "polx", "poly", "conx", "cony", "ncon")}
    steps = int(secs / m.opt.timestep)
    for k in range(steps):
        if k % CTRL_EVERY == 0:
            z = float(d.qpos[2])
            q = d.qpos[3:7]
            pitch = float(np.arctan2(2 * (q[0] * q[2] - q[3] * q[1]),
                                     1 - 2 * (q[1] ** 2 + q[2] ** 2)))
            roll = float(np.arctan2(2 * (q[0] * q[1] + q[2] * q[3]),
                                    1 - 2 * (q[1] ** 2 + q[2] ** 2)))
            u, _ = PARSER.command({"z": z, "pitch": pitch, "roll": roll})
            d.ctrl[:] = u if u is not None else 0.0
        mujoco.mj_step(m, d)
        if k % CTRL_EVERY == 0:
            com = d.subtree_com[0]
            xp = [float(d.xpos[b][0]) for b in fb]
            yp = [float(d.xpos[b][1]) for b in fb]
            foot = np.array([np.mean(xp), np.mean(yp)])
            tr["t"].append(k * m.opt.timestep)
            tr["z"].append(float(d.qpos[2]))
            tr["comx"].append(float(com[0]) - foot[0])
            tr["comy"].append(float(com[1]) - foot[1])
            # LANDMARK A -- the four foot-body ORIGINS, which is what f3_stand prints today.
            tr["polx"].append(max(1e-9, 0.5 * (max(xp) - min(xp))))
            tr["poly"].append(max(1e-9, 0.5 * (max(yp) - min(yp))))
            # LANDMARK B -- THE CONTACT POINTS THEMSELVES, which is what a base of support IS.
            # The four origins are body FRAMES: they sit inside the feet and know nothing about
            # how wide a foot is, so they understate the polygon by construction. A contact is
            # a point the floor is actually pushing on.
            cx, cy = [], []
            for ci in range(d.ncon):
                c = d.contact[ci]
                if int(c.geom1) in foot_geoms or int(c.geom2) in foot_geoms:
                    cx.append(float(c.pos[0])); cy.append(float(c.pos[1]))
            tr["ncon"].append(len(cx))
            tr["conx"].append(max(1e-9, 0.5 * (max(cx) - min(cx))) if len(cx) > 1 else np.nan)
            tr["cony"].append(max(1e-9, 0.5 * (max(cy) - min(cy))) if len(cy) > 1 else np.nan)
            if float(d.qpos[2]) < 0.5 * tgt:
                break
    return tr


def score_against(tr, hw, hl):
    """The CoM excursion against ONE base. `hw`/`hl` may be scalars (a published stance) or
    per-sample arrays (a measured polygon). Returns (peak, pct_outside)."""
    x = np.abs(np.asarray(tr["comx"], dtype=float))
    y = np.abs(np.asarray(tr["comy"], dtype=float))
    hw = np.asarray(hw, dtype=float) * np.ones_like(y)
    hl = np.asarray(hl, dtype=float) * np.ones_like(x)
    ratio = np.maximum(x / hl, y / hw)
    good = np.isfinite(ratio)
    if not good.any():
        return float("nan"), float("nan")
    r = ratio[good]
    return float(r.max()), float(100.0 * (r > 1.0).mean())


def main() -> int:
    import mujoco
    a = sys.argv
    nseeds = int(a[a.index("--seeds") + 1]) if "--seeds" in a else 10
    secs = float(a[a.index("--secs") + 1]) if "--secs" in a else 20.0
    tp = Path(a[a.index("--theta") + 1]) if "--theta" in a else THETA
    if not tp.is_absolute():
        tp = OUTDIR / tp.name
    if not tp.exists():
        raise SystemExit(f"no {tp} -- refusing to choose a stance for a policy that does not "
                         f"exist (rule 20).")
    theta = np.load(tp)
    P = derive_stand_port()
    # THE THREE PUBLISHED STANCES, read from theStance directly rather than from the port --
    # the port publishes only the ONE it picked, which is the thing under question here.
    S = read("theStance", ("together_half_width_m", "together_half_length_m",
                           "natural_half_width_m", "natural_half_length_m",
                           "braced_half_width_m", "braced_half_length_m", "foot_breadth_m"))
    m, g = load_body(MYOBODY, mujoco)
    d = mujoco.MjData(m)
    jids = joint_ids(m, mujoco)
    tgt = P["OUT pelvis_target_m"]

    runs = [rollout(m, d, mujoco, theta, P, jids, secs, s) for s in range(nseeds)]
    surv = np.array([r["t"][-1] for r in runs])
    labels = [classify_trace(r, tgt)["label"] for r in runs]

    bases = [
        ("together (the pick)", float(S["together_half_width_m"]),
         float(S["together_half_length_m"]), None),
        ("natural", float(S["natural_half_width_m"]), float(S["natural_half_length_m"]), None),
        ("braced", float(S["braced_half_width_m"]), float(S["braced_half_length_m"]), None),
        ("foot-origin spread", None, None, "pol"),
        ("CONTACT polygon", None, None, "con"),
    ]

    print(f"\nSTANCE CHOICE -- {tp.name}, {nseeds} seeds x {secs:.0f} s, ONE set of rollouts "
          f"scored five ways")
    print("=" * 104)
    print(f"  the stance is a JUDGING landmark: it changes nothing in the plant, so survival is "
          f"IDENTICAL by construction")
    print(f"  across every row and cannot discriminate between them. Printed once, not five "
          f"times pretending to compare.")
    print(f"  SURVIVAL  median {float(np.median(surv)):.2f} s   min {surv.min():.2f} s   "
          f"max {surv.max():.2f} s   spread {surv.max()-surv.min():.2f} s   "
          f"falls: {', '.join(sorted(set(labels)))}")
    print("-" * 104)
    print(f"  {'base of support':24}{'half-width m':>14}{'CoM peak':>11}{'% outside':>12}"
          f"{'seeds outside':>15}")
    rows = []
    for name, hw, hl, meas in bases:
        peaks, pcts = [], []
        widths = []
        for r in runs:
            if meas == "pol":
                _hw, _hl = r["poly"], r["polx"]
            elif meas == "con":
                _hw, _hl = r["cony"], r["conx"]
            else:
                _hw, _hl = hw, hl
            pk, pc = score_against(r, _hw, _hl)
            peaks.append(pk); pcts.append(pc)
            widths.append(float(np.nanmean(np.asarray(_hw, dtype=float)))
                          if meas else float(hw))
        med_pk = float(np.nanmedian(peaks))
        med_pc = float(np.nanmedian(pcts))
        n_out = int(sum(1 for v in peaks if np.isfinite(v) and v > 1.0))
        w = float(np.nanmedian(widths))
        rows.append(dict(base=name, half_width_m=w, com_peak_median=med_pk,
                         pct_outside_median=med_pc, seeds_outside=n_out,
                         com_peak_per_seed=[float(v) for v in peaks]))
        tag = "  (measured)" if meas else ""
        print(f"  {name:24}{w:>14.4f}{med_pk:>11.2f}{med_pc:>11.1f}%{n_out:>10}/{nseeds}{tag}")
    print("=" * 104)

    # ---- THE VERDICT ------------------------------------------------------------------
    con_w = rows[4]["half_width_m"]
    pub = {r["base"]: r["half_width_m"] for r in rows[:3]}
    nearest = min(pub, key=lambda k: abs(pub[k] - con_w))
    # THE GRAIN: theStance builds every stance width out of `foot_breadth_m`, so the finest
    # lateral distance it can resolve is one foot breadth. A gap under that is inside the
    # published number's own resolution and is not a disagreement.
    grain = float(S["foot_breadth_m"])
    gap = abs(pub[nearest] - con_w)
    matched = gap <= grain
    disagree = len({r["seeds_outside"] > 0 for r in rows}) > 1
    print(f"  MEASURED contact half-width {con_w:.4f} m. Nearest published: {nearest} "
          f"{pub[nearest]:.4f} m (gap {gap:.4f} m)")
    print(f"  theStance's own grain is one foot breadth, {grain:.4f} m -- every stance width it "
          f"publishes is built from it.")
    print(f"  FALSIFIER (the polygon matches a published stance inside that grain): "
          + (f"FIRES -- the gap {gap:.4f} m <= {grain:.4f} m, so `{nearest}` IS the measurement "
             f"and\n    the pick is a NAMING question, not a physics one."
             if matched else
             f"does not fire -- the gap {gap:.4f} m exceeds the grain."))
    print(f"  DO THE LANDMARKS DISAGREE ABOUT THE VERDICT? "
          + ("YES -- at least one base says the CoM left it and at least one says it did not."
             if disagree else
             "NO -- every base returns the same in/out verdict on every seed."))
    print("-" * 104)
    print("  RECOMMENDATION (the physics, stated; the line is the operator's to sign):")
    print("    A base of support is not a posture. It is the convex hull of the points actually")
    print("    carrying load -- that is the definition the falsifier is written in ('outside it")
    print("    the body IS a falling pendulum'), and it is the only one of the five that is a")
    print("    FACT ABOUT THIS ROLLOUT. The three published widths describe postures a person")
    print("    can adopt; judging this body against one it did not adopt is one quantity with")
    print("    two landmarks (rule 19).")
    print(f"    -> F3's bar should read the CONTACT POLYGON. The published `{nearest}` is the")
    print(f"       closest description of what this body does and belongs in the report as the")
    print(f"       comparison it is, not as the bar.")
    print("    NOTE THE FOOT-ORIGIN ROW, and do not adopt it: those four points are body FRAMES")
    print("    inside the feet and know nothing about how wide a foot is, so they understate the")
    print("    polygon by construction. It is printed because f3_stand prints it today.")

    LOGDIR.mkdir(parents=True, exist_ok=True)
    out = LOGDIR / f"stance_choice_{tp.stem}.json"
    out.write_text(json.dumps(dict(
        theta=tp.name, seeds=nseeds, secs=secs, g=g,
        survival_median_s=float(np.median(surv)), survival_min_s=float(surv.min()),
        survival_max_s=float(surv.max()), fall_labels=labels,
        published=dict(together=float(S["together_half_width_m"]),
                       natural=float(S["natural_half_width_m"]),
                       braced=float(S["braced_half_width_m"]),
                       foot_breadth_grain=grain),
        rows=rows, measured_contact_half_width_m=con_w, nearest_published=nearest,
        gap_m=gap, matches_within_grain=bool(matched),
        landmarks_disagree=bool(disagree)), indent=1), encoding="utf8")
    print(f"  JSON: {out}")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 2, figsize=(13.8, 5.0))
    cols = ["#c0392b", "#e67e22", "#8e44ad", "#7f8c8d", "#1a7f37"]
    for (nm, hw, hl, meas), c in zip(bases, cols):
        w = [r for r in rows if r["base"] == nm][0]["half_width_m"]
        h = float(hl) if hl is not None else float(np.nanmedian(
            [np.nanmean(np.asarray(r["conx" if meas == "con" else "polx"], dtype=float))
             for r in runs]))
        ax[0].add_patch(plt.Rectangle((-w, -h), 2 * w, 2 * h, fill=False, ec=c, lw=2.0,
                                      label=f"{nm} ({w:.3f} m)"))
    for r in runs:
        ax[0].plot(r["comy"], r["comx"], color="#333", lw=0.7, alpha=0.45)
    ax[0].set_xlim(-0.45, 0.45); ax[0].set_ylim(-0.45, 0.45); ax[0].set_aspect("equal")
    ax[0].set_xlabel("lateral m"); ax[0].set_ylabel("fore-aft m"); ax[0].legend(fontsize=7)
    ax[0].set_title(f"the same {nseeds} CoM traces against five candidate bases", fontsize=9)
    xs = np.arange(len(rows))
    ax[1].bar(xs, [r["com_peak_median"] for r in rows], color=cols)
    ax[1].axhline(1.0, color="#c0392b", ls="--", lw=1.6, label="the bar: outside the base")
    ax[1].set_xticks(xs)
    ax[1].set_xticklabels([r["base"].replace(" ", "\n") for r in rows], fontsize=7)
    ax[1].set_ylabel("median CoM peak, fraction of base"); ax[1].legend(fontsize=7)
    ax[1].set_title("which landmark says the body left its base?", fontsize=9)
    fig.suptitle(f"STANCE CHOICE -- {tp.name}: measured contact half-width {con_w:.4f} m vs "
                 f"together {pub['together (the pick)']:.4f} / natural {pub['natural']:.4f} / "
                 f"braced {pub['braced']:.4f}", fontsize=11)
    png = OUTDIR / f"stance_choice_{tp.stem}.png"
    fig.savefig(png, dpi=104, bbox_inches="tight"); plt.close(fig)
    print(f"  PICTURE: {png}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
