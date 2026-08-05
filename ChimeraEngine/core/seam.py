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
