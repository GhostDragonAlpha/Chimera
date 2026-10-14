#!/usr/bin/env python3
"""Generate obs_section_v2.json -- THE MANIFEST'S OBSERVATION SECTION for the
extended schema (the manifest block the P4 trainer lane binds; the actor resize
64 -> 80 inputs is that lane's contract, recorded here).

Normalization = P3's recipe verbatim (build_policy_manifest.normalization_from_slice):
per-field mean/std over the ticks where the lane's record set actually delivers
the channel; never-available -> mean 0, std 1 (the mask carries the
unavailability); std floored at 1e-3. The record set here is the reconstructed
wave-47 channel set (band_channels_wave47.json, pinned to the trace sha
c6f9b6c0...), so the split channels' normalization derives from REAL measured
traces, and the endpoint-identity fields are declared never-available ON THIS
RECORD SET (0/1) exactly because the preserved outputs do not carry the
endpoint identity -- the future instrument's logs will.
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
EXPORT = os.path.join(REPO, "tools", "science_funnel", "typeb_export")
sys.path.insert(0, EXPORT)

import observation_schema as oschema  # noqa: E402
import pad_channels  # noqa: E402

TRACE = os.environ.get(
    "W47_TRACE",
    r"E:\ChimeraWork\w47-agent\.tmp\w47_receipt\base_tr_stderr.txt")

parsed = pad_channels.parse_wave4x_trace(TRACE, expect_sha256=pad_channels.WAVE47_TRACE_SHA256)
recon = pad_channels.reconstruct_pairs(parsed)
records = pad_channels.build_records(recon)

# P3's recipe verbatim over the lane record set (identity normalization in,
# raw values out)
mean = np.zeros(oschema.OBS_DIM, dtype=np.float64)
std = np.ones(oschema.OBS_DIM, dtype=np.float64)
counts = np.zeros(oschema.OBS_DIM, dtype=np.int64)
sums = np.zeros(oschema.OBS_DIM, dtype=np.float64)
sqsums = np.zeros(oschema.OBS_DIM, dtype=np.float64)
zero = np.zeros(oschema.OBS_DIM, dtype=np.float32)
prev = {}
for rec in records:
    obs, mask = oschema.project_trace(rec, zero, np.ones_like(zero), prev)
    for i in range(oschema.OBS_DIM):
        if mask[i] > 0:
            counts[i] += 1
            sums[i] += float(obs[i])
            sqsums[i] += float(obs[i]) ** 2
    # same prev maintenance as the lane projector
    gaps = rec.get("pad_gaps") or {}
    ordering = rec.get("pad_pair_ordering") or {}
    for leg in ("hl", "hr"):
        pair = gaps.get(leg)
        if pair is None:
            for base in ("pad_g_heel_", "pad_g_mp_", "pad_split_abs_", "pad_split_"):
                prev.pop(base + leg, None)
            continue
        signed = ordering.get(leg, "heel_mp") == "heel_mp"
        a, b = float(pair[0]), float(pair[1])
        vals = {"pad_g_heel_" + leg: a, "pad_g_mp_" + leg: b,
                "pad_split_abs_" + leg: abs(b - a)}
        if signed:
            vals["pad_split_" + leg] = b - a
        prev.update(vals)
for i in range(oschema.OBS_DIM):
    if counts[i] >= 2:
        mean[i] = sums[i] / counts[i]
        var = max(sqsums[i] / counts[i] - mean[i] ** 2, 0.0)
        std[i] = max(float(np.sqrt(var)), 1e-3)

section = oschema.schema_summary(mean.astype(np.float32), std.astype(np.float32))
section["schema_version"] = oschema.OBS_SCHEMA_VERSION
section["legacy_block"] = {
    "dim": oschema.LEGACY_OBS_DIM,
    "contract": "FIELDS[:64] is the frozen P3 v1 table (1b6d7749); legacy records "
                "project bitwise-identically; a v1 consumer (64-length norm arrays) "
                "replays P3's banked action stream byte-identically",
}
section["pad_split_group"] = {
    "fields": oschema.FIELD_NAMES[64:],
    "pair_ordering_contract": "rec['pad_gaps'][leg] = [a, b] with "
                              "rec['pad_pair_ordering'][leg] in {'heel_mp' (endpoint "
                              "identity measured; the default when absent), 'lohi' "
                              "(reconstructed pair [g_lo=gmin, g_hi=2*pad_y-g_lo], the "
                              "wave-46 calibration identity)}; under 'lohi' the "
                              "endpoint-signed fields are declared unavailable",
    "calibration": "split_abs = 2*(pad_y - gmin); plane_model_y_ = pad radius = 0.004",
    "class_labels": "LIFT/STALL era classes + the separating windows: "
                    "mine_wave47_out.txt (LEVEL (0.551, 6.902) mm; era-RATE "
                    "(0.275, 0.767) mm/tick; per-tick INC (0.536, 0.872) mm/tick) -- "
                    "the free training labels of the first learned skill",
}
section["normalization_rule"] = ("mean/std over available ticks of the lane record set "
                                 "(the reconstructed wave-47 channel set, trace sha "
                                 "c6f9b6c0...); never-available -> 0/1; std floor 1e-3")
section["record_set"] = {"ticks": len(records),
                         "pad_split_abs_available": int((counts[64:] > 0).sum())}
# which v2 fields the record set never delivers (the endpoint identity on this set)
never = [oschema.FIELD_NAMES[i] for i in range(oschema.OBS_DIM) if counts[i] == 0]
section["record_set"]["never_available_here"] = never

out = os.path.join(HERE, "obs_section_v2.json")
with open(out, "w", encoding="utf-8") as f:
    json.dump(section, f, indent=1)
print("written", out)
print("dim", section["dim"], "| never-available on this record set:", len(never))
