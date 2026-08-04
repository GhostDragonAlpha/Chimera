"""fall_exit.py -- WHICH EDGE OF ITS BASE DOES THE BODY LEAVE, AND WITH WHAT PITCH?

MEASURE IT, DO NOT FIX IT. This file records; it changes no gain and proposes no repair.

RULE 0, stated before the run:

    STATEMENT   The roll feedback term turned 10/10 LATERAL falls into 9/10 BACKWARD ones at a
                7x tighter seed spread. That is not a partial cure -- it is a CHANGE OF
                MECHANISM. With the lateral escape closed, `kp * pitch` is the only large
                restoring term left, and a proportional term with no damping overshoots: the
                body is driven through the sagittal equilibrium and out of the POSTERIOR edge
                of its base.

    PREDICTION  Across arm A's ten seeds, the CoM exits the POSTERIOR (behind-the-heel) edge of
                the base of support in >= 7 of 10.

    FALSIFIER   If the exit edges are distributed -- no edge taken by 7 of 10 -- there is no
                single mechanism to name, `kp` overcorrection is not the story, and this is
                recorded and stopped rather than pursued.

TWO INSTANTS, NOT ONE, because they answer different questions. The FALL BAR (pelvis below 50%
of target) is when the body has visibly gone; the BoS EXIT is when it became inevitable, and it
comes first. An exit edge read at the fall bar is read after the body has already toppled and
tells you where it landed, not where it left. This records both and reports the exit.

THE BASE IS THE CONTACT POLYGON (`tools/stance_choice.py`, 2026-08-04): the convex hull of the
points actually carrying load, measured per sample. theStance's `together_half_width_m` matches
it to 0.5 mm and is printed beside it, but the edge a CoM crosses is a fact about the polygon.

    python tools/fall_exit.py --theta stand_theta_roll_A.npy
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from world import load_body                                       # noqa: E402
from stand_port import derive_stand_port, MYOBODY                 # noqa: E402
from train_stand import (joint_ids, seat_in_limits,               # noqa: E402
                         CTRL_EVERY, NUDGE)
from parser import Parser, default_registry                       # noqa: E402

OUTDIR = ROOT / "ChimeraEngine" / "output" / "ports"
LOGDIR = ROOT / "agent_logs"
FOOT_BODIES = ("calcn_r", "calcn_l", "toes_r", "toes_l")
EDGES = ("anterior", "posterior", "left", "right")


def rollout(m, d, mujoco, theta, P, jids, secs, seed):
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
    foot_geoms = {gi for gi in range(m.ngeom) if int(m.geom_bodyid[gi]) in fb}
    tr = {k: [] for k in ("t", "z", "pitch", "roll", "comx", "comy",
                          "fore_lo", "fore_hi", "lat_lo", "lat_hi", "ncon")}
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
            last = (pitch, roll)
        mujoco.mj_step(m, d)
        if k % CTRL_EVERY == 0:
            com = d.subtree_com[0]
            cx, cy = [], []
            for ci in range(d.ncon):
                c = d.contact[ci]
                if int(c.geom1) in foot_geoms or int(c.geom2) in foot_geoms:
                    cx.append(float(c.pos[0])); cy.append(float(c.pos[1]))
            tr["t"].append(k * m.opt.timestep)
            tr["z"].append(float(d.qpos[2]))
            tr["pitch"].append(last[0]); tr["roll"].append(last[1])
            tr["comx"].append(float(com[0])); tr["comy"].append(float(com[1]))
            tr["ncon"].append(len(cx))
            # THE POLYGON'S SIGNED EDGES, in world coordinates. Signed, not half-extents: the
            # question is WHICH edge the CoM crossed, and a half-width centred on the foot mean
            # cannot tell front from back. `nan` when fewer than two contacts -- the body is not
            # standing on a base at all then, and an edge would be invented.
            if len(cx) > 1:
                tr["fore_lo"].append(min(cx)); tr["fore_hi"].append(max(cx))
                tr["lat_lo"].append(min(cy)); tr["lat_hi"].append(max(cy))
            else:
                for kk in ("fore_lo", "fore_hi", "lat_lo", "lat_hi"):
                    tr[kk].append(np.nan)
            if float(d.qpos[2]) < 0.5 * tgt:
                break
    return tr


def margins_at(tr, i):
    """SIGNED distance to each edge of the loaded polygon; positive = inside."""
    if not np.isfinite(tr["fore_lo"][i]):
        return None
    return {
        "anterior": tr["fore_hi"][i] - tr["comx"][i],     # room in front of the CoM
        "posterior": tr["comx"][i] - tr["fore_lo"][i],    # room behind it
        "left": tr["lat_hi"][i] - tr["comy"][i],
        "right": tr["comy"][i] - tr["lat_lo"][i],
    }


def first_exit(tr):
    """The FIRST sample outside the loaded polygon. A diagnostic, and NOT the fall.

    Measured 2026-08-04 and kept because the number is instructive: on every seed this lands at
    t = 0.02 s -- the first control tick. It is not a fall mechanism, it is the START: the
    keyframe is a POSE, not an equilibrium, only the HEELS are loaded at that instant, so the
    polygon's anterior edge is the heel line and a CoM 4.9 cm forward of it reads "outside".
    f3_stand already carries the same finding from the other direction ("against heels alone the
    CoM reads ~15 cm forward and OUTSIDE the box; against heels AND toes it is 4.8 mm forward").
    Reporting this as the exit edge would answer a question about the keyframe and label it a
    question about the fall.
    """
    for i in range(len(tr["t"])):
        marg = margins_at(tr, i)
        if marg and min(marg.values()) < 0.0:
            return i, min(marg, key=marg.get), marg
    return None, None, None


def committed_exit(tr):
    """THE EXIT THAT CAUSED THE FALL: the last inside -> outside crossing never recovered from.

    Scanned BACKWARD for the last sample at which the CoM was inside its loaded polygon; the
    exit is the sample after it. Everything before that was recovered from -- by definition,
    since the body came back inside -- and a body that recovers has not fallen out of anything.
    """
    last_in = None
    for i in range(len(tr["t"]) - 1, -1, -1):
        marg = margins_at(tr, i)
        if marg and min(marg.values()) >= 0.0:
            last_in = i
            break
    if last_in is None:
        return None, None, None, 0            # never inside its own loaded polygon at all
    j = last_in + 1
    while j < len(tr["t"]) and margins_at(tr, j) is None:
        j += 1
    if j >= len(tr["t"]):
        return None, None, None, last_in      # still inside when the record ended
    marg = margins_at(tr, j)
    return j, min(marg, key=marg.get), marg, last_in


def main() -> int:
    import mujoco
    a = sys.argv
    tp = Path(a[a.index("--theta") + 1]) if "--theta" in a else OUTDIR / "stand_theta_roll_A.npy"
    if not tp.is_absolute():
        tp = OUTDIR / tp.name
    nseeds = int(a[a.index("--seeds") + 1]) if "--seeds" in a else 10
    secs = float(a[a.index("--secs") + 1]) if "--secs" in a else 20.0
    if not tp.exists():
        raise SystemExit(f"no {tp} -- refusing to attribute a fall to a policy that does not "
                         f"exist (rule 20).")
    theta = np.load(tp)
    P = derive_stand_port()
    m, g = load_body(MYOBODY, mujoco)
    d = mujoco.MjData(m)
    jids = joint_ids(m, mujoco)
    tgt = P["OUT pelvis_target_m"]

    print(f"\nFALL EXIT -- {tp.name}, {nseeds} seeds x {secs:.0f} s. MEASURED, NOT FIXED.")
    print("=" * 108)
    print(f"  THE EXIT IS THE *COMMITTED* ONE -- the last inside->outside crossing never "
          f"recovered from. The FIRST")
    print(f"  exit is printed beside it and is not the fall: it lands at the first control tick "
          f"on every seed,")
    print(f"  because only the HEELS are loaded at the keyframe and the polygon's front edge is "
          f"then the heel line.")
    print("-" * 108)
    print(f"{'seed':>5}{'1st out':>9}{'exit t':>9}{'exit EDGE':>12}{'pitch@exit':>12}"
          f"{'roll@exit':>11}{'fore marg':>11}{'lat marg':>11}{'fall t':>9}{'pitch@fall':>12}")
    rows = []
    runs = []
    for s in range(nseeds):
        tr = rollout(m, d, mujoco, theta, P, jids, secs, s)
        runs.append(tr)
        f_i, _fe, _fm = first_exit(tr)
        i, edge, marg, last_in = committed_exit(tr)
        fall_t = tr["t"][-1] if tr["z"][-1] < 0.5 * tgt else None
        p_fall = float(tr["pitch"][-1])
        f_txt = f"{tr['t'][f_i]:.2f}s" if f_i is not None else "-"
        if i is None:
            note = "never inside" if last_in == 0 and f_i == 0 else "still inside"
            print(f"{s:>5}{f_txt:>9}{'-':>9}{note:>12}{'-':>12}{'-':>11}{'-':>11}{'-':>11}"
                  f"{(f'{fall_t:.2f}s' if fall_t else '-'):>9}{np.degrees(p_fall):>11.1f}d")
            rows.append(dict(seed=s, exit_t=None, edge=None, first_out_t=(
                float(tr["t"][f_i]) if f_i is not None else None), fall_t=fall_t))
            continue
        fore = min(marg["anterior"], marg["posterior"])
        lat = min(marg["left"], marg["right"])
        rows.append(dict(seed=s, exit_t=float(tr["t"][i]), edge=edge,
                         first_out_t=(float(tr["t"][f_i]) if f_i is not None else None),
                         pitch_exit_deg=float(np.degrees(tr["pitch"][i])),
                         roll_exit_deg=float(np.degrees(tr["roll"][i])),
                         fore_margin_m=float(fore), lat_margin_m=float(lat),
                         margins_m={k: float(v) for k, v in marg.items()},
                         fall_t=fall_t, pitch_fall_deg=float(np.degrees(p_fall))))
        print(f"{s:>5}{f_txt:>9}{tr['t'][i]:>8.2f}s{edge:>12}"
              f"{np.degrees(tr['pitch'][i]):>11.1f}d{np.degrees(tr['roll'][i]):>10.1f}d"
              f"{fore:>+11.4f}{lat:>+11.4f}"
              f"{(f'{fall_t:.2f}s' if fall_t else '-'):>9}{np.degrees(p_fall):>11.1f}d")
    print("-" * 108)
    counts = {e: sum(1 for r in rows if r.get("edge") == e) for e in EDGES}
    counts["never left"] = sum(1 for r in rows if r.get("edge") is None)
    for e, c in sorted(counts.items(), key=lambda p: -p[1]):
        if c:
            print(f"  {e:12} {c}/{nseeds}" + ("  <- the prediction's edge" if e == "posterior"
                                              else ""))
    got = counts.get("posterior", 0)
    exits = [r for r in rows if r.get("edge")]
    if exits:
        pe = np.array([r["pitch_exit_deg"] for r in exits])
        print(f"  pitch at exit: median {np.median(pe):+.1f} deg, range {pe.min():+.1f}.."
              f"{pe.max():+.1f} deg   (a NEGATIVE pitch here is leaning BACK)")
        et = np.array([r["exit_t"] for r in exits])
        ft = np.array([r["fall_t"] for r in exits if r["fall_t"]])
        print(f"  the CoM leaves at median {np.median(et):.2f} s and the pelvis crosses the fall "
              f"bar at median {np.median(ft):.2f} s")
        print(f"  -> {np.median(ft) - np.median(et):.2f} s of toppling AFTER the outcome was "
              f"decided. Reading an edge at the fall bar reads the landing.")
    print("=" * 108)
    fires = got < 7
    print(f"  PREDICTION (CoM exits the POSTERIOR edge in >= 7/10): "
          + (f"HOLDS -- {got}/{nseeds}." if not fires else f"NOT MET -- {got}/{nseeds}."))
    print(f"  FALSIFIER (exits distributed, no single mechanism): "
          + (f"FIRES -- no edge takes 7 of {nseeds}. There is no single mechanism to name; "
             f"kp overcorrection\n    is not established. RECORDED AND STOPPED, per the task."
             if fires else
             f"does not fire -- the posterior edge takes {got} of {nseeds}, so the exit has "
             f"ONE mechanism\n    and `kp * pitch` driving the body out the back is the "
             f"reading the measurement supports."))

    LOGDIR.mkdir(parents=True, exist_ok=True)
    out = LOGDIR / f"fall_exit_{tp.stem}.json"
    out.write_text(json.dumps(dict(
        theta=tp.name, seeds=nseeds, secs=secs, g=g, counts=counts,
        posterior_count=got, prediction_holds=bool(not fires),
        falsifier_fires=bool(fires), rows=rows), indent=1), encoding="utf8")
    print(f"  JSON: {out}")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 3, figsize=(15.5, 4.6))
    for tr, r in zip(runs, rows):
        fx = np.array(tr["fore_lo"], dtype=float)
        ok = np.isfinite(fx)
        ax[0].plot(np.array(tr["comy"])[ok], np.array(tr["comx"])[ok], lw=0.9, alpha=0.7)
        if r.get("exit_t") is not None:
            i = tr["t"].index(r["exit_t"])
            ax[0].scatter([tr["comy"][i]], [tr["comx"][i]], s=42, marker="X", color="#c0392b",
                          zorder=5)
    ax[0].set_xlabel("lateral m (world)"); ax[0].set_ylabel("fore-aft m (world)")
    ax[0].set_aspect("equal")
    ax[0].set_title("CoM path; X = the instant it left the contact polygon", fontsize=9)
    for tr in runs:
        ax[1].plot(tr["t"], np.degrees(tr["pitch"]), lw=1.0, alpha=0.75)
    for r in rows:
        if r.get("exit_t") is not None:
            ax[1].scatter([r["exit_t"]], [r["pitch_exit_deg"]], s=36, marker="X",
                          color="#c0392b", zorder=5)
    ax[1].axhline(0, color="#999", lw=0.9)
    ax[1].set_xlabel("s"); ax[1].set_ylabel("pitch deg  (negative = leaning back)")
    ax[1].set_title("pitch, and where the CoM left", fontsize=9)
    ks = [e for e in EDGES if counts.get(e)] + (["never left"] if counts["never left"] else [])
    ax[2].bar(range(len(ks)), [counts[k] for k in ks],
              color=["#c0392b" if k == "posterior" else "#7f8c8d" for k in ks])
    ax[2].axhline(7, color="#1a7f37", ls="--", lw=1.6, label="the prediction: 7 of 10")
    ax[2].set_xticks(range(len(ks))); ax[2].set_xticklabels(ks, fontsize=8)
    ax[2].set_ylabel(f"seeds of {nseeds}"); ax[2].legend(fontsize=7)
    ax[2].set_title("which edge did it leave by?", fontsize=9)
    fig.suptitle(f"FALL EXIT -- {tp.name}: posterior {got}/{nseeds}, "
                 f"{'falsifier FIRES' if fires else 'one mechanism'}", fontsize=11.5)
    png = OUTDIR / f"fall_exit_{tp.stem}.png"
    fig.savefig(png, dpi=104, bbox_inches="tight"); plt.close(fig)
    print(f"  PICTURE: {png}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
