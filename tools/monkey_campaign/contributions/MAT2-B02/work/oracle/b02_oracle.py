"""MAT2-B02 exact-arithmetic oracle for tetrahedral mass properties.

Pure stdlib. Imports nothing from the frozen tree and shares no code with it
(frozen prediction P-OR; preregistration section "Frozen oracle"). All
quantities are computed as exact rationals via the reference-simplex affine
map, then converted to float only at the comparison boundary.
"""
from __future__ import annotations

from fractions import Fraction
from math import factorial

F0 = Fraction(0)
F1 = Fraction(1)


def _ref_monomial(power):
    """Exact integral of x^a y^b z^c over the reference simplex
    conv{(0,0,0),(1,0,0),(0,1,0),(0,0,1)} = a!b!c!/(a+b+c+3)!."""
    a, b, c = power
    return Fraction(factorial(a) * factorial(b) * factorial(c),
                    factorial(a + b + c + 3))


_MOMENT_CACHE = {}


def _ref_second_moment(i, j):
    """Exact integral of x_i * x_j over the reference simplex."""
    key = (i, j)
    if key not in _MOMENT_CACHE:
        power = [0, 0, 0]
        power[i] += 1
        power[j] += 1
        _MOMENT_CACHE[key] = _ref_monomial(tuple(power))
    return _MOMENT_CACHE[key]


def _ref_first_moment(i):
    key = ("first", i)
    if key not in _MOMENT_CACHE:
        power = [0, 0, 0]
        power[i] += 1
        _MOMENT_CACHE[key] = _ref_monomial(tuple(power))
    return _MOMENT_CACHE[key]


def tet_integrals_exact(vertices, density):
    """Return (volume, mass, first_moment_vector, raw_second_moment_matrix)
    about the ORIGIN, all exact Fractions, for one tet with uniform density.

    vertices: four (x,y,z) rows of exact Fractions/ints.
    density: exact Fraction (or int).
    """
    p0 = [Fraction(v) for v in vertices[0]]
    cols = [[Fraction(vertices[k][d]) - p0[d] for k in range(1, 4)]
            for d in range(3)]
    # determinant of the 3x3 map whose columns are p1-p0, p2-p0, p3-p0
    det = (cols[0][0] * (cols[1][1] * cols[2][2] - cols[1][2] * cols[2][1])
           - cols[1][0] * (cols[0][1] * cols[2][2] - cols[0][2] * cols[2][1])
           + cols[2][0] * (cols[0][1] * cols[1][2] - cols[0][2] * cols[1][1]))
    if det <= 0:
        raise AssertionError("oracle fixture tet must be positively oriented")
    volume = det / 6
    mass = volume * Fraction(density)
    # mass-weighted integrals: integral_T f dm = density * det * integral_R f
    wdet = Fraction(density) * det

    # x_d = p0_d + sum_k cols[d][k] * xi_k over the reference coords xi.
    # first moment of x_d: integrate p0_d + sum cols[d][k]*xi_k
    first = []
    for d in range(3):
        acc = p0[d] * _ref_monomial((0, 0, 0))
        for k in range(3):
            acc += cols[d][k] * _ref_first_moment(k)
        first.append(acc * wdet)

    # second moment E[x_i x_j] = integrate the product of two affine forms
    second = [[F0] * 3 for _ in range(3)]
    for i in range(3):
        for j in range(i, 3):
            acc = p0[i] * p0[j] * _ref_monomial((0, 0, 0))
            for k in range(3):
                acc += (p0[i] * cols[j][k] + p0[j] * cols[i][k]) \
                    * _ref_first_moment(k)
                for l in range(3):
                    # E[xi_k xi_l]
                    e_kl = _ref_second_moment(min(k, l), max(k, l))
                    acc += cols[i][k] * cols[j][l] * e_kl
            second[i][j] = second[j][i] = acc * wdet
    return volume, mass, first, second


def body_properties_exact(cells, density_by_cell):
    """Combine cells -> (volume, mass, com, inertia_about_com) exact.

    cells: list of dicts with "vertex_ids" and "vertices" (the 4 positions).
    density_by_cell: cell_id -> exact Fraction density.
    """
    volume = F0
    mass = F0
    first = [F0] * 3
    second = [[F0] * 3 for _ in range(3)]
    for cell in cells:
        v, m, f, s = tet_integrals_exact(cell["vertices"],
                                         density_by_cell[cell["cell_id"]])
        volume += v
        mass += m
        for d in range(3):
            first[d] += f[d]
        for i in range(3):
            for j in range(3):
                second[i][j] += s[i][j]
    com = [first[d] / mass for d in range(3)]
    central = [[second[i][j] - mass * com[i] * com[j] for j in range(3)]
               for i in range(3)]
    trace = central[0][0] + central[1][1] + central[2][2]
    inertia = [[trace - central[i][j] if i == j else -central[i][j]
                for j in range(3)] for i in range(3)]
    return volume, mass, com, inertia


def to_float(value):
    if isinstance(value, list):
        return [to_float(v) for v in value]
    return float(value)
