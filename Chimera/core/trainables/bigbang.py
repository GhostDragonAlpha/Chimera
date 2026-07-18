"""bigbang — the cosmic rung: grow a solar system from a seeded cloud, as a trainable domain.

Commissioned 2026-07-18, the human: "Theoretically we should be able to just create a
metaphorical big bang and allow solar systems to form as it were. That would be natural
emergence." And the two refinements that name the architecture: "You just have to think
of it as a multiplication matrix but a three dimensional one. The other thing that
matters is INITIAL CONDITIONS — you seed the universe with the Big Bang correctly and
you create humanity with enough time. Not that we could simulate that. We want to get
as close to that as possible." / "We know TRICKS TO SPEED UP EVOLUTION — that's what's
trained, feature by feature."

THE GENOME SPLITS INTO EXACTLY THOSE TWO HALVES:
    SEED (initial conditions — where all authorship lives once the law is fixed):
        spin      — cloud rotation as a fraction of local circular speed
        flatten0  — initial cloud oblateness (1.0 = a raw sphere; the DISK must emerge)
    SHORTCUTS (tricks that compress un-simulable megayears into the budget):
        merge_scale — collision cross-section scale: gravitational focusing + the
                      whole un-modeled collisional cascade, compressed to a factor
        k_circ      — gas-drag circularization: megayears of nebular gas dynamics
                      as one damping coefficient on radial+vertical motion
The objective then demands we land at the RESEARCHED ATTRACTOR real evolution reaches:
a dominant central mass, a handful of planets, a flat disk, low eccentricities, and
Kepler's third law MEASURED EMPIRICALLY from the grown orbits (log T vs log a slope
-> 1.5). The law is never coded anywhere in this file — it has to emerge, which is
what makes it usable as an objective (it cannot be faked, only produced).

THE PHYSICS (all of it — nothing else is in the loop):
    - Softened pairwise gravity (eps=SOFT), leapfrog kick-drift-kick (symplectic).
    - Perfectly inelastic mergers when two bodies pass within
      merge_scale*(R_i+R_j), R = R0*(m/m0)^(1/3): momentum-conserving, the heavier
      body survives at the pair's barycenter.
    - Circularization drag: only the RADIAL and VERTICAL velocity components damp
      (tangential untouched) — a purely radial/vertical force is TORQUE-FREE about
      z, so it circularizes without stealing orbital angular momentum, which is
      what real nebular gas does to planetesimals.

THE HONESTY LEDGER (L_z, exactly conserved, every leak accounted):
    Pairwise central forces exert zero net torque (d x f = 0, f || d), and leapfrog
    kicks inherit that exactly — so L_z drift measures ONLY floating-point error
    and bookkeeping sins, never "physics". Mergers dump the pair's internal angular
    momentum into body SPIN (planets rotate! — tracked in a spin ledger, an
    emergent bonus fact); escapees carry their L_z out in a removal ledger.
    l_z(alive) + l_z(spin ledger) + l_z(removed ledger) must equal l_z(t0) to
    ~1e-6 or the rollout is dishonest — a HARD objective wall.

WHAT v0 DELIBERATELY IS NOT (honest scope):
    - A planetesimal-scale toy: N0 bodies of equal seed mass. Real mass ratios
      (Sun:Mercury = 6e6) are unreachable at N0=96 — the researched anchors are
      ARCHITECTURE-level (central dominance, Kepler slope, flatness, settledness),
      never absolute masses or Myr timescales.
    - No gas dynamics, no fragmentation, no resonance migration: those are later
      rungs' shortcuts, each to be trained against its own researched attractor.

TOTALITY: every loop is a bounded for. A cloud that collapses into one blob, or
flings itself apart, is REPORTED (walls kill it), not guarded against.

HONEST EVAL (TRAINING_PROTOCOL S3.5): N-body dynamics are chaotic — one rollout is
a coin toss. measure() runs N_RESTARTS fixed-seed restarts (EVAL_SEED + r for every
genome alike) and worst-cases the facts the objective binds.

DOMAIN CONTRACT: seed(rng) -> genome ; mutate(genome, rng) -> genome ;
measure(genome) -> {fact: float}. Facts only — docs/objectives/bigbang.json says
which facts are GOOD.
"""

from __future__ import annotations

import math

import numpy as np

# --- sim settings (test conditions, NOT genome) --------------------------------
N0 = 96                  # planetesimals in the cloud
M_TOT = 1.0              # total cloud mass (G = 1 units)
G = 1.0
R_CLOUD = 1.0            # cloud scale radius
SOFT = 0.005             # gravitational softening
SOFT2 = SOFT * SOFT
R0 = 0.006               # body radius at seed mass m0 (merge cross-sections)
DT = 0.0045
STEPS = 10000            # T_sim = 45 time units (~hundreds of inner orbits)
MERGE_EVERY = 4          # merge pass cadence (steps)
ESCAPE_R = 50.0          # beyond this, a body has left the system (ledgered)
SAMPLE_FRAC = 0.30       # trailing fraction of steps sampled for empirical Kepler
SAMPLE_EVERY = 8
PLANET_MIN_MERGES = 3    # a planet is a body that accreted at least this many seeds
LATE_FRAC = 0.20         # trailing fraction over which "settled" is judged
N_RESTARTS = 5
EVAL_SEED = 20260719
THERMAL_FRAC = 0.05      # velocity noise as a fraction of local circular speed

GENOME_SCHEMA = {
    # --- SEED: the initial conditions ---
    "spin":        {"min": 0.30, "max": 1.05, "init": 0.85},
    "flatten0":    {"min": 0.15, "max": 1.00, "init": 1.00},
    # Radial extent of the cloud. Added after the first GPU training run
    # plateaued at 1-2 planets with central_frac pinned on its FLOOR: a
    # compact collapsed disk is ONE feeding zone, and one feeding zone grows
    # ONE runaway body (real protoplanetary disks are extended - separated
    # feeding zones are why systems have several planets). The optimizer
    # told us the seed was missing a degree of freedom reality has.
    "spread":      {"min": 0.60, "max": 3.00, "init": 1.00},
    # --- SHORTCUTS: compressed evolution ---
    "merge_scale": {"min": 0.80, "max": 4.00, "init": 1.50},
    "k_circ":      {"min": 0.00, "max": 0.80, "init": 0.10},
}


def seed(rng=None) -> dict:
    r = _rand01_fn(rng)
    return {k: s["min"] + r() * (s["max"] - s["min"])
            for k, s in GENOME_SCHEMA.items()}


def mutate(genome: dict, rng=None) -> dict:
    g = _gauss_fn(rng)
    out = dict(genome)
    for k, s in GENOME_SCHEMA.items():
        sigma = (s["max"] - s["min"]) * 0.12
        out[k] = float(min(s["max"], max(s["min"], genome[k] + g(sigma))))
    return out


def _rand01_fn(rng):
    if rng is None:
        rng = np.random.default_rng()
    return rng.random if hasattr(rng, "random") else rng.rand


def _gauss_fn(rng):
    if rng is None:
        rng = np.random.default_rng()
    if hasattr(rng, "normal"):
        return lambda s: float(rng.normal(0.0, s))
    return lambda s: rng.gauss(0.0, s)


# --- the universe ---------------------------------------------------------------

def _accel(pos: np.ndarray, m: np.ndarray) -> np.ndarray:
    """Softened pairwise gravity. Dead bodies have m=0 and contribute nothing.
    This IS the human's 3D multiplication matrix: one uniform law contracted
    over every pair of the state field, every tick."""
    d = pos[None, :, :] - pos[:, None, :]
    r2 = np.einsum("ijk,ijk->ij", d, d) + SOFT2
    inv = r2 ** -1.5
    np.fill_diagonal(inv, 0.0)
    inv *= m[None, :]
    return G * np.einsum("ijk,ij->ik", d, inv)


def _lz(pos: np.ndarray, vel: np.ndarray, m: np.ndarray) -> float:
    """z angular momentum about the origin — the conserved honesty currency."""
    return float(np.sum(m * (pos[:, 0] * vel[:, 1] - pos[:, 1] * vel[:, 0])))


def _rollout(genome: dict, restart: int) -> dict:
    rng = np.random.default_rng(EVAL_SEED + restart)
    spin, flat0 = genome["spin"], genome["flatten0"]
    mscale, k_circ = genome["merge_scale"], genome["k_circ"]

    m0 = M_TOT / N0
    m = np.full(N0, m0)
    merges_of = np.ones(N0, dtype=np.int32)          # seeds absorbed (self counts 1)
    alive = np.ones(N0, dtype=bool)

    spread = float(genome.get("spread", 1.0))        # pre-spread genomes: 1.0
    pos = rng.normal(0.0, spread * R_CLOUD / 2.0, (N0, 3))
    pos[:, 2] *= flat0
    pos -= pos.mean(axis=0)

    rxy = np.hypot(pos[:, 0], pos[:, 1]) + 0.05
    v_circ = np.sqrt(G * M_TOT / rxy)
    tang = np.stack([-pos[:, 1] / rxy, pos[:, 0] / rxy, np.zeros(N0)], axis=1)
    vel = spin * v_circ[:, None] * tang
    vel += rng.normal(0.0, 1.0, (N0, 3)) * (THERMAL_FRAC * v_circ[:, None])
    vel -= (m[:, None] * vel).sum(axis=0) / m.sum()   # zero net momentum

    lz0 = _lz(pos, vel, m)
    lz_spin_ledger = 0.0                              # merger-absorbed internal L
    lz_removed_ledger = 0.0                           # escapees' exported L
    merges_total, merges_late = 0, 0
    late_start = int(STEPS * (1.0 - LATE_FRAC))
    sample_start = int(STEPS * (1.0 - SAMPLE_FRAC))
    theta_hist: list[np.ndarray] = []
    r_hist: list[np.ndarray] = []

    acc = _accel(pos, m)
    for step in range(STEPS):
        vel += 0.5 * DT * acc
        pos += DT * vel
        acc = _accel(pos, m)
        vel += 0.5 * DT * acc

        if k_circ > 0.0:
            # Damp radial + vertical components only (torque-free about z):
            # megayears of nebular gas compressed into one coefficient.
            rho = np.hypot(pos[:, 0], pos[:, 1]) + 1e-9
            rx, ry = pos[:, 0] / rho, pos[:, 1] / rho
            v_r = vel[:, 0] * rx + vel[:, 1] * ry
            f = k_circ * DT
            vel[:, 0] -= f * v_r * rx
            vel[:, 1] -= f * v_r * ry
            vel[:, 2] *= (1.0 - f)

        if step % MERGE_EVERY == 0:
            idx = np.flatnonzero(alive)
            if idx.size > 1:
                sub = pos[idx]
                d = sub[None, :, :] - sub[:, None, :]
                dist = np.sqrt(np.einsum("ijk,ijk->ij", d, d))
                rad = R0 * (m[idx] / m0) ** (1.0 / 3.0)
                thr = mscale * (rad[None, :] + rad[:, None])
                ii, jj = np.nonzero(np.triu(dist < thr, k=1))
                if ii.size:
                    order = np.argsort(dist[ii, jj])
                    used: set[int] = set()
                    for k in order:
                        a, b = int(idx[ii[k]]), int(idx[jj[k]])
                        if a in used or b in used:
                            continue
                        used.add(a)
                        used.add(b)
                        if m[b] > m[a]:
                            a, b = b, a               # a survives
                        lz_before = (
                            m[a] * (pos[a, 0] * vel[a, 1] - pos[a, 1] * vel[a, 0])
                            + m[b] * (pos[b, 0] * vel[b, 1] - pos[b, 1] * vel[b, 0]))
                        mt = m[a] + m[b]
                        pos[a] = (m[a] * pos[a] + m[b] * pos[b]) / mt
                        vel[a] = (m[a] * vel[a] + m[b] * vel[b]) / mt
                        m[a] = mt
                        merges_of[a] += merges_of[b]
                        lz_after = mt * (pos[a, 0] * vel[a, 1]
                                         - pos[a, 1] * vel[a, 0])
                        lz_spin_ledger += lz_before - lz_after   # -> body spin
                        alive[b] = False
                        m[b] = 0.0
                        pos[b] = (1e6 + 10.0 * b, 0.0, 0.0)
                        vel[b] = 0.0
                        merges_total += 1
                        if step >= late_start:
                            merges_late += 1

            # Escapees: ledger their L_z and remove them from the system.
            far = alive & (np.einsum("ij,ij->i", pos, pos) > ESCAPE_R ** 2)
            for b in np.flatnonzero(far):
                lz_removed_ledger += m[b] * (pos[b, 0] * vel[b, 1]
                                             - pos[b, 1] * vel[b, 0])
                alive[b] = False
                m[b] = 0.0
                pos[b] = (1e6 + 10.0 * b, 0.0, 0.0)
                vel[b] = 0.0

            # THE LEDGER'S FIRST CATCH (smoke run: lz_drift 0.527, structural):
            # the next step's first kick would use accelerations computed BEFORE
            # this pass mutated masses/positions — unpaired forces from bodies
            # that no longer exist inject net torque at every merge. Refresh the
            # force field so every kick is torque-free again.
            acc = _accel(pos, m)

        if step >= sample_start and step % SAMPLE_EVERY == 0:
            theta_hist.append(np.where(alive, np.arctan2(pos[:, 1], pos[:, 0]),
                                       np.nan))
            r_hist.append(np.where(alive, np.hypot(pos[:, 0], pos[:, 1]),
                                   np.nan))

    lz_end = _lz(pos, vel, m) + lz_spin_ledger + lz_removed_ledger
    lz_drift = abs(lz_end - lz0) / (abs(lz0) + 1e-12)

    return _facts(pos, vel, m, alive, merges_of, m0,
                  np.array(theta_hist), np.array(r_hist),
                  merges_late, lz_drift, lz_spin_ledger, lz0)


def _facts(pos, vel, m, alive, merges_of, m0, theta_hist, r_hist,
           merges_late, lz_drift, lz_spin, lz0) -> dict:
    live = np.flatnonzero(alive)
    escaped_mass = M_TOT - float(m[live].sum()) if live.size else M_TOT
    bad = {"central_frac": 0.0, "n_planets": 0.0, "ecc_median": 1.0,
           "incl_rms_deg": 90.0, "kepler_slope": 0.0, "kepler_r2": 0.0,
           "planet_mass_frac": 0.0, "merges_late": float(merges_late),
           "escaped_frac": escaped_mass / M_TOT, "lz_drift": lz_drift,
           "spin_l_frac": abs(lz_spin) / (abs(lz0) + 1e-12)}
    if live.size == 0:
        return bad

    c = live[int(np.argmax(m[live]))]                 # the star, if one formed
    central_frac = float(m[c] / M_TOT)
    others = [b for b in live if b != c]

    # Two-body orbital elements about the central body; inclination vs the
    # system's own total angular momentum axis (the invariable plane).
    l_tot = np.zeros(3)
    for b in live:
        l_tot += m[b] * np.cross(pos[b], vel[b])
    l_hat = l_tot / (np.linalg.norm(l_tot) + 1e-12)

    planets, eccs, incls = [], [], []
    for b in others:
        if merges_of[b] < PLANET_MIN_MERGES:
            continue
        rv = pos[b] - pos[c]
        vv = vel[b] - vel[c]
        mu = G * (m[c] + m[b])
        r = np.linalg.norm(rv)
        e_orb = 0.5 * float(vv @ vv) - mu / r
        if e_orb >= 0.0:
            continue                                   # unbound: not a planet
        h = np.cross(rv, vv)
        h2 = float(h @ h)
        ecc = math.sqrt(max(0.0, 1.0 + 2.0 * e_orb * h2 / (mu * mu)))
        incl = math.degrees(math.acos(
            max(-1.0, min(1.0, float(h @ l_hat) / (math.sqrt(h2) + 1e-12)))))
        planets.append(b)
        eccs.append(ecc)
        incls.append(incl)

    if not planets:
        out = dict(bad)
        out["central_frac"] = central_frac
        return out

    # EMPIRICAL Kepler: period from unwrapped angular rate over the sampled
    # window, size from the mean sampled radius. The 1.5 slope is never
    # assumed — it either emerges from the grown orbits or the fit says no.
    logT, logA = [], []
    for b in planets:
        th = theta_hist[:, b]
        rr = r_hist[:, b]
        ok = np.isfinite(th) & np.isfinite(rr)
        if ok.sum() < 8:
            continue
        th_u = np.unwrap(th[ok])
        span = abs(th_u[-1] - th_u[0])
        if span < math.pi:                             # under half an orbit: skip
            continue
        t_span = (ok.sum() - 1) * SAMPLE_EVERY * DT
        period = 2.0 * math.pi * t_span / span
        logT.append(math.log(period))
        logA.append(math.log(float(np.nanmean(rr[ok]))))
    if len(logT) >= 3:
        slope, intercept = np.polyfit(logA, logT, 1)
        pred = np.polyval([slope, intercept], logA)
        ss_res = float(np.sum((np.array(logT) - pred) ** 2))
        ss_tot = float(np.sum((np.array(logT) - np.mean(logT)) ** 2))
        r2 = 1.0 - ss_res / (ss_tot + 1e-12)
    else:
        slope, r2 = 0.0, 0.0

    non_central = M_TOT - float(m[c]) - escaped_mass
    planet_mass = float(sum(m[b] for b in planets))
    return {
        "central_frac": central_frac,
        "n_planets": float(len(planets)),
        "ecc_median": float(np.median(eccs)),
        "incl_rms_deg": float(np.sqrt(np.mean(np.square(incls)))),
        "kepler_slope": float(slope),
        "kepler_r2": float(r2),
        "planet_mass_frac": planet_mass / max(non_central, 1e-9),
        "merges_late": float(merges_late),
        "escaped_frac": escaped_mass / M_TOT,
        "lz_drift": lz_drift,
        "spin_l_frac": abs(lz_spin) / (abs(lz0) + 1e-12),
    }


# --- the domain measure ----------------------------------------------------------

def measure(genome: dict) -> dict:
    """FACTS ONLY, worst-cased across N_RESTARTS fixed-seed restarts."""
    runs = [_rollout(genome, r) for r in range(N_RESTARTS)]
    arr = {k: np.array([r[k] for r in runs]) for k in runs[0]}
    return {
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
    }


if __name__ == "__main__":
    import json as _json
    import time as _time
    g = {k: s["init"] for k, s in GENOME_SCHEMA.items()}
    t0 = _time.perf_counter()
    facts = measure(g)
    dt = _time.perf_counter() - t0
    print(_json.dumps(facts, indent=1))
    print(f"one eval ({N_RESTARTS} restarts x {STEPS} steps, N0={N0}): "
          f"{dt:.1f}s -> {1.0 / dt:.3f} evals/sec/worker")
