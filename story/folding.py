"""folding.py -- what a law can bind to, and what it must never bind to.

THE OPERATOR'S IDEA (2026-07-31): give the SOLUTIONS serial numbers the way the materials have them,
and let the serial say what a thing can connect to -- protein folding as the metaphor.

The metaphor is load-bearing, not decorative, and here is why. In a protein, the SEQUENCE determines
the FOLD, the fold presents a BINDING SITE, and two molecules bind when their surfaces are
complementary. Proteins with the same fold -- a domain family -- are interchangeable in the socket.
And a protein can MISFOLD: the right sequence, the wrong shape, so it binds the wrong thing or
nothing at all, silently, and the cell is poisoned by something that looked correct.

EVERY SERIOUS BUG FOUND IN THIS PROJECT TODAY WAS A MISFOLD:

    theBiomes   passed 294.19 KELVIN into a table whose axis is CELSIUS.  The whole planet --
                poles included -- rendered as "hot desert". Same dimension. Wrong offset.
    theHuman    bound the foot at the TOE TIP where the law wants the BALL. 3.6 cm of stature,
                and it looked like a gait bug for weeks.
    theAtmosphere  drew its scale height as 0.05 of a radius where its own derivation says
                0.00215. Both dimensionless, both "correct" to any type check. 23x wrong.

Three failures, three different kinds of wrongness -- and that is what sets the design:

    THE FOLD is the DIMENSIONAL signature.  It says what may SUBSTITUTE for what. Two laws that
        consume a temperature and produce a pressure share a fold; either can sit in that socket.
        This is the domain family.
    THE BOND is the EXACT unit, offset included.  It says what may CONNECT. Kelvin and Celsius
        share a fold and MUST NOT bond -- that is theBiomes' bug, caught by construction.
    THE REGIME is the range the law is true over.  It catches what neither of the above can:
        a number of the right unit and the right dimension that is simply out of the world --
        theAtmosphere's 23x. In protein terms it is the pH and temperature a bond needs to hold.

WHAT THIS DELIBERATELY DOES NOT DO. It does not infer a law's signature from its equation text, and
it does not score binding by similarity. Proteins fold spontaneously from sequence; a law's
signature is DECLARED, because parsing intent out of prose is a guessing machine and this whole
catalog exists so that nothing in it is a guess. And a fuzzy match would reintroduce the exact
failure mode that made this project's own witnesses report three phantom defects in one afternoon:
a silent default standing in for a missing declaration.

    python -m folding report          what binds to what, and what is still unbound
    python -m folding membrane theHuman
"""
from __future__ import annotations

import hashlib
import math
import json
import re
from pathlib import Path

_HERE = Path(__file__).resolve().parent
CATALOG = _HERE / "data" / "physics_catalog.json"

# ── DIMENSIONS. The seven SI base dimensions, in a fixed order so a signature hashes stably.
DIMS = ("M", "L", "T", "Th", "I", "N", "J")
_Z = (0, 0, 0, 0, 0, 0, 0)


def _d(**kw):
    return tuple(kw.get(k, 0) for k in DIMS)


# ── UNITS. Each is (dimension exponents, scale to SI, offset to SI).
#
# THE OFFSET COLUMN IS THE WHOLE POINT. K and degC have identical dimensions and identical scale;
# they differ ONLY by an offset of 273.15, and that difference is what turned a temperate world into
# a hot desert. A units table without offsets cannot represent the bug, so it cannot catch it.
UNITS = {
    # dimensionless
    "1":      (_Z, 1.0, 0.0),          "frac":  (_Z, 1.0, 0.0),
    "ratio":  (_Z, 1.0, 0.0),          "count": (_Z, 1.0, 0.0),
    # length, mass, time
    "m":      (_d(L=1), 1.0, 0.0),     "km":  (_d(L=1), 1e3, 0.0),
    "mm":     (_d(L=1), 1e-3, 0.0),    "au":  (_d(L=1), 1.495978707e11, 0.0),
    "kg":     (_d(M=1), 1.0, 0.0),     "g":   (_d(M=1), 1e-3, 0.0),
    "s":      (_d(T=1), 1.0, 0.0),     "yr":  (_d(T=1), 3.15576e7, 0.0),
    # temperature -- SAME FOLD, DIFFERENT BOND
    "K":      (_d(Th=1), 1.0, 0.0),
    "degC":   (_d(Th=1), 1.0, 273.15),
    # A TEMPERATURE DIFFERENCE IS NOT A TEMPERATURE, and this is a third misfold class the audit
    # would otherwise miss. `dT_equator_pole = 45` is 45 K OF DIFFERENCE -- which is also 45 degC
    # of difference, because a span has no zero point to disagree about. Bond a delta into an
    # absolute socket and you get a 45 K planet; bond an absolute into a delta socket and you get
    # a 279 K gradient. Same dimension, and neither offset is right, so it gets its own unit.
    "dK":     (_d(Th=1), 1.0, float("nan")),
    # angle (dimensionless but not interchangeable in practice, so tracked by name)
    "rad":    (_Z, 1.0, 0.0),          "deg": (_Z, 0.017453292519943295, 0.0),
    # derived
    "m/s":    (_d(L=1, T=-1), 1.0, 0.0),
    "m/s2":   (_d(L=1, T=-2), 1.0, 0.0),
    "N":      (_d(M=1, L=1, T=-2), 1.0, 0.0),
    "N.m":    (_d(M=1, L=2, T=-2), 1.0, 0.0),
    "J":      (_d(M=1, L=2, T=-2), 1.0, 0.0),
    "W":      (_d(M=1, L=2, T=-3), 1.0, 0.0),
    "TW":     (_d(M=1, L=2, T=-3), 1e12, 0.0),
    "W/m2":   (_d(M=1, T=-3), 1.0, 0.0),
    "Pa":     (_d(M=1, L=-1, T=-2), 1.0, 0.0),
    "kPa":    (_d(M=1, L=-1, T=-2), 1e3, 0.0),
    "bar":    (_d(M=1, L=-1, T=-2), 1e5, 0.0),
    "kg/m3":  (_d(M=1, L=-3), 1.0, 0.0),
    "kg.m2":  (_d(M=1, L=2), 1.0, 0.0),
    "N.m/kg": (_d(L=2, T=-2), 1.0, 0.0),
    "1/s":    (_d(T=-1), 1.0, 0.0),
    "rad/s":  (_d(T=-1), 1.0, 0.0),
    "K/km":   (_d(Th=1, L=-1), 1e-3, 0.0),
    "m2":     (_d(L=2), 1.0, 0.0),
    "h":      (_d(T=1), 3600.0, 0.0),
    "GPa":    (_d(M=1, L=-1, T=-2), 1e9, 0.0),
    "litre":  (_d(L=3), 1e-3, 0.0),
    "Msun":   (_d(M=1), 1.98892e30, 0.0),
    "Rsun":   (_d(L=1), 6.957e8, 0.0),
    "Lsun":   (_d(M=1, L=2, T=-3), 3.828e26, 0.0),
    "min":    (_d(T=1), 60.0, 0.0),
    "day":    (_d(T=1), 86400.0, 0.0),
    "Myr":    (_d(T=1), 3.15576e13, 0.0),
    "kyr":    (_d(T=1), 3.15576e10, 0.0),
    "kpc":    (_d(L=1), 3.0856775814913673e19, 0.0),
    "1/min":  (_d(T=-1), 1.0 / 60.0, 0.0),
    "litre/min": (_d(L=3, T=-1), 1e-3 / 60.0, 0.0),
    # PER TONNE, and the name said per kilogram. The SCALE was right for the keys it serves
    # (`_kwh_t`, Bond work index) and the LABEL was wrong by 1000x -- so anything reading the name
    # to decide what to multiply by would have been out by three orders. Caught by an agent doing
    # arithmetic on the table rather than trusting it, which is the whole method applied to the
    # checker itself.
    "kWh/t":  (_d(L=2, T=-2), 3.6e6 / 1000.0, 0.0),
    "mm/kyr": (_d(L=1, T=-1), 1e-3 / 3.15576e10, 0.0),
    "pct":    (_Z, 0.01, 0.0),
    "MPa":    (_d(M=1, L=-1, T=-2), 1e6, 0.0),
    "uT":     (_d(M=1, T=-2, I=-1), 1e-6, 0.0),
    "T_mag":  (_d(M=1, T=-2, I=-1), 1.0, 0.0),
    "A.m2":   (_d(I=1, L=2), 1.0, 0.0),
    "J/kgK":  (_d(L=2, T=-2, Th=-1), 1.0, 0.0),
    "Zsun":   (_Z, 1.0, 0.0),
    # published in this tree and unreadable until now -- the gap a signature agent surfaced by
    # trying to declare continuum mechanics and finding viscosity alone blocked three rows.
    "Pa.s":   (_d(M=1, L=-1, T=-1), 1.0, 0.0),
    "m2/s":   (_d(L=2, T=-1), 1.0, 0.0),
    "N/m":    (_d(M=1, T=-2), 1.0, 0.0),
    "J/m2":   (_d(M=1, T=-2), 1.0, 0.0),
    "m3/kg":  (_d(M=-1, L=3), 1.0, 0.0),
    "J/K":    (_d(M=1, L=2, T=-2, Th=-1), 1.0, 0.0),
    "W/mK":   (_d(M=1, L=1, T=-3, Th=-1), 1.0, 0.0),
    "W/m2K":  (_d(M=1, T=-3, Th=-1), 1.0, 0.0),
    "W/kg":   (_d(L=2, T=-3), 1.0, 0.0),
    "kg.m/s": (_d(M=1, L=1, T=-1), 1.0, 0.0),
    # the units behind the misread keys -- real speeds and areal densities the tree publishes
    "km/s":   (_d(L=1, T=-1), 1e3, 0.0),
    "cm/yr":  (_d(L=1, T=-1), 0.01 / 3.15576e7, 0.0),
    "g/kg":   (_Z, 1e-3, 0.0),
    "kg/m2":  (_d(M=1, L=-2), 1.0, 0.0),
    "mW/m2":  (_d(M=1, T=-3), 1e-3, 0.0),
    "1/km":   (_d(L=-1), 1e-3, 0.0),
    "K/km_":  (_d(Th=1, L=-1), 1e-3, 0.0),
    "nm":     (_d(L=1), 1e-9, 0.0),          # WAVELENGTH. See the _nm note below -- it was a torque.
    "1/m":    (_d(L=-1), 1.0, 0.0),          # absorption coefficient; blocked 3 human rows
    "W/m3":   (_d(M=1, L=-1, T=-3), 1.0, 0.0),
    "rad/s2": (_d(T=-2), 1.0, 0.0),
    "cd/m2":  (_d(J=1, L=-2), 1.0, 0.0),     # luminance -- blocked four of the six eye rows
    "cd":     (_d(J=1), 1.0, 0.0),
    "lm":     (_d(J=1), 1.0, 0.0),
    "lx":     (_d(J=1, L=-2), 1.0, 0.0),
    "lm/W":   (_d(J=1, M=-1, L=-2, T=3), 1.0, 0.0),
    "deg/s":  (_Z, 0.017453292519943295, 0.0),
    # ── ELECTRICAL. Seven rows of electromagnetism and five of quantum were unbindable for want
    # of a volt. The tree has no electrical membrane today, so most will dock nowhere -- but a row
    # that cannot be STATED is different from a row with nothing to attach to, and only the second
    # is honest bookkeeping.
    "V":      (_d(M=1, L=2, T=-3, I=-1), 1.0, 0.0),
    "A":      (_d(I=1), 1.0, 0.0),
    "C":      (_d(I=1, T=1), 1.0, 0.0),
    "ohm":    (_d(M=1, L=2, T=-3, I=-2), 1.0, 0.0),
    "Wb":     (_d(M=1, L=2, T=-2, I=-1), 1.0, 0.0),
    "F":      (_d(M=-1, L=-2, T=4, I=2), 1.0, 0.0),
    "S":      (_d(M=-1, L=-2, T=3, I=2), 1.0, 0.0),
    "V/m":    (_d(M=1, L=1, T=-3, I=-1), 1.0, 0.0),
    "mV":     (_d(M=1, L=2, T=-3, I=-1), 1e-3, 0.0),
    # ── AMOUNT. The N dimension was reserved in DIMS and no unit ever used it, so the whole of
    # chemistry could not be written down.
    "mol":    (_d(N=1), 1.0, 0.0),
    "J/mol":  (_d(M=1, L=2, T=-2, N=-1), 1.0, 0.0),
    "J/molK": (_d(M=1, L=2, T=-2, N=-1, Th=-1), 1.0, 0.0),
    "kg/mol": (_d(M=1, N=-1), 1.0, 0.0),
    "mol/m3": (_d(N=1, L=-3), 1.0, 0.0),
    "mol/s":  (_d(N=1, T=-1), 1.0, 0.0),
    # ── PARTICLE ENERGIES, and the two radiation units. Sv and Gy share L2T-2 with N.m/kg exactly,
    # which is why an agent refused to borrow one for the other -- they are named separately here
    # so a dose can be STATED without pretending it is a specific torque.
    "eV":     (_d(M=1, L=2, T=-2), 1.602176634e-19, 0.0),
    "MeV":    (_d(M=1, L=2, T=-2), 1.602176634e-13, 0.0),
    "Gy":     (_d(L=2, T=-2), 1.0, 0.0),
    "Sv":     (_d(L=2, T=-2), 1.0, 0.0),
    "Bq":     (_d(T=-1), 1.0, 0.0),
    "Pa/m":   (_d(M=1, L=-2, T=-2), 1.0, 0.0),      # a pressure gradient -- Darcy needs one
    "Pa.m0.5":(_d(M=1, L=-0.5, T=-2), 1.0, 0.0),    # fracture toughness K_IC, a half-integer again
    "Pa/K":   (_d(M=1, L=-1, T=-2, Th=-1), 1.0, 0.0),  # Clausius-Clapeyron slope
    "J/kg":   (_d(L=2, T=-2), 1.0, 0.0),               # specific latent heat
    # HALF-INTEGER DIMENSIONS ARE REAL. A planet publishes the Froude COEFFICIENT -- a speed per
    # root-length -- so a body with a leg can finish the multiplication. Its dimension is
    # L^0.5 T^-1, and refusing to represent that would mean the two most-published unread keys in
    # the tree stay unread for a formatting reason. Exponents are numbers, not integers.
    "m0.5/s": (_d(L=0.5, T=-1), 1.0, 0.0),
    "s/m0.5": (_d(L=-0.5, T=1), 1.0, 0.0),
    "m3":     (_d(L=3), 1.0, 0.0),
}

# ── READING UNITS OFF THE MEMBRANES, because they already declare them.
#
# 91% of the 1,156 numbers in this story carry a unit suffix in the KEY NAME -- `extent_m`,
# `duration_s`, `mass_kg`, `foot_pressure_kPa`, `heat_flux_W_m2`. That is a convention this project
# already follows on purpose, so reading it is READING, not inference. Keys that do not follow it
# come back as undeclared and are REPORTED, which is how the convention gets finished.
SUFFIX_UNITS = [
    ("_W_m2", "W/m2"), ("_kg_m3", "kg/m3"), ("_kgm2", "kg.m2"), ("_Nm_per_kg", "N.m/kg"),
    ("_Nm", "N.m"), ("_K_km", "K/km"), ("_kPa", "kPa"), ("_Pa", "Pa"), ("_bar", "bar"),
    ("_TW", "TW"), ("_W", "W"), ("_J", "J"), ("_N", "N"),
    ("_m_s2", "m/s2"), ("_ms", "m/s"), ("_m_s", "m/s"), ("_rad_s", "rad/s"),
    ("_km", "km"), ("_mm", "mm"), ("_au", "au"), ("_m2", "m2"), ("_m3", "m3"),
    ("_kg", "kg"), ("_s", "s"), ("_yr", "yr"), ("_deg", "deg"), ("_rad", "rad"),
    ("_C", "degC"), ("_K", "K"), ("_m", "m"),
    ("_frac", "frac"), ("_fraction", "frac"), ("_ratio", "ratio"),
    # a second pass over what the first left unread -- each covers real keys in this tree
    ("_energy_kwh_t", "kWh/t"), ("_kwh_t", "kWh/t"),
    ("_per_sqrt_leg", None),          # resolved by name in units.json: speed vs period coefficient
    ("_l_min", "litre/min"), ("_steps_min", "1/min"), ("_per_min", "1/min"),
    ("_mm_kyr", "mm/kyr"), ("_kpc", "kpc"), ("_myr", "Myr"), ("_kyr", "kyr"),
    ("_day_h", "h"), ("_h", "h"), ("_days", "day"), ("_min", "min"),
    ("_pct", "pct"), ("_percentile", "pct"),
    # dimensionless by construction -- a factor, a margin, an exponent, a count, an albedo
    ("_factor", "1"), ("_margin", "ratio"), ("_exponent", "1"), ("_count", "count"),
    ("_albedo", "frac"), ("_efficiency", "frac"), ("_slope", "1"), ("_index", "1"),
    ("_MPa", "MPa"), ("_uT", "uT"), ("_Am2", "A.m2"), ("_J_kgK", "J/kgK"), ("_zsun", "Zsun"),
    # NOTE the ORDER: these must precede the bare "_m2" rule, which would otherwise read
    # `U_visor_W_m2K` as an AREA. First match wins, so the longer suffix has to come first.
    ("_W_m2K", "W/m2K"), ("_W_mK", "W/mK"), ("_Pas", "Pa.s"), ("_W_kg", "W/kg"),
    ("_km_s", "km/s"), ("_cm_yr", "cm/yr"), ("_g_kg", "g/kg"), ("_kg_m2", "kg/m2"),
    ("_cd_m2", "cd/m2"), ("_lm_per_W", "lm/W"), ("_deg_s", "deg/s"), ("_W_m3", "W/m3"),
    ("_J_mol", "J/mol"), ("_J_molK", "J/molK"), ("_kg_mol", "kg/mol"), ("_mol_m3", "mol/m3"),
    ("_mV", "mV"), ("_eV", "eV"), ("_MeV", "MeV"), ("_Sv", "Sv"), ("_Gy", "Gy"), ("_Bq", "Bq"),
    ("_V_m", "V/m"), ("_ohm", "ohm"), ("_Wb", "Wb"),
    ("_rad_s2", "rad/s2"), ("_per_m", "1/m"), ("_lx", "lx"), ("_l", "litre"),
    # _nm IS A WAVELENGTH, and it was reading as NEWTON-METRES. `_nm` was absent from this table,
    # so the exact pass missed it and the case-INSENSITIVE fallback matched `_Nm`. Every wavelength
    # in theSkin and theEye -- spectrum_nm, skin_bands_nm -- was on the binding surface typed as a
    # TORQUE. Same dimension as nothing it could meet, so it never misfolded loudly; it was simply
    # wrong and silent. Declared exactly, and the fallback is now guarded (below).
    ("_nm", "nm"),
    ("_mW_m2", "mW/m2"), ("_per_km", "1/km"), ("_K_per_km", "K/km"),
    ("_m2_s", "m2/s"), ("_N_m", "N/m"), ("_J_K", "J/K"),
]

# CASE. `dynamic_pressure_pa` and `P_surface_Pa` are the same unit spelled two ways, and a
# case-sensitive table reads one and not the other. That is a naming inconsistency in the tree
# rather than a physics problem, so it is absorbed here and REPORTED rather than left to hide.
# LONGEST SUFFIX WINS, ALWAYS -- and this is a rule, not an ordering of the list above.
#
# Matching was first-in-list-wins, so any compound unit ending in a shorter unit's name was read as
# the shorter one: `seismic_p_speed_km_s` came back as SECONDS, `plate_speed_cm_yr` as YEARS,
# `column_mass_kg_m2` as an AREA, `U_visor_W_m2K` as an area again. That is worse than an
# undeclared key, because a bond can SUCCEED against a wrong unit -- six real speeds in this tree
# were on the binding surface wearing the wrong dimension.
#
# Hand-ordering the list fixed whichever ones somebody happened to notice. Sorting by length fixes
# the class, and keeps fixing it for suffixes added later by people who never read this comment.
SUFFIX_UNITS = sorted(SUFFIX_UNITS, key=lambda su: -len(su[0]))
_SUFFIX_CI = [(suf.lower(), suf, u) for suf, u in SUFFIX_UNITS]


DECLARED = _HERE / "data" / "units.json"
_DECL = None


def declared_units() -> dict:
    """The units stated in story/data/units.json for keys whose names do not carry one.

    DECLARED, NOT RENAMED, and not guessed. `g`, `R`, `M`, `T` are universal physics symbols that
    read worse with a suffix, and renaming a published key breaks every child that reads it by
    name. Anything absent from that file stays unread ON PURPOSE -- a guessed unit is worse than a
    missing one, because it makes a bad bond look legal."""
    global _DECL
    if _DECL is None:
        _DECL = json.loads(DECLARED.read_text(encoding="utf8")) if DECLARED.exists() else {}
    return _DECL


def unit_of_key(key: str, membrane: str = None):
    """The unit of a published number. Precedence:
         1. an explicit OVERRIDE in units.json  -- for keys whose own name is WRONG
         2. the key's own suffix
         3. a per-membrane declaration, then a global one
         4. None -- undeclared, and reported

    THE SUFFIX USUALLY WINS, because a name carrying its unit cannot drift out of step with a table
    somewhere else. But a suffix is a PATTERN MATCH on a name, and a name can simply be wrong:

        aHuman.dT_defended_K = 26.96   is a SPAN (33.0 degC - 6.04 degC), not a temperature.
                                       Read as absolute Kelvin it is 246 degrees below absolute zero.
        theHuman.cadence_steps_s = 1.687  is a RATE -- exactly 1/step_time_s -- so its dimension is
                                       T^-1 and its name says T^1.

    Both are consumed by other membranes under those names, so renaming them mid-flight would break
    live code. An explicit override states the truth NOW; the rename is owed and is recorded in
    units.json under `renames_owed` so it does not quietly become permanent."""
    d0 = declared_units().get("overrides", {})
    if membrane and key in d0.get(membrane, {}):
        return d0[membrane][key]
    if key in d0.get("_any", {}):
        return d0["_any"][key]
    for suf, u in SUFFIX_UNITS:
        if key.endswith(suf):
            if u is not None:
                return u
            break          # the suffix is real but ambiguous -- let the declaration decide
    else:
        kl = key.lower()
        for sl, suf, u in _SUFFIX_CI:
            # single-letter units are case-BEARING: N and n, K and k, T and t are different things,
            # and folding them together typed a sample count as a force.
            if u is not None and len(suf.lstrip("_")) > 1 and kl.endswith(sl):
                return u
    d = declared_units()
    if membrane:
        bym = d.get("by_membrane", {}).get(membrane, {})
        if key in bym:
            return bym[key]
    return d.get("global", {}).get(key)


def dim_of(unit: str):
    u = UNITS.get(unit)
    return None if u is None else u[0]


def fold_of(consumes, produces) -> str:
    """THE FOLD -- a short stable id for the DIMENSIONAL shape of a law.

    Two laws with the same fold are interchangeable in the same socket: swap one bearing-capacity
    law for another and everything downstream still docks. That is a protein domain family, and it
    is the whole reason the fold is dimensional rather than exact -- exactness would make every law
    unique and nothing would ever be substitutable.

    Derived, never assigned. A serial you can choose is a serial that can lie."""
    def side(d):
        out = []
        for u in sorted(d.values()):
            dim = dim_of(u)
            out.append("?" if dim is None else ",".join(str(x) for x in dim))
        return ";".join(sorted(out))
    key = side(consumes) + "->" + side(produces)
    return "f" + hashlib.sha1(key.encode()).hexdigest()[:8]


def fold_of_shapes(shapes_in, shapes_out) -> str:
    """The same idea for a method: a stable id for its DATA SHAPE, prefixed `s` so a shape fold can
    never be mistaken for a dimensional one."""
    key = ";".join(sorted(shapes_in)) + "->" + ";".join(sorted(shapes_out))
    return "s" + hashlib.sha1(key.encode()).hexdigest()[:8]


def dim_code(unit: str) -> str:
    """A dimension written so a person can read it: M1L2T-2, or `1` for dimensionless.

    THE SERIAL HAS TO SAY SOMETHING. `f7588543f` is a perfectly good index and a useless label --
    you cannot look at it and know what it plugs into, which was the whole point of the operator's
    idea. A material's serial identifies a material; a law's serial should identify a SOCKET.
    So the readable form is the dimensional signature spelled out, and the hash is kept beside it
    as the short alias for exact comparison."""
    d = dim_of(unit)
    if d is None:
        return "?"
    out = "".join(f"{n}{e:g}" for n, e in zip(DIMS, d) if e)
    return out or "1"


# ════════════════════════════════════════════════════════════════════════════════════════════════
#  MATHEMATICS BINDS BY SHAPE, NOT BY DIMENSION
#
#  A Kalman filter does not care whether it is filtering metres or kelvin. A k-d tree does not care
#  what it indexes. Marching cubes does not care what the field means. MATHEMATICS IS DIMENSIONLESS
#  BY CONSTRUCTION -- that is what makes it mathematics rather than physics -- so the dimensional
#  serial cannot describe it, and forcing one would be the same species of error as typing a unit
#  nobody measured.
#
#  What a method DOES have is a shape of data it takes and a shape it returns. That is its binding
#  site, and it gives the same payoff the dimensional fold gives a law: TWO METHODS WITH THE SAME
#  SHAPE SERIAL ARE INTERCHANGEABLE. Semi-implicit Euler and RK4 both take (state, step) and give a
#  state, so either can sit in that socket -- which is a fact worth being able to look up, because
#  it is exactly the question "can I swap this integrator" asks.
SHAPES = (
    "scalar",      # one number
    "vector",      # a fixed-length tuple of numbers -- a position, a velocity
    "matrix",      # a 2-D array, usually an operator
    "state",       # a system's full configuration: q and qdot, or a filter's mean and covariance
    "field",       # values sampled over a grid -- a heightfield, a density, a temperature
    "mesh",        # vertices and faces
    "cloud",       # unordered points, optionally with attributes -- a splat buffer is one
    "graph",       # nodes and edges: a kinematic tree, a contact graph
    "series",      # values over time
    "dist",        # a probability distribution or a population of samples
    "spectrum",    # values over wavelength or frequency
    "image",       # a 2-D raster with channels
    "step",        # a timestep or an iteration count -- the thing that advances a solver
)


def shape_serial(sig) -> str:
    """THE SERIAL FOR A METHOD: what shape of data goes in, what comes out.

        state + step -> state          any integrator. Euler and RK4 share this socket.
        field -> mesh                  marching cubes, dual contouring -- interchangeable.
        cloud -> image                 a rasteriser.

    Same rule as the dimensional serial: derived, never stored, and a shared one means the two
    rows SUBSTITUTE for each other."""
    ins = " + ".join(sorted(sig.shapes_in)) or "-"
    outs = " + ".join(sorted(sig.shapes_out)) or "-"
    return f"{ins} -> {outs}"


def serial(sig) -> str:
    """THE SERIAL: what this law takes, and what it gives back, in dimensions.

        M1 + L1 -> M1L2          an inertia: a mass and a length become a moment of inertia
        Th1 -> M1T-3             a temperature becomes a flux -- Stefan-Boltzmann's socket

    Two laws with the same serial are the same SOCKET and substitute for each other; that is the
    protein domain family, and it is why the serial is dimensional rather than exact. It is derived
    from the signature every time, never stored as an editable field -- a serial you can type is a
    serial that can disagree with the thing it labels."""
    ins = " + ".join(sorted(dim_code(u) for u in sig.consumes.values())) or "-"
    outs = " + ".join(sorted(dim_code(u) for u in sig.produces.values())) or "-"
    return f"{ins} -> {outs}"


# ── BONDING. Three outcomes, and the middle one is the interesting one.
BINDS, CONVERTS, MISFOLD, ABSENT = "binds", "converts", "MISFOLD", "absent"


def bond(need_unit: str, have_unit: str):
    """Can a quantity in `have_unit` be plugged into a socket wanting `need_unit`?

    BINDS      identical -- plug it in.
    CONVERTS   same dimension, both zero-offset, different scale (kPa into Pa). Safe and
               mechanical, but it must be DONE, and saying so is the point.
    MISFOLD    same dimension, DIFFERENT OFFSET (degC into K), or a different dimension entirely.
               This is the one that renders a planet as desert and looks fine doing it.
    """
    if need_unit == have_unit:
        return BINDS, "identical"
    a, b = UNITS.get(need_unit), UNITS.get(have_unit)
    if a is None or b is None:
        return ABSENT, f"unknown unit {need_unit if a is None else have_unit!r}"
    if a[0] != b[0]:
        return MISFOLD, f"different dimension: {need_unit} is not {have_unit}"
    import math as _m
    if _m.isnan(a[2]) != _m.isnan(b[2]):
        return MISFOLD, (f"a temperature DIFFERENCE and a temperature are not the same thing: "
                         f"{have_unit} into {need_unit}")
    if not _m.isnan(a[2]) and a[2] != b[2]:
        return MISFOLD, (f"same dimension, different ZERO POINT: {have_unit} into {need_unit} "
                         f"is off by {abs(a[2] - b[2])} -- this is theBiomes' bug")
    if a[1] != b[1]:
        return CONVERTS, f"x{b[1] / a[1]:g} to go from {have_unit} to {need_unit}"
    return BINDS, "same dimension and zero point"


def in_regime(value, lo=None, hi=None):
    """THE THIRD CHECK, and the only one that catches theAtmosphere.

    A scale height drawn at 0.05 of a planet's radius where the derivation says 0.00215 is
    dimensionally perfect, unit-perfect, and 23x wrong. Nothing about the type of the number is
    unusual; it is simply not a number this world contains. So a signature may state the range its
    law is true over, and a value outside it is refused with the range quoted."""
    v = float(value)
    if lo is not None and v < float(lo):
        return False, f"{v:g} below the law's range ({lo:g})"
    if hi is not None and v > float(hi):
        return False, f"{v:g} above the law's range ({hi:g})"
    return True, "in range"


# ── SIGNATURES. Declared, never inferred.
class Signature:
    """What a law consumes, what it produces, and where it is true.

    `consumes` and `produces` map a SYMBOL to a UNIT -- the symbol is what the law calls it, the
    unit is what makes the bond checkable. `regime` maps a symbol to (lo, hi) in that unit."""

    def __init__(self, consumes: dict, produces: dict, regime: dict = None, note: str = "",
                 keys: dict = None, shapes_in=None, shapes_out=None):
        # SHAPES are for the mathematics rows, which have no dimensions to sign. A row carries one
        # kind or the other; a few carry both, because some rows ARE a physics law expressed as an
        # algorithm (Newton-Euler produces torques AND takes a state).
        self.shapes_in = tuple(shapes_in or ())
        self.shapes_out = tuple(shapes_out or ())
        for sh in self.shapes_in + self.shapes_out:
            if sh not in SHAPES:
                raise ValueError(f"unknown data shape {sh!r}; have {SHAPES}")
        self.consumes = dict(consumes)
        self.produces = dict(produces)
        self.regime = dict(regime or {})
        self.note = note
        # SPECIFICITY. A unit is the SHAPE of a binding site; it is not enough on its own, and the
        # first run of this module proved it -- "segment moments of inertia" happily bound to
        # aNitrogenAtmosphere and aSaltOcean, because every membrane publishes something in metres
        # and something in kilograms. In a protein that is a site that binds everything, which is a
        # site that is not doing its job. `keys` gives each symbol the NAME fragment it expects, so
        # shape AND chemistry both have to match.
        self.keys = dict(keys or {})

    @property
    def fold(self):
        if not self.consumes and not self.produces and (self.shapes_in or self.shapes_out):
            return fold_of_shapes(self.shapes_in, self.shapes_out)
        return fold_of(self.consumes, self.produces)

    @property
    def serial(self):
        """The readable form of the fold -- see serial() above. A mathematics row with no
        dimensional side reports its SHAPE serial instead, because that is the socket it has."""
        if not self.consumes and not self.produces and (self.shapes_in or self.shapes_out):
            return shape_serial(self)
        return serial(self)

    @property
    def is_method(self):
        return bool(self.shapes_in or self.shapes_out) and not self.consumes

    def as_dict(self):
        return {"consumes": self.consumes, "produces": self.produces,
                "regime": {k: list(v) for k, v in self.regime.items()},
                "keys": self.keys, "fold": self.fold, "note": self.note}

    def __repr__(self):
        return (f"<Signature {self.fold} "
                f"{'+'.join(self.consumes)} -> {'+'.join(self.produces)}>")


def surface(numbers: dict, membrane: str = None) -> dict:
    """A MEMBRANE'S BINDING SURFACE: every number it publishes whose key declares a unit.

    This is the complementary face -- what is available to bind against. Keys whose names carry no
    unit are not on the surface, and `undeclared()` lists them, because a quantity nothing can read
    the unit of is a quantity nothing can safely bind."""
    out = {}
    for k, v in numbers.items():
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            u = unit_of_key(k, membrane)
            if u:
                out[k] = u
    return out


def undeclared(numbers: dict, membrane: str = None) -> list:
    return sorted(k for k, v in numbers.items()
                  if isinstance(v, (int, float)) and not isinstance(v, bool)
                  and unit_of_key(k, membrane) is None)


def dock(sig: Signature, numbers: dict) -> dict:
    """CAN THIS LAW BIND TO THIS MEMBRANE? One verdict per consumed symbol.

    A symbol binds if the membrane publishes something of a compatible unit. Where several keys
    fit, the closest-named one wins, and the choice is reported -- an ambiguous bond is a real
    finding (in biology, a site that binds everything is a site that is not doing its job)."""
    surf = surface(numbers)
    verdicts, ok = {}, True
    for sym, need in sig.consumes.items():
        want = sig.keys.get(sym, sym).lower()
        cands = []
        for key, have in surf.items():
            state, why = bond(need, have)
            if state not in (BINDS, CONVERTS):
                continue
            # SPECIFICITY: the key must actually be the thing the symbol names. Unit-compatible but
            # unrelated is not a bond -- it is the promiscuity that made this module's own first
            # run claim leg inertia binds to an ocean.
            if want not in key.lower():
                continue
            cands.append(((0 if state == BINDS else 1, len(key)), key, state, why))
        if not cands:
            # is there something of the right DIMENSION that would misfold? name it -- that is a
            # far more useful failure than "not found".
            near = [(k, bond(need, u)[1]) for k, u in surf.items()
                    if want in k.lower()
                    and dim_of(u) == dim_of(need) and bond(need, u)[0] == MISFOLD]
            verdicts[sym] = {"state": MISFOLD if near else ABSENT,
                             "need": need,
                             "why": near[0][1] if near else f"nothing published in {need}",
                             "candidate": near[0][0] if near else None}
            ok = False
            continue
        cands.sort()
        _s, key, state, why = cands[0]
        v = {"state": state, "need": need, "key": key, "why": why,
             "alternatives": [c[1] for c in cands[1:4]]}
        lo, hi = sig.regime.get(sym, (None, None))
        if lo is not None or hi is not None:
            # THE REGIME IS STATED IN THE SOCKET'S UNIT, so the value has to arrive in that unit.
            # This compared the RAW published number: a socket wanting Pa with a band of 1e4..1e7
            # would convict a perfectly good key published in kPa, and pass a bad one published in
            # bar. Converting first is the difference between a range check and a units accident.
            A, B = UNITS.get(need), UNITS.get(surf[key])
            # `val`, NOT `v` -- `v` is the verdict dict two lines down, and shadowing it made this
            # raise TypeError for EVERY signature carrying a consumed regime. Introduced while
            # fixing the raw-value bug above and caught within the hour by an agent whose own work
            # it blocked. Two defects in four lines, both about a name meaning the wrong thing.
            val = float(numbers[key])
            if A and B and not (math.isnan(A[2]) or math.isnan(B[2])):
                val = ((val * B[1] + B[2]) - A[2]) / A[1]
            good, msg = in_regime(val, lo, hi)
            v["regime"] = msg
            if not good:
                v["state"] = MISFOLD
                ok = False
        verdicts[sym] = v
    return {"fold": sig.fold, "binds": ok, "symbols": verdicts}


# ── THE CATALOG SIDE
def catalog() -> dict:
    if not CATALOG.exists():
        raise FileNotFoundError(f"{CATALOG} missing -- run tools/parse_physics_catalog.py")
    return json.loads(CATALOG.read_text(encoding="utf8"))


SIG_DIR = _HERE / "data" / "signatures"


def rows_with_signatures() -> dict:
    """The declared signatures, keyed by catalog row id. Everything not in here is UNBOUND, and
    that count is the honest measure of how far the physics tree actually reaches the code.

    TWO SOURCES, AND THE SPLIT IS ABOUT WRITERS RATHER THAN PHYSICS. The dict below in this file
    holds the seed set. `story/data/signatures/*.json` holds the rest, ONE FILE PER BRANCH, so that
    several people (or agents) can declare signatures for different branches at once without
    writing to the same file. A single shared dict is a conflict waiting to happen, and a merge
    conflict inside a physics declaration is how a signature ends up attached to the wrong row --
    which is a misfold, committed by the tooling instead of by the physics.

    Each JSON file is  {"E2.11": {"consumes": {...}, "produces": {...}, "regime": {...},
                                  "keys": {...}, "note": "..."} , ...}
    In-code entries win on a clash, and the clash is REPORTED rather than silently resolved."""
    out = dict(SIGNATURES)
    if SIG_DIR.exists():
        for f in sorted(SIG_DIR.glob("*.json")):
            try:
                blob = json.loads(f.read_text(encoding="utf8"))
            except Exception as e:
                print(f"  WARNING: {f.name} will not parse ({e}); skipped")
                continue
            for rid, d in blob.items():
                if rid.startswith("_"):
                    continue          # allow "_note"-style keys in the file
                if rid in out:
                    print(f"  WARNING: {rid} declared both in folding.py and {f.name}; "
                          f"the in-code one wins")
                    continue
                try:
                    out[rid] = Signature(d.get("consumes", {}), d.get("produces", {}),
                                         {k: tuple(v) for k, v in (d.get("regime") or {}).items()},
                                         d.get("note", ""), d.get("keys"),
                                         d.get("shapes_in"), d.get("shapes_out"))
                except Exception as e:
                    print(f"  WARNING: {rid} in {f.name} is malformed ({e}); skipped")
    return out


# ════════════════════════════════════════════════════════════════════════════════════════════════
#  DECLARED SIGNATURES -- seeded from laws this story already implements.
#
#  Every one of these was read off a working membrane, not invented: the consumes are the numbers
#  that membrane actually reaches for, and the produces are what it publishes. That is why this is
#  a bootstrap and not a wish list. Rows without an entry report as unbound.
# ════════════════════════════════════════════════════════════════════════════════════════════════
SIGNATURES = {
    # E1.01 -- Newton's laws | F = dp/dt
    "E1.01": Signature({"m": "kg", "a": "m/s2"}, {"F": "N"},
                       keys={"m": "mass", "a": "g"},
                       note="Newton: force is mass times acceleration"),
    # E1.05 -- Rigid-body rotation | Euler equations; inertia tensor I
    "E1.05": Signature({"m": "kg", "L": "m"}, {"I": "kg.m2"},
                       keys={"m": "mass", "L": "length"},
                       note="inertia tensor of a body from its mass and its size"),
    # E2.11 -- Granular rheology | mu(I) law; Hertz-Mindlin contacts
    "E2.11": Signature({"rho": "kg/m3", "g": "m/s2"}, {"q": "Pa"},
                       keys={"rho": "density", "g": "g"},
                       regime={"q": (1e4, 1e7)},
                       note="what a granular bed carries -- theGround's Terzaghi bearing capacity. "
                            "The regime is what a real soil holds: 10 kPa to 10 MPa"),
    # E3.07 -- Thermal radiation | Stefan-Boltzmann P = eps.sigma.T^4
    "E3.07": Signature({"T": "K"}, {"M": "W/m2"},
                       keys={"T": "T"},
                       regime={"T": (1.0, 1e9)},
                       note="Stefan-Boltzmann. T IS IN KELVIN and the regime says so -- this is the "
                            "socket theBiomes plugged Celsius into and rendered a planet as desert"),
    # E3.02 -- Ideal gas | PV = nRT  (the scale height a hydrostatic atmosphere follows)
    "E3.02": Signature({"T": "K", "g": "m/s2"}, {"H": "m"},
                       keys={"T": "T_surface", "g": "g"},
                       regime={"H": (1e2, 1e5)},
                       note="scale height H = RT/(Mg) from the gas law under hydrostatic balance. "
                            "The regime is 100 m to 100 km -- theAtmosphere derives 11.3 km and its "
                            "RENDER drew 0.05 of a radius, 23x too thick. Only a range sees that"),
    # H1.02 -- Segment moments of inertia | de Leva radius of gyration per segment
    "H1.02": Signature({"h": "m", "m": "kg"}, {"I": "kg.m2"},
                       keys={"h": "height", "m": "mass"},
                       note="segment inertia about the hip, de Leva composite -- theHuman"),
    # H2.06 -- Moment arms | tau = sum r_i(q) . F_i
    "H2.06": Signature({"m": "kg", "g": "m/s2"}, {"tau": "N.m"},
                       keys={"m": "mass", "g": "g"},
                       regime={"tau": (0.0, 1e4)},
                       note="joint moment through a measured lever -- theAnkle's push-off, now read "
                            "from the Van Criekinge curves rather than a lever product"),
    # H3.03 -- Inverted-pendulum walking mechanics
    "H3.03": Signature({"g": "m/s2", "H": "m"}, {"w0": "rad/s"},
                       keys={"g": "g", "H": "com_height"},
                       note="w0 = sqrt(g/H): how fast a standing body falls over. Sets the capture "
                            "point, and it is the same law on every world"),
    # H3.07 -- Gravity dependence of gait & ballistics (the Froude number)
    "H3.07": Signature({"v": "m/s", "g": "m/s2", "L": "m"}, {"Fr": "1"},
                       keys={"v": "speed", "g": "g", "L": "leg_length"},
                       regime={"Fr": (0.0, 3.0)},
                       note="Froude Fr = v^2/(gL): the same 0.5 walk-run transition on every world, "
                            "which is why the Moon prediction was not fitted"),
    # H5.02 -- Whole-body thermoregulation
    "H5.02": Signature({"T_air": "degC", "Q": "W", "A": "m2"}, {"d": "m"},
                       keys={"T_air": "T", "Q": "heat", "A": "area"},
                       regime={"d": (0.0, 0.5)},
                       note="suit insulation d = kA(dT)/Q -- aHuman. THIS SOCKET IS IN CELSIUS while "
                            "E3.07's is in KELVIN: same fold, and they must never bond to each "
                            "other. That pair is the reason this whole module exists"),
}


# ════════════════════════════════════════════════════════════════════════════════════════════════
#  THE REPORT -- coverage as a NUMBER, which is the thing nobody could answer before
# ════════════════════════════════════════════════════════════════════════════════════════════════
def membranes() -> dict:
    out = {}
    for p in _HERE.rglob("numbers.json"):
        try:
            out[p.parent.name] = json.loads(p.read_text(encoding="utf8"))
        except Exception:
            continue
    return out


def report() -> int:
    cat = catalog()
    sigs = rows_with_signatures()
    mems = membranes()
    rows = cat["rows"]
    byid = {r["id"]: r for r in rows}

    print(f"THE PHYSICS TREE       {len(rows)} rows in {len(cat['branches'])} branches")
    print(f"SIGNATURES DECLARED    {len(sigs)}  ({100.0*len(sigs)/max(len(rows),1):.1f}%)")
    print(f"UNBOUND                {len(rows)-len(sigs)} rows nothing can dock to yet")
    print()

    folds = {}
    for rid, s in sigs.items():
        folds.setdefault(s.fold, []).append(rid)
    fam = {f: ids for f, ids in folds.items() if len(ids) > 1}
    print(f"FOLDS  {len(folds)} distinct, {len(fam)} of them shared "
          f"-- a shared fold means the rows SUBSTITUTE for each other:")
    for f, ids in sorted(fam.items(), key=lambda kv: -len(kv[1])):
        names = ", ".join(f"{i} {byid.get(i,{}).get('name','?')[:26]}" for i in sorted(ids))
        print(f"   {f}  {names}")
    if not fam:
        print("   (none yet -- every declared law has a distinct dimensional shape)")
    print()

    print("BINDING:")
    for rid in sorted(sigs):
        s, row = sigs[rid], byid.get(rid, {})
        hits, mis = [], []
        for name, nums in mems.items():
            d = dock(s, nums)
            if d["binds"]:
                hits.append(name)
            elif any(v["state"] == MISFOLD for v in d["symbols"].values()):
                mis.append(name)
        print(f"   {rid:<7} {row.get('name','?')[:36]:<36} -> "
              f"{', '.join(sorted(hits)[:4]) if hits else '(nothing)'}"
              f"{'  +%d' % (len(hits)-4) if len(hits) > 4 else ''}")
        if mis:
            print(f"   {'':<7} {'':<36}    MISFOLD at {', '.join(sorted(mis)[:4])}")
    print()

    tot = und = 0
    worst = []
    for name, nums in mems.items():
        u = undeclared(nums, name)
        n = sum(1 for k, v in nums.items()
                if isinstance(v, (int, float)) and not isinstance(v, bool))
        tot += n
        und += len(u)
        if u:
            worst.append((len(u), name, u[:4]))
    print(f"THE SURFACE            {tot-und} of {tot} numbers declare a unit in their key name "
          f"({100.0*(tot-und)/max(tot,1):.0f}%)")
    print("   nothing can safely bind to the rest:")
    for n, name, ex in sorted(worst, reverse=True)[:5]:
        print(f"     {name:<20} {n:3d} undeclared   e.g. {', '.join(ex)}")
    return 0


def show_membrane(name: str) -> int:
    mems = membranes()
    if name not in mems:
        print(f"no membrane {name!r}")
        return 1
    nums = mems[name]
    surf = surface(nums, name)
    print(f"{name}: {len(surf)} numbers on its binding surface\n")
    print("laws that dock here:")
    any_ = False
    for rid, s in sorted(rows_with_signatures().items()):
        d = dock(s, nums)
        if d["binds"]:
            any_ = True
            detail = ", ".join(f"{k} <- {v['key']}" for k, v in d["symbols"].items())
            print(f"   {rid}  {d['fold']}  {detail}")
        else:
            bad = [f"{k}: {v['why']}" for k, v in d["symbols"].items() if v["state"] == MISFOLD]
            if bad:
                any_ = True
                print(f"   {rid}  MISFOLD  {bad[0]}")
    if not any_:
        print("   (none of the declared laws)")
    u = undeclared(nums)
    if u:
        print(f"\n{len(u)} numbers declare no unit, so nothing can bind them: {', '.join(u[:10])}")
    return 0


# ════════════════════════════════════════════════════════════════════════════════════════════════
#  THE AUDIT -- misfolds found without a single signature
#
#  Docking needs a declared signature per law, and there are 148 rows without one. But two whole
#  classes of misfold need no signature at all, because the membranes already declare their units
#  in their key names. Both are pure consequences of the unit having a MEANING:
#
#    IMPOSSIBLE      a value its own declared unit forbids. A Kelvin below zero, a fraction above
#                    one, a negative mass. Not "unlikely" -- forbidden by what the unit IS.
#    INCONSISTENT    the same quantity published twice in two units that do not agree under
#                    conversion. `foot_pressure_Pa` and `foot_pressure_kPa` must differ by exactly
#                    1000, or one of them is stale and something downstream is reading the wrong one.
#
#  This is the sharp end of the operator's idea: a serial that carries its unit lets a machine find
#  contradictions nobody has looked for.
# ════════════════════════════════════════════════════════════════════════════════════════════════

# What each unit FORBIDS. Not taste, not a plausible band -- the values the unit cannot hold.
FORBIDDEN = {
    "K":     (0.0, None, "a temperature below absolute zero"),
    "degC":  (-273.15, None, "a temperature below absolute zero"),
    "kg":    (0.0, None, "negative mass"),
    "m2":    (0.0, None, "negative area"),
    "m3":    (0.0, None, "negative volume"),
    "kg/m3": (0.0, None, "negative density"),
    "s":     (0.0, None, "negative duration"),
    "yr":    (0.0, None, "negative duration"),
    "frac":  (0.0, 1.0, "a fraction outside 0..1"),
    "Pa":    (0.0, None, "negative absolute pressure"),
    "kPa":   (0.0, None, "negative absolute pressure"),
    "bar":   (0.0, None, "negative absolute pressure"),
    "deg":   (-360.0, 360.0, "an angle outside one turn"),
    "kg.m2": (0.0, None, "negative moment of inertia"),
}

# ── KIND. Dimensions are not enough to say two quantities are comparable.
#
# An ANGLE is dimensionless. So is a RATIO. So the pair check compared theLoad's `lean_limit_rad`
# (0.164 rad) against its `lean_limit_ratio` (0.953) -- two different quantities that happen to
# share a stem and a dimension -- and convicted a membrane whose own angle pair agrees to zero.
# A false conviction is worse than a missed one here: it teaches people to ignore the audit.
#
# So units carry a KIND, and only same-kind quantities are compared. Angles are their own kind
# precisely because being dimensionless does not make them numbers.
KIND = {
    "rad": "angle", "deg": "angle", "deg/s": "angle_rate",
    "frac": "number", "ratio": "number", "pct": "number", "1": "number", "count": "number",
    "Zsun": "number",
}


def kind_of(unit: str) -> str:
    """What sort of thing a unit measures, where the dimension alone cannot say."""
    return KIND.get(unit, "dimensional")


# Key pairs that are the SAME quantity in two units. The stem is what is left after the suffix.
_PAIRABLE = ("Pa", "kPa", "bar", "m", "km", "mm", "s", "yr", "kg", "K", "C", "TW", "W",
             "deg", "rad", "frac", "m2", "au")


def _stem(key: str):
    for suf, unit in SUFFIX_UNITS:
        if key.endswith(suf):
            return key[: -len(suf)], unit
    return None, None


def audit(verbose: bool = True) -> dict:
    """Every published number, checked against what its own declared unit permits."""
    mems = membranes()
    impossible, inconsistent = [], []

    for name, nums in sorted(mems.items()):
        # -- 1. values their unit forbids
        for k, v in nums.items():
            if not isinstance(v, (int, float)) or isinstance(v, bool):
                continue
            u = unit_of_key(k, name)
            if u is None or u not in FORBIDDEN:
                continue
            lo, hi, why = FORBIDDEN[u]
            if (lo is not None and v < lo) or (hi is not None and v > hi):
                impossible.append((name, k, v, u, why))

        # -- 2. the same stem published in two units that must agree
        by_stem = {}
        for k, v in nums.items():
            if not isinstance(v, (int, float)) or isinstance(v, bool):
                continue
            st, u = _stem(k)
            u = u or unit_of_key(k, name)
            if st and u:
                by_stem.setdefault(st, []).append((k, u, float(v)))
        for st, entries in by_stem.items():
            if len(entries) < 2:
                continue
            for i in range(len(entries)):
                for j in range(i + 1, len(entries)):
                    (ka, ua, va), (kb, ub, vb) = entries[i], entries[j]
                    if ua == ub or dim_of(ua) != dim_of(ub):
                        continue
                    if kind_of(ua) != kind_of(ub):
                        continue        # an angle is not a ratio, however dimensionless both are
                    A, B = UNITS.get(ua), UNITS.get(ub)
                    if not A or not B:
                        continue
                    # convert b into a's unit and compare
                    si_b = vb * B[1] + B[2]
                    pred = (si_b - A[2]) / A[1]
                    if abs(va) + abs(pred) < 1e-12:
                        continue
                    rel = abs(va - pred) / max(abs(va), abs(pred), 1e-12)
                    if rel > 1e-6:
                        inconsistent.append((name, ka, va, ua, kb, vb, ub, pred, rel))

    if verbose:
        print("=" * 92)
        print("MISFOLD AUDIT -- no signatures needed; the key names already declare the units")
        print("=" * 92)
        print(f"\nIMPOSSIBLE VALUES  ({len(impossible)})  -- a value its own unit forbids")
        for name, k, v, u, why in impossible:
            print(f"   {name:<20} {k:<32} = {v:<14.6g} [{u}]  {why}")
        if not impossible:
            print("   none")
        print(f"\nINCONSISTENT PAIRS ({len(inconsistent)})  -- one quantity, two units, no agreement")
        for name, ka, va, ua, kb, vb, ub, pred, rel in inconsistent:
            print(f"   {name}")
            print(f"      {ka:<30} = {va:<16.8g} [{ua}]")
            print(f"      {kb:<30} = {vb:<16.8g} [{ub}]  -> {pred:.8g} {ua}"
                  f"   ({rel*100:.1f}% apart)")
        if not inconsistent:
            print("   none")
    return {"impossible": impossible, "inconsistent": inconsistent}


def show_serial(query: str) -> int:
    """WHAT CONNECTS TO THIS. Give it a row id (H3.07), a fold (f7588543f), or a serial fragment
    (M1L2), and it answers the question the operator's idea was for: what is this, what is
    interchangeable with it, and what can it plug into."""
    sigs = rows_with_signatures()
    cat = catalog()
    byid = {r["id"]: r for r in cat["rows"]}
    mems = membranes()
    q = query.strip().lower()

    hits = [rid for rid, s in sigs.items()
            if q == rid.lower() or q == s.fold.lower() or q in s.serial.lower()]
    if not hits:
        print(f"nothing matches {query!r} -- try a row id, a fold, or a dimension like M1L2")
        return 1

    for rid in sorted(hits):
        sg = sigs[rid]
        row = byid.get(rid, {})
        print("")
        print(f"{rid}  {row.get('name','?')}")
        print(f"   serial   {sg.serial}")
        print(f"   fold     {sg.fold}")
        print(f"   takes    " + ", ".join(f"{k} [{v}]" for k, v in sg.consumes.items()))
        print(f"   gives    " + ", ".join(f"{k} [{v}]" for k, v in sg.produces.items()))
        same = [r for r in sigs if r != rid and sigs[r].fold == sg.fold]
        if same:
            print(f"   SAME SOCKET, so these substitute for it:")
            for r in sorted(same):
                print(f"      {r}  {byid.get(r,{}).get('name','?')}")
        docks = sorted(n for n, nums in mems.items() if dock(sg, nums)["binds"])
        print(f"   CONNECTS TO  {', '.join(docks) if docks else '(nothing yet)'}")
    return 0


def write_serials() -> int:
    """Stamp every declared law's serial into the catalog, so a row carries its own label."""
    cat = catalog()
    sigs = rows_with_signatures()
    n = 0
    for r in cat["rows"]:
        sg = sigs.get(r["id"])
        if sg:
            r["serial"] = sg.serial
            r["fold"] = sg.fold
            n += 1
    CATALOG.write_text(json.dumps(cat, ensure_ascii=False, indent=1), encoding="utf8")
    print(f"stamped {n} serials into {CATALOG.name}")
    return 0

if __name__ == "__main__":
    import sys
    a = sys.argv[1:]
    if a and a[0] == "serial" and len(a) > 1:
        sys.exit(show_serial(a[1]))
    if a and a[0] == "stamp":
        sys.exit(write_serials())
    if a and a[0] == "audit":
        r = audit()
        sys.exit(1 if (r["impossible"] or r["inconsistent"]) else 0)
    if a and a[0] == "membrane" and len(a) > 1:
        sys.exit(show_membrane(a[1]))
    sys.exit(report())
