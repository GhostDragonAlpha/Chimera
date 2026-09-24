"""B6 preregistration derivation -- EXACT rational arithmetic only.

Derives, from the fixture geometry and densities alone (never from any
exporter output), the predicted mass properties of each body:

  Route A (barycentric monomial moments):
      Over the standard simplex, E[l_i^2] = 1/10 and E[l_i l_j] = 1/20 (i != j),
      so for a tet with vertices p0..p3 and centroid c:
          E[x x^T] = (1/10) * sum_i p_i p_i^T + (4/5) * c c^T
          Cov      = E[x x^T] - c c^T            (per unit volume)
  Route B (centroid deviation form):
          Cov      = (1/20) * sum_i q_i q_i^T,  q_i = p_i - c
  Route C (origin second moments, body level):
          W   = sum_i m_i * E_i[x x^T]           (raw second moment about origin)
          I_c = (tr W) I - W - (tr(M c c^T)) I + M c c^T,  c = COM, M = total mass

Route A and Route B are asserted EXACTLY equal (Fractions) per cell.
Body inertia is assembled two independent ways:
  (i)  cellwise: sum_i [ (tr J_i) I - J_i + m_i (d_i^2 I - d_i d_i^T) ], d_i = c_i - COM
  (ii) origin second moments (Route C)
and asserted EXACTLY equal.

Internal identities asserted:
  - diag-sum of (tr J) I - J equals 2 tr J, per cell
  - trace(I_body) == 2 * sum_i (tr J_i + m_i |d_i|^2)
  - sum_i m_i c_i == M * COM

Outputs prereg_predictions.json: exact fraction strings + float64 values,
fixture SHA-256 hashes, and the frozen tolerance block. No exporter output
is read anywhere in this file.
"""
from __future__ import annotations

import hashlib
import json
from fractions import Fraction
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
FIX = HERE.parent / "fixtures"


def F(x) -> Fraction:
    return Fraction(x) if not isinstance(x, float) else Fraction(x)


def mat3(rows):
    return [[F(x) for x in row] for row in rows]


def m_sub(a, b):
    return [[a[i][j] - b[i][j] for j in range(3)] for i in range(3)]


def m_add(a, b):
    return [[a[i][j] + b[i][j] for j in range(3)] for i in range(3)]


def m_scale(a, s: Fraction):
    return [[a[i][j] * s for j in range(3)] for i in range(3)]


def m_trace(a) -> Fraction:
    return a[0][0] + a[1][1] + a[2][2]


def eye3():
    return [[F(1), F(0), F(0)], [F(0), F(1), F(0)], [F(0), F(0), F(1)]]


def eye_scaled(s: Fraction):
    return [[s if i == j else F(0) for j in range(3)] for i in range(3)]


def outer(u, v):
    return [[u[i] * v[j] for j in range(3)] for i in range(3)]


def m_dot(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def to_float(a):
    return np.asarray([[float(x) for x in row] for row in a], dtype=np.float64)


def vec3(v):
    return [F(x) for x in v]


def v_sub(a, b):
    return [a[i] - b[i] for i in range(3)]


def v_add(a, b):
    return [a[i] + b[i] for i in range(3)]


def v_scale(a, s: Fraction):
    return [a[i] * s for i in range(3)]


def v_dot(a, b) -> Fraction:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def tet_volume(p) -> Fraction:
    e1 = v_sub(p[1], p[0])
    e2 = v_sub(p[2], p[0])
    e3 = v_sub(p[3], p[0])
    triple = (e1[0] * (e2[1] * e3[2] - e2[2] * e3[1])
              - e1[1] * (e2[0] * e3[2] - e2[2] * e3[0])
              + e1[2] * (e2[0] * e3[1] - e2[1] * e3[0]))
    return triple / F(6)


def centroid(p):
    return v_scale(v_add(v_add(v_add(p[0], p[1]), p[2]), p[3]), Fraction(1, 4))


def route_A_cov(p) -> list:
    """E[xx^T] = (1/20) sum p p^T + (4/5) c c^T ; Cov = E - c c^T (per volume).

    From E[l_i^2] = 1/10, E[l_i l_j] = 1/20:
        E[xx^T] = (1/10) S_pp + (1/20)(16 c c^T - S_pp)
                = (1/20) S_pp + (4/5) c c^T,   S_pp = sum_i p_i p_i^T.
    """
    c = centroid(p)
    s = [[F(0)] * 3 for _ in range(3)]
    for v in p:
        s = m_add(s, outer(v, v))
    E = m_add(m_scale(s, Fraction(1, 20)), m_scale(outer(c, c), Fraction(4, 5)))
    return m_sub(E, outer(c, c))


def route_B_cov(p) -> list:
    """Cov = (1/20) sum q q^T, q_i = p_i - c (per volume)."""
    c = centroid(p)
    s = [[F(0)] * 3 for _ in range(3)]
    for v in p:
        q = v_sub(v, c)
        s = m_add(s, outer(q, q))
    return m_scale(s, Fraction(1, 20))


def route_A_E(p) -> list:
    c = centroid(p)
    s = [[F(0)] * 3 for _ in range(3)]
    for v in p:
        s = m_add(s, outer(v, v))
    return m_add(m_scale(s, Fraction(1, 20)), m_scale(outer(c, c), Fraction(4, 5)))


def load(name):
    with open(FIX / name, encoding="utf-8") as f:
        return json.load(f)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    manifest = load("manifest.json")
    partition = load("partition.json")
    groups = load("groups.json")

    vertices = {v["vertex_id"]: vec3(v["position"]) for v in partition["vertices"]}
    scale = F(partition["coordinate_frame"]["scale_to_m"])
    assert scale == F(1), "derivation assumes scale_to_m == 1"
    materials = {m["material_id"]: F(m["density_kg_m3"]) for m in partition["materials"]}
    cell_rows = {c["cell_id"]: c for c in partition["cells"]}

    bodies_out = {}
    for group in groups["body_groups"]:
        body_id = group["body_id"]
        frame = group["body_frame"]
        R = mat3(frame["domain_from_body"]["rotation"])
        origin = vec3(frame["domain_from_body"]["origin_m"])
        # authored-frame sanity, exact
        RtR = m_dot([[R[j][i] for j in range(3)] for i in range(3)], R)
        assert RtR == eye3(), f"{body_id}: R not exactly orthonormal"
        detR = (R[0][0] * (R[1][1] * R[2][2] - R[1][2] * R[2][1])
                - R[0][1] * (R[1][0] * R[2][2] - R[1][2] * R[2][0])
                + R[0][2] * (R[1][0] * R[2][1] - R[1][1] * R[2][0]))
        assert detR == F(1), f"{body_id}: det(R) != +1"

        cells = []
        for cid in sorted(group["cell_ids"]):
            row = cell_rows[cid]
            assert row["proposals"] == [row["proposals"][0]]
            region_id = row["proposals"][0]
            region = next(r for r in partition["regions"] if r["region_id"] == region_id)
            rho = materials[region["material_id"]]
            p = [v_scale(vertices[vid], scale) for vid in row["vertex_ids"]]
            V = tet_volume(p)
            assert V > 0, f"{cid}: non-positive volume"
            c = centroid(p)
            covA, covB = route_A_cov(p), route_B_cov(p)
            assert covA == covB, f"{cid}: Route A != Route B"
            cells.append({"cell_id": cid, "rho": rho, "V": V, "m": V * rho, "c": c,
                          "cov": covA, "E_origin": route_A_E(p),
                          "p": p})

        M = sum((cell["m"] for cell in cells), F(0))
        V_tot = sum((cell["V"] for cell in cells), F(0))
        mc = [(cell["m"], cell["c"]) for cell in cells]
        com = [sum((m * c[i] for m, c in mc), F(0)) / M for i in range(3)]
        # identity: sum m_i c_i == M * COM (trivially true; assert for completeness)
        assert [sum((m * c[i] for m, c in mc), F(0)) for i in range(3)] == [M * com[i] for i in range(3)]

        # (i) cellwise parallel-axis assembly
        I_cellwise = [[F(0)] * 3 for _ in range(3)]
        trace_check = F(0)
        for cell in cells:
            J = m_scale(cell["cov"], cell["m"])
            trJ = m_trace(J)
            P = m_sub(eye_scaled(trJ), J)                    # (tr J) I - J
            d = v_sub(cell["c"], com)
            d2 = v_dot(d, d)
            A = m_sub(eye_scaled(cell["m"] * d2), m_scale(outer(d, d), cell["m"]))
            assert m_trace(P) == F(2) * trJ                  # diag-sum identity
            assert m_trace(A) == F(2) * cell["m"] * d2
            trace_check += F(2) * (trJ + cell["m"] * d2)
            I_cellwise = m_add(I_cellwise, m_add(P, A))
        assert m_trace(I_cellwise) == trace_check            # trace identity

        # (ii) origin-second-moments assembly (Route C)
        W = [[F(0)] * 3 for _ in range(3)]
        for cell in cells:
            W = m_add(W, m_scale(cell["E_origin"], cell["m"]))
        cc = outer(com, com)
        I_origin = m_sub(m_sub(eye_scaled(m_trace(W)), W),
                         m_sub(eye_scaled(M * m_trace(cc)), m_scale(cc, M)))
        assert I_origin == I_cellwise, f"{body_id}: cellwise != origin-moment assembly"

        # body-frame transform (authored frame): center_b = R^T (com - o); I_b = R^T I R
        com_shift = v_sub(com, origin)
        com_body = [sum(com_shift[k] * R[k][i] for k in range(3)) for i in range(3)]
        Rt = [[R[j][i] for j in range(3)] for i in range(3)]
        I_body = m_dot(m_dot(Rt, I_cellwise), R)

        If = to_float(I_body)
        Cf = to_float(I_cellwise)
        eigvals = np.linalg.eigvalsh((If + If.T) / 2.0)
        l1, l2, l3 = sorted(eigvals)
        det_exact = (I_body[0][0] * (I_body[1][1] * I_body[2][2] - I_body[1][2] * I_body[2][1])
                     - I_body[0][1] * (I_body[1][0] * I_body[2][2] - I_body[1][2] * I_body[2][0])
                     + I_body[0][2] * (I_body[1][0] * I_body[2][1] - I_body[1][1] * I_body[2][0]))

        def fs(x: Fraction):
            return f"{x.numerator}/{x.denominator}"

        bodies_out[body_id] = {
            "mass_kg": {"fraction": fs(M), "float": float(M)},
            "volume_m3": {"fraction": fs(V_tot), "float": float(V_tot)},
            "com_domain_m": [{"fraction": fs(x), "float": float(x)} for x in com],
            "com_body_m": [{"fraction": fs(x), "float": float(x)} for x in com_body],
            "inertia_domain_com_kg_m2": [[{"fraction": fs(x), "float": float(x)} for x in row]
                                          for row in I_cellwise],
            "inertia_body_com_kg_m2": [[{"fraction": fs(x), "float": float(x)} for x in row]
                                        for row in I_body],
            "per_cell": [{"cell_id": cell["cell_id"],
                          "rho_kg_m3": {"fraction": fs(cell["rho"]), "float": float(cell["rho"])},
                          "volume_m3": {"fraction": fs(cell["V"]), "float": float(cell["V"])},
                          "mass_kg": {"fraction": fs(cell["m"]), "float": float(cell["m"])},
                          "centroid_m": [{"fraction": fs(x), "float": float(x)} for x in cell["c"]],
                          "cov_about_centroid": [[{"fraction": fs(x), "float": float(x)} for x in r]
                                                  for r in cell["cov"]]}
                         for cell in cells],
            "eigenvalues_body_sorted": [float(l1), float(l2), float(l3)],
            "triangle_margin_l1_l2_minus_l3": float(l1 + l2 - l3),
            "triangle_margin_l1_l3_minus_l2": float(l1 + l3 - l2),
            "triangle_margin_l2_l3_minus_l1": float(l2 + l3 - l1),
            "det_inertia_exact": {"fraction": fs(det_exact), "float": float(det_exact)},
            "trace_exact": {"fraction": fs(m_trace(I_body)), "float": float(m_trace(I_body))},
        }

    predictions = {
        "prereg": "B6-tensor-checks-20260924",
        "derivation": "exact Fraction arithmetic; routes A==B per cell; "
                      "cellwise parallel-axis assembly == origin-second-moment assembly",
        "input_sha256": {name: sha256_file(FIX / name)
                         for name in ("manifest.json", "partition.json", "groups.json")},
        "tolerances_frozen": {
            "A_symmetry_max_abs_asym": 1e-15,
            "B_eig_max_abs_imag": 1e-12,
            "B_min_eigenvalue_strict_positive": True,
            "B_triangle_margin_min_abs": -1e-12,
            "B_triangle_margin_fixture_strict_positive": True,
            "B_det_positive": True,
            "B_det_vs_pred_rel": 1e-12,
            "B_trace_vs_pred_rel": 1e-12,
            "B_mass_vs_pred_rel": 1e-12,
            "B_com_vs_pred_abs_m": 1e-12,
            "B_eigenvalues_vs_pred_abs": 1e-9,
            "C_recomb_max_rel_to_tensor_scale": 1e-12,
        },
        "bodies": bodies_out,
    }
    out = HERE.parent / "prereg_predictions.json"
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(predictions, f, indent=2)
        f.write("\n")
    print(f"wrote {out}")
    print("predictions_sha256", hashlib.sha256(out.read_bytes()).hexdigest())
    for body_id, b in bodies_out.items():
        print(body_id, "m =", b["mass_kg"]["fraction"],
              "com_body =", [x["fraction"] for x in b["com_body_m"]])
        print("  I_body =", [[x["fraction"] for x in row] for row in b["inertia_body_com_kg_m2"]])
        print("  eig =", b["eigenvalues_body_sorted"], "det =", b["det_inertia_exact"]["fraction"])


if __name__ == "__main__":
    main()
