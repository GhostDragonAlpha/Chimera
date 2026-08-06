"""
FREE-style constants for the LightEngine kernel.

These are the seed's free numbers — declared ONCE before the first run and
never retuned after a failure.  If the falsifier fires, the verdict is reported
with the metrics that triggered it; the numbers here stay fixed.

Unit convention: positions in "light units" (lu), time in "ticks", and mass /
charge are dimensionless (m = 1, q = 1 for every point).
"""

FREE = {
    # ── Geometry of an identical point ──────────────────────────────
    # R_WALL is the "packet size": the one length a point owns.  It is the
    # inner radius of the short-range resistance wall and sets the scale for
    # the softening and the bond distance.
    "R_WALL": 0.05,

    # R_BOND is the mid-range equilibrium of the resistance spring.
    # Chosen as 3 * R_WALL so a bonded pair sits just outside the wall and
    # still feels strong repulsion if compressed.
    "R_BOND": 0.15,

    # R_C is the neighbor cutoff: beyond this distance the resistance force is
    # exactly zero.  2 * R_BOND keeps the neighbor list small while allowing
    # second-neighbor interactions that can stabilize clumps.
    "R_C": 0.30,

    # P_WALL is the power of the wall repulsion.  A value of 6 gives a steep,
    # short-range wall that prevents point overlap without needing a separate
    # collision event.
    "P_WALL": 6,

    # ── Force strengths ─────────────────────────────────────────────
    # G is the strength of the long-range blind draw.  Set so that gravity
    # and the bond spring are comparable just outside the bond distance
    # (G/r_bond^2 ~ K_BOND*(r - r_bond)/r_bond^2 for a small stretch),
    # letting the two forces compete rather than the draw dominating
    # everywhere outside the wall.
    "G": 0.01,

    # K_WALL is the prefactor of the strong short-range repulsion.  It is set
    # to unity so that the wall is the reference strength against which G and
    # K_BOND are judged.
    "K_WALL": 1.0,

    # K_BOND is the prefactor of the bond spring.  With this value a particle
    # compressed from r_bond to r_wall feels an acceleration of order 1.
    "K_BOND": 1.0,

    # ── Draw softening ──────────────────────────────────────────────
    # EPS softens the inverse-square draw so the point is a packet, not a
    # singularity.  EPS = R_WALL / 2.5 makes the draw Newtonian well outside
    # the wall region.
    "EPS": 0.02,

    # ── Time step ───────────────────────────────────────────────────
    # DT is derived from the fastest interaction: a head-on wall collision at
    # r = R_WALL / 2 produces acceleration
    #     a_max = K_WALL * (R_WALL / r)^P_WALL / r
    #           = K_WALL * 2^(P_WALL + 1) / R_WALL.
    # With P_WALL = 6 this is a_max = 2560 lu / tick^2.  Requiring that a
    # particle cross no more than a fraction f = 0.1 of R_WALL in one step:
    #     dt = sqrt(2 * f * R_WALL / a_max)
    #        = sqrt(2 * 0.1 * 0.05 / 2560) ~ 1.98e-3.
    # We take the more conservative value 5e-4 to also comfortably resolve the
    # bond spring (omega_bond = sqrt(K_BOND / R_BOND) ~ 2.58 / tick, period
    # ~ 2.43 ticks; ~500 steps per period).
    "DT": 5e-4,
}

# Convenience aliases
R_WALL = FREE["R_WALL"]
R_BOND = FREE["R_BOND"]
R_C = FREE["R_C"]
P_WALL = FREE["P_WALL"]
G = FREE["G"]
K_WALL = FREE["K_WALL"]
K_BOND = FREE["K_BOND"]
EPS = FREE["EPS"]
DT = FREE["DT"]
