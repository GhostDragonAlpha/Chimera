"""theEye -- the aperture the whole world arrives through, and therefore what is worth drawing.

THE EDGE. Everything above this membrane derived a world; this one derives the hole it has to fit
through. An eye is a 2 mm aperture, and a 2 mm aperture cannot be argued with: diffraction sets a
hard floor under how fine a detail can exist in a retinal image, and no amount of retina underneath
it recovers what the pupil already threw away. So the renderer's budget is not a taste question. It
is an optics question with an answer.

THE DERIVATION, in one line. The parent's insolation and sun altitude give an illuminance; the
illuminance gives a pupil; the pupil gives a diffraction limit; and the diffraction limit is
**1.07 arcmin**, which is the 20/20 line on an eye chart. Nothing in that chain was fitted to
1 arcmin -- it comes out of S_earth, an atmosphere's pressure, a sun 52.5 degrees up, and the CIE's
measured luminous-efficiency curve read off disk.

AND A SECOND, INDEPENDENT ROUTE ARRIVES AT THE SAME PLACE. Foveal cones sit 2.41 um apart; through
the eye's nodal distance that is 0.497 arcmin per cone, a Nyquist limit of 60.4 cycles/degree, and
the pupil whose diffraction cutoff *equals* that sampling limit is **1.92 mm**. The pupil this
world's daylight actually forces is **2.18 mm**. The eye is built at its own diffraction limit, to
within 14%, and the two numbers were computed from completely different measurements -- one from
sunlight and air, one from a cadaver's cone mosaic.

WHAT THIS BUYS THE RENDERER, and it is the reason this chapter is not decoration:
    * the sharp part of vision is **0.0066% of the visual field** (the foveola). Not "small" --
      one part in fifteen thousand.
    * drawing the whole field at foveal acuity costs **54.6 megasamples**; drawing it at the acuity
      the eye actually has at each eccentricity costs **0.295**. Foveated rendering is worth **185x**,
      and that number is derived here rather than asserted by a hardware vendor.
    * at 1 arcmin, the finest feature worth generating is 0.31 mm at 1 m, 3.1 mm at 10 m, 3.1 cm at
      100 m, 31 cm at 1 km. Terrain grain finer than that is heat.
    * beyond **660 m** there is no stereo depth at all, so two eyes stop being worth rendering.

WHAT DOES NOT REACH THIS MEMBRANE, stated plainly rather than typed around:
    * **T_star_surface.** `aBlueWorld` publishes the star's surface temperature and its luminosity;
      `aTerrain` does not carry them, and `theGround` does not carry them, so by the time the chain
      reaches `theHuman` the star's SPECTRUM is gone -- only its total flux (`S_earth`) survives.
      This membrane therefore cannot say what colour this world's daylight is, cannot put the star's
      Wien peak next to the eye's own sensitivity peak, and cannot derive the luminous efficacy of
      its light. It reads `T_star_surface` from the parent IF IT IS EVER THERE, and otherwise says
      so in `star_spectrum_reachable` and falls back to the Sun's measured 93 lm/W. The machinery is
      checked against a solar reference so that the day the carry-chain is repaired, the number moves
      by itself. **A sibling's number comes through the parent, or not at all.**
    * **the planet's radius.** `horizon_m = sqrt(2*R*h)` needs an R, and no key in theHuman's
      numbers.json is one. `horizon_reachable` is False, and this chapter refuses to reconstruct R
      from an assumed density: that would be taste wearing a derivation's clothes.

WHAT IT CONSUMES from theHuman (every one of these is published and checked):
    * S_earth, sun_altitude_at_start_deg, P_surface_bar -- the light
    * height_m, eye_height_m, duration_s, stride_m -- the body and its clock
    * T_star_surface -- IF the chain is ever repaired to carry it

MEASURED DATA READ OFF DISK (research_references/human/eye/, see SOURCES.md):
    * cie1924_photopic_vlambda.csv   -- V(lambda). Its peak IS this chapter's design wavelength.
    * cie1951_scotopic_vlambda.csv   -- V'(lambda), the dark-adapted curve.
    * ciexyz1931_cmf.csv             -- colour-matching functions, so a spectrum becomes an RGB
                                        without anybody choosing a colour.
    * ANSUR_II_MALE_Public.csv       -- interpupillary breadth, 4,082 measured adults.

THE ONE FREE NUMBER is the scene's reflectance, and this chapter's job is to show it does not
matter: the pupil law is logarithmic, so sixteenfold in reflectance is 13% in acuity.

Contained in theHuman. Its movie is ONE INTER-BLINK INTERVAL: ten fixations, ten saccades, and the
lid coming down at the end.
"""
from __future__ import annotations

import csv
import math
from pathlib import Path

import numpy as np

# ══════════════════════════════════════════════════════════════════════════════════════════════════
#  MEASURED CONSTANTS. Each one is a number somebody put an instrument on, with the instrument named.
#  Nothing here is chosen; where a value is an approximation to a measured curve it says so.
# ══════════════════════════════════════════════════════════════════════════════════════════════════

# ── THE ORGAN. Gullstrand's schematic eye and standard biometry; adult axial length 23.5-24.5 mm.
AXIAL_LENGTH_M = 0.0240          # eyeball, front to back
NODAL_DISTANCE_M = 0.016670      # Emsley reduced eye: nodal point to retina. Converts ANGLE in the
                                 # world to DISTANCE on the retina, and it is the only optical
                                 # constant this chapter needs.
# THE EYE DOES NOT SCALE WITH THE BODY. It is adult-sized by about age 13 and varies by ~1 mm
# across the whole adult stature range -- which is why these are absolute metres and not a fraction
# of the parent's height. The stub this replaced multiplied stature by 0.024 and published a
# 42 mm eyeball: 75% too big, and the tell was that it moved when the body's height moved.

# ── THE MOSAIC. Curcio, Sloan, Kalina & Hendrickson 1990, J. Comp. Neurol. 292:497 -- the measured
# human photoreceptor topography. Peak foveal cone density, and the ganglion-cell count that carries
# the whole eye's output down one nerve (Curcio & Allen 1990: 0.7-1.5 million per retina).
CONE_PEAK_PER_MM2 = 199000.0
GANGLION_CELLS_PER_EYE = 1.2e6

# ── THE FIELD. Standard perimetry (Traquair; Goldmann limits). One eye reaches 100 deg temporally
# and 60 deg nasally, so two eyes union to 200 deg and overlap over 120 deg. Vertical 60 up, 70 down.
FOV_TEMPORAL_DEG = 100.0
FOV_NASAL_DEG = 60.0
FOV_UP_DEG = 60.0
FOV_DOWN_DEG = 70.0

# ── THE FOVEA, as anatomy rather than as an angle: a 1.5 mm pit with a 0.35 mm rod-free floor.
# The ANGLES are derived below by dividing these by the nodal distance -- which is the check, because
# they have to come out at the ~5.2 deg and ~1.2 deg the clinical literature quotes.
FOVEA_M = 1.50e-3
FOVEOLA_M = 0.35e-3

# ── THE HOLE. The optic disc: no receptors at all where the nerve and the vessels leave. Centred
# ~15.5 deg temporal and ~1.5 deg below fixation, about 5.5 x 7.5 deg (standard perimetry).
BLIND_SPOT_ECC_DEG = 15.5
BLIND_SPOT_DOWN_DEG = 1.5
BLIND_SPOT_W_DEG = 5.5
BLIND_SPOT_H_DEG = 7.5

# ── ACUITY VS ECCENTRICITY. Weymouth 1958; Levi, Klein & Aitsebaomo 1985, Vision Res. 25:963 --
# the E2 form: the minimum resolvable angle doubles E2 degrees out from fixation. E2 = 2.5 deg for
# resolution acuity. This one law is the entire justification for foveated rendering.
E2_DEG = 2.5

# ── THE PUPIL. Moon & Spencer 1944, JOSA 34:319 -- diameter against adapting field luminance.
# Spans 1.9 mm at 1e6 cd/m2 to 7.9 mm at absolute threshold, which is the measured human range.
def pupil_diameter_m(luminance_cd_m2: float) -> float:
    """D = 4.9 - 3*tanh(0.4*log10 L), in millimetres, returned in metres."""
    L = max(float(luminance_cd_m2), 1e-12)
    return (4.9 - 3.0 * math.tanh(0.4 * math.log10(L))) * 1e-3


# ── THE OPERATING RANGE. Absolute scotopic threshold of a scene, and the level at which light is
# painful. Standard visual-science limits; the span is what "the eye works over ten orders" means.
LUMINANCE_MIN_CD_M2 = 1e-6
LUMINANCE_MAX_CD_M2 = 1e8
INSTANT_RANGE_LOG10 = 3.0        # what a single adaptation state covers (photoreceptor response range)

# ── DARK ADAPTATION. Hecht, Haig & Chase 1937, J. Gen. Physiol. 20:831 (archived in the eye/ dir):
# the two-branch curve. Cones finish in ~5 min and buy ~2 log units; the rod-cone break is at ~7 min;
# rods keep going for another half hour and buy ~5 log units in total.
CONE_ADAPT_S = 300.0
ROD_CONE_BREAK_S = 420.0
ROD_ADAPT_S = 2100.0
# The pupil's own reflex, for contrast: fast, and almost irrelevant to the range. Standard pupillometry.
PUPIL_LATENCY_S = 0.22
PUPIL_CONSTRICT_S = 1.0
PUPIL_DILATE_S = 5.0

# ── THE CLOCK. Bentivoglio et al. 1997, Mov. Disord. 12:1028 -- measured spontaneous blink rate at
# rest, 17/min. Rayner 1998 / Henderson 2003 -- fixation durations in natural scene viewing,
# 250-350 ms. Bahill, Adler & Stark 1975 -- the SACCADIC MAIN SEQUENCE, duration = 2.2*A + 21 ms.
BLINK_RATE_PER_MIN = 17.0
BLINK_DURATION_S = 0.15
FIXATION_S = 0.300
SACCADE_AMPLITUDE_DEG = 12.0     # mean amplitude in free viewing of natural scenes
# Burr, Morrone & Ross 1994, Nature 371:511 -- contrast sensitivity falls ~0.5 log unit during a
# saccade. The world does not smear, because it is turned down while the eye is moving.
SACCADIC_SUPPRESSION_LOG10 = 0.5

# ── AND A FIXATION IS NOT STILL. Ratliff & Riggs 1950; Martinez-Conde, Macknik & Hubel 2004 --
# ocular DRIFT of a few arcminutes at a few arcminutes per second, with a TREMOR of about a third
# of an arcminute at 30-100 Hz riding on it.
#
# IT MUST NOT BE STILL, and this is the measurement that says so: Ditchburn & Ginsborg 1952 and
# Riggs et al. 1953 optically STABILISED the retinal image so it could not move, and it FADED TO
# NOTHING within a couple of seconds. A perfectly steady eye is a blind eye -- the receptors are
# differencing detectors and a constant signal is no signal.
#
# The excursion is a few ARCMINUTES against a 200-degree field, so it is invisible in the picture,
# and that is the honest thing for it to be. It is also about three FOVEAL RESOLVABLE ELEMENTS
# wide, which is why it is enough.
DRIFT_ARCMIN = 2.5
TREMOR_ARCMIN = 0.3
TREMOR_HZ = 60.0

# ── STEREO. Best clinical stereoacuity thresholds (Titmus/Randot) run 20-40 arcsec; trained
# observers reach 2-6 arcsec. 20 arcsec is the number that sets where two eyes stop paying.
STEREOACUITY_ARCSEC = 20.0

# ── THE AIR AND THE STAR. Solar constant (IAU 2015 nominal 1361 W/m2) and the luminous efficacy of
# sunlight at the ground, ~93 lm/W. The efficacy is a property of the STAR'S SPECTRUM, so it is a
# FALLBACK here and is replaced the instant the parent carries T_star_surface -- see derive().
SOLAR_CONSTANT_W_M2 = 1361.0
SOLAR_EFFICACY_LM_PER_W = 93.0
SOLAR_T_REFERENCE_K = 5772.0     # used ONLY to check this file's own integrator, never as this star
# Broadband clear-sky optical depth at Earth sea level, giving direct-normal transmission ~0.75 at
# one air mass. Scaled by the parent's own surface pressure, because a thinner sky extinguishes less.
TAU_CLEAR_EARTH = 0.28
P_EARTH_BAR = 1.0

# ── MACULAR PIGMENT. Lutein and zeaxanthin, concentrated in the fovea -- the macula LUTEA, the
# yellow spot, and the one real colour an eye has of its own. Peak optical density 0.35-0.50 at
# 460 nm at the foveal centre, falling with an e-folding of ~1.5 deg (Hammond, Wooten & Snodderly
# 1997 and the heterochromatic-flicker literature). The BAND SHAPE below is a single Gaussian fitted
# by eye to the measured absorbance envelope -- an approximation, and it is labelled as one.
MP_PEAK_OD = 0.40
MP_CENTRE_NM = 460.0
MP_SIGMA_NM = 34.0
MP_EFOLD_DEG = 1.5

WIEN_B_M_K = 2.897771955e-3      # CODATA displacement constant
H_PLANCK, C_LIGHT, K_BOLTZ = 6.62607015e-34, 2.99792458e8, 1.380649e-23
LUMEN_PER_WATT_AT_PEAK = 683.0   # SI definition of the candela

FREE = {
    # WHAT THE PERSON IS STANDING IN FRONT OF. The adapting luminance is the scene's reflectance
    # times the illuminance, and this chapter does not know the scene -- so it is free, and the
    # chapter's job is to demonstrate that it barely matters. Sixteenfold here is 13% in acuity.
    "scene_reflectance": {"lo": 0.02, "hi": 0.90, "default": 0.20,
                          "label": "mean scene reflectance", "unit": "fraction",
                          "local": "what the eye is looking at is not a property of the eye"},
}


# ══════════════════════════════════════════════════════════════════════════════════════════════════
#  THE MEASURED CURVES, read off disk. A membrane may type a law; it may not type a measurement.
# ══════════════════════════════════════════════════════════════════════════════════════════════════
_CACHE: dict = {}


def _refdir() -> Path:
    """research_references/human/, found by walking up -- the pattern skin_optics.py established."""
    q = Path(__file__).resolve().parent
    for _ in range(24):
        f = q / "research_references" / "human"
        if f.is_dir():
            return f
        q = q.parent
    raise FileNotFoundError("research_references/human -- see research_references/human/SOURCES.md")


def _csv(name: str, ncol: int = 2) -> np.ndarray:
    """A numeric CSV with no header noise: every row that parses, in order."""
    if name in _CACHE:
        return _CACHE[name]
    rows = []
    with open(_refdir() / "eye" / name, newline="") as f:
        for row in csv.reader(f):
            try:
                rows.append([float(x) for x in row[:ncol]])
            except (ValueError, IndexError):
                continue
    if not rows:
        raise ValueError(f"{name} parsed to nothing")
    _CACHE[name] = np.asarray(rows, dtype=np.float64)
    return _CACHE[name]


def photopic():
    """CIE 1924 V(lambda) -- the daylight luminous-efficiency function. MEASURED, not modelled."""
    a = _csv("cie1924_photopic_vlambda.csv")
    return a[:, 0], a[:, 1]


def scotopic():
    """CIE 1951 V'(lambda) -- the same curve for the dark-adapted, rod-driven eye."""
    a = _csv("cie1951_scotopic_vlambda.csv")
    return a[:, 0], a[:, 1]


def cmf():
    """CIE 1931 colour-matching functions: the bridge from a spectrum to a colour, with no taste in it."""
    a = _csv("ciexyz1931_cmf.csv", 4)
    return a[:, 0], a[:, 1], a[:, 2], a[:, 3]


def _integ(y, x):
    f = getattr(np, "trapezoid", None) or np.trapz
    return float(f(y, x))


def curve_peak_nm(nm, v) -> float:
    """WHERE A MEASURED CURVE PEAKS, refined between samples by a parabola through the top three.

    This is how this chapter gets its design wavelength. Nobody types 555 nm here: the CIE's own
    1924 table is read off disk and asked where it is highest."""
    nm = np.asarray(nm, float)
    v = np.asarray(v, float)
    i = int(np.argmax(v))
    if i == 0 or i == len(v) - 1:
        return float(nm[i])
    y0, y1, y2 = v[i - 1], v[i], v[i + 1]
    den = y0 - 2.0 * y1 + y2
    off = 0.0 if den == 0.0 else 0.5 * (y0 - y2) / den
    return float(nm[i] + off * (nm[i + 1] - nm[i]))


def planck_nm(nm, T):
    """Spectral radiance per unit wavelength of a blackbody, in whatever units cancel here."""
    lam = np.asarray(nm, float) * 1e-9
    x = H_PLANCK * C_LIGHT / (lam * K_BOLTZ * float(T))
    return (2.0 * H_PLANCK * C_LIGHT * C_LIGHT / lam ** 5) / np.expm1(np.clip(x, 1e-12, 700.0))


def luminous_efficacy(T: float) -> float:
    """HOW MANY LUMENS A WATT OF THIS STAR'S LIGHT IS WORTH -- 683 * int(B*V) / int(B).

    A watt is a watt; a LUMEN is a watt weighted by the eye that receives it. So this number is the
    handshake between a star and a retina, and it is the reason the missing T_star_surface matters:
    without it, the brightness of this world's day cannot be stated, only guessed at from the Sun's.

    CHECKED AGAINST ITSELF: at 5772 K this returns 92.0 lm/W where the measured solar value is ~93,
    and it maxes at 95.4 lm/W near 6600 K where the literature puts the blackbody maximum at ~95.
    Two agreements the integrator was not fitted to."""
    nm, V = photopic()
    num = _integ(planck_nm(nm, T) * V, nm)
    full = np.linspace(1.0, 40000.0, 60000)
    den = _integ(planck_nm(full, T), full)
    return LUMEN_PER_WATT_AT_PEAK * num / max(den, 1e-300)


def spectrum_to_srgb(nm_grid, power) -> np.ndarray:
    """A SPECTRUM'S COLOUR, through the CIE 1931 observer and the sRGB primaries. No palette exists
    anywhere in this file; every colour it draws arrives through this function."""
    wl, xb, yb, zb = cmf()
    p = np.interp(wl, np.asarray(nm_grid, float), np.asarray(power, float), left=0.0, right=0.0)
    X, Y, Z = _integ(p * xb, wl), _integ(p * yb, wl), _integ(p * zb, wl)
    s = X + Y + Z
    if s <= 0:
        return np.zeros(3, np.float64)
    M = np.array([[3.2406, -1.5372, -0.4986],
                  [-0.9689, 1.8758, 0.0415],
                  [0.0557, -0.2040, 1.0570]])
    rgb = np.clip(M @ np.array([X / s, Y / s, Z / s]), 0.0, None)
    return rgb / max(rgb.max(), 1e-12)


def macular_transmittance_rgb(ecc_deg) -> np.ndarray:
    """THE COLOUR OF THE FOVEA, and it is a real filter rather than a look.

    Lutein and zeaxanthin sit in front of the foveal cones and absorb blue. The optical density is
    ~0.40 at the centre and e-folds away over ~1.5 deg, so the middle of the visual field is
    genuinely YELLOWER than its edge -- which is why the anatomists called it the yellow spot before
    anybody could measure a spectrum.

    Normalised by the unfiltered periphery, so what comes back is the pigment's effect ALONE. That
    matters here for an honest reason: the ILLUMINANT is unknown (theHuman does not carry the star's
    temperature), so the day's own colour cannot be supplied. Everything outside the macula is
    therefore drawn neutral, and that neutrality is the missing number made visible."""
    wl = cmf()[0]
    band = np.exp(-0.5 * ((wl - MP_CENTRE_NM) / MP_SIGMA_NM) ** 2)
    ref = spectrum_to_srgb(wl, np.ones_like(wl))
    out = np.empty((len(np.atleast_1d(ecc_deg)), 3), np.float64)
    for i, E in enumerate(np.atleast_1d(ecc_deg)):
        od = MP_PEAK_OD * math.exp(-float(E) / MP_EFOLD_DEG)
        c = spectrum_to_srgb(wl, 10.0 ** (-od * band))
        c = c / np.maximum(ref, 1e-9)
        out[i] = c / max(c.max(), 1e-12)
    return out


def interpupillary_m():
    """IPD FROM 4,082 MEASURED ADULTS, and the reason it is not scaled to this body's height.

    ANSUR II records interpupillary breadth in tenths of a millimetre (the median 640 is 64.0 mm --
    every other linear column in the file is whole millimetres, and 640 mm between the eyes would be
    a horse). Returned with the Pearson correlation against stature, which is **0.18**: stature
    explains 3% of the variance, so an eye's separation is very nearly a constant of the species and
    NOT a fraction of a person. Same fact as the eyeball itself, measured a second way."""
    try:
        ipd, stat = [], []
        with open(_refdir() / "ANSUR_II_MALE_Public.csv", encoding="latin-1", newline="") as f:
            for row in csv.DictReader(f):
                try:
                    ipd.append(float(row["interpupillarybreadth"]) * 1e-4)   # 0.1 mm -> m
                    stat.append(float(row["stature"]) * 1e-3)                # mm -> m
                except (KeyError, ValueError, TypeError):
                    continue
        if len(ipd) < 100:
            raise ValueError("too few rows")
        a, b = np.asarray(ipd), np.asarray(stat)
        r = float(np.corrcoef(b, a)[0, 1])
        return float(np.median(a)), r, len(a)
    except Exception:
        # Honest fallback, flagged by n = 0 so measure() can see it did not come from the file.
        return 0.0640, float("nan"), 0


# ══════════════════════════════════════════════════════════════════════════════════════════════════
#  THE LAWS
# ══════════════════════════════════════════════════════════════════════════════════════════════════
def rayleigh_rad(lambda_m: float, D_m: float) -> float:
    """theta = 1.22 * lambda / D. The floor under every optical system that ever existed: two points
    closer than this land in one another's diffraction disc and there is no image of two points."""
    return 1.22 * float(lambda_m) / max(float(D_m), 1e-12)


def mar_at(ecc_deg, mar0_rad: float) -> np.ndarray:
    """The minimum resolvable angle E degrees out from fixation: MAR0 * (1 + E/E2). Levi & Klein."""
    return float(mar0_rad) * (1.0 + np.asarray(ecc_deg, float) / E2_DEG)


def field_ellipse_rad():
    """The head-fixed field as an ellipse in azimuth and elevation, from the perimetry limits above.
    Horizontal is symmetric because two eyes union; vertical is not (a brow beats a cheek)."""
    return math.radians(FOV_TEMPORAL_DEG), math.radians(0.5 * (FOV_UP_DEG + FOV_DOWN_DEG))


def field_solid_angle_sr(n: int = 900) -> float:
    """SOLID ANGLE OF THE VISUAL FIELD, integrated rather than approximated.

    A rectangle-on-a-sphere formula breaks down past 90 deg of azimuth and this field is 200 wide,
    so the cos(elevation) weighting is summed directly over the ellipse. The answer, 5.27 sr, is 42%
    of the whole sphere -- a person standing still sees very nearly half of everywhere, at almost
    none of the resolution they think they have."""
    A, B = field_ellipse_rad()
    az = np.linspace(-A, A, n)
    el = np.linspace(-B, B, n)
    AZ, EL = np.meshgrid(az, el)
    inside = (AZ / A) ** 2 + (EL / B) ** 2 <= 1.0
    return float((np.cos(EL) * inside).sum() * (az[1] - az[0]) * (el[1] - el[0]))


def cone_solid_angle_sr(diameter_deg: float) -> float:
    """2*pi*(1 - cos a) for a circular patch of the field, a = half its angular diameter."""
    return 2.0 * math.pi * (1.0 - math.cos(math.radians(0.5 * float(diameter_deg))))


def sample_counts(mar0_rad: float, n: int = 700):
    """HOW MANY RESOLVABLE ELEMENTS THE FIELD HOLDS -- once at foveal acuity everywhere, and once at
    the acuity the eye actually has. The ratio is what foveated rendering is worth, and it is not a
    marketing number: it is an integral of a measured falloff over a measured field."""
    A, B = field_ellipse_rad()
    az = np.linspace(-A, A, n)
    el = np.linspace(-B, B, n)
    AZ, EL = np.meshgrid(az, el)
    inside = (AZ / A) ** 2 + (EL / B) ** 2 <= 1.0
    dA = (az[1] - az[0]) * (el[1] - el[0])
    w = np.cos(EL) * inside * dA
    ecc = np.degrees(np.arccos(np.clip(np.cos(EL) * np.cos(AZ), -1.0, 1.0)))
    uniform = float((w / mar0_rad ** 2).sum())
    foveated = float((w / mar_at(ecc, mar0_rad) ** 2).sum())
    return uniform, foveated


# ══════════════════════════════════════════════════════════════════════════════════════════════════
#  THE EDGE
# ══════════════════════════════════════════════════════════════════════════════════════════════════
def derive(parent, free):
    if parent is None or "S_earth" not in parent:
        raise ValueError("theEye requires theHuman as its parent")
    free = free or {}
    rho = float(free.get("scene_reflectance", FREE["scene_reflectance"]["default"]))

    S = float(parent["S_earth"])
    alt_deg = float(parent["sun_altitude_at_start_deg"])
    P_bar = float(parent["P_surface_bar"])
    stride_s = float(parent["duration_s"])
    stride_m = float(parent.get("stride_m", 1.0))
    h_eye = float(parent["eye_height_m"])
    h_body = float(parent["height_m"])

    # ── 1. THE DESIGN WAVELENGTH, read off the CIE's measured curve ─────────────────────────────
    lam_ph_nm = curve_peak_nm(*photopic())
    lam_sc_nm = curve_peak_nm(*scotopic())
    lam_m = lam_ph_nm * 1e-9

    # ── 2. THE STAR'S SPECTRUM, if it survived the chain ────────────────────────────────────────
    # It does not. aBlueWorld derives T_star_surface and L_star; aTerrain drops them. The .get() is
    # here so that repairing the carry-chain moves this number and everything downstream of it
    # WITHOUT ANYONE EDITING THIS FILE -- which is the slider test, wired in advance.
    T_star = parent.get("T_star_surface")
    star_reachable = T_star is not None
    if star_reachable:
        T_star = float(T_star)
        efficacy = luminous_efficacy(T_star)
        wien_nm = WIEN_B_M_K / T_star * 1e9
    else:
        efficacy = SOLAR_EFFICACY_LM_PER_W
        wien_nm = None
    # the integrator, checked against a star whose answer is published, and labelled as a reference
    efficacy_check = luminous_efficacy(SOLAR_T_REFERENCE_K)
    wien_check_nm = WIEN_B_M_K / SOLAR_T_REFERENCE_K * 1e9

    # ── 3. THE LIGHT ON THE GROUND ──────────────────────────────────────────────────────────────
    # Beer-Lambert through the parent's OWN atmosphere: optical depth scaled by its surface pressure,
    # air mass from the sun altitude it publishes. Half of what is scattered out of the beam comes
    # back as skylight -- a crude split, stated as crude, and worth 9% of the total.
    E_top_lux = S * SOLAR_CONSTANT_W_M2 * efficacy
    tau = TAU_CLEAR_EARTH * (P_bar / P_EARTH_BAR)
    sin_alt = math.sin(math.radians(alt_deg))
    airmass = 1.0 / max(sin_alt, 1e-6)
    T_atm = math.exp(-tau * airmass)
    E_direct = E_top_lux * T_atm * sin_alt
    E_diffuse = 0.5 * (1.0 - T_atm) * E_top_lux * sin_alt
    E_lux = E_direct + E_diffuse

    # ── 4. THE APERTURE ─────────────────────────────────────────────────────────────────────────
    L_scene = E_lux * rho / math.pi            # Lambertian scene: L = E*rho/pi
    D = pupil_diameter_m(L_scene)
    # and the demonstration that the free number is not doing the work
    D_lo = pupil_diameter_m(E_lux * 0.05 / math.pi)
    D_hi = pupil_diameter_m(E_lux * 0.80 / math.pi)

    # ── 5. ACUITY, THE UNFITTED CHECK ───────────────────────────────────────────────────────────
    mar0 = rayleigh_rad(lam_m, D)
    acuity_arcmin = math.degrees(mar0) * 60.0
    cutoff_cyc_deg = D / lam_m * math.radians(1.0)

    # ── 6. THE SECOND ROUTE: the mosaic underneath ──────────────────────────────────────────────
    # A hexagonal lattice at the measured peak density: area per cone = (sqrt3/2) s^2.
    area_per_cone_m2 = 1.0 / (CONE_PEAK_PER_MM2 * 1e6)
    cone_spacing_m = math.sqrt(2.0 * area_per_cone_m2 / math.sqrt(3.0))
    cone_angle_rad = cone_spacing_m / NODAL_DISTANCE_M
    nyquist_cyc_deg = 1.0 / (2.0 * cone_angle_rad) * math.radians(1.0)
    # THE PUPIL AT WHICH OPTICS AND SAMPLING MEET. Below it the retina is finer than the image;
    # above it the image is finer than the retina. Either way one of them is wasted, so a body that
    # spent nothing on waste should sit near it -- and this one does.
    matched_pupil_m = lam_m / (2.0 * cone_angle_rad)
    retinal_scale_micron_per_degree = NODAL_DISTANCE_M * 1e6 * math.radians(1.0)

    # ── 7. THE FIELD, and how little of it is sharp ─────────────────────────────────────────────
    fovea_deg = math.degrees(FOVEA_M / NODAL_DISTANCE_M)
    foveola_deg = math.degrees(FOVEOLA_M / NODAL_DISTANCE_M)
    Omega = field_solid_angle_sr()
    om_fovea = cone_solid_angle_sr(fovea_deg)
    om_foveola = cone_solid_angle_sr(foveola_deg)
    om_blind = math.pi * math.radians(0.5 * BLIND_SPOT_W_DEG) * math.radians(0.5 * BLIND_SPOT_H_DEG)

    # ── 8. WHAT IS WORTH DRAWING ────────────────────────────────────────────────────────────────
    n_uniform, n_foveated = sample_counts(mar0)
    ipd_m, ipd_r, ipd_n = interpupillary_m()
    stereo_rad = STEREOACUITY_ARCSEC / 206264.806
    stereo_range_m = ipd_m / stereo_rad

    # the horizon, and the honest refusal
    R_planet = None
    for k in ("planet_radius_m", "R_planet_m", "R_planet", "radius_m", "R"):
        if k in parent:
            R_planet = float(parent[k])
            break
    # A NUMBER THAT CANNOT BE DERIVED IS NOT PUBLISHED AS A NaN. A NaN carries the right unit and
    # the right name and poisons everything that binds to it -- which is precisely the failure
    # THE_FOLDING was written to stop. The KEY IS ABSENT and a boolean says why.

    # ── 9. THE RANGE, AND HOW LONG IT TAKES TO CROSS IT ─────────────────────────────────────────
    D_bright = pupil_diameter_m(LUMINANCE_MAX_CD_M2)
    D_dark = pupil_diameter_m(LUMINANCE_MIN_CD_M2)
    pupil_log10 = 2.0 * math.log10(D_dark / D_bright)          # area, not diameter
    range_log10 = math.log10(LUMINANCE_MAX_CD_M2 / LUMINANCE_MIN_CD_M2)

    # ── 10. THE CLOCK ───────────────────────────────────────────────────────────────────────────
    blink_interval_s = 60.0 / BLINK_RATE_PER_MIN
    saccade_s = (2.2 * SACCADE_AMPLITUDE_DEG + 21.0) * 1e-3    # Bahill's main sequence
    cycle_s = FIXATION_S + saccade_s
    # a raised-cosine displacement over the measured duration -- the WAVEFORM is not derived, but
    # its peak velocity is then a prediction, and the main sequence says 300-500 deg/s at 12 deg.
    peak_vel_deg_s = math.pi * SACCADE_AMPLITUDE_DEG / (2.0 * saccade_s)

    out = {
        # ── the organ, and its own clock ────────────────────────────────────────────────────────
        # ITS REAL SIZE, and it is NOT a fraction of the body: an eyeball is 24 mm in a tall person
        # and 24 mm in a short one. The frame emit() draws in is a different thing and says so.
        "extent_m": AXIAL_LENGTH_M,
        # ITS OWN DURATION: one inter-blink interval, the eye's longest closed loop -- the period at
        # which the tear film has to be renewed or the cornea stops being an optic. Ten fixations
        # and ten saccades fit inside it, which is the mechanism the whole chapter is about.
        "duration_s": blink_interval_s,
        "emit_frame": "unit sphere of gaze directions (radius 1 = 1 direction); extent_m is the organ",
        "axial_length_m": AXIAL_LENGTH_M,
        "nodal_distance_m": NODAL_DISTANCE_M,
        "eye_over_stature_ratio": AXIAL_LENGTH_M / h_body,
        "eye_scales_with_body": False,
        "retinal_scale_micron_per_degree": retinal_scale_micron_per_degree,
        "ipd_m": ipd_m,
        "ipd_sample_size": ipd_n,

        # ── the light this world actually delivers ──────────────────────────────────────────────
        "star_spectrum_reachable": star_reachable,
        "luminous_efficacy_lumen_per_watt": efficacy,
        "efficacy_is_a_solar_fallback": not star_reachable,
        "efficacy_at_solar_reference_lumen_per_watt": efficacy_check,
        "wien_peak_wavelength_at_solar_reference": wien_check_nm,
        "illuminance_top_of_atmosphere_lux": E_top_lux,
        "optical_depth": tau,
        "airmass": airmass,
        "atmospheric_transmission_frac": T_atm,
        "sun_altitude_deg": alt_deg,
        "daylight_illuminance_lux": E_lux,
        "daylight_direct_lux": E_direct,
        "daylight_diffuse_lux": E_diffuse,
        "scene_reflectance_frac": rho,
        "adapting_luminance_nit": L_scene,

        # ── the aperture ────────────────────────────────────────────────────────────────────────
        "pupil_diameter_m": D,
        "pupil_area_mm2": math.pi * (D * 1e3 / 2.0) ** 2,
        "retinal_illuminance_td": L_scene * math.pi * (D * 1e3 / 2.0) ** 2,
        "pupil_diameter_at_albedo_005_m": D_lo,
        "pupil_diameter_at_albedo_080_m": D_hi,

        # ── acuity: the check nobody fitted ─────────────────────────────────────────────────────
        "photopic_peak_wavelength": lam_ph_nm,
        "scotopic_peak_wavelength": lam_sc_nm,
        "acuity_rad": mar0,
        "acuity_arcmin": acuity_arcmin,
        "snellen_denominator": 20.0 * acuity_arcmin,
        "diffraction_cutoff_cycles_per_degree": cutoff_cyc_deg,
        "acuity_at_albedo_005_arcmin": math.degrees(rayleigh_rad(lam_m, D_lo)) * 60.0,
        "acuity_at_albedo_080_arcmin": math.degrees(rayleigh_rad(lam_m, D_hi)) * 60.0,
        "acuity_albedo_sensitivity_pct": 100.0 * (math.degrees(rayleigh_rad(lam_m, D_hi)) * 60.0 /
                                                  (math.degrees(rayleigh_rad(lam_m, D_lo)) * 60.0) - 1.0),

        # ── the mosaic: the same answer by a different road ─────────────────────────────────────
        "cone_spacing_m": cone_spacing_m,
        "cone_spacing_arcmin": math.degrees(cone_angle_rad) * 60.0,
        "cone_nyquist_cycles_per_degree": nyquist_cyc_deg,
        "matched_pupil_m": matched_pupil_m,
        "pupil_over_matched_ratio": D / matched_pupil_m,

        # ── the field, and how little of it is sharp ────────────────────────────────────────────
        # The left eye spans -100 to +60 and the right +60 to -60: their UNION is 2*temporal and
        # their OVERLAP is 2*nasal. Two eyes buy 200 degrees of awareness and 120 of depth.
        "fov_horizontal_total_deg": 2.0 * FOV_TEMPORAL_DEG,
        "fov_binocular_deg": 2.0 * FOV_NASAL_DEG,
        "fov_monocular_deg": FOV_TEMPORAL_DEG + FOV_NASAL_DEG,
        "fov_vertical_deg": FOV_UP_DEG + FOV_DOWN_DEG,
        "field_solid_angle_sr": Omega,
        "field_share_of_sphere_frac": Omega / (4.0 * math.pi),
        "fovea_deg": fovea_deg,
        "foveola_deg": foveola_deg,
        "fovea_solid_angle_sr": om_fovea,
        "foveola_solid_angle_sr": om_foveola,
        "fovea_share_of_field_frac": om_fovea / Omega,
        "foveola_share_of_field_frac": om_foveola / Omega,
        "blind_spot_ecc_deg": BLIND_SPOT_ECC_DEG,
        "blind_spot_solid_angle_sr": om_blind,
        "blind_spot_over_foveola_ratio": om_blind / om_foveola,

        # ── what is worth drawing ───────────────────────────────────────────────────────────────
        "render_pixels_per_degree": 1.0 / math.degrees(mar0),
        "resolvable_elements_uniform_count": n_uniform,
        "resolvable_elements_foveated_count": n_foveated,
        "foveation_gain_ratio": n_uniform / max(n_foveated, 1e-9),
        "ganglion_cells_per_eye_count": GANGLION_CELLS_PER_EYE,
        "axons_per_element_count": GANGLION_CELLS_PER_EYE / max(n_foveated, 1e-9),
        "render_grain_at_1m_m": mar0 * 1.0,
        "render_grain_at_10m_m": mar0 * 10.0,
        "render_grain_at_100m_m": mar0 * 100.0,
        "render_grain_at_1km_m": mar0 * 1000.0,
        "person_vanishes_m": h_body / mar0,
        "stereo_range_m": stereo_range_m,
        "stereoacuity_arcsec": STEREOACUITY_ARCSEC,
        "horizon_reachable": R_planet is not None,
        "eye_height_m": h_eye,

        # ── the range, and the time it costs to cross it ────────────────────────────────────────
        "luminance_min_nit": LUMINANCE_MIN_CD_M2,
        "luminance_max_nit": LUMINANCE_MAX_CD_M2,
        "luminance_range_log10": range_log10,
        "instantaneous_range_log10": INSTANT_RANGE_LOG10,
        "pupil_diameter_bright_m": D_bright,
        "pupil_diameter_dark_m": D_dark,
        "pupil_range_log10": pupil_log10,
        "pupil_share_of_range_frac": pupil_log10 / range_log10,
        "cone_adapt_s": CONE_ADAPT_S,
        "rod_cone_break_s": ROD_CONE_BREAK_S,
        "rod_adapt_s": ROD_ADAPT_S,
        "dark_adapt_strides_count": ROD_ADAPT_S / stride_s,
        "dark_adapt_walk_m": ROD_ADAPT_S / stride_s * stride_m,
        "pupil_latency_s": PUPIL_LATENCY_S,
        "pupil_constrict_s": PUPIL_CONSTRICT_S,
        "pupil_dilate_s": PUPIL_DILATE_S,

        # ── the clock in detail ─────────────────────────────────────────────────────────────────
        "blink_rate_per_min": BLINK_RATE_PER_MIN,
        "blink_interval_s": blink_interval_s,
        "blink_duration_s": BLINK_DURATION_S,
        "blink_duty_frac": BLINK_DURATION_S / blink_interval_s,
        "fixation_s": FIXATION_S,
        "saccade_amplitude_deg": SACCADE_AMPLITUDE_DEG,
        "saccade_s": saccade_s,
        "saccade_cycle_s": cycle_s,
        "saccades_per_blink_interval_count": blink_interval_s / cycle_s,
        "saccade_peak_velocity_degrees_per_second": peak_vel_deg_s,
        "saccadic_suppression_log10": SACCADIC_SUPPRESSION_LOG10,
        # AND THE EYE IS NEVER STILL. The drift is a few arcminutes -- nothing against a 200 deg
        # field, and a couple of FOVEAL ELEMENTS, which is the scale that matters. Hold it truly
        # still and vision fails: a stabilised retinal image fades to nothing in about two seconds.
        "fixation_drift_arcmin": DRIFT_ARCMIN,
        "fixation_tremor_arcmin": TREMOR_ARCMIN,
        "tremor_frequency_hz": TREMOR_HZ,
        "drift_over_acuity_ratio": math.radians(DRIFT_ARCMIN / 60.0) / mar0,
        "e2_deg": E2_DEG,

        # ── carried on, so a child never re-reaches past this membrane ──────────────────────────
        "S_earth": S,
        "height_m": h_body,
    }
    # THE KEYS THAT ONLY EXIST IF THE CHAIN CARRIES WHAT THEY NEED. Present or absent, never NaN.
    if star_reachable:
        out["T_star_surface"] = float(T_star)
        out["wien_peak_wavelength"] = wien_nm
    if R_planet is not None:
        out["planet_radius_m"] = R_planet
        out["horizon_m"] = math.sqrt(2.0 * R_planet * h_eye)
        out["horizon_grain_m"] = mar0 * out["horizon_m"]
    if ipd_n > 0:
        out["ipd_stature_pearson_r"] = ipd_r
    return out


# ══════════════════════════════════════════════════════════════════════════════════════════════════
#  THE MATTER -- the eye's own sampling lattice, over one inter-blink interval
# ══════════════════════════════════════════════════════════════════════════════════════════════════
def _lattice(mar0, coarse, emax_deg=118.0):
    """EVERY RESOLVABLE ELEMENT IN THE FIELD, laid out by the acuity law and nothing else.

    Rings in eccentricity spaced by the local minimum resolvable angle, and around each ring, the
    same spacing again. That is the entire construction -- and what falls out of it is the LOG-POLAR
    layout the visual cortex is actually wired in. Nobody put it there; tiling a field with elements
    whose size grows as (1 + E/E2) has no other shape available to it.

    `coarse` is a stated decimation: the true lattice at this world's acuity holds 295,000 elements
    per eye and a splat buffer will not take that, so the same law is run at a coarser MAR0. The
    RELATIVE sizes -- which is the whole content of the picture -- are exact."""
    ang = []
    E, ring = 0.0, 0
    emax = math.radians(emax_deg)
    while E < emax:
        step = mar0 * (1.0 + math.degrees(E) / E2_DEG) * coarse
        if ring == 0:
            ang.append((0.0, 0.0))
        else:
            k = max(int(2.0 * math.pi * math.sin(E) / step), 6)
            a = np.arange(k) * (2.0 * math.pi / k) + 0.6180339887 * ring
            for aa in a:
                ang.append((E * math.cos(aa), E * math.sin(aa)))
        E += step
        ring += 1
    A = np.asarray(ang, np.float64)
    ecc = np.hypot(A[:, 0], A[:, 1])
    s = np.where(ecc > 1e-9, np.sin(ecc) / np.maximum(ecc, 1e-9), 1.0)
    d = np.stack([A[:, 0] * s, A[:, 1] * s, np.cos(ecc)], 1)      # true unit directions
    return d, np.degrees(ecc)


GAZE_LIMIT_DEG = 25.0        # the globe turns ~45 deg in its orbit; free viewing uses far less
_WALK: dict = {}


def _fixation_walk(amp_deg, n):
    """THE SEQUENCE OF PLACES THE EYE LOOKS -- and this is the one thing in the chapter that is
    neither derived nor measured, so it is fenced off here and labelled.

    Nothing in this membrane knows what is worth looking at; that is a property of the scene, and
    there is no scene. What IS measured is the STEP: free viewing of natural images gives a mean
    saccade amplitude near 12 deg, so the walk takes measured-length steps in deterministic
    pseudo-random directions and REFLECTS off the limit of the orbit rather than piling up on it."""
    key = (round(float(amp_deg), 6), int(n))
    if key in _WALK:
        return _WALK[key]
    rng = np.random.default_rng(20260731)
    A = math.radians(float(amp_deg))
    lim = math.radians(GAZE_LIMIT_DEG)
    p = np.zeros(2)
    out = [p.copy()]
    for _ in range(int(n)):
        a = rng.uniform(0.0, 2.0 * math.pi)
        r = A * (0.55 + 0.90 * rng.random())        # scatter about the measured mean
        p = p + np.array([r * math.cos(a), r * math.sin(a) * 0.7])   # the field is wider than tall
        for j in (0, 1):
            while abs(p[j]) > lim:
                p[j] = math.copysign(2.0 * lim - abs(p[j]), p[j])    # reflect, do not pile up
        out.append(p.copy())
    _WALK[key] = out
    return out


def _gaze(nums, t):
    """WHERE THE FOVEA IS POINTING AT TIME t, and whether the eye is in flight.

    Ten fixations and ten saccades in one inter-blink interval, then the lid. The AMPLITUDE and the
    TIMING are measured (Bahill's main sequence for the duration, Rayner's fixation durations for
    the dwell); only the direction of each step is arbitrary, and _fixation_walk says so.

    The displacement through a saccade is a raised cosine, which is an approximation to the real
    velocity profile. Its consequence is not an approximation: peak velocity comes out at 398 deg/s
    where the main sequence measures 300-500 for a 12 degree saccade."""
    T = float(nums["duration_s"])
    cyc = float(nums["saccade_cycle_s"])
    sac = float(nums["saccade_s"])
    tt = (float(t) % 1.0) * T
    i = int(tt // cyc)
    u = (tt - i * cyc) / cyc
    frac_fix = 1.0 - sac / cyc

    walk = _fixation_walk(nums["saccade_amplitude_deg"], int(T / cyc) + 3)
    p0, p1 = walk[min(i, len(walk) - 2)], walk[min(i + 1, len(walk) - 1)]
    if u < frac_fix:
        pos, flight = p0, 0.0
    else:
        v = (u - frac_fix) / max(1.0 - frac_fix, 1e-9)
        pos = p0 + (p1 - p0) * 0.5 * (1.0 - math.cos(math.pi * v))
        flight = math.sin(math.pi * v)         # 0..1..0: how deep in the saccade the eye is

    # A FIXATION IS NOT A STOP. Drift plus tremor, at their measured amplitudes -- so there is no
    # instant in this movie at which the eye is not moving, which is a fact about eyes and not a
    # convenience. Two incommensurate slow components for the drift and a 60 Hz tremor on top; the
    # WAVEFORMS are a stand-in for a random walk, the AMPLITUDES are measured, and the whole
    # excursion is a few arcminutes -- three foveal elements, and invisible at this framing.
    dr = math.radians(DRIFT_ARCMIN / 60.0)
    tr = math.radians(TREMOR_ARCMIN / 60.0)
    w = 2.0 * math.pi * tt
    pos = pos + np.array([
        dr * math.sin(0.83 * w) + tr * math.sin(TREMOR_HZ * w),
        dr * math.sin(1.31 * w + 1.1) + tr * math.cos(1.07 * TREMOR_HZ * w),
    ])
    return pos, flight


def emit(nums, t=1.0):
    """THE EYE'S SAMPLING LATTICE, over one inter-blink interval.

    LOCAL UNITS: radius 1 is the unit sphere of GAZE DIRECTIONS. This membrane's matter is angular,
    because what an eye owns is directions -- `extent_m` is the organ (24 mm of tissue) and the two
    are different quantities, which the chapter says rather than reconciling with a fudge.

    WHAT IS BEING DRAWN, and every property of it is a measurement:
      * ONE GRAIN PER RESOLVABLE ELEMENT, placed by the acuity law MAR(E) = MAR0*(1 + E/2.5deg).
      * ITS SIZE IS THE ANGLE IT RESOLVES. A splat of angular size s at radius 1 subtends s radians,
        so the grain is not a symbol for the resolution -- it IS the resolution, at true scale. The
        knot at the fovea and the boulders at the edge are the same law at two eccentricities.
      * THE HOLE is the optic disc: no receptors, 15.5 deg out, and 28 TIMES THE AREA of the
        sharpest part of vision. It is eye-fixed, so watch it travel with the fovea.
      * THE OVAL IS THE HEAD'S FIELD and does not move. The lattice inside it does. That is the
        whole trick of vision: 0.0066% of the field is sharp, and the eye hides that by moving the
        sharp part three times a second.
      * THE COLOUR IS THE MACULAR PIGMENT and nothing else. Amber at the centre where lutein
        absorbs blue, neutral by 8 degrees out. It is neutral out there because the ILLUMINANT IS
        UNKNOWN -- theHuman does not carry the star's temperature -- so that grey is a missing
        number rather than a choice.
      * IT DIMS WHILE THE EYE IS IN FLIGHT, by the measured 0.5 log unit of saccadic suppression.
      * AT THE END THE LID COMES DOWN. What is under a closed lid is not black: hemoglobin passes
        long wavelengths, which is the same measurement theSkin derives its own colour from.
    """
    from matter import blank, lit, SOLID

    mar0 = float(nums["acuity_rad"])
    COARSE = 10.0                                  # stated decimation; see _lattice()
    d0, ecc = _lattice(mar0, COARSE)

    gaze, in_flight = _gaze(nums, t)
    ca, sa = math.cos(gaze[0]), math.sin(gaze[0])
    ce, se = math.cos(gaze[1]), math.sin(gaze[1])
    # elevate then swing: R @ (0,0,1) lands at exactly (azimuth, elevation) = gaze, +y is up
    R = np.array([[ca, 0.0, sa], [0.0, 1.0, 0.0], [-sa, 0.0, ca]]) @ \
        np.array([[1.0, 0.0, 0.0], [0.0, ce, se], [0.0, -se, ce]])
    d = d0 @ R.T

    # the head's field, fixed: an ellipse in azimuth and elevation from the perimetry limits
    A_fov, B_fov = field_ellipse_rad()
    az = np.arctan2(d[:, 0], d[:, 2])
    el = np.arcsin(np.clip(d[:, 1], -1.0, 1.0))
    inside = (az / A_fov) ** 2 + (el / B_fov) ** 2 <= 1.0

    # the blind spot, eye-fixed: tested in the FOVEA's frame, so it rides along with the gaze
    faz = np.degrees(np.arctan2(d0[:, 0], d0[:, 2]))
    fel = np.degrees(np.arcsin(np.clip(d0[:, 1], -1.0, 1.0)))
    hole = (((faz - BLIND_SPOT_ECC_DEG) / (0.5 * BLIND_SPOT_W_DEG)) ** 2 +
            ((fel + BLIND_SPOT_DOWN_DEG) / (0.5 * BLIND_SPOT_H_DEG)) ** 2) <= 1.0

    # TWO DIFFERENT KINDS OF NOTHING, and telling them apart is the point.
    #   the blind spot   -- NO RECEPTORS. There is no matter there, so no grain is emitted.
    #   outside the field -- receptors, but the brow and the cheek and the nose are in the way.
    #     The matter exists and nothing arrives on it, so it is emitted and lit by ZERO. It goes
    #     black by the same lit() call that lights everything else, and the faint ghost beyond the
    #     oval is how much retina a face costs.
    # This also makes the emitted count CONSTANT across t -- the hole is eye-fixed, so only the
    # illumination moves, and a frame-to-frame difference is a difference and not a reindexing.
    d, ecc = d[~hole], ecc[~hole]
    el = el[~hole]
    seen = inside[~hole]
    n = len(d)

    # ── COLOUR: the scene's reflectance, through the macular pigment. Nothing else is in it ──────
    # The grains are samples OF something, and the only thing this chapter knows about that
    # something is the reflectance the pupil was derived from -- so that is the albedo, tinted by
    # the one filter the eye supplies itself. A 20% scene reads as a 20% grey, which is what an
    # adapted eye is for.
    bands = np.array([0.0, 0.25, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0, 9.0, 15.0, 30.0, 60.0, 120.0])
    lut = macular_transmittance_rgb(bands) * float(nums["scene_reflectance_frac"])
    alb = lut[np.clip(np.searchsorted(bands, ecc), 0, len(bands) - 1)].astype(np.float32)

    # ── HOW MUCH LIGHT IS GETTING THROUGH, right now ────────────────────────────────────────────
    supp = 10.0 ** (-float(nums["saccadic_suppression_log10"]) * in_flight)
    E_ref = float(nums["retinal_illuminance_td"])
    E_now = np.where(seen, E_ref * supp, 0.0)      # occluded receptors receive nothing

    # ── THE LID, over the last blink_duration_s of the interval ─────────────────────────────────
    T = float(nums["duration_s"])
    bd = float(nums["blink_duration_s"])
    tt = (float(t) % 1.0) * T
    lid = np.zeros(n, bool)
    if tt > T - bd:
        v = (tt - (T - bd)) / bd                    # 0..1 across the blink
        # down fast, up slower: the measured asymmetry of a spontaneous blink
        close = math.sin(math.pi * min(v / 0.4, 1.0)) if v < 0.4 else 1.0 - (v - 0.4) / 0.6
        margin = B_fov - 2.0 * B_fov * max(0.0, min(close, 1.0))
        lid = el > margin

    col = lit(alb, E_now, e_ref=E_ref, tone=0.35)
    if lid.any():
        # through a closed lid: hemoglobin passes red and eats the rest. Same physics as theSkin.
        col[lid] = col[lid] * np.array([0.20, 0.045, 0.030], np.float32)

    b = blank(n)
    b[:, 0:3] = d
    # A FIELD OF DIRECTIONS HAS NO SURFACE, therefore no normal. The column is left zero on purpose
    # so nothing is back-face culled -- the periphery beyond 90 deg is the point of the picture.
    b[:, 16:19] = col
    b[:, 24:27] = alb
    # the occluded rim is faint because there is nothing on it, not because it was faded on purpose
    b[:, 19] = np.where(seen, np.where(lid, 0.85, 0.94), 0.10)
    # THE SIZE IS THE MEASUREMENT: the angle this element resolves, at radius 1, times the stated
    # decimation. Nothing about it is a look.
    b[:, 20] = (mar0 * (1.0 + ecc / E2_DEG) * COARSE * 0.62).astype(np.float32)
    b[:, 11] = SOLID
    return b


def measure(nums):
    """Facts a reader can check without trusting a word of the prose above."""
    return {
        # ── THE CHECK THIS CHAPTER WAS NOT FITTED TO. Insolation, air pressure and a sun altitude
        # went in; the 20/20 line came out.
        "acuity_arcmin": nums["acuity_arcmin"],
        "acuity_is_the_2020_line": abs(nums["acuity_arcmin"] - 1.0) < 0.15,
        "snellen_denominator": nums["snellen_denominator"],

        # ── AND THE SECOND ROUTE, from a cone mosaic that knows nothing about this world's sun
        "cone_nyquist_cycles_per_degree": nums["cone_nyquist_cycles_per_degree"],
        "nyquist_is_60_cyc_per_deg": abs(nums["cone_nyquist_cycles_per_degree"] - 60.0) < 4.0,
        "pupil_over_matched_ratio": nums["pupil_over_matched_ratio"],
        "eye_sits_at_its_own_diffraction_limit": 0.7 < nums["pupil_over_matched_ratio"] < 1.5,

        # ── the optics constants reproduce the clinical ones they were not given
        "retinal_scale_micron_per_degree": nums["retinal_scale_micron_per_degree"],
        "retinal_scale_matches_drasdo_fowler": abs(nums["retinal_scale_micron_per_degree"] - 291.0) < 6.0,
        "fovea_deg": nums["fovea_deg"],
        "fovea_is_about_5_deg": 4.6 < nums["fovea_deg"] < 5.8,
        "foveola_deg": nums["foveola_deg"],
        "foveola_is_about_1_deg": 1.0 < nums["foveola_deg"] < 1.4,

        # ── this file's own integrator, checked against a star with a published answer
        "efficacy_at_solar_reference_lumen_per_watt": nums["efficacy_at_solar_reference_lumen_per_watt"],
        "efficacy_matches_measured_sunlight": abs(nums["efficacy_at_solar_reference_lumen_per_watt"] - 93.0) < 3.0,

        # ── the free number is shown not to matter, rather than argued not to
        "acuity_albedo_sensitivity_pct": nums["acuity_albedo_sensitivity_pct"],
        "acuity_insensitive_to_scene": abs(nums["acuity_albedo_sensitivity_pct"]) < 20.0,

        # ── what the renderer is being told
        "foveola_share_of_field_frac": nums["foveola_share_of_field_frac"],
        "sharp_part_is_under_a_thousandth": nums["foveola_share_of_field_frac"] < 1e-3,
        "foveation_gain_ratio": nums["foveation_gain_ratio"],
        "axons_per_element_count": nums["axons_per_element_count"],
        # ON and OFF midget pairs plus parasol cells is ~4 axons per sampled point, so a whole-field
        # integral landing near 4 is the retina's own wiring agreeing with this chapter's arithmetic.
        "nerve_matches_element_count": 1.5 < nums["axons_per_element_count"] < 8.0,
        "blind_spot_over_foveola_ratio": nums["blind_spot_over_foveola_ratio"],

        # ── the saccade's waveform predicted a velocity it was not given
        "saccade_peak_velocity_degrees_per_second": nums["saccade_peak_velocity_degrees_per_second"],
        "peak_velocity_on_main_sequence": 300.0 <= nums["saccade_peak_velocity_degrees_per_second"] <= 500.0,

        # ── the iris is nearly irrelevant, and that is a derived result
        "pupil_share_of_range_frac": nums["pupil_share_of_range_frac"],
        "adaptation_is_chemical_not_mechanical": nums["pupil_share_of_range_frac"] < 0.15,

        # ── its own rhythm needs no gearing, like theAnkle's and theSkin's
        "duration_in_human_band": 0.04 <= nums["duration_s"] <= 10.0,

        # ── AND THE TWO HONEST GAPS, reported as facts rather than hidden
        "star_spectrum_reachable": nums["star_spectrum_reachable"],
        "horizon_reachable": nums["horizon_reachable"],
        "ipd_measured_from_ansur": nums["ipd_sample_size"] > 100,
    }
