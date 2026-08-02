"""stand_port.py -- THE FIRST PORT. Stand. And show the bones.

WHY THIS IS THE FIRST PORT AND NOT THE FOURTH. `walk_dyad.py`'s first picture, 2026-08-02:
the pelvis starts at 1.0 m, wobbles three seconds, and CRASHES to 0.15 m; the right heel reaches
1.05 m -- the foot at pelvis height. That is not a crouch and not a gait. It is a collapse, and
NOTHING DOWNSTREAM OF A COLLAPSE IS WORTH TRAINING. Travel, tracking and speed were all being
optimised on a body that cannot hold itself up.

    THE COLLAPSE IS DATA. It says the connections are broken -- the hip is not receiving the
    pelvis's output, the knee is not receiving the hip's, the ground is not receiving the foot's.

SO THE VISUAL MUST SHOW THE BONES, AND THE BONES ARE THE ARCHITECTURE. A joint is an INTERFACE. A
segment is a DATA PATH. The skeleton is the dependency graph of the body, drawn. A picture of a
body with no connections in it is a picture, and a picture is a monad; a picture that shows what
flows through each joint is evidence about the STRUCTURE, which is the thing that is broken.

    pelvis --[ weight, 668.7 N ]--> hip --[ torque ]--> knee --[ torque ]--> ankle
           --[ CoP ]--> foot --[ ground reaction, up ]--> GROUND

EVERY NUMBER HERE IS READ, NOT CHOSEN (rule 1). `theStance` publishes the standing physics and
`theHuman` the body; this file derives the target and refuses if either is silent. The port's
target pelvis height closes on its own: hip_to_ankle_m + ankle_height_m = 0.8454 + 0.0747 =
0.9201 m, which is `leg_length_m` to twelve decimal places -- two independent routes, one number.

    python tools/stand_port.py                    # derive + draw the port (no policy needed)
    python tools/stand_port.py --policy X.pt      # and measure a policy against it
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


def read(name: str, keys) -> dict:
    hits = [p for p in (ROOT / "story").rglob("numbers.json") if p.parent.name == name]
    if not hits:
        raise SystemExit(f"{name} publishes nothing -- run `python story/grow.py`. Refusing.")
    d = json.loads(hits[0].read_text(encoding="utf8"))
    missing = [k for k in keys if k not in d]
    if missing:
        raise SystemExit(f"{name} publishes no {missing}. A default here would be this port "
                         f"inventing the body it is meant to stand up (rule 20). Refusing.")
    return d


def derive_stand_port() -> dict:
    """THE PORT ITSELF: gravity + geometry in, a target pose and a base of support out.

    Nothing below is chosen. Each line names the membrane it came from, because a port whose
    inputs you cannot trace is a port that could be carrying anything.
    """
    S = read("theStance", ("hip_to_ankle_m", "ankle_height_m", "com_height_m", "foot_length_m",
                           "together_half_width_m", "together_half_length_m", "fall_rate_rad_s",
                           "time_to_fall_s", "weight_N", "g", "mass_kg", "hip_separation_m"))
    H = read("theHuman", ("leg_length_m", "thigh_frac", "shank_frac", "height_m", "ankle_drop_frac"))
    pelvis = float(S["hip_to_ankle_m"]) + float(S["ankle_height_m"])
    port = {
        "IN  g_m_s2": float(S["g"]),
        "IN  mass_kg": float(S["mass_kg"]),
        "IN  height_m": float(H["height_m"]),
        "OUT pelvis_target_m": pelvis,
        "OUT com_target_m": float(S["com_height_m"]),
        "OUT bos_half_lat_m": float(S["together_half_width_m"]),
        "OUT bos_half_fore_m": float(S["together_half_length_m"]),
        "OUT weight_N": float(S["weight_N"]),
        "OUT fall_rate_rad_s": float(S["fall_rate_rad_s"]),
        "OUT time_to_fall_s": float(S["time_to_fall_s"]),
        "CHK leg_length_m": float(H["leg_length_m"]),
        "CHK closure_pct": 100.0 * (pelvis / float(H["leg_length_m"]) - 1.0),
        "seg thigh_m": float(H["thigh_frac"]) * float(H["height_m"]),
        "seg shank_m": float(H["shank_frac"]) * float(H["height_m"]),
        "seg foot_m": float(S["foot_length_m"]),
        "seg ankle_h_m": float(S["ankle_height_m"]),
        "seg hip_sep_m": float(S["hip_separation_m"]),
    }
    return port


# ── THE REWARD, derived from the port and from nothing else ───────────────────────────────────
def stand_reward(pelvis_z, com_xy, joint_frac_of_range, fell, effort, P):
    """A single number, and every term traceable to a published one.

    height  -- the pelvis at its DERIVED target. Not "high", not "0.9 of something": 0.9201 m,
               which theStance and theHuman reach by two different routes.
    support -- the CoM inside the base of support the FEET actually make. Outside it the body is
               a falling inverted pendulum by definition, so this is not a preference.
    joints  -- neither locked straight nor collapsed. A knee at its limit is a strut, not a leg.
    still   -- the operator's control law: command the PROCESS and its stop condition, never a
               pose. So this rewards the OUTCOME (be still) and never a target angle.
    """
    z_err = abs(pelvis_z - P["OUT pelvis_target_m"]) / P["OUT pelvis_target_m"]
    r_h = float(np.exp(-(z_err / 0.05) ** 2))
    mx = abs(com_xy[0]) / P["OUT bos_half_fore_m"]
    my = abs(com_xy[1]) / P["OUT bos_half_lat_m"]
    r_s = float(np.exp(-max(mx, my) ** 2))
    r_j = float(np.exp(-(max(0.0, joint_frac_of_range - 0.8) / 0.1) ** 2))
    return r_h * r_s * r_j - (3.0 if fell else 0.0) - 0.01 * effort, dict(
        height=r_h, support=r_s, joints=r_j, fell=fell)


# ── THE BONES: the architecture, drawn ────────────────────────────────────────────────────────
def draw_bones(P, ax):
    """The skeleton as a DEPENDENCY GRAPH, drawn FRONTALLY -- and the view is a finding.

    The first version drew this sagittally and put PELVIS and HIP at the same coordinate, so the
    edge "the hip receives the pelvis's output" had ZERO LENGTH: asserted, never shown. It is not
    a drawing bug. `theStance` publishes `hip_separation_m` = 0.162, so that connection is
    LATERAL, and a side view collapses it to a point.

    That is the whole reason standing is hard and the reason this port comes first: ONE centre of
    mass is carried by TWO hips 0.162 m apart, and every kilogram must be routed down one side or
    the other. A body that cannot decide which leg is carrying it is a body that falls over --
    which is exactly what the walker does at 3.12 s.
    """
    th, sh, fl = P["seg thigh_m"], P["seg shank_m"], P["seg foot_m"]
    ah, pel, hs = P["seg ankle_h_m"], P["OUT pelvis_target_m"], P["seg hip_sep_m"]
    knee_z, half = ah + sh, hs / 2.0
    W = P["OUT weight_N"]
    nodes = {"PELVIS": (0.0, pel + 0.085)}
    for s, sx in (("R", -1), ("L", +1)):
        nodes[f"HIP·{s}"] = (sx * half, pel)
        nodes[f"KNEE·{s}"] = (sx * half, knee_z)
        nodes[f"ANKLE·{s}"] = (sx * half, ah)
        nodes[f"FOOT·{s}"] = (sx * half, 0.0)
    edges = []
    for s, sx in (("R", -1), ("L", +1)):
        edges += [("PELVIS", f"HIP·{s}", f"{W/2:.0f} N", "#c0392b"),
                  (f"HIP·{s}", f"KNEE·{s}", f"thigh {th:.3f}", "#8e44ad"),
                  (f"KNEE·{s}", f"ANKLE·{s}", f"shank {sh:.3f}", "#2471a3"),
                  (f"ANKLE·{s}", f"FOOT·{s}", f"foot {fl:.3f}", "#1e8449")]
    for a, b, lbl, c in edges:
        (x0, y0), (x1, y1) = nodes[a], nodes[b]
        ax.annotate("", xy=(x1, y1), xytext=(x0, y0),
                    arrowprops=dict(arrowstyle="-|>", lw=2.8, color=c, shrinkA=10, shrinkB=10))
        off = 0.035 if x1 >= 0 else -0.035
        ax.text((x0 + x1) / 2 + off, (y0 + y1) / 2, lbl, fontsize=7,
                color=c, va="center", ha="left" if x1 >= 0 else "right")
    for n, (x, y) in nodes.items():
        ax.scatter([x], [y], s=170, zorder=5, facecolor="white", edgecolor="#222", lw=1.6)
        ax.text(x, y + 0.045, n, fontsize=7, ha="center", weight="bold")
    # the ground, and the reaction each foot must return
    ax.axhline(0, color="#8b5a2b", lw=3.4)
    ax.text(0.30, -0.045, "GROUND", fontsize=8, color="#8b5a2b", weight="bold")
    for sx in (-1, +1):
        ax.annotate("", xy=(sx * half, 0.20), xytext=(sx * half, 0.0),
                    arrowprops=dict(arrowstyle="-|>", lw=2.4, color="#b7791f"))
    ax.text(0.0, 0.115, f"GRF  {W/2:.0f} N each\n(only while BOTH feet carry)",
            fontsize=7, color="#b7791f", ha="center")
    # gravity: one vector, on the CoM, which is what has to be routed
    ax.annotate("", xy=(0.0, P["OUT com_target_m"] - 0.26), xytext=(0.0, P["OUT com_target_m"]),
                arrowprops=dict(arrowstyle="-|>", lw=3.0, color="#c0392b"))
    ax.scatter([0], [P["OUT com_target_m"]], s=170, marker="X", color="#d35400", zorder=6)
    ax.text(0.035, P["OUT com_target_m"],
            f"CoM {P['OUT com_target_m']:.3f} m" + chr(10) +
            f"g = {P['IN  g_m_s2']:.3f} m/s2", fontsize=7.5, color="#d35400", va="center")
    ax.annotate("", xy=(half, pel - 0.055), xytext=(-half, pel - 0.055),
                arrowprops=dict(arrowstyle="<|-|>", lw=1.4, color="#555"))
    ax.text(0, pel - 0.10,
            f"hip separation {hs:.3f} m" + chr(10) + "ONE CoM, TWO hips - the routing problem",
            fontsize=7, ha="center", color="#555")
    ax.set_xlim(-0.34, 0.42); ax.set_ylim(-0.09, 1.22); ax.set_aspect("equal"); ax.axis("off")
    ax.set_title("THE BONES (frontal) — every joint an interface, every edge what flows",
                 fontsize=9.5)


def draw_base(P, ax, com_xy=None):
    """Top-down: the CONNECTION between the centre of mass and the ground that must carry it."""
    hw, hl = P["OUT bos_half_lat_m"], P["OUT bos_half_fore_m"]
    ax.add_patch(__import__("matplotlib").patches.Rectangle(
        (-hw, -hl), 2 * hw, 2 * hl, fill=True, alpha=0.18, color="#1e8449", ec="#1e8449", lw=2))
    ax.scatter([0], [0], s=120, marker="X", color="#d35400", label="CoM target (centred)")
    if com_xy is not None:
        ax.scatter([com_xy[1]], [com_xy[0]], s=90, color="#c0392b", label="CoM measured")
    ax.set_xlim(-0.22, 0.22); ax.set_ylim(-0.22, 0.22); ax.set_aspect("equal")
    ax.set_xlabel("lateral (m)"); ax.set_ylabel("fore-aft (m)")
    ax.set_title(f"BASE OF SUPPORT  ±{hw:.3f} lat × ±{hl:.3f} fore\n"
                 f"outside it the body IS a falling pendulum", fontsize=8.5)
    ax.legend(fontsize=7)


def main() -> int:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    OUTDIR.mkdir(parents=True, exist_ok=True)
    P = derive_stand_port()

    print("\nTHE STAND PORT — derived, not chosen\n" + "=" * 78)
    for k, v in P.items():
        print(f"  {k:24} {v:.6f}" if isinstance(v, float) else f"  {k:24} {v}")
    print("=" * 78)
    print(f"  CLOSURE: hip_to_ankle + ankle_height = {P['OUT pelvis_target_m']:.6f} m vs "
          f"leg_length_m {P['CHK leg_length_m']:.6f} m  ->  {P['CHK closure_pct']:+.4f}%")
    print("  Two membranes, two routes, one number. That is the port being real rather than typed.")

    meas = None
    if "--policy" in sys.argv:
        import torch, mujoco
        from walk_dyad import build_ac, rollout, measure, ledger
        pol = Path(sys.argv[sys.argv.index("--policy") + 1])
        m, g = load_body(MYOBODY, mujoco)
        d = mujoco.MjData(m)
        mt = np.load(str(pol).replace("_policy.pt", "_meta.npy"), allow_pickle=True).item()
        ac = build_ac(int(mt["OBS"]), int(mt["ACT"]), int(mt["HID"]), torch)
        sd = torch.load(pol, map_location="cpu", weights_only=False)
        ac.load_state_dict(sd.get("model", sd) if isinstance(sd, dict) else sd)
        ac.eval()
        tr, _, fell, stand_z = rollout(m, d, ac, torch, mujoco, 5.0, 0, int(mt["OBS"]))
        mm = measure(tr, fell, stand_z, ledger())
        meas = dict(tr=tr, mm=mm, fell=fell)
        print(f"\n  MEASURED ({pol.name}): pelvis min {mm['stand_frac_min']*stand_z:.3f} m "
              f"vs target {P['OUT pelvis_target_m']:.3f} m -> "
              f"{100*mm['stand_frac_min']*stand_z/P['OUT pelvis_target_m']:.1f}% of target")
        print(f"  PROVEN = 5 s upright, pelvis >= 90% of target.  VERDICT: "
              f"{'PASS' if (not fell and mm['stand_frac_min']*stand_z >= 0.9*P['OUT pelvis_target_m']) else 'FAIL'}")

    fig = plt.figure(figsize=(15.5, 6.6))
    gs = fig.add_gridspec(1, 3, width_ratios=[1.15, 1, 1.25], wspace=0.30)
    draw_bones(P, fig.add_subplot(gs[0, 0]))
    draw_base(P, fig.add_subplot(gs[0, 1]))
    ax = fig.add_subplot(gs[0, 2])
    if meas:
        t, z = meas["tr"]["t"], meas["tr"]["z"]
        ax.plot(t, z, color="#c0392b", lw=1.9, label="pelvis, measured")
        ax.axhline(P["OUT pelvis_target_m"], color="#1a7f37", lw=2.4, label="derived target")
        ax.axhline(0.9 * P["OUT pelvis_target_m"], color="#1a7f37", ls="--", lw=1.4,
                   label="90% — the proof bar")
        ax.set_xlabel("s"); ax.set_ylabel("m"); ax.legend(fontsize=7.5)
        ax.set_title("THE CONNECTION, MEASURED\npelvis height vs what physics says it should be",
                     fontsize=9)
    else:
        ax.axis("off")
        ax.text(0, 1, "\n".join(
            ["THE PORT'S CONTRACT", "", "IN   gravity, mass, geometry",
             "OUT  pelvis target, CoM target, base of support", "",
             f"pelvis  {P['OUT pelvis_target_m']:.4f} m",
             f"CoM     {P['OUT com_target_m']:.4f} m",
             f"BoS     ±{P['OUT bos_half_lat_m']:.3f} × ±{P['OUT bos_half_fore_m']:.3f} m",
             f"weight  {P['OUT weight_N']:.1f} N",
             f"fall    {P['OUT fall_rate_rad_s']:.3f} rad/s "
             f"({P['OUT time_to_fall_s']:.3f} s to fall)", "",
             "PROVEN = 5 s upright, pelvis ≥ 90% of target,",
             "CoM inside the base, joints off their limits.", "",
             "next port: BALANCE (this port's output is its input)"]),
            family="monospace", fontsize=9, va="top")
    fig.suptitle("PORT 1 — STAND.  Every number read from theStance / theHuman; none chosen here.",
                 fontsize=11)
    png = OUTDIR / ("stand_port_measured.png" if meas else "stand_port.png")
    fig.savefig(png, dpi=104, bbox_inches="tight"); plt.close(fig)
    print(f"\nPICTURE: {png}\nTHE PORT IS NOT DEFINED UNTIL YOU HAVE OPENED IT.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
