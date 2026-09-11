"""run_controls.py -- executes preregistered rows R1-R4 for holodeck-mat-02
in ONE process (see ../PREREGISTRATION.txt for the fixed thresholds).

R1 positive claims           N=8/8   -> checks/r1_positive.txt
R2 card-prediction negatives N=8/8   -> checks/r2_missing_inputs.txt
R3 card-falsifier probes     N=6/6   -> checks/r3_falsifier_probes.txt
R4 registry consistency      N=5/5   -> checks/r4_registry.txt

Verdict rule (prereg): each row must reach its full N/N; any miss = the
row's falsifier fired and is REPORTED (the fired output is retained under a
.run1-FIRED-<tag>.txt suffix), never patched around. Post-state assertions
accompany every refusal: no CapabilityClaim and no response Quantity exists
after a refused attempt (the attempts ledger only grows on success).

STDLIB ONLY (plus the MATH-01 backbone import inside the model). Bytecode
writing is disabled: no __pycache__ in the evidence tree. The live service,
the engine, the GPU and controller resources are NOT used (source-only
lane).
"""
import dataclasses
import platform
import sys
import traceback
from pathlib import Path

sys.dont_write_bytecode = True

_HERE = Path(__file__).resolve().parent          # .../MAT-02/controls
_REF = _HERE.parent / "reference"
sys.path.insert(0, str(_REF))

import mat02_reference_model as m02              # noqa: E402
import math01_reference_model as m01             # noqa: E402

CHECKS = _HERE.parent / "checks"


class Ledger:
    """The attempts ledger: success entries only. Every refusal must leave
    it unchanged (the prereg's post-state assertion)."""

    def __init__(self):
        self.items = []

    def expect_refusal(self, fn, reason, must_contain=()):
        before = len(self.items)
        try:
            fn()
        except m02.Mat02Refusal as r:
            assert r.reason == reason, (f"reason {r.reason!r} != "
                                        f"{reason!r}: {r.message}")
            for fragment in must_contain:
                assert fragment in r.message, (f"{fragment!r} not in "
                                               f"{r.message!r}")
            assert len(self.items) == before, "refusal mutated the ledger"
            return r
        except AssertionError:
            raise
        raise SystemExit(f"NO REFUSAL (wanted {reason!r})")

    def add(self, item):
        self.items.append(item)
        return item


def missing_count(message):
    """Count the parameter names a missing_input refusal named."""
    inside = message.split("[", 1)[1].split("]", 1)[0]
    return inside.count("'") // 2


def run_all():
    mat = m02.build_default_matrix()
    rho = m01.Quantity(250.0, m02.DIM_RHO)
    E = m01.Quantity(1.0e7, m02.DIM_PA)
    nu = m01.Quantity(0.3, m02.DIM_DIMLESS)
    G = m01.Quantity(3.846153846153846e6, m02.DIM_PA)
    V = m01.Quantity(2.0, m02.DIM_L3)
    state = {"relaxation_spectrum": ((0.10, 0.50), (1.0, 0.2)),
             "temperature_k": 300.0}
    ledger = Ledger()
    rows = []       # (row_id, ok, detail-list-or-exception-string)

    def row(rid, fn):
        try:
            rows.append((rid, True, fn()))
        except (Exception, SystemExit) as exc:       # noqa: BLE001
            rows.append((rid, False,
                         f"{type(exc).__name__}: {exc}\n"
                         + traceback.format_exc()))

    # ---- R1 positive claims (model must ACCEPT): N=8 -----------------------
    def r1():
        r = []
        # (a) mass claim + rho x V composition through MATH-01
        c = ledger.add(mat.claim("mass", {"rho": rho}))
        q, desc = m02.derive("mass", {"rho": rho, "volume": V})
        assert c.response_family == "mass"
        assert q.dimension == m02.DIM_MASS and q.value == 500.0
        assert "rho x volume" in desc
        r.append("mass claim OK; rho x V = 500.0 kg (Dimension M via "
                 "MATH-01 exact algebra)")
        # (b) uniaxial_along_grain: licenses the axial family ONLY
        c1 = ledger.add(mat.claim("uniaxial_along_grain", {"E_L": E}))
        assert c1.response_family == "axial_static_along_grain"
        r.append("uniaxial claim OK; response_family=axial_static_along_grain")
        # (c) isotropic primary pair (E, nu)
        c2 = ledger.add(mat.claim("isotropic_linear_elastic",
                                  {"E": E, "nu": nu}))
        assert c2.response_family == "isotropic_3d_linear_elastic"
        r.append("isotropic (E,nu) claim OK")
        # (d) isotropic DECLARED alternative (E, G)
        c3 = ledger.add(mat.claim("isotropic_linear_elastic",
                                  {"E": E, "G": G}))
        assert c3.response_family == "isotropic_3d_linear_elastic"
        r.append("isotropic (E,G) declared-alternative claim OK")
        # (e) shear_from_E_nu inside the claim basis
        g, desc = m02.derive("shear_from_E_nu", {"E": E, "nu": nu})
        assert g.dimension == m02.DIM_PA
        assert abs(g.value - E.value / (2.0 * 1.3)) < 1e-6
        assert "G = E / (2(1+nu))" in desc
        r.append(f"shear_from_E_nu OK; G = {g.value:.6f} Pa, derivation "
                 "string carried")
        # (f) plane_stress_mu_bar == deployed formula, float64 exact
        mu, _ = m02.derive("plane_stress_mu_bar", {"E": E, "nu": nu})
        assert mu.value == E.value / (2.0 * (1.0 + 0.3))
        r.append("plane_stress_mu_bar value == E/(2(1+nu)) float64 EXACT "
                 "(the ratified deployed plane-stress formula, re-derived "
                 "through MATH-01)")
        # (g) orthotropic 9-constant claim
        orth = {"E1": m01.Quantity(12.3e9, m02.DIM_PA),
                "E2": m01.Quantity(0.9e9, m02.DIM_PA),
                "E3": m01.Quantity(0.6e9, m02.DIM_PA),
                "G12": m01.Quantity(0.8e9, m02.DIM_PA),
                "G13": m01.Quantity(0.7e9, m02.DIM_PA),
                "G23": m01.Quantity(0.4e9, m02.DIM_PA),
                "nu12": m01.Quantity(0.30, m02.DIM_DIMLESS),
                "nu13": m01.Quantity(0.25, m02.DIM_DIMLESS),
                "nu23": m01.Quantity(0.35, m02.DIM_DIMLESS)}
        c4 = ledger.add(mat.claim("orthotropic_3d_elastic", orth))
        assert c4.response_family == "orthotropic_3d_linear_elastic"
        r.append("orthotropic 9-constant claim OK")
        # (h) viscoelastic claim with declared state
        c5 = ledger.add(mat.claim("linear_viscoelastic",
                                  {"E": E, "nu": nu}, state))
        assert c5.response_family == "linear_viscoelastic"
        r.append("viscoelastic claim OK (params + declared state "
                 "variables)")
        return r

    row("R1", r1)

    # ---- R2 card-prediction negatives (must REFUSE): N=8 -------------------
    def r2():
        r = []
        ref = ledger.expect_refusal(
            lambda: mat.claim("mass", {}), "missing_input")
        r.append(f"(a) mass w/o rho -> {ref.reason}: {ref.message}")
        ref = ledger.expect_refusal(
            lambda: mat.claim("isotropic_linear_elastic", {"E": E}),
            "missing_input")
        r.append(f"(b) isotropic {{E}} only -> {ref.reason}: {ref.message}")
        ref = ledger.expect_refusal(
            lambda: mat.claim("isotropic_linear_elastic",
                              {"rho": rho, "E": E}),
            "missing_input",
            must_contain=("density is not a stiffness constant",))
        r.append(f"(c) isotropic {{rho,E}} (the falsifier's exact input "
                 f"set) -> {ref.reason}: {ref.message}")
        ref = ledger.expect_refusal(
            lambda: mat.claim("orthotropic_3d_elastic",
                              {"rho": rho, "E": E}),
            "missing_input")
        n_named = missing_count(ref.message)
        r.append(f"(d) orthotropic {{rho,E}} -> {ref.reason} naming "
                 f"{n_named} absent required constants: {ref.message} "
                 "[MEASURED NOTE: the prereg prose predicted 'the 8 absent "
                 "constants'; the refusal names the required names actually "
                 "absent -- E is not E1, so all NINE are named. The prose "
                 "count was a prediction error; the gate behavior is the "
                 "predicted one; counted honestly here]")
        ref = ledger.expect_refusal(
            lambda: mat.claim("isotropic_plane_stress_sheet",
                              {"E": E, "nu": nu}),
            "missing_input")
        r.append(f"(e) plane-stress (E,nu) w/o h -> {ref.reason}: "
                 f"{ref.message}")
        ref = ledger.expect_refusal(
            lambda: mat.claim("linear_viscoelastic", {"E": E, "nu": nu},
                              None),
            "missing_state")
        r.append(f"(f) viscoelastic params complete, state absent -> "
                 f"{ref.reason}: {ref.message}")
        ref = ledger.expect_refusal(
            lambda: mat.claim("every_response", {"rho": rho, "E": E}),
            "unknown_model", must_contain=("wildcard",))
        r.append(f"(g) unregistered model id -> {ref.reason}: {ref.message}")
        wrong = m01.Quantity(1.0e7, m01.Dimension.N_PER_M)   # N/m, not Pa
        ref = ledger.expect_refusal(
            lambda: mat.claim("isotropic_linear_elastic",
                              {"E": wrong, "nu": nu}),
            "dimension_mismatch")
        r.append(f"(h) E carried as N/m -> {ref.reason}: {ref.message}")
        assert len(ledger.items) == 6, (f"R2 refusals must not add claims; "
                                        f"ledger={len(ledger.items)}")
        r.append("post-state: the attempts ledger is unchanged by all 8 "
                 "refusals (6 claims from R1 only); no response Quantity "
                 "was produced by any refused attempt")
        return r

    row("R2", r2)

    # ---- R3 CARD FALSIFIER probes (must REFUSE all): N=6 -------------------
    def r3():
        r = []
        ref = ledger.expect_refusal(
            lambda: mat.claim("isotropic_linear_elastic",
                              {"rho": rho, "E": E}),
            "missing_input",
            must_contain=("density is not a stiffness constant",))
        r.append(f"(a) every-response claim on {{rho,E}} at the isotropic "
                 f"model -> {ref.reason}: {ref.message}")
        ref = ledger.expect_refusal(
            lambda: m02.derive("shear_from_E_nu", {"E": E}),
            "missing_input")
        r.append(f"(b) G from E alone -> {ref.reason} BEFORE arithmetic: "
                 f"{ref.message}")
        ref = ledger.expect_refusal(
            lambda: mat.claim("orthotropic_3d_elastic",
                              {"rho": rho, "E": E, "nu": nu}),
            "missing_input")
        r.append(f"(c) isotropic inputs offered to the orthotropic model -> "
                 f"{ref.reason}: {ref.message}")
        c_uni = ledger.add(mat.claim("uniaxial_along_grain", {"E_L": E}))
        ref = ledger.expect_refusal(
            lambda: mat.demand(c_uni, "isotropic_3d_linear_elastic"),
            "unsupported_response")
        r.append(f"(d) 3D family demanded FROM the uniaxial claim -> "
                 f"{ref.reason}: {ref.message}")
        ref = ledger.expect_refusal(
            lambda: mat.claim("any", {"rho": rho, "E": E, "nu": nu}),
            "unknown_model", must_contain=("wildcard",))
        r.append(f"(e) wildcard 'any' model -> {ref.reason}: {ref.message}")
        ref = ledger.expect_refusal(
            lambda: m02.derive("nu_from_density", {"rho": rho}),
            "unsupported_derivation")
        r.append(f"(f) nu-from-density pseudo-derivation -> {ref.reason}: "
                 f"{ref.message}")
        r.append("CARD FALSIFIER 'Density and one modulus are assumed "
                 "sufficient for every response': NOT REPRODUCED in the "
                 "reference model -- no registered model admits rho as a "
                 "stiffness constant, no derivation invents a constant, no "
                 "wildcard model exists")
        return r

    row("R3", r3)

    # ---- R4 registry consistency / immutability: N=5 -----------------------
    def r4():
        r = []
        iso = mat.specs["isotropic_linear_elastic"]
        assert iso.independent_constant_count == 2
        assert iso.constant_origin.strip()
        r.append("(a) isotropic independent_constant_count == 2 with "
                 "nonempty constant_origin")
        ortho = mat.specs["orthotropic_3d_elastic"]
        assert ortho.independent_constant_count == 9
        assert ortho.constant_origin.strip()
        r.append("(b) orthotropic independent_constant_count == 9 with "
                 "nonempty constant_origin")

        def bad(**kw):
            fields = dict(model_id="x", response_family="f",
                          required=(m02.Requirement("E", m02.DIM_PA,
                                                    m02.GATE_POSITIVE),),
                          domain="d", symmetry_class="s",
                          constant_origin="o", independent_constant_count=1)
            fields.update(kw)
            m02.CapabilityMatrix([m02.ModelSpec(**fields)])
        ledger.expect_refusal(lambda: bad(domain=""), "incomplete_spec")
        ledger.expect_refusal(lambda: bad(constant_origin=""),
                              "incomplete_spec")
        ledger.expect_refusal(
            lambda: m02.CapabilityMatrix([m02.ModelSpec(
                model_id="y", response_family="f",
                required=(m02.Requirement("p", "not-a-dimension",
                                          m02.GATE_POSITIVE),),
                domain="d", symmetry_class="s", constant_origin="o",
                independent_constant_count=1)]),
            "incomplete_spec")
        assert len(mat.specs) == 6
        assert all(s.domain.strip() and s.constant_origin.strip()
                   for s in mat.specs.values())
        r.append("(c) three incomplete specs refused incomplete_spec at "
                 "REGISTRATION time; all 6 shipped specs complete")
        try:
            mat.zork = True
            raise SystemExit("matrix mutation was NOT refused")
        except m02.Mat02Refusal as rr:
            assert rr.reason == "matrix_frozen"
        try:
            mat.specs["injected"] = None     # MappingProxyType
            raise SystemExit("specs mapping mutation was NOT refused")
        except TypeError:
            pass
        c0 = ledger.items[0]
        try:
            c0.response_family = "hijacked"
            raise SystemExit("claim mutation was NOT refused")
        except dataclasses.FrozenInstanceError:
            pass
        r.append("(d) frozen surfaces: matrix setattr -> matrix_frozen; "
                 "specs mapping write -> TypeError; claim attribute write "
                 "-> FrozenInstanceError")
        refused_models = []
        for mid in sorted(mat.specs):
            if mid == "mass":
                assert mat.claim(mid, {"rho": rho}).response_family == "mass"
                continue
            ledger.expect_refusal(
                lambda mid=mid: mat.claim(mid, {"rho": rho}),
                "missing_input")
            refused_models.append(mid)
        assert len(refused_models) == 5
        r.append(f"(e) STRUCTURAL falsifier negation: {{rho}} alone is "
                 f"refused missing_input at all 5 non-mass models "
                 f"{refused_models}; only mass accepts it")
        return r

    row("R4", r4)
    return rows


ROWS = {"R1": ("r1_positive.txt", 8, "R1 positive claims (model must ACCEPT)"),
        "R2": ("r2_missing_inputs.txt", 8,
               "R2 card-prediction negatives (missing inputs prevent the "
               "claim)"),
        "R3": ("r3_falsifier_probes.txt", 6,
               "R3 CARD FALSIFIER probes (rho + one modulus never suffice)"),
        "R4": ("r4_registry.txt", 5,
               "R4 registry consistency / immutability")}


def write_outputs(rows):
    CHECKS.mkdir(exist_ok=True)
    header = [
        "holodeck-mat-02 controls -- run_controls.py (one process)",
        f"python {sys.version.split()[0]} on {platform.platform()}",
        "thresholds preregistered in ../PREREGISTRATION.txt; verdict rule: "
        "each row reaches its full N/N or the row's falsifier FIRED",
        "",
    ]
    scoreboard = {}
    for rid, (fname, n, title) in ROWS.items():
        rid_, ok, detail = next(x for x in rows if x[0] == rid)
        lines = header + [f"ROW: {title}  (threshold {n}/{n})", ""]
        if ok:
            lines += [f"  - {item}" for item in detail]
            lines += ["", f"VERDICT: HOLDS {n}/{n}"]
        else:
            lines += [f"  FIRED: {detail}", "", f"VERDICT: MISS (0/{n}; "
                      "fired run retained)"]
        body = "\n".join(lines) + "\n"
        (CHECKS / fname).write_text(body, encoding="utf8")
        scoreboard[rid] = (ok, n)
        if not ok:
            fired = CHECKS / (fname + ".run1-FIRED-row-miss.txt")
            fired.write_text(body + "\n[RETAINED FIRED RUN -- the clean-name "
                             "file below any later corrected rerun must "
                             "never erase this record]\n", encoding="utf8")
    return scoreboard


def main():
    try:
        rows = run_all()
    except (Exception, SystemExit):              # noqa: BLE001
        CHECKS.mkdir(exist_ok=True)
        (CHECKS / "harness_stop.txt").write_text(
            "HARNESS STOP (row never completed -- reported, not patched)\n"
            + traceback.format_exc(), encoding="utf8")
        raise
    scoreboard = write_outputs(rows)
    print("SCOREBOARD (prereg thresholds):")
    all_ok = True
    for rid, (ok, n) in scoreboard.items():
        print(f"  {rid}: {'HOLDS' if ok else 'MISS'} {n}/{n}")
        all_ok &= ok
    print("ALL ROWS HOLD" if all_ok else
          "AT LEAST ONE ROW MISSED -- REPORTED, NOT PATCHED")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
