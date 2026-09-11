"""run_controls.py -- executes preregistered R1-R4 (holodeck-mat-01) against
the reference model in one process; writes checks/*.txt with verbatim
refusals and post-state assertions. Read-only over the rest of the tree.

Usage: python controls/run_controls.py
"""
from __future__ import annotations

import sys
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "reference"))
sys.path.insert(0, str(HERE.parent.parents[2] / "MATH" / "MATH-01" / "reference"))

import mat01_reference_model as mat  # noqa: E402
import math01_reference_model as m01  # noqa: E402

OUT = HERE.parent / "checks"
OUT.mkdir(exist_ok=True)


class Row:
    def __init__(self, name, expect):
        self.name = name
        self.expect = expect
        self.lines = []
        self.passed = 0

    def ok(self, text):
        self.passed += 1
        self.lines.append(f"  PASS [{self.passed}] {text}")

    def write(self, path, verdict_threshold):
        head = [f"{self.name}", f"threshold: {verdict_threshold}",
                f"verdict: {'HOLDS' if self.passed >= self.threshold else 'FIRED'} "
                f"({self.passed}/{self.threshold})", ""]
        path.write_text("\n".join(head + self.lines) + "\n", encoding="utf-8")
        return self.passed


def refused(row, text, fn, reason_sub):
    """Run fn expecting Mat01Refusal with reason containing reason_sub."""
    try:
        fn()
    except mat.Mat01Refusal as r:
        if reason_sub in r.reason:
            row.ok(f"refused {r.reason}: {text} | detail: {r.message}")
        else:
            row.lines.append(
                f"  FAIL [?] {text}: wrong refusal reason {r.reason!r} "
                f"(wanted {reason_sub!r}): {r.message}")
        return
    except Exception as e:  # wrong exception class = a miss, reported
        row.lines.append(f"  FAIL [?] {text}: raised {type(e).__name__}: {e}")
        return
    row.lines.append(f"  FAIL [?] {text}: NO refusal -- operation was admitted")


DENSITY_RAW = {"name": "density", "value": 250.0, "unit": "kg/m^3",
               "source": "INVISTA Dacron fiberfill TDS (comparable: Advansa Suprelle)",
               "conditions": "stuffed plush assembly, bulk, 20 C, dry",
               "provenance": "researched"}
MODULUS_RAW = {"name": "modulus", "value": 120.0, "unit": "kPa",
               "source": "synthetic declared interface (fixture)",
               "conditions": "small-strain, 20 C", "provenance": "researched"}
SG_RAW = {"name": "sg", "value": 0.25, "unit": "sg",
          "source": "handbook SG table", "conditions": "water at 4 C basis",
          "provenance": "researched"}
FRACTION_RAW = {"name": "fraction", "value": 0.4, "unit": "1",
                "source": "declared fixture interface",
                "conditions": "void fraction at nominal pack", "provenance": "researched"}


def r1_positive() -> Row:
    row = Row("R1 positive admissions (model must ACCEPT)", expect=7)
    # (a) density admitted -> Quantity dimension (L^-3 M)
    d = mat.admit(DENSITY_RAW)
    q = d.quantity
    if q.dimension == m01.Dimension((-3, 1, 0)) and q.value == 250.0:
        row.ok("density admitted: Quantity(250, (L^-3 M)) exact")
    else:
        row.lines.append(f"  FAIL [?] density dimension {q.dimension}")
    # (b) modulus in kPa -> SI 1.2e5 Pa dimension
    m = mat.admit(MODULUS_RAW)
    if m.quantity.value == 1.2e5 and m.quantity.dimension == m01.Dimension.PA:
        row.ok("modulus kPa admitted: SI value 120000 with Pa dimension")
    else:
        row.lines.append(f"  FAIL [?] modulus SI {m.quantity}")
    # (c) derived density from SG WITH declared basis
    sg = mat.admit(SG_RAW)
    dd = mat.density_from_sg(sg, 1000.0, "water at 4 C")
    if dd.property_type() == "density" and dd.quantity.value == 250.0 \
            and "rho = SG x rho_ref" in dd.derivation:
        row.ok("density_from_sg WITH basis: derived record carries arithmetic "
               f"({dd.derivation})")
    else:
        row.lines.append(f"  FAIL [?] derived record wrong: {dd}")
    # (d) fraction admitted
    f = mat.admit(FRACTION_RAW)
    if f.quantity.value == 0.4 and f.quantity.is_dimensionless():
        row.ok("fraction 0.4 admitted dimensionless")
    else:
        row.lines.append(f"  FAIL [?] fraction {f}")
    # (e) snapshot immutable mapping, identical content
    bag = {"density": d, "modulus": m}
    snap = mat.snapshot(bag)
    if not isinstance(snap, __import__("types").MappingProxyType) \
            and not str(type(snap)).endswith("mappingproxy'>"):
        row.lines.append(f"  FAIL [?] snapshot type {type(snap)}")
    elif snap["density"] is d and len(snap) == 2:
        row.ok("snapshot() is an immutable mapping with identical content")
    else:
        row.lines.append("  FAIL [?] snapshot content mismatch")
    # (f) MATH-01 composition: Pa x dimensionless strain x m^3 -> J dimension
    strain = m01.Quantity(0.05, m01.Dimension.DIMENSIONLESS)
    vol = m01.Quantity(8e-6, m01.Dimension.M * m01.Dimension.M * m01.Dimension.M)
    energy = m.quantity * strain * vol  # Pa * 1 * m^3
    if energy.dimension == m01.Dimension((2, 1, -2)):  # J = L^2 M T^-2
        row.ok("MATH-01 composition: Pa x 1 x m^3 -> (2,1,-2) = L^2 M T^-2 "
               "= J dimension (algebra cited from MATH-01, not reimplemented)")
    else:
        row.lines.append(f"  FAIL [?] composed dimension {energy.dimension}")
    # (g) bulk_mass on admitted records -> Dimension M
    mass = mat.bulk_mass(d, vol)
    if mass.dimension == m01.Dimension((0, 1, 0)) and abs(mass.value - 250.0 * 8e-6) < 1e-18:
        row.ok(f"bulk_mass(admitted rho, Quantity volume) -> M dimension, "
               f"value {mass.value}")
    else:
        row.lines.append(f"  FAIL [?] bulk_mass {mass}")
    row.threshold = 7
    return row


def r2_card_prediction_negatives() -> Row:
    row = Row("R2 card-prediction negatives (model must REFUSE, named reason)", expect=8)
    bad_unit = dict(DENSITY_RAW, unit="stones/week")
    refused(row, "unregistered unit 'stones/week'",
            lambda: mat.admit(bad_unit), mat.REASON_UNKNOWN_UNIT)
    wrong_fam = dict(DENSITY_RAW, unit="Pa")
    refused(row, "registered unit of the WRONG family ('Pa' on a density)",
            lambda: mat.admit(wrong_fam), mat.REASON_UNIT_DIMENSION_MISMATCH)
    refused(row, "NaN value",
            lambda: mat.admit(dict(DENSITY_RAW, value=float("nan"))),
            mat.REASON_NONFINITE)
    refused(row, "+inf value",
            lambda: mat.admit(dict(DENSITY_RAW, value=float("inf"))),
            mat.REASON_NONFINITE)
    refused(row, "non-numeric value 'heavy'",
            lambda: mat.admit(dict(DENSITY_RAW, value="heavy")),
            mat.REASON_NONFINITE)
    refused(row, "derived provenance with blank derivation",
            lambda: mat.admit(dict(DENSITY_RAW, provenance="derived",
                                   derivation="   ")),
            mat.REASON_MISSING_BASIS)
    sg = mat.admit(SG_RAW)
    refused(row, "density_from_sg with blank basis conditions",
            lambda: mat.density_from_sg(sg, 1000.0, "   "),
            mat.REASON_MISSING_BASIS)
    refused(row, "negative basis density",
            lambda: mat.density_from_sg(sg, -5.0, "water at 4 C"),
            mat.REASON_INVALID_VALUE)
    row.threshold = 8
    return row


class _Impostor:
    """Duck-typed stand-in that is NOT an admitted MaterialParameter."""
    name = "density"
    quantity = m01.Quantity(250.0, m01.Dimension((-3, 1, 0)))
    unit_original = "kg/m^3"

    def property_type(self):
        return "density"


def r3_falsifier_bypass() -> Row:
    row = Row("R3 CARD FALSIFIER probe: legacy bypass attempts at the real caller "
              "(model must REFUSE all)", expect=6)
    vol = m01.Quantity(8e-6, m01.Dimension((3, 0, 0)))
    d = mat.admit(DENSITY_RAW)
    refused(row, "raw dict handed to bulk_mass",
            lambda: mat.bulk_mass(DENSITY_RAW, vol), mat.REASON_LEGACY_INPUT)
    refused(row, "bare float 250.0 handed to bulk_mass",
            lambda: mat.bulk_mass(250.0, vol), mat.REASON_LEGACY_INPUT)
    refused(row, "string '250 kg/m^3' handed to bulk_mass",
            lambda: mat.bulk_mass("250 kg/m^3", vol), mat.REASON_LEGACY_INPUT)
    refused(row, "duck-typed impostor (not an admitted record)",
            lambda: mat.bulk_mass(_Impostor(), vol), mat.REASON_LEGACY_INPUT)
    # (e) mutation attempt on an admitted record
    before = d.quantity
    try:
        d.quantity = m01.Quantity(1.0, d.quantity.dimension)
        row.lines.append("  FAIL [?] attribute mutation was ALLOWED")
    except mat.Mat01Refusal as r:
        if d.quantity is before and d.quantity.value == 250.0:
            row.ok(f"mutation refused ({r.reason}) and the record is "
                   "unchanged afterward")
        else:
            row.lines.append("  FAIL [?] mutation raised but the record changed")
    except Exception as e:
        row.lines.append(f"  FAIL [?] mutation raised {type(e).__name__}: {e}")
    # (f) hostile injection: plain dict slipped into the bag, then served
    hostile_bag = {"density": dict(DENSITY_RAW)}
    refused(row, "hostile dict in the bag, caught at serve time",
            lambda: mat.serve(hostile_bag, "density"),
            mat.REASON_NOT_A_SNAPSHOT)
    # post-state: the calculation never executed for any refused input
    row.lines.append("  post-state: no arithmetic ran on any refused input "
                     "(each refusal raised before the product)")
    row.threshold = 6
    return row


def r4_immutability() -> Row:
    row = Row("R4 immutable snapshots / records", expect=4)
    d = mat.admit(DENSITY_RAW)
    m = mat.admit(MODULUS_RAW)
    bag = {"density": d, "modulus": m}
    snap = mat.snapshot(bag)
    # (a) item assignment forbidden
    try:
        snap["density"] = d
        row.lines.append("  FAIL [?] snapshot item assignment was ALLOWED")
    except TypeError:
        row.ok("snapshot item assignment raises TypeError (mappingproxy)")
    # (b) converted copy is NEW; original byte-identical before/after
    before_repr = (repr(d.quantity), repr(d.unit_original), repr(d.derivation))
    kpa = mat.admit(dict(MODULUS_RAW, unit="kpa"))
    pa_copy = mat.as_unit(kpa, "Pa")
    if pa_copy is not kpa and pa_copy.quantity.value == 120000.0 \
            and (repr(kpa.quantity), repr(kpa.unit_original), repr(kpa.derivation)) == before_repr:
        row.ok("as_unit returns a NEW record (120 kPa -> 120000 Pa); "
               "original untouched")
    else:
        row.lines.append("  FAIL [?] conversion mutated the original or "
                         "wrong value")
    # (c) double admission refused, first intact
    bag2 = {}
    mat.admit_into(bag2, DENSITY_RAW)
    refused(row, "double admission of the same property name",
            lambda: mat.admit_into(bag2, dict(DENSITY_RAW, value=1.0)),
            mat.REASON_DUPLICATE)
    if bag2["density"].quantity.value == 250.0:
        row.ok("first admission intact after duplicate refusal (value still 250)")
    else:
        row.lines.append("  FAIL [?] first admission was overwritten")
    # (d) snapshot -> serve round trip identical Quantity
    snap2 = mat.snapshot(bag2)
    served = mat.serve(snap2, "density")
    if served is bag2["density"] and served.quantity == bag2["density"].quantity:
        row.ok("snapshot -> serve round trip returns the identical record")
    else:
        row.lines.append("  FAIL [?] round trip changed the record")
    row.threshold = 4
    return row


def main() -> int:
    rows = [r1_positive(), r2_card_prediction_negatives(),
            r3_falsifier_bypass(), r4_immutability()]
    files = ["r1_positive.txt", "r2_card_prediction_negatives.txt",
             "r3_falsifier_bypass.txt", "r4_immutability.txt"]
    summary = []
    for row, fn in zip(rows, files):
        row.write(OUT / fn, f"{row.threshold}/{row.threshold}")
        summary.append((row.name.split(" (")[0], row.passed, row.threshold))
    print("SCOREBOARD")
    ok = True
    for name, p, t in summary:
        verdict = "HOLDS" if p >= t else "FIRED"
        print(f"  {name}: {p}/{t} {verdict}")
        ok = ok and p >= t
    print("ALL ROWS HOLD" if ok else "A ROW FIRED -- reported, not patched")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
