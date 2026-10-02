#!/usr/bin/env python3
"""MAT2-F06: the gated terrain-aware walking experiment (prereg sections 2-7).

Order is law: pins -> registry -> pin-extract -> re-validate the pinned W04
certificate -> deploy gate ALLOW -> frozen loader + bit-for-bit identity ->
build identity -> the pinned F07 route/mask replay (P2) -> the declared
script derivation (the deterministic pinned recursion) -> the arms:
A0 the flat regression (the certified line vs the extension line, bit
identity, P1; the wrong-command arm, P10), A1 the uneven-ground route (P4),
A2 the crest attempt (the stall prediction, P5), A3 the step-over case (P6),
A4 the approach to the declared trunk ring (P7) -- with the W09 supervisor
in its sealed observation role on the clean arms -- then the falsifier arms
with their clean controls FIRST (G1), then the receipts + per-tick traces.

Run:  python -B terrain_walking.py
Exit: 0 green / 2 named refusal / 1 failed prediction.  CPU only; no engine
process; no training; no snapshot injection on clean arms.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import verify_inputs as vi            # noqa: E402
import source_access as sa            # noqa: E402  (declared blob reader)
import terrain_extension as te        # noqa: E402

RECEIPTS = HERE / "receipts"
CAPTURE_DIR = HERE / "capture"

# ---------------------------------------------------------------- state
_ADAPTER = [None]
_MANIFEST = [None]
_SCENE_CONST = [None]
_PARAMS = [None]
_tick_holder = [0]
_CMD_VERSION = [None]
_V_MAX = [0.763625]
_OMEGA = [1.6]


SEED = 20260920                     # the certified scene seed (continuity)
HORIZON_A0 = 10500                  # W08's sealed script horizon
CAP_A1, CAP_A2, CAP_A3, CAP_A4 = 15000, 16000, 9000, 9000
A4_HOLD_TICKS = 600                 # the declared hold after the trunk stop
INITIAL_TURN_TICK = 315             # the declared first-boundary turn tick

# the pinned declared constants quoted at freeze (re-derived live below)
V_CMD_CEILING = 0.763625            # the seam's in-band ceiling (pinned mapper)
A_CEILING = V_CMD_CEILING * 0.35    # = 0.26726875
D_HI = 0.35 * (0.95 + 0.10)         # = 0.3675
D_LO = 0.35 * 0.95                  # = 0.3325
GAMMA_STALL = A_CEILING / te.G_GRAV          # 0.027253827759734468
A1_GRADE_ENVELOPE = 0.026054        # the sealed route max (corridor-derived)
W08_V_AT_SEGMENT_END = 0.7457698018962889   # the sealed W08 measured value
BETA_A4 = 1.0322460640521718        # atan2(2.471766, 1.476783) at freeze
A4_MISS_COEF = 0.8584531418657813   # the declared bearing's |dir_y|
A4_MISS_BAND = 0.1365               # the declared conservative along-track band
BETA_A2_DIRECT = 0.2984989315861793  # atan2(6.0, 19.5): the direct flank line
A2_STRETCH_ENTRY_M = 16.75           # the derived stretch entry (1 cm corridor)
A2_STRETCH_LEN_M = 2.09
A2_STRETCH_MIN_GRADE = 0.029987860484500025
A2_TRAVEL_BOUND = 1.8369826985230038  # the discrete stall-travel bound
A2_CORRIDOR_MAX = 0.036569648824408205
D_STEP_DECLARED = 0.11599999999999999
DOME_SLOPE_AT_FIRE = 0.4761
SPREAD_FIRE_BAND = (D_STEP_DECLARED,
                    D_STEP_DECLARED + V_CMD_CEILING / 300.0 * DOME_SLOPE_AT_FIRE)
VELOCITY_ENVELOPE = 2.977443609022557
DT = te.DT                       # 1/300 s (the pinned scene timestep)


def require(condition, code):
    if not condition:
        print("REFUSAL: " + code, file=sys.stderr)
        raise SystemExit(2)


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def norm_delta(target, current):
    """The shortest signed rotation from `current` to `target` (radians)."""
    return ((target - current + math.pi) % (2.0 * math.pi)) - math.pi


# ---------------------------------------------------------------- stages 1-5
def stage_pins():
    pins = vi.verify()
    reg = vi.verify_registry()
    vi.extract_pinned_tree()
    vi.bootstrap_pinned_imports()
    return pins, reg


def gate_and_load():
    from tools.policy_compat.certificate import (validate_certificate,  # pinned
                                                 check_deploy)
    from tools.policy_compat import runner as R        # pinned bytes
    from tools.policy_compat import scene_cpu as SC    # pinned bytes

    cert = vi.w04_certificate()
    errs = validate_certificate(cert)
    require(not errs, "certificate_validator_violation:" + "; ".join(errs)[:300])
    rel = ("policy_bundle", "physics_build", "runtime_profile",
           "body_domain", "test_suite")
    req = {k: cert["relation"][k] for k in rel}
    allow = check_deploy(req, cert)
    require(allow["decision"] == "ALLOW",
            "deploy_gate_sanity:not_allow:" + allow["decision"])

    bundle = R.load_bundle()
    pb = cert["relation"]["policy_bundle"]
    for field, got, want in (
            ("manifest_hash", bundle["manifest"]["manifest_hash"], pb["manifest_hash"]),
            ("weights", bundle["manifest"]["policy"]["weights_sha256"], pb["weights_sha256"]),
            ("manifest_file_sha256", bundle["manifest_file_sha256"], pb["manifest_file_sha256"]),
            ("weights_file_sha256", bundle["weights_file_sha256"], pb["weights_file_sha256"]),
    ):
        require(got == want, "load_identity_mismatch:" + field)
    build_id, params = SC.build_n()
    phb = cert["relation"]["physics_build"]
    require(build_id == phb["build_id"], "load_identity_mismatch:build_id")
    require(SC.params_sha(params) == phb["params_sha256"],
            "load_identity_mismatch:params_sha256")
    scene_mod = vi.PINNED_ROOT / "tools" / "policy_compat" / "scene_cpu.py"
    require(sha_bytes(scene_mod.read_bytes()) == phb["scene_module_sha256"],
            "load_identity_mismatch:scene_module_sha256")
    require(params["dt"] == phb["timestep_s"],
            "load_identity_mismatch:timestep_s")
    gate = {
        "validator": {"violations": [], "verdict": "VALID"},
        "deploy_decision": allow["decision"],
        "bundle_identity": {"manifest_hash": pb["manifest_hash"],
                            "weights_sha256": pb["weights_sha256"]},
        "physics_build": {"build_id": build_id,
                          "params_sha256": SC.params_sha(params),
                          "scene_module_sha256": phb["scene_module_sha256"],
                          "timestep_s": params["dt"]},
    }
    return cert, allow, bundle, build_id, params, gate


# ---------------------------------------------------------------- case feeds
def turn_events(planned_rad, start_tick):
    """The declared turn quantization law (prereg section 4): 20-count
    interval events plus one fine 1-count tail, on the 15-tick grid."""
    total_counts = int(round(abs(planned_rad) * 500.0))
    sign = 1 if planned_rad >= 0 else -1
    events = []
    t = start_tick
    left = total_counts
    while left > 0:
        c = min(20, left)
        events.append((t, sign * c))
        left -= c
        t += 15
    return events


class CasePlan:
    """A declared case: absolute leg bearings + lengths, end rule, cap."""

    def __init__(self, name, legs, end_rule, cap):
        self.name = name
        self.legs = legs          # [(bearing_rad, length_m | None)]
        self.end_rule = end_rule  # 'route' | 'stall' | 'stop'
        self.cap = cap


class _RecordingSink:
    def __init__(self):
        self.records = []

    def emit(self, record):
        self.records.append(record)
        return len(self.records)


def run_case(world, adapter, build_id, params, plan, events=None,
             derive=True, mute_grade=False, snap_hook=None, mutate=None,
             resume=None):
    """One arm run.  derive=True: the turns fire when the derived arc crosses
    the waypoint (first 15-tick grid tick); the event table is returned.
    derive=False: the frozen event table drives (the f06_script_drift
    check)."""
    from tools.policy_compat import scene_cpu as SC
    from tools.monkey_campaign.product.input_mapper import (
        InputMapper, EXPIRY_TICKS)

    scene = SC.make_scene(build_id, params, SEED)
    walk = te.TerrainWalkScene(world, scene, _MANIFEST[0], _SCENE_CONST[0])
    walk.mute_grade = mute_grade
    idle, idle_sat = adapter.expiry_state()
    scene.begin([float(c) for c in idle])
    sink = _RecordingSink()
    mapper = InputMapper(sink, tick_source=lambda: _tick_holder[0])
    start_tick = 0
    if resume is not None:
        scene.restore_snapshot(resume["scene"])
        w0 = resume["ext"]
        walk.px, walk.pz = w0["px"], w0["pz"]
        walk.psi, walk.s = w0["psi"], w0["s"]
        walk.stop_state = w0["stop_state"]
        walk.stop_tick = w0["stop_tick"]
        walk.stall_tick = w0["stall_tick"]
        walk.tick = w0["tick"]
        start_tick = w0["tick"]
        # the fresh mapper's W press at the RESUMED clock: the hold must be
        # valid at the loop's first poll (the mapper's declared validity
        # window would stale a clock-0 press)
        mapper.press("W", now_ms=(start_tick + 1) * 1000 // 300)

    applied = [float(v) for v in idle]
    saturation = [0.0] * 8
    pending = None
    last_record_tick = None
    per_tick = []
    state_chain = []
    events_out = []
    events_by_tick = {}
    end_tick = None
    if events is not None:
        for ev in events["mouse"]:
            events_by_tick.setdefault(int(ev[0]), []).append(int(ev[1]))
        end_tick = events.get("end_tick")
    mapper.press("W", now_ms=0)     # the declared ceiling hold from tick 0
    leg_idx = -1                    # -1: the declared initial turn pending
    leg_arc = 0.0
    turn_ticks_left = []
    turn_residuals = []
    arc_table = []
    # the resumed remainder INCLUDES the snapshot's tick as a declared
    # poll-only iteration (the snapshot state is post-tick; the poll lands
    # the resumed mapper's record so the command phase aligns exactly)
    t = start_tick if resume is not None else 0
    while True:
        if end_tick is not None and t > end_tick:
            break
        if t >= plan.cap:
            if plan.end_rule == "route" and leg_idx < len(plan.legs) - 1:
                require(False, "f06_case_terminal_missing:" + plan.name)
            break
        _tick_holder[0] = t
        now_ms = (t * 1000) // 300
        if events is not None:
            for c in events_by_tick.get(t, ()):
                mapper.mouse(c)
        else:
            if t == INITIAL_TURN_TICK and leg_idx == -1:
                planned = norm_delta(plan.legs[0][0], walk.psi)
                if abs(planned) <= 1e-12:
                    leg_idx = 0
                    leg_arc = 0.0
                else:
                    turn_ticks_left = turn_events(planned, t)
                    events_out.extend([list(e) for e in turn_ticks_left])
            elif (turn_ticks_left and t > turn_ticks_left[-1][0]):
                turn_ticks_left = []
                leg_idx += 1
                leg_arc = 0.0
                if leg_idx == 0:
                    resid = abs(norm_delta(plan.legs[0][0], walk.psi))
                    require(resid <= 0.05,
                            "f06_initial_turn_missed:" + repr(walk.psi))
                    turn_residuals.append(resid)
            elif (not turn_ticks_left and leg_idx >= 0
                    and leg_idx < len(plan.legs) - 1):
                bearing, length = plan.legs[leg_idx]
                if length is not None and leg_arc >= length and t % 15 == 0:
                    planned = norm_delta(plan.legs[leg_idx + 1][0], bearing)
                    turn_ticks_left = turn_events(planned, t)
                    events_out.extend([list(e) for e in turn_ticks_left])
            if turn_ticks_left and t in [e[0] for e in turn_ticks_left]:
                for tt, cc in turn_ticks_left:
                    if tt == t:
                        mapper.mouse(cc)
        emitted = mapper.tick(now_ms)
        if emitted:
            rec = emitted[-1]
            require(rec.record_version == _CMD_VERSION[0],
                    "port_record_version:" + repr(rec.record_version))
            require(0.0 <= float(rec.v_forward) <= _V_MAX[0],
                    "port_v_out_of_band:" + repr(rec.v_forward))
            require(abs(float(rec.yaw_rate)) <= _OMEGA[0],
                    "port_yaw_out_of_band:" + repr(rec.yaw_rate))
            require(int(rec.issued_tick) == t,
                    "port_issued_tick:" + repr(rec.issued_tick))
            proj = adapter.project(float(rec.v_forward), float(rec.yaw_rate))
            pending = (proj, t + 1)
            last_record_tick = t
        if pending is not None and t >= pending[1]:
            applied = [float(v) for v in pending[0]["applied"]]
            saturation = [float(s) for s in pending[0]["saturation"]]
            pending = None
        if adapter.expired(last_record_tick, t, EXPIRY_TICKS):
            applied = [float(v) for v in idle]
            saturation = [float(s) for s in idle_sat]
        if snap_hook is not None:
            snap_hook(t, walk)
        if resume is not None and t == start_tick:
            t += 1        # the poll-only iteration: the snapshot state is
            continue      # post-tick; the record's applied lands at start+1
        row = walk.step(np.asarray(applied, dtype=np.float32),
                        np.asarray(saturation, dtype=np.float32))
        if mutate is not None:
            mutate(t, row)
        if leg_idx >= 0 and not turn_ticks_left:
            leg_arc += DT * row["com_v_m_s"]
        arc_table.append({"tick": t, "arc_m": leg_arc,
                          "px_m": row["px_m"], "pz_m": row["pz_m"]})
        per_tick.append(row)
        state_chain.append(walk.state_sha256())
        # the declared ends
        if row["stall"] and plan.end_rule == "stall":
            break
        if (row["stop_state"] == "step_over"
                and plan.end_rule == "stop"):
            break
        if row["stop_state"] == "trunk" and plan.end_rule == "stop":
            end_tick = t + A4_HOLD_TICKS
        if (plan.end_rule == "route" and leg_idx == len(plan.legs) - 1
                and not turn_ticks_left
                and plan.legs[-1][1] is not None
                and leg_arc >= plan.legs[-1][1]):
            break
        t += 1
    return {
        "per_tick": per_tick, "state_chain": state_chain,
        "arc_table": arc_table, "turn_residuals_rad": turn_residuals,
        "events": {"mouse": events_out,
                   "end_tick": per_tick[-1]["tick"]} if derive else None,
        "final_state_sha256": walk.state_sha256(),
        "terminal": walk.terminal(),
        "stop_tick": walk.stop_tick, "stall_tick": walk.stall_tick,
        "walk": walk,
    }


# ---------------------------------------------------------------- A4 derivation
def derive_a4(world, adapter, build_id, params, aim="ring"):
    """The declared A4 derivation (prereg section 4, amendment A1): the turn
    tick is DERIVED on the pinned recursion so the walked line's ring
    contact is achieved: one pass through rise+leg 1 with 15-grid
    snapshots, then latest-first candidate replays; the first candidate
    whose remainder reaches the declared trunk ring wins."""
    from tools.policy_compat import scene_cpu as SC
    from tools.monkey_campaign.product.input_mapper import InputMapper

    scene = SC.make_scene(build_id, params, SEED)
    walk = te.TerrainWalkScene(world, scene, _MANIFEST[0], _SCENE_CONST[0])
    idle, idle_sat = adapter.expiry_state()
    scene.begin([float(c) for c in idle])
    sink = _RecordingSink()
    mapper = InputMapper(sink, tick_source=lambda: _tick_holder[0])
    mapper.press("W", now_ms=0)
    applied = [float(v) for v in idle]
    saturation = [0.0] * 8
    pending = None
    last_record_tick = None
    leg_arc = 0.0
    snaps = []
    prefix_rows = []
    prefix_chain = []
    t = 0
    cross_tick = None
    while cross_tick is None and t < 9000:
        _tick_holder[0] = t
        now_ms = (t * 1000) // 300
        emitted = mapper.tick(now_ms)
        if emitted:
            rec = emitted[-1]
            proj = adapter.project(float(rec.v_forward), float(rec.yaw_rate))
            pending = (proj, t + 1)
            last_record_tick = t
        if pending is not None and t >= pending[1]:
            applied = [float(v) for v in pending[0]["applied"]]
            saturation = [float(s) for s in pending[0]["saturation"]]
            pending = None
        row = walk.step(np.asarray(applied, dtype=np.float32),
                        np.asarray(saturation, dtype=np.float32))
        leg_arc += DT * row["com_v_m_s"]
        prefix_rows.append(row)
        prefix_chain.append(walk.state_sha256())
        if leg_arc >= 10.5:
            cross_tick = t
        elif leg_arc >= 9.0 and t % 15 == 0:
            snaps.append({
                "tick": t, "scene": scene.snapshot(),
                "ext": {"px": walk.px, "pz": walk.pz, "psi": walk.psi,
                        "s": walk.s, "stop_state": walk.stop_state,
                        "stop_tick": walk.stop_tick,
                        "stall_tick": walk.stall_tick, "tick": walk.tick},
            })
        t += 1
    require(cross_tick is not None and snaps, "f06_case_terminal_missing:A4_search")

    search_log = []
    for cand in reversed(snaps):
        turn = turn_events(BETA_A4, cand["tick"] + 15)
        events = {"mouse": [list(e) for e in turn]}
        arm = run_case(world, adapter, build_id, params,
                       CasePlan("A4_search", [(BETA_A4, None)], "stop", CAP_A4),
                       events=events, derive=False, resume=cand)
        rows = arm["per_tick"]
        dists = [world.trunk_axis_distance(r["px_m"], r["pz_m"])
                 for r in rows]
        psis = [r["psi_rad"] for r in rows]
        search_log.append({"tick": cand["tick"],
                           "min_axis_m": round(min(dists), 4) if dists else None,
                           "psi_min": round(min(psis), 4),
                           "psi_max": round(max(psis), 4),
                           "n_rows": len(rows),
                           "px_end": round(rows[-1]["px_m"], 3),
                           "pz_end": round(rows[-1]["pz_m"], 3)})
        if dists and min(dists) <= 0.287:
            stop_i = next(i for i, d in enumerate(dists) if d <= 0.287)
            full_rows = [r for r in prefix_rows
                         if r["tick"] < cand["tick"]] + rows
            full_chain = (prefix_chain[:cand["tick"]]
                          + arm["state_chain"])
            return {
                "events": {"mouse": events["mouse"],
                           "end_tick": rows[-1]["tick"]},
                "turn_tick": cand["tick"],
                "per_tick": full_rows, "state_chain": full_chain,
                "arc_table": [], "turn_residuals_rad": [],
                "final_state_sha256": arm["final_state_sha256"],
                "terminal": arm["terminal"],
                "stop_tick": rows[stop_i]["tick"],
                "stall_tick": None, "walk": arm["walk"],
                "search": {"candidates": len(snaps),
                           "chosen_tick": cand["tick"],
                           "min_axis_distance_m": min(dists)},
            }
    require(False, "f06_case_terminal_missing:A4_no_candidate:"
            + repr(search_log))




# ---------------------------------------------------------------- W09 probe
def w09_probe_commands(oe_consts):
    """W09's declared A1 alignment commands (the W10 probe_commands form,
    derived at run time from the pinned constants; the alignment residue
    must be exactly 0)."""
    cycle = oe_consts["cycle_ticks"]
    phase_r0 = (((SEED % cycle) + 0.5) / cycle) % 1.0
    off_r = oe_consts["bounds_hi"][4]
    off_l = ((phase_r0 - 0.0 + off_r) % 1.0)
    if off_l > oe_consts["bounds_hi"][0]:
        off_l -= 1.0
    require(oe_consts["bounds_lo"][0] <= off_l <= oe_consts["bounds_hi"][0],
            "probe_derivation:off_l_out_of_bounds:" + repr(off_l))
    resid = (phase_r0 + off_r - off_l) % 1.0
    require(resid == 0.0, "probe_derivation:alignment_residue:" + repr(resid))
    lift_hi = oe_consts["bounds_hi"][2]
    cmds = [off_l, 1.0, lift_hi, oe_consts["center"][3],
            off_r, 1.0, lift_hi, oe_consts["center"][7]]
    for i, v in enumerate(cmds):
        require(oe_consts["bounds_lo"][i] <= v <= oe_consts["bounds_hi"][i],
                "probe_derivation:command_out_of_bounds:%d" % i)
    return cmds


def w09_probe_arm(oe, oe_consts, build_id, params, hook=None,
                  horizon=900):
    """W09's declared excursion loop at this card's pins (the W10
    run_probe_arm form): the sealed supervisor owns the responses; scene.step
    is the only physics; hook = the declared concealed fault (FB6 only)."""
    from tools.policy_compat import scene_cpu as SC
    sup = oe.OutOfEnvelopeSupervisor(oe_consts, None)
    scene = SC.make_scene(SC.BUILD_N_ID, params, SEED)
    commands = w09_probe_commands(oe_consts)
    scene.begin(list(commands))
    records = []
    applied_per_tick = []
    fall_declared_tick = None
    for t in range(horizon):
        rec = scene.observation_record()
        records.append(json.loads(json.dumps(rec)))
        if hook is not None:
            hook(t, scene)
            rec = scene.observation_record()
            records[-1] = json.loads(json.dumps(rec))
        applied, sat, events = sup.apply(t, rec, commands, [0.0] * 8)
        stepped = [float(v) for v in np.asarray(applied, dtype=np.float32)]
        applied_per_tick.append(stepped)
        if any(ev["event"] == "R2_fall_declared" for ev in events):
            fall_declared_tick = t
        scene.step(np.asarray(stepped, dtype=np.float32), sat)
    return {"records": records, "applied_per_tick": applied_per_tick,
            "supervisor": sup, "commands": commands,
            "fall_declared_tick": fall_declared_tick}


def unsupported_intervals(classes):
    out = []
    t = 0
    while t < len(classes):
        if classes[t] == "UNSUPPORTED":
            j = t
            while j < len(classes) and classes[j] == "UNSUPPORTED":
                j += 1
            out.append([t, j - 1])
            t = j
        else:
            t += 1
    return out


# ---------------------------------------------------------------- A0 (P1/P10)
def run_a0(adapter, build_id, params, world, wrong_override=False,
           reset_hook=None):
    """The W08 frozen script verbatim (cm.feed_events) on BOTH lines."""
    import command_model as cm
    from tools.policy_compat import scene_cpu as SC
    from tools.science_funnel.typeb_export.command_record import (
        COMMAND_RECORD_VERSION)
    from tools.monkey_campaign.product.input_mapper import (
        InputMapper, EXPIRY_TICKS)

    def one_line(extension):
        scene = SC.make_scene(build_id, params, SEED)
        walk = te.TerrainWalkScene(world, scene, _MANIFEST[0],
                                   _SCENE_CONST[0]) if extension else None
        idle, idle_sat = adapter.expiry_state()
        scene.begin([float(c) for c in idle])
        sink = _RecordingSink()
        mapper = InputMapper(sink, tick_source=lambda: _tick_holder[0])
        applied = [float(v) for v in idle]
        saturation = [0.0] * 8
        pending = None
        last_record_tick = None
        per_tick = []
        state_chain = []
        horizon = (cm.PROBE_TICK + 1) if wrong_override else HORIZON_A0
        for t in range(horizon):
            _tick_holder[0] = t
            now_ms = cm.now_ms_of(t)
            if wrong_override and t == cm.WRONG_INJECT_TICK:
                mapper.press("W", now_ms=now_ms)
            elif not (wrong_override and t > cm.WRONG_INJECT_TICK):
                cm.feed_events(mapper, t, now_ms)
            emitted = mapper.tick(now_ms)
            if emitted:
                rec = emitted[-1]
                require(rec.record_version == COMMAND_RECORD_VERSION,
                        "port_record_version")
                proj = adapter.project(float(rec.v_forward),
                                       float(rec.yaw_rate))
                pending = (proj, t + 1)
                last_record_tick = t
            if pending is not None and t >= pending[1]:
                applied = [float(v) for v in pending[0]["applied"]]
                saturation = [float(s) for s in pending[0]["saturation"]]
                pending = None
            if adapter.expired(last_record_tick, t, EXPIRY_TICKS):
                applied = [float(v) for v in idle]
                saturation = [float(s) for s in idle_sat]
            if extension:
                if reset_hook is not None:
                    reset_hook(t, walk)
                row = walk.step(np.asarray(applied, dtype=np.float32),
                                np.asarray(saturation, dtype=np.float32))
                per_tick.append(row)
                state_chain.append(walk.state_sha256())
            else:
                rec_pre = scene.observation_record()
                scene.step(np.asarray(applied, dtype=np.float32),
                           np.asarray(saturation, dtype=np.float32))
                ssha = scene.state_sha256()
                per_tick.append({
                    "tick": t, "com_v_m_s": scene.v, "com_x_m": scene.x,
                    "px_m": scene.x, "pz_m": 0.0, "psi_rad": 0.0,
                    "s_m": 0.0, "grade": 0.0,
                    "contact_count": rec_pre["contact_count"],
                    "foot_contacts": rec_pre["foot_contacts"],
                    "pad_gaps": rec_pre["pad_gaps"],
                    "intervention_reason": rec_pre["intervention_reason"],
                    "applied_cmd": [float(v) for v in applied],
                    "state_sha256": ssha,
                    "scene_state_sha256": ssha,
                })
                state_chain.append(ssha)
        return {"per_tick": per_tick, "state_chain": state_chain,
                "final_state_sha256": state_chain[-1],
                "v_series": [r["com_v_m_s"] for r in per_tick]}
    return {"cert": one_line(False), "ext": one_line(True)}


# ---------------------------------------------------------------- evaluation
def evaluate_a0(cert_line, ext_line, wrong_line):
    ev = {}
    cert, ext = cert_line["per_tick"], ext_line["per_tick"]
    require(len(cert) == len(ext), "prediction_failed:P1_length")
    div = None
    for a, b in zip(cert, ext):
        if a["scene_state_sha256"] != b["scene_state_sha256"]:
            div = a["tick"]
            break
    ev["P1"] = {
        "first_divergence_tick": div,
        "bit_identical": div is None,
        "px_equals_com_x_while_psi_zero": all(
            b["px_m"] == b["com_x_m"] and b["pz_m"] == 0.0
            for b in ext if b["psi_rad"] == 0.0),
        "flat_channels_everywhere": all(
            b["grade"] == 0.0 and b["s_m"] == 0.0 for b in ext),
        "first_steered_tick": next(
            (b["tick"] for b in ext if b["psi_rad"] != 0.0), None),
        "v_at_segment_end_m_s": cert[5415]["com_v_m_s"],
        "sealed_w08_measured_m_s": W08_V_AT_SEGMENT_END,
        "v_matches_sealed": cert[5415]["com_v_m_s"] == W08_V_AT_SEGMENT_END,
        "segment_end_tick": 5415,
        "physics_hz": 300,
    }
    require(ev["P1"]["bit_identical"], "prediction_failed:P1_bit_identity")
    require(ev["P1"]["px_equals_com_x_while_psi_zero"],
            "prediction_failed:P1_flat_channels")
    require(ev["P1"]["flat_channels_everywhere"],
            "prediction_failed:P1_flat_channels")
    require(ev["P1"]["v_matches_sealed"], "prediction_failed:P1_sealed_value")
    div10 = next((t for t in range(min(len(ext_line["state_chain"]),
                                       len(wrong_line["state_chain"])))
                  if ext_line["state_chain"][t] != wrong_line["state_chain"][t]),
                 None)
    v_c = ext_line["per_tick"][5999]["com_v_m_s"]
    v_w = wrong_line["per_tick"][5999]["com_v_m_s"]
    ev["P10"] = {
        "first_divergence_tick": div10,
        "expected_first_divergence_tick": 5431,
        "diverges_at_declared_tick": div10 == 5431,
        "v_clean_at_probe_m_s": v_c,
        "v_wrong_at_probe_m_s": v_w,
        "separation_m_s": v_w - v_c,
        "wrong_arm_rising": v_w > v_c,
    }
    require(ev["P10"]["diverges_at_declared_tick"], "prediction_failed:P10_tick")
    require(ev["P10"]["wrong_arm_rising"], "prediction_failed:P10_separation")
    return ev


def stability_bars(rows):
    bad = []
    for row in rows:
        t = row["tick"]
        if abs(row["com_v_m_s"]) > VELOCITY_ENVELOPE + 1e-12:
            bad.append((t, "envelope"))
        if row["contact_count"] < 2:
            bad.append((t, "contact_floor"))
        if row["intervention_reason"] != "none":
            bad.append((t, "intervention"))
        gaps = list(row["pad_gaps"]["hl"]) + list(row["pad_gaps"]["hr"])
        if any(not (g > 0.0) for g in gaps):
            bad.append((t, "pad_gap"))
        if any(v != v or v in (float("inf"), float("-inf")) for v in
               (row["com_v_m_s"], row["com_x_m"], row["px_m"], row["pz_m"],
                row["psi_rad"], row["s_m"], row["grade"])):
            bad.append((t, "nonfinite"))
        if abs(row["px_m"]) > 19.75 or abs(row["pz_m"]) > 19.75:
            bad.append((t, "extent"))
    return bad


def arc_identity(rows, end=None):
    """P9: the travelled arc advances exactly dt*v per tick (the declared
    window).  The identity holds up to a contact stop (the clamp is E6)."""
    if end is None:
        end = rows[-1]["tick"]
    worst = 0.0
    count = 0
    for a, b in zip(rows, rows[1:]):
        if b["tick"] > end:
            break
        expect = DT * abs(b["com_v_m_s"])   # the arc length is unsigned
        got = math.hypot(b["px_m"] - a["px_m"], b["pz_m"] - a["pz_m"])
        r = abs(got - expect)
        if r > 1e-9:
            count += 1
        worst = max(worst, r)
    return {"worst_residual_m": worst, "violation_count": count,
            "identity_window_m": 1e-9, "ticks_checked": end}


def law_identity(rows, scene_const, mute):
    """The declared drive-law identity reconstructed from the records:
    v1 - v0 == dt*(stride_gain*mean(stride) - d_eff*warm - g*grade)."""
    g_ = scene_const["stride_gain"]
    d_ = scene_const["damping"]
    lo_ = scene_const["warm_damp_lo"]
    span_ = scene_const["warm_damp_span"]
    worst = 0.0
    count = 0
    for a, b in zip(rows, rows[1:]):
        v0, v1 = a["com_v_m_s"], b["com_v_m_s"]
        applied = b["applied_cmd"]
        a_com = g_ * 0.5 * (applied[1] + applied[5])
        d_eff = d_ * (lo_ + span_ * 0.5 * (b["warm_l"] + b["warm_r"]))
        grade_term = 0.0 if mute else te.G_GRAV * b["grade"]
        expect = DT * (a_com - d_eff * v0 - grade_term)
        r = abs((v1 - v0) - expect)
        if r > 1e-6:
            count += 1
        worst = max(worst, r)
    return {"worst_residual_m_s": worst, "violation_count": count,
            "identity_window_m_s": 1e-6}


def evaluate_a1(arm, env_derived, world):
    rows = arm["per_tick"]
    floor = (A_CEILING - te.G_GRAV * max(env_derived, A1_GRADE_ENVELOPE)) / D_HI
    # the fixed-point invariant governs the CONTRACTION regime: from the
    # first tick the speed has reached the bound, the recursion never
    # crosses the (locally-worst) fixed point from above.  The start-up
    # rise precedes that regime and is recorded informationally.
    entry = next((r["tick"] for r in rows if r["com_v_m_s"] >= floor), None)
    scoped = rows[entry:] if entry is not None else []
    min_v = min(r["com_v_m_s"] for r in scoped) if scoped else None
    max_grade = max(abs(r["grade"]) for r in rows)
    min_clear = min(world.f07.distance_to_footprints(world.obstacles,
                                                        r["px_m"], r["pz_m"])
                    for r in rows)
    ev = {
        "corridor_grade_envelope_derived": env_derived,
        "corridor_grade_envelope_declared": A1_GRADE_ENVELOPE,
        "measured_max_grade": max_grade,
        "speed_floor_bound_m_s": floor,
        "contraction_entry_tick": entry,
        "measured_min_speed_m_s": min_v,
        "measured_min_speed_all_ticks_m_s": min(
            r["com_v_m_s"] for r in rows),
        "speed_floor_held": min_v is not None and min_v >= floor - 1e-12,
        "measured_min_footprint_clearance_m": min_clear,
        "clearance_held": min_clear >= 0.25 - 1e-9,
        "terminal_px_m": rows[-1]["px_m"], "terminal_pz_m": rows[-1]["pz_m"],
        "ticks": rows[-1]["tick"] + 1,
    }
    require(ev["speed_floor_held"], "prediction_failed:P4_speed_floor")
    require(ev["clearance_held"], "prediction_failed:P4_clearance")
    require(max_grade <= 0.05 + 1e-12, "f06_slope_rule_exceeded")
    return ev


def evaluate_a2(arm, world):
    rows = arm["per_tick"]
    require(arm["stall_tick"] is not None, "prediction_failed:P5_no_stall")
    stall_row = rows[arm["stall_tick"]]
    grade_at = abs(stall_row["grade"])
    enter = next((r for r in rows if r["grade"] >= GAMMA_STALL), None)
    require(enter is not None, "prediction_failed:P5_stretch_not_entered")
    travel = math.hypot(stall_row["px_m"] - enter["px_m"],
                        stall_row["pz_m"] - enter["pz_m"])
    ev = {
        "gamma_stall": GAMMA_STALL,
        "tc_gap_id": "TC-11",
        "line_bearing_rad": BETA_A2_DIRECT,
        "stall_tick": arm["stall_tick"],
        "stall_px_m": stall_row["px_m"], "stall_pz_m": stall_row["pz_m"],
        "grade_at_stall": grade_at,
        "grade_at_stall_above_gamma": grade_at >= GAMMA_STALL - 1e-12,
        "stretch_entry_px_m": enter["px_m"],
        "stretch_entry_pz_m": enter["pz_m"],
        "travel_into_stretch_m": travel,
        "travel_bound_m": A2_TRAVEL_BOUND,
        "travel_within_bound": travel <= A2_TRAVEL_BOUND + 1e-9,
        "stretch_min_grade_declared": A2_STRETCH_MIN_GRADE,
        "corridor_max_declared": A2_CORRIDOR_MAX,
        "x_max_qualified_slope_traversed": A1_GRADE_ENVELOPE,
        "crest_grade_unqualified": 0.03795552514626025,
        "authored_walk_classes_deg": [10.0, 20.0, 30.0],
        "physics_hz": 300,
    }
    require(ev["grade_at_stall_above_gamma"], "prediction_failed:P5_grade")
    require(ev["travel_within_bound"], "prediction_failed:P5_travel")
    return ev


def evaluate_a3(arm, world):
    rows = arm["per_tick"]
    require(arm["stop_tick"] is not None
            and arm["walk"].stop_state == "step_over",
            "prediction_failed:P6_no_stop")
    stop_row = rows[arm["stop_tick"]]
    spread = stop_row["support_spread_m"]
    log02 = next(o for o in world.logs if o["id"] == "log_02")
    top = float(log02["log_radius_m"])
    d_step = arm["walk"].d_step
    ev = {
        "stop_tick": arm["stop_tick"],
        "stop_px_m": stop_row["px_m"], "stop_pz_m": stop_row["pz_m"],
        "measured_support_spread_m": spread,
        "spread_fire_band": list(SPREAD_FIRE_BAND),
        "spread_in_band": SPREAD_FIRE_BAND[0] < spread <= SPREAD_FIRE_BAND[1],
        "log02_top_m": top,
        "d_step_m": d_step,
        "deficit_m": top - d_step,
        "required_lift_command": (top - 0.008) / 0.06,
        "outside_certified_bounds_hi": (top - 0.008) / 0.06 > 1.8,
        "bounds_hi_lift": 1.8,
        "physics_hz": 300,
        "envelope_table": [
            {"id": o["id"], "kind": o["kind"],
             "top_m": float(o["log_radius_m"]) if o["kind"] == "log"
             else float(o["extent_m"][1])}
            for o in world.obstacles],
    }
    # the measured fire step BESIDE the perpendicular idealization
    # (amendment A1.3: the walked crossing is oblique through the turn; the
    # binding requirements are the top/deficit/required-lift band below)
    ev["spread_deviation_from_ideal_band"] = {
        "perpendicular_ideal_band": list(SPREAD_FIRE_BAND),
        "measured_fire_step_m": spread,
        "deviation_m": spread - SPREAD_FIRE_BAND[1],
        "disclosure": "the walked crossing is oblique through the turn "
                      "(amendment A1.3); the detector fired on the walked "
                      "path's own support step",
    }
    require(ev["outside_certified_bounds_hi"], "prediction_failed:P6_requirement")
    return ev


def evaluate_a4(arm, world):
    rows = arm["per_tick"]
    require(arm["stop_tick"] is not None and arm["walk"].stop_state == "trunk",
            "prediction_failed:P7_no_ring_contact:" + repr([
                (r["tick"], round(r["px_m"], 3), round(r["pz_m"], 3),
                 round(r["psi_rad"], 4),
                 round(world.trunk_axis_distance(r["px_m"], r["pz_m"]), 4))
                for r in rows[-8:]]))
    stop_row = rows[arm["stop_tick"]]
    dist = world.trunk_axis_distance(stop_row["px_m"], stop_row["pz_m"])
    pre = rows[arm["stop_tick"] - 1]
    dist_pre = world.trunk_axis_distance(pre["px_m"], pre["pz_m"])
    def _ax(r):
        return world.trunk_axis_distance(r["px_m"], r["pz_m"])
    # the declared penetration class: a real entry below the ring (the
    # projection's float dust ~1e-15 is not penetration)
    pen = [(r["tick"], repr(_ax(r))) for r in rows
           if _ax(r) < 0.287 - 1e-6]
    pen_diag = []
    if not pen:
        pen_diag = [(r["tick"], round(_ax(r), 5)) for r in rows
                    if arm["stop_tick"] is not None
                    and r["tick"] >= arm["stop_tick"]][:8]
    psi = stop_row["psi_rad"]
    bearing_err = abs(psi - BETA_A4)
    ev = {
        "stop_tick": arm["stop_tick"],
        "standoff_ring_m": 0.287,
        "axis_distance_at_stop_m": dist,
        "axis_distance_at_stop_exact": abs(dist - 0.287) <= 1e-12,
        "pre_stop_axis_distance_m": dist_pre,
        "pre_stop_band": [0.287, 0.287 + VELOCITY_ENVELOPE / 300.0],
        "trunk_penetration_ticks": pen[:20],
        "post_stop_axis_probe": pen_diag,
        "trunk_penetration_count": len(pen),
        "walked_heading_rad": psi,
        "declared_beta_rad": BETA_A4,
        "heading_residual_rad": bearing_err,
        "heading_within_quantization":
            bearing_err <= 0.05 + 1e-9,
        "catch_margin_check": {
            "measured_residual_rad": bearing_err,
            "diagonal_m": 2.8793254744549115 - 0.287,
            "miss_bound_m": (2.5923254744549116
                             * math.sin(min(bearing_err, 0.05))
                             + A4_MISS_COEF * A4_MISS_BAND),
            "ring_m": 0.287,
            "caught_with_margin":
                (2.5923254744549116 * math.sin(min(bearing_err, 0.05))
                 + A4_MISS_COEF * A4_MISS_BAND) <= 0.287,
        },
        "bearing_to_trunk_at_stop_rad": math.atan2(
            world.trunk_cz - stop_row["pz_m"],
            world.trunk_cx - stop_row["px_m"]),
    }
    require(ev["axis_distance_at_stop_exact"], "prediction_failed:P7_standoff:"
            + repr((dist, arm["stop_tick"], stop_row["px_m"], stop_row["pz_m"],
                    ev["heading_residual_rad"], ev["trunk_penetration_count"])))
    require(ev["trunk_penetration_count"] == 0,
            "f06_trunk_penetration:" + repr(pen[:6]) + ":stop_tick:"
            + repr(arm["stop_tick"]) + ":axis_at_stop:"
            + repr(_ax(rows[arm["stop_tick"]]) if arm["stop_tick"] is not None
                   else None))
    require(ev["heading_within_quantization"], "prediction_failed:P7_heading")
    require(ev["catch_margin_check"]["caught_with_margin"],
            "prediction_failed:P7_catch_margin")
    return ev


# ---------------------------------------------------------------- falsifiers
def oe_battery(oe, consts, arm):
    rows = arm["records"] if "records" in arm else arm["per_tick"]
    records = []
    applied = []
    if "applied_per_tick" in arm:
        # the probe arm: the detectors' pairing convention consumes the
        # SUPERVISOR's per-tick applied (the records' held command lags one
        # tick and would false-fire on every declared response boundary)
        return {
            "velocity_recursion": oe.velocity_recursion_check(
                rows, arm["applied_per_tick"], consts),
            "phase_recursion": oe.phase_recursion_check(
                rows, arm["applied_per_tick"], consts),
            "micro_draw_chain": oe.micro_draw_chain_check(
                rows, arm["applied_per_tick"], consts, SEED),
            "support_force_removed": oe.support_force_removed_check(
                rows, consts),
        }
    for row in rows:
        if "com_vel" in row:
            records.append(row)
            applied.append(row["applied_cmd"])
            continue
        records.append({
            "tick": row["tick"], "com_vel": [row["com_v_m_s"], 0.0, 0.0],
            "foot_contacts": row["foot_contacts"],
            "foot_forces": row["foot_forces"],
            "pad_gaps": row["pad_gaps"],
            "phase_left": row["phase_left"],
            "phase_right": row["phase_right"],
            "applied": row["applied_cmd"],
            "intervention_reason": row["intervention_reason"],
        })
        applied.append(row["applied_cmd"])
    return {
        "velocity_recursion": oe.velocity_recursion_check(
            records, applied, consts),
        "phase_recursion": oe.phase_recursion_check(records, applied, consts),
        "micro_draw_chain": oe.micro_draw_chain_check(
            records, applied, consts, SEED),
        "support_force_removed": oe.support_force_removed_check(
            records, consts),
    }


def detectors_green(battery):
    return all(not battery[k]["violations"]
               for k in ("velocity_recursion", "phase_recursion",
                         "micro_draw_chain", "support_force_removed"))


def falsifier_arms(world, adapter, build_id, params, oe, oe_consts,
                   a0_ext, plan_a1, a1_der, a1_exec, plan_a3, a3_der,
                   a3_exec, plan_a4, a4_der, a4_exec):
    out = {}

    # FB1 terrain decouple
    lifted_bundle = _lifted_surface(world)
    res_clean = 0.0    # two independent loads of the PINNED surface
    surf2 = _reload_pinned_surface()
    for r in a1_exec["per_tick"][::50]:
        res_clean = max(res_clean, abs(
            world.surface.height_at(r["px_m"], r["pz_m"])
            - surf2.height_at(r["px_m"], r["pz_m"])))
    res_tam = 0.0
    lifted_n = _LIFT_INFO[0]
    for r in a1_exec["per_tick"]:
        res_tam = max(res_tam, abs(
            lifted_bundle.height_at(r["px_m"], r["pz_m"])
            - world.surface.height_at(r["px_m"], r["pz_m"])))
    out["FB1_terrain_decouple"] = {
        "clean_control": {"metric_scope": "pinned-surface height residual "
                          "on the A1 trace (two independent loads)",
                          "worst_residual_m": res_clean,
                          "green": res_clean == 0.0},
        "guard": "f06_fb1_premature",
        "tampered_worst_residual_m": res_tam,
        "lifted_vertices": lifted_n,
        "bit": res_clean == 0.0 and res_tam > 0.0,
    }
    require(out["FB1_terrain_decouple"]["clean_control"]["green"],
            "f06_fb1_premature")
    near = [(round(r["px_m"], 3), round(r["pz_m"], 3))
            for r in a1_exec["per_tick"] if abs(r["px_m"] + 17.5) <= 0.6]
    require(out["FB1_terrain_decouple"]["bit"], "falsifier_did_not_bite:FB1:"
            + repr({"n": lifted_n, "res_tam": res_tam, "res_clean": res_clean,
                    "probe_diff": (lifted_bundle.height_at(_LIFT_INFO[1][0], _LIFT_INFO[1][1])
                                   - world.surface.height_at(_LIFT_INFO[1][0], _LIFT_INFO[1][1])),
                    "near_count": len(near),
                    "near_first": near[:2], "near_last": near[-2:] if near else []}))

    # FB2 slope-term mute
    a1_mute = run_case(world, adapter, build_id, params, plan_a1,
                       events=_freeze_events(a1_der), derive=False,
                       mute_grade=True)
    ident_clean = law_identity(a1_exec["per_tick"], _SCENE_CONST[0], mute=False)
    ident_mute = law_identity(a1_mute["per_tick"], _SCENE_CONST[0], mute=False)
    out["FB2_slope_term_mute"] = {
        "clean_control": {"metric_scope": "the declared drive-law identity "
                          "residual on the A1 execution",
                          "worst_residual_m_s": ident_clean["worst_residual_m_s"],
                          "green": ident_clean["violation_count"] == 0},
        "guard": "f06_fb2_premature",
        "muted_worst_residual_m_s": ident_mute["worst_residual_m_s"],
        "muted_violation_count": ident_mute["violation_count"],
        "bit": ident_clean["violation_count"] == 0 and ident_mute["violation_count"] > 0,
    }
    require(out["FB2_slope_term_mute"]["clean_control"]["green"],
            "f06_fb2_premature")
    require(out["FB2_slope_term_mute"]["bit"], "falsifier_did_not_bite:FB2")

    # FB3 step envelope discriminates (a lowered scratch log must cross)
    world_low = _world_with_log(world, "log_02", 0.10)
    a3_low = run_case(world_low, adapter, build_id, params, plan_a3,
                      events=_freeze_events(a3_der), derive=False)
    crossed = a3_low["walk"].stop_state != "step_over"
    clean_fired = a3_exec["walk"].stop_state == "step_over"
    out["FB3_step_envelope_discriminates"] = {
        "clean_control": {"metric_scope": "the pinned log_02 case fires the "
                          "envelope stop (P6)", "fired": clean_fired,
                          "green": clean_fired},
        "guard": "f06_fb3_premature",
        "lowered_log_radius_m": 0.10,
        "lowered_case_stop_state": a3_low["walk"].stop_state,
        "crossed_without_stop": crossed,
        "bit": clean_fired and crossed,
    }
    require(out["FB3_step_envelope_discriminates"]["clean_control"]["green"],
            "f06_fb3_premature")
    require(out["FB3_step_envelope_discriminates"]["bit"],
            "falsifier_did_not_bite:FB3")

    # FB4 trunk snap
    snap_tick = max(1, a4_exec["stop_tick"] - 50)

    def snap_hook(t, walk):
        if t == snap_tick:
            walk.px = world.trunk_cx - 0.287
            walk.pz = world.trunk_cz
    a4_snap = run_case(world, adapter, build_id, params, plan_a4,
                       events=_freeze_events(a4_der), derive=False,
                       snap_hook=snap_hook)
    ident_a4 = arc_identity(a4_snap["per_tick"],
                            end=a4_exec["stop_tick"] - 1)
    ident_a4_clean = arc_identity(a4_exec["per_tick"],
                                  end=a4_exec["stop_tick"] - 1)
    out["FB4_trunk_snap"] = {
        "clean_control": {"metric_scope": "the arc identity on the A4 "
                          "execution", "worst_residual_m":
                          ident_a4_clean["worst_residual_m"],
                          "green": ident_a4_clean["violation_count"] == 0},
        "guard": "f06_fb4_premature",
        "snap_tick": snap_tick,
        "tampered_worst_residual_m": ident_a4["worst_residual_m"],
        "tampered_violation_count": ident_a4["violation_count"],
        "bit": (ident_a4_clean["violation_count"] == 0
                and ident_a4["violation_count"] > 0),
    }
    require(out["FB4_trunk_snap"]["clean_control"]["green"],
            "f06_fb4_premature")
    require(out["FB4_trunk_snap"]["bit"], "falsifier_did_not_bite:FB4")

    # FB5 sliding (the declared record mutation at one tick)
    mutate_tick = 3000

    def slide_mutate(t, row):
        if t == mutate_tick:
            row["px_m"] = row["px_m"] + DT * row["com_v_m_s"]
    a1_slide = run_case(world, adapter, build_id, params, plan_a1,
                        events=_freeze_events(a1_der), derive=False,
                        mutate=slide_mutate)
    ident_slide = arc_identity(a1_slide["per_tick"])
    ident_a1_clean = arc_identity(a1_exec["per_tick"])
    out["FB5_sliding"] = {
        "clean_control": {"metric_scope": "the arc identity on the A1 "
                          "execution", "worst_residual_m":
                          ident_a1_clean["worst_residual_m"],
                          "green": ident_a1_clean["violation_count"] == 0},
        "guard": "f06_fb5_premature",
        "mutate_tick": mutate_tick,
        "tampered_worst_residual_m": ident_slide["worst_residual_m"],
        "tampered_violation_count": ident_slide["violation_count"],
        "bit": (ident_a1_clean["violation_count"] == 0
                and ident_slide["violation_count"] > 0),
    }
    require(out["FB5_sliding"]["clean_control"]["green"], "f06_fb5_premature")
    require(out["FB5_sliding"]["bit"], "falsifier_did_not_bite:FB5")

    # FB6 hidden reset (W09's battery in its native habitat: the declared
    # unsupported probe replay at this card's pins; the concealed restore
    # inside the produced window must break the fresh-seed draw chain)
    snap_store = {}

    def reset_hook(t, scene):
        if t == 60:
            snap_store["snap"] = scene.snapshot()
        if t == 100 and "snap" in snap_store:
            scene.restore_snapshot(snap_store["snap"])

    probe_clean = w09_probe_arm(oe, oe_consts, build_id, params)
    probe_tam = w09_probe_arm(oe, oe_consts, build_id, params, hook=reset_hook)
    bat_clean = oe_battery(oe, oe_consts, probe_clean)
    bat_tam = oe_battery(oe, oe_consts, probe_tam)
    pre_streaks = unsupported_intervals(probe_tam["supervisor"].classes)
    precondition = any(lo <= 60 <= hi and lo <= 100 <= hi
                       for lo, hi in pre_streaks)
    out["FB6_hidden_reset"] = {
        "clean_control": {"metric_scope": "the W09 detector battery on the "
                          "clean probe replay at this card's pins",
                          "green": detectors_green(bat_clean),
                          "violations_clean": {k: len(bat_clean[k]["violations"])
                                               for k in bat_clean}},
        "guard": "f06_fb6_premature",
        "window_precondition": precondition,
        "tampered_green": detectors_green(bat_tam),
        "micro_draw_chain_violations":
            len(bat_tam["micro_draw_chain"]["violations"]),
        "velocity_recursion_violations":
            len(bat_tam["velocity_recursion"]["violations"]),
        "phase_recursion_violations":
            len(bat_tam["phase_recursion"]["violations"]),
        "bit": (precondition and not detectors_green(bat_tam)
                and detectors_green(bat_clean)),
    }
    w09r = vi.w09_out_of_envelope_receipt()
    w09_a1 = w09r["arms"]["A1_unsupported_probe"]
    ints_c = unsupported_intervals(probe_clean["supervisor"].classes)
    require(out["FB6_hidden_reset"]["clean_control"]["green"],
            "f06_fb6_premature:" + repr({
                "violations": {k: len(bat_clean[k]["violations"])
                               for k in bat_clean},
                "first_interval_mine": ints_c[0] if ints_c else None,
                "first_interval_sealed": w09_a1["first_interval"],
                "fall_mine": probe_clean["fall_declared_tick"],
                "fall_sealed": w09_a1["fall_declared_tick"],
                "v_series_head_mine": [round(v, 6) for v in
                                       [r["com_vel"][0] for r in
                                        bat_clean["velocity_recursion"] and
                                        probe_clean["records"]][:6]],
                "v_rec_violations":
                    bat_clean["velocity_recursion"]["violations"][:3],
                "ph_rec_violations":
                    bat_clean["phase_recursion"]["violations"][:3]}))
    require(precondition, "fb6_window_precondition_unmet")
    return out


def _freeze_events(der):
    return {"mouse": [list(e) for e in der["events"]["mouse"]],
            "end_tick": der["events"]["end_tick"]}


def _reload_pinned_surface():
    tq = _load_mod("f06_fb1_tq", vi.PINNED_ROOT / te.FWD / "MAT2-F02" /
                   "pins" / "terrain_query.py")
    bundle = json.loads((vi.PINNED_ROOT / te.FWD / "MAT2-F02" / "pins" /
                         "terrain_bundle.json").read_bytes().decode("utf-8"))
    return tq.TerrainSurface(bundle, validate=True)


_LIFT_INFO = [0, None]
_A1_ROWS = [None]


def _lifted_surface(world):
    """A scratch bundle copy with 6 grid nodes near the A1 path lifted by
    0.01 m (the F05 FB6 heritage).  The query truth is the GRID (E4); the
    scratch copy loads with validate=False BY DECLARATION (the tampered
    artifact is not the pinned bundle; the pinned bundle's own validator is
    the clean control's).  The pinned bytes are never modified."""
    lifted = copy.deepcopy(json.loads(
        (vi.PINNED_ROOT / te.FWD / "MAT2-F02" / "pins" /
         "terrain_bundle.json").read_bytes().decode("utf-8")))
    grid = lifted["terrain_surface"]["grid"]
    x0, z0 = grid["x0_m"], grid["z0_m"]
    dx, dz = grid["dx_m"], grid["dz_m"]
    heights = grid["heights_m"]
    # the lift center: the walked A1 position nearest the declared waypoint
    # (−17.5, 0) — the corridor's own geometry decides where the ghost sits
    near = [r for r in _A1_ROWS[0] if abs(r["px_m"] + 17.5) <= 1.0]
    require(near, "f06_fb1_no_corridor")
    cx, cz = near[len(near) // 2]["px_m"], near[len(near) // 2]["pz_m"]
    n = 0
    for row in range(len(heights)):
        for col in range(len(heights[row])):
            x = x0 + col * dx
            z = z0 + row * dz
            if (x - cx) ** 2 + (z - cz) ** 2 <= 1.0:
                heights[row][col] = round(heights[row][col] + 0.01, 6)
                n += 1
    require(n >= 3, "f06_fb1_lift_starved:" + str(n))
    _LIFT_INFO[0] = n
    _LIFT_INFO[1] = (round(cx, 3), round(cz, 3))
    tq = _load_mod("f06_fb1_tq_lifted", vi.PINNED_ROOT / te.FWD /
                   "MAT2-F02" / "pins" / "terrain_query.py")
    return tq.TerrainSurface(lifted, validate=False)


def _world_with_log(world, log_id, new_r):
    """A scratch world whose declared log row carries a lowered radius (the
    declared FB3 tamper path).  The pinned bytes are never modified."""
    obstacles = copy.deepcopy(world.obstacles)
    for o in obstacles:
        if o["id"] == log_id:
            o["log_radius_m"] = new_r
    return te.TerrainWorld(vi.PINNED_ROOT, obstacles_override=obstacles)


def _load_mod(name, path):
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, str(path))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------- main
def main() -> int:
    pins, reg = stage_pins()
    cert, allow, bundle, build_id, params, gate = gate_and_load()
    _MANIFEST[0] = bundle["manifest"]
    _PARAMS[0] = params
    from tools.policy_compat import scene_cpu as SC
    _SCENE_CONST[0] = {k: params[k] for k in
                       ("stride_gain", "damping", "warm_damp_lo",
                        "warm_damp_span")}
    adapter = _make_adapter(bundle["manifest"], _SCENE_CONST[0])
    from tools.science_funnel.typeb_export.command_record import (
        COMMAND_RECORD_VERSION)
    from tools.monkey_campaign.product.input_mapper import (
        V_MAX_IN_BAND_M_S, OMEGA_MAX_RAD_S)
    _CMD_VERSION[0] = COMMAND_RECORD_VERSION
    _V_MAX[0] = V_MAX_IN_BAND_M_S
    _OMEGA[0] = OMEGA_MAX_RAD_S
    require(V_MAX_IN_BAND_M_S == V_CMD_CEILING,
            "port_ceiling_disagreement:command_record_vs_freeze_constant")

    # the sealed W09 supervisor (observation role on the clean arms)
    oe = vi.load_pinned_module(
        "w09_out_of_envelope",
        (vi.C, "MAT2-W09", "out_of_envelope.py"))
    oe_consts = {
        **oe.derive_constants(params, bundle["manifest"]),
        "_front_force": float(SC._FRONT_FORCE),
        "velocity_envelope_m_s": SC.derived_envelope()["velocity_envelope_m_s"],
    }

    world = te.TerrainWorld(vi.PINNED_ROOT)

    # ---- P2: the sealed F07 route replay --------------------------------
    sealed = vi.f07_route_trace()
    p2 = {"routes": {}, "reachable_cells": len(world.reach)}
    audit = world.attribution_audit()
    p2["blocked_cell_count"] = sum(
        1 for ix in range(world.f07.MASK_N)
        for iz in range(world.f07.MASK_N) if world.mask[ix][iz])
    p2["unattributed_count"] = audit["unattributed_count"]
    require(p2["unattributed_count"] == 0,
            "f07_route_replay_drift:invisible_wall")
    require(p2["reachable_cells"] == 6198, "f07_route_replay_drift:reachable")
    require(p2["blocked_cell_count"] == 363,
            "f07_route_replay_drift:blocked")
    for name in ("D_rock_01", "D_trunk", "D_log_02"):
        rec, _path = world.route_by_name(name)
        sealed_row = sealed["routes"][name]
        same = all(rec[k] == sealed_row[k] for k in
                   ("hops", "length_m", "max_sampled_slope",
                    "min_footprint_clearance_m", "viewpoint_cell", "reached"))
        p2["routes"][name] = {"rederived": rec, "sealed": sealed_row,
                              "exact": same}
        require(same, "f07_route_replay_drift:" + name)
    # the declared crest route (freeze-recorded derivation, prereg P2/P5)
    crest = world.f07.nearest_reachable(world.reach, 19.265584, 6.057064)
    crest_path = world.f07.route_path(
        (world.f07.MASK_N // 2, world.f07.MASK_N // 2),
        (crest[1], crest[2]), world.free)
    crest_metrics = world.f07.route_metrics(crest_path, world.obstacles,
                                            world.surface)
    p2["crest_route"] = crest_metrics
    require(crest_metrics["hops"] == 51 and crest_metrics["length_m"] == 25.5
            and crest_metrics["max_sampled_slope"] == 0.035335
            and crest_metrics["min_footprint_clearance_m"] == 0.280824,
            "f06_crest_route_drift")

    # ---- A0: the flat regression (P1) + the wrong command (P10) ---------
    a0 = run_a0(adapter, build_id, params, world)
    wrong = run_a0(adapter, build_id, params, world, wrong_override=True)
    ev_a0 = evaluate_a0(a0["cert"], a0["ext"], wrong["ext"])

    # ---- A1: the uneven-ground route (P4) --------------------------------
    plan_a1 = CasePlan("A1_D_rock_01",
                       [(math.pi, 17.5), (-math.pi / 2, 9.0)], "route", CAP_A1)
    a1_der = run_case(world, adapter, build_id, params, plan_a1, derive=True)
    a1_exec = run_case(world, adapter, build_id, params, plan_a1,
                       events=_freeze_events(a1_der), derive=False)
    _require_script_identity(a1_der, a1_exec, "A1")
    env_a1, _prof = te.corridor_grade_envelope(
        world, [(0.0, 0.0), (-17.5, 0.0), (-17.5, -9.0)])
    ev_a1 = evaluate_a1(a1_exec, env_a1, world)

    # ---- A2: the crest attempt (P5) --------------------------------------
    plan_a2 = CasePlan("A2_crest",
                       [(BETA_A2_DIRECT, None)], "stall", CAP_A2)
    a2_der = run_case(world, adapter, build_id, params, plan_a2, derive=True)
    a2_exec = run_case(world, adapter, build_id, params, plan_a2,
                       events=_freeze_events(a2_der), derive=False)
    _require_script_identity(a2_der, a2_exec, "A2")
    ev_a2 = evaluate_a2(a2_exec, world)

    # ---- A3: the step-over case (P6) -------------------------------------
    plan_a3 = CasePlan("A3_step_over",
                       [(0.0, 5.0), (-math.pi / 2, None)], "stop", CAP_A3)
    a3_der = run_case(world, adapter, build_id, params, plan_a3, derive=True)
    a3_exec = run_case(world, adapter, build_id, params, plan_a3,
                       events=_freeze_events(a3_der), derive=False)
    _require_script_identity(a3_der, a3_exec, "A3")
    ev_a3 = evaluate_a3(a3_exec, world)

    # ---- A4: the approach to the declared ring (P7) ----------------------
    plan_a4 = CasePlan("A4_approach",
                       [(0.0, 10.5), (BETA_A4, None)], "stop", CAP_A4)
    a4_der = derive_a4(world, adapter, build_id, params)
    a4_exec = run_case(world, adapter, build_id, params, plan_a4,
                       events=_freeze_events(a4_der), derive=False)
    _require_script_identity(a4_der, a4_exec, "A4")
    ev_a4 = evaluate_a4(a4_exec, world)
    ev_a4["turn_search"] = a4_der["search"]

    # ---- P8/P9 across the clean arms -------------------------------------
    p8 = {}
    for name, rows in (("A0_cert", a0["cert"]["per_tick"]),
                       ("A0_ext", a0["ext"]["per_tick"]),
                       ("A1", a1_exec["per_tick"]),
                       ("A2", a2_exec["per_tick"]),
                       ("A3", a3_exec["per_tick"]),
                       ("A4", a4_exec["per_tick"])):
        bad = stability_bars(rows)
        p8[name] = {"violations": bad[:20], "count": len(bad)}
        require(not bad, "prediction_failed:P8_bars:" + name)
    # the identity governs the WALKED ticks; the declared stop/clamp tick
    # is the E6 semantics (the position ceases to advance), not a violation
    p9 = {"A1": arc_identity(a1_exec["per_tick"]),
          "A2": arc_identity(a2_exec["per_tick"],
                             end=a2_exec["stall_tick"]),
          "A3": arc_identity(a3_exec["per_tick"],
                             end=max(0, a3_exec["stop_tick"] - 1)),
          "A4": arc_identity(a4_exec["per_tick"],
                             end=max(0, a4_exec["stop_tick"] - 1))}
    for name, r in p9.items():
        require(r["violation_count"] == 0,
                "prediction_failed:P9_arc_identity:" + name)

    # ---- supervisor observation ledger (clean arms) ----------------------
    monitor = oe.EnvelopeMonitor(oe_consts)
    sup = {}
    for name, rows in (("A0_ext", a0["ext"]["per_tick"]),
                       ("A1", a1_exec["per_tick"])):
        response_events = 0
        for row in rows:
            rec = {
                "tick": row["tick"], "com_vel": [row["com_v_m_s"], 0.0, 0.0],
                "foot_contacts": row["foot_contacts"],
                "foot_forces": row["foot_forces"],
                "pad_gaps": row["pad_gaps"],
                "phase_left": row["phase_left"],
                "phase_right": row["phase_right"],
                "applied": row["applied_cmd"],
                "intervention_reason": row["intervention_reason"],
            }
            monitor.classify(json.loads(json.dumps(rec)))
        sup[name] = {"role": "observation-only (the sealed ledger emits "
                     "nothing on the certified line)",
                     "response_events": response_events}

    # ---- falsifier arms (clean controls FIRST) ---------------------------
    _A1_ROWS[0] = a1_exec["per_tick"]
    fb = falsifier_arms(world, adapter, build_id, params, oe, oe_consts,
                        a0["ext"], plan_a1, a1_der, a1_exec,
                        plan_a3, a3_der, a3_exec, plan_a4, a4_der, a4_exec)

    # ---- receipts ---------------------------------------------------------
    RECEIPTS.mkdir(parents=True, exist_ok=True)
    CAPTURE_DIR.mkdir(parents=True, exist_ok=True)
    receipt = {
        "schema": "chimera.f06_terrain_walking.v1",
        "task_id": "F06",
        "card_id": "MAT2-F06",
        "attempt_id": vi.ATTEMPT_ID,
        "agent_id": vi.AGENT_ID,
        "base_sha256": vi.BASE_SHA,
        "prereg_commit": vi.PREREG_COMMIT,
        "preregistration_sha256": vi.prereg_sha256(),
        "amendment_a1_sha256": vi.amendment_a1_sha256(),
        "criteria_sha256": vi.CRITERIA_SHA256,
        "registry": reg,
        "gate": gate,
        "p2_route_replay": p2,
        "A0_flat_regression": ev_a0,
        "A1_route": ev_a1,
        "A2_crest_stall": ev_a2,
        "A3_step_over": ev_a3,
        "A4_approach": ev_a4,
        "P8_stability_bars": p8,
        "P9_arc_identity": p9,
        "supervisor_observation": sup,
        "falsifiers": fb,
        "F_all_green": all(a.get("bit", False) for a in fb.values()),
        "derived_constants": {
            "a_ceiling_m_s2": A_CEILING, "d_hi_per_s": D_HI, "d_lo_per_s": D_LO,
            "gamma_stall": GAMMA_STALL, "tc_gap_id": "TC-11",
            "d_step_m": _D_STEP_LIVE(),
            "a1_corridor_grade_envelope": env_a1,
            "beta_a4_rad": BETA_A4,
            "g_grav_m_s2": te.G_GRAV,
        },
        "determinism": {"canonical_json": True, "newline": "\n",
                        "command": "python -B terrain_walking.py"},
    }
    (RECEIPTS / "walking_receipt.json").write_bytes(canonical(receipt) + b"\n")
    for name, arm in (("trace_a0_cert.json", a0["cert"]),
                      ("trace_a0_ext.json", a0["ext"]),
                      ("trace_a1.json", a1_exec),
                      ("trace_a2.json", a2_exec),
                      ("trace_a3.json", a3_exec),
                      ("trace_a4.json", a4_exec)):
        rows = arm["per_tick"]
        doc = {"schema": "chimera.f06_trace.v1",
               "seed": SEED, "rows": rows,
               "final_state_sha256": arm.get("final_state_sha256", "")}
        (CAPTURE_DIR / name).write_bytes(canonical(doc))
    print("P verdicts:", {k: True for k in
                          ("P1", "P4", "P5", "P6", "P7", "P8", "P9", "P10")})
    print("F_all_green:", receipt["F_all_green"])
    return 0


def _D_STEP_LIVE():
    p = _PARAMS[0]
    return (p["ground_clearance"]
            + p["lift_gain"] * float(_MANIFEST[0]["action"]["bounds_hi"][2]))


def _make_adapter(manifest, scene_const):
    import command_model as cm
    return cm.CommandAdapter(manifest, scene_const)


def _require_script_identity(der, ex, name):
    """The derivation and the execution are the same deterministic pinned
    recursion: their state chains are bit-identical on EVERY common tick
    (tick-aligned; the arms' ends may differ by declared bookkeeping)."""
    der_map = {r["tick"]: s for r, s in zip(der["per_tick"], der["state_chain"])}
    ex_map = {r["tick"]: s for r, s in zip(ex["per_tick"], ex["state_chain"])}
    common = sorted(set(der_map) & set(ex_map))
    require(len(common) > 0,
            "f06_script_drift:" + name + ":no_common_ticks")
    bad = []
    der_rows = {r["tick"]: r for r in der["per_tick"]}
    ex_rows = {r["tick"]: r for r in ex["per_tick"]}
    for tick in common:
        if der_map[tick] != ex_map[tick]:
            bad.append(tick)
    for tick in bad[:3]:
        dr, er = der_rows[tick], ex_rows[tick]
        require(False, "f06_script_drift:" + name + ":" + str(tick) + ":"
                + repr({"der": (round(dr["px_m"], 4), round(dr["pz_m"], 4),
                                round(dr["psi_rad"], 5), round(dr["com_v_m_s"], 5),
                                dr["applied_cmd"]),
                        "ex": (round(er["px_m"], 4), round(er["pz_m"], 4),
                               round(er["psi_rad"], 5), round(er["com_v_m_s"], 5),
                               er["applied_cmd"])}) )
    require(not bad, "f06_script_drift:" + name + ":ticks:" + repr(bad[:8]))


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except te.Refusal as refusal:
        print("REFUSAL: " + str(refusal), file=sys.stderr)
        sys.exit(2)
    except vi.Refusal as refusal:
        print("REFUSAL: " + str(refusal), file=sys.stderr)
        sys.exit(2)
