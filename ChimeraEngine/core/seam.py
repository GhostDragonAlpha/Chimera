"""seam.py -- Stage 9: the saturated-density contact carries a body, and propagates sound.

THE INTEGRATION the refutation earned (docs/THE_TWO_FORCES.md Stage 8 v2 -> Stage 9). If contact
really is the overlap of density packets, then the SAME stiffness that closed the grain-pair seam
must also do the two other jobs a contact law has:

  1. CARRY A BODY.  theHuman's published weight on theGround's published grains, and the answer
     must be consistent with what theGround already says a footprint does.
  2. CARRY A WAVE.  Contact stiffness is what sound IS. A chain of packets must propagate a
     compression front at the speed the material's own bulk modulus and density command -- and
     aSaltOcean publishes its sound speed from an oceanographic T/S formula that knows nothing
     about contact mechanics. That is a number this model was never fitted to.

THE TWO DERIVED IDENTITIES everything here rests on, both pure geometry, no chosen constant:

  STIFFNESS.  At first touch the lens force F = (pi B/8)(4R^2 - d^2) has slope
      k = pi B R / 2 = B * (pi R^2) / (2R)
  -- which is EXACTLY the rod stiffness E*A/L of the sphere's own great circle across the centre
  spacing. The packet chain is stiff like a rod of its own cross-section. Nobody arranged that;
  it falls out of the lens volume.

  INERTIA.  A line of touching spheres fills 2/3 of its bounding cylinder ((4/3)pi R^3 over
  pi R^2 * 2R) -- the LINEAR PACKING FRACTION, exactly 2/3. So the chain has a rod's stiffness
  with two thirds of a rod's mass, and must therefore run sqrt(3/2) = 1.2247x faster than the
  continuum:
      c_chain = 2R sqrt(k/m) = sqrt(3B / (2 rho0)) = c_continuum / sqrt(2/3)
  The 1.2247 is not a correction factor anyone fitted -- it is the inverse root of a packing
  fraction that can be computed from a sphere and a cylinder.

NAMED LIMITS, stated before anyone measures around them:
  * NO DISSIPATION. The force is conservative (proven in test_overlap), so restitution is exactly
    1.0 and a dropped packet returns to its drop height forever. Real contact damps. A dissipative
    term is UNBUILT.
  * LINEAR, NOT HERTZIAN. k is finite at zero penetration, so a light load reads as stiff as
    solid rock. Hertz (k ~ sqrt(h)) is the named refinement; where it matters is measured here
    rather than argued (`softening_robustness`).
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

_ROOT = Path(__file__).resolve().parents[2]
_STORY = _ROOT / "story"
if str(_STORY) not in sys.path:
    sys.path.insert(0, str(_STORY))

from ChimeraEngine.core.overlap import rest_radius, saturated_force  # noqa: E402

# The linear packing fraction of touching spheres, COMPUTED from the two volumes rather than
# quoted: (4/3) pi R^3 / (pi R^2 * 2R). Independent of R, as a fraction must be.
LINEAR_PACKING = ((4.0 / 3.0) * math.pi) / (math.pi * 2.0)      # = 2/3, exactly


def contact_stiffness(m: float, B: float, rho0: float) -> float:
    """k = pi B R / 2 at first touch, with R the packet's rest radius (mass at rest density)."""
    return math.pi * float(B) * rest_radius(m, rho0) / 2.0


def rod_stiffness_of_great_circle(m: float, B: float, rho0: float) -> float:
    """The SAME number by the other route: E*A/L for the sphere's great circle over the centre
    spacing. Written separately so the identity is a test, not a comment."""
    r = rest_radius(m, rho0)
    return float(B) * (math.pi * r * r) / (2.0 * r)


def chain_speed_derived(B: float, rho0: float) -> float:
    """c_chain = sqrt(3B / 2 rho0) -- note it carries NO R: the wave speed of a packet chain is
    independent of packet size, which is what makes it a statement about the material."""
    return math.sqrt(1.5 * float(B) / float(rho0))


def continuum_speed(B: float, rho0: float) -> float:
    """c = sqrt(B/rho) -- the chain speed with the derived packing fraction taken back out."""
    return math.sqrt(float(B) / float(rho0))


def pair_force_equal(d, r: float, B: float):
    """The lens force for EQUAL packets, vectorised: F = (pi B / 8)(4R^2 - d^2), zero outside
    contact. Same closed form as overlap.saturated_force -- the identity is CHECKED in
    test_seam.py rather than trusted, because a second copy of a formula is exactly where a
    silent divergence lives."""
    d = np.asarray(d, dtype=np.float64)
    f = (math.pi * float(B) / 8.0) * (4.0 * r * r - d * d)
    return np.where((d > 0.0) & (d < 2.0 * r), f, 0.0)


def pair_pe_equal(d, r: float, B: float):
    """U(d) = (B/2) V_lens for EQUAL packets, vectorised: pi B (2R-d)^2 (d^2+4Rd) / (24 d).

    IT IS WRITTEN FROM THE REFEREED FORM ON PURPOSE. The first version of this integrated the
    force by hand and got the SIGN BACKWARDS -- U came out negative, the pulse energy with it, and
    every energy ratio downstream exploded to -1e8 while an `imbalance <= tol` check passed
    vacuously on the negative number. Two lessons kept as code: derive the potential from the
    energy that already has a referee, and never write a tolerance check that a negative value
    can satisfy."""
    d = np.asarray(d, dtype=np.float64)
    safe = np.where(d > 0.0, d, 1.0)
    u = math.pi * float(B) * (2.0 * r - safe) ** 2 * (safe * safe + 4.0 * r * safe) / (24.0 * safe)
    return np.where((d > 0.0) & (d < 2.0 * r), u, 0.0)


def impactor_decay(n_grains: int, m_imp: float, m: float, B: float, rho0: float, v0: float,
                   steps_per_period: int = 200, n_efold: float = 3.0):
    """THE IMPACT ROUTE TO Z, and the cleanest statement damping has here.

    A mass striking a semi-infinite medium decelerates as v(t) = v0 exp(-Z t / M): classical, and
    it names the impedance directly. This runs an impactor into a chain whose contacts are PURELY
    ELASTIC -- there is no damping term in this code path at all -- and fits the decay. If the
    measured rate is Z/M with Z = sqrt(km), the "damping coefficient" was never a free parameter;
    it is what the medium does.

    The fit window is DERIVED, not chosen: it starts after the contact spring's own transient
    (5 sqrt(M/k)) and ends before the wave could return from the chain's far end. Returns
    (rate_measured, rate_predicted, r2, far_grain_speed).
    """
    r = rest_radius(m, rho0)
    a0 = 2.0 * r
    k = math.pi * float(B) * a0 / 4.0
    z = math.sqrt(k * m)
    c = a0 * math.sqrt(k / m)
    dt = (2.0 * math.pi * math.sqrt(m / k)) / float(steps_per_period)
    t1 = 5.0 * math.sqrt(m_imp / k)
    # TWO CEILINGS, both derived: the wave must not have returned from the far end, AND the fit
    # must not run so deep into the decay that it is fitting numerical dust. At M/m = 40 the
    # chain-only window was 8 e-foldings -- v had fallen by e^-8 and R^2 dropped to 0.976, which
    # is the fit reporting on the residue rather than the physics. `n_efold` is a fit-window
    # resolution, and the test checks the answer is INSENSITIVE to it rather than trusting it.
    t2 = min(0.80 * (n_grains * a0) / c, t1 + n_efold * m_imp / z)
    n_steps = int(t2 / dt)

    x = np.arange(n_grains, dtype=np.float64) * a0
    v = np.zeros(n_grains)
    xi, vi = -a0, float(v0)
    ts, vs = [], []

    def forces(xx):
        fp = pair_force_equal(xx[1:] - xx[:-1], r, B)
        f = np.zeros(n_grains)
        f[:-1] -= fp
        f[1:] += fp
        return f

    f = forces(x)
    fc = float(pair_force_equal(np.array([x[0] - xi]), r, B)[0])
    f[0] += fc
    fi = -fc
    for s in range(n_steps):
        vi += 0.5 * dt * fi / m_imp
        v += 0.5 * dt * f / m
        xi += dt * vi
        x += dt * v
        f = forces(x)
        fc = float(pair_force_equal(np.array([x[0] - xi]), r, B)[0])
        f[0] += fc
        fi = -fc
        vi += 0.5 * dt * fi / m_imp
        v += 0.5 * dt * f / m
        t = (s + 1) * dt
        if t1 <= t <= t2 and vi > 0.0:
            ts.append(t)
            vs.append(vi)

    if len(ts) < 50:
        raise RuntimeError(f"only {len(ts)} samples in the derived fit window -- widen the chain, "
                           f"do not widen the tolerance")
    ts_a = np.asarray(ts)
    lv = np.log(np.asarray(vs))
    slope, icpt = np.polyfit(ts_a, lv, 1)
    pred = slope * ts_a + icpt
    r2 = 1.0 - float(np.sum((lv - pred) ** 2)) / max(float(np.sum((lv - lv.mean()) ** 2)), 1e-300)
    return -slope, z / m_imp, r2, float(abs(v[-1]))


def simulate_chain(n_grains: int, m: float, B: float, rho0: float, v_drive: float,
                   steps_per_period: int = 120, cross_margin: float = 1.25,
                   trigger_frac: float = 1e-6):
    """A 1D chain of packets, velocity-Verlet, driven by a PISTON on grain 0.

    Returns (c_measured, r2, dt).

    TWO THINGS THIS GETS RIGHT THAT THE FIRST VERSION DID NOT, both recorded because each was a
    real defect the run caught:

      RUN LENGTH IS DERIVED, NOT CHOSEN. The first version ran 3 oscillation periods, in which
      the front crosses only ~19 of 60 grains -- the other 41 never moved, their arrival times
      stayed at zero, and the fit returned a NEGATIVE speed at R^2 = 0.06. The horizon is now
      the time the front needs to cross the chain at the DERIVED speed, times a margin. A
      simulation window that is not tied to the thing being measured is an instrument set to
      the wrong scale.

      ARRIVAL IS FIRST MOTION, AGAINST AN EXTERNAL REFERENCE. The threshold is a millionth of
      the PISTON speed -- an input, not a statistic of the signal being measured. (Timing the
      peak instead fails here for a real physical reason: with no adhesion the chain separates
      behind the front, so the largest excursion at a grain need not be the front at all.)
    """
    r = rest_radius(m, rho0)
    a = 2.0 * r
    k = contact_stiffness(m, B, rho0)
    period = 2.0 * math.pi * math.sqrt(m / k)
    dt = period / float(steps_per_period)
    length = (n_grains - 1) * a
    n_steps = int(cross_margin * length / chain_speed_derived(B, rho0) / dt)

    x = np.arange(n_grains, dtype=np.float64) * a
    v = np.zeros(n_grains)
    v[0] = +v_drive                                    # TOWARD grain 1: a compression piston
    arrival = np.full(n_grains, np.nan)
    arrival[0] = 0.0
    trigger = v_drive * float(trigger_frac)

    def forces(xx):
        fp = pair_force_equal(xx[1:] - xx[:-1], r, B)
        f = np.zeros(n_grains)
        f[:-1] -= fp
        f[1:] += fp
        return f

    f = forces(x)
    for s in range(n_steps):
        v += 0.5 * dt * f / m
        x += dt * v
        f = forces(x)
        v += 0.5 * dt * f / m
        v[0] = +v_drive                                # the piston holds its speed
        f[0] = 0.0
        new = np.isnan(arrival) & (np.abs(v) > trigger)
        arrival[new] = (s + 1) * dt

    lo, hi = max(2, n_grains // 6), n_grains - max(2, n_grains // 6)
    idx = np.arange(lo, hi)
    if np.any(np.isnan(arrival[idx])):
        raise RuntimeError(
            f"the front did not cross the measurement window in {n_steps} steps -- "
            f"{int(np.isnan(arrival[idx]).sum())} of {len(idx)} grains never moved. "
            f"Raise cross_margin; do NOT fit around it.")
    dist = idx * a
    slope, icpt = np.polyfit(dist, arrival[idx], 1)
    pred = slope * dist + icpt
    ss_res = float(np.sum((arrival[idx] - pred) ** 2))
    ss_tot = float(np.sum((arrival[idx] - arrival[idx].mean()) ** 2))
    r2 = 1.0 - ss_res / max(ss_tot, 1e-300)
    return 1.0 / slope, r2, dt


def measure_mode_speed(n_grains: int, m: float, B: float, rho0: float,
                       precompress_frac: float = 1e-4, amp_frac: float = 0.1,
                       steps_per_period: int = 200, n_periods: float = 4.0):
    """THE SOUND SPEED, measured with NO THRESHOLD ANYWHERE -- and this is the instrument that
    replaced a wrong one.

    WHY THE FRONT MEASUREMENT WAS NOT THIS. `simulate_chain` times a wavefront's first arrival
    against a fraction of the piston speed, and its answer DEPENDS ON THAT FRACTION: measured
    1795.0 / 1824.7 / 1878.8 / 1928.8 / 1975.6 / 2069.3 m/s at triggers 3e-1 ... 1e-6, i.e. up
    to 15% above the acoustic speed. That is a real property of a discrete lattice -- nearest-
    neighbour coupling puts an exponentially small PRECURSOR ahead of the energy-carrying front,
    so a lower trigger always reports a faster "arrival". The threshold being an EXTERNAL number
    (the piston's own speed) did not save it: external or not, it defines a quantity that is not
    the sound speed. An instrument needs an instrument.

    WHAT THIS DOES INSTEAD. Excite the chain's fundamental standing mode and time its period.
    A period is an integral property of the whole oscillation -- there is nothing to threshold.
    The chain is lightly PRE-COMPRESSED (a physical requirement, not a numerical one: at exactly
    zero penetration the tension half-cycle would separate grains that cannot pull), and the
    exact discrete dispersion is used, so the finite-N correction is derived rather than assumed:

        omega = 2 sqrt(k/m) sin(q a / 2)      =>      c = (omega/q) * (q a/2) / sin(q a/2)

    Returns (c_measured, c_predicted, period_measured).
    """
    r = rest_radius(m, rho0)
    h0 = float(precompress_frac) * r
    a0 = 2.0 * r - h0
    k0 = math.pi * float(B) * a0 / 4.0                 # exact -dF/dd at the compressed spacing
    length = (n_grains - 1) * a0
    q = math.pi / length
    theta = q * a0 / 2.0
    c_pred = a0 * math.sqrt(k0 / m)
    omega_pred = 2.0 * math.sqrt(k0 / m) * math.sin(theta)
    dt = (2.0 * math.pi * math.sqrt(m / k0)) / float(steps_per_period)
    n_steps = int(n_periods * (2.0 * math.pi / omega_pred) / dt)

    j = np.arange(n_grains, dtype=np.float64)
    x0 = j * a0
    x = x0 + amp_frac * h0 * np.sin(math.pi * j / (n_grains - 1))
    v = np.zeros(n_grains)
    mid = (n_grains - 1) // 2

    def forces(xx):
        fp = pair_force_equal(xx[1:] - xx[:-1], r, B)
        f = np.zeros(n_grains)
        f[:-1] -= fp
        f[1:] += fp
        f[0] = 0.0
        f[-1] = 0.0                                    # fixed ends
        return f

    f = forces(x)
    prev = x[mid] - x0[mid]
    crossings = []
    for s in range(n_steps):
        v += 0.5 * dt * f / m
        x += dt * v
        f = forces(x)
        v += 0.5 * dt * f / m
        v[0] = v[-1] = 0.0
        cur = x[mid] - x0[mid]
        if prev != 0.0 and (cur < 0.0) != (prev < 0.0):
            t_cross = (s + 1) * dt - dt * cur / (cur - prev)    # linear interpolation
            crossings.append(t_cross)
        prev = cur

    if len(crossings) < 3:
        raise RuntimeError(f"only {len(crossings)} zero crossings in {n_steps} steps -- "
                           f"the mode did not oscillate; do not fit around this")
    period = 2.0 * float(np.mean(np.diff(crossings)))
    omega = 2.0 * math.pi / period
    return (omega / q) * (theta / math.sin(theta)), c_pred, period


def chain_energy(x: np.ndarray, v: np.ndarray, m: float, B: float, rho0: float) -> float:
    from ChimeraEngine.core.overlap import saturated_energy
    r = rest_radius(m, rho0)
    ke = 0.5 * m * float(np.sum(v * v))
    pe = sum(saturated_energy(m, r, m, r, float(x[i + 1] - x[i]), B, rho0)
             for i in range(len(x) - 1))
    return ke + pe


# ── THE BODY ON THE GROUND ───────────────────────────────────────────────────────────────────────
def grain_number_density(porosity: float, r: float) -> float:
    """Grains per m^3 of ground: the solid fraction divided by one grain's volume. Read from the
    membrane's published porosity and median grain size -- nothing chosen."""
    return (1.0 - float(porosity)) / ((4.0 / 3.0) * math.pi * float(r) ** 3)


def grain_areal_density(porosity: float, r: float) -> float:
    """Grains per m^2 of surface = (grains per m^3)^(2/3) -- the standard dimensional reduction,
    exact for a cubic arrangement and the right order for any."""
    return grain_number_density(porosity, r) ** (2.0 / 3.0)


def column_modulus(B: float, porosity: float, r: float) -> float:
    """The effective Young's modulus of a column of contact-coupled grains:
        sigma = F * n_area,  eps = h/(2R) = F/(pi B R^2)   =>   E_eff = n_area * pi B R^2
    This is where the LINEAR contact law shows its hand: E_eff comes out near-solid, because k
    does not vanish at zero penetration the way Hertz's does. Measured, not hidden."""
    return grain_areal_density(porosity, r) * math.pi * float(B) * float(r) ** 2


def elastic_settlement(pressure_Pa: float, influence_depth_m: float,
                       B: float, porosity: float, r: float) -> float:
    """How far the ground's ELASTIC contacts compress under a footing's pressure. The influence
    depth is the footing's own equivalent width (sqrt of its published area) -- the standard
    shallow-foundation scale, taken from theHuman's numbers rather than picked."""
    return float(pressure_Pa) / column_modulus(B, porosity, r) * float(influence_depth_m)


def softening_robustness(pressure_Pa: float, influence_depth_m: float, B: float,
                         porosity: float, r: float, factor: float) -> float:
    """The same settlement with the contact law softened by `factor` -- the honest way to ask
    whether a conclusion depends on the linear-vs-Hertz choice. Softening B softens k in exactly
    the same proportion, so this brackets the whole family."""
    return elastic_settlement(pressure_Pa, influence_depth_m, B / float(factor), porosity, r)


# ═══ STAGE 10: DAMPING IS NOT A PARAMETER -- IT IS THE MEDIUM ════════════════════════════════════
# THE STATEMENT. A struck grain does not lose energy to a fitted coefficient; it launches a
# compression wave into the material behind it and that energy never comes back. What a truncated
# simulation calls "damping" is the IMPEDANCE of the medium it truncated:
#
#     Z = sqrt(k m)          (chain)   =   sqrt(2/3) * sqrt(B rho0) * pi R^2   (continuum)
#
# and the two routes agree through the SAME computed linear packing fraction that set the wave
# speed -- the chain carries a rod's stiffness with 2/3 a rod's mass, so it carries sqrt(2/3) of a
# rod's impedance. Nothing here is chosen; `test_damping.py` checks the identity rather than
# trusting it.
#
# THE PROOF THAT Z IS THE MEDIUM AND NOT A KNOB is a dyad: run one impact TWICE -- once against an
# explicit chain with PURELY ELASTIC contacts (no damping term exists anywhere in that run; the
# energy leaves as sound), and once against a single dashpot Z. If the restitutions agree, the
# dashpot IS the chain, summarised. That is the only sense in which this model may be said to
# have damping.

def radiation_impedance(m: float, B: float, rho0: float, d: float = None) -> float:
    """Z = sqrt(k m) -- the characteristic impedance of a chain of these packets. `d` is the
    contact separation if the chain is pre-compressed (k = pi B d / 4); defaults to first touch."""
    r = rest_radius(m, rho0)
    dd = 2.0 * r if d is None else float(d)
    k = math.pi * float(B) * dd / 4.0
    return math.sqrt(k * float(m))


def continuum_impedance(m: float, B: float, rho0: float) -> float:
    """The same impedance by the other route: sqrt(2/3) * (rho0 c) * A for the great circle.
    Written separately so the agreement is a test, not an assertion."""
    r = rest_radius(m, rho0)
    return math.sqrt(LINEAR_PACKING) * math.sqrt(float(B) * float(rho0)) * math.pi * r * r


def simulate_reflection(n_grains: int, m: float, B: float, rho0: float, term_factor: float,
                        pulse_width_grains: float = 12.0, amp_frac: float = 0.05,
                        precompress_frac: float = 1e-3, steps_per_period: int = 200):
    """Launch a purely RIGHTWARD long-wavelength pulse and ask what the right-hand terminator
    reflects. Both ends carry dashpots: the LEFT one at exactly Z (perfect, so returning energy is
    captured and cannot bounce again), the RIGHT one at term_factor * Z (the thing under test).

    Reflection is then read off the two absorbed totals with no timing window and no threshold:
        R = E_absorbed_left / E_0      T = E_absorbed_right / E_0      R + T = 1 (checked)
    Transmission-line theory predicts R = ((f-1)/(f+1))^2 for f = Z_term/Z: 0 at f=1, 1/9 at f=2
    and at f=1/2, and 1 at f=0 (a free end reflects everything). Returns (R, T, books_error).
    """
    r = rest_radius(m, rho0)
    h0 = float(precompress_frac) * r
    a0 = 2.0 * r - h0
    k0 = math.pi * float(B) * a0 / 4.0
    c = a0 * math.sqrt(k0 / m)
    z = math.sqrt(k0 * m)
    z_right = float(term_factor) * z
    dt = (2.0 * math.pi * math.sqrt(m / k0)) / float(steps_per_period)
    n_steps = int(3.0 * (n_grains * a0 / c) / dt)

    j = np.arange(n_grains, dtype=np.float64)
    x0 = j * a0
    u = amp_frac * h0 * np.exp(-(((j - 0.25 * n_grains) / pulse_width_grains) ** 2))
    v = -c * np.gradient(u, a0)                        # v = -c du/dx  =>  purely rightward
    x = x0 + u

    u_ref = float(pair_pe_equal(np.array([a0]), r, B)[0])

    def pair_pe(xx):
        # relative to the uniform pre-compressed state: the PULSE's own energy, nothing else
        return float(np.sum(pair_pe_equal(xx[1:] - xx[:-1], r, B) - u_ref))

    def forces(xx):
        fp = pair_force_equal(xx[1:] - xx[:-1], r, B)
        f = np.zeros(n_grains)
        f[:-1] -= fp
        f[1:] += fp
        return f

    # THE CONFINING CLAMP, and it is not optional. A pre-compressed chain with FREE ends is not
    # in equilibrium: grain 0 has a neighbour pushing it outward and nothing pushing back, so the
    # whole chain relaxes explosively and the dashpots absorb THAT instead of the pulse. (First
    # run: R and T both ~3.8e5 -- the static release dwarfing the signal by five orders.) A
    # constant end force equal to the pre-compression's own F(a0) balances the ends exactly, which
    # is what a confining pressure physically is.
    f_clamp = float(pair_force_equal(np.array([a0]), r, B)[0])

    def total_forces(xx, vv):
        f = forces(xx)
        f[0] += f_clamp - z * vv[0]
        f[-1] += -f_clamp - z_right * vv[-1]
        return f

    e0 = 0.5 * m * float(np.sum(v * v)) + pair_pe(x)
    abs_l = abs_r = 0.0
    f = total_forces(x, v)
    for _ in range(n_steps):
        v += 0.5 * dt * f / m
        x += dt * v
        f = total_forces(x, v)
        v += 0.5 * dt * f / m
        abs_l += z * v[0] * v[0] * dt
        abs_r += z_right * v[-1] * v[-1] * dt

    left_over = 0.5 * m * float(np.sum(v * v)) + pair_pe(x)
    books = abs((abs_l + abs_r + left_over) - e0) / e0
    return abs_l / e0, abs_r / e0, books


def simulate_impact_radiating(n_grains: int, m_imp: float, m: float, B: float, rho0: float,
                              v0: float, steps_per_period: int = 400):
    """LEG ONE OF THE DYAD. An impactor strikes a chain whose contacts are PURELY ELASTIC -- there
    is no damping term anywhere in this function. Restitution below 1 can only come from energy
    walking away as sound. The chain is long enough that nothing reflects back during contact
    (checked: the far grain must never move)."""
    r = rest_radius(m, rho0)
    a0 = 2.0 * r
    k = math.pi * float(B) * a0 / 4.0
    dt = (2.0 * math.pi * math.sqrt(m_imp / k)) / float(steps_per_period)
    x = np.arange(n_grains, dtype=np.float64) * a0
    v = np.zeros(n_grains)
    xi = -a0                                            # impactor, just touching grain 0
    vi = float(v0)

    def forces(xx):
        fp = pair_force_equal(xx[1:] - xx[:-1], r, B)
        f = np.zeros(n_grains)
        f[:-1] -= fp
        f[1:] += fp
        return f

    def contact():
        return float(pair_force_equal(np.array([x[0] - xi]), r, B)[0])

    f = forces(x)
    fc = contact()
    f[0] += fc
    fi = -fc
    for _ in range(steps_per_period * 40):
        vi += 0.5 * dt * fi / m_imp
        v += 0.5 * dt * f / m
        xi += dt * vi
        x += dt * v
        f = forces(x)
        fc = contact()
        f[0] += fc
        fi = -fc
        vi += 0.5 * dt * fi / m_imp
        v += 0.5 * dt * f / m
        if fc == 0.0 and vi < 0.0:                      # separated and moving away
            break
    return -vi / v0, float(abs(v[-1]))


def restitution_lumped_series(m_imp: float, m: float, B: float, rho0: float, v0: float,
                              z_factor: float = 1.0, steps: int = 2000000):
    """The medium as ONE dashpot -- IN SERIES with the contact spring, which is the correction the
    explicit chain forced.

    THE REFUTED VERSION AND WHY. This first modelled the medium as a dashpot in PARALLEL with the
    contact stiffness (Kelvin-Voigt), giving zeta = Z/(2 sqrt(kM)) = 0.05 at M = 100m and a lively
    e = 0.859. The radiating chain -- which contains no damping term to argue with -- returned
    e ~ 0.00. The chain was right: the impactor pushes the contact spring, and the spring pushes
    a medium that radiates, so the two act IN SEQUENCE, not side by side. Series inverts the
    damping ratio to zeta = sqrt(kM)/(2Z) = 5, overdamped, and the body lands instead of bouncing.

        M v' = -k h ,   h' = v - (k/Z) h ,   separation when h <= 0

    A wrong topology is invisible to dimensional analysis: both wirings have the same units and
    the same constants, and only a model that could disagree found it.
    """
    r = rest_radius(m, rho0)
    k = math.pi * float(B) * (2.0 * r) / 4.0
    z = float(z_factor) * math.sqrt(k * float(m))
    dt = (2.0 * math.pi * math.sqrt(m_imp / k)) / 20000.0
    h, v = 0.0, float(v0)
    for _ in range(steps):
        v += dt * (-k * h) / m_imp
        h += dt * (v - (k / z) * h)
        if h <= 0.0:
            break
    return v / v0


# ── FRICTION: the tangential half, from an angle this world GREW ────────────────────────────────
# mu = tan(phi) IS the definition of a friction angle, so this is a restatement and is labelled as
# one -- what makes it non-trivial is WHERE phi comes from. theGround's repose angle was not looked
# up: it EMERGED at 40.03 +- 1.55 degrees from the granular trainer's local stochastic rule
# (core/trainables/granular.py), inside the researched lunar-regolith band. So the tangential force
# available to a foot is set by a number this world grew.

def friction_coefficient(repose_deg: float) -> float:
    return math.tan(math.radians(float(repose_deg)))


def max_walkable_slope_deg(mu: float) -> float:
    """A slope is walkable while the required friction stays under what is available; equality is
    the repose angle itself, which is what makes repose the ceiling on standable ground."""
    return math.degrees(math.atan(float(mu)))


def drop_restitution(m: float, B: float, rho0: float, v_impact: float,
                     steps_per_period: int = 400) -> float:
    """Bounce one packet off a fixed one and return v_out/v_in. The force is conservative, so the
    answer must be 1 -- this MEASURES that the model has no dissipation rather than asserting it,
    and any deviation is the integrator, not the physics."""
    r = rest_radius(m, rho0)
    k = contact_stiffness(m, B, rho0)
    dt = (2.0 * math.pi * math.sqrt(m / k)) / float(steps_per_period)
    d = 2.0 * r                                        # start exactly at first touch
    v = -abs(v_impact)
    f = 0.0
    for _ in range(steps_per_period * 4):
        v += 0.5 * dt * f / m
        d += dt * v
        f = saturated_force(m, r, m, r, d, B, rho0)
        v += 0.5 * dt * f / m
        if d >= 2.0 * r and v > 0.0:
            break
    return v / abs(v_impact)
