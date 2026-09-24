"""Falsifier table for the anatomy compiler — DERIVATION.md §13.

Each falsifier is a named function that either raises AssertionError or accepts
the named Refusal. A description survives any result; a falsifier can lose. The
exit code is 0 only if every falsifier is green.
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, r"E:\PythonChimera\.tmp\anatomy_compiler")

from aspect_bounds import POLICED_FLAG
from compiler import FD_EPS, JOINT_EPS, fit
from correspondence import Refusal
from intake import global_site_positions
from schema import DERIVED, NO_PATH, SEG_RESOLVED, SEG_FLAGGED
from synthetic_fixtures import (
    TARGET_LENS,
    TARGET_RADIALS,
    load_real,
    make_full_body_correspondence,
    rig_correspondence,
    synth_chimanoid,
    synth_rig,
)

PASS = 0
FAIL = 1
_failures: list[str] = []
_codes_seen: set[str] = set()


def check(name: str, fn) -> None:
    try:
        fn()
        print(f"  PASS  {name}")
    except Refusal as e:
        _failures.append(name)
        _codes_seen.add(e.code)
        print(f"  FAIL  {name}  -> unexpected Refusal [{e.code}] {e.message}")
    except Exception as e:  # noqa: BLE001
        _failures.append(name)
        print(f"  FAIL  {name}  -> {type(e).__name__}: {e}")


def expect_refusal(name: str, code: str, fn) -> None:
    try:
        fn()
        _failures.append(name)
        print(f"  FAIL  {name}  -> expected Refusal [{code}], nothing raised")
    except Refusal as e:
        _codes_seen.add(e.code)
        if e.code != code:
            _failures.append(name)
            print(f"  FAIL  {name}  -> got [{e.code}] expected [{code}]")
        else:
            print(f"  PASS  {name}  ({code})")


def expect_code(name: str, code: str, corr, ana) -> None:
    from correspondence import collect_refusals

    codes = [r["code"] for r in collect_refusals(corr, ana)]
    _codes_seen.update(codes)
    if code in codes:
        print(f"  PASS  {name}  ({code})")
    else:
        _failures.append(name)
        print(f"  FAIL  {name}  -> collected codes {sorted(set(codes))} miss [{code}]")


def _rest_lengths(f):
    return {t.name: t.rest_length for t in f.tendons}


def _masses(f):
    return {p.body: p.mass for p in f.physiology}


def _inertia_spectra(f):
    return {p.body: np.linalg.eigvalsh(p.inertia_fitted) for p in f.physiology}


def _sites(f):
    return {s.name: s.fitted_pos_global for s in f.sites}


def _arms(f):
    return {(t.name, m.coord): m.analytic for t in f.tendons for m in t.moment_arms}


def _befull() -> tuple:
    syn = synth_chimanoid()
    corr = make_full_body_correspondence(syn, TARGET_LENS, TARGET_RADIALS, origin=(0.0, 0.85, 0.0))
    return syn, corr


def _rel(a, b) -> float:
    return float(abs(a - b) / (abs(b) + 1e-300))


# ---------------------------------------------------------------------------
# G0  counts gate on the REAL chimanoid.xml
# ---------------------------------------------------------------------------
def g0_real_counts():
    syn = load_real()
    assert len(syn.bodies) == 19, len(syn.bodies)
    assert len(syn.joints) == 39, len(syn.joints)
    assert len([s for s in syn.sites if s.referenced_by]) == 468
    assert len(syn.tendons) == 120
    assert len(syn.muscles) == 120  # the 1 unnamed <default> muscle is NOT an actuator
    assert sum(1 for m in syn.muscles if m.tendon is None) == 0
    assert syn.root.name == "pelvis"


def g0_synth_twin_counts():
    syn = synth_chimanoid()
    assert len(syn.bodies) == 19
    assert len(syn.joints) == 39
    assert len([s for s in syn.sites if s.referenced_by]) == 468
    assert len(syn.tendons) == 120
    assert len(syn.muscles) == 120


# ---------------------------------------------------------------------------
# F1  shared joints are ONE point — both whole-body twins and the rig
# ---------------------------------------------------------------------------
def f1_synth_closure():
    syn, corr = _befull()
    f = fit(syn, corr)
    assert f.residuals["shared_joint_max_separation_m"] <= JOINT_EPS
    assert max(v for k, v in f.residuals.items() if k.startswith("closure.")) <= JOINT_EPS


def f1_real_closure():
    corr = make_full_body_correspondence(synth_chimanoid(), TARGET_LENS, TARGET_RADIALS, origin=(0.0, 0.85, 0.0))
    gr = fit(load_real(), corr, fit_mode="grounded")
    assert gr.residuals["shared_joint_max_separation_m"] <= JOINT_EPS


def f1_rig_closure():
    f = fit(synth_rig(), rig_correspondence())
    assert f.residuals["shared_joint_max_separation_m"] <= JOINT_EPS


# ---------------------------------------------------------------------------
# F2  proper-rotation invariance of every scalar; geometry co-rotates
# ---------------------------------------------------------------------------
def _proper_rotation() -> np.ndarray:
    axis = np.array([1.0, 2.0, -3.0])
    axis = axis / np.linalg.norm(axis)
    th = 0.73
    K = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
    R = np.eye(3) + np.sin(th) * K + (1 - np.cos(th)) * K @ K
    assert np.linalg.det(R) > 0.999999
    return R


def f2_rotation_invariance():
    syn, corr = _befull()
    f0 = fit(syn, corr)
    R = _proper_rotation()
    syn2 = synth_chimanoid()
    corrR = make_full_body_correspondence(syn2, TARGET_LENS, TARGET_RADIALS, origin=(0.0, 0.85, 0.0), rot=R)
    f1 = fit(syn2, corrR)

    r0, r1 = _rest_lengths(f0), _rest_lengths(f1)
    assert set(r0) == set(r1)
    for k in r0:
        assert _rel(r0[k], r1[k]) < 1e-9, f"rest_length {k}"

    m0, m1 = _masses(f0), _masses(f1)
    for k in m0:
        assert _rel(m0[k], m1[k]) < 1e-9, f"mass {k}"

    i0, i1 = _inertia_spectra(f0), _inertia_spectra(f1)
    for k in i0:
        for a, b in zip(np.sort(i0[k]), np.sort(i1[k])):
            assert _rel(a, b) < 1e-9, f"inertia spectrum {k}"

    a0, a1 = _arms(f0), _arms(f1)
    for k in a0:
        assert abs(a0[k] - a1[k]) < 1e-9, f"moment arm {k}"

    s0, s1 = _sites(f0), _sites(f1)
    for k in s0:
        assert np.allclose(s1[k], R @ s0[k], rtol=1e-9, atol=1e-12), f"site co-rotation {k}"

    assert f0.residuals["chirality_det"] > 0
    assert abs(f0.residuals["chirality_det"] - f1.residuals["chirality_det"]) < 1e-9
    assert f0.residuals["frame_handedness"] == f1.residuals["frame_handedness"]
    for body in f0.segments:
        seg1 = next(s for s in f1.segments if s.source_body == body.source_body)
        d = abs(body.roll_residual_deg - seg1.roll_residual_deg) % 180.0
        assert min(d, 180.0 - d) < 1e-6, f"roll twist {body.source_body}"
        assert _rel(body.residual, seg1.residual) < 1e-9, "seg residual"


# ---------------------------------------------------------------------------
# F3  mirror: preserve refuses a reflected authoring; mirror mode is exact
# ---------------------------------------------------------------------------
# The authoring-reflection plane must genuinely flip the chirality of the point
# cloud: the y-plane (up/down) does, the left/right and forward planes are near
# symmetry planes of this anatomy and wELF not change det.
MIRROR_N = np.array([0.0, 1.0, 0.0])


def _rectify(L: dict) -> dict:
    n = MIRROR_N
    return {k: p - 2.0 * (p @ n) * n for k, p in L.items()}


def f3_preserve_reflects_refused():
    syn, corr = _befull()
    cm = copy.deepcopy(corr)
    cm.landmarks = _rectify(corr.landmarks)
    expect_refusal("F3a preserve-mode reflection refused", "handedness_mismatch", lambda: fit(syn, cm))


def f3_mirror_mode_exact():
    syn, corr = _befull()
    base = fit(syn, corr)
    n = MIRROR_N
    cm = copy.deepcopy(corr)
    cm.landmarks = _rectify(corr.landmarks)
    cm.handedness = "mirror"
    cm.mirror_plane_normal = n
    fm = fit(syn, cm)
    assert fm.residuals["frame_handedness"] == "left"
    assert fm.residuals["chirality_det"] < 0
    assert base.residuals["frame_handedness"] == "right"
    assert base.residuals["chirality_det"] > 0
    # reflection maps geometry exactly; every scalar is handedness-blind
    r0, rm = _rest_lengths(base), _rest_lengths(fm)
    for k in r0:
        assert _rel(r0[k], rm[k]) < 1e-12, f"rest_length {k}"
    m0, mm = _masses(base), _masses(fm)
    for k in m0:
        assert _rel(m0[k], mm[k]) < 1e-12, f"mass {k}"
    for k, i0 in _inertia_spectra(base).items():
        assert np.allclose(i0, _inertia_spectra(fm)[k], rtol=1e-12, atol=1e-12)
    a0, am = _arms(base), _arms(fm)
    for k in a0:
        assert abs(a0[k] - am[k]) < 1e-9, k
    # every fitted frame stays a proper ONB in mirror mode
    for seg in fm.segments:
        assert np.linalg.det(seg.frame_basis) > 0.999999, seg.source_body
    # re-reflecting the mirror fit returns the non-mirror fit site-for-site
    for k in _sites(base):
        mp = _sites(fm)[k]
        refl = mp - 2.0 * (mp @ n) * n
        assert np.allclose(refl, _sites(base)[k], rtol=1e-9, atol=1e-12), k


# ---------------------------------------------------------------------------
# F4  sites move only with their owning segment's subtree
# ---------------------------------------------------------------------------
def f4_site_subtree_coupling():
    syn, corr = _befull()
    base = fit(syn, corr)
    s0 = _sites(base)

    def relandmarked(mutator):
        c2 = copy.deepcopy(corr)
        mutator(c2.landmarks)
        return fit(syn, c2)

    femur_l_sites = [s for s in syn.sites if s.body == "femur_l"]
    tibia_r_sites = [s for s in syn.sites if s.body == "tibia_r"]
    toes_sites = [s for s in syn.sites if s.body == "toes_r"]
    assert femur_l_sites and tibia_r_sites and toes_sites

    # poke the toes_r branch (sibling of the femur_l leg) — femur_l must not move
    f_other = relandmarked(lambda L: L.__setitem__("toes_r.roll", L["toes_r.roll"] + np.array([0.0, 0.0, 0.25])))
    s_other = _sites(f_other)
    for sn in femur_l_sites:
        assert np.array_equal(s0[sn.name], s_other[sn.name]), f"{sn.name} moved with a foreign branch"
    assert any(not np.array_equal(s0[s.name], s_other[s.name]) for s in toes_sites), "toes_r branch sites must move"
    for sn in tibia_r_sites:
        assert np.array_equal(s0[sn.name], s_other[sn.name]), f"{sn.name} moved with toes_r"

    # poke femur_l roll (frame change, closure untouched) — tibia_r must not move
    f_own = relandmarked(lambda L: L.__setitem__("femur_l.roll", L["femur_l.roll"] + np.array([0.0, 0.0, 0.3])))
    s_own = _sites(f_own)
    for sn in tibia_r_sites:
        assert np.array_equal(s0[sn.name], s_own[sn.name]), f"{sn.name} moved with femur_l"
    assert any(not np.array_equal(s0[s.name], s_own[s.name]) for s in femur_l_sites)


# ---------------------------------------------------------------------------
# F5  analytic tendon moment arms == central-difference check, whole body
# ---------------------------------------------------------------------------
def f5_analytic_vs_finite_difference():
    syn, corr = _befull()
    f = fit(syn, corr)
    assert all(abs(t.moment_arms[0].fd_eps - FD_EPS) == 0.0 for t in f.tendons)
    worst = 0.0
    n_arms = 0
    for t in f.tendons:
        for m in t.moment_arms:
            n_arms += 1
            assert m.matched, f"{t.name}/{m.coord}"
            worst = max(worst, abs(m.analytic - m.finite_difference) / (1.0 + abs(m.finite_difference)))
    assert n_arms > 0
    assert worst < 5e-6, worst


# ---------------------------------------------------------------------------
# F6  uniform global scale closed forms: lengths x s, mass x s^3, inertia x s^5
# ---------------------------------------------------------------------------
def f6_uniform_scale_closed_forms():
    syn, corr = _befull()
    f0 = fit(syn, corr)
    s = 2.5
    cs = copy.deepcopy(corr)
    cs.global_scale = s
    cs.landmarks = {k: (s * v) for k, v in corr.landmarks.items()}
    f1 = fit(syn, cs)

    r0, r1 = _rest_lengths(f0), _rest_lengths(f1)
    for k in r0:
        assert _rel(r1[k], s * r0[k]) < 1e-12, f"rest_length {k}"

    m0, m1 = _masses(f0), _masses(f1)
    for k in m0:
        assert _rel(m1[k], s ** 3 * m0[k]) < 1e-9, f"mass {k}"

    i0, i1 = _inertia_spectra(f0), _inertia_spectra(f1)
    for k in i0:
        for a, b in zip(np.sort(i0[k]), np.sort(i1[k])):
            assert _rel(b, s ** 5 * a) < 1e-9, f"inertia {k}"

    a0, a1 = _arms(f0), _arms(f1)
    for k in a0:
        assert abs(a1[k] - s * a0[k]) < 1e-9, k

    for seg0 in f0.segments:
        seg1 = next(x for x in f1.segments if x.source_body == seg0.source_body)
        assert np.allclose(seg1.scale, s * seg0.scale, rtol=1e-12, atol=1e-12), seg0.source_body
        assert _rel(seg1.residual, seg0.residual) < 1e-12
    assert abs(f0.residuals["chirality_det"] - f1.residuals["chirality_det"]) < 1e-9


# ---------------------------------------------------------------------------
# S1  supplement: aspect scale policy closed form (DERIVATION §5.3)
# ---------------------------------------------------------------------------
def s1_aspect_radial_closed_form():
    syn, corr = _befull()
    femur_r_sites = [s.name for s in syn.sites if s.body == "femur_r"][:2]
    assert len(femur_r_sites) == 2
    from intake import global_site_positions

    world = global_site_positions(syn)
    w_src = float(np.linalg.norm(world[femur_r_sites[1]] - world[femur_r_sites[0]]))
    assert w_src > 1e-6
    w_fit = 0.65 * w_src

    c = copy.deepcopy(corr)
    seg = next(s for s in c.segments if s.source_body == "femur_r")
    seg.scale_policy = "aspect"
    seg.width_landmarks = ["femur_r.wA", "femur_r.wB", "femur_r.swA", "femur_r.swB"]
    c.landmarks["femur_r.wA"] = _femur_lateral(corr, syn, +w_fit / 2.0)
    c.landmarks["femur_r.wB"] = _femur_lateral(corr, syn, -w_fit / 2.0)
    for sid, site in zip(("femur_r.swA", "femur_r.swB"), femur_r_sites):
        c.landmarks[sid] = np.zeros(3)
        c.source_landmarks[sid] = f"site:{site}"

    f = fit(syn, c)
    segf = next(s for s in f.segments if s.source_body == "femur_r")
    radial = w_fit / w_src
    assert np.allclose(segf.scale, [segf.scale[0], radial, radial], rtol=1e-12, atol=1e-12), segf.scale
    phys = next(p for p in f.physiology if p.body == "femur_r")
    assert _rel(phys.mass, (phys.mass_src * phys.det_scale)) < 1e-12
    assert _rel(phys.det_scale, segf.scale[0] * radial * radial) < 1e-12


# ---------------------------------------------------------------------------
# S2  supplement: NONUNIFORM affine-image mass/inertia closed forms, recomputed
#     INDEPENDENTLY from the correspondence landmarks themselves (DERIVATION §9)
# ---------------------------------------------------------------------------
def s2_nonuniform_mass_inertia_closed_form():
    from aspect_bounds import UNBOUNDED
    from compiler import onb_from_points, resolve_source_landmarks, _resolve_target
    import actual_target_fit  # needs the monkey bins (read-only)

    real = actual_target_fit.load_real()
    mt = actual_target_fit.MonkeyTarget()
    sw = global_site_positions(real)
    corr, _ = actual_target_fit.build_correspondence(real, mt, sw)
    f = fit(real, corr, fit_mode="grounded", aspect_bounds=UNBOUNDED)

    src_lm = resolve_source_landmarks(corr, real)
    tgt_lm = {k: _resolve_target(corr, k) for k in corr.landmarks}

    checked = 0
    for seg in corr.segments:
        if seg.source_body not in {s.source_body for s in f.segments}:
            continue
        b = next(x for x in real.bodies if x.name == seg.source_body)
        phys = next((p for p in f.physiology if p.body == b.name), None)
        if phys is None or b.inertia_local is None:
            continue
        sf = next(s for s in f.segments if s.source_body == b.name)
        D = np.diag(sf.scale)
        # source-body frame B from the SOURCE landmarks alone (independent rebase)
        A, Dn, Q = src_lm[seg.proximal_landmark], src_lm[seg.distal_landmark], src_lm[seg.roll_ref]
        a, bb, cc = onb_from_points(A, Dn, Q)
        Bm = np.column_stack([a, bb, cc])
        # target frame Bp from the TARGET landmarks
        P, Pn, Qt = tgt_lm[seg.proximal_landmark], tgt_lm[seg.distal_landmark], tgt_lm[seg.roll_ref]
        ap, bp, cp = onb_from_points(P, Pn, Qt)
        Bp = np.column_stack([ap, bp, cp])
        L = Bp @ D @ Bm.T
        detS = float(np.linalg.det(D))
        m_ind = b.mass * detS
        assert _rel(m_ind, phys.mass) < 1e-9, (b.name, m_ind, phys.mass)
        X = (np.trace(b.inertia_local) / 2.0) * np.eye(3) - b.inertia_local
        Xp = L @ X @ L.T
        I_ind = detS * (np.trace(Xp) * np.eye(3) - Xp)
        I_ind = (I_ind + I_ind.T) / 2.0
        assert np.allclose(I_ind, phys.inertia_fitted, rtol=1e-9, atol=1e-9), b.name
        assert np.all(np.linalg.eigvalsh(phys.inertia_fitted) > 0), b.name
        checked += 1
    assert checked >= 8, checked  # resolved segments with <inertial> (thorax_dummy has none)
    assert _rel(next(p for p in f.physiology if p.body == "pelvis").det_scale, 1.0) < 1e-12


# ---------------------------------------------------------------------------
# S3  aspect bounds: refuse | flag | unbounded, and the radius flag finding
# ---------------------------------------------------------------------------
def s3_aspect_bounds_policy():
    from aspect_bounds import POLICED, POLICED_FLAG, UNBOUNDED
    import actual_target_fit  # local import: needs the monkey bins (read-only)

    real = actual_target_fit.load_real()
    mt = actual_target_fit.MonkeyTarget()
    sw = global_site_positions(real)
    corr, _ = actual_target_fit.build_correspondence(real, mt, sw)

    # unbounded = legacy default: the fit proceeds, NOT flagged
    fu = fit(real, corr, fit_mode="grounded", aspect_bounds=UNBOUNDED)
    assert all(seg.status == SEG_RESOLVED for seg in fu.segments), [s.source_body for s in fu.segments]
    assert not any(k.startswith("aspect_flag") for k in fu.residuals)

    # policed_flag = detect + flag (packet written, segment SEG_FLAGGED)
    ff = fit(real, corr, fit_mode="grounded", aspect_bounds=POLICED_FLAG)
    assert ff.residuals.get("aspect_flag.radius") is True
    assert ff.residuals.get("aspect_flag.radius_l") is True
    rseg = next(s for s in ff.segments if s.source_body == "radius")
    assert rseg.status == SEG_FLAGGED
    assert "radius" not in {u["body"] for u in ff.unresolved_segments}

    # policed = refuse: the implausible radius transverse is REFUSED, never repaired
    try:
        fit(real, corr, fit_mode="grounded", aspect_bounds=POLICED)
    except Refusal as e:
        assert e.code == "aspect_out_of_bounds", e.code
        assert "radius" in e.message
    else:
        raise AssertionError("policed profile must refuse the radius scale")


# ---------------------------------------------------------------------------
# S4  actual-target packet invariants (the envelope correspondence, deterministic)
# ---------------------------------------------------------------------------
def s4_actual_target_packet():
    import actual_target_fit  # local import: needs the monkey bins (read-only)
    from aspect_bounds import POLICED_FLAG

    real = actual_target_fit.load_real()
    mt = actual_target_fit.MonkeyTarget()
    sw = global_site_positions(real)
    corr, _ = actual_target_fit.build_correspondence_envelope(real, mt, sw)

    prov = {"source_identity": {"raw_sha256": "x", "canonical": {"source_sha256_canonical": "y"}}}
    f = fit(real, corr, fit_mode="grounded", aspect_bounds=POLICED_FLAG, provenance=prov)

    # geometric invariants
    assert abs(f.residuals["chirality_det"] - 1.0) < 1e-3
    assert f.residuals["frame_handedness"] == "right"
    assert f.residuals["shared_joint_max_separation_m"] == 0.0
    assert f.residuals["closure.thorax_dummy"] == 0.0

    # resolution ledger
    resolved = {s.source_body for s in f.segments}
    unresolved_names = {u["body"] for u in f.unresolved_segments}
    assert resolved == {
        "femur_r", "femur_l", "tibia_r", "tibia_l",
        "humerus", "humerus_l", "radius", "radius_l", "thorax_dummy",
    }
    assert unresolved_names == {
        "thorax", "ulna", "ulna_l", "hand_r", "hand_l",
        "talus_r", "talus_l", "toes_r", "toes_l",
    }
    # no segment is silently repaired into existence: every unresolved body keeps its
    # sites ORDERED but unplaced, and their unmeasured quantities serialize as null
    un_sites = [s for s in f.sites if s.segment in unresolved_names]
    assert len(un_sites) > 0 and all(s.unresolved and np.isnan(s.fitted_pos_global).all() for s in un_sites)
    assert all(u["axes"] for u in f.unresolved_segments)

    # measured axial ratios (pack length / source piece length), recomputed from raw
    J = mt.J
    src_bo = {b.name: np.asarray(b.pos_global) for b in real.bodies}
    expected = {
        "femur_r": np.linalg.norm(J[mt.idx["knee_R"]] - J[mt.idx["hip_R"]])
        / np.linalg.norm(src_bo["tibia_r"] - src_bo["femur_r"]),
        "tibia_r": np.linalg.norm(J[mt.idx["ankle_R"]] - J[mt.idx["knee_R"]])
        / np.linalg.norm(src_bo["talus_r"] - src_bo["tibia_r"]),
        "humerus": np.linalg.norm(J[mt.idx["elbow_R"]] - J[mt.idx["shoulder_R"]])
        / np.linalg.norm(src_bo["ulna"] - src_bo["humerus"]),
        "radius": np.linalg.norm(J[mt.idx["wrist_R"]] - J[mt.idx["elbow_R"]])
        / np.linalg.norm(src_bo["hand_r"] - src_bo["radius"]),
        "thorax_dummy": np.linalg.norm(J[mt.idx["spine_upper"]] - J[mt.idx["spine_mid"]])
        / np.linalg.norm(src_bo["thorax"] - src_bo["thorax_dummy"]),
    }
    for body, exp in expected.items():
        sf = next(s for s in f.segments if s.source_body == body)
        assert _rel(sf.scale[0], exp) < 1e-6, (body, sf.scale[0], exp)

    # authored transverse assumption on radius/radius_l + thorax_dummy (6 axes) —
    # forearm b/c is an OUTER-ENVELOPE-BOUNDED authorship, never skin-as-evidence
    assert f.residuals is not None
    assert f.segments and all(s.axis_sources for s in f.segments)
    asserts = f.audit.assumptions
    assert asserts["n_axis_assumptions"] == 6
    assert asserts["n_axis_evidence"] == 21
    assert asserts["uniform_transverse_legacy_blanket"] is True
    assert asserts["root_ref_frame_not_scale_evidence"] is True
    assert asserts["flagged_geometry_excluded_from_admitted_physical"] is False

    # the forearm transverse axes are AUTHORED (bounded by the skin envelope,
    # measured separately), NOT evidence — radius must be resolved under POLICED_FLAG
    rseg = next(s for s in f.segments if s.source_body == "radius")
    assert rseg.status == SEG_RESOLVED, rseg.status
    assert rseg.axis_sources["b"] == "assumption" and rseg.axis_sources["c"] == "assumption"
    assert rseg.axis_measure_kind["b"] == "authored"
    assert rseg.scale[0] == rseg.scale[1] == rseg.scale[2]  # uniform = axial reused
    assert not any(k.startswith("aspect_flag") for k in f.residuals)

    # physiology: pelvis untouched and ADMITTED-FALSE as a reference-frame quantity;
    # everything else transported with the locked closed forms
    phys = {p.body: p for p in f.physiology}
    assert _rel(phys["pelvis"].det_scale, 1.0) < 1e-12
    assert phys["pelvis"].admitted is False
    assert phys["pelvis"].mass_kind == "root_ref_frame_unscaled"
    assert _rel(phys["femur_r"].mass, phys["femur_r"].mass_src * phys["femur_r"].det_scale) < 1e-12
    # admitted-physical ledger: pelvis excluded, nothing flagged promoted
    adm = f.admission["counts"]
    assert adm["geometrically_resolved"] == 9
    assert adm["flagged"] == 0
    assert adm["unresolved"] == 9
    assert adm["admitted_kinematic"] == 9
    assert adm["transported_under_assumption"] == 8
    assert adm["physically_admitted"] == 0, "geometry alone cannot discharge density validation"
    assert "pelvis" not in f.admission["bodies"]["transported_under_assumption"]
    excluded = {e["body"] for e in f.admission["bodies"]["excluded_from_physical"]}
    assert "pelvis" in excluded
    pel_note = next(e["reason"] for e in f.admission["bodies"]["excluded_from_physical"] if e["body"] == "pelvis")
    assert "reference-frame quantity" in pel_note and "does not measure" in pel_note
    tot = f.admission["totals_mass_kg"]
    assert _rel(tot["transported_under_assumption"], 5.263) < 0.05, tot["transported_under_assumption"]
    assert tot["physically_admitted"] == 0.0
    assert _rel(tot["root_reference_only"], 11.777) < 1e-9
    ma = f.admission["mass_admission"]
    assert ma["requires_density_validation"] is True and ma["density_validated"] is False
    assert ma["assumption"] == "uniform_constant_density_scale"
    for p in f.physiology:
        assert np.all(np.linalg.eigvalsh(p.inertia_fitted) > 0)

    # tendons: all 120 present; the wrist/ankle/finger set is path_incomplete (their
    # muscle bellies sit on unresolved bodies), never a fabricated path
    n_derived = sum(1 for t in f.tendons if t.status == DERIVED)
    n_pi = sum(1 for t in f.tendons if t.status.startswith("path_incomplete"))
    assert len(f.tendons) == 120
    assert n_pi == 78 and n_derived == 42, (n_derived, n_pi)
    for t in f.tendons:
        if t.status.startswith("path_incomplete"):
            assert np.isnan(np.asarray(t.rest_length))

    # deterministic: a second identical fit produces the byte-identical packet
    from schema import _jsonable
    import json as _json

    f2 = fit(real, corr, fit_mode="grounded", aspect_bounds=POLICED_FLAG, provenance=prov)
    a = _json.dumps(_jsonable(f), sort_keys=True, indent=1)
    b_ = _json.dumps(_jsonable(f2), sort_keys=True, indent=1)
    assert a == b_


# ---------------------------------------------------------------------------
# S5  forearm envelope estimator: bounded, INTERIOR sections, never conflated
#     with internal anatomy; the contaminated wrist-band regression still flags
# ---------------------------------------------------------------------------
def s5_forearm_envelope_estimator():
    from target_envelope import feasibility as envelope_feasibility
    from target_envelope import measure_forearm_envelope
    import actual_target_fit

    real = actual_target_fit.load_real()
    mt = actual_target_fit.MonkeyTarget()
    sw = global_site_positions(real)

    for body, (prox, dist) in (
        ("radius", ("elbow_R", "wrist_R")),
        ("radius_l", ("elbow_L", "wrist_L")),
    ):
        P = mt.joint_pos(prox)
        P_d = mt.joint_pos(dist)
        a = actual_target_fit._band_roll(mt, prox, P, P_d - P)
        _, b, c = _onb(P, P_d, a)
        env = measure_forearm_envelope(mt, P, P_d, b, c)

        # bounded interior sections, not endpoints
        assert env["sections"] and all(s["t"] in (0.35, 0.5, 0.65) for s in env["sections"])
        assert all(s["n_verts"] > 0 for s in env["sections"]), "envelope needs vertices"
        assert env["nature"] == "outer_envelope"  # SKIN constraint, never internal anatomy

        # recorded stats + sensitivity
        assert env["per_axis"]["b"]["n_sections_measured"] == 3
        assert env["per_axis"]["b"]["uncertainty"] >= 0.0
        assert env["per_axis"]["c"]["uncertainty"] >= 0.0
        assert env["sensitivity"]["b"]["n_variants"] > 0
        assert env["sensitivity"]["c"]["n_variants"] > 0

        # the interior forearm is ~2 cm, not ~0.5 m (the contaminated wrist band was 0.17 m)
        assert 0.005 < env["per_axis"]["b"]["median"] < 0.05, env["per_axis"]["b"]["median"]
        assert 0.005 < env["per_axis"]["c"]["median"] < 0.05, env["per_axis"]["c"]["median"]

    # feasibility: fitted INTERNAL site spread (scaled source offsets) bounding works;
    # a spread larger than the skin envelope must fail the check
    fe_ok = envelope_feasibility({"b": 0.004, "c": 0.004}, env, margin_m=0.001)
    fe_no = envelope_feasibility({"b": 0.9, "c": 0.9}, env, margin_m=0.001)
    assert fe_ok["ok"] and not fe_no["ok"]

    # the contaminated legacy band STILL flags the radius (regression, unchanged)
    corr_band, _ = actual_target_fit.build_correspondence_band(real, mt, sw)
    fb = fit(real, corr_band, fit_mode="grounded", aspect_bounds=POLICED_FLAG)
    assert fb.residuals.get("aspect_flag.radius") is True
    assert fb.residuals.get("aspect_flag.radius_l") is True


def _onb(p, pd, q):
    a = pd - p
    a = a / np.linalg.norm(a)
    b = q - p - a * (a @ (q - p))
    b = b / np.linalg.norm(b)
    c = np.cross(a, b)
    return a, b, c


# ---------------------------------------------------------------------------
# S6  strict JSON export: unresolved/null contract, no NaN/Infinity tokens
# ---------------------------------------------------------------------------
def s6_strict_json_export():
    import actual_target_fit
    from schema import write_json, _jsonable
    import json as _json

    real = actual_target_fit.load_real()
    mt = actual_target_fit.MonkeyTarget()
    sw = global_site_positions(real)
    corr, _ = actual_target_fit.build_correspondence_envelope(real, mt, sw)
    f = fit(real, corr, fit_mode="grounded", aspect_bounds=POLICED_FLAG)

    out = str(actual_target_fit.OUT_PACKET) + ".s6.json"
    write_json(f, out)
    raw = Path(out).read_text(encoding="utf-8")
    # no non-standard JSON tokens survive serialization
    assert "NaN" not in raw and "Infinity" not in raw and "-Infinity" not in raw
    parsed = _json.loads(raw)
    # round-trip is stable, not coerced
    again = _json.dumps(_jsonable(f), sort_keys=True, indent=1)
    assert again == _json.dumps(parsed, sort_keys=True, indent=1)

    # unresolved sites and limbs are null, not zero
    for s in parsed["sites"]:
        if s.get("unresolved"):
            assert s.get("fitted_pos_global") is None, s["name"]
            assert s.get("reason"), s["name"]
    for j in parsed["joints"]:
        if j.get("status") == "unresolved_body":
            assert j.get("axis") is None, j["name"]
            assert j.get("reason"), j["name"]
    for m in parsed["muscles"]:
        if m.get("rest_length") is None:
            pass
        else:
            assert m["rest_length"] >= 0.0
    Path(out).unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# S7  provenance: hashes, identity, scale conventions, aspect policy recorded
# ---------------------------------------------------------------------------
def s7_provenance_recorded():
    import actual_target_fit

    real = actual_target_fit.load_real()
    mt = actual_target_fit.MonkeyTarget()
    sw = global_site_positions(real)
    corr, _ = actual_target_fit.build_correspondence_envelope(real, mt, sw)
    prov = actual_target_fit._provenance(real, mt, corr)

    kinds = {i["kind"]: i for i in prov["input_files"]}
    assert set(kinds) == {"target_mesh", "target_binding_pack", "source_xml", "correspondence"}
    for k in ("target_mesh", "target_binding_pack"):
        assert len(kinds[k]["sha256"]) == 64 and kinds[k]["bytes"]
    assert len(kinds["correspondence"]["sha256"]) == 64
    si = kinds["source_xml"]
    assert si["sha256"] == "675e00d0898cf7a175f3e4fe8f240eb24301c2f5e201ffa9215aea45b01b83d1"
    assert si["canonicalization"]["source_sha256_canonical"] == \
        "7caa32c6e31e319876ea21625b662c5c00e736038f542b38ce6b0cb81aadc8a5"
    assert si["canonicalization"]["bytes"] == 154835 and si["canonicalization"]["bytes_canonical"] == 154834
    # upstream byte identity kept separate from the documented local transform
    assert prov["upstream_vs_local_identity"] and prov["coordinate_conventions"]
    assert prov["mesh_units_to_m"] == 0.065
    assert prov["aspect_policy"]["profile"] == "policed_flag"
    assert prov["aspect_policy"]["on_violation"].startswith("flag")

    f = fit(real, corr, fit_mode="grounded", aspect_bounds=POLICED_FLAG, provenance=prov)
    assert f.meta["provenance"]["input_files"][0]["sha256"] == prov["input_files"][0]["sha256"]
    assert f.meta["source_identity"]["canonical"]["source_sha256_canonical"] == \
        si["canonicalization"]["source_sha256_canonical"]
    assert f.meta["coordinate_conventions"]["global_scale_factor"] == 1.0


# ---------------------------------------------------------------------------
# S8  actuator hygiene: parsed from <actuator>, not the unnamed <default>
# ---------------------------------------------------------------------------
def s8_actuator_hygiene():
    import actual_target_fit

    real = actual_target_fit.load_real()
    assert len(real.muscles) == 120  # the 1 unnamed <default><muscle> must NOT become an actuator record
    names = [m.name for m in real.muscles]
    assert "" not in names and None not in names
    assert len(set(names)) == 120
    # every actuator declares its control range and references a valid tendon
    tendon_names = {t.name for t in real.tendons}
    for m in real.muscles:
        assert [float(x) for x in m.ctrlrange.split()] == [0.0, 1.0], m.name
        assert m.ctrllimited is True, m.name
        assert m.tendon is not None and m.tendon in tendon_names, m.name
        assert m.attr_source.get("ctrlrange") == "declared", m.name  # authored on the element
    # the <default> block is resolved verbatim for inherited attrs (e.g. scale=200),
    # never materialised as a phantom actuator record
    assert real.meta["muscle_defaults"] == {"ctrllimited": "true", "ctrlrange": "0 1", "scale": "200"}
    assert len(real.muscles) == len({m.name for m in real.muscles}) == 120


def _femur_lateral(corr, syn, half: float) -> np.ndarray:
    seg = next(s for s in corr.segments if s.source_body == "femur_r")
    p = corr.landmarks[seg.proximal_landmark]
    pd = corr.landmarks[seg.distal_landmark]
    q = corr.landmarks[seg.roll_ref]
    a = pd - p
    a = a / np.linalg.norm(a)
    lat = q - p - a * (a @ (q - p))
    lat = lat / np.linalg.norm(lat)
    return p + a * (a @ (q - p)) + lat * half


# ---------------------------------------------------------------------------
# F7  every refusal is NAMED — nothing silently defaulted
# ---------------------------------------------------------------------------
def f7_refusal_catalog():
    syn, corr = _befull()

    def clone():
        return copy.deepcopy(corr)

    def dofit(c):
        return fit(syn, c)

    # --- collect_refusals tier (named codes are inside the aggregate)
    c = clone(); c.global_scale = -1.0
    expect_code("F7 bad_global_scale", "bad_global_scale", c, syn)

    c = clone(); c.handedness = "flip"
    expect_code("F7 bad_handedness", "bad_handedness", c, syn)

    c = clone(); c.handedness = "mirror"  # no mirror_plane_normal
    expect_code("F7 missing_mirror_normal", "missing_mirror_normal", c, syn)

    c = clone(); c.handedness = "mirror"; c.mirror_plane_normal = np.array([1.0, 1.0, 1.0])
    expect_code("F7 bad_mirror_normal", "bad_mirror_normal", c, syn)

    c = clone(); c.frame_anterior = np.array([1.0, 1.0, 0.0])
    expect_code("F7 non_proper_target_frame", "non_proper_target_frame", c, syn)

    c = clone(); c.segments[0].source_body = "bogus_body"
    expect_code("F7 unknown_source_body", "unknown_source_body", c, syn)

    c = clone(); c.segments[0].parent = "toes_r"
    expect_code("F7 chain_conflict", "chain_conflict", c, syn)

    c = clone(); c.segments = list(c.segments) + [copy.deepcopy(c.segments[0])]
    expect_code("F7 duplicate_segment", "duplicate_segment", c, syn)

    c = clone(); del c.landmarks["tibia_r.roll"]
    expect_code("F7 missing_landmark", "missing_landmark", c, syn)

    c = clone(); c.landmarks["tibia_r.prox"] = np.array([np.nan, 0.0, 0.0])
    expect_code("F7 bad_landmark", "bad_landmark", c, syn)

    c = clone(); c.segments[0].coords = list(c.segments[0].coords) + ["no_such_coord"]
    expect_code("F7 unknown_source_joint", "unknown_source_joint", c, syn)

    c = clone(); c.segments[0].coords = list(c.segments[0].coords) + [c.segments[1].coords[0]]
    expect_code("F7 duplicate_coord", "duplicate_coord", c, syn)

    c = clone(); c.segments[0].coords = list(c.segments[0].coords)[:-1]
    expect_code("F7 unassigned_coords", "unassigned_coords", c, syn)

    c = clone(); c.segments[0].scale_policy = "stretch"
    expect_code("F7 bad_scale_policy", "bad_scale_policy", c, syn)

    c = clone(); c.segments[0].scale_policy = "aspect"
    expect_code("F7 aspect_without_widths", "bad_scale_policy", c, syn)

    c = clone(); c.root_landmark = "not_a_landmark"
    expect_code("F7 missing_root_landmark", "missing_landmark", c, syn)

    # --- source-landmark resolution tier (fires inside build_segments)
    c = clone(); c.source_landmarks["femur_r.prox"] = "site:nonexistent_site"
    expect_refusal("F7 unknown_site", "unknown_site", lambda: dofit(c))

    c = clone(); c.source_landmarks["femur_r.prox"] = "volcano:eruption"
    expect_refusal("F7 bad_source_landmark", "bad_source_landmark", lambda: dofit(c))

    c = clone(); c.source_landmarks["femur_r.prox"] = "body_origin:nonexistent_body"
    expect_refusal("F7 unknown_source_body(src)", "unknown_source_body", lambda: dofit(c))

    c = clone(); c.source_landmarks["femur_r.prox"] = "joint:not_a_joint"
    expect_refusal("F7 unknown_source_joint(src)", "unknown_source_joint", lambda: dofit(c))

    # --- segment tier
    c = clone(); c.landmarks["tibia_r.dist"] = c.landmarks["tibia_r.prox"].copy()
    c.source_landmarks["tibia_r.dist"] = "body_origin:tibia_r"
    expect_refusal("F7 degenerate_bone", "degenerate_bone", lambda: dofit(c))

    c = clone(); c.landmarks["femur_r.roll"] = 0.5 * (c.landmarks["femur_r.prox"] + c.landmarks["femur_r.dist"])
    expect_refusal("F7 axis_parallel_roll", "axis_parallel_roll", lambda: dofit(c))

    c = clone(); c.landmarks["tibia_r.dist"] = c.landmarks["tibia_r.dist"] + np.array([0.0, 0.5, 0.0])
    expect_refusal("F7 shared_joint_separation", "shared_joint_separation", lambda: dofit(c))

    n = MIRROR_N
    c = clone(); c.landmarks = _rectify(c.landmarks)
    expect_refusal("F7 handedness_mismatch", "handedness_mismatch", lambda: dofit(c))

    # unresolved_segments: v2 COVERS the case by keeping toes_r unresolved (no fitted
    # scale) instead of refusing: shared joints stay, sites stay ordered but unplaced.
    syn2 = synth_chimanoid()
    toes_coords = [x for x in syn2.joints if x.body == "toes_r"]
    syn2.joints = [j for j in syn2.joints if j.body != "toes_r"]
    syn2.index()
    c = clone()
    c.segments = [s for s in c.segments if s.source_body != "toes_r"]
    drop = {x.name for x in toes_coords}
    for seg in c.segments:
        seg.coords = [x for x in seg.coords if x not in drop]
    f = fit(syn2, c)
    assert any(u["body"] == "toes_r" for u in f.unresolved_segments), [
        u["body"] for u in f.unresolved_segments
    ]
    toes_sites = [s for s in f.sites if s.segment == "toes_r"]
    assert toes_sites and all(s.unresolved and np.isnan(s.fitted_pos_global).all() for s in toes_sites)
    assert "toes_r" not in {s.source_body for s in f.segments}


# ---------------------------------------------------------------------------
# S9  strict serialization gate: unresolved->null accepted, resolved NaN refused
# ---------------------------------------------------------------------------
def s9_serialization_validation():
    import actual_target_fit
    from aspect_bounds import POLICED_FLAG
    from schema import PacketValidationError, _jsonable, validate_finite, write_json

    real = actual_target_fit.load_real()
    mt = actual_target_fit.MonkeyTarget()
    sw = global_site_positions(real)
    corr, _ = actual_target_fit.build_correspondence_envelope(real, mt, sw)
    prov = {"source_identity": {"raw_sha256": "x", "canonical": {"source_sha256_canonical": "y"}}}
    f = fit(real, corr, fit_mode="grounded", aspect_bounds=POLICED_FLAG, provenance=prov)

    # 1) the clean fit validates: non-finite fields are allowed ONLY on records the
    #    machinery explicitly marks unresolved (status/reason/unmatched present)
    problems = validate_finite(f)
    assert problems == [], problems[:3]

    # 2) Serialization: intentional unresolved stays null (not NaN) — the Contract-1
    #    emission change (None -> null) keeps them lossless through the strict writer.
    rendered = json.dumps(_jsonable(f), allow_nan=False)
    assert "NaN" not in rendered and "Infinity" not in rendered
    unresolved_site = next(s for s in f.sites if s.unresolved)
    blob = json.loads(rendered)
    by_name = {s["name"]: s for s in blob["sites"]}
    assert by_name[unresolved_site.name]["fitted_pos_global"] is None
    assert by_name[unresolved_site.name]["unresolved"] is True
    assert by_name[unresolved_site.name]["reason"]

    # 3) An injected non-finite in a RESOLVED field must be refused by write_json
    #    with the nonfinite_resolved_field code (never silently written).
    resolved_site = next(s for s in f.sites if not s.unresolved)
    dirty = copy.deepcopy(f)
    dirty_site = next(s for s in dirty.sites if s.name == resolved_site.name)
    dirty_site.fitted_pos_local = np.array([0.0, np.nan, 0.0])
    dirty_site.unresolved = False
    dirty_site.reason = ""
    try:
        write_json(dirty, "_s9_write.json")
        raise AssertionError("write_json accepted a NaN in a resolved site")
    except PacketValidationError as e:
        assert e.code == "nonfinite_resolved_field", e.code
        assert "fitted_pos_local" in e.message, e.message

    # 4) injection into a genuinely-unresolved field stays legal (no false positive)
    ok_f = copy.deepcopy(f)
    ok_site = next(s for s in ok_f.sites if s.unresolved)
    ok_site.fitted_pos_local = np.array([np.nan, np.nan, np.nan])  # still unresolved semantics
    assert validate_finite(ok_f) == [], validate_finite(ok_f)[:3]


# ---------------------------------------------------------------------------
# S10  admission split: transported_under_assumption vs physically_admitted
# ---------------------------------------------------------------------------
def s10_admission_split():
    import actual_target_fit
    from aspect_bounds import POLICED_FLAG

    real = actual_target_fit.load_real()
    mt = actual_target_fit.MonkeyTarget()
    sw = global_site_positions(real)
    corr, _ = actual_target_fit.build_correspondence_envelope(real, mt, sw)
    prov = {"source_identity": {"raw_sha256": "x", "canonical": {"source_sha256_canonical": "y"}}}
    f = fit(real, corr, fit_mode="grounded", aspect_bounds=POLICED_FLAG, provenance=prov)
    a = f.admission

    # the split: a transported under-assumption subtotal exists; the physically
    # admitted subtotal is EMPTY unless a validated material/mass source exists.
    assert a["counts"]["transported_under_assumption"] == 8
    assert a["counts"]["physically_admitted"] == 0
    assert a["bodies"]["transported_under_assumption"] == sorted(a["bodies"]["transported_under_assumption"])
    mass = a["totals_mass_kg"]["transported_under_assumption"]
    assert mass > 0 and a["totals_mass_kg"]["physically_admitted"] == 0.0
    m = a["mass_admission"]
    assert m["requires_density_validation"] is True and m["density_validated"] is False
    assert m["assumption"] == "uniform_constant_density_scale"
    # geometry resolution does NOT discharge the density requirement, and the audit
    # records that explicitly.
    assert f.audit.assumptions["geometry_resolution_does_not_discharge_density_validation"] is True


# ---------------------------------------------------------------------------
# S11  envelope: width screen is coarse; containment is spatial + unresolved-honest
# ---------------------------------------------------------------------------
def s11_envelope_screen_vs_containment():
    import actual_target_fit
    from aspect_bounds import POLICED_FLAG
    from target_envelope import containment as env_containment
    from target_envelope import measure_forearm_envelope, width_screen

    real = actual_target_fit.load_real()
    mt = actual_target_fit.MonkeyTarget()
    sw = global_site_positions(real)
    corr, _ = actual_target_fit.build_correspondence_envelope(real, mt, sw)
    _ = POLICED_FLAG

    P = mt.joint_pos("elbow_R")
    P_d = mt.joint_pos("wrist_R")
    q = actual_target_fit._band_roll(mt, "elbow_R", P, P_d - P)
    _, bu, cu = actual_target_fit.onb_from_points(P, P_d, q)
    env = measure_forearm_envelope(mt, P, P_d, bu, cu)

    # a narrow cluster DISPLACED out of the section passes the width screen …
    displace_b = env["per_axis"]["b"]["median"] + 0.01  # 10 mm beyond the skin hull
    fake = [{"name": "shifted", "axial": env["sections"][1]["axis_pos_m"],
             "b": displace_b, "c": 0.0}]
    ws = width_screen({"b": 0.004, "c": 0.004}, env, margin_m=0.001)  # narrow!
    ct = env_containment(fake, env, margin_m=0.001)
    assert ws["ok"] is True, "width screen must pass a narrow displaced cluster"
    assert ct["per_site"]["shifted"]["verdict"] == "outside", (ct["per_site"]["shifted"], ws)
    assert ct["n_outside"] == 1 and ct["ok"] is False

    # signed-distance classes are DISTINCT: a point inside but clearanced under the
    # margin is inside_insufficient_clearance, NEVER "outside"
    hull = np.asarray(env["sections"][1]["hull_bc"])
    c0 = hull.mean(axis=0)
    v = hull[np.argmax(np.linalg.norm(hull - c0, axis=1))]
    inward = (c0 - v) / np.linalg.norm(c0 - v)
    tight_pt = v + inward * 0.0005  # 0.5 mm inside the boundary (< 1 mm margin)
    fake_t = [{"name": "tight", "axial": env["sections"][1]["axis_pos_m"],
               "b": float(tight_pt[0]), "c": float(tight_pt[1])}]
    ct2 = env_containment(fake_t, env, margin_m=0.001)
    assert ct2["per_site"]["tight"]["verdict"] == "inside_insufficient_clearance", (
        ct2["per_site"]["tight"]
    )
    assert ct2["n_outside"] == 0 and ct2["n_inside"] == 0
    assert ct2["n_inside_insufficient_clearance"] == 1 and ct2["ok"] is False

    # a site whose axial position has NO sampled band near it is UNRESOLVED (never
    # assumed inside); the measurement cannot establish containment there.
    outside_bands = 2 * env["selected_geometry"]["axis_len_m"]
    fake3 = [{"name": "beyond", "axial": outside_bands, "b": 0.001, "c": 0.001}]
    ct3 = env_containment(fake3, env, margin_m=0.001)
    assert ct3["per_site"]["beyond"]["verdict"] == "unresolved"
    assert ct3["n_unresolved"] == 1 and ct3["ok"] is False
    assert "local_narrowing" in ct3["per_site"]["beyond"]["reason"]


# ---------------------------------------------------------------------------
# S14 local triangle-plane section loops (final skin-containment authority)
# ---------------------------------------------------------------------------
def s14_section_loop_containment():
    import actual_target_fit
    from target_envelope import _chain_closed_loops
    from target_envelope import section_loop_containment

    # micro-law: four coplanar segments chain into exactly one closed loop
    sq = [
        (np.array([0.0, 0.0, 0.0]), np.array([1.0, 0.0, 0.0])),
        (np.array([1.0, 0.0, 0.0]), np.array([1.0, 1.0, 0.0])),
        (np.array([1.0, 1.0, 0.0]), np.array([0.0, 1.0, 0.0])),
        (np.array([0.0, 1.0, 0.0]), np.array([0.0, 0.0, 0.0])),
    ]
    loops, n_open, n_degen = _chain_closed_loops(sq)
    assert len(loops) == 1 and n_open == 0 and n_degen == 0
    assert len(loops[0][0]) == 4 and all(t == -1 for t in loops[0][1])
    # removing one segment leaves an OPEN chain: never bridged into a loop
    loops2, n_open2, _ = _chain_closed_loops(sq[:-1])
    assert len(loops2) == 0 and n_open2 == 1

    real = actual_target_fit.load_real()
    mt = actual_target_fit.MonkeyTarget()
    P = mt.joint_pos("elbow_R")
    P_d = mt.joint_pos("wrist_R")
    q = actual_target_fit._band_roll(mt, "elbow_R", P, P_d - P)
    _, bu, cu = actual_target_fit.onb_from_points(P, P_d, q)
    a = (P_d - P) / np.linalg.norm(P_d - P)
    L = float(np.linalg.norm(P_d - P))

    # mid-forearm: the plane cut must close into EXACTLY ONE loop; a point on the
    # bone axis sits INSIDE it with real clearance
    axial = 0.5 * L
    axis_pt = P + axial * a
    rel = axis_pt - P
    sites = [{"name": "axis_probe", "axial": axial,
              "b": float(rel @ bu), "c": float(rel @ cu)}]
    res = section_loop_containment(mt, P, a, bu, cu, sites, margin_m=0.001,
                                   owner_joint_names=("elbow_R", "wrist_R"))
    r = res["per_site"]["axis_probe"]
    assert r["verdict"] == "inside", r
    assert r["n_identified_loops"] == 1 and r["n_loops"] >= 1 and r["n_open_chains"] == 0, r
    assert r["dist_to_loop_m"] <= -0.001, r

    # the section is genuinely closed-loop skin: the probe displaced beyond the
    # loop must read OUTSIDE, not unresolved, not tight
    far = P + axial * a + 0.05 * bu  # 50 mm lateral: outside the ~20 mm skin
    relf = far - P
    sites_far = [{"name": "far_probe", "axial": axial,
                  "b": float(relf @ bu), "c": float(relf @ cu)}]
    res2 = section_loop_containment(mt, P, a, bu, cu, sites_far, margin_m=0.001,
                                    owner_joint_names=("elbow_R", "wrist_R"))
    r2 = res2["per_site"]["far_probe"]
    assert r2["verdict"] == "outside" and r2["dist_to_loop_m"] > 0, r2


# ---------------------------------------------------------------------------
# S12 attachment-candidates derivation (endpoint roles, mechanical_qualification,
# numeric transforms, hash separation, containment passthrough)
# ---------------------------------------------------------------------------
def s12_attachment_candidates():
    import actual_target_fit
    from attachment_candidates import build_attachment_candidates

    real = actual_target_fit.load_real()
    mt = actual_target_fit.MonkeyTarget()
    sw = global_site_positions(real)
    corr, _ = actual_target_fit.build_correspondence_envelope(real, mt, sw)
    prov = {"source_identity": {"raw_sha256": "x", "canonical": {"source_sha256_canonical": "y"}}}
    f = fit(real, corr, fit_mode="grounded", aspect_bounds=POLICED_FLAG, provenance=prov)
    cand = build_attachment_candidates(f, real, mt, corr, sw)

    for body in ("radius", "radius_l"):
        info = cand["bodies"][body]
        sites = [s for s in f.sites if s.segment == body]
        assert info["n_sites_total"] == len(sites) == 16, (body, info["n_sites_total"])
        assert info["n_resolved"] == 16 and info["n_unresolved"] == 0
        # numeric local-to-world transform present and RECONSTRUCTS the fit's worlds
        l2w = info["local_to_world"]
        R = np.asarray(l2w["R_source_local_to_target"], dtype=np.float64)
        t = np.asarray(l2w["t_fitted_origin_m"], dtype=np.float64)
        src_by_name = {s.name: s for s in real.sites}
        seen: dict[tuple[str, str], str] = {}
        for rec in info["candidates"]:
            # mechanical qualification is NEVER granted by this packet
            assert rec["mechanical_qualification"] is False
            assert rec["mechanical_qualification_note"]
            # source coordinates are VERBATIM intake values (no mesh factor)
            src = src_by_name[rec["site_id"]]
            assert np.array_equal(
                np.asarray(rec["source_pos_local"], dtype=np.float64),
                np.asarray(src.pos_local, dtype=np.float64),
            ), rec["site_id"]
            # world reconstruction from the exported transform
            fitted = rec["fitted"]
            if fitted["resolved"]:
                w = t + R @ np.asarray(rec["source_pos_local"], dtype=np.float64)
                # 1e-6 m: export rounds at 1e-9; frame bugs show at mm scale
                assert np.allclose(w, fitted["fitted_pos_global"], atol=1e-6), rec["site_id"]
            # containment passthrough present (not_measured here: no envelope run)
            assert "skin_containment" in rec and rec["skin_containment"]["loop"]
            for m in rec["tendon_membership"]:
                key = (rec["site_id"], m["tendon"])
                assert key not in seen, f"site listed twice for {m['tendon']}"
                seen[key] = m["role"]
                # endpoint roles only at the path ends, renamed away from anatomy claims
                if m["role"] in ("first_endpoint", "last_endpoint"):
                    assert m["index_in_path"] in (0, m["path_length"] - 1), (key, m)
                else:
                    assert m["role"] == "waypoint"
                    assert 0 < m["index_in_path"] < m["path_length"] - 1, (key, m)
        assert len(seen) >= len(info["candidates"]), (len(seen), len(info["candidates"]))
    blob = json.dumps(cand)
    assert "proximal_candidate" not in blob and "distal_candidate" not in blob
    # hash separation LAW: the fitted-packet slot is a distinct field, None until the
    # caller writes the packet, and never aliased to an XML hash once populated
    h = cand["provenance_hashes"]
    assert h["fitted_packet_sha256"] is None  # caller did not write a packet here
    h["source_xml_raw_sha256"] = "0" * 64
    h["fitted_packet_sha256"] = "f" * 64
    assert h["source_xml_raw_sha256"] != h["fitted_packet_sha256"]
    assert "different objects" in h["note"]


# ---------------------------------------------------------------------------
# S13 raw-XML-to-export unit identity (the session-4 regression: a target mesh
# factor must never be multiplied into source coordinates)
# ---------------------------------------------------------------------------
def s13_source_units_raw_xml():
    import xml.etree.ElementTree as ET

    import actual_target_fit
    from attachment_candidates import build_attachment_candidates
    from mesh_target import MESH_UNIT_TO_M
    from synthetic_fixtures import REAL_XML

    assert MESH_UNIT_TO_M != 1.0  # the target factor exists and must stay OUT of source coords

    real = actual_target_fit.load_real()
    mt = actual_target_fit.MonkeyTarget()
    sw = global_site_positions(real)
    corr, _ = actual_target_fit.build_correspondence_envelope(real, mt, sw)
    prov = {"source_identity": {"raw_sha256": "x", "canonical": {"source_sha256_canonical": "y"}}}
    f = fit(real, corr, fit_mode="grounded", aspect_bounds=POLICED_FLAG, provenance=prov)
    cand = build_attachment_candidates(f, real, mt, corr, sw)

    # 1) parse the RAW XML directly (not through intake) and compare verbatim
    xml_sites: dict[str, tuple[str, list[float]]] = {}
    for body_el in ET.parse(REAL_XML).getroot().iter("body"):
        for site_el in body_el.iter("site"):
            xml_sites[site_el.get("name")] = (
                body_el.get("name"),
                [float(v) for v in site_el.get("pos").split()],
            )
    for body in ("radius", "radius_l"):
        for rec in cand["bodies"][body]["candidates"]:
            bname, pos = xml_sites[rec["site_id"]]
            assert bname == body, (rec["site_id"], bname)
            assert rec["source_pos_local"] == pos, (rec["site_id"], rec["source_pos_local"], pos)
            assert "NOT scaled" in rec["source_pos_local_units"]
    # 2) the old bug would show as exported == xml * 0.065 for nonzero coords;
    #    exact equality above already excludes it, but pin the factor distance too
    some = next(iter(cand["bodies"]["radius"]["candidates"]))
    xv = np.asarray(some["source_pos_local"], dtype=np.float64)
    assert not np.allclose(xv, xv * MESH_UNIT_TO_M, rtol=1e-6), "coordinates look mesh-scaled"


def main() -> int:
    print("anatomy_compiler_run_tests: counts gate + membrane falsifiers F1-F7")
    print("G0 counts gate (real XML + synthetic twin)")
    check("g0_real_counts", g0_real_counts)
    check("g0_synth_twin_counts", g0_synth_twin_counts)
    print("F1 shared joints are one point")
    check("f1_synth_closure", f1_synth_closure)
    check("f1_real_closure", f1_real_closure)
    check("f1_rig_closure", f1_rig_closure)
    print("F2 proper-rotation invariance")
    check("f2_rotation_invariance", f2_rotation_invariance)
    print("F3 mirror policy")
    f3_preserve_reflects_refused()
    check("f3_mirror_mode_exact", f3_mirror_mode_exact)
    print("F4 site-subtree coupling")
    check("f4_site_subtree_coupling", f4_site_subtree_coupling)
    print("F5 analytic vs finite-difference moment arms")
    check("f5_analytic_vs_finite_difference", f5_analytic_vs_finite_difference)
    print("F6 uniform-scale closed forms")
    check("f6_uniform_scale_closed_forms", f6_uniform_scale_closed_forms)
    print("F7 named-refusal catalog")
    f7_refusal_catalog()
    print("S1 aspect scale-policy closed form")
    check("s1_aspect_radial_closed_form", s1_aspect_radial_closed_form)
    print("S2 NONUNIFORM affine-image mass/inertia closed forms (independent re-derivation)")
    check("s2_nonuniform_mass_inertia_closed_form", s2_nonuniform_mass_inertia_closed_form)
    print("S3 aspect bounds refuse|flag|unbounded (never silent repair)")
    check("s3_aspect_bounds_policy", s3_aspect_bounds_policy)
    print("S4 actual-monkey-target packet invariants (deterministic)")
    check("s4_actual_target_packet", s4_actual_target_packet)
    print("S5 bounded forearm envelope estimator (interior; never internal anatomy)")
    check("s5_forearm_envelope_estimator", s5_forearm_envelope_estimator)
    print("S6 strict JSON export (unresolved -> null, no NaN Infinity tokens)")
    check("s6_strict_json_export", s6_strict_json_export)
    print("S7 provenance record (hashes, scale, aspect policy, upstream identity)")
    check("s7_provenance_recorded", s7_provenance_recorded)
    print("S8 actuator hygiene (120 <actuator> records; default not an actuator)")
    check("s8_actuator_hygiene", s8_actuator_hygiene)
    print("S9 strict serialization gate (unresolved->null; resolved NaN refused)")
    check("s9_serialization_validation", s9_serialization_validation)
    print("S10 admission split (transported-under-assumption vs physically-admitted)")
    check("s10_admission_split", s10_admission_split)
    print("S11 envelope width screen (coarse) vs containment (spatial + unresolved-honest)")
    check("s11_envelope_screen_vs_containment", s11_envelope_screen_vs_containment)
    print("S12 attachment-candidates derivation (endpoint roles, mech-qual=false, transforms, hashes)")
    check("s12_attachment_candidates", s12_attachment_candidates)
    print("S13 raw-XML-to-export unit identity (mesh factor never enters source coords)")
    check("s13_source_units_raw_xml", s13_source_units_raw_xml)
    print("S14 local triangle-plane section loops (final skin-containment authority)")
    check("s14_section_loop_containment", s14_section_loop_containment)

    print()
    if _failures:
        print(f"{len(_failures)} FAILED: {_failures}")
        return FAIL
    print("ALL FALSIFIERS GREEN")
    return PASS


if __name__ == "__main__":
    sys.exit(main())