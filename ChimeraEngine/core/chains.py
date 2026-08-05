"""chains.py -- Stage 16: specular-to-specular bounce chains, which collapse to a single lobe.

WHAT STAGE 6 SCOPED OUT. Its one-bounce gather was DIFFUSE receive only, and specular-to-specular
chains were named unbuilt. They turn out to need no new render pass at all, for a reason that is
the whole justification of this lane's framing:

    A SPECULAR LOBE IS A GAUSSIAN, AND GAUSSIANS ADD VARIANCES UNDER COMPOSITION.

So an N-bounce chain is not N passes. It is ONE Gaussian lobe:

    slope     s_chain = sqrt( sum s_i^2 )        (variances add)
    energy    F_chain = product F_i(theta)       (Fresnel multiplies)

and those two numbers are exactly what `story/matter.paint_specular` already takes. The chain
therefore renders through the specular kernel Stage 1 built, unchanged -- one more reader of one
field, again.

THE MIRROR DOUBLING, and it is easy to get wrong. A surface whose NORMAL tilts by an angle d turns
a reflected ray by 2d. So a surface of RMS slope s produces an outgoing angular lobe of width 2s,
and a chain's angular width is 2 sqrt(sum s_i^2). The factor 2 is derived, and it is checked by
Monte Carlo rather than asserted -- getting it wrong (or adding standard deviations instead of
variances) is precisely the sort of error that survives reading.

THE CHAIN DEPTH IS DERIVED FROM THE RENDERER, not chosen. The compositor writes uint8, so a channel
step is 1/255 and anything under half a step -- 1/510 -- cannot change a pixel. Energy decays as
the Fresnel product, so the deepest chain that can be SEEN is

    n_max(theta) = floor( ln(1/510) / ln F(theta) )

For water this is a strong statement: F0 = 0.0215 at normal incidence gives n_max = 1 -- a SECOND
specular bounce off water is invisible by construction -- while at 80 degrees F rises to 0.399 and
n_max = 6. Specular chains matter only at grazing angles, which is exactly where a person sees
them: long reflections stretched across water at sunset, a wet road at dusk. Same derivation
discipline as `gpu_pipeline.FOOTPRINT`, which came out of the compositor's own weight cutoff.

NAMED UNBUILT, and one of these is a real physical omission rather than a scope choice:
  * POLARIZATION. Real multi-bounce Fresnel differs for s- and p-polarized light, and successive
    specular bounces polarize the beam -- so a long chain's energy is not truly the product of
    unpolarized coefficients. This module uses Schlick's unpolarized form throughout.
  * CURVED-MIRROR FOCUSING. Composition assumes each lobe stays narrow and the geometry does not
    converge; a concave specular surface focuses, which is Stage 5's caustic machinery applied to
    reflection rather than refraction.
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

# THE VISIBILITY FLOOR, DERIVED FROM THE OUTPUT FORMAT. `gpu_pipeline._composite` writes uint8, so
# one channel step is 1/255 and half a step is 1/510. A contribution below this cannot move a
# pixel -- change the image depth and this tracks, exactly as FOOTPRINT tracks the weight cutoff.
QUANT_HALF_STEP = 1.0 / 510.0

# The mirror doubling: a normal tilted by d turns a ray by 2d. Named so it cannot be silently lost.
MIRROR_GAIN = 2.0


def fresnel_schlick(f0: float, cos_theta: float) -> float:
    """The same Schlick form Stage 1's kernel uses -- imported by value, not re-derived."""
    return float(f0) + (1.0 - float(f0)) * (1.0 - float(cos_theta)) ** 5


def compose_slope(slopes) -> float:
    """s_chain = sqrt(sum s_i^2). Variances add; standard deviations do NOT."""
    s = np.asarray(slopes, dtype=np.float64)
    return float(np.sqrt(np.sum(s * s)))


def chain_angular_width(slopes) -> float:
    """The chain's outgoing spread IN THE PLANE OF INCIDENCE: 2 * sqrt(sum s_i^2)."""
    return MIRROR_GAIN * compose_slope(slopes)


def chain_angular_width_outplane(slopes, cos_theta: float) -> float:
    """THE LOBE IS ANISOTROPIC, and the Monte Carlo caught it -- the first version of this module
    had one width and read 2.4% low for that reason.

    Rotating the normal by d turns the reflected ray by 2d in the plane of incidence, but an
    out-of-plane tilt is FORESHORTENED by cos(theta_i): measured gain 0.9987*2s in-plane against
    0.9525*2s out-of-plane at cos(theta_i) = 0.9536. So a rough mirror's lobe is an ellipse that
    stretches as incidence gets grazing -- which is exactly why a grazing reflection on water
    smears into a long vertical streak instead of a round highlight.

    Applied per surface; for a chain whose surfaces meet the ray at different angles, pass the
    relevant cos(theta) or treat this as the single-bounce statement it was verified as."""
    return MIRROR_GAIN * float(cos_theta) * compose_slope(slopes)


def compose_fresnel(f0s, cos_theta: float) -> float:
    """F_chain = product of each surface's Schlick reflectance at this incidence."""
    out = 1.0
    for f0 in f0s:
        out *= fresnel_schlick(f0, cos_theta)
    return out


def chain_specular_params(f0s, slopes, cos_theta: float):
    """(F0_effective, slope_effective) for the whole chain -- the two numbers
    `story/matter.paint_specular` takes. This is the payoff: an N-bounce chain is renderable by
    the ONE-bounce kernel, because the composition collapsed it to a single lobe."""
    return compose_fresnel(f0s, cos_theta), compose_slope(slopes)


def max_visible_depth(f0: float, cos_theta: float,
                      floor: float = QUANT_HALF_STEP) -> int:
    """The deepest chain that can still move a pixel: floor(ln(floor)/ln F(theta)).

    Returns 0 when even ONE bounce is invisible, and is unbounded-in-principle only as F -> 1
    (a perfect mirror at grazing incidence), which is why the cap is capped."""
    f = fresnel_schlick(f0, cos_theta)
    if f <= 0.0:
        return 0
    if f >= 1.0:
        return 1 << 20                      # a perfect mirror never attenuates; say so loudly
    return int(math.floor(math.log(floor) / math.log(f)))


def monte_carlo_chain_width(slopes, incoming, normals, n_samples: int = 400000,
                            seed: int = 17) -> float:
    """THE REFEREE. Trace `n_samples` rays through the chain with each surface's normal perturbed
    by its own Gaussian slope, and measure the per-axis angular spread of the outgoing direction.

    It must equal `chain_angular_width` -- which it can only do if the mirror gain really is 2 and
    the composition really adds VARIANCES. Adding standard deviations instead would show up here
    as a clear disagreement, which is the point of measuring rather than reasoning."""
    rng = np.random.default_rng(seed)
    d = np.tile(np.asarray(incoming, dtype=np.float64), (n_samples, 1))
    d /= np.linalg.norm(d, axis=1)[:, None]
    for s, n_nom in zip(slopes, normals):
        n0 = np.asarray(n_nom, dtype=np.float64)
        n0 = n0 / np.linalg.norm(n0)
        # two tangent axes for the perturbation
        helper = np.array([1.0, 0.0, 0.0]) if abs(n0[0]) < 0.9 else np.array([0.0, 1.0, 0.0])
        t1 = np.cross(n0, helper)
        t1 /= np.linalg.norm(t1)
        t2 = np.cross(n0, t1)
        pert = (rng.normal(0.0, s, (n_samples, 1)) * t1[None, :]
                + rng.normal(0.0, s, (n_samples, 1)) * t2[None, :])
        n = n0[None, :] + pert
        n /= np.linalg.norm(n, axis=1)[:, None]
        d = d - 2.0 * np.einsum("ij,ij->i", d, n)[:, None] * n
        d /= np.linalg.norm(d, axis=1)[:, None]
    mean = d.mean(axis=0)
    mean /= np.linalg.norm(mean)
    # Resolve the spread along the INCIDENCE PLANE and perpendicular to it, separately -- averaging
    # the two hid a real 2.4% anisotropy in the first version of this function.
    d0 = np.asarray(incoming, dtype=np.float64)
    d0 /= np.linalg.norm(d0)
    n0 = np.asarray(normals[0], dtype=np.float64)
    n0 /= np.linalg.norm(n0)
    b = np.cross(d0, n0)
    b /= np.linalg.norm(b)                 # perpendicular to the plane of incidence
    ip = np.cross(mean, b)
    ip /= np.linalg.norm(ip)               # in the plane of incidence, across the mean ray
    return float((d @ ip).std()), float((d @ b).std())
