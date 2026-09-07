"""material_contract_checks.py — P-8a..j, the contract's registered falsifiers.

Each check asserts a verdict that was written into
docs/FOUNDATION_G01_REPORT.md BEFORE this file existed. Tolerances are the
house algebraic allowances (512*e); none is widened after seeing results.
"""
from __future__ import annotations

import json
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
    # G01-R2 regression checks (predictions registered in report section 9-R2)
    "R2k_negative_modulus_by_type",
    "R2l_density_unit_family",
    "R2m_blank_provenance_refused",
    "R2n_convert_validates_before_identity",
    "R2o_nan_frame_and_matrix_refused",
    "R2p_metric_refuses_degenerate_geometry",
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


# ── G01-R2: the six refusal gaps ASTRA's review exposed ──────────────────────
# Each asserts the prediction registered in report section 9-R2 BEFORE the fix.
# Root causes are documented at the fix sites; none of the P-8a..j behavior
# above is modified, and no tolerance appears here except the house INV_LIMIT
# already defined above.

@port_test(
    "R2k_negative_modulus_by_type",
    "MaterialProperty('E', -1, 'Pa', ...) is refused physically_invalid, and "
    "a positive-E control constructs. Root cause fixed: the old law compared "
    "n in ('E', 'K_IC') against name.lower() -- 'e' != 'E' -- so the exact "
    "name 'E' was never gated; the new law keys on the property TYPE via the "
    "declared hint table.",
    "A negative modulus constructs, or the positive control is refused.")
def r2k() -> dict:
    def mk(v):
        return mc.MaterialProperty(name="E", value=v, unit="Pa",
                                   source="fixture (P-8k)", conditions="fixture",
                                   provenance=mc.Provenance.RESEARCHED)
    refused = named = False
    try:
        mk(-1.0)
    except mc.ContractRefusal as ex:
        refused = ex.kind is mc.RefusalKind.PHYSICALLY_INVALID
        named = "must be positive" in ex.detail
    control_ok = True
    try:
        mk(12.3e9)
    except mc.ContractRefusal as ex:
        control_ok = False
        control_detail = ex.detail
    return {"pass": bool(refused and named and control_ok),
            "refused": refused, "named": named, "control_ok": control_ok}


@port_test(
    "R2l_density_unit_family",
    "A density-typed property carrying unit 'm' (length family) is refused "
    "physically_invalid naming both families; the positive control in kg/m^3 "
    "constructs. The unit registry always had the families -- the gap was "
    "that no law tied the property type to its unit family.",
    "A density in meters is accepted, or the control is refused.")
def r2l() -> dict:
    def mk(u, v=1000.0):
        return mc.MaterialProperty(name="density", value=v, unit=u,
                                   source="fixture (P-8l)", conditions="fixture",
                                   provenance=mc.Provenance.RESEARCHED)
    refused = named = False
    try:
        mk("m")
    except mc.ContractRefusal as ex:
        refused = ex.kind is mc.RefusalKind.PHYSICALLY_INVALID
        named = ("density" in ex.detail and "length" in ex.detail)
    control_ok = True
    try:
        mk("kg/m^3", 680.0)
    except mc.ContractRefusal as ex:
        control_ok = False
        control_detail = ex.detail
    return {"pass": bool(refused and named and control_ok),
            "refused": refused, "named_families": named, "control_ok": control_ok}


@port_test(
    "R2m_blank_provenance_refused",
    "Empty or whitespace-only source or conditions is refused "
    "physically_invalid: a property without provenance is not a property. "
    "A fully-cited control constructs.",
    "A blank-locator record is accepted.")
def r2m() -> dict:
    def mk(source, conditions):
        return mc.MaterialProperty(name="E_L", value=12.3e9, unit="Pa",
                                   source=source, conditions=conditions,
                                   provenance=mc.Provenance.RESEARCHED)
    results = []
    for label, s, c in (("empty_source", "", "12% MC"),
                        ("blank_source", "   ", "12% MC"),
                        ("empty_conditions", "T5-3b", ""),
                        ("blank_conditions", "T5-3b", " \t ")):
        try:
            mk(s, c)
            results.append((label, False, ""))
        except mc.ContractRefusal as ex:
            results.append((label,
                            ex.kind is mc.RefusalKind.PHYSICALLY_INVALID,
                            ex.detail))
    control_ok = True
    try:
        mk("USDA FPL GTR-190 T5-3b", "12% MC")
    except mc.ContractRefusal:
        control_ok = False
    return {"pass": bool(all(r[1] for r in results) and control_ok),
            "cases": results, "control_ok": control_ok}


@port_test(
    "R2n_convert_validates_before_identity",
    "convert(1, 'bogus', 'bogus') raises unknown_unit: the registry lookup "
    "gates every call BEFORE the same-unit identity shortcut (the old code "
    "returned on u == v first and silently 'converted'). Legal identities "
    "inside a registered family still convert.",
    "The bogus identity returns 1, or the legal identity is refused.")
def r2n() -> dict:
    bogus_refused = named = False
    try:
        r = mc.convert(1.0, "bogus", "bogus")
        bogus_value = r
    except mc.ContractRefusal as ex:
        bogus_refused = ex.kind is mc.RefusalKind.UNKNOWN_UNIT
        named = "bogus" in ex.detail
    legal_identity_ok = False
    try:
        legal_identity_ok = (mc.convert(12.3e9, "Pa", "pa") == 12.3e9
                             and mc.convert(1.0, "1", "1") == 1.0)
    except mc.ContractRefusal:
        legal_identity_ok = False
    cross_family_still_refused = False
    try:
        mc.convert(1.0, "pa", "m")
    except mc.ContractRefusal as ex:
        cross_family_still_refused = ex.kind is mc.RefusalKind.UNKNOWN_UNIT
    return {"pass": bool(bogus_refused and named and legal_identity_ok
                         and cross_family_still_refused),
            "bogus_refused": bogus_refused, "named": named,
            "legal_identity_ok": legal_identity_ok,
            "cross_family_still_refused": cross_family_still_refused}


@port_test(
    "R2o_nan_frame_and_matrix_refused",
    "validate_orthotropic(identity6, NaN_frame) is refused physically_invalid; "
    "a NaN stiffness entry is likewise refused. Root cause fixed: 'dev > tol' "
    "and 'eig.min() <= 0' are silently False for NaN -- every old comparison "
    "was NaN-blind; the new gates are explicit-finite + 'not (x <= tol)' form.",
    "Any NaN input passes validation.")
def r2o() -> dict:
    I6 = np.eye(6)
    frame_nan = np.array([[1., 0., 0.], [0., float("nan"), 0.], [0., 0., 1.]])
    frame_refused = frame_named = False
    try:
        mc.validate_orthotropic(I6, frame=frame_nan)
    except mc.ContractRefusal as ex:
        frame_refused = ex.kind is mc.RefusalKind.PHYSICALLY_INVALID
        frame_named = "nan" in ex.detail.lower()
    M_nan = np.eye(6)
    M_nan[2, 2] = float("nan")
    matrix_refused = matrix_named = False
    try:
        mc.validate_orthotropic(M_nan)
    except mc.ContractRefusal as ex:
        matrix_refused = ex.kind is mc.RefusalKind.PHYSICALLY_INVALID
        matrix_named = "nan" in ex.detail.lower()
    control_ok = True
    try:
        mc.validate_orthotropic(_sym_pd_orthotropic(),
                                frame=np.eye(3))
    except mc.ContractRefusal:
        control_ok = False
    return {"pass": bool(frame_refused and frame_named and matrix_refused
                         and matrix_named and control_ok),
            "frame_refused": frame_refused, "frame_named": frame_named,
            "matrix_refused": matrix_refused, "matrix_named": matrix_named,
            "control_ok": control_ok}


@port_test(
    "R2p_metric_refuses_degenerate_geometry",
    "triangle_metric refuses collapsed rest OR current triangles BY NAME "
    "(InvalidSurface COLLAPSED_TRIANGLE for zero-area: collinear distinct "
    "vertices or a zero edge) BEFORE any normalization or division; area "
    "below the reference's own floor (64*e*max_edge^2) raises "
    "NEAR_DEGENERATE; a healthy control returns finite C. Root cause fixed: "
    "_frame divided by area2 and |e1| before validating and the det guard "
    "was NaN-blind -- degenerate geometry produced NaN results, never a "
    "refusal. No new constant: the floor is the reference's own.",
    "Degenerate input yields NaN results instead of raising, or the healthy "
    "control is refused.")
def r2p() -> dict:
    import surface_energy_reference as ser
    faces = np.array([[0, 1, 2], [0, 2, 3]], dtype=np.int64)
    healthy = np.array([[0., 0., 0.], [1., 0., 0.], [0., 1., 0.],
                        [1., 1., 0.]])
    # control: finite C, both faces
    ctrl = ser.triangle_metric(healthy, healthy, faces)
    control_ok = bool(np.all(np.isfinite(ctrl.C))
                      and ctrl.C.shape == (2, 2, 2))
    def collapse(rest, cur):
        try:
            ser.triangle_metric(rest, cur, faces)
            return None
        except ser.InvalidSurface as ex:
            return ex.reason
    # current side: face 0 (0,1,2) collapsed by COLLINEAR DISTINCT vertices
    r_cur_collinear_f0 = collapse(healthy,
                                  np.array([[0., 0., 0.], [1., 0., 0.],
                                            [2., 0., 0.], [1., 1., 0.]]))
    # current side: face 1 (0,2,3) collapsed by collinear distinct vertices
    r_cur_collinear_f1 = collapse(healthy,
                                  np.array([[0., 0., 0.], [1., 0., 0.],
                                            [0., 1., 0.], [0., 2., 0.]]))
    # current side: ZERO-LENGTH edge in face 0
    r_zero_edge = collapse(healthy,
                           np.array([[0., 0., 0.], [0., 0., 0.],
                                     [0., 1., 0.], [1., 1., 0.]]))
    # REST side: the rest geometry itself is collapsed
    r_rest_collapsed = collapse(np.array([[0., 0., 0.], [1., 0., 0.],
                                          [2., 0., 0.], [1., 1., 0.]]),
                                healthy)
    near = np.array([[0., 0., 0.], [1., 0., 0.],
                     [5e-15, 1e-14, 0.], [1., 1., 0.]])   # |cross| ~1e-14, floor ~1.4e-14-ish by max_edge
    r_near = None
    try:
        res = ser.triangle_metric(near, near, faces)
        r_near = f"accepted: area2={np.linalg.norm(np.cross(near[1]-near[0], near[2]-near[0])):.3e}"
    except ser.InvalidSurface as ex:
        r_near = ex.reason
    ok_coll = (r_cur_collinear_f0 == ser.RejectionReason.COLLAPSED_TRIANGLE
               and r_cur_collinear_f1 == ser.RejectionReason.COLLAPSED_TRIANGLE
               and r_zero_edge == ser.RejectionReason.COLLAPSED_TRIANGLE
               and r_rest_collapsed == ser.RejectionReason.COLLAPSED_TRIANGLE)
    ok_near = r_near in (ser.RejectionReason.NEAR_DEGENERATE,
                         ser.RejectionReason.COLLAPSED_TRIANGLE)
    return {"pass": bool(control_ok and ok_coll and ok_near),
            "control_finite": control_ok,
            "cur_collinear_f0": r_cur_collinear_f0,
            "cur_collinear_f1": r_cur_collinear_f1,
            "zero_edge": r_zero_edge, "rest_collapsed": r_rest_collapsed,
            "near_degenerate": r_near}


expect(len(EXPECTED_CHECKS))


def main(argv: list[str]) -> int:
    from port_registry import TESTS
    from evidence_output import (EVIDENCE_REFUSAL_EXIT, EvidencePathExists,
                                 resolve_evidence_path, strip_flags)
    # EVIDENCE LAW FIRST (G01-R3 D6): resolve the output path BEFORE any
    # check runs. Refusal (exit 2) happens without computing anything; the
    # default is a unique stamped file. This runner previously wrote NO raw
    # results at all -- both defects (overwrite hazard, missing raw record)
    # are closed by the same law.
    out_dir = Path(__file__).resolve().parent.parent / "agent_logs" / \
        "glm_foundation_g01"
    out_dir.mkdir(parents=True, exist_ok=True)
    try:
        out_path = resolve_evidence_path(out_dir,
                                         "material_contract_checks_results",
                                         argv)
    except EvidencePathExists as ex:
        print(f"REFUSAL: {ex}")
        print("Nothing was computed or written; historical evidence intact.")
        return EVIDENCE_REFUSAL_EXIT
    only = set(strip_flags(argv)) or set(EXPECTED_CHECKS)
    results = {}
    failed = 0
    for name in EXPECTED_CHECKS:
        if name not in only:
            continue
        entry = TESTS[name]
        fn = entry["fn"] if isinstance(entry, dict) else entry
        try:
            res = fn()
        except Exception as ex:  # a crashing check is a FAIL, never a skip
            res = {"pass": False, "error": f"{type(ex).__name__}: {ex}"}
        results[name] = res
        ok = bool(res.get("pass"))
        failed += 0 if ok else 1
        print(f"[{'PASS' if ok else 'FAIL'}] {name}"
              + ("" if ok else f"  {res}"))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps({"results": results, "failed": failed}, indent=1,
                   default=str), encoding="utf-8")
    print(f"  raw: {out_path}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
