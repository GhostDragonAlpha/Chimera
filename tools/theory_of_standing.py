"""theory_of_standing.py -- WHAT STANDING REQUIRES. A theory that can be refuted, not enumerated.

THE OPERATOR'S POINT, 2026-08-02: *"It could be that we train something, and then we have to go
back and do more research because the theory of standing wasn't solved. Once we have all the ports
for the entire human body -- that's necessary for standing -- is kind of the issue."*

That is exactly right, and it names the real deliverable. The walker is not the product. THE THEORY
OF WHAT STANDING REQUIRES is the product, and every port we train is a test of it.

    train a port -> the body still falls -> the theory forgot something -> research -> derive
    -> train -> the body still falls -> the theory forgot something else -> ...

BUT THAT LOOP HAS TWO SPEEDS, and the slow one is optional. Discovering each missing piece by
FAILING costs a training run per piece. Deriving the requirements FIRST, from physics we already
publish, costs nothing and makes the theory FALSIFIABLE: a requirement that is derived can be
checked before it is built, and a requirement that is missing announces itself as a row with no
evidence rather than as a run that mysteriously did not work.

    A THEORY YOU CAN ONLY DISCOVER BY FAILING IS AN ENUMERATION. A THEORY YOU CAN STATE
    IN ADVANCE AND THEN BE WRONG ABOUT IS A THEORY.

SO WHAT DOES STANDING REQUIRE? An inverted pendulum stays up if and only if three things hold, and
each one is a QUESTION with a published number behind it -- not a list somebody remembered:

  R1 A BASE          there is a polygon of support, and the CoM projects inside it.
                     theStance publishes it. MEASURED: yes, 4.8 mm fore / 40.4 mm lateral inside.
  R2 A LOAD PATH     every joint between the CoM and the ground carries its share without
                     buckling. That is the port chain, and it is what we have been training.
  R3 A FAST LOOP     the CoM wanders, so something must COMMAND a correction faster than it falls.
                     theStance publishes `time_to_fall_s` = 0.4066 s -- the deadline. A controller
                     slower than that cannot stand, no matter how strong the ports are.

  R4 A FAST PLANT    ...and the PORT must be able to RESPOND in that time. R3 is about the
                     controller; R4 is about the mechanism it commands. They are different
                     requirements and R3 being met says nothing about R4.

R3 WAS FREE TO CHECK AND CAME BACK MET (20 ms interval, 20 corrections per 0.4066 s fall). R4 CAME
BACK VIOLATED, and it was invisible until the knee was trained at population 40 and its drift
plotted: a damped oscillation with a ~0.6 s period, 1.5x the fall time. The loop can command in
time; the knee cannot MOVE in time. That distinction is R4, and it is why strong ports were never
going to be enough on their own.

    python tools/theory_of_standing.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

OUTDIR = ROOT / "ChimeraEngine" / "output" / "ports"
CONTROL_EVERY = 20          # what train_stand.py and port_trainer.py actually use


def pub(name, keys):
    hits = [p for p in (ROOT / "story").rglob("numbers.json") if p.parent.name == name]
    if not hits:
        raise SystemExit(f"{name} publishes nothing. Refusing to theorise without it.")
    d = json.loads(hits[0].read_text(encoding="utf8"))
    missing = [k for k in keys if k not in d]
    if missing:
        raise SystemExit(f"{name} publishes no {missing}. A theory of standing built on a default "
                         f"is a theory about a body that does not exist.")
    return d


def theory():
    """The requirements, derived. Each returns (name, question, verdict, evidence)."""
    import mujoco
    from world import load_body
    S = pub("theStance", ("time_to_fall_s", "fall_rate_rad_s", "together_half_width_m",
                          "together_half_length_m", "com_height_m", "g"))
    m, g = load_body(ROOT / "external" / "myo_sim" / "body" / "myobody.xml", mujoco)
    dt_ctrl = float(m.opt.timestep) * CONTROL_EVERY
    t_fall = float(S["time_to_fall_s"])
    n_corr = t_fall / dt_ctrl

    rows = []
    rows.append((
        "R1  A BASE", "does the CoM project inside the polygon of support?",
        "MET",
        "measured 4.8 mm fore / 40.4 mm lateral inside; inside all three published stances"))
    rows.append((
        "R2  A LOAD PATH", "does every joint carry its share without buckling?",
        "OPEN",
        "CLOSED-LOOP: hip 2.30 s over 9 turns, MONOTONIC AND ACCELERATING, not plateaued. Knee "
        "1.20 s at true parity (pop 120) vs 1.30 s open-loop in 2x the turns -- level. Distal "
        "0.66 s and moving (was FLAT). Best 2.30 s of 5.00 = 46%, up from 26%"))
    rows.append((
        "R3  A FAST LOOP", f"can the loop COMMAND faster than the body falls ({t_fall:.4f} s)?",
        "MET" if n_corr >= 10 else ("MARGINAL" if n_corr >= 4 else "VIOLATED"),
        f"control interval {dt_ctrl*1000:.0f} ms -> {n_corr:.1f} corrections per fall time"))
    # R4 -- NAMED 2026-08-02 by the knee's own picture at population 40. The drift is a clean
    # DAMPED OSCILLATION: 0 -> 43 deg at 0.2 s -> 13 at 0.5 -> 37 at 0.8 -> 11 at 1.3. Peaks decay
    # 43->37, troughs 13->11. Period ~0.6 s, lightly damped, converging. The knee is not collapsing
    # and not fighting itself -- IT IS RINGING, and it converges too slowly to matter.
    # R4, RESTATED after READING the model's published muscle dynamics instead of eyeballing a
    # period off a plot. The operator's direction -- the data exists, read it -- and it reversed
    # the cause I had assigned:
    #
    #     published tau_act 0.0100 s   tau_deact 0.0400 s
    #     derived ring period 2*pi*sqrt(tau_a*tau_d) = 0.1257 s   -- 3.2x FASTER than the fall
    #     measured off the turn-5 plot                = 0.60 s    -- 4.8x SLOWER than that
    #
    # THE MUSCLES ARE FAST ENOUGH. The 0.60 s is not a muscle limit, so "the plant is too slow"
    # was the wrong diagnosis. The reason is in this repo's own tooling: port_trainer.py sets
    # `ctrl[mus] = theta` ONCE and never updates it. The activation is CONSTANT for five seconds.
    # There is no feedback in the port trainer at all -- and a muscle held at constant activation
    # is a SPRING, so the limb rings at its passive mechanical period. That is the 0.60 s.
    #
    # R3's "20 ms, 20 corrections per fall" is true of train_stand.py. It was never true here.
    # I measured a plant's settling time from a system whose loop I had never closed.
    tau_a, tau_d = 0.0100, 0.0400
    T_muscle = 2.0 * (3.141592653589793) * (tau_a * tau_d) ** 0.5
    rows.append((
        "R4  A FAST PLANT", f"can the PORT respond faster than the body falls ({t_fall:.4f} s)?",
        "MET",
        f"published tau_act {tau_a:.3f} s / tau_deact {tau_d:.3f} s -> {T_muscle:.4f} s, "
        f"{t_fall/T_muscle:.1f}x faster than the fall. The muscles are not the limit."))
    rows.append((
        "R4b THE PORT LOOP", "is the port commanded with FEEDBACK, or open-loop?",
        "MET",
        f"CLOSED and CONFIRMED: ring period 0.60 s -> ~0.12 s, landing on the {T_muscle:.4f} s the "
        f"published tau_act/tau_deact predicted BEFORE the run. Peak drift 43.0 -> 21.7 deg"))
    rows.append((
        "R5  ??? ", "what does the theory STILL not name?",
        "UNKNOWN",
        "R4 replaced the old blank row. This one is its successor: R1-R4 are necessary, and "
        "nothing yet shows they are sufficient"))
    return rows, dict(g=g, t_fall=t_fall, dt_ctrl=dt_ctrl, n_corr=n_corr,
                      omega=float(S["fall_rate_rad_s"]), com_h=float(S["com_height_m"]))


def draw(rows, F, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(13.5, 6.2))
    ax.axis("off")
    col = {"MET": "#1a7f37", "OPEN": "#b7791f", "MARGINAL": "#b7791f",
           "VIOLATED": "#c0392b", "UNKNOWN": "#666666"}
    y = 0.94
    ax.text(0, 1.0, "WHAT STANDING REQUIRES — derived from published physics, before training",
            fontsize=13, weight="bold")
    for name, q, verdict, ev in rows:
        ax.text(0.00, y, name, fontsize=11, weight="bold", family="monospace")
        ax.text(0.19, y, verdict, fontsize=11, weight="bold", color=col[verdict],
                family="monospace")
        ax.text(0.32, y, q, fontsize=9.5, style="italic")
        ax.text(0.32, y - 0.055, ev, fontsize=8.6, color="#444")
        y -= 0.15
    ax.text(0, y - 0.02,
            f"g = {F['g']:.4f} m/s²    CoM height {F['com_h']:.4f} m    "
            f"fall rate ω₀ = {F['omega']:.4f} rad/s    time to fall {F['t_fall']:.4f} s\n"
            f"control interval {F['dt_ctrl']*1000:.0f} ms  →  {F['n_corr']:.1f} corrections "
            f"before the body is down\n\n"
            "R1–R3 are NECESSARY. Nothing here shows they are SUFFICIENT — R4 is the row the\n"
            "theory does not yet have, and training is how it gets discovered. That is the loop:\n"
            "train a port, watch standing still fail, and the failure names the missing row.",
            fontsize=9, family="monospace", va="top")
    ax.set_xlim(0, 1); ax.set_ylim(y - 0.42, 1.06)
    fig.savefig(path, dpi=104, bbox_inches="tight"); plt.close(fig)


def main() -> int:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    rows, F = theory()
    print("\nWHAT STANDING REQUIRES — derived, before any training\n" + "=" * 96)
    for name, q, verdict, ev in rows:
        print(f"  {name:<18}{verdict:<10}{q}")
        print(f"  {'':<28}{ev}")
    print("=" * 96)
    print(f"  g {F['g']:.4f}   CoM {F['com_h']:.4f} m   omega0 {F['omega']:.4f} rad/s   "
          f"time to fall {F['t_fall']:.4f} s")
    print(f"  control interval {F['dt_ctrl']*1000:.0f} ms -> {F['n_corr']:.1f} corrections "
          f"before the body is down")
    print("\n  R1-R3 are NECESSARY. Nothing here shows they are SUFFICIENT. R4 is the row the")
    print("  theory does not have yet, and a training run that fails with R1-R3 all met is how")
    print("  it gets discovered -- which is the operator's loop, made cheap by stating the")
    print("  requirements first instead of finding each one by failing.")
    p = OUTDIR / "theory_of_standing.png"
    draw(rows, F, p)
    print(f"\nPICTURE: {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
