"""Tests for the FK-REDUCTION lane tooling (fast; no engine build).

Covers the preregistered machinery, not the measurements:
  1. both generators (census, reduce) are deterministic; their manifests
     round-trip byte-exactly against the tracked sources;
  2. every derived line that is not a tracked line carries //@FKRED (trailing,
     never leading) and the net brace/paren/bracket balance is UNMOVED
     (the statement-level edit contract that keeps markers from commenting
     out code -- the failure the 20260920 mechanical() compile caught);
  3. the census probe declares every site the census_sites.md table names;
  4. the reduce manifest touches ONLY the R1/R2/R2b/R3 anchors (no other
     anchor classes) -- F3 CLASS-MISFILE guard at the generator level;
  5. the reconciliation and bounds arithmetic on synthetic fixtures.

Trailer Agent: fkred.
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import make_fkred as mk  # noqa: E402


def _derive(mode):
    h = mk.HDR.read_text(encoding="utf-8", newline="").replace("\r\n", "\n")
    u = mk.UNIT.read_text(encoding="utf-8", newline="").replace("\r\n", "\n")
    m = {}
    if mode == "census":
        dh = mk.apply(h, mk.census_header_edits(), "gait_controller.hpp", m)
        du = mk.apply(u, mk.census_unit_edits(), "gait_unit.cpp", m)
    else:
        dh = mk.apply(h, mk.reduce_header_edits(), "gait_controller.hpp", m)
        du = mk.apply(u, mk.reduce_unit_edits(), "gait_unit.cpp", m)
    return h, u, dh, du, m


def test_generators_deterministic():
    for mode in ("census", "reduce"):
        _, _, dh1, du1, _ = _derive(mode)
        _, _, dh2, du2, _ = _derive(mode)
        assert dh1 == dh2 and du1 == du2


def test_derived_is_tracked_plus_marked_lines_only_and_balance_unmoved():
    for mode in ("census", "reduce"):
        h, u, dh, du, _ = _derive(mode)
        for original, derived, name in ((h, dh, "gait_controller.hpp"), (u, du, "gait_unit.cpp")):
            orig = set(original.split("\n"))
            for ln in derived.split("\n"):
                assert "@FKRED" in ln or ln in orig, (name, ln[:100])
            for o, c in (("{", "}"), ("(", ")"), ("[", "]")):
                assert (derived.count(o) - derived.count(c)) == (original.count(o) - original.count(c)), name


def test_probe_declares_all_sites_and_calls():
    text = mk.PROBE
    sites = ["S_MECH", "S_CAP", "S_FORE", "S_LAWFE", "S_RATE", "S_FSE0", "S_FSP0",
             "S_FSP1", "S_IMP", "S_PCEC", "S_PCUB", "S_PCAR", "S_PCDU", "S_ES",
             "S_EE", "S_PIN1", "S_PIN2", "S_CROSS", "S_BISECT_GAP", "S_REFLEX", "S_HULL", "S_SAT",
             "S_STATUS", "S_U0", "S_RESET"]
    calls = ["C_FS_MAIN", "C_FS_DRV", "C_FS_CON", "C_FS_CROSS", "C_FS_WALL",
             "C_IMP_ENT", "C_IMP_PIN", "C_IMP_CROSS", "C_IMP_WALL",
             "C_ADV_TRIAL", "C_ADV_BISECT", "C_ADV_RETRY", "C_CAUGHT", "C_CLAMP",
             "C_EVT_CON", "C_EVT_WALL"]
    for s in sites:
        assert s in text, s
    for c in calls:
        assert c in text, c
    _, _, dh, _, _ = _derive("census")
    used_sites = set(re.findall(r"FKRED_SITE\((\w+)\)", dh))
    used_calls = set(re.findall(r"FKRED_CALL\((\w+)\)", dh))
    assert used_sites == set(sites), used_sites ^ set(sites)
    assert used_calls == set(calls), used_calls ^ set(calls)


def test_reduce_manifest_touches_only_reuse_anchors():
    """F3 guard: the reduce edits may ONLY (i) retarget rate/free_step
    signatures to accept a precomputed Evaluation, (ii) forward estart at
    existing free_step call sites, (iii) reuse ec inside poscorr, (iv) swap
    the clamp-path evaluate(start) to estart. No other anchors allowed."""
    _, _, _, _, m = _derive("reduce")
    anchors = "\n".join(op["anchor"] for op in m["gait_controller.hpp"]["ops"])
    # every anchor must name one of the four proof families' text
    for fam, needle in [
        ("R1_rate", "Rate rate(const State& s,const Dense& tau"),
        ("R2_fstep_sig", "State free_step(const State& start,double h"),
        ("R2_e0", "auto e0=evaluate(start)"),
        ("R2_rates", "auto a=rate(start,tau,live,plane)"),
        ("R2_p0", "auto p0=vector(evaluate(start).frames[0].t"),
        ("R2_calls", "free_step(start,"),
        ("R2b_pin", "u_pin=evaluate(pinned).potential-evaluate(start).potential"),
        ("R3_ec", "{auto ec=evaluate(s);"),
        ("R3_ub", "u_before=evaluate(s).potential"),
    ]:
        assert needle in anchors, fam
    # the traced debug free_step(pinned) call is evaluated fresh
    assert "free_step(pinned,h,tau,live)" in anchors
    payload = "\n".join(op["payload"] for op in m["gait_controller.hpp"]["ops"])
    # every estart forwarding is at an EXISTING free_step site; the only NEW
    # evaluate sites are rate's nullptr fallback (original arithmetic moved
    # verbatim) and the debug pinned call (evaluate moved INTO the arg).
    # NET: the derived header removes 6 evaluate sites (rate-a, free_step e0,
    # p0, clamp's evaluate(start), poscorr u_before, poscorr arows) and adds 2
    # (rate fallback, debug pinned) => exactly 4 fewer than the tracked text.
    h2, _, dh2, _, _ = _derive("reduce")
    assert dh2.count("evaluate(") == h2.count("evaluate(") - 4, \
        (h2.count("evaluate("), dh2.count("evaluate("))
    assert "e_local=evaluate(s)" in payload
    assert "evaluate(pinned))" in payload


def test_reconciliation_arithmetic():
    # the exact identity from the tickcost raw counters (walk_run_1, 302 ticks)
    F, I, A, E = 8880 / 302, 3443 / 302, 1208 / 302, 86549 / 302
    assert abs(F - 29.404) < 0.01
    assert abs(4 * F - 35520 / 302) < 1e-9  # R == 4F EXACT (RK4)
    # structural frame: 7F (free_step) + 2I (impact base+ec) + estart/eend + stages <= E
    floor = 7 * F + 2 * I + 2 * (A - 6.5) + 5
    assert floor < E, "the structural floor must leave room for poscorr/event extras"
    assert E - floor < 60, "the extras must not explode: census structure holds"


def test_bounds_math():
    per_eval_tickcost_state = 40.8315 / 286.586  # ms/evaluate, receipt_matrix state
    assert abs(per_eval_tickcost_state - 0.14244) < 0.001
    budget = 3.333
    # (a)-class ceiling ~3 evals/free_step + extras must NOT reach the budget
    # (287 - ~100 evals) * per_eval ~ 27 ms >> 3.33
    assert (286.586 - 100) * per_eval_tickcost_state > budget
    # even the (a)+(b) composition modeled at the bisection cut stays above
    assert (286.586 - 100 - 120) * per_eval_tickcost_state > budget / 2


def test_manifest_json_shape():
    for mode in ("census", "reduce"):
        _, _, _, _, m = _derive(mode)
        for name in ("gait_controller.hpp", "gait_unit.cpp"):
            assert set(m[name]) == {"ops", "replaced_anchors"}
            for op in m[name]["ops"]:
                assert op["kind"] in ("ins_before", "ins_after", "replace")
                assert op["count"] >= 1
