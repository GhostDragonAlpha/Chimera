#!/usr/bin/env python3
"""MAT2-U07: the generated report (from the receipts; nothing hand-written).

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
    receipt = load("controls_receipt.json")
    checks = load("checks_receipt.json")
    capture = load(os.path.join("capture", "capture_receipt.json"))

    reg = receipt["registry"]
    pred = receipt["predictions"]
    require(checks["verdict"] == "GREEN", "report_checks_not_green")
    require(capture["validation"]["structurally_valid"] is True,
            "report_capture_not_valid")
    require(receipt["verdict"]["P_all_green"] is True,
            "report_predictions_not_green")

    p1 = pred["P1_first_response"]
    p2 = pred["P2_consumed_lag"]
    p3 = pred["P3_presented_lag"]
    p4 = pred["P4_poll_cadence"]
    p7 = pred["P7_expiry_revert"]
    p11 = pred["P11_limits_honesty"]
    window = receipt["render"]

    lines = [
        "# REPORT — MAT2-U07 measure controls during actual play",
        "",
        "Generated from the sealed stage receipts; no hand-entered numbers.",
        "",
        "## Identity",
        "",
        "- Card MAT2-U07, attempt %s, agent %s." % (receipt["attempt_id"],
                                                    receipt["agent_id"]),
        "- Base %s; prereg sha256 %s." % (receipt["base_sha256"],
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
        "- P1 first_response_ms_max = %s over %d input transitions (chains "
        "%d; limit 50.0 ms, C12 seam cadence, caller data; AMENDMENT-A1 "
        "law) -> %s."
        % (p1["first_response_ms_max"], p1["transitions"], p1["chains"],
           "QUALIFIED" if p1["first_response_ms_max"] <= 50.0
           else "FAILED"),
        "- P2 consumed_lag_ticks_max = %s (ZOH boundary law) -> QUALIFIED."
        % p2["consumed_lag_ticks_max"],
        "- P3 presented_lag_ticks_max = %s over %d window chains (bound %s); "
        "presented = the DECLARED CPU-line frame record (A1)."
        % (p3["presented_lag_ticks_max"], p3["window_chains"],
           p3["bound_ticks"]),
        "- P4 poll_period_ms_max = %s (P06 frozen ui-poll-cadence-ms = %s ms) "
        "-> QUALIFIED against the ONLY frozen P06 cadence numeric."
        % (p4["poll_period_ms_max"], p4["p06_frozen_limit_ms"]),
        "- P7 first_revert_age_ticks = %s (EXPIRY_TICKS=%s; the stuck-command "
        "law reverts at age %d)." % (p7["first_revert_age_ticks"],
                                     p7["expiry_ticks_const"],
                                     p7["expiry_ticks_const"] + 1),
        "- P5/P6/P8/P9/P10/P12: all green in controls_receipt.json "
        "(repeatable scene bit-identical; wrong-key response flagged; focus "
        "blur drops named and recovery is a new chain; camera fields "
        "complete; obstruction numerics executed; mixed-clock refused).",
        "",
        "## Honest negatives (the unqualified part of the done_when)",
        "",
        "- P11 wall-clock end-to-end latency: status %r (%s). No frozen "
        "wall-clock SLA exists — P06 network-latency-sla-ms is an open "
        "OPERATOR_DECISION_REQUESTED; nothing is inferred or defaulted."
        % (p11["wall_clock_status"], p11["wall_clock_reason"]),
        "- A1 native engine recorder seams: ABSENT; the presented stage is "
        "the declared CPU-line frame record; only the declared window "
        "(chains %d) carries presented events."
        % len(window["window_seqs"]),
        "- A3 human feel: NOT measured (distinct acceptance field).",
        "- A4/A5/A6/A7: camera HTTP transport, session controls, OS focus "
        "and W10's physical-separation claim: declared/cited, not exercised "
        "or re-claimed (controls_receipt.json absent_inventory).",
        "",
        "## Checks and capture",
        "",
        "- Named checks: %s (%s)." % (checks["verdict"], checks["claim"]),
        "- Capture: %d frames, video sha %s, decode probes pixel-exact %s, "
        "validator %s." % (capture["video"]["frames"],
                           capture["video"]["sha256"][:16],
                           capture["decode_probes_pixel_exact"],
                           capture["validation"]["structurally_valid"]),
        "- Pins: %d U07 rows + %d W10 certified-line rows, byte-exact."
        % (len(receipt["pin_rows"]),
           receipt["w10_layer"]["w10_pin_rows"]),
        "",
        "## Verdict",
        "",
        "The frozen structural controls laws (P1/P2/P3/P4) and the camera "
        "behavior structure (P9) are QUALIFIED on the certified CPU line "
        "under repeatable scenes. The wall-clock end-to-end latency claim is "
        "UNQUALIFIED by law (A2) and the native presented frame is ABSENT "
        "(A1). This receipt alone does not close the card: lead-approved "
        "exact-head PR with full qualification evidence remains.",
        "",
    ]
    (OUT / "REPORT.md").write_bytes("\n".join(lines).encode("utf-8"))
    print("report written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
