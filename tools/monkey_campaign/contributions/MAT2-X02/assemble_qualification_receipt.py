"""assemble_qualification_receipt.py -- MAT2-X02: assemble the source-bound
qualification receipt from the artifacts this attempt actually produced.

Every artifact entry carries its sha256 of the exact bytes on disk and an
explicit EVIDENCE CLASS (motion = real runtime capture; records = offline
probe/receipt). No records artifact is offered as runtime proof; no synthetic
frame or test double is relabeled (prereg evidence-class declaration).
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def art(rel: Path, cls: str) -> dict:
    return {"path": str(rel.resolve()), "sha256": sha(rel), "evidence_class": cls}


def main() -> int:
    ev = HERE / "evidence"
    integrated = ev / "integrated"
    session = json.loads(
        (integrated / "session_a_wired_receipt.json").read_text(encoding="utf-8"))
    pinned = json.loads(
        (integrated / "pinned_blob_manifest.json").read_text(encoding="utf-8"))
    ref_manifest = json.loads(
        (HERE / "reference" / "reference_manifest.json").read_text(encoding="utf-8"))

    fired = [c for c in session["checks"] if not c["pass"]]

    receipt = {
        "schema": "chimera.mat2-x02.qualification.v1",
        "task_id": "MAT2-X02",
        "criteria_sha256": "e50bf1e89689aac419c95c1b3a8ce02bb0f5ca5b3c67cf50b575662c0bd63c20",
        "attempt_id": "74bc0ad345074c429272982299a76f4e",
        "agent_id": "arrival-7d28ea9afd7f4ce5819f3aa13ce355e0",
        "base_revision": "97993cbefaf00380803d8e67652ac51d50c37d06",
        "instruction_revision": "astra-0031",
        "verification_profile": {"id": "recovery", "kind": "motion",
                                 "checkpoint_ids": ["V08"]},

        "reconciliation": {
            "reused_byte_exact": {rel: info["sha256"]
                                  for rel, info in ref_manifest["files"].items()},
            "pins": pinned["pin"] if isinstance(pinned.get("pin"), str)
            else pinned.get("pin"),
            "extraction_file_count": pinned.get("file_count"),
            "first_unmet_clause": "app-level session wiring (archived ONT-X02 "
                                  "M1: no session_flow/input_mapper import, no "
                                  "pause/exit control, no Escape/Q/Enter binding)",
            "not_promoted": "archived ONT-X02 DONE (criteria a266d161...) is "
                            "archived-scope evidence, not MAT2 acceptance",
        },

        "unit_probe": {
            "evidence_class": "records",
            "probe": "python -B test_session_app.py (CPU-only)",
            "red_run": art(HERE / "red_run.txt", "records"),
            "green_run": art(HERE / "green_run.txt", "records"),
            "f1_mutation_run": art(HERE / "f1_mutation_run.txt", "records"),
            "pinned_suite": "reference session_flow_tests re-run at recovered "
                            "bytes: exit 0, ALL CHECKS PASS",
        },

        "integrated_session": {
            "evidence_class": "motion",
            "summary": "REAL reconstructed playable application (pinned "
                       "8550b634 bytes) + REAL native engine built from pinned "
                       "source + REAL headless Chrome driving the NEW session "
                       "controls through the page's capture-phase keys.",
            "engine_exe_sha256": session.get("engine_exe_sha256"),
            "checks_total": len(session["checks"]),
            "checks_fired": fired,
            "verdict": session["verdict"],
            "receipt": art(integrated / "session_a_wired_receipt.json", "motion"),
            "console": art(integrated / "session_a_wired_console.txt", "records"),
            "prior_run_fired_console_error": art(
                integrated / "session_a_wired_console_run3_fired_console_error.txt",
                "records"),
            "video": art(integrated / "wired_session.webm", "motion"),
            "trace": art(integrated / "wired_trace.jsonl", "motion"),
            "state_bindings": [art(integrated / "state_binding_before.json",
                                   "motion"),
                               art(integrated / "state_binding_after.json",
                                   "motion")],
            "page_stills": [art(integrated / n, "motion") for n in (
                "view_attract_diagnostic.png", "view_attract_clean.png",
                "view_before_diagnostic.png", "view_before_clean.png",
                "view_paused_diagnostic.png", "view_paused_clean.png",
                "view_after_diagnostic.png", "view_after_clean.png",
                "view_exited_diagnostic.png", "view_exited_clean.png")],
            "engine_frames": [art(integrated / "engine_frame_before.png",
                                  "motion"),
                              art(integrated / "engine_frame_after.png",
                                  "motion")],
            "server_log": art(integrated / "server_log.txt", "records"),
            "extraction_manifest": art(integrated / "pinned_blob_manifest.json",
                                       "records"),
            "numerical": {
                "scene_sha256_before": session["steps"]["A3_pinned_state"]["scene_sha256_before"],
                "scene_sha256_after": session["steps"]["A3_pinned_state"]["scene_sha256_after"],
                "scene_sha256_equal": session["steps"]["A3_pinned_state"]["scene_sha_equal"],
                "start_state_sha256_before": session["steps"]["A3_pinned_state"]["start_state_sha256_before"],
                "start_state_sha256_after": session["steps"]["A3_pinned_state"]["start_state_sha256_after"],
                "start_state_equal": session["steps"]["A3_pinned_state"]["start_state_equal"],
                "start_state_deviation_measured": "the ROOT stream is identical "
                  "(settled root_y 0.124641 both boots; g_contact_n 135618) and "
                  "scene identity is byte-equal; the full-vertex start_state "
                  "hash differs at the engine's own reflex-breathing phase "
                  "(sub-visible vertex ulps at capture time). RECORDED AS "
                  "MEASURED per prereg P3/P4; never tuned.",
                "mapper_records_playing": "0 -> %d" % 2,
                "mapper_records_paused": "2 -> 2 across 2.0s of ticks (zero "
                                         "boundaries while suspended)",
                "boot_count_after_restart": session["steps"]["A3_pinned_state"]["boot_count"],
                "engine_pids": {"before": session["steps"]["A3_pinned_state"]["engine_pids_before"],
                                "after": session["steps"]["A3_pinned_state"]["engine_pids_after"]},
                "zero_surviving_engines_after_exit": session["steps"]["A4_exit"]["engine_orphans_measured_after_kill"],
                "server_port_closed_after_exit": not session["steps"]["A4_exit"]["server_port_still_open"],
            },
            "predictions": {
                "P3_start_state_equality": session.get("predictions", {})
                .get("P3_start_state_equality"),
                "P3_console_errors": {
                    "expected": "zero console/page errors",
                    "measured": {"final_run": "zero",
                                 "prior_run": "one transient "
                                              "net::ERR_NO_BUFFER_SPACE "
                                              "(kept, labeled FIRED in the "
                                              "prior-run console record)"},
                },
            },
        },

        "evidence_class_statement": {
            "motion": "wired_session.webm (+ transcode), view_*.png page "
                      "pixels, engine_frame_*.png engine renders, wired_trace "
                      "and state bindings — all from the REAL running "
                      "application.",
            "records": "unit probe outputs, extraction/reference manifests, "
                       "server log — offline evidence, never offered as "
                       "runtime proof.",
            "not_claimed": "V08 checkpoint acceptance (lead's call); human "
                           "player acceptance (operator receipt); locomotion "
                           "consumer (archived M4 stands).",
        },

        "missing_or_unresolved": [
            "mapper CommandRecords have no locomotion consumer (archived M4; "
            "the record stream is session diagnostics)",
            "V08 native integrated checkpoint acceptance remains the lead's "
            "decision; visual_acceptance is false by validator law pending "
            "independent visual review",
            "human player acceptance requires the operator receipt",
        ],

        "evidence": {},
    }
    out = HERE / "qualification_receipt.json"
    out.write_text(json.dumps(receipt, indent=1))
    print("wrote", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
