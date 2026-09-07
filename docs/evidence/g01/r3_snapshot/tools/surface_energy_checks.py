"""surface_energy_checks.py -- THE REGISTERED FALSIFIER BATTERY for the
constant-gamma surface-energy reference. (G01)

Every check here was registered in docs/FOUNDATION_G01_REPORT.md (predictions
P-1..P-7) and in docs/THE_SURFACE_ENERGY_TRANSLATION.md (falsifiers 1..7)
BEFORE this file was written. The battery implements each one against the
independent instrument named there. No silently skipped test may count as
PASS: a check that raises a skip still fails the run.

TOLERANCES AND THEIR DERIVATION (printed with results):
  e          = 2.220446049250313e-16  (double-precision epsilon, np.finfo)
  FD step    h = e^(1/3) ~ 6.06e-6    (balances O(h^2) truncation vs O(e/h)
               cancellation of central differences)
  F1 limit   256*e^(2/3) ~ 9.387e-9   (preregistered numerical allowance for
               the derivative checks; NOT a rigorous bound for arbitrary
               geometry -- ASTRA's preregistration says so explicitly)
  F2/F8 limit 512*e ~ 1.137e-13      (preregistered algebraic invariance
               allowance)
  F5 gate    strict monotone decrease, <= 1% at level 4 (discretization gate,
               NOT a material constant or engine certification)
  Normalization for F1/F3: err = max|F_fd - F_impl| / max(1, max|F_impl|).
  Fixtures are O(1) (gamma=1, radius 1), so this is max-abs in practice; the
  denominator only keeps the metric from exploding on a degenerate fixture.

INSTRUMENT INDEPENDENCE: the finite-difference reference energy is HERON'S
formula on side lengths -- no cross product, no normal, no shared code path
with the implementation's area. A mutant that breaks the derivative breaks
against a formula that cannot share the bug (F3 proves the battery catches
sign flips, zero force, spurious force, and the frozen-normal law).

Run:  python tools/surface_energy_checks.py          # exit 0 = all PASS
      python tools/surface_energy_checks.py --json   # machine-readable dump
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from port_registry import port_test, expect  # the ONE house harness

sys.path.insert(0, str(Path(__file__).resolve().parent))
import surface_energy_reference as ser

EPS = float(np.finfo(np.float64).eps)
FD_H = ser.FD_H
DERIV_LIMIT = ser.DERIV_LIMIT
INV_LIMIT = ser.INVARIANCE_LIMIT
EXPECTED_CHECKS = 8


# ── fixtures ─────────────────────────────────────────────────────────────────

def unit_octahedron() -> tuple[np.ndarray, np.ndarray]:
    """6 vertices, 8 outward-oriented faces, radius 1."""
    V = np.array([[1., 0., 0.], [-1., 0., 0.], [0., 1., 0.],
                  [0., -1., 0.], [0., 0., 1.], [0., 0., -1.]])
    F = np.array([[0, 2, 4], [2, 1, 4], [1, 3, 4], [3, 0, 4],
                  [2, 0, 5], [1, 2, 5], [3, 1, 5], [0, 3, 5]])
    return V, F


def subdivide_to_sphere(V, F, level: int):
    """1->4 Loop-style subdivision, midpoints projected back to the unit sphere."""
    V = V.copy().astype(np.float64)
    F = F.copy().astype(np.int64)
    for _ in range(level):
        V, F = _subdivide_once(V, F)
    V /= np.linalg.norm(V, axis=1, keepdims=True)   # renormalize ALL to unit
    return V, F


def _subdivide_once(V, F):
    cache: dict[tuple[int, int], int] = {}

    def mid(i, j):
        key = (min(i, j), max(i, j))
        if key not in cache:
            V = np.vstack  # noqa: F841  (clarity no-op)
            p = 0.5 * (V_POS[key[0]] + V_POS[key[1]])
            cache[key] = len(V_POS)
            V_POS.append(p)
        return cache[key]

    V_POS = [row.copy() for row in V]
    newF = []
    for a, b, c in F:
        m_ab, m_bc, m_ca = mid(a, b), mid(b, c), mid(c, a)
        newF += [[a, m_ab, m_ca], [m_ab, b, m_bc],
                 [m_ca, m_bc, c], [m_ab, m_bc, m_ca]]
    return np.array(V_POS), np.array(newF, dtype=np.int64)


def distorted_octa1(seed: int = 7):
    """Level-1 octahedron with a deterministic radial perturbation (well-conditioned)."""
    V, F = subdivide_to_sphere(*unit_octahedron(), 1)
    rng = np.random.default_rng(seed)
    V = V * (1.0 + 0.08 * rng.standard_normal((V.shape[0], 1)))
    return V, F


def open_grid(n: int = 3):
    """An n x n open patch in z=0 with a gentle deterministic ripple."""
    xs = np.linspace(-1.0, 1.0, n + 1)
    g = np.array([[x, y, 0.15 * math.sin(2.4 * x) * math.cos(1.7 * y)]
                  for y in xs for x in xs])
    faces = []
    for j in range(n):
        for i in range(n):
            v00 = j * (n + 1) + i
            v10 = v00 + 1
            v01 = v00 + (n + 1)
            v11 = v01 + 1
            faces += [[v00, v10, v11], [v00, v11, v01]]
    return g, np.array(faces, dtype=np.int64)


def flat_square():
    """Unit square as two CCW triangles in z=0 (for the equal-area counterexample)."""
    V = np.array([[0., 0., 0.], [1., 0., 0.], [1., 1., 0.], [0., 1., 0.]])
    F = np.array([[0, 1, 2], [0, 2, 3]])
    return V, F


# ── the independent instrument ───────────────────────────────────────────────

def heron_energy(pos: np.ndarray, F: np.ndarray, gamma) -> float:
    """U = sum gamma_t * HeronArea. NO cross products, NO normals, NO shared
    code with the implementation -- this independence is what makes F1/F3 mean
    something. Well-conditioned fixtures only (Heron loses precision on
    near-degenerate triangles; the preregistration scopes F1 to O(1) ones)."""
    a = pos[F[:, 0]]
    b = pos[F[:, 1]]
    c = pos[F[:, 2]]
    la = np.linalg.norm(b - c, axis=1)
    lb = np.linalg.norm(c - a, axis=1)
    lc = np.linalg.norm(a - b, axis=1)
    s = 0.5 * (la + lb + lc)
    areas = np.sqrt(np.maximum(s * (s - la) * (s - lb) * (s - lc), 0.0))
    return float(np.sum(gamma * areas))


def heron_eval(pos, F, gamma):
    """(energy, vertex_forces) with forces by central FD of the Heron energy.
    h = e^(1/3) -- preregistered. Vectorized per (vertex, coordinate)."""
    pos = np.asarray(pos, dtype=np.float64)
    nV = pos.shape[0]
    f_fd = np.zeros((nV, 3))
    for i in range(nV):
        for k in range(3):
            pp = pos.copy(); pp[i, k] += FD_H
            pm = pos.copy(); pm[i, k] -= FD_H
            f_fd[i, k] = -(heron_energy(pp, F, gamma)
                           - heron_energy(pm, F, gamma)) / (2.0 * FD_H)
    return heron_energy(pos, F, gamma), f_fd


def _norm_err(f_impl: np.ndarray, f_ref: np.ndarray) -> float:
    scale = max(1.0, float(np.abs(f_impl).max()))
    return float(np.abs(f_impl - f_ref).max()) / scale


def generalized_pressure(ev: ser.Evaluation, pos: np.ndarray,
                         F: np.ndarray) -> float:
    """P_disc = -sum_i (F_i . x_i) / (3V), V by the divergence theorem
    (signed; outward-oriented meshes give V > 0)."""
    a, b, c = pos[F[:, 0]], pos[F[:, 1]], pos[F[:, 2]]
    V = float(np.sum(np.einsum('ij,ij->i', a, np.cross(b, c))) / 6.0)
    return float(-np.sum(np.einsum('ij,ij->i', ev.vertex_forces, pos)) / (3.0 * V))


# ── F1: force vs independent Heron-area finite differences ───────────────────

@port_test(
    "F1_force_vs_heron_fd",
    "The implemented vertex forces are the exact gradient of U = sum gamma*A: "
    "central FD of an INDEPENDENT energy (Heron on side lengths, h=e^(1/3)) "
    "reproduces them to <= 256*e^(2/3) normalized on every fixture.",
    "Measured normalized max error exceeds 256*e^(2/3) on any fixture, or the "
    "FD instrument itself is broken (F3 catches that).")
def f1_force_vs_heron_fd() -> dict:
    gam = 1.0
    fixtures = {
        "octahedron_L0": unit_octahedron(),
        "octahedron_L1_distorted": distorted_octa1(),
        "open_grid_3x3": open_grid(3),
    }
    rows, worst = {}, 0.0
    for name, (V, F) in fixtures.items():
        ev = ser.evaluate_surface(V, F, gam)
        _, f_fd = heron_eval(V, F, gam)
        err = _norm_err(ev.vertex_forces, f_fd)
        rows[name] = err
        worst = max(worst, err)
    return {"pass": worst <= DERIV_LIMIT, "worst": worst, "limit": DERIV_LIMIT,
            "per_fixture": rows,
            "note": "open patch included: FD applies at boundary vertices "
                    "(their forces are real boundary traction)"}


# ── F2: invariances ──────────────────────────────────────────────────────────

@port_test(
    "F2_invariances",
    "The force law is objective and balanced: rigid rotation+translation "
    "transforms forces covariantly and torque about the correspondingly "
    "transformed pivot covariantly; a closed mesh has sum F = 0 and sum tau = 0; "
    "zero gamma gives exactly zero energy and force; force scales linearly in "
    "gamma. All residuals <= 512*e normalized.",
    "Any normalized invariance residual exceeds 512*e, or an exact-zero case "
    "is not exactly zero.")
def f2_invariances() -> dict:
    V, F = unit_octahedron()
    gam = 1.3  # non-unit on purpose: scaling is checked against gamma=1
    ev = ser.evaluate_surface(V, F, gam)

    # rotation: 41 deg about (1,2,-1)/sqrt(6), plus a translation
    ax = np.array([1.0, 2.0, -1.0]); ax /= np.linalg.norm(ax)
    th = 0.7156
    K = np.array([[0, -ax[2], ax[1]], [ax[2], 0, -ax[0]], [-ax[1], ax[0], 0]])
    R = np.eye(3) + math.sin(th) * K + (1 - math.cos(th)) * (K @ K)
    t = np.array([0.4, -1.1, 2.2])
    Vr = V @ R.T + t
    evr = ser.evaluate_surface(Vr, F, gam)

    res = {}
    res["force_rotation"] = _norm_err(evr.vertex_forces,
                                      ev.vertex_forces @ R.T)
    # translation must not change forces (sum F = 0 makes this well-defined)
    # torque about pivot p transforms as tau' = R tau about the rotated pivot
    def torque(pos, forces, pivot):
        return np.cross(pos - pivot, forces).sum(axis=0)

    p = np.array([0.3, -0.2, 0.9])
    tau0 = torque(V, ev.vertex_forces, p)
    tau1 = torque(Vr, evr.vertex_forces, R @ p + t)
    res["torque_covariance"] = _norm_err(tau1[None, :], (R @ tau0)[None, :])

    # internal balance on a closed mesh
    res["force_balance"] = _norm_err(ev.vertex_forces.sum(axis=0)[None, :],
                                     np.zeros((1, 3)))
    tau_origin = torque(V, ev.vertex_forces, np.zeros(3))
    res["torque_balance"] = _norm_err(tau_origin[None, :], np.zeros((1, 3)))

    # zero gamma is EXACTLY zero (no allowance needed; anything else fails)
    ev0 = ser.evaluate_surface(V, F, 0.0)
    res["zero_gamma_exact"] = 0.0 if (ev0.energy == 0.0 and
                                      not ev0.vertex_forces.any()) else float("inf")

    # linear gamma scaling
    ev1 = ser.evaluate_surface(V, F, 1.0)
    res["gamma_scaling"] = _norm_err(ev.vertex_forces, gam * ev1.vertex_forces)
    res["energy_scaling"] = abs(ev.energy - gam * ev1.energy) / max(1.0, abs(ev1.energy))

    worst = max(res.values())
    return {"pass": worst <= INV_LIMIT, "worst": worst, "limit": INV_LIMIT,
            "per_invariance": res}


# ── F3: negative controls (the instrument must be able to fail) ──────────────

@port_test(
    "F3_negative_controls",
    "The battery DETECTS four sabotages: force sign reversal, zero force, a "
    "spurious extra force on one vertex, and the frozen-import-normal "
    "derivative evaluated after a 90-degree rotation (the law ca_triangle.py "
    "actually implements). Each must FAIL the F1-style FD check.",
    "Any mutation passes the FD check it attacks -- that falsifies the "
    "instrument, and per preregistration the battery itself is then void.")
def f3_negative_controls() -> dict:
    V, F = unit_octahedron()
    _, f_fd = heron_eval(V, F, 1.0)
    ev = ser.evaluate_surface(V, F, 1.0)
    results = {}

    def detected(name, mutant):
        err = _norm_err(mutant, f_fd)
        results[name] = {"err": err, "detected": err > DERIV_LIMIT}
        return err > DERIV_LIMIT

    detected("sign_reversal", -ev.vertex_forces)
    detected("zero_force", np.zeros_like(ev.vertex_forces))

    spur = ev.vertex_forces.copy()
    spur[0] += np.array([1e-6, 0.0, 0.0])   # >> limit, << O(1) forces
    detected("spurious_vertex_force", spur)

    # THE DISCRIMINATOR: the frozen-normal law (signed area vs import normal),
    # identical to ca_triangle.area_grads' formula, evaluated after rotating
    # the geometry 90 degrees about z. At the rest pose it coincides with the
    # true law; after rotation the normals differ and it must fail.
    c90, s90 = 0.0, 1.0
    Rz = np.array([[c90, -s90, 0.0], [s90, c90, 0.0], [0.0, 0.0, 1.0]])
    Vr = V @ Rz.T
    n0 = ser.evaluate_surface(V, F, 1.0).normals        # frozen at REST pose
    a, b, c = Vr[F[:, 0]], Vr[F[:, 1]], Vr[F[:, 2]]
    grad_a = 0.5 * np.cross(n0, c - b)
    grad_b = 0.5 * np.cross(n0, a - c)
    grad_c = 0.5 * np.cross(n0, b - a)
    corner = -np.stack([grad_a, grad_b, grad_c], axis=1)  # (nF,3,3)
    frozen_vf = np.zeros_like(Vr)
    np.add.at(frozen_vf, F.reshape(-1), corner.reshape(-1, 3))
    _, f_fd_rot = heron_eval(Vr, F, 1.0)
    err = _norm_err(frozen_vf, f_fd_rot)
    results["frozen_normal_after_rotation"] = {"err": err,
                                               "detected": err > DERIV_LIMIT}
    # control: the CURRENT-normal law on the same rotated mesh must still pass
    ev_rot = ser.evaluate_surface(Vr, F, 1.0)
    err_rot = _norm_err(ev_rot.vertex_forces, f_fd_rot)
    results["current_normal_control_still_passes"] = {
        "err": err_rot, "detected": err_rot > DERIV_LIMIT}

    ok = (all(results[k]["detected"] for k in
              ("sign_reversal", "zero_force", "spurious_vertex_force",
               "frozen_normal_after_rotation"))
          and not results["current_normal_control_still_passes"]["detected"])
    return {"pass": ok, "limit": DERIV_LIMIT, "controls": results}


# ── F4: the refusal set ──────────────────────────────────────────────────────

@port_test(
    "F4_rejections",
    "Every malformed input raises InvalidSurface with the NAMED reason: "
    "malformed indices, nonfinite positions, nonfinite gamma, negative gamma, "
    "empty faces, repeated-vertex face, collapsed triangle, near-degenerate "
    "triangle (|cross| <= 64*e*max_edge^2). No valid fixture is refused.",
    "A malformed input is accepted, is refused under the wrong name, or a "
    "valid fixture is refused.")
def f4_rejections() -> dict:
    V, F = unit_octahedron()
    cases = []  # (case name, callable, expected reason)

    def _mut_indices():
        Fb = F.copy(); Fb[0, 0] = 99
        ser.evaluate_surface(V, Fb, 1.0)
    cases.append(("indices_out_of_range", _mut_indices,
                  ser.RejectionReason.MALFORMED_INDICES))

    def _mut_nonfinite_pos():
        Vb = V.copy(); Vb[2, 1] = np.nan
        ser.evaluate_surface(Vb, F, 1.0)
    cases.append(("nan_positions", _mut_nonfinite_pos,
                  ser.RejectionReason.NONFINITE_POSITIONS))

    def _mut_neg_gamma():
        ser.evaluate_surface(V, F, -0.5)
    cases.append(("negative_gamma", _mut_neg_gamma,
                  ser.RejectionReason.NEGATIVE_GAMMA))

    def _mut_nan_gamma():
        ser.evaluate_surface(V, F, np.nan)
    cases.append(("nan_gamma", _mut_nan_gamma,
                  ser.RejectionReason.NONFINITE_GAMMA))

    def _mut_empty():
        ser.evaluate_surface(V, np.zeros((0, 3), dtype=np.int64), 1.0)
    cases.append(("empty_faces", _mut_empty, ser.RejectionReason.EMPTY_FACES))

    def _mut_repeat():
        Fb = F.copy(); Fb[3] = [0, 0, 1]
        ser.evaluate_surface(V, Fb, 1.0)
    cases.append(("repeated_vertex", _mut_repeat,
                  ser.RejectionReason.REPEATED_VERTEX))

    def _mut_collapsed():
        # all three vertices identical: exact zero cross product
        Vb = np.array([[0., 0., 0.], [1., 0., 0.], [0., 1., 0.], [0., 0., 0.]])
        ser.evaluate_surface(Vb, np.array([[3, 3, 3]]), 1.0)
    cases.append(("collapsed_repeated", _mut_collapsed,
                  ser.RejectionReason.REPEATED_VERTEX))

    def _mut_collapsed2():
        Vb = np.array([[0., 0., 0.], [1., 0., 0.], [2., 0., 0.]])
        ser.evaluate_surface(Vb, np.array([[0, 1, 2]]), 1.0)
    cases.append(("collinear_collapsed", _mut_collapsed2,
                  ser.RejectionReason.COLLAPSED_TRIANGLE))

    def _mut_near_degenerate():
        # sliver BELOW the derived floor: height 1e-15 with unit edges gives
        # |cross| ~ 1e-15 < floor = 64*e*max_edge^2 ~ 1.42e-14. (The 2026-09-06
        # run caught the ORIGINAL fixture at h=1e-13 being rightly ACCEPTED:
        # its |cross| = 1e-13 sits 5.6x ABOVE the floor I derived -- a fixture
        # bug against my own floor law, not a tolerance change.)
        Vb = np.array([[0., 0., 0.], [1., 0., 0.], [0.5, 1e-15, 0.]])
        ser.evaluate_surface(Vb, np.array([[0, 1, 2]]), 1.0)
    cases.append(("near_degenerate_sliver", _mut_near_degenerate,
                  ser.RejectionReason.NEAR_DEGENERATE))

    rows = {}
    ok = True
    for name, fn, want in cases:
        try:
            fn()
            rows[name] = {"refused": False, "reason": None}
            ok = False
        except ser.InvalidSurface as ex:
            good = ex.reason == want
            rows[name] = {"refused": True, "reason": ex.reason, "expected": want}
            ok = ok and good
        except Exception as ex:  # a crash is not a refusal
            rows[name] = {"refused": True, "reason": f"WRONG-TYPE {type(ex).__name__}"}
            ok = False

    # valid fixtures must NOT be refused (a refusal-happy instrument is also broken)
    try:
        ser.evaluate_surface(*unit_octahedron(), 1.0)
        ser.evaluate_surface(*distorted_octa1(), 0.0)   # zero gamma is legal
        rows["valid_fixtures_accepted"] = {"refused": False}
    except ser.InvalidSurface as ex:
        rows["valid_fixtures_accepted"] = {"refused": True, "reason": ex.reason}
        ok = False
    return {"pass": ok, "cases": rows}


# ── F5: sphere refinement to 2*gamma/R ───────────────────────────────────────

@port_test(
    "F5_sphere_refinement",
    "Subdivided unit octahedra (levels 0..4) converge to the Young-Laplace "
    "pressure 2*gamma/R in generalized pressure P = -sum(F.x)/(3V): the error "
    "decreases strictly with level and is <= 1% at level 4.",
    "The error sequence is not strictly decreasing, or the level-4 error "
    "exceeds 1%. (1% is a discretization gate, not a material constant.)")
def f5_sphere_refinement() -> dict:
    R, gam = 1.0, 1.0
    rows = {}
    errors = []
    for level in range(5):
        V, F = subdivide_to_sphere(*unit_octahedron(), level)
        ev = ser.evaluate_surface(V, F, gam)
        P = generalized_pressure(ev, V, F)
        err = abs(P - 2.0 * gam / R) / (2.0 * gam / R)
        errors.append(err)
        rows[level] = {"n_faces": int(F.shape[0]), "P_disc": P,
                       "rel_err": err}
    monotone = all(errors[i + 1] < errors[i] for i in range(len(errors) - 1))
    level4 = errors[-1] <= 0.01
    return {"pass": monotone and level4, "monotone": monotone,
            "level4_within_1pct": level4, "per_level": rows,
            "target": 2.0, "gamma": gam, "R": R}


# ── F6: the equal-area distortion counterexample ─────────────────────────────

@port_test(
    "F6_equal_area_distortion",
    "Applying diag(2, 1/2) to a flat unit square (two triangles) preserves "
    "every area (ratio 1 within 512*e) while the tangent-plane metric differs "
    "from the identity by diag(4, 1/4) -- area alone is not the solid strain.",
    "The area ratio deviates from 1 beyond 512*e, or the metric fails to show "
    "the diag(4, 1/4) deviation -- either invalidates the counterexample.")
def f6_equal_area_distortion() -> dict:
    V, F = flat_square()
    T = np.diag([2.0, 0.5, 1.0]).astype(np.float64)
    Vc = V @ T.T
    ev_rest = ser.evaluate_surface(V, F, 1.0)
    ev_cur = ser.evaluate_surface(Vc, F, 1.0)
    ratio_dev = float(np.abs(ev_cur.areas / ev_rest.areas - 1.0).max())

    met = ser.triangle_metric(V, Vc, F)
    # FRAME LAW (2026-09-06, found by this check's own failure): C is expressed
    # in EACH triangle's own tangent frame (first edge = u), not world axes.
    # Tri 0 (axis-aligned first edge) reads diag(4, 1/4) exactly; tri 1 (the
    # diagonal is its first edge) reads the same distortion in its own 45 deg
    # basis. The frame-FREE invariant is det(C) = (A_cur/A_rest)^2 -- that is
    # the counterexample's content: area preserved (ratio 1) while the metric
    # differs from identity. Asserted with no tolerance widening.
    tri0_dev = float(np.abs(met.C[0] - np.diag([4.0, 0.25])).max())
    ar = ev_cur.areas / ev_rest.areas
    det_dev = float(np.abs(np.linalg.det(met.C) - ar ** 2).max())
    met_dev = float(np.abs(met.C - np.eye(2)[None, :, :]).max())
    # control: the undeformed square must read C = I to the same allowance
    met_id = ser.triangle_metric(V, V, F)
    id_dev = float(np.abs(met_id.C - np.eye(2)[None, :, :]).max())
    return {"pass": bool(ratio_dev <= INV_LIMIT and tri0_dev <= INV_LIMIT
                         and det_dev <= INV_LIMIT and met_dev > 0.5
                         and id_dev <= INV_LIMIT),
            "area_ratio_max_dev": ratio_dev,
            "tri0_dev_from_diag4_quarter": tri0_dev,
            "detC_vs_area_ratio_sq_dev": det_dev,
            "metric_dev_from_identity": met_dev,
            "identity_control_dev": id_dev, "limit": INV_LIMIT,
            "frame_law": "C is per-triangle-frame; tri0's frame is world "
                         "axes (first edge), tri1's is its diagonal -- the "
                         "frame-free invariant is det(C) = (area ratio)^2"}


# ── F7: prescribed moving surface (a moving input control, NOT a simulation) ─

@port_test(
    "F7_moving_geometry_control",
    "A prescribed analytic moving closed surface (2 s, 121 samples at 60/s: "
    "breathing radius + rigid rotation of the unit octahedron) satisfies the "
    "F1 force/energy agreement at EVERY sample under the same derivative "
    "limit. This is a moving input control, not an integrated simulation and "
    "not substitute engine footage.",
    "Any single sample exceeds the F1 limit.")
def f7_moving_geometry_control() -> dict:
    V0, F = unit_octahedron()
    dt, T = 1.0 / 60.0, 2.0
    n = int(round(T / dt)) + 1          # 121 endpoints
    worst, worst_t = 0.0, -1.0
    for s in range(n):
        t = s * dt
        R_b = 1.0 + 0.15 * math.sin(2.0 * math.pi * t / T)
        th = 2.0 * math.pi * t / T
        c, sn = math.cos(th), math.sin(th)
        Rz = np.array([[c, -sn, 0.0], [sn, c, 0.0], [0.0, 0.0, 1.0]])
        V = (V0 * R_b) @ Rz.T
        ev = ser.evaluate_surface(V, F, 1.0)
        _, f_fd = heron_eval(V, F, 1.0)
        err = _norm_err(ev.vertex_forces, f_fd)
        if err > worst:
            worst, worst_t = err, t
    return {"pass": worst <= DERIV_LIMIT, "worst": worst, "at_t": worst_t,
            "limit": DERIV_LIMIT, "n_samples": n,
            "sample_rate_hz": 1.0 / dt,
            "honesty": "prescribed input control; no dynamics integrated"}


# ── F8: adjacency gather vs independent scatter (work-list step 12) ──────────

@port_test(
    "F8_adjacency_gather_matches_scatter",
    "The CSR vertex->corner adjacency is complete and deterministic (every "
    "corner appears exactly once; fixed vertex/face/slot order) and the "
    "gathered vertex forces match an independent np.add.at scatter on a "
    "shared-vertex mesh within 512*e.",
    "A corner is lost or duplicated, the order is not the declared fixed "
    "order, or gather and scatter disagree beyond 512*e.")
def f8_adjacency_gather_matches_scatter() -> dict:
    V, F = distorted_octa1()
    ev = ser.evaluate_surface(V, F, 1.0)
    offsets, corner_idx = ser.build_vertex_corner_adjacency(F, V.shape[0])

    # completeness: every corner exactly once
    counts = np.diff(offsets)
    ok_complete = int(counts.sum()) == 3 * F.shape[0] and int(offsets[0]) == 0
    # determinism: corner indices inside each segment ascend (face, then slot)
    seg_sorted = all(np.all(np.diff(corner_idx[offsets[v]:offsets[v + 1]]) > 0)
                     for v in range(V.shape[0]))

    # independent scatter (different order: face-major additions)
    scatter = np.zeros_like(V)
    np.add.at(scatter, F.reshape(-1), ev.face_corner_forces.reshape(-1, 3))
    dev = _norm_err(ev.vertex_forces, scatter)
    return {"pass": bool(ok_complete and seg_sorted and dev <= INV_LIMIT),
            "complete": ok_complete, "segments_sorted": seg_sorted,
            "gather_vs_scatter_dev": dev, "limit": INV_LIMIT,
            "note": "gather (CSR reduceat) and scatter (add.at) sum the same "
                    "values in different orders; 512*e is the algebraic "
                    "allowance, exact bit equality is not claimed"}


expect(EXPECTED_CHECKS)


def main(argv: list[str]) -> int:
    from port_registry import TESTS
    from evidence_output import (EVIDENCE_REFUSAL_EXIT, EvidencePathExists,
                                 resolve_evidence_path)
    # EVIDENCE LAW FIRST (G01-R3 D6): resolve the output path BEFORE any
    # check runs. A run aimed at an existing file refuses (exit 2) without
    # computing or writing anything; the default is a unique stamped file.
    out_dir = Path(__file__).resolve().parent.parent / "agent_logs" / \
        "glm_foundation_g01"
    out_dir.mkdir(parents=True, exist_ok=True)
    try:
        out_path = resolve_evidence_path(out_dir,
                                         "surface_energy_checks_results",
                                         argv)
    except EvidencePathExists as ex:
        print(f"REFUSAL: {ex}")
        print("Nothing was computed or written; historical evidence intact.")
        return EVIDENCE_REFUSAL_EXIT
    order = ["F1_force_vs_heron_fd", "F2_invariances", "F3_negative_controls",
             "F4_rejections", "F5_sphere_refinement", "F6_equal_area_distortion",
             "F7_moving_geometry_control", "F8_adjacency_gather_matches_scatter"]
    results = {}
    failed = 0
    print("=" * 100)
    print("  SURFACE-ENERGY REFERENCE: the registered falsifier battery (G01)")
    print(f"  limits: FD {DERIV_LIMIT:.6e} = 256*e^(2/3);  invariance "
          f"{INV_LIMIT:.6e} = 512*e;  e = {EPS:.6e}")
    print("=" * 100)
    for name in order:
        rec = TESTS[name]
        print(f"\n[{name}]\n  STATEMENT : {rec['statement'][:96]}...")
        try:
            r = rec["fn"]()
            results[name] = r
            verdict = "PASS" if r.get("pass") else "FAIL"
            if not r.get("pass"):
                failed += 1
            meas = {k: v for k, v in r.items()
                    if k not in ("pass",) and not isinstance(v, dict)}
            print(f"  FALSIFIER : {rec['falsifier'][:96]}...")
            print(f"  -> {verdict}   {json.dumps(meas, default=str)[:300]}")
        except Exception as ex:  # a crashing check is a FAIL, never a skip
            failed += 1
            results[name] = {"pass": False, "error": f"{type(ex).__name__}: {ex}"}
            print(f"  -> FAIL (exception) {type(ex).__name__}: {ex}")
    print("\n" + "-" * 100)
    print(f"  {len(order) - failed}/{len(order)} checks PASS. "
          f"Tolerances are preregistered; none was widened after seeing results.")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps({"results": results, "failed": failed}, indent=1, default=str),
        encoding="utf-8")
    print(f"  raw: {out_path}")
    if "--json" in argv:
        print(json.dumps(results, indent=1, default=str))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
