# grasp_screen_v22.py - the GRASP-CANDIDATES v2.2 CHEAP GEOMETRIC SCREEN
# (POSTURE VARIATION: cmc_flexion x mp_flexion scan within the certified
# ranges, at the sealed v2.1 placement solve - the ladder's declared next
# candidate after v2.1 rejected).
#
# FROZEN LAW:
#   1. the COMMITTED prereg (commit 655047b466f5d959e065252670bd275153a4d775,
#      bytes e5bfa3cd32d26785bdcd7441f6af720fdc4a561938ff1c8de3f21dd7a6545106)
#      - the ladder law authorizing v2.2 and its scope (cmc/mp flexion);
#   2. V2_2_ADDENDUM.md, sha256
#      cf7da1a8cc75f522acaa958045ce1977e12f37187211db6980c48f4f1a7c90f4
#      - the concrete frozen grid (this code pins it and refuses on drift).
#
# Declared construction (addendum): 25 postures (cmc_flexion x mp_flexion at
# certified-range fractions {0.05, 0.275, 0.5, 0.725, 0.95}, all other joints
# at the sealed q_c values); stage 1 coarse theta (every 8th of 720) x the
# v2.1 phi grid x 2 mirrors = 1,440 axes/posture; stage 2 = full-resolution
# re-run (11,520 axes) ONLY for postures with >= 1 stage-1 S0-survivor.
# Screens/caps/pad gate IDENTICAL to sealed v2.1. Predictions V2.2-P1/P2 and
# the EXHAUSTED law are frozen in the addendum.
#
# REUSED: the merged instrument (unmodified), the v2.0 module (model build,
# light gate, posture prep, sound vertex scan, exact predicate), the v2.1
# module (axis construction, two-contact solve, per-axis screen). Serial,
# deterministic, stdlib-only.

import hashlib
import json
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import instrument_v2 as iv
import grasp_screen as gs
import grasp_screen_v21 as v21

PREREG_COMMIT = v21.PREREG_COMMIT
PREREG_SHA256 = v21.PREREG_SHA256
INSTRUMENT_PREREG_NAME = v21.INSTRUMENT_PREREG_NAME
INSTRUMENT_PREREG_SHA256 = v21.INSTRUMENT_PREREG_SHA256
CONTROL_TABLE_NAME = v21.CONTROL_TABLE_NAME
CONTROL_TABLE_SHA256 = v21.CONTROL_TABLE_SHA256
INSTRUMENT_SHA256 = v21.INSTRUMENT_SHA256

ADDENDUM_SHA256 = (
    "cf7da1a8cc75f522acaa958045ce1977e12f37187211db6980c48f4f1a7c90f4")
ADDENDUM_NAME = "V2_2_ADDENDUM.md"

THETA_STRIDE = 8                     # stage-1 coarse theta (720/8 = 90)
RANGE_FRACTIONS = (0.05, 0.275, 0.5, 0.725, 0.95)
SCAN_JOINTS = ("cmc_flexion", "mp_flexion")


def sha_of(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def canonical(x):
    return json.dumps(x, indent=1, sort_keys=True)


def build_posture_grid(model):
    """The 25 frozen postures: grid values computed FROM the parsed
    certified ranges at run; refusal if any value leaves the range."""
    bodies, joints_by_name = model[0], model[1]
    base = {}
    for jn in joints_by_name:
        base[jn] = iv.Q_C_PRIMARY.get(jn, 0.0)
    grid = []
    recs = {}
    for jn in SCAN_JOINTS:
        for bname in bodies:
            for (jn2, _ax, rng) in bodies[bname]["joints"]:
                if jn2 == jn:
                    recs[jn] = (bname, rng)
    if len(recs) != len(SCAN_JOINTS):
        iv.refuse("input_pin_missing", "scan joint missing from model")
    values = {}
    for jn in SCAN_JOINTS:
        _b, (lo, hi) = recs[jn]
        vals = []
        for f in RANGE_FRACTIONS:
            v = lo + f * (hi - lo)
            if v < lo - 1e-12 or v > hi + 1e-12:
                iv.refuse("posture_outside_certified_ranges",
                          "%s %r outside %r" % (jn, v, (lo, hi)))
            vals.append(v)
        values[jn] = vals
    for i, cf in enumerate(values["cmc_flexion"]):
        for j, mf in enumerate(values["mp_flexion"]):
            q = dict(base)
            q["cmc_flexion"] = cf
            q["mp_flexion"] = mf
            grid.append(dict(pid="P%02d_cmc%d_mp%d" % (i * 5 + j, i, j),
                             q=q,
                             cmc_flexion=cf, mp_flexion=mf))
    return grid


def screen_coarse(prep, s1_clock, phi_grid):
    counters = dict(
        axes_total=(720 // THETA_STRIDE) * len(phi_grid) * 2,
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
    for k in range(0, 720, THETA_STRIDE):
        for phi_rad in phi_grid:
            for mirror in (0, 1):
                rej, surv, padf = v21.screen_axis_v21(
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
                clearance_by_bone=dict(sorted(prep.clearance_by_bone.items())),
                survivors=survivors,
                pad_gate_failed=pad_failed,
                rejects=rejects,
                coverage_ok=coverage_ok,
                determinism_slice=prep.det_slice)


def pipeline():
    # ---- identity gates ----
    if gs.N_THETA != v21.N_THETA:
        iv.refuse("module_constant_drift", "gs.N_THETA vs v21.N_THETA")
    if v21.N_THETA != 720:
        iv.refuse("v21_constant_drift", "v21.N_THETA must be 720")
    psha = sha_of(os.path.join(HERE, "PREREGISTRATION.md"))
    if psha != PREREG_SHA256:
        iv.refuse("preregistration_sha_mismatch", psha)
    asha = sha_of(os.path.join(HERE, ADDENDUM_NAME))
    if asha != ADDENDUM_SHA256:
        iv.refuse("addendum_sha_mismatch", asha)
    ipsha = sha_of(os.path.join(HERE, INSTRUMENT_PREREG_NAME))
    if ipsha != INSTRUMENT_PREREG_SHA256:
        iv.refuse("instrument_preregistration_sha_mismatch", ipsha)
    isha = sha_of(os.path.join(HERE, "instrument_v2.py"))
    if isha != INSTRUMENT_SHA256:
        iv.refuse("instrument_copy_mismatch", isha)
    table_path = os.path.join(HERE, CONTROL_TABLE_NAME)
    tsha = sha_of(table_path)
    if tsha != CONTROL_TABLE_SHA256:
        iv.refuse("control_input_table_mismatch", tsha)
    gate, _mut, _stl_files, _bounds = iv.run_input_gate(
        os.path.join(HERE, INSTRUMENT_PREREG_NAME))
    gs.emit("=" * 78)
    gs.emit("GATE. prereg COMMIT %s bytes %s MATCH; addendum %s MATCH;"
            " instrument copy %s MATCH; control table MATCH; inherited"
            " input gate ok=%s pins=%d."
            % (PREREG_COMMIT[:12], psha[:16], asha[:16], isha[:16],
               gate["ok"], len(gate["pins"])))
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
            " and chord %r." % wit["chord"])
    phi_grid = [math.radians(d) for d in v21.PHI_GRID_DEG]
    grid = build_posture_grid(model)
    gs.emit("V2.2 GRID: %d postures (cmc_flexion x mp_flexion at range"
            " fractions %r); stage-1 axes/posture = %d."
            % (len(grid), RANGE_FRACTIONS,
               (720 // THETA_STRIDE) * len(phi_grid) * 2))
    receipt = dict(
        schema="chimera.grasp_candidates.screen_v22.v1",
        task="GRASP-CANDIDATES-20261002 v2.2 cheap screen (posture"
             " variation: cmc_flexion x mp_flexion scan at the sealed v2.1"
             " placement solve; ladder branch after the v2.1 rejection)",
        lane="E:/ChimeraWork/monkey-coordination/grasp-candidates/",
        prereg_commit=PREREG_COMMIT,
        preregistration_sha256=psha,
        addendum_sha256=asha,
        instrument_copy_sha256=isha,
        instrument_preregistration_sha256=ipsha,
        control_input_table_sha256=tsha,
        frozen_constants=dict(tau=iv.TAU, pi_c=iv.PI_C, r_joint=iv.R_JOINT,
                              scale=iv.SCALE, trunk_r=iv.TRUNK_R,
                              trunk_h=iv.TRUNK_H,
                              n_theta=720, theta_stride=THETA_STRIDE,
                              phi_grid_deg=list(v21.PHI_GRID_DEG),
                              range_fractions=list(RANGE_FRACTIONS),
                              scan_joints=list(SCAN_JOINTS),
                              tau_bracket=v21.TAU_BRACKET,
                              bisect_iters=v21.BISECT_ITERS,
                              tau_scan_samples=v21.TAU_SCAN_SAMPLES,
                              s_bracket=[gs.S_BRACKET_LO, gs.S_BRACKET_HI],
                              cap_s1_per_posture=gs.CAP_S1_PER_POSTURE,
                              s1_time_budget_s=gs.S1_TIME_BUDGET_S,
                              pad_gate_min_cos=v21.PAD_GATE_MIN_COS),
        input_gate=gate,
        witness_identity=wit,
        light_gate=lg,
        posture_grid=[dict(pid=g["pid"], cmc_flexion=g["cmc_flexion"],
                           mp_flexion=g["mp_flexion"]) for g in grid],
        postures={},
    )
    s1_clock = [0.0]
    hits = []
    for g in grid:
        prep = v21.prep_posture_v21(model, g["q"],
                                    ("distal_thumb", "distph3"))
        gs.emit("-" * 78)
        gs.emit("POSTURE %s cmc_flexion=%r mp_flexion=%r pair=(distal_thumb,"
                " distph3) chord(T1 origins)=%r m."
                % (g["pid"], g["cmc_flexion"], g["mp_flexion"], prep.chord))
        res = screen_coarse(prep, s1_clock, phi_grid)
        res["chord_t1"] = prep.chord
        reachable = res["counters"]["axes_total"] - \
            res["counters"]["s0_reject_no_approach"]
        res["reachable_axes"] = reachable
        res["tip_deep_share_reachable"] = (
            res["counters"]["s0_reject_tip_deep"] / reachable
            if reachable > 0 else None)
        receipt["postures"][g["pid"]] = res
        gs.emit("  counters: %s" % json.dumps(res["counters"],
                                              sort_keys=True))
        gs.emit("  coverage_ok=%s s0_survivors=%d survivors=%d"
                " tip_deep_share=%s"
                % (res["coverage_ok"], res["counters"]["s0_survivors"],
                   res["counters"]["survivors"],
                   repr(res["tip_deep_share_reachable"])))
        if not res["coverage_ok"]:
            iv.refuse("coverage_arithmetic_broken", g["pid"])
        if res["counters"]["s0_survivors"] >= 1:
            hits.append(g)
    gs.emit("=" * 78)
    gs.emit("STAGE 1 COMPLETE: %d/%d postures with >= 1 S0-survivor."
            % (len(hits), len(grid)))
    # stage 2: full-resolution re-run, hits only
    for g in hits:
        prep = v21.prep_posture_v21(model, g["q"],
                                    ("distal_thumb", "distph3"))
        gs.emit("STAGE 2 POSTURE %s (full 720-theta resolution)." % g["pid"])
        res = v21.screen_posture_v21(prep, s1_clock, phi_grid)
        res["chord_t1"] = prep.chord
        receipt["postures"][g["pid"]]["stage2"] = res
        gs.emit("  stage2 counters: %s" % json.dumps(res["counters"],
                                                     sort_keys=True))
        gs.emit("  stage2 coverage_ok=%s s0_survivors=%d survivors=%d"
                % (res["coverage_ok"], res["counters"]["s0_survivors"],
                   res["counters"]["survivors"]))
        if not res["coverage_ok"]:
            iv.refuse("coverage_arithmetic_broken", g["pid"] + ":stage2")
    # predictions
    stage1_hit = len(hits) >= 1
    shares = [receipt["postures"][g["pid"]]["tip_deep_share_reachable"]
              for g in grid]
    shares = [s for s in shares if s is not None]
    best_share = min(shares) if shares else None
    receipt["v22_predictions"] = dict(
        P1_any_stage1_hit=bool(stage1_hit),
        P2_best_tip_deep_share_below_50pct=bool(best_share is not None
                                                and best_share < 0.5),
        best_tip_deep_share_reachable=best_share,
    )
    gs.emit("V2.2 P1 any stage-1 hit: %s; P2 best tip-deep share: %s"
            % (stage1_hit, repr(best_share)))
    # determinism slice: re-solve recorded cells of the first posture only
    # (bounded); cells were recorded per posture by the v2.1 recorder
    first_pid = grid[0]["pid"]
    if receipt["postures"][first_pid]["determinism_slice"]:
        g0 = grid[0]
        prep = v21.prep_posture_v21(model, g0["q"],
                                    ("distal_thumb", "distph3"))
        det_ok = True
        det_cells = 0
        for (k, phi_rad, mirror, u, s_star, tau_star) in \
                receipt["postures"][first_pid]["determinism_slice"]:
            u2, w2, _th, e2, c2m, s2m = v21.axis_v21(prep, k, phi_rad,
                                                     mirror)
            sol2 = v21.solve_two_contact(prep, e2, w2, c2m, s2m)
            if sol2 is None:
                same = (s_star is None and tau_star is None) and \
                    (canonical([u2]) == canonical([u]))
            else:
                s2, t2 = sol2
                same = (canonical([u2, s2, t2])
                        == canonical([u, s_star, tau_star]))
            det_ok = det_ok and same
            det_cells += 1
        receipt["determinism_slice"] = dict(posture=first_pid,
                                            cells=det_cells, ok=det_ok)
        gs.emit("DETERMINISM SLICE (%s): %d cells byte-identical = %s"
                % (first_pid, det_cells, det_ok))
    exact_total = 0
    s0_total = 0
    for pid in sorted(receipt["postures"]):
        r = receipt["postures"][pid]
        s0_total += r["counters"]["s0_survivors"]
        exact_total += r["counters"]["survivors"]
        if "stage2" in r:
            exact_total += r["stage2"]["counters"]["survivors"]
    receipt["totals"] = dict(stage1_s0_survivors=s0_total,
                             exact_survivors_all_stages=exact_total)
    if exact_total > 0:
        receipt["verdict"] = "SURVIVORS_PRESENT_SWEEP_AND_FORCE_BRANCH"
    elif s0_total > 0:
        receipt["verdict"] = "S0_SURVIVORS_ONLY_NO_EXACT_SURVIVOR"
    else:
        receipt["verdict"] = "ZERO_SURVIVORS_LADDER_EXHAUSTED"
    receipt["s1_cumulative_clock_s"] = s1_clock[0]
    gs.emit("=" * 78)
    gs.emit("VERDICT: %s (stage1_s0=%d exact_all_stages=%d)"
            % (receipt["verdict"], s0_total, exact_total))
    return receipt


def main():
    outdir = os.environ.get("CHIMERA_OUTPUT_DIR", "outputs")
    os.makedirs(outdir, exist_ok=True)
    try:
        receipt = pipeline()
        text = "\n".join(gs._report) + "\n"
    except iv.GateRefusal as exc:
        with open(os.path.join(outdir, "grasp_screen_v22_gate_receipt.json"),
                  "w", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(dict(
                schema="chimera.grasp_candidates.gate.v1",
                ok=False, refusal=exc.detail), indent=1) + "\n")
        print("REFUSAL: %s" % exc.detail, flush=True)
        raise SystemExit(3)
    with open(os.path.join(outdir, "grasp_screen_v22_receipt.json"), "w",
              encoding="utf-8", newline="\n") as fh:
        fh.write(canonical(receipt) + "\n")
    with open(os.path.join(outdir, "grasp_screen_v22_report.txt"), "w",
              encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    raise SystemExit(0)


if __name__ == "__main__":
    main()
