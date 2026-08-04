"""grab_load_path.py -- IS THE CARRIED STONE'S WEIGHT ACTUALLY ROUTED THROUGH THE BODY?

RULE 0, stated before the run:

    STATEMENT   On GRAB, the stone's weight is carried by the same legs that were holding the
                body up, so the pelvis must SAG -- and the sag is not a decoration, it is what
                a compliant column does under load. The stand formula's height channel
                `a0 + kh*(tgt - z)` is a proportional spring: in steady state the extra muscle
                force must equal the added weight, so `dz = W / k_eff` with `k_eff` a property
                of the body and the policy, not of the stone. The pelvis recovers on release.

    PREDICTION  Three clauses, and the second is the one that can fail honestly:
                (a) sag is LINEAR in carried mass -- r^2 >= 0.90 over the mass response curve;
                (b) `k_eff` calibrated on a KNOWN VERTICAL FORCE AT THE PELVIS predicts the
                    welded stone's sag OUT OF SAMPLE, within a factor of two;
                (c) 10-seed median stand survival is SHORTER loaded than unloaded.

    FALSIFIER   No measurable load effect -- the loaded sag is inside the unloaded run's own
                jitter -- in which case the load path is DECORATIVE: the weld holds the stone
                and the body never learns it is carrying anything. Record and stop.

THE MASS CURVE IS A RESPONSE, NOT A SWEEP (rule 1). A sweep is forbidden when it asks "which
number is best" -- there is no best mass here and nothing is being chosen. Measuring dz at
several masses is how you test that the response is a straight line, which is what "a spring"
MEANS; the derivation predicts the SHAPE and the calibration sets the level.

AND THE CALIBRATION IS A CONTROL, in this project's own sense: a KNOWN subject pushed through
the whole instrument. `k_eff` is measured with a pure vertical force on the pelvis -- a thing
we made, of a size we chose -- and is then asked to predict a DIFFERENT experiment, a stone
welded to the torso 0.40 m forward. If it predicts that, the sag is the load path. If it does
not, the disagreement is the finding and gets published (rule 17), because the stone's offset
puts a moment on the trunk that a pure vertical force never applies.

    python tools/grab_load_path.py [--seeds 10] [--theta stand_theta.npy]
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
from grab_port import (derive_grab_port, stone_xml, spawn_stone,  # noqa: E402
                       snap_stone_to_carry, support_stone_weight, weld_load,
                       RAMP_S, STONE_BODY, WELD_NAME)

OUTDIR = ROOT / "ChimeraEngine" / "output" / "ports"
LOGDIR = ROOT / "agent_logs"
THETA = OUTDIR / "stand_theta.npy"
T_GRAB = 2.0      # the grab instant: late enough that the keyframe's settle is over (f3 shows
                  # the CoM settled by ~1 s), early enough to leave a carry inside the stand's
                  # own survival. Not tuned -- moved once would be a different experiment.
T_REL = 5.0       # the release, 3.0 s of carry later
SECS = 8.0


def run(m, d, mujoco, theta, P, jids, seed, mass_scale=None, pelvis_force_N=0.0,
        grab=True, secs=SECS):
    """One life. `mass_scale` scales the stone; `pelvis_force_N` is the calibration probe.

    The two loads are applied by the SAME mechanism the carry already uses -- `xfrc_applied`
    and the weld -- so the calibration and the measurement are not two different physics.
    """
    tgt, nu = P["OUT pelvis_target_m"], m.nu
    PARSER = Parser(default_registry(theta, tgt, nu))
    PARSER.set_verb("STAND", True)
    sid = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, STONE_BODY)
    eq = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_EQUALITY, WELD_NAME)
    pid = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, "pelvis")
    # THE MASS IS SET BEFORE THE RESET, and that ordering is a bug this file paid for.
    # `mj_setConst` recomputes the model's constants FOR THE qpos0 CONFIGURATION and USES `d`
    # AS ITS SCRATCH -- it overwrites the state. Called after `mj_resetDataKeyframe`,
    # `spawn_stone` and `seat_in_limits`, it silently threw all three away and started the body
    # from qpos0: unseated, outside its own joint limits, falling at 1.64 s instead of 3.44 s.
    # MEASURED, not reasoned about: `mass_scale=1.0` -- the SAME mass the unscaled path uses --
    # gave 1.64 s where `mass_scale=None` gave 3.44 s. Identical physics, different survival,
    # so the difference was in the call and not in the body. (`grab_port` had already moved off
    # this pattern for its own reasons: v10's `support_stone_weight` keeps the mass constant and
    # applies a force, precisely to stop touching the model mid-run.)
    if sid >= 0 and mass_scale is not None:
        m.body_mass[sid] = _FULL_MASS[0] * mass_scale
        m.body_inertia[sid] = _FULL_INERTIA[0] * mass_scale
        mujoco.mj_setConst(m, d)
    mujoco.mj_resetDataKeyframe(m, d, 0)
    mujoco.mj_forward(m, d)
    seat_in_limits(m, d, mujoco, jids)
    if sid >= 0:
        spawn_stone(m, d, mujoco, derive_grab_port())
        d.eq_active[eq] = 0
    if seed:
        d.qpos[:] = d.qpos + np.random.default_rng(seed).normal(0.0, NUDGE, size=d.qpos.shape)
    mujoco.mj_forward(m, d)
    steps = int(secs / m.opt.timestep)
    tr = {k: [] for k in ("t", "z", "wl", "held")}
    snapped = False
    for k in range(steps):
        t = k * m.opt.timestep
        if grab and sid >= 0 and not snapped and t >= T_GRAB:
            snap_stone_to_carry(m, d, mujoco)
            d.eq_active[eq] = 1
            snapped = True
        if snapped:
            if t < T_REL:
                # the giver's hands let go over RAMP_S -- the port's own arrival window
                support_stone_weight(m, d, mujoco, min(1.0, (t - T_GRAB) / RAMP_S))
            else:
                # THE RELEASE: the giver takes the weight back, then the weld opens
                f = max(0.0, 1.0 - (t - T_REL) / RAMP_S)
                support_stone_weight(m, d, mujoco, f)
                if t >= T_REL + RAMP_S and int(d.eq_active[eq]):
                    d.eq_active[eq] = 0
                    d.xfrc_applied[sid] = np.zeros(6)
        if pelvis_force_N and t >= T_GRAB:
            # THE CALIBRATION PROBE: a pure vertical force, DOWN, on the pelvis. No moment, no
            # offset, nothing the body could confuse with a stone -- which is the point.
            d.xfrc_applied[pid] = [0.0, 0.0, -pelvis_force_N, 0.0, 0.0, 0.0]
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
            tr["t"].append(t)
            tr["z"].append(float(d.qpos[2]))
            tr["wl"].append(weld_load(m, d, mujoco) if sid >= 0 else 0.0)
            if float(d.qpos[2]) < 0.5 * tgt:
                break
    tr["survived"] = tr["t"][-1] if tr["t"] else 0.0
    tr["fell"] = bool(tr["z"] and tr["z"][-1] < 0.5 * tgt)
    return tr


MIN_WINDOW_S = 0.20     # a window shorter than this is not a measurement of a held state


def window_mean(tr, t0, t1, dt=0.02):
    """Mean pelvis height over [t0, t1), or nan if the body was not THERE for enough of it.

    THE GUARD IS THE POINT, and it was added after the first run returned three nans and one
    contaminated number (2026-08-04). At full stone mass the body FALLS DURING THE CARRY, so a
    window running to `T_REL` averages a collapse and calls it a sag. A mean over two samples of
    a body on its way down is not a steady state; it is the fall, misnamed. So: samples inside
    the window are counted, and fewer than `MIN_WINDOW_S` worth returns nan rather than a
    number that reads like a measurement.
    """
    v = [z for t, z in zip(tr["t"], tr["z"]) if t0 <= t < t1]
    return float(np.mean(v)) if len(v) * dt >= MIN_WINDOW_S else float("nan")


def settle_mean(tr, t0, dt=0.02):
    """The pelvis over the FIRST `MIN_WINDOW_S` after `t0` -- the closest thing to a held state.

    Reported beside the full-window mean because they answer different questions: this one is
    the elastic sag under the arrived load, the other includes however much of the collapse the
    window caught. Publishing both is what stops the second silently standing in for the first.
    """
    v = [z for t, z in zip(tr["t"], tr["z"]) if t0 <= t < t0 + MIN_WINDOW_S]
    return float(np.mean(v)) if len(v) * dt >= MIN_WINDOW_S - 1e-9 else float("nan")


_FULL_MASS, _FULL_INERTIA = [0.0], [None]


def main() -> int:
    import mujoco
    a = sys.argv
    nseeds = int(a[a.index("--seeds") + 1]) if "--seeds" in a else 10
    tp = Path(a[a.index("--theta") + 1]) if "--theta" in a else THETA
    if not tp.is_absolute():
        tp = OUTDIR / tp.name
    if not tp.exists():
        raise SystemExit(f"no {tp} -- refusing to load a body that cannot stand (rule 20).")
    theta = np.load(tp)
    P, G = derive_stand_port(), derive_grab_port()
    xml = stone_xml(MYOBODY, G)
    m, g = load_body(xml, mujoco)
    d = mujoco.MjData(m)
    jids = joint_ids(m, mujoco)
    sid = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, STONE_BODY)
    _FULL_MASS[0] = float(m.body_mass[sid])
    _FULL_INERTIA[0] = m.body_inertia[sid].copy()
    W_stone = _FULL_MASS[0] * abs(float(m.opt.gravity[2]))

    print(f"\nTHE GRAB LOAD PATH -- {tp.name}, g {g:.4f} m/s2")
    print("=" * 100)
    print(f"  stone {_FULL_MASS[0]:.3f} kg -> {W_stone:.2f} N, "
          f"{100*G['OUT load_frac_of_body']:.1f}% of the {G['OUT body_mass_kg']:.2f} kg body")
    print(f"  grab at {T_GRAB:.1f} s, release at {T_REL:.1f} s, arrival window {RAMP_S:.1f} s, "
          f"run {SECS:.1f} s")

    # ── THE UNLOADED CONTROL, and its own jitter ───────────────────────────────────────────
    base = [run(m, d, mujoco, theta, P, jids, s, grab=False) for s in range(nseeds)]
    z_base = np.array([settle_mean(t, T_GRAB + RAMP_S) for t in base])
    jitter = float(np.nanmax(z_base) - np.nanmin(z_base))
    surv_base = np.array([t["survived"] for t in base])
    print("-" * 100)
    print(f"  UNLOADED CONTROL ({nseeds} seeds): pelvis over the carry window "
          f"{np.nanmean(z_base):.5f} m, seed-to-seed jitter {1000*jitter:.2f} mm")
    print(f"                    survival median {np.median(surv_base):.2f} s "
          f"(min {surv_base.min():.2f}, max {surv_base.max():.2f})")

    # ── THE CALIBRATION: a KNOWN vertical force on the pelvis ──────────────────────────────
    # Sizes bracket the stone's weight so the probe and the prediction live in one regime; a
    # stiffness read far from the load it is asked about is a stiffness read on a different body.
    probes = [0.25 * W_stone, 0.5 * W_stone, W_stone]
    print(f"  CALIBRATION -- a pure vertical force on the PELVIS, seed 0, no stone:")
    print(f"     {'force N':>10}{'pelvis m':>12}{'sag mm':>10}{'k N/m':>12}")
    ks = []
    for F in probes:
        t = run(m, d, mujoco, theta, P, jids, 0, pelvis_force_N=F, grab=False)
        z = settle_mean(t, T_GRAB + RAMP_S)
        sag = z_base[0] - z
        k = F / sag if sag > 1e-9 else float("nan")
        ks.append(k)
        print(f"     {F:>10.2f}{z:>12.5f}{1000*sag:>10.2f}{k:>12.1f}")
    k_eff = float(np.nanmedian(ks))
    dz_pred = W_stone / k_eff if k_eff > 0 else float("nan")
    print(f"     -> k_eff (median) {k_eff:.1f} N/m; PREDICTED stone sag "
          f"{1000*dz_pred:.2f} mm at {W_stone:.2f} N")

    # ── THE MEASUREMENT: the welded stone ──────────────────────────────────────────────────
    load = [run(m, d, mujoco, theta, P, jids, s) for s in range(nseeds)]
    z_load = np.array([settle_mean(t, T_GRAB + RAMP_S) for t in load])
    z_full = np.array([window_mean(t, T_GRAB + RAMP_S, T_REL) for t in load])
    z_rel = np.array([settle_mean(t, T_REL + RAMP_S) for t in load])
    n_carried = int(sum(1 for t in load if not t["fell"] or t["survived"] >= T_REL))
    surv_load = np.array([t["survived"] for t in load])
    sag = z_base - z_load
    rec = z_rel - z_load
    wl = np.array([float(np.nanmedian([v for t_, v in zip(t["t"], t["wl"])
                                       if T_GRAB + RAMP_S <= t_ < T_REL] or [np.nan]))
                   for t in load])
    print("-" * 100)
    print(f"  LOADED ({nseeds} seeds, the stone welded and carried):")
    print(f"     pelvis over the carry window {np.nanmean(z_load):.5f} m")
    print(f"     carried the full {T_REL-T_GRAB:.1f} s without falling: {n_carried}/{nseeds} seeds")
    print(f"     SAG vs the control  median {1000*np.nanmedian(sag):.2f} mm  "
          f"(min {1000*np.nanmin(sag):.2f}, max {1000*np.nanmax(sag):.2f})   "
          f"against a control jitter of {1000*jitter:.2f} mm")
    print(f"     weld load, median over the carry {np.nanmedian(wl):+.3f} of the stone's weight "
          f"(1.0 = the body carries all of it)")
    if np.isfinite(np.nanmedian(rec)):
        print(f"     RECOVERY after release: pelvis rises {1000*np.nanmedian(rec):+.2f} mm "
              f"({100*np.nanmedian(rec)/max(np.nanmedian(sag), 1e-9):.0f}% of the sag)")
    else:
        print(f"     RECOVERY: NOT MEASURABLE -- {nseeds - n_carried}/{nseeds} seeds fell while "
              f"carrying, before the release at {T_REL:.1f} s.")
        print(f"       That is not a missing number, it is the answer to a different question: "
              f"the load is so far")
        print(f"       inside the stand's margin that there is no held state to recover FROM.")
    print(f"     survival median {np.median(surv_load):.2f} s "
          f"(min {surv_load.min():.2f}, max {surv_load.max():.2f})")

    # ── THE RESPONSE CURVE: is the sag linear in the carried mass? ─────────────────────────
    fracs = [0.25, 0.50, 0.75, 1.00]
    print(f"  MASS RESPONSE (seed 0) -- a response curve, not a search: nothing is chosen here.")
    print(f"     {'mass kg':>10}{'weight N':>11}{'sag mm':>10}{'weld load':>12}")
    xs, ys = [], []
    for f in fracs:
        t = run(m, d, mujoco, theta, P, jids, 0, mass_scale=f)
        z = settle_mean(t, T_GRAB + RAMP_S)
        s_ = z_base[0] - z
        w_ = float(np.nanmedian([v for t_, v in zip(t["t"], t["wl"])
                                 if T_GRAB + RAMP_S <= t_ < T_REL] or [np.nan]))
        xs.append(f * W_stone); ys.append(s_)
        note = "" if np.isfinite(s_) else "   FELL before the load arrived"
        _s = f"{1000*s_:>10.2f}" if np.isfinite(s_) else f"{'--':>10}"
        _w = f"{w_:>12.3f}" if np.isfinite(w_) else f"{'--':>12}"
        print(f"     {f*_FULL_MASS[0]:>10.3f}{f*W_stone:>11.2f}{_s}{_w}{note}")
    xs_a, ys_a = np.array(xs), np.array(ys)
    good = np.isfinite(ys_a)
    if good.sum() >= 3:
        slope, icept = np.polyfit(xs_a[good], ys_a[good], 1)
        pred = slope * xs_a[good] + icept
        ss_res = float(((ys_a[good] - pred) ** 2).sum())
        ss_tot = float(((ys_a[good] - ys_a[good].mean()) ** 2).sum())
        r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")
        k_curve = 1.0 / slope if slope > 0 else float("nan")
    else:
        slope = icept = r2 = k_curve = float("nan")
    print(f"     -> linear fit r^2 {r2:.4f}, slope {1000*slope:.4f} mm/N "
          f"=> k from the curve {k_curve:.1f} N/m (calibration said {k_eff:.1f})")

    # ── THE VERDICTS ───────────────────────────────────────────────────────────────────────
    med_sag = float(np.nanmedian(sag))
    decorative = abs(med_sag) <= jitter
    lin_ok = np.isfinite(r2) and r2 >= 0.90
    ratio = (med_sag / dz_pred) if (np.isfinite(dz_pred) and dz_pred > 0) else float("nan")
    pred_ok = np.isfinite(ratio) and 0.5 <= ratio <= 2.0
    surv_ok = float(np.median(surv_load)) < float(np.median(surv_base))
    print("=" * 100)
    print(f"  FALSIFIER (no measurable load effect -- the sag is inside the control's jitter): "
          + (f"FIRES -- sag {1000*med_sag:.2f} mm <= jitter {1000*jitter:.2f} mm. THE LOAD PATH "
             f"IS DECORATIVE:\n    the weld holds the stone and the body never learns it is "
             f"carrying anything. Recorded, stopped."
             if decorative else
             f"does not fire -- sag {1000*med_sag:.2f} mm against a {1000*jitter:.2f} mm "
             f"jitter, {abs(med_sag/max(jitter,1e-12)):.1f}x it."))
    print(f"  (a) sag LINEAR in carried mass (r^2 >= 0.90): "
          + (f"HOLDS -- r^2 {r2:.4f}" if lin_ok else f"FAILS -- r^2 {r2:.4f}"))
    print(f"  (b) k_eff from the PELVIS probe predicts the STONE's sag within 2x: "
          + (f"HOLDS -- predicted {1000*dz_pred:.2f} mm, measured {1000*med_sag:.2f} mm "
             f"({ratio:.2f}x)" if pred_ok else
             f"FAILS -- predicted {1000*dz_pred:.2f} mm, measured {1000*med_sag:.2f} mm "
             f"({ratio:.2f}x)"))
    if not pred_ok and np.isfinite(ratio):
        print(f"      PUBLISHED, NOT RECONCILED (rule 17). The probe is a pure vertical force on "
              f"the pelvis;\n      the stone hangs {0.40:.2f} m FORWARD of the torso, so it "
              f"applies a pitching moment the\n      calibration never applies. A stiffness read "
              f"in one direction predicting a load applied\n      in another is exactly the "
              f"disagreement worth keeping.")
    print(f"  (c) loaded survival SHORTER than unloaded: "
          + (f"HOLDS -- {np.median(surv_load):.2f} s vs {np.median(surv_base):.2f} s"
             if surv_ok else
             f"FAILS -- {np.median(surv_load):.2f} s vs {np.median(surv_base):.2f} s"))

    LOGDIR.mkdir(parents=True, exist_ok=True)
    out = LOGDIR / f"grab_load_path_{tp.stem}.json"
    out.write_text(json.dumps(dict(
        theta=tp.name, seeds=nseeds, g=g, stone_mass_kg=_FULL_MASS[0], stone_weight_N=W_stone,
        t_grab=T_GRAB, t_release=T_REL, ramp_s=RAMP_S, secs=SECS,
        control_pelvis_m=float(np.nanmean(z_base)), control_jitter_m=jitter,
        control_survival_median_s=float(np.median(surv_base)),
        k_eff_N_per_m=k_eff, predicted_sag_m=dz_pred,
        measured_sag_median_m=med_sag, measured_sag_per_seed=[float(v) for v in sag],
        recovery_median_m=float(np.nanmedian(rec)),
        weld_load_median=float(np.nanmedian(wl)),
        loaded_survival_median_s=float(np.median(surv_load)),
        mass_response_N=[float(v) for v in xs], mass_response_sag_m=[float(v) for v in ys],
        linear_r2=float(r2), k_from_curve_N_per_m=float(k_curve),
        falsifier_fires=bool(decorative), linear_holds=bool(lin_ok),
        prediction_holds=bool(pred_ok), survival_shortens=bool(surv_ok)), indent=1),
        encoding="utf8")
    print(f"  JSON: {out}")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 3, figsize=(15.5, 4.6))
    for t in base:
        ax[0].plot(t["t"], t["z"], color="#7f8c8d", lw=0.9, alpha=0.6)
    for t in load:
        ax[0].plot(t["t"], t["z"], color="#c0392b", lw=1.1, alpha=0.8)
    ax[0].axvline(T_GRAB, color="#1a7f37", lw=1.4); ax[0].axvline(T_REL, color="#2471a3", lw=1.4)
    ax[0].text(T_GRAB + 0.05, 0.55, "GRAB", fontsize=7.5, color="#1a7f37")
    ax[0].text(T_REL + 0.05, 0.55, "RELEASE", fontsize=7.5, color="#2471a3")
    ax[0].set_xlabel("s"); ax[0].set_ylabel("pelvis m")
    ax[0].set_title(f"grey = unloaded, red = carrying {_FULL_MASS[0]:.1f} kg", fontsize=9)
    ax[1].plot(xs_a, 1000 * ys_a, "o-", color="#8e44ad", lw=1.6, label="measured sag")
    if np.isfinite(slope):
        ax[1].plot(xs_a, 1000 * (slope * xs_a + icept), "--", color="#1a7f37", lw=1.3,
                   label=f"linear, r2 {r2:.3f}")
    if np.isfinite(dz_pred):
        ax[1].scatter([W_stone], [1000 * dz_pred], s=70, marker="X", color="#c0392b", zorder=5,
                      label=f"predicted from k_eff")
    ax[1].set_xlabel("carried weight N"); ax[1].set_ylabel("pelvis sag mm"); ax[1].legend(fontsize=7)
    ax[1].set_title("is the sag a spring?", fontsize=9)
    ax[2].bar([0, 1], [np.median(surv_base), np.median(surv_load)],
              color=["#7f8c8d", "#c0392b"])
    ax[2].set_xticks([0, 1]); ax[2].set_xticklabels(["unloaded", "carrying"])
    ax[2].set_ylabel(f"median survival s, {nseeds} seeds")
    ax[2].set_title("does the load cost the stand?", fontsize=9)
    fig.suptitle(f"THE GRAB LOAD PATH -- sag {1000*med_sag:.2f} mm vs {1000*jitter:.2f} mm "
                 f"jitter; {'DECORATIVE' if decorative else 'the load is routed'}", fontsize=11.5)
    png = OUTDIR / f"grab_load_path_{tp.stem}.png"
    fig.savefig(png, dpi=104, bbox_inches="tight"); plt.close(fig)
    print(f"  PICTURE: {png}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
