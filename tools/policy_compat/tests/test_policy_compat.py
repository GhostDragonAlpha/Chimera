"""policy_compat unit tests.

Run: python -m pytest tools/policy_compat/tests -q
(from the repo root; the suite is self-contained and touches nothing outside
tools/policy_compat/ and its own tmp dirs.)
"""
from __future__ import annotations

import copy
import json
import os
import sys

import numpy as np
import pytest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, REPO)

from tools.policy_compat import SCHEMA_VERSION                          # noqa: E402
from tools.policy_compat.certificate import (INVENTORY_ITEMS,           # noqa: E402
                                             cert_hash, check_deploy,
                                             compat_key, issue_certificate,
                                             json_schema, sha256_hex,
                                             validate_certificate,
                                             verify_evidence_chain)
from tools.policy_compat.runner import (P3_DIR, PolicyCompatError,      # noqa: E402
                                        build_corpus, build_relation,
                                        inventory_block, load_bundle,
                                        policy_restore, policy_snapshot,
                                        requalify, run_closed_loop,
                                        scope_block)
from tools.policy_compat.scene_cpu import (SnapshotError, build_n,      # noqa: E402
                                           build_n1, derived_envelope,
                                           make_scene)


@pytest.fixture(scope="module")
def bundle():
    return load_bundle()


@pytest.fixture(scope="module")
def short_run(bundle):
    build_id, p = build_n()
    return run_closed_loop(bundle, build_id, p, 20260920, 45,
                           checkpoint_ticks=(30,))


# ------------------------------------------------------- certificate schema

def _chained_events():
    """A minimal valid two-event chain (the evidence-chain convention)."""
    initial = "0" * 64
    prev = sha256_hex(f"chain0:{initial}".encode())
    evs = []
    for t in (14, 29):
        s = sha256_hex(f"s{t}".encode())
        chain = sha256_hex(f"{prev}:{t}:state:{s}".encode())
        evs.append({"tick": t, "kind": "state", "state_sha256": s,
                    "chain_sha256": chain})
        prev = chain
    return initial, evs


def _minimal_cert():
    rel = {k: {"id": k} for k in ("policy_bundle", "physics_build",
                                  "runtime_profile", "body_domain", "test_suite")}
    inv = {"deployment_class": "surrogate",
           "items": [{"name": n, "snapshotable": True, "snapshot_key": n,
                      "contents": n} for n in INVENTORY_ITEMS],
           "registered_gaps": []}
    initial, evs = _chained_events()
    ev = {"initial_snapshot_sha256": initial, "events": evs,
          "periodic_stride": 15, "final_state_sha256": "1" * 64,
          "monitors": [{"name": "m", "pass": True, "detail_sha256": "2" * 64}],
          "trajectory_sha256": "3" * 64}
    scope = {"bodies": [], "skills": [], "transitions": [], "ranges": {},
             "horizons": {}, "bars": {b: b for b in (
                 "bounds_honored", "no_nan_inf", "no_intervention",
                 "contact_floor", "availability_exact", "velocity_envelope")},
             "non_regression_margins": [
                 {"name": "m", "quantity": "q", "bound": 1.0, "derivation": "d"}]}
    cert = issue_certificate(rel, inv, ev, scope, {"issued_by": "t", "lane": "t",
                                                   "base_commit": "t",
                                                   "prereg_receipt": "t",
                                                   "prereg_rule0_sha": "4" * 64})
    return cert


def test_round_trip_valid():
    cert = _minimal_cert()
    assert validate_certificate(cert) == []
    tampered = copy.deepcopy(cert)
    tampered["relation"]["physics_build"]["id"] = "other"
    assert any("compat_key" in v for v in validate_certificate(tampered))


def test_cert_hash_detects_any_byte():
    cert = _minimal_cert()
    for key_path in (("lane",), ("qualification_scope", "bodies")):
        t = copy.deepcopy(cert)
        if len(key_path) == 1:
            t[key_path[0]] = "moved"
        else:
            t[key_path[0]][key_path[1]] = ["moved"]
        errs = validate_certificate(t)
        assert any("cert_hash mismatch" in e for e in errs), key_path


def test_production_class_blocks_unresolved_gaps():
    cert = _minimal_cert()
    cert["restart_state_inventory"]["deployment_class"] = "production"
    cert["restart_state_inventory"]["registered_gaps"] = [
        {"name": "g", "item": "reflex_state", "status": "REGISTERED GAP",
         "cause": "c", "clears_when": "w"}]
    assert any("PRODUCTION" in v and "BLOCKED" in v
               for v in validate_certificate(cert))


def test_missing_inventory_item_invalidates():
    cert = _minimal_cert()
    cert["restart_state_inventory"]["items"].pop(3)  # held_command
    assert any("held_command" in v for v in validate_certificate(cert))


def test_evidence_chain_tamper_detected():
    cert = _minimal_cert()
    ev = cert["replay_evidence"]
    ok, detail = verify_evidence_chain(ev)
    assert ok, detail
    ev["events"][1]["state_sha256"] = "f" * 64
    ok, detail = verify_evidence_chain(ev)
    assert not ok and "tick 29" in detail


def test_margin_without_derivation_is_a_violation():
    cert = _minimal_cert()
    cert["qualification_scope"]["non_regression_margins"][0]["derivation"] = "  "
    assert any("DERIVATION REQUIRED" in v for v in validate_certificate(cert))


def test_deploy_gate_missing_and_mismatch():
    cert = _minimal_cert()
    req = {k: {"id": k} for k in ("policy_bundle", "physics_build",
                                  "runtime_profile", "body_domain", "test_suite")}
    assert check_deploy(req, None)["decision"] == "BLOCK"
    assert check_deploy(req, cert)["decision"] == "ALLOW"
    other = copy.deepcopy(req)
    other["physics_build"] = {"id": "foreign"}
    verdict = check_deploy(other, cert)
    assert verdict["decision"] == "BLOCK"
    assert any("compat_key" in r or "compatibility key mismatch" in r
               for r in verdict["reasons"])


def test_json_schema_wellformed():
    s = json_schema()
    assert s["$id"].startswith("chimera:policy_compat")
    assert set(s["required"]) >= {"relation", "replay_evidence",
                                  "restart_state_inventory",
                                  "qualification_scope", "cert_hash"}


# ------------------------------------------------------------- scene sanity

def test_scene_determinism_and_builds():
    _, pn = build_n()
    _, pn1 = build_n1()
    assert pn1["damping"] == pn["damping"] * 1.01
    a = make_scene("b", pn, 7)
    b = make_scene("b", pn, 7)
    a.begin([0.0, 1.0, 1.0, 1.25] * 2)
    b.begin([0.0, 1.0, 1.0, 1.25] * 2)
    cmd = np.float32([0.0, 1.1, 0.9, 1.2, 0.0, 1.0, 1.1, 1.3])
    for _ in range(50):
        a.step(cmd, [0.0] * 8)
        b.step(cmd, [0.0] * 8)
    assert a.state_sha256() == b.state_sha256()
    c = make_scene("b", pn1, 7)
    c.begin([0.0, 1.0, 1.0, 1.25] * 2)
    for _ in range(50):
        c.step(cmd, [0.0] * 8)
    assert c.state_sha256() != a.state_sha256()


def test_snapshot_round_trip_bit_exact():
    _, pn = build_n()
    scene = make_scene("b", pn, 11)
    scene.begin([0.0, 1.0, 1.0, 1.25] * 2)
    cmd = np.float32([0.05, 1.2, 0.8, 1.1, 0.0, 0.9, 1.3, 1.4])
    for _ in range(37):
        scene.step(cmd, [0.0] * 8)
    before = scene.state_sha256()
    snap = scene.snapshot()
    import json as _json
    rt = _json.loads(_json.dumps(snap))
    scene2 = make_scene("b", pn, 11)
    scene2.restore_snapshot(rt)
    assert scene2.state_sha256() == before
    assert scene2.observation_record() == scene.observation_record()


def test_incomplete_snapshot_refused_by_name():
    _, pn = build_n()
    scene = make_scene("b", pn, 11)
    scene.begin([0.0, 1.0, 1.0, 1.25] * 2)
    scene.step(np.float32([0.0, 1.0, 1.0, 1.25] * 2), [0.0] * 8)
    snap = scene.snapshot()
    for drop in ("rng_stream", "contact_warm_start_cache", "body_state"):
        broken = copy.deepcopy(snap)
        del broken[drop]
        with pytest.raises(SnapshotError) as ei:
            make_scene("b", pn, 11).restore_snapshot(broken)
        assert drop in str(ei.value)


def test_policy_snapshot_round_trip(bundle):
    build_id, p = build_n()
    res = run_closed_loop(bundle, build_id, p, 5, 40, checkpoint_ticks=(17,))
    pol = bundle["NumpyPolicy"](bundle["manifest"], bundle["params"])
    snap = res["snapshots"][17]
    policy_restore(pol, snap["policy"])
    full = json.loads(json.dumps(snap))
    assert full["policy"]["decision_phase"]["tick"] == 17
    with pytest.raises(PolicyCompatError):
        policy_restore(pol, {"decision_phase": snap["policy"]["decision_phase"]})


def test_derived_envelope_matches_prereg():
    env = derived_envelope()
    assert env["velocity_envelope_m_s"] == pytest.approx(2.977443609022557)
    assert env["openloop_crossbuild_margin_m_s"] == pytest.approx(0.03103119967715015)
    assert "0.95" in env["derivation"] and "1.01" in env["derivation"]


# ------------------------------------------------------- corpus + requalify

def test_corpus_reproduces_p3_recorded_bytes(bundle):
    corpus = build_corpus(bundle)
    with open(os.path.join(P3_DIR, "actions_run1.bin"), "rb") as f:
        p3_sha = sha256_hex(f.read())
    assert corpus["n_ticks"] == 900 and corpus["n_decisions"] == 60
    assert corpus["actions_sha256"] == p3_sha, (
        "the frozen loader's corpus must reproduce the P3 lane's own recorded "
        "fresh-process bytes (F-CHANNELS-INERT, independent re-verification)")


def test_requalify_refuses_action_replay(bundle, short_run, tmp_path):
    build_id, p = build_n()
    with pytest.raises(PolicyCompatError) as ei:
        requalify(bundle, build_id, p, 20260920, 45,
                  precomputed_actions=short_run["applied_per_tick"])
    assert "ACTION_REPLAY_REFUSED" in str(ei.value)
    with pytest.raises(PolicyCompatError) as ei2:
        requalify(bundle, build_id, p, 20260920, 45, mode="action_replay")
    assert "ACTION_REPLAY_REFUSED" in str(ei2.value)


def test_relation_and_blocks_shape(bundle):
    build_id, p = build_n()
    rel = build_relation(bundle, build_id, p)
    assert set(rel) == {"policy_bundle", "physics_build", "runtime_profile",
                        "body_domain", "test_suite"}
    assert rel["policy_bundle"]["manifest_hash"].startswith("9ca7e976")
    assert rel["physics_build"]["params_sha256"] is not None
    inv = inventory_block()
    assert inv["deployment_class"] == "surrogate"
    assert {i["name"] for i in inv["items"]} == set(INVENTORY_ITEMS)
    assert len(inv["registered_gaps"]) == 4
    scope = scope_block()
    assert scope["non_regression_margins"][0]["bound"] == pytest.approx(
        derived_envelope()["openloop_crossbuild_margin_m_s"])
