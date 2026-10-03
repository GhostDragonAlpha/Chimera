# grasp_screen_digit.py - the GRASP-DIGIT-SCAN DIGIT-SIDE JOINT SCAN
# (the exhausted ladder's named unscanned DOF direction: the opposing-digit
# clearance rejection class), at the sealed v2.1 placement solve.
#
# FROZEN LAW:
#   1. the COMMITTED prereg (commit
#      1a567c39164d4b44d9fa0efb048429f8b3d03fe8,
#      origin/review/GRASP-DIGIT-SCAN-20261003, parent
#      2ee691818ad365610665408f7445cf2b9f0d2ae2), bytes
#      05a2bba9774d9bf4bcfd8b376a5ed785bef56747ec3c9d1d093e173c31864328 -
#      this code pins the committed bytes (in-package copy) and refuses on
#      drift;
#   2. V2_2_ADDENDUM.md sha cf7da1a8cc75f522acaa958045ce1977e12f37187211db69
#      80c48f4f1a7c90f4 - the declared scope limit that names THIS direction
#      ("the v2.1 rejection class 'opposing digit crosses the solid' ...
#      is NOT addressed by cmc_flexion/mp_flexion").
#
# Declared construction (committed prereg sections 2-5, binding):
#   - the 16 certified digit-side joints: mcp{k}_flexion + mcp{k}_abduction
#     on proxph{k}, pm{k}_flexion on midph{k}, md{k}_flexion on distph{k},
#     k in {2,3,4,5}; grid values computed FROM the parsed certified A05
#     ranges at run (refusal posture_outside_certified_ranges otherwise);
#   - thumb-side + wrist joints HELD at the sealed q_c(PRIMARY) values
#     (instrument_v2.Q_C_PRIMARY); contact pair (distal_thumb, distph3);
#   - R0 REFERENCE posture (sealed q_c, NOT a scan point) + 98 scan
#     postures: TIER A single-joint 80 (16 joints x fractions
#     {0.05,0.275,0.5,0.725,0.95}), TIER B flexion waves 12 (digits 2/3/4 x
#     {0.275,0.5,0.725,0.95}, abduction at q_c), TIER C abduction extremes 6
#     (digits 2/3/4 x {0.05,0.95} with the flexion triple at 0.95);
#   - STAGE 1 coarse: theta every 8th of 720 x the v2.1 phi grid x 2 mirrors
#     = 1,440 axes/posture (the sealed v2.2 coarse law, reused verbatim via
#     v22.screen_coarse); STAGE 2 full resolution (v21.screen_posture_v21)
#     for hitting postures only; S1 exact under the inherited caps
#     (CAP_S1_PER_POSTURE=96, cumulative 2.5 h per job) inside the per-axis
#     path; pad-orientation cos > 0 at S1-survivor recording;
#   - JOBS: argv[1] in {"job1","job2"}: job1 = R0 + digits-{2,4,5} tiers
#     (1 + 72 = 73 postures); job2 = digit-3 tiers (26 postures); counts are
#     asserted against the declared split (refusal otherwise);
#   - FROZEN PREDICTIONS recorded per the committed prereg section 4:
#     DS-P1 (predicted zero stage-1 S0-survivors), DS-P2 (job1 replication
#     gate: no_approach and s3_reject_bracket counts IDENTICAL across R0 and
#     every digit-2/4/5-only posture - their per-axis solves are
#     digit-joint-invariant because the contact tips are unmoved; failure =>
#     results withheld, exit 3, evidence preserved), DS-P3 (every
#     digit-2/4/5-only posture zero S0-survivors), DS-P5 (the recorded
#     distph2 relief trajectory: per digit-2 posture clearance-event count +
#     min proven depth, R0 as reference).
#   - STAGE-2 WALL GUARD (declared durability/scoping mechanism, prereg
#     section 5 job law "a stage-2 hit list may run in a deterministic
#     follow-up job"): in-job stage 2 runs while elapsed < 3.0 h; remaining
#     hits are recorded staged_followup (deterministic pid order) - never a
#     silent drop. A partial receipt is rewritten after EVERY posture
#     (outputs/...partial.json) so a timeout preserves the scan state.
#
# REUSED UNMODIFIED (byte-identical in-package copies, sha-pinned below):
# instrument_v2 (the merged instrument), grasp_screen (v2.0), grasp_screen_v21
# (axis construction + two-contact solve + per-axis screen + full-resolution
# posture screen), grasp_screen_v22 (the coarse-stage screen law). Serial,
# deterministic, stdlib-only. NO new screen predicate is defined in this
# file: every per-axis verdict comes from the sealed v2.1/v2.2 code path.

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
import grasp_screen_v22 as v22

PREREG_COMMIT = "1a567c39164d4b44d9fa0efb048429f8b3d03fe8"
PREREG_SHA256 = (
    "05a2bba9774d9bf4bcfd8b376a5ed785bef56747ec3c9d1d093e173c31864328")
ADDENDUM_NAME = "V2_2_ADDENDUM.md"
ADDENDUM_SHA256 = (
    "cf7da1a8cc75f522acaa958045ce1977e12f37187211db6980c48f4f1a7c90f4")
INSTRUMENT_PREREG_NAME = "INSTRUMENT_PREREGISTRATION.md"
INSTRUMENT_PREREG_SHA256 = v21.INSTRUMENT_PREREG_SHA256
CONTROL_TABLE_NAME = v21.CONTROL_TABLE_NAME
CONTROL_TABLE_SHA256 = v21.CONTROL_TABLE_SHA256
INSTRUMENT_SHA256 = v21.INSTRUMENT_SHA256
GS_NAME = "grasp_screen.py"
GS_SHA256 = (
    "6b924e87151f5e2235b9d9c023be85d0f7602d42020b37df4ba7bf58c0e9e0ea")
V21_NAME = "grasp_screen_v21.py"
V21_SHA256 = (
    "a35facd2f0876d5b7aa595c3af5be7151f121d315f151cdb7a42e9dee86c0407")
V22_NAME = "grasp_screen_v22.py"
V22_SHA256 = (
    "96ad2809ed928969571fe3b943117d6dba5d9ae905620b963039595313c5cb1b")

THETA_STRIDE = 8                      # == v22.THETA_STRIDE (asserted)
RANGE_FRACTIONS_TIER_A = (0.05, 0.275, 0.5, 0.725, 0.95)
RANGE_FRACTIONS_WAVE = (0.275, 0.5, 0.725, 0.95)
RANGE_FRACTIONS_TIER_C_AB = (0.05, 0.95)
TIER_C_FLEX = 0.95
CONTACT_PAIR = ("distal_thumb", "distph3")
STAGE2_WALL_GUARD_S = 3.0 * 3600.0

JOB_DEFS = {
    "job1": dict(digits=(2, 4, 5), with_r0=True, declared_postures=73),
    "job2": dict(digits=(3,), with_r0=False, declared_postures=26),
}


def sha_of(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def canonical(x):
    return json.dumps(x, indent=1, sort_keys=True)


def digit_joint_names(k):
    return ("mcp%d_flexion" % k, "mcp%d_abduction" % k,
            "pm%d_flexion" % k, "md%d_flexion" % k)


def joint_range(bodies, jn):
    """The certified range of one joint, parsed from the A05 model
    (mirrors the sealed v2.2 grid builder's lookup)."""
    for bname in bodies:
        for (jn2, _ax, rng) in bodies[bname]["joints"]:
            if jn2 == jn:
                return bname, rng
    iv.refuse("input_pin_missing", "scan joint missing from model: " + jn)


def range_value(bodies, jn, frac):
    """v = lo + frac*(hi-lo), computed FROM the parsed certified range;
    refusal if the value leaves the range (frozen law)."""
    _b, (lo, hi) = joint_range(bodies, jn)
    v = lo + frac * (hi - lo)
    if v < lo - 1e-12 or v > hi + 1e-12:
        iv.refuse("posture_outside_certified_ranges",
                  "%s %r outside %r" % (jn, v, (lo, hi)))
    return v


def build_posture_grid(model, digits, with_r0):
    """The declared grid: R0 reference + Tiers A/B/C over the requested
    digits. Deterministic order; every moved value range-checked."""
    bodies = model[0]
    base = {}
    for jn in model[1]:
        base[jn] = iv.Q_C_PRIMARY.get(jn, 0.0)
    grid = []
    if with_r0:
        grid.append(dict(pid="R0_REFERENCE", q=dict(base), tier="R0",
                         digit=None, moved={}, role="reference_not_a_scan_point"))
    # TIER A: each digit-side joint alone at the five declared fractions
    for k in digits:
        for jn in digit_joint_names(k):
            for fi, f in enumerate(RANGE_FRACTIONS_TIER_A):
                q = dict(base)
                v = range_value(bodies, jn, f)
                q[jn] = v
                grid.append(dict(pid="A_d%d_%s_f%d" % (k, jn, fi), q=q,
                                 tier="A", digit=k, moved={jn: v},
                                 role="scan"))
    # TIER B: flexion wave (mcp/pm/md flexion together), abduction at q_c
    for k in digits:
        if k not in (2, 3, 4):
            continue
        fj = ("mcp%d_flexion" % k, "pm%d_flexion" % k, "md%d_flexion" % k)
        ab = "mcp%d_abduction" % k
        for fi, f in enumerate(RANGE_FRACTIONS_WAVE):
            q = dict(base)
            moved = {}
            for jn in fj:
                v = range_value(bodies, jn, f)
                q[jn] = v
                moved[jn] = v
            grid.append(dict(pid="B_d%d_f%d" % (k, fi), q=q, tier="B",
                             digit=k, moved=moved, role="scan"))
    # TIER C: abduction extreme with the flexion triple at full 0.95
    for k in digits:
        if k not in (2, 3, 4):
            continue
        fj = ("mcp%d_flexion" % k, "pm%d_flexion" % k, "md%d_flexion" % k)
        ab = "mcp%d_abduction" % k
        for fi, f in enumerate(RANGE_FRACTIONS_TIER_C_AB):
            q = dict(base)
            moved = {}
            v = range_value(bodies, ab, f)
            q[ab] = v
            moved[ab] = v
            for jn in fj:
                v2 = range_value(bodies, jn, TIER_C_FLEX)
                q[jn] = v2
                moved[jn] = v2
            grid.append(dict(pid="C_d%d_ab%d" % (k, fi), q=q, tier="C",
                             digit=k, moved=moved, role="scan"))
    return grid


def distph2_rows(res):
    """The recorded distph2 clearance reject rows of one posture result."""
    return [r for r in res["rejects"]
            if len(r) >= 6 and r[3] == "S0_REJECT_CLEARANCE"
            and r[4] == "distph2"]


def distph2_summary(res):
    rows = distph2_rows(res)
    depths = []
    for r in rows:
        try:
            depths.append(float(r[5]))
        except ValueError:
            pass
    cnt = res["clearance_by_bone"].get("distph2", 0)
    return dict(events=cnt, rows=len(rows),
                min_proven_depth=(min(depths) if depths else None),
                max_proven_depth=(max(depths) if depths else None))


def pipeline(job):
    if job not in JOB_DEFS:
        iv.refuse("job_argument_invalid", repr(job))
    jd = JOB_DEFS[job]
    # ---- identity gates (the v2.2 discipline, extended to this card) ----
    if gs.N_THETA != v21.N_THETA:
        iv.refuse("module_constant_drift", "gs.N_THETA vs v21.N_THETA")
    if v21.N_THETA != 720:
        iv.refuse("v21_constant_drift", "v21.N_THETA must be 720")
    if v22.THETA_STRIDE != THETA_STRIDE:
        iv.refuse("v22_constant_drift", "v22.THETA_STRIDE must be 8")
    if v22.RANGE_FRACTIONS != RANGE_FRACTIONS_TIER_A:
        iv.refuse("v22_constant_drift", "v22.RANGE_FRACTIONS changed")
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
    gsha = sha_of(os.path.join(HERE, GS_NAME))
    if gsha != GS_SHA256:
        iv.refuse("v2_module_copy_mismatch", GS_NAME + " " + gsha)
    v1sha = sha_of(os.path.join(HERE, V21_NAME))
    if v1sha != V21_SHA256:
        iv.refuse("v2_module_copy_mismatch", V21_NAME + " " + v1sha)
    v2sha = sha_of(os.path.join(HERE, V22_NAME))
    if v2sha != V22_SHA256:
        iv.refuse("v2_module_copy_mismatch", V22_NAME + " " + v2sha)
    table_path = os.path.join(HERE, CONTROL_TABLE_NAME)
    tsha = sha_of(table_path)
    if tsha != CONTROL_TABLE_SHA256:
        iv.refuse("control_input_table_mismatch", tsha)
    gate, _mut, _stl_files, _bounds = iv.run_input_gate(
        os.path.join(HERE, INSTRUMENT_PREREG_NAME))
    gs.emit("=" * 78)
    gs.emit("GATE. prereg COMMIT %s bytes %s MATCH; addendum %s MATCH;"
            " instrument copy %s MATCH; v2.0/v2.1/v2.2 module copies MATCH;"
            " control table MATCH; inherited input gate ok=%s pins=%d."
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
    grid = build_posture_grid(model, jd["digits"], jd["with_r0"])
    scan_postures = [g for g in grid if g["role"] == "scan"]
    if len(grid) != jd["declared_postures"] or len(scan_postures) != \
            jd["declared_postures"] - (1 if jd["with_r0"] else 0):
        iv.refuse("declared_job_split_mismatch",
                  "%s built %d postures (%d scan), declared %d"
                  % (job, len(grid), len(scan_postures),
                     jd["declared_postures"]))
    axes_stage1 = (720 // THETA_STRIDE) * len(phi_grid) * 2
    gs.emit("DIGIT GRID [%s]: %d postures (R0 reference: %s; scan tiers"
            " A/B/C over digits %r); stage-1 axes/posture = %d."
            % (job, len(grid), jd["with_r0"], list(jd["digits"]),
               axes_stage1))
    receipt = dict(
        schema="chimera.digit_scan.screen.v1",
        task="GRASP-DIGIT-SCAN-20261003 digit-side joint scan (" + job +
             ": the exhausted ladder's named unscanned DOF direction - the"
             " opposing-digit clearance rejection class - at the sealed"
             " v2.1 placement solve)",
        lane="E:/ChimeraWork/monkey-coordination/digit-scan/",
        job=job,
        job_def=dict(digits=list(jd["digits"]), with_r0=jd["with_r0"],
                     declared_postures=jd["declared_postures"]),
        prereg_commit=PREREG_COMMIT,
        preregistration_sha256=psha,
        addendum_sha256=asha,
        instrument_copy_sha256=isha,
        v2_module_copies_sha256=dict(grasp_screen=gsha,
                                     grasp_screen_v21=v1sha,
                                     grasp_screen_v22=v2sha),
        instrument_preregistration_sha256=ipsha,
        control_input_table_sha256=tsha,
        frozen_constants=dict(tau=iv.TAU, pi_c=iv.PI_C,
                              r_joint=iv.R_JOINT, scale=iv.SCALE,
                              trunk_r=iv.TRUNK_R, trunk_h=iv.TRUNK_H,
                              n_theta=720, theta_stride=THETA_STRIDE,
                              phi_grid_deg=list(v21.PHI_GRID_DEG),
                              range_fractions_tier_a=list(
                                  RANGE_FRACTIONS_TIER_A),
                              range_fractions_wave=list(
                                  RANGE_FRACTIONS_WAVE),
                              tier_c_flex=TIER_C_FLEX,
                              contact_pair=list(CONTACT_PAIR),
                              tau_bracket=v21.TAU_BRACKET,
                              bisect_iters=v21.BISECT_ITERS,
                              tau_scan_samples=v21.TAU_SCAN_SAMPLES,
                              s_bracket=[gs.S_BRACKET_LO, gs.S_BRACKET_HI],
                              cap_s1_per_posture=gs.CAP_S1_PER_POSTURE,
                              s1_time_budget_s=gs.S1_TIME_BUDGET_S,
                              pad_gate_min_cos=v21.PAD_GATE_MIN_COS,
                              stage2_wall_guard_s=STAGE2_WALL_GUARD_S),
        input_gate=gate,
        witness_identity=wit,
        light_gate=lg,
        posture_grid=[dict(pid=g["pid"], tier=g["tier"], digit=g["digit"],
                           moved=g["moved"], role=g["role"]) for g in grid],
        postures={},
    )
    outdir = os.environ.get("CHIMERA_OUTPUT_DIR", "outputs")
    os.makedirs(outdir, exist_ok=True)
    partial_path = os.path.join(
        outdir, "grasp_screen_digit_receipt_%s_partial.json" % job)

    def write_partial():
        with open(partial_path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(canonical(receipt) + "\n")

    s1_clock = [0.0]
    t0 = time.monotonic()
    hits = []
    for g in grid:
        prep = v21.prep_posture_v21(model, g["q"], CONTACT_PAIR)
        if g["pid"] == "R0_REFERENCE":
            ai = v21.axis_identity_check(prep)
            receipt["axis_identity"] = ai
            gs.emit("AXIS FAMILY IDENTITY (R0 vs sealed v2.0 axis_basis):"
                    " %s" % json.dumps(ai, sort_keys=True))
            if not ai["ok"]:
                iv.refuse("axis_family_identity_failed", json.dumps(ai))
        gs.emit("-" * 78)
        gs.emit("POSTURE %s tier=%s digit=%r moved=%s chord(T1 origins)=%r m."
                % (g["pid"], g["tier"], g["digit"],
                   json.dumps(g["moved"], sort_keys=True), prep.chord))
        res = v22.screen_coarse(prep, s1_clock, phi_grid)
        res["chord_t1"] = prep.chord
        reachable = res["counters"]["axes_total"] - \
            res["counters"]["s0_reject_no_approach"]
        res["reachable_axes"] = reachable
        res["tip_deep_share_reachable"] = (
            res["counters"]["s0_reject_tip_deep"] / reachable
            if reachable > 0 else None)
        if g["pid"] == "R0_REFERENCE":
            res["distph2_summary"] = distph2_summary(res)
            gs.emit("  R0 distph2 reference: %s"
                    % json.dumps(res["distph2_summary"], sort_keys=True))
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
        if g["role"] == "scan" and \
                res["counters"]["s0_survivors"] >= 1:
            hits.append(g["pid"])
        if g["pid"] == "R0_REFERENCE":
            # R0 replication against the sealed map: the coarse axes are a
            # SUBSET of the sealed v2.1 full-resolution q_c axes, and the
            # sealed full-resolution result is 0 S0-survivors at q_c
            # (job f0da9bb122bb411f9acef57b650f674c) - any R0 coarse
            # survivor would contradict the sealed map (drift => refusal).
            if res["counters"]["s0_survivors"] != 0:
                iv.refuse("r0_sealed_map_replication_failed",
                          "R0 coarse S0-survivors %d vs sealed v2.1"
                          " full-resolution 0"
                          % res["counters"]["s0_survivors"])
            gs.emit("R0 sealed-map replication: stage-1 S0-survivors = 0"
                    " (consistent with the sealed v2.1 full-resolution"
                    " q_c rejection).")
        write_partial()
    gs.emit("=" * 78)
    gs.emit("STAGE 1 COMPLETE [%s]: %d/%d scan postures with >= 1"
            " S0-survivor." % (job, len(hits), len(scan_postures)))
    # DS-P2 (job1 only): the solve-invariance replication gate
    if jd["with_r0"]:
        na = dict((g["pid"], receipt["postures"][g["pid"]]["counters"]
                   ["s0_reject_no_approach"]) for g in grid)
        br = dict((g["pid"], receipt["postures"][g["pid"]]["counters"]
                   ["s3_reject_bracket"]) for g in grid)
        ds_p2_ok = (len(set(na.values())) == 1
                    and len(set(br.values())) == 1)
        receipt["ds_p2_replication_gate"] = dict(
            scope="R0 + digit-2/4/5-only postures of " + job,
            no_approach_by_posture=na, s3_bracket_by_posture=br,
            ok=bool(ds_p2_ok),
            law="their per-axis solves are digit-joint-invariant (the"
                " contact tips are unmoved); any drift is an"
                " instrument/posture-prep defect => results withheld")
        gs.emit("DS-P2 replication gate (no_approach/s3_bracket identity):"
                " ok=%s" % ds_p2_ok)
    else:
        receipt["ds_p2_replication_gate"] = dict(
            scope="not_applicable_" + job,
            note="digit-3 postures move the distph3 contact tip; the solve"
                 " re-forms per posture (committed prereg DS-P4)")
    # DS-P5: the distph2 relief trajectory (recorded, never gating)
    if jd["with_r0"]:
        traj = {}
        for g in grid:
            res = receipt["postures"][g["pid"]]
            if "distph2" in res["clearance_by_bone"] or \
                    g["pid"] == "R0_REFERENCE":
                traj[g["pid"]] = distph2_summary(res)
        receipt["ds_p5_distph2_trajectory"] = traj
    # stage 2: full-resolution re-run, hits only, declared wall guard
    staged_followup = []
    for pid in hits:
        if time.monotonic() - t0 > STAGE2_WALL_GUARD_S:
            staged_followup.append(pid)
            continue
        g = [x for x in grid if x["pid"] == pid][0]
        prep = v21.prep_posture_v21(model, g["q"], CONTACT_PAIR)
        gs.emit("STAGE 2 POSTURE %s (full 720-theta resolution)." % pid)
        res = v21.screen_posture_v21(prep, s1_clock, phi_grid)
        res["chord_t1"] = prep.chord
        receipt["postures"][pid]["stage2"] = res
        gs.emit("  stage2 counters: %s" % json.dumps(res["counters"],
                                                     sort_keys=True))
        gs.emit("  stage2 coverage_ok=%s s0_survivors=%d survivors=%d"
                % (res["coverage_ok"], res["counters"]["s0_survivors"],
                   res["counters"]["survivors"]))
        if not res["coverage_ok"]:
            iv.refuse("coverage_arithmetic_broken", pid + ":stage2")
        write_partial()
    if staged_followup:
        receipt["stage2_staged_followup"] = dict(
            pids=staged_followup,
            law="committed prereg section 5: a stage-2 hit list may run in"
                " a deterministic follow-up job under THIS prereg; never a"
                " silent drop")
    # determinism slice: re-solve recorded cells of the FIRST posture
    first_pid = grid[0]["pid"]
    if receipt["postures"][first_pid]["determinism_slice"]:
        g0 = grid[0]
        prep = v21.prep_posture_v21(model, g0["q"], CONTACT_PAIR)
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
    # frozen predictions + verdict
    stage1_s0_total = 0
    exact_total = 0
    for pid in sorted(receipt["postures"]):
        r = receipt["postures"][pid]
        stage1_s0_total += r["counters"]["s0_survivors"]
        exact_total += r["counters"]["survivors"]
        if "stage2" in r:
            exact_total += r["stage2"]["counters"]["survivors"]
    ds_p2_ok = receipt.get("ds_p2_replication_gate", {}).get("ok")
    if jd["with_r0"] and ds_p2_ok is False:
        receipt["verdict"] = "DS_P2_FALSIFIED_RESULTS_WITHHELD"
    elif exact_total > 0:
        receipt["verdict"] = "SURVIVORS_PRESENT_FORCE_STAGE_INPUTS"
    elif stage1_s0_total > 0:
        receipt["verdict"] = "S0_SURVIVORS_STAGE2_DONE_OR_STAGED"
    else:
        receipt["verdict"] = "ZERO_SURVIVORS_DIGIT_SIDE"
    receipt["predictions"] = dict(
        ds_p1_any_stage1_hit=bool(len(hits) > 0),
        ds_p1_predicted="zero (observed zero SUPPORTS the prediction;"
                        " observed hits FALSIFY it and trigger stage 2)",
        ds_p2_ok=ds_p2_ok,
        ds_p3_digit245_only_zero_survivors=(
            bool(len(hits) == 0) if jd["with_r0"] else None),
        stage1_s0_survivors_incl_reference=stage1_s0_total,
        stage1_s0_survivors_scan_postures=len(hits),
        exact_survivors_all_stages=exact_total,
        hits=[h for h in hits],
    )
    receipt["totals"] = dict(stage1_s0_survivors=stage1_s0_total,
                             exact_survivors_all_stages=exact_total)
    receipt["s1_cumulative_clock_s"] = s1_clock[0]
    gs.emit("=" * 78)
    gs.emit("VERDICT [%s]: %s (stage1_s0=%d exact_all_stages=%d)"
            % (job, receipt["verdict"], stage1_s0_total, exact_total))
    return receipt


def main():
    job = sys.argv[1] if len(sys.argv) > 1 else ""
    outdir = os.environ.get("CHIMERA_OUTPUT_DIR", "outputs")
    os.makedirs(outdir, exist_ok=True)
    try:
        receipt = pipeline(job)
        text = "\n".join(gs._report) + "\n"
    except iv.GateRefusal as exc:
        with open(os.path.join(
                outdir,
                "grasp_screen_digit_gate_receipt_%s.json"
                % (job or "unspecified")),
                "w", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(dict(
                schema="chimera.digit_scan.gate.v1", job=job,
                ok=False, refusal=exc.detail), indent=1) + "\n")
        print("REFUSAL: %s" % exc.detail, flush=True)
        raise SystemExit(3)
    with open(os.path.join(
            outdir, "grasp_screen_digit_receipt_%s.json" % job), "w",
            encoding="utf-8", newline="\n") as fh:
        fh.write(canonical(receipt) + "\n")
    with open(os.path.join(
            outdir, "grasp_screen_digit_report_%s.txt" % job), "w",
            encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    raise SystemExit(0)


if __name__ == "__main__":
    main()
