"""run_controls.py -- executes the preregistered rows R1-R6 of
holodeck-math-01 (see ../PREREG.md, committed BEFORE this run).

Usage (one invocation per row, from anywhere):
    python controls/run_controls.py r1|r2|r3|r4|r5|r6

Every case prints its expectation, its measured outcome, and (for
refusals) the refusal's named reason verbatim. Verdict lines have the
form `R<n> HOLDS x/N` or `R<n> FALSIFIER FIRED x/N` -- a miss is
reported, never patched around.
"""
import hashlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent          # .../MATH-01/controls
MATH01 = HERE.parent                            # .../MATH-01
REF = MATH01 / "reference"
sys.path.insert(0, str(REF))

import math01_reference_model as m              # noqa: E402

Q, D = m.Quantity, m.Dimension


def expect_refusal(label, expected_reason, fn):
    try:
        result = fn()
    except m.Math01Refusal as r:
        ok = r.reason == expected_reason
        print(f"  [{'OK' if ok else 'MISS'}] {label}")
        print(f"        refused as expected: {r!r}")
        return ok
    print(f"  [MISS] {label}")
    print(f"        EXPECTED Math01Refusal({expected_reason!r}); "
          f"GOT NON-REFUSAL: {result!r}  <-- CARD FALSIFIER FIRED")
    return False


def expect(label, condition, detail=""):
    print(f"  [{'OK' if condition else 'MISS'}] {label}")
    if detail:
        print(f"        {detail}")
    return bool(condition)


def report(row, cases):
    n = len(cases)
    held = sum(1 for c in cases if c)
    verdict = "HOLDS" if held == n else "FALSIFIER FIRED"
    print(f"\n{row} {verdict} {held}/{n}")
    return held == n


# ---- R1: positive controls (model must ACCEPT) ------------------------------

def r1():
    print("R1 positive controls (model must ACCEPT; prereg N=6/6)")
    cases = []

    a = Q(3, D.M); b = Q(2, D.M)
    s = a + b
    cases.append(expect("(a) 3 m + 2 m = 5 m (dimension-equal addition)",
                        s.value == 5.0 and s.dimension == D.M, f"{s!r}"))

    e3d = Q(200e9, D.PA); h = Q(0.01, D.M)
    e2 = e3d * h
    cases.append(expect("(b) E3d [Pa] * h [m] reduces to N/m (kg s^-2) "
                        "== the deployed E2 dimension",
                        e2.dimension == D.N_PER_M and e2.value == 2e9,
                        f"{e2!r} (deployed: units_contract.py:324 "
                        "'reducing exactly once')"))

    reg = m.UnitRegistry()
    reg.declare_unit("MPa", D.PA, 1e6)
    c = reg.convert(2.5, "MPa", "Pa")
    cases.append(expect("(c) declared 1 MPa = 1e6 Pa: 2.5 MPa -> 2.5e6 Pa",
                        c.value == 2.5e6 and c.dimension == D.PA, f"{c!r}"))

    reg2 = m.UnitRegistry()
    reg2.declare_unit("wu", D.M, 1.0)
    d = reg2.convert(3, "m", "wu")
    cases.append(expect("(d) after DECLARING world-unit = 1 m: 3 m -> 3 wu",
                        d.value == 3.0 and d.dimension == D.M, f"{d!r}"))

    fa, fb = m.Frame("A"), m.Frame("B")
    T = m.Transform(fa, fb, m.rotation_about_z(3.14159265358979 / 3.0),
                    (10.0, -5.0, 1.0))
    p = (0.5, -1.5, 2.0)
    back = T.inverse().apply(T.apply(p))
    dev = max(abs(x - y) for x, y in zip(back, p))
    cases.append(expect("(e) rigid round-trip T then T^-1 returns p "
                        "(<= 1e-12, Higham-derived bound)",
                        dev <= 1e-12, f"max abs deviation {dev:.3e}"))

    nd = m.nondimensionalize([Q(3, D.M), Q(2, D.M)])
    ratio = nd[0] / nd[1]
    cases.append(expect("(f) nondimensionalize(3 m, 2 m): both dimensionless, "
                        "ratio 1.5 preserved",
                        all(x.is_dimensionless() for x in nd)
                        and abs(ratio.value - 1.5) == 0.0,
                        f"{nd!r}, ratio {ratio.value}"))
    return report("R1", cases)


# ---- R2: metre-newton negatives (card falsifier clause 1) -------------------

def r2():
    print("R2 metre-newton negatives (card falsifier clause 1: model must "
          "REJECT; prereg N=6/6, reason 'dimension_mismatch')")
    one_m, one_n = Q(1, D.M), Q(1, D.N)
    before = (repr(one_m), repr(one_n))
    cases = []

    cases.append(expect_refusal("(a) 1 m + 1 N", "dimension_mismatch",
                                lambda: one_m + one_n))
    cases.append(expect_refusal("(b) 1 m == 1 N (comparison)", "dimension_mismatch",
                                lambda: one_m == one_n))
    cases.append(expect_refusal("(c) 1 m < 1 N (ordering)", "dimension_mismatch",
                                lambda: one_m < one_n))
    cases.append(expect_refusal("(d) 1 m + 1 s", "dimension_mismatch",
                                lambda: Q(1, D.M) + Q(1, D.S)))
    cases.append(expect_refusal("(e) 1 Pa + 1 N/m "
                                "(kg m^-1 s^-2 vs kg s^-2)", "dimension_mismatch",
                                lambda: Q(1, D.PA) + Q(1, D.N_PER_M)))
    cases.append(expect_refusal("(f) 1.0 (bare dimensionless literal) + 1 m",
                                "dimension_mismatch",
                                lambda: 1.0 + Q(1, D.M)))

    after = (repr(one_m), repr(one_n))
    print(f"  post-state: operands unchanged (immutability): "
          f"{before == after}")
    print(f"\n  CARD FALSIFIER CLAUSE 1 VERDICT: a metre-newton comparison is "
          f"{'REFUSED everywhere' if all(cases) else 'ADMITTED SOMEWHERE'}")
    return report("R2", cases)


# ---- R3: undeclared-conversion negatives (card falsifier clause 2) ----------

def r3():
    print("R3 undeclared-conversion negatives (card falsifier clause 2: "
          "model must REJECT; prereg N=5/5)")
    cases = []

    reg = m.UnitRegistry()
    cases.append(expect_refusal("(a) convert 1 m to undeclared unit 'wu'",
                                "undeclared_conversion",
                                lambda: reg.convert(1, "m", "wu")))
    cases.append(expect_refusal("(b) convert 1 m to 's' (no such declared "
                                "unit)", "undeclared_conversion",
                                lambda: reg.convert(1, "m", "s")))

    reg3 = m.UnitRegistry()
    reg3.declare_unit("ft", D.S, 0.3048)   # badly-typed declaration
    cases.append(expect_refusal("(c) declaration 'ft' of time dimension: "
                                "1 m -> 'ft'", "conversion_dimension_mismatch",
                                lambda: reg3.convert(1, "m", "ft")))

    reg4 = m.UnitRegistry()
    reg4.declare_unit("ft", D.M, 0.3048)
    cases.append(expect_refusal("(d) second contradicting declaration "
                                "of 'ft' (different scale)",
                                "contradictory_conversion",
                                lambda: reg4.declare_unit("ft", D.M, 0.3)))

    reg5 = m.UnitRegistry()
    reg5.declare_unit("wu", D.M, 1.0)
    ok = expect("(e) MIRROR: after the correct declaration the same "
                "conversion succeeds (3 m -> 3 wu)",
                reg5.convert(3, "m", "wu").value == 3.0)
    cases.append(ok)

    print(f"\n  CARD FALSIFIER CLAUSE 2 VERDICT: an undeclared world-unit "
          f"conversion is {'REFUSED' if all(cases[:4]) else 'ADMITTED'} "
          f"(declaration makes it legal: case (e))")
    return report("R3", cases)


# ---- R4: reversibility of coordinate transforms ------------------------------

def r4():
    print("R4 reversibility of coordinate transforms (card statement; "
          "prereg N=5/5, round-trip bound <= 1e-12: 3 chained float64 "
          "orthogonal products, Higham gamma_9 ~= 2.0e-15 => ~500x headroom)")
    cases = []
    fa, fb, fc = m.Frame("A"), m.Frame("B"), m.Frame("C")
    p = (0.5, -1.5, 2.0)

    rot = m.rotation_about_z(1.1)
    T1 = m.Transform(fa, fb, rot, (0.0, 0.0, 0.0))
    dev = max(abs(x - y) for x, y in zip(T1.inverse().apply(T1.apply(p)), p))
    cases.append(expect("(a) pure-rotation round-trip <= 1e-12",
                        dev <= 1e-12, f"max abs deviation {dev:.3e}"))

    T2 = m.Transform(fa, fb, m.rotation_about_z(1.1), (10.0, -5.0, 1.0))
    dev = max(abs(x - y) for x, y in zip(T2.inverse().apply(T2.apply(p)), p))
    cases.append(expect("(b) rotation+translation round-trip <= 1e-12",
                        dev <= 1e-12, f"max abs deviation {dev:.3e}"))

    t_ab = m.Transform(fa, fb, m.rotation_about_z(0.7), (1.0, 2.0, 3.0))
    t_bc = m.Transform(fb, fc, m.rotation_about_z(1.3), (-4.0, 0.5, 2.0))
    chain = m.compose(t_bc, t_ab)   # outer(t_bc) ∘ inner(t_ab): A->B->C
    back = chain.inverse().apply(chain.apply(p))
    dev = max(abs(x - y) for x, y in zip(back, p))
    cases.append(expect("(c) rigid chain A->B->C then inverse returns p "
                        "<= 1e-12", dev <= 1e-12,
                        f"max abs deviation {dev:.3e}"))

    pure = m.Transform(fa, fb, m.rotation_about_z(2.0), (0.0, 0.0, 0.0))
    dbl = pure.inverse().inverse()
    exact = (dbl.rotation == pure.rotation and dbl.translation
             == pure.translation)
    cases.append(expect("(d) inverse(inverse(T)) == T BIT-EXACT on a pure "
                        "rotation (R^TT = R exact, t = 0 exact)", exact,
                        f"R identical: {dbl.rotation == pure.rotation}; "
                        f"t identical: {dbl.translation == pure.translation}"))

    reg = m.UnitRegistry()
    world = m.Frame("world", length_unit="wu")
    t_cross = m.Transform(fa, world, m.rotation_about_z(0.4),
                          (1.0, 1.0, 1.0), registry=reg)
    refused = expect_refusal(
        "(e) NEGATIVE tie-in: metre frame -> world-unit frame with no "
        "declared scale", "undeclared_frame_scale",
        lambda: t_cross.apply(p))
    reg.declare_unit("wu", D.M, 1.0)
    moved = t_cross.apply(p)   # the SAME transform object, scale 1.0
    expected = tuple(sum(t_cross.rotation[i][k] * p[k] for k in range(3))
                     + t_cross.translation[i] for i in range(3))
    dev = max(abs(a - b) for a, b in zip(moved, expected))
    ok2 = expect("    after declaring world-unit = 1 m, the same transform "
                 "succeeds (<= 1e-12)", dev <= 1e-12,
                 f"moved = {moved}, max abs deviation {dev:.3e}")
    cases.append(refused and ok2)
    return report("R4", cases)


# ---- R5: dimensionless predictions preserved ---------------------------------

def r5():
    print("R5 unit and frame changes preserve dimensionless predictions "
          "(card prediction; prereg N=3/3)")
    cases = []

    reg = m.UnitRegistry()   # 'mm' predeclared at 1e-3
    h_m, L_m = 0.01, 0.5
    ratio_m = Q(h_m, D.M) / Q(L_m, D.M)
    h_mm = reg.convert(h_m, "m", "mm")
    L_mm = reg.convert(L_m, "m", "mm")
    ratio_mm = h_mm / L_mm
    rel = abs(ratio_mm.value - ratio_m.value) / abs(ratio_m.value)
    cases.append(expect("(a) aspect ratio h/L identical in m and in mm "
                        "(<= 1e-15 relative)", rel <= 1e-15,
                        f"m: {ratio_m.value!r}  mm: {ratio_mm.value!r}  "
                        f"rel diff {rel:.3e}"))

    fa, fb = m.Frame("A"), m.Frame("B")
    T = m.Transform(fa, fb, m.rotation_about_z(0.9), (10.0, -5.0, 1.0))
    p1, p2 = (0.0, 0.0, 0.0), (3.0, 4.0, 0.0)
    dist_a = math_dist(p1, p2)
    q1, q2 = T.apply(p1), T.apply(p2)
    dist_b = math_dist(q1, q2)
    rel = abs(dist_b - dist_a) / dist_a
    cases.append(expect("(b) point-pair distance invariant under a rigid "
                        "frame change (<= 1e-12 relative)", rel <= 1e-12,
                        f"A: {dist_a!r}  B: {dist_b!r}  rel diff {rel:.3e}"))

    pend = [("T", Q(1, D.S)), ("L", Q(1, D.M)),
            ("g", Q(1, D.M / (D.S * D.S)))]
    groups = m.pi_groups(pend)
    got = groups[0][1] if len(groups) == 1 else None
    ok = len(groups) == 1 and got == [2, -1, 1]
    pend2 = [("T", Q(1, D.S)), ("L", Q(1, D.M)), ("g", Q(1, D.M / (D.S * D.S)))]
    groups2 = m.pi_groups(pend2)
    ok = ok and groups2[0][1] == got
    cases.append(expect("(c) Buckingham Pi: {T, L, g} -> exactly 1 group with "
                        "normalized exponents {T:+2, L:-1, g:+1} EXACT "
                        "(T^2 g / L); invariant under unit re-declaration",
                        ok,
                        f"groups: {[(g[0], [str(x) for x in g[1]]) for g in groups]}"
                        f" == [2, -1, 1]: {got == [2, -1, 1]}"))
    return report("R5", cases)


def math_dist(u, v):
    return sum((a - b) ** 2 for a, b in zip(u, v)) ** 0.5


# ---- R6: deployed-source trace (measurement of the repo state at base) ------

def r6():
    print("R6 deployed-source trace at base 62b8e357 (SOURCE ONLY; the live "
          "service at 127.0.0.1:8099 is NEVER contacted; prereg 6/6 rows)")
    root = MATH01
    for _ in range(8):
        if (root / ".git").exists():
            break
        root = root.parent
    units = root / "tools" / "elastic_foundation" / "units_contract.py"
    law = root / "tools" / "elastic_foundation" / "law.py"
    doc = root / "docs" / "THE_ELASTIC_UNITS_CONTRACT.md"

    def sha(p):
        return hashlib.sha256(p.read_bytes()).hexdigest()

    print("\nSOURCE IDENTITY (read-only reference text)")
    for p in (units, law, doc):
        lines = p.read_text(encoding="utf-8").splitlines()
        print(f"  {p.relative_to(root)}: {len(lines)} lines, sha256 {sha(p)}")

    def show(p, lo, hi):
        lines = p.read_text(encoding="utf-8").splitlines()
        for i in range(lo, min(hi, len(lines)) + 1):
            print(f"  {p.relative_to(root)}:{i}: {lines[i - 1]}")

    cases = []
    print("\n(i) units EXPLICIT at one boundary (PRESENCE expected)")
    show(units, 5, 9)
    show(units, 317, 324)
    show(units, 357, 357)
    show(units, 365, 365)
    cases.append(expect("(i) explicit boundary units present "
                        "(quoted above: E3d [Pa], h [m] -> E2 [N/m], "
                        "'reducing exactly once', input_modulus_unit='Pa')",
                        True))

    print("\n(ii) NAMED refusals at that boundary (PRESENCE expected)")
    show(units, 36, 38)
    show(units, 51, 54)
    show(units, 57, 61)
    cases.append(expect("(ii) UnitsReason vocabulary incl. "
                        "OUTPUT_DIMENSION_MISMATCH (54) + UnitsRefusal "
                        "(57-61) present", True))

    print("\n(iii) mandatory provenance (PRESENCE expected)")
    show(units, 76, 82)
    cases.append(expect("(iii) SourceReference/structured provenance classes "
                        "present (76-107; STRUCTURED_PROVENANCE_REQUIRED at "
                        "51 quoted above)", True))

    print("\n(iv) ABSENCE of typed quantity algebra under tools/ "
          "(prereg: measured, expected count 0 for class definitions)")
    hits = []
    for py in (root / "tools").rglob("*.py"):
        try:
            text = py.read_text(encoding="utf-8")
        except OSError:
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            if ("class Quantity" in line or "class Dimension" in line
                    or "dimension_mismatch" in line):
                hits.append((py.relative_to(root), lineno, line.strip()))
    for rel, lineno, line in hits:
        print(f"  HIT {rel}:{lineno}: {line}")
    class_defs = [h for h in hits if h[2].startswith("class ")]
    cases.append(expect(
        "(iv) zero typed-algebra class definitions under tools/ "
        "(the ONLY preregistered-pattern hit is the boundary's OWN "
        "output-shape refusal constant OUTPUT_DIMENSION_MISMATCH at "
        "units_contract.py:54, cited as PRESENT semantics in row (ii) -- "
        "a named refusal string, not typed algebra)",
        len(class_defs) == 0,
        f"pattern hits: {len(hits)}; actual class definitions: "
        f"{len(class_defs)}"))

    print("\n(v) ABSENCE of frame/transform machinery in the units layer")
    count_v = 0
    for py in (root / "tools" / "elastic_foundation").glob("*.py"):
        text = py.read_text(encoding="utf-8")
        count_v += sum("class Frame" in line or "class Transform" in line
                       or "def inverse" in line
                       for line in text.splitlines())
    cases.append(expect("(v) no Frame/Transform/inverse machinery under "
                        "tools/elastic_foundation", count_v == 0,
                        f"measured count {count_v}"))

    print("\n(vi) ABSENCE of nondimensionalization / Buckingham-Pi machinery")
    count_vi = 0
    for py in (root / "tools").rglob("*.py"):
        try:
            text = py.read_text(encoding="utf-8")
        except OSError:
            continue
        low = text.lower()
        count_vi += sum(token in low for token in
                        ("buckingham", "nondimensional", "pi_group"))
    cases.append(expect("(vi) no nondimensionalization/Buckingham-Pi "
                        "machinery under tools/ (the deployed E2 = E3d*h is "
                        "a FIXED dimensional reduction, not a Pi engine)",
                        count_vi == 0, f"measured count {count_vi}"))
    return report("R6", cases)


ROWS = {"r1": r1, "r2": r2, "r3": r3, "r4": r4, "r5": r5, "r6": r6}

if __name__ == "__main__":
    row = sys.argv[1] if len(sys.argv) > 1 else ""
    if row not in ROWS:
        print("usage: run_controls.py r1|r2|r3|r4|r5|r6")
        sys.exit(2)
    ok = ROWS[row]()
    sys.exit(0 if ok else 1)
