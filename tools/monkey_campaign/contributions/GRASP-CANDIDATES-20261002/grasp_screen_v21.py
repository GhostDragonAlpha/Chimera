# grasp_screen_v21.py - the GRASP-CANDIDATES v2.1 CHEAP GEOMETRIC SCREEN
# (axis-tilt phi grid x two-contact offset solve - the two structurally
# missing placement DOF).
#
# FROZEN LAW: the COMMITTED preregistration, git commit
# 655047b466f5d959e065252670bd275153a4d775
# (origin/review/GRASP-CANDIDATES-20261002, parent 27ba0ff8 = the
# instrument-merged tip), file
# tools/monkey_campaign/contributions/GRASP-CANDIDATES-20261002/PREREGISTRATION.md,
# sha256 e5bfa3cd32d26785bdcd7441f6af720fdc4a561938ff1c8de3f21dd7a6545106.
# This package is BASED at that commit: the base tree carries the frozen
# prereg bytes; this code verifies them at run and refuses on drift.
#
# Declared construction (prereg section 5):
#   theta: 720 (unchanged) x phi in {+60,+45,+30,+15,-15,-30,-45,-60} degrees
#   (axis tilted out of the perpendicular-to-chord plane, two senses)
#   x mirror {0,1} = 11,520 axes per posture;
#   PLUS the two-contact offset solve: 1-D bisection (40 iterations) on the
#   chord-direction offset tau_vh in [-0.05, +0.05] m equalizing the two tip
#   meshes' vertex upper-root envelopes, giving the offset pair (s, tau_vh).
#   POSTURES: q_c PRIMARY first; the other four ONLY if q_c yields >= 1
#   S0-survivor (the declared CPU cap law).
#   SCREENS: unchanged from the frozen formulation (same S0/S3/S1 classes,
#   same soundness law, CAP_S1_PER_POSTURE = 96, S1 budget 2.5 h, tolerances
#   frozen); ONE new active gate declared a priori: pad-orientation
#   cos > 0, active at S1-survivor recording.
#
# REUSED: the merged instrument (instrument_v2.py, unmodified) and the v2.0
# screen module grasp_screen.py (model build, light gate C1/C2/C3, posture
# prep, sound vertex scan, exact predicate). Serial, deterministic.
#
# Two-contact solve algebra (exact, per vertex p of a tip mesh, axis
# u = cos(phi) e + sin(phi) vh with e = the perpendicular axis at theta,
# offset point o = m + w s + vh tau, w = unit(vh x u)):
#   d = p - w s - vh tau; d.u = c*pe + s*pn - tau*s  (pe = p.e, pn = p.vh)
#   dist^2 = |d|^2 - (d.u)^2 = s^2 - 2Bs + K(tau) with
#   K(tau) = A - R^2 + c^2 tau^2 - 2 tau g,  A = p2 - (c*pe + s*pn)^2,
#   B = p.w, g = c*(c*pn - s*pe).
#   Upper root in s: s_v+(tau) = B + sqrt(D), D = B^2 - K
#                  = E - c^2 tau^2 + 2 tau g,  E = R^2 - A + B^2.
#   S_X(tau) = max_v s_v+(tau); the two-contact construction solves
#   S_A(tau) = S_B(tau) by bisection on [−0.05, +0.05].
#   Pruning: a vertex with E + max_t(-c^2 t^2 + 2 g t) <= 0 on the bracket
#   has NO root at ANY tau in the bracket and can never win the max; it is
#   dropped (sound: the max over the kept set equals the max over all).

import hashlib
import json
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import instrument_v2 as iv          # the merged, sealed instrument (unmodified)
import grasp_screen as gs           # the v2.0 screen module (shared helpers)

PREREG_COMMIT = "655047b466f5d959e065252670bd275153a4d775"
PREREG_SHA256 = (
    "e5bfa3cd32d26785bdcd7441f6af720fdc4a561938ff1c8de3f21dd7a6545106")
INSTRUMENT_PREREG_NAME = "INSTRUMENT_PREREGISTRATION.md"
INSTRUMENT_PREREG_SHA256 = (
    "897ca164ac5a63437c465783af2dd8f9c743d6c587d5423f4d3cec1b7190bdaf")
CONTROL_TABLE_NAME = "control_input_table.json"
CONTROL_TABLE_SHA256 = gs.CONTROL_TABLE_SHA256
INSTRUMENT_SHA256 = gs.INSTRUMENT_SHA256

# frozen v2.1 constants (prereg section 5; NOTHING here overrides the
# instrument's frozen TAU / PI_C / R / HH or the v2.0 screen caps)
N_THETA = 720
PHI_GRID_DEG = (-60, -45, -30, -15, 15, 30, 45, 60)
N_MIRROR = 2
TAU_BRACKET = 0.05                  # |tau_vh| <= 0.05 m (prereg)
BISECT_ITERS = 40                   # prereg-declared bisection iterations
TAU_SCAN_SAMPLES = 41               # declared bracketing pre-scan (uniform)
PAD_GATE_MIN_COS = 0.0              # the a-priori pad-orientation gate
DET_SLICE_AXES = 8
AXIS_IDENTITY_AXES = 4              # my u_perp at phi=0 vs gs.axis_basis

ANCHOR = gs.ANCHOR


def sha_of(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def canonical(x):
    return json.dumps(x, indent=1, sort_keys=True)


def axis_u_perp(prep, k):
    """The sealed GP1-CC3 perpendicular axis direction at theta_k
    (verbatim construction; identity vs gs.axis_basis asserted at run)."""
    vh = prep.vh
    helper = (0.0, 0.0, 1.0) if abs(vh[2]) < 0.9 else (0.0, 1.0, 0.0)
    e1 = iv.unit(iv.cross(vh, helper))
    e2 = iv.cross(vh, e1)
    theta = 2.0 * math.pi * k / N_THETA
    u_perp = iv.add(iv.scale(e1, math.cos(theta)),
                    iv.scale(e2, math.sin(theta)))
    return u_perp, theta


def axis_v21(prep, k, phi_rad, mirror):
    """The tilted axis: u = cos(phi) u_perp + sin(phi) vh (unit since the
    factors are orthonormal); w = +/-unit(vh x u) (independent of the tilt
    sign; the mirror flips it)."""
    u_perp, theta = axis_u_perp(prep, k)
    c = math.cos(phi_rad)
    s = math.sin(phi_rad)
    u = iv.add(iv.scale(u_perp, c), iv.scale(prep.vh, s))
    w_base = iv.unit(iv.cross(prep.vh, u))
    w = w_base if mirror == 0 else iv.scale(w_base, -1.0)
    return u, w, theta, u_perp, c, s


def tip_root_table(prep, tip, e, w, c, s):
    """Per-vertex quantities of one tip mesh (see header algebra). Returns
    parallel lists (B, g, E) restricted to vertices that can root somewhere
    in the tau bracket (sound pruning; see header)."""
    R = iv.TRUNK_R
    c2 = c * c
    pw = prep.p[tip]
    p2w = prep.p2[tip]
    pvh = prep.pvh[tip]
    B_l = []
    g_l = []
    E_l = []
    for i in range(len(pw)):
        p = pw[i]
        pe = iv.dot(p, e)
        pn = pvh[i]
        pu = c * pe + s * pn
        A = p2w[i] - pu * pu
        B = iv.dot(w, p)
        g = c * (c * pn - s * pe)
        E = R * R - A + B * B
        tc = g / c2
        if tc > TAU_BRACKET:
            tc = TAU_BRACKET
        elif tc < -TAU_BRACKET:
            tc = -TAU_BRACKET
        if E + 2.0 * g * tc - c2 * tc * tc <= 0.0:
            continue
        B_l.append(B)
        g_l.append(g)
        E_l.append(E)
    return B_l, g_l, E_l


def s_env(B_l, g_l, E_l, c2, tau):
    """S(tau) = max_v s_v+(tau); None if no kept vertex roots at this tau."""
    best = None
    base = c2 * tau * tau
    lin = 2.0 * tau
    for i in range(len(B_l)):
        D = E_l[i] - base + lin * g_l[i]
        if D > 0.0:
            sv = B_l[i] + math.sqrt(D)
            if best is None or sv > best:
                best = sv
    return best


def solve_two_contact(prep, e, w, c, s):
    """Equalize the two tip envelopes: g_fn(tau) = S_A(tau) - S_B(tau).
    Bisection REQUIRES a bracketing interval: per vertex D_v(tau) is
    concave in tau, so each side's defined set is an interval and the
    defined set of g_fn is an interval; the declared bracketing stage is a
    uniform pre-scan of TAU_SCAN_SAMPLES samples over [-0.05, +0.05] (None
    samples skipped; D may vanish at the exact bracket ends), then
    BISECT_ITERS halvings inside the first sign change. Returns
    (s_star, tau_star) or None (construction cannot form the two-contact
    candidate at this axis - recorded NO_APPROACH)."""
    c2 = c * c
    A_tbl = tip_root_table(prep, prep.tips[0], e, w, c, s)
    B_tbl = tip_root_table(prep, prep.tips[1], e, w, c, s)
    if not A_tbl[0] or not B_tbl[0]:
        return None

    def g_fn(tau):
        sa = s_env(A_tbl[0], A_tbl[1], A_tbl[2], c2, tau)
        if sa is None:
            return None
        sb = s_env(B_tbl[0], B_tbl[1], B_tbl[2], c2, tau)
        if sb is None:
            return None
        return sa - sb

    lo = hi = None
    glo = None
    prev_t = prev_g = None
    for i in range(TAU_SCAN_SAMPLES):
        t = -TAU_BRACKET + (2.0 * TAU_BRACKET) * i / (TAU_SCAN_SAMPLES - 1)
        g = g_fn(t)
        if g is None:
            continue
        if g == 0.0:
            lo = hi = t
            break
        if prev_g is not None and (g < 0.0) != (prev_g < 0.0):
            lo, hi = prev_t, t
            glo = prev_g
            break
        prev_t, prev_g = t, g
    if lo is None:
        return None
    if lo == hi:
        tau_star = lo
    else:
        for _ in range(BISECT_ITERS):
            mid = 0.5 * (lo + hi)
            gm = g_fn(mid)
            if gm == 0.0:
                lo = hi = mid
                break
            if (gm < 0.0) == (glo < 0.0):
                lo = mid
                glo = gm
            else:
                hi = mid
        tau_star = 0.5 * (lo + hi)
    s_star = s_env(A_tbl[0], A_tbl[1], A_tbl[2], c2, tau_star)
    if s_star is None:
        return None
    return s_star, tau_star


def pad_cos(prep, tip, o, u):
    """The v2.0 pad-orientation column definition: cos between the tip's
    distal-extent direction (joint origin -> farthest mesh vertex, world)
    and the inward cylinder radial at the tip origin."""
    origin = prep.positions[tip]
    far = max(prep.world[tip], key=lambda v: iv.dist(v, origin))
    dird = iv.unit(iv.sub(far, origin))
    rad = iv.sub(origin, o)
    rad = iv.sub(rad, iv.scale(u, iv.dot(rad, u)))
    rn = iv.norm(rad)
    if rn == 0.0:
        return None
    return iv.dot(dird, iv.scale(rad, -1.0 / rn))


def screen_axis_v21(prep, s1_clock, counters, k, phi_rad, mirror):
    """One candidate axis. Returns (reject_row or None, survivor or None,
    pad_failed_row or None). Slice cells are recorded on prep regardless of
    outcome."""
    u, w, theta, e, c, s = axis_v21(prep, k, phi_rad, mirror)
    sol = solve_two_contact(prep, e, w, c, s)
    if len(prep.det_slice) < DET_SLICE_AXES:
        prep.det_slice.append([k, phi_rad, mirror, list(u),
                               None if sol is None else sol[0],
                               None if sol is None else sol[1]])
    if sol is None:
        counters["s0_reject_no_approach"] += 1
        return [k, phi_rad, mirror, "S0_REJECT_NO_APPROACH"], None, None
    s_star, tau_star = sol
    if s_star < gs.S_BRACKET_LO or s_star > gs.S_BRACKET_HI:
        counters["s3_reject_bracket"] += 1
        return [k, phi_rad, mirror, "S3_REJECT_BRACKET", repr(s_star)], \
            None, None
    o = iv.add(prep.m, iv.add(iv.scale(w, s_star),
                              iv.scale(prep.vh, tau_star)))
    proven_bad = None
    unknown_bones = []
    bone_state = {}
    for name in prep.bones:
        (sc, sr) = prep.sphere_w[name]
        f_center = iv.cyl_sdf(iv.cyl_to_local(sc, o, u),
                              iv.TRUNK_R, iv.TRUNK_H / 2.0)
        if f_center > sr:
            bone_state[name] = dict(cls="SOUND_CLEAR", d=None, depth=None)
            continue
        sc_res = gs.scan_bone_vertices(prep, name, o, u)
        if sc_res["kind"] == "PENETRATED":
            proven_bad = (name, "S0_REJECT_CLEARANCE", sc_res["depth"])
            prep.clearance_by_bone[name] = \
                prep.clearance_by_bone.get(name, 0) + 1
            break
        if sc_res["kind"] == "TIP_DEEP":
            proven_bad = (name, "S0_REJECT_TIP_DEEP", sc_res["depth"])
            prep.clearance_by_bone[name] = \
                prep.clearance_by_bone.get(name, 0) + 1
            break
        unknown_bones.append(name)
    if proven_bad is not None:
        if proven_bad[1] == "S0_REJECT_CLEARANCE":
            counters["s0_reject_clearance"] += 1
        else:
            counters["s0_reject_tip_deep"] += 1
        return [k, phi_rad, mirror, proven_bad[1], proven_bad[0],
                repr(proven_bad[2])], None, None
    counters["s0_survivors"] += 1
    if counters["s1_cells_run"] >= gs.CAP_S1_PER_POSTURE:
        counters["s0_only_cap"] += 1
        return None, None, None
    if s1_clock[0] >= gs.S1_TIME_BUDGET_S:
        counters["s0_only_timing_cap"] += 1
        return None, None, None
    t0 = time.time()
    exact_state = {}
    for name in prep.bones:
        if name in bone_state and \
                bone_state[name]["cls"] == "SOUND_CLEAR":
            exact_state[name] = dict(cls="CLEAR", d=None, depth=None,
                                     how="level1_sound_clear")
    for name in sorted(set(unknown_bones) | set(prep.tips)):
        r = iv.adjudicate_body_vs_cylinder(prep.frames[name], o, u, iv.TAU)
        exact_state[name] = dict(cls=r["class"], d=r["d"], depth=r["depth"],
                                 how="level2_exact")
    verdict, reason = gs.classify_placement_bones(exact_state,
                                                  prep.contact_pair)
    s1_clock[0] += time.time() - t0
    counters["s1_cells_run"] += 1
    if verdict == "REJECT":
        if reason.startswith("S1_REJECT_NONCONTACT_PENETRATE"):
            counters["s1_reject_noncontact_penetrate"] += 1
        elif reason.startswith("S1_REJECT_NONCONTACT_TOUCH"):
            counters["s1_reject_noncontact_touch"] += 1
        elif reason.startswith("S2_REJECT_NO_CONTACT"):
            counters["s2_reject_no_contact"] += 1
        elif reason.startswith("S2_REJECT_DEEP"):
            counters["s2_reject_deep"] += 1
        return [k, phi_rad, mirror, reason], None, None
    ares = iv.adjudicate_body_vs_cylinder(prep.frames[ANCHOR], o, u, iv.TAU)
    pad_cols = {tb: pad_cos(prep, tb, o, u) for tb in prep.tips}
    tip_rows = {tb: dict(cls=exact_state[tb]["cls"], d=exact_state[tb]["d"],
                         depth=exact_state[tb]["depth"])
                for tb in prep.tips}
    pi_variants = {}
    for pi_v in iv.PI_C_VARIANTS:
        ok_v = True
        for tb in prep.tips:
            st = exact_state[tb]
            if st["cls"] == "CLEAR":
                ok_v = False
            elif st["cls"] == "GENUINE_PENETRATION":
                if st["depth"] is None or st["depth"] > pi_v:
                    ok_v = False
        pi_variants[repr(pi_v)] = ok_v
    row = dict(theta_index=k, theta=theta, phi_rad=phi_rad, mirror=mirror,
               s_star=s_star, tau_vh=tau_star, chord_t1=prep.chord,
               u=list(u), w=list(w), o=list(o),
               tips=tip_rows, pad_cos=pad_cols,
               pi_c_variants_pass=pi_variants,
               anchor_envelope=dict(cls=ares["class"], d=ares["d"],
                                    depth=ares["depth"],
                                    flag=ares["level1"]["flag"]),
               bodies=sorted((n, exact_state[n]["cls"], exact_state[n]["d"],
                              exact_state[n]["depth"])
                             for n in exact_state))
    pad_ok = all(pc is not None and pc > PAD_GATE_MIN_COS
                 for pc in pad_cols.values())
    if not pad_ok:
        counters["s1_survivor_pad_gate_failed"] += 1
        return None, None, row
    counters["survivors"] += 1
    return None, row, None


def prep_posture_v21(model, q_map, pair):
    prep = gs.prepare_posture(model, q_map, pair)
    # per-posture p.vh for the tip meshes (axis-independent solve input)
    prep.pvh = {}
    for tb in prep.tips:
        prep.pvh[tb] = [iv.dot(p, prep.vh) for p in prep.p[tb]]
    prep.clearance_by_bone = {}
    prep.det_slice = []
    return prep


def screen_posture_v21(prep, s1_clock, phi_grid):
    counters = dict(
        axes_total=N_THETA * len(phi_grid) * N_MIRROR,
        s0_reject_no_approach=0,
        s3_reject_bracket=0,
        s0_reject_clearance=0,
        s0_reject_tip_deep=0,
        s0_survivors=0,
        s0_only_cap=0,
        s0_only_timing_cap=0,
        s1_reject_noncontact_penetrate=0,
        s1_reject_noncontact_touch=0,
        s2_reject_no_contact=0,
        s2_reject_deep=0,
        s1_survivor_pad_gate_failed=0,
        survivors=0,
        s1_cells_run=0,
    )
    rejects = []
    survivors = []
    pad_failed = []
    for k in range(N_THETA):
        for phi_rad in phi_grid:
            for mirror in range(N_MIRROR):
                rej, surv, padf = screen_axis_v21(
                    prep, s1_clock, counters, k, phi_rad, mirror)
                if rej is not None:
                    rejects.append(rej)
                if surv is not None:
                    survivors.append(surv)
                if padf is not None:
                    pad_failed.append(padf)
    counted = sum(counters[key] for key in (
        "s0_reject_no_approach", "s3_reject_bracket", "s0_reject_clearance",
        "s0_reject_tip_deep", "survivors", "s0_only_cap",
        "s0_only_timing_cap", "s1_reject_noncontact_penetrate",
        "s1_reject_noncontact_touch", "s2_reject_no_contact",
        "s2_reject_deep", "s1_survivor_pad_gate_failed"))
    coverage_ok = (counted == counters["axes_total"]) and \
        (len(rejects) + len(survivors) + len(pad_failed)
         + counters["s0_only_cap"] + counters["s0_only_timing_cap"]
         == counters["axes_total"])
    return dict(counters=counters,
                clearance_by_bone=dict(sorted(
                    prep.clearance_by_bone.items())),
                survivors=survivors,
                pad_gate_failed=pad_failed,
                rejects=rejects,
                coverage_ok=coverage_ok,
                determinism_slice=prep.det_slice)


def axis_identity_check(prep):
    """My u_perp construction is IDENTICAL to the sealed v2.0 module's
    axis_basis (both at the frozen 720) over the declared slice."""
    ok = True
    cells = 0
    for k in range(AXIS_IDENTITY_AXES):
        u_mine, theta_mine = axis_u_perp(prep, k)
        u_gs, _w, theta_gs = gs.axis_basis(prep, k, 0)
        same = (canonical([u_mine, theta_mine])
                == canonical([u_gs, theta_gs]))
        ok = ok and same
        cells += 1
    return dict(cells=cells, ok=ok)


def pipeline():
    # ---- identity gates ----
    if gs.N_THETA != N_THETA:
        iv.refuse("v2_module_constant_drift", "gs.N_THETA vs N_THETA")
    prereg_path = os.path.join(HERE, "PREREGISTRATION.md")
    psha = sha_of(prereg_path)
    if psha != PREREG_SHA256:
        iv.refuse("preregistration_sha_mismatch", psha)
    instr_prereg = os.path.join(HERE, INSTRUMENT_PREREG_NAME)
    ipsha = sha_of(instr_prereg)
    if ipsha != INSTRUMENT_PREREG_SHA256:
        iv.refuse("instrument_preregistration_sha_mismatch", ipsha)
    isha = sha_of(os.path.join(HERE, "instrument_v2.py"))
    if isha != INSTRUMENT_SHA256:
        iv.refuse("instrument_copy_mismatch", isha)
    table_path = os.path.join(HERE, CONTROL_TABLE_NAME)
    tsha = sha_of(table_path)
    if tsha != CONTROL_TABLE_SHA256:
        iv.refuse("control_input_table_mismatch", tsha)
    gate, _mut, _stl_files, _bounds = iv.run_input_gate(instr_prereg)
    gs.emit("=" * 78)
    gs.emit("GATE. prereg COMMIT %s bytes %s MATCH (base tree carries the"
            " frozen prereg); instrument copy %s MATCH; instrument prereg"
            " %s MATCH; control table MATCH; inherited input gate ok=%s"
            " pins=%d." % (PREREG_COMMIT[:12], psha[:16], isha[:16],
                           ipsha[:16], gate["ok"], len(gate["pins"])))
    model = gs.build_model()
    with open(table_path, "r", encoding="utf-8") as fh:
        table = json.load(fh)
    lg = gs.light_gate(model, table)
    gs.emit("LIGHT GATE C1/C2/C3 (in-situ, frozen table): ok=%s %s"
            % (lg["ok"], json.dumps(lg["controls"], sort_keys=True)))
    if not lg["ok"]:
        iv.refuse("instrument_invalid_in_situ", json.dumps(lg["failures"]))
    wit = iv.check_witness_identity(model[0], model[1], model[2])
    gs.emit("WITNESS. sealed q_c(PRIMARY) FK reproduces the GP1 receipt tips"
            " and chord %r (T1 origins; refuse on drift)." % wit["chord"])
    phi_grid = [math.radians(d) for d in PHI_GRID_DEG]
    receipt = dict(
        schema="chimera.grasp_candidates.screen_v21.v1",
        task="GRASP-CANDIDATES-20261002 v2.1 cheap screen (axis-tilt phi"
             " grid x two-contact offset solve; prereg-frozen; chain stop 2)",
        lane="E:/ChimeraWork/monkey-coordination/grasp-candidates/",
        prereg_commit=PREREG_COMMIT,
        preregistration_sha256=psha,
        instrument_copy_sha256=isha,
        instrument_preregistration_sha256=ipsha,
        control_input_table_sha256=tsha,
        instrument_declaration_sha256=iv.DECLARATION_SHA256,
        frozen_constants=dict(tau=iv.TAU, pi_c=iv.PI_C, r_joint=iv.R_JOINT,
                              scale=iv.SCALE, trunk_r=iv.TRUNK_R,
                              trunk_h=iv.TRUNK_H,
                              n_theta=N_THETA,
                              phi_grid_deg=list(PHI_GRID_DEG),
                              n_mirror=N_MIRROR,
                              tau_bracket=TAU_BRACKET,
                              bisect_iters=BISECT_ITERS,
                              s_bracket=[gs.S_BRACKET_LO,
                                         gs.S_BRACKET_HI],
                              cap_s1_per_posture=gs.CAP_S1_PER_POSTURE,
                              s1_time_budget_s=gs.S1_TIME_BUDGET_S,
                              pad_gate_min_cos=PAD_GATE_MIN_COS),
        input_gate=gate,
        witness_identity=wit,
        light_gate=lg,
        postures={},
        predictions=dict(P1_min_qc_s0_survivors=1,
                         P2_max_qc_tip_deep_share_reachable=0.5,
                         P3_max_exact_survivors=20,
                         P4_both_tips_established=True),
    )
    s1_clock = [0.0]
    pmaps = gs.posture_maps(model[1])
    qc_name, qc_map, qc_pair = pmaps[0]
    prep = prep_posture_v21(model, qc_map, qc_pair)
    afc = axis_identity_check(prep)
    gs.emit("AXIS IDENTITY vs v2.0 axis_basis (phi=0 slice): cells=%d"
            " identical=%s" % (afc["cells"], afc["ok"]))
    if not afc["ok"]:
        iv.refuse("axis_identity_failed", "v21 vs v2")
    receipt["axis_identity"] = afc
    gs.emit("-" * 78)
    gs.emit("POSTURE %s pair=%s chord(T1 origins)=%r m (RECORDED, no gate)."
            % (qc_name, qc_pair, prep.chord))
    res = screen_posture_v21(prep, s1_clock, phi_grid)
    res["chord_t1"] = prep.chord
    receipt["postures"][qc_name] = res
    gs.emit("  counters: %s" % json.dumps(res["counters"], sort_keys=True))
    gs.emit("  clearance/tip-deep rejects by bone: %s"
            % json.dumps(res["clearance_by_bone"], sort_keys=True))
    gs.emit("  coverage_ok=%s s0_survivors=%d survivors=%d"
            % (res["coverage_ok"], res["counters"]["s0_survivors"],
               res["counters"]["survivors"]))
    if not res["coverage_ok"]:
        iv.refuse("coverage_arithmetic_broken", qc_name)
    reachable = res["counters"]["axes_total"] - \
        res["counters"]["s0_reject_no_approach"]
    tip_share = (res["counters"]["s0_reject_tip_deep"] / reachable
                 if reachable > 0 else None)
    receipt["q_c_metrics"] = dict(
        reachable_axes=reachable,
        tip_deep_share_reachable=tip_share,
        P1_s0_survivors_ge_1=bool(res["counters"]["s0_survivors"] >= 1),
        P2_tip_deep_share_below_50pct=bool(tip_share is not None
                                           and tip_share < 0.5),
    )
    gs.emit("  P1 s0_survivors>=1: %s; P2 tip_deep share reachable = %s"
            % (receipt["q_c_metrics"]["P1_s0_survivors_ge_1"],
               repr(tip_share)))
    # the declared posture cap law: other postures ONLY if q_c yields
    # >= 1 S0-survivor
    if res["counters"]["s0_survivors"] >= 1:
        for (pname, q_map, pair) in pmaps[1:]:
            prep = prep_posture_v21(model, q_map, pair)
            gs.emit("-" * 78)
            gs.emit("POSTURE %s pair=%s chord(T1 origins)=%r m."
                    % (pname, pair, prep.chord))
            res = screen_posture_v21(prep, s1_clock, phi_grid)
            res["chord_t1"] = prep.chord
            receipt["postures"][pname] = res
            gs.emit("  counters: %s"
                    % json.dumps(res["counters"], sort_keys=True))
            gs.emit("  coverage_ok=%s s0_survivors=%d survivors=%d"
                    % (res["coverage_ok"], res["counters"]["s0_survivors"],
                       res["counters"]["survivors"]))
            if not res["coverage_ok"]:
                iv.refuse("coverage_arithmetic_broken", pname)
    else:
        receipt["postures_law"] = ("q_c yielded 0 S0-survivors; the other"
                                   " four postures NOT run (the declared"
                                   " cap law)")
        gs.emit("POSTURE LAW: q_c 0 S0-survivors -> other postures not run.")
    # determinism slice: re-solve recorded cells; byte-compare
    det_ok = True
    det_cells = 0
    for pname in sorted(receipt["postures"]):
        hit = None
        for (nm, qm, pr) in pmaps:
            if nm == pname:
                hit = (qm, pr)
                break
        if hit is None:
            continue
        qm, pr = hit
        prep = prep_posture_v21(model, qm, pr)
        for (k, phi_rad, mirror, u, s_star, tau_star) in \
                receipt["postures"][pname]["determinism_slice"]:
            u2, w2, _th, e2, c2m, s2m = axis_v21(prep, k, phi_rad, mirror)
            sol2 = solve_two_contact(prep, e2, w2, c2m, s2m)
            if sol2 is None:
                same = (s_star is None and tau_star is None) and \
                    (canonical([u2]) == canonical([u]))
            else:
                s2, t2 = sol2
                same = (canonical([u2, s2, t2])
                        == canonical([u, s_star, tau_star]))
            det_ok = det_ok and same
            det_cells += 1
    receipt["determinism_slice"] = dict(cells=det_cells, ok=det_ok)
    gs.emit("DETERMINISM SLICE: %d cells re-solved byte-identical = %s"
            % (det_cells, det_ok))
    survivors_total = sum(receipt["postures"][p]["counters"]["survivors"]
                          for p in sorted(receipt["postures"]))
    s0_total = sum(receipt["postures"][p]["counters"]["s0_survivors"]
                   for p in sorted(receipt["postures"]))
    receipt["totals"] = dict(s0_survivors=s0_total,
                             exact_survivors=survivors_total)
    if survivors_total > 0:
        receipt["verdict"] = "SURVIVORS_PRESENT_SWEEP_AND_FORCE_BRANCH"
    elif s0_total > 0:
        receipt["verdict"] = "S0_SURVIVORS_ONLY_NO_EXACT_SURVIVOR"
    else:
        receipt["verdict"] = "ZERO_SURVIVORS_V22_LADDER_BRANCH"
    receipt["s1_cumulative_clock_s"] = s1_clock[0]
    gs.emit("=" * 78)
    gs.emit("VERDICT: %s (s0_survivors=%d exact_survivors=%d)"
            % (receipt["verdict"], s0_total, survivors_total))
    return receipt


def main():
    outdir = os.environ.get("CHIMERA_OUTPUT_DIR", "outputs")
    os.makedirs(outdir, exist_ok=True)
    try:
        receipt = pipeline()
        text = "\n".join(gs._report) + "\n"
    except iv.GateRefusal as exc:
        with open(os.path.join(outdir, "grasp_screen_v21_gate_receipt.json"),
                  "w", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(dict(
                schema="chimera.grasp_candidates.gate.v1",
                ok=False, refusal=exc.detail), indent=1) + "\n")
        print("REFUSAL: %s" % exc.detail, flush=True)
        raise SystemExit(3)
    with open(os.path.join(outdir, "grasp_screen_v21_receipt.json"), "w",
              encoding="utf-8", newline="\n") as fh:
        fh.write(canonical(receipt) + "\n")
    with open(os.path.join(outdir, "grasp_screen_v21_report.txt"), "w",
              encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    raise SystemExit(0)


if __name__ == "__main__":
    main()
