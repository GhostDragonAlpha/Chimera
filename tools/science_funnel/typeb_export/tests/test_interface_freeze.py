"""THE INTERFACE-FREEZE TESTS (lane/policy-interface-freeze-20260920).

F2 FREEZE-DRIFT: the frozen tables are pinned; any change without a declared
version bump fails here. Plus the projection law's bit-identity tests, the
certificate validator, the manifest backward-compatibility pin, and the
3-run byte-identity replay.

Run: python -m pytest tools/science_funnel/typeb_export/tests/test_interface_freeze.py -q
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import struct
import sys

import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
EXPORT = os.path.dirname(HERE)
VALDIR = os.path.join(EXPORT, "..", "validation")
LANEDIR = os.path.join(VALDIR, "policy_interface_freeze_20260920")
P3VAL = os.path.join(VALDIR, "typeb_p3_20260921")
OBSSPLIT = os.path.join(VALDIR, "obs_split_channels_20260921")
sys.path.insert(0, EXPORT)

import command_record as crec  # noqa: E402
import dummy_actor  # noqa: E402
import interface_freeze  # noqa: E402
import legacy_v1_table  # noqa: E402
import observation_schema as oschema  # noqa: E402
import option_certificate as oCert  # noqa: E402
import policy_manifest as pman  # noqa: E402
from infer_numpy import NumpyPolicy  # noqa: E402
from run_f_cpu_policy_bytes import fixed_obs_sequence, replay  # noqa: E402

# ---- the pre-lane pins (prereg_policy_interface_freeze.json) ----------------
P3_MANIFEST_HASH = "9ca7e976dfb0dedd3f56dfa404673ee77c00801acb2753cdfd83604c480c35b7"
P3_REPLAY_SHA = "e25406e86cbf5347683ee3824d385bc1d07bfd500e83eb6b9133a1e82d4bfbd9"
SECTION_SHA = "3de82a1156ac2f39ed04da24c7fd40357642d7bc029e09b509dfc3ea1af63079"


# ---------- F2: the 80-field interface table ---------------------------------

def test_interface_table_regenerates_byte_identical():
    """F2 pin: the committed table == the live code's regeneration, BYTES."""
    committed = open(os.path.join(LANEDIR, "observation_interface_v2.json"), "rb").read()
    regen = interface_freeze.regen_bytes(os.path.join(OBSSPLIT, "obs_section_v2.json"))
    assert committed == regen, (
        "the frozen interface table drifted from the live schema -- this is F2: "
        "bump OBS_SCHEMA_VERSION / INTERFACE_FREEZE_VERSION together, regenerate, "
        "re-review, and recommit")


def test_interface_table_shape_and_versions():
    table = json.loads(open(os.path.join(LANEDIR, "observation_interface_v2.json"),
                            encoding="utf-8").read())
    assert table["kind"] == "policy_observation_interface"
    assert table["interface_freeze_version"] == interface_freeze.INTERFACE_FREEZE_VERSION
    assert table["obs_schema_version"] == oschema.OBS_SCHEMA_VERSION == 2
    assert table["dim"] == oschema.OBS_DIM == 80
    assert table["legacy_dim"] == oschema.LEGACY_OBS_DIM == 64
    assert len(table["fields"]) == 80
    assert [f["index"] for f in table["fields"]] == list(range(80))
    assert table["order"] == oschema.FIELD_NAMES
    assert table["normalization_source"]["sha256"] == SECTION_SHA
    assert table["privileged_forbidden"] is True
    for f in table["fields"]:
        assert f["meaning"] and f["unit"] and f["frame"] and f["availability_rule"]
        assert f["missing_value_semantics"]
        assert set(f["normalization"]) >= {"mean", "std", "clip"}


def test_legacy_block_frozen_v1_literal():
    got = [{k: f[k] for k in ("name", "group", "source", "unit", "frame",
                              "privileged", "dtype", "shape")}
           for f in oschema.FIELDS[:64]]
    assert got == legacy_v1_table.LEGACY_FIELDS


def test_table_normalization_matches_pinned_section():
    section = json.loads(open(os.path.join(OBSSPLIT, "obs_section_v2.json"),
                              encoding="utf-8").read())
    table = json.loads(open(os.path.join(LANEDIR, "observation_interface_v2.json"),
                            encoding="utf-8").read())
    for f in table["fields"]:
        pf = section["per_field"][f["name"]]
        assert f["normalization"]["mean"] == pf["mean"]
        assert f["normalization"]["std"] == pf["std"]
        assert f["normalization"]["clip"] == 8.0


# ---------- the command record v1 + the projection law -----------------------

def test_command_record_domain_and_canonical_bytes():
    r = crec.CommandRecord(v_forward=0.5, yaw_rate=0.0, issued_tick=150)
    b = r.canonical_bytes()
    assert json.loads(b) == {"record_version": 1, "v_forward": 0.5, "yaw_rate": 0.0,
                             "issued_tick": 150, "source": "planner"}
    assert r.canonical_sha256() == hashlib.sha256(b).hexdigest()
    with pytest.raises(crec.CommandRecordError):
        crec.CommandRecord(v_forward=-0.1)          # the plant law's own domain
    with pytest.raises(crec.CommandRecordError):
        crec.CommandRecord(v_forward=float("nan"))
    with pytest.raises(crec.CommandRecordError):
        crec.CommandRecord(v_forward=0.5, record_version=2)  # v2 is a NEW declared format


def test_projection_law_v2_record_through_v1_adapter_bit_identical():
    """THE LAW's test: a v2 wire (extra fields, bumped declared version) through
    the v1 decoder + v1 adapter == the v1 wire's projection, bit for bit."""
    v1_wire = {"record_version": 1, "v_forward": 0.418500, "yaw_rate": -0.27,
               "issued_tick": 150, "source": "planner/test"}
    v2_wire = {"record_version": 2, "v_forward": 0.418500, "yaw_rate": -0.27,
               "issued_tick": 150, "source": "planner/test",
               # every future field imaginable -- none may leak:
               "stopping_target_m": 3.25, "gait_freq_scale": 1.1,
               "planner_epoch": 7, "certified_option": "walk_v1"}
    assert crec.wire_version(v1_wire) == 1 and crec.wire_version(v2_wire) == 2
    r1, r2 = crec.decode_v1(v1_wire), crec.decode_v1(v2_wire)
    ad = crec.V1FamilyAdapter()
    assert r1.v1_field_bits() == r2.v1_field_bits()
    assert struct.pack("<d", 0.418500) + struct.pack("<d", -0.27) == r1.v1_field_bits()
    assert ad.projection_bytes(r1) == ad.projection_bytes(r2)
    assert ad.project_to_actor_conditioning(r1) == b"" == ad.project_to_actor_conditioning(r2)
    p = ad.project(r1)
    assert p["commanded_target_velocity_x"] == 0.418500   # float64 passthrough, no clamp
    assert p["routed_yaw_rate"] is False                   # carried, NO route (reserved)


def test_old_actor_gets_exactly_its_old_projection():
    """Law clause 2: the v1 actor conditioning is EMPTY; the actor's own 8-dim
    output path (the limiter mapping) is untouched by the adapter."""
    ad = crec.V1FamilyAdapter()
    r = crec.CommandRecord(v_forward=0.763625, issued_tick=0)
    assert ad.project_to_actor_conditioning(r) == b""
    # and the projection never touches the actor's action mapping:
    m = pman.load_manifest(os.path.join(P3VAL, "policy_manifest.json"),
                           os.path.join(P3VAL, "dummy_actor.npz"))
    assert m["action"]["mapping"] == \
        "applied = clip(center + scale * raw, lo, hi) -- the command limiter; requested==applied except where clipped"


def test_command_record_declared_semantics():
    assert crec.RANGES["v_forward"]["in_band_hi"] == 0.763625
    assert crec.RANGES["v_forward"]["domain_lo"] == 0.0
    assert crec.RANGES["yaw_rate"]["authority"].startswith("NONE")
    assert crec.RATE_LIMITS["v_forward_per_s"] is None   # declared, not invented
    assert crec.RATE_LIMITS["yaw_rate_per_s"] is None
    assert "NOT a stop bar" in crec.ZERO_SPEED_SEMANTICS
    assert "constant seed" in crec.R4_SEMANTIC_CONSTRAINT


# ---------- the option certificates ------------------------------------------

def test_declared_certificates_validate():
    reg = oCert.declared_registry(oschema.FIELD_NAMES)
    verdicts = reg.revalidate_all()
    for name, errs in verdicts.items():
        assert errs == [], f"{name}: {errs}"
    assert set(reg.certs) == {"walk_v1", "recovery_v1", "rear_up_v1"}
    # the fallback graph closes: walk -> recovery -> rear_up -> recovery
    assert reg.get("walk_v1")["named_fallback"] == "recovery_v1"
    assert reg.get("recovery_v1")["named_fallback"] == "rear_up_v1"
    assert reg.get("rear_up_v1")["named_fallback"] == "recovery_v1"


def test_certificate_validator_catches_drift():
    good = oCert.declared_examples()[0]
    field_names = oschema.FIELD_NAMES
    assert pman  # imported for symmetry of the freeze suite
    assert oCert.validate_certificate(good, field_names, {"recovery_v1"}) == []
    bad = copy.deepcopy(good)
    bad["entry_guard"][0]["field"] = "root_pose_x"          # a PRIVILEGED invention
    assert any("vocabulary" in e for e in
               oCert.validate_certificate(bad, field_names, {"recovery_v1"}))
    bad = copy.deepcopy(good)
    bad["named_fallback"] = "teleport_v1"                    # unregistered fallback
    assert any("not a registered option" in e for e in
               oCert.validate_certificate(bad, field_names, {"recovery_v1"}))
    bad = copy.deepcopy(good)
    bad["command_payload"]["command_record_version"] = 2     # undecreed payload
    assert any("command_record_version" in e for e in
               oCert.validate_certificate(bad, field_names, {"recovery_v1"}))
    bad = copy.deepcopy(good)
    del bad["registered_timeout"]                            # timeout discipline
    assert any("registered_timeout" in e for e in
               oCert.validate_certificate(bad, field_names, {"recovery_v1"}))
    bad = copy.deepcopy(good)
    bad["entry_guard"][0]["op"] = "~="                       # no invented predicates
    assert any("op" in e for e in
               oCert.validate_certificate(bad, field_names, {"recovery_v1"}))


def test_certificate_guard_evaluates_through_the_frozen_reader():
    """A guard's semantics == the deployed projection's semantics (the public
    read_field delegate), proven on a real trace record from the audit's
    declared examples."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "mine_aliasing_audit",
        os.path.join(LANEDIR, "mine_aliasing_audit.py"))
    mine = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mine)
    repo = os.path.abspath(os.path.join(EXPORT, "..", "..", ".."))
    trace = os.path.normpath(os.path.join(repo, ".tmp", "ifreeze", "audit",
                                          "audit_stderr.txt"))
    if not os.path.exists(trace):
        pytest.skip("the audit trace is ephemeral (.tmp); the receipt pins its sha")
    parsed = mine.parse_run(trace)
    recs, _ = mine.build(parsed)
    reg = oCert.declared_registry(oschema.FIELD_NAMES)
    guard = reg.get("walk_v1")["entry_guard"]
    entered = 0
    for rec in recs[60:300]:   # outside the settle window
        vals = [oCert.evaluate_predicate(p, oschema.read_field, rec, {})
                for p in guard]
        if all(v is True for v in vals):
            entered += 1
    assert entered > 0, "the walk_v1 guard must admit post-settle walk ticks"


# ---------- F2: the manifest backward compatibility --------------------------

def test_existing_manifest_loads_with_pinned_hash():
    """The P3 manifest (no inference_freeze block) must load exactly as before
    this lane: same violations-free validation, same canonical hash."""
    m = pman.load_manifest(os.path.join(P3VAL, "policy_manifest.json"),
                           os.path.join(P3VAL, "dummy_actor.npz"))
    assert m["manifest_hash"] == P3_MANIFEST_HASH


def test_inference_freeze_block_validates_and_binds():
    m = json.loads(open(os.path.join(P3VAL, "policy_manifest.json"), "rb").read()
                   .decode("utf-8"))
    wb = open(os.path.join(P3VAL, "dummy_actor.npz"), "rb").read()
    norm = m["normalization"]
    blk = pman.inference_freeze_block(wb, norm["mean"], norm["std"], norm["clip"],
                                      m["action"]["clock"])
    assert blk["deployment_inference_version"] == pman.DEPLOYMENT_INFERENCE_VERSION
    extended = dict(m, inference_freeze=blk)
    assert pman.validate_manifest(extended, wb) == []
    # the block binds: every frozen fact is caught when tampered
    tam = copy.deepcopy(extended)
    tam["inference_freeze"]["deterministic_action_selection"] = False
    assert pman.validate_manifest(tam, wb)
    tam = copy.deepcopy(extended)
    tam["inference_freeze"]["exported_graph"]["graph_sha256"] = "0" * 64
    assert any("graph_sha256" in e for e in pman.validate_manifest(tam, wb))
    tam = copy.deepcopy(extended)
    tam["inference_freeze"]["normalization_constants"]["digest_sha256"] = "0" * 64
    assert any("digest_sha256" in e for e in pman.validate_manifest(tam, wb))
    tam = copy.deepcopy(extended)
    tam["inference_freeze"]["precision"]["storage"] = "float16"
    assert any("precision" in e for e in pman.validate_manifest(tam, wb))
    tam = copy.deepcopy(extended)
    tam["inference_freeze"]["clock"]["hold_ticks"] = 10
    assert any("clock" in e for e in pman.validate_manifest(tam, wb))
    # and the extension MOVES the canonical hash (F-CPU-POLICY-BYTES discipline):
    assert pman.manifest_hash(extended) != P3_MANIFEST_HASH


# ---------- the 3-run byte-identity replay ------------------------------------

def test_p3_action_stream_replay_3run_byte_identity():
    """The frozen P3 manifest + actor replay the fixed sequence to the banked
    stream, byte-identically, THREE runs in this process (the replay law this
    freeze inherits; the banked sha is the obs-split lane's pin)."""
    manifest = pman.load_manifest(os.path.join(P3VAL, "policy_manifest.json"),
                                  os.path.join(P3VAL, "dummy_actor.npz"))
    params = dict(np.load(os.path.join(P3VAL, "dummy_actor.npz")))
    ev = manifest["evaluation"]["fixed_obs_sequence"]
    seq = fixed_obs_sequence(os.path.join(P3VAL, "trace_slice_wave38.json"),
                             ev["passes"], ev["n_ticks"])
    shas = set()
    for _ in range(3):
        policy = NumpyPolicy(manifest, params)
        stream, decisions = replay(policy, seq)
        assert len(decisions) == ev["n_decisions"] == 60
        shas.add(hashlib.sha256(stream).hexdigest())
    assert len(shas) == 1
    assert shas.pop() == P3_REPLAY_SHA
