"""matter_data.py -- the published constants the non-human passive ports are derived FROM.

WHY THIS MODULE EXISTS. `docs/THE_COMPILER.md` states the passive-tissue framework for grass,
rock, tree, terrain, fabric and vehicle and then says, in its own words, that the framework is
SPECIFIED and not VALIDATED, for exactly two reasons:

    k, c, E, sigma_max ARE FREE NUMBERS AND RULE 1 APPLIES TO ALL OF THEM. Writing F = kx + cv
    programs the FORM. It says NOTHING about k. Each must be DERIVED from a parent, INGESTED
    from a citable measurement, or TRAINED -- and where the data cannot support one, the honest
    output is A REFUSAL WITH A NAME, not a plausible constant.

So this module holds the INGESTED half and nothing else. Every entry carries its source. There is
no default and no fallback: `cite()` raises `Uncited` when a number is missing, because a fallback
is an assumption wearing a hat and this project has paid for that lesson twice (`tools/world.py`
raises rather than assume Earth; `lm_gateway` raises rather than load a model nobody asked for).

    A NUMBER WITHOUT A SOURCE IS A NUMBER SOMEONE CHOSE.

THREE PROVENANCE CLASSES, matching `Chimera/docs/matter/matter_library.json`:

    parent      already published by a membrane of this world -- read through, never re-typed
    researched  a citable external measurement, with the citation stored beside the number
    derived     computed here from `parent`/`researched` entries; the arithmetic is in the entry

WHAT IS DELIBERATELY ABSENT. There is no `chosen` class. If a port needs a number this file cannot
supply, the port must REFUSE and name what is missing -- see `port_tests_matter.py`, where the
rock's Griffith flaw size is derived from two independently published strengths rather than typed,
and the grass blade's damping is refused outright because nobody published it.

    python tools/matter_data.py            # print the whole table with sources
    python tools/matter_data.py --audit    # every entry's unit + provenance, and what is missing
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LIBRARY = ROOT / "Chimera" / "docs" / "matter" / "matter_library.json"


class Uncited(RuntimeError):
    """Raised when a port asks for a constant no source in this file supplies.

    It is a REFUSAL, not an error to be handled. The correct response is to find the measurement
    or to state that the port cannot be validated -- never to supply a plausible value.
    """


def _lib() -> dict:
    """The world's own researched materials library, read through -- never copied.

    `Chimera/docs/matter/matter_library.json` already holds researched density, friction angle,
    cohesion and Young's modulus with the citations attached. Re-typing any of them here would
    make this file a stale copy, which is the defect the instrument rules name four convictions
    for in one day: THE INSTRUMENT MUST MOVE WITH THE MEMBRANE AND KEEP NO COPY OF IT.
    """
    if not LIBRARY.exists():
        raise Uncited(f"the materials library is missing at {LIBRARY}. Every `parent` constant "
                      f"below reads through it; there is no copy here to fall back on.")
    return json.loads(LIBRARY.read_text(encoding="utf8"))


def _from_library(material: str, key: str) -> dict:
    """One researched number out of the library, with its note carried as the citation."""
    lib = _lib()
    mat = lib.get("materials", {}).get(material)
    if mat is None:
        raise Uncited(f"the library holds no material {material!r} -- it holds "
                      f"{sorted(lib.get('materials', {}))}")
    ent = mat.get("physical", {}).get(key)
    if ent is None:
        raise Uncited(f"the library's {material!r} publishes no {key!r} -- it publishes "
                      f"{sorted(mat.get('physical', {}))}. Refusing to substitute a value.")
    if ent.get("provenance") != "researched":
        raise Uncited(f"library {material}.{key} is provenance {ent.get('provenance')!r}, not "
                      f"'researched'. A design or seed value is a CHOICE and may not be cited "
                      f"as a measurement.")
    return dict(value=ent["mean"], spread=ent.get("spread"), unit=key.rsplit("_", 1)[-1],
                source=f"matter_library.json::{material}.{key} -- {ent.get('note', '')}",
                provenance="parent")


# ── THE TABLE ─────────────────────────────────────────────────────────────────────────────────
# Every entry: value, unit, spread (the published uncertainty, NOT a guess), source, provenance.
# `spread` is load-bearing and not decoration -- it is where the TOLERANCE comes from. THE_COMPILER
# warns that "within 5%" is a round number with no source and that a tolerance chosen to be
# comfortable is a falsifier chosen to be survivable. The measurement's own spread is the grain.

def _e(value, unit, source, provenance, spread=None, note=None) -> dict:
    return dict(value=value, unit=unit, spread=spread, source=source,
                provenance=provenance, note=note)


# GRASS -- Vincent, J.F.V. (1982) "The mechanical design of grass", Journal of Materials Science
# 17:856-860. The canonical measurement, on Lolium perenne (perennial ryegrass). Vincent's finding
# is that a grass leaf is an ORIENTED FIBROUS COMPOSITE whose sclerenchyma fibres carry 90-95% of
# the longitudinal stiffness at ~4% volume fraction -- which is why the longitudinal and transverse
# moduli differ by a factor of 39, and why a blade folds across but never along.
_VINCENT = "Vincent 1982, J. Mater. Sci. 17:856-860, 'The mechanical design of grass' (Lolium perenne)"

GRASS = {
    "E_long":      _e(554e6, "Pa", _VINCENT, "researched",
                      note="whole-leaf static longitudinal modulus, 5.54e8 N/m^2"),
    "E_trans":     _e(14.08e6, "Pa", _VINCENT, "researched",
                      note="whole-leaf transverse modulus, 1.408e7 N/m^2"),
    "E_fibre":     _e(22.6e9, "Pa", _VINCENT, "researched",
                      note="sclerenchyma fibre modulus, 2.26e10 N/m^2"),
    "E_bundle":    _e(838e6, "Pa", _VINCENT, "researched", note="vascular bundle modulus"),
    "V_fibre":     _e(0.0424, "1", _VINCENT, "researched", note="sclerenchyma volume fraction"),
    "V_bundle":    _e(0.0412, "1", _VINCENT, "researched", note="vascular bundle volume fraction"),
    "work_fract":  _e(30.0, "J/m2", _VINCENT, "researched", note="specific work of fracture"),
}

# BLADE GEOMETRY -- Lolium perenne, the same species Vincent measured, so the modulus and the
# section belong to one plant rather than to an average of two.
#   THIS IS THE ONE PLACE A DIMENSION IS INGESTED RATHER THAN DERIVED, and it is stated loudly.
#   A grass blade's length and width are the plant's phenotype; no law in this tree derives them
#   yet, because no chapter under theTerrain has grown a sward. When one does, these become
#   `parent` and this block is deleted -- it is a named debt, not a constant.
_GRASS_MORPH = ("Hubbard, C.E. 'Grasses' (3rd ed.) / GrassBase (Kew) species description for "
                "Lolium perenne: leaf blade 4-20 cm long, 2-6 mm wide, flat; mid-band taken")

GRASS_BLADE = {
    "length":    _e(0.12, "m", _GRASS_MORPH, "researched", spread=0.08,
                    note="4-20 cm published range; 12 cm is mid-band. Spread IS the range/2."),
    "width":     _e(4.0e-3, "m", _GRASS_MORPH, "researched", spread=2.0e-3,
                    note="2-6 mm published range"),
    "thickness": _e(0.25e-3, "m", _GRASS_MORPH, "researched", spread=0.1e-3,
                    note="lamina thickness; the thinnest dimension and the one that sets I"),
}

# BASALT -- three independent publications, and their OVER-DETERMINATION is the check.
# E from the library (parent). Strengths from Schultz 1993. Toughness from Balme 2004.
_SCHULTZ = ("Schultz, R.A. 1993, J. Geophys. Res. Planets 98(E6):10883, 'Brittle strength of "
            "basaltic rock masses with applications to Venus' -- intact basalt, 20 degC, "
            "negligible confining pressure")
_BALME = ("Balme, M.R. et al. 2004, J. Volcanol. Geotherm. Res. 132:159-172, 'Fracture toughness "
          "measurements on igneous rocks using a high-pressure, high-temperature rock fracture "
          "mechanics cell' -- Icelandic/Vesuvian/Etnean basalts, 30-600 degC, 0-30 MPa confining")

ROCK = {
    "sigma_t":  _e(14.5e6, "Pa", _SCHULTZ, "researched", spread=3.3e6,
                  note="tensile strength -14.5 +- 3.3 MPa; sign dropped, magnitude kept"),
    "UCS":      _e(266e6, "Pa", _SCHULTZ, "researched", spread=98e6,
                  note="unconfined compressive strength 266 +- 98 MPa"),
    "K_IC":     _e(2.4e6, "Pa*m^0.5", _BALME, "researched", spread=1.2e6,
                  note="ambient band 1.4-3.8 MPa*sqrt(m); 2.4 is mid-band and is the value "
                       "docs/THE_LIVING_MATTER.md already carries. Spread = half the band."),
}

# WOOD -- USDA Forest Products Laboratory, Wood Handbook (FPL-GTR-190), Chapter 5.
# Table 5-1 gives the ELASTIC RATIOS (dimensionless, so they transport between species and
# moisture contents); Table 5-3b gives E_L and the strengths in SI at 12% moisture content.
#   THE RATIOS AND THE ABSOLUTE COME FROM DIFFERENT TABLES ON PURPOSE. Multiplying a ratio by an
#   absolute from the same handbook is the derivation; had both been read off one row there would
#   be nothing to check.
_WH_T51 = "USDA Wood Handbook FPL-GTR-190 Table 5-1 (elastic ratios, ~12% moisture content)"
_WH_T53 = "USDA Wood Handbook FPL-GTR-190 Table 5-3b (SI, clear straight-grained, 12% MC)"

WOOD = {
    "white_oak": {
        "E_L":      _e(12.3e9, "Pa", _WH_T53, "researched", note="MOE 12,300 MPa"),
        "ET_EL":    _e(0.072, "1", _WH_T51, "researched"),
        "ER_EL":    _e(0.163, "1", _WH_T51, "researched"),
        "GLR_EL":   _e(0.086, "1", _WH_T51, "researched"),
        "MOR":      _e(105e6, "Pa", _WH_T53, "researched", note="modulus of rupture 105,000 kPa"),
        "shear_par": _e(13.8e6, "Pa", _WH_T53, "researched", note="shear parallel to grain"),
        "tens_perp": _e(5.5e6, "Pa", _WH_T53, "researched", note="tension perpendicular to grain"),
        "SG":       _e(0.68, "1", _WH_T53, "researched", note="specific gravity at 12% MC"),
    },
    "douglas_fir": {
        "E_L":      _e(13.4e9, "Pa", _WH_T53, "researched", note="Coast, MOE 13,400 MPa"),
        "ET_EL":    _e(0.050, "1", _WH_T51, "researched"),
        "ER_EL":    _e(0.068, "1", _WH_T51, "researched"),
        "GLR_EL":   _e(0.064, "1", _WH_T51, "researched"),
        "MOR":      _e(85e6, "Pa", _WH_T53, "researched", note="Coast, 85,000 kPa"),
        "shear_par": _e(7.8e6, "Pa", _WH_T53, "researched"),
        "tens_perp": _e(2.3e6, "Pa", _WH_T53, "researched"),
        "SG":       _e(0.48, "1", _WH_T53, "researched"),
    },
}

# SOIL -- the Winkler subgrade modulus. Terzaghi 1955 is the source of record; the band is
# reproduced in every foundation text and in the pavement literature in pci.
_TERZAGHI = ("Terzaghi, K. 1955, Geotechnique 5(4):297-326, 'Evaluation of coefficients of "
             "subgrade reaction' -- k_s1 for a 1 ft square plate; band corroborated by the "
             "pavement literature's 50-1000 pci = 13.5-270 MN/m^3")

SOIL = {
    "k_s_loose":  _e(6.3e6, "N/m3", _TERZAGHI, "researched", spread=6.3e6,
                    note="dry/moist LOOSE sand, 0.64-1.92 kgf/cm^3 = 6.3-18.8 MN/m^3; low end"),
    "k_s_medium": _e(56e6, "N/m3", _TERZAGHI, "researched", spread=37e6,
                    note="MEDIUM dense sand, 1.92-9.6 kgf/cm^3 = 18.8-94.2 MN/m^3; mid-band"),
    "k_s_dense":  _e(204e6, "N/m3", _TERZAGHI, "researched", spread=110e6,
                    note="DENSE sand, 9.6-32 kgf/cm^3 = 94.2-314 MN/m^3; mid-band"),
}

# FIBRE ROPE -- the Cordage Institute's testing standard is what every published rope table is
# measured against, so the ELONGATION-AT-A-STATED-FRACTION-OF-BREAKING-STRENGTH is the citable
# quantity, not a modulus. A rope has no meaningful E: it is a helical structure whose apparent
# stiffness rises as the lay tightens, which is exactly why the industry publishes strain at a
# stated load fraction instead.
_CORDAGE = ("Cordage Institute standard test methods for fiber rope / ASTM D-4268; elongation "
            "figures as published by Practical Sailor and by cordage manufacturers' data sheets")

ROPE = {
    "nylon_eps_at_10pct":     _e(0.025, "1", _CORDAGE, "researched",
                                 note="2.5% elongation at 10% of breaking strength"),
    "polyester_eps_at_10pct": _e(0.060, "1", _CORDAGE, "researched",
                                 note="6% elongation at 10% of breaking strength"),
    "nylon_eps_break":        _e(0.215, "1", _CORDAGE, "researched", spread=0.035,
                                 note="18-25% elongation at break; mid-band"),
    "polyester_eps_break":    _e(0.125, "1", _CORDAGE, "researched", spread=0.025,
                                 note="10-15% elongation at break; mid-band"),
    "safety_factor":          _e(5.0, "1", _CORDAGE, "researched",
                                 note="WLL = breaking strength / 5, the standard factor"),
}

# VEHICLE SUSPENSION -- the quarter-car model's published parameters. TWO ROUTES ARE PUBLISHED AND
# THEY DISAGREE, which is stated here rather than resolved silently: the widely-used default pair
# (k = 20,000 N/m, m = 250 kg) gives a ride frequency of 1.42 Hz, which is OUTSIDE the published
# comfort band of 1.0-1.2 Hz and inside the published SPORT band of 1.2-1.5 Hz. The port derives k
# and c from the DYNAMIC targets (frequency and damping ratio) and uses the default pair as an
# independent check -- see `port_tests_matter.py::t_suspension`.
_QCAR = ("quarter-car model parameters as published in the vehicle-dynamics literature: sprung "
         "mass 250 kg/corner, spring 20,000 N/m, damper 545.5 N*s/m")
_RIDE = ("published ride-frequency bands: comfort cars 1.0-1.2 Hz, sport 1.2-1.5 Hz, race "
         "1.5-2.5 Hz; passenger-car suspension damping ratio 0.2-0.4 for comfort, up to 0.5 "
         "when response is the target")

SUSPENSION = {
    "m_sprung":   _e(250.0, "kg", _QCAR, "researched", note="quarter-car sprung mass"),
    "k_default":  _e(20000.0, "N/m", _QCAR, "researched", note="the widely-used default spring"),
    "c_default":  _e(545.5, "N*s/m", _QCAR, "researched", note="the widely-used default damper"),
    "f_comfort":  _e(1.10, "Hz", _RIDE, "researched", spread=0.10,
                    note="comfort ride frequency band 1.0-1.2 Hz; mid-band"),
    "zeta":       _e(0.30, "1", _RIDE, "researched", spread=0.10,
                    note="comfort damping ratio band 0.2-0.4; mid-band"),
    "k_tyre":     _e(225e3, "N/m", _RIDE, "researched", spread=75e3, note="150-300 kN/m"),
}


# REINFORCED CONCRETE -- ACI 318, and it is the ONE material here whose "constants" are a code's
# design equations rather than a laboratory measurement. That is stated because it changes what a
# falsifier can mean: a lab number can be wrong about the world, a code equation can only be wrong
# about the code. What makes this testable anyway is that ACI's equations are OVER-DETERMINED --
# the balanced-ratio formula contains a bare 600 MPa that turns out to be E_s * eps_cu, so the
# code's own constants predict each other and the closure is checkable.
_ACI = ("ACI 318 (metric): E_c = 4700*sqrt(f'c) MPa for normal-weight concrete; beta1 = 0.85 for "
        "f'c <= 28 MPa, 0.85 - 0.05(f'c-28)/7 above; eps_cu = 0.003; Grade 420 = ASTM A615 "
        "Grade 60, f_y 420 MPa, E_s 200 GPa")

CONCRETE = {
    "fc":      _e(30e6, "Pa", _ACI, "researched", spread=10e6,
                  note="specified compressive strength; 20-40 MPa is ordinary structural concrete"),
    "eps_cu":  _e(0.003, "1", _ACI, "researched",
                  note="ACI's crushing strain -- the assumed extreme-fibre limit"),
    "fy":      _e(420e6, "Pa", _ACI, "researched",
                  note="Grade 420 / Grade 60, the standard US rebar"),
    "E_s":     _e(200e9, "Pa", _ACI, "researched", note="steel, and it is the same 200 GPa "
                                                        "everywhere -- rebar is not special"),
}


def concrete_Ec() -> tuple[float, str]:
    """E_c = 4700*sqrt(f'c), ACI's own empirical fit. Returns (Pa, the arithmetic)."""
    fc = val("concrete", "fc")
    ec = 4700.0 * math.sqrt(fc / 1e6) * 1e6
    return ec, f"E_c = 4700*sqrt({fc/1e6:.0f} MPa) = {ec/1e9:.2f} GPa"


def concrete_beta1() -> tuple[float, str]:
    fc = val("concrete", "fc") / 1e6
    b = 0.85 if fc <= 28.0 else max(0.65, 0.85 - 0.05 * (fc - 28.0) / 7.0)
    return b, f"beta1 = 0.85 - 0.05({fc:.0f}-28)/7 = {b:.4f}"


def balanced_ratio() -> tuple[float, str]:
    """ACI's balanced reinforcement ratio -- and the check is that its 600 MPa is DERIVED.

        rho_b = 0.85 * beta1 * (f'c/f_y) * 600/(600+f_y)

    The 600 sits in the code as a bare number. It is E_s * eps_cu = 200 GPa * 0.003 = 600 MPa, and
    the whole fraction is the strain-compatibility geometry: eps_cu/(eps_cu + eps_y) is where the
    neutral axis sits when the concrete crushes at the same instant the steel yields. So the
    formula is not an empirical curve with a magic constant in it; it is a similar-triangles
    argument, and that it CLOSES is the thing to test.
    """
    fc, fy = val("concrete", "fc"), val("concrete", "fy")
    b1, _ = concrete_beta1()
    six = val("concrete", "E_s") * val("concrete", "eps_cu")     # 600 MPa, derived not typed
    rho = 0.85 * b1 * (fc / fy) * six / (six + fy)
    return rho, (f"rho_b = 0.85*{b1:.4f}*({fc/1e6:.0f}/{fy/1e6:.0f})*"
                 f"{six/1e6:.0f}/({six/1e6:.0f}+{fy/1e6:.0f}) = {100*rho:.3f}%")


# ── ACCESS ────────────────────────────────────────────────────────────────────────────────────
_TABLES = {"grass": GRASS, "grass_blade": GRASS_BLADE, "rock": ROCK, "concrete": CONCRETE,
           "soil": SOIL, "rope": ROPE, "suspension": SUSPENSION}


def cite(table: str, key: str, species: str | None = None) -> dict:
    """One constant, with its source. RAISES rather than returning a default.

    The raise is the feature. Eight call sites each forgot to override gravity and every run for
    months simulated Earth, because a default was available to be forgotten. There is no default
    here to forget.
    """
    if table == "wood":
        if species is None:
            raise Uncited("wood is orthotropic AND species-specific; name the species. "
                          f"available: {sorted(WOOD)}")
        t = WOOD.get(species)
        if t is None:
            raise Uncited(f"no published wood {species!r}; have {sorted(WOOD)}")
    elif table in ("sand", "basin", "rock_lib", "metal", "ice", "bone"):
        return _from_library({"rock_lib": "rock"}.get(table, table), key)
    else:
        t = _TABLES.get(table)
        if t is None:
            raise Uncited(f"no table {table!r}; have {sorted(_TABLES)} + wood + the library")
    ent = t.get(key)
    if ent is None:
        raise Uncited(f"{table}{'.' + species if species else ''} publishes no {key!r} -- it "
                      f"publishes {sorted(t)}. Refusing to substitute a value; find the "
                      f"measurement or state that the port cannot be validated.")
    return ent


def val(table: str, key: str, species: str | None = None) -> float:
    return float(cite(table, key, species)["value"])


def spread(table: str, key: str, species: str | None = None) -> float:
    """The published uncertainty, or a REFUSAL. This is where a tolerance comes from.

    A test that wants "within 5%" and cannot say where 5% came from is testing its own comfort.
    A test that wants "within the published spread" is testing the model against the grain of the
    measurement the model was derived from -- which is the only tolerance that means anything.
    """
    s = cite(table, key, species).get("spread")
    if s is None:
        raise Uncited(f"{table}.{key} publishes no spread. A single value with no stated "
                      f"uncertainty cannot set a tolerance; either find the band or say in the "
                      f"falsifier that the tolerance is chosen and therefore weak.")
    return float(s)


# ── DERIVATIONS THAT BELONG TO THE DATA, NOT TO ANY ONE PORT ──────────────────────────────────

def grass_second_moment() -> tuple[float, str]:
    """I for a flat lamina bending about its WEAK axis -- the only way a blade ever bends.

    I = w*t^3/12. The cube on thickness is why a 0.25 mm blade is 4096x more compliant than a
    4 mm one of the same width, and it is why the whole port is sensitive to the one dimension
    hardest to measure. Stated here so the sensitivity is visible rather than buried.
    """
    w, t = val("grass_blade", "width"), val("grass_blade", "thickness")
    return w * t ** 3 / 12.0, f"I = w*t^3/12 = {w:.4g}*{t:.4g}^3/12"


def griffith_flaw() -> tuple[float, str]:
    """The critical flaw size basalt's OWN two published strengths imply. Nothing is chosen.

    sigma_t = K_IC / (Y*sqrt(pi*a))  =>  a = (K_IC/(Y*sigma_t))^2 / pi

    Y = 1.0, the through-crack-in-an-infinite-plate geometry factor: the only value that is not a
    choice about a specimen shape nobody has specified. Reported so the next reader can put their
    own Y in and see the answer move.

    THIS IS THE OVER-DETERMINATION CHECK. K_IC and sigma_t were measured by different people, in
    different decades, by different methods, on different basalts. The flaw size that reconciles
    them is a PREDICTION about basalt's microstructure, and it can land somewhere absurd.
    """
    import math
    K, s = val("rock", "K_IC"), val("rock", "sigma_t")
    a = (K / s) ** 2 / math.pi
    return a, f"a = (K_IC/sigma_t)^2/pi = ({K:.4g}/{s:.4g})^2/pi = {a*1000:.3f} mm"


def _rows():
    for name, tab in _TABLES.items():
        for k, e in tab.items():
            yield name, k, e
    for sp, tab in WOOD.items():
        for k, e in tab.items():
            yield f"wood.{sp}", k, e


def main(argv) -> int:
    audit = "--audit" in argv
    print("=" * 100)
    print("  PUBLISHED CONSTANTS FOR THE NON-HUMAN PASSIVE PORTS")
    print("  Every one INGESTED with a citation or read through from the world's own library.")
    print("=" * 100)
    srcs, n_spread = {}, 0
    for tab, k, e in _rows():
        s = e["spread"]
        n_spread += s is not None
        band = f" +- {s:.4g}" if s is not None else "   (no published spread)"
        print(f"  {tab:>18}.{k:<22} {e['value']:>14.6g} {e['unit']:<10}{band}")
        srcs.setdefault(e["source"], []).append(f"{tab}.{k}")
    n = sum(1 for _ in _rows())
    print("-" * 100)
    print(f"  {n} constants, {n_spread} with a published spread ({100*n_spread/n:.0f}%).")
    print(f"  A constant with no spread cannot set a tolerance -- the port must say so out loud.")
    if audit:
        print("\n  SOURCES")
        for s, keys in sorted(srcs.items(), key=lambda kv: -len(kv[1])):
            print(f"    [{len(keys)}] {s[:150]}")
            print(f"        {', '.join(keys)}")
        print("\n  READ THROUGH FROM THE WORLD'S LIBRARY (never copied here):")
        for mat, key in (("sand", "friction_angle_deg"), ("sand", "cohesion_kpa"),
                         ("sand", "density_kg_m3"), ("rock", "youngs_modulus_gpa"),
                         ("rock", "density_kg_m3")):
            try:
                e = _from_library(mat, key)
                print(f"    {mat}.{key} = {e['value']} (+- {e['spread']})")
            except Uncited as ex:
                print(f"    {mat}.{key} REFUSED: {ex}")
        a, how = griffith_flaw()
        print(f"\n  DERIVED HERE: {how}")
        i, how = grass_second_moment()
        print(f"  DERIVED HERE: {how} = {i:.4g} m^4")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
