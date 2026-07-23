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
