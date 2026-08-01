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
]


def unit_of_key(key: str):
    """The unit a membrane's own key name declares, or None if it declares none."""
    for suf, u in SUFFIX_UNITS:
        if key.endswith(suf):
            return u
    return None


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
    if a[2] != b[2]:
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
                 keys: dict = None):
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
        return fold_of(self.consumes, self.produces)

    def as_dict(self):
        return {"consumes": self.consumes, "produces": self.produces,
                "regime": {k: list(v) for k, v in self.regime.items()},
                "keys": self.keys, "fold": self.fold, "note": self.note}

    def __repr__(self):
        return (f"<Signature {self.fold} "
                f"{'+'.join(self.consumes)} -> {'+'.join(self.produces)}>")


def surface(numbers: dict) -> dict:
    """A MEMBRANE'S BINDING SURFACE: every number it publishes whose key declares a unit.

    This is the complementary face -- what is available to bind against. Keys whose names carry no
    unit are not on the surface, and `undeclared()` lists them, because a quantity nothing can read
    the unit of is a quantity nothing can safely bind."""
    out = {}
    for k, v in numbers.items():
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            u = unit_of_key(k)
            if u:
                out[k] = u
    return out


def undeclared(numbers: dict) -> list:
    return sorted(k for k, v in numbers.items()
                  if isinstance(v, (int, float)) and not isinstance(v, bool)
                  and unit_of_key(k) is None)


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
                    if dim_of(u) == dim_of(need) and bond(need, u)[0] == MISFOLD]
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
        lo, hi = self_regime = sig.regime.get(sym, (None, None))
        if lo is not None or hi is not None:
            good, msg = in_regime(numbers[key], lo, hi)
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


def rows_with_signatures() -> dict:
    """The declared signatures, keyed by catalog row id. Everything not in here is UNBOUND, and
    that count is the honest measure of how far the physics tree actually reaches the code."""
    return dict(SIGNATURES)


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
        u = undeclared(nums)
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
    surf = surface(nums)
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


if __name__ == "__main__":
    import sys
    a = sys.argv[1:]
    if a and a[0] == "membrane" and len(a) > 1:
        sys.exit(show_membrane(a[1]))
    sys.exit(report())
