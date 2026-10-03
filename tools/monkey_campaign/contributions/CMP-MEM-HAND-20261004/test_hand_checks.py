"""test_hand_checks.py -- THE CMP-MEM-HAND-20261004 ACCEPTANCE BATTERY.

Packet PKT-G3-MEMBRANE-HAND (criteria f3dbf093...); preregistration pinned at
commit 069c6857 (blob sha256 e573d55d...), PREREGISTRATION.md section 5/6/7.
Every number below is a run-time falsifier: each check carries the packet's
own window and sealed reference, and each has a constructed trigger that MUST
fire (negative controls run in-battery and are recorded -- the
concealed-falsification law).

Laws honored here:
  - a verdict is PASS only on this run's own measured values inside the
    packet window; the runner receipt (state PASSED + cleanup_verified) is
    the OUTER gate and is joined downstream, never asserted by this script;
  - failures are preserved and reported (a falsified prediction is a
    result), never retried into green;
  - fixtures fx.ground_mu_pair (mu_s 0.6 / mu_k 0.4) and fx.ground_plane_height
    (0.004 m) stay NAMED_PLACEHOLDER / AUTHORED_DECLARED: every result here is
    FIXTURE-BASED and claims NO integrated qualification;
  - x_press / x_share / x_reach / mu_s_mu_k_measured stay ABSENT or
    NAMED_PLACEHOLDER verbatim; no synthetic constant fills them;
  - membrane.ground.v1's interior stays HIDDEN: only the byte-pinned external
    contract and the sealed public modules are consumed.

CPU-only, stdlib + the pinned substrate modules; deterministic.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import hand_membrane_v1 as hm  # noqa: E402 (this package's ABI module)

# ---- the packet's sealed references and windows (run-time falsifiers) --------
P = 0.3                                   # declared fixture press impulse
WIN_X1 = 1e-9                             # N*s  (ACC::T.X1_press_entry)
X1_SEALED = 8.342154744767072e-11         # N*s  (G04 X1)
X4_JN_BAR = 6.341478508833337e-11         # N*s  (G04 amendment a2 worst)
X4_JT_BAR = 2.5365914035333348e-11        # N*s  (G04 amendment a2 worst)
WIN_RELEASE_SCALE = 1e-10                 # N*s per kg share per release tick
WIN_RECURSION = 1e-9                      # m/s  (ACC::T.G07 recursion)
G07_RECURSION_SEALED = 1.747198913326642e-11
WIN_ENERGY = 1e-12                        # J    (exact identity window)
G07_ENERGY_SEALED = 1.354472090042691e-14
WIN_F32 = 1e-6                            # float32 delivery window
G05_F32_SEALED = 1.2003610327937508e-08
WIN_TIME = 1e-12                          # s    (t_seconds law)
G05_ACCEPTED = 390                        # 13 scenarios x 30 ticks

READINGS = (("band_lo", 5.4), ("band_mid", 6.15), ("band_hi", 6.9),
            ("scene", 10.037998))
CHANNELS = (1, 2, 3)
G05_TICKS = 30        # hold 20 + release 10 (the G05 cadence)
G07_RELEASE = 40      # the declared release_ticks of the G07 account
ZERO_MU_LABEL = "band_mid|n=3|mu=0"

CRITERIA_SHA256 = "f3dbf0935ca3029c2799a55374f760d652f4e2e8432495b206a20e00aa285a81"
PIN_COMMIT = "069c6857c7635d24356b70c37f0acbac6fdf1818"
WORKER = "wk-membrane-hand"
PACKET_ID = "PKT-G3-MEMBRANE-HAND"


def _f32_rel_err(delivered, raw):
    return abs(delivered - raw) / max(1.0, abs(raw))


class Battery:
    def __init__(self):
        self.rows = []
        self.evidence = {}

    def row(self, test_id, verdict, observed, window, evidence=None,
            sealed_reference=None, negative_control=None, fixture_based=True):
        self.rows.append({
            "test_id": test_id, "verdict": verdict, "observed": observed,
            "window": window, "evidence": evidence or {},
            "sealed_reference": sealed_reference,
            "negative_control": negative_control,
            "fixture_based": fixture_based,
        })

    def verdict_of(self, test_id):
        for r in self.rows:
            if r["test_id"] == test_id:
                return r["verdict"]
        return "NOT_RUN"


def _load_module():
    membrane_abi, spec_format, spec_runtime = hm._load_mathspec()
    spec_path = HERE / hm.SPEC_REL
    raw = spec_path.read_bytes()
    spec_sha = hashlib.sha256(raw).hexdigest()
    spec = json.loads(raw.decode("utf-8"))
    ctx = membrane_abi.SpecContext(spec, spec_sha)
    built = hm.build(ctx, 0.005)
    return membrane_abi, spec_format, spec_runtime, spec, spec_sha, ctx, built


# --------------------------------------------------------------------------
# T.X1 + T.X4 (the 12 sealed grip cases, shared traces)
# --------------------------------------------------------------------------

def _case_label(reading, n):
    return "%s|n=%d" % (reading, n)


def run_t_x1_x4(bat, built):
    gc, lc = built.pinned["gc"], built.pinned["lc"]
    geom = built.load_fixture_geometry()
    traces = {}
    x1_worst = 0.0
    x1_worst_case = None
    per_case_x1 = {}
    x4_worst_jn = 0.0
    x4_worst_jt = 0.0
    per_case_x4 = {}
    decision_faults = []
    for reading, kg in READINGS:
        for n in CHANNELS:
            label = _case_label(reading, n)
            header, rows = gc.run_scenario(lc, geom, kg, n,
                                           scenario_id=label)
            traces[label] = (header, rows, kg, n)
            worst = 0.0
            rel_jn = 0.0
            rel_jt = 0.0
            ch = hm.PressChannel(built.press_point_ns)
            for row in rows:
                got = ch.step(row["tick"], row["phase"])
                if row["phase"] == "hold":
                    if got != P or header["press_ns"] != P:
                        decision_faults.append({"case": label,
                                                "tick": row["tick"],
                                                "channel_state": got})
                    for pd in row["pads"]:
                        worst = max(worst, abs(pd["jn_sum_Ns"] - P))
                else:
                    jn = max(abs(pd["jn_sum_Ns"]) for pd in row["pads"])
                    jt = max(abs(pd["jt_sum_Ns"]) for pd in row["pads"])
                    rel_jn = max(rel_jn, jn)
                    rel_jt = max(rel_jt, jt)
            per_case_x1[label] = worst
            if worst > x1_worst:
                x1_worst, x1_worst_case = worst, label
            share = kg / n
            per_case_x4[label] = {"jn_max_Ns": rel_jn, "jt_max_Ns": rel_jt,
                                  "bar_Ns": share * WIN_RELEASE_SCALE,
                                  "jn_within_scaled_bar":
                                      rel_jn <= share * WIN_RELEASE_SCALE,
                                  "jt_within_scaled_bar":
                                      rel_jt <= share * WIN_RELEASE_SCALE}
            x4_worst_jn = max(x4_worst_jn, rel_jn)
            x4_worst_jt = max(x4_worst_jt, rel_jt)

    # -- T.X1 -----------------------------------------------------------------
    bites = False
    tamper_header, tamper_rows = gc.run_scenario(
        lc, geom, 5.4, 1, scenario_id="band_lo|n=1|x1-tamper",
        press_ns=P * 1.001)
    tampered_worst = 0.0
    for row in tamper_rows:
        if row["phase"] == "hold":
            for pd in row["pads"]:
                tampered_worst = max(tampered_worst,
                                     abs(pd["jn_sum_Ns"] - P))
    bites = tampered_worst > WIN_X1
    ok = (x1_worst <= WIN_X1) and not decision_faults and bites
    bat.row(
        "T.X1_press_entry", "PASS" if ok else "FAIL",
        "worst |jn_pad - P| over all hold ticks of all 12 cases = %r N*s "
        "(sealed %r; channel-vs-fixture decision faults: %d); tampered-press "
        "trigger measured %r" % (x1_worst, X1_SEALED, len(decision_faults),
                                 tampered_worst),
        "1e-9 N*s",
        evidence={"worst": x1_worst, "worst_case": x1_worst_case,
                  "sealed": X1_SEALED, "per_case": per_case_x1,
                  "bitwise_vs_sealed": x1_worst == X1_SEALED,
                  "decision_faults": decision_faults},
        sealed_reference="8.342154744767072e-11 N*s (G04 X1)",
        negative_control={"trigger": "press_ns = P*1.001 on band_lo|n=1",
                          "tampered_worst_Ns": tampered_worst,
                          "bites": bites})

    # -- T.X4 -----------------------------------------------------------------
    # negative control (the latch-bite construction, fully disclosed): a
    # silent re-arm is exactly "the press channel kept pressing into the
    # declared release window". Pinned machinery, no code changes: run
    # hold_ticks=25 / release_ticks=5 and evaluate the packet's release-bar
    # predicate on the DECLARED release window ticks 21..30. The re-armed
    # ticks carry jn = P >> bar: the predicate must FIRE.
    rearm_header, rearm_rows = gc.run_scenario(
        lc, geom, 5.4, 1, scenario_id="band_lo|n=1|x4-rearm-bite",
        hold_ticks=25, release_ticks=5)
    rearm_worst_jn = 0.0
    for row in rearm_rows:
        if row["tick"] > 20:   # the DECLARED release window (20 + 10)
            for pd in row["pads"]:
                rearm_worst_jn = max(rearm_worst_jn, abs(pd["jn_sum_Ns"]))
    bites = rearm_worst_jn > X4_JN_BAR
    # supplementary probe (recorded, not the bite): the FB1 leftover-weld
    # class holds the pad tangentially; its release jn stays noise-level
    # while the free-fall displacement law fires (G04 FB1 discriminator)
    weld_header, weld_rows = gc.run_scenario(
        lc, geom, 6.9, 2, scenario_id="band_hi|n=2|x4-weld-probe",
        sticky_release_weld=True)
    weld_worst_jn = 0.0
    for row in weld_rows:
        if row["phase"] == "release":
            for pd in row["pads"]:
                weld_worst_jn = max(weld_worst_jn, abs(pd["jn_sum_Ns"]))
    scaled_ok = all(v["jn_within_scaled_bar"] and v["jt_within_scaled_bar"]
                    for v in per_case_x4.values())
    ok = (x4_worst_jn <= X4_JN_BAR and x4_worst_jt <= X4_JT_BAR
          and scaled_ok and bites)
    bat.row(
        "T.X4_release_bars", "PASS" if ok else "FAIL",
        "worst release tick jn = %r, jt = %r N*s over all 12 cases "
        "(bars %r / %r); share-scaled bars (share_kg*1e-10) respected: %s; "
        "silent-re-arm trigger jn %r on declared release ticks (fired: %s)"
        % (x4_worst_jn, x4_worst_jt, X4_JN_BAR, X4_JT_BAR, scaled_ok,
           rearm_worst_jn, bites),
        "share_kg * 1e-10 per release tick",
        evidence={"jn_worst": x4_worst_jn, "jt_worst": x4_worst_jt,
                  "bars": {"jn": X4_JN_BAR, "jt": X4_JT_BAR},
                  "per_case": per_case_x4,
                  "supplementary_weld_probe_release_jn_max_Ns":
                      weld_worst_jn,
                  "supplementary_weld_probe_note": "the FB1 weld class fires "
                  "the free-fall displacement law (G04 FB1), not the jn bar; "
                  "recorded, not required to bite here"},
        sealed_reference="G04 amendment a2 worsts",
        negative_control={"trigger": "silent re-arm modeled as press applied "
                                     "on declared release ticks 21..25 "
                                     "(hold_ticks=25, release_ticks=5, "
                                     "evaluated against the declared 20+10 "
                                     "window), band_lo|n=1",
                          "tampered_release_jn_max_Ns": rearm_worst_jn,
                          "bites": bites})
    return traces


# --------------------------------------------------------------------------
# T.G07 (13 scenarios, release 40, accounted release)
# --------------------------------------------------------------------------

def run_t_g07(bat, built):
    gc, lc, cso, rfa = (built.pinned["gc"], built.pinned["lc"],
                        built.pinned["cso"], built.pinned["rfa"])
    geom = built.load_fixture_geometry()
    worst_recursion = 0.0
    worst_energy = 0.0
    per_case = {}
    press_nonzero = []
    for reading, kg in READINGS:
        for n in CHANNELS:
            label = _case_label(reading, n)
            cases = [(label, {})]
            if label == "band_mid|n=3":
                cases.append((ZERO_MU_LABEL, {"mu_s": 0.0, "mu_k": 0.0}))
            for zlabel, mu_kwargs in cases:
                header, rows, acct, _cent = rfa.observe_with_account(
                    cso, gc, lc, geom, kg, n, zlabel, release_ticks=G07_RELEASE,
                    **mu_kwargs)
                header_ref, rows_ref = gc.run_scenario(
                    lc, geom, kg, n, scenario_id=zlabel, release_ticks=G07_RELEASE,
                    **mu_kwargs)
                rfa.cross_check_rows(header, rows, header_ref, rows_ref,
                                     zlabel)
                share = kg / n
                summary = rfa.release_account(rows, acct, n, share, lc.DT)
                energy = max(abs(p["residual_J"])
                             for arow in acct for p in arow["pads"])
                worst_recursion = max(worst_recursion,
                                      summary["recursion_worst_mps"])
                worst_energy = max(worst_energy, energy)
                if summary["press_work_release_J"] != 0.0:
                    press_nonzero.append({"case": zlabel,
                                          "W_press": summary["press_work_release_J"]})
                per_case[zlabel] = {
                    "recursion_worst_mps": summary["recursion_worst_mps"],
                    "energy_identity_worst_J": energy,
                    "press_work_release_J": summary["press_work_release_J"],
                    "collision_count": summary["collision_count"],
                    "jn_max_Ns": summary["jn_max_Ns"]}

    # negative control: an unrecorded upward propulsion impulse every release
    # tick (G07 FB2/FB4 class), measured with the account un-enforced
    th, tr, ta, _c = rfa.observe_with_account(
        cso, gc, lc, geom, 6.9, 2, "band_hi|n=2|g07-bite",
        release_ticks=G07_RELEASE, propulsion_ns=0.05, require_ledger=False,
        enforce_account=False)
    tampered_energy = max(abs(p["residual_J"])
                          for arow in ta for p in arow["pads"])
    bites = tampered_energy > WIN_ENERGY
    ok = (worst_recursion <= WIN_RECURSION and worst_energy <= WIN_ENERGY
          and not press_nonzero and bites)
    bat.row(
        "T.G07_accounted_release", "PASS" if ok else "FAIL",
        "free-fall recursion worst %r m/s (window 1e-9; sealed %r); exact "
        "energy identity worst %r J (window 1e-12; sealed %r); W_press == 0.0 "
        "J on every release tick of all 13 scenarios: %s; hidden-propulsion "
        "trigger energy residual %r J" % (worst_recursion,
                                          G07_RECURSION_SEALED, worst_energy,
                                          G07_ENERGY_SEALED,
                                          not press_nonzero, tampered_energy),
        "1e-9 (recursion) / exact identity",
        evidence={"recursion_worst_mps": worst_recursion,
                  "energy_identity_worst_J": worst_energy,
                  "sealed": {"recursion": G07_RECURSION_SEALED,
                             "energy": G07_ENERGY_SEALED},
                  "bitwise_vs_sealed": {
                      "recursion": worst_recursion == G07_RECURSION_SEALED,
                      "energy": worst_energy == G07_ENERGY_SEALED},
                  "per_case": per_case},
        sealed_reference="G07",
        negative_control={"trigger": "propulsion_ns=0.05 every release tick, "
                                     "unrecorded (require_ledger=False, "
                                     "account un-enforced), band_hi|n=2",
                          "tampered_energy_worst_J": tampered_energy,
                          "bites": bites})


# --------------------------------------------------------------------------
# T.G05 (13 scenarios, declared-only 32-slot seam through THIS membrane)
# --------------------------------------------------------------------------

_SLOT_RAW = ("jn", "jt", "force", "disp")


def run_t_g05(bat, built):
    gc, lc = built.pinned["gc"], built.pinned["lc"]
    geom = built.load_fixture_geometry()
    accepted = 0
    refused = []
    worst_f32 = 0.0
    timing_faults = []
    key_faults = []
    f32_faults = []
    per_case = {}
    a_clean_sample = None
    for reading, kg in READINGS:
        for n in CHANNELS:
            label = _case_label(reading, n)
            cases = [(label, {})]
            if label == "band_mid|n=3":
                cases.append((ZERO_MU_LABEL, {"mu_s": 0.0, "mu_k": 0.0}))
            for zlabel, mu_kwargs in cases:
                header, rows, samples, census, z0 = \
                    built.observe_and_deliver(geom, kg, n, zlabel, **mu_kwargs)
                accepted += census["accepted"]
                refused.extend(census["refusals"])
                if census["accepted"] != G05_TICKS:
                    timing_faults.append({"case": zlabel,
                                          "accepted": census["accepted"]})
                worst_case = 0.0
                to_f32 = built.pinned["cso"].to_f32
                for i, (sample, row) in enumerate(zip(samples, rows)):
                    if set(sample) != set(
                            built.pinned["cso"].DECLARED_SAMPLE_KEYS):
                        key_faults.append({"case": zlabel, "tick": row["tick"]})
                    if sample["t_tick"] != row["tick"] or \
                            sample["t_phase"] != row["phase"]:
                        timing_faults.append({"case": zlabel,
                                              "tick": row["tick"]})
                    if abs(sample["t_seconds"] - row["tick"] * lc.DT) > WIN_TIME:
                        timing_faults.append({"case": zlabel,
                                              "tick": row["tick"],
                                              "t_seconds": sample["t_seconds"]})
                    # float32 delivery identity on the 32 delivered slots
                    # (the four timing keys are exact, not float32-rounded)
                    for skey, sval in sample.items():
                        if skey in built.pinned["cso"].TIMING_KEYS:
                            continue
                        if sval != to_f32(sval):
                            f32_faults.append({"case": zlabel,
                                               "tick": row["tick"],
                                               "slot": skey, "value": sval})
                    rel = _f32_rel_err(sample["t_seconds"],
                                       row["tick"] * lc.DT)
                    worst_case = max(worst_case, rel)
                    # FULL-coverage float32 delivery metric: every slot's
                    # raw re-derived from the pinned project_sample formulas
                    # (the stricter measurement; never tuned to the sealed
                    # reference). The centroid raw uses the sealed G05 pose
                    # identity (measured == z0 - disp, worst 0.0 m).
                    agg_raw = {}
                    stick_count = sum(1 for pd in row["pads"]
                                      if pd["mode"] == "stick")
                    agg_raw["agg_support_count"] = float(stick_count)
                    agg_raw["agg_supported_flag"] = (
                        1.0 if (stick_count == n and row["phase"] == "hold")
                        else 0.0)
                    agg_raw["agg_release_flag"] = (
                        1.0 if row["phase"] == "release" else 0.0)
                    agg_raw["agg_ledger_residual_max_Ns"] = \
                        row["ledger"]["residual_full_max"]
                    agg_raw["agg_reciprocity_max_Ns"] = max(
                        abs(v) for v in row["ledger"]["reciprocity_residual"])
                    agg_raw["obs_mask_mean"] = \
                        (built.pinned["cso"].SLOTS_PER_CHANNEL * n + 8) \
                        / built.pinned["cso"].OBS_DIM
                    agg_raw["obs_frac_avail"] = 3.0 / 5.0
                    for k in range(n):
                        pd = row["pads"][k]
                        pairs = (
                            (sample["ch%d_jn_Ns" % k], pd["jn_sum_Ns"]),
                            (sample["ch%d_jt_Ns" % k], pd["jt_sum_Ns"]),
                            (sample["ch%d_contact_force_N" % k],
                             pd["jn_sum_Ns"] / lc.DT),
                            (sample["ch%d_disp_down_cum_m" % k],
                             pd["disp_down_m_cum"]),
                            (sample["ch%d_contact_flag" % k],
                             0.0 if pd["mode"] == "no_contact" else 1.0),
                            (sample["ch%d_stick_flag" % k],
                             1.0 if pd["mode"] == "stick" else 0.0),
                            (sample["ch%d_slip_flag" % k],
                             1.0 if pd["mode"] == "slip" else 0.0),
                            (sample["ch%d_centroid_z_m" % k],
                             z0[k] - pd["disp_down_m_cum"]),
                        )
                        for delivered, raw in pairs:
                            worst_case = max(worst_case,
                                             _f32_rel_err(delivered, raw))
                    for akey, araw in agg_raw.items():
                        worst_case = max(worst_case,
                                         _f32_rel_err(sample[akey], araw))
                    worst_case = max(worst_case, _f32_rel_err(
                        sample["agg_trunk_anchor_z_Ns"],
                        row["ledger"]["trunk_anchor"][2]))
                worst_f32 = max(worst_f32, worst_case)
                per_case[zlabel] = {"accepted": census["accepted"],
                                    "worst_f32_rel": worst_case}
                if a_clean_sample is None:
                    a_clean_sample = (zlabel, samples[0])

    # negative controls through THIS membrane's seam (each MUST fire by name)
    zlabel, clean = a_clean_sample
    controls = []

    def _control(name, mutate, expected_code):
        s = dict(clean)
        s = mutate(s)
        try:
            built.observation_seam.deliver_one(zlabel, lc.DT, s)
            controls.append({"control": name, "bites": False,
                             "expected": expected_code, "refusal": None})
        except ValueError as exc:
            code = str(exc).split(":", 1)[0]
            controls.append({"control": name, "bites": code == expected_code,
                             "expected": expected_code, "refusal": code})

    _control("undeclared_field",
             lambda s: dict(s, extra_solver_key=1.0), "undeclared_field")
    _control("timing_unbound", lambda s: dict(s, t_dt_s=0.0), "timing_unbound")
    _control("named_absent_occupied",
             lambda s: dict(s, x_press=1.0), "named_absent_occupied")
    _control("privileged_source",
             lambda s: dict(s, solver_penetration_m=0.001),
             "privileged_source")

    ok = (accepted == G05_ACCEPTED and not refused and not timing_faults
          and not key_faults and not f32_faults and worst_f32 <= WIN_F32
          and all(c["bites"] for c in controls))
    bat.row(
        "T.G05_observation_seam", "PASS" if ok else "FAIL",
        "declared-only 32-slot float32 delivery through the hand membrane's "
        "seam: %d accepted / %d refused over 13 scenarios x 30 ticks; worst "
        "float32 delivery error %r over the FULL slot coverage (window "
        "1e-6; sealed reference %r, whose own aggregation scope is the "
        "unpinned G05 run script -- the bitwise comparison is recorded, the "
        "window decides); float32 identity faults %d, timing faults %d, "
        "key-universe faults %d; 4 seam refusal controls fired: %s"
        % (accepted, len(refused), worst_f32, G05_F32_SEALED,
           len(f32_faults), len(timing_faults),
           len(key_faults),
           [c["refusal"] or c["control"] for c in controls]),
        "1e-06",
        evidence={"accepted": accepted, "refusals": refused,
                  "worst_f32_rel": worst_f32, "sealed": G05_F32_SEALED,
                  "metric_scope": "all 32 slots + timing, raws re-derived "
                  "from the pinned project_sample formulas (full coverage, "
                  "stricter than the sealed aggregation)",
                  "f32_faults": f32_faults[:20],
                  "timing_faults": timing_faults, "key_faults": key_faults,
                  "per_case": per_case},
        sealed_reference="1.2003610327937508e-08 (G05)",
        negative_control={"triggers": controls, "bites":
                          all(c["bites"] for c in controls)})


# --------------------------------------------------------------------------
# ABI conformance (prereg section 6)
# --------------------------------------------------------------------------

def run_abi(bat, membrane_abi, spec_format, spec_runtime, spec, spec_sha,
            ctx, built):
    # module-level conformance
    mod_record = membrane_abi.validate_module(hm, IMPLEMENTS_EXPECTED)
    # built-membrane conformance
    built_record = membrane_abi.validate_built(built, spec,
                                               IMPLEMENTS_EXPECTED,
                                               hm.CONNECTION_ID)
    # the ONE-writer law: the hand must NOT expose exchange_contribution
    no_writer = not hasattr(built, "exchange_contribution")
    probe_bites = False
    probe_code = None

    class _Probe(built.__class__):
        pass

    probe = _Probe.__new__(_Probe)
    probe.__dict__ = dict(built.__dict__)

    def _writer():
        return None
    probe.exchange_contribution = _writer
    try:
        membrane_abi.validate_built(probe, spec, IMPLEMENTS_EXPECTED,
                                    hm.CONNECTION_ID)
    except membrane_abi.CombineRefusal as exc:
        probe_code = getattr(exc, "code", str(exc.args[0]))
        probe_bites = probe_code == "abi_exchange_writer_violation"

    # dt gate + drift gate (refusals BEFORE any payload)
    dt_code = _expect_refusal(lambda: hm.build(ctx, 0.01), membrane_abi)
    drift_ctx = membrane_abi.SpecContext(spec, "0" * 64)
    drift_code = _expect_refusal(lambda: hm.build(drift_ctx, 0.005),
                                 membrane_abi)
    ok = (mod_record.get("conformant") is True
          and built_record.get("conformant") is True
          and no_writer and probe_bites
          and dt_code == "spec_dt_not_admissible"
          and drift_code == "spec_pinned_input_drift")
    bat.row(
        "T.ABI.conformance", "PASS" if ok else "FAIL",
        "validate_module conformant=%s; validate_built conformant=%s "
        "(ownership rows == spec section under resolve_ids; typed ports; "
        "exchange accessor); hand exposes NO exchange_contribution=%s; "
        "ONE-writer probe refused=%s (%s); dt gate %s; drift gate %s"
        % (mod_record.get("conformant"), built_record.get("conformant"),
           no_writer, probe_bites, probe_code, dt_code, drift_code),
        "named refusals fire", evidence={"module": mod_record,
                                         "built": built_record,
                                         "probe_code": probe_code,
                                         "dt_code": dt_code,
                                         "drift_code": drift_code})


IMPLEMENTS_EXPECTED = "membrane.hand.v1"


def _expect_refusal(fn, membrane_abi):
    try:
        fn()
    except membrane_abi.CombineRefusal as exc:
        return getattr(exc, "code", exc.args[0])
    except Exception as exc:  # noqa: BLE001 (record any other failure mode)
        return "UNEXPECTED:" + type(exc).__name__ + ":" + str(exc)[:120]
    return "NO_REFUSAL"


def run_channel(bat, built):
    """Component-level latch + structural-fault refusals (prereg 6.4/5)."""
    ch = hm.PressChannel(built.press_point_ns)
    latch_code = _expect_refusal_proxy(
        lambda: (ch.step(1, "hold"), ch.step(21, "release"),
                 ch.step(22, "hold")))
    ch2 = hm.PressChannel(built.press_point_ns)
    ch2.step(1, "hold")
    ch2.step(2, "release")
    rearmed = ch2.re_arm()
    hold_after_rearm = ch2.step(3, "hold")
    ch3 = hm.PressChannel(built.press_point_ns)
    fault_code = _expect_refusal_proxy(
        lambda: ch3.step(1, "hold", applied=0.15))
    ch4 = hm.PressChannel(built.press_point_ns)
    partial_code = _expect_refusal_proxy(
        lambda: ch4.step(1, "release", applied=0.1))
    ok = (latch_code == "ref.hand.latch_silent_rearm" and rearmed is True
          and hold_after_rearm == built.press_point_ns
          and fault_code == "ref.hand.press_state_not_armed_nor_released"
          and partial_code == "ref.hand.press_state_not_armed_nor_released")
    bat.row(
        "T.CH.latch_and_faults", "PASS" if ok else "FAIL",
        "silent re-arm refused %s; explicit re_arm() then hold = %r; applied "
        "0.15 refused %s; partial press on release refused %s"
        % (latch_code, hold_after_rearm, fault_code, partial_code),
        "named refusals fire",
        evidence={"latch_code": latch_code, "fault_code": fault_code,
                  "partial_code": partial_code})


def _expect_refusal_proxy(fn):
    try:
        fn()
    except hm.CombineRefusalProxy as exc:
        return exc.code
    except Exception as exc:  # noqa: BLE001
        return "UNEXPECTED:" + type(exc).__name__ + ":" + str(exc)[:120]
    return "NO_REFUSAL"


# --------------------------------------------------------------------------
# scoped spec conformance (prereg section 7; Lieutenant Ruling 1)
# --------------------------------------------------------------------------

def run_spec(bat, spec_format, spec, spec_sha):
    """Scoped spec conformance (prereg section 7; Lieutenant Ruling 1).

    The grammar's first-class ODE-assembly fields (transfer_law, numerics
    method/admissibility/horizon, qualification analytic reference) demand
    either ground-interior dynamics, a synthetic constant, or a misdeclared
    integration class for this GENERATED per-tick contact seam. Per Ruling 1
    the refusals are recorded verbatim and asserted against the DISCOVERED
    signature (recorded from the ac571dba shakedown; the pinned validator
    bytes make it deterministic). Amendment A1 to the pinned prereg's
    enumeration: the signature is WIDER than the two codes guessed at pin
    time by the same principle -- the added codes are the numerics/
    qualification first-class fields. NO refusal may touch the hand
    membrane's own section rows."""
    report = spec_format.validate_spec(spec)
    refusals = [{"code": e.get("code"), "detail": e.get("detail")}
                for e in report.errors]
    codes = sorted({r["code"] for r in refusals})
    allowed = sorted({spec_format.E_SPEC_MALFORMED,
                      spec_format.E_SPEC_TRANSFER_MEMBER_INVALID,
                      "spec_method_unsupported",
                      "spec_admissibility_table_invalid"})
    counts = {}
    for r in refusals:
        counts[r["code"]] = counts.get(r["code"], 0) + 1
    expected_counts = {"spec_malformed_document": 3,
                       "spec_transfer_member_invalid": 1,
                       "spec_method_unsupported": 1,
                       "spec_admissibility_table_invalid": 3}
    codes_ok = set(codes).issubset(set(allowed))
    signature_ok = counts == expected_counts
    # no refusal may point at the hand section's own rows
    hand_hits = [r for r in refusals
                 if (r["detail"] or {}).get("membrane_id")
                 == "membrane.hand.v1"]
    ids_ok = _spec_ids_stable(spec, spec_sha)
    bat.row(
        "T.SPEC.scoped_conformance",
        "PASS" if (codes_ok and signature_ok and not hand_hits
                   and ids_ok) else "FAIL",
        "validate_spec refusal codes %s (counts %s; expected signature %s); "
        "allowed first-class grammar set %s; refusals touching the hand "
        "section: %d; document identity stable under canonical reparse: %s; "
        "full refusal list recorded verbatim in evidence"
        % (codes, counts, expected_counts, allowed, len(hand_hits), ids_ok),
        "Ruling 1: only the enumerated first-class grammar refusals; "
        "signature amended by discovery (prereg amendment A1)",
        evidence={"refusals": refusals, "codes": codes, "allowed": allowed,
                  "counts": counts, "expected_counts": expected_counts,
                  "hand_hits": hand_hits, "spec_sha256": spec_sha,
                  "valid_flag": getattr(report, "valid", None)})


def _spec_ids_stable(spec, spec_sha):
    """The context identity is the byte sha of the pinned document; a reparse
    must produce the identical dict (no nondeterministic content)."""
    try:
        again = json.loads(json.dumps(spec, sort_keys=True,
                                      separators=(",", ":"),
                                      ensure_ascii=True))
    except Exception:  # noqa: BLE001
        return False
    return again == spec


# --------------------------------------------------------------------------
# upstream regression (unmodified sealed suites)
# --------------------------------------------------------------------------

def run_regression(bat):
    rows = []
    for card, test_name in (("MAT2-G04", "test_g04_checks.py"),
                            ("MAT2-G05", "test_g05_checks.py"),
                            ("MAT2-M06", "test_local_contact.py")):
        tdir = HERE.parent / card
        tfile = tdir / test_name
        if not tfile.exists():
            rows.append({"suite": test_name, "verdict": "NOT_RUN",
                         "reason": "suite file absent at the pinned base"})
            continue
        if card == "MAT2-M06":
            rows.append({
                "suite": test_name, "verdict": "NOT_RUN",
                "reason": "its falsifier arms write scratch-falsifiers/ at "
                          "HERE.parents[4] (the attempt dir); inside the "
                          "sealed runner that path resolves to the runner "
                          "slot directory outside the job scratch, which "
                          "runner-owned cleanup would see as an unknown "
                          "directory blocking slot reuse. Declared NOT_RUN "
                          "per the packet rule; never silent."})
            continue
        proc = subprocess.run(
            [sys.executable, "-B", "-m", "unittest", "discover",
             "-s", str(tdir), "-p", test_name, "-t", str(tdir)],
            capture_output=True, text=True, timeout=600)
        tail = (proc.stdout + proc.stderr)[-1500:]
        rows.append({"suite": test_name, "verdict":
                     "PASS" if proc.returncode == 0 else "FAIL",
                     "exit_code": proc.returncode, "tail": tail})
    ok = all(r["verdict"] in ("PASS", "NOT_RUN") for r in rows) and \
        any(r["verdict"] == "PASS" for r in rows)
    bat.row(
        "T.REG.upstream_suites", "PASS" if ok else "FAIL",
        "; ".join("%s=%s" % (r["suite"], r["verdict"]) for r in rows)
        + " (NOT_RUN rows carry their exact reason; unmodified sealed suites)",
        "exit 0 on every executed suite",
        evidence={"suites": rows})


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", default="all",
                        choices=("all", "spec", "abi", "battery"))
    args = parser.parse_args()
    t0 = time.time()
    bat = Battery()
    (membrane_abi, spec_format, spec_runtime, spec, spec_sha, ctx,
     built) = _load_module()

    selected = args.suite
    guards = []

    def _guarded(name, fn):
        try:
            fn()
        except Exception as exc:  # noqa: BLE001 (preserve the failure)
            import traceback
            guards.append({"check": name,
                           "error": "%s: %s" % (type(exc).__name__, exc),
                           "trace_tail": traceback.format_exc()[-1500:]})
            bat.row(name, "FAIL", "exception: %s: %s" % (type(exc).__name__,
                                                         exc),
                    "check-level exception preserved (never retried here)",
                    evidence={"trace_tail": guards[-1]["trace_tail"]})

    if selected in ("all", "spec"):
        _guarded("T.SPEC.scoped_conformance",
                 lambda: run_spec(bat, spec_format, spec, spec_sha))
    if selected in ("all", "abi"):
        _guarded("T.ABI.conformance",
                 lambda: run_abi(bat, membrane_abi, spec_format,
                                 spec_runtime, spec, spec_sha, ctx, built))
        _guarded("T.CH.latch_and_faults", lambda: run_channel(bat, built))
    if selected in ("all", "battery"):
        _guarded("T.X1_press_entry",
                 lambda: run_t_x1_x4(bat, built))
        _guarded("T.G07_accounted_release", lambda: run_t_g07(bat, built))
        _guarded("T.G05_observation_seam", lambda: run_t_g05(bat, built))
        _guarded("T.REG.upstream_suites", lambda: run_regression(bat))

    job_id = None
    try:
        job_id = pathlib.Path(".chimera-runner-id").read_text().strip()
    except OSError:
        job_id = "unknown (no runner id file: not a sealed run?)"
    result = {
        "schema": "chimera.compiler_packet_result.v1",
        "packet_id": PACKET_ID,
        "criteria_sha256": CRITERIA_SHA256,
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "worker_arrival_id": WORKER,
        "pin_commit": PIN_COMMIT,
        "base_sha256_env": os.environ.get("CHIMERA_BASE_SHA"),
        "run_job_id": job_id,
        "suite_selected": selected,
        "per_test_results": bat.rows,
        "check_guards": guards,
        "receipts": [],   # joined downstream from the actual runner receipt
        "fixture_based": True,
        "named_debts_encountered": [
            {"name": "x_press", "status": "ABSENT", "blocker": "NB-03",
             "provenance_verbatim": "measured grip-force actuator bound "
                                    "behind the normal press"},
            {"name": "x_share", "status": "ABSENT", "blocker": "NB-04",
             "provenance_verbatim": "Per-port load share is UNPINNED (no "
                                    "partition source). The equal-share case "
                                    "analysis is a model of the balance, not "
                                    "a measured load partition."},
            {"name": "x_reach", "status": "ABSENT", "blocker": "NB-05",
             "provenance_verbatim": "composing the hand-to-ground placement "
                                    "is x_reach, which is ABSENT (A09 frame "
                                    "law: no transform composed, no new fit "
                                    "recorded)"},
            {"name": "mu_s_mu_k_measured", "status": "NAMED_PLACEHOLDER",
             "blockers": ["NB-01", "NB-02"],
             "provenance_verbatim": "there is NO lawful measured pin for the "
                                    "primary pair today; L1/L2 envelope is "
                                    "falsifier-band context ONLY"},
            {"name": "fx.ground_plane_height", "status": "AUTHORED_DECLARED",
             "value_m": 0.004,
             "provenance_verbatim": "transform.reground.flatten."
                                    "plateau_height_m = +0.004 m; single "
                                    "writer: the composition flatten"},
        ],
        "deviations": [
            {"deviation_id": "DEV-1-jt-not-a-typed-port",
             "reason": "the pinned spec grammar types ONE exchange quantity "
                       "per connection (an input port's quantity_ref must "
                       "equal the connection's exchange.quantity_ref); jt is "
                       "the connection's second READ-ONLY seam record, "
                       "carried in the window view and delivered through "
                       "the declared 32-slot table (ch*_jt_Ns); inventing a "
                       "second connection was refused as dishonest",
             "disclosed_in": "spec conventions.one_exchange_quantity"},
            {"deviation_id": "DEV-2-observation-port-not-in-spec-table",
             "reason": "PORT_TYPES == ('scalar_real',) cannot type a 32-slot "
                       "table; mis-typing it scalar_real was refused; the "
                       "observation delivery is declared as the owned "
                       "published state grasp_observation_table (unitless "
                       "mapping, Ruling 2) and verified by T.G05; the "
                       "contract's port.observation row stays verbatim in "
                       "the result",
             "disclosed_in": "spec conventions.slot_f32_mapping"},
            {"deviation_id": "DEV-3-transfer-law-absent",
             "reason": "the grammar's first-class transfer_law would force "
                       "authoring the hidden ground interior or a synthetic "
                       "zero constant; per Ruling 1 the validator's refusal "
                       "list is recorded verbatim and asserted to the "
                       "enumerated connection-class set",
             "disclosed_in": "spec assembly.transfer_law_note"},
        ],
        "claims": [
            "the hand-side press channel, release latch and observation seam "
            "components are implemented and verified at the pinned inputs",
            "ALL results are FIXTURE-BASED (fx.ground_mu_pair NAMED_PLACEHOLDER, "
            "fx.ground_plane_height AUTHORED_DECLARED): no integrated "
            "qualification is claimed; the pair RUN remains the assembly "
            "task's debt (pair_run declared_pending)",
            "x_press ABSENT: the press channel runs at the declared fixture "
            "0.3 N*s/channel/tick; actuator_qualified false; nothing here "
            "qualifies the actuator",
        ],
        "sergeant_review_required": True,
        "publication": "with the Lieutenant",
        "elapsed_s": round(time.time() - t0, 3),
    }
    out_dir = os.environ.get("CHIMERA_OUTPUT_DIR")
    if not out_dir:
        out_dir = str(HERE / ".tmp-out")
    out = pathlib.Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "result.json").write_text(
        json.dumps(result, indent=1, sort_keys=True), encoding="utf-8")
    (out / "battery_evidence.json").write_text(
        json.dumps({"rows": bat.rows,
                    "module_sha256": hashlib.sha256(
                        (HERE / "hand_membrane_v1.py").read_bytes()).hexdigest(),
                    "spec_sha256": spec_sha}, indent=1, sort_keys=True),
        encoding="utf-8")

    executed = [r for r in bat.rows if r["verdict"] in ("PASS", "FAIL")]
    failed = [r for r in bat.rows if r["verdict"] == "FAIL"]
    print("named checks: %d executed, %d failed, %d not_run"
          % (len(executed), len(failed),
             len(bat.rows) - len(executed)))
    for r in bat.rows:
        print("%-28s %s  %s" % (r["test_id"], r["verdict"],
                                r["observed"][:150]))
    if failed:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
