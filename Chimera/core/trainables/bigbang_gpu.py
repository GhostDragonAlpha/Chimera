"""bigbang_gpu — the cosmic rung on the GPU, the way it was intended.

The human, rejecting a CPU training run (2026-07-18): "You need to use the GPU also
the way it was intended." The intention is the brain_gpu doctrine (CLAUDE.md):

    THE WHOLE POPULATION x EVERY RESTART IN ONE RESIDENT BATCH,
    ZERO CPU<->GPU SYNCS INSIDE THE ROLLOUT LOOP, ONE READBACK AT THE END.

This is also the human's "3D multiplication matrix" made literal: one uniform law
(softened pairwise gravity) contracted over the whole state field every tick — and
here the field is (worlds x bodies x 3), so a training generation IS a single
batched tensor program: every candidate universe evolves in flight simultaneously.

Same physics, same settings, same fact names as core/trainables/bigbang.py (the
CPU twin — one objective file serves both). Differences, stated honestly:
  - fp32 state (consumer-GPU reality; the 4090 runs fp64 at 1:64). The L_z
    honesty ledger therefore drifts at fp32 cancellation scale, not fp64 —
    the objective wall is set from MEASURED smoke drift, not wishful 1e-6.
  - In-kernel merging is INDEX-ORDERED per pass (a serial per-world scan),
    not distance-ordered like the CPU twin's greedy sort. Both are
    deterministic; borderline triple encounters can resolve differently.
    Chaos makes trajectory-level parity meaningless anyway — the honest
    parity claim is fact-level agreement on the same genome, not bitwise.
  - The empirical-Kepler sampler accumulates WINDING (unwrapped delta-theta)
    and mean radius on-GPU instead of storing histories: same period math,
    O(1) memory, no mid-loop readback.

The stale-acceleration lesson (the CPU twin's first smoke: lz_drift 0.527,
structural) is inherited by construction: forces are recomputed by kernel after
every merge/escape pass, so no kick ever uses a dead body's unpaired force.

DOMAIN CONTRACT (GPU flavor): seed/mutate re-exported from the CPU twin;
measure_batch(genomes) -> list[{fact: float}] — the trainer auto-selects the GPU
backend when measure_batch is present (Pool unused).
"""

from __future__ import annotations

import math

import numpy as np

from core.trainables.bigbang import (
    DT, ESCAPE_R, EVAL_SEED, G, GENOME_SCHEMA, LATE_FRAC, M_TOT, MERGE_EVERY,
    N0, N_RESTARTS, PLANET_MIN_MERGES, R0, R_CLOUD, SAMPLE_EVERY, SAMPLE_FRAC,
    SOFT, STEPS, THERMAL_FRAC, build_init, mutate, seed,
)

__all__ = ["seed", "mutate", "measure_batch", "rollout_states"]

import warp as wp

_M0 = M_TOT / N0

wp.init()

C_N0 = wp.constant(int(N0))
C_G = wp.constant(float(G))
C_SOFT2 = wp.constant(float(SOFT * SOFT))
C_R0 = wp.constant(float(R0))
C_M0 = wp.constant(float(_M0))
C_ESC2 = wp.constant(float(ESCAPE_R * ESCAPE_R))
C_PI = wp.constant(math.pi)


@wp.kernel
def k_accel(pos: wp.array2d(dtype=wp.vec3), m: wp.array2d(dtype=float),
            acc: wp.array2d(dtype=wp.vec3)):
    w, i = wp.tid()
    p = pos[w, i]
    a = wp.vec3(0.0, 0.0, 0.0)
    for j in range(C_N0):
        d = pos[w, j] - p                    # zero vector when j == i: no self term
        r2 = wp.dot(d, d) + C_SOFT2
        a += d * (m[w, j] / (r2 * wp.sqrt(r2)))
    acc[w, i] = a * C_G


@wp.kernel
def k_kick(vel: wp.array2d(dtype=wp.vec3), acc: wp.array2d(dtype=wp.vec3),
           dt_half: float):
    w, i = wp.tid()
    vel[w, i] = vel[w, i] + acc[w, i] * dt_half


@wp.kernel
def k_drift(pos: wp.array2d(dtype=wp.vec3), vel: wp.array2d(dtype=wp.vec3),
            dt: float):
    w, i = wp.tid()
    pos[w, i] = pos[w, i] + vel[w, i] * dt


@wp.kernel
def k_drag(pos: wp.array2d(dtype=wp.vec3), vel: wp.array2d(dtype=wp.vec3),
           kcirc: wp.array(dtype=float), ramp: wp.array(dtype=float),
           dt: float, ramp_t: float):
    # Radial + vertical damping only: torque-free about z (the gas shortcut).
    # Effective drag = k_circ * min(1, t/ramp): per-world ramp fraction rides
    # in as an array; the CURRENT time fraction ramp_t is a launch scalar -
    # no readback, the schedule is known in advance.
    w, i = wp.tid()
    r_frac = 1.0
    if ramp[w] > 0.0:
        r_frac = wp.min(1.0, ramp_t / ramp[w])
    f = kcirc[w] * r_frac * dt
    if f > 0.0:
        p = pos[w, i]
        rho = wp.sqrt(p[0] * p[0] + p[1] * p[1]) + 1.0e-9
        rx = p[0] / rho
        ry = p[1] / rho
        v = vel[w, i]
        vr = v[0] * rx + v[1] * ry
        vel[w, i] = wp.vec3(v[0] - f * vr * rx, v[1] - f * vr * ry,
                            v[2] * (1.0 - f))


@wp.kernel
def k_merge_escape(pos: wp.array2d(dtype=wp.vec3), vel: wp.array2d(dtype=wp.vec3),
                   m: wp.array2d(dtype=float), merges_of: wp.array2d(dtype=int),
                   mscale: wp.array(dtype=float), lz_spin: wp.array(dtype=float),
                   lz_removed: wp.array(dtype=float),
                   merges_late: wp.array(dtype=int), is_late: int):
    # One thread per WORLD: a serial scan so the ledger needs no atomics.
    w = wp.tid()
    for i in range(C_N0):
        if m[w, i] > 0.0:
            for j in range(i + 1, C_N0):
                if m[w, j] > 0.0:
                    d = pos[w, j] - pos[w, i]
                    ri = C_R0 * wp.pow(m[w, i] / C_M0, 1.0 / 3.0)
                    rj = C_R0 * wp.pow(m[w, j] / C_M0, 1.0 / 3.0)
                    thr = mscale[w] * (ri + rj)
                    if wp.dot(d, d) < thr * thr:
                        s = i                    # survivor: the heavier body
                        l = j
                        if m[w, j] > m[w, i]:
                            s = j
                            l = i
                        ps = pos[w, s]
                        pl = pos[w, l]
                        vs = vel[w, s]
                        vl = vel[w, l]
                        lz_b = (m[w, s] * (ps[0] * vs[1] - ps[1] * vs[0])
                                + m[w, l] * (pl[0] * vl[1] - pl[1] * vl[0]))
                        mt = m[w, s] + m[w, l]
                        pn = (ps * m[w, s] + pl * m[w, l]) / mt
                        vn = (vs * m[w, s] + vl * m[w, l]) / mt
                        pos[w, s] = pn
                        vel[w, s] = vn
                        m[w, s] = mt
                        merges_of[w, s] = merges_of[w, s] + merges_of[w, l]
                        lz_spin[w] = lz_spin[w] + (
                            lz_b - mt * (pn[0] * vn[1] - pn[1] * vn[0]))
                        m[w, l] = 0.0
                        pos[w, l] = wp.vec3(1.0e6 + 10.0 * float(l), 0.0, 0.0)
                        vel[w, l] = wp.vec3(0.0, 0.0, 0.0)
                        merges_of[w, l] = 0
                        if is_late == 1:
                            merges_late[w] = merges_late[w] + 1
                        if s == j:               # survivor lives at j: i is dead
                            break                # stop scanning from dead i
    for i in range(C_N0):
        if m[w, i] > 0.0:
            p = pos[w, i]
            if wp.dot(p, p) > C_ESC2:
                v = vel[w, i]
                lz_removed[w] = lz_removed[w] + m[w, i] * (
                    p[0] * v[1] - p[1] * v[0])
                m[w, i] = 0.0
                pos[w, i] = wp.vec3(1.0e6 + 10.0 * float(i), 0.0, 0.0)
                vel[w, i] = wp.vec3(0.0, 0.0, 0.0)
                merges_of[w, i] = 0


@wp.kernel
def k_sample(pos: wp.array2d(dtype=wp.vec3), m: wp.array2d(dtype=float),
             prev_theta: wp.array2d(dtype=float),
             winding: wp.array2d(dtype=float), r_sum: wp.array2d(dtype=float),
             n_s: wp.array2d(dtype=float), first: int):
    # Winding accumulator: the empirical-Kepler sampler with O(1) memory.
    w, i = wp.tid()
    if m[w, i] > 0.0:
        p = pos[w, i]
        th = wp.atan2(p[1], p[0])
        if first == 0 and n_s[w, i] > 0.0:
            dth = th - prev_theta[w, i]
            if dth > C_PI:
                dth = dth - 2.0 * C_PI
            if dth < -C_PI:
                dth = dth + 2.0 * C_PI
            winding[w, i] = winding[w, i] + dth
        prev_theta[w, i] = th
        r_sum[w, i] = r_sum[w, i] + wp.sqrt(p[0] * p[0] + p[1] * p[1])
        n_s[w, i] = n_s[w, i] + 1.0


# --- world init (CPU, outside the loop — allowed) --------------------------------

def _init_world(genome: dict, restart: int):
    """v2: both twins build worlds through bigbang.build_init — one shared
    constructor, zero init drift between CPU and GPU."""
    rng = np.random.default_rng(EVAL_SEED + restart)
    return build_init(genome, rng)


def rollout_states(genomes: list[dict], restarts: int = N_RESTARTS,
                   snapshot_every: int = 0):
    """Run len(genomes) x restarts universes wholly on the GPU; return final
    per-world numpy state (for facts, renders, or UE5 wiring). No readback
    happens until every step of every universe is enqueued.

    snapshot_every > 0 breaks the zero-sync rule ON PURPOSE and only here:
    it reads positions back every K steps for TRAJECTORY RENDERING of a few
    worlds. Never used by measure_batch / training — the render path is
    allowed to pay for pictures; the training path is not."""
    W = len(genomes) * restarts
    pos0 = np.empty((W, N0, 3), np.float32)
    vel0 = np.empty((W, N0, 3), np.float32)
    m0 = np.empty((W, N0), np.float32)
    lz0 = np.empty(W, np.float64)
    kcirc = np.empty(W, np.float32)
    mscale = np.empty(W, np.float32)
    kramp = np.empty(W, np.float32)
    for g, genome in enumerate(genomes):
        for r in range(restarts):
            w = g * restarts + r
            p, v, mm, l0 = _init_world(genome, r)
            pos0[w], vel0[w], m0[w], lz0[w] = p, v, mm, l0
            kcirc[w] = genome["k_circ"]
            mscale[w] = genome["merge_scale"]
            kramp[w] = float(genome.get("k_ramp", 0.0))

    dev = wp.get_device()
    pos = wp.array(pos0.reshape(W, N0, 3), dtype=wp.vec3, device=dev)
    vel = wp.array(vel0.reshape(W, N0, 3), dtype=wp.vec3, device=dev)
    m = wp.array(m0, dtype=float, device=dev)
    acc = wp.zeros((W, N0), dtype=wp.vec3, device=dev)
    merges_of = wp.array(np.ones((W, N0), np.int32), dtype=int, device=dev)
    kc = wp.array(kcirc, dtype=float, device=dev)
    ms = wp.array(mscale, dtype=float, device=dev)
    kr = wp.array(kramp, dtype=float, device=dev)
    lz_spin = wp.zeros(W, dtype=float, device=dev)
    lz_removed = wp.zeros(W, dtype=float, device=dev)
    merges_late = wp.zeros(W, dtype=int, device=dev)
    prev_theta = wp.zeros((W, N0), dtype=float, device=dev)
    winding = wp.zeros((W, N0), dtype=float, device=dev)
    r_sum = wp.zeros((W, N0), dtype=float, device=dev)
    n_s = wp.zeros((W, N0), dtype=float, device=dev)

    late_start = int(STEPS * (1.0 - LATE_FRAC))
    sample_start = int(STEPS * (1.0 - SAMPLE_FRAC))
    dim2 = (W, N0)
    first_sample = 1
    snaps: list[tuple[np.ndarray, np.ndarray]] = []
    for step in range(STEPS):
        if snapshot_every and step % snapshot_every == 0:
            snaps.append((pos.numpy().reshape(W, N0, 3).copy(),
                          m.numpy().copy()))
        wp.launch(k_accel, dim=dim2, inputs=[pos, m, acc], device=dev)
        wp.launch(k_kick, dim=dim2, inputs=[vel, acc, 0.5 * DT], device=dev)
        wp.launch(k_drift, dim=dim2, inputs=[pos, vel, DT], device=dev)
        wp.launch(k_accel, dim=dim2, inputs=[pos, m, acc], device=dev)
        wp.launch(k_kick, dim=dim2, inputs=[vel, acc, 0.5 * DT], device=dev)
        wp.launch(k_drag, dim=dim2,
                  inputs=[pos, vel, kc, kr, DT, step / float(STEPS)],
                  device=dev)
        if step % MERGE_EVERY == 0:
            wp.launch(k_merge_escape, dim=W,
                      inputs=[pos, vel, m, merges_of, ms, lz_spin, lz_removed,
                              merges_late, 1 if step >= late_start else 0],
                      device=dev)
            # forces refresh next iteration's k_accel: no stale-force kicks.
        if step >= sample_start and step % SAMPLE_EVERY == 0:
            wp.launch(k_sample, dim=dim2,
                      inputs=[pos, m, prev_theta, winding, r_sum, n_s,
                              first_sample], device=dev)
            first_sample = 0

    wp.synchronize_device(dev)
    return {
        "snaps": snaps,
        "pos": pos.numpy().reshape(W, N0, 3).astype(np.float64),
        "vel": vel.numpy().reshape(W, N0, 3).astype(np.float64),
        "m": m.numpy().astype(np.float64),
        "merges_of": merges_of.numpy(),
        "winding": winding.numpy().astype(np.float64),
        "r_sum": r_sum.numpy().astype(np.float64),
        "n_s": n_s.numpy().astype(np.float64),
        "lz_spin": lz_spin.numpy().astype(np.float64),
        "lz_removed": lz_removed.numpy().astype(np.float64),
        "merges_late": merges_late.numpy(),
        "lz0": lz0,
    }


# --- facts (CPU, after the single readback) --------------------------------------

def _world_facts(st, w: int) -> dict:
    pos, vel, m = st["pos"][w], st["vel"][w], st["m"][w]
    merges_of = st["merges_of"][w]
    alive = m > 0.0
    lz_end = (float(np.sum(m * (pos[:, 0] * vel[:, 1] - pos[:, 1] * vel[:, 0])))
              + float(st["lz_spin"][w]) + float(st["lz_removed"][w]))
    lz_drift = abs(lz_end - st["lz0"][w]) / (abs(st["lz0"][w]) + 1e-12)
    live = np.flatnonzero(alive)
    escaped_mass = M_TOT - float(m[live].sum()) if live.size else M_TOT
    out = {"central_frac": 0.0, "n_planets": 0.0, "ecc_median": 1.0,
           "incl_rms_deg": 90.0, "kepler_slope": 0.0, "kepler_r2": 0.0,
           "planet_mass_frac": 0.0, "merges_late": float(st["merges_late"][w]),
           "escaped_frac": escaped_mass / M_TOT, "lz_drift": lz_drift,
           "spin_l_frac": abs(float(st["lz_spin"][w]))
           / (abs(st["lz0"][w]) + 1e-12)}
    if live.size == 0:
        return out
    c = live[int(np.argmax(m[live]))]
    out["central_frac"] = float(m[c] / M_TOT)

    l_tot = np.zeros(3)
    for b in live:
        l_tot += m[b] * np.cross(pos[b], vel[b])
    l_hat = l_tot / (np.linalg.norm(l_tot) + 1e-12)

    planets, eccs, incls = [], [], []
    for b in live:
        if b == c or merges_of[b] < PLANET_MIN_MERGES:
            continue
        rv = pos[b] - pos[c]
        vv = vel[b] - vel[c]
        mu = G * (m[c] + m[b])
        r = np.linalg.norm(rv)
        e_orb = 0.5 * float(vv @ vv) - mu / r
        if e_orb >= 0.0:
            continue
        h = np.cross(rv, vv)
        h2 = float(h @ h)
        eccs.append(math.sqrt(max(0.0, 1.0 + 2.0 * e_orb * h2 / (mu * mu))))
        incls.append(math.degrees(math.acos(max(-1.0, min(1.0,
            float(h @ l_hat) / (math.sqrt(h2) + 1e-12))))))
        planets.append(b)
    if not planets:
        return out

    logT, logA = [], []
    for b in planets:
        ns = st["n_s"][w][b]
        span = abs(st["winding"][w][b])
        if ns < 8 or span < math.pi:
            continue
        t_span = (ns - 1) * SAMPLE_EVERY * DT
        logT.append(math.log(2.0 * math.pi * t_span / span))
        logA.append(math.log(st["r_sum"][w][b] / ns))
    if len(logT) >= 3:
        slope, intercept = np.polyfit(logA, logT, 1)
        pred = np.polyval([slope, intercept], logA)
        ss_res = float(np.sum((np.array(logT) - pred) ** 2))
        ss_tot = float(np.sum((np.array(logT) - np.mean(logT)) ** 2))
        r2 = 1.0 - ss_res / (ss_tot + 1e-12)
    else:
        slope, r2 = 0.0, 0.0

    non_central = M_TOT - float(m[c]) - escaped_mass
    out.update({
        "n_planets": float(len(planets)),
        "ecc_median": float(np.median(eccs)),
        "incl_rms_deg": float(np.sqrt(np.mean(np.square(incls)))),
        "kepler_slope": float(slope),
        "kepler_r2": float(r2),
        "planet_mass_frac": float(sum(m[b] for b in planets))
        / max(non_central, 1e-9),
    })
    return out


def measure_batch(genomes: list[dict]) -> list[dict]:
    """The GPU contract: every genome x restart as one resident batch."""
    st = rollout_states(genomes, N_RESTARTS)
    out = []
    for g in range(len(genomes)):
        runs = [_world_facts(st, g * N_RESTARTS + r) for r in range(N_RESTARTS)]
        arr = {k: np.array([r[k] for r in runs]) for k in runs[0]}
        out.append({
            "central_frac_mean": float(arr["central_frac"].mean()),
            "n_planets_worst": float(arr["n_planets"].min()),
            "n_planets_mean": float(arr["n_planets"].mean()),
            "ecc_median_mean": float(arr["ecc_median"].mean()),
            "incl_rms_deg_mean": float(arr["incl_rms_deg"].mean()),
            "kepler_slope_mean": float(arr["kepler_slope"].mean()),
            "kepler_slope_spread": float(arr["kepler_slope"].max()
                                         - arr["kepler_slope"].min()),
            "kepler_r2_worst": float(arr["kepler_r2"].min()),
            "planet_mass_frac_worst": float(arr["planet_mass_frac"].min()),
            "merges_late_worst": float(arr["merges_late"].max()),
            "escaped_frac_worst": float(arr["escaped_frac"].max()),
            "lz_drift_worst": float(arr["lz_drift"].max()),
            "spin_l_frac_mean": float(arr["spin_l_frac"].mean()),
        })
    return out


def render_winner(trained_json: str, png_path: str) -> str:
    """Grow the trained winner once more WITH trajectory snapshots and paint
    the system: top view (the disk), edge view (the flattening), trails for
    every body, gold star, mass-scaled planets. The picture the whole rung
    was for: a solar system nobody placed."""
    import json
    from pathlib import Path

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    genome = json.load(open(trained_json))["genome"]
    st = rollout_states([genome], restarts=N_RESTARTS, snapshot_every=40)
    per_world = [_world_facts(st, w) for w in range(N_RESTARTS)]
    w = int(np.argmax([f["n_planets"] + f["kepler_r2"] for f in per_world]))
    facts = per_world[w]

    snaps_pos = np.array([s[0][w] for s in st["snaps"]])      # (S, N0, 3)
    snaps_m = np.array([s[1][w] for s in st["snaps"]])        # (S, N0)

    # Survivor table — the diagnosis view theory kept missing.
    me, pe, ve = st["m"][w], st["pos"][w], st["vel"][w]
    cw = int(np.argmax(me))
    print(f"world {w}: central mass {me[cw]/M_TOT*100:.1f}%  survivors:")
    for b in np.flatnonzero(me > 0):
        if b == cw:
            continue
        rv = pe[b] - pe[cw]
        vv = ve[b] - ve[cw]
        mu = G * (me[cw] + me[b])
        r = np.linalg.norm(rv)
        e_orb = 0.5 * float(vv @ vv) - mu / r
        a_el = -mu / (2 * e_orb) if e_orb < 0 else float("inf")
        h2 = float(np.cross(rv, vv) @ np.cross(rv, vv))
        ecc = math.sqrt(max(0.0, 1.0 + 2.0 * e_orb * h2 / (mu * mu)))
        print(f"  body {b:3d}: m={me[b]/M_TOT*100:5.1f}%  seeds={st['merges_of'][w][b]:3d}  "
              f"r_now={r:6.2f}  a={a_el:6.2f}  e={ecc:5.2f}")
    m_end = st["m"][w]
    pos_end = st["pos"][w]
    alive = m_end > 0.0
    c = int(np.argmax(m_end))
    lim = 2.2

    fig, (ax1, ax2) = plt.subplots(
        1, 2, figsize=(15, 7.6), facecolor="#06060e",
        gridspec_kw={"width_ratios": [1.0, 1.0]})
    for ax, (ix, iy), title in ((ax1, (0, 1), "top view - the disk"),
                                (ax2, (0, 2), "edge view - the flattening")):
        ax.set_facecolor("#06060e")
        for b in range(N0):
            tr = snaps_pos[:, b, (ix, iy)]
            ok = (snaps_m[:, b] > 0) & (np.abs(snaps_pos[:, b]).max(1) < 20)
            if ok.sum() < 2:
                continue
            if b == c:
                col, a_, lw = "#ffd35c", 0.9, 1.2
            elif alive[b]:
                col, a_, lw = plt.cm.cool(0.15 + 0.7 * (b / N0)), 0.85, 0.9
            else:
                col, a_, lw = "#3a3a55", 0.35, 0.5
            ax.plot(tr[ok, 0], tr[ok, 1], color=col, alpha=a_, lw=lw)
        for b in np.flatnonzero(alive):
            r_dot = 40.0 * (m_end[b] / M_TOT) ** (1.0 / 3.0) + 2.0
            ax.scatter(pos_end[b, ix], pos_end[b, iy],
                       s=r_dot ** 2 if b == c else r_dot ** 1.6,
                       color="#ffd35c" if b == c else "#8fe8ff",
                       zorder=5, edgecolors="none")
        ax.set_xlim(-lim, lim)
        ax.set_ylim(-lim, lim)
        ax.set_aspect("equal")
        ax.set_title(title, color="#c9c9e0", fontsize=11)
        ax.tick_params(colors="#55556a", labelsize=7)
        for s in ax.spines.values():
            s.set_color("#22223a")
    fig.suptitle(
        "GROWN, NOT PLACED - a solar system from a seeded cloud\n"
        f"star {facts['central_frac']*100:.0f}% of mass | "
        f"{facts['n_planets']:.0f} planets | Kepler slope "
        f"{facts['kepler_slope']:.2f} (law: 1.50) r2 {facts['kepler_r2']:.3f} | "
        f"ecc median {facts['ecc_median']:.2f} | disk rms "
        f"{facts['incl_rms_deg']:.1f} deg | L_z drift {facts['lz_drift']:.1e}",
        color="#e8e8f8", fontsize=10)
    out = Path(png_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"rendered world {w}: {out}")
    return str(out)


def export_catalog(trained_json: str, out_json: str) -> str:
    """THE RUNG HANDOFF: grow the trained winner's N_RESTARTS systems once and
    write every surviving planet as (m_rel, a, e) — the solar rung's output
    coalesced into data the planet-averages rung consumes. Each planet is ONE."""
    import json
    from pathlib import Path

    genome = json.load(open(trained_json))["genome"]
    st = rollout_states([genome], restarts=N_RESTARTS)
    systems = []
    for w in range(N_RESTARTS):
        m, pos, vel = st["m"][w], st["pos"][w], st["vel"][w]
        merges = st["merges_of"][w]
        c = int(np.argmax(m))
        planets = []
        for b in np.flatnonzero(m > 0):
            if b == c or merges[b] < PLANET_MIN_MERGES:
                continue
            rv, vv = pos[b] - pos[c], vel[b] - vel[c]
            mu = G * (m[c] + m[b])
            r = float(np.linalg.norm(rv))
            e_orb = 0.5 * float(vv @ vv) - mu / r
            if e_orb >= 0.0:
                continue
            h = np.cross(rv, vv)
            ecc = math.sqrt(max(0.0, 1.0 + 2.0 * e_orb * float(h @ h)
                                / (mu * mu)))
            planets.append({"m_rel": float(m[b] / m[c]),
                            "a": float(-mu / (2.0 * e_orb)),
                            "e": round(ecc, 4)})
        systems.append(sorted(planets, key=lambda p: p["a"]))
    out = Path(out_json)
    out.write_text(json.dumps({
        "source": trained_json, "star_mass_frac": float(
            max(st["m"][w].max() for w in range(N_RESTARTS)) / M_TOT),
        "systems": systems}, indent=1))
    n = sum(len(s) for s in systems)
    print(f"catalog: {len(systems)} systems, {n} planets -> {out}")
    return str(out)


if __name__ == "__main__":
    import argparse
    import json as _json
    import time as _time
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--render", default=None,
                    help="trained json -> grow the winner and paint it")
    ap.add_argument("--png",
                    default=r"E:\PythonChimera\Chimera\Saved\BigBang\solar_system.png")
    ap.add_argument("--export-catalog", default=None,
                    help="trained json -> write bigbang.systems.json for the planet rung")
    a = ap.parse_args()
    if a.export_catalog:
        export_catalog(
            a.export_catalog,
            r"E:\PythonChimera\Chimera\docs\objectives\bigbang.systems.json")
    elif a.render:
        render_winner(a.render, a.png)
    else:
        g0 = {k: s["init"] for k, s in GENOME_SCHEMA.items()}
        rng = np.random.default_rng(7)
        batch = [g0] + [mutate(g0, rng) for _ in range(7)]
        t0 = _time.perf_counter()
        facts = measure_batch(batch)
        dt = _time.perf_counter() - t0
        n_worlds = len(batch) * N_RESTARTS
        print(_json.dumps(facts[0], indent=1))
        print(f"batch: {len(batch)} genomes x {N_RESTARTS} restarts = {n_worlds} "
              f"universes x {STEPS} steps in {dt:.1f}s "
              f"-> {len(batch) / dt:.2f} evals/sec")
        print("(first eval includes Warp kernel compilation)")
