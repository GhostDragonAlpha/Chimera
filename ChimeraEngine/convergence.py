"""convergence.py -- THE MEASURED CONVERGENCE (the two messengers must AGREE ON A NUMBER).

Your idea taken to its teeth. It is not enough that a term HAS an appearance -- the appearance must
MEASURABLY carry the physics. So for each term we PREDICT an observable feature from the physics
law, MEASURE that same feature independently from the rendered pixels (the light that actually left
the projector), and require them to CONVERGE. Two messengers, one membrane; proof is the moment the
number the physics predicts and the number the pixels show land on top of each other.

This is what forbids the aesthetic pass: recolor the star blue "because it looks nice" and the
measured chromaticity leaves the Planck locus -- convergence fails, prove() refuses. The look is not
free; it is a measurement of the physics or it is a lie.

Multi-messenger astronomy is the literal precedent: GW170817 became a detection because the
gravitational-wave distance and the electromagnetic redshift AGREED. One messenger is a claim; two
that converge are evidence. "You can't measure a system with itself" -- so we measure it with the
other messenger, and their difference is the residual that either clears the gate or does not.
"""
from __future__ import annotations

import math
from pathlib import Path

# --- the physics genome for the terms that HAVE a light-view -------------------
# Real measured constants of the referents (terminal = PHYSICS), NOT free knobs: Sol is a G2V star
# near 5772 K; a star holds ~99.9% of its system's mass and sits at the barycenter; a lush habitable
# surface is vegetation-dominated (chlorophyll). Each term names the ONE feature its appearance must
# reproduce and the law that predicts it. Grows as terms get a projector + a measurable prediction.
PHYSICS = {
    "theStar":        {"feature": "glow_chromaticity", "T_eff": 5778,
                       "law": "Planck's law + CIE 1931 -> the Sun's true blackbody color"},
    "theSolarSystem": {"feature": "bright_centroid",
                       "law": "the star holds ~99.9% of system mass -> it sits at the barycenter (center)"},
    "thePlanets":     {"feature": "climate_gradient",
                       "law": "T_eq ~ a^-0.5 (falls with distance) -> inner worlds hotter (warmer color) than outer; the habitable zone emerges between"},
    "theGarden":      {"feature": "green_dominance", "floor": 0.12,
                       "law": "chlorophyll reflectance -> a lush habitable surface is vegetation-dominated"},
    "aPlanet":        {"feature": "green_dominance", "floor": 0.12,
                       "law": "chlorophyll reflectance -> a lush habitable surface is vegetation-dominated"},
}

# convergence tolerances: the residual must be strictly BELOW these. Set with margin from the
# measured real-render residual (rule 4), wide enough to survive honest render/blend error, tight
# enough to reject an appearance that has left the physics (a blue star, an off-center barycenter).
TOL = {"glow_chromaticity": 0.055, "bright_centroid": 0.14, "climate_gradient": 15.0}


# --- Planck's law x the CIE 1931 observer -> a blackbody's true sRGB color -----
_C2 = 1.438776877e-2      # second radiation constant hc/k, m*K


def _planck(l_nm: float, T: float) -> float:
    """Relative spectral radiance of a blackbody at wavelength l_nm (constants that cancel dropped)."""
    l = l_nm * 1e-9
    return (l ** -5) / (math.exp(_C2 / (l * T)) - 1.0)


def _g(x: float, mu: float, s1: float, s2: float) -> float:
    s = s1 if x < mu else s2
    t = (x - mu) * s
    return math.exp(-0.5 * t * t)


def _cmf(l: float) -> tuple[float, float, float]:
    """CIE 1931 2-deg color matching functions, Wyman-Sloan-Shirley (2013) multi-lobe analytic fit."""
    x = 1.056 * _g(l, 599.8, 0.0264, 0.0323) + 0.362 * _g(l, 442.0, 0.0624, 0.0374) - 0.065 * _g(l, 501.1, 0.0490, 0.0382)
    y = 0.821 * _g(l, 568.8, 0.0213, 0.0247) + 0.286 * _g(l, 530.9, 0.0613, 0.0322)
    z = 1.217 * _g(l, 437.0, 0.0845, 0.0278) + 0.681 * _g(l, 459.0, 0.0385, 0.0725)
    return x, y, z


def blackbody_srgb(T: float) -> tuple[int, int, int]:
    """The true color of a blackbody at temperature T, from FIRST PRINCIPLES: integrate Planck's law
    against the CIE observer -> XYZ -> sRGB. This is the physics the star's appearance must reproduce;
    it is not a hand-picked yellow. 3200 K reads orange, 5778 K warm white, 20000 K blue-white."""
    X = Y = Z = 0.0
    for lam in range(380, 781, 5):
        p = _planck(lam, T)
        cx, cy, cz = _cmf(lam)
        X += p * cx; Y += p * cy; Z += p * cz
    X /= Y; Z /= Y; Y = 1.0                                   # normalize to luminance
    r = 3.2406 * X - 1.5372 * Y - 0.4986 * Z                  # linear sRGB (D65)
    g = -0.9689 * X + 1.8758 * Y + 0.0415 * Z
    b = 0.0557 * X - 0.2040 * Y + 1.0570 * Z
    r, g, b = (max(0.0, v) for v in (r, g, b))
    m = max(r, g, b, 1e-9); r, g, b = r / m, g / m, b / m     # scale into gamut
    gamma = lambda c: 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055
    return tuple(int(round(255 * gamma(c))) for c in (r, g, b))


def _chroma(rgb) -> tuple[float, float, float]:
    s = sum(rgb) or 1.0
    return (rgb[0] / s, rgb[1] / s, rgb[2] / s)


def _fmt(c) -> str:
    return f"({c[0]:.3f},{c[1]:.3f},{c[2]:.3f})"


# --- MEASURE the same feature from the rendered pixels (the independent readout) ---
def _load(png: str):
    from PIL import Image
    import numpy as np
    return np.asarray(Image.open(png).convert("RGB"), dtype=float)


def measure_glow_chromaticity(a):
    """The chromaticity of the star's colored glow -- bright, but excluding the saturated white core
    (which carries no temperature signature) and the dark background. This is where a star's color
    lives in real astrophotography: the limb and halo, not the blown-out center."""
    import numpy as np
    bright = a.sum(-1)
    sat = a.max(-1) - a.min(-1)
    hi = np.percentile(bright, 90)
    core = bright >= np.percentile(bright, 99.7)              # drop the blown-out white core
    mask = (bright >= hi) & (~core) & (sat > 10)
    if mask.sum() < 25:
        mask = (bright >= hi) & (sat > 6)
    if mask.sum() == 0:
        return None
    return _chroma(a[mask].mean(0))


def measure_bright_centroid(a):
    """Offset of the brightest source from the image center, in normalized units (0 = dead center).
    The star dominates the system's mass and sits at the barycenter, so its light should be centered."""
    import numpy as np
    bright = a.sum(-1)
    ys, xs = np.where(bright >= np.percentile(bright, 99.3))
    if len(xs) == 0:
        return 1.0
    H, W = bright.shape
    return math.hypot(xs.mean() / W - 0.5, ys.mean() / H - 0.5)


def measure_climate_gradient(a):
    """Inner-minus-outer warmth of the worlds. T_eq falls with orbital distance, so a family of
    grown worlds must run warm (inner) -> cool (outer): the colored disks on the left half are
    hotter-colored than those on the right. Returns (left_warmth - right_warmth); >0 = the physical
    gradient is present, <=0 = uniform or reversed (an appearance that has left the physics)."""
    import numpy as np
    H, W = a.shape[:2]
    r, b = a[..., 0], a[..., 2]
    sat = a.max(-1) - a.min(-1)
    colored = sat > 25                                       # the planet disks, not background/text/limb
    cols = np.arange(W)[None, :]
    left = colored & (cols < W / 2)
    right = colored & (cols >= W / 2)
    if left.sum() < 20 or right.sum() < 20:
        return None
    warmth = r - b                                           # red-minus-blue: hot worlds warm, frozen worlds cool
    return float(warmth[left].mean() - warmth[right].mean())


def measure_green_dominance(a):
    """Fraction of the frame where the green channel leads and is bright -- vegetation cover. A lush
    habitable surface (chlorophyll) is green-dominated; a desert or a gas world is not."""
    import numpy as np
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    veg = (g > r * 1.05) & (g > b * 1.05) & (g > 60)
    return float(veg.mean())


# --- the convergence test: predicted (physics) vs measured (pixels) ------------
def converge(term: str, png: str) -> dict:
    """Do the term's two messengers AGREE? Predict the feature from the physics law, measure it from
    the pixels, and return the residual against the tolerance. `has_test=False` means this term has a
    light-view but no measurable prediction yet -- an unchecked appearance, which the gate treats as
    NOT converged (a picture with no test behind it is the old rubber stamp)."""
    spec = PHYSICS.get(term)
    if not spec:
        return {"has_test": False, "converged": False,
                "detail": f"`{term}` has a light-view but no convergence law yet -- appearance is UNCHECKED"}
    a = _load(png)
    feat = spec["feature"]

    if feat == "glow_chromaticity":
        pc = _chroma(blackbody_srgb(spec["T_eff"]))
        mc = measure_glow_chromaticity(a)
        if mc is None:
            return {"has_test": True, "converged": False, "feature": feat,
                    "detail": "no colored glow found in the render -- nothing to compare to the physics"}
        resid = math.dist(pc, mc); tol = TOL[feat]
        return {"has_test": True, "converged": resid < tol, "feature": feat, "law": spec["law"],
                "predicted": _fmt(pc), "measured": _fmt(mc), "residual": round(resid, 4), "tol": tol,
                "detail": (f"blackbody({spec['T_eff']}K) chromaticity {_fmt(pc)} vs rendered glow "
                           f"{_fmt(mc)}; residual {resid:.4f} {'<' if resid < tol else '>='} tol {tol}")}

    if feat == "bright_centroid":
        off = measure_bright_centroid(a); tol = TOL[feat]
        return {"has_test": True, "converged": off < tol, "feature": feat, "law": spec["law"],
                "predicted": "0.000 (barycenter at center)", "measured": f"{off:.4f}",
                "residual": round(off, 4), "tol": tol,
                "detail": (f"brightest source at offset {off:.4f} from center; the barycenter predicts "
                           f"~0.000; {'<' if off < tol else '>='} tol {tol}")}

    if feat == "climate_gradient":
        grad = measure_climate_gradient(a)
        if grad is None:
            return {"has_test": True, "converged": False, "feature": feat,
                    "detail": "no worlds found in the render -- nothing to measure a gradient across"}
        tol = TOL[feat]
        return {"has_test": True, "converged": grad > tol, "feature": feat, "law": spec["law"],
                "predicted": f"inner warmer than outer (> {tol})", "measured": f"{grad:.1f}",
                "residual": round(grad, 1), "tol": tol,
                "detail": (f"inner-minus-outer warmth {grad:.1f} (red-minus-blue); T_eq ~ a^-0.5 predicts "
                           f"inner hotter, so > {tol}; {'>' if grad > tol else '<='} tol")}

    if feat == "green_dominance":
        frac = measure_green_dominance(a); floor = spec["floor"]
        return {"has_test": True, "converged": frac >= floor, "feature": feat, "law": spec["law"],
                "predicted": f">= {floor}", "measured": f"{frac:.3f}", "residual": round(frac, 3), "tol": floor,
                "detail": (f"vegetation-green cover {frac:.3f} vs lush floor {floor}; "
                           f"{'>=' if frac >= floor else '<'} floor")}

    return {"has_test": False, "converged": False, "detail": f"unknown feature `{feat}`"}


if __name__ == "__main__":
    for T in (3200, 4500, 5778, 8500, 20000):
        rgb = blackbody_srgb(T)
        print(f"  blackbody {T:>6}K -> sRGB {rgb}  chroma {_fmt(_chroma(rgb))}")
