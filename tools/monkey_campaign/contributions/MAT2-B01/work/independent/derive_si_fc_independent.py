"""MAT2-B01 attempt 67fafbdd: from-scratch independent derivation (P3).

Written fresh for this attempt by the attempt agent (different author and
tooling from the original proof/author session). Pure standard library;
imports nothing from tools/; no third-party packages.

Route A (exact): monomial expansion over the reference simplex with Fraction
arithmetic.  For a tetrahedron with vertices v0..v3,

    p(u,v,w) = v0 + u*(v1-v0) + v*(v2-v0) + w*(v3-v0),
    over {u,v,w >= 0, u+v+w <= 1},  dV = |det J| du dv dw,

with the reference-simplex monomial integral

    int_T u^a v^b w^c du dv dw = a! b! c! / (a+b+c+3)!,

self-checked below against exact known values (volume 1/6, first moment
1/24).  This is a general-polynomial path, NOT the original prereg's
uniform-right-tet raw-moment shortcut and NOT any shipped code.

Route B (independent quadrature): Gauss-Legendre product rule over the Duffy
collapsed map of the unit cube onto the reference tetrahedron,
    (u,v,w) = (x, y*(1-x), z*(1-x)*(1-y)),  Jacobian (1-x)^2 (1-y),
with Legendre nodes/weights computed by this file's own Newton iteration.
8-point rule: every axis factor below is a polynomial of degree <= 7, so each
one-dimensional integral is exact and the only error is float round-off.
Different method AND different author from the frozen Hammer-Stroud route Q
and from route A.

Comparisons are against the FROZEN decimal literals copied verbatim from the
two preregistration documents (provenance recorded in
FROZEN_LITERALS_PROVENANCE).  Falsifier F-B01-3 fires if any deviation exceeds
TOL = 1e-12 (absolute where |expected| <= 1, else relative).  Falsifier
F-B01-7 (negative control) MUST fire: one perturbed literal must be rejected.
"""
import json
import math
import sys
from fractions import Fraction
from math import factorial
from pathlib import Path

TOL = 1e-12

HERE = Path(__file__).resolve().parent
FROZEN_TOOLS = HERE.parent / "frozen" / "1af0bbde" / "tools"
RUNS = HERE.parent / "runs"

FROZEN_LITERALS_PROVENANCE = (
    "SI literals: work/frozen/1af0bbde/Chimera/docs/matter/"
    "material_volume_export_proof_prereg_shared_interface.md frozen-decimals "
    "block (commit 1af0bbde blob). FC literals: .../"
    "material_volume_export_proof_prereg_frame_composition.md domain table "
    "and frozen run-expectation block (commit 1af0bbde blob).")

# ---------------------------------------------------------------- route A ---


def _ref_int(poly):
    """Exact integral of a u,v,w Fraction polynomial over the ref simplex."""
    total = Fraction(0)
    for (a, b, c), coef in poly.items():
        total += coef * Fraction(factorial(a) * factorial(b) * factorial(c),
                                 factorial(a + b + c + 3))
    return total


def _poly_mul(p, q):
    out = {}
    for (a, b, c), ca in p.items():
        for (d, e, f), cb in q.items():
            k = (a + d, b + e, c + f)
            out[k] = out.get(k, Fraction(0)) + ca * cb
    return {k: v for k, v in out.items() if v != 0}


def tet_exact(verts, rho):
    """Exact (mass, com, raw_second_about_origin, volume) for one tet."""
    v = [[Fraction(str(c)) for c in row] for row in verts]
    d = [[v[i][j] - v[0][j] for j in range(3)] for i in (1, 2, 3)]
    det = (d[0][0] * (d[1][1] * d[2][2] - d[1][2] * d[2][1])
           - d[0][1] * (d[1][0] * d[2][2] - d[1][2] * d[2][0])
           + d[0][2] * (d[1][0] * d[2][1] - d[1][1] * d[2][0]))
    jac = abs(det)
    rho = Fraction(str(rho))
    lin = [{(0, 0, 0): v[0][j], (1, 0, 0): d[0][j],
            (0, 1, 0): d[1][j], (0, 0, 1): d[2][j]} for j in range(3)]
    one = {(0, 0, 0): Fraction(1)}
    # dV = |det J| du dv dw and int_ref 1 = 1/6, so no extra factor:
    vol = jac * _ref_int(one)
    mass = vol * rho
    com = [jac * _ref_int(lin[j]) * rho / mass for j in range(3)]
    raw = [[jac * _ref_int(_poly_mul(lin[a], lin[b])) * rho
            for b in range(3)] for a in range(3)]
    return mass, com, raw, vol


def inertia_about_com(mass, com, raw):
    """I = tr(C)E - C, C = raw - m c c^T (about COM)."""
    C = [[raw[a][b] - mass * com[a] * com[b] for b in range(3)] for a in range(3)]
    tr = C[0][0] + C[1][1] + C[2][2]
    return [[tr * (1 if a == b else 0) - C[a][b] for b in range(3)]
            for a in range(3)]


# ---------------------------------------------------------------- route B ---
def gauss_legendre(n):
    nodes, weights = [], []
    for i in range(1, n + 1):
        # standard initial guess for the i-th root of P_n
        x = math.cos(math.pi * (i - 0.25) / (n + 0.25))
        dp = 1.0
        for _ in range(100):
            p0, p1 = 1.0, x
            for k in range(2, n + 1):
                p0, p1 = p1, ((2 * k - 1) * x * p1 - (k - 1) * p0) / k
            dp = n * (x * p1 - p0) / (x * x - 1.0)
            dx = p1 / dp
            x -= dx
            if abs(dx) < 1e-16:
                break
        nodes.append(x)
        weights.append(2.0 / ((1.0 - x * x) * dp * dp))
    return nodes, weights


_GL = gauss_legendre(8)


def tet_quad(verts, rho):
    """Route B float (mass, com, raw_second_about_origin, volume) for one tet.

    The Gauss-Legendre rule is defined on [-1,1]; the Duffy map needs [0,1],
    so nodes are affinely mapped and weights halved per axis."""
    v = [[float(c) for c in row] for row in verts]
    d = [[v[i][j] - v[0][j] for j in range(3)] for i in (1, 2, 3)]
    det = (d[0][0] * (d[1][1] * d[2][2] - d[1][2] * d[2][1])
           - d[0][1] * (d[1][0] * d[2][2] - d[1][2] * d[2][0])
           + d[0][2] * (d[1][0] * d[2][1] - d[1][1] * d[2][0]))
    jac = abs(det)
    rho_f = float(Fraction(str(rho)))
    xs = [(0.5 * (node + 1.0), 0.5 * w) for node, w in zip(_GL[0], _GL[1])]
    m0 = 0.0
    m1 = [0.0, 0.0, 0.0]
    m2 = [[0.0] * 3 for _ in range(3)]
    for x, wx in xs:
        for y, wy in xs:
            for z, wz in xs:
                u = x
                vv = y * (1 - x)
                ww = z * (1 - x) * (1 - y)
                j = (1 - x) ** 2 * (1 - y)
                wgt = wx * wy * wz * j
                p = [v[0][k] + u * d[0][k] + vv * d[1][k] + ww * d[2][k]
                     for k in range(3)]
                m0 += wgt
                for a in range(3):
                    m1[a] += wgt * p[a]
                    for b in range(3):
                        m2[a][b] += wgt * p[a] * p[b]
    vol = m0 * jac              # int over ref simplex of 1, mapped
    mass = vol * rho_f
    com = [m1[a] * jac * rho_f / mass for a in range(3)]
    raw = [[m2[a][b] * jac * rho_f for b in range(3)] for a in range(3)]
    return mass, com, raw, vol


# ------------------------------------------------------------- comparator ---
def dev(expected, observed):
    e, o = float(expected), float(observed)
    scale = 1.0 if abs(e) <= 1.0 else abs(e)
    return abs(o - e) / scale


def compare(tag, expected, observed, failures):
    d = dev(expected, observed)
    ok = d <= TOL
    if not ok:
        failures.append((tag, expected, observed, d))
    return ok, d


def perturb(x):
    return float(x) * (1.0 + 1e-6)


# ----------------------------------------------------- fixture reading ------
def load_fixture_set(tools_dir, prefix, groups_suffix="groups_example"):
    """My own reader for the frozen fixture documents.

    Returns (cells, groups) where cells maps cell_id ->
    {verts, density, region} and groups maps body_id -> [cell_id]."""
    man = load_json(tools_dir / f"{prefix}_manifest_example.json")
    part = load_json(tools_dir / f"{prefix}_partition_example.json")
    regions = {r["region_id"]: r for r in part["regions"]}
    materials = {m["material_id"]: m for m in part["materials"]}
    verts = {v["vertex_id"]: v["position"] for v in man["vertices"]}
    cells = {}
    for c in part["cells"]:
        region_id = c["proposals"][0]
        region = regions[region_id]
        mat = materials[region["material_id"]]
        cells[c["cell_id"]] = {
            "verts": [verts[i] for i in c["vertex_ids"]],
            "density": mat["density_kg_m3"],
            "region": region_id,
        }
    grp = load_json(tools_dir / f"{prefix}_{groups_suffix}.json")
    groups = {g["body_id"]: g["cell_ids"] for g in grp["body_groups"]}
    return cells, groups


def load_json(p):
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def aggregate_exact(cells, wanted):
    mt = Fraction(0)
    mct = [Fraction(0)] * 3
    rawt = [[Fraction(0)] * 3 for _ in range(3)]
    for cid in wanted:
        c = cells[cid]
        m, com, raw, _v = tet_exact(c["verts"], c["density"])
        mt += m
        for a in range(3):
            mct[a] += m * com[a]
            for b in range(3):
                rawt[a][b] += raw[a][b]
    com = [mct[a] / mt for a in range(3)]
    return mt, com, inertia_about_com(mt, com, rawt)


def aggregate_quad(cells, wanted):
    mt = 0.0
    mct = [0.0] * 3
    rawt = [[0.0] * 3 for _ in range(3)]
    for cid in wanted:
        c = cells[cid]
        m, com, raw, _v = tet_quad(c["verts"], c["density"])
        mt += m
        for a in range(3):
            mct[a] += m * com[a]
            for b in range(3):
                rawt[a][b] += raw[a][b]
    com = [mct[a] / mt for a in range(3)]
    return mt, com, inertia_about_com(mt, com, rawt)


def recombine(props_list):
    """Parallel-axis recombination of (mass, com, I) tuples about the combined
    COM:  I_c[a][b] = sum I[a][b] + m*(|d|^2*delta_ab - d_a*d_b)."""
    m_c = sum(p[0] for p in props_list)
    com_c = [sum(p[0] * p[1][a] for p in props_list) / m_c for a in range(3)]
    I_c = [[type(m_c)(0)] * 3 for _ in range(3)]
    for m, com, I in props_list:
        d = [com[a] - com_c[a] for a in range(3)]
        d2 = d[0] * d[0] + d[1] * d[1] + d[2] * d[2]
        for a in range(3):
            for b in range(3):
                I_c[a][b] += I[a][b] + m * ((d2 if a == b else 0) - d[a] * d[b])
    return m_c, com_c, I_c


def check_props(tag_prefix, frozen, props, route, report, failures):
    m, com, I = props
    rows = report[f"route{route}_vs_frozen"]
    entries = [(f"{tag_prefix}.mass", frozen["mass"], m)]
    entries += [(f"{tag_prefix}.com[{k}]", frozen["com"][k], com[k])
                for k in range(3)]
    entries += [(f"{tag_prefix}.I[{a}][{b}]", frozen["I"][a][b], I[a][b])
                for a in range(3) for b in range(3)]
    for tag, exp, obs in entries:
        ok, d = compare(tag, exp, obs, failures)
        rows.append((tag, str(exp), float(obs), d, ok))


# ------------------------------------------------------------------- main ---
def main():
    failures = []
    report = {"routeA_vs_frozen": [], "routeB_vs_frozen": [],
              "negative_control": None, "tol": TOL}

    # ---- SI coupon (frozen decimals, prereg 1/2) --------------------------
    si_cells, si_groups = load_fixture_set(
        FROZEN_TOOLS, "material_volume_shared_interface")
    si_frozen = {
        "si-body-A": {"mass": 2.0, "com": [0.25, 0.25, 0.25],
                      "I": [[0.15, 0.025, 0.025], [0.025, 0.15, 0.025],
                            [0.025, 0.025, 0.15]]},
        "si-body-B": {"mass": 1.0, "com": [0.25, 0.25, -0.25],
                      "I": [[0.075, 0.0125, -0.0125], [0.0125, 0.075, -0.0125],
                            [-0.0125, -0.0125, 0.075]]},
        "combined": {"mass": 3.0, "com": [0.25, 0.25, 0.08333333333333333],
                     "I": [[0.39166666666666666, 0.0375, 0.0125],
                           [0.0375, 0.39166666666666666, 0.0125],
                           [0.0125, 0.0125, 0.225]]},
    }
    si_exact = {b: aggregate_exact(si_cells, cw) for b, cw in si_groups.items()}
    si_exact["combined"] = recombine(
        [si_exact[b] for b in ("si-body-A", "si-body-B")])
    si_quad = {b: aggregate_quad(si_cells, cw) for b, cw in si_groups.items()}
    si_quad["combined"] = recombine(
        [si_quad[b] for b in ("si-body-A", "si-body-B")])
    for body, f in si_frozen.items():
        check_props(body, f, si_exact[body], "A", report, failures)
        check_props(body, f, si_quad[body], "B", report, failures)

    # ---- negative control F-B01-7: MUST reject a perturbed literal --------
    bad = perturb(si_frozen["si-body-A"]["mass"])
    ok_ctrl, d_ctrl = compare("CTRL:si-body-A.mass", bad, si_exact["si-body-A"][0], [])
    report["negative_control"] = {
        "perturbed_expected": bad,
        "observed": float(si_exact["si-body-A"][0]),
        "deviation": d_ctrl,
        "rejected_by_comparator": not ok_ctrl,
        "F-B01-7_ok": not ok_ctrl,
    }

    # ---- FC coupon domain rows (prereg 2/2 domain table) ------------------
    fc_cells, fc_groups = load_fixture_set(
        FROZEN_TOOLS, "material_volume_frame_composition",
        groups_suffix="groups_shared_example")
    fc_exact = {b: aggregate_exact(fc_cells, cw) for b, cw in fc_groups.items()}
    fc_frozen_domain = {
        "fc-body-A": {"mass": 2.0, "com": [0.25, 0.25, 0.25],
                      "I": [[3 / 20, 1 / 40, 1 / 40], [1 / 40, 3 / 20, 1 / 40],
                            [1 / 40, 1 / 40, 3 / 20]]},
        "fc-body-B": {"mass": 1.0, "com": [2.25, -0.75, 0.75],
                      "I": [[3 / 40, 1 / 80, 1 / 80], [1 / 80, 3 / 40, 1 / 80],
                            [1 / 80, 1 / 80, 3 / 40]]},
    }
    for body, f in fc_frozen_domain.items():
        check_props(body, f, fc_exact[body], "A", report, failures)
    fc_combined = recombine([fc_exact["fc-body-A"], fc_exact["fc-body-B"]])
    fc_combined_frozen = {
        "mass": 3.0, "com": [11 / 12, -1 / 12, 5 / 12],
        "I": [[127 / 120, 329 / 240, -151 / 240],
              [329 / 240, 367 / 120, 89 / 240],
              [-151 / 240, 89 / 240, 427 / 120]]}
    check_props("fc-combined", fc_combined_frozen, fc_combined, "A",
                report, failures)

    # ---- reference-formula self-tests -------------------------------------
    assert _ref_int({(0, 0, 0): Fraction(1)}) == Fraction(1, 6)
    assert _ref_int({(1, 0, 0): Fraction(1)}) == Fraction(1, 24)

    report["failures"] = [
        {"tag": t, "expected": str(e), "observed": str(o), "dev": d}
        for t, e, o, d in failures]
    report["F-B01-3_fired"] = bool(failures)
    report["frozen_literals_provenance"] = FROZEN_LITERALS_PROVENANCE
    report["counts"] = {"routeA": len(report["routeA_vs_frozen"]),
                        "routeB": len(report["routeB_vs_frozen"])}

    RUNS.mkdir(parents=True, exist_ok=True)
    with open(RUNS / "derive_si_fc_independent_result.json", "w",
              encoding="utf-8", newline="\n") as fh:
        json.dump(report, fh, indent=1)

    print(f"route A checks: {report['counts']['routeA']}, "
          f"route B checks: {report['counts']['routeB']}")
    print(f"F-B01-3 fired: {report['F-B01-3_fired']}")
    print(f"F-B01-7 negative control rejected perturbation: "
          f"{report['negative_control']['rejected_by_comparator']}")
    if failures:
        for t, e, o, d in failures:
            print(f"FAIL {t}: expected {e} observed {o} dev {d:.3e}")
        return 1
    if not report["negative_control"]["rejected_by_comparator"]:
        print("FAIL negative control: comparator accepted a perturbed value")
        return 2
    print("ALL FROZEN LITERALS REPRODUCED (routes A and B); negative control OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
