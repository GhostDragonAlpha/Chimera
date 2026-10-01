"""THE BODY-VELOCITY DELIVERY BRIDGE (V2 obs): sensor-side delivery of the
body_velocity group's deciding scalar, field 21 `com_vel_x_heading`.

Lane/obs-populate-20260920 (Agent: obspop), prereg frozen in
`tools/science_funnel/validation/obs_populate_20260920/record.md` BEFORE this
build. Serves the interface-freeze lane's declared forward path: its F1
STATE-ALIASING audit fired on 21 aliased pairs whose deciding quantities live
in fields the walk record never delivered (the field exists in the frozen
80-field table; its value was never in the record). This module delivers
field 21 from quantities the trace ALREADY carries -- zero engine bytes, the
obs-split-channels pattern (their pad-split delivery, pad_channels.py).

THE DERIVATION (one line, no new numbers): the [dv] instrument line prints the
support state's CoM projection per tick (`support.com_projection_east_m`,
gait_unit.cpp) as `com=(east,south)`; first-differenced at the walk's own
300 Hz clock (the interface-freeze mine's own constant, their label line
`vx = (bx_t - bx_{t-1}) * 300.0`) this is the CoM x velocity in m/s --

    com_vel_x(t) = (com_east(t) - com_east(t-1)) * 300.0

t0 has no predecessor and is NOT delivered (the schema masks it: mean fill,
mask 0 -- a missing scalar under a delivered group, the group_delivery
availability rule).

THE FRAME CONDITION (declared, not derived): the delivered delta is world/east;
field 21's declared frame is `heading`. On this walk the two coincide because
the v1 command record's yaw authority is NONE (command_record.py: yaw_rate
RESERVED, zero measured authority) -- the equivalence is a property of the
frozen command set, not a new number.

THE READER IS UNCHANGED: observation_schema._read_field already resolves
`com_vel[0]` (the field's declared source) through the group gate
(`available_groups`); delivery is therefore purely record-side: declare the
group, carry the scalar. Fields 22-25 are NOT delivered here (outside the
lane's decree; declared in the prereg). The per-foot slots (9-20) are
STRUCTURAL on this body (the frozen reader's all-or-nothing 6-slot vector read
vs four paws) -- not delivered, never invented.

Rule 0: the falsifiers F1 SEPARATION / F2 TRACE-INVARIANCE / F3
TABLE-INVARIANCE / F4 CORPUS-REFREEZE / F5 DETERMINISM are declared in the
prereg and measured by the lane's mine (mine_obs_populate.py), not here.
"""
from __future__ import annotations

BODY_VELOCITY_GROUP = "body_velocity"
# the schema's declared source for com_vel_x_heading (observation_schema._GROUPS);
# _read_field resolves it literally: rec["com_vel[0]"]
COM_VEL_X_SOURCE_KEY = "com_vel[0]"
TICK_HZ = 300.0   # the walk's own physics clock (the interface-freeze mine's own constant)


def com_vel_x_series(dv: dict) -> dict[int, float]:
    """Per-tick CoM x velocity (m/s) from the parsed [dv] table
    (mine_aliasing_audit.parse_run's `dv`: tick -> {com_e, ...}).
    Returns {tick: value} for every tick WITH a predecessor (t0 excluded)."""
    ticks = sorted(dv)
    out: dict[int, float] = {}
    for prev_t, t in zip(ticks, ticks[1:]):
        out[t] = (float(dv[t]["com_e"]) - float(dv[prev_t]["com_e"])) * TICK_HZ
    return out


def deliver_body_velocity(recs: list[dict], series: dict[int, float]) -> int:
    """Deliver the body_velocity group into the per-tick records, in place.

    Every record gains the group declaration (`available_groups` += body_velocity
    -- the sensor path ran this tick); ticks whose scalar the trace determines
    (t >= 1) additionally carry `com_vel[0]`. t0 keeps the group but no scalar:
    the projector masks it (missing scalar under a delivered group). Returns the
    number of delivered scalars."""
    n = 0
    for rec in recs:
        groups = rec.setdefault("available_groups", [])
        if BODY_VELOCITY_GROUP not in groups:
            groups.append(BODY_VELOCITY_GROUP)
        v = series.get(rec.get("tick"))
        if v is not None:
            rec[COM_VEL_X_SOURCE_KEY] = float(v)
            n += 1
    return n
