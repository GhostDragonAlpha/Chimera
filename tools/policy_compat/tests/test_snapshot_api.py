"""policy_compat :: the ENGINE snapshot-API registry tests.

Extends the upgrade-gate suite: the four registered engine gaps
(gap_engine_{contact_warm_start,reflex_state,controller_history,world_state})
close ONLY through a RESOLVED status with a VERIFIABLE proof block; a RESOLVED
gap without proof is a validator violation; the surrogate path's bytes and
verdicts are unchanged. Run: python -m pytest tools/policy_compat/tests -q
"""
from __future__ import annotations

import copy
import json
import os
import sys

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, REPO)

from tools.policy_compat.certificate import (cert_hash, check_deploy,  # noqa: E402
                                             compat_key, issue_certificate,
                                             validate_certificate)
from tools.policy_compat import snapshot_api                      # noqa: E402
from tools.policy_compat.runner import inventory_block             # noqa: E402


# ------------------------------------------------------------- helpers

def synthetic_relation():
    return {k: {"component": k, "sha256": "0" * 64} for k in
            ("policy_bundle", "physics_build", "runtime_profile",
             "body_domain", "test_suite")}


def synthetic_evidence():
    from tools.policy_compat.certificate import sha256_hex
    initial = sha256_hex(b"initial")
    chain0 = sha256_hex(f"chain0:{initial}".encode("utf-8"))
    state = sha256_hex(b"state0")
    ev = {"tick": 0, "kind": "state", "state_sha256": state,
          "chain_sha256": sha256_hex(f"{chain0}:0:state:{state}".encode("utf-8"))}
    return {"initial_snapshot_sha256": initial,
            "events": [ev], "periodic_stride": 15,
            "final_state_sha256": state,
            "monitors": [{"name": "m", "pass": True, "detail_sha256": state}],
            "trajectory_sha256": state}


def synthetic_scope():
    return {"bodies": ["b"], "skills": ["s"], "transitions": ["t"],
            "ranges": {}, "horizons": {"ticks": 1},
            "bars": {"bounds_honored": 1, "no_nan_inf": 1, "no_intervention": 1,
                     "contact_floor": 1, "availability_exact": 1,
                     "velocity_envelope": 1},
            "non_regression_margins": [{"name": "m", "quantity": "q", "bound": 1,
                                        "derivation": "derived for the test"}]}


CANONICAL_ITEMS = ("body_state", "contact_warm_start_cache", "reflex_state",
                   "held_command", "decision_phase", "controller_history",
                   "rng_stream", "world_state")


def production_items():
    return [{"name": n, "snapshotable": True, "contents": "x"} for n in CANONICAL_ITEMS]


def make_cert(inventory):
    return issue_certificate(synthetic_relation(), inventory, synthetic_evidence(),
                             synthetic_scope(),
                             {"issued_by": "test", "lane": "test", "base_commit": "0" * 8,
                              "prereg_receipt": "r", "prereg_rule0_sha": "0" * 64})


def proof_block(**over):
    base = {"reader": "gait_snapshot_api/test", "kind": "out-of-tree build flag",
            "proof_receipt_sha256": "a" * 64, "restore_bit_identity": True,
            "ship_invariance": "PASS", "load_bearing_forced_drops": True}
    base.update(over)
    return base


_UNSET = object()


def resolved_gap(item="world_state", proof=_UNSET, **proof_over):
    """proof= replaces the whole proof block (named so the parametrize's
    {'proof': ...} mutations land at the GAP level, not inside the block)."""
    return {"name": f"gap_engine_{item}", "item": item,
            "status": "RESOLVED (snapshot-api reader + proof)",
            "cause": "closed by the reader", "clears_when": "n/a",
            "proof": proof_block(**proof_over) if proof is _UNSET else proof}


def unresolved_gap(item="world_state"):
    return {"name": f"gap_engine_{item}", "item": item,
            "status": "REGISTERED GAP (pending engine binding)",
            "cause": "not yet exposed", "clears_when": "engine snapshot API"}


# ----------------------------------------------- the surrogate path: unchanged

def test_surrogate_inventory_still_validates_with_unresolved_gaps():
    inv = inventory_block()
    assert inv["deployment_class"] == "surrogate"
    unresolved = [g for g in inv["registered_gaps"]
                  if "RESOLVED" not in g["status"].upper()]
    assert len(unresolved) == 4  # the four engine gaps, still registered
    cert = make_cert(inv)
    assert validate_certificate(cert) == []


def test_production_with_unresolved_gaps_still_blocked():
    inv = {"deployment_class": "production", "items": production_items(),
           "registered_gaps": [unresolved_gap(item) for item in
                               ("contact_warm_start", "reflex_state",
                                "controller_history", "world_state")]}
    errs = validate_certificate(make_cert(inv))
    assert any("PRODUCTION certificate with UNRESOLVED registered gaps" in e for e in errs)


# ------------------------------------------------- RESOLVED gaps need PROOF

def test_resolved_gap_with_full_proof_validates():
    inv = {"deployment_class": "production", "items": production_items(),
           "registered_gaps": [resolved_gap(item) for item in
                               ("contact_warm_start_cache", "reflex_state",
                                "controller_history", "world_state")]}
    assert validate_certificate(make_cert(inv)) == []


@pytest.mark.parametrize("mutation,fragment", [
    ({"proof": None}, "NO proof block"),
    ({"proof": {"reader": "x"}}, "proof missing fields"),
    ({"restore_bit_identity": False}, "restore_bit_identity is not True"),
    ({"ship_invariance": "DRIFT"}, "ship_invariance is not PASS"),
    ({"load_bearing_forced_drops": False}, "load_bearing_forced_drops is not True"),
    ({"proof_receipt_sha256": "nothex"}, "not a sha256 hex digest"),
])
def test_resolved_gap_without_verifiable_proof_is_a_violation(mutation, fragment):
    g = resolved_gap(**mutation)
    inv = {"deployment_class": "production", "items": production_items(),
           "registered_gaps": [g]}
    errs = validate_certificate(make_cert(inv))
    assert any(fragment in e for e in errs), errs


def test_resolved_gap_accepted_in_surrogate_class_too():
    """The proof contract is class-independent; the surrogate class may also
    carry resolved gaps (this is how a build upgrades its own inventory)."""
    inv = inventory_block()
    inv = copy.deepcopy(inv)
    inv["registered_gaps"] = [resolved_gap(item) for item in
                              ("contact_warm_start_cache", "reflex_state",
                               "controller_history", "world_state")]
    assert validate_certificate(make_cert(inv)) == []


# --------------------------------------------- the ENGINE registry (live lane)

LANE = snapshot_api.LANE_DIR


def _lane_proofs_present():
    return os.path.exists(os.path.join(LANE, "runs", "proof_compare.json"))


@pytest.mark.skipif(not _lane_proofs_present(), reason="lane proof artifacts not yet run")
def test_lane_proofs_verify_green():
    ok, reasons = snapshot_api.verify_lane_proofs()
    assert ok, reasons


@pytest.mark.skipif(not _lane_proofs_present(), reason="lane proof artifacts not yet run")
def test_registry_completeness_manifest_covers_prereg_classes():
    ok, reasons = snapshot_api.check_registry_completeness()
    assert ok, reasons


@pytest.mark.skipif(not _lane_proofs_present(), reason="lane proof artifacts not yet run")
def test_production_inventory_closes_all_four_gaps():
    inv = snapshot_api.production_inventory()
    assert inv["deployment_class"] == "production"
    assert all("RESOLVED" in g["status"] for g in inv["registered_gaps"])
    assert len(inv["registered_gaps"]) == 4
    cert = make_cert(inv)
    assert validate_certificate(cert) == []
    # and a production deploy gate now ALLOWs on a matching relation
    req = {k: dict(v) for k, v in cert["relation"].items()}
    assert check_deploy(req, cert)["decision"] == "ALLOW"
    foreign = copy.deepcopy(req)
    foreign["physics_build"]["sha256"] = "1" * 64
    assert check_deploy(foreign, cert)["decision"] == "BLOCK"


def test_registry_fails_safe_without_artifacts(tmp_path):
    gaps, reasons = snapshot_api.engine_gap_registry(lane_dir=str(tmp_path))
    assert reasons  # the missing artifacts are named
    assert all("RESOLVED" not in g["status"].upper() for g in gaps)


def test_engine_registry_names_all_four_registered_gaps():
    assert {g["name"] for g in snapshot_api.ENGINE_GAPS} == {
        "gap_engine_contact_warm_start", "gap_engine_reflex_state",
        "gap_engine_controller_history", "gap_engine_world_state"}
