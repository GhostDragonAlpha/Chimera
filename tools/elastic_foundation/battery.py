"""battery.py -- the falsification battery for the elastic foundation (BP-ELASTIC-FOUNDATION §D).

Every class F0..F12 + the six mutations, each a preregistered membrane (PREREGISTRATION.md).
Budgets: ALG = 512*eps, FD_LIMIT = 256*eps**(2/3) (DERIVATION.md section 10). A check returns a
Check record; the battery RUNNER decides PASS/FAIL. Nothing here writes evidence files.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

import numpy as np

from . import geometry as G
from . import law as L
from . import materials as M

EPS = float(np.finfo(np.float64).eps)
ALG = 512.0 * EPS                      # algebraic invariance budget
FD_LIMIT = 256.0 * EPS ** (2.0 / 3.0)  # finite-difference budget
FD_H = EPS ** (1.0 / 3.0)


@dataclass
class Check:
    tag: str
    name: str
    passed: bool
    facts: Dict[str, Any]
    message: str = ""


def energy_scale(rest: G.RestGeometry, mat: M.ElasticMaterial2D) -> float:
    return mat.stiffness_scale * rest.total_area0


def force_scale(rest: G.RestGeometry, mat: M.ElasticMaterial2D) -> float:
    lbar = float(np.max(rest.max_edge0)) if rest.n_faces else 1.0
    return mat.stiffness_scale * rest.total_area0 / lbar


def torque_scale(rest: G.RestGeometry, mat: M.ElasticMaterial2D) -> float:
    lbar = float(np.max(rest.max_edge0)) if rest.n_faces else 1.0
    return lbar * force_scale(rest, mat)


# ---------------------------------------------------------------- fixtures
NONALIGN = np.array([[0.10, 0.20, 0.00],
                     [1.00, 0.05, 0.00],
                     [0.15, 0.90, 0.00]], dtype=np.float64)
STRETCH = np.array([[1.2, 0.0, 0.0], [0.0, 0.93, 0.0], [0.0, 0.0, 1.0]], dtype=np.float64)
SHEAR = np.array([[1.0, 0.35, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]], dtype=np.float64)
TRANSLATE = np.array([0.27, -0.13, 0.05], dtype=np.float64)


def tri_geom(positions=NONALIGN, faces=((0, 1, 2),)):
    return G.build_rest_geometry(positions, faces, build_info={"units": "m", "kind": "battery"})


def mat(nu=0.3, E=1.0, h=1.0):
    return M.synthetic(E=E, nu=nu, h=h)


# ---------------------------------------------------------------- F0 (membrane preamble)
def f0_membrane() -> Check:
    return Check("F0", "membrane preamble", True,
                 {"statement": "preregistered on record", "source":
                  "docs/evidence/elastic_foundation/PREREGISTRATION.md"})


# ---------------------------------------------------------------- F1 rest state
def f1_rest() -> Check:
    facts = {}
    ok = True
    for name, geom, material in (("single", tri_geom(), mat()),
                                 ("2x2 patch", _patch_geom(2, 2), mat(0.33, 2.0, 0.1))):
        ev = L.evaluate_elastic(geom, material, geom.positions)
        u_lim = ALG * energy_scale(geom, material)
        f_lim = ALG * force_scale(geom, material)
        Emax = float(np.max(np.abs(ev.per_face.E)))
        Cmax = float(np.max(np.abs(ev.per_face.C - np.eye(2))))
        facts[f"{name}_energy"] = ev.energy
        facts[f"{name}_Emax"] = Emax
        facts[f"{name}_Cmax"] = Cmax
        facts[f"{name}_fmax"] = ev.max_abs_vertex_force
        facts[f"{name}_u_lim"] = u_lim
        facts[f"{name}_f_lim"] = f_lim
        ok = ok and (abs(ev.energy) <= u_lim and ev.max_abs_vertex_force <= f_lim)
    return Check("F1", "rest-state energy/stress/force", ok, facts)


def _patch(nx, ny):
    pos, faces = G.unit_make_grid(1.0, 1.0, nx, ny, z0=0.0)
    return G.build_rest_geometry(pos, faces, build_info={"units": "m", "kind": "battery"}), pos, faces


def _patch_geom(nx, ny):
    return _patch(nx, ny)[0]


# ---------------------------------------------------------------- F2 rotation/translation invariance
def _rigid(x, axis, angle, t):
    a = np.asarray(axis, dtype=np.float64) / np.linalg.norm(axis)
    c = math.cos(angle); s = math.sin(angle)
    K = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]], dtype=np.float64)
    R = np.eye(3) + s * K + (1 - c) * (K @ K)
    return (x @ R.T) + t, R


def f2_rotation() -> Check:
    geom = tri_geom()
    material = mat()
    uc = energy_scale(geom, material)
    fc = force_scale(geom, material)
    facts = {}

    # (a) pure rigid motion of the REST pose -> no strain/no energy
    rot_rest, R = _rigid(geom.positions, (1.0, 0.3, 2.0), 0.61, (1.3, -0.7, 0.2))
    ev_a = L.evaluate_elastic(geom, material, rot_rest)
    facts["a_energy"] = ev_a.energy
    facts["a_lim"] = ALG * uc
    a_ok = abs(ev_a.energy) <= ALG * uc and ev_a.max_abs_vertex_force <= ALG * fc

    # (b) deformed pose mapped rigidly: energy invariant, forces rotate with the body
    y = G.apply_affine(geom.positions, STRETCH, t=TRANSLATE)
    ev0 = L.evaluate_elastic(geom, material, y)
    yr, R = _rigid(y, (0.0, 1.0, 0.4), 0.9, (0.5, 0.8, -0.3))
    evb = L.evaluate_elastic(geom, material, yr)
    du = abs(evb.energy - ev0.energy)
    df = float(np.max(np.abs(evb.vertex_forces - (ev0.vertex_forces @ R.T))))
    facts["b_du"] = du
    facts["b_df"] = df
    facts["b_u_lim"] = ALG * uc
    facts["b_f_lim"] = ALG * fc
    b_ok = du <= ALG * uc and df <= ALG * fc

    # (c) finite rotation is NOT small strain: huge gap between E and the linear-strain law
    rot90, _ = _rigid(geom.positions, (0.0, 0.0, 1.0), 0.73, (0.0, 0.0, 0.0))
    ev_rot = L.evaluate_elastic(geom, material, rot90)
    ev_rot_lin = L.evaluate_elastic(geom, material, rot90, _mutations={"linear_strain": True})
    facts["c_elastic_energy"] = ev_rot.energy
    facts["c_linear_strain_energy"] = ev_rot_lin.energy
    c_ok = (abs(ev_rot.energy) <= ALG * uc
            and ev_rot_lin.energy >= 1e-3
            and (ev_rot_lin.energy / max(abs(ev_rot.energy), 1e-300)) >= 1e5)

    return Check("F2", "rigid translation and finite-rotation invariance", a_ok and b_ok and c_ok, facts)


# ---------------------------------------------------------------- F3 gradient vs finite differences
def f3_fd() -> Check:
    geom = tri_geom()
    material = mat()
    y = G.apply_affine(geom.positions, STRETCH, t=TRANSLATE)
    ev = L.evaluate_elastic(geom, material, y)
    want = ev.vertex_forces  # -grad U
    nv = geom.n_vertices

    def energy_at(p):
        return L.evaluate_elastic(geom, material, p).energy

    hvals = [2e-7, 5e-7, 1e-6, 3e-6, 1e-5, 3e-5, 1e-4, 1e-3]
    errs = []
    for h in hvals:
        g = np.zeros_like(want)
        for i in range(nv):
            for d in range(3):
                pp = np.array(y, copy=True); pm = np.array(y, copy=True)
                pp[i, d] += h; pm[i, d] -= h
                # gradient of U is -force; we compare the FD FORCE with the analytic force
                g[i, d] = -(energy_at(pp) - energy_at(pm)) / (2.0 * h)
        errs.append(float(np.max(np.abs(g - want)) / max(float(np.max(np.abs(want))), 1e-300)))
    hbest = hvals[int(np.argmin(errs))]
    best = min(errs)
    # cancellation analysis: err ~ a*h^2 (truncation on the right arm) + b*eps/h (rounding on
    # the left arm). Fit a from the largest two steps, b from the smallest two, then predict
    # the optimum h* = (b*eps/(2a))^(1/3) BEFORE the run (falsifier: the sweep must show the
    # predicted V-shape, each arm scaling with its own law).
    a = (errs[-1] - errs[-2]) / (hvals[-1] ** 2 - hvals[-2] ** 2)
    b = (errs[1] - errs[0]) / (EPS / hvals[1] - EPS / hvals[0])
    if a <= 0 or not np.isfinite(a):
        a = 1.0
    if b < 0 or not np.isfinite(b):
        b = max(errs[0] * hvals[0] / EPS, 1e-300)
    hstar = (b * EPS / (2.0 * a)) ** (1.0 / 3.0)
    est_best = a * hstar ** 2 + b * EPS / hstar
    # left arm must be rounding-dominated (err ~ 1/h -> ratio ~ h_i/h_j), right arm
    # truncation-dominated (err ~ h^2 -> ratio ~ 100 per decade)
    round_arm = errs[0] / errs[1]            # expect ~ h1/h0 = 2.5
    trunc_arm = errs[-1] / errs[-2]          # expect ~ (h_hi/h_lo)^2 = 100
    ok = (best <= FD_LIMIT
          and min(hvals) <= hstar <= max(hvals) * 10
          and hbest <= 10 * hstar and hstar <= 10 * hbest
          and 1.1 <= round_arm <= 12 and 20 <= trunc_arm <= 500
          and est_best <= 10 * best)
    return Check("F3", "analytic force vs central-difference energy gradient", ok,
                 {"errs": errs, "hvals": hvals, "hbest": hbest, "best": best,
                  "fd_limit": FD_LIMIT, "trunc_coef_a": a, "round_coef_b": b,
                  "predicted_hstar": hstar, "predicted_best": est_best,
                  "round_arm_ratio": round_arm, "trunc_arm_ratio": trunc_arm})


# ---------------------------------------------------------------- F4 net force and torque zero
def f4_balance() -> Check:
    facts = {}
    ok = True
    pgeom, ppos, _ = _patch(3, 2)
    y_patch = G.apply_affine(ppos, np.diag([1.15, 0.9, 1.0]))
    for name, geom, material, y in (
            ("single", tri_geom(), mat(), G.apply_affine(NONALIGN, SHEAR)),
            ("patch", pgeom, mat(), y_patch)):
        ev = L.evaluate_elastic(geom, material, y)
        sf = ALG * force_scale(geom, material)
        st = ALG * torque_scale(geom, material)
        Fnet = float(np.max(np.abs(np.sum(ev.vertex_forces, axis=0))))
        torque = float(np.max(np.abs(np.sum(np.cross(y, ev.vertex_forces), axis=0))))
        facts[name + "_fnet"] = Fnet
        facts[name + "_torque"] = torque
        facts[name + "_sf"] = sf
        facts[name + "_st"] = st
        ok = ok and Fnet <= sf and torque <= st
    return Check("F4", "net internal force and torque balance", ok, facts)


# ---------------------------------------------------------------- F5 uniform extension / shear analytic
def _analytics(geom, S, mat):
    """Independent closed form for affine current maps y = S x (planar in z=0)."""
    X = np.stack([geom.t1, geom.t2], axis=2)      # (nF,3,2) basis
    F = np.einsum("ij,fjk->fik", S, X)            # (nF,3,2)
    C = np.einsum("fji,fjk->fik", F, F)
    E = 0.5 * (C - np.eye(2))
    trE = E[:, 0, 0] + E[:, 1, 1]
    trE2 = E[:, 0, 0] ** 2 + 2 * E[:, 0, 1] ** 2 + E[:, 1, 1] ** 2
    Wbar = 0.5 * mat.lambda_bar * trE ** 2 + mat.mu_bar * trE2
    S2 = np.empty_like(E)
    S2[:, 0, 0] = mat.lambda_bar * trE + 2 * mat.mu_bar * E[:, 0, 0]
    S2[:, 1, 1] = mat.lambda_bar * trE + 2 * mat.mu_bar * E[:, 1, 1]
    S2[:, 0, 1] = 2 * mat.mu_bar * E[:, 0, 1]
    S2[:, 1, 0] = S2[:, 0, 1]
    P = F @ S2
    u1 = np.einsum("fij,fj->fi", P, geom.B[:, 0, :])
    u2 = np.einsum("fij,fj->fi", P, geom.B[:, 1, :])
    A0 = geom.areas0
    corner = np.stack([A0[:, None] * (u1 + u2), A0[:, None] * (-u1), A0[:, None] * (-u2)], axis=1)
    return C, E, Wbar, u1, u2, corner


def f5_analytic() -> Check:
    facts = {}
    ok = True
    geom = tri_geom()
    material = mat()
    for tag, S in (("biaxial", STRETCH), ("shear", SHEAR)):
        y = G.apply_affine(NONALIGN, S)
        ev = L.evaluate_elastic(geom, material, y)
        C, E, Wbar, u1, u2, corner = _analytics(geom, S, material)
        dC = float(np.max(np.abs(ev.per_face.C - C)))
        dE = float(np.max(np.abs(ev.per_face.E - E)))
        dW = float(np.max(np.abs(ev.per_face.Wbar - Wbar)))
        dCorner = float(np.max(np.abs(ev.corner_forces - corner)))
        scale_c = max(1.0, float(np.max(np.abs(ev.per_face.C))))
        scale_w = max(1.0, float(np.max(np.abs(Wbar))))
        scale_f = max(1.0, float(np.max(np.abs(ev.corner_forces))))
        facts[tag + "_dC"] = dC
        facts[tag + "_dE"] = dE
        facts[tag + "_dW"] = dW
        facts[tag + "_dCorner"] = dCorner
        ok = ok and (dC / scale_c <= ALG and dE / scale_c <= ALG and dW / scale_w <= ALG
                     and dCorner / scale_f <= ALG)
    return Check("F5", "uniform extension and shear vs analytic closed form", ok, facts)


# ---------------------------------------------------------------- F6 stiffness and thickness scaling
def f6_scaling() -> Check:
    geom = tri_geom()
    base = mat(E=1.0, nu=0.3, h=1.0)
    y = G.apply_affine(NONALIGN, STRETCH, t=TRANSLATE)
    ev0 = L.evaluate_elastic(geom, base, y)
    facts = {}
    ok = True
    cases = (("E2", mat(E=2.0), 2.0, 2.0, 2.0),
             ("E0.1", mat(E=0.1), 0.1, 0.1, 0.1),
             ("h2", mat(E=1.0, h=2.0), 1.0, 1.0, 0.5))
    for tag, material, expect_u, expect_f, expect_wvol in cases:
        ev = L.evaluate_elastic(geom, material, y)
        ru = ev.energy / ev0.energy if ev0.energy != 0 else 1.0
        dU = abs(ru - expect_u) / max(expect_u, 1e-300)
        dF = float(np.max(np.abs(ev.vertex_forces - expect_f * ev0.vertex_forces))
                   / max(float(np.max(np.abs(ev0.vertex_forces))), 1e-300))
        rw = ev.per_face.w_vol[0] / ev0.per_face.w_vol[0]
        dVol = abs(rw - expect_wvol) / max(expect_wvol, 1e-300)
        facts[tag + "_ratio_u"] = ru
        facts[tag + "_dU"] = dU
        facts[tag + "_dF"] = dF
        facts[tag + "_ratio_wvol"] = rw
        facts[tag + "_dVol"] = dVol
        ok = ok and dU <= ALG and dF <= ALG and dVol <= ALG
    return Check("F6", "stiffness and thickness scaling", ok, facts)


# ---------------------------------------------------------------- F7 frame independence, isotropic limit, orthotropic refusal
def f7_frame_isotropic() -> Check:
    facts = {}
    material = mat()
    geom0 = tri_geom()
    cur0 = G.apply_affine(NONALIGN, STRETCH, t=TRANSLATE)
    ev0 = L.evaluate_elastic(geom0, material, cur0)
    uc = energy_scale(geom0, material)
    fc = force_scale(geom0, material)
    ok = True
    ref_C = ev0.per_face.C.copy()
    for ang in (math.pi / 6, math.pi / 2):
        c, s = math.cos(ang), math.sin(ang)
        # Rigid re-placement of the WHOLE configuration (rest and current rotated together):
        # the reference (t1,t2) basis rotates physically with the body, so the strain
        # TENSORS are coefficient-identical and the world vertex forces rotate exactly.
        Rz = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]], dtype=np.float64)
        rest_r = NONALIGN @ Rz.T
        cur_r = (NONALIGN @ STRETCH.T) @ Rz.T + TRANSLATE
        geom_r = tri_geom(positions=rest_r)
        ev_r = L.evaluate_elastic(geom_r, material, cur_r)
        dU = abs(ev_r.energy - ev0.energy) / max(abs(ev0.energy), 1e-300)
        dF = float(np.max(np.abs(ev_r.vertex_forces - ev0.vertex_forces @ Rz.T))) / fc
        dC = float(np.max(np.abs(ev_r.per_face.C - ref_C)))
        facts[f"ang{ang}_dU"] = dU
        facts[f"ang{ang}_dF"] = dF
        facts[f"ang{ang}_dC"] = dC
        ok = ok and (dU <= ALG and dF <= ALG and dC <= ALG)
    # handedness no-leak is f10's reverse leg (reference-basis t2 flip)
    # orthotropic refusal
    try:
        M.require_isotropic(material)
        facts["orthotropic"] = "NO_REFUSAL"
        ok = False
    except M.InvalidMaterial as e:
        facts["orthotropic"] = e.reason
        ok = ok and e.reason == M.MaterialReason.ORTHOTROPIC_UNSUPPORTED
    # real-material refusal
    try:
        M.material_from_library("rock")
        facts["library_rock"] = "NO_REFUSAL"
        ok = False
    except M.InvalidMaterial as e:
        facts["library_rock"] = e.reason
        ok = ok and e.reason == M.MaterialReason.POISSON_RATIO_NOT_MEASURED
    return Check("F7", "material-axis rotation, isotropy and named orthotropic refusal", ok, facts)


# ---------------------------------------------------------------- F8 coordinate re-scaling
def f8_units() -> Check:
    geom = tri_geom()
    material = mat(E=1.0, nu=0.3, h=1.0)
    y = G.apply_affine(NONALIGN, STRETCH, t=TRANSLATE)
    ev = L.evaluate_elastic(geom, material, y)
    facts = {}
    ok = True
    for s in (1000.0, 0.37):
        geom_s = G.build_rest_geometry(geom.positions * s, geom.faces)
        evs = L.evaluate_elastic(geom_s, material, y * s)
        # Wbar and the strain tensors are per-area invariants; energy and force scale as
        # s^2 resp. s (rest and current re-scaled by s, material untouched, one unit system).
        dW = float(np.max(np.abs(evs.per_face.Wbar - ev.per_face.Wbar)))
        rW = max(float(np.max(np.abs(ev.per_face.Wbar))), 1e-300)
        dU = abs(evs.energy - s * s * ev.energy) / max(s * s * abs(ev.energy), 1e-300)
        dF = float(np.max(np.abs(evs.vertex_forces - s * ev.vertex_forces))
                   / max(s * float(np.max(np.abs(ev.vertex_forces))), 1e-300))
        facts[f"s{s}_dWbar"] = dW / rW
        facts[f"s{s}_dU"] = dU
        facts[f"s{s}_dF"] = dF
        ok = ok and dU <= 2 * ALG and dF <= 2 * ALG and dW <= 2 * ALG * rW
    return Check("F8", "coordinate re-scaling s: U -> s^2 U, f -> s f, Wbar invariant", ok, facts)


# ---------------------------------------------------------------- F9 refusals
def f9_invalid() -> Check:
    geom = tri_geom()
    material = mat()
    facts = {}
    ok = True

    def expect(refusal, fn, tag):
        nonlocal ok
        try:
            fn()
            facts[tag] = ("NO_REFUSAL", None)
            ok = False
        except (L.InvalidDeformation, L.InvalidGeometry, M.InvalidMaterial) as e:
            facts[tag] = (getattr(e, "reason", "?"), str(getattr(e, "message", e)))
            ok = ok and getattr(e, "reason", None) == refusal

    nan_y = np.array(NONALIGN, copy=True); nan_y[1, 2] = np.nan
    expect("nonfinite_positions", lambda: L.evaluate_elastic(geom, material, nan_y), "nan_pos")

    coll = np.array(NONALIGN, copy=True)
    coll[2] = 0.5 * (coll[0] + coll[1])
    expect("collapsed_triangle", lambda: L.evaluate_elastic(geom, material, coll), "collapsed")

    near = np.array(NONALIGN, copy=True)
    near[2] = 0.5 * (near[0] + near[1]) + np.array([0.0, 1e-15, 0.0])
    expect("near_degenerate_triangle", lambda: L.evaluate_elastic(geom, material, near), "near_degen")

    overflow = NONALIGN * 1e100
    expect("nonfinite_result", lambda: L.evaluate_elastic(geom, material, overflow), "overflow")

    for val, tag in ((0.0, "E0"), (-1.0, "Eneg"), (-1.0, "nu_-1"), (0.5, "nu_05"), (1.0, "nu_1"), (0.0, "h0")):
        if tag.startswith("E"):
            m = mat(E=val)
        elif tag.startswith("nu"):
            m = mat(nu=val)
        else:
            m = mat(h=val)
        expect("nonpositive_young_modulus" if tag.startswith("E") else
               ("poisson_out_of_range" if tag.startswith("nu") else "nonpositive_thickness"),
               lambda mm=m: L.evaluate_elastic(geom, mm, geom.positions), "mat_" + tag)

    # inverted-but-resolvable pose: finite energy, inverted flag set, NO exception
    Rmirr = np.diag([-1.0, 1.0, 1.0])           # reflection => det F < 0, |det F| = 1
    inv_y = NONALIGN @ Rmirr.T
    try:
        ev = L.evaluate_elastic(geom, material, inv_y)
        facts["inverted"] = (ev.per_face.inverted.tolist(), ev.energy, math.isfinite(ev.energy))
        ok = ok and bool(ev.per_face.inverted[0]) and math.isfinite(ev.energy)
    except Exception as e:
        facts["inverted"] = ("EXCEPTION", str(e))
        ok = False
    return Check("F9", "collapse, inversion, nonfinite, invalid-material refusal", ok, facts)


# ---------------------------------------------------------------- F10 winding / index changes
def f10_winding() -> Check:
    material = mat()
    facts = {}
    ok = True
    y = G.apply_affine(NONALIGN, STRETCH, t=TRANSLATE)

    perm_sets = [
        ("cyclic1", (1, 2, 0), lambda v: v[[1, 2, 0]]),
        ("cyclic2", (2, 0, 1), lambda v: v[[2, 0, 1]]),
        ("reverse", (0, 2, 1), lambda v: v[[0, 2, 1]]),
    ]
    pos0 = NONALIGN
    geom0 = tri_geom(positions=pos0, faces=((0, 1, 2),))
    ev0 = L.evaluate_elastic(geom0, material, y)
    for tag, perm, remap in perm_sets:
        geom_p = tri_geom(positions=remap(pos0), faces=((0, 1, 2),))
        evp = L.evaluate_elastic(geom_p, material, remap(y))
        # map evp vertex forces back onto the original vertex numbering
        invmap = np.argsort(perm)
        f_back = evp.vertex_forces[invmap]
        dU = abs(evp.energy - ev0.energy) / max(abs(ev0.energy), 1e-300)
        dF = float(np.max(np.abs(f_back - ev0.vertex_forces))
                   / max(float(np.max(np.abs(ev0.vertex_forces))), 1e-300))
        facts[tag + "_dU"] = dU
        facts[tag + "_dF"] = dF
        ok = ok and dU <= ALG and dF <= ALG

    # patch: reverse EVERY face -> handedness of per-face reference frames flips
    # (t2 flips with the normal). The isotropic sheet energy and the world vertex
    # forces are observables and must not change. This is the handedness no-leak leg.
    pos, faces = G.unit_make_grid(1.0, 1.0, 2, 2)
    yp = G.apply_affine(pos, STRETCH, t=TRANSLATE)
    geom_f = G.build_rest_geometry(pos, faces)
    geom_r = G.build_rest_geometry(pos, faces[:, ::-1])
    evf = L.evaluate_elastic(geom_f, material, yp)
    evr = L.evaluate_elastic(geom_r, material, yp)
    dUp = abs(evr.energy - evf.energy) / max(abs(evf.energy), 1e-300)
    dFp = float(np.max(np.abs(evr.vertex_forces - evf.vertex_forces)))
    f_lim = ALG * force_scale(geom_f, material)
    facts["patch_reverse_dU"] = dUp
    facts["patch_reverse_dF"] = dFp
    facts["patch_reverse_f_lim"] = f_lim
    ok = ok and dUp <= ALG and dFp <= f_lim
    return Check("F10", "winding and index changes under the declared convention", ok, facts)


# ---------------------------------------------------------------- F11 affine patch tests
def f11_affine_patch() -> Check:
    material = mat(E=1.0, nu=0.3, h=1.0)
    S = np.diag([1.15, 0.9, 1.0])
    t = (0.1, -0.2, 0.0)
    facts = {}
    ok = True
    densities = []
    # analytic reference density for the constant field: single-triangle Wbar
    ref_geom = tri_geom()
    ref_ev = L.evaluate_elastic(ref_geom, material, G.apply_affine(NONALIGN, S, t=t))
    density_ref = float(ref_ev.per_face.Wbar[0])
    facts["density_ref"] = density_ref
    for tag, nx, ny in (("A_3x2", 3, 2), ("B_3x2_flip", 3, 2), ("C_6x4", 6, 4)):
        pos, faces = G.unit_make_grid(2.0, 1.0, nx, ny)
        if tag == "B_3x2_flip":
            faces = _quad_flip(nx, ny)
        geom = G.build_rest_geometry(pos, faces)
        y = G.apply_affine(pos, S, t=t)
        ev = L.evaluate_elastic(geom, material, y)
        density = ev.energy / geom.total_area0
        densities.append(density)
        facts[tag + "_density"] = density
        # interior vertex forces: weak-form exactness for a constant stress field -> ~0,
        # for ANY conforming triangulation. This is the affine patch test. For a convex sheet
        # the interior is exactly the points with 1 <= i <= nx-1 and 1 <= j <= ny-1 in the x/y grid.
        W = 2.0; H = 1.0
        interior_mask = (np.abs(pos[:, 0] - 0.5 * W) < 0.5 * W - 1e-12) & \
                        (np.abs(pos[:, 1] - 0.5 * H) < 0.5 * H - 1e-12)
        if not np.any(interior_mask):
            raise AssertionError(f"no interior vertices in {tag} (grid nx={nx} ny={ny})")
        fint = float(np.max(np.abs(ev.vertex_forces[interior_mask])))
        f_lim = ALG * force_scale(geom, material)
        facts[tag + "_f_max_interior"] = fint
        facts[tag + "_f_lim"] = f_lim
        facts[tag + "_inverted_any"] = bool(np.any(ev.per_face.inverted))
        ok = ok and fint <= f_lim
    facts["densities"] = densities
    spread = (max(densities) - min(densities)) / max(max(densities), 1e-300)
    facts["density_spread"] = spread
    d_ref = (max(densities) - density_ref) / max(density_ref, 1e-300)
    facts["density_vs_ref"] = d_ref
    ok = ok and spread <= ALG and abs(d_ref) <= ALG
    return Check("F11", "affine patch tests across triangulations", ok, facts)


def _quad_flip(nx, ny):
    faces = []
    for j in range(ny):
        for i in range(nx):
            v00 = j * (nx + 1) + i
            v10 = v00 + 1
            v01 = (j + 1) * (nx + 1) + i
            v11 = v01 + 1
            if (i + j) % 2 == 0:
                faces.append((v00, v10, v01)); faces.append((v10, v11, v01))
            else:
                faces.append((v00, v10, v11)); faces.append((v00, v11, v01))
    return np.array(faces, dtype=np.int64)


def _nonaffine_field(pos, Lx=2.0, Ly=1.0):
    x = pos[:, 0]; y = pos[:, 1]
    u = 0.05 * np.sin(np.pi * x / Lx) * np.cos(np.pi * y / Ly)
    v = 0.12 * np.sin(np.pi * y / Ly) * np.cos(np.pi * x / Lx)
    return pos + np.stack([u, v, np.zeros_like(x)], axis=1)


def f12_nonuniform() -> Check:
    material = mat(E=1.0, nu=0.3, h=1.0)
    facts = {}
    Us = {}
    for tag, nx, ny in (("coarse", 2, 1), ("mid", 4, 2), ("fine", 8, 4)):
        pos, faces = G.unit_make_grid(2.0, 1.0, nx, ny)
        geom = G.build_rest_geometry(pos, faces)
        y = _nonaffine_field(pos)
        ev = L.evaluate_elastic(geom, material, y)
        Us[tag] = ev.energy
        facts[tag + "_U"] = ev.energy
        facts[tag + "_min_detF"] = float(np.min(ev.per_face.detF))
    # monotone convergence of the relative gaps
    g_cm = abs(Us["mid"] - Us["coarse"]) / max(abs(Us["coarse"]), 1e-300)
    g_mf = abs(Us["fine"] - Us["mid"]) / max(abs(Us["mid"]), 1e-300)
    facts["gap_coarse_mid"] = g_cm
    facts["gap_mid_fine"] = g_mf
    facts["coarse_fine_diff"] = abs(Us["fine"] - Us["coarse"]) / max(abs(Us["coarse"]), 1e-300)
    ok = (g_cm > g_mf > 0.0 and (g_cm / max(g_mf, 1e-300)) > 1.2
          and facts["coarse_fine_diff"] > ALG)
    return Check("F12", "nonuniform deformation and discretization dependence", ok, facts)


# ---------------------------------------------------------------- mutations (negative controls)
_MUTATION_TARGETS = {
    "sign": ("F3", "gradient FD"),
    "swap_corners": ("F3", "gradient FD"),
    "current_area_source": ("F5", "analytic uniform-extension energy"),
    "linear_strain": ("F2", "finite-rotation invariance"),
    "eulerian_frame": ("F2", "finite-rotation invariance"),
    "gather_drop": ("F4", "net-force balance on connected patch"),
}


def _fd_violation(geom, material, y, mut) -> float:
    """Return normalized max violation of the gradient identity under the mutated law."""
    ev = L.evaluate_elastic(geom, material, y, _mutations=mut)
    want = ev.vertex_forces
    h = 1e-5
    g = np.zeros_like(want)

    def energy_at(p):
        return L.evaluate_elastic(geom, material, p, _mutations=mut).energy

    for i in range(geom.n_vertices):
        for d in range(3):
            pp = np.array(y, copy=True); pm = np.array(y, copy=True)
            pp[i, d] += h; pm[i, d] -= h
            g[i, d] = -(energy_at(pp) - energy_at(pm)) / (2 * h)
    n = max(float(np.max(np.abs(want))), 1e-300)
    return float(np.max(np.abs(g - want)) / n), n


def _balance_violation(geom, material, y, mut) -> float:
    ev = L.evaluate_elastic(geom, material, y, _mutations=mut)
    return float(np.max(np.abs(np.sum(ev.vertex_forces, axis=0)))), float(np.sum(ev.vertex_forces) ** 0)


def _rotation_violation(geom, material, y, mut) -> float:
    """Normalized change of energy under a rigid rotation of a deformed pose."""
    ev0 = L.evaluate_elastic(geom, material, y, _mutations=mut)
    _, R = _rigid(y, (0.0, 1.0, 0.4), 0.9, (0.5, 0.8, -0.3))
    ev1 = L.evaluate_elastic(geom, material, (y @ R.T), _mutations=mut)
    n = max(max(abs(ev0.energy), abs(ev1.energy)), 1e-300)
    return float(abs(ev1.energy - ev0.energy) / n)


def _analytic_violation(geom, material, mut) -> float:
    y = G.apply_affine(NONALIGN, STRETCH)
    ev = L.evaluate_elastic(geom, material, y, _mutations=mut)
    C, E, Wbar, u1, u2, corner = _analytics(geom, STRETCH, material)
    return float(np.max(np.abs(ev.per_face.Wbar - Wbar)) / max(1e-300, float(np.max(np.abs(Wbar)))))


def mutations() -> List[Check]:
    geom = tri_geom()
    material = mat()
    y = G.apply_affine(NONALIGN, STRETCH, t=TRANSLATE)
    checks = []
    for mut_name, (target, why) in _MUTATION_TARGETS.items():
        mut = {mut_name: True}
        try:
            if target == "F3":
                v, n = _fd_violation(geom, material, y, mut)
                violated = v > FD_LIMIT
            elif target == "F5":
                v = _analytic_violation(geom, material, mut)
                violated = v > ALG
            elif target == "F2":
                v = _rotation_violation(geom, material, y, mut)
                violated = v > ALG
            elif target == "F4":
                v, _ = _balance_violation(geom, material, y, mut)
                violated = v > ALG * force_scale(geom, material)
            else:
                raise AssertionError(target)
        except Exception as e:    # a crash inside a mutation is a FAILED instrument
            violated = False
            v = float("nan")
            facts = {"error": repr(e), "why": why}
        else:
            facts = {"violation": v, "why": why, "must_fail": True}
        # The battery validates the INSTRUMENT: the mutation MUST be caught.
        caught = violated
        checks.append(Check(f"M{list(_MUTATION_TARGETS).index(mut_name) + 1}",
                            f"mutation {mut_name} (must fail {target}: {why})",
                            caught, facts,
                            "mutation must fail its independent check"))
    return checks


def run_all() -> List[Check]:
    checks = []
    for fn in (f0_membrane, f1_rest, f2_rotation, f3_fd, f4_balance, f5_analytic,
               f6_scaling, f7_frame_isotropic, f8_units, f9_invalid, f10_winding,
               f11_affine_patch, f12_nonuniform):
        try:
            checks.append(fn())
        except Exception as e:
            checks.append(Check(fn.__name__, fn.__doc__ or fn.__name__, False,
                                {"error": repr(e)}, "check crashed"))
    checks.extend(mutations())
    return checks


def summarize(checks: Sequence[Check]) -> Tuple[int, int, List[Check]]:
    failed = [c for c in checks if not c.passed]
    return len(checks), len(failed), failed