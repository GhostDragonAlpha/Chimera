"""Exact-rational oracle for the material-volume integration model.

Implements EXACTLY the formulas documented in
Chimera/docs/matter/material_volume_compiler.md ("Derivation") and coded in
material_volume.py / material_volume_body_export.py, in Fraction arithmetic on
the exact float64 inputs. Every formula here is polynomial in the inputs, so
Fraction evaluation is EXACT: measured differences vs the float64 code are pure
implementation roundoff.

  V_t = det([x1-x0, x2-x0, x3-x0]) / 6
  m_t = rho_t * V_t
  c_t = sum_i x_i / 4
  C   = sum(m_t c_t) / M
  Q_t = (m_t/20) * sum_i (x_i - c_t)(x_i - c_t)^T
  I_C = sum_t [ trace(Q_t) I - Q_t + m_t((d.d) I - d d^T) ],  d_t = c_t - C
"""
from fractions import Fraction as F
import math

U = 2.0 ** -53                      # unit roundoff
EPS = 2.0 * U                       # np.finfo(float64).eps
G = 64.0 * EPS                      # declared nondegeneracy gate (compiler doc)


def _det3(d1, d2, d3):
    return (d1[0] * (d2[1] * d3[2] - d2[2] * d3[1])
            - d1[1] * (d2[0] * d3[2] - d2[2] * d3[0])
            + d1[2] * (d2[0] * d3[1] - d2[1] * d3[0]))


def _sub(a, b):
    return [a[k] - b[k] for k in range(3)]


def oracle(vertices, tets, densities):
    """Exact masses/COM/inertia. vertices: (n,3) floats; tets: (n,4) ints;
    densities: (n,) floats. Returns floats + exact Fractions."""
    V = [[F(x) for x in row] for row in vertices]
    vols, masses, cents = [], [], []
    for tet, rho in zip(tets, densities):
        p = [V[int(i)] for i in tet]
        d1, d2, d3 = (_sub(p[1], p[0]), _sub(p[2], p[0]), _sub(p[3], p[0]))
        det = _det3(d1, d2, d3)
        vol = det / F(6)
        m = F(rho) * vol
        c = [(p[0][k] + p[1][k] + p[2][k] + p[3][k]) / F(4) for k in range(3)]
        vols.append(vol); masses.append(m); cents.append(c)
    total_v = sum(vols, F(0))
    total_m = sum(masses, F(0))
    com = [sum((masses[t] * cents[t][k] for t in range(len(masses))), F(0)) / total_m
           for k in range(3)]
    I = [[F(0)] * 3 for _ in range(3)]
    for tet, rho, vol, m, c in zip(tets, densities, vols, masses, cents):
        p = [V[int(i)] for i in tet]
        q = [[F(0)] * 3 for _ in range(3)]          # Q_t about c_t
        for xi in p:
            l = _sub(xi, c)
            for a in range(3):
                for b in range(3):
                    q[a][b] += (m / F(20)) * l[a] * l[b]
        d = _sub(c, com)
        dd = sum(d[k] * d[k] for k in range(3))
        tr = q[0][0] + q[1][1] + q[2][2]
        for a in range(3):
            for b in range(3):
                I[a][b] += (tr if a == b else F(0)) - q[a][b] \
                    + m * ((dd if a == b else F(0)) - d[a] * d[b])
    return {
        "volume": float(total_v), "mass": float(total_m),
        "com": [float(x) for x in com],
        "inertia": [[float(x) for x in row] for row in I],
        "exact": {"volume": total_v, "mass": total_m, "com": com, "inertia": I},
    }


def fixture_shape(vertices, tets):
    """Exact delta = |det|/max_edge^3 per cell (min over cells), max |coord|,
    max edge length — the quantities the frozen bounds are written against."""
    V = [[F(x) for x in row] for row in vertices]
    delta_min = None
    scale_max = 0.0
    for tet in tets:
        p = [V[int(i)] for i in tet]
        d = [_sub(p[1], p[0]), _sub(p[2], p[0]), _sub(p[3], p[0])]
        det = abs(float(_det3(*d)))
        sq = []
        edges = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]
        for i, j in edges:
            e = _sub(p[j], p[i])
            sq.append(float(sum(x * x for x in e)))
        scale = math.sqrt(max(sq))
        scale_max = max(scale_max, scale)
        delta = det / scale ** 3
        delta_min = delta if delta_min is None else min(delta_min, delta)
    x_max = max(abs(float(x)) for row in vertices for x in row)
    return {"delta": delta_min, "scale": scale_max, "x_max": x_max}


def bounds_for(delta, scale, x_max):
    """Frozen per-rung bounds from PREREGISTRATION.md section 2.
    delta == 0 (collapsed/degenerate fixture) => bounds undefined (None)."""
    if delta is None or delta <= 0.0:
        return {"V_rel": None, "M_rel": None,
                "com_abs": None, "I_rel": None}
    return {
        "V_rel": 20.0 * U + 12.0 * U / delta,
        "M_rel": 20.0 * U + 12.0 * U / delta,
        "com_abs": 6.0 * U * max(x_max, scale, 1.0),
        "I_rel": 30.0 * U * (1.0 + x_max),
    }


def rel_fro(a, b):
    """|A-B|_F / |B|_F for nested 3x3 lists."""
    num = math.sqrt(sum((float(a[i][j]) - float(b[i][j])) ** 2
                        for i in range(3) for j in range(3)))
    den = math.sqrt(sum(float(b[i][j]) ** 2 for i in range(3) for j in range(3)))
    return num / den


def rot_t_vec(R, v):
    return [sum(R[k][i] * v[k] for k in range(3)) for i in range(3)]


def rot_t_mat_R_mat(R, M_):
    T = [[sum(R[k][i] * M_[k][j] for k in range(3)) for j in range(3)]
         for i in range(3)]
    return [[sum(T[i][k] * R[k][j] for k in range(3)) for j in range(3)]
            for i in range(3)]
