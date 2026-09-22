"""OBS-SPLIT-CHANNELS lane tests (agent/obs-split-channels-20260921).

The three lane falsifiers' unit-level faces:
- F-CHANNELS-INERT: FIELDS[:64] equals the frozen P3 v1 table (the 1b6d7749
  literal in legacy_v1_table.py), and a v1 consumer (64-length norm arrays)
  gets a bitwise-equal projection on legacy records;
- the pad_split group: mask semantics (pre-contact absent pair -> 0, first
  sample deltas -> 0, 'lohi' endpoint-signed channels -> 0, split_abs live
  under both orderings), and delta continuity across caller-owned prev_state;
- privileged ban over all 80 fields.
Run: python -m pytest tools/science_funnel/typeb_export/tests -q
"""
from __future__ import annotations

import json
import os
import sys
import tempfile

import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
EXPORT = os.path.dirname(HERE)
sys.path.insert(0, EXPORT)

import legacy_v1_table  # noqa: E402
import observation_schema as oschema  # noqa: E402
import pad_channels  # noqa: E402


def test_legacy_block_is_frozen_field_for_field():
    assert oschema.OBS_DIM == 80
    assert oschema.LEGACY_OBS_DIM == 64
    assert oschema.OBS_SCHEMA_VERSION == 2
    got = [{k: f[k] for k in ("name", "group", "source", "unit", "frame",
                              "privileged", "dtype", "shape")}
           for f in oschema.FIELDS[:64]]
    assert got == legacy_v1_table.LEGACY_FIELDS, \
        "the legacy 64-field block moved -- F-CHANNELS-INERT"


def test_pad_group_layout():
    names = oschema.FIELD_NAMES[64:]
    legs = ("hl", "hr")
    expect = ([f"pad_g_heel_{l}" for l in legs] + [f"pad_g_mp_{l}" for l in legs]
              + [f"pad_dg_heel_{l}" for l in legs] + [f"pad_dg_mp_{l}" for l in legs]
              + [f"pad_split_{l}" for l in legs] + [f"pad_split_rate_{l}" for l in legs]
              + [f"pad_split_abs_{l}" for l in legs]
              + [f"pad_split_abs_rate_{l}" for l in legs])
    assert names == expect
    for f in oschema.FIELDS[64:]:
        assert f["group"] == "pad_split" and f["privileged"] is False
        assert f["source"] == "pad_gaps"


def _proj(rec, dim=80):
    mean = np.zeros(dim, dtype=np.float32)
    std = np.ones(dim, dtype=np.float32)
    return oschema.project_trace(rec, mean, std, {})


def test_v1_consumer_projection_bitwise_legacy_record():
    # The v1 consumer (64-length norm arrays, the frozen manifest's dim) must
    # reproduce the ORIGINAL v1 projection bitwise on a legacy record: all 62
    # data positions equal the v2 projection's [0:62] (the frozen block), and
    # the two sensor_health positions carry the v1-width aggregates (the mean
    # computed BEFORE the self-fill -- the frozen v1 semantic). The one
    # declared v2 delta is exactly the sensor_health aggregates at the
    # consumer's dim.
    rec = dict(tick=10, phase_left=0.3, contact_count=2,
               available_groups=["gait_phase", "contact_aggregate"])
    obs80, mask80 = _proj(rec, 80)
    obs64, mask64 = _proj(rec, 64)
    i_mm, i_mf = (oschema.FIELD_NAMES.index("mask_mean"),
                  oschema.FIELD_NAMES.index("mask_frac_avail"))
    # all non-sensor_health legacy positions bitwise equal (the frozen block)
    keep = [i for i in range(64) if i not in (i_mm, i_mf)]
    assert np.array_equal(obs80[keep], obs64[keep])
    assert np.array_equal(mask80[keep], mask64[keep])
    # v1 width: the aggregates are the mean over the 64-wide pre-self-fill mask
    # (gait_phase delivers 2 channels, contact_aggregate 2 -> 4/64 = 0.0625)
    pre = mask64.copy()
    pre[i_mm:i_mf + 1] = 0.0
    assert float(obs64[i_mm]) == pytest.approx(float(np.mean(pre)), abs=1e-9)
    assert float(obs64[i_mf]) == pytest.approx(float(np.mean(pre)), abs=1e-9)
    # a v2 consumer's aggregates are covered by the dedicated sensor_health test
    # the undelivered pad channels are masked and mean-filled (0/1 identity norm)
    i = oschema.FIELD_NAMES.index("pad_split_abs_hl")
    assert mask80[i] == 0.0 and float(obs80[i]) == 0.0


def test_pad_mask_and_split_semantics_lohi():
    rec = dict(tick=100, available_groups=["pad_split"],
               pad_gaps={"hl": [1.0e-4, 3.0e-4]},
               pad_pair_ordering={"hl": "lohi"})
    obs, mask = _proj(rec)
    idx = oschema.FIELD_NAMES.index
    # endpoint identity not in the record -> declared unavailable, never invented
    for nm in ("pad_g_heel_hl", "pad_g_mp_hl", "pad_dg_heel_hl", "pad_dg_mp_hl",
               "pad_split_hl", "pad_split_rate_hl"):
        assert mask[idx(nm)] == 0.0, nm
    # ordering-free channels live
    assert mask[idx("pad_split_abs_hl")] == 1.0
    assert float(obs[idx("pad_split_abs_hl")]) == pytest.approx(2.0e-4, abs=1e-9)
    # the other leg is pre-contact: nothing delivered
    for nm in ("pad_g_heel_hr", "pad_split_abs_hr", "pad_split_abs_rate_hr"):
        assert mask[idx(nm)] == 0.0, nm
    # first delivered sample: no rate yet
    assert mask[idx("pad_split_abs_rate_hl")] == 0.0


def test_pad_delta_continuity_via_prev_state():
    idx = oschema.FIELD_NAMES.index
    zero = np.zeros(80, dtype=np.float32)
    one = np.ones(80, dtype=np.float32)
    rec1 = dict(tick=100, available_groups=["pad_split"],
                pad_gaps={"hl": [1.0e-4, 3.0e-4]},
                pad_pair_ordering={"hl": "heel_mp"})
    rec2 = dict(tick=101, available_groups=["pad_split"],
                pad_gaps={"hl": [1.5e-4, 3.0e-4]},
                pad_pair_ordering={"hl": "heel_mp"})
    prev = {}
    o1, m1 = oschema.project_trace(rec1, zero, one, prev)
    assert m1[idx("pad_split_abs_rate_hl")] == 0.0          # no previous sample
    assert float(o1[idx("pad_split_hl")]) == pytest.approx(2.0e-4, abs=1e-9)
    # caller maintains prev: key present iff the tick delivered the channel
    prev.update({"pad_g_heel_hl": 1.0e-4, "pad_g_mp_hl": 3.0e-4,
                 "pad_split_abs_hl": 2.0e-4, "pad_split_hl": 2.0e-4})
    o2, m2 = oschema.project_trace(rec2, zero, one, prev)
    assert float(o2[idx("pad_dg_heel_hl")]) == pytest.approx(0.5e-4, abs=1e-9)
    assert float(o2[idx("pad_dg_mp_hl")]) == pytest.approx(0.0, abs=1e-9)
    assert float(o2[idx("pad_split_rate_hl")]) == pytest.approx(-0.5e-4, abs=1e-9)
    # |1.5e-4 - 3.0e-4| = 1.5e-4 vs the previous 2.0e-4 -> the abs gap narrowed
    assert float(o2[idx("pad_split_abs_rate_hl")]) == pytest.approx(-0.5e-4, abs=1e-9)
    # a delivery gap pops the keys -> the next delta is unavailable
    prev.pop("pad_split_abs_hl")
    rec3 = dict(rec2, tick=102)
    o3, m3 = oschema.project_trace(rec3, zero, one, prev)
    assert m3[idx("pad_split_abs_rate_hl")] == 0.0


def test_pad_group_gate_and_sensor_health():
    # the group gate: a record whose available_groups omits pad_split delivers
    # nothing even with pad keys present (P3's group convention)
    rec = dict(tick=1, available_groups=["gait_phase"],
               pad_gaps={"hl": [0.0, 1.0]}, pad_pair_ordering={"hl": "lohi"})
    obs, mask = _proj(rec)
    assert mask[oschema.FIELD_NAMES.index("pad_split_abs_hl")] == 0.0
    # sensor_health observes the (80-wide) mask itself, by its declared v1
    # semantic: the mean is taken over the mask BEFORE the self-fill of the
    # two sensor_health positions (the frozen v1 behavior, at the consumer dim)
    rec2 = dict(tick=2, available_groups=["pad_split"],
                pad_gaps={"hl": [0.0, 1.0]}, pad_pair_ordering={"hl": "lohi"})
    obs2, mask2 = _proj(rec2)
    i_mm, i_mf = (oschema.FIELD_NAMES.index("mask_mean"),
                  oschema.FIELD_NAMES.index("mask_frac_avail"))
    pre = mask2.copy()
    pre[i_mm:i_mf + 1] = 0.0
    assert float(obs2[i_mm]) == pytest.approx(float(np.mean(pre)), abs=1e-7)
    assert mask2[i_mm] == 1.0 and mask2[i_mf] == 1.0  # self-filled after


def test_privileged_ban_all_80():
    for f in oschema.FIELDS:
        assert f["source"].split("[")[0] not in oschema.PRIVILEGED_SOURCES


def test_norm_dim_guard():
    rec = dict(tick=1, available_groups=["pad_split"], pad_gaps={"hl": [0.0, 1.0]})
    with pytest.raises(ValueError):
        oschema.project_trace(rec, np.zeros(10, dtype=np.float32),
                              np.ones(10, dtype=np.float32), {})


def test_parse_and_reconstruct_synthetic():
    # a minimal synthetic trace through the declared parse + reconstruction
    lines = [
        "WALK REFUSED tick 1: budget",
        "[dvfa] t=5 leg=1 br=h held=1 sg=0.10000 c=0.00800 cmd_y=0.100000000 pad_y=0.000200000 plant_y=0.000000000",
        "[dvfl] t=5 leg=1 g1=1.000000000e-04 g2=1.000000000e-04 edge=1.1e-05 hd=1 ht=3 tm=0.0 clr=-1 oth=0 dl=0",
        "WALK REFUSED tick 9: budget",
    ]
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False,
                                     encoding="utf-8") as tf:
        tf.write("\n".join(lines) + "\n")
        path = tf.name
    try:
        parsed = pad_channels.parse_wave4x_trace(path)
        assert parsed["refusal"] == (9, "budget")
        recon = pad_channels.reconstruct_pairs(parsed)
        p = recon["pairs"][5][1]
        # g_hi = 2*pad_y - g_lo = 4e-4 - 1e-4 = 3e-4 ; split_abs = 2e-4
        assert p["g_lo"] == 1.0e-4
        assert p["g_hi"] == pytest.approx(3.0e-4, abs=1e-9)
        assert p["split_abs"] == pytest.approx(2.0e-4, abs=1e-9)
        recs = pad_channels.build_records(recon)
        # the engine's hind array order: index 0 = left, 1 = right
        # (gait_controller.hpp: 'left_heel'->hind_heel_pt_[0], leg==0?"left":"right")
        assert recs[0]["pad_pair_ordering"]["hr"] == "lohi"
        assert recs[0]["pad_gaps"]["hr"] == [1.0e-4, pytest.approx(3.0e-4, abs=1e-9)]
        proj = pad_channels.project_records(recs)
        chan = pad_channels.channel_split_abs_series(recs, proj)
        assert chan["series"][5][1] == pytest.approx(2.0e-4, abs=1e-9)
        assert chan["masks"][5][1] == 1.0
    finally:
        os.unlink(path)
