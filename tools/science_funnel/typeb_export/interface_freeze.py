"""POLICY INTERFACE FREEZE (lane/policy-interface-freeze-20260920): the typed,
per-field documentation of the 80-field deployed observation, generated from the
LIVE schema code and the pinned v2 manifest section -- never hand-maintained.

Rule 0 (prereg policy_interface_freeze_20260920, frozen before this build): the
interface table is a FROZEN artifact. Its falsifier F2 FREEZE-DRIFT fires on any
change to the table (field order, name, unit, frame, availability rule, meaning,
or normalization) that is not accompanied by a declared version bump. The unit
test regenerates the table from the live code and compares BYTES against the
committed JSON -- the only legal drift is OBS_SCHEMA_VERSION (and this module's
INTERFACE_FREEZE_VERSION) moving together with a regenerated, re-reviewed table.

The table documents, per field: meaning (what the field IS), units, frame, the
source trace quantity, the ordering (the declared foot/leg/channel orders), the
missing-value semantics (which availability rule governs it), and the exact
normalization applied by the deployed recipe (mean/std from the v2 manifest
section the obs-split lane measured, clip 8.0, the only arithmetic).

Usage: python interface_freeze.py gen <out.json> [obs_section_v2.json]
"""
from __future__ import annotations

import hashlib
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import observation_schema as oschema  # noqa: E402

INTERFACE_FREEZE_VERSION = "policy-interface/2.0.0"

# The declared foot order of the per-foot groups (the trace vocabulary's
# foot_contacts / foot_forces indexing; fl/fr = fore pair, ml/mr = mid pair,
# hl/hr = hind pair).
FOOT_ORDER = ("fl", "fr", "ml", "mr", "hl", "hr")
LEG_ORDER = ("l", "r")
CMD_CHANNEL_ORDER = ("phase_off", "stride_amp", "lift_amp", "stiff")
# command-vector index = leg*4 + channel (the projector's own _cmd_index law)
PAD_LEG_ORDER = ("hl", "hr")

# The availability rules (the missing-value semantics; the mask convention:
# an unavailable channel is DECLARED UNAVAILABLE -- mask 0, mean fill -- and
# never invented; the mask itself is observed via the sensor_health fields).
_AVAIL_GROUP = "group_delivery"
_AVAIL_RULES = {
    "group_delivery":
        "unavailable iff the field's group was not delivered this tick or the "
        "source scalar is missing from the record -> mask 0, mean fill",
    "pair_delivery":
        "pad-split: unavailable iff the leg's pad pair is not delivered; "
        "endpoint-signed fields additionally require ordering 'heel_mp' "
        "(a 'lohi' reconstructed pair leaves them unavailable -- never invented)",
    "delta_prev":
        "delta field: additionally unavailable unless the previous delivered "
        "sample of its base channel is in prev_state (a delivery gap masks the "
        "next delta)",
    "self_observing":
        "observes the availability mask itself; available whenever the "
        "projection runs (mask pinned to 1 by construction)",
    "derived_flag":
        "derived from other recorded scalars (one-hot / delta / support "
        "predicate); unavailable exactly when its base scalar(s) are missing",
}

_FIELD_MEANINGS = {
    # ---- gait_phase (5) ----
    "gait_phase_sin_left": "sin(2*pi*phase_left): left-leg gait-clock phase on the unit circle, x component (phase = cycle fraction of T_CYCLE)",
    "gait_phase_cos_left": "cos(2*pi*phase_left): left-leg gait-clock phase on the unit circle, y component",
    "gait_phase_sin_right": "sin(2*pi*phase_right): right-leg gait-clock phase on the unit circle, x component (the right clock runs the walk's own phase offset)",
    "gait_phase_cos_right": "cos(2*pi*phase_right): right-leg gait-clock phase on the unit circle, y component",
    "gait_phase_frac": "the gait clock's raw cycle fraction (0..1) this tick (source phase_frac)",
    # ---- contact_aggregate (4) ----
    "contact_count_norm": "number of feet in contact this tick, as the record's contact census states it (exact count only on census ticks; elsewhere declared unavailable)",
    "support_ge3_flag": "1.0 iff contact_count >= 3 (the support census forms a polygon), else 0.0",
    "unload_class_flag": "1.0 iff the machinery declared the unload class this tick (the unload_class census), else 0.0",
    "hind_step_class_flag": "1.0 iff the machinery declared a hind-step class event this tick (the hind_step_class census), else 0.0",
    # ---- contact_per_foot (6) ----
    **{f"foot_contact_{f}": f"binary contact flag of foot {f} ({name}) this tick"
       for f, name in zip(FOOT_ORDER, ("fore left", "fore right", "mid left", "mid right", "hind left", "hind right"))},
    # ---- contact_force (6) ----
    **{f"foot_force_{f}": f"contact force of foot {f} ({name}) in body-weight fractions (N_bw_frac)"
       for f, name in zip(FOOT_ORDER, ("fore left", "fore right", "mid left", "mid right", "hind left", "hind right"))},
    # ---- body_velocity (5) ----
    "com_vel_x_heading": "CoM velocity, x component, heading frame (m/s)",
    "com_vel_y_heading": "CoM velocity, y component, heading frame (m/s)",
    "com_vel_z": "CoM velocity, z component, world frame (m/s)",
    "yaw_rate": "body yaw rate this tick (rad/s, world frame)",
    "yaw_rate_prev": "body yaw rate of the PREVIOUS tick (the projector's held previous sample; 0.0 before the first tick)",
    # ---- prev_requested_cmd (8) ----
    **{f"prev_req_{leg}_{ch}": f"previously REQUESTED walk-interface command, leg {leg}, channel {ch} (the policy's own last demanded value, pre-limiter)"
       for leg in LEG_ORDER for ch in CMD_CHANNEL_ORDER},
    # ---- prev_applied_cmd (8) ----
    **{f"prev_app_{leg}_{ch}": f"previously APPLIED walk-interface command, leg {leg}, channel {ch} (post-limiter, what the machinery actually consumed)"
       for leg in LEG_ORDER for ch in CMD_CHANNEL_ORDER},
    # ---- limiter_saturation (8) ----
    **{f"lim_sat_{leg}_{ch}": f"limiter saturation indicator, leg {leg}, channel {ch}: 1.0 iff the limiter clipped that channel at the last decision, else 0.0"
       for leg in LEG_ORDER for ch in CMD_CHANNEL_ORDER},
    # ---- intervention (5) ----
    "intv_none": "1.0 iff intervention_reason == 'none' this tick, else 0.0",
    "intv_refusal": "1.0 iff intervention_reason == 'refusal' (the walk refused) this tick, else 0.0",
    "intv_ledger_breach": "1.0 iff intervention_reason == 'ledger_breach' this tick, else 0.0",
    "intv_falsifier_red": "1.0 iff intervention_reason == 'falsifier_red' this tick, else 0.0",
    "ticks_since_intv": "ticks since the last intervention, clamped at 3000 by the projector, normalized",
    # ---- command_clock (3) ----
    "hold_tick_frac": "position within the zero-order hold (hold_tick: the tick's offset inside the hold window) at the 20 Hz decision clock",
    "policy_gate": "1.0 iff this tick is a decision tick (physics_tick % hold_ticks == 0), else 0.0 -- the 20 Hz gate over the 300 Hz physics",
    "freq_scale": "the gait frequency scale applied by the walk interface this tick",
    # ---- sensor_health (2) ----
    "mask_mean": "mean of the availability mask itself at the consumer's declared dim (the fraction of channels available this tick)",
    "mask_frac_avail": "fraction of channels whose mask > 0 this tick",
    # ---- phase_dynamics (4) ----
    "phase_rate_norm": "the gait clock's per-tick advance (1/cycle_ticks as recorded), normalized",
    "contact_count_delta": "contact_count minus contact_count_prev this tick (the contact event's first difference)",
    "contact_count_prev": "the PREVIOUS tick's contact count",
    "time_since_reset": "ticks since the last reset, normalized",
    # ---- pad_split (16; the V2 block, obs_split_channels_20260921) ----
}
_PAD_MEANING_TEMPLATES = {
    "pad_g_heel_": "hind leg {leg}: the HEEL endpoint pad gap (g_heel) BEFORE gap_of's min, meters (endpoint identity measured under ordering 'heel_mp')",
    "pad_g_mp_": "hind leg {leg}: the MP (metatarsophalangeal) endpoint pad gap (g_mp) BEFORE gap_of's min, meters (ordering 'heel_mp')",
    "pad_dg_heel_": "hind leg {leg}: per-tick delta of g_heel, m/tick (needs the previous delivered sample)",
    "pad_dg_mp_": "hind leg {leg}: per-tick delta of g_mp, m/tick (needs the previous delivered sample)",
    "pad_split_": "hind leg {leg}: SIGNED split g_heel - g_mp, meters -- the sole's rotational DOF (ordering 'heel_mp')",
    "pad_split_rate_": "hind leg {leg}: per-tick delta of the signed split, m/tick (ordering 'heel_mp', needs previous sample)",
    "pad_split_abs_": "hind leg {leg}: |split| = 2*(pad_y - gmin), meters -- the wave-46/47 calibrated quantity, ordering-free",
    "pad_split_abs_rate_": "hind leg {leg}: per-tick delta of |split|, m/tick -- the wave-47 LIFT/STALL class quantity, ordering-free (needs previous sample)",
}
for _leg in PAD_LEG_ORDER:
    for _pref, _tmpl in _PAD_MEANING_TEMPLATES.items():
        _FIELD_MEANINGS[_pref + _leg] = _tmpl.format(leg=_leg)


def _availability_rule(name: str) -> str:
    if name in ("mask_mean", "mask_frac_avail"):
        return "self_observing"
    if name.startswith("pad_dg_") or name in ("pad_split_rate_hl", "pad_split_rate_hr",
                                              "pad_split_abs_rate_hl", "pad_split_abs_rate_hr"):
        return "delta_prev"
    if name.startswith("pad_"):
        return "pair_delivery"
    if name in ("support_ge3_flag", "contact_count_delta", "intv_none", "intv_refusal",
                "intv_ledger_breach", "intv_falsifier_red"):
        return "derived_flag"
    return "group_delivery"


def build_interface_table(obs_section_path: str) -> dict:
    """The full frozen table, generated from the LIVE schema + the pinned v2
    manifest section (normalization). Deterministic: same inputs -> byte-equal
    JSON. This determinism IS the F2 pin."""
    with open(obs_section_path, "rb") as f:
        section = json.loads(f.read().decode("utf-8"))
    assert section["dim"] == oschema.OBS_DIM, "obs section dim != live OBS_DIM"
    assert section["order"] == oschema.FIELD_NAMES, "obs section order != live FIELD_NAMES"

    fields = []
    for i, f in enumerate(oschema.FIELDS):
        pf = section["per_field"][f["name"]]
        assert pf["index"] == i
        rule = _availability_rule(f["name"])
        fields.append({
            "index": i,
            "name": f["name"],
            "group": f["group"],
            "meaning": _FIELD_MEANINGS[f["name"]],
            "unit": f["unit"],
            "frame": f["frame"],
            "source_trace_key": f["source"],
            "dtype": "float32",
            "privileged": False,
            "ordering": _ordering_note(f["name"]),
            "availability_rule": rule,
            "missing_value_semantics": _AVAIL_RULES[rule],
            "normalization": {
                "recipe": "x = clip((raw - mean) / max(std, 1e-8), -clip, +clip); unavailable -> mean fill (exactly 0.0 in normalized space)",
                "mean": pf["mean"],
                "std": pf["std"],
                "clip": pf.get("clip", 8.0),
            },
        })

    return {
        "kind": "policy_observation_interface",
        "interface_freeze_version": INTERFACE_FREEZE_VERSION,
        "obs_schema_version": oschema.OBS_SCHEMA_VERSION,
        "dim": oschema.OBS_DIM,
        "legacy_dim": oschema.LEGACY_OBS_DIM,
        "legacy_block_law": "FIELDS[:64] is field-for-field the frozen v1 table (legacy_v1_table.py, 1b6d7749); a v1 consumer (64-dim norm arrays) receives a v1-width projection and mask",
        "dtype": "float32",
        "order": oschema.FIELD_NAMES,
        "history_ticks": 0,
        "declared_orders": {
            "feet": list(FOOT_ORDER),
            "command_legs": list(LEG_ORDER),
            "command_channels": list(CMD_CHANNEL_ORDER),
            "command_index_law": "index = leg_index*4 + channel_index (leg l=0, r=1; channels phase_off, stride_amp, lift_amp, stiff)",
            "pad_legs": list(PAD_LEG_ORDER),
            "pad_pair_orderings": {"heel_mp": "pair [a, b] = [g_heel, g_mp] -- endpoint identity measured", "lohi": "pair [g_lo, g_hi] reconstructed -- endpoint identity NOT in the record; endpoint-signed fields declared unavailable"},
        },
        "clip": 8.0,
        "normalization_source": {
            "path": "tools/science_funnel/validation/obs_split_channels_20260921/obs_section_v2.json",
            "sha256": _sha256_file(obs_section_path),
            "recipe": "mean/std over the available ticks of the lane record set; never-available -> 0/1; std floored at 1e-3 (the P3 normalization law)",
        },
        "privileged_forbidden": True,
        "availability_recipe": section["availability_recipe"],
        "fields": fields,
    }


def _ordering_note(name: str) -> str:
    if name.startswith("foot_contact_") or name.startswith("foot_force_"):
        return "foot order " + ", ".join(FOOT_ORDER)
    if name.startswith(("prev_req_", "prev_app_", "lim_sat_")):
        return "leg-major (l, r) x channel (" + ", ".join(CMD_CHANNEL_ORDER) + "); vector index = leg*4 + channel"
    if name.startswith("pad_"):
        return "hind-leg order " + ", ".join(PAD_LEG_ORDER)
    return "singleton"


def canonical_table_bytes(table: dict) -> bytes:
    return json.dumps(table, indent=1, sort_keys=False, ensure_ascii=False).encode("utf-8")


def _sha256_file(path: str) -> str:
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def regen_bytes(obs_section_path: str) -> bytes:
    return canonical_table_bytes(build_interface_table(obs_section_path))


def main() -> None:
    here = os.path.dirname(os.path.abspath(__file__))
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        here, "..", "validation", "policy_interface_freeze_20260920",
        "observation_interface_v2.json")
    section = sys.argv[2] if len(sys.argv) > 2 else os.path.join(
        here, "..", "validation", "obs_split_channels_20260921", "obs_section_v2.json")
    b = regen_bytes(section)
    with open(out, "wb") as f:
        f.write(b)
    print("interface table bytes:", len(b))
    print("interface table sha256:", hashlib.sha256(b).hexdigest())
    print("written:", os.path.abspath(out))


if __name__ == "__main__":
    main()
