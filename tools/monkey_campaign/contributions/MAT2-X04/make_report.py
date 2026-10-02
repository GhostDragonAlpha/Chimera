#!/usr/bin/env python3
"""MAT2-X04: the generated report (from the receipts; nothing hand-written).

Reads the stage receipts from CHIMERA_OUTPUT_DIR and emits REPORT.md with
every number cited from a receipt field. No new measurement happens here.

Run:  python -B make_report.py   (exit 0 green / 2 named refusal)
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = Path(os.environ.get("CHIMERA_OUTPUT_DIR", HERE / "outputs"))


def require(condition, code):
    if not condition:
        print("REFUSAL:" + str(code), file=sys.stderr)
        raise SystemExit(2)


def load(name):
    return json.loads((OUT / name).read_bytes().decode("utf-8"))


def main() -> int:
    receipt = load("presentation_receipt.json")
    checks = load("checks_receipt.json")
    capture = load(os.path.join("capture", "capture_receipt.json"))
    gate = load("capture_gate_summary.json")

    reg = receipt["registry"]
    pred = receipt["predictions"]
    bites = receipt["falsifier_bites"]
    require(checks["verdict"] == "GREEN", "report_checks_not_green")
    require(capture["validation"]["structurally_valid"] is True,
            "report_capture_not_valid")
    require(gate.get("verdict") == "GREEN"
            and gate.get("all_production_green") is True
            and gate.get("all_defects_rejected") is True,
            "report_capture_gate_not_green")
    require(receipt["verdict"]["P_all_green"] is True,
            "report_predictions_not_green")
    require(receipt["verdict"]["FB_all_bit_with_clean_controls"] is True,
            "report_bites_not_green")

    p1 = pred["P1_connected_chain"]
    p2 = pred["P2_contact_labels_follow_state"]
    p3 = pred["P3_climb_state_honest"]
    p4 = pred["P4_single_pose_source"]
    p5 = pred["P5_material_mapping"]
    p7 = pred["P7_clean_view_no_diagnostics"]
    p12 = pred["P12_deform_follows_state"]

    lines = [
        "# REPORT — MAT2-X04 render readable animal and environment state",
        "",
        "Generated from the sealed stage receipts; no hand-entered numbers.",
        "",
        "## Identity",
        "",
        "- Card MAT2-X04, attempt %s, agent %s." % (receipt["attempt_id"],
                                                    receipt["agent_id"]),
        "- Base %s; prereg commit %s; prereg sha256 %s."
        % (receipt["base_sha256"], receipt["prereg_commit"]["commit"],
           receipt["preregistration_sha256"]),
        "- done_when (verbatim): %s" % reg["done_when"],
        "- Profile: %s/%s (registry read-only at run time; checked BEFORE "
        "any capture)." % (reg["profile"]["id"], reg["profile"]["kind"]),
        "- Certified line: %s (W10 gate identity re-executed; deploy %s)."
        % (receipt["gate"]["physics_build"]["build_id"],
           receipt["gate"]["deploy_decision"]),
        "",
        "## Measured variables (named, preregistered)",
        "",
        "- P1 connected chain: links observed %s, sites per leg %s, "
        "coverage complete %s (chain audit over every rendered frame)."
        % (p1["links_observed"], p1["sites_per_leg"],
           p1["coverage_complete"]),
        "- P2 contact labels follow actual state: %s left / %s right "
        "contact transitions in the consumed window %s; %s label pairs "
        "differ across transitions; labels equal the committed rows."
        % (p2["left_transitions"], p2["right_transitions"], p2["window"],
           p2["label_pairs_differ_at_transitions"]),
        "- P3 climb state honest: derived %r (observation keys %s; the "
        "scratch climb-key injection derives %r); label text CLIMB NONE is "
        "the true state, never a claimed capability."
        % (p3["clean"]["climb_state"], p3["clean"]["observation_key_count"],
           p3["scratch_flipped"]["climb_state"]),
        "- P4 single pose source: V3 clean pair identical %s, V3 "
        "diagnostic pair identical %s, re-render identical %s; the declared "
        "phase tamper (delta %s) changes %s pixels — the pose follows the "
        "records; no second pose generator exists in the contribution."
        % (p4["v3_clean_identical"], p4["v3_diag_identical"],
           p4["rerender_identical"], p4["tamper_phase_delta"],
           p4["tamper_diff_px"]),
        "- P5 material mapping verified: max deviation %s m over %s "
        "audited frames (bitwise zero %s); render joints identical to the "
        "re-derived chain (M12 render_binding_audit law form)."
        % (p5["max_deviation_m"], p5["frames_audited"], p5["bitwise_zero"]),
        "- P7 clean view: %s clean frames probed, layer pixels total %s "
        "(per-frame zero %s)."
        % (p7["clean_frames_probed"], p7["layer_pixels_total"],
           p7["per_frame_zero"]),
        "- P12 deform follows state: %s clean frames carry %s distinct "
        "pose identifiers — the ONE pose moves because the material state "
        "moves." % (p12["clean_frames"], p12["distinct_pose_ids"]),
        "- P6/P8/P9/P10/P11: camera fields complete (%s profile fields, "
        "occlusion mode %s); diagnostic frames carry all three declared "
        "layers with exact glyph-law geometry; A2 repeat state chain "
        "identical %s; label receipts bound to their rows."
        % (pred["P6_camera_fields_complete"]["required_field_count"],
           pred["P6_camera_fields_complete"]["occlusion_mode"],
           pred["P10_repeatable_states"]["state_chains_identical"]),
        "",
        "## Falsifier bites (each with its passing clean control first)",
        "",
    ]
    for name in sorted(bites):
        b = bites[name]
        lines.append("- %s: bit=%s; guard %s; clean control {%s}."
                     % (name, b["bit"],
                        b["premature_guard"].split(" (")[0],
                        "; ".join("%s: %s" % (k, v) for k, v
                                  in b["clean_control"].items())))
    lines += [
        "",
        "## Honest negatives (the absent inventory)",
        "",
    ]
    for key in sorted(receipt["absent_inventory"]):
        lines.append("- %s: %s" % (key, receipt["absent_inventory"][key]))
    lines += [
        "",
        "## Checks and capture",
        "",
        "- Named checks: %s (%s)." % (checks["verdict"], checks["claim"]),
        "- Capture: %s frames, video sha %s, decode probes pixel-exact %s, "
        "validator %s."
        % (capture["video"]["frames"], capture["video"]["sha256"][:16],
           capture["decode_probes_pixel_exact"],
           capture["validation"]["structurally_valid"]),
        "- Two-stage capture gate (standing template, in addition to the "
        "frozen capture law): %s over %s cases — %s production frames "
        "GREEN %s, defects rejected %s; view-spec prereg sha %s."
        % (gate["verdict"], gate["case_count"],
           gate["production_frames_total"], gate["all_production_green"],
           gate["all_defects_rejected"],
           gate["view_spec_prereg_sha256"][:16]),
        "- Pins: %s X04 rows + %s W10 certified-line rows, byte-exact."
        % (receipt["pin_row_count"], receipt["w10_layer"]["w10_pin_rows"]),
        "",
        "## Verdict",
        "",
        "The connected, contact and climbing states are READABLE in the "
        "actual captures (declared layers, measured glyph geometry, "
        "row-bound labels), the render deforms from the actual material "
        "state through the verified mapping, and the debug layers are "
        "invisible in the clean play view while present in verification. "
        "The climbing controller itself is ABSENT on the certified walking "
        "line (the label reports the derived absent_declared value) and the "
        "presented frames remain the declared CPU-line frame records, "
        "visual acceptance false by design. This receipt alone does not "
        "close the card: lead-approved exact-head PR with full "
        "qualification evidence remains.",
        "",
    ]
    (OUT / "REPORT.md").write_bytes("\n".join(lines).encode("utf-8"))
    print("report written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
