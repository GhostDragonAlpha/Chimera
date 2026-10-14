"""The cert-dryrun lane's tests: identity binding, tamper semantics, conventions.

Unit tests run anywhere (no .tmp builds needed). Live-lane tests exercise the
real artifacts and skip cleanly when the lane has not run in this checkout.
"""
import copy
import json
import os

import pytest

from tools.policy_compat import engine_cert as ec
from tools.policy_compat.certificate import (canonical_json, cert_hash,
                                             check_deploy, compat_key,
                                             issue_certificate,
                                             validate_certificate)
from tools.policy_compat import snapshot_api

REPO = ec.REPO
LANE = ec.LANE


def _lane_run() -> bool:
    return os.path.exists(os.path.join(ec.TMP, "runs", "run1", "certificate.json"))


# ------------------------------------------------------- strip / dormancy

def test_strip_removes_snapshot_api_regions_with_nesting():
    src = "#include <x>\n#ifdef GAIT_SNAPSHOT_API\nint a;\n#ifdef OTHER\nint b;\n#endif\nint c;\n#endif\nint d;\n"
    assert ec._strip_snapshot_api(src) == "#include <x>\nint d;\n"


def test_strip_keeps_unrelated_conditionals():
    src = "#ifdef A\nint a;\n#endif\nint b;\n"
    assert ec._strip_snapshot_api(src) == src


def test_strip_on_the_real_copies_matches_shipped_on_every_nonblank_line():
    nat = ec.inst_dir()
    for rel, ship_rel in ec.SHIPPED_COUNTERPART.items():
        copy_text = ec.rd(os.path.join(nat, rel)).decode("utf-8")
        ship_text = ec.rd(os.path.join(REPO, ship_rel)).decode("utf-8")
        stripped = ec._strip_snapshot_api(copy_text).replace("\r\n", "\n")
        ship_lf = ship_text.replace("\r\n", "\n")
        assert ec._content_lines(stripped) == ec._content_lines(ship_lf), rel


def test_engine_identity_dormancy_and_conventions():
    ident = ec.engine_identity()
    assert ident["instrument_dormancy"]["pass"] is True
    assert ident["build_id"].startswith("engine-walk-instrument/")
    assert len(ident["build_id"]) == len("engine-walk-instrument/") + 16
    assert ident["scene_pin_sha256"] == ec.ANCHORS["scene_sha256"]
    # build_id is a pure function of the closure + harness + scene pin
    closure_sha = ident["engine_source_closure_sha256"]
    assert closure_sha == ec.sha256_hex(canonical_json(ident["closure"]))
    # no engine-provided build id exists: the identity says so, by name
    assert "NO engine-provided build id" in ident["kind"]


# --------------------------------------------------- tamper semantics

def _minimal_cert() -> dict:
    inventory = {
        "deployment_class": "production",
        "items": [{"name": n, "snapshotable": True, "contents": "x"}
                  for n in ("body_state", "contact_warm_start_cache", "reflex_state",
                            "held_command", "decision_phase", "controller_history",
                            "rng_stream", "world_state")],
        "registered_gaps": [],
    }
    evidence = {"initial_snapshot_sha256": "a" * 64,
                "events": [{"tick": 1, "kind": "state", "state_sha256": "b" * 64,
                            "chain_sha256": ec.sha256_hex(
                                ec.sha256_hex(f"chain0:{'a' * 64}".encode()).encode()
                                + f":1:state:{'b' * 64}".encode())}],
                "periodic_stride": 1, "final_state_sha256": "b" * 64,
                "monitors": [{"name": "m", "pass": True, "detail_sha256": "c" * 64}],
                "trajectory_sha256": "d" * 64}
    scope = {"bodies": [], "skills": [], "transitions": [], "ranges": {},
             "horizons": {}, "bars": {b: "x" for b in
                                      ("bounds_honored", "no_nan_inf", "no_intervention",
                                       "contact_floor", "availability_exact", "velocity_envelope")},
             "non_regression_margins": [{"name": "m", "quantity": "q", "bound": 0,
                                         "derivation": "derived"}]}
    relation = {k: {"v": k} for k in ("policy_bundle", "physics_build",
                                      "runtime_profile", "body_domain", "test_suite")}
    return issue_certificate(relation, inventory, evidence, scope,
                             {"issued_by": "t", "lane": "t", "base_commit": "t",
                              "prereg_receipt": "t", "prereg_rule0_sha": "e" * 64})


def test_minimal_production_certificate_validates():
    assert validate_certificate(_minimal_cert()) == []


def test_t1_bumped_state_hash_with_recomputed_cert_hash_is_caught_by_the_chain():
    cert = _minimal_cert()
    t = copy.deepcopy(cert)
    ev = t["replay_evidence"]["events"][0]["state_sha256"]
    t["replay_evidence"]["events"][0]["state_sha256"] = ("0" if ev[0] != "0" else "1") + ev[1:]
    t["cert_hash"] = cert_hash(t)  # a SELF-CONSISTENT forgery
    errs = validate_certificate(t)
    assert any("chain mismatch" in e for e in errs)


def test_t2_swapped_normalization_constant_is_rejected_at_both_layers():
    cert = _minimal_cert()
    req = dict(cert["relation"])
    t_stored = copy.deepcopy(cert)
    t_stored["relation"]["test_suite"] = {"v": "tampered"}
    errs = validate_certificate(t_stored)
    assert any("compat_key" in e for e in errs)
    # self-consistent variant: the deploy gate must BLOCK the true request
    t_self = copy.deepcopy(cert)
    t_self["relation"]["test_suite"] = {"v": "tampered"}
    t_self["compat_key"] = compat_key(t_self["relation"])
    t_self["cert_hash"] = cert_hash(t_self)
    assert validate_certificate(t_self) == []      # internally consistent...
    assert check_deploy(req, t_self)["decision"] == "BLOCK"  # ...but not THE certified bundle


def test_t3_stale_build_id_is_rejected_at_both_layers():
    cert = _minimal_cert()
    req = dict(cert["relation"])
    t = copy.deepcopy(cert)
    t["relation"]["physics_build"] = {"v": "stale"}
    errs = validate_certificate(t)
    assert any("compat_key" in e for e in errs)
    t["compat_key"] = compat_key(t["relation"])
    t["cert_hash"] = cert_hash(t)
    assert check_deploy(req, t)["decision"] == "BLOCK"


# ------------------------------------------------- live lane (skip-safe)

@pytest.mark.skipif(not _lane_run(), reason="cert-dryrun lane has not run in this checkout")
def test_lane_certificate_is_valid_and_production():
    cert = ec.rj(os.path.join(ec.TMP, "runs", "run1", "certificate.json"))
    assert validate_certificate(cert) == []
    assert cert["restart_state_inventory"]["deployment_class"] == "production"
    assert cert["relation"]["physics_build"]["build_id"].startswith("engine-walk-instrument/")


@pytest.mark.skipif(not _lane_run(), reason="cert-dryrun lane has not run in this checkout")
def test_lane_tamper_suite_three_for_three():
    rep = ec.rj(os.path.join(ec.TMP, "runs", "run1", "tamper_report.json"))
    assert rep["suite_pass"] is True
    for k in ("T1_bumped_state_hash", "T2_swapped_normalization_constant", "T3_stale_build_id"):
        assert rep[k]["rejected"] is True, k
    assert rep["clean_reissue"]["valid"] is True
    assert rep["clean_reissue"]["deploy"] == "ALLOW"


@pytest.mark.skipif(not _lane_run(), reason="cert-dryrun lane has not run in this checkout")
def test_lane_f4_payloads_byte_identical():
    shas = set()
    for i in (1, 2, 3):
        p = os.path.join(ec.TMP, f"payload_run{i}.json")
        if os.path.exists(p):
            shas.add(ec.sha256_hex(ec.rd(p)))
    assert len(shas) == 1, "the 3 pipeline runs' canonical payloads differ"
