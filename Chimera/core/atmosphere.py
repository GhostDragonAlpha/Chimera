"""atmosphere — the sky is NOT an object. It is what light does crossing matter.

THE CORRECTION (operator, 2026-07-23): I proposed a "sky primitive" — an inward-facing
dome clothed in a material. That is a painted backdrop, and CLAUDE.md forbids it:
NO AESTHETIC PASSES, appearance DERIVES from the matter model. A dome is the aesthetic
pass wearing a hat.

What is actually up there:
    AIR       a density field, not a surface. Static pressure falls off from the ground
              to the top of the atmosphere by the barometric law.
    THE BLUE  Rayleigh scattering off N2/O2 molecules. beta goes as 1/lambda^4, so blue
              scatters ~5.7x more than red. Nobody chooses the colour -- it falls out.
    RED SUNS  at a low sun the path through air is long, blue has been scattered OUT of
              the beam, and what reaches you is what is left.
    HAZE      Mie scattering off aerosols -- larger particles, wavelength-neutral,
              strongly forward-biased. This is the white glare near the sun.
    CLOUDS    condensed water. NOT part of this file: clouds are MATTER and belong in
              the genome pipeline like everything else (see docs/THE_WORKFLOW.md).
              An atmosphere is the medium; a cloud is a thing in it.

EVERYTHING HERE IS float64. At Earth's radius float32 resolves 0.5 m -- measured -- so
positions jitter by half a metre and any altitude-dependent quantity dithers with them.
Rendering may cast to float32 AFTER subtracting the camera origin, never before.

Coefficients are the standard sea-level values used in atmospheric-scattering literature
(Nishita 1993, Bruneton 2008), in inverse metres. They are MEASURED CONSTANTS OF EARTH'S
AIR, not tuning knobs -- change them and you are simulating a different planet, which is
a legitimate thing to do deliberately and a bug to do accidentally.
"""
from __future__ import annotations

import numpy as np

# --- Earth's air, measured ------------------------------------------------
R_PLANET = 6.371e6          # m, mean radius
H_RAYLEIGH = 8.0e3          # m, scale height of the molecular atmosphere
H_MIE = 1.2e3               # m, aerosols hug the ground
TOP_OF_ATMOSPHERE = 6.0e4   # m, above this the density is negligible

# scattering coefficients at sea level, per metre, for R/G/B (~680/550/440 nm)
BETA_RAYLEIGH = np.array([5.802e-6, 13.558e-6, 33.100e-6], dtype=np.float64)
BETA_MIE = np.array([21.0e-6, 21.0e-6, 21.0e-6], dtype=np.float64)
MIE_G = 0.76                # forward-scattering asymmetry of haze
MIE_ABSORB = 1.1            # aerosols absorb as well as scatter

SUN_IRRADIANCE = np.array([1.0, 1.0, 1.0], dtype=np.float64)


def density(altitude, scale_height: float = H_RAYLEIGH) -> np.ndarray:
    """Barometric law: rho(h) = rho0 * exp(-h / H). The 'static pressure' profile.

    This is the whole reason a sky has depth: looking up you cross a little air, looking
    at the horizon you cross a lot, and the difference is what colours the view.
    """
    h = np.asarray(altitude, dtype=np.float64)
    return np.exp(-np.maximum(h, 0.0) / scale_height)


def _ray_atmosphere_exit(origin, direction) -> np.ndarray:
    """Distance from origin to the top of the atmosphere along direction (float64)."""
    o = np.asarray(origin, dtype=np.float64)
    d = np.asarray(direction, dtype=np.float64)
    d = d / np.linalg.norm(d, axis=-1, keepdims=True)
    top = R_PLANET + TOP_OF_ATMOSPHERE
    b = 2.0 * np.sum(o * d, axis=-1)
    c = np.sum(o * o, axis=-1) - top * top
    disc = np.maximum(b * b - 4.0 * c, 0.0)
    return (-b + np.sqrt(disc)) * 0.5


def optical_depth(origin, direction, steps: int = 32) -> tuple[np.ndarray, np.ndarray]:
    """Integrate density along a ray. Returns (rayleigh_depth, mie_depth) in metres."""
    o = np.asarray(origin, dtype=np.float64)
    d = np.asarray(direction, dtype=np.float64)
    d = d / np.linalg.norm(d)
    L = float(_ray_atmosphere_exit(o, d))
    t = (np.arange(steps, dtype=np.float64) + 0.5) * (L / steps)
    p = o[None, :] + d[None, :] * t[:, None]
    h = np.linalg.norm(p, axis=1) - R_PLANET
    dt = L / steps
    return (density(h, H_RAYLEIGH).sum() * dt, density(h, H_MIE).sum() * dt)


def transmittance(origin, direction, steps: int = 32) -> np.ndarray:
    """Fraction of light surviving the path — Beer-Lambert."""
    dr, dm = optical_depth(origin, direction, steps)
    return np.exp(-(BETA_RAYLEIGH * dr + BETA_MIE * MIE_ABSORB * dm))


def _phase_rayleigh(mu: float) -> float:
    return 3.0 / (16.0 * np.pi) * (1.0 + mu * mu)


def _phase_mie(mu: float, g: float = MIE_G) -> float:
    g2 = g * g
    return (3.0 / (8.0 * np.pi)) * ((1.0 - g2) * (1.0 + mu * mu)) / \
           ((2.0 + g2) * (1.0 + g2 - 2.0 * g * mu) ** 1.5)


def sky_radiance(view_dir, sun_dir, altitude: float = 2.0,
                 steps: int = 32, light_steps: int = 16) -> np.ndarray:
    """What you SEE looking along view_dir, with the sun at sun_dir. Single scattering.

    The colour is not chosen anywhere in this function. It emerges from beta ~ 1/lambda^4
    and the geometry of the two paths: eye->sample and sample->sun.
    """
    v = np.asarray(view_dir, dtype=np.float64)
    v = v / np.linalg.norm(v)
    s = np.asarray(sun_dir, dtype=np.float64)
    s = s / np.linalg.norm(s)

    o = np.array([0.0, 0.0, R_PLANET + max(altitude, 0.0)], dtype=np.float64)
    L = float(_ray_atmosphere_exit(o, v))
    dt = L / steps

    mu = float(np.dot(v, s))
    ph_r, ph_m = _phase_rayleigh(mu), _phase_mie(mu)

    total = np.zeros(3, dtype=np.float64)
    acc_r = acc_m = 0.0
    for i in range(steps):
        p = o + v * ((i + 0.5) * dt)
        h = float(np.linalg.norm(p) - R_PLANET)
        dr = float(density(h, H_RAYLEIGH)) * dt
        dm = float(density(h, H_MIE)) * dt
        acc_r += dr
        acc_m += dm

        # is the sun even visible from this sample, or is the planet in the way?
        sun_r, sun_m = optical_depth(p, s, light_steps)
        below = np.dot(p, s) < 0 and np.linalg.norm(p - s * np.dot(p, s)) < R_PLANET
        if below:
            continue

        tr = np.exp(-(BETA_RAYLEIGH * (acc_r + sun_r)
                      + BETA_MIE * MIE_ABSORB * (acc_m + sun_m)))
        total += tr * (BETA_RAYLEIGH * ph_r * dr + BETA_MIE * ph_m * dm)

    return SUN_IRRADIANCE * total


def sky_colour(view_dir, sun_dir, altitude: float = 2.0, exposure: float = 22.0):
    """Tone-mapped sRGB-ish colour in 0..1, for looking at."""
    rad = sky_radiance(view_dir, sun_dir, altitude)
    return np.clip(1.0 - np.exp(-rad * exposure), 0.0, 1.0) ** (1.0 / 2.2)


def sun_elevation_dir(deg: float) -> np.ndarray:
    """Sun direction at a given elevation above the horizon, due east."""
    a = np.deg2rad(deg)
    return np.array([np.cos(a), 0.0, np.sin(a)], dtype=np.float64)


def main() -> None:
    print(f'  float64 throughout. At R={R_PLANET:.3e} m float32 resolves '
          f'{np.spacing(np.float32(R_PLANET)):.3f} m -- unusable.')
    print(f'  scale heights: rayleigh {H_RAYLEIGH:.0f} m, mie {H_MIE:.0f} m')
    print(f'  beta_rayleigh R:G:B = {np.round(BETA_RAYLEIGH / BETA_RAYLEIGH[0], 2)}'
          f'   (blue scatters {BETA_RAYLEIGH[2] / BETA_RAYLEIGH[0]:.1f}x red)')
    print()
    up = np.array([0.0, 0.0, 1.0])
    horizon = np.array([1.0, 0.0, 0.02])
    for elev in (60.0, 20.0, 5.0, 1.0):
        s = sun_elevation_dir(elev)
        z = sky_colour(up, s)
        hz = sky_colour(horizon, s)
        print(f'  sun {elev:>4.0f} deg   zenith {np.round(z, 3)}   horizon {np.round(hz, 3)}')


if __name__ == '__main__':
    main()


# ===========================================================================
# THE ATMOSPHERE GENOME (2026-07-24, backlog T4). The scattering coefficients above ARE an
# atmosphere's DNA: change BETA and the scale heights and you change the planet's sky, and
# nobody picks the colour -- it still falls out of beta ~ 1/lambda^4 and the geometry. Earth
# is blue because its molecular scattering is blue-heavy; Mars is butterscotch because thin
# air lets dust (Mie) dominate; Titan is orange under a thick methane haze. Same physics,
# different genome.
#
# An atmosphere is NOT a placeable blob like matter/light/fluid -- it is the MEDIUM, the last
# of the four port kinds. The operator's rule stands: "you don't make the sky, you make the
# clouds." This does not build a dome; it drives the PHYSICAL sky_colour, and clouds remain
# separate matter/fluid IN the medium. AUTHORED coefficients from planetary-atmosphere
# literature (the legitimate second intake), same as emissive and fluid.
# ===========================================================================

import contextlib as _contextlib

ATMOSPHERE_SCHEMA = {
    'beta_r': (0.2, 40.0), 'beta_g': (0.2, 40.0), 'beta_b': (0.2, 40.0),  # 1e-6 /m, molecular
    'beta_mie': (1.0, 80.0),        # aerosol/haze scattering, 1e-6 /m
    'h_rayleigh': (4.0e3, 14.0e3),  # molecular scale height (thicker air = larger)
    'h_mie': (0.5e3, 3.0e3),        # aerosol scale height
    'density': (0.01, 3.0),         # overall thickness: 0.01 near-vacuum, 3 = Venus-thick
}

ATMOSPHERE_ARCHETYPES = {
    'earth':  dict(beta_r=5.8,  beta_g=13.6, beta_b=33.1, beta_mie=21.0,
                   h_rayleigh=8.0e3,  h_mie=1.2e3, density=1.0),
    'mars':   dict(beta_r=19.9, beta_g=13.4, beta_b=8.6,  beta_mie=40.0,   # dust reddens it
                   h_rayleigh=11.0e3, h_mie=1.0e3, density=0.10),
    'titan':  dict(beta_r=16.0, beta_g=8.0,  beta_b=3.0,  beta_mie=60.0,   # thick methane haze
                   h_rayleigh=20.0e3, h_mie=2.5e3, density=1.6),
    'venus':  dict(beta_r=28.0, beta_g=26.0, beta_b=10.0, beta_mie=70.0,   # thick, yellow-white
                   h_rayleigh=15.0e3, h_mie=2.0e3, density=3.0),
    'thin':   dict(beta_r=5.8,  beta_g=13.6, beta_b=33.1, beta_mie=8.0,    # near-vacuum: dark sky
                   h_rayleigh=8.0e3,  h_mie=1.2e3, density=0.02),
}


def atmosphere_seed(name: str = 'earth') -> dict:
    if name not in ATMOSPHERE_ARCHETYPES:
        raise KeyError(f'no atmosphere archetype {name!r}; have {sorted(ATMOSPHERE_ARCHETYPES)}')
    return dict(ATMOSPHERE_ARCHETYPES[name])


def atmosphere_recombine(a: dict, b: dict, t: float = 0.5) -> dict:
    return {k: float(a[k] * (1 - t) + b[k] * t) for k in ATMOSPHERE_SCHEMA}


@_contextlib.contextmanager
def apply_atmosphere(genome: dict):
    """Temporarily drive the module's scattering constants from a genome, then restore.

    Swaps BETA and the scale heights (read at call time by sky_radiance/density), scaled by
    `density`. MIE_G stays at its default -- _phase_mie binds it at definition, so it is not
    genome-driven here; the visible planet-to-planet difference is the beta spectrum and the
    thickness, which this does drive.
    """
    global BETA_RAYLEIGH, BETA_MIE, H_RAYLEIGH, H_MIE
    saved = (BETA_RAYLEIGH.copy(), BETA_MIE.copy(), H_RAYLEIGH, H_MIE)
    try:
        d = float(genome['density'])
        BETA_RAYLEIGH = np.array([genome['beta_r'], genome['beta_g'], genome['beta_b']]) * 1e-6 * d
        BETA_MIE = np.full(3, genome['beta_mie'] * 1e-6 * d)
        H_RAYLEIGH = float(genome['h_rayleigh'])
        H_MIE = float(genome['h_mie'])
        yield
    finally:
        BETA_RAYLEIGH, BETA_MIE, H_RAYLEIGH, H_MIE = saved


def sky_swatch(genome: dict, sun_elev_deg: float = 20.0, n: int = 24) -> np.ndarray:
    """Horizon->zenith sky colours for a genome, as an (n,3) array in 0..1. The proof: earth
    comes out blue, mars butterscotch, titan orange, thin near-black -- none of it chosen."""
    s = sun_elevation_dir(sun_elev_deg)
    out = np.zeros((n, 3))
    with apply_atmosphere(genome):
        for i in range(n):
            el = np.deg2rad(1.0 + (88.0) * i / (n - 1))       # horizon -> zenith
            v = np.array([np.cos(el), 0.0, np.sin(el)])
            out[i] = sky_colour(v, s)
    return out


def atmosphere_facts(genome: dict) -> dict:
    """Measured facts of an atmosphere: its zenith and horizon colour, and which hue dominates."""
    sw = sky_swatch(genome, 25.0, 12)
    zenith, horizon = sw[-1], sw[0]
    hue = ('blue' if zenith[2] >= max(zenith[0], zenith[1]) else
           'red' if zenith[0] >= zenith[1] else 'green')
    return {'zenith': [round(float(x), 3) for x in zenith],
            'horizon': [round(float(x), 3) for x in horizon],
            'zenith_hue': hue, 'brightness': round(float(sw.mean()), 3)}


def atmosphere_propose(n: int = 8, seed: int = 0) -> list:
    """N admissible atmospheres for an `atmospheric` stud, each measured, ranked, never chosen."""
    names = list(ATMOSPHERE_ARCHETYPES)
    rng = np.random.default_rng(seed)
    out = []
    for i in range(n):
        a, b = (names[int(rng.integers(len(names)))] for _ in range(2))
        t = float(rng.uniform(0, 1))
        g = atmosphere_recombine(ATMOSPHERE_ARCHETYPES[a], ATMOSPHERE_ARCHETYPES[b], t)
        f = atmosphere_facts(g)
        out.append({'parents': (a, b), 'blend': round(t, 3),
                    'zenith_hue': f['zenith_hue'], 'brightness': f['brightness'],
                    'zenith': f['zenith'], 'genome': g, 'seed': seed + i})
    out.sort(key=lambda c: -c['brightness'])           # clearer/brighter skies first
    return out
