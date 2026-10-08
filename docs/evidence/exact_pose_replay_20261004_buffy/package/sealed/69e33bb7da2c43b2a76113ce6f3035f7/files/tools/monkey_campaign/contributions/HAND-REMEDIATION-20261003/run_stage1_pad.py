# run_stage1_pad.py - HAND-REMEDIATION-20261003 R1 STAGE 1 (released by the
# Lieutenant AFTER the digit-scan result was on record: 0/98 postures, both
# causes posture-independent at the current geometry).
#
# Executes the pinned prereg 4def67e4 (bytes 9213bf7d...) + AMENDMENT-1
# 0c06e093 (bytes 018f0bc1...) exactly: the SEALED instrument (9514c5b1...)
# and SEALED v2.0 screen (6b924e87...) are imported UNMODIFIED; the S0 loop
# below is a verbatim mirror of the sealed screen_posture structure using the
# sealed functions, PROVEN byte-identical to the published v2.0 receipt rows
# by the in-run SEALED-ROW IDENTITY GATE (refusal SEALED_ROW_DRIFT on any
# mismatch). The pad layer is a POST-HOC classification layer: no bone is
# moved, no tolerance enlarged, every bone-level class byte-identical; a
# falsified frozen prediction is a RESULT, never an error.
import hashlib
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import instrument_v2 as iv   # noqa: E402  sealed, unmodified
import grasp_screen as gs    # noqa: E402  sealed, unmodified
import vpl1_pad as vp        # noqa: E402  the VPL-1 layer (this package)

ANCHOR = gs.ANCHOR
OUT_NAME_RECEIPT = "stage1_pad_receipt.json"
OUT_NAME_REPORT = "stage1_pad_report.txt"


def build_postures(joints_by_name):
    zero = {jn: 0.0 for jn in joints_by_name}
    q_c = dict(zero)
    q_c.update(iv.Q_C_PRIMARY)
    return [
        ("q_c_PRIMARY", q_c, ("distal_thumb", "distph3")),
        ("q_zero_CONTROL", dict(zero), ("distal_thumb", "distph3")),
    ]


def sha_of(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def canonical(x):
    return json.dumps(x, indent=1, sort_keys=True)


def emit(line=""):
    gs._report.append(line)
    print(line, flush=True)


# ---------------------------------------------------------------------------
# the S0 mirror loop (sealed structure, sealed functions; per-axis state
# carried forward for the pad layer; byte-identity gated against the receipt)
# ---------------------------------------------------------------------------
def s0_mirror(model, prep):
    counters = dict(
        axes_total=gs.N_THETA * gs.N_MIRROR,
        s0_reject_no_approach=0, s3_reject_bracket=0,
        s0_reject_clearance=0, s0_reject_tip_deep=0,
        s0_survivors=0, s0_only_cap=0, s0_only_timing_cap=0,
        s1_reject_noncontact_penetrate=0, s1_reject_noncontact_touch=0,
        s2_reject_no_contact=0, s2_reject_deep=0, survivors=0,
        s1_cells_run=0)
    clearance_by_bone = {}
    rejects = []
    axes = []
    determinism_slice = []
    for k in range(gs.N_THETA):
        for mirror in range(gs.N_MIRROR):
            u, w, theta = gs.axis_basis(prep, k, mirror)
            s_star, n_roots, win_body = gs.solve_s_star(prep, u, w)
            if len(determinism_slice) < gs.DET_SLICE_AXES:
                determinism_slice.append([k, mirror, list(u), s_star])
            if s_star is None:
                counters["s0_reject_no_approach"] += 1
                rejects.append([k, mirror, "S0_REJECT_NO_APPROACH"])
                axes.append(dict(k=k, mirror=mirror, s_star=None,
                                 proven=None))
                continue
            if s_star < gs.S_BRACKET_LO or s_star > gs.S_BRACKET_HI:
                counters["s3_reject_bracket"] += 1
                rejects.append([k, mirror, "S3_REJECT_BRACKET",
                                repr(s_star)])
                axes.append(dict(k=k, mirror=mirror, s_star=s_star,
                                 proven=None))
                continue
            o = iv.add(prep.m, iv.scale(w, s_star))
            proven_bad = None
            unknown_bones = []
            bone_state = {}
            for name in prep.bones:
                (sc, sr) = prep.sphere_w[name]
                f_center = iv.cyl_sdf(iv.cyl_to_local(sc, o, u),
                                      iv.TRUNK_R, iv.TRUNK_H / 2.0)
                if f_center > sr:
                    bone_state[name] = dict(cls="SOUND_CLEAR", d=None,
                                            depth=None)
                    continue
                sc_res = gs.scan_bone_vertices(prep, name, o, u)
                if sc_res["kind"] == "PENETRATED":
                    proven_bad = (name, "S0_REJECT_CLEARANCE",
                                  sc_res["depth"])
                    clearance_by_bone[name] = \
                        clearance_by_bone.get(name, 0) + 1
                    break
                if sc_res["kind"] == "TIP_DEEP":
                    proven_bad = (name, "S0_REJECT_TIP_DEEP",
                                  sc_res["depth"])
                    clearance_by_bone[name] = \
                        clearance_by_bone.get(name, 0) + 1
                    break
                unknown_bones.append(name)
            if proven_bad is not None:
                if proven_bad[1] == "S0_REJECT_CLEARANCE":
                    counters["s0_reject_clearance"] += 1
                else:
                    counters["s0_reject_tip_deep"] += 1
                rejects.append([k, mirror, proven_bad[1], proven_bad[0],
                                repr(proven_bad[2])])
            else:
                counters["s0_survivors"] += 1
            axes.append(dict(k=k, mirror=mirror, s_star=s_star, o=list(o),
                             u=list(u), bone_state=bone_state,
                             unknown_bones=unknown_bones,
                             proven=proven_bad, win_body=win_body))
    counted = (counters["s0_reject_no_approach"]
               + counters["s3_reject_bracket"]
               + counters["s0_reject_clearance"]
               + counters["s0_reject_tip_deep"]
               + counters["s0_survivors"])
    coverage_ok = counted == counters["axes_total"] and \
        len(rejects) + counters["s0_survivors"] == counters["axes_total"]
    return dict(counters=counters,
                clearance_by_bone=dict(sorted(clearance_by_bone.items())),
                rejects=rejects, axes=axes, coverage_ok=coverage_ok,
                determinism_slice=determinism_slice)


def identity_gate(mirror_res, sealed_posture, pname):
    """SEALED-ROW IDENTITY GATE: the mirror S0 rows/counters must equal the
    published v2.0 receipt exactly (class strings, bone names, depth repr
    strings, counter dict, by-bone map, determinism slice)."""
    diffs = []
    if mirror_res["counters"] != sealed_posture["counters"]:
        diffs.append("counters")
    if mirror_res["clearance_by_bone"] != \
            sealed_posture.get("clearance_by_bone", {}):
        diffs.append("clearance_by_bone")
    if mirror_res["rejects"] != sealed_posture["rejects"]:
        diffs.append("rejects")
    if canonical(mirror_res["determinism_slice"]) != \
            canonical(sealed_posture["determinism_slice"]):
        diffs.append("determinism_slice")
    return dict(posture=pname, ok=not diffs, diffs=diffs)


def axis_by_key(axes, k, mirror):
    for a in axes:
        if a["k"] == k and a["mirror"] == mirror:
            return a
    return None


# ---------------------------------------------------------------------------
# the pad layer over the rejection rows + the S1 stage for pad-satisfied rows
# ---------------------------------------------------------------------------
def pad_layer_and_s1(model, prep, pad_data, mirror_res, s1_clock):
    counters = dict(pad_rows_evaluated=0, pad_not_eligible=0,
                    pad_absorbed=0, pad_contact=0,
                    pad_refused_depth=0, pad_refused_patch=0,
                    pad_no_contact=0,
                    pad_window_exceeded_after_full_scan=0,
                    post_pad_s1_cells_run=0,
                    post_pad_s1_reject_noncontact_penetrate=0,
                    post_pad_s1_reject_noncontact_touch=0,
                    post_pad_s2_reject_no_contact=0,
                    post_pad_s2_reject_deep=0,
                    post_pad_survivors=0,
                    post_pad_s0_only_cap=0,
                    post_pad_s0_only_timing_cap=0)
    pad_rows = []
    post_pad_rows = []
    survivors = []
    s1_done = 0
    pad_det_slice = []
    satisfied_by_axis = {}
    for row in mirror_res["rejects"]:
        k, mirror = row[0], row[1]
        if len(row) < 4:
            pad_rows.append([k, mirror, row[2], "-", "PAD_NOT_APPLICABLE",
                             None, None, None, None, None, None])
            continue
        cls, bone = row[2], row[3]
        ax = axis_by_key(mirror_res["axes"], k, mirror)
        if ax is None or ax.get("proven") is None or \
                bone not in vp.COVERED_BODIES or ax.get("o") is None:
            counters["pad_not_eligible"] += 1
            pad_rows.append([k, mirror, cls, bone, "PAD_NOT_ELIGIBLE",
                             None, None, None, None, None, None])
            continue
        counters["pad_rows_evaluated"] += 1
        scan = vp.pad_scan(prep, pad_data, bone, tuple(ax["o"]),
                           tuple(ax["u"]))
        pcl, u_val = vp.classify_pad(scan)
        measured_anchored = None
        if pcl in vp.PAD_SATISFIED:
            satisfied_by_axis[(k, mirror)] = bone
            measured_anchored = bool(u_val is not None
                                     and 0.0 < u_val <= 0.8e-3)
            d_cov = scan["d_covered_max"]
            if pcl == "PAD_ABSORBED":
                counters["pad_absorbed"] += 1
            else:
                counters["pad_contact"] += 1
            if d_cov is not None and d_cov > vp.WINDOW_HI:
                counters["pad_window_exceeded_after_full_scan"] += 1
        elif pcl == "PAD_REFUSED_DEPTH":
            counters["pad_refused_depth"] += 1
        elif pcl == "PAD_REFUSED_PATCH":
            counters["pad_refused_patch"] += 1
        else:
            counters["pad_no_contact"] += 1
        force_n = None
        if pcl == "PAD_CONTACT" and u_val is not None:
            force_n = vp.pad_force_column(
                u_val, pad_data[bone]["mask_area_m2"])
        pad_rows.append([k, mirror, cls, bone, pcl,
                         None if scan["d_covered_max"] is None
                         else repr(scan["d_covered_max"]),
                         repr(u_val) if u_val is not None else None,
                         scan["witness"],
                         None if scan["witness_na"] is None
                         else repr(scan["witness_na"]),
                         measured_anchored,
                         repr(force_n) if force_n is not None else None])
        if len(pad_det_slice) < gs.DET_SLICE_AXES:
            pad_det_slice.append([k, mirror, bone,
                                  repr(scan["d_covered_max"])])
    # ---- S1 for pad-satisfied rows (caps inherited, never enlarged) ----
    for row in mirror_res["rejects"]:
        k, mirror = row[0], row[1]
        key = (k, mirror)
        if key not in satisfied_by_axis:
            continue
        if s1_done >= gs.CAP_S1_PER_POSTURE:
            counters["post_pad_s0_only_cap"] += 1
            post_pad_rows.append([k, mirror, "POST_PAD_S0_ONLY_CAP"])
            continue
        if s1_clock[0] >= gs.S1_TIME_BUDGET_S:
            counters["post_pad_s0_only_timing_cap"] += 1
            post_pad_rows.append([k, mirror, "POST_PAD_S0_ONLY_TIMING_CAP"])
            continue
        ax = axis_by_key(mirror_res["axes"], k, mirror)
        o = tuple(ax["o"])
        u = tuple(ax["u"])
        pad_bone = satisfied_by_axis[key]
        t0 = time.time()
        exact_state = {}
        for name in prep.bones:
            st = ax["bone_state"].get(name)
            if st is not None and st["cls"] == "SOUND_CLEAR":
                exact_state[name] = dict(cls="CLEAR", d=None, depth=None,
                                         how="level1_sound_clear")
        check_set = set(ax["unknown_bones"]) | set(prep.tips)
        check_set.discard(pad_bone)   # the pad-substituted body
        for name in sorted(check_set):
            r = iv.adjudicate_body_vs_cylinder(prep.frames[name], o, u,
                                               iv.TAU)
            exact_state[name] = dict(cls=r["class"], d=r["d"],
                                     depth=r["depth"], how="level2_exact")
        sub_state = {n: v for n, v in exact_state.items() if n != pad_bone}
        verdict, reason = gs.classify_placement_bones(sub_state,
                                                      prep.contact_pair)
        s1_clock[0] += time.time() - t0
        s1_done += 1
        counters["post_pad_s1_cells_run"] += 1
        if verdict == "REJECT":
            if reason.startswith("S1_REJECT_NONCONTACT_PENETRATE"):
                counters["post_pad_s1_reject_noncontact_penetrate"] += 1
            elif reason.startswith("S1_REJECT_NONCONTACT_TOUCH"):
                counters["post_pad_s1_reject_noncontact_touch"] += 1
            elif reason.startswith("S2_REJECT_NO_CONTACT"):
                counters["post_pad_s2_reject_no_contact"] += 1
            elif reason.startswith("S2_REJECT_DEEP"):
                counters["post_pad_s2_reject_deep"] += 1
            post_pad_rows.append([k, mirror, reason,
                                  "pad_body=" + pad_bone])
            continue
        ares = iv.adjudicate_body_vs_cylinder(prep.frames[ANCHOR], o, u,
                                              iv.TAU)
        pad_bone_rows = [p for p in pad_rows
                         if p[0] == k and p[1] == mirror
                         and p[3] == pad_bone]
        survivors.append(dict(
            theta_index=k, mirror=mirror, s_star=ax["s_star"],
            o=list(o), u=list(u),
            pad_body=pad_bone,
            pad_class=(pad_bone_rows[0][4] if pad_bone_rows else None),
            pad_u=(float(pad_bone_rows[0][6])
                   if pad_bone_rows and pad_bone_rows[0][6] else None),
            pad_force_N=(float(pad_bone_rows[0][10])
                         if pad_bone_rows and pad_bone_rows[0][10]
                         else None),
            anchor_envelope=dict(cls=ares["class"], d=ares["d"],
                                 depth=ares["depth"],
                                 flag=ares["level1"]["flag"]),
            bodies=sorted((n, exact_state[n]["cls"], exact_state[n]["d"],
                           exact_state[n]["depth"])
                          for n in exact_state),
        ))
        counters["post_pad_survivors"] += 1
    counted = sum(counters[v] for v in (
        "post_pad_s1_reject_noncontact_penetrate",
        "post_pad_s1_reject_noncontact_touch",
        "post_pad_s2_reject_no_contact", "post_pad_s2_reject_deep",
        "post_pad_survivors", "post_pad_s0_only_cap",
        "post_pad_s0_only_timing_cap"))
    arithmetic_ok = counted == s1_done + counters["post_pad_s0_only_cap"] \
        + counters["post_pad_s0_only_timing_cap"]
    return dict(counters=counters, pad_rows=pad_rows,
                post_pad_rows=post_pad_rows, survivors=survivors,
                pad_det_slice=pad_det_slice,
                pad_s1_arithmetic_ok=arithmetic_ok)


# ---------------------------------------------------------------------------
# P1-P4 (frozen; each names its contradicting observation; a falsified
# prediction is a RESULT recorded in the receipt)
# ---------------------------------------------------------------------------
def verify_predictions(pname, mirror_res, pad_res, battery, identity):
    pad_rows = pad_res["pad_rows"]
    p = {}
    # P1: window+patch TIP_DEEP rows reclassify; no conversion without a
    # witness; no PAD_CONTACT with u > u_max.
    bad = []
    counts = dict(rows=0, pad_contact=0, pad_absorbed=0,
                  refused_depth=0, refused_patch=0, not_eligible=0)
    for r in pad_rows:
        if len(r) < 5 or r[2] != "S0_REJECT_TIP_DEEP":
            continue
        counts["rows"] += 1
        pcl = r[4]
        if pcl == "PAD_CONTACT":
            counts["pad_contact"] += 1
            u_val = float(r[6]) if r[6] else None
            if r[7] is None:
                bad.append("conversion without witness %r" % (r[:3],))
            if u_val is None or u_val > vp.U_MAX:
                bad.append("u over u_max %r" % (r[:3],))
        elif pcl == "PAD_ABSORBED":
            counts["pad_absorbed"] += 1
            if r[7] is None:
                bad.append("absorbed without witness %r" % (r[:3],))
        elif pcl == "PAD_REFUSED_DEPTH":
            counts["refused_depth"] += 1
        elif pcl == "PAD_REFUSED_PATCH":
            counts["refused_patch"] += 1
        else:
            counts["not_eligible"] += 1
    p["P1"] = dict(posture=pname, ok=not bad, violations=bad[:10],
                   counts=counts, note="u recorded as max(d_pad-t,0); the "
                   "pinned u-range (0,u_max] holds for the PAD_CONTACT "
                   "class; PAD_ABSORBED rows carry u=0 inside the pad's "
                   "free thickness (recorded split, never merged)")
    # P2: zero rows of ANY body with d_pad > window classify pad-satisfied.
    bad2 = [r[:5] for r in pad_rows
            if len(r) >= 5 and r[4] in vp.PAD_SATISFIED
            and r[5] is not None and float(r[5]) > vp.WINDOW_HI]
    p["P2"] = dict(posture=pname, ok=not bad2, violations=bad2[:10],
                   refused_depth_total=pad_res["counters"][
                       "pad_refused_depth"])
    # P3 (q_c_PRIMARY): >= 442 of 486 distph2 rows remain refused
    # (contradiction routes to the Lieutenant before anything else runs).
    if pname == "q_c_PRIMARY":
        dp2 = [r for r in pad_rows if len(r) >= 5 and r[3] == "distph2"]
        sat = [r for r in dp2 if r[4] in vp.PAD_SATISFIED]
        p["P3"] = dict(posture=pname, distph2_rows=len(dp2),
                       pad_satisfied=len(sat),
                       refused=len(dp2) - len(sat),
                       required_refused_at_least=442,
                       ok=(len(dp2) - len(sat)) >= 442,
                       contradiction_action="route_to_lieutenant")
    # P4: battery identity + arithmetic coherence (the q_zero control keeps
    # its role via the identity gate).
    p["P4"] = dict(posture=pname,
                   battery_ok=bool(battery["ok"]),
                   identity_ok=bool(identity["ok"]),
                   pad_arithmetic_ok=bool(pad_res["pad_s1_arithmetic_ok"]))
    p["P4"]["ok"] = (p["P4"]["battery_ok"] and p["P4"]["identity_ok"]
                     and p["P4"]["pad_arithmetic_ok"])
    return p


# ---------------------------------------------------------------------------
def pipeline():
    # ---- pinned identities (refused on drift) ----
    pins = {
        "PREREGISTRATION_R1_PAD_LAYER.md": vp.PREREG_R1_SHA,
        "R1_AMENDMENT_1.md": vp.AMENDMENT_1_SHA,
        "instrument_v2.py": vp.INSTRUMENT_SHA,
        "grasp_screen.py": vp.SCREEN_SHA,
        "control_input_table.json": vp.CONTROL_SEALED_SHA,
        vp.CONTROL_VPL1_NAME: vp.CONTROL_VPL1_SHA,
        "grasp_screen_receipt_sealed_v20.json": vp.RECEIPT_V20_SHA,
        "mesh_input_table.json": vp.MESH_TABLE_SHA,
        "mutation_structure.json": vp.MUTSTRUCT_SHA,
    }
    for fname, expect in sorted(pins.items()):
        got = sha_of(os.path.join(HERE, fname))
        if got != expect:
            iv.refuse("input_pin_mismatch", "%s %s" % (fname, got))
    emit("=" * 78)
    emit("GATE. all %d in-package pins MATCH (prereg %s / amendment %s / "
         "instrument %s / screen %s)."
         % (len(pins), vp.PREREG_R1_SHA[:16], vp.AMENDMENT_1_SHA[:16],
            vp.INSTRUMENT_SHA[:16], vp.SCREEN_SHA[:16]))
    # ---- the inherited input gate (sealed instrument prereg bytes) ----
    gate, _mut, _stl_files, _bounds = iv.run_input_gate(
        os.path.join(HERE, "PREREGISTRATION.md"))
    emit("INHERITED INPUT GATE ok=%s pins=%d." % (gate["ok"],
                                                  len(gate["pins"])))
    model = gs.build_model()
    # ---- sealed C1-C3 light gate (sealed table) ----
    with open(os.path.join(HERE, "control_input_table.json"),
              encoding="utf-8") as fh:
        sealed_table = json.load(fh)
    lg = gs.light_gate(model, sealed_table)
    emit("SEALED LIGHT GATE C1-C3: ok=%s" % lg["ok"])
    if not lg["ok"]:
        iv.refuse("instrument_invalid_in_situ",
                  json.dumps(lg["failures"]))
    # ---- pad data at q_zero + the FK palmar check + battery C6-C10 ----
    postures = build_postures(model[1])
    zero_name, zero_q, zero_pair = postures[1]
    prep_zero = gs.prepare_posture(model, zero_q, zero_pair)
    pad_data_zero = vp.build_pad_data(model, prep_zero)
    base_preps = {name: (prep_zero, zero_q) for name in vp.COVERED_BODIES}
    fk_check = vp.palmar_axis_fk_identity(model, pad_data_zero, base_preps)
    emit("PALMAR AXIS FK IDENTITY (declared sign rule vs certified model):"
         " ok=%s %s" % (fk_check["ok"],
                        json.dumps(fk_check["rows"], sort_keys=True)))
    if not fk_check["ok"]:
        iv.refuse("palmar_axis_fk_failed",
                  json.dumps(fk_check["rows"]))
    with open(os.path.join(HERE, vp.CONTROL_VPL1_NAME),
              encoding="utf-8") as fh:
        vtable = json.load(fh)
    battery = vp.vpl1_battery(model, prep_zero, pad_data_zero, vtable, lg)
    emit("VPL1 BATTERY C6-C10: ok=%s %s"
         % (battery["ok"],
            json.dumps(battery["controls"], sort_keys=True)))
    if not battery["ok"]:
        if any("anti-masking" in f for f in battery["failures"]):
            iv.refuse("instrument_invalid_pad_masks_bone",
                      json.dumps(battery["failures"]))
        iv.refuse("instrument_invalid_in_situ",
                  json.dumps(battery["failures"]))
    # ---- witness + axis family identity (sealed constructions) ----
    wit = iv.check_witness_identity(model[0], model[1], model[2])
    emit("WITNESS. sealed q_c(PRIMARY) FK reproduces the GP1 receipt tips "
         "and chord %r." % wit["chord"])
    afc = gs.axis_family_identity_check(model)
    emit("AXIS FAMILY IDENTITY vs sealed iv.placement_family: cells=%d "
         "identical=%s" % (afc["cells"], afc["ok"]))
    if not afc["ok"]:
        iv.refuse("axis_family_identity_failed", "q_zero slice")
    # ---- the sealed receipt (comparison set of the identity gate) ----
    with open(os.path.join(HERE, "grasp_screen_receipt_sealed_v20.json"),
              encoding="utf-8") as fh:
        sealed = json.load(fh)
    receipt = dict(
        schema="chimera.hand_remediation.stage1_pad.v1",
        task="HAND-REMEDIATION-20261003 R1 STAGE 1 (the VPL-1 pad layer, "
             "post-hoc, bones rigid + fully checked; released after the "
             "digit-scan 0/98 record)",
        lane="E:/ChimeraWork/monkey-coordination/hand-remediation/",
        preregistration_r1_sha256=vp.PREREG_R1_SHA,
        amendment_1_sha256=vp.AMENDMENT_1_SHA,
        instrument_copy_sha256=vp.INSTRUMENT_SHA,
        screen_copy_sha256=vp.SCREEN_SHA,
        sealed_receipt_v20_sha256=vp.RECEIPT_V20_SHA,
        control_vpl1_sha256=vp.CONTROL_VPL1_SHA,
        instrument_preregistration_sha256=iv.PREREG_SHA256,
        instrument_declaration_sha256=iv.DECLARATION_SHA256,
        digit_scan_gate=dict(job1="3a1ff276b9d84cabab33f558539deb05",
                             receipt_sha256=vp.RECEIPT_V20_SHA,
                             verdict="ZERO_SURVIVORS_DIGIT_SIDE (0/98 "
                                     "postures combined; on record "
                                     "before this run)"),
        frozen_constants=dict(
            tau=iv.TAU, pi_c=iv.PI_C, r_joint=iv.R_JOINT, scale=iv.SCALE,
            trunk_r=iv.TRUNK_R, trunk_h=iv.TRUNK_H,
            n_theta=gs.N_THETA, n_mirror=gs.N_MIRROR,
            s_bracket=[gs.S_BRACKET_LO, gs.S_BRACKET_HI],
            cap_s1_per_posture=gs.CAP_S1_PER_POSTURE,
            s1_time_budget_s=gs.S1_TIME_BUDGET_S,
            vpl1=dict(covered_bodies=list(vp.COVERED_BODIES), t=vp.T,
                      u_max=vp.U_MAX, window=[vp.WINDOW_LO, vp.WINDOW_HI],
                      k_eff_n_per_m=vp.K_EFF, a_thumb_m2=vp.A_THUMB,
                      k_pa=vp.K, sign_table=vp.SIGN_TABLE,
                      force_label="DECLARED-MODEL-FORCE")),
        input_gate=gate, witness_identity=wit, axis_family_identity=afc,
        sealed_light_gate=lg, palmar_fk_check=fk_check, battery=battery,
        identity_gates={}, postures={}, predictions={},
    )
    s1_clock = [0.0]
    for (pname, q_map, pair) in postures:
        prep = gs.prepare_posture(model, q_map, pair)
        emit("-" * 78)
        emit("POSTURE %s pair=%s chord(T1)=%r" % (pname, pair, prep.chord))
        pad_data = vp.build_pad_data(model, prep)
        mirror_res = s0_mirror(model, prep)
        sealed_posture = sealed["postures"][pname]
        ident = identity_gate(mirror_res, sealed_posture, pname)
        chord_ok = canonical(prep.chord) == \
            canonical(sealed_posture["chord_t1"])
        ident["chord_ok"] = bool(chord_ok)
        ident["ok"] = bool(ident["ok"] and chord_ok)
        receipt["identity_gates"][pname] = ident
        emit("SEALED-ROW IDENTITY GATE %s: ok=%s diffs=%s chord_ok=%s"
             % (pname, ident["ok"], ident["diffs"], chord_ok))
        if not ident["ok"]:
            iv.refuse("sealed_row_drift",
                      "%s %s" % (pname, json.dumps(ident["diffs"])))
        pad_res = pad_layer_and_s1(model, prep, pad_data, mirror_res,
                                   s1_clock)
        preds = verify_predictions(pname, mirror_res, pad_res, battery,
                                   ident)
        receipt["predictions"].update(preds)
        res = dict(
            counters_sealed_mirror=mirror_res["counters"],
            clearance_by_bone=mirror_res["clearance_by_bone"],
            coverage_ok=mirror_res["coverage_ok"],
            determinism_slice=mirror_res["determinism_slice"],
            pad_counters=pad_res["counters"],
            pad_rows=pad_res["pad_rows"],
            post_pad_rows=pad_res["post_pad_rows"],
            survivors=pad_res["survivors"],
            pad_det_slice=pad_res["pad_det_slice"],
            pad_s1_arithmetic_ok=pad_res["pad_s1_arithmetic_ok"],
            chord_t1=prep.chord,
        )
        receipt["postures"][pname] = res
        emit("  sealed counters: %s"
             % json.dumps(mirror_res["counters"], sort_keys=True))
        emit("  pad counters: %s"
             % json.dumps(pad_res["counters"], sort_keys=True))
        emit("  predictions: %s"
             % json.dumps({k: v.get("ok") for k, v in preds.items()},
                          sort_keys=True))
        emit("  post-pad survivors=%d"
             % pad_res["counters"]["post_pad_survivors"])
        if not mirror_res["coverage_ok"]:
            iv.refuse("coverage_arithmetic_broken", pname)
        if not pad_res["pad_s1_arithmetic_ok"]:
            iv.refuse("post_pad_arithmetic_broken", pname)
    # ---- determinism: pad slice cells re-solved byte-identical ----
    det_ok = True
    det_cells = 0
    for (pname, q_map, pair) in postures:
        prep = gs.prepare_posture(model, q_map, pair)
        pad_data = vp.build_pad_data(model, prep)
        for (k, mirror, bone, d_repr) in \
                receipt["postures"][pname]["pad_det_slice"]:
            u2, w2, _ = gs.axis_basis(prep, k, mirror)
            s2, _nr, _wb = gs.solve_s_star(prep, u2, w2)
            o2 = iv.add(prep.m, iv.scale(w2, s2))
            scan2 = vp.pad_scan(prep, pad_data, bone, o2, u2)
            same = repr(scan2["d_covered_max"]) == d_repr
            det_ok = det_ok and same
            det_cells += 1
    receipt["determinism_slice_pad"] = dict(cells=det_cells, ok=det_ok)
    emit("PAD DETERMINISM SLICE: %d cells re-solved byte-identical = %s"
         % (det_cells, det_ok))
    # ---- verdicts ----
    survivors_total = sum(
        receipt["postures"][p]["pad_counters"]["post_pad_survivors"]
        for (p, _, _) in postures)
    p3 = receipt["predictions"].get("P3", {})
    p_ok = {k: bool(v.get("ok")) for k, v in
            receipt["predictions"].items()}
    if p3 and not p3.get("ok", True):
        receipt["verdict"] = "P3_FALSIFIED_ROUTE_TO_LIEUTENANT"
    elif survivors_total > 0:
        receipt["verdict"] = "PAD_ADMITTED_SURVIVORS_PRESENT_STAGE1"
    else:
        receipt["verdict"] = \
            "ZERO_SURVIVORS_PAD_STAGE1_CAUSE1_CLASSES_RECORDED"
    receipt["predictions_ok"] = p_ok
    receipt["survivors_total"] = survivors_total
    receipt["s1_cumulative_clock_s"] = s1_clock[0]
    emit("=" * 78)
    emit("PREDICTIONS: %s" % json.dumps(p_ok, sort_keys=True))
    emit("VERDICT: %s (post-pad survivors=%d)"
         % (receipt["verdict"], survivors_total))
    return receipt


def main():
    t_start = time.time()
    outdir = os.environ.get("CHIMERA_OUTPUT_DIR", "outputs")
    os.makedirs(outdir, exist_ok=True)
    try:
        receipt = pipeline()
        text = "\n".join(gs._report) + "\n"
        receipt["wall_clock_s"] = time.time() - t_start
    except iv.GateRefusal as exc:
        with open(os.path.join(outdir, "stage1_pad_gate_receipt.json"),
                  "w", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(dict(
                schema="chimera.hand_remediation.gate.v1",
                ok=False, refusal=exc.detail), indent=1) + "\n")
        print("REFUSAL: %s" % exc.detail, flush=True)
        raise SystemExit(3)
    with open(os.path.join(outdir, OUT_NAME_RECEIPT), "w",
              encoding="utf-8", newline="\n") as fh:
        fh.write(canonical(receipt) + "\n")
    with open(os.path.join(outdir, OUT_NAME_REPORT), "w",
              encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    raise SystemExit(0)


if __name__ == "__main__":
    main()
