"""The falsifier battery — PREREG.md's bars P1-P6, run against the three
constructions, plus the negative controls the prereg names.

Every probe returns numbers, not impressions; `bar_table()` assembles the
PREREG bars into the printed table. Falsifier verdicts live in
BATTERY_RESULTS.md (evidence), next to the prereg that named them.
"""
import numpy as np

from . import measured as M
from . import solver as S
from .model import rig_single_piston, ring_coupled, SlabChain

DIVERGE_RATIO = S.DIVERGE_RATIO
PRESS_DOFS = [2]                     # the hip ring direction
PRESS_FORCE = M.CELL_MASS[3] * M.G   # a press the world delivers: torso weight

_CACHE = {}                          # probes are deterministic: compute once


def _cached(key, fn):
    if key not in _CACHE:
        _CACHE[key] = fn()
    return _CACHE[key]


def _ticks_for(n):
    """Decay-scaled trace length: the numerical damping grows with
    omega*h_sub, so bigger n needs fewer ticks for the same alive window."""
    return 2048 if n <= 4 else (1024 if n <= 11 else 512)


# ---------------------------------------------------------------------------
# P1 — pressure recovery (the constitutive law is unchanged)
# ---------------------------------------------------------------------------
def p1_rest(ticks=10, n_sub=M.N_STABILITY):
    """At rest (zero press, zero intent): lambda -> 0, P = 0, V = V0."""
    sys = ring_coupled()
    worst_P, worst_dV = 0.0, 0.0
    for _ in range(ticks):
        rep = S.xpbd_tick(sys, n_sub=n_sub)
        worst_P = max(worst_P, float(np.max(np.abs(rep.pressure))))
        worst_dV = max(worst_dV, S.amplitude(sys))
    return {"max_P_pa": worst_P, "max_dV_rel": worst_dV}


def p1_under_press(n_sub=M.N_STABILITY):
    """Under a probe press (torso weight at the hip ring, 3 ticks): the
    recovered P = lambda/h_s^2 must equal -dV/(kappa V0) within 1%."""
    sys = ring_coupled()
    miss = 0.0
    for t in range(3):
        sys.external = S._press_vector(sys, PRESS_DOFS, PRESS_FORCE)
        rep = S.xpbd_tick(sys, n_sub=n_sub)
        P_lam, P_law, m = S.pressure_check(sys, rep)
        miss = max(miss, float(np.max(m)))
    return {"miss_percent": miss, "pressure_pa": P_law.tolist()}


# ---------------------------------------------------------------------------
# P2 / falsifier (b) — the substep boundary, explicit family vs coupled solve
# ---------------------------------------------------------------------------
def derived_explicit_multiplier(omega, n):
    """Symplectic-Euler per-substep multiplier of one mode when x = omega
    (h/n) > 2: |eig| = (x^2-2+sqrt(x^4-4x^2))/2 — the derived divergence
    rate the explicit demo is compared against."""
    x = omega * M.H_TICK / n
    if x <= 2.0:
        return 1.0
    return 0.5 * (x * x - 2.0 + np.sqrt(x**4 - 4.0 * x * x))


def p2_probe(family, n, max_ticks=60, want_trace=False):
    """ONE cell of the preregistered boundary matrix (the atomic probe the
    parallel pool runs): family 'explicit'|'xpbd' at substep count n, under
    the standard probe press. Returns verdict numbers (+ the trace when
    `want_trace`, for the printed divergence demo)."""
    sys = ring_coupled()
    trace, diverged = S.divergence_probe(
        sys, M.H_TICK, n, family, PRESS_DOFS, PRESS_FORCE,
        press_ticks=3, max_ticks=max_ticks)
    rate = 0.0
    if diverged and len(trace) >= 3:
        tail = np.array([np.log(max(a, 1e-300)) for a in trace[-4:]])
        rate = float(np.mean(np.diff(tail)))   # log growth / tick
    row = {
        "diverged_at": diverged,
        "max_amplitude": float(max(trace)),
        "log_growth_per_tick": rate,
    }
    if want_trace:
        row["trace"] = [float(a) for a in trace]
    return row


def p2_boundary(n_values=(1, 2, 4), max_ticks=60):
    """The preregistered matrix: explicit family vs the coupled XPBD solve
    at each substep count, under the same probe press. Serial assembly of
    the atomic p2_probe cells (the parallel runner runs the cells directly)."""
    key = ("p2_boundary", tuple(n_values), max_ticks)
    if key in _CACHE:
        return _CACHE[key]
    rows = {}
    for family in ("explicit", "xpbd"):
        for n in n_values:
            rows[(family, n)] = p2_probe(family, n, max_ticks)
    _CACHE[key] = rows
    return rows


def p2_demo(ticks=12):
    """The divergence demo numbers: explicit n=1 vs XPBD n=4, tick by tick."""
    out = {}
    for family, n in (("explicit", 1), ("xpbd", 4)):
        row = p2_probe(family, n, max_ticks=ticks, want_trace=True)
        out[family] = {"trace": row["trace"], "diverged_at": row["diverged_at"]}
    return out


# ---------------------------------------------------------------------------
# P3 / falsifier (a) — the frequencies (per-cell rigs + the coupled ring)
# ---------------------------------------------------------------------------
def p3_rig_probe(cell, n, v_rel=10.0):
    """ONE per-cell frequency row (the atomic probe): the single-piston rig
    for `cell` at substep count n, excited with the momentum-free relative
    velocity (COM still), measured by AR(2)."""
    sys = rig_single_piston(cell)
    j = M.GOVERNING_PLANE[cell]
    mb, ma = M.M_BELOW[j], M.M_ABOVE[j]
    sys.v[:] = [-ma / (mb + ma) * v_rel, +mb / (mb + ma) * v_rel]
    tr, dt = S.run_free(sys, _ticks_for(n), n, lambda s: float(s.q[1] - s.q[0]))
    w = S.spectral_peak(tr, dt)
    pred = M.OMEGA_CELL[cell]
    return {
        "cell": cell, "predicted": pred, "measured": w,
        "miss_percent": 100.0 * (w / pred - 1.0),
        "derived_bias_percent": 100.0 * (M.predicted_bias(pred, n) - 1.0),
    }


def p3_ring_probe(mode, n):
    """ONE coupled-ring frequency row: ring mode `mode` excited on its
    predicted mass-normalized eigenvector, measured vs the predicted omega
    and the derived discrete map."""
    om, V = M.ring_modes()
    sys = ring_coupled()
    sys.v[:] = V[:, mode]
    tr, dt = S.run_free(sys, _ticks_for(n), n, lambda s: float(s.q[2]))
    w = S.spectral_peak(tr, dt)
    return {
        "mode": mode, "predicted": om[mode], "measured": w,
        "miss_percent": 100.0 * (w / om[mode] - 1.0),
        "derived_bias_percent": 100.0 * (M.predicted_bias(om[mode], n) - 1.0),
        "derived_decay": M.predicted_decay(om[mode], n),
    }


def p3_rigs(n_values=(4, M.N_FIDELITY_10PCT, 32), v_rel=10.0):
    """Per-cell single-piston probes vs OMEGA_CELL, at the operating point
    (n=4), the fidelity count (n=11), and the model-validation count (n=32).
    Excitation: momentum-free relative velocity (COM still); the response is
    a single damped mode, measured by AR(2)."""
    key = ("p3_rigs", tuple(n_values), v_rel)
    if key in _CACHE:
        return _CACHE[key]
    table = {}
    for n in n_values:
        table[n] = [p3_rig_probe(cell, n, v_rel) for cell in range(4)]
    _CACHE[key] = table
    return table


def p3_ring(n_values=(4, M.N_FIDELITY_10PCT, 32)):
    """Coupled-ring probes: each mode excited on its predicted mass-normalized
    eigenvector (so the single-mode instrument applies), measured vs the
    predicted omega and the derived discrete map."""
    key = ("p3_ring", tuple(n_values))
    if key in _CACHE:
        return _CACHE[key]
    table = {}
    for n in n_values:
        table[n] = [p3_ring_probe(i, n) for i in range(3)]
    _CACHE[key] = table
    return table


def chain_spectrum_witness():
    """Witness, not a bar: the full planar chain's axial-piston spectrum vs
    the reduced-mass ring — the inertia-idealization spread on this world."""
    ch = SlabChain()
    # axial perturbation: seed all slabs with generic axial velocities
    for i in range(4):
        ch.sys.v[3 * i + 1] = [0.4, -1.0, 0.7, 0.25][i]
    tr, dt = S.run_free(ch.sys, 256, 32, lambda s: float(s.q[10]))  # torso y
    return S.spectrum_peaks(tr, dt, 3)


# ---------------------------------------------------------------------------
# P4 — servo reaction forces (the coupling is real)
# ---------------------------------------------------------------------------
def rigid_field(ch, vcom, wz):
    """A constraint-CONSISTENT rigid-body velocity field about the COM
    (the clean momentum-probe instrument: no constraint transient to
    transport)."""
    com = ch.com()
    for i in range(4):
        r = np.array([ch.sys.q[3 * i], ch.sys.q[3 * i + 1]]) - com
        ch.sys.v[3 * i] = vcom[0] - wz * r[1]
        ch.sys.v[3 * i + 1] = vcom[1] + wz * r[0]
        ch.sys.v[3 * i + 2] = wz


def p4_servo_reaction(ticks=20, target=0.05):
    """Servo intent drives the knee FROM REST; the solve exerts
    equal-and-opposite torque through the joint (net momenta stay at the
    projection-transport floor, ~1e-6 relative), while the pose-overwrite
    writer (the current joint_deg_ architecture, idealized) measurably
    injects momentum by writing a pose no force produced."""
    # -- the coupled solve --
    ch = SlabChain()
    ch.set_servo_target(1, target)
    p0, L0 = ch.momentum()
    for _ in range(ticks):
        S.xpbd_tick(ch.sys, n_sub=M.N_STABILITY)
    p1, L1 = ch.momentum()
    # (the servo row is (0,...,-1,+1,...): the generalized impulse pair is
    #  (+lam, -lam) on the two thetas — asserted numerically in the tests.)
    # -- the pose-overwrite contrast (also from rest) --
    ch2 = SlabChain()
    for _ in range(ticks):
        th_rel = ch2.sys.q[3 * 2 + 2] - ch2.sys.q[3 * 1 + 2]
        ch2.sys.q[3 * 2 + 2] += 0.3 * (target - th_rel)   # the overwrite
        S.xpbd_tick(ch2.sys, n_sub=M.N_STABILITY)
    p1o, L1o = ch2.momentum()
    return {
        "solve_dp": float(np.max(np.abs(np.array(p1) - p0))),
        "solve_dL": float(L1 - L0),
        "overwrite_dp": float(np.max(np.abs(np.array(p1o)))),
        "overwrite_dL": float(L1o),
    }


# ---------------------------------------------------------------------------
# P5 — momentum conservation across the coupled solve
# ---------------------------------------------------------------------------
def p5_momentum(ticks=100):
    """Gravity off, no contacts, no intent, CONSISTENT rigid-field start:
    linear and angular momentum of the slab chain across coupled ticks.
    Bar (prereg P5): drift < 0.1% of the momentum scale. The constraint
    kicks are momentum-neutral to machine precision (measured: the rigid
    projection of the impulse is ~1e-17); what remains is bounded
    projection-transport during corrections, ~1e-6 relative."""
    ch = SlabChain()
    rigid_field(ch, (0.3, 0.2), 0.05)
    p0, L0 = ch.momentum()
    dp, dL = 0.0, 0.0
    for _ in range(ticks):
        S.xpbd_tick(ch.sys, n_sub=M.N_STABILITY)
        p, L = ch.momentum()
        dp = max(dp, float(np.max(np.abs(p - p0))))
        dL = max(dL, abs(L - L0))
    scale = float(np.linalg.norm(p0) + abs(L0)) + 1e-30
    # the transient-start variant (constraint-violating impulse): the same
    # transport is larger but still bounded — reported, not a bar
    ch2 = SlabChain()
    ch2.sys.v[9] = 0.3
    ch2.sys.v[10] = 0.2
    ch2.sys.v[11] = 0.05
    _, L0b = ch2.momentum()
    dLb = 0.0
    for _ in range(ticks):
        S.xpbd_tick(ch2.sys, n_sub=M.N_STABILITY)
        dLb = max(dLb, abs(ch2.momentum()[1] - L0b))
    return {"p0": p0.tolist(), "L0": L0, "max_dp": dp, "max_dL": dL,
            "drift_percent": 100.0 * (dp + dL) / scale,
            "transient_start_max_dL": dLb}


# ---------------------------------------------------------------------------
# P6 — balance is its own gate: force AND moment feasibility
# ---------------------------------------------------------------------------
SUPPORT_EPS = 1e-9   # m: required support-polygon interior margin


def balance_gate(contacts, com, m_total, mu=M.MU_FRICTION, n_max=None):
    """The stance bar (PREREG P6, Astra's separation): a configuration is
    BALANCED iff
      (1) SUPPORT:   the COM's ground projection is strictly inside the
                     support polygon (a single point has empty interior —
                     refused by construction, a knife-edge is a fall);
      (2) FORCE:     contact forces exist within the friction cones
                     (Coulomb mu) and actuator caps with sum F = m g;
      (3) MOMENT:    the same forces also carry sum M_about_COM = 0.
    Planar, ground contacts at equal height, pushes only (unilateral).
    Returns (verdict, per-gate dict)."""
    W = m_total * M.G
    n_max = n_max if n_max is not None else W   # no contact exceeds the weight
    xs = np.array([c[0] for c in contacts])
    c_x = com[0]

    support_margin = (min(c_x - xs.min(), xs.max() - c_x)
                      if len(xs) > 1 else 0.0)
    support_ok = support_margin > SUPPORT_EPS

    if len(contacts) == 1:
        # force: n = W, t = 0; moment demands (x-c)W = 0 — a measure-zero
        # knife edge even when the force gate alone can pass.
        force_ok = (0.0 <= W <= n_max)
        moment_slack = -abs(contacts[0][0] - c_x) * W   # <= 0: never strict
        moment_ok = False
        friction_slack = mu * W
    else:
        # load split from the moment equation (t-force couple carries no
        # moment at equal height: their arm times zero net sum cancels):
        n1 = W * (c_x - xs[1]) / (xs[0] - xs[1])
        n2 = W - n1
        force_ok = (n1 > 0 and n2 > 0 and n1 <= n_max and n2 <= n_max)
        friction_slack = mu * min(n1, n2) if force_ok else 0.0
        # moment: t pair determined by friction only; any |t1| <= mu*min works
        # and carries zero net moment at equal height -> strictly feasible
        moment_ok = force_ok and friction_slack > 0.0
        moment_slack = friction_slack

    ok = bool(support_ok and force_ok and moment_ok)
    return (ok, {
        "support_margin_m": float(support_margin),
        "support_ok": bool(support_ok),
        "force_ok": bool(force_ok),
        "moment_ok": bool(moment_ok),
        "friction_slack_n": float(friction_slack),
        "moment_slack_nm": float(moment_slack),
    })


def p6_balance():
    """The P6 bar rows: a real two-foot stance PASSES; a single-point
    balance is REFUSED; COM outside the support is REFUSED."""
    ch = SlabChain()
    feet = ch.foot_points()
    com = ch.com()
    m_tot = float(ch.m.sum())
    key = "p6_balance"
    if key in _CACHE:
        return _CACHE[key]
    stance, stance_g = balance_gate(feet, com, m_tot)
    single, single_g = balance_gate([feet[0]], (feet[0][0], com[1]), m_tot)
    outside, outside_g = balance_gate(
        feet, (feet[-1][0] + 10 * ch.width[0], com[1]), m_tot)
    out = {"stance": (stance, stance_g), "single_point": (single, single_g),
           "com_outside": (outside, outside_g)}
    _CACHE[key] = out
    return out


# ---------------------------------------------------------------------------
# falsifier (d) — negative controls
# ---------------------------------------------------------------------------
def wrong_compliance_control(n_sub=M.N_STABILITY):
    """A solve with alpha = kappa (missing V0) must FAIL the pressure check
    by the predicted ratio V0: at convergence the regularized solve gives
    P_wrong = -dV/kappa, the true law is -dV/(kappa V0), so
    P_wrong/P_true = V0 per cell."""
    sys = ring_coupled()
    # swap the compliance rows for the wrong ones (alpha = kappa, missing V0)
    for r in sys.rows:
        if r.name.startswith("volume"):
            orig = r.evaluate

            def wrong(q, orig=orig):
                C, J, a = orig(q)
                return C, J, np.full_like(a, M.KAPPA)

            r.evaluate = wrong
            break
    miss_ratios = []
    for t in range(3):
        sys.external = S._press_vector(sys, PRESS_DOFS, PRESS_FORCE)
        rep = S.xpbd_tick(sys, n_sub=n_sub)
        P_lam, P_law, miss = S.pressure_check(sys, rep)
        ratio = P_lam / P_law
        miss_ratios.append(ratio.tolist())
    return {"predicted_ratio": M.V0.tolist(),
            "measured_ratio": miss_ratios[-1],
            "miss_percent": float(np.max(miss))}


# ---------------------------------------------------------------------------
# port datums
# ---------------------------------------------------------------------------
def port_datums():
    """Iteration counts and CPU cost per tick — the realtime-budget datum
    the appliance's risk register asks B1 for."""
    import time
    ch = SlabChain()
    ch.set_servo_target(1, 0.05)
    ch.sys.v[9] = 0.3
    iters = []
    t0 = time.perf_counter()
    for _ in range(50):
        rep = S.xpbd_tick(ch.sys, n_sub=M.N_STABILITY)
        iters.append(rep.iterations)
    dt = (time.perf_counter() - t0) / 50.0
    return {"iterations_per_tick_mean": float(np.mean(iters)),
            "iterations_per_tick_max": int(np.max(iters)),
            "python_seconds_per_tick": dt}


# ---------------------------------------------------------------------------
# the PARALLEL battery: atomic probes + a picklable dispatcher.
# Every probe above is deterministic and independent (fresh systems inside);
# the runner maps this task list over a process pool. run_probe is a
# module-level function so 'spawn' children can pickle the work by name.
# ---------------------------------------------------------------------------
def parallel_task_list():
    """The (name, kwargs) atoms of the battery: 2x P1, 6x P2 (the full
    boundary matrix, traces kept), 12 rig + 9 ring P3 probes, the chain
    witness, P4, P5, P6, the negative control, port datums — 35 independent
    probes."""
    tasks = [("P1_rest", {}), ("P1_press", {})]
    for family in ("explicit", "xpbd"):
        for n in (1, 2, 4):
            tasks.append((f"P2 {family} n={n}",
                          {"family": family, "n": n, "want_trace": True}))
    for n in (4, M.N_FIDELITY_10PCT, 32):
        tasks.extend((f"P3 rig cell={c} n={n}", {"cell": c, "n": n})
                     for c in range(4))
        tasks.extend((f"P3 ring mode={i} n={n}", {"mode": i, "n": n})
                     for i in range(3))
    tasks.append(("P3_chain_witness", {}))
    tasks.append(("P4_servo", {}))
    tasks.append(("P5_momentum", {}))
    tasks.append(("P6_balance", {}))
    tasks.append(("wrong_compliance", {}))
    tasks.append(("port_datums", {}))
    return tasks


_PROBES = {
    "P1_rest": p1_rest,
    "P1_press": p1_under_press,
    "P3_chain_witness": chain_spectrum_witness,
    "P4_servo": p4_servo_reaction,
    "P5_momentum": p5_momentum,
    "P6_balance": p6_balance,
    "wrong_compliance": wrong_compliance_control,
    "port_datums": port_datums,
}


def run_probe(spec):
    """Pool worker body: (name, kwargs) -> (name, json-ready result)."""
    name, kwargs = spec
    if name.startswith("P2 "):
        val = p2_probe(**kwargs)
    elif name.startswith("P3 rig"):
        val = p3_rig_probe(**kwargs)
    elif name.startswith("P3 ring"):
        val = p3_ring_probe(**kwargs)
    else:
        val = _PROBES[name](**kwargs)
        if name == "P6_balance":
            val = {"verdicts": {k: v[0] for k, v in val.items()},
                   "detail": {k: v[1] for k, v in val.items()}}
    return name, _plain(val)


def _plain(v):
    """numpy scalars/arrays -> plain python (pickling + json)."""
    if isinstance(v, dict):
        return {k: _plain(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [_plain(x) for x in v]
    if isinstance(v, np.generic):
        return v.item()
    if isinstance(v, np.ndarray):
        return v.tolist()
    return v


def assemble(results):
    """The flat {name: value} probe results -> the dict `format_bar_table`
    consumes (same shape bar_table returns)."""
    r = {"P1_rest": results["P1_rest"], "P1_press": results["P1_press"]}
    r["P2_boundary"] = {
        (f, n): results[f"P2 {f} n={n}"]
        for f in ("explicit", "xpbd") for n in (1, 2, 4)}
    r["P2_demo"] = {
        "explicit": {"trace": results["P2 explicit n=1"]["trace"],
                     "diverged_at": results["P2 explicit n=1"]["diverged_at"]},
        "xpbd": {"trace": results["P2 xpbd n=4"]["trace"],
                 "diverged_at": results["P2 xpbd n=4"]["diverged_at"]}}
    r["P3_rigs"] = {n: [results[f"P3 rig cell={i} n={n}"] for i in range(4)]
                    for n in (4, M.N_FIDELITY_10PCT, 32)}
    r["P3_ring"] = {n: [results[f"P3 ring mode={i} n={n}"] for i in range(3)]
                    for n in (4, M.N_FIDELITY_10PCT, 32)}
    r["P3_chain_witness"] = results["P3_chain_witness"]
    r["P4_servo"] = results["P4_servo"]
    r["P5_momentum"] = results["P5_momentum"]
    r["P6_balance"] = results["P6_balance"]["verdicts"]
    r["P6_balance_detail"] = results["P6_balance"]["detail"]
    r["wrong_compliance"] = results["wrong_compliance"]
    r["port_datums"] = results["port_datums"]
    return r


# ---------------------------------------------------------------------------
def bar_table():
    """Run every bar and return the structured results dict."""
    results = {}
    results["P1_rest"] = p1_rest()
    results["P1_press"] = p1_under_press()
    results["P2_boundary"] = p2_boundary()
    results["P2_demo"] = p2_demo()
    results["P3_rigs"] = p3_rigs()
    results["P3_ring"] = p3_ring()
    results["P3_chain_witness"] = chain_spectrum_witness()
    results["P4_servo"] = p4_servo_reaction()
    results["P5_momentum"] = p5_momentum()
    results["P6_balance"] = {k: v[0] for k, v in p6_balance().items()}
    results["P6_balance_detail"] = {k: v[1] for k, v in p6_balance().items()}
    results["wrong_compliance"] = wrong_compliance_control()
    results["port_datums"] = port_datums()
    return results


def format_bar_table(r):
    """The human-readable bar table (the BATTERY_RESULTS.md core)."""
    L = []
    L.append("  BAR                         PREDICTED            MEASURED                       VERDICT")
    L.append("  " + "-" * 88)
    p1 = r["P1_press"]["miss_percent"]
    L.append("  P1 pressure recovery        miss < 1%%            miss %.3g %%" % p1
             + "                    " + ("PASS" if p1 < 1.0 else "FAIL"))
    rest = r["P1_rest"]
    rest_ok = max(rest["max_P_pa"], rest["max_dV_rel"]) < 1e-9
    L.append("  P1 at rest                  P=0, dV=0            maxP %.3g Pa, maxdV %.3g    %s"
             % (rest["max_P_pa"], rest["max_dV_rel"], "PASS" if rest_ok else "FAIL"))
    b = r["P2_boundary"]
    for (family, n), row in sorted(b.items()):
        pred = "bounded" if (family, n) in (("explicit", 4),) or family == "xpbd" \
            else "diverges"
        got = ("DIVERGES @t=%d" % row["diverged_at"]) if row["diverged_at"] else \
            ("bounded (max %.2f)" % row["max_amplitude"])
        L.append("  P2 %-14s n=%-2d        %-19s %s" % (family, n, pred, got))
    L.append("  P3/falsifier(a) rigs @ n=4 (operating point, +-10%% bar):")
    for row in r["P3_rigs"][4]:
        L.append("    cell %d  pred %7.1f   measured %7.1f   %+.1f%%   (derived %+.1f%%)"
                 % (row["cell"], row["predicted"], row["measured"],
                    row["miss_percent"], row["derived_bias_percent"]))
    L.append("  P3/falsifier(a) coupled ring @ n=4:")
    for row in r["P3_ring"][4]:
        L.append("    mode %d  pred %7.1f   measured %7.1f   %+.1f%%   (derived %+.1f%%)"
                 % (row["mode"], row["predicted"], row["measured"],
                    row["miss_percent"], row["derived_bias_percent"]))
    L.append("  P3 model validation @ n=11 (fidelity) / n=32: worst misses "
             "%.1f%% / %.1f%%" % (
                 max(abs(row["miss_percent"]) for rows in
                     (r["P3_rigs"][M.N_FIDELITY_10PCT], r["P3_ring"][M.N_FIDELITY_10PCT])
                     for row in rows),
                 max(abs(row["miss_percent"]) for rows in
                     (r["P3_rigs"][32], r["P3_ring"][32]) for row in rows)))
    L.append("  P3 chain witness (distributed inertia): "
             + ", ".join("%.0f" % w for w in r["P3_chain_witness"]) + " rad/s")
    p4 = r["P4_servo"]
    L.append("  P4 servo reactions         dp=0, dL=0           dp %.3g, dL %.3g kg.m2/s"
             % (p4["solve_dp"], p4["solve_dL"]))
    L.append("  P4 pose-overwrite contrast dL != 0           dL %.3g kg.m2/s"
             % abs(p4["overwrite_dL"]))
    p5 = r["P5_momentum"]
    L.append("  P5 momentum (100 ticks)    drift < 0.1%%         drift %.3g%%"
             % p5["drift_percent"])
    for name in ("stance", "single_point", "com_outside"):
        L.append("  P6 balance %-13s %s" % (name, "PASS" if r["P6_balance"][name] else "REFUSED"))
    wc = r["wrong_compliance"]
    L.append("  (d) wrong compliance      ratio V0             measured %s"
             % ["%.3f" % v for v in wc["measured_ratio"]])
    L.append("  (d) predicted V0 per cell %s" % ["%.3f" % v for v in wc["predicted_ratio"]])
    pd_ = r["port_datums"]
    L.append("  port: iters/tick mean %.1f max %d; %.2f ms/tick (python, 12-DOF chain)"
             % (pd_["iterations_per_tick_mean"], pd_["iterations_per_tick_max"],
                1e3 * pd_["python_seconds_per_tick"]))
    return "\n".join(L)
