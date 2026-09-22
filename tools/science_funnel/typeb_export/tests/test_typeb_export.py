"""TypeB-P3 unit tests + the observation-harness test against the recorded trace slice.

Run: python -m pytest tools/science_funnel/typeb_export/tests -q
"""
from __future__ import annotations

import copy
import json
import os
import sys

import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
EXPORT = os.path.dirname(HERE)
sys.path.insert(0, EXPORT)
VALDIR = os.path.join(EXPORT, "..", "validation", "typeb_p3_20260921")

import dummy_actor  # noqa: E402
import observation_schema as oschema  # noqa: E402
import policy_manifest as pman  # noqa: E402
from infer_numpy import NumpyPolicy, PolicyClock  # noqa: E402


@pytest.fixture(scope="module")
def manifest():
    return pman.load_manifest(os.path.join(VALDIR, "policy_manifest.json"),
                              os.path.join(VALDIR, "dummy_actor.npz"))


@pytest.fixture(scope="module")
def policy(manifest):
    params = dict(np.load(os.path.join(VALDIR, "dummy_actor.npz")))
    return NumpyPolicy(manifest, params)


# ---------- schema / loader ----------

def test_schema_is_64_fields_nonprivileged():
    # AMENDED by agent/obs-split-channels-20260921 (declared in its prereg,
    # frozen at 97fd15fb BEFORE the build): the schema version bump 64 -> 80
    # adds the pad_split group (the TYPE-B convergence's channels). The v1
    # contract is preserved as the frozen legacy block: FIELDS[:64] must equal
    # the v1 table field-for-field (asserted in
    # test_obs_split_channels.py against the 1b6d7749 literal) and the legacy
    # records still project bitwise-identically on [0:64].
    assert oschema.OBS_SCHEMA_VERSION == 2
    assert oschema.LEGACY_OBS_DIM == 64
    assert oschema.OBS_DIM == 80
    assert len(oschema.FIELDS) == 80
    assert len(set(oschema.FIELD_NAMES)) == 80
    for f in oschema.FIELDS:
        assert f["privileged"] is False
        assert f["source"].split("[")[0] not in oschema.PRIVILEGED_SOURCES


def test_actor_sizing_matches_astra():
    assert dummy_actor.param_count() == 25864
    assert dummy_actor.mac_count() == 25600


def test_weights_are_deterministic():
    a = dummy_actor.weights_sha256(dummy_actor.export_dummy_actor())
    b = dummy_actor.weights_sha256(dummy_actor.export_dummy_actor())
    assert a == b
    c = dummy_actor.weights_sha256(dummy_actor.export_dummy_actor(seed=1))
    assert c != a


def test_loader_rejects_tampered_weights(manifest):
    bad = copy.deepcopy(manifest)
    bad["policy"]["weights_sha256"] = "0" * 64
    errs = pman.validate_manifest(bad, b"not-the-weights")
    assert any("weights sha256 mismatch" in e for e in errs)
    # the loader itself must refuse bytes that do not match the pinned sha
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as tf:
        json.dump(bad, tf)
        tmp = tf.name
    try:
        with pytest.raises(ValueError, match="weights sha256 mismatch"):
            pman.load_manifest(tmp, os.path.join(VALDIR, "dummy_actor.npz"))
    finally:
        os.unlink(tmp)


def test_loader_rejects_privileged_field(manifest):
    bad = copy.deepcopy(manifest)
    name = bad["observation"]["order"][0]
    bad["observation"]["per_field"][name]["privileged"] = True
    errs = pman.validate_manifest(bad)
    assert any("privileged" in e for e in errs)


def test_loader_rejects_broken_clock(manifest):
    bad = copy.deepcopy(manifest)
    bad["action"]["clock"]["hold_ticks"] = 10
    assert any("clock" in e for e in pman.validate_manifest(bad))


# ---------- clock ----------

def test_clock_20hz_300hz_15hold():
    c = PolicyClock(20, 300, 15)
    assert c.is_decision_tick
    decisions = sum(c.is_decision_tick or True for _ in range(0))  # placeholder
    got = []
    for _ in range(300):
        if c.is_decision_tick:
            got.append(c.tick)
        c.advance()
    assert len(got) == 20 and got[0] == 0 and got[1] == 15
    with pytest.raises(AssertionError):
        PolicyClock(20, 300, 10)


# ---------- observation harness on the RECORDED slice ----------

@pytest.fixture(scope="module")
def trace_slice():
    with open(os.path.join(VALDIR, "trace_slice_wave38.json"), "rb") as f:
        return json.loads(f.read().decode("utf-8"))


def _project_all(manifest, slice_):
    mean = np.asarray(manifest["normalization"]["mean"], dtype=np.float32)
    std = np.asarray(manifest["normalization"]["std"], dtype=np.float32)
    zero = np.zeros(oschema.OBS_DIM, dtype=np.float32)
    out = []
    for rec in slice_["ticks"]:
        out.append(oschema.project_trace(rec, mean, std, {}))
    return out


def test_projection_reproduces_recorded_census(manifest, trace_slice):
    """The projection must reproduce the recorded wave-38 contact census exactly."""
    proj = _project_all(manifest, trace_slice)
    mean = np.asarray(manifest["normalization"]["mean"], dtype=np.float32)
    std = np.asarray(manifest["normalization"]["std"], dtype=np.float32)
    i_count = oschema.FIELD_NAMES.index("contact_count_norm")
    i_unl = oschema.FIELD_NAMES.index("unload_class_flag")
    i_hind = oschema.FIELD_NAMES.index("hind_step_class_flag")
    i_refusal = oschema.FIELD_NAMES.index("intv_refusal")

    def raw(i, t):
        return float(proj[t][0][i]) * float(std[i]) + float(mean[i])

    two = [t for t, rec in enumerate(trace_slice["ticks"])
           if rec.get("contact_count") == 2]
    assert two, "slice must contain the recorded two-contact windows"
    for t in two:
        assert abs(raw(i_count, t) - 2.0) < 1e-6, f"tick {t} census misread"
    # census-free ticks: aggregate stays mean-filled (unavailable), never invented
    off = [t for t in range(len(trace_slice["ticks"])) if t not in two]
    for t in off[:50]:
        rec = trace_slice["ticks"][t]
        if rec.get("contact_count") is None:
            assert abs(raw(i_count, t) - float(mean[i_count])) < 1e-6
    # real class ticks from the record
    unl = [t for t, rec in enumerate(trace_slice["ticks"]) if rec.get("unload_class")]
    for t in unl:
        assert abs(raw(i_unl, t) - 1.0) < 1e-6
    hind = [t for t, rec in enumerate(trace_slice["ticks"]) if rec.get("hind_step_class")]
    for t in hind:
        assert abs(raw(i_hind, t) - 1.0) < 1e-6
    # the real refusal tick fires the intervention one-hot; pre-refusal ticks do not.
    # Rare-event fields clip in normalized space (declared recipe), so assert there:
    # fired -> x = (1-mean)/std, far positive; not fired -> x = -mean/std, negative.
    rt = trace_slice["refused_tick"]
    x_fired = float(proj[rt][0][i_refusal])
    assert x_fired >= 4.0, "refusal one-hot must fire hard at the recorded refusal tick"
    assert all(float(proj[t][0][i_refusal]) < 0.0 for t in range(rt)), \
        "refusal one-hot must be silent on every pre-refusal tick"
    # phase clock: recorded cycle_ticks drive the phase fields (de-normalized check)
    i_psin = oschema.FIELD_NAMES.index("gait_phase_sin_left")
    ct = trace_slice["cycle_ticks"]
    t0 = 10
    expect_sin = float(np.sin(2 * np.pi * (t0 % ct) / ct))
    assert abs(raw(i_psin, t0) - expect_sin) < 1e-5


def test_projection_meanfills_unavailable_groups(manifest, trace_slice):
    proj = _project_all(manifest, trace_slice)
    mean = np.asarray(manifest["normalization"]["mean"], dtype=np.float32)
    i_fl = oschema.FIELD_NAMES.index("foot_contact_fl")
    i_vx = oschema.FIELD_NAMES.index("com_vel_x_heading")
    t = 5  # a tick with forces/velocity declared unavailable
    # unavailable channels sit at their mean-fill value = exactly 0.0 normalized
    assert float(proj[t][0][i_fl]) == 0.0
    assert float(proj[t][0][i_vx]) == 0.0
    # and the mask says so
    assert proj[t][1][i_fl] == 0.0


def test_projection_clips_normalized_space(manifest, trace_slice):
    proj = _project_all(manifest, trace_slice)
    for obs, _mask in proj[:100]:
        assert np.all(np.abs(obs) <= 8.0 + 1e-6)


# ---------- policy behavior ----------

def test_hold_semantics(policy, trace_slice):
    """Decisions every 15 ticks; applied commands held between decisions."""
    policy.reset()
    recs = trace_slice["ticks"]
    held_changes = 0
    prev = None
    for k in range(45):
        rec = dict(recs[k % len(recs)])
        rec["tick"] = k
        applied, info = policy.act(rec)
        if not info["deciding"] and prev is not None:
            if not np.array_equal(applied, prev):
                held_changes += 1
        prev = applied
    assert held_changes == 0, "commands must be zero-order held between decisions"
    assert policy.clock.decisions == 3  # ticks 0, 15, 30


def test_action_bounds_respected(policy, trace_slice):
    policy.reset()
    for k in range(120):
        rec = dict(trace_slice["ticks"][k % len(trace_slice["ticks"])]); rec["tick"] = k
        applied, _ = policy.act(rec)
        assert np.all(applied >= policy.lo - 1e-6)
        assert np.all(applied <= policy.hi + 1e-6)


def test_reset_semantics(policy):
    policy.reset()
    assert policy.clock.tick == 0 and policy.clock.is_decision_tick
    assert float(policy.prev_applied[0]) == float(policy.center[0])
    assert policy.ticks_since_intervention >= 10**6


def test_full_replay_matches_banked_stream(policy, trace_slice, manifest):
    """The harness replay of the fixed sequence reproduces the banked stream sha."""
    import hashlib
    from run_f_cpu_policy_bytes import fixed_obs_sequence, replay
    ev = manifest["evaluation"]["fixed_obs_sequence"]
    seq = fixed_obs_sequence(os.path.join(VALDIR, "trace_slice_wave38.json"),
                             ev["passes"], ev["n_ticks"])
    stream, decisions = replay(policy, seq)
    with open(os.path.join(VALDIR, "actions_run1.bin"), "rb") as f:
        banked = f.read()
    assert stream == banked
    assert len(decisions) == ev["n_decisions"] == 60
    with open(os.path.join(VALDIR, "actions_run1.json")) as f:
        assert hashlib.sha256(stream).hexdigest() == json.load(f)["sha256"]
