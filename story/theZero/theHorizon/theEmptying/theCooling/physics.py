"""theCooling -- expansion cools the sea, and each threshold PERMITS a structure to survive.

The parent handed down a hot sea with a temperature and a clock. One law governs this whole
membrane: a bound thing survives once kT drops below what binds it -- delayed by the photon glut,
because 10^9 photons per particle means even the tail keeps breaking things.
"""
from math import exp, log, pi

KB = 1.380649e-23
EV = 1.602176634e-19
HBAR = 1.054571817e-34
H = 6.62607015e-34
C = 2.99792458e8
M_E = 9.1093837015e-31
ZETA3 = 1.2020569

ETA = 6.1e-10                    # baryon-to-photon ratio (measured); the reason every threshold is late
E_DEUTERON = 2.22e6 * EV         # nuclear binding: what holds a nucleus together
E_HYDROGEN = 13.6 * EV           # atomic binding: what holds an electron to a proton
HELIUM_MASS_FRAC = 0.25          # frozen in at nucleosynthesis and never changed since
DELTA = 1.0e-5                   # density contrast at last scattering: one part in 100,000


def permitted_at(E_bind):
    """ESTIMATE of the temperature at which a structure bound by E_bind survives.

    NOT E_bind/k: with eta photons per baryon, the hot tail keeps dissociating until the typical
    photon is ln(1/eta) ~ 21x weaker than the bond. HONEST LIMIT -- this counts photons but not the
    phase space the freed particle has to escape into, so it lands high. For nuclei it gives 1.2e9 K
    where the deuterium bottleneck is ~8e8 K (right to ~50%). For atoms it gave 7438 K where the
    real answer is ~3700 K -- which is why atoms are solved properly below, with Saha."""
    return E_bind / (KB * log(1.0 / ETA))


def saha_ionized_fraction(T):
    """The fraction of hydrogen still ionized at temperature T (Saha equilibrium).

        x^2/(1-x) = (1/n_b) * (2*pi*m_e*k*T/h^2)^(3/2) * exp(-E/kT)

    The right-hand side is the ratio of ways to be FREE versus BOUND: the exponential says the bond
    is hard to break, but the (m_e k T)^(3/2) phase-space term says a freed electron has an enormous
    number of places to go, and 10^9 photons per baryon keep offering. Ionization wins far below
    13.6 eV, which is the whole reason atoms are late."""
    n_gamma = (2.0 * ZETA3 / pi ** 2) * (KB * T / (HBAR * C)) ** 3
    n_b = ETA * n_gamma
    rhs = (2.0 * pi * M_E * KB * T / H ** 2) ** 1.5 / n_b * exp(-E_HYDROGEN / (KB * T))
    return 2.0 / (1.0 + (1.0 + 4.0 / rhs) ** 0.5)      # solve x^2/(1-x) = rhs for x in (0,1)


def atoms_permitted_at(target=0.5):
    """The temperature where half the hydrogen has gone neutral -- solved, not assumed."""
    lo, hi = 500.0, 20000.0
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        if saha_ionized_fraction(mid) > target:
            hi = mid                                    # still too ionized -> the answer is COLDER
        else:
            lo = mid                                    # already neutral -> the answer is hotter
    return 0.5 * (lo + hi)


def derive(parent, free):
    if parent is None or "T" not in parent:
        raise ValueError("theCooling requires a parent sea with a temperature")
    T_nuclei = permitted_at(E_DEUTERON)             # photon-glut estimate: 1.2e9 K (bottleneck ~8e8)
    T_atoms = atoms_permitted_at(0.5)               # SOLVED from Saha, not estimated
    return {
        # ITS REAL SIZE: how far light had got by then. Everything emits at radius ~1 locally, so this is
        # the only place the true scale is recorded -- and a human needs it to know what they see.
        "extent_m": 2.99792458e8 * 3.8e5 * 3.1557e7,
        # ITS OWN DURATION: to recombination: 380,000 years. t=1 in emit() means this much real time.
        "duration_s": 3.8e5 * 3.1557e7,
        "T_start": parent["T"],
        "T_nuclei": T_nuclei,                       # ~1e9 K: nuclei survive
        # `T_atoms` RETIRED: T_end above is the same temperature -- the one atoms formed at, 3760 K, and it is the name theCloud already reads.
        "T_end": T_atoms,
        # DERIVED, not assumed: how many times weaker than the bond the typical photon must be
        "delay_factor": E_HYDROGEN / (KB * T_atoms),
        "hydrogen_frac": 1.0 - HELIUM_MASS_FRAC,
        "helium_frac": HELIUM_MASS_FRAC,
        "transparent": True,                        # nothing left for photons to scatter from
        "delta_rho_over_rho": DELTA,                # what gravity is finally allowed to pull on
        # CARRIED FOR THE CHILD, and it closes a duplicate. eta IS the baryon density -- there are
        # this many baryons for every photon, and the photon count follows from T alone. theCloud
        # was carrying its own separate measurement of the same fact (today's baryon density) and
        # running it back through the redshift. Two independently measured constants standing for
        # one number is how they drift; they currently agree to 0.16%, which is the check, not the
        # excuse. The child now derives rho from this.
        "eta": ETA,
        "n_gamma_per_K3": 2.0288e7,                 # (2 zeta(3)/pi^2)(k/hbar c)^3 -- photons per m^3 per K^3
        "neutral": True,
    }


def emit(nums, t=1.0):
    """The matter of theCooling, in its own local units.

    The movie IS the physics: the sea starts OPAQUE and blue-white hot, and as its own time runs the
    temperature falls, the colour reddens along the blackbody it actually has, and the opacity
    collapses -- because transparency is not a look, it is what happens when there is nothing left to
    scatter from. At the end, faint density contrast is visible: the one part in 100,000 that gravity
    will act on next."""
    import numpy as np
    from matter import blank, fibonacci_sphere, paint, blackbody_rgb, surface_grain, GLOW

    n = 14000
    tt = float(t)
    rng = np.random.default_rng(11)
    d = fibonacci_sphere(n)
    rad = (0.15 + 0.85 * rng.random(n) ** 0.5) * (1.0 + 0.8 * tt)      # the sea expands
    b = blank(n)
    b[:, 0:3] = d * rad[:, None]

    # T falls from the parent's horizon temperature to the atom threshold, log-spaced (T ~ 1/a)
    T0, T1 = float(nums["T_start"]), float(nums["T_end"])
    T = T0 * (T1 / T0) ** tt
    rgb = blackbody_rgb(min(T, 4.0e4))

    opacity = 0.95 * (1.0 - tt) ** 2 + 0.05        # OPAQUE -> transparent, all at once near the end
    # GRAIN SIZE FROM THE SPACING. (It used to divide by 6 to undo a hidden multiplier in the
    # rasteriser; that multiplier is gone, so the number here is now the number that renders.)
    #
    # This read 0.055, which the rasteriser turned into 0.33 -- TEN TIMES the distance between
    # neighbouring grains at this count. Every pixel then accumulated ~100 overlapping splats and the
    # whole sea saturated to a FLAT SALMON DISK with no structure in it: the expansion invisible, the
    # density contrast invisible, a render lying about density. It also put 6,379 splats into one
    # 32-px tile.
    #
    # A soft volume genuinely wants overlap -- that is what makes it read as gas rather than as
    # beads -- so this asks for about twice the closing size, which is a field you can see through.
    grain = 2.0 * surface_grain(n, radius=float(np.median(rad)))
    paint(b, rgb, opacity, grain, GLOW)

    if tt > 0.55:                                   # the density contrast, once there is light to see it by
        m = rng.random(n) < 0.06
        b[m, 19] = min(1.0, opacity * 3.5)
        b[m, 20] = grain * 1.4      # the contrast grains, slightly larger
    return b


def measure(nums):
    """What training must check -- both are facts, not preferences: atoms are permitted LATER than
    nuclei (a weaker bond needs a colder sea), and every threshold is late by the same factor."""
    return {"atoms_after_nuclei": nums["T_atoms"] < nums["T_nuclei"],
            "delay_factor": nums["delay_factor"]}
