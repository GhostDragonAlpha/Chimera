"""walk_dyad.py -- one TURN of walking: train a little, then LOOK, with a derived pass/fail.

WHY THIS EXISTS. On 2026-08-02 a six-hour training run was launched and killed twenty minutes in,
because it was hiding the thing it was supposed to reveal. The run before it had reported
`surv% = 92.8` while the body crouched at 13% of its target speed: the number designed to report
success reported success. A batch job is ONE TURN, and a turn nobody looks at cannot be corrected.

    core/dyad.py, first line:  "THE DRIVER. Two minds that drive development, turn by turn."

Every real finding in this project came from a turn ending and someone looking -- a `-9.81` on the
third line of a rollout, a knee 92.1% out of phase, an ankle demanding 15 deg of Earth push-off.
None came from a converging curve. So this module makes the looking mandatory and cheap:

    ONE TURN = train a short burst -> roll out -> MEASURE -> RENDER A PICTURE -> print what moved

THE STAGES ARE NOT A PARAMETER SWEEP (rule 1). Each asks a QUESTION the body can answer yes or no,
and every acceptance number is DERIVED -- read from what `theHuman` publishes, never chosen here:

    STAND   can it hold its own weight?          pelvis height vs the keyframe stand pose
    SHIFT   can it stand on ONE leg?             single-support fraction vs the published duty
    RHYTHM  does it repeat?                      footfall periodicity + period vs the pendulum
    SWING   does the swing leg follow the law?   hip/knee RMSE *and PHASE* vs the published envelope
    PUSH    does the ankle deliver toe-off?      ankle envelope, at the derived timing
    TRAVEL  does it move at the speed it derived? mean speed vs comfortable_speed_ms

A stage unlocks only when the one before it passes. That is a curriculum of QUESTIONS, not a search
over numbers: at no point does anything here ask "which value is best".

    python tools/walk_dyad.py --look                      # witness the current policy, no training
    python tools/walk_dyad.py --look --policy X.pt
    python tools/walk_dyad.py --look --secs 6 --seeds 3

Writes ChimeraEngine/output/dyad/turn_<n>.png (filmstrip + traces vs the derived envelope) and
turn_<n>.json (every measure). THE PNG IS THE POINT. If you did not open it, the turn did not end.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from world import load_body, gravity            # the ONE place gravity is decided

MYOBODY = ROOT / "external" / "myo_sim" / "body" / "myobody.xml"
OUTDIR = ROOT / "ChimeraEngine" / "output" / "dyad"
CONTROL_EVERY = 20
BODIES = {"pelvis": "pelvis", "calcn_r": "calcn_r", "calcn_l": "calcn_l",
          "toes_r": "toes_r", "toes_l": "toes_l"}


# ── THE LEDGER: every acceptance number below comes from here, none from taste ────────────────
def ledger() -> dict:
    hits = [p for p in (ROOT / "story").rglob("numbers.json") if p.parent.name == "theHuman"]
    if not hits:
        raise SystemExit("theHuman publishes nothing -- run `python story/grow.py`.")
    L = json.loads(hits[0].read_text(encoding="utf8"))
    need = ("g", "comfortable_speed_ms", "step_time_s", "duty_factor", "gait_envelope_deg")
    missing = [k for k in need if k not in L]
    if missing:
        raise SystemExit(f"theHuman publishes no {missing}. A default here would be this instrument "
                         f"inventing the gait it is meant to judge (rule 20). Refusing.")
    return L


def stages(L: dict) -> list:
    """The questions, in order, each with the DERIVED number that answers it."""
    stride = 2.0 * float(L["step_time_s"])
    return [
        dict(name="STAND", q="can it hold its own weight?",
             key="stand_frac", want=">= 0.90", note="of the keyframe stand height, sustained"),
        dict(name="SHIFT", q="can it put all its weight on ONE leg?",
             key="single_support_frac", want=f"~ {1 - 2*(1-float(L['duty_factor'])):.3f}",
             note="published duty_factor implies this much single support"),
        dict(name="RHYTHM", q="does it repeat?",
             key="periodicity", want=">= 0.60",
             note=f"and period ~ {stride:.4f} s, the leg as a compound pendulum at g={L['g']:.3f}"),
        dict(name="SWING", q="does the swing leg follow the law?",
             key="knee_phase_lag_pct", want="<= 10",
             note="RMSE is not enough -- the baseline sat inside +/-15 deg while 92.1% out of phase"),
        dict(name="PUSH", q="does the ankle deliver toe-off?",
             key="ankle_rmse_deg", want="<= 8",
             note="against theHuman's Froude-matched envelope, not CMU's Earth one"),
        dict(name="TRAVEL", q="does it move at the speed it derived for itself?",
             key="speed_ms", want=f"~ {float(L['comfortable_speed_ms']):.4f} m/s",
             note="held WHILE every stage above still passes"),
    ]


# ── THE ROLLOUT: the same contract policy_gait_eval uses, so the two agree ────────────────────
def build_ac(obs, act, hid, torch):
    import torch.nn as nn

    class AC(nn.Module):
        def __init__(s):
            super().__init__()
            s.body = nn.Sequential(nn.Linear(obs, hid), nn.Tanh(), nn.Linear(hid, hid), nn.Tanh())
            s.mean = nn.Linear(hid, act)
            s.log_std = nn.Parameter(torch.zeros(act))   # name matches the checkpoint's
            s.v = nn.Linear(hid, 1)

        def forward(s, o):
            h = s.body(o)
            mu = s.mean(h)
            return mu, s.log_std.exp().expand_as(mu), s.v(h)
    return AC()


def rollout(m, d, ac, torch, mujoco, secs, seed, obs_dim, cmd=0, frames=0):
    """One life. Returns traces + optional rendered frames -- the picture and the numbers together,
    from the SAME run, because a picture of a different rollout is not evidence about this one."""
    mujoco.mj_resetDataKeyframe(m, d, 0)
    nj = m.nq - 7
    d.qpos[7:] += np.random.default_rng(seed).normal(0, 0.03, nj)
    mujoco.mj_forward(m, d)
    stand_z = float(m.key_qpos[0][2])
    bid = {r: mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, n) for r, n in BODIES.items()}
    steps = int(secs / m.opt.timestep)
    grab = set(np.linspace(0, steps - 1, frames).astype(int)) if frames else set()

    ren = None
    if frames:
        ren = mujoco.Renderer(m, height=240, width=320)
    tr = {k: [] for k in ("z", "x", "vx", "hip_r", "knee_r", "ankle_r", "c_r", "c_l", "t")}
    pics, fell_at = [], None
    with torch.no_grad():
        for k in range(0, steps, CONTROL_EVERY):
            v = np.concatenate([d.qpos[3:7], d.qvel[3:6], d.qvel[0:3], d.qpos[7:], d.qvel[6:]])
            if obs_dim > v.size:
                oh = np.zeros(obs_dim - v.size)
                if oh.size != 4:
                    raise SystemExit(f"obs gap {oh.size}, not the 4-wide command one-hot. Refusing "
                                     f"to pad a shape this instrument does not understand.")
                oh[cmd] = 1.0
                v = np.concatenate([v, oh])
            ob = torch.tensor(np.nan_to_num(v), dtype=torch.float32).unsqueeze(0).clamp(-20, 20)
            mean, std, _ = ac(ob)
            a = (mean + std * torch.randn_like(std)).clamp(0.0, 1.0).squeeze(0).numpy()
            d.ctrl[:] = a
            for j in range(CONTROL_EVERY):
                mujoco.mj_step(m, d)
                i = k + j
                if i in grab and ren is not None:
                    ren.update_scene(d)
                    pics.append(ren.render().copy())
            tr["t"].append(k * m.opt.timestep)
            tr["z"].append(float(d.qpos[2])); tr["x"].append(float(d.qpos[0]))
            tr["vx"].append(float(d.qvel[0]))
            for role, arr in (("calcn_r", "c_r"), ("calcn_l", "c_l")):
                tr[arr].append(float(d.xpos[bid[role]][2]))
            hip, knee, ank = joint_angles(m, d, mujoco)
            tr["hip_r"].append(hip); tr["knee_r"].append(knee); tr["ankle_r"].append(ank)
            if fell_at is None and float(d.qpos[2]) < 0.6 * stand_z:
                fell_at = k * m.opt.timestep
    if ren is not None:
        ren.close()
    return tr, pics, fell_at, stand_z


def joint_angles(m, d, mujoco):
    """Sagittal hip/knee/ankle of the RIGHT leg, in degrees, from world segment vectors --
    the same convention tools/mocap_gait.py uses, so the comparison is apples to apples."""
    def p(n):
        return d.xpos[mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, n)]
    try:
        pel, fem, tib, cal, toe = p("pelvis"), p("femur_r"), p("tibia_r"), p("calcn_r"), p("toes_r")
    except Exception:
        return 0.0, 0.0, 0.0

    def ang(a, b):
        v = np.array([b[0] - a[0], b[2] - a[2]])
        return np.degrees(np.arctan2(v[0], -v[1]))
    def wrap(a):
        """TURN 0 FOUND THIS IN THIS FILE. Each `ang` is +/-180, so a difference of two of them
        spans +/-360 and `foot - shank - 90` spans +/-450 -- the first run reported an ANKLE AT
        -400 deg and an RMSE of 146.7. Those were the instrument, not the body. An angle that is
        not wrapped is not an angle (rule 24: an instrument needs an instrument)."""
        return (float(a) + 180.0) % 360.0 - 180.0
    thigh, shank, foot = ang(fem, tib), ang(tib, cal), ang(cal, toe)
    return wrap(thigh), wrap(thigh - shank), wrap(foot - shank - 90.0)


# ── THE MEASURES: what the picture must agree with ────────────────────────────────────────────
def measure(tr, fell_at, stand_z, L):
    z = np.array(tr["z"]); vx = np.array(tr["vx"]); t = np.array(tr["t"])
    cr, cl = np.array(tr["c_r"]), np.array(tr["c_l"])
    thr = min(cr.min(), cl.min()) + 0.02
    pr, pl = cr < thr, cl < thr
    both, either = pr & pl, pr | pl
    sig = pr.astype(float) - pl.astype(float)
    sig = sig - sig.mean()
    ac_ = np.correlate(sig, sig, "full")[len(sig) - 1:]
    ac_ = ac_ / (ac_[0] + 1e-9)
    lag = int(np.argmax(ac_[3:]) + 3) if len(ac_) > 4 else 0
    dt = float(t[1] - t[0]) if len(t) > 1 else 0.02
    env = L["gait_envelope_deg"]
    n = len(t)
    ph = (np.arange(n) * dt / (2 * float(L["step_time_s"]))) % 1.0
    idx = (ph * (len(env["hip"]) - 1)).astype(int)

    def rmse(sig_deg, name):
        return float(np.sqrt(np.mean((np.array(sig_deg) - np.array(env[name])[idx]) ** 2)))

    def phase_lag(sig_deg, name):
        a = np.array(sig_deg) - np.mean(sig_deg)
        b = np.array(env[name])[idx] - np.mean(np.array(env[name])[idx])
        if a.std() < 1e-6 or b.std() < 1e-6:
            return 100.0
        c = np.correlate(a, b, "full")
        return abs(int(np.argmax(c)) - (len(a) - 1)) / max(n, 1) * 100.0

    return {
        "stand_frac": float(z[-1] / stand_z),
        "stand_frac_min": float(z.min() / stand_z),
        # ONLY MEANINGFUL WHILE THE BODY IS UP. Turn 0 reported 0.985 single support for a body
        # lying on the floor: with the pelvis at 11% of stand height one "foot" clears the
        # threshold almost always. A support measure taken on a corpse is not a support measure.
        "single_support_frac": (float((either & ~both).sum() / max(either.sum(), 1))
                                if float(z.min() / stand_z) >= 0.5 else float("nan")),
        "double_support_frac": float(both.sum() / max(either.sum(), 1)),
        "periodicity": float(ac_[lag]) if lag else 0.0,
        "period_s": float(lag * dt),
        "knee_phase_lag_pct": phase_lag(tr["knee_r"], "knee"),
        "hip_rmse_deg": rmse(tr["hip_r"], "hip"),
        "knee_rmse_deg": rmse(tr["knee_r"], "knee"),
        "ankle_rmse_deg": rmse(tr["ankle_r"], "ankle"),
        "speed_ms": float(np.mean(vx)),
        "distance_m": float(tr["x"][-1] - tr["x"][0]),
        "survival_s": float(t[-1] if fell_at is None else fell_at),
        "fell": fell_at is not None,
    }


def verdict(mm, L):
    """PASS/FAIL per stage, against DERIVED numbers. The first FAIL is where the work is."""
    duty = float(L["duty_factor"])
    want_single = 1 - 2 * (1 - duty)
    stride = 2.0 * float(L["step_time_s"])
    v_want = float(L["comfortable_speed_ms"])
    out = []
    out.append(("STAND", mm["stand_frac_min"] >= 0.90, f"{mm['stand_frac_min']:.3f} of stand", ">= 0.900"))
    out.append(("SHIFT", abs(mm["single_support_frac"] - want_single) <= 0.10,
                f"{mm['single_support_frac']:.3f}", f"{want_single:.3f} +/- 0.10"))
    out.append(("RHYTHM", mm["periodicity"] >= 0.60 and abs(mm["period_s"] - stride) / stride <= 0.20,
                f"per {mm['periodicity']:.2f}, T {mm['period_s']:.3f}s", f">=0.60, T~{stride:.3f}s"))
    out.append(("SWING", mm["knee_phase_lag_pct"] <= 10.0,
                f"knee lag {mm['knee_phase_lag_pct']:.1f}%", "<= 10%"))
    out.append(("PUSH", mm["ankle_rmse_deg"] <= 8.0, f"{mm['ankle_rmse_deg']:.1f} deg", "<= 8 deg"))
    out.append(("TRAVEL", abs(mm["speed_ms"] - v_want) / v_want <= 0.15,
                f"{mm['speed_ms']:.3f} m/s", f"{v_want:.3f} +/- 15%"))
    return out


def draw(turn, tr, pics, mm, ver, L, path):
    """THE PICTURE. Filmstrip on top, the three joints against their derived envelope below."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    env = L["gait_envelope_deg"]
    ncol = max(len(pics), 1)
    fig = plt.figure(figsize=(max(12, 1.6 * ncol), 8.6))
    gs = fig.add_gridspec(3, 3, height_ratios=[1.25, 1, 1], hspace=0.42, wspace=0.22)
    if pics:
        strip = np.concatenate(pics, axis=1)
        ax = fig.add_subplot(gs[0, :]); ax.imshow(strip); ax.axis("off")
        ax.set_title(f"turn {turn} -- {len(pics)} frames across one derived stride "
                     f"({2*float(L['step_time_s']):.3f} s)  |  g = {L['g']:.4f} m/s^2", fontsize=10)
    dt = tr["t"][1] - tr["t"][0]
    ph = (np.arange(len(tr["t"])) * dt / (2 * float(L["step_time_s"]))) % 1.0
    for j, name in enumerate(("hip", "knee", "ankle")):
        ax = fig.add_subplot(gs[1, j])
        x = np.linspace(0, 1, len(env[name]))
        ax.plot(x, env[name], color="#1a7f37", lw=2.4, label="derived (theHuman)")
        ax.scatter(ph, tr[f"{name}_r"], s=4, alpha=0.45, color="#c0392b", label="the walker")
        ax.set_title(f"{name}   RMSE {mm[name+'_rmse_deg']:.1f} deg", fontsize=9)
        ax.set_xlabel("cycle"); ax.set_ylabel("deg")
        if j == 0:
            ax.legend(fontsize=7)
    ax = fig.add_subplot(gs[2, 0]); ax.plot(tr["t"], tr["z"], color="#2471a3")
    ax.set_title("pelvis height (m)", fontsize=9); ax.set_xlabel("s")
    ax = fig.add_subplot(gs[2, 1])
    ax.plot(tr["t"], tr["c_r"], label="R heel"); ax.plot(tr["t"], tr["c_l"], label="L heel")
    ax.set_title("foot height -- the footfall pattern", fontsize=9); ax.legend(fontsize=7)
    ax = fig.add_subplot(gs[2, 2]); ax.axis("off")
    rows = "\n".join(f"{'PASS' if ok else 'FAIL'}  {n:<7} {got:<22} want {want}"
                     for n, ok, got, want in ver)
    first = next((n for n, ok, *_ in ver if not ok), None)
    ax.text(0, 1, rows + f"\n\nTHE WORK IS AT: {first or 'nothing -- it walks'}",
            family="monospace", fontsize=8.5, va="top")
    fig.savefig(path, dpi=104, bbox_inches="tight")
    plt.close(fig)


def main() -> int:
    import torch
    import mujoco
    a = sys.argv
    pol = Path(a[a.index("--policy") + 1]) if "--policy" in a else \
        ROOT / "ChimeraEngine" / "output" / "myobody_walk_r5_policy.pt"
    secs = float(a[a.index("--secs") + 1]) if "--secs" in a else 5.0
    seeds = int(a[a.index("--seeds") + 1]) if "--seeds" in a else 1
    turn = int(a[a.index("--turn") + 1]) if "--turn" in a else 0
    OUTDIR.mkdir(parents=True, exist_ok=True)

    L = ledger()
    m, g = load_body(MYOBODY, mujoco)
    d = mujoco.MjData(m)
    meta = np.load(str(pol).replace("_policy.pt", "_meta.npy"), allow_pickle=True).item()
    OBS, HID, ACT = int(meta["OBS"]), int(meta["HID"]), int(meta["ACT"])
    ac = build_ac(OBS, ACT, HID, torch)
    sd = torch.load(pol, map_location="cpu", weights_only=False)
    ac.load_state_dict(sd.get("model", sd) if isinstance(sd, dict) else sd)
    ac.eval()

    print(f"\nTURN {turn}  --  {pol.name}   g = {g:.6f} m/s^2   {seeds} seed(s) x {secs}s")
    print(f"{'stage':<8}{'question':<44}{'measured':<24}{'derived want'}")
    print("-" * 104)
    runs = [rollout(m, d, ac, torch, mujoco, secs, s, OBS,
                    frames=(8 if s == 0 else 0)) for s in range(seeds)]
    tr, pics, fell, stand_z = runs[0]
    mm = measure(tr, fell, stand_z, L)
    if seeds > 1:                       # worst-of-N: one rollout is a coin toss
        for tr2, _, f2, sz2 in runs[1:]:
            m2 = measure(tr2, f2, sz2, L)
            if m2["survival_s"] < mm["survival_s"]:
                mm, tr = m2, tr2
    ver = verdict(mm, L)
    qs = {s["name"]: s["q"] for s in stages(L)}
    for n, ok, got, want in ver:
        print(f"{'PASS' if ok else 'FAIL':<8}{qs[n]:<44}{got:<24}{want}")
    first = next((n for n, ok, *_ in ver if not ok), None)
    print("-" * 104)
    print(f"survival {mm['survival_s']:.2f}s   distance {mm['distance_m']:+.3f} m   "
          f"fell={mm['fell']}")
    print(f"THE WORK IS AT: {first or 'nothing -- it walks'}")

    png = OUTDIR / f"turn_{turn:03d}.png"
    draw(turn, tr, pics, mm, ver, L, png)
    (OUTDIR / f"turn_{turn:03d}.json").write_text(
        json.dumps({"turn": turn, "policy": pol.name, "g": g, "measures": mm,
                    "verdict": [{"stage": n, "pass": ok, "got": got, "want": w}
                                for n, ok, got, w in ver]}, indent=2), encoding="utf8")
    print(f"\nPICTURE: {png}")
    print("THE TURN HAS NOT ENDED UNTIL YOU HAVE OPENED IT.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
