# run_gp1_battery.py - GP1 CANDIDATE-POSTURE FEASIBILITY battery (CC0-CC6).
# Implementation lane wk-gp1-impl, 2026-10-02, card MAT2-GP1-POSTURE-FEASIBILITY.
#
# Executes EXACTLY the declared experiment design of the frozen prereg
# (commit a18fe92e0ea7ed95edf4c4c383203c1af749b04d; committed bytes sha256
# bb7bf71829067d8f61142679948145a394f0413e0d0ddfbade7c0141bec13c2e, embedded
# below as preregistration_sha256 and refused on any mismatch).
#
# Experiment class: deterministic, sealed, stdlib-only derivation battery at a
# FROZEN configuration. NO physics-engine run, NO dynamics claim, NO GPU work,
# NO friction measurement, NO training. Frozen executable quantities: candidate
# solves over the declared 6-joint subboxes (grid 7/joint + 4 zoom rounds +
# coordinate polish 3 passes x 80 iters); placement sweep 720 angles x 2
# mirrors; STL parse 19 files + anchor bounds. No tick windows exist; no
# seconds annotation appears in any receipt (grid sizes and counts only).
#
# Exit semantics: 0 = run completed with recorded verdicts (candidate closures
# and NON-CLOSE load-support verdicts are DECLARED HONEST OUTCOMES, not run
# failures; the refusal-wording law applies); 3 = gate refusal
# (threshold_pin_mismatch / input_pin_mismatch / input_pin_missing /
# preregistration_sha_mismatch) or determinism/consistency-gate failure.

import hashlib
import json
import math
import os
import re
import sys

import gp1_physics as gp

VENDOR_MESHES = gp.REPO + "vendor/myo_sim/meshes/"

CANDIDATE_LADDER = [
    dict(cid="PRIMARY", digit=3),
    dict(cid="F1", digit=4),
    dict(cid="F2", digit=5),
    dict(cid="F3", digit=2),
]
SOLVE_TOL = 1e-6
SECONDARY_FIT_TOL = 1e-4
N_THETA = 720
ANTIPARALLEL_TOL = 1e-12
LINEARITY_TOL = 1e-12
IDENTITY_TOL = 1e-12
THRESHOLD_MATCH_TOL = 1e-9
SCENARIO_MU = 0.41  # DECLARED SCENARIO PARAMETER (labeled on every use)

_report = []


def emit(line=""):
    _report.append(line)
    print(line)


class GateRefusal(SystemExit):
    def __init__(self, code, detail):
        SystemExit.__init__(self, code)
        self.code = code
        self.detail = detail


def refuse(code, detail):
    raise GateRefusal(3, code + ": " + detail)


# ===========================================================================
# CC0 INPUT GATE
# ===========================================================================


def run_input_gate():
    gate = dict(schema="chimera.gp1.input_gate.v1", pins=[], constants=[])
    here = os.path.dirname(os.path.abspath(__file__))
    prereg_path = os.path.join(here, "PREREGISTRATION.md")
    if not os.path.isfile(prereg_path):
        prereg_path = os.path.join(
            os.getcwd(),
            "tools/monkey_campaign/contributions/GP1-POSTURE-20261002/PREREGISTRATION.md")
    if not os.path.isfile(prereg_path):
        refuse("input_pin_missing", "committed prereg bytes not found")
    h = gp.sha256_file(prereg_path)
    if h != gp.PREREG_SHA256:
        refuse("preregistration_sha_mismatch", h)
    gate["preregistration_sha256"] = h
    gate["prereg_commit"] = gp.PREREG_COMMIT
    emit("=" * 78)
    emit("CC0. INPUT GATE (hash pins, constant re-parse, prefix identity)")
    emit("  committed prereg bytes sha256 %s: MATCH (embedded as preregistration_sha256)" % h)

    for path, expect in sorted(gp.PINS_ABS.items()):
        if not os.path.isfile(path):
            refuse("input_pin_missing", path)
        h2 = gp.sha256_file(path)
        ok = h2 == expect
        gate["pins"].append(dict(path=path, sha256=h2, match=ok))
        if not ok:
            refuse("input_pin_mismatch", path + " " + h2)
    emit("  %d absolute-path pins hash-verified (all MATCH)" % len(gp.PINS_ABS))

    gm_path = gp.COORD_BASE + "x-aperture/GRASP_MECHANISMS.md"
    with open(gm_path, "rb") as fh:
        gm_cur = fh.read()
    prefix_len = None
    for ln in range(len(gm_cur) + 1):
        if hashlib.sha256(gm_cur[:ln]).hexdigest() == gp.GRASP_MECH_PRE_AMENDMENT_SHA:
            prefix_len = ln
            break
    gate["grasp_mechanisms"] = dict(
        current_sha256=hashlib.sha256(gm_cur).hexdigest(),
        pre_amendment_sha256=gp.GRASP_MECH_PRE_AMENDMENT_SHA,
        prefix_identity_verified=prefix_len is not None,
        prefix_len=prefix_len,
        append_only_record_present=gp.GRASP_MECH_PRE_AMENDMENT_SHA.encode() in gm_cur,
        note="declared dual-hash discrepancy (prereg section 7): current bytes pin the"
             " APPEND-ONLY section 7; prefix identity re-verified against the"
             " pre-amendment hash; never silently normalized",
    )
    emit("  GRASP_MECHANISMS: current ac5e2583... MATCH; prefix identity %s"
         % ("VERIFIED at prefix byte length %d" % prefix_len
            if prefix_len is not None else "FAILED"))
    if prefix_len is None:
        refuse("input_pin_mismatch", "GRASP_MECHANISMS prefix identity not found")

    def parse_float(path, pattern, expect, label, group=1):
        with open(path, "r", encoding="utf-8") as fh:
            text = fh.read()
        m = re.search(pattern, text)
        if m is None:
            refuse("threshold_pin_mismatch", "%s pattern not found for %s" % (path, label))
        val = float(m.group(group))
        ok = (val == expect)
        gate["constants"].append(dict(source=path, label=label, pattern=pattern,
                                      parsed=val, expected=expect, match=ok))
        if not ok:
            refuse("threshold_pin_mismatch", "%s %s parsed %r expected %r"
                   % (path, label, val, expect))
        return val

    g01 = gp.COORD_BASE + "evidence-store/MAT2-G01/report/REPORT.md"
    D = parse_float(g01, r"declared_trunk_diameter_m=([0-9.eE+-]+)", 0.074,
                    "declared_trunk_diameter_m")
    SPAN = parse_float(g01, r"recorded_fingertip_span_m=([0-9.eE+-]+)",
                       0.056663099802559125, "recorded_fingertip_span_m")
    MARGIN = parse_float(g01, r"margin_m=(-?[0-9.eE+-]+)", -0.01733690019744087,
                         "g01_wrap_margin_m")
    R_TRUNK = parse_float(g01, r"\| declared trunk radius \(from sealed analytic volume\)"
                               r" \| ([0-9.]+) m \|", 0.037, "declared_trunk_radius_m")
    H_TRUNK = parse_float(g01, r"\| trunk height \| ([0-9.]+) m \|", 1.158, "trunk_height_m")
    CAP36_REC = parse_float(g01, r"\| capacity at record-g 9\.81 \| ([0-9.]+) N \|", 36.0,
                            "per_contact_capacity_record_g_N")
    CAP36_STD = parse_float(g01, r"\| capacity at standard g 9\.80665 \| ([0-9.]+) N \|",
                            35.98770642201834, "per_contact_capacity_std_g_N")
    if abs((SPAN - D) - MARGIN) > 1e-15:
        refuse("threshold_pin_mismatch", "G01 margin identity (span - D != margin)")

    rtc = gp.COORD_BASE + "b07-prereqs/RUNTIME_CONTRACT.md"
    CAP_MP = parse_float(rtc, r"torque_cap_N_m hip 11\.2125 / knee 6\.6375 / ankle 7\.4 /"
                              r" MP ([0-9.]+)", 0.8875, "MP_torque_cap_Nm")
    M_ASSEMBLY = parse_float(rtc, r"assembly_mass_kg ([0-9.]+)", 10.037998000000004,
                             "assembly_mass_kg")
    W_STD = parse_float(rtc, r"weight_N ([0-9.]+)", 98.43913308670002, "weight_N_std_g")

    bench = gp.BENCH + "GRASP_BENCHMARK.md"
    MU_BENCH = parse_float(bench, r"mu_s = ([0-9.]+)", 0.6, "mu_s_placeholder")
    JN = parse_float(bench, r"`jn = ([0-9.]+) N\*s`", 0.30, "jn_Ns_per_contact_tick")
    DT = parse_float(bench, r"`dt = ([0-9.]+) s`", 0.005, "dt_s")
    ANCHOR_KG = parse_float(bench, r"\*\*([0-9.]+) kg supported-load capacity\*\*",
                            3.6697247706422016, "benchmark_anchor_kg")
    ANCHOR_STD = parse_float(bench, r"kg x 9\.80665 m/s\^2 = ([0-9.]+) N",
                             35.98770642201834, "benchmark_anchor_std_g_N")
    PRESS = JN / DT
    if PRESS != 60.0:
        refuse("threshold_pin_mismatch", "jn/DT != 60.0 N (%r)" % PRESS)

    fric = gp.COORD_BASE + "g04-friction/FRICTION_SOURCES.md"
    H_FRIC = parse_float(fric, r"radius\s+0\.037 m, height ([0-9.]+) m", 1.158,
                         "friction_sources_trunk_height_m")
    if H_FRIC != H_TRUNK:
        refuse("threshold_pin_mismatch", "trunk height disagreement FRICTION_SOURCES vs G01")
    parse_float(fric, r"`jn/dt = ([0-9.]+) N`", 60.0, "friction_sources_press_N")
    with open(fric, "r", encoding="utf-8") as fh:
        fric_text = fh.read()
    for needle, lab in (("0.41", "gerhardt_scenario_parameter"),
                        ("32-segment", "trunk_32_segment_mesh"),
                        ("trunk_01.lateral", "grip_surface"),
                        ("CONFIRMED GAP", "friction_gap_verdict")):
        if needle not in fric_text:
            refuse("threshold_pin_mismatch", "FRICTION_SOURCES missing %s" % lab)

    gg = gp.COORD_BASE + "climb-derivation/grasp-geometry/derivation_output.txt"
    WINDOW_RECORDED = parse_float(gg, r"\[([0-9.]+), 0\.074\] m", 0.06345447650272827,
                                  "pincer_window_recorded_m")
    MUCRIT_RECORDED = parse_float(gg, r"mu_crit = ([0-9.]+)", 0.8399663223427114,
                                  "recorded_mu_crit")
    window_recomputed = D * math.cos(math.atan(MU_BENCH))
    if window_recomputed != WINDOW_RECORDED:
        refuse("threshold_pin_mismatch",
               "window re-derivation delta %r (sealed precedent: delta 0.0)"
               % abs(window_recomputed - WINDOW_RECORDED))
    mcrit_recomputed = math.tan(math.acos(SPAN / D))
    if mcrit_recomputed != MUCRIT_RECORDED:
        refuse("threshold_pin_mismatch",
               "mu_crit re-derivation delta %r (sealed precedent: delta 0.0)"
               % abs(mcrit_recomputed - MUCRIT_RECORDED))
    emit("  WRAP-2 window D*cos(atan 0.6) re-derived delta 0.0; recorded mu_crit")
    emit("  tan(acos(span/D)) re-derived delta 0.0")

    with open(gp.COORD_BASE + "climb-derivation/derivation_output.txt", "r",
              encoding="utf-8") as fh:
        climb_out = fh.read()
    if "0.048761970806378674" not in climb_out:
        refuse("threshold_pin_mismatch", "m_eff line missing from climb derivation_output")

    with open(gp.COORD_BASE + "evidence-store/MAT2-D-MASSREG/numerical/mass_register.json") as fh:
        massreg = json.load(fh)
    if massreg["totals"]["builder_order_sum_kg"]["value"] != 10.037998000000004:
        refuse("threshold_pin_mismatch", "mass_register builder_order_sum_kg")

    with open(gp.COORD_BASE + "evidence-store/MAT2-B07/unclassified/adoption_record.json",
              "r", encoding="utf-8") as fh:
        adoption_text = fh.read()
    gate["adoption_tc8_present"] = "TC-8" in adoption_text

    mmap = gp.REPO + "tools/monkey_campaign/MONKEY_COMPLETION_MAP.md"
    with open(mmap, "r", encoding="utf-8") as fh:
        mmap_text = fh.read()
    if "| C16 | Grasp reach and anatomical correspondence |" not in mmap_text \
            or "geometry feasibility precedes skill training" not in mmap_text:
        refuse("threshold_pin_mismatch", "C16 row text not found in MONKEY_COMPLETION_MAP")

    with open(gp.COORD_BASE + "evidence-store/MAT2-A09/numerical/grasp_package.json") as fh:
        a09 = json.load(fh)
    pin_a05 = a09["input_pins"]["a05_mutation_structure"]["sha256"]
    a05_path = (gp.COORD_BASE +
                "evidence-store/MAT2-A05/workspace_evidence/48b037593f63_mutation_structure.json")
    if pin_a05 != gp.PINS_ABS[a05_path]:
        refuse("input_pin_mismatch", "A09 a05_mutation_structure pin chain")

    with open(a05_path) as fh:
        mut = json.load(fh)
    scale_a = float(mut["allometry"]["mutation_scale"])
    scale_b = float(mut["bodies"][0]["mutation"]["scale"])
    if scale_a != scale_b or scale_a != 0.5384048132470733:
        refuse("threshold_pin_mismatch", "allometry mutation scale")
    stl_pins = {}
    for b in mut["bodies"]:
        for g in b.get("geometry", []):
            if "stl_sha256" in g:
                stl_pins[b["name"]] = g["stl_sha256"]
    if len(stl_pins) != 19:
        refuse("input_pin_missing", "expected 19 stl pins, found %d" % len(stl_pins))
    on_disk = {}
    for fname in sorted(os.listdir(VENDOR_MESHES)):
        if fname.lower().endswith(".stl"):
            on_disk[fname] = gp.sha256_file(VENDOR_MESHES + fname)
    stl_files = {}
    for name in sorted(stl_pins):
        hits = [f for f, h3 in on_disk.items() if h3 == stl_pins[name]]
        if len(hits) != 1:
            refuse("input_pin_mismatch",
                   "stl pin for %s matched %d files" % (name, len(hits)))
        stl_files[name] = VENDOR_MESHES + hits[0]
    gate["mesh_pins"] = dict(count=len(stl_files), all_match=True,
                             files=dict(sorted(stl_files.items())))
    emit("  19/19 A05 stl_sha256 pins matched on-disk vendor meshes (1:1)")
    emit("  all quoted constants re-parsed and value-matched (mismatch = refusal)")
    gate["ok"] = True

    return gate, dict(a09=a09, mut=mut, stl_files=stl_files,
                      bounds=mut["envelope_check"]["hand_vtp_bounds_m"],
                      D=D, R=R_TRUNK, H=H_TRUNK, span=SPAN, window=WINDOW_RECORDED,
                      mu=MU_BENCH, jn=JN, dt=DT, press=PRESS, cap_mp=CAP_MP,
                      m_assembly=M_ASSEMBLY, w_std=W_STD,
                      anchor_kg=ANCHOR_KG, anchor_std=ANCHOR_STD,
                      cap36_rec=CAP36_REC, cap36_std=CAP36_STD,
                      scale=scale_a, mcrit_recorded=MUCRIT_RECORDED)


# ===========================================================================
# CC2 segments
# ===========================================================================

_STL_CACHE = {}


def parse_stl_cached(path):
    if path not in _STL_CACHE:
        _STL_CACHE[path] = gp.parse_stl_vertices(path)
    return _STL_CACHE[path]


def build_segments(bodies, stl_files, bounds, scale, positions, rotations,
                   contact_bodies):
    segs = []
    anchor_center_local, anchor_r = gp.anchor_bounds_sphere(bounds)
    segs.append(dict(name="macaque_hand_anchor", center_local=anchor_center_local,
                     radius=anchor_r,
                     is_contact="macaque_hand_anchor" in contact_bodies,
                     source="hand_vtp_bounds_m AABB"))
    for name in sorted(bodies):
        if name == "macaque_hand_anchor":
            continue
        verts, ntri = parse_stl_cached(stl_files[name])
        center_local, r = gp.bounding_sphere_scaled(verts, scale)
        segs.append(dict(name=name, center_local=center_local, radius=r,
                         is_contact=name in contact_bodies, source="stl", tris=ntri))
    out = []
    for s in segs:
        wc = gp.add(positions[s["name"]], gp.mat_vec(rotations[s["name"]], s["center_local"]))
        out.append(dict(name=s["name"], center=wc, radius=s["radius"],
                        is_contact=s["is_contact"], source=s["source"],
                        center_local=list(s["center_local"]), tris=s.get("tris")))
    return out


def self_collision_table(bodies, segments):
    rows = []
    n_overlap = 0
    n_tested = 0
    for i in range(len(segments)):
        for j in range(i + 1, len(segments)):
            si, sj = segments[i], segments[j]
            adjacent = (bodies[si["name"]]["parent"] == sj["name"]) or \
                       (bodies[sj["name"]]["parent"] == si["name"])
            d = gp.norm(gp.sub(si["center"], sj["center"]))
            overlap = bool(d < si["radius"] + sj["radius"])
            rows.append(dict(a=si["name"], b=sj["name"], distance=d,
                             radius_sum=si["radius"] + sj["radius"],
                             clearance=d - (si["radius"] + sj["radius"]),
                             adjacent=bool(adjacent), proxy_overlap=overlap))
            if not adjacent:
                n_tested += 1
                if overlap:
                    n_overlap += 1
    return rows, n_tested, n_overlap


# ===========================================================================
# CC5 statics helpers
# ===========================================================================


def contact_set_at(names_points, o_w, u_w):
    """Declared radial normals at the witness placement for each contact."""
    contacts = []
    for (name, p) in names_points:
        d = gp.sub(p, o_w)
        z = gp.dot(d, u_w)
        n = gp.unit(gp.sub(d, gp.scale(u_w, z)))
        contacts.append(dict(name=name, point=list(p), normal=list(n), axial_coord=z))
    return contacts


def joint_torque_table(joint_records, loaded_joints, contacts, press):
    table = {}
    for (jn, body, o, u) in joint_records:
        tau = 0.0
        arms = {}
        for c in contacts:
            p = tuple(c["point"])
            n = tuple(c["normal"])
            fvec = gp.scale(n, press)
            rvec = gp.sub(p, o)
            tau += gp.dot(gp.cross(rvec, fvec), u)
            arms[c["name"]] = gp.norm(gp.cross(rvec, u))
        table[jn] = dict(body=body, origin=list(o), axis=list(u), tau=tau, arms=arms,
                         loaded_chain=jn in loaded_joints)
    return table


def gravity_torque_table(bodies, positions, rotations, joint_records, loaded_joints,
                         g_dir, g_mag, anchor_name):
    """Two DECLARED alternative allocation views (never summed):
    view A: the 0.049 kg effective anchor mass at the anchor mass center -
            loads exactly the joints declared IN the anchor (the wrist);
    view B: the 19 declared digit mass priors (proportional redistribution) -
            each loads the joints whose subtree carries it."""
    desc = gp.descendants_map(bodies)
    mc_a = tuple(bodies[anchor_name]["mass_center"])
    c_anchor = gp.add(positions[anchor_name], gp.mat_vec(rotations[anchor_name], mc_a))
    gvec = gp.scale(g_dir, g_mag)
    mass_a = bodies[anchor_name]["mass_kg"]
    viewA = {}
    viewB = {}
    mass_sum_b = 0.0
    for name in sorted(bodies):
        if name != anchor_name:
            mass_sum_b += bodies[name]["mass_kg"]
    for (jn, body, o, u) in joint_records:
        if body == anchor_name:
            tau_a = gp.dot(gp.cross(gp.sub(c_anchor, o), gp.scale(gvec, mass_a)), u)
        else:
            tau_a = 0.0  # view A has no mass downstream of the wrist joints
        loaded = [body] + desc[body]
        tau_b = 0.0
        for s in loaded:
            if s == anchor_name:
                continue
            m_s = bodies[s]["mass_kg"]
            c_s = gp.add(positions[s], gp.mat_vec(rotations[s], bodies[s]["mass_center"]))
            tau_b += gp.dot(gp.cross(gp.sub(c_s, o), gp.scale(gvec, m_s)), u)
        viewA[jn] = dict(tau=tau_a, loaded_chain=jn in loaded_joints)
        viewB[jn] = dict(tau=tau_b, loaded_chain=jn in loaded_joints)
    return viewA, viewB, mass_sum_b


def load_support_block(n, thr, C, formula_only=False):
    t = thr["n%d" % n]
    closes_std = bool(t["p_req_std"] <= C["press"])
    closes_rec = bool(t["p_req_rec"] <= C["press"])
    thr_std = t["threshold_mu_std"]
    thr_rec = t["threshold_mu_rec"]
    return dict(
        n=n,
        formula_only=formula_only,
        formula_only_note="recorded as the declared B-G4 arithmetic ONLY; no achieved"
                          " collision-checked n=%d contact set exists at this candidate" % n
                          if formula_only else None,
        p_req_std_g_N=t["p_req_std"], p_req_rec_g_N=t["p_req_rec"],
        declared_ceiling_N=C["press"],
        verdict_placeholder_mu_std_g="CLOSE" if closes_std else "NON-CLOSE",
        verdict_placeholder_mu_rec_g="CLOSE" if closes_rec else "NON-CLOSE",
        threshold_mu_std_g=thr_std, threshold_mu_rec_g=thr_rec,
        threshold_inside_FA_band=bool(0.3 <= thr_std <= 1.0),
        above_placeholder_0p6=bool(thr_std > 0.6),
        scenario_mu_041=dict(
            label="DECLARED SCENARIO PARAMETER (human-analogue Gerhardt-2008"
                  " single-coefficient reading; NOT monkey-bark, UNMEASURED)",
            value=SCENARIO_MU,
            verdict="NON-CLOSE" if SCENARIO_MU < thr_std else "CLOSE",
            p_req_041_std_g_N=C["w_std"] / (n * SCENARIO_MU),
            diagnostic_only=True,
        ),
        per_contact_capacity_at_placeholder=dict(
            rec_g_N=C["cap36_rec"], std_g_N=C["cap36_std"],
            formula="mu_s * jn/DT (rec-g label); benchmark 3.6697247706422016 kg x"
                    " 9.80665 (std-g)"),
    )


# ===========================================================================
# the pipeline (executed twice for the CC6 determinism receipt)
# ===========================================================================


def pipeline():
    del _report[:]
    gate, C = run_input_gate()
    mut, bodies, joints_by_name, anchor_name, worst_pos = gp.parse_hand_model(
        gp.COORD_BASE +
        "evidence-store/MAT2-A05/workspace_evidence/48b037593f63_mutation_structure.json",
        gp.COORD_BASE +
        "evidence-store/MAT2-A05/workspace_evidence/9c91124600ab_macaque_hand_mutation.xml")
    tips, palm = gp.parse_a09_tips(C["a09"])

    emit("=" * 78)
    emit("MODEL. Certified hand parsed from pinned bytes (A05 authority; A05 XML")
    emit("  cross-checked exactly at parse; worst XML-vs-JSON position delta %r m)."
         % worst_pos)
    zero = {jn: 0.0 for jn in joints_by_name}
    max_delta = 0.0
    for name in sorted(tips):
        p0 = gp.fk_origin(bodies, anchor_name, zero, tips[name]["body"])
        d = max(abs(x - y) for x, y in zip(p0, tips[name]["recorded"]))
        max_delta = max(max_delta, d)
    palm0 = gp.fk_origin(bodies, anchor_name, zero, palm["body"])
    dpalm = max(abs(x - y) for x, y in zip(palm0, palm["recorded"]))
    if max_delta >= IDENTITY_TOL or dpalm >= IDENTITY_TOL:
        refuse("threshold_pin_mismatch",
               "q=0 records identity broken (%r, palm %r)" % (max_delta, dpalm))
    emit("  records identity: FK(q=0) origins == recorded A09 endpoints (+ palm ref),")
    emit("  max |delta| = %r m (sealed-aperture parser discipline)." % max_delta)

    w_rec = C["m_assembly"] * 9.81
    thr = {}
    for n in (2, 3):
        thr["n%d" % n] = dict(
            p_req_std=C["w_std"] / (n * C["mu"]),
            p_req_rec=w_rec / (n * C["mu"]),
            threshold_mu_std=C["w_std"] / (n * C["press"]),
            threshold_mu_rec=w_rec / (n * C["press"]),
        )
    emit("=" * 78)
    emit("LOAD-SUPPORT LAW (K01/G04 arithmetic; P_req = W/(n*mu); threshold")
    emit("  mu >= W/(n*(jn/DT)); std-g authority + rec-g duals; ceiling = press):")
    for n in (2, 3):
        t = thr["n%d" % n]
        emit("  n=%d: P_req std-g %r N, rec-g %r N; threshold mu std-g %r, rec-g %r"
             % (n, t["p_req_std"], t["p_req_rec"], t["threshold_mu_std"],
                t["threshold_mu_rec"]))
    pred_checks = dict(p_req_n2_std=82.03261090558335, thr_n2_std=0.8203261090558336,
                       thr_n2_rec=0.8206063365000001, p_req_n3_std=54.68840727038889,
                       thr_n3_std=0.5468840727038889)
    pred_match = dict(
        p_req_n2_std=abs(thr["n2"]["p_req_std"] - pred_checks["p_req_n2_std"]) <= THRESHOLD_MATCH_TOL,
        thr_n2_std=abs(thr["n2"]["threshold_mu_std"] - pred_checks["thr_n2_std"]) <= THRESHOLD_MATCH_TOL,
        thr_n2_rec=abs(thr["n2"]["threshold_mu_rec"] - pred_checks["thr_n2_rec"]) <= THRESHOLD_MATCH_TOL,
        p_req_n3_std=abs(thr["n3"]["p_req_std"] - pred_checks["p_req_n3_std"]) <= THRESHOLD_MATCH_TOL,
        thr_n3_std=abs(thr["n3"]["threshold_mu_std"] - pred_checks["thr_n3_std"]) <= THRESHOLD_MATCH_TOL,
    )
    emit("  prereg P7 quote cross-checks (tol 1e-9): %s"
         % json.dumps(pred_match, sort_keys=True))
    if not all(pred_match.values()):
        refuse("threshold_pin_mismatch", "P7 quoted-threshold cross-check failed")

    # ---------------- CC1: candidate solves ----------------
    emit("=" * 78)
    emit("CC1. CANDIDATE CONTACT CONFIGURATIONS (declared 6-joint subboxes; the")
    emit("  other 16 joints held at 0; nominal target c_t = D = %r m; tolerance" % C["D"])
    emit("  |chord - c_t| <= %r m; declared window [%r, %r] m)"
         % (SOLVE_TOL, C["window"], C["D"]))

    def moving_joints(tip_body):
        tl = []
        for jn in sorted(joints_by_name):
            if jn in ("mutation_wrist_flexion", "mutation_wrist_abduction"):
                continue
            moved = 0.0
            for q in joints_by_name[jn]["range"]:
                qm = dict(zero)
                qm[jn] = q
                moved = max(moved, gp.norm(gp.sub(
                    gp.fk_origin(bodies, anchor_name, qm, tip_body),
                    gp.fk_origin(bodies, anchor_name, zero, tip_body))))
            if moved > 0.0:
                tl.append(jn)
        return tl

    tip_joints = {name: moving_joints(tips[name]["body"]) for name in sorted(tips)}
    for name in sorted(tip_joints):
        emit("  sensitivity: %s tip origin moved by %s" % (name, tip_joints[name]))

    candidates = []
    for cand in CANDIDATE_LADDER:
        k = cand["digit"]
        dname = "digit%d" % k
        jlist = sorted(set(tip_joints["thumb"]) | set(tip_joints[dname]))
        declared = {"cmc_abduction", "cmc_flexion", "mp_flexion",
                    "mcp%d_abduction" % k, "mcp%d_flexion" % k, "pm%d_flexion" % k}
        if set(jlist) != declared:
            refuse("threshold_pin_mismatch",
                   "declared 6-joint set mismatch for %s: %s" % (dname, sorted(jlist)))
        emit("  %s (thumb-%s): declared 6-joint subbox %s" % (cand["cid"], dname, jlist))

        def chord_fn(vals, ja="thumb", jb=dname, jl=jlist):
            qm = dict(zero)
            for jn, v in zip(jl, vals):
                qm[jn] = v
            return gp.norm(gp.sub(
                gp.fk_origin(bodies, anchor_name, qm, tips[ja]["body"]),
                gp.fk_origin(bodies, anchor_name, qm, tips[jb]["body"])))

        ranges = [joints_by_name[jn]["range"] for jn in jlist]
        sol = gp.solve_target(jlist, ranges, chord_fn, C["D"], window_hi=C["D"])
        chord = sol["chord"]
        in_window = bool(C["window"] <= chord <= C["D"])
        tol_met = bool(sol["residual"] <= SOLVE_TOL)
        if in_window and tol_met:
            status = "SOLVED_NOMINAL"
        elif in_window:
            status = "PROCEED_AT_ACHIEVED"
        else:
            status = "CLOSED_SOLVE"
        emit("  %s: achieved chord %r m (residual %r m; best-any %r; evals %d) -> %s"
             % (cand["cid"], chord, sol["residual"], sol["best_any_chord"],
                sol["evals"], status))
        candidates.append(dict(
            cid=cand["cid"], pair=["thumb", dname], digit=k, joints=jlist,
            solve=dict(q=sol["q"], achieved_chord=chord, residual=sol["residual"],
                       best_any_chord=sol["best_any_chord"],
                       best_any_residual=sol["best_any_residual"], evals=sol["evals"],
                       grid_n=sol["grid_n"], zooms=sol["zooms"],
                       polish_passes=sol["polish_passes"],
                       polish_iters=sol["polish_iters"],
                       objective="window-admissible |chord - D| (samples above D rejected"
                                 " lexicographically; best-any sample recorded)"),
            window_membership=in_window, solve_tolerance_met=tol_met, status=status))

    receipt = dict(
        schema="chimera.gp1.posture_feasibility.v1",
        task="MAT2-GP1-POSTURE-FEASIBILITY",
        implementation_lane="wk-gp1-impl (E:/ChimeraWork/monkey-coordination/gp1-impl/)",
        preregistration_sha256=gp.PREREG_SHA256,
        prereg_commit=gp.PREREG_COMMIT,
        prereg_branch="origin/review/GP1-POSTURE-20261002",
        package_base_sha=gp.PREREG_COMMIT,
        experiment_class="deterministic sealed stdlib-only derivation battery at a frozen"
                         " configuration; no physics-engine run, no dynamics claim, no GPU,"
                         " no friction measurement, no training",
        candidate_law="a candidate failure closes ONLY that candidate (Captain's law,"
                      " prereg section 0); the fallback ladder exists for that reason; any"
                      " GP1 pass is FEASIBILITY evidence at the declared parameters, never a"
                      " physical grasp claim; the reaching fence stands (GP2)",
        assumption_set=dict(
            A1="declared mass line (PROVISIONAL 10.037998 kg lineage; reserved decision"
               " KEEP-10.038-AS-DYNAMICS | ORDER-BAND-MASS-ASSEMBLY |"
               " ROUTE-TO-WALK-TIER-CARD stays OPEN)",
            A2="contact points are the certified A09 fingertip ORIGINS - POINTS, pads ABSENT",
            A3="declared press operating point 60.0 N per contact (jn/DT; never"
               " actuator-qualified; x_press ABSENT)",
            A4="declared trunk: exact analytic cylinder radius 0.037 m, diameter 0.074 m,"
               " height 1.158 m, 32-segment contact mesh, surface trunk_01.lateral",
            A5="friction placeholders mu_s=0.6 / mu_k=0.4 (NAMED PLACEHOLDERS, verdict GAP,"
               " NB-01/02); 0.41 a DECLARED SCENARIO PARAMETER (human-analogue"
               " Gerhardt-2008 single-coefficient reading; NOT monkey-bark, UNMEASURED)",
            A6="law forms: WRAP-2 cone/chord, static P_req = W/(n*mu), torque map"
               " tau = J(q)^T f on the certified chain, record-g 9.81 vs standard-g"
               " 9.80665 labeled per convention",
            A7="F-A band [0.3, 1.0] a declared screening band",
            A8="collision/penetration instruments are the DECLARED conservative mesh-derived"
               " proxies of CC2/CC3 (certified collision geometry ABSENT; DERIVED-PROXY,"
               " necessary-condition class)",
        ),
        frozen_quantities=dict(grid_n=gp.GRID_N, zooms=gp.ZOOMS,
                               polish_passes=gp.POLISH_PASSES,
                               polish_iters=gp.POLISH_ITERS,
                               sweep_angles=N_THETA, sweep_mirrors=2,
                               stl_files=19, solve_tolerance_m=SOLVE_TOL,
                               secondary_fit_tolerance_m=SECONDARY_FIT_TOL,
                               candidate_order=[c["cid"] for c in CANDIDATE_LADDER]),
        input_gate=gate,
        parsed=dict(trunk_diameter_m=C["D"], trunk_radius_m=C["R"],
                    trunk_height_m=C["H"], recorded_span_m=C["span"],
                    pincer_window_m=C["window"], mu_placeholder=C["mu"],
                    jn_Ns=C["jn"], dt_s=C["dt"], press_N=C["press"],
                    MP_cap_Nm=C["cap_mp"], assembly_mass_kg=C["m_assembly"],
                    weight_N_std=C["w_std"], weight_N_rec=w_rec,
                    w_rec_formula="assembly_mass_kg * 9.81 (record-g dual, labeled)",
                    allometry_scale=C["scale"], mu_crit_recorded=C["mcrit_recorded"],
                    benchmark_anchor_kg=C["anchor_kg"],
                    benchmark_anchor_std_g_N=C["anchor_std"],
                    per_contact_capacity_rec_g_N=C["cap36_rec"],
                    per_contact_capacity_std_g_N=C["cap36_std"],
                    hand_body_m_eff_kg=0.048761970806378674,
                    m_eff_source="climb-derivation/derivation_output.txt (pinned); B-G6:"
                                 " hand-body support UNDECIDABLE until TC-3/TC-8 - GP1"
                                 " computes required torques, never solver support"),
        load_support_constants=thr,
        prereg_quote_cross_checks=dict(quoted=pred_checks, matched=pred_match,
                                       tolerance=THRESHOLD_MATCH_TOL),
        cc1_candidates=candidates,
        gravity_reference=dict(direction_anchor_frame=[0.0, -1.0, 0.0],
                               label="DECLARED-REFERENCE CONDITIONAL-CALCULATION: gravity"
                                     " direction in the hand frame is undeclared in pinned"
                                     " bytes; this reference makes the separately-recorded"
                                     " gravity table determinate; not a measured or runtime"
                                     " posture",
                               magnitudes=dict(std_g=9.80665, rec_g=9.81)),
    )

    # ------- ladder: evaluate alive candidates in declared order -------
    evaluated_records = []
    chosen = None
    for cand in candidates:
        if cand["status"] not in ("SOLVED_NOMINAL", "PROCEED_AT_ACHIEVED"):
            continue
        rec = evaluate_candidate(cand, bodies, joints_by_name, anchor_name, tips, C, thr)
        evaluated_records.append(rec)
        if rec["candidate_status"] in ("ALIVE_N2", "ALIVE_N3"):
            chosen = rec
            break
        emit("  %s CLOSED (%s); the ladder follows (a candidate failure closes ONLY"
             " that candidate)." % (cand["cid"], rec["candidate_status"]))
    receipt["evaluated_candidates"] = evaluated_records
    receipt["selected_candidate_cid"] = chosen["cid"] if chosen else None

    predictions = build_verdicts(gate, candidates, evaluated_records, chosen, C, thr)
    receipt["predictions"] = predictions["predictions"]
    receipt["overall_verdict"] = predictions["overall"]
    receipt["fenced_not_run"] = dict(
        reach_placement_path="NOT_RUN (GP2/x_reach/C01 fenced; CC3's placement family is a"
                             " final-posture construct derived FROM the candidate contacts,"
                             " never a reach)",
        transfer_ascent_descent="NOT_RUN (B5 fences)",
        palm_contact="NOT_RUN (grasp.palm_anchor is role grasp_palm_reference; the palm"
                     " contact patch record is MISSING; non-analyzable; no palm contact"
                     " counted in any contact set)",
        n4="NOT_RUN (activates only on a Captain declaration)",
        measured_friction="NOT_RUN (NB-01/02 GAP; placeholders preserved with labels;"
                          " never tuned, never promoted)",
        recorded_config_rerun="NOT_RUN (K01 closed it: wrap margin -0.01733690019744087 m"
                              " mu-independent; pincer mu_crit 0.8399663223427114 > 0.6;"
                              " docket context only)",
        finger_finger_wrap="NOT_TESTED (CLOSED mu-independently at every lawful"
                           " configuration, GRASP_MECHANISMS section 7.1; finger-finger"
                           " contacts may enter only as additional same-side contacts)",
        solver_dynamics="NOT_RUN (static card; hand-body support B6-UNDECIDABLE)",
    )
    receipt["exit_semantics"] = dict(
        zero="run completed; verdicts recorded (candidate closures and NON-CLOSE"
             " load-support verdicts are declared honest outcomes; the refusal-wording law"
             " applies: a predicted refusal observed is a SUPPORTED prediction)",
        three="gate refusal or determinism/consistency-gate failure",
    )
    receipt["honest_absent"] = dict(
        certified_collision_geometry="ABSENT (A05 geoms are visual meshes; CC2/CC3 are"
                                     " DERIVED-PROXY instruments; a proxy PASS is"
                                     " necessary-condition clearance, a proxy FAIL is the"
                                     " declared candidate-closure instrument)",
        fingertip_pads="ABSENT (contact points are body origins; pad-level establishment"
                       " untestable; normals are declared radial constructions)",
        tendon_moment_arms="ABSENT (C18 explicitly_unresolved; the CC5 map is the"
                           " certified-kinematics static map tau = J^T f, NOT a tendon or"
                           " muscle model; no muscle capacity comparison claimed)",
        x_reach="ABSENT (C01 round-trip still-REQUIRED; fenced to GP2)",
        x_press="ABSENT (TC-8 ports 0/8; the 60 N press is the DECLARED fixture operating"
                " point; the MP-cap comparison records x_press DEBT, qualifies nothing)",
        measured_friction="ABSENT (NB-01/02; every mu is a declared placeholder or the"
                          " labeled 0.41 scenario parameter)",
        measured_rom="ABSENT (A09 C05 limits explicitly_unresolved; the joint box is the"
                     " DECLARED mutation-model ranges; every configuration is a"
                     " CONDITIONAL-CALCULATION, never a measured macaque posture)",
        dynamics="ABSENT by design (static map + contact arithmetic only)",
        muscle_force_capacity="ABSENT (A08-U1..U5 explicitly_unresolved)",
        mass_accounting="OI-1..OI-5 carried OPEN; none closed here",
    )
    emit("=" * 78)
    emit("OVERALL VERDICT: %s" % predictions["overall"])
    emit("  honest feasibility statement: any GP1 pass is FEASIBILITY evidence of the")
    emit("  FINAL posture under the declared assumption set A1-A8 - NEVER a physical")
    emit("  grasp claim (static closure at placeholder mu is necessary-condition class;")
    emit("  sufficiency needs x_reach, certified contact geometry, x_press and measured")
    emit("  mu, each NAMED ABSENT). Reaching is fenced (GP2).")
    if chosen is None and evaluated_records:
        emit("  per the Captain's candidate law the closures above close ONLY those")
        emit("  candidates; the docket options (friction bench at mu >= the recorded")
        emit("  thresholds; x_aperture geometry admission to the graph; resolved")
        emit("  parameters; Captain n=4 declaration) escalate to the Lieutenant with")
        emit("  the recorded margins. The aperture result is NOT invalidated (B-G1).")
    return receipt


# ===========================================================================
# per-candidate battery (CC2/CC3/CC4/CC5 + secondary n=3)
# ===========================================================================


def sweep_record(sweep, instrument):
    witness = sweep["witness"]

    def full_detail(pl):
        if pl is None:
            return None
        return dict(theta_index=pl["theta_index"], mirror=pl["mirror"],
                    u=list(pl["u"]), o=list(pl["o"]), w=list(pl["w"]), h=pl["h"],
                    segments=[dict(name=s["name"], rho=s["rho"], z=s["z"],
                                   margin=s["margin"], cls=s["cls"], fail=s["fail"],
                                   intersection_depth=s["intersection_depth"])
                              for s in pl["segments"]])

    sweep_map = []
    for pl in sweep["placements"]:
        sweep_map.append(dict(
            theta_index=pl["theta_index"], mirror=pl["mirror"],
            worst_margin=pl["worst_margin"], n_fail=pl["n_fail"],
            fails=[s["name"] for s in pl["segments"] if s["fail"]],
            seg=[[s["rho"], s["z"], s["margin"], 1 if s["fail"] else 0]
                 for s in pl["segments"]],
        ))
    return dict(
        instrument=instrument,
        placement_count=len(sweep["placements"]),
        placements_with_zero_fail=sum(1 for p in sweep["placements"] if p["n_fail"] == 0),
        witness_index=[witness["theta_index"], witness["mirror"]] if witness else None,
        witness=full_detail(witness),
        min_clearance_index=[sweep["min_clearance"]["theta_index"],
                             sweep["min_clearance"]["mirror"]] if sweep["min_clearance"] else None,
        min_clearance_worst_margin=sweep["min_clearance"]["worst_margin"] if sweep["min_clearance"] else None,
        max_penetration_index=[sweep["max_penetration"]["theta_index"],
                               sweep["max_penetration"]["mirror"]] if sweep["max_penetration"] else None,
        max_penetration_worst_margin=sweep["max_penetration"]["worst_margin"] if sweep["max_penetration"] else None,
        sweep_map=sweep_map,
        verdict="PENETRATION_FREE" if witness is not None
                else "PENETRATION_PROXY_FAIL_ALL_PLACEMENTS",
    )


CC3_INSTRUMENT = ("DERIVED-PROXY necessary-condition (deterministic 720x2 placement sweep;"
                  " contact segments exempt per declared law: FAIL only on gross"
                  " bounding-sphere-center intrusion; absent pad geometry makes finer"
                  " resolution untestable - named proxy limitation)")
CC2_INSTRUMENT = ("DERIVED-PROXY necessary-condition (conservative bounding spheres from"
                  " the 19 pinned STLs scaled 0.5384048132470733 + the certified anchor"
                  " AABB; certified collision geometry ABSENT)")


def evaluate_candidate(cand, bodies, joints_by_name, anchor_name, tips, C, thr):
    k = cand["digit"]
    dname = "digit%d" % k
    q_c = {jn: 0.0 for jn in joints_by_name}
    q_c.update(cand["solve"]["q"])
    thumb_body = tips["thumb"]["body"]
    dig_body = tips[dname]["body"]
    a = gp.fk_origin(bodies, anchor_name, q_c, thumb_body)
    b = gp.fk_origin(bodies, anchor_name, q_c, dig_body)
    chord = gp.norm(gp.sub(b, a))
    emit("=" * 78)
    emit("CANDIDATE %s (thumb-%s) at q_c: chord %r m" % (cand["cid"], dname, chord))

    record = dict(cid=cand["cid"], pair=cand["pair"],
                  q_c={jn: q_c[jn] for jn in sorted(q_c)},
                  tip_positions={"thumb": list(a), dname: list(b)},
                  achieved_chord=chord)

    # ---------------- CC2 self-collision proxy ----------------
    positions, rotations, joint_records = gp.fk_frames(bodies, anchor_name, q_c)
    segments = build_segments(bodies, C["stl_files"], C["bounds"], C["scale"],
                              positions, rotations,
                              contact_bodies={thumb_body, dig_body})
    rows, n_tested, n_overlap = self_collision_table(bodies, segments)
    overlaps = [r for r in rows if r["proxy_overlap"] and not r["adjacent"]]
    record["cc2"] = dict(
        instrument=CC2_INSTRUMENT,
        segment_count=len(segments),
        segment_order=[s["name"] for s in segments],
        segment_spheres=[dict(name=s["name"], radius=s["radius"],
                              center_local=s["center_local"],
                              center_world=list(s["center"]), source=s["source"])
                         for s in segments],
        pair_count=len(rows), nonadjacent_tested=n_tested,
        nonadjacent_overlaps=n_overlap,
        overlap_rows=overlaps,
        separations=rows,
        verdict="SELF_COLLISION_FREE" if n_overlap == 0 else "SELF_COLLISION_PROXY_OVERLAP",
    )
    emit("CC2 self-collision (DERIVED-PROXY): 190 pairs, %d non-adjacent tested,"
         " %d proxy overlaps -> %s" % (n_tested, n_overlap, record["cc2"]["verdict"]))
    if n_overlap > 0:
        record["candidate_status"] = "CLOSED_SELF_COLLISION"
        return record

    # ---------------- CC3 trunk penetration proxy ----------------
    sweep = gp.placement_sweep(a, b, segments, C["R"], C["H"] / 2.0, n_theta=N_THETA)
    record["cc3"] = sweep_record(sweep, CC3_INSTRUMENT)
    record["cc3"]["chord"] = chord
    record["cc3"]["m"] = list(sweep["m"])
    record["cc3"]["h"] = sweep["h"]
    record["cc3"]["cylinder"] = dict(radius=C["R"], height=C["H"],
                                     half_extent=C["H"] / 2.0)
    emit("CC3 trunk penetration (DERIVED-PROXY): %d placements, %d zero-FAIL -> %s"
         % (record["cc3"]["placement_count"], record["cc3"]["placements_with_zero_fail"],
            record["cc3"]["verdict"]))
    witness = sweep["witness"]
    if witness is None:
        record["candidate_status"] = "CLOSED_TRUNK_PENETRATION"
        return record

    o_w = tuple(witness["o"])
    u_w = tuple(witness["u"])
    contacts = contact_set_at([("thumb", a), (dname, b)], o_w, u_w)
    resid = gp.norm(gp.add(tuple(contacts[0]["normal"]), tuple(contacts[1]["normal"])))
    closed_form = math.sqrt(max(0.0, 4.0 - (chord / C["D"]) ** 2))
    in_window = bool(C["window"] <= chord <= C["D"])

    # ---------------- CC4 opposing contacts ----------------
    record["cc4"] = dict(
        labels="DERIVED-GEOMETRY; contact points are the certified tip origins (pads"
               " ABSENT); normals are the declared radial construction (unit radial"
               " directions of the placement family at the witness placement)",
        contacts=contacts,
        chord=chord,
        window=[C["window"], C["D"]],
        window_membership=in_window,
        two_contact_closure_placeholder_mu=in_window,
        antiparallel_residual=resid,
        antiparallel_residual_closed_form=closed_form,
        normals_antiparallel_at_exact_antipodal=bool(resid <= ANTIPARALLEL_TOL),
        construction_consistent=bool(abs(resid - closed_form) <= 1e-12),
        witness_placement=[witness["theta_index"], witness["mirror"]],
        n_contact_reading="the WRAP-2 chord window is the certified TWO-contact class;"
                          " any n>2 reading goes through the declared B-G4 load-support"
                          " law (cc5 load_support), never through an invented cone form",
    )
    emit("CC4 opposing contacts: chord %r in window: %s; two-contact closure at"
         " placeholder mu=0.6: %s; antiparallel residual %r (closed form %r)"
         % (chord, in_window, in_window, resid, closed_form))
    if not record["cc4"]["construction_consistent"]:
        record["candidate_status"] = "CLOSED_CONSTRUCTION_INCONSISTENT"
        return record

    # ---------------- secondary n=3 surface-fit solves ----------------
    fits = []
    for d in (2, 3, 4, 5):
        if d == k:
            continue
        djoints = sorted(["mcp%d_flexion" % d, "mcp%d_abduction" % d,
                          "pm%d_flexion" % d])
        tip_body = tips["digit%d" % d]["body"]

        def fit_fn(vals, tb=tip_body, jl=djoints):
            qm = dict(q_c)
            for jn, v in zip(jl, vals):
                qm[jn] = v
            p = gp.fk_origin(bodies, anchor_name, qm, tb)
            dvec = gp.sub(p, o_w)
            z = gp.dot(dvec, u_w)
            rho = gp.norm(gp.sub(dvec, gp.scale(u_w, z)))
            return abs(rho - C["R"])

        franges = [joints_by_name[jn]["range"] for jn in djoints]
        sol = gp.solve_target(djoints, franges, fit_fn, C["R"], window_hi=None)
        q3_try = dict(q_c)
        q3_try.update(sol["q"])
        p3 = gp.fk_origin(bodies, anchor_name, q3_try, tip_body)
        dvec = gp.sub(p3, o_w)
        z3 = gp.dot(dvec, u_w)
        rho3 = gp.norm(gp.sub(dvec, gp.scale(u_w, z3)))
        fits.append(dict(digit="digit%d" % d, joints=djoints,
                         fit_m=sol["chord"], q=sol["q"], evals=sol["evals"],
                         tip_position=list(p3), radial_dist=rho3, axial_coord=z3,
                         axial_within_extent=bool(abs(z3) <= C["H"] / 2.0),
                         achieved=bool(sol["chord"] <= SECONDARY_FIT_TOL
                                       and abs(z3) <= C["H"] / 2.0)))
        emit("  secondary fit %s: fit %r m (tol %r), radial %r, axial %r -> %s"
             % (fits[-1]["digit"], sol["chord"], SECONDARY_FIT_TOL, rho3, z3,
                "ACHIEVED" if fits[-1]["achieved"] else "not achieved"))
    achieved = sorted([f for f in fits if f["achieved"]],
                      key=lambda f: (f["fit_m"], f["digit"]))
    record["secondary"] = dict(
        declared_tolerance_m=SECONDARY_FIT_TOL,
        witness_axis=dict(o=list(o_w), u=list(u_w)),
        fits=fits,
        achieved=[f["digit"] for f in achieved],
        n3_set=None, n3=None, n3_enlarged_set_valid=False,
    )
    frames_n3 = None
    if achieved:
        best = achieved[0]
        record["secondary"]["n3_set"] = best["digit"]
        emit("  n=3 set candidate: primary pair + %s (fit %r m); CC2-CC4 re-run for"
             " the enlarged set" % (best["digit"], best["fit_m"]))
        frames_n3, n3_valid = run_n3(record, bodies, joints_by_name, anchor_name,
                                     tips, C, best, q_c, o_w, u_w, a, b,
                                     thumb_body, dig_body)
        record["secondary"]["n3_enlarged_set_valid"] = n3_valid

    # ---------------- CC5 statics (n=2; n=3 if the enlarged set is valid) ----
    loaded_joints = set(joint_name for (joint_name, body, o, u) in joint_records
                        if body == anchor_name)
    for tb in (thumb_body, dig_body):
        for name in gp.chain_to(bodies, anchor_name, tb):
            for (joint_name, body, o, u) in joint_records:
                if body == name:
                    loaded_joints.add(joint_name)

    record["cc5"] = dict()
    frames_n2 = (positions, rotations, joint_records)
    sets_def = [("n2_primary", 2, contacts, frames_n2, False)]
    if record["secondary"]["n3_set"] is not None:
        n3_contacts = contact_set_at(
            [("thumb", a), (dname, b),
             (record["secondary"]["n3_set"], tuple(record["secondary"]["n3"]["third_tip_position"]))],
            o_w, u_w)
        sets_def.append(("n3_secondary", 3, n3_contacts, frames_n3,
                         record["secondary"]["n3_enlarged_set_valid"]))
    for set_name, n, cset, frames, valid in sets_def:
        press_table = joint_torque_table(frames[2], loaded_joints, cset, C["press"])
        neg_contacts = [dict(name=c["name"], point=c["point"],
                             normal=[-x for x in c["normal"]]) for c in cset]
        neg_table = joint_torque_table(frames[2], loaded_joints, neg_contacts, C["press"])
        lin_breach = 0.0
        nonfinite = False
        for jn in press_table:
            t1 = press_table[jn]["tau"]
            t2 = neg_table[jn]["tau"]
            if not math.isfinite(t1):
                nonfinite = True
            lin_breach = max(lin_breach, abs(t1 + t2))
        grav = {}
        for glabel, gmag in (("std_g_9p80665", 9.80665), ("rec_g_9p81", 9.81)):
            va, vb, mass_sum_b = gravity_torque_table(
                bodies, frames[0], frames[1], frames[2], loaded_joints,
                (0.0, -1.0, 0.0), gmag, anchor_name)
            grav[glabel] = dict(view_A_anchor_effective=va, view_B_digit_priors=vb)
        cap_rows = []
        for jn in sorted(press_table):
            if not press_table[jn]["loaded_chain"]:
                continue
            t = abs(press_table[jn]["tau"])
            cap_rows.append(dict(joint=jn, body=press_table[jn]["body"],
                                 tau_Nm=press_table[jn]["tau"], abs_tau_Nm=t,
                                 MP_cap_Nm=C["cap_mp"],
                                 exceeds_cap=bool(t > C["cap_mp"]),
                                 moment_arms=press_table[jn]["arms"]))
        debt = [r for r in cap_rows if r["exceeds_cap"]]
        record["cc5"][set_name] = dict(
            n=n,
            contact_set_collision_checked=bool(valid) if n == 3 else True,
            contacts=cset,
            press_N=C["press"],
            torque_map=dict(
                instrument="certified-kinematics static map tau = J(q)^T f (tendon moment"
                           " arms C18 ABSENT; not a tendon/muscle model); force on the hand"
                           " = +F*n_i (trunk reaction to the declared press); joint origin ="
                           " certified child-body frame origin; axis = certified local axis"
                           " in world at q (axis-frame convention parsed and cross-checked"
                           " against the A05 XML)",
                joints=press_table,
                loaded_chain_joints=sorted(loaded_joints),
                finite_all=bool(not nonfinite),
                antisymmetry_max_breach_Nm=lin_breach,
                antisymmetry_ok=bool(lin_breach <= LINEARITY_TOL),
            ),
            gravity_torques_separate=grav,
            digit_prior_mass_sum_kg=mass_sum_b,
            digit_prior_sum_note="view B total is an alternative allocation of the same"
                                 " 0.049 kg effective hand mass; never summed with view A",
            MP_cap_comparison=dict(
                cap_Nm=C["cap_mp"],
                rows=cap_rows,
                debt_rows=[r["joint"] for r in debt],
                reading="a torque exceeding the declared MP cap is RECORDED as an x_press"
                        " DEBT finding at that joint (the declared 60 N press is beyond the"
                        " declared cap there); never a silent pass, never a card failure"
                        " (B-G7: no pass/fail of this card hinges on the cap comparison)",
            ),
            load_support=load_support_block(n, thr, C,
                                            formula_only=(n == 3 and not valid)),
        )
        emit("CC5 %s: torque table recorded (%d joints, %d loaded-chain); antisymmetry"
             " breach %r N*m; x_press debt rows: %s"
             % (set_name, len(press_table), len(loaded_joints), lin_breach,
                [r["joint"] for r in debt] if debt else "none"))
        ls = record["cc5"][set_name]["load_support"]
        emit("  load support n=%d at placeholder mu: %s (P_req std-g %r N vs %r N"
             " ceiling); at 0.41: %s (labeled diagnostic)"
             % (n, ls["verdict_placeholder_mu_std_g"], ls["p_req_std_g_N"],
                C["press"], ls["scenario_mu_041"]["verdict"]))
    record["candidate_status"] = "ALIVE_N3" if record["secondary"]["n3_set"] else "ALIVE_N2"
    return record


def run_n3(record, bodies, joints_by_name, anchor_name, tips, C, best,
            q_c, o_w, u_w, a, b, thumb_body, dig_body):
    """CC2-CC3 re-runs for the enlarged set; returns (frames, valid)."""
    d = int(best["digit"][-1])
    q3 = dict(q_c)
    q3.update(best["q"])
    third_body = tips["digit%d" % d]["body"]
    p3 = gp.fk_origin(bodies, anchor_name, q3, third_body)
    positions, rotations, joint_records = gp.fk_frames(bodies, anchor_name, q3)
    segments = build_segments(bodies, C["stl_files"], C["bounds"], C["scale"],
                              positions, rotations,
                              contact_bodies={thumb_body, dig_body, third_body})
    rows, n_tested, n_overlap = self_collision_table(bodies, segments)
    overlaps = [r for r in rows if r["proxy_overlap"] and not r["adjacent"]]
    sweep = gp.placement_sweep(a, b, segments, C["R"], C["H"] / 2.0, n_theta=N_THETA)
    n3 = dict(
        digit=best["digit"], fit_m=best["fit_m"],
        q3={jn: q3[jn] for jn in sorted(q3)},
        third_tip_position=list(p3),
        cc2_rerun=dict(
            instrument=CC2_INSTRUMENT,
            pair_count=len(rows), nonadjacent_tested=n_tested,
            nonadjacent_overlaps=n_overlap, overlap_rows=overlaps,
            separations=rows,
            verdict="SELF_COLLISION_FREE" if n_overlap == 0
                    else "SELF_COLLISION_PROXY_OVERLAP"),
        cc3_rerun=sweep_record(sweep, CC3_INSTRUMENT),
    )
    record["secondary"]["n3"] = n3
    valid = (n_overlap == 0 and sweep["witness"] is not None)
    if not valid:
        n3["exclusion_note"] = ("the enlarged set fails the CC2/CC3 re-run; the n=3"
                                " load-support reading is recorded as the declared B-G4"
                                " arithmetic ONLY, never as an achieved collision-checked"
                                " contact set")
    emit("  n=3 re-runs: CC2 %s (%d overlaps); CC3 %s (%d zero-FAIL placements) -> %s"
         % (n3["cc2_rerun"]["verdict"], n_overlap, n3["cc3_rerun"]["verdict"],
            n3["cc3_rerun"]["placements_with_zero_fail"],
            "VALID" if valid else "NOT VALID (formula-only n=3 reading)"))
    return (positions, rotations, joint_records), valid


# ===========================================================================
# P1-P8 verdicts
# ===========================================================================


def build_verdicts(gate, candidates, evaluated_records, chosen, C, thr):
    preds = {}
    preds["P1"] = dict(
        name="input_pins_verified_values_matched",
        verdict="SUPPORTED" if gate.get("ok") else "REFUSED",
        detail="%d pins hash-verified; constants value-matched; GRASP_MECHANISMS prefix"
               " identity %s" %
               (len(gate["pins"]),
                "verified at prefix length %d" % gate["grasp_mechanisms"]["prefix_len"]
                if gate["grasp_mechanisms"]["prefix_identity_verified"] else "FAILED"),
    )
    alive_solve = [c for c in candidates
                   if c["status"] in ("SOLVED_NOMINAL", "PROCEED_AT_ACHIEVED")]
    preds["P2"] = dict(
        name="candidate_contact_config_exists",
        verdict="SUPPORTED" if alive_solve else "CLOSED_ALL_CANDIDATES",
        detail={c["cid"]: dict(status=c["status"],
                               achieved_chord=c["solve"]["achieved_chord"],
                               residual=c["solve"]["residual"]) for c in candidates},
    )
    closures = [dict(cid=r["cid"], status=r["candidate_status"])
                for r in evaluated_records if r["candidate_status"].startswith("CLOSED")]
    cc2_findings = [dict(cid=r["cid"], verdict=r["cc2"]["verdict"],
                         nonadjacent_overlaps=r["cc2"]["nonadjacent_overlaps"],
                         overlap_pairs=len(r["cc2"]["overlap_rows"]))
                    for r in evaluated_records if "cc2" in r]
    if chosen is not None:
        preds["P3"] = dict(
            name="candidate_self_collision_proxy",
            verdict="PASS_NECESSARY_CONDITION_PROXY"
                    if chosen["cc2"]["verdict"] == "SELF_COLLISION_FREE"
                    else "FINDING_CANDIDATE_INVALIDATED",
            instrument="DERIVED-PROXY (no corpus number predicted this; new measurement of"
                       " the certified geometry)",
            candidate=chosen["cid"],
            nonadjacent_overlaps=chosen["cc2"]["nonadjacent_overlaps"],
            candidate_closures_before_selection=closures,
        )
        preds["P4"] = dict(
            name="candidate_trunk_penetration_proxy",
            verdict="PASS_NECESSARY_CONDITION_PROXY"
                    if chosen["cc3"]["verdict"] == "PENETRATION_FREE"
                    else "FINDING_CANDIDATE_INVALIDATED",
            instrument="DERIVED-PROXY existential over the declared 720x2 placement family",
            candidate=chosen["cid"],
            zero_fail_placements=chosen["cc3"]["placements_with_zero_fail"],
            candidate_closures_before_selection=closures,
        )
        cc4 = chosen["cc4"]
        preds["P5"] = dict(
            name="opposing_contacts_identified_window_cleared",
            verdict="SUPPORTED" if (cc4["window_membership"]
                                    and cc4["construction_consistent"])
                    else "FALSIFIER_OBSERVED",
            chord=cc4["chord"], window=cc4["window"],
            two_contact_closure_placeholder_mu=cc4["two_contact_closure_placeholder_mu"],
            window_rederivation="delta 0.0 (gate)",
            antiparallel_residual=cc4["antiparallel_residual"],
        )
        n2 = chosen["cc5"]["n2_primary"]
        p6_ok = (n2["torque_map"]["finite_all"] and n2["torque_map"]["antisymmetry_ok"])
        preds["P6"] = dict(
            name="static_torque_map_recorded",
            verdict="RECORDED_SANITY_OK" if p6_ok else "FALSIFIER_OBSERVED",
            detail="full contact->joint torque tables at the declared 60 N press (plus the"
                   " separately-recorded gravity tables, both allocation views, both g"
                   " conventions) with the MP-cap comparison rows (x_press debt evidence)",
            finite=n2["torque_map"]["finite_all"],
            antisymmetry_max_breach_Nm=n2["torque_map"]["antisymmetry_max_breach_Nm"],
            debt_joints=n2["MP_cap_comparison"]["debt_rows"],
        )
        ls2 = n2["load_support"]
        n2_obs = ls2["verdict_placeholder_mu_std_g"]
        p7_ok = (n2_obs == "NON-CLOSE")
        p7_detail = dict(
            n2=dict(predicted="NON-CLOSE (P_req 82.03261090558335 std-g > 60 N; threshold"
                              " 0.8203261090558336 std-g / 0.8206063365000001 rec-g > 0.6)",
                    observed=n2_obs,
                    status="SUPPORTED_NON_CLOSE_OBSERVED" if p7_ok
                           else "FALSIFIER_OBSERVED"),
            scenario_041=dict(
                label="DECLARED SCENARIO PARAMETER (human-analogue; UNMEASURED)",
                predicted="NON-CLOSE at n=2 and n=3 (0.41 < thresholds)",
                observed_n2=ls2["scenario_mu_041"]["verdict"]),
        )
        if chosen["secondary"]["n3_set"] is not None:
            ls3 = chosen["cc5"]["n3_secondary"]["load_support"]
            n3_obs = ls3["verdict_placeholder_mu_std_g"]
            p7_detail["n3"] = dict(
                predicted="CLOSE (P_req 54.68840727038889 std-g <= 60 N; threshold"
                          " 0.5468840727038888 std-g / 0.5470708910000001 rec-g)",
                observed=n3_obs,
                enlarged_set_collision_checked=chosen["secondary"]["n3_enlarged_set_valid"],
                formula_only=ls3["formula_only"],
                status="SUPPORTED_CLOSE_OBSERVED" if n3_obs == "CLOSE"
                       else "FALSIFIER_OBSERVED_RECORDS_DISCREPANCY_ROUTED")
            if n3_obs != "CLOSE" or ls2["scenario_mu_041"]["verdict"] != "NON-CLOSE":
                p7_ok = False
        if ls2["scenario_mu_041"]["verdict"] != "NON-CLOSE":
            p7_ok = False
        preds["P7"] = dict(
            name="load_support_extended_law",
            verdict="SUPPORTED_AS_PREDICTED" if p7_ok
                    else "FALSIFIER_OBSERVED_RECORDS_DISCREPANCY_ROUTED",
            detail=p7_detail,
            reading="a predicted refusal observed is a SUPPORTED prediction"
                    " (refusal-wording law); a NON-CLOSE closes THIS candidate's"
                    " load-support leg at n=2, never the aperture result and never the"
                    " objective")
    else:
        preds["P3"] = dict(
            name="candidate_self_collision_proxy",
            verdict="FINDINGS_RECORDED_ALL_CANDIDATES_CLOSED" if cc2_findings
                    else "NOT_RUN_NO_ALIVE_CANDIDATE",
            instrument="DERIVED-PROXY (no corpus number predicted this; new measurement of"
                       " the certified geometry); a proxy FAIL is the declared"
                       " candidate-closure instrument and closes ONLY that candidate",
            per_candidate_cc2=cc2_findings,
            candidate_closures=closures,
            reading="the aperture admittance result is NOT invalidated by any GP1 failure"
                    " (B-G1); docket options escalate to the Lieutenant with the recorded"
                    " margins")
        preds["P4"] = dict(
            name="candidate_trunk_penetration_proxy",
            verdict="NOT_RUN_ALL_CANDIDATES_CLOSED_AT_CC2" if cc2_findings
                    else "NOT_RUN_NO_ALIVE_CANDIDATE",
            candidate_closures=closures)
        preds["P5"] = dict(name="opposing_contacts_identified_window_cleared",
                           verdict="NOT_RUN_NO_ALIVE_CANDIDATE")
        preds["P6"] = dict(name="static_torque_map_recorded",
                           verdict="NOT_RUN_NO_ALIVE_CANDIDATE")
        preds["P7"] = dict(name="load_support_extended_law",
                           verdict="NOT_RUN_NO_ALIVE_CANDIDATE")
    if chosen is not None:
        overall = "CONFIRMING_MIXED_AS_PREDICTED"
        if preds["P7"]["verdict"] != "SUPPORTED_AS_PREDICTED" \
                or preds["P5"]["verdict"] == "FALSIFIER_OBSERVED" \
                or preds["P6"]["verdict"] == "FALSIFIER_OBSERVED":
            overall = "RECORDS_DISCREPANCY_ROUTED_FOR_REVIEW"
        if preds["P3"]["verdict"] == "FINDING_CANDIDATE_INVALIDATED" \
                or preds["P4"]["verdict"] == "FINDING_CANDIDATE_INVALIDATED":
            overall = "CANDIDATE_INVALIDATED_FINDINGS_RECORDED"
    elif evaluated_records:
        overall = "CANDIDATES_CLOSED_MEASURED_FINDINGS_RECORDED_LADDER_EXHAUSTED"
    else:
        overall = "ALL_CANDIDATES_CLOSED_AT_SOLVE_LEVEL_DOCKET_ESCALATION_RECORDED"
    preds["P8"] = dict(
        name="reach_transfer_palm_n4_fenced_not_run",
        verdict="FENCES_HELD",
        detail="no reach/path/placement claim, no transfer, no palm contact, no n=4, no"
               " measured friction enters any receipt; any conclusion text reading a GP1"
               " verdict as reach or physical-grasp evidence fails prereg compliance",
    )
    return dict(predictions=preds, overall=overall)


# ===========================================================================
# main: gate-refusal preservation, CC6 determinism, outputs
# ===========================================================================


def write_outputs(outdir, names_values):
    for name, value in names_values:
        with open(os.path.join(outdir, name), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(value)


def main():
    outdir = os.environ.get("CHIMERA_OUTPUT_DIR", "outputs")
    os.makedirs(outdir, exist_ok=True)
    try:
        receipt1 = pipeline()
        text1 = "\n".join(_report) + "\n"
        receipt2 = pipeline()
        text2 = "\n".join(_report) + "\n"
    except GateRefusal as exc:
        emit("")
        emit("REFUSAL RECORDED: %s" % exc.detail)
        emit("nothing is normalized; the run stops (exit 3)")
        write_outputs(outdir, [("gp1_gate_receipt.json",
                                json.dumps(dict(schema="chimera.gp1.gate.v1", ok=False,
                                                refusal=exc.detail), indent=1) + "\n")])
        raise SystemExit(3)

    s1 = json.dumps(receipt1, indent=1) + "\n"
    s2 = json.dumps(receipt2, indent=1) + "\n"
    identical = (s1 == s2) and (text1 == text2)
    det = dict(
        schema="chimera.gp1.determinism.v1",
        rerun_identical=identical,
        receipt_sha256_run1=hashlib.sha256(s1.encode("utf-8")).hexdigest(),
        receipt_sha256_run2=hashlib.sha256(s2.encode("utf-8")).hexdigest(),
        report_sha256_run1=hashlib.sha256(text1.encode("utf-8")).hexdigest(),
        report_sha256_run2=hashlib.sha256(text2.encode("utf-8")).hexdigest(),
        note="CC6: every construction closed-form or deterministic-enumerative;"
             " repeat run bit-identical (the x-aperture precedent)",
    )
    absence = {}
    for q in gp.RETRACTED_QUOTES:
        absence[q] = bool(q in s1 or q in text1)
    det["retracted_quotes_absent"] = {q: (not present) for q, present in absence.items()}
    det["retracted_quotes_gate"] = ("ABSENT_OK" if not any(absence.values())
                                    else "RETRACTED_QUOTE_PRESENT_CONSISTENCY_GATE_FAILED")
    write_outputs(outdir, [
        ("gp1_experiment_receipt.json", s1),
        ("gp1_experiment_receipt_rerun2.json", s2),
        ("gp1_report.txt", text1),
        ("gp1_report_rerun2.txt", text2),
        ("determinism_receipt.json", json.dumps(det, indent=1) + "\n"),
        ("gp1_gate_receipt.json", json.dumps(dict(
            schema="chimera.gp1.gate.v1",
            ok=bool(receipt1["input_gate"]["ok"]),
            pins=len(receipt1["input_gate"]["pins"]),
            prefix_identity=receipt1["input_gate"]["grasp_mechanisms"],
            retracted_quotes_gate=det["retracted_quotes_gate"]), indent=1) + "\n"),
    ])
    emit("=" * 78)
    emit("CC6 DETERMINISM: rerun bit-identical = %s" % identical)
    emit("  retracted-quote consistency gate: %s" % det["retracted_quotes_gate"])
    if not identical or any(absence.values()):
        raise SystemExit(3)
    raise SystemExit(0)


if __name__ == "__main__":
    main()
