#!/usr/bin/env python3
"""MAT2-X04: the presentation harness (prereg section 3).

The certified line is exercised through W10's OWN sealed run_commanded
(imported UNMODIFIED from the byte-verified extraction) — arms A1/A2. The
frame plan, window constants and declared views are the prereg's frozen
numbers. The render consumes the committed per-tick records ONLY (W10's
records-only renderer, imported); the three declared diagnostic layers are
drawn by this card's state_readout module onto diagnostic frames.
"""
from __future__ import annotations

import hashlib
import json

import numpy as np

import state_readout as sr

BUILD_ID = "cpu-walk-scene-build-N"
SEED = 20260920                     # the certified scene seed (continuity)
HORIZON_A1 = 10500                  # W10's declared R1 horizon

# Frozen window (prereg section 3): PW0 = 20 x 213 (the pinned CYCLE_TICKS);
# exactly two gait cycles inside the scripted turn/hold segment.
CYCLE_TICKS = 213                   # pinned scene constant (declared input)
PW0 = 4260
PW1 = 4686                          # consumed ticks [4260, 4686)
V1_CLEAN_TICKS = list(range(4260, 4681, 15))      # 29 frames (motion axis)
V1_DIAG_TICKS = [4275, 4470, 4665]
V2_CLEAN_TICKS = [4470, 4650]
V2_DIAG_TICKS = [4470]
V3_TICK = 4275

# Declared views (registry verbatim names; body-anchored follow offsets;
# clearing frame x,z ground / y up; metres; right-handed Y-up; perspective).
X04_VIEWS = {
    "V1_normal_player_camera": {
        "profile_name": "normal player camera",
        "position": [1.2, 1.6, 3.2], "target": [0.0, 0.5, 0.0],
        "follow": True, "vfov_deg": 50.0, "near_far": [0.05, 50.0]},
    "V2_detail_display_asset": {
        "profile_name": "detail of affected display/asset",
        "position": [0.35, 0.7, 0.9], "target": [0.0, 0.5, 0.0],
        "follow": True, "vfov_deg": 45.0, "near_far": [0.01, 10.0]},
    "V3_alternate_angle": {
        "profile_name": "alternate-angle visibility",
        "position": [0.0, 1.2, 4.0], "target": [0.0, 0.5, 0.0],
        "follow": True, "vfov_deg": 40.0, "near_far": [0.05, 50.0]},
}
VIEW_ORDER = ["V1_normal_player_camera", "V2_detail_display_asset",
              "V3_alternate_angle"]
CLEAN_VIEW = "V1_normal_player_camera"

# The declared tamper delta for FB2/P4(c) (prereg sections 4-5).
TAMPER_PHASE_DELTA = 0.25
# Placeholder constants (FB1's declared fake state source).
PLACEHOLDER = {"contact": 1, "force_n": 0.25, "link": "L5/5 R5/5",
               "climb": "absent_declared", "mode": "WALK"}


def require(condition, code):
    if not condition:
        raise RuntimeError("REFUSAL:" + str(code))


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def load_w10_modules():
    """Import the W10 sealed line modules from THIS card's byte-verified
    extraction (import identity; never copies)."""
    import verify_inputs_x04 as vi4
    wd = vi4.load_pinned_module(
        "x04_walking_demo",
        ("tools", "monkey_campaign", "contributions", "MAT2-W10",
         "walking_demo.py"))
    vz = vi4.load_pinned_module(
        "x04_visualization",
        ("tools", "monkey_campaign", "contributions", "MAT2-W10",
         "visualization.py"))
    return wd, vz


def scene_source_bytes():
    """The pinned scene module bytes (the schema audit's input).

    The scene is a W10 CERTIFIED-LINE pin (W10's own pin table, group
    "lane", sha-verified inside w10_layer()): the bytes are read from the
    W10 layer's byte-verified extraction root. Order is law: the layer must
    have run first (stage_pins / setUpModule / every stage's vi4 preamble);
    reading from this card's own extraction would be a DIFFERENT byte
    source than the one the W10 pin table verified."""
    import sys
    wvi = sys.modules.get("w10_verify_inputs")
    if wvi is None:
        import verify_inputs_x04 as vi4
        wvi = vi4.load_pinned_module(
            "w10_verify_inputs",
            ("tools", "monkey_campaign", "contributions", "MAT2-W10",
             "verify_inputs.py"))
    path = wvi.PINNED_ROOT / "tools" / "policy_compat" / "scene_cpu.py"
    require(path.exists(),
            "input_pin_missing:scene_cpu_w10_extraction_not_extracted")
    return path.read_bytes()


def run_arms(adapter, build_id, params):
    """A1 WALK + A2 REPEAT: W10's own sealed run_commanded (the frozen
    script, the pinned seam, the no-teleport sink)."""
    wd, _vz = load_w10_modules()
    res1 = wd.run_commanded(adapter, build_id, params, horizon=HORIZON_A1)
    res2 = wd.run_commanded(adapter, build_id, params, horizon=HORIZON_A1)
    return res1, res2


def row_index(rows):
    return {int(r["tick"]): r for r in rows}


def transition_coverage(rows):
    """The window's committed rows' contact transitions (P2's precondition;
    counted, never assumed)."""
    by_tick = row_index(rows)
    left, right = [], []
    for t in range(PW0, PW1):
        a, b = by_tick.get(t - 1), by_tick.get(t)
        if a is None or b is None:
            continue
        if int(a["foot_contacts"][4]) != int(b["foot_contacts"][4]):
            left.append({"tick": t,
                         "from": int(a["foot_contacts"][4]),
                         "to": int(b["foot_contacts"][4])})
        if int(a["foot_contacts"][5]) != int(b["foot_contacts"][5]):
            right.append({"tick": t,
                          "from": int(a["foot_contacts"][5]),
                          "to": int(b["foot_contacts"][5])})
    return {"left": left, "right": right,
            "left_count": len(left), "right_count": len(right)}


def build_frame_plan():
    """The declared render plan (prereg section 3; deterministic order)."""
    plan = []
    idx = 0

    def add(view, tick, diagnostic, frame_id):
        nonlocal idx
        plan.append({"frame_id": frame_id, "view": view, "tick": tick,
                     "diagnostic": diagnostic, "render_index": idx})
        idx += 1

    for k, tick in enumerate(V1_CLEAN_TICKS):
        add(CLEAN_VIEW, tick, False, "P%02d_V1_clean_t%d" % (k, tick))
    for tick in V1_DIAG_TICKS:
        add("V1_normal_player_camera", tick, True, "D_V1_t%d" % tick)
    for tick in V2_CLEAN_TICKS:
        add("V2_detail_display_asset", tick, False, "C_V2_clean_t%d" % tick)
    for tick in V2_DIAG_TICKS:
        add("V2_detail_display_asset", tick, True, "D_V2_t%d" % tick)
    add("V3_alternate_angle", V3_TICK, False, "S_pass1_t%d" % V3_TICK)
    add("V3_alternate_angle", V3_TICK, False, "S_pass2_t%d" % V3_TICK)
    add("V3_alternate_angle", V3_TICK, True, "S_pass1_diag_t%d" % V3_TICK)
    add("V3_alternate_angle", V3_TICK, True, "S_pass2_diag_t%d" % V3_TICK)
    return plan


def render_frames(rows, geom, viz, f04, plan, climb_audit, with_layers=True):
    """Render the declared plan from committed records ONLY; diagnostic
    frames carry the three declared layers; every frame's label receipt,
    render-time joints and pose identifier are recorded.

    Returns (colours, metas). The state chain was recorded BEFORE any
    render call (the caller asserts equality across this stage)."""
    by_tick = row_index(rows)

    def row_at(tick):
        r = by_tick.get(int(tick))
        require(r is not None, "render_tick_missing:" + str(tick))
        return r

    colours, metas = [], []
    for spec in plan:
        view = X04_VIEWS[spec["view"]]
        row = row_at(spec["tick"])
        prev = by_tick.get(int(spec["tick"]) - 1)
        state = sr.derive_state(row, prev, climb_audit, viz, geom)
        pose = state["pose"]
        colour, drawn, cam = viz.render_frame(
            f04, view, pose, spec["diagnostic"], spec["tick"],
            "t%d v=%.3f %s" % (spec["tick"], row["com_v_m_s"],
                               spec["view"]))
        label_receipt = None
        if spec["diagnostic"] and with_layers:
            label_receipt = sr.draw_layers(colour, state)
        joints = {side: {site: [float(p[0]), float(p[1])]
                         for site, p in chain.items()}
                  for side, chain in pose["legs"].items()}
        pose_id = sha_bytes(canonical(
            {"tick": state["tick"], "legs": joints}))
        colours.append(colour)
        metas.append({"frame_id": spec["frame_id"], "view": spec["view"],
                      "tick": spec["tick"],
                      "diagnostic": spec["diagnostic"],
                      "render_index": spec["render_index"],
                      "triangles_drawn": int(drawn),
                      "state_sha256": row["state_sha256"],
                      "anchor_xy": [row["com_x_m"], 0.0],
                      "label_receipt": label_receipt,
                      "render_joints": joints,
                      "pose_id": pose_id,
                      "state": {k: state[k] for k in
                                ("tick", "link", "contact_l", "contact_r",
                                 "force_l_n", "force_r_n", "climb_state",
                                 "mode", "event", "com_v_m_s")}})
    return colours, metas


def pose_hash_series(metas, view):
    """P12: the distinct pose identifiers across a view's clean frames."""
    return [m["pose_id"] for m in metas if m["view"] == view
            and not m["diagnostic"]]


def tamper_row(row, delta):
    """A DECLARED tampered copy (P4c/FB2's probe source): the row's gait
    phase shifted by the frozen delta; nothing else changes."""
    t = dict(row)
    t["phase_left"] = (float(row["phase_left"]) + delta) % 1.0
    return t
