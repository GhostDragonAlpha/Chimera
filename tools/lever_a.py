"""lever_a.py -- P-A: pin the forward lever's STATICS. `docs/THE_LEVERS.md` section A, executed.

    STATEMENT   (THE_LEVERS A)  forward = 1.0 places COM exactly on BoS edge, within named
                                tolerance -- measurable from stand theta alone, no dynamics needed.
    PREDICTION            d_m, the fore edge of the MEASURED phase-1 contact polygon read from its
                          own contacts, lands near together_half_length_m (the lateral analogue did:
                          0.5 mm gap, stance_choice), and tilting the trained standing pose by
                          theta_step = asin(d_m / h_c) about its contact center puts the measured COM
                          within +/-2% of that edge.
    FALSIFIER             |static offset - d_m| / d_m > 2%  =>  theta_step re-derived from the
                          measured polygon (THE_LEVERS falsifier A). The run prints delta (resting
                          COM offset from CoP) and h_a vs h_c so the failing input is named, not
                          guessed.

WHY THE STATIC OFFSET IS MEASURED AND NOT ALGEBRAIC. h_c*sin(asin(d_m/h_c)) equals d_m by
construction -- that check can never fail and would pin nothing. The offset is therefore read from
the body: the settled standing pose (stand theta, no gait) is tilted rigidly about its contact
center in ONE mj_forward -- no integration, no stepping, "no dynamics needed" literally -- and the
COM's fore-aft position is read off. It deviates from d_m exactly when the resting COM is not over
the CoP (delta != 0) or the pose's COM height h_a differs from the port's h_c: both are real
properties of the trained body, and both are printed.

    python tools/lever_a.py [--theta <path>] [--seeds 4] [--secs 5]
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
THETA = OUTDIR / "stand_theta.npy"
FOOT_BODIES = ("calcn_r", "calcn_l", "toes_r", "toes_l")
TOL = 0.02                                                        # THE_LEVERS A: pass band +/-2%


def foot_contacts(m, d, fb):
    """(fore-aft x, lateral y of every load-bearing contact point, normal-force weight) for the
    four feet. Index 0 is fore-aft in this model -- stance_choice scores com[0] against
    bos_half_fore_m."""
    xs, ys, ws = [], [], []
    for ci in range(d.ncon):
        c = d.contact[ci]
        if int(c.geom1) in fb or int(c.geom2) in fb:
            xs.append(float(c.pos[0]))                            # fore-aft
            ys.append(float(c.pos[1]))                            # lateral
            ws.append(abs(float(c.force[2])))                     # normal component, order-safe
    return np.asarray(xs), np.asarray(ys), np.asarray(ws)


def cop(xs, ys, ws):
    """Contact center (fore-aft x, lateral y), force-weighted; unweighted mean when no contact
    carries load."""
    if len(ys) == 0:
        return None
    w = ws.sum()
    if w > 1e-9:
        return float((ws * xs).sum() / w), float((ws * ys).sum() / w)
    return float(np.mean(xs)), float(np.mean(ys))


def rollout_phase1(m, d, mujoco, theta, P, jids, secs, seed):
    """One phase-1 life (STAND on, f3_stand's first `secs` seconds), recording per sample the CoP,
    the fore edge of the contact hull and the COM -- all in world frame."""
    tgt = P["OUT pelvis_target_m"]
    PARSER = Parser(default_registry(theta, tgt, m.nu))
    PARSER.set_verb("STAND", True)
    mujoco.mj_resetDataKeyframe(m, d, 0)
    mujoco.mj_forward(m, d)
    seat_in_limits(m, d, mujoco, jids)
    if seed:
        d.qpos[:] = d.qpos + np.random.default_rng(seed).normal(0.0, NUDGE, size=d.qpos.shape)
        mujoco.mj_forward(m, d)
    fb = {mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, n) for n in FOOT_BODIES}
    tr = {"t": [], "z": [], "comx": [], "comz": [], "cop": [], "edge": []}
    steps = int(secs / m.opt.timestep)
    fell = False
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
            xs, ys, ws = foot_contacts(m, d, fb)
            c = cop(xs, ys, ws)
            tr["t"].append(k * m.opt.timestep)
            tr["z"].append(float(d.qpos[2]))
            tr["comx"].append(float(com[0]))
            tr["comz"].append(float(com[2]))
            tr["cop"].append(c[0] if c is not None else np.nan)   # CoP fore-aft
            tr["edge"].append(float(np.max(xs)) if len(xs) else np.nan)  # fore edge of hull
            if float(d.qpos[2]) < 0.5 * tgt:
                fell = True
                break
    return tr, fell


def quat_mul(a, b):
    """Hamilton product, (w,x,y,z). a applied AFTER b in the body frame = premultiply."""
    aw, ax, ay, az = a
    bw, bx, by, bz = b
    return (aw * bw - ax * bx - ay * by - az * bz,
            aw * bx + ax * bw + ay * bz - az * by,
            aw * by - ax * bz + ay * bw + az * bx,
            aw * bz + ax * by - ay * bx + az * bw)


def static_offset(m, d, mujoco, q0, theta):
    """Tilt the settled pose rigidly about its contact center by `theta` (one mj_forward, no
    dynamics) and return (COM fore-aft offset from CoP, resting delta, resting COM height)."""
    d.qpos[:] = q0
    mujoco.mj_forward(m, d)
    com = np.asarray(d.subtree_com[0], dtype=float)
    fb = {mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, n) for n in FOOT_BODIES}
    xs, ys, ws = foot_contacts(m, d, fb)
    c = cop(xs, ys, ws)
    if c is None:
        return float("nan"), float("nan"), float("nan")
    cop = np.array([c[0], c[1], 0.0])                             # CoP on the floor plane
    delta = float(com[0] - cop[0])
    h_a = float(com[2])
    # rotate about the Y (lateral) axis by theta: top toward +x (fore). World-frame rotation =>
    # premultiply the free-joint quaternion; translate so the CoP stays fixed.
    q_lean = (np.cos(theta / 2), 0.0, np.sin(theta / 2), 0.0)
    qw, qx, qy, qz = quat_mul(q_lean, d.qpos[3:7])
    nrm = float(np.hypot(np.hypot(qw, qx), np.hypot(qy, qz)))
    ct, st = np.cos(theta), np.sin(theta)
    p = d.qpos[0:3] - cop
    new_pos = cop + np.array([p[0] * ct + p[2] * st, p[1], -p[0] * st + p[2] * ct])
    d.qpos[0:3] = new_pos
    d.qpos[3:7] = (qw / nrm, qx / nrm, qy / nrm, qz / nrm)
    mujoco.mj_forward(m, d)
    return float(d.subtree_com[0][0] - cop[0]), delta, h_a


def main() -> int:
    import mujoco
    a = sys.argv
    nseeds = int(a[a.index("--seeds") + 1]) if "--seeds" in a else 4
    secs = float(a[a.index("--secs") + 1]) if "--secs" in a else 5.0
    tp = Path(a[a.index("--theta") + 1]) if "--theta" in a else THETA
    if not tp.is_absolute():
        tp = OUTDIR / tp.name
    if not tp.exists():
        raise SystemExit(f"no {tp} -- refusing to pin a lever for a policy that does not exist "
                         f"(rule 20).")
    theta = np.load(tp)
    P = derive_stand_port()
    h_c = float(P["OUT com_target_m"])
    hl_pub = float(P["OUT bos_half_fore_m"])

    m, g = load_body(MYOBODY, mujoco)
    d = mujoco.MjData(m)
    jids = joint_ids(m, mujoco)

    runs, q0s, fell = [], [], []
    for s in range(nseeds):
        tr, f = rollout_phase1(m, d, mujoco, theta, P, jids, secs, s)
        runs.append(tr)
        fell.append(f)
        if not f:
            q0s.append(d.qpos.copy())

    ok = [r for r, f in zip(runs, fell) if not f]
    if len(ok) < 2:
        raise SystemExit(f"only {len(ok)} of {nseeds} seeds survived phase 1 -- a lever cannot be "
                         f"pinned on a falling body. Refusing.")

    # d_m: fore edge of the measured contact polygon, from its own contacts, per sample.
    dm = []
    for r in ok:
        v = np.asarray(r["edge"], dtype=float) - np.asarray(r["cop"], dtype=float)
        dm.extend(v[np.isfinite(v)].tolist())
    d_m = float(np.median(dm))
    if not np.isfinite(d_m) or d_m <= 0.02:
        raise SystemExit(f"measured fore edge {d_m} m -- no meaningful forward extent of the "
                         f"contact polygon; the measurement is broken, refusing to pin anything.")

    offs, deltas, h_as = [], [], []
    # theta_step needs d_m first; then tilt every settled pose at it and take the median offset.
    th_step = float(np.arcsin(min(1.0, d_m / h_c)))
    for q0 in q0s:
        off, delta, h_a = static_offset(m, d, mujoco, q0, th_step)
        offs.append(off); deltas.append(delta); h_as.append(h_a)
    x_off = float(np.median(offs))
    algebraic = h_c * np.sin(th_step)
    gap = abs(x_off - d_m) / d_m

    print(f"\nLEVER A -- statics at the edge  ({tp.name}, {len(ok)} seeds x {secs:.0f} s phase 1, "
          f"g={g})")
    print("=" * 96)
    print(f"  h_c (port com_target_m)      {h_c:.4f} m")
    print(f"  published bos_half_fore_m    {hl_pub:.4f} m   (the box, for comparison only)")
    print("-" * 96)
    print(f"  measured d_m (fore edge of the phase-1 contact polygon, from its own contacts)")
    print(f"      median over {len(dm)} samples:  {d_m:.4f} m   "
          f"(gap to published {abs(d_m - hl_pub):.4f} m)")
    for i, r in enumerate([r for r, f in zip(runs, fell) if not f]):
        v = np.asarray(r["edge"], dtype=float) - np.asarray(r["cop"], dtype=float)
        print(f"      seed {i}:  median {float(np.nanmedian(v)):.4f} m   "
              f"min {float(np.nanmin(v)):.4f} / max {float(np.nanmax(v)):.4f}")
    print("-" * 96)
    print(f"  theta_step = asin(d_m/h_c)   {th_step:.5f} rad  ({np.degrees(th_step):.2f} deg)")
    print(f"  static offset at forward=1.0, side by side:")
    print(f"      algebraic h_c*sin(theta_step)   {algebraic:.4f} m   (= d_m by construction; "
          f"printed, not the check)")
    print(f"      MEASURED (pose tilted about CoP, one mj_forward)  {x_off:.4f} m")
    for i, o in enumerate(offs):
        print(f"      seed {i}:  {o:.4f} m   delta {deltas[i]:+.4f} m   h_a {h_as[i]:.4f} m")
    print("-" * 96)
    verdict = gap <= TOL
    print(f"  CHECK |measured - d_m| / d_m = {gap:.4%}   pass band +/-{TOL:.0%}")
    print(f"  VERDICT: {'PASS -- the lever is pinned at theta_step = asin(d_m/h_c)' if verdict else
          'FALSIFIER A FIRES -- theta_step re-derived from the measured polygon; see delta and h_a above for the failing input'}")

    LOGDIR.mkdir(parents=True, exist_ok=True)
    out = LOGDIR / f"lever_a_{tp.stem}.json"
    out.write_text(json.dumps(dict(
        theta=tp.name, seeds=len(ok), of_seeds=nseeds, secs=secs, g=g, tol=TOL,
        h_c_m=h_c, hl_published_m=hl_pub, d_m_m=d_m, gap_to_published_m=abs(d_m - hl_pub),
        n_samples=len(dm), theta_step_rad=th_step,
        static_offset_algebraic_m=float(algebraic), static_offset_measured_m=x_off,
        per_seed=dict(offset=[float(v) for v in offs], delta=[float(v) for v in deltas],
                      h_a=[float(v) for v in h_as]),
        gap_frac=gap, verdict="pass" if verdict else "falsifier_A"), indent=1), encoding="utf8")
    print(f"  JSON: {out}")
    return 0 if verdict else 1


if __name__ == "__main__":
    sys.exit(main())
