"""f4_walk.py -- THE BODY WALKS THROUGH THE PARSER, or the walk membrane's falsifiers fire.

`docs/THE_SLICE.md` rung 3's successor: the musculoskeletal body WALKING on muscle control --
not a mover with gait playback, and not a black-box policy. MOVE is a formula registered in the
real parser (`tools/parser.py`), and its content is the STAND port plus one derived oscillator.

RULE 0 lives in `tools/walk_port.py`'s docstring, stated before the build. Restated here as the
three things this harness measures, because a falsifier that is not in the harness is a wish:

    1. TRAVEL      mean forward speed within 25% of theHuman's comfortable_speed_ms (0.9924 m/s)
    2. PERIODICITY footfall autocorrelation >= 0.60 -- a limit cycle, not a drift downfield
    3. UPRIGHT     pelvis >= 80% of the derived stand target for the whole run
    ABLATION       oscillator amplitudes forced to zero -> travel collapses below 20% of target

FALSIFIER 1 IS THE ONE THIS PROJECT HAS ALREADY BEEN CAUGHT BY. A distance is a receipt, and the
trainer hands you the same receipt for a walk, a bound, and a seizure that drifts downfield: the
celebrated 13.52-body-length walker scored PERIODICITY 0.25 -- no repeating cycle at all -- and
lost 5.5 body lengths to a one-micron nudge. Speed alone can never distinguish those, so speed
alone is not reported here without the cycle beside it.

FALSIFIER 2 IS THE ABLATION, AND IT RUNS THE SAME CODE. `gain=0.0` multiplies the oscillator
amplitudes out inside `walk_formula` itself -- it is not a second harness that could drift away
from the thing it ablates. A body that travels just as far with the oscillator off was falling
forward, and the rhythm proved nothing.

ZERO POSE-SCRIPTED FRAMES, BY CONSTRUCTION. After `seat_in_limits` at reset, nothing here writes
`d.qpos`. Every frame is `mj_step` under muscle control and this world's gravity.

    python tools/f4_walk.py           # exit 0 PASS, 1 FAIL
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from world import load_body                                              # noqa: E402
from stand_port import derive_stand_port, MYOBODY                        # noqa: E402
from train_stand import joint_ids, seat_in_limits, joint_frac_named      # noqa: E402
from classify_fall import classify_trace                                 # noqa: E402
from walk_port import (derive_walk_port, muscle_groups, move_formula_fn,  # noqa: E402
                       N_FREE)
from train_walk import foot_contact, CTRL_EVERY                          # noqa: E402
from chimera_gait import _periodicity                                    # noqa: E402
from parser import Parser, default_registry, Formula, EXCLUSIVE          # noqa: E402

OUTDIR = ROOT / "ChimeraEngine" / "output" / "ports"
STAND_THETA = OUTDIR / "stand_theta.npy"
WALK_THETA = OUTDIR / "walk_theta.npy"
SECS = 6.0                    # JUDGED at 6 s; train_walk optimises 8 s -- train past what you judge
SPEED_TOL = 0.25              # the prediction's own 25%
PERIODICITY_BAR = 0.60
UPRIGHT_FRAC = 0.80
ABLATION_BAR = 0.20


def run_one(m, d, mujoco, P, theta_stand, theta_walk, groups, tgt, nu, gain, frames=0):
    """One life THROUGH THE PARSER. `gain=0.0` is the ablation, same code path."""
    reg = default_registry(theta_stand, tgt, nu)
    # MOVE was a named Refusal ("no trained formula -- its atoms are M3"). This is the formula.
    reg["MOVE"] = Formula("MOVE", move_formula_fn(theta_stand, theta_walk, groups, tgt, nu, P,
                                                  gain=gain), EXCLUSIVE)
    PARSER = Parser(reg)
    PARSER.set_verb("MOVE", True)

    jids = joint_ids(m, mujoco)
    mujoco.mj_resetDataKeyframe(m, d, 0)
    mujoco.mj_forward(m, d)
    seat_in_limits(m, d, mujoco, jids)
    steps = int(SECS / m.opt.timestep)
    grab = set(np.linspace(0, steps - 1, frames).astype(int)) if frames else set()
    ren = mujoco.Renderer(m, height=240, width=320) if frames else None
    # `all` / `jf` / `jn` carry the PER-JOINT diagnostic ported from f3_stand.py (2026-08-04).
    # comx/comy/polx/poly carry the CoM against the polygon the feet make, so classify_fall can
    # label the failure. Both exist for the same reason: F4 used to return a bare scalar per
    # falsifier, and a scalar that moves for reasons you cannot attribute is the shape of
    # measurement this project keeps getting caught by. A walk that fails now names the joints
    # it failed at and which way it went down.
    tr = {k: [] for k in ("t", "x", "z", "cr", "cl", "sup", "jf", "jn", "all",
                          "comx", "comy", "polx", "poly")}
    pics, fell_t, x0, driver = [], None, float(d.qpos[0]), None
    _b = lambda n: d.xpos[mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, n)]
    for k in range(steps):
        if k % CTRL_EVERY == 0:
            z = float(d.qpos[2])
            q = d.qpos[3:7]
            pitch = float(np.arctan2(2 * (q[0] * q[2] - q[3] * q[1]),
                                     1 - 2 * (q[1] ** 2 + q[2] ** 2)))
            u, trace = PARSER.command({"z": z, "pitch": pitch, "t": float(d.time)})
            driver = trace.driver
            if u is not None:
                d.ctrl[:] = u
        mujoco.mj_step(m, d)
        if k in grab and ren is not None:
            ren.update_scene(d); pics.append(ren.render().copy())
        if k % CTRL_EVERY == 0:
            z = float(d.qpos[2])
            cr, cl = foot_contact(m, d, mujoco)
            tr["t"].append(k * m.opt.timestep); tr["x"].append(float(d.qpos[0]))
            tr["z"].append(z); tr["cr"].append(cr); tr["cl"].append(cl)
            tr["sup"].append((1.0 if cr > 0 else 0.0) + (1.0 if cl > 0 else 0.0))
            _jf, _jn = joint_frac_named(d, jids)
            tr["jf"].append(_jf); tr["jn"].append(_jn)
            # EVERY joint, every sample -- not just the worst. f3_stand.py's own note: recording
            # only the argmax and then asking "how bad was joint X" by filtering the samples
            # where X happened to be worst overall answers a different question and always
            # understates. A joint at 1.08 under another at 1.10 is invisible to it.
            tr["all"].append({n: abs(float(d.qpos[adr]) - c) / h for adr, c, h, n in jids})
            com = d.subtree_com[0]
            foot = 0.25 * (_b("calcn_r") + _b("calcn_l") + _b("toes_r") + _b("toes_l"))
            _px = [float(_b(n)[0]) for n in ("calcn_r", "calcn_l", "toes_r", "toes_l")]
            _py = [float(_b(n)[1]) for n in ("calcn_r", "calcn_l", "toes_r", "toes_l")]
            tr["comx"].append(float(com[0] - foot[0]))
            tr["comy"].append(float(com[1] - foot[1]))
            tr["polx"].append(max(1e-9, 0.5 * (max(_px) - min(_px))))
            tr["poly"].append(max(1e-9, 0.5 * (max(_py) - min(_py))))
            if z < 0.5 * tgt and fell_t is None:
                fell_t = k * m.opt.timestep
                break
    if ren is not None:
        ren.close()
    dt_s = CTRL_EVERY * m.opt.timestep
    per, period = _periodicity(np.array(tr["sup"]), dt_s) if len(tr["sup"]) > 16 else (0.0, 0.0)
    elapsed = max(tr["t"][-1], 1e-9) if tr["t"] else 1e-9
    # PER-JOINT PEAK AND TIME-OVER-STOP, the diagnostic f3_stand.py already carries. `over` is
    # the one the ligament membranes are written in: a peak says a joint touched its stop, the
    # FRACTION says whether anything caught it. A ligament that engages late still shows a peak;
    # what says it CAUGHT the joint is the joint coming back inside.
    names = sorted(tr["all"][0]) if tr["all"] else []
    nsamp = max(len(tr["all"]), 1)
    peak = {n: max((s[n] for s in tr["all"]), default=0.0) for n in names}
    over = {n: 100.0 * sum(1 for s in tr["all"] if s[n] >= 1.0) / nsamp for n in names}
    return dict(speed=(float(tr["x"][-1]) - x0) / elapsed if tr["x"] else 0.0,
                periodicity=per, period_s=period, fell_t=fell_t, driver=driver,
                z_min=min(tr["z"]) if tr["z"] else 0.0, held=elapsed,
                duty_r=float(np.mean([c > 0 for c in tr["cr"]])) if tr["cr"] else 0.0,
                duty_l=float(np.mean([c > 0 for c in tr["cl"]])) if tr["cl"] else 0.0,
                jmax=max(tr["jf"]) if tr["jf"] else 0.0,
                jworst=(max(zip(tr["jf"], tr["jn"]))[1] if tr["jf"] else "?"),
                peak=peak, over=over,
                fall=classify_trace(tr, tgt) if tr["t"] else None,
                tr=tr, pics=pics)


def run() -> int:
    import mujoco
    if not WALK_THETA.exists():
        raise SystemExit(f"no {WALK_THETA} -- run `python tools/train_walk.py` first. Refusing to "
                         f"judge a walk that was never trained (rule 20).")
    if not STAND_THETA.exists():
        raise SystemExit(f"no {STAND_THETA} -- walking is composed over standing. Refusing.")
    theta_stand, theta_walk = np.load(STAND_THETA), np.load(WALK_THETA)
    P, S = derive_walk_port(), derive_stand_port()
    m, g = load_body(MYOBODY, mujoco)
    d = mujoco.MjData(m)
    groups = muscle_groups(m, d, mujoco)
    tgt, nu = S["OUT pelvis_target_m"], m.nu
    vt = P["OUT target_speed_ms"]

    live = run_one(m, d, mujoco, P, theta_stand, theta_walk, groups, tgt, nu, 1.0, frames=8)
    abl = run_one(m, d, mujoco, P, theta_stand, theta_walk, groups, tgt, nu, 0.0)

    pct = 100.0 * live["speed"] / vt
    abl_pct = 100.0 * abl["speed"] / vt
    ok_travel = abs(live["speed"] - vt) <= SPEED_TOL * vt
    ok_cycle = live["periodicity"] >= PERIODICITY_BAR
    ok_up = live["z_min"] >= UPRIGHT_FRAC * tgt and live["fell_t"] is None
    ok_abl = abs(abl["speed"]) < ABLATION_BAR * vt
    ok = ok_travel and ok_cycle and ok_up and ok_abl

    print("\nF4 -- THE BODY WALKS THROUGH THE PARSER")
    print("=" * 78)
    print(f"  world: g = {g:.4f} m/s2 (theHuman, via load_body -- never assumed)")
    print(f"  parser driver: {live['driver']}   (MOVE was a named Refusal until this rung)")
    print(f"  DERIVED, not searched: omega {P['OUT omega_rad_s']:.4f} rad/s "
          f"(stride {P['OUT stride_s']:.4f} s), antiphase pi, target {vt:.4f} m/s")
    # N_FREE, not a re-derived `2*len(OSC_JOINTS)`: that expression was correct until the
    # oscillator gained eps and kappa, and then it silently reported 6 for an 8-number search.
    # An instrument that recomputes a fact instead of reading it will disagree with the thing
    # it measures the moment the thing changes.
    print(f"  free numbers trained: {N_FREE} ({theta_walk.size} on disk)  |  stand theta FROZEN "
          f"({theta_stand.size} numbers, reused unchanged)")
    if theta_walk.size != N_FREE:
        raise SystemExit(f"walk_theta.npy holds {theta_walk.size} numbers, the port declares "
                         f"{N_FREE}. Refusing to judge a walk against a theta of the wrong shape.")
    print("-" * 78)
    print(f"  1. TRAVEL       {live['speed']:+.4f} m/s = {pct:.0f}% of derived "
          f"(bar {100*(1-SPEED_TOL):.0f}-{100*(1+SPEED_TOL):.0f}%)  ->  "
          f"{'PASS' if ok_travel else 'FAIL'}")
    print(f"  2. PERIODICITY  {live['periodicity']:.2f} (bar >= {PERIODICITY_BAR:.2f}), "
          f"period {live['period_s']:.2f} s vs derived stride {P['OUT stride_s']:.2f} s  ->  "
          f"{'PASS' if ok_cycle else 'FAIL'}")
    print(f"  3. UPRIGHT      pelvis MIN {live['z_min']:.4f} m = "
          f"{100*live['z_min']/tgt:.0f}% of target (bar {100*UPRIGHT_FRAC:.0f}%), held "
          f"{live['held']:.2f}/{SECS:.1f} s  ->  {'PASS' if ok_up else 'FAIL'}")
    print(f"     duty R/L {live['duty_r']:.2f}/{live['duty_l']:.2f} "
          f"(theHuman publishes {P['OUT duty_factor']:.2f})")
    print(f"  4. ABLATION     oscillator OFF (gain=0, same code path): "
          f"{abl['speed']:+.4f} m/s = {abl_pct:.0f}% of derived")
    print(f"     bar: must stay under {100*ABLATION_BAR:.0f}%  ->  "
          f"{'PASS -- the rhythm is doing the work' if ok_abl else 'FAIL -- it travels without the oscillator; the rhythm is decorative'}")
    # ── WHICH JOINTS, AND WHICH WAY IT WENT DOWN (ported from f3_stand.py, 2026-08-04) ──────
    # F4 used to return a bare scalar per falsifier. A walk that fails now NAMES its offenders,
    # because "periodicity 0.22" tells you the gait is not a gait and nothing about what to fix.
    print(f"  5. JOINTS       worst {live['jmax']:.2f} of range at {live['jworst']}"
          + ("  (< 1.00, none through a stop)" if live['jmax'] < 1.0 else "  -- THROUGH ITS STOP"))
    _off = sorted(((n, v) for n, v in live["peak"].items() if v >= 0.90), key=lambda p: -p[1])
    if _off:
        print(f"     per joint, peak and % of the run spent at/past the stop:")
        for _n, _v in _off[:6]:
            print(f"       {_n:22} peak {_v:.2f}   over {live['over'][_n]:5.1f}% of the run")
    else:
        print(f"     no joint reached 0.90 of its range")
    if live["fall"] is not None:
        _f = live["fall"]
        print(f"  6. THE FALL     {_f['label'].upper()}"
              + (f" at t={_f['t_fall']:.2f} s, confidence {_f['confidence']:.2f}"
                 if _f['t_fall'] is not None else " -- did not fall")
              + f"   (CoM peak: fore {_f.get('peak_fore_frac', 0):.2f}, "
                f"lat {_f.get('peak_lat_frac', 0):.2f} of the base the feet make)")
        if _f["confidence"] < 0.35 and _f["t_fall"] is not None:
            print(f"     LOW CONFIDENCE -- both axes left the base together, so this is a "
                  f"diagonal/tumbling fall, not a clean {_f['label']} one. Reported as the "
                  f"weak separation it is rather than as a label that reads clean.")
    print(f"  qpos writes after reset: 0 (by construction -- the harness contains no write)")
    print("=" * 78)
    print(f"  F4 VERDICT: {'PASS -- the body walks' if ok else 'FAIL'}")
    if not ok:
        which = [n for n, v in (("1 TRAVEL", ok_travel), ("2 PERIODICITY", ok_cycle),
                                ("3 UPRIGHT", ok_up), ("4 ABLATION", ok_abl)) if not v]
        print(f"  FIRED: {', '.join(which)}")
        if not ok_cycle and ok_travel:
            print("    speed reached WITHOUT a cycle -- this is falsifier 1 exactly: it arrives,")
            print("    it does not walk. The 13.52-body-length champion scored 0.25 here.")
        if not ok_abl:
            print("    the ablation travelled too -- the body is falling forward and the")
            print("    oscillator proved nothing (a primitive whose ablation passes proved nothing).")

    # ---- THE PICTURE ------------------------------------------------------
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig = plt.figure(figsize=(15.0, 7.4))
    gs = fig.add_gridspec(2, 3, height_ratios=[1.05, 1], hspace=0.4, wspace=0.28)
    if live["pics"]:
        ax = fig.add_subplot(gs[0, :]); ax.imshow(np.concatenate(live["pics"], axis=1))
        ax.axis("off")
        ax.set_title("eight frames: MOVE held, walking on muscle control", fontsize=10)
    t = live["tr"]["t"]
    ax = fig.add_subplot(gs[1, 0])
    ax.plot(t, live["tr"]["x"], color="#c0392b", lw=2.0, label="walked")
    ax.plot(abl["tr"]["t"], abl["tr"]["x"], color="#7f8c8d", lw=1.6, ls="-.",
            label="ABLATION (oscillator off)")
    ax.plot(t, [vt * s for s in t], color="#1a7f37", ls="--", lw=1.4, label=f"derived {vt:.3f} m/s")
    ax.set_xlabel("s"); ax.set_ylabel("m"); ax.legend(fontsize=7)
    ax.set_title(f"TRAVEL -- {live['speed']:.3f} m/s ({pct:.0f}%) vs ablation "
                 f"{abl['speed']:.3f} ({abl_pct:.0f}%)", fontsize=9)
    ax = fig.add_subplot(gs[1, 1])
    ax.step(t, [c > 0 for c in live["tr"]["cr"]], color="#c0392b", lw=1.4, where="post", label="R")
    ax.step(t, [1.3 if c > 0 else 0.3 for c in live["tr"]["cl"]], color="#2471a3", lw=1.4,
            where="post", label="L")
    ax.set_ylim(-0.3, 1.9); ax.set_xlabel("s"); ax.legend(fontsize=7)
    ax.set_title(f"FOOTFALL -- periodicity {live['periodicity']:.2f} "
                 f"(bar {PERIODICITY_BAR:.2f}), period {live['period_s']:.2f} s", fontsize=9)
    ax = fig.add_subplot(gs[1, 2])
    ax.plot(t, live["tr"]["z"], color="#8e44ad", lw=1.6)
    ax.axhline(tgt, color="#1a7f37", lw=2.0, label=f"stand target {tgt:.3f} m")
    ax.axhline(UPRIGHT_FRAC * tgt, color="#1a7f37", ls="--", lw=1.2,
               label=f"{100*UPRIGHT_FRAC:.0f}% -- the bar")
    ax.set_xlabel("s"); ax.set_ylabel("m"); ax.legend(fontsize=7)
    ax.set_title(f"UPRIGHT -- pelvis MIN {100*live['z_min']/tgt:.0f}% of target", fontsize=9)
    fig.suptitle(f"F4 -- WALK THROUGH THE PARSER   g={g:.3f} m/s2   "
                 f"{'PASS' if ok else 'FAIL'}   speed {pct:.0f}%  periodicity "
                 f"{live['periodicity']:.2f}  ablation {abl_pct:.0f}%", fontsize=12)
    OUTDIR.mkdir(parents=True, exist_ok=True)
    png = OUTDIR / "f4_walk.png"
    fig.savefig(png, dpi=100, bbox_inches="tight"); plt.close(fig)
    print(f"  PICTURE: {png}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(run())
