"""aStar -- the star that actually formed here. Its mass decides everything else about it.

theStar established what a star IS: a fall stopped by fire, above a minimum mass. This membrane is
the instance -- it inherits that star's mass and derives its size, its light, the temperature its
surface is FORCED to sit at, the convection you can see on it, and how long it will last.
"""
from math import pi

SIGMA_SB = 5.670374419e-8
M_SUN = 1.98892e30
R_SUN = 6.957e8
L_SUN = 3.828e26
T_SUN = 5772.0
SUN_LIFETIME_YR = 1.0e10

GRANULE_KM = 1000.0          # measured size of a solar convection cell
GRANULE_DT = 250.0           # K between a granule's bright centre and its dark lane


def radius(M):
    """Main-sequence mass-radius. Empirical, and said so."""
    return R_SUN * (M / M_SUN) ** 0.8


def luminosity(M):
    """Main-sequence mass-luminosity: L ~ M^3.5. Empirical, and said so."""
    return L_SUN * (M / M_SUN) ** 3.5


def surface_temperature(L, R):
    """NOT chosen -- FORCED. Whatever is generated inside must leave through the surface, so the
    surface sits at exactly the temperature that radiates it away: L = 4 pi R^2 sigma T^4."""
    return (L / (4.0 * pi * R * R * SIGMA_SB)) ** 0.25


# THE NAME IS DERIVED, NOT ASSIGNED. Stars are classified by surface temperature -- the Harvard
# sequence O B A F G K M -- and the colour word IS that class. So a membrane's name states what the
# physics found, and measure() checks that the folder is still called the right thing. Rename it
# wrongly and the check fails; change the star's mass and the class (and the name) must change too.
SPECTRAL = [(30000.0, "O", "Blue"), (10000.0, "B", "BlueWhite"), (7500.0, "A", "White"),
            (6000.0, "F", "YellowWhite"), (5200.0, "G", "Yellow"), (3700.0, "K", "Orange"),
            (0.0, "M", "Red")]


def spectral_class(T):
    """(letter, colour) from the surface temperature alone."""
    for t_min, letter, colour in SPECTRAL:
        if T >= t_min:
            return letter, colour
    return "M", "Red"


def lifetime_years(M):
    """Fuel over burn rate: M/L ~ M^-2.5. A star twice as heavy lives less than a fifth as long."""
    return SUN_LIFETIME_YR * (M / M_SUN) / (luminosity(M) / L_SUN)


def derive(parent, free):
    if parent is None or "M_star_solar" not in parent:
        raise ValueError("aStar requires theStar as its parent")
    M = float(parent["M_star_solar"]) * M_SUN
    R = radius(M)
    L = luminosity(M)
    T = surface_temperature(L, R)
    return {
        # ITS OWN DURATION: its whole life -- fuel over burn rate. t=1 in emit() means this much real time.
        "duration_s": lifetime_years(M) * 3.1557e7,
        "M": M,
        "M_solar": M / M_SUN,
        "R": R,
        "R_solar": R / R_SUN,
        "L": L,
        "L_solar": L / L_SUN,
        "T_surface": T,                                   # 5772 K -- forced by balance, not picked
        "spectral_class": spectral_class(T)[0],           # G -- from the temperature alone
        "colour": spectral_class(T)[1],                   # Yellow -- and this IS the membrane's name
        "name": "a" + spectral_class(T)[1] + "Star",      # aYellowStar, derived rather than chosen
        "lifetime_yr": lifetime_years(M),
        "granules_across": 2.0 * R / (GRANULE_KM * 1e3),  # how many convection cells span the disk
        "granule_dT": GRANULE_DT,
        "burning": True,
    }


def emit(nums, t=1.0):
    """The matter of aStar, in its own local units (1 = its photosphere).

    The colour is a MEASUREMENT: every grain is painted at the blackbody temperature of the patch of
    photosphere it is, so the star is yellow-white because 5772 K IS yellow-white. The surface is not
    smooth either -- heat cannot escape by radiation alone out here, so the gas OVERTURNS, and the
    photosphere is tiled with granules: hot rising centres, cooler sinking lanes, ~250 K apart. The
    movie is ignition: a dim contracting ball that lights and settles onto its balance temperature."""
    import numpy as np
    from matter import blank, fibonacci_sphere, paint, blackbody_rgb, SOLID, GLOW

    tt = float(t)
    T0 = float(nums.get("T_surface", T_SUN))
    rng = np.random.default_rng(97)

    # ── the photosphere: a shell, tiled with convection cells ──
    n = 26000
    d = fibonacci_sphere(n, jitter=0.85, seed=97)
    # granulation: a high-frequency field over the sphere. Its scale is DERIVED -- the cell size the
    # star's own convection produces -- not chosen for looks.
    across = float(nums.get("granules_across", 1400.0))
    cells = np.zeros(n)
    amp, tot = 1.0, 0.0
    for o in range(3):
        freq = across / 60.0 * (1.8 ** o)                   # low count = big cells, as the star has
        for _ in range(5):
            k = rng.normal(size=3); k /= np.linalg.norm(k) + 1e-12
            cells += amp * np.sin(freq * (d @ k) + rng.uniform(0, 2 * pi))
            tot += amp
        amp *= 0.5
    cells /= max(tot, 1e-9)

    T = T0 * (0.45 + 0.55 * tt ** 2)                        # it lights as its own time runs
    b = blank(n)
    b[:, 0:3] = d
    b[:, 21:24] = d
    cols = np.array([blackbody_rgb(max(1200.0, T + GRANULE_DT * c)) for c in np.round(cells, 2)],
                    dtype=np.float32)
    b[:, 16:19] = cols
    b[:, 19] = 0.55
    b[:, 20] = 0.030
    b[:, 11] = SOLID

    # ── the corona: thin, hot, and only visible against the dark ──
    n_c = 5000
    dc = fibonacci_sphere(n_c, jitter=1.0, seed=98)
    rad = 1.0 + 0.55 * rng.random(n_c) ** 0.7
    c = blank(n_c)
    c[:, 0:3] = dc * rad[:, None]
    paint(c, blackbody_rgb(min(T * 1.15, 4.0e4)), 0.035 * tt, 0.055, GLOW)
    return np.concatenate([b, c], axis=0)


def measure(nums):
    """Facts: the surface temperature is what balance forces (5772 K for a solar mass), and the life
    is set by mass alone -- both derived, neither chosen."""
    from pathlib import Path
    folder = Path(__file__).resolve().parent.name
    return {"T_surface": nums["T_surface"],
            "spectral_class": nums["spectral_class"],
            # THE NAME MUST MATCH THE PHYSICS. The folder is called what the temperature says it is,
            # so a wrong rename -- or a changed mass that moves the class -- fails here.
            "name_matches_class": folder == nums["name"],
            "matches_sun": abs(nums["T_surface"] - T_SUN) < 60.0 if abs(nums["M_solar"] - 1) < 0.02 else None,
            "lifetime_gyr": nums["lifetime_yr"] / 1e9}
