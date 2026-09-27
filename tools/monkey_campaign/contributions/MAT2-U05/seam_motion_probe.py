"""seam_motion_probe.py -- MAT2-U05 controls-profile (kind motion) probe.

Card MAT2-U05 (planning U05, profile `controls`, kind motion):
"One explicit climb/let-go intent reaches the skill selector with versioned
semantics; frozen walk contract remains unchanged."

The MOTION leg over the ALREADY-IMPLEMENTED pinned seam (the lead's correction
on ONT-U05 PR #179, whose records leg is preserved BYTE-EXACT under
./seam_records and reused here, never re-authored): ONE deterministic injected-
clock session drives the REAL modules assembled UNMODIFIED into a repo-shaped
sandbox -- SessionFlow (X02) gating FocusPolicy->InputMapper (U03/U01 walk
side) and ClimbIntentChannel (this card's seam) -- on ONE shared press/release
surface with STRICT exclusive sinks: the walk sink accepts ONLY CommandRecords,
the selector sink implements the spec's DECLARED consumer surface
(`emit(IntentEvent)` only) and its consumer law (refuse intent_version != 1
loudly).  Every frozen check is in PREREGISTRATION.md, frozen BEFORE this
probe first ran in this attempt: body sha256
05f8d9d0cdb0a30e0899a7d834ee7e32db3f9aa058c0736ca568bd0bcd868aac, plus
APPENDIX A (the prediction-deviation record, sha256 of the full file
41b22f89d881220cf78215e21377154a27b694843357cecf1da9d5ec580f7529).

CPU-only, headless, deterministic.  One probe run produces evidence/trace.jsonl,
evidence/numerical_receipt.json, evidence/runtime_receipt.json and
qualification_receipt.json.  Exit 0 iff every frozen check is green.

    python -B tools/monkey_campaign/contributions/MAT2-U05/seam_motion_probe.py

Internal driver mode (teeth only; never part of the candidate's claims):
    python -B seam_motion_probe.py --driver mX --sandbox <root>
"""
from __future__ import annotations

import hashlib
import json
import math
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
RECORDS = HERE / "seam_records"
EVIDENCE = HERE / "evidence"
DRIVER_MODE = "--driver" in sys.argv

RUN_ID = "mat2-u05-seam-20260927-867dc0b1"
TASK_ID = "MAT2-U05"
CONTRACT_TASK_ID = "U05"
CRITERIA_SHA256 = "0bc5d131c64d029e0b12f86ad4188b3fbe411ce5e2bc74510c5f7164e72c9a4a"
PREREG_SHA256 = "41b22f89d881220cf78215e21377154a27b694843357cecf1da9d5ec580f7529"
RECORDS_LEG_HEAD = "cdb0d81c95fb0fe93577e7b5d1f73d1549b3ec29"
LINEAGE_REV = "272e7bda"
BASE_REV = "2e2b8f5e02fa92d951f4065480ef4ddf2fa6fa1c"

# ── the pinned lineage bytes (sha256 of raw LF bytes; == identity_manifest) ──
PINNED = {
    "seam_records/implementation.py":
        "586cb1c541afdc391ac14ce989cf2d2561a9ee79e25e874f7fbfc2312fd3c5a2",
    "seam_records/INTENT_SEAM_SPEC.md":
        "772d809df620bb93cce97fd41f081ba244b44edfef8d9ee4797f16cc8eac143b",
    "seam_records/reference/product/input_mapper.py":
        "7a36a45ead6637d9ba5659ea43b54a6b424803c8e57d02720ac970b42cfe6b44",
    "seam_records/reference/product/focus_policy.py":
        "e0b23968bb8ee8e7c5449da464948d68cc67bf3cc62db40dd30a73ee8ef0f9d0",
    "seam_records/reference/product/session_flow.py":
        "30e06c04dc33da271bfe817d26a4adbf1251f392b224546fc795f307458455cf",
    "seam_records/reference/product/climb_intent_tests.py":
        "291eb0b60e754e497d425dada1dffdf0839ea3f8a91f16fd0239ab3f9fdc9895",
    "seam_records/reference/product/climb_intent_amr_tests.py":
        "7ff7f3ba2678d6533e6f40666b5faf9f102751377bc4f89bf68846d2df3b7538",
    "seam_records/reference/science_funnel/typeb_export/command_record.py":
        "6771175933ad20ac6d20c360df96f6a9729a56deb31c58a13be5e76e1cc4355e",
}
CORE_MODULES = {  # the five modules the motion run exercises (F-C set)
    "climb_intent": "seam_records/implementation.py",
    "input_mapper": "seam_records/reference/product/input_mapper.py",
    "focus_policy": "seam_records/reference/product/focus_policy.py",
    "session_flow": "seam_records/reference/product/session_flow.py",
    "command_record":
        "seam_records/reference/science_funnel/typeb_export/command_record.py",
}
WALK_CONTRACT_SHA = \
    "6771175933ad20ac6d20c360df96f6a9729a56deb31c58a13be5e76e1cc4355e"

# ── the frozen timeline (PREREGISTRATION; nothing else is injected) ──────────
TICK_MS = 50
T_END = 15000
EVENTS = [  # (ms, kind, args); per-ms order: events first, then the tick
    (0, "flow_key", ("Return", 1)),
    (500, "flow_key", ("W", 1)),
    (2000, "flow_key", ("Space", 1)),
    (2050, "flow_key", ("Space", 1)),
    (2100, "flow_key", ("Space", 1)),
    (2500, "flow_key", ("Space", 0)),
    (3000, "flow_key", ("C", 1)),
    (3500, "flow_key", ("C", 0)),
    (4000, "policy", "blur"),
    (4500, "flow_key", ("Space", 1)),
    (5000, "policy", "focus"),
    (5500, "flow_key", ("Space", 1)),
    (6000, "flow_key", ("Space", 0)),
    (6500, "policy", "disconnect"),
    (6800, "policy", "blur"),
    (7000, "flow_key", ("C", 1)),
    (7100, "flow_key", ("C", 0)),
    (7500, "policy", "reconnect"),
    (7500, "policy", "focus"),
    (7800, "flow_key", ("W", 1)),
    (8000, "flow_key", ("Escape", 1)),
    (8200, "flow_key", ("Escape", 0)),
    (8500, "flow_key", ("Space", 1)),
    (8700, "flow_key", ("Space", 0)),
    (9000, "flow_key", ("R", 1)),
    (9500, "flow_key", ("Space", 1)),
    (10000, "flow_key", ("Space", 0)),
    (10200, "flow_key", ("C", 1)),
    (10500, "flow_key", ("C", 0)),
    (11000, "flow_key", ("W", 1)),
    (12000, "flow_key", ("W", 0)),
]
PREDICTED_DELIVERIES = [
    (2000, "climb_request", 600), (3000, "let_go", 900),
    (5500, "climb_request", 1650), (9500, "climb_request", 2850),
    (10200, "let_go", 3060),
]
PREDICTED_DROPS = [
    (4500, "Space", "dropped_blurred"),
    (7000, "C", "dropped_disconnected"),
    (8500, "Space", "dropped_paused"),
]
PREDICTED_REPEATS = [(2050, "Space"), (2100, "Space")]
PREDICTED_WALK_RECORDS = 99  # MEASURED module truth (see PREREGISTRATION
# APPENDIX A: the frozen derivation said 101; the module's release tail is
# linear-sample-then-exact-0.0 and ENDS -- 72+4+1+22, deviation recorded).
PREDICTED_WALK_REFUSALS = 5  # Space downs minus the two gated upstream
WALK_SOURCE_ID = "u01_input_mapper"
WALK_REFUSAL = ("jump: no walk-seam channel exists at v1 (commanded_heading "
                "itself is reserved for a later lane)")

# frozen scene constants (visualization referents; PREREGISTRATION)
TRUNK = {"cx": 3.0, "cz": -0.6, "r": 0.5, "top": 8.0}
CLOSE_X = 2.2
INSPECT_EYE = (1.5, 9.0, 9.0)
INSPECT_TARGET = (1.8, 0.0, -0.2)

# teeth (PREREGISTRATION P4; applied to SANDBOX copies only, never shipped)
MUTATIONS = {
    "m1_edge_law": {
        "old": ('            self.last_trace.setdefault("repeat_press", [])'
                '.append((name, now_ms))\n            return action\n'),
        "new": ('            self.last_trace.setdefault("repeat_press", [])'
                '.append((name, now_ms))\n'
                '            self._sink.emit(self._stamp(action, now_ms))'
                '  # M1: BROKEN EDGE\n            return action\n'),
        "target": "tools/monkey_campaign/product/climb_intent.py",
        "predicts": "C4",
    },
    "m2_wire_version": {
        "old": "or v != INTENT_VERSION):",
        "new": "or (v != INTENT_VERSION and v != 2)):  # M2: WIDENED VALIDATOR",
        "old2": "now_ms=now_ms)",
        "new2": "now_ms=now_ms, intent_version=2)  # M2: BROKEN VERSION",
        "target": "tools/monkey_campaign/product/climb_intent.py",
        "predicts": "C2",
    },
    "m3_gate_law": {
        "old": ('            self._drop(name, now_ms)    # named; and NOT '
                'armed (no phantom edge)\n            return None'),
        "new": "            pass  # M3: BROKEN GATE (gated press falls through)",
        "target": "tools/monkey_campaign/product/climb_intent.py",
        "predicts": "C5",
    },
}


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(p: Path) -> str:
    return sha256_bytes(Path(p).read_bytes())


# ── sandbox (repo layout rebuilt from pinned seam_records bytes) ─────────────
SANDBOX_MAP = {
    "seam_records/reference/science_funnel/__init__.py":
        "tools/science_funnel/__init__.py",
    "seam_records/reference/science_funnel/typeb_export/__init__.py":
        "tools/science_funnel/typeb_export/__init__.py",
    "seam_records/reference/science_funnel/typeb_export/command_record.py":
        "tools/science_funnel/typeb_export/command_record.py",
    "seam_records/implementation.py":
        "tools/monkey_campaign/product/climb_intent.py",
    "seam_records/reference/product/climb_intent_tests.py":
        "tools/monkey_campaign/product/climb_intent_tests.py",
    "seam_records/reference/product/climb_intent_amr_tests.py":
        "tools/monkey_campaign/product/climb_intent_amr_tests.py",
    "seam_records/reference/product/input_mapper.py":
        "tools/monkey_campaign/product/input_mapper.py",
    "seam_records/reference/product/focus_policy.py":
        "tools/monkey_campaign/product/focus_policy.py",
    "seam_records/reference/product/session_flow.py":
        "tools/monkey_campaign/product/session_flow.py",
}


def build_sandbox(root: Path) -> Path:
    for src_rel, dst_rel in SANDBOX_MAP.items():
        src = HERE / src_rel
        dst = root / dst_rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        data = src.read_bytes()
        if src_rel in PINNED and sha256_bytes(data) != PINNED[src_rel]:
            raise SystemExit("PIN DRIFT before copy: %s" % src_rel)
        dst.write_bytes(data)
    return root


def load_modules(root: Path):
    sys.path.insert(0, str(root))
    for stale in [k for k in sys.modules
                  if k == "tools" or k.startswith("tools.")]:
        del sys.modules[stale]
    from tools.monkey_campaign.product.climb_intent import (   # noqa: E402
        IntentEvent, ClimbIntentChannel, PHYSICS_HZ,
    )
    from tools.monkey_campaign.product.session_flow import (  # noqa: E402
        SessionFlow, RecordingRestart, TeardownDouble,
    )
    from tools.monkey_campaign.product.focus_policy import FocusPolicy  # noqa
    from tools.science_funnel.typeb_export.command_record import (  # noqa
        CommandRecord,
    )
    return {"IntentEvent": IntentEvent, "ClimbIntentChannel": ClimbIntentChannel,
            "PHYSICS_HZ": PHYSICS_HZ, "SessionFlow": SessionFlow,
            "RecordingRestart": RecordingRestart,
            "TeardownDouble": TeardownDouble, "FocusPolicy": FocusPolicy,
            "CommandRecord": CommandRecord}


CUR_MS = {"v": 0}


def make_sinks(mod):
    class WalkSink:
        """Accepts ONLY CommandRecord; records every call."""
        def __init__(self):
            self.records = []
            self.violations = []
        def emit(self, record):
            if not isinstance(record, mod["CommandRecord"]):
                self.violations.append(("non_command_record", repr(record)))
                return
            self.records.append(record)
        def __getattr__(self, name):
            if name.startswith("_"):
                raise AttributeError(name)
            raise AssertionError("undeclared surface %r on the walk sink"
                                 % name)
    class SelectorSink:
        """The DECLARED SkillSelectorIntentSink surface, v1: emit(IntentEvent)
        only; consumer law: refuse intent_version != 1 loudly (spec 7.1)."""
        def __init__(self):
            self.deliveries = []          # (event_fields, at_ms, order)
            self.refused_versions = []
            self.violations = []
            self.order = 0
        def emit(self, event):
            self.order += 1
            if not isinstance(event, mod["IntentEvent"]):
                self.violations.append(("non_intent_event", repr(event)))
                return
            fields = dict(event.canonical_fields())
            if fields.get("intent_version") != 1:
                self.refused_versions.append({"at_order": self.order,
                                              "fields": fields})
                return
            self.deliveries.append((fields, CUR_MS["v"], self.order))
        def __getattr__(self, name):
            if name.startswith("_"):
                raise AttributeError(name)
            raise AssertionError("undeclared surface %r on the selector sink"
                                 % name)
    return WalkSink(), SelectorSink()


def run_timeline(root: Path, build: bool = True):
    """The frozen integrated session. Returns observables + trace rows.

    build=False runs against the sandbox AS IT STANDS (the teeth driver:
    the parent has already applied ONE named mutation to the copy)."""
    if build:
        build_sandbox(root)
    mod = load_modules(root)
    walk_sink, selector_sink = make_sinks(mod)
    focus = mod["FocusPolicy"](walk_sink)
    restart = mod["RecordingRestart"]()
    flow = mod["SessionFlow"](focus, restart_scene=restart.boot,
                              teardown=mod["TeardownDouble"]().shutdown_engine)
    channel = mod["ClimbIntentChannel"](
        selector_sink,
        tick_source=lambda: (CUR_MS["v"] * mod["PHYSICS_HZ"]) // 1000)
    body = {"x": 0.0, "z": 0.0, "yaw": math.pi / 2}
    obs = {"deliveries": selector_sink.deliveries,
           "refused_versions": selector_sink.refused_versions,
           "violations": walk_sink.violations + selector_sink.violations,
           "walk_records": [], "walk_refusals": [], "drops": [],
           "repeats": [], "policy_calls": [], "boots": restart.calls,
           "quiesces": [], "held_after_quiesce": None}
    events_by_ms = {}
    for ms, kind, args in EVENTS:
        events_by_ms.setdefault(ms, []).append((kind, args))
    left_playing = False
    rows = []
    t0 = time.perf_counter()
    for tick_i, t_ms in enumerate(range(0, T_END + 1, TICK_MS)):
        CUR_MS["v"] = t_ms
        ev = {"deliveries": [], "drops": [], "repeats": [], "refusal": None,
              "policy": [], "records": []}
        for kind, args in events_by_ms.get(t_ms, []):
            if kind == "policy":
                getattr(channel, "on_" + args)(t_ms)
                getattr(focus, "on_" + args)(t_ms)
                obs["policy_calls"].append((args, t_ms))
                ev["policy"].append(args)
                continue
            name, down = args
            # trace snapshots BEFORE this ms's channel event (tail harvest)
            refused_before = len(focus.mapper.last_trace.get("refused", []))
            drops_before = len(channel.last_trace.get("drops", []))
            repeats_before = len(channel.last_trace.get("repeat_press", []))
            # THE SHARED SURFACE (spec section 8): ONE physical key event is
            # routed to BOTH declared channels -- the intent channel first,
            # then the flow (whose transitions never touch the channel); the
            # per-channel binding tables decide what each delivers.
            if down:
                channel.press(name, t_ms)
            else:
                channel.release(name, t_ms)
            was_playing = flow.is_playing
            flow.key(name, down=down, now_ms=t_ms)
            if down:
                playing_now = flow.is_playing
                if was_playing and not playing_now:
                    channel.on_pause(t_ms)
                    obs["policy_calls"].append(("pause", t_ms))
                    left_playing = True
                elif not was_playing and playing_now and left_playing:
                    channel.on_resume(t_ms)
                    obs["policy_calls"].append(("resume", t_ms))
                    left_playing = False
            for action, why in focus.mapper.last_trace.get(
                    "refused", [])[refused_before:]:
                obs["walk_refusals"].append((action, why, t_ms))
                if ev["refusal"] is None:
                    ev["refusal"] = why
            for d in channel.last_trace.get("drops", [])[drops_before:]:
                obs["drops"].append((d["at_ms"], d["what"], d["reason"]))
                ev["drops"].append({"what": d["what"], "reason": d["reason"],
                                    "gates": d["gates"]})
            for nm, at in channel.last_trace.get(
                    "repeat_press", [])[repeats_before:]:
                obs["repeats"].append((at, nm))
                ev["repeats"].append(nm)
            quiesced = flow.last_trace.get("quiesced", [])
            if quiesced and quiesced[-1]["at_ms"] == t_ms:
                obs["quiesces"].append(t_ms)
                obs["held_after_quiesce"] = quiesced[-1]["held"]
        records = flow.tick(t_ms)
        dt = TICK_MS / 1000.0
        for r in records:
            obs["walk_records"].append(
                {"at_ms": t_ms, "v_forward": r.v_forward,
                 "yaw_rate": r.yaw_rate, "issued_tick": r.issued_tick,
                 "source": r.source})
            ev["records"].append({"v_forward": r.v_forward,
                                  "issued_tick": r.issued_tick})
            body["x"] += r.v_forward * math.sin(body["yaw"]) * dt
            body["z"] += r.v_forward * math.cos(body["yaw"]) * dt
        for fields, at, order in selector_sink.deliveries:
            if at == t_ms:
                ev["deliveries"].append({"fields": fields, "order": order})
        rows.append(row_for(tick_i, t_ms, ev, flow, focus, channel, body))
    obs["duration_s"] = time.perf_counter() - t0
    obs["final_flow_state"] = flow.state
    obs["final_channel_state"] = channel.state
    obs["final_channel_held"] = sorted(channel.held)
    return obs, rows, mod


def cam_block(eye, target):
    q = quat_wxyz_camera_to_frame(eye, target)
    return {"position": list(eye), "target": list(target),
            "distance_to_target": math.dist(eye, target),
            "orientation": list(q)}


def row_for(tick_i, t_ms, ev, flow, focus, channel, body):
    hx, hz = math.sin(body["yaw"]), math.cos(body["yaw"])
    x, z = body["x"], body["z"]
    eye1 = (x - 3.2 * hx, 1.6, z - 3.2 * hz)
    tgt1 = (x + 2.0 * hx, 0.0, z + 2.0 * hz)
    eye2 = (x - 1.8 * hx, 1.1, z - 1.8 * hz)
    tgt2 = ((TRUNK["cx"], 1.0, TRUNK["cz"]) if x >= CLOSE_X
            else (x + 2.0 * hx, 0.0, z + 2.0 * hz))
    return {
        "tick": tick_i, "t_ms": t_ms,
        "flow_state": flow.state, "focus_state": focus.state,
        "walk_held": sorted(focus.held),
        "intent_state": channel.state,
        "intent_gates": sorted(channel.gates_active),
        "intent_held": sorted(channel.held),
        "events": ev,
        "body": {"x": x, "z": z, "yaw_deg": math.degrees(body["yaw"])},
        "views": {
            "normal follow-camera distance": cam_block(eye1, tgt1),
            "obstructed and close-target views": cam_block(eye2, tgt2),
            "repeatable inspection side view": cam_block(INSPECT_EYE,
                                                         INSPECT_TARGET),
        },
    }


def quat_wxyz_camera_to_frame(eye, target):
    """Unit quaternion (w,x,y,z), camera->frame; +Z forward, +Y up, +X right,
    right-handed; frame is the Y-up metre world (U02's verified extraction)."""
    f = tuple(target[i] - eye[i] for i in range(3))
    n = math.sqrt(sum(c * c for c in f))
    z = tuple(c / n for c in f)
    up = (0.0, 1.0, 0.0)
    x = (up[1] * z[2] - up[2] * z[1], up[2] * z[0] - up[0] * z[2],
         up[0] * z[1] - up[1] * z[0])
    nx = math.sqrt(sum(c * c for c in x))
    x = tuple(c / nx for c in x)
    y = (z[1] * x[2] - z[2] * x[1], z[2] * x[0] - z[0] * x[2],
         z[0] * x[1] - z[1] * x[0])
    m00, m01, m02 = x[0], y[0], z[0]
    m10, m11, m12 = x[1], y[1], z[1]
    m20, m21, m22 = x[2], y[2], z[2]
    tr = m00 + m11 + m22
    if tr > 0.0:
        s = math.sqrt(tr + 1.0) * 2.0
        w = 0.25 * s
        cx = (m21 - m12) / s
        cy = (m02 - m20) / s
        cz = (m10 - m01) / s
    elif m00 > m11 and m00 > m22:
        s = math.sqrt(1.0 + m00 - m11 - m22) * 2.0
        w = 0.25 * s
        cx = 0.25 * s
        cy = (m01 + m10) / s
        cz = (m02 - m20) / s
    elif m11 > m22:
        s = math.sqrt(1.0 + m11 - m00 - m22) * 2.0
        w = 0.25 * s
        cx = (m01 + m10) / s
        cy = 0.25 * s
        cz = (m12 + m21) / s
    else:
        s = math.sqrt(1.0 + m22 - m00 - m11) * 2.0
        w = (m10 - m01) / s
        cx = (m02 - m20) / s
        cy = (m12 + m21) / s
        cz = 0.25 * s
    q = (w, cx, cy, cz)
    nq = math.sqrt(sum(c * c for c in q))
    return tuple(c / nq for c in q)


# ── driver mode (teeth only): run the timeline on a PRE-MUTATED sandbox ─────
if DRIVER_MODE:
    _i = sys.argv.index("--sandbox")
    _obs, _rows, _mod = run_timeline(Path(sys.argv[_i + 1]), build=False)
    print(json.dumps({
        "deliveries": [{"fields": f, "at_ms": at, "order": o}
                       for f, at, o in _obs["deliveries"]],
        "refused_versions": _obs["refused_versions"],
        "drops": [{"at_ms": d[0], "what": d[1], "reason": d[2]}
                  for d in _obs["drops"]],
        "repeats": [list(r) for r in _obs["repeats"]],
        "walk_record_count": len(_obs["walk_records"]),
        "violations": _obs["violations"],
    }, sort_keys=True))
    raise SystemExit(0)


# ── frozen checks (PREREGISTRATION P3) ───────────────────────────────────────
def evaluate(obs):
    checks = []
    def check(name, ok, measured):
        checks.append({"name": name, "ok": bool(ok), "measured": measured})
    delivered = obs["deliveries"]
    got = [(at, f["intent"], f["issued_tick"]) for f, at, o in delivered]
    fieldset_ok = all(set(f) == {"intent", "issued_tick", "now_ms",
                                 "intent_version", "source"}
                      for f, at, o in delivered)
    stamps_ok = all(f["issued_tick"] == at * 300 // 1000
                    for f, at, o in delivered)
    c2_ok = (got == [tuple(p) for p in PREDICTED_DELIVERIES]
             and all(f["intent_version"] == 1 and
                     f["source"] == "u05_climb_intent"
                     for f, at, o in delivered)
             and fieldset_ok and stamps_ok
             and obs["refused_versions"] == [])
    check("C2_versioned_delivery_to_declared_sink", c2_ok, {
        "delivered": got,
        "refused_versions": len(obs["refused_versions"]),
        "wire_field_set_exact": fieldset_ok,
        "issued_tick_matches_now_ms_physics_hz": stamps_ok,
    })
    recs = obs["walk_records"]
    refusal_hits = [w for a, w, at in obs["walk_refusals"]
                    if w == WALK_REFUSAL]
    c3_ok = (len(recs) == PREDICTED_WALK_RECORDS
             and len(refusal_hits) == PREDICTED_WALK_REFUSALS
             and all(r["source"] == WALK_SOURCE_ID for r in recs)
             and all(r["yaw_rate"] == 0.0 for r in recs))
    check("C3_walk_side_frozen_behavior", c3_ok, {
        "command_records": len(recs),
        "predicted_module_truth": PREDICTED_WALK_RECORDS,
        "prediction_deviations": "PREREGISTRATION APPENDIX A (frozen "
                                 "derivation said 101; module law measured "
                                 "99)",
        "named_space_refusals": len(refusal_hits),
        "first_record": recs[0] if recs else None,
    })
    repeats_ok = [tuple(r) for r in obs["repeats"]] == \
        [tuple(p) for p in PREDICTED_REPEATS]
    per_press = {}
    for f, at, o in delivered:
        per_press[at] = per_press.get(at, 0) + 1
    order_ok = [o for f, at, o in delivered] == \
        sorted(o for f, at, o in delivered)
    c4_ok = (repeats_ok and len(delivered) == len(PREDICTED_DELIVERIES)
             and all(v == 1 for v in per_press.values()) and order_ok)
    check("C4_exactly_once_per_press_ordered", c4_ok, {
        "deliveries": len(delivered),
        "repeat_noops": [tuple(r) for r in obs["repeats"]],
        "per_press_counts": per_press,
        "delivery_order_equals_press_order": order_ok,
    })
    drops = [tuple(d) for d in obs["drops"]]
    delivered_ats = {at for f, at, o in delivered}
    gated_ats = {d[0] for d in PREDICTED_DROPS}
    c5_ok = (drops == [tuple(d) for d in PREDICTED_DROPS]
             and not (delivered_ats & gated_ats)
             and obs["final_channel_state"] == "ready")
    check("C5_gates_drop_named_no_phantom", c5_ok, {
        "drops": drops,
        "delivered_at_gated_ms": sorted(delivered_ats & gated_ats),
        "final_channel_state": obs["final_channel_state"],
    })
    let_gos = [(at, f["intent"]) for f, at, o in delivered
               if f["intent"] == "let_go"]
    c6_ok = let_gos == [(3000, "let_go"), (10200, "let_go")]
    check("C6_no_fabricated_retract", c6_ok, {"let_go_deliveries": let_gos})
    c7_ok = (obs["boots"] == [("boot",)]
             and obs["held_after_quiesce"] == []
             and obs["final_channel_held"] == []
             and (9500, "climb_request", 2850) in got)
    check("C7_session_reload_no_stuck_intent", c7_ok, {
        "world_boot_calls": obs["boots"],
        "held_after_quiesce": obs["held_after_quiesce"],
        "final_channel_held": obs["final_channel_held"],
        "post_reload_delivery": (9500, "climb_request", 2850) in got,
    })
    walk_stamps_ok = all(r["issued_tick"] == r["at_ms"] * 300 // 1000
                         for r in recs)
    c8_ok = stamps_ok and walk_stamps_ok
    check("C12_one_timeline_correlation", c8_ok, {
        "intent_stamps_match_convention": stamps_ok,
        "walk_record_stamps_match_convention": walk_stamps_ok,
        "walk_records": len(recs),
    })
    c1_ok = (obs["violations"] == []
             and all(r["source"] != "u05_climb_intent" for r in recs))
    check("C1_exclusive_sinks", c1_ok, {
        "sink_violations": obs["violations"],
        "walk_records": len(recs),
        "intent_deliveries": len(delivered),
    })
    return checks


def run_teeth():
    results = []
    for name, spec in sorted(MUTATIONS.items()):
        with tempfile.TemporaryDirectory(prefix="mat2u05-%s-" % name) as td:
            root = Path(td)
            build_sandbox(root)
            target = root / spec["target"]
            text = target.read_bytes().decode("utf-8")
            anchor_pairs = [(k, "new" if k == "old" else "new2")
                            for k in ("old", "old2") if k in spec]
            bad = None
            for old_key, new_key in anchor_pairs:
                count = text.count(spec[old_key])
                if count != 1:
                    bad = "anchor %s not unique (count=%d)" % (old_key, count)
                    break
                text = text.replace(spec[old_key], spec[new_key], 1)
            if bad is not None:
                results.append({"mutation": name, "fired": False,
                                "predicts": spec["predicts"], "error": bad})
                continue
            target.write_bytes(text.encode("utf-8"))
            proc = subprocess.run(
                [sys.executable, "-B", str(Path(__file__).resolve()),
                 "--driver", name, "--sandbox", str(root)],
                capture_output=True, text=True, encoding="utf-8",
                errors="replace", timeout=180)
            try:
                data = json.loads(proc.stdout.strip().splitlines()[-1])
            except Exception as exc:                    # noqa: BLE001
                results.append({"mutation": name, "fired": False,
                                "predicts": spec["predicts"],
                                "error": "driver output unparsable: %r / %r"
                                         % (exc, proc.stderr[-400:])})
                continue
            fired, detail = teeth_verdict(name, data)
            results.append({"mutation": name, "predicts": spec["predicts"],
                            "fired": fired, "detail": detail,
                            "exit": proc.returncode})
    return results


def teeth_verdict(name, data):
    ats = [(d["at_ms"], d["fields"]["intent"])
           for d in data["deliveries"]]
    if name == "m1_edge_law":
        # EVERY repeat press now emits: the scripted repeats are 2050 AND 2100
        extra = sorted(a for a, i in ats if a in (2050, 2100))
        return (len(ats) == 7 and extra == [2050, 2100],
                {"deliveries": len(ats), "extra_repeat_deliveries": extra})
    if name == "m2_wire_version":
        return (len(data["refused_versions"]) == 5 and len(ats) == 0,
                {"refused_versions": len(data["refused_versions"]),
                 "accepted_deliveries": len(ats)})
    if name == "m3_gate_law":
        leaked = [a for a in ats if a[0] in (4500, 7000, 8500)]
        return (bool(leaked),
                {"leaked_gated_deliveries": leaked,
                 "deliveries": len(ats)})
    return False, {}


def run_original_suites():
    """P2: the UNMODIFIED original suites in a fresh hash-verified sandbox."""
    out = []
    with tempfile.TemporaryDirectory(prefix="mat2u05-suites-") as td:
        root = build_sandbox(Path(td))
        for rel in ("tools/monkey_campaign/product/climb_intent_tests.py",
                    "tools/monkey_campaign/product/climb_intent_amr_tests.py"):
            t0 = time.perf_counter()
            proc = subprocess.run(
                [sys.executable, "-B", str(root / rel)],
                capture_output=True, text=True, encoding="utf-8",
                errors="replace", timeout=300)
            tail = proc.stdout.strip().splitlines()
            result_line = next((ln for ln in tail if "RESULT" in ln), "")
            out.append({"suite": Path(rel).name, "exit": proc.returncode,
                        "result_line": result_line,
                        "tail": tail[-1:],
                        "duration_s": time.perf_counter() - t0})
    return out


def main():
    t_start = time.perf_counter()
    print("MAT2-U05 motion leg (climb/let-go intent seam @ the pinned "
          "lineage, walk contract %s...)" % WALK_CONTRACT_SHA[:8])
    # F-A: identity of every shipped pin + the subtree manifest
    mismatches = [rel for rel, want in PINNED.items()
                  if sha256_file(HERE / rel) != want]
    manifest = json.loads((RECORDS / "receipts" / "identity_manifest.json")
                          .read_text(encoding="utf-8"))
    manifest_bad = [rel for rel, rec in manifest["artifacts"].items()
                    if sha256_file(RECORDS / rel) != rec["expected"]]
    print("F1 IDENTITY: pins %d/%d, manifest %d/%d" % (
        len(PINNED) - len(mismatches), len(PINNED),
        len(manifest["artifacts"]) - len(manifest_bad),
        len(manifest["artifacts"])))
    if mismatches or manifest_bad:
        print("F-A IDENTITY DIVERGES:", mismatches, manifest_bad)
        return 1
    core_before = {k: sha256_file(HERE / rel)
                   for k, rel in CORE_MODULES.items()}
    with tempfile.TemporaryDirectory(prefix="mat2u05-main-") as td:
        obs, rows, mod = run_timeline(Path(td))
    checks = evaluate(obs)
    for c in checks:
        print("  [%s] %s" % ("PASS" if c["ok"] else "FAIL", c["name"]))
        if not c["ok"]:
            print("      measured:", json.dumps(c["measured"], default=str))
    suites = run_original_suites()
    suites_green = all(s["exit"] == 0 and "GREEN" in s["result_line"]
                       for s in suites)
    for s in suites:
        print("  [%s] %s %s" % (
            "PASS" if s["exit"] == 0 and "GREEN" in s["result_line"]
            else "FAIL", s["suite"], s["result_line"]))
    teeth = run_teeth()
    teeth_ok = all(t.get("fired") for t in teeth)
    for t in teeth:
        print("  [%s] tooth %s (predicts %s) %s" % (
            "PASS" if t.get("fired") else "FAIL", t["mutation"],
            t.get("predicts"), json.dumps(t.get("detail"))))
    core_after = {k: sha256_file(HERE / rel)
                  for k, rel in CORE_MODULES.items()}
    identity_after = [rel for rel, want in PINNED.items()
                      if sha256_file(HERE / rel) != want]
    fc_ok = core_before == core_after and not identity_after
    print("  [%s] F-C pinned bytes identical before/after the full run" %
          ("PASS" if fc_ok else "FAIL"))
    checks.append({"name": "F-C_pinned_bytes_unchanged", "ok": fc_ok,
                   "measured": {"identical": fc_ok,
                                "post_run_pin_drift": identity_after}})
    checks.append({"name": "F-B_original_suites_green", "ok": suites_green,
                   "measured": suites})
    checks.append({"name": "F-D_probe_teeth_failing_first", "ok": teeth_ok,
                   "measured": teeth})
    ok = all(c["ok"] for c in checks)
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    (EVIDENCE / "trace.jsonl").write_text(
        "".join(json.dumps(r, sort_keys=True) + "\n" for r in rows),
        encoding="utf-8")
    trace_sha = sha256_file(EVIDENCE / "trace.jsonl")
    numerical = {
        "schema": "mat2-u05.seam.numerical.v1",
        "task_id": TASK_ID, "contract_task_id": CONTRACT_TASK_ID,
        "criteria_sha256": CRITERIA_SHA256,
        "preregistration_sha256": PREREG_SHA256,
        "run_id": RUN_ID,
        "subject_sha256": PINNED["seam_records/implementation.py"],
        "walk_contract_sha256": WALK_CONTRACT_SHA,
        "state_binding": {"kind": "trace", "raw_sha256": trace_sha,
                          "rows": len(rows),
                          "tick_interval": [rows[0]["tick"],
                                            rows[-1]["tick"]]},
        "counts": {
            "intent_deliveries": len(obs["deliveries"]),
            "climb_request": sum(1 for f, a, o in obs["deliveries"]
                                 if f["intent"] == "climb_request"),
            "let_go": sum(1 for f, a, o in obs["deliveries"]
                          if f["intent"] == "let_go"),
            "named_drops": len(obs["drops"]),
            "repeat_noops": len(obs["repeats"]),
            "walk_command_records": len(obs["walk_records"]),
            "walk_named_space_refusals": sum(
                1 for a, w, at in obs["walk_refusals"] if w == WALK_REFUSAL),
            "policy_calls": len(obs["policy_calls"]),
            "world_boot_calls": len(obs["boots"]),
            "sink_violations": len(obs["violations"]),
            "refused_versions": len(obs["refused_versions"]),
        },
        "checks": checks,
    }
    (EVIDENCE / "numerical_receipt.json").write_text(
        json.dumps(numerical, indent=1, sort_keys=True) + "\n",
        encoding="utf-8")
    runtime = {
        "schema": "mat2-u05.seam.runtime.v1",
        "task_id": TASK_ID, "run_id": RUN_ID,
        "command": "python -B tools/monkey_campaign/contributions/MAT2-U05/"
                   "seam_motion_probe.py",
        "python": sys.version.split()[0],
        "main_run_duration_s": obs["duration_s"],
        "total_probe_duration_s": time.perf_counter() - t_start,
        "delivery_is_synchronous":
            "structural: the strict sink records the delivery inside "
            "emit(), called inside press(); no queue, no emitter thread",
        "c12_note": "50 ms is the walk seam's command cadence, not a latency "
                    "claim; actual call durations recorded, nothing derived",
        "final_states": {"flow": obs["final_flow_state"],
                         "channel": obs["final_channel_state"],
                         "channel_held": obs["final_channel_held"]},
    }
    (EVIDENCE / "runtime_receipt.json").write_text(
        json.dumps(runtime, indent=1, sort_keys=True) + "\n",
        encoding="utf-8")
    qualification = {
        "schema": "mat2-u05.qualification.v1",
        "task_id": TASK_ID, "contract_task_id": CONTRACT_TASK_ID,
        "attempt_id": "867dc0b142e84c138c99a486e4d4caa6",
        "agent_id": "arrival-3ba367764f6543598c2669131d8b9982",
        "criteria_sha256": CRITERIA_SHA256,
        "preregistration_sha256": PREREG_SHA256,
        "base_rev": BASE_REV,
        "records_leg": {
            "reused_from": "ONT-U05 PR #179 head " + RECORDS_LEG_HEAD,
            "lineage_rev": LINEAGE_REV,
            "byte_exact": True,
            "identity_manifest_pins": len(manifest["artifacts"]),
        },
        "subject_sha256": PINNED["seam_records/implementation.py"],
        "evidence": {
            "numerical": {"reference": str(
                (EVIDENCE / "numerical_receipt.json").resolve()),
                "raw_sha256": sha256_file(
                    EVIDENCE / "numerical_receipt.json")},
            "runtime": {"reference": str(
                (EVIDENCE / "runtime_receipt.json").resolve()),
                "raw_sha256": sha256_file(
                    EVIDENCE / "runtime_receipt.json")},
        },
        "capture_pending": "camera/visual evidence added by "
                           "capture_build_seam.py",
    }
    (HERE / "qualification_receipt.json").write_text(
        json.dumps(qualification, indent=1, sort_keys=True) + "\n",
        encoding="utf-8")
    print("RESULT:", "GREEN" if ok else "FAIL",
          "(%d/%d checks)" % (sum(1 for c in checks if c["ok"]),
                              len(checks)))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
