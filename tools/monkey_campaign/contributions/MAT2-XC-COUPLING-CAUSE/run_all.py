#!/usr/bin/env python3
"""MAT2-XC-COUPLING-CAUSE: the gated run (one sealed command).

Stages (each must exit green; the first failure stops the driver):
  1. unit_battery   (run_checks.py: the prereg/schedule/record checks)
  2. arms           (A, then D, then E with the E3 selection recorded
                     before its physics; EVERY arm re-executed once —
                     the frozen F1 determinism law)
  3. determination  (the frozen matrix; the four named verdicts ONLY)
  4. report         (generation + lint; every load-bearing number traced
                     to a receipt)

Exit: 0 green / the failing stage's exit code.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CARD = "MAT2-XC-COUPLING-CAUSE"
STORE = Path("E:/ChimeraWork/monkey-coordination/evidence-store")
A12_JOB = Path("E:/ChimeraWork/task-runner/results/"
               "ca111cdc917e420eb78c41339d88c41b")


def out_dir():
    out = os.environ.get("CHIMERA_OUTPUT_DIR")
    require(out is not None, "output_dir_undeclared")
    Path(out).mkdir(parents=True, exist_ok=True)
    return Path(out)


def require(condition, code):
    if not condition:
        raise RuntimeError("REFUSAL:" + str(code))


def write_json(path, obj):
    path.write_bytes(json.dumps(obj, ensure_ascii=False, sort_keys=True,
                                separators=(",", ":"), allow_nan=False,
                                indent=1).encode("utf-8") + b"\n")


# ---------------------------------------------------------------- stage 1
def stage_unit_battery() -> int:
    spec = importlib.util.spec_from_file_location(
        "xc_checks", HERE / "run_checks.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["xc_checks"] = mod
    spec.loader.exec_module(mod)
    return mod.main()


# ---------------------------------------------------------------- stage 2
def stage_arms() -> dict:
    import verify_inputs_xc as vxc
    import probe_driver_xc as pd

    require(vxc.main() == 0, "pin_layer_main_refused")
    vxc.extract_execution_tree()
    vxc.w10_layer()
    vxc.u07_layer()
    # controls_harness resolves from THIS card's byte-verified extraction
    u07_dir = str(vxc.PINNED_ROOT.joinpath(*vxc.U07_DIR))
    while u07_dir in sys.path:
        sys.path.remove(u07_dir)
    sys.path.insert(0, u07_dir)

    import command_model as cm         # W10 bytes (the frozen script law)
    import walking_demo as wd          # W10 bytes (its dir is sys.path[0])
    it, ad = vxc.load_accepted_trace_modules()

    # the certified line's own gate (W10's sealed code, unmodified)
    (cert, _req, allow, bundle, build_id, params, scene_const, bounds,
     gate) = wd.gate_and_load()
    require(allow["decision"] == "ALLOW", "deploy_gate_not_allow")
    import controls_harness as ch      # certified U07 bytes
    require(build_id == ch.BUILD_ID, "build_id_mismatch:" + str(build_id))
    adapter = cm.CommandAdapter(bundle["manifest"], scene_const)
    ad_adapter = {"trace_modules": (it, ad),
                  "expiry_state": adapter.expiry_state,
                  "project": adapter.project,
                  "expired": adapter.expired}

    findings = []
    arms = {}

    def run(tag, **kw):
        res = pd.run_arm(tag, ad_adapter, build_id, params, **kw)
        arms[tag] = res
        return res

    def run_det(tag, **kw):
        """One arm + its F1 determinism re-execution (frozen group B)."""
        r1 = run(tag + "_r1", **kw)
        r2 = run(tag + "_r2", **kw)
        require(r1["window_rows"] == r2["window_rows"]
                and r1["final_state_sha256"] == r2["final_state_sha256"],
                "F1_determinism_breach:" + tag)
        return r1

    # ---- arm group A: the harness-form gate (controls, both forms)
    a1a = run_det("A1a_cut_control", form="cut")
    a1b = run_det("A1b_full_control", form="full")
    a1_pass = a1a["window_rows"] == a1b["window_rows"]
    a1_rows = offset_rows(a1b["window_rows"], a1a["window_rows"])
    if not a1_pass:
        findings.append({"finding": "xc_harness_form_offset",
                         "detail": "the two harness forms' CONTROL arms "
                                   "differ over the same pinned bytes",
                         "offset_rows": a1_rows})

    # ---- A2: the offset detector on the SEALED records (no new physics)
    a12_rec = json.loads((A12_JOB / "artifacts" / "outputs"
                          / "driver_pair_P01_BRAKE-SHORT.json").read_bytes())
    x05_rec = json.loads((STORE / "MAT2-X05" / "numerical"
                          / "driver_pair_P01_BRAKE-SHORT.json").read_bytes())
    a2_rows = offset_rows(x05_rec["window_rows"]["B"],
                          a12_rec["window_rows"]["B"])
    # the phases are float32 values: the exact-symmetric law is
    # evaluated at the float32 grid (tolerance 1e-8; disclosed).
    TOL = 1e-8
    a2_exact = all(abs(r["d_left"] - 0.2) <= TOL
                   and abs(r["d_right"] + 0.2) <= TOL
                   for r in a2_rows)
    if not a2_exact:
        findings.append({"finding": "xc_offset_pattern_deviation",
                         "detail": "the cross-line control offset is the "
                                   "exact symmetric +0.2/-0.2 through the "
                                   "pre-A-press rows then ratchets in "
                                   "exact wrap quantums after the script's "
                                   "A-press region",
                         "offset_rows": a2_rows})

    # ---- arm group D: the regime depth sweep (form 'full')
    d_pairs = {}
    for cls, ns in (("BRAKE-SHORT", [1, 3, 5, 7, 9]),
                    ("BRAKE-LONG", [2, 4, 6, 8, 10]),
                    ("BRAKE-DEEP", [11, 12, 13, 14])):
        for n in ns:
            d_pairs["%s|%d" % (cls, n)] = run_release_pair(
                run_det, pd, cls, n)

    # D0 control + replication (the prereg's control replication)
    run_det("D0_full_control", form="full")

    # replication anchors: D1/D2 A+B rows == the sealed x05 P01/P02 rows
    repl = replication_anchors(d_pairs, findings)

    # ---- arm group E: the mechanism channel (form 'full')
    e = stage_e(run_det, pd, d_pairs, findings)

    # ---- the window robustness scan (analysis-only, same rows)
    scan = window_scan(pd, d_pairs)

    receipt = {
        "schema": "chimera.xc.arms_receipt.v1",
        "card": CARD, "base": vxc.BASE_SHA,
        "build_id": build_id,
        "forms": {"a1_pass_bit_identity": a1_pass,
                  "a1_offset_rows": a1_rows,
                  "a2_sealed_offset_rows": a2_rows,
                  "a2_pattern_exact_symmetric_020": a2_exact,
                  "a1_offset_equals_a2_offset": offset_seqs_equal(
                      a1_rows, a2_rows)},
        "arms": {k: summarize(v) for k, v in arms.items()},
        "d_pairs": d_pairs,
        "replication_anchors": repl,
        "e": e,
        "window_scan": scan,
        "findings": findings,
    }
    return receipt


def offset_seqs_equal(rows_a, rows_b, tol=1e-8):
    """Per-row equality of two offset sequences at the float32 grid."""
    if len(rows_a) != len(rows_b):
        return False
    return all(ra["tick"] == rb["tick"]
               and abs(ra["d_left"] - rb["d_left"]) <= tol
               and abs(ra["d_right"] - rb["d_right"]) <= tol
               for ra, rb in zip(rows_a, rows_b))


def run_release_pair(run_det, pd, cls, n):
    t0 = pd.t_in(n)
    delta = pd.CLASS_REPRESS[cls]
    a = run_det("D_%s_n%d_A" % (cls, n), form="full",
                probe={"kind": "release-w", "t_in": t0, "repress": delta})
    b = run_det("D_%s_n%d_B" % (cls, n), form="full")
    ident, first_div = pd.window_identity(a["window_rows"], b["window_rows"])
    vdiv = pd.v_divergence_count(a["window_rows"], b["window_rows"])
    return {"cls": cls, "n": n, "t_in": t0, "repress": delta,
            "identity": ident, "first_divergence_tick": first_div,
            "v_divergence": vdiv,
            "band_A": pd.band(a["window_rows"]),
            "band_B": pd.band(b["window_rows"]),
            "A": a, "B": b}


def stage_e(run_det, pd, d_pairs, findings):
    # E2: the S-press class verbatim, 5 pairs (controls: the D B arms)
    e2 = []
    for n in (1, 2, 3, 4, 5):
        t0 = pd.t_in(n)
        a = run_det("E2_pressS_n%d_A" % n, form="full",
                    probe={"kind": "press-s", "t_in": t0,
                           "hold": pd.E2_HOLD_TICKS})
        # the D control at the SAME n (classes interleave by parity; the
        # full-form controls are bit-identical across pairs — asserted by
        # the per-pair B2 receipts — so the pairing is sound and honest).
        cls_n = "BRAKE-SHORT" if n % 2 == 1 else "BRAKE-LONG"
        b = d_pairs["%s|%d" % (cls_n, n)]["B"]
        ident, first_div = pd.window_identity(a["window_rows"],
                                              b["window_rows"])
        vdiv = pd.v_divergence_count(a["window_rows"], b["window_rows"])
        e2.append({"n": n, "identity": ident,
                   "first_divergence_tick": first_div,
                   "v_divergence": vdiv,
                   "band_A": pd.band(a["window_rows"]),
                   "inert": vdiv == 0,
                   "A": a})
    e2_inert = all(r["inert"] for r in e2)
    # E1 = the D SHORT arm (shared; no duplicate run)
    e1_band = d_pairs["BRAKE-SHORT|1"]["band_A"]["min_com_v"]
    # E3 selection: the smallest listed hold duration whose achieved
    # min com_v is within +/-0.01 m/s of E1's, chosen from RECORDED rows
    # BEFORE any E3 physics; other durations are recorded by running the
    # E2-variant probes ONLY when E2@150 is not inert.
    listed = [50, 100, 150, 200, 300, 450]
    achieved = {}
    if not e2_inert:
        for hold in listed:
            if hold == 150:
                achieved[hold] = e2[0]["band_A"]["min_com_v"]
                continue
            a = run_det("E3sel_pressS_hold%d" % hold, form="full",
                        probe={"kind": "press-s",
                               "t_in": pd.t_in(1), "hold": hold})
            achieved[hold] = pd.band(a["window_rows"])["min_com_v"]
    matched = [h for h in listed if abs(achieved.get(h, 1e9) - e1_band)
               <= 0.01]
    e3 = {"status": "NOT_ATTEMPTED" if e2_inert else (
        "MATCHED" if matched else "NOT_ACHIEVABLE"),
          "e1_min_com_v": e1_band, "achieved_by_hold": achieved,
          "matched_holds": matched, "e2_inert": e2_inert}
    if e3["status"] == "NOT_ACHIEVABLE":
        findings.append({"finding": "xc_band_match_unachievable",
                         "detail": "no listed S-press hold duration "
                                   "reaches E1's achieved band; the "
                                   "matched-band matrix rows are not "
                                   "claimable"})
    if e3["status"] == "MATCHED":
        hold = matched[0]
        a = run_det("E3_pressS_hold%d" % hold, form="full",
                    probe={"kind": "press-s", "t_in": pd.t_in(1),
                           "hold": hold})
        b = d_pairs["BRAKE-SHORT|1"]["B"]
        ident, first_div = pd.window_identity(a["window_rows"],
                                              b["window_rows"])
        e3.update({"E3_identity": ident,
                   "E3_first_divergence_tick": first_div,
                   "E3_v_divergence": pd.v_divergence_count(
                       a["window_rows"], b["window_rows"]),
                   "E3_band": pd.band(a["window_rows"])})
    return {"e2": e2, "e3": e3}


X05_SEALED = {
    "P01_BRAKE-SHORT": (
        STORE / "MAT2-X05" / "numerical" / "driver_pair_P01_BRAKE-SHORT.json",
        "31e4d11eec3f867ab044ddd97b6de1c54a5e82daf4fd055ecad696913eb3e918"),
    "P02_BRAKE-LONG": (
        STORE / "MAT2-X05" / "numerical" / "driver_pair_P02_BRAKE-LONG.json",
        "e05620c8999ffeca7840d4b932992cad7c4d489b01d769f79a88b4dee859231e"),
}


def replication_anchors(d_pairs, findings):
    """D1/D2 (n=1 SHORT, n=2 LONG) window rows == the sealed x05 P01/P02
    rows (exact float equality; each sealed record loaded BY NAME and
    sha-asserted) — proves THIS materialization identity is the sealed X05
    identity."""
    import hashlib
    out = {}
    for key, (name, (path, expected)) in (
            ("BRAKE-SHORT|1", ("P01_BRAKE-SHORT",
                               X05_SEALED["P01_BRAKE-SHORT"])),
            ("BRAKE-LONG|2", ("P02_BRAKE-LONG",
                              X05_SEALED["P02_BRAKE-LONG"]))):
        got = hashlib.sha256(path.read_bytes()).hexdigest()
        require(got == expected, "anchor_pin_mismatch:" + name)
        sealed = json.loads(path.read_bytes())
        mine = d_pairs[key]
        same_a = rows_equal(mine["A"]["window_rows"],
                            sealed["window_rows"]["A"])
        same_b = rows_equal(mine["B"]["window_rows"],
                            sealed["window_rows"]["B"])
        out[name] = {"A_exact": same_a, "B_exact": same_b}
        if not (same_a and same_b):
            findings.append({"finding": "xc_replication_mismatch",
                             "detail": name + ": the sealed x05 rows did "
                             "not reproduce exactly on this "
                             "materialization"})
    return out


def rows_equal(mine, sealed):
    if len(mine) != len(sealed):
        return False
    for m, s in zip(mine, sealed):
        for k in ("tick", "phase_left", "phase_right", "com_v_m_s",
                  "com_x_m", "state_sha256"):
            if m[k] != s[k]:
                return False
    return True


def offset_rows(rows_x, rows_y):
    """Per-row phase offsets x-minus-y (the frozen A2 detector form)."""
    return [{"tick": rx["tick"],
             "d_left": rx["phase_left"] - ry["phase_left"],
             "d_right": rx["phase_right"] - ry["phase_right"]}
            for rx, ry in zip(rows_x, rows_y)]


def summarize(arm):
    return {k: arm[k] for k in ("arm", "form", "horizon", "decision_count",
                                "sink_record_count", "probe_events",
                                "final_state_sha256", "expiry_reverts")}


def window_scan(pd, d_pairs):
    """The frozen robustness scan: identity counts over window starts
    {4365, 4380, 4395} on the SAME recorded rows (analysis-only)."""
    out = {}
    for key, pair in d_pairs.items():
        per_start = {}
        for start in (4365, 4380, 4395):
            ra = [r for r in pair["A"]["window_rows"] if r["tick"] >= start]
            rb = [r for r in pair["B"]["window_rows"] if r["tick"] >= start]
            ident, _ = pd.window_identity(ra, rb)
            per_start[str(start)] = ident
        out[key] = per_start
    return out


# ---------------------------------------------------------------- stage 3
def stage_determination(arms_receipt) -> dict:
    a1_pass = arms_receipt["forms"]["a1_pass_bit_identity"]
    a2_exact = arms_receipt["forms"]["a2_pattern_exact_symmetric_020"]
    a1_eq_a2 = arms_receipt["forms"]["a1_offset_equals_a2_offset"]
    d = arms_receipt["d_pairs"]
    e = arms_receipt["e"]
    findings = arms_receipt["findings"]

    classes = ("BRAKE-SHORT", "BRAKE-LONG", "BRAKE-DEEP")
    idents = {c: [d[k]["identity"] for k in sorted(d)
                  if k.startswith(c + "|")] for c in classes}
    d_diverges = any(i < 21 for c in classes for i in idents[c])
    d_all_ident = all(i == 21 for c in classes for i in idents[c])
    e2_all_ident = all(r["identity"] == 21 for r in e["e2"])
    e3 = e["e3"]
    firsts = {c: sorted(d[k]["first_divergence_tick"]
                        for k in sorted(d)
                        if k.startswith(c + "|")
                        and d[k]["first_divergence_tick"] is not None)
              for c in classes}
    onset = (d_diverges
             and all(firsts[c] for c in classes)
             and min(firsts["BRAKE-SHORT"]) < min(firsts["BRAKE-LONG"])
             < min(firsts["BRAKE-DEEP"]))
    repl_ok = all(v["A_exact"] and v["B_exact"]
                  for v in arms_receipt["replication_anchors"].values())

    verdict = "CAUSE_NOT_ISOLATED"
    basis = []
    if (a1_pass and e3["status"] == "MATCHED" and e2_all_ident
            and e3.get("E3_identity", 0) == 21 and d_diverges):
        verdict = "ISOLATED_COMMAND_CHANNEL"
        basis.append("P-COMMAND: A1 pass; E2/E3 identity 21/21 while the "
                     "release arms diverge; bands matched")
    elif (a1_pass and onset and e3["status"] == "MATCHED"
            and e3.get("E3_identity", 21) != 21):
        verdict = "ISOLATED_VELOCITY_COUPLING"
        basis.append("P-VELOCITY: onset tracks the band monotonically and "
                     "replicates in the matched S-press channel")
    elif (not a1_pass) and a1_eq_a2 and d_all_ident and e2_all_ident:
        verdict = "ISOLATED_HARNESS_SCENE"
        basis.append("P-HARNESS: the A1 offset replicates the sealed "
                     "cross-line pattern; every depth/channel shows phase "
                     "identity")
    elif a1_pass and d_all_ident and e2_all_ident:
        verdict = "ISOLATED_HARNESS_SCENE"
        basis.append("P-HARNESS: forms bit-identical; every depth/channel "
                     "shows phase identity")
    else:
        basis.append("no frozen matrix row's preconditions held at "
                     "isolated-cause strength")
    if verdict == "CAUSE_NOT_ISOLATED":
        if not repl_ok:
            basis.append("the x05 replication anchors did NOT reproduce "
                         "(the materialization identity differs from the "
                         "sealed X05 identity)")
        if (not a1_pass) and a1_eq_a2:
            basis.append("the cross-line control offset ISOLATES to the "
                         "harness form (the a12 line's post-4350 script "
                         "cut) as a SUB-FINDING; the total determination "
                         "stays capped per the frozen matrix")
    receipt = {"schema": "chimera.xc.determination.v1",
               "card": CARD,
               "verdict": verdict,
               "basis": basis,
               "inputs": {"a1_pass": a1_pass,
                          "a2_exact_020": a2_exact,
                          "a1_equals_a2": a1_eq_a2,
                          "identities": idents,
                          "first_divergence": firsts,
                          "onset_monotone": bool(onset),
                          "e2_all_ident": e2_all_ident,
                          "e3_status": e3["status"],
                          "replication_anchors_ok": repl_ok,
                          "findings": [f["finding"] for f in findings]},
               "ruling": "Do not claim that gait responds to speed until a "
                         "controlled comparison isolates that causal "
                         "relationship.",
               "payoff": ("the certified-line coupling follow-up becomes "
                          "implementable" if verdict ==
                          "ISOLATED_VELOCITY_COUPLING" else
                          "the X05 observational finding stays honestly "
                          "observational; the coupling card closes "
                          "absent-with-cause" if verdict ==
                          "ISOLATED_HARNESS_SCENE" else
                          "the coupling card closes absent-UNVERIFIED with "
                          "these arms recorded as the named follow-up")}
    return receipt


# ---------------------------------------------------------------- stage 4
def stage_report(arms_receipt, determination) -> int:
    spec = importlib.util.spec_from_file_location(
        "xc_report", HERE / "make_report.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["xc_report"] = mod
    spec.loader.exec_module(mod)
    return mod.main(arms_receipt, determination)


# ---------------------------------------------------------------- driver
def main(argv) -> int:
    stage = argv[1] if len(argv) > 1 else "all"
    determination = None
    if stage in ("all", "checks"):
        rc = stage_unit_battery()
        require(rc == 0, "unit_battery_failed")
        print("stage unit_battery: GREEN")
        if stage == "checks":
            return 0
    if stage in ("all", "arms"):
        arms_receipt = stage_arms()
        write_json(out_dir() / "arms_receipt.json", arms_receipt)
        print("stage arms: %d arms, %d findings"
              % (len(arms_receipt["arms"]),
                 len(arms_receipt["findings"])))
        if stage == "arms":
            return 0
    if stage in ("all", "determine"):
        arms_receipt = json.loads(
            (out_dir() / "arms_receipt.json").read_bytes())
        determination = stage_determination(arms_receipt)
        write_json(out_dir() / "determination_receipt.json", determination)
        print("stage determination: %s" % determination["verdict"])
        if stage == "determine":
            return 0
    if stage in ("all", "report"):
        arms_receipt = json.loads(
            (out_dir() / "arms_receipt.json").read_bytes())
        determination = json.loads(
            (out_dir() / "determination_receipt.json").read_bytes())
        rc = stage_report(arms_receipt, determination)
        require(rc == 0, "report_stage_failed")
        print("stage report: GREEN")
        if stage == "report":
            return 0
    summary = {"schema": "chimera.xc.result.v1", "card": CARD,
               "pass": True,
               "verdict": (determination["verdict"] if determination
                           else "stage_only:" + stage)}
    write_json(out_dir() / "result.json", summary)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv))
    except RuntimeError as r:
        print(str(r), file=sys.stderr)
        sys.exit(2)
