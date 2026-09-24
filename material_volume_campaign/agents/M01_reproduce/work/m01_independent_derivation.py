"""M01 independent derivation of the SI/FC analytic expectations.

Written by M01 from scratch, stdlib only, BEFORE running any frozen proof
suite. Deliberately independent algebra:

- Unit-simplex monomial integration: for u on the standard 3-simplex
  {(u1,u2,u3) >= 0, u1+u2+u3 <= 1},
    int 1 du = 1/6,  int u_i du = 1/24,  int u_i^2 du = 1/60,
    int u_i u_j du = 1/120 (i != j).
  Every tet moment is obtained by the exact rational affine map
  x = E u + p0 (E = edge matrix, det J = det E) and term-by-term expansion:
    int_TET x_i dV          = det(E) * int x_i du
    com_i                   = (int x_i dV) / V
    int x_i x_j dm          = rho * det(E) * int x_i x_j du
    M[i][j] (central, mass) = int x_i x_j dm - m * com_i * com_j
    I = tr(M) * Id - M.
  No (m/20)(Sum p p + S S^T) vertex-moment formula, no Hammer-Stroud
  quadrature, no tensor congruence anywhere.
- Frame composition is done exactly in Q(sqrt3) via a tiny quadratic-field
  type (a + b*sqrt3, Fraction coefficients); body-frame expectations come
  from transforming VERTICES into the body frame exactly and integrating
  there. No tensor is ever rotated.

Compares against the frozen literals transcribed from the two preregistration
documents (cross-checked against the proof scripts' constants separately);
exits nonzero on any disagreement > 1e-12 (post float conversion).
"""
from fractions import Fraction as F
from math import factorial, sqrt
import sys

TOL = 1e-12

# ---------------------------------------------------------------- Q(sqrt3)


class QS:
    """a + b*sqrt(3), exact."""

    __slots__ = ("a", "b")

    def __init__(self, a=F(0), b=F(0)):
        self.a, self.b = F(a), F(b)

    def __add__(self, o):
        o = _c(o)
        return QS(self.a + o.a, self.b + o.b)

    __radd__ = __add__

    def __sub__(self, o):
        o = _c(o)
        return QS(self.a - o.a, self.b - o.b)

    def __rsub__(self, o):
        o = _c(o)
        return QS(o.a - self.a, o.b - self.b)

    def __neg__(self):
        return QS(-self.a, -self.b)

    def __mul__(self, o):
        o = _c(o)
        return QS(self.a * o.a + 3 * self.b * o.b,
                  self.a * o.b + self.b * o.a)

    __rmul__ = __mul__

    def __truediv__(self, o):
        o = _c(o)
        den = o.a * o.a - 3 * o.b * o.b
        assert den != 0, "division by zero in Q(sqrt3)"
        return QS((self.a * o.a - 3 * self.b * o.b) / den,
                  (self.b * o.a - self.a * o.b) / den)

    def __float__(self):
        return float(self.a) + float(self.b) * sqrt(3.0)

    def __repr__(self):
        return f"QS({self.a},{self.b})"


def _c(x):
    return x if isinstance(x, QS) else QS(x)


HALF = QS(F(1)) / QS(2)          # 1/2
ROOT3_HALF = QS(F(0), F(1)) / QS(2)  # sqrt(3)/2
ZERO = QS(0)
ONE = QS(1)


def rot_z(deg):
    if deg == 30:
        c, s = ROOT3_HALF, HALF
    elif deg == 90:
        c, s = ZERO, ONE
    else:
        raise ValueError(deg)
    return [[c, -s, ZERO], [s, c, ZERO], [ZERO, ZERO, ONE]]


def rot_y_90():
    return [[ZERO, ZERO, ONE], [ZERO, ONE, ZERO], [-ONE, ZERO, ZERO]]


def mmul(A, B):
    return [[sum((A[i][k] * B[k][j] for k in range(3)), ZERO)
             for j in range(3)] for i in range(3)]


def mvec(A, v):
    return tuple(sum((A[i][k] * v[k] for k in range(3)), ZERO)
                 for i in range(3))


def mT(A):
    return [[A[j][i] for j in range(3)] for i in range(3)]


# ------------------------------------------------- exact moment engine
SIMPLEX = {(0, 0, 0): F(1, 6),
           (1, 0, 0): F(1, 24), (0, 1, 0): F(1, 24), (0, 0, 1): F(1, 24),
           (2, 0, 0): F(1, 60), (0, 2, 0): F(1, 60), (0, 0, 2): F(1, 60),
           (1, 1, 0): F(1, 120), (1, 0, 1): F(1, 120), (0, 1, 1): F(1, 120)}
for e, v in SIMPLEX.items():  # the dict IS a!b!c!/(a+b+c+3)! for deg <= 2
    assert (v == F(factorial(e[0]) * factorial(e[1]) * factorial(e[2]),
                   factorial(sum(e) + 3))), e


def _lin(p0, E, i, zero, one_terms):
    t = {(0, 0, 0): p0[i]}
    for k in range(3):
        key = tuple(1 if j == k else 0 for j in range(3))
        t[key] = t.get(key, zero) + E[k][i]
    return t


def _mul(A_, B_, zero):
    out = {}
    for ea, ca in A_.items():
        for eb, cb in B_.items():
            e = (ea[0] + eb[0], ea[1] + eb[1], ea[2] + eb[2])
            out[e] = out.get(e, zero) + ca * cb
    return out


def tet_props(verts, rho):
    """verts: 4 coordinate tuples whose entries are F (rational) or QS.
    rho: F or QS. Returns dict with mass, volume, com, inertia (same type)."""
    qs_mode = any(isinstance(x, QS) for v in verts for x in v)
    zero, one = (ZERO, ONE) if qs_mode else (F(0), F(1))
    conv = (lambda x: x) if qs_mode else (lambda x: F(x))
    p0 = [conv(verts[0][i]) for i in range(3)]
    E = [[conv(verts[k + 1][i]) - p0[i] for i in range(3)] for k in range(3)]
    det = (E[0][0] * (E[1][1] * E[2][2] - E[1][2] * E[2][1])
           - E[0][1] * (E[1][0] * E[2][2] - E[1][2] * E[2][0])
           + E[0][2] * (E[1][0] * E[2][1] - E[1][1] * E[2][0]))
    if qs_mode:
        assert det.b == 0 and det.a > 0, "positive orientation required"
    else:
        assert det > 0, "positive orientation required"
    vol = det / conv(6) if qs_mode else det / 6
    rho_c = _c(rho) if qs_mode else F(rho)
    mass = rho_c * vol

    def integrate(poly):
        s = zero
        for e, c in poly.items():
            # integrands are degree <= 2 so all tuples are in SIMPLEX
            assert e in SIMPLEX, f"unexpected monomial {e}"
            s = s + c * conv(SIMPLEX[e])
        return s

    def lin(i):
        return _lin(p0, E, i, zero, None)

    first_int = [integrate(lin(i)) for i in range(3)]
    second_int = [[integrate(_mul(lin(i), lin(j), zero))
                   for j in range(3)] for i in range(3)]
    com = [det * first_int[i] / vol for i in range(3)]
    M = [[rho_c * det * second_int[i][j] - mass * com[i] * com[j]
          for j in range(3)] for i in range(3)]
    tr = M[0][0] + M[1][1] + M[2][2]
    inertia = [[(tr if i == j else zero) - M[i][j] for j in range(3)]
               for i in range(3)]
    return {"mass": mass, "volume": vol, "com": com, "inertia": inertia}


def recombine_exact(parts):
    mass = sum(p["mass"] for p in parts)
    com = [sum(p["mass"] * p["com"][i] for p in parts) / mass for i in range(3)]
    zero = F(0) if not any(isinstance(x, QS) for p in parts for x in p["inertia"][0]) else ZERO
    inertia = [[zero] * 3 for _ in range(3)]
    for p in parts:
        d = [p["com"][i] - com[i] for i in range(3)]
        dd = sum(x * x for x in d)
        for i in range(3):
            for j in range(3):
                inertia[i][j] += (p["inertia"][i][j]
                                  + p["mass"] * ((dd if i == j else zero) - d[i] * d[j]))
    return {"mass": mass, "com": com, "inertia": inertia}


def to_body_points(frame_R, frame_t, verts):
    """x_body = R^T (x_domain - t), exact in QS."""
    Rt = mT(frame_R)
    out = []
    for v in verts:
        dom = [QS(F(v[i])) for i in range(3)]
        shifted = [dom[i] - _c(frame_t[i]) for i in range(3)]
        out.append(mvec(Rt, shifted))
    return out


# ---------------------------------------------------------------- fixtures
SI_CELLS = {
    "si-body-A": ([(0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1)], F(12)),
    "si-body-B": ([(0, 0, 0), (0, 1, 0), (1, 0, 0), (0, 0, -1)], F(6)),
}
FC_CELLS = {
    "fc-cell-A": ([(0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1)], F(12)),
    "fc-cell-B": ([(2, -1, F(1, 2)), (2, 0, F(1, 2)),
                   (2, -1, F(3, 2)), (3, -1, F(1, 2))], F(6)),
}

# Frozen literals transcribed from the two preregistration DOCUMENTS.
FROZEN = {
    "si-body-A": {"mass": 2.0, "com": [0.25, 0.25, 0.25],
                  "inertia": [[0.15, 0.025, 0.025], [0.025, 0.15, 0.025], [0.025, 0.025, 0.15]]},
    "si-body-B": {"mass": 1.0, "com": [0.25, 0.25, -0.25],
                  "inertia": [[0.075, 0.0125, -0.0125], [0.0125, 0.075, -0.0125], [-0.0125, -0.0125, 0.075]]},
    "si-combined": {"mass": 3.0, "com": [0.25, 0.25, 0.08333333333333333],
                    "inertia": [[0.39166666666666666, 0.0375, 0.0125], [0.0375, 0.39166666666666666, 0.0125], [0.0125, 0.0125, 0.225]]},
    "fc-cell-A": {"mass": 2.0, "com": [0.25, 0.25, 0.25],
                  "inertia": [[0.15, 0.025, 0.025], [0.025, 0.15, 0.025], [0.025, 0.025, 0.15]]},
    "fc-cell-B": {"mass": 1.0, "com": [2.25, -0.75, 0.75],
                  "inertia": [[0.075, 0.0125, 0.0125], [0.0125, 0.075, 0.0125], [0.0125, 0.0125, 0.075]]},
    "fc-combined": {"mass": 3.0, "com": [0.9166666666666666, -0.08333333333333333, 0.4166666666666667],
                    "inertia": [[1.0583333333333333, 1.3708333333333333, -0.6291666666666667], [1.3708333333333333, 3.058333333333333, 0.37083333333333335], [-0.6291666666666667, 0.37083333333333335, 3.558333333333333]]},
    "shared-A": {"mass": 2.0, "com": [0.4754809471616711, 2.323557158514987, -0.25],
                 "inertia": [[0.17165063509461018, 0.012500000000000178, 0.03415063509461097], [0.012500000000000178, 0.12834936490538898, 0.009150635094610893], [0.03415063509461097, 0.009150635094610893, 0.14999999999999908]]},
    "shared-B": {"mass": 1.0, "com": [1.7075317547305482, 0.45753175473054825, 0.25],
                 "inertia": [[0.0858253175473055, 0.006249999999999978, 0.017075317547305402], [0.006249999999999978, 0.06417468245269468, 0.004575317547305488], [0.017075317547305402, 0.004575317547305488, 0.07500000000000015]]},
    "composed-A": {"mass": 2.0, "com": [2.323557158514987, 0.02451905283832875, -0.5],
                   "inertia": [[0.128349364905389, -0.012499999999999997, 0.00915063509461067], [-0.012499999999999997, 0.1716506350946101, -0.03415063509461097], [0.00915063509461067, -0.03415063509461097, 0.1499999999999992]]},
    "composed-B": {"mass": 1.0, "com": [-0.75, -0.29246824526945175, 1.7075317547305482],
                   "inertia": [[0.07500000000000019, -0.004575317547305502, -0.017075317547305513], [-0.004575317547305502, 0.06417468245269464, 0.006250000000000033], [-0.017075317547305513, 0.006250000000000033, 0.0858253175473055]]},
}

errors = []


def compare(label, props, frozen):
    dm = abs(float(props["mass"]) - frozen["mass"])
    dc = max(abs(float(props["com"][i]) - frozen["com"][i]) for i in range(3))
    di = max(abs(float(props["inertia"][i][j]) - frozen["inertia"][i][j])
             for i in range(3) for j in range(3))
    ok = dm <= TOL and dc <= TOL and di <= TOL
    print(f"{label:26s} dmass={dm:.3e} dcom={dc:.3e} dI={di:.3e} -> "
          f"{'OK' if ok else 'FAIL'}")
    if not ok:
        errors.append(label)


# ---------------------------------------------------------------- SI checks
si_parts = []
for body, (verts, rho) in SI_CELLS.items():
    v = [tuple(F(x) for x in vt) for vt in verts]
    p = tet_props(v, rho)
    si_parts.append(p)
    compare(f"derivation {body}", p, FROZEN[body])
compare("derivation si-combined", recombine_exact(si_parts), FROZEN["si-combined"])

# interface face {v0,v1,v2}: right triangle legs (1,0,0),(0,1,0) -> area 1/2
area = F(1, 2)
print(f"SI interface area: {float(area)} (frozen 0.5) -> "
      f"{'OK' if area == F(1, 2) else 'FAIL'}")
if area != F(1, 2):
    errors.append("si-interface-area")

# ---------------------------------------------------------------- FC domain
fc_parts = []
for cell, (verts, rho) in FC_CELLS.items():
    v = [tuple(F(x) if not isinstance(x, F) else x for x in vt) for vt in verts]
    p = tet_props(v, rho)
    fc_parts.append(p)
    compare(f"derivation {cell}", p, FROZEN[cell])
compare("derivation fc-combined", recombine_exact(fc_parts), FROZEN["fc-combined"])

# ------------------------------------------------- FC frames (exact QS)
P = {"R": rot_z(30), "t": (ONE, -QS(2), HALF)}
LA = {"R": rot_z(90), "t": (HALF, ZERO, QS(F(1, 4)))}
LB = {"R": rot_y_90(), "t": (ZERO, QS(F(3, 4)), -HALF)}


def compose(outer, inner):
    R = mmul(outer["R"], inner["R"])
    t = tuple(mvec(outer["R"], inner["t"])[i] + outer["t"][i] for i in range(3))
    return {"R": R, "t": t}


DA = compose(P, LA)
DB = compose(P, LB)

spot = [("R_DA[0][0]", DA["R"][0][0], -0.5),
        ("R_DA[0][1]", DA["R"][0][1], -0.8660254037844386),
        ("R_DA[1][0]", DA["R"][1][0], 0.8660254037844386),
        ("R_DA[2][2]", DA["R"][2][2], 1.0),
        ("R_DB[0][1]", DB["R"][0][1], -0.5),
        ("R_DB[0][2]", DB["R"][0][2], 0.8660254037844386),
        ("R_DB[1][1]", DB["R"][1][1], 0.8660254037844386),
        ("R_DB[2][0]", DB["R"][2][0], -1.0),
        ("t_DA[0]", DA["t"][0], 1.4330127018922192),
        ("t_DA[1]", DA["t"][1], -1.75),
        ("t_DA[2]", DA["t"][2], 0.75),
        ("t_DB[0]", DB["t"][0], 0.625),
        ("t_DB[1]", DB["t"][1], -1.350480947161671),
        ("t_DB[2]", DB["t"][2], 0.0)]
for name, val, exp in spot:
    d = abs(float(val) - exp)
    ok = d <= TOL
    print(f"composed spot {name:10s} observed={float(val)!r} frozen={exp!r} "
          f"d={d:.3e} -> {'OK' if ok else 'FAIL'}")
    if not ok:
        errors.append(f"spot-{name}")

# RUN-SHARED: bodies expressed in the parent frame P
for cell, body_key in (("fc-cell-A", "shared-A"), ("fc-cell-B", "shared-B")):
    verts, rho = FC_CELLS[cell]
    pts = to_body_points(P["R"], P["t"], verts)
    props = tet_props(pts, rho)
    compare(f"derivation {body_key}", props, FROZEN[body_key])

# RUN-COMPOSED: bodies in their pre-composed local frames
for cell, frame, body_key in (("fc-cell-A", DA, "composed-A"),
                              ("fc-cell-B", DB, "composed-B")):
    verts, rho = FC_CELLS[cell]
    pts = to_body_points(frame["R"], frame["t"], verts)
    props = tet_props(pts, rho)
    compare(f"derivation {body_key}", props, FROZEN[body_key])

print()
if errors:
    print(f"INDEPENDENT DERIVATION: {len(errors)} FAILURES: {errors}")
    sys.exit(1)
print("INDEPENDENT DERIVATION: ALL FROZEN LITERALS CONFIRMED (tol 1e-12)")
