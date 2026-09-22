"""TypeB-P3 observation schema: the typed projection the policy will see.

Astra's envelope (lane-archive astra-typeb-pilots-20260921.md, P3/P4): the deployed
actor sees relevant phase, contact, controller-memory summaries, prior commands and
intervention indicators -- and NEVER privileged information (no root pose, no anatomy,
no acceptance-monitor state, no physics internals).

Each field is declared, not inferred: name, dtype, shape, unit, frame, source trace
quantity, availability semantics, normalization. The projector turns one per-tick walk
trace record into (obs_vector, availability_mask); unavailable channels are
mean-filled per the declared recipe and the mask itself is an observed field, so the
policy can in principle condition on what it could not see.

Rule 0: the field table below is the theory. Its falsifier (F-OBSERVATION-LEAK, schema
audit) fires on any privileged source field, any misrepresentation of the recorded
census, or any unavailable channel silently read as data.

V2 EXTENSION (agent/obs-split-channels-20260921, prereg frozen at 97fd15fb BEFORE
this build; the Type-A half of the TYPE-B convergence, receipt_wave47.json's bank):
the pad-split group -- per hind leg the individual pad gaps BEFORE gap_of's min
(g_heel heel endpoint, g_mp MP endpoint), their per-tick deltas, and the derived
split channels (signed split + rate; ordering-free split_abs + rate -- the wave-46/47
calibrated quantity whose LIFT/STALL class windows mine_wave47_out.txt measured).
The legacy 64-field block is FROZEN: FIELDS[:64] is field-for-field the v1 table,
and legacy records (no pad keys) project bitwise-identically to v1 on [0:64]
(F-CHANNELS-INERT). The mask convention is carried: a channel the record does not
determine is DECLARED UNAVAILABLE (mask 0, mean fill), never invented -- including
the endpoint identity itself: a record whose pad pair carries ordering 'lohi'
(reconstructed, endpoint identity not measured) masks the endpoint-signed fields.
"""
from __future__ import annotations

import numpy as np

OBS_SCHEMA_VERSION = 2
LEGACY_OBS_DIM = 64   # the frozen P3 v1 block: FIELDS[:LEGACY_OBS_DIM]
OBS_DIM = 80          # 64 legacy + 16 pad-split channels

# Trace-record field names mirror the walk telemetry vocabulary (wave-38 banked run:
# cycle_ticks, per-tick contact census, unload/hind-step class, refused_tick,
# requested/applied commands, limiter saturation, intervention reason).

_GROUPS = [
    # (group, [(name, source_trace_key, unit, frame, privileged)], size, default_available)
    ("gait_phase", [
        ("gait_phase_sin_left",  "phase_left",  "1", "gait_clock", False),
        ("gait_phase_cos_left",  "phase_left",  "1", "gait_clock", False),
        ("gait_phase_sin_right", "phase_right", "1", "gait_clock", False),
        ("gait_phase_cos_right", "phase_right", "1", "gait_clock", False),
        ("gait_phase_frac",      "phase_frac",  "1", "gait_clock", False),
    ]),
    ("contact_aggregate", [
        ("contact_count_norm",    "contact_count",    "1", "body", False),
        ("support_ge3_flag",      "contact_count",    "1", "body", False),
        ("unload_class_flag",     "unload_class",     "1", "body", False),
        ("hind_step_class_flag",  "hind_step_class",  "1", "body", False),
    ]),
    ("contact_per_foot", [
        ("foot_contact_fl", "foot_contacts[0]", "1", "body", False),
        ("foot_contact_fr", "foot_contacts[1]", "1", "body", False),
        ("foot_contact_ml", "foot_contacts[2]", "1", "body", False),
        ("foot_contact_mr", "foot_contacts[3]", "1", "body", False),
        ("foot_contact_hl", "foot_contacts[4]", "1", "body", False),
        ("foot_contact_hr", "foot_contacts[5]", "1", "body", False),
    ]),
    ("contact_force", [
        ("foot_force_fl", "foot_forces[0]", "N_bw_frac", "body", False),
        ("foot_force_fr", "foot_forces[1]", "N_bw_frac", "body", False),
        ("foot_force_ml", "foot_forces[2]", "N_bw_frac", "body", False),
        ("foot_force_mr", "foot_forces[3]", "N_bw_frac", "body", False),
        ("foot_force_hl", "foot_forces[4]", "N_bw_frac", "body", False),
        ("foot_force_hr", "foot_forces[5]", "N_bw_frac", "body", False),
    ]),
    ("body_velocity", [
        ("com_vel_x_heading", "com_vel[0]", "m_s", "heading", False),
        ("com_vel_y_heading", "com_vel[1]", "m_s", "heading", False),
        ("com_vel_z",         "com_vel[2]", "m_s", "world",   False),
        ("yaw_rate",          "yaw_rate",   "rad_s", "world",  False),
        ("yaw_rate_prev",     "yaw_rate",   "rad_s", "world",  False),
    ]),
    ("prev_requested_cmd", [
        (f"prev_req_{leg}_{ch}", "requested_cmd", "cmd", "walk_interface", False)
        for leg in ("l", "r") for ch in ("phase_off", "stride_amp", "lift_amp", "stiff")
    ]),
    ("prev_applied_cmd", [
        (f"prev_app_{leg}_{ch}", "applied_cmd", "cmd", "walk_interface", False)
        for leg in ("l", "r") for ch in ("phase_off", "stride_amp", "lift_amp", "stiff")
    ]),
    ("limiter_saturation", [
        (f"lim_sat_{leg}_{ch}", "limiter_saturation", "1", "walk_interface", False)
        for leg in ("l", "r") for ch in ("phase_off", "stride_amp", "lift_amp", "stiff")
    ]),
    ("intervention", [
        ("intv_none",           "intervention_reason", "1", "controller", False),
        ("intv_refusal",        "intervention_reason", "1", "controller", False),
        ("intv_ledger_breach",  "intervention_reason", "1", "controller", False),
        ("intv_falsifier_red",  "intervention_reason", "1", "controller", False),
        ("ticks_since_intv",    "ticks_since_intervention", "tick_norm", "controller", False),
    ]),
    ("command_clock", [
        ("hold_tick_frac",  "hold_tick",       "1", "controller", False),
        ("policy_gate",     "is_decision_tick", "1", "controller", False),
        ("freq_scale",      "freq_scale",      "1", "walk_interface", False),
    ]),
    ("sensor_health", [
        ("mask_mean",         "availability_mask", "1", "observation", False),
        ("mask_frac_avail",   "availability_mask", "1", "observation", False),
    ]),
    ("phase_dynamics", [
        ("phase_rate_norm",     "phase_rate",     "1", "gait_clock", False),
        ("contact_count_delta", "contact_count",  "1", "body", False),
        ("contact_count_prev",  "contact_count",  "1", "body", False),
        ("time_since_reset",    "ticks_since_reset", "tick_norm", "controller", False),
    ]),
    # V2 pad-split channels (agent/obs-split-channels-20260921). Per hind leg
    # (hl=4, hr=5) the pair gap_of computes and erases: gh (heel endpoint) and
    # gm (MP endpoint). rec['pad_gaps'][leg] = [a, b] with
    # rec['pad_pair_ordering'][leg] in {'heel_mp' (endpoint identity measured:
    # a=g_heel, b=g_mp -- the instrument contract; the default when absent),
    # 'lohi' (reconstructed pair [g_lo=gmin, g_hi=2*pad_y-g_lo], the wave-46
    # calibration identity; endpoint identity NOT in the record)}. Under 'lohi'
    # the endpoint-signed fields (g_heel, g_mp, dg_heel, dg_mp, split,
    # split_rate) are DECLARED UNAVAILABLE -- the record does not determine
    # them, so they are never invented (the mask convention applied to
    # semantics); the ordering-free split_abs/split_abs_rate stay live under
    # both orderings. Deltas need the previous delivered sample via
    # prev_state (caller-owned: store prev['pad_<chan>_<leg>'] = value when
    # available, pop it when not -- a delivery gap masks the next delta).
    ("pad_split", [
        ("pad_g_heel_hl", "pad_gaps", "m", "world", False),
        ("pad_g_heel_hr", "pad_gaps", "m", "world", False),
        ("pad_g_mp_hl",   "pad_gaps", "m", "world", False),
        ("pad_g_mp_hr",   "pad_gaps", "m", "world", False),
        ("pad_dg_heel_hl", "pad_gaps", "m_per_tick", "world", False),
        ("pad_dg_heel_hr", "pad_gaps", "m_per_tick", "world", False),
        ("pad_dg_mp_hl",   "pad_gaps", "m_per_tick", "world", False),
        ("pad_dg_mp_hr",   "pad_gaps", "m_per_tick", "world", False),
        ("pad_split_hl",       "pad_gaps", "m", "world", False),
        ("pad_split_hr",       "pad_gaps", "m", "world", False),
        ("pad_split_rate_hl",  "pad_gaps", "m_per_tick", "world", False),
        ("pad_split_rate_hr",  "pad_gaps", "m_per_tick", "world", False),
        ("pad_split_abs_hl",       "pad_gaps", "m", "world", False),
        ("pad_split_abs_hr",       "pad_gaps", "m", "world", False),
        ("pad_split_abs_rate_hl",  "pad_gaps", "m_per_tick", "world", False),
        ("pad_split_abs_rate_hr",  "pad_gaps", "m_per_tick", "world", False),
    ]),
]

FIELDS = []
for gname, flds in _GROUPS:
    for fname, src, unit, frame, privileged in flds:
        FIELDS.append({
            "name": fname, "group": gname, "source": src, "unit": unit,
            "frame": frame, "privileged": privileged, "dtype": "float32", "shape": [1],
        })

assert len(FIELDS) == OBS_DIM, f"field table is {len(FIELDS)}, must be {OBS_DIM}"
FIELD_NAMES = [f["name"] for f in FIELDS]
_NAME_TO_IDX = {n: i for i, n in enumerate(FIELD_NAMES)}
assert len(_NAME_TO_IDX) == OBS_DIM, "duplicate observation field name"

PRIVILEGED_SOURCES = frozenset([
    "root_pose", "root_quat", "anatomy", "moving_ledger", "acceptance_monitor",
    "gravity", "bond_state", "membrane_force", "training_reward", "critic_value",
])

# Neutral fill values live in the manifest normalization block; the schema only fixes
# order, meaning and availability semantics.
_CLIP = 8.0  # normalized-space clip, declared in the recipe and mirrored in the manifest


def project_trace(rec: dict, norm_mean: np.ndarray, norm_std: np.ndarray,
                  prev_state: dict) -> tuple[np.ndarray, np.ndarray]:
    """Project one per-tick walk trace record to (obs64 float32, mask64 float32).

    rec keys (per the walk telemetry vocabulary): tick, phase_left, phase_right,
    phase_frac, phase_rate, contact_count, contact_count_prev, foot_contacts (6 or
    None), foot_forces (6 or None), unload_class, hind_step_class, com_vel (3 or None),
    yaw_rate, requested_cmd (8), applied_cmd (8), limiter_saturation (8),
    intervention_reason (str), ticks_since_intervention, hold_tick, is_decision_tick,
    freq_scale, ticks_since_reset, available_groups (set of group names the sensor
    path delivered this tick); V2: pad_gaps ({'hl','hr'} -> [a, b] or absent),
    pad_pair_ordering ({'hl','hr'} -> 'heel_mp' | 'lohi', absent -> 'heel_mp').
    Returns (obs, mask) at the consumer's declared dim: 64 (a v1 manifest's norm
    arrays) or 80 (v2).
    """
    avail_groups = rec.get("available_groups")
    obs = np.empty(OBS_DIM, dtype=np.float32)
    mask = np.zeros(OBS_DIM, dtype=np.float32)
    n_norm = int(len(norm_mean))  # v1 consumers carry 64; slices applied below
    for i, f in enumerate(FIELDS):
        g = f["group"]
        group_available = (avail_groups is None) or (g in avail_groups)
        v = _read_field(f, rec, prev_state) if group_available else None
        if v is None:
            # group not delivered this tick, OR the scalar is missing under an
            # available group: declared unavailable -> mean-fill, mask 0. A missing
            # value is NEVER silently read as data (F-OBSERVATION-LEAK discipline).
            obs[i] = float(norm_mean[i]) if i < n_norm else 0.0
            mask[i] = 0.0
        else:
            obs[i] = v
            mask[i] = 1.0
    # V2 compat (declared in the obs_split_channels prereg): a v1 consumer
    # carries LEGACY_OBS_DIM-length norm arrays -- its frozen manifest pins the
    # v1 dim -- so the projection is sliced to the consumer's declared dim
    # BEFORE the sensor_health aggregates are computed. A v1 consumer therefore
    # observes a v1-width mask and its replay is bitwise the v1 record; a v2
    # consumer observes the full v2 mask (the only value-level delta on legacy
    # records, and exactly the declared sensor_health semantics: the aggregates
    # observe the mask itself).
    d = n_norm
    if d == LEGACY_OBS_DIM:
        obs, mask = obs[:d], mask[:d]
    elif d != OBS_DIM:
        raise ValueError(
            f"norm arrays must be length {LEGACY_OBS_DIM} (v1 manifest) or {OBS_DIM} (v2), got {d}")
    # sensor_health fields observe the mask itself (always available), at the
    # consumer's declared dim
    i_mm, i_mf = _NAME_TO_IDX["mask_mean"], _NAME_TO_IDX["mask_frac_avail"]
    obs[i_mm] = float(np.mean(mask))
    obs[i_mf] = float(np.mean(mask > 0))
    mask[i_mm:i_mf + 1] = 1.0
    # normalization + clip (the only arithmetic the deployed recipe performs here)
    x = (obs - norm_mean) / np.maximum(norm_std, 1e-8)
    return np.clip(x, -_CLIP, _CLIP).astype(np.float32), mask


def _read_field(f: dict, rec: dict, prev: dict):
    """Raw scalar for one field, or None if the trace record does not carry it.
    The caller owns availability: None -> mean-fill + mask 0."""
    n, src = f["name"], f["source"]
    if n in ("mask_mean", "mask_frac_avail"):
        return None  # filled by caller after the mask is complete
    if n.startswith("pad_"):
        return _read_pad_field(n, rec, prev)
    if src in ("requested_cmd", "applied_cmd", "limiter_saturation"):
        v = rec.get(src)
        return None if v is None else float(v[_cmd_index(n)])
    if src.startswith("foot_contacts[") or src.startswith("foot_forces["):
        base = src.split("[")[0]
        idx = int(src[-2])
        v = rec.get(base)
        return None if v is None else float(v[idx])
    if n == "intv_none":      return 1.0 if rec.get("intervention_reason", "none") == "none" else 0.0
    if n == "intv_refusal":   return 1.0 if rec.get("intervention_reason") == "refusal" else 0.0
    if n == "intv_ledger_breach": return 1.0 if rec.get("intervention_reason") == "ledger_breach" else 0.0
    if n == "intv_falsifier_red": return 1.0 if rec.get("intervention_reason") == "falsifier_red" else 0.0
    if n == "support_ge3_flag":
        cc = rec.get("contact_count")
        return None if cc is None else (1.0 if float(cc) >= 3 else 0.0)
    if n == "contact_count_delta":
        cc, cp = rec.get("contact_count"), rec.get("contact_count_prev")
        return None if (cc is None or cp is None) else float(cc) - float(cp)
    if n == "yaw_rate_prev":
        return float(prev.get("yaw_rate", 0.0) or 0.0)
    if n.startswith("gait_phase_sin_") or n.startswith("gait_phase_cos_"):
        # the sin/cos encoding of the gait clock phase, per leg
        ph = rec.get(src)
        return None if ph is None else float(
            np.sin(2.0 * np.pi * float(ph)) if n.startswith("gait_phase_sin_")
            else np.cos(2.0 * np.pi * float(ph)))
    v = rec.get(src if src in rec else n)
    return None if v is None else float(v)


def _cmd_index(name: str) -> int:
    # prev_req_l_stride_amp -> channel 1 ; order: phase_off, stride_amp, lift_amp, stiff
    ch = next(i for i, c in enumerate(("phase_off", "stride_amp", "lift_amp", "stiff"))
              if name.endswith("_" + c))
    leg = 0 if "_l_" in name else 1
    return leg * 4 + ch


_PAD_LEGACY_KEYS = ("pad_g_heel_", "pad_g_mp_", "pad_split_abs_rate_",
                    "pad_split_abs_", "pad_split_rate_", "pad_split_")


def _read_pad_field(n: str, rec: dict, prev: dict):
    """One pad-split channel (V2), or None when the record does not determine it.

    Availability (the mask convention, prereg obs_split_channels_20260921):
    - the leg's pair not delivered this tick -> None for every pad channel;
    - endpoint-signed channels need ordering 'heel_mp' (the measured endpoint
      identity); a 'lohi' record leaves them None -- never invented;
    - pad_split_abs / pad_split_abs_rate are ordering-free (|g_heel - g_mp|);
    - delta channels need the previous delivered sample of their base channel
      via prev_state (caller-owned: the key present iff the previous tick
      delivered that channel)."""
    leg = "hr" if n.endswith("_hr") else "hl"
    gaps = rec.get("pad_gaps")
    pair = gaps.get(leg) if isinstance(gaps, dict) else None
    if pair is None or len(pair) != 2:
        return None
    ordering = (rec.get("pad_pair_ordering") or {}).get(leg, "heel_mp")
    a, b = float(pair[0]), float(pair[1])
    signed = ordering == "heel_mp"
    if n.startswith("pad_g_heel_"):
        return a if signed else None
    if n.startswith("pad_g_mp_"):
        return b if signed else None
    if n.startswith("pad_dg_heel_"):
        p = prev.get("pad_g_heel_" + leg)
        return None if (p is None or not signed) else a - float(p)
    if n.startswith("pad_dg_mp_"):
        p = prev.get("pad_g_mp_" + leg)
        return None if (p is None or not signed) else b - float(p)
    if n.startswith("pad_split_abs_rate_"):
        p = prev.get("pad_split_abs_" + leg)
        return None if p is None else abs(b - a) - float(p)
    if n.startswith("pad_split_abs_"):
        return abs(b - a)
    if n.startswith("pad_split_rate_"):
        p = prev.get("pad_split_" + leg)
        return None if (p is None or not signed) else (b - a) - float(p)
    if n.startswith("pad_split_"):
        return (b - a) if signed else None
    return None


def schema_summary(norm_mean, norm_std, clip=_CLIP) -> dict:
    """The observation block embedded in the policy manifest."""
    per_field = {}
    for i, f in enumerate(FIELDS):
        per_field[f["name"]] = {
            "index": i, "group": f["group"], "source": f["source"], "unit": f["unit"],
            "frame": f["frame"], "privileged": f["privileged"],
            "mean": float(norm_mean[i]), "std": float(norm_std[i]), "clip": clip,
        }
    return {
        "dim": OBS_DIM, "dtype": "float32", "order": FIELD_NAMES,
        "history_ticks": 0,
        "availability_recipe": "unavailable group -> mean-fill, availability mask observed via mask_mean/mask_frac_avail",
        "privileged_forbidden": True,
        "per_field": per_field,
    }
