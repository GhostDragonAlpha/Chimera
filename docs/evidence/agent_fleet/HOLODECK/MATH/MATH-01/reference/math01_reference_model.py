"""math01_reference_model.py -- independent reference model of catalogue card
MATH-01 "Units and coordinate algebra" (holodeck-math-01).

Card contract (quoted from the card, preregistered in ../PREREG.md):
  STATEMENT: Typed quantity/frame contract and reversible coordinate transforms
  PREDICTION: Unit and frame changes preserve dimensionless predictions
  FALSIFIER: A metre-newton comparison or undeclared world-unit conversion
             is admitted
  MATHEMATICS: SI dimensions; nondimensionalization; Buckingham Pi

STDLIB ONLY (fractions, math). This is an independent model of the INTENDED
contract: exact rational SI dimension algebra, declared-only unit conversions,
rigid reversible frames, and an exact-rational Buckingham-Pi nullspace. It is
NOT the deployed elastic boundary (tools/elastic_foundation/units_contract.py),
which is measured separately in checks/r6_source_trace.txt.

Every refusal carries a named reason; the two card-falsifier reasons are
`dimension_mismatch` (metre-newton) and `undeclared_conversion` /
`undeclared_frame_scale` (undeclared world-unit conversion).
"""
from __future__ import annotations

import math
from fractions import Fraction

# ---- the one refusal type (named, like the deployed boundary's UnitsRefusal)


class Math01Refusal(ValueError):
    """Named refusal of the typed algebra."""

    def __init__(self, reason: str, message: str):
        super().__init__(message)
        self.reason = reason
        self.message = message

    def __repr__(self):
        return f"Math01Refusal({self.reason!r}, {self.message!r})"


# ---- exact SI dimensions (L, M, T) with Fraction exponents ------------------


def _frac3(seq) -> tuple:
    vals = tuple(Fraction(v) for v in seq)
    if len(vals) != 3:
        raise ValueError("dimension exponents are a length-3 (L, M, T) vector")
    return vals


class Dimension:
    """Exact SI base-dimension exponent vector over (m, kg, s)."""

    __slots__ = ("exponents",)

    def __init__(self, exponents=(0, 0, 0)):
        object.__setattr__(self, "exponents", _frac3(exponents))

    # named base and derived dimensions used by the controls
    M = None      # set after class body
    KG = None
    S = None
    PA = None     # kg m^-1 s^-2
    N = None      # kg m s^-2
    N_PER_M = None   # kg s^-2
    DIMENSIONLESS = None

    def __mul__(self, other):
        return Dimension(tuple(a + b for a, b in
                               zip(self.exponents, other.exponents)))

    def __truediv__(self, other):
        return Dimension(tuple(a - b for a, b in
                               zip(self.exponents, other.exponents)))

    def __eq__(self, other):
        return isinstance(other, Dimension) and self.exponents == other.exponents

    def __hash__(self):
        return hash(self.exponents)

    def __repr__(self):
        L, M, T = self.exponents
        return f"Dimension(L={L}, M={M}, T={T})"


Dimension.M = Dimension((1, 0, 0))
Dimension.KG = Dimension((0, 1, 0))
Dimension.S = Dimension((0, 0, 1))
Dimension.PA = Dimension((-1, 1, -2))
Dimension.N = Dimension((1, 1, -2))
Dimension.N_PER_M = Dimension((0, 1, -2))
Dimension.DIMENSIONLESS = Dimension((0, 0, 0))


# ---- typed quantities --------------------------------------------------------


def _finite_number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise Math01Refusal(
            "nonfinite_quantity",
            f"quantity value must be a real number, got {type(value).__name__}")
    if isinstance(value, float) and not math.isfinite(value):
        raise Math01Refusal(
            "nonfinite_quantity", f"quantity value must be finite, got {value}")
    return float(value)


class Quantity:
    """Immutable typed quantity: float64 value + exact Dimension.

    The card falsifier lives here: ANY operation between unequal dimensions
    (including a metre-newton comparison) raises Math01Refusal with reason
    `dimension_mismatch`. Dimensions compose exactly; values are float64.
    """

    __slots__ = ("value", "dimension")

    def __init__(self, value, dimension: Dimension):
        object.__setattr__(self, "value", _finite_number(value))
        if not isinstance(dimension, Dimension):
            raise Math01Refusal(
                "nonfinite_quantity", "dimension must be a Dimension")
        object.__setattr__(self, "dimension", dimension)

    def is_dimensionless(self):
        return self.dimension == Dimension.DIMENSIONLESS

    def __mul__(self, other):
        if not isinstance(other, Quantity):
            raise Math01Refusal(
                "dimension_mismatch",
                "multiplication is only defined between Quantities")
        return Quantity(self.value * other.value, self.dimension * other.dimension)

    def __truediv__(self, other):
        if not isinstance(other, Quantity):
            raise Math01Refusal(
                "dimension_mismatch",
                "division is only defined between Quantities")
        return Quantity(self.value / other.value, self.dimension / other.dimension)

    def _same_dimension(self, other, op):
        if not isinstance(other, Quantity) or self.dimension != other.dimension:
            have = (type(other).__name__ if not isinstance(other, Quantity)
                    else str(other.dimension))
            raise Math01Refusal(
                "dimension_mismatch",
                f"cannot {op} quantities of {self.dimension} and {have}")

    def __add__(self, other):
        self._same_dimension(other, "add")
        return Quantity(self.value + other.value, self.dimension)

    def __radd__(self, other):
        self._same_dimension(other, "add (reflected)")
        return Quantity(self.value + other.value, self.dimension)

    def __rsub__(self, other):
        self._same_dimension(other, "subtract (reflected)")
        return Quantity(other.value - self.value, self.dimension)

    def __sub__(self, other):
        self._same_dimension(other, "subtract")
        return Quantity(self.value - other.value, self.dimension)

    def __eq__(self, other):
        self._same_dimension(other, "compare (==)")
        return self.value == other.value

    def __lt__(self, other):
        self._same_dimension(other, "order (<)")
        return self.value < other.value

    def __le__(self, other):
        self._same_dimension(other, "order (<=)")
        return self.value <= other.value

    def __gt__(self, other):
        self._same_dimension(other, "order (>)")
        return self.value > other.value

    def __ge__(self, other):
        self._same_dimension(other, "order (>=)")
        return self.value >= other.value

    def __hash__(self):
        return hash((self.value, self.dimension))

    def __repr__(self):
        return f"Quantity({self.value}, {self.dimension})"


# ---- declared-only unit conversions -----------------------------------------

DEFAULT_UNITS = {
    # name: (Dimension, scale_to_si)  -- SI anchors, preregistered set
    "m": (Dimension.M, 1.0),
    "mm": (Dimension.M, 1e-3),
    "kg": (Dimension.KG, 1.0),
    "Pa": (Dimension.PA, 1.0),
    "N": (Dimension.N, 1.0),
    "N/m": (Dimension.N_PER_M, 1.0),
}


class UnitRegistry:
    """Conversions exist ONLY by explicit declaration (the card falsifier's
    `undeclared` is the refusal condition; declaring makes it legal)."""

    def __init__(self):
        self.units = dict(DEFAULT_UNITS)

    def declare_unit(self, name, dimension, scale_to_si):
        if name in self.units:
            old_dim, old_scale = self.units[name]
            if old_dim != dimension or old_scale != scale_to_si:
                raise Math01Refusal(
                    "contradictory_conversion",
                    f"unit {name!r} already declared as "
                    f"({old_dim}, {old_scale}); conflicting declaration "
                    f"({dimension}, {scale_to_si})")
            return
        self.units[name] = (dimension, float(scale_to_si))

    def convert(self, value, source_unit: str, target_unit: str) -> Quantity:
        """Re-express `value` from source_unit to target_unit.

        Both units must be DECLARED; the declaration is the only bridge.
        Returns a Quantity carrying the target dimension.
        """
        for unit in (source_unit, target_unit):
            if unit not in self.units:
                raise Math01Refusal(
                    "undeclared_conversion",
                    f"no declared unit {unit!r}: an undeclared "
                    "world-unit conversion is refused, never admitted")
        src_dim, src_scale = self.units[source_unit]
        tgt_dim, tgt_scale = self.units[target_unit]
        if src_dim != tgt_dim:
            raise Math01Refusal(
                "conversion_dimension_mismatch",
                f"cannot convert {source_unit!r} of {src_dim} to "
                f"{target_unit!r} of {tgt_dim}")
        return Quantity(float(value) * src_scale / tgt_scale, tgt_dim)


# ---- rigid frames and reversible transforms ---------------------------------


def _check_orthonormal(rotation):
    for i in range(3):
        for j in range(3):
            dot = sum(rotation[i][k] * rotation[j][k] for k in range(3))
            want = 1.0 if i == j else 0.0
            if abs(dot - want) > 1e-12:
                raise Math01Refusal(
                    "non_orthonormal_rotation",
                    f"R·Rᵀ[{i}][{j}] = {dot} deviates from {want}")


def _mat_vec(m, v):
    return tuple(sum(m[i][k] * v[k] for k in range(3)) for i in range(3))


def _transpose(m):
    return tuple(tuple(m[j][i] for j in range(3)) for i in range(3))


def rotation_about_z(theta):
    c, s = math.cos(theta), math.sin(theta)
    return ((c, -s, 0.0), (s, c, 0.0), (0.0, 0.0, 1.0))


class Frame:
    """A named coordinate frame with a DECLARED length unit."""

    __slots__ = ("name", "length_unit")

    def __init__(self, name, length_unit="m"):
        self.name = name
        self.length_unit = length_unit


class Transform:
    """Rigid transform source->target: orthonormal R, translation t.

    Reversibility: inverse() is exactly (Rᵀ, -Rᵀt); the double inverse of a
    pure rotation is bit-exact. Cross-unit transforms require the target
    unit to be DECLARED at apply() time (`undeclared_frame_scale`).
    """

    def __init__(self, source: Frame, target: Frame, rotation, translation,
                 registry=None):
        _check_orthonormal(rotation)
        self.source = source
        self.target = target
        self.rotation = tuple(tuple(float(x) for x in row) for row in rotation)
        self.translation = tuple(float(x) for x in translation)
        self.registry = registry

    def apply(self, point):
        p = _mat_vec(self.rotation, point)
        moved = tuple(p[i] + self.translation[i] for i in range(3))
        if self.source.length_unit == self.target.length_unit:
            return moved
        # Cross-unit frames: the scale must be DECLARED in the registry.
        if self.registry is None:
            raise Math01Refusal(
                "undeclared_frame_scale",
                f"frame {self.source.name!r} ({self.source.length_unit}) -> "
                f"{self.target.name!r} ({self.target.length_unit}): no "
                "declared scale between the frames' length units")
        try:
            _, src_scale = self.registry.units[self.source.length_unit]
            _, tgt_scale = self.registry.units[self.target.length_unit]
        except KeyError as missing:
            raise Math01Refusal(
                "undeclared_frame_scale",
                f"frame {self.source.name!r} ({self.source.length_unit}) -> "
                f"{self.target.name!r} ({self.target.length_unit}): length "
                f"unit {missing.args[0]!r} is not declared") from None
        scale = src_scale / tgt_scale
        return tuple(x * scale for x in moved)

    def inverse(self):
        rt = _transpose(self.rotation)
        t_inv = tuple(-sum(rt[i][k] * self.translation[k] for k in range(3))
                      for i in range(3))
        return Transform(self.target, self.source, rt, t_inv)


def compose(outer: Transform, inner: Transform) -> Transform:
    """(outer ∘ inner)(p) = outer(inner(p))."""
    if inner.target.name != outer.source.name:
        raise Math01Refusal(
            "frame_mismatch",
            "compose requires inner.target == outer.source")
    r = tuple(tuple(sum(outer.rotation[i][k] * inner.rotation[k][j]
                        for k in range(3)) for j in range(3))
              for i in range(3))
    t = tuple(outer.rotation[i][0] * inner.translation[0]
              + outer.rotation[i][1] * inner.translation[1]
              + outer.rotation[i][2] * inner.translation[2]
              + outer.translation[i] for i in range(3))
    return Transform(inner.source, outer.target, r, t)


# ---- nondimensionalization and Buckingham Pi --------------------------------


def nondimensionalize(quantities):
    """Reduce a dimensionally-consistent list by its first member: every
    result is dimensionless and all ratios are preserved."""
    if not quantities:
        return []
    ref = quantities[0]
    out = []
    for q in quantities:
        out.append(q / ref)   # refuses dimension_mismatch on any odd member
    return out


def pi_groups(quantities):
    """Buckingham Pi: the exact rational nullspace of the dimension matrix.

    n quantities, rank k of the (3 x n) rational dimension matrix -> exactly
    n - k independent dimensionless groups. Each group is returned as a dict
    {quantity_name: Fraction exponent}, normalized to a primitive integer
    vector (cleared denominators, divided by the gcd, first nonzero
    exponent positive) -- the normalization under which the preregistered
    pendulum certificate {T:+2, L:-1, g:+1} is exact.
    """
    names = [q[0] for q in quantities]
    dims = [q[1].dimension.exponents for q in quantities]
    n = len(dims)
    # matrix rows = basis (L, M, T); columns = quantities; entries Fraction
    rows = [[Fraction(dims[j][b]) for j in range(n)] for b in range(3)]
    rank, pivots = _rref(rows)
    free = [j for j in range(n) if j not in pivots]
    groups = []
    for f in free:
        vec = [Fraction(0)] * n
        vec[f] = Fraction(1)
        for r, p in enumerate(pivots):
            vec[p] = -rows[r][f]
        groups.append((names, _primitive(vec)))
    return groups


def _rref(rows):
    """Reduced row echelon form over Q (in place); returns (rank, pivot_cols)."""
    pivots = []
    r = 0
    for c in range(len(rows[0])):
        pivot = next((i for i in range(r, len(rows)) if rows[i][c] != 0), None)
        if pivot is None:
            continue
        rows[r], rows[pivot] = rows[pivot], rows[r]
        inv = rows[r][c]
        rows[r] = [x / inv for x in rows[r]]
        for i in range(len(rows)):
            if i != r and rows[i][c] != 0:
                f = rows[i][c]
                rows[i] = [a - f * b for a, b in zip(rows[i], rows[r])]
        pivots.append(c)
        r += 1
        if r == len(rows):
            break
    return r, pivots


def _primitive(vec):
    """Scale a rational vector to coprime integers, first nonzero positive."""
    from math import gcd
    den = 1
    for x in vec:
        den = den * x.denominator // gcd(den, x.denominator)
    ints = [int(x * den) for x in vec]
    g = 0
    for x in ints:
        g = gcd(g, abs(x))
    if g:
        ints = [x // g for x in ints]
    for x in ints:
        if x != 0:
            if x < 0:
                ints = [-y for y in ints]
            break
    return ints


# convenience constructors ----------------------------------------------------

def q_metres(x):
    return Quantity(x, Dimension.M)


def q_of(value, dimension):
    return Quantity(value, dimension)
