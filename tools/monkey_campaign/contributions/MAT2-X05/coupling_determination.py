#!/usr/bin/env python3
"""MAT2-X05: the coupling determination, RE-EXECUTED at run (prereg section
0; X-P10).

Inputs: the SEALED attempt-12 driver records of WK-LATENCY-20261002 (job
`ca111cdc917e420eb78c41339d88c41b`, byte-pinned in verify_inputs_x05), which
carry per-tick `phase_left`, `phase_right`, `com_v_m_s`, `com_x_m` for BOTH
arms of the brake pairs over the declared window. The numbers are re-derived
from the pinned bytes at run — never hand-copied — and the declared-absent
disposition is restated with them.

Determination (sealed): the gait phases are IDENTICAL between the brake arm
and the control arm in 42/42 window frames (both depths, all 21 presented
ticks of P01 SHORT and P02 LONG) while the velocity state GENUINELY diverged
in the same frames (com_v differs in 40/42). Therefore the certified scene's
phase oscillators do not consume the measured speed in this regime: there is
NO contact-record basis for a stride-velocity coupling, and any rendered
stride change keyed to velocity would require a phase source OTHER than the
committed row's recorded phase — the forbidden second pose source (X04 P4
law). Disposition: coupling DECLARED ABSENT (absent inventory A1); the
certified-line follow-up (a phase law that consumes the measured speed) is a
RUNTIME change, outside this card's no-runtime-change scope; it requires its
own prereg and card.
"""
from __future__ import annotations

import hashlib
import json


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def derive(driver_records):
    """driver_records: {cls: (P01, 'BRAKE-SHORT') / (P02, 'BRAKE-LONG')}
    dict of loaded driver_pair JSON records (byte-pinned inputs)."""
    out = {"frames_total": 0, "phase_identical_frames": 0,
           "com_v_divergent_frames": 0, "per_depth": {}}
    for cls, d in sorted(driver_records.items()):
        arms = d["window_rows"]
        A, B = arms["A"], arms["B"]
        require_same_ticks(A, B)
        depth = {"frames": len(A), "phase_identical": 0,
                 "com_v_divergent": 0,
                 "com_v_first_A": A[0]["com_v_m_s"],
                 "com_v_last_A": A[-1]["com_v_m_s"],
                 "com_v_last_B": B[-1]["com_v_m_s"],
                 "com_x_travel_A": A[-1]["com_x_m"] - A[0]["com_x_m"],
                 "com_x_travel_B": B[-1]["com_x_m"] - B[0]["com_x_m"],
                 "probe_events": d["probe_events"],
                 "t_in": d["t_in"]}
        for ra, rb in zip(A, B):
            same = (ra["phase_left"] == rb["phase_left"]
                    and ra["phase_right"] == rb["phase_right"])
            depth["phase_identical"] += int(same)
            depth["com_v_divergent"] += int(
                ra["com_v_m_s"] != rb["com_v_m_s"])
        out["frames_total"] += depth["frames"]
        out["phase_identical_frames"] += depth["phase_identical"]
        out["com_v_divergent_frames"] += depth["com_v_divergent"]
        out["per_depth"][cls] = depth
    out["phase_identity"] = "%d/%d" % (out["phase_identical_frames"],
                                       out["frames_total"])
    out["com_v_divergence"] = "%d/%d" % (out["com_v_divergent_frames"],
                                         out["frames_total"])
    out["determination"] = (
        "phases IDENTICAL %s while com_v diverges %s window frames in the "
        "SEALED A12 LINE'S RECORDS: the a12 records show the certified "
        "scene's phase oscillators not consuming the measured speed in "
        "THAT regime" % (out["phase_identity"],
                         out["com_v_divergence"]))
    # R1 (review): the disposition is REGIME-SCOPED. The a12-based
    # determination and THIS card's own run behavior are separate
    # measurements; the run's own divergence is derived in
    # derive_run_phases() and recorded as the named finding
    # x_run_phase_divergence_observed. The deeper question (why the a12
    # records and the X05 run differ) is routed to the Lieutenant for the
    # follow-up card - disclosed, never silently contradicted.
    out["disposition"] = "DECLARED_ABSENT_IN_THE_A12_LINE_REGIME"
    out["scope_note"] = ("regime-scoped: ABSENT in the a12 line's records; "
                         "the X05 run's own phase behavior is a separate "
                         "measurement recorded alongside this "
                         "determination")
    out["follow_up"] = ("a certified-line change in which the scene's phase "
                        "law consumes the measured speed is a RUNTIME "
                        "change outside this card's no-runtime-change "
                        "scope; it requires its own prereg and card; the "
                        "a12-vs-X05 divergence question routes to the "
                        "Lieutenant")
    return out


def derive_run_phases(pairs_window_rows):
    """THE RUN'S OWN phase determination (R1; the honest possibility the
    prereg anticipated): per pair, brake-vs-control phase identity over
    the 21 presented window rows and the first divergent presented tick.
    When the phases DIVERGE in this run, the finding
    `x_run_phase_divergence_observed` is recorded with its census. THE
    CLAIM IS OBSERVATIONAL ONLY: the phases diverge in this run; THE
    CAUSE REMAINS UNVERIFIED (regime, seed, window or mechanism
    differences are candidates; none is isolated). Disclosed alongside
    the a12-based, regime-scoped determination - never silently
    contradicted by it, and never promoted to a causal claim.

    pairs_window_rows: {pair_key: {"A": rows, "B": rows}} with rows
    carrying tick/phase_left/phase_right (the run's own window rows)."""
    out = {"pairs_total": 0, "pairs_with_divergence": 0,
           "identity_counts": {}, "first_divergent_tick": None,
           "law": "the run's own brake-vs-control phase columns over the "
                  "presented window rows; divergence here is a RECORDED "
                  "FINDING (x_run_phase_divergence_observed), never tuned "
                  "and never contradicted by the a12-based determination"}
    for key in sorted(pairs_window_rows):
        A = pairs_window_rows[key]["A"]
        B = pairs_window_rows[key]["B"]
        require_same_ticks(A, B)
        out["pairs_total"] += 1
        ident = 0
        first_div = None
        for ra, rb in zip(A, B):
            same = (ra["phase_left"] == rb["phase_left"]
                    and ra["phase_right"] == rb["phase_right"])
            ident += int(same)
            if not same and first_div is None:
                first_div = int(ra["tick"])
        out["identity_counts"][key] = "%d/%d" % (ident, len(A))
        if first_div is not None:
            out["pairs_with_divergence"] += 1
            if out["first_divergent_tick"] is None                     or first_div < out["first_divergent_tick"]:
                out["first_divergent_tick"] = first_div
    out["run_phase_divergence_observed"] = out["pairs_with_divergence"] > 0
    if out["run_phase_divergence_observed"]:
        out["finding"] = {
            "code": "x_run_phase_divergence_observed",
            "law": "OBSERVATIONAL ONLY: the X05 run's own window rows "
                   "show brake-vs-control phase DIVERGENCE; THE CAUSE "
                   "REMAINS UNVERIFIED (regime, seed, window or mechanism "
                   "differences are candidates; none is isolated). "
                   "Disclosed alongside the a12-based regime-scoped "
                   "determination - the two are separate measurements of "
                   "different runs; the deeper a12-vs-X05 question routes "
                   "to the Lieutenant. The landmark-visibility result "
                   "stands independently of this finding.",
        }
    return out


def require_same_ticks(A, B):
    if len(A) != len(B):
        raise ValueError("window_row_count_mismatch")
    for ra, rb in zip(A, B):
        if ra["tick"] != rb["tick"]:
            raise ValueError("window_tick_mismatch")


def audit_no_velocity_to_stride(contribution_dir):
    """X-P10's structural audit: the contribution contains NO code path from
    velocity to stride/phase rendering. AST walk over every contribution
    module: any call whose target name mentions stride/phase AND whose
    argument names mention com_v/velocity/speed refuses
    (`x05_velocity_to_stride_path`). The render signature admits no such
    channel (render_x05.render_frame_x05 consumes the row via the pinned
    pose law only)."""
    import ast
    from pathlib import Path
    refusals = []
    files = sorted(Path(contribution_dir).glob("*.py"))
    for path in files:
        tree = ast.parse(path.read_bytes().decode("utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            target = ""
            if isinstance(node.func, ast.Attribute):
                target = node.func.attr
            elif isinstance(node.func, ast.Name):
                target = node.func.id
            if not any(k in target.lower()
                       for k in ("stride", "phase")):
                continue
            arg_names = []
            for arg in node.args + [kw.value for kw in node.keywords]:
                if isinstance(arg, ast.Name):
                    arg_names.append(arg.id.lower())
                elif isinstance(arg, ast.Attribute):
                    arg_names.append(arg.attr.lower())
            if any(k in a for a in arg_names
                   for k in ("com_v", "velocity", "speed")):
                refusals.append({"file": path.name, "line": node.lineno,
                                 "call": target})
    if refusals:
        raise ValueError("x05_velocity_to_stride_path:" + repr(refusals[:3]))
    return {"law": "no code path from velocity to stride/phase rendering",
            "files_audited": [p.name for p in files],
            "refusals": refusals}
