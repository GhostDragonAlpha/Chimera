"""TypeB-P3 observation schema: the typed projection the policy will see.

Astra's envelope (lane-archive astra-typeb-pilots-20260921.md, P3/P4): the deployed
actor sees relevant phase, contact, controller-memory summaries, prior commands and
intervention indicators -- and NEVER privileged information (no root pose, no anatomy,
no acceptance-monitor state, no physics internals).

Each field is declared, not inferred: name, dtype, shape, unit, frame, source trace
quantity, availability semantics, normalization. The projector turns one per-tick walk
trace record into (obs_vector[64], availability_mask[64]); unavailable channels are
mean-filled per the declared recipe and the mask itself is an observed field, so the
policy can in principle condition on what it could not see.

Rule 0: the field table below is the theory. Its falsifier (F-OBSERVATION-LEAK, schema
audit) fires on any privileged source field, any misrepresentation of the recorded
census, or any unavailable channel silently read as data.
"""
from __future__ import annotations

import numpy as np

OBS_DIM = 64

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
    path delivered this tick).
    """
    avail_groups = rec.get("available_groups")
    obs = np.empty(OBS_DIM, dtype=np.float32)
    mask = np.zeros(OBS_DIM, dtype=np.float32)
    for i, f in enumerate(FIELDS):
        g = f["group"]
        group_available = (avail_groups is None) or (g in avail_groups)
        v = _read_field(f, rec, prev_state) if group_available else None
        if v is None:
            # group not delivered this tick, OR the scalar is missing under an
            # available group: declared unavailable -> mean-fill, mask 0. A missing
            # value is NEVER silently read as data (F-OBSERVATION-LEAK discipline).
            obs[i] = float(norm_mean[i])
            mask[i] = 0.0
        else:
            obs[i] = v
            mask[i] = 1.0
    # sensor_health fields observe the mask itself (always available)
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
