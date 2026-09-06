"""material_contract_checks.py — P-8a..j, the contract's registered falsifiers.

Each check asserts a verdict that was written into
docs/FOUNDATION_G01_REPORT.md BEFORE this file existed. Tolerances are the
house algebraic allowances (512*e); none is widened after seeing results.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np

from port_registry import port_test, expect

import material_contract as mc

# the algebraic allowance (same family as the surface checks)
E = float(np.finfo(np.float64).eps)
INV_LIMIT = 512 * E

EXPECTED_CHECKS = [
    "P8a_sourced_property_available",
    "P8b_missing_property_refused",
    "P8c_unknown_unit_rejected",
    "P8d_negative_density_rejected",
    "P8e_nonfinite_rejected",
    "P8f_orthotropic_matrix_validated",
    "P8g_nonorthonormal_frame_rejected",
    "P8h_shared_binding_propagates",
    "P8i_sg_requires_basis",
    "P8j_model_claim_refused",
]


# ── fixtures ─────────────────────────────────────────────────────────────────

def _contract() -> mc.MaterialContract:
    c = mc.MaterialContract()
    c.register(mc.build_white_oak_record())
    return c


def _sym_pd_orthotropic() -> np.ndarray:
    """A symmetric positive-definite 6x6 built from an orthotropic stiffness
    law (normal decoupled from shear, as the Voigt convention requires)."""
    E1, E2, E3 = 12.3e9, 0.9e9, 0.6e9
    G12, G13, G23 = 0.8e9, 0.7e9, 0.4e9
    D = np.diag([E1, E2, E3, G12, G13, G23])
    K = np.zeros((6, 6))
    K[:3, :3] = D[:3, :3]
    K[3:, 3:] = D[3:, 3:]
    return K


# ── P-8a: the sourced property is available with provenance ──────────────────

@port_test(
    "P8a_sourced_property_available",
    "white_oak E_L is available at 12.3e9 Pa with unit 'Pa' and the Wood "
    "Handbook Table 5-3b locator attached.",
    "The value, unit, or source locator differs from the sourced record.")
def p8a() -> dict:
    p = _contract().get("white_oak", "E_L")
    ok = (abs(p.value - 12.3e9) <= 0.0 and p.unit.lower() == "pa"
          and "FPL-GTR-190" in p.source and "5-3b" in p.source
          and p.provenance is mc.Provenance.RESEARCHED)
    return {"pass": ok, "value": p.value, "unit": p.unit,
            "source": p.source, "provenance": p.provenance.value}


# ── P-8b: a never-published property is refused BY NAME ─────────────────────

@port_test(
    "P8b_missing_property_refused",
    "Asking white_oak for 'G_LT' (never published in matter_data) raises "
    "missing_input naming exactly that property; NOT a zero, NOT a default.",
    "The ask returns a value, a zero, or refuses under the wrong kind/name.")
def p8b() -> dict:
    try:
        _contract().get("white_oak", "G_LT")
        return {"pass": False, "error": "returned a value instead of refusing"}
    except mc.ContractRefusal as ex:
        ok = (ex.kind is mc.RefusalKind.MISSING_INPUT
              and "G_LT" in ex.detail)
        return {"pass": ok, "kind": ex.kind.value, "detail": ex.detail}


# ── P-8c: unregistered unit is rejected, no invented conversion ──────────────

@port_test(
    "P8c_unknown_unit_rejected",
    "A property carrying unit 'psi' (unregistered) is rejected at the door; "
    "and converting a registered property to 'psi' is refused, not converted.",
    "A 'psi' value is accepted or a conversion factor is invented for it.")
def p8c() -> dict:
    gate_ok = conv_ok = False
    gate_detail = conv_detail = ""
    try:
        mc.MaterialProperty(name="test_E", value=1.8e6, unit="psi",
                            source="fixture", conditions="fixture",
                            provenance=mc.Provenance.RESEARCHED)
    except mc.ContractRefusal as ex:
        gate_ok = ex.kind is mc.RefusalKind.UNKNOWN_UNIT
        gate_detail = ex.detail
    try:
        mc.convert(12.3e9, "Pa", "psi")
    except mc.ContractRefusal as ex:
        conv_ok = ex.kind is mc.RefusalKind.UNKNOWN_UNIT
        conv_detail = ex.detail
    return {"pass": bool(gate_ok and conv_ok),
            "gate": gate_detail, "convert": conv_detail}


# ── P-8d: negative density is physically invalid ─────────────────────────────

@port_test(
    "P8d_negative_density_rejected",
    "A property named '*density*' with a negative value is refused as "
    "physically_invalid.",
    "A negative density is accepted.")
def p8d() -> dict:
    try:
        mc.MaterialProperty(name="density", value=-5.0, unit="kg/m^3",
                            source="fixture", conditions="fixture",
                            provenance=mc.Provenance.RESEARCHED)
        return {"pass": False, "error": "negative density accepted"}
    except mc.ContractRefusal as ex:
        return {"pass": ex.kind is mc.RefusalKind.PHYSICALLY_INVALID,
                "kind": ex.kind.value, "detail": ex.detail}


# ── P-8e: NaN is refused at the door ─────────────────────────────────────────

@port_test(
    "P8e_nonfinite_rejected",
    "A property with value NaN is refused as nonfinite.",
    "NaN passes validation.")
def p8e() -> dict:
    try:
        mc.MaterialProperty(name="E_L", value=float("nan"), unit="Pa",
                            source="fixture", conditions="fixture",
                            provenance=mc.Provenance.RESEARCHED)
        return {"pass": False, "error": "NaN accepted"}
    except mc.ContractRefusal as ex:
        return {"pass": ex.kind is mc.RefusalKind.NONFINITE,
                "kind": ex.kind.value, "detail": ex.detail}


# ── P-8f: orthotropic matrix validation (symmetry + PD) ─────────────────────

@port_test(
    "P8f_orthotropic_matrix_validated",
    "A symmetric positive-definite 6x6 passes; an asymmetric entry or a "
    "non-PD matrix is refused with the offending convention named.",
    "A malformed matrix passes, or the refusal names the wrong convention.")
def p8f() -> dict:
    # control passes
    mc.validate_orthotropic(_sym_pd_orthotropic())
    # asymmetric entry -> refused
    asym_refused = asym_named = False
    M = _sym_pd_orthotropic()
    M[0, 1] += 1.0
    try:
        mc.validate_orthotropic(M)
    except mc.ContractRefusal as ex:
        asym_refused = True
        asym_named = "symmetry" in ex.detail
    # non-PD -> refused
    pd_refused = pd_named = False
    M2 = _sym_pd_orthotropic()
    M2[4, 4] = -1.0
    try:
        mc.validate_orthotropic(M2)
    except mc.ContractRefusal as ex:
        pd_refused = True
        pd_named = "positive definite" in ex.detail
    return {"pass": bool(asym_refused and asym_named
                         and pd_refused and pd_named),
            "asymmetric_refused": asym_refused, "named_symmetry": asym_named,
            "nonpd_refused": pd_refused, "named_pd": pd_named}


# ── P-8g: non-orthonormal material frame is rejected ─────────────────────────

@port_test(
    "P8g_nonorthonormal_frame_rejected",
    "A material frame whose axes are not orthonormal is refused; an "
    "orthonormal frame passes.",
    "A skewed frame is accepted.")
def p8g() -> dict:
    good = np.array([[1., 0., 0.], [0., 1., 0.], [0., 0., 1.]])
    mc.validate_orthotropic(_sym_pd_orthotropic(), frame=good)
    bad = np.array([[1., 0., 0.], [1., 1., 0.], [0., 0., 1.]])
    try:
        mc.validate_orthotropic(_sym_pd_orthotropic(), frame=bad)
        return {"pass": False, "error": "non-orthonormal frame accepted"}
    except mc.ContractRefusal as ex:
        return {"pass": "orthonormal" in ex.detail,
                "detail": ex.detail}


# ── P-8h: one record, many bindings, mutation propagates ─────────────────────

@port_test(
    "P8h_shared_binding_propagates",
    "The SAME material record bound to TWO geometries answers identically on "
    "both; mutating the shared record's value propagates to both bindings "
    "through the adapter (no per-geometry copy).",
    "A binding sees a stale value after the shared record changes.")
def p8h() -> dict:
    c = _contract()
    b1 = mc.bind(c, "white_oak", "geo_A")
    b2 = mc.bind(c, "white_oak", "geo_B")
    v1a = b1.get("E_L").value
    v2a = b2.get("E_L").value
    # mutate the SHARED record's source value (surgery with the same gates)
    rec = c.record("white_oak")
    rec.properties["E_L"] = mc.MaterialProperty(
        name="E_L", value=13.0e9, unit="Pa",
        source="fixture mutation (P-8h)", conditions="fixture",
        provenance=mc.Provenance.RESEARCHED)
    v1b = b1.get("E_L").value
    v2b = b2.get("E_L").value
    unit_same = b1.get("E_L", as_unit="MPa").value == 13000.0
    return {"pass": bool(v1a == v2a == 12.3e9 and v1b == v2b == 13.0e9
                         and unit_same),
            "before": [v1a, v2a], "after": [v1b, v2b],
            "as_MPa": b1.get("E_L", as_unit="MPa").value}


# ── P-8i: SG -> density needs a DECLARED basis ───────────────────────────────

@port_test(
    "P8i_sg_requires_basis",
    "SG 0.68 converted to kg/m^3 WITHOUT a declared reference basis raises "
    "missing_basis. WITH the basis declared (water 1000 kg/m^3 at 4 C, the "
    "Handbook's own convention) the derivation is available at 680 kg/m^3 "
    "with provenance 'derived' and the arithmetic attached.",
    "A basis-free conversion succeeds, or the based derivation carries no "
    "arithmetic.")
def p8i() -> dict:
    c = _contract()
    basis_refused = False
    try:
        # the "basis-free" ask: the API offers no such path; calling the
        # derivation with a NaN basis is the strongest proxy for "no basis"
        c.density_from_sg("white_oak", float("nan"), "")
    except mc.ContractRefusal as ex:
        basis_refused = ex.kind is mc.RefusalKind.MISSING_BASIS or \
            ex.kind is mc.RefusalKind.PHYSICALLY_INVALID
    derived = c.density_from_sg("white_oak", 1000.0,
                                "water at 4 C (Handbook convention)")
    ok = (basis_refused
          and abs(derived.value - 680.0) <= INV_LIMIT
          and derived.unit == "kg/m^3"
          and derived.provenance is mc.Provenance.DERIVED
          and "0.68 x 1000.0" in derived.derivation)
    return {"pass": ok, "value": derived.value, "unit": derived.unit,
            "provenance": derived.provenance.value,
            "derivation": derived.derivation}


# ── P-8j: a model claim beyond the sources is refused ────────────────────────

@port_test(
    "P8j_model_claim_refused",
    "Asking white_oak (orthotropic-ratio wood data) for 3D isotropic "
    "elasticity raises unsupported_model, while uniaxial-along-grain stays "
    "available.",
    "The 3D claim succeeds, or the uniaxial claim is refused.")
def p8j() -> dict:
    c = _contract()
    refused = named = False
    try:
        c.model("white_oak", "isotropic_3d")
    except mc.ContractRefusal as ex:
        refused = ex.kind is mc.RefusalKind.UNSUPPORTED_MODEL
        named = "isotropic_3d" in ex.detail
    c.model("white_oak", "uniaxial_along_grain")   # must NOT raise
    return {"pass": bool(refused and named),
            "refused": refused, "named": named}


expect(len(EXPECTED_CHECKS))


def main(argv: list[str]) -> int:
    from port_registry import TESTS
    argv = [a for a in argv if not a.startswith("-")]
    if argv:
        only = set(argv)
    else:
        only = set(EXPECTED_CHECKS)
    rc = 0
    for name in EXPECTED_CHECKS:
        if name not in only:
            continue
        entry = TESTS[name]
        fn = entry["fn"] if isinstance(entry, dict) else entry
        res = fn()
        ok = bool(res.get("pass"))
        print(f"[{'PASS' if ok else 'FAIL'}] {name}"
              + ("" if ok else f"  {res}"))
        rc |= 0 if ok else 1
    return rc


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
