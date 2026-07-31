"""theSkin -- the boundary itself: what light does on it, heat out, and what a laser does to it.

THE OPTICS ARE NOW DERIVED, not stubbed (2026-07-31, F1). The law is story/skin_optics.py --
Jacques' measured epidermis/dermis model over Prahl's archived hemoglobin table -- and the parent
(theHuman) publishes its answer at the renderer's three bands so this membrane and aHuman's face
are the same skin. What THIS chapter owns is the whole spectrum and the boundary's own numbers:
its area (DuBois, read from the parent), its two layers' thicknesses, and what each colour's
subsurface reach is.

STILL OPEN (the rest of the original agenda, honestly not yet derived):
    * damage as an ENERGY, not a hit point: joules deposited, over what area, in what time
    * what a breach costs -- theBreath's loop pressure is what leaks, and it derived that
    * healing as a rate, so time is the currency rather than a potion

THE STORY'S VERBS THAT LAND HERE:
    * Administer Bio-Patch [C] -- local coagulants after a laser graze
    * the suit breach the story implies but never spells out
"""
from __future__ import annotations

import math

import numpy as np


def derive(parent, free):
    if parent is None or "skin_albedo_rgb" not in parent:
        raise ValueError("theSkin requires theHuman as its parent (it publishes the skin optics)")
    import skin_optics as _skin

    f_mel = float(parent["melanin_fraction"])
    f_blood = float(parent["skin_blood_fraction"])

    # THE WHOLE SPECTRUM, this membrane's own view: the parent publishes three bands because the
    # renderer needs three; a boundary is the whole curve. Sampled where the physics has features
    # -- the 415 nm Soret peak of hemoglobin, the 542/577 nm oxy twin peaks, the melanin ramp.
    spectrum_nm = [415, 465, 535, 577, 615, 700, 800, 940]
    spectrum_R = [_skin.skin_reflectance(nm, f_mel, f_blood) for nm in spectrum_nm]

    return {
        "extent_m": float(parent["height_m"]),
        "duration_s": float(parent["duration_s"]),

        # THE TWO LAYERS, measured conventions (Jacques): a 60 um melanin filter over a
        # blood-bearing collagen diffuser. The epidermis is 0.003% of stature -- a membrane in
        # the literal sense, three orders below the body it wraps.
        "epidermis_m": _skin.D_EPIDERMIS_CM / 100.0,
        "epidermis_over_stature": _skin.D_EPIDERMIS_CM / 100.0 / float(parent["height_m"]),

        # THE OPTICS, READ FROM THE PARENT -- one derivation, two consumers.
        "melanin_fraction": f_mel,
        "melanin_class": str(parent["melanin_class"]),
        "blood_fraction": f_blood,
        "skin_albedo_rgb": [float(x) for x in parent["skin_albedo_rgb"]],
        "skin_bands_nm": [float(x) for x in parent["skin_bands_nm"]],
        "skin_sss_mfp_mm": [float(x) for x in parent["skin_sss_mfp_mm"]],
        "skin_area_m2": float(parent["skin_area_m2"]),
        "spectrum_nm": spectrum_nm,
        "spectrum_reflectance": spectrum_R,
        # RED GOES FURTHEST -- the gradient IS the subsurface glow.
        "sss_red_over_blue": float(parent["skin_sss_mfp_mm"][0]) / float(parent["skin_sss_mfp_mm"][2]),
        "optics_source": str(parent["skin_optics_source"]),
    }


def emit(nums, t=1.0):
    """A PATCH OF SKIN, curved like the limb it would wrap, lit so the subsurface shows.

    One body the derivation did produce: a section of cylindrical surface (a forearm's worth of
    boundary) -- no owner, no face, no fingers, because none of those were derived here. Its
    albedo is the parent's measured skin, and the shading WRAPS: light diffusing millimetres
    through the dermis softens the terminator instead of ending at it. The wrap width per colour
    is that colour's measured mean free path, so the red bleeds furthest around the curve -- the
    same gradient that makes a finger glow red against a torch.
    """
    from matter import blank, lit, SOLID, AR, AG, AB

    alb = np.array(nums["skin_albedo_rgb"], np.float32)
    mfp = np.array(nums["skin_sss_mfp_mm"], np.float32)

    # a cylindrical patch: radius 1 in this membrane's own frame, spanning ~120 deg and ~1.6 radii
    n_theta, n_z = 40, 26
    th = np.linspace(-1.05, 1.05, n_theta)
    zz = np.linspace(-0.8, 0.8, n_z)
    TH, ZZ = np.meshgrid(th, zz)
    TH = TH.ravel()[:, None]
    pts = np.concatenate([np.cos(TH), np.sin(TH), ZZ.ravel()[:, None]], axis=1).astype(np.float32)
    nrm = np.concatenate([np.cos(TH), np.sin(TH), np.zeros_like(TH)], axis=1).astype(np.float32)

    n = len(pts)
    b = blank(n)
    b[:, 0], b[:, 1], b[:, 2] = pts[:, 0], pts[:, 1], pts[:, 2]
    b[:, 21:24] = nrm

    # WRAP LIGHTING FROM THE MEASURED MFPS. Lambert ends light exactly at the terminator; skin
    # does not -- a photon random-walks mfp millimetres before it forgets its direction, so the
    # lit region reaches past the geometric terminator by that amount against the patch's own
    # scale. Here the patch stands for a forearm (~28 mm of radius on this body): the wrap per
    # colour is mfp / (2*pi*r) of a radian, and red wraps furthest. Measured inputs, no palette.
    r_patch_mm = 0.028 * 1.755 * 1000.0          # the limb this patch stands for
    wrap = np.clip(mfp / r_patch_mm, 0.0, 1.0)   # per band: the fraction of a radian light reaches
    sun = np.array([0.55, -0.72, 0.42], np.float32)
    sun /= np.linalg.norm(sun)
    lam = np.clip(nrm @ sun, -1.0, 1.0)          # signed: the wrap is what carries light past 0
    wrapped = np.clip((lam[:, None] + wrap[None, :]) / (1.0 + wrap[None, :]), 0.0, 1.0)
    b[:, 16:19] = lit(alb[None, :] * wrapped, 1.4, e_ref=1.0, tone=0.45)
    b[:, AR:AB + 1] = alb
    b[:, 19] = 0.97
    # close the surface: grains sized from the patch's own sampling (matter's law, applied here)
    spacing = 2.0 * math.pi * 1.0 / n_theta
    b[:, 20] = 0.62 * spacing
    b[:, 11] = SOLID
    return b


def measure(nums):
    """Facts a reader can check without trusting the prose."""
    import skin_optics as _skin
    checks = _skin.check_against_archive()
    own = _skin.skin_albedo_rgb(float(nums["melanin_fraction"]), float(nums["blood_fraction"]))
    agrees = all(abs(a - b) < 1e-9 for a, b in zip(own, nums["skin_albedo_rgb"]))
    return {
        "archive_spot_values_close": all(c["ok"] for c in checks.values()),
        "spot_detail": {k: f"got {c['got']:.3g} want {c['want']:.3g}" for k, c in checks.items()},
        "reads_parent_not_own_copy": agrees,
        "red_reaches_further_than_blue": nums["sss_red_over_blue"] > 1.5,
        "area_is_a_persons": 1.5 < nums["skin_area_m2"] < 2.5,
        "melanin_class_matches_fraction": _skin.F_MEL_CLASSES[nums["melanin_class"]][0]
                                          <= nums["melanin_fraction"] <=
                                          _skin.F_MEL_CLASSES[nums["melanin_class"]][1],
    }
