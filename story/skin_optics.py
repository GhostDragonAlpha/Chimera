"""skin_optics.py -- THE MEASURED LIGHT MODEL OF SKIN, once, shared.

What leaves a face is not a colour somebody picked: it is what survives two passes through the
epidermis (a melanin filter) after diffusing through the dermis (a blood-and-collagen turbid
medium). Every number here is a MEASUREMENT with a citation, and the module exists at the story
root -- next to matter.py -- because more than one membrane reads it: theHuman publishes what the
body's skin does at the renderer's three bands, and theSkin specialises in the full spectrum.

SOURCES, both archived under research_references/human/ (see SOURCES.md):
  * Jacques, OMLC News Jan 1998 (`skin_optics_omlc_jacques.html`): baseline absorption, melanin
    absorption per melanosome, melanosome volume fractions by pigmentation class, dermal blood
    fractions, and the Rayleigh+Mie reduced-scattering law for dermal collagen.
  * Prahl's OMLC compilation of the Gratzer/Kollias measurements
    (`hemoglobin_extinction_prahl.json`): molar extinction of oxy- and deoxy-hemoglobin,
    250-1000 nm. Jacques' own Figure 2 was an unarchived GIF; this is the table behind it.

THE MODEL (the standard one -- an epidermal filter over a diffusing dermis):
  R(lambda) = T_epi(lambda)^2 * Rd_dermis(lambda)
  T_epi     = exp(-mua_epi * d_epi)              one pass; light crosses twice (Jacques' convention:
                                                 "total photon path is twice the epidermal thickness")
  Rd_dermis = diffusion approximation for a semi-infinite turbid medium
              (Farrell, Patterson & Wilson 1992), internal reflection at n=1.4 (Groenhuis 1983).

UNITS: wavelengths in nm, coefficients in cm^-1. Reflectance is dimensionless and IS the albedo
the renderer's albedo channel expects (a fraction returned, lit by matter.lit).
"""
from __future__ import annotations

import json
import math
from pathlib import Path

# ── THE RENDERER'S THREE BANDS. The same wavelengths the walker's sky already integrates
# (walker.py: "0.64 / 1.12 / 1.96 across R, G, B at 615/535/465 nm"), so skin is measured where
# the light it sits under is measured.
BANDS_NM = (615.0, 535.0, 465.0)

# ── MEASURED CONSTANTS (Jacques 1998) ─────────────────────────────────────────────────────────
D_EPIDERMIS_CM = 0.006          # 60 um -- the thickness Jacques' f.mel convention assumes
F_BLOOD_AVG = 0.002             # average dermal blood volume fraction (0.2%; 2-5% in the plexus)
F_MEL_CLASSES = {"light": (0.013, 0.063), "moderate": (0.11, 0.16), "dark": (0.18, 0.43)}
N_SKIN = 1.4                    # tissue refractive index, the standard skin-optics value
HB_G_PER_L = 150.0              # whole blood (~45% hematocrit, Jacques/Prahl convention)
HB_MW = 64500.0                 # g/mole, Prahl's conversion factor
# DECLARED CONVENTION, NOT MEASURED: the oxygenated fraction of cutaneous blood. Skin blood is a
# capillary/venous mix; 0.75 is the value skin-optics modelling standardises on. It moves the red
# band most (Hb vs HbO2 differ 7x at 615 nm) and is stated so it can be challenged.
OXY_FRAC = 0.75

# ── ARCHIVED SPOT VALUES, so the law can be checked against the numbers it was written from
# (Jacques' own worked examples -- a prediction the model must reproduce, not a fit).
SPOT_MUA_MEL = {694.0: 230.0, 755.0: 170.0, 1064.0: 55.0}                    # cm^-1
SPOT_MUA_EPI_F10 = {694.0: 23.0, 755.0: 17.0, 1064.0: 5.7}                   # at f.mel = 10%

_PRAHL = None


def _prahal():
    """The archived hemoglobin table, loaded once. Fails loudly if it is not on disk."""
    global _PRAHL
    if _PRAHL is None:
        q = Path(__file__).resolve().parent
        for _ in range(6):
            f = q / "research_references" / "human" / "hemoglobin_extinction_prahl.json"
            if f.exists():
                _PRAHL = json.loads(f.read_text())
                break
            q = q.parent
        else:
            raise FileNotFoundError("hemoglobin_extinction_prahl.json -- see research_references/human/SOURCES.md")
    return _PRAHL


def mua_baseline(nm):
    """Absorption of melaninless, bloodless skin [cm^-1] (Huang rat-skin, 350-1100 nm)."""
    return 0.244 + 85.3 * math.exp(-(nm - 154.0) / 66.2)


def mua_melanosome(nm):
    """Absorption inside one melanosome [cm^-1] (Jacques/McAuliffe 1991)."""
    return 6.6e11 * nm ** -3.33


def mua_blood(nm, oxy=OXY_FRAC):
    """Absorption of WHOLE BLOOD [cm^-1] at 150 g/L, from Prahl's archived molar extinction:
    mua = 2.303 * e * x / 64500, linear in the oxy/deoxy mix. Interpolated on the 2 nm grid."""
    p = _prahal()
    ws = p["wavelength_nm"]
    if nm <= ws[0]:
        i, f = 0, 0.0
    elif nm >= ws[-1]:
        i, f = len(ws) - 2, 1.0
    else:
        x = (nm - ws[0]) / (ws[1] - ws[0])
        i = min(int(x), len(ws) - 2)
        f = x - i
    e_o2 = p["HbO2_cm-1_per_M"][i] * (1 - f) + p["HbO2_cm-1_per_M"][i + 1] * f
    e_hb = p["Hb_cm-1_per_M"][i] * (1 - f) + p["Hb_cm-1_per_M"][i + 1] * f
    e = oxy * e_o2 + (1.0 - oxy) * e_hb
    return 2.303 * e * HB_G_PER_L / HB_MW


def musp_dermis(nm):
    """Reduced scattering of dermis [cm^-1]: Rayleigh small-structure + Mie collagen fibres."""
    return 2.0e12 * nm ** -4.0 + 2.0e5 * nm ** -1.5


def mua_epidermis(nm, f_mel):
    """Net epidermal absorption: melanosomes diluted in baseline skin (Jacques eq. 1.4)."""
    return f_mel * mua_melanosome(nm) + (1.0 - f_mel) * mua_baseline(nm)


def mua_dermis(nm, f_blood):
    """Net dermal absorption: blood diluted in baseline skin (Jacques eq. 2.3)."""
    return f_blood * mua_blood(nm) + (1.0 - f_blood) * mua_baseline(nm)


def _internal_reflection(n=N_SKIN):
    """Groenhuis 1983: fraction of diffuse light internally reflected at the tissue-air surface."""
    ri = -1.440 / (n * n) + 0.710 / n + 0.668 + 0.0636 * n
    return (1.0 + ri) / (1.0 - ri)


def diffuse_reflectance(nm, f_blood):
    """Rd of a semi-infinite turbid medium (Farrell, Patterson & Wilson 1992) -- the dermis."""
    mua = mua_dermis(nm, f_blood)
    ap = musp_dermis(nm) / (mua + musp_dermis(nm))          # transport albedo
    if ap >= 1.0:
        return 1.0
    A = _internal_reflection()
    s = math.sqrt(3.0 * (1.0 - ap))
    return 0.5 * ap * (1.0 + math.exp(-(4.0 / 3.0) * A * s)) * math.exp(-s)


def skin_reflectance(nm, f_mel, f_blood=F_BLOOD_AVG):
    """What fraction of light skin returns at one wavelength: the epidermis filters twice
    (down and back up), the dermis diffuses. This number IS the skin's albedo."""
    t = math.exp(-mua_epidermis(nm, f_mel) * D_EPIDERMIS_CM)
    return t * t * diffuse_reflectance(nm, f_blood)


def transport_mfp_cm(nm, f_blood=F_BLOOD_AVG):
    """1/(mua+musp) -- how far a photon random-walks in the dermis before the walk forgets its
    direction. Red light goes millimetres, blue a fraction of one: that gradient IS subsurface
    scattering, and it is why skin glows red-lit from within."""
    return 1.0 / (mua_dermis(nm, f_blood) + musp_dermis(nm))


def skin_albedo_rgb(f_mel, f_blood=F_BLOOD_AVG):
    """The reflectance at the renderer's three bands, R/G/B order, clipped to [0, 1]."""
    return [min(1.0, max(0.0, skin_reflectance(nm, f_mel, f_blood))) for nm in BANDS_NM]


def skin_sss_mfp_mm(f_blood=F_BLOOD_AVG):
    """The transport mean free path at each band, in mm -- the subsurface reach of each colour."""
    return [10.0 * transport_mfp_cm(nm, f_blood) for nm in BANDS_NM]


def check_against_archive():
    """The law against the numbers it was written from (Jacques' worked examples).
    A derivation that cannot reproduce its own source's spot values is a story, not a law."""
    out = {}
    for nm, want in SPOT_MUA_MEL.items():
        out[f"mua_mel_{int(nm)}nm"] = {"got": mua_melanosome(nm), "want": want,
                                       "ok": abs(mua_melanosome(nm) / want - 1.0) < 0.06}
    for nm, want in SPOT_MUA_EPI_F10.items():
        got = mua_epidermis(nm, 0.10)
        out[f"mua_epi_f10_{int(nm)}nm"] = {"got": got, "want": want,
                                           "ok": abs(got / want - 1.0) < 0.06}
    return out


if __name__ == "__main__":
    for name, c in check_against_archive().items():
        print(f"{name:22} got {c['got']:8.3f}  want {c['want']:8.3f}  {'OK' if c['ok'] else 'FAIL'}")
    for cls, (lo, hi) in F_MEL_CLASSES.items():
        mid = 0.5 * (lo + hi)
        rgb = skin_albedo_rgb(mid)
        mfp = skin_sss_mfp_mm()
        print(f"{cls:9} f.mel {mid:5.1%}  albedo RGB [{rgb[0]:.3f} {rgb[1]:.3f} {rgb[2]:.3f}]"
              f"  mfp mm [{mfp[0]:.2f} {mfp[1]:.2f} {mfp[2]:.2f}]")
