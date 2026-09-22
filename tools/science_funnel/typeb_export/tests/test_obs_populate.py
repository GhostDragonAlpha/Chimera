"""THE OBS-POPULATE TESTS (lane/obs-populate-20260920).

The delivery's law, unit-tested WITHOUT the ephemeral trace: the derivation,
the group-gate delivery, the projection's field-21/mask behavior, the F1
separation mechanism (two bit-identical records split by the delivered field),
the STRUCTURAL per-foot reader claim (all-or-nothing 6-slot read vs the
4-paw body), the declared yaw_rate_prev side effect, and the frozen-table
pins this lane must not move.

Run: python -m pytest tools/science_funnel/typeb_export/tests/test_obs_populate.py -q
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
VALDIR = os.path.join(EXPORT, "..", "validation")
LANEDIR = os.path.join(VALDIR, "obs_populate_20260920")
IFREEZE = os.path.join(VALDIR, "policy_interface_freeze_20260920")
sys.path.insert(0, EXPORT)

import body_velocity as bvel  # noqa: E402
import legacy_v1_table  # noqa: E402
import observation_schema as oschema  # noqa: E402


def _frozen_mean_std() -> tuple[np.ndarray, np.ndarray]:
    """The frozen normalization (the interface table's per-field constants)."""
    table = json.load(open(os.path.join(IFREEZE, "observation_interface_v2.json"),
                           encoding="utf-8"))
    mean = np.zeros(oschema.OBS_DIM, dtype=np.float32)
    std = np.ones(oschema.OBS_DIM, dtype=np.float32)
    for f in table["fields"]:
        mean[f["index"]] = f["normalization"]["mean"]
        std[f["index"]] = f["normalization"]["std"]
    return mean, std


def _base_rec(tick: int) -> dict:
    return dict(
        tick=tick, phase_left=0.25, phase_right=0.75, phase_frac=0.25,
        phase_rate=1.0 / 30, contact_count=3, contact_count_prev=3,
        foot_contacts=None, foot_forces=None,
        intervention_reason="none", ticks_since_intervention=3000,
        hold_tick=tick % 15, is_decision_tick=tick % 15 == 0,
        ticks_since_reset=tick,
        available_groups=["gait_phase", "contact_aggregate", "command_clock",
                          "intervention", "sensor_health", "phase_dynamics"],
    )


# ---------- the derivation ----------

def test_com_vel_x_series_first_difference_at_the_walk_clock():
    dv = {0: dict(com_e=1.000000), 1: dict(com_e=1.002000),
          2: dict(com_e=1.004500), 3: dict(com_e=1.004400)}
    s = bvel.com_vel_x_series(dv)
    assert set(s) == {1, 2, 3}          # t0 has no predecessor: never delivered
    assert s[1] == pytest.approx(0.600, abs=1e-12)
    assert s[2] == pytest.approx(0.750, abs=1e-12)
    assert s[3] == pytest.approx(-0.030, abs=1e-12)


# ---------- the delivery ----------

def test_delivery_declares_group_and_carries_the_scalar():
    recs = [_base_rec(t) for t in range(3)]
    n = bvel.deliver_body_velocity(recs, {1: 0.65, 2: 0.66})
    assert n == 2                       # t0 excluded
    for rec in recs:                    # the GROUP is declared on every tick
        assert "body_velocity" in rec["available_groups"]
    assert bvel.COM_VEL_X_SOURCE_KEY not in recs[0]
    assert recs[1][bvel.COM_VEL_X_SOURCE_KEY] == 0.65
    # the frozen reader's own resolution of the declared source
    assert oschema.read_field("com_vel_x_heading", recs[1], {}) == 0.65
    assert oschema.read_field("com_vel_x_heading", recs[0], {}) is None


def test_projection_field21_available_t0_masked_neighbors_stay_masked():
    mean, std = _frozen_mean_std()
    recs = [_base_rec(t) for t in range(2)]
    bvel.deliver_body_velocity(recs, {1: 0.65})
    i = {n: oschema.FIELD_NAMES.index(n) for n in
         ("com_vel_x_heading", "com_vel_y_heading", "com_vel_z", "yaw_rate",
          "yaw_rate_prev")}
    for t, rec in enumerate(recs):
        obs, mask = oschema.project_trace(rec, mean, std, {})
        if t == 0:
            assert mask[i["com_vel_x_heading"]] == 0.0     # no predecessor
            assert obs[i["com_vel_x_heading"]] == mean[i["com_vel_x_heading"]]
        else:
            # the frozen body_velocity constants are the 0/1 never-available
            # placeholders -> raw passthrough under clip 8 (F4's declared cause)
            assert obs[i["com_vel_x_heading"]] == pytest.approx(0.65, abs=1e-6)
            assert mask[i["com_vel_x_heading"]] == 1.0
        for n in ("com_vel_y_heading", "com_vel_z", "yaw_rate"):
            assert mask[i[n]] == 0.0                       # not delivered
        # the DECLARED side effect: the frozen reader's group law gives
        # yaw_rate_prev its own default once the group is delivered
        assert mask[i["yaw_rate_prev"]] == 1.0
        assert obs[i["yaw_rate_prev"]] == 0.0


# ---------- the F1 separation mechanism ----------

def test_separation_bit_identical_records_split_by_field21_only():
    """The audit's mechanism, encoded: two ticks whose observations were
    bit-identical split EXACTLY at field 21 once it is delivered."""
    mean, std = _frozen_mean_std()
    a, b = _base_rec(8), _base_rec(38)
    b["ticks_since_reset"] = a["ticks_since_reset"]   # the projected clock equal
    # (hold_tick 8 == 38 mod 15; both non-decision ticks -- every projected
    # channel equal, only the record's tick key differs)
    obs0, _ = oschema.project_trace(a, mean, std, {})
    obs1, _ = oschema.project_trace(b, mean, std, {})
    assert obs0.tobytes() == obs1.tobytes()          # the aliased state
    recs = [a, b]
    bvel.deliver_body_velocity(recs, {8: 0.6627, 38: 0.6489})
    i21 = oschema.FIELD_NAMES.index("com_vel_x_heading")
    obs2, _ = oschema.project_trace(recs[0], mean, std, {})
    obs3, _ = oschema.project_trace(recs[1], mean, std, {})
    assert obs2.tobytes() != obs3.tobytes()          # F1: separated
    diff = np.nonzero(obs2 != obs3)[0].tolist()
    assert diff and set(diff) <= {i21}               # via field 21 ONLY


# ---------- the STRUCTURAL per-foot claim ----------

def test_per_foot_reader_is_all_or_nothing_structural_on_the_4paw_body():
    mean, std = _frozen_mean_std()
    rec = _base_rec(5)
    obs, mask = oschema.project_trace(rec, mean, std, {})
    idx = [oschema.FIELD_NAMES.index("foot_contact_%s" % s)
           for s in ("fl", "fr", "ml", "mr", "hl", "hr")]
    assert all(mask[k] == 0.0 for k in idx)          # undelivered -> masked
    # no lawful per-element delivery exists: the reader consumes a 6-float
    # vector, and a None element (an uninhabited slot) is a hard error -- the
    # interface-freeze lane's walker-shape finding, encoded. The group must be
    # DECLARED for the reader to be consulted at all (the group gate).
    rec2 = _base_rec(5)
    rec2["available_groups"] = rec2["available_groups"] + ["contact_per_foot"]
    rec2["foot_contacts"] = [1.0, 0.0, None, None, 0.0, 1.0]  # ml/mr: NO body
    with pytest.raises(TypeError):
        oschema.project_trace(rec2, mean, std, {})


# ---------- the pins this lane must not move ----------

def test_frozen_table_and_schema_version_untouched():
    assert oschema.OBS_SCHEMA_VERSION == 2 and oschema.OBS_DIM == 80
    assert oschema.LEGACY_OBS_DIM == 64
    assert [{k: f[k] for k in ("name", "group", "source", "unit", "frame",
                               "privileged", "dtype", "shape")}
            for f in oschema.FIELDS[:64]] == legacy_v1_table.LEGACY_FIELDS
    table = json.load(open(os.path.join(IFREEZE, "observation_interface_v2.json"),
                           encoding="utf-8"))
    f21 = next(f for f in table["fields"] if f["name"] == "com_vel_x_heading")
    assert f21["index"] == 21 and f21["group"] == "body_velocity"
    assert f21["source_trace_key"] == "com_vel[0]" and f21["unit"] == "m_s"
    assert f21["frame"] == "heading" and f21["availability_rule"] == "group_delivery"
    assert f21["normalization"]["mean"] == 0.0 and f21["normalization"]["std"] == 1.0


def test_lane_artifact_pair_ledger_matches_the_pinned_census():
    """The committed run artifacts: 21 pairs, all separated, zero survivors."""
    art = json.load(open(os.path.join(LANEDIR, "aliased_pairs_after.json"),
                         encoding="utf-8"))
    pinned = json.load(open(os.path.join(IFREEZE, "aliased_pairs.json"),
                            encoding="utf-8"))
    assert art["trace_sha256"] == pinned["trace_sha256"]
    assert art["control"]["matches_pinned_census"] is True
    assert art["control"]["aliased_pairs"] == 21
    assert art["aliased_pairs_after"] == []            # zero survivors
    assert art["verdict_f1"] == "GREEN"
    assert len(art["pair_ledger"]) == 21
    assert all(d["separated"] for d in art["pair_ledger"])
    assert all(d["differing_fields"][0] == "com_vel_x_heading"
               for d in art["pair_ledger"])
    assert art["delivery"]["delivered_ticks"] == 301
