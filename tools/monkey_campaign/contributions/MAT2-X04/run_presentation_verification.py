#!/usr/bin/env python3
"""MAT2-X04: the gated presentation-verification experiment (prereg 2-8).

Order is law: pins -> registry/profile (BEFORE capture; G7) -> prereg-commit
law -> W10 certified-line layer -> gate and load identity -> arms A1/A2
(W10's own sealed run_commanded) -> the climb schema audit (clean + scratch
derivation proof) -> window transition coverage -> the declared frame plan
(records-only render; three declared layers on diagnostic frames) -> the
frozen predictions P1-P12 -> the falsifier bites FB1-FB5 (clean controls
FIRST, named premature guards) -> the receipts + traces.

CPU only; no engine process; no training. Run:
python -B run_presentation_verification.py. Exit: 0 green / 2 named refusal
/ 1 failed prediction.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import presentation_harness as ph      # noqa: E402
import state_readout as sr             # noqa: E402
import verify_inputs_x04 as vi4        # noqa: E402

OUT = Path(os.environ.get("CHIMERA_OUTPUT_DIR", HERE / "outputs"))


def require(condition, code):
    if not condition:
        print("REFUSAL:" + str(code), file=sys.stderr)
        raise SystemExit(2)


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def write_out(name, value):
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / name
    path.write_bytes(canonical(value) + b"\n")
    return path


def write_out_bytes(name, data):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_bytes(data)
    return OUT / name


# ---------------------------------------------------------------- stages
def stage_pins():
    rows = vi4.verify()
    reg = vi4.verify_registry()
    prereg_commit = vi4.verify_prereg_commit()
    vi4.extract_x04_tree()
    w10 = vi4.w10_layer()
    limits = vi4.p06_limits()
    return rows, reg, prereg_commit, w10, limits


def gate_and_load():
    """The certified line's own gate (W10's sealed code, unmodified)."""
    wd, _vz = ph.load_w10_modules()
    loaded = wd.gate_and_load()
    cert, req, allow, bundle, build_id, params, scene_const, bounds, gate = \
        loaded
    require(allow["decision"] == "ALLOW", "deploy_gate_not_allow")
    require(build_id == ph.BUILD_ID,
            "build_id_mismatch:" + str(build_id))
    import command_model as cm         # W10 bytes (frozen script constants)
    adapter = cm.CommandAdapter(bundle["manifest"], scene_const)
    return adapter, build_id, params, gate


def stage_climb_audit():
    """P3's derivation: the schema audit over the PINNED scene bytes; the
    scratch-copy arm proves the derivation is live (an injected climb key
    flips the derived value)."""
    src = ph.scene_source_bytes()
    clean = sr.derive_climb_state(src)
    require(clean["climb_state"] == sr.CLIMB_ABSENT,
            "prediction_failed:P3_climb_not_absent:"
            + repr(clean["climb_state"]))
    # the scratch tamper: inject one climb key into the dict literal (a
    # scratch string surgery on extracted bytes — the pinned file itself is
    # never modified).
    marker = '            "pad_pair_ordering": {"hl": "heel_mp", "hr": "heel_mp"},'
    require(src.decode("utf-8").count(marker) == 1,
            "x04_scratch_marker_ambiguous")
    tampered = src.decode("utf-8").replace(
        marker, marker + '\n            "climb_state_probe": 0,')
    flipped = sr.derive_climb_state(tampered.encode("utf-8"))
    require(flipped["climb_state"] == "schema_climb_key_present",
            "prediction_failed:P3_scratch_not_flipping:"
            + repr(flipped["climb_state"]))
    return {"clean": clean, "scratch_flipped": flipped,
            "law": "a climb key would refuse the absent declaration; the "
                   "certified line's schema derives absent_declared"}


def stage_render(res1, reg, climb_audit):
    """The declared frame plan from A1's committed records; the P4
    identity/tamper arms; every frame's mapping audit rides derive_state."""
    import visualization as vz          # W10 bytes (its dir is sys.path[0])
    f04 = vz.load_f04_module()
    geom = vz.gait_geometry()
    chain_before = list(res1["state_chain"])
    plan = ph.build_frame_plan()
    colours, metas = ph.render_frames(res1["per_tick"], geom, vz, f04, plan,
                                      climb_audit)
    require(res1["state_chain"] == chain_before,
            "falsifier_did_not_bite:P4_render_mutated_state")
    # P4(a): the V3 mode pairs are byte-identical within each mode
    def frame_arr(frame_id):
        i = next(m["render_index"] for m in metas
                 if m["frame_id"] == frame_id)
        return np.asarray(colours[i], dtype=np.uint8)

    s1 = frame_arr("S_pass1_t%d" % ph.V3_TICK)
    s2 = frame_arr("S_pass2_t%d" % ph.V3_TICK)
    d1 = frame_arr("S_pass1_diag_t%d" % ph.V3_TICK)
    d2 = frame_arr("S_pass2_diag_t%d" % ph.V3_TICK)
    v3_clean_identical = bool(np.array_equal(s1, s2))
    v3_diag_identical = bool(np.array_equal(d1, d2))
    require(v3_clean_identical and v3_diag_identical,
            "prediction_failed:P4_v3_pairs_not_identical")
    # P4(b): a fresh re-render of one V1 clean frame from the same records
    re_plan = [{"frame_id": "RERENDER_V1_t%d" % ph.V1_CLEAN_TICKS[0],
                "view": ph.CLEAN_VIEW, "tick": ph.V1_CLEAN_TICKS[0],
                "diagnostic": False, "render_index": 0}]
    re_colours, _re_metas = ph.render_frames(res1["per_tick"], geom, vz, f04,
                                             re_plan, climb_audit)
    base0 = frame_arr("P00_V1_clean_t%d" % ph.V1_CLEAN_TICKS[0])
    rerender_identical = bool(np.array_equal(
        np.asarray(re_colours[0], dtype=np.uint8), base0))
    require(rerender_identical, "prediction_failed:P4_rerender_not_identical")
    # P4(c): a tampered row renders a DIFFERENT frame (> 0 pixels)
    row0 = next(r for r in res1["per_tick"]
                if r["tick"] == ph.V1_CLEAN_TICKS[0])
    tam = ph.tamper_row(row0, ph.TAMPER_PHASE_DELTA)
    tam_plan = [{"frame_id": "TAMPER_V1_t%d" % ph.V1_CLEAN_TICKS[0],
                 "view": ph.CLEAN_VIEW, "tick": ph.V1_CLEAN_TICKS[0],
                 "diagnostic": False, "render_index": 0}]
    tam_colours, _tam_metas = ph.render_frames([tam], geom, vz, f04, tam_plan,
                                               climb_audit)
    tam_diff = int((np.asarray(tam_colours[0], dtype=np.uint8)
                    != base0).any(axis=2).sum())
    require(tam_diff > 0, "prediction_failed:P4_tamper_not_visible")
    # P7: every CLEAN frame has zero layer pixels (executed probe)
    clean_probes = []
    for m in metas:
        if m["diagnostic"]:
            continue
        arr = frame_arr(m["frame_id"])
        probe = sr.probe_clean_frame(arr)
        require(probe["clean_ok"],
                "prediction_failed:P7_clean_leak:" + m["frame_id"])
        clean_probes.append({"frame_id": m["frame_id"],
                             "layer_pixels_total":
                                 probe["layer_pixels_total"]})
    # P8/P9/P11: every DIAGNOSTIC frame's probes are exact
    diag_probes = []
    for m in metas:
        if not m["diagnostic"]:
            continue
        arr = frame_arr(m["frame_id"])
        findings = sr.probe_layer_pixels(arr, m["label_receipt"])
        for rowres in findings["rows"]:
            require(rowres["count_ok"] and rowres["bbox_ok"],
                    "prediction_failed:P9_label_geometry:"
                    + m["frame_id"] + ":" + rowres["text"])
        for key in ("l1_bg", "l1_border", "l2_bg", "l3_bg"):
            require(findings["layers"][key + "_px"]
                    == findings["layers"][key + "_expected"],
                    "prediction_failed:P8_layer_geometry:"
                    + m["frame_id"] + ":" + key)
        require(findings["body_pixels_inside_inset"] == 0,
                "prediction_failed:P8_body_inside_inset:" + m["frame_id"])
        diag_probes.append({"frame_id": m["frame_id"],
                            "rows_all_exact": True,
                            "layers_exact": True,
                            "body_inside_inset": 0})
    # P12: the clean V1 series deforms with the actual cycle
    pose_ids = ph.pose_hash_series(metas, ph.CLEAN_VIEW)
    require(len(pose_ids) == len(ph.V1_CLEAN_TICKS),
            "prediction_failed:P12_series_incomplete")
    distinct = len(set(pose_ids))
    require(distinct >= 2,
            "prediction_failed:P12_single_pose_render")
    return {"f04": f04, "vz": vz, "geom": geom, "plan": plan,
            "colours": colours, "metas": metas,
            "v3_clean_identical": v3_clean_identical,
            "v3_diag_identical": v3_diag_identical,
            "rerender_identical": rerender_identical,
            "tamper_diff_px": tam_diff,
            "clean_probes": clean_probes, "diag_probes": diag_probes,
            "pose_distinct_count": distinct}


def stage_predictions(res1, res2, reg, climb_audit, render):
    ev = {}
    metas = render["metas"]
    geom = render["geom"]
    vz = render["vz"]

    # ---- P1/P5 (every rendered frame's mapping audit is in derive_state) --
    worst = 0.0
    links = set()
    coverage_ok = True
    by_tick = ph.row_index(res1["per_tick"])
    for m in metas:
        row = by_tick[m["tick"]]
        require(row is not None, "prediction_failed:P1_row_missing")
        prev = by_tick.get(m["tick"] - 1)
        state = sr.derive_state(row, prev, climb_audit, vz, geom)
        for side in ("left", "right"):
            a = state["chain_audit"][side]
            worst = max(worst, a["max_deviation_m"])
            if a["connected_sites"] != 5 or a["sites"] != 5:
                coverage_ok = False
        links.add(state["link"])
        # the render-time joints must be the audited chain bitwise
        for side in ("left", "right"):
            for site, vals in m["render_joints"][side].items():
                pose_site = state["pose"]["legs"][side][site]
                require(float(vals[0]) == float(pose_site[0])
                        and float(vals[1]) == float(pose_site[1]),
                        "prediction_failed:P5_joint_identity:"
                        + m["frame_id"] + ":" + side + ":" + site)
    require(coverage_ok and links == {"L5/5 R5/5"},
            "prediction_failed:P1_connected_chain")
    ev["P1_connected_chain"] = {
        "links_observed": sorted(links), "sites_per_leg": 5,
        "coverage_complete": coverage_ok,
        "law": "chain audit: five sites x two legs, declared attachments"}
    ev["P5_material_mapping"] = {
        "max_deviation_m": worst, "bitwise_zero": worst == 0.0,
        "frames_audited": len(metas),
        "render_joint_identity": True,
        "law": "M12 render_binding_audit law form: rendered == re-derived "
               "mechanical snapshot, full coverage",
        "mapping_identity": "W10 visualization.py + derived_numbers.json "
                            "(sha-pinned rows in pins_x04.json / the W10 "
                            "pin layer)"}
    require(worst == 0.0, "prediction_failed:P5_mapping_not_bitwise")

    # ---- P2 (contact labels follow actual state; transition coverage) ----
    cov = ph.transition_coverage(res1["per_tick"])
    require(cov["left_count"] >= 1 and cov["right_count"] >= 1,
            "prediction_failed:P2_no_transitions_in_window")
    label_pairs_differ = 0
    for m in metas:
        row = by_tick[m["tick"]]
        require(m["state"]["contact_l"] == int(row["foot_contacts"][4])
                and m["state"]["contact_r"] == int(row["foot_contacts"][5])
                and float(m["state"]["force_l_n"])
                == float(row["foot_forces"][4])
                and float(m["state"]["force_r_n"])
                == float(row["foot_forces"][5]),
                "prediction_failed:P2_label_not_row:" + m["frame_id"])
    for tr in (cov["left"][:1] + cov["right"][:1]):
        a = by_tick[tr["tick"] - 1]
        b = by_tick[tr["tick"]]
        sa = sr.derive_state(a, None, climb_audit, vz, geom)
        sb = sr.derive_state(b, a, climb_audit, vz, geom)
        if sr.label_lines(sa) != sr.label_lines(sb):
            label_pairs_differ += 1
    require(label_pairs_differ >= 1,
            "prediction_failed:P2_labels_not_following_transitions")
    ev["P2_contact_labels_follow_state"] = {
        "left_transitions": cov["left_count"],
        "right_transitions": cov["right_count"],
        "transition_examples": (cov["left"][:2] + cov["right"][:2]),
        "label_pairs_differ_at_transitions": label_pairs_differ,
        "window": [ph.PW0, ph.PW1],
        "law": "labels derive from the committed rows; a transition changes "
               "the label"}

    # ---- P3 (climb state honest; the scratch proof rode stage_climb_audit)
    ev["P3_climb_state_honest"] = dict(climb_audit)
    ev["P3_climb_state_honest"]["labels_read"] = sorted(
        {m["state"]["climb_state"] for m in metas})

    # ---- P4 (single pose source; identity + tamper + structural) ---------
    ev["P4_single_pose_source"] = {
        "v3_clean_identical": render["v3_clean_identical"],
        "v3_diag_identical": render["v3_diag_identical"],
        "rerender_identical": render["rerender_identical"],
        "tamper_phase_delta": ph.TAMPER_PHASE_DELTA,
        "tamper_diff_px": render["tamper_diff_px"],
        "render_consumes_records_only": True,
        "state_chain_recorded_before_render": True,
        "loop_has_camera_channel": False,
        "w10_fb6_heritage": "cited (sealed), not re-claimed"}
    require(render["tamper_diff_px"] > 0,
            "prediction_failed:P4_tamper_not_visible")

    # ---- P6/P7/P8/P9/P11 (ride the render probes; recorded here) ---------
    required_fields = reg["profile"]["camera_required_fields"]
    ev["P6_camera_fields_complete"] = {
        "required_field_count": len(required_fields),
        "required_fields": list(required_fields),
        "prereg_recorded_field_count": 15,
        "registry_drift_disclosure": (
            "the frozen prereg text recorded 15 camera_required_fields at "
            "freeze; the live registry profile (read-only, consumed per G7) "
            "declares %d; the operative law is ALL profile fields carried "
            "per row, which the capture manifest asserts" %
            len(required_fields)),
        "law": "asserted per manifest row in the capture stage; the camera "
               "records carry every profile field",
        "occlusion_mode": "depth_tested",
        "occlusion_note": "no occluder declared in this profile (A6)"}
    ev["P7_clean_view_no_diagnostics"] = {
        "clean_frames_probed": len(render["clean_probes"]),
        "layer_pixels_total": sum(p["layer_pixels_total"]
                                  for p in render["clean_probes"]),
        "per_frame_zero": all(p["layer_pixels_total"] == 0
                              for p in render["clean_probes"])}
    ev["P8_debug_layers_present"] = {
        "diagnostic_frames_probed": len(render["diag_probes"]),
        "layers": reg["profile"]["diagnostic_layers"],
        "all_rows_exact": True, "body_inside_inset_any":
            any(p["body_inside_inset"] for p in render["diag_probes"])}
    ev["P9_readability_measured"] = {
        "probe": "exact palette-pixel count + bbox vs the glyph law",
        "diagnostic_frames": [p["frame_id"] for p in render["diag_probes"]],
        "detail_view_frame": "D_V2_t%d" % ph.V2_DIAG_TICKS[0],
        "all_exact": True}
    ev["P11_label_content_bound"] = {
        "label_receipts": sum(1 for m in metas if m["label_receipt"]),
        "receipts_bound_to_rows": True,
        "law": "every diagnostic frame's receipt binds strings, origins and "
               "glyph-law expectations; the state block binds the row"}

    # ---- P10 (repeatable states) -----------------------------------------
    chains_equal = res1["state_chain"] == res2["state_chain"]
    ev["P10_repeatable_states"] = {
        "state_chains_identical": chains_equal,
        "a1_final_state_sha256": res1["final_state_sha256"],
        "a2_final_state_sha256": res2["final_state_sha256"],
        "law": "A2 is a fresh re-execution; the states the labels report "
               "are reproducible"}
    require(chains_equal, "prediction_failed:P10_repeatable_states")

    # ---- P12 (deform follows state) ---------------------------------------
    ev["P12_deform_follows_state"] = {
        "clean_frames": len(ph.V1_CLEAN_TICKS),
        "distinct_pose_ids": render["pose_distinct_count"],
        "nonvacuity_guard": "29 frames rendered; a single-pose render "
                            "would fail this prediction",
        "law": "the ONE pose moves because the material state moves"}
    require(render["pose_distinct_count"] >= 2,
            "prediction_failed:P12_single_pose_render")
    return ev


def stage_bites(res1, reg, climb_audit, render):
    """FB1-FB5: each with its own passing clean control FIRST and a named
    premature guard (G1/P1)."""
    geom = render["geom"]
    vzmod = render["vz"]
    f04 = render["f04"]
    metas = render["metas"]
    by_tick = ph.row_index(res1["per_tick"])
    bites = {}

    def frame_arr(frame_id):
        i = next(m["render_index"] for m in metas
                 if m["frame_id"] == frame_id)
        return np.asarray(render["colours"][i], dtype=np.uint8)

    # ---- FB1 placeholder state ------------------------------------------
    # selection: the first diagnostic tick whose actual state differs from
    # the declared placeholders (the premature guard IS this selection).
    sel = None
    for tick in sorted({m["tick"] for m in metas if m["diagnostic"]}):
        row = by_tick[tick]
        if (int(row["foot_contacts"][4]) != ph.PLACEHOLDER["contact"]
                or int(row["foot_contacts"][5]) != ph.PLACEHOLDER["contact"]
                or float(row["foot_forces"][4]) != ph.PLACEHOLDER["force_n"]
                or float(row["foot_forces"][5]) != ph.PLACEHOLDER["force_n"]):
            sel = tick
            break
    require(sel is not None, "x04_fb1_premature:no_discriminating_tick")
    actual = next(m for m in metas if m["diagnostic"] and m["tick"] == sel)
    actual_arr = frame_arr(actual["frame_id"])
    row = by_tick[sel]
    prev = by_tick.get(sel - 1)
    real_state = sr.derive_state(row, prev, climb_audit, vzmod, geom)
    placeholder_state = {
        "tick": sel, "link": ph.PLACEHOLDER["link"],
        "contact_l": ph.PLACEHOLDER["contact"],
        "contact_r": ph.PLACEHOLDER["contact"],
        "force_l_n": ph.PLACEHOLDER["force_n"],
        "force_r_n": ph.PLACEHOLDER["force_n"],
        "climb_state": ph.PLACEHOLDER["climb"], "mode": ph.PLACEHOLDER["mode"],
        "event": "-", "com_v_m_s": 0.0,
        "state_sha256": "placeholder_not_a_row_value"}
    ph_colour = np.asarray(actual_arr).copy().tolist()
    ph_receipt = sr.draw_layers(ph_colour, {
        **placeholder_state, "pose": real_state["pose"]})
    ph_arr = np.asarray(ph_colour, dtype=np.uint8)
    diff_px = int((ph_arr != actual_arr).any(axis=2).sum())
    refused = None
    try:
        sr.binding_audit(ph_receipt, row, prev, climb_audit, vzmod, geom)
    except sr.Refusal as r:
        refused = str(r)
    require(refused is not None and refused.startswith("x04_"),
            "falsifier_did_not_bite:FB1_placeholder_accepted")
    require(diff_px > 0, "falsifier_did_not_bite:FB1_pixels_identical")
    clean_ctl = sr.binding_audit(actual["label_receipt"], row, prev,
                                 climb_audit, vzmod, geom)
    bites["FB1_placeholder_state"] = {
        "selected_tick": sel,
        "premature_guard": "x04_fb1_premature (actual state differs from "
                           "the placeholders at the selected tick)",
        "clean_control": {"binding_audit_pass": bool(clean_ctl["ok"]),
                          "metric_scope": "the actual frame's receipt "
                                          "against its own row"},
        "placeholder_refusal": refused,
        "placeholder_pixel_diff": diff_px,
        "bit": True}

    # ---- FB2 second pose (the canned-pose bite) --------------------------
    canned = {"body_xy": (row["com_x_m"], 0.0), "heading_rad": 0.0,
              "com_height_m": vzmod.BODY_LIFT_M,
              "legs": {"left": {"hip": (0.0, 0.5), "knee": (0.1, 0.45),
                                "ankle": (0.2, 0.4), "mp": (0.3, 0.35),
                                "heel": (0.05, 0.35)},
                       "right": {"hip": (0.04, 0.5), "knee": (0.14, 0.45),
                                 "ankle": (0.24, 0.4), "mp": (0.34, 0.35),
                                 "heel": (0.09, 0.35)}},
              "com_vel": row["com_v_m_s"], "tick": sel,
              "foot_contacts": row["foot_contacts"],
              "foot_forces": row["foot_forces"],
              "applied_cmd": row["applied_cmd"]}
    canned_audit = sr.audit_chain(canned, vzmod, geom, row)
    canned_worst = max(canned_audit[s]["max_deviation_m"]
                       for s in ("left", "right"))
    view = ph.X04_VIEWS["V1_normal_player_camera"]
    c_colour, _d, _cam = vzmod.render_frame(
        f04, view, canned, False, sel, "canned")
    c_arr = np.asarray(c_colour, dtype=np.uint8)
    c_diff = int((c_arr != actual_arr).any(axis=2).sum())
    require(canned_worst > 0.0,
            "x04_fb2_premature:canned_pose_matches_the_law")
    require(c_diff > 0, "falsifier_did_not_bite:FB2_pixels_identical")
    clean_ctl2 = sr.audit_chain(real_state["pose"], vzmod, geom, row)
    clean2_worst = max(clean_ctl2[s]["max_deviation_m"]
                       for s in ("left", "right"))
    require(clean2_worst == 0.0, "x04_fb2_premature:clean_control_not_zero")
    bites["FB2_second_pose"] = {
        "premature_guard": "x04_fb2_premature (the canned pose differs "
                           "from the row's law; the actual pose passes the "
                           "same audit bitwise)",
        "clean_control": {"same_row_max_deviation_m": clean2_worst,
                          "metric_scope": "the actual render against its "
                                          "own row"},
        "canned_mapping_worst_deviation_m": canned_worst,
        "canned_pixel_diff": c_diff,
        "bit": True}

    # ---- FB3 missing layer / schema-refused ------------------------------
    miss_plan = [{"frame_id": "MISSING_LAYER_t%d" % sel,
                  "view": "V1_normal_player_camera", "tick": sel,
                  "diagnostic": True, "render_index": 0}]
    miss_colours, miss_metas = ph.render_frames(
        res1["per_tick"], geom, vzmod, f04, miss_plan, climb_audit,
        with_layers=False)
    miss_arr = np.asarray(miss_colours[0], dtype=np.uint8)
    findings = sr.probe_layer_pixels(miss_arr, actual["label_receipt"])
    layer_missing = not all(r["count_ok"] and r["bbox_ok"]
                            for r in findings["rows"])
    require(layer_missing,
            "falsifier_did_not_bite:FB3_layer_present_without_drawing")
    require(climb_audit["scratch_flipped"]["climb_state"]
            == "schema_climb_key_present",
            "falsifier_did_not_bite:FB3_schema_not_flipping")
    clean_diag_ok = all(p["rows_all_exact"] and p["layers_exact"]
                        for p in render["diag_probes"])
    require(clean_diag_ok, "x04_fb3_premature:clean_diagnostic_failed")
    bites["FB3_missing_layer"] = {
        "premature_guard": "x04_fb3_premature (the real diagnostic frames "
                           "pass their own probes first)",
        "clean_control": {"diagnostic_probes_exact": clean_diag_ok,
                          "metric_scope": "all real diagnostic frames"},
        "missing_layer_probe_fired": layer_missing,
        "schema_scratch_flip": climb_audit["scratch_flipped"],
        "bit": True}

    # ---- FB4 clean leak ---------------------------------------------------
    clean_ids = [m["frame_id"] for m in metas if not m["diagnostic"]][:1]
    base_clean = frame_arr(clean_ids[0])
    leak = base_clean.copy()
    leak[sr.L1_RECT[1] + 1, sr.L1_RECT[0] + 1] = sr.L1_TEXT
    leak_probe = sr.probe_clean_frame(leak)
    require(not leak_probe["clean_ok"],
            "falsifier_did_not_bite:FB4_leak_not_caught")
    real_clean_probe = sr.probe_clean_frame(base_clean)
    require(real_clean_probe["clean_ok"],
            "x04_fb4_premature:real_clean_frame_already_leaking")
    bites["FB4_clean_leak"] = {
        "premature_guard": "x04_fb4_premature (the real clean frame has "
                           "zero layer pixels)",
        "clean_control": {"layer_pixels_total":
                          real_clean_probe["layer_pixels_total"],
                          "metric_scope": "the untampered clean still"},
        "leak_pixels_detected": leak_probe["layer_pixels_total"],
        "bit": True}

    # ---- FB5 stale mapping ------------------------------------------------
    tick_a, tick_b = ph.V1_CLEAN_TICKS[0], ph.V1_CLEAN_TICKS[1]
    row_a, row_b = by_tick[tick_a], by_tick[tick_b]
    pose_a = vzmod.pose_at(row_a, geom, 0.0, (row_a["com_x_m"], 0.0))
    stale_audit = sr.audit_chain(pose_a, vzmod, geom, row_b)
    stale_worst = max(stale_audit[s]["max_deviation_m"]
                      for s in ("left", "right"))
    fresh_audit = sr.audit_chain(pose_a, vzmod, geom, row_a)
    fresh_worst = max(fresh_audit[s]["max_deviation_m"]
                      for s in ("left", "right"))
    require(fresh_worst == 0.0, "x04_fb5_premature:clean_control_not_zero")
    require(row_a["phase_left"] != row_b["phase_left"],
            "x04_fb5_premature:rows_share_a_phase")
    require(stale_worst > 0.0,
            "falsifier_did_not_bite:FB5_stale_mapping_passed")
    bites["FB5_stale_mapping"] = {
        "premature_guard": "x04_fb5_premature (same-row audit bitwise 0; "
                           "the rows' phases genuinely differ)",
        "clean_control": {"same_row_max_deviation_m": fresh_worst,
                          "metric_scope": "frame A audited against row A"},
        "stale_max_deviation_m": stale_worst,
        "declared_law": "audit refuses any pose not re-derived from ITS OWN "
                        "committed row",
        "bit": True}
    return bites


def declared_refusal_proofs(res_by_arm):
    proofs = {}
    for arm, res in res_by_arm.items():
        proofs[arm] = {
            "arm": arm,
            "final_state_sha256": res["final_state_sha256"],
            "declared": "W10 sealed run_commanded: the port's only channel "
                        "is the recording sink; no engine process"}
    return proofs


def main() -> int:
    rows, reg, prereg_commit, w10, limits = stage_pins()
    require(reg["profile"]["id"] == "presentation",
            "profile_check_after_capture_forbidden")
    adapter, build_id, params, gate = gate_and_load()
    climb_audit = stage_climb_audit()

    res1, res2 = ph.run_arms(adapter, build_id, params)
    render = stage_render(res1, reg, climb_audit)
    ev = stage_predictions(res1, res2, reg, climb_audit, render)
    bites = stage_bites(res1, reg, climb_audit, render)

    receipt = {
        "schema": "chimera.x04_presentation_receipt.v1",
        "task_id": "X04", "card_id": "MAT2-X04",
        "attempt_id": vi4.ATTEMPT_ID, "agent_id": vi4.AGENT_ID,
        "criteria_sha256": vi4.CRITERIA_SHA256,
        "base_sha256": vi4.BASE_SHA,
        "prereg_commit": prereg_commit,
        "preregistration_sha256": vi4.prereg_sha256(),
        "registry": reg,
        "pin_rows": rows, "pin_row_count": len(rows),
        "w10_layer": w10,
        "p06_caller_limits": {"ui_poll_cadence_ms":
                              limits["ui_poll_cadence_ms"]},
        "gate": gate,
        "arms": {"A1": {"run_id": "mat2-x04/A1",
                        "horizon": ph.HORIZON_A1,
                        "final_state_sha256": res1["final_state_sha256"],
                        "expiry_revert_ticks": res1["expiry_revert_ticks"],
                        "sink_record_count": len(res1["sink_records"]),
                        "decision_count": len(res1["decisions"])},
                 "A2": {"run_id": "mat2-x04/A2",
                        "horizon": ph.HORIZON_A1,
                        "final_state_sha256": res2["final_state_sha256"],
                        "expiry_revert_ticks": res2["expiry_revert_ticks"],
                        "sink_record_count": len(res2["sink_records"]),
                        "decision_count": len(res2["decisions"])}},
        "window": {"consumed_ticks": [ph.PW0, ph.PW1],
                   "cycle_ticks": ph.CYCLE_TICKS,
                   "clean_frames": len(ph.V1_CLEAN_TICKS),
                   "frame_plan_entries": len(render["plan"])},
        "predictions": ev,
        "falsifier_bites": bites,
        "declared_channel": declared_refusal_proofs(
            {"A1": res1, "A2": res2}),
        "render": {"frame_count": len(render["plan"]),
                   "v3_pairs_identical":
                       [render["v3_clean_identical"],
                        render["v3_diag_identical"]],
                   "pose_distinct_count": render["pose_distinct_count"]},
        "absent_inventory": {
            "A1_climbing_controller": "ABSENT (the pinned scene schema has "
                                      "no climbing state; the label reports "
                                      "the DERIVED absent_declared value; no "
                                      "climbing pose is fabricated — that "
                                      "would be the forbidden second "
                                      "locomotion pose; A9's law cited)",
            "A2_native_engine_frame": "ABSENT (declared CPU-line frame "
                                      "records of the records-only "
                                      "renderer; W10 N1/N2/N3 + U07 A1 "
                                      "carried)",
            "A3_cosmetic_skin": "ABSENT (the DECLARED gait-walker skeleton "
                                "visualization; W10 FB5 heritage cited)",
            "A4_audio_cues": "NOT claimed on this card (X05's scope; C24 "
                             "not exercised)",
            "A5_session_inspector_overlays": "NOT exercised (X02/X06 "
                                             "surfaces)",
            "A6_occlusion_camera_collision_probes": "NOT declared in this "
                                                    "profile's views (U07's "
                                                    "arm); depth_tested "
                                                    "recorded",
            "A7_human_feel": "readability here is the measured glyph "
                             "geometry (P9); human acceptance remains the "
                             "independent picture review"},
        "determinism": {"canonical_json": True, "newline": "\n",
                        "command": "python -B "
                                   "tools/monkey_campaign/contributions/"
                                   "MAT2-X04/run_presentation_verification"
                                   ".py"},
    }

    # verdicts on the evidence (honest: the done_when is bounded by A1/A2)
    verdict = {
        "P_all_green": True,
        "FB_all_bit_with_clean_controls": True,
        "qualified": ["P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8", "P9",
                      "P10", "P11", "P12"],
        "bounded_by_absent_inventory": [
            "A1 climbing controller ABSENT (the honest state label)",
            "A2 native engine frame ABSENT (declared CPU-line records)"],
    }
    receipt["verdict"] = verdict

    write_out("presentation_receipt.json", receipt)
    write_out("trace_a1_window.json", {
        "arm": "A1", "horizon": ph.HORIZON_A1,
        "window": [ph.PW0, ph.PW1],
        "rows": [r for r in res1["per_tick"]
                 if ph.PW0 <= r["tick"] < ph.PW1]})
    write_out_bytes("frames_meta.json", canonical(
        {"plan": render["plan"], "metas": render["metas"]}) + b"\n")
    np.save(str(OUT / "frames.npy"),
            np.stack(render["colours"]).astype(np.uint8))
    print("presentation verification: P_all_green; frames %d; pose "
          "distinctness %d; FB bites %d"
          % (len(render["plan"]), render["pose_distinct_count"],
             len(bites)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
