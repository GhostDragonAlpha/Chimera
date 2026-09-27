"""input_settings_probe.py -- MAT2-U04 controls-profile (kind motion) probe.

Card MAT2-U04 (planning U04, verification profile `controls`, kind motion):
"Sensitivity, inversion and bindings needed for the selected controls work and
persist."  The frozen procedure is PREREGISTRATION.md, committed BEFORE this
probe first ran in this attempt (freeze commit 9b93a848).

CPU-only, headless, deterministic: injected integer milliseconds; the REAL
pinned input_settings.py (SUBJECT, 8d1a49d6) + input_mapper.py (7a36a45e) +
command_record.py (67711759) loaded byte-exact from ./reference (hashes
asserted at import; any drift aborts BEFORE any check).  The walk body is the
harness's declared integration of the REAL emitted CommandRecords (frozen law
in the prereg); the probe owns no physics.

One green run drives the frozen timeline through the SUBJECT'S OWN PUBLIC
SURFACE (load_settings / save_settings / apply_settings / configured_mapper /
InputSettings), producing evidence/trace.jsonl and the numerical receipt, and
spawns a SEPARATE OS process (`child_load_probe.py`) that re-loads the saved
settings in a fresh interpreter and replays the frozen replay sequence.
Exit 0 iff every frozen check is green.

    python -B tools/monkey_campaign/contributions/MAT2-U04/input_settings_probe.py
    python -B tools/monkey_campaign/contributions/MAT2-U04/input_settings_probe.py --selftest
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REFERENCE = HERE / "reference"
EVIDENCE = HERE / "evidence"

# ── the pinned lineage, byte-exact (no live-tree import; drift aborts) ───────
PINNED_SHA = {
    "tools/monkey_campaign/product/input_settings.py":
        "8d1a49d63f85164f3b9ac27f3387237d0a0790f68075e2455a74e2caa485a2f1",
    "tools/monkey_campaign/product/input_mapper.py":
        "7a36a45ead6637d9ba5659ea43b54a6b424803c8e57d02720ac970b42cfe6b44",
    "tools/monkey_campaign/product/input_settings_tests.py":
        "5845178ab12a69773e6b4bcdf2e8aa0b9fd144cddff7ee1e89204e0c5dd3720f",
    "tools/science_funnel/__init__.py":
        "c5a9f9b162177ec18d127edb799bbfe1ba08442ed95c72f8f0947f9d64618b19",
    "tools/science_funnel/typeb_export/__init__.py":
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "tools/science_funnel/typeb_export/command_record.py":
        "6771175933ad20ac6d20c360df96f6a9729a56deb31c58a13be5e76e1cc4355e",
}
SUBJECT_SHA256 = PINNED_SHA["tools/monkey_campaign/product/input_settings.py"]

RUN_ID = "mat2-u04-input-20260927-d9ce4334"
CRITERIA_SHA256 = "192ca43f061c4b6b2763d11213e0246ea075c3f62e6948948ba8c64213bf5180"
SCOPE_SHA256 = "cb5475f8486197a973edc4360b177fc31a629c4f0979ebf80dd76aae57996097"
ATTEMPT_ID = "d9ce4334674e435d95b9cb95373327e5"
AGENT_ID = "arrival-1390bce44d204c709636097a9613e84f"
CARD_ID = "MAT2-U04"
TASK_ID = "U04"
PLAY_HEAD = "f30f2224663324e9374b076938c56672febf4082"
INTEGRATION_COMMIT = "4699b37d"
RECORDS_LEG_HEAD = "939e8e6f725d162b18e8998aa725ad24f53fdb36"

TICK_MS = 50
T_END_MS = 19500
PHYSICS_HZ = 300
DT_S = 0.05

# ── frozen timeline events (PREREGISTRATION; nothing else is injected) ───────
PRESS_W = 200
MOUSE_BASELINE = (250, 2450, 5)
S1_T, S1_SENS = 2500, 0.008
MOUSE_S1 = (2500, 5450, 5)
S2_T = 5500
MOUSE_S2 = (5500, 8450, 5)
S3_T = 8500
MOUSE_S3A = (8500, 8950, 5)
PRESS_A_PRE = 9000
CANCEL_MOUSE = (9000, 9450, 5)        # key path + inverted mouse -> exact 0.0
RELEASE_A_PRE = 9500
MOUSE_S3B = (9500, 11450, 5)
S4_T = 11500
MOUSE_S4A = (11500, 11950, 5)
PRESS_A_POST = 12000
RELEASE_A_POST = 12500                # release A, press D (same tick)
RELEASE_D_POST = 13000                # release D; E pressed same tick (refused)
PRESS_E = 13000
SAVE_T = 13500
RELOAD_T = 14000
MOUSE_POST = (14000, 15950, 5)
RELEASE_W = 18500
CANCEL_WINDOW = (PRESS_A_PRE, RELEASE_A_PRE - TICK_MS)

# frozen replay sequence (parent M2 and child, identical injected clock)
REPLAY_MOUSE = (100, 300, 2)
REPLAY_LAST_BOUNDARY = 450            # 500 is the grid-dissolve tick (inert)


def _assert_pins():
    for rel, want in PINNED_SHA.items():
        got = hashlib.sha256((REFERENCE / rel).read_bytes()).hexdigest()
        if got != want:
            raise SystemExit("PIN DRIFT: %s is %s, pinned %s" % (rel, got, want))


_assert_pins()

sys.path.insert(0, str(REFERENCE))
for stale in [k for k in sys.modules if k == "tools" or k.startswith("tools.")]:
    del sys.modules[stale]

from tools.monkey_campaign.product import input_settings as IS          # noqa: E402
from tools.monkey_campaign.product import input_mapper as IM            # noqa: E402
from tools.science_funnel.typeb_export import command_record as CR      # noqa: E402


# ── small frozen helpers ─────────────────────────────────────────────────────
def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(Path(path).read_bytes())


def bindings_digest(bindings: dict) -> str:
    return sha256_bytes(json.dumps(dict(sorted(bindings.items())),
                                   sort_keys=True, separators=(",", ":"),
                                   ensure_ascii=False).encode("utf-8"))


def clamp(counts: int, sensitivity: float) -> float:
    """The mapper's own mouse law, recomputed with the pinned constants
    (identical expression -> bit-exact comparability)."""
    raw = counts * sensitivity / (IM.INTERVAL_MS / 1000.0)
    return max(-IM.OMEGA_MAX_RAD_S, min(IM.OMEGA_MAX_RAD_S, raw))


def record_dict(rec) -> dict:
    return {"v_forward": rec.v_forward, "yaw_rate": rec.yaw_rate,
            "issued_tick": rec.issued_tick, "source": rec.source,
            "record_version": rec.record_version}


def records_equal(a: dict, b: dict) -> bool:
    return (a["v_forward"] == b["v_forward"] and a["yaw_rate"] == b["yaw_rate"]
            and a["issued_tick"] == b["issued_tick"]
            and a["source"] == b["source"]
            and a["record_version"] == b["record_version"])


class Check:
    """One frozen numerical check: id, prediction, measured outcome."""

    def __init__(self, cid, prediction):
        self.id = cid
        self.prediction = prediction
        self.ok = True
        self.detail = []
        self.counts = {}

    def require(self, ok, detail=""):
        if not ok:
            self.ok = False
            self.detail.append(str(detail))
        return ok

    def as_dict(self):
        return {"id": self.id, "prediction": self.prediction, "ok": self.ok,
                "detail": self.detail[:20], "counts": self.counts}


# ── frozen settings vectors (PREREGISTRATION) ────────────────────────────────
def s4_bindings():
    b = dict(IM.DEFAULT_BINDINGS)
    b["A"] = "turn_right"
    b["D"] = "turn_left"
    b["E"] = "sprint"
    return b


def s4_vector():
    return IS.InputSettings(bindings=s4_bindings(),
                            sensitivity=IS.SENS_YAW_MAX_RAD_PER_COUNT,
                            invert_yaw=True)


def vector_at(t):
    if t < S1_T:
        return IS.default_settings()
    if t < S2_T:
        return IS.InputSettings(dict(IM.DEFAULT_BINDINGS), S1_SENS, False)
    if t < S3_T:
        return IS.InputSettings(dict(IM.DEFAULT_BINDINGS),
                                IS.SENS_YAW_MAX_RAD_PER_COUNT, False)
    if t < S4_T:
        return IS.InputSettings(dict(IM.DEFAULT_BINDINGS),
                                IS.SENS_YAW_MAX_RAD_PER_COUNT, True)
    return s4_vector()


def invert_at(t):
    return t >= S3_T


def mouse_window(t):
    for lo, hi, n in (MOUSE_BASELINE, MOUSE_S1, MOUSE_S2, MOUSE_S3A,
                      CANCEL_MOUSE, MOUSE_S3B, MOUSE_S4A, MOUSE_POST):
        if lo <= t <= hi:
            return n
    return 0


def in_cancel_window(t):
    return CANCEL_WINDOW[0] <= t <= CANCEL_WINDOW[1]


# ── the frozen replay sequence (parent M2 and child run it identically) ──────
def replay_law_records(settings):
    """Recompute the replay's expected emitted records from the pinned mapper
    laws (grid, key remap, signed mouse clamp, release-decay), used by N6 to
    show the reloaded mapper obeys the frozen laws."""
    s = settings.signed_sensitivity()
    remap = settings.bindings
    press = {0: ["W"], 50: ["A"]}
    release = {350: ["A"], 400: ["W"]}
    held: set = set()
    counts = 0.0
    next_due = None
    last_v = 0.0
    tail = None
    out = []

    def held_speed_action(n):
        return remap.get(n) in ("forward", "backward")

    for now in range(0, 501, TICK_MS):
        for name in press.get(now, []):
            held.add(name)
        if REPLAY_MOUSE[0] <= now <= REPLAY_MOUSE[1]:
            counts += REPLAY_MOUSE[2]
        for name in release.get(now, []):
            held.discard(name)
            if held_speed_action(name) and not any(held_speed_action(n) for n in held) \
                    and last_v > 0.0 and tail is None:
                tail = (last_v, now, 0)
        speed = IM.V_MAX_IN_BAND_M_S if any(held_speed_action(n) for n in held) else None
        pending = speed is not None or tail is not None or counts != 0.0
        if next_due is None:
            if not pending:
                continue
            next_due = now
        if now < next_due:
            continue
        next_due = now + TICK_MS
        if tail is not None and speed is None:
            v0, released_ms, seen = tail
            if seen == 0:
                elapsed = max(0, now - released_ms)
                if elapsed >= IM.RELEASE_DECAY_MS:
                    tail = None
                    v = 0.0
                else:
                    tail = (v0, released_ms, 1)
                    v = v0 * (1.0 - elapsed / IM.RELEASE_DECAY_MS)
            else:
                tail = None
                v = 0.0
        else:
            v = speed
        if v is None:
            counts = 0.0
            continue
        key_yaw = (-IM.OMEGA_MAX_RAD_S if any(remap.get(n) == "turn_right"
                                              for n in held) else 0.0) \
            + (IM.OMEGA_MAX_RAD_S if any(remap.get(n) == "turn_left"
                                         for n in held) else 0.0)
        mouse_yaw = 0.0
        if counts:
            mouse_yaw = clamp(int(counts), s)
            counts = 0.0
        yaw = max(-IM.OMEGA_MAX_RAD_S, min(IM.OMEGA_MAX_RAD_S, key_yaw + mouse_yaw))
        out.append({"t_ms": now, "v_forward": float(v), "yaw_rate": yaw,
                    "issued_tick": (now * PHYSICS_HZ) // 1000})
        if speed is not None:
            last_v = float(speed)
    return out


# ── the child-process persistence leg ────────────────────────────────────────
def run_child(settings_path: Path, scratch: Path):
    """Spawn child_load_probe.py in a SEPARATE OS process."""
    child = HERE / "child_load_probe.py"
    out_path = Path(scratch) / "child_records.json"
    cmd = [sys.executable, "-B", str(child), str(settings_path), str(out_path)]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if proc.returncode != 0:
        return False, {"stderr": proc.stderr[-2000:], "stdout": proc.stdout[-2000:]}
    return True, json.loads(out_path.read_text(encoding="utf-8"))


# ── the green run ────────────────────────────────────────────────────────────
def seam_snapshot():
    return {"omega": IM.OMEGA_MAX_RAD_S, "v_max": IM.V_MAX_IN_BAND_M_S,
            "interval": IM.INTERVAL_MS, "sens": IM.SENS_RAD_PER_COUNT,
            "bindings": dict(IM.DEFAULT_BINDINGS),
            "record_version": CR.COMMAND_RECORD_VERSION}


def green_run(scratch: Path, checks: list, seam_before: dict, events_log: list,
              child_stats: dict | None = None):
    child_stats = child_stats if child_stats is not None else {}
    (C0, C1, C2, C3, C4, C5, C6, C7, C8, C9) = checks
    scratch = Path(scratch)
    scratch.mkdir(parents=True, exist_ok=True)
    settings_path = scratch / "monkey_input_settings.json"
    trace = []
    records_all = []
    body = {"x": 0.0, "y": 0.0, "z": 0.0, "heading": 0.0}
    press_windows = {PRESS_W: ["W"], PRESS_A_PRE: ["A"], PRESS_A_POST: ["A"],
                     PRESS_E: ["E"]}
    release_windows = {RELEASE_A_PRE: ["A"], RELEASE_D_POST: ["D"],
                       RELEASE_W: ["W"]}

    def phase_of(t):
        if t < PRESS_W: return "first_run_defaults"
        if t < S1_T: return "baseline_sensitivity_default"
        if t < S2_T: return "sensitivity_x4"
        if t < S3_T: return "sensitivity_ceiling"
        if t < S4_T: return "inverted_mouse_axis"
        if t < SAVE_T: return "rebound_keys"
        if t < RELOAD_T: return "saved_to_disk"
        if t < MOUSE_POST[1]: return "reloaded_parent_child_verified"
        if t < RELEASE_W: return "straight_walk"
        return "release_decay"

    # N1: first run on an ABSENT declared path
    C1.require(not settings_path.exists(), "declared path must start absent")
    listing_before = sorted(p.name for p in scratch.iterdir())
    lr0 = IS.load_settings(settings_path)
    listing_after = sorted(p.name for p in scratch.iterdir())
    C1.require(lr0.status == "first_run", "status %r" % lr0.status)
    C1.require(lr0.settings == IS.default_settings(), "defaults mismatch")
    C1.require(listing_before == listing_after,
               "load created files: %r" % listing_after)
    C1.counts["refusals"] = len(lr0.refusals)

    current = lr0.settings
    mapper = IS.configured_mapper(IM.MockSink(), current)

    saved_bytes = None
    reload_result = None
    replay_parent = None
    child_payload = None
    child_ok = None

    for t in range(0, T_END_MS + 1, TICK_MS):
        pre = []
        for name in press_windows.get(t, []):
            mapper.press(name, t)
            pre.append({"event": "press", "name": name})
            events_log.append({"t": t, "event": "press", "name": name})
        if t == RELEASE_A_POST:
            mapper.release("A", t)
            mapper.press("D", t)
            pre += [{"event": "release", "name": "A"}, {"event": "press", "name": "D"}]
            events_log += [{"t": t, "event": "release", "name": "A"},
                           {"t": t, "event": "press", "name": "D"}]
        for name in release_windows.get(t, []):
            mapper.release(name, t)
            pre.append({"event": "release", "name": name})
            events_log.append({"t": t, "event": "release", "name": name})
        counts = mouse_window(t)
        if counts:
            mapper.mouse(counts)
            pre.append({"event": "mouse", "counts": counts})

        # frozen settings events (through the module's own apply surface)
        if t == S1_T:
            current = vector_at(t)
            IS.apply_settings(current, mapper)
        elif t == S2_T:
            current = vector_at(t)
            IS.apply_settings(current, mapper)
        elif t == S3_T:
            current = vector_at(t)
            IS.apply_settings(current, mapper)
        elif t == S4_T:
            current = vector_at(t)
            IS.apply_settings(current, mapper)
        elif t == SAVE_T:
            saved_bytes = IS.canonical_bytes(current)
            IS.save_settings(current, settings_path)
        elif t == RELOAD_T:
            reload_result = IS.load_settings(settings_path)
            replay_parent = run_replay(reload_result.settings, events_log)
            child_started = time.monotonic()
            child_ok, child_payload = run_child(settings_path, scratch)
            child_stats["wall_ms"] = (time.monotonic() - child_started) * 1000.0
            child_stats["pid"] = child_payload.get("pid") if child_ok else None

        emitted = mapper.tick(t)
        records_all.extend((t, r) for r in emitted)
        # frozen body integration (harness-owned; PREREGISTRATION)
        for rec in emitted:
            body["heading"] += rec.yaw_rate * DT_S
            body["x"] += rec.v_forward * math.cos(body["heading"]) * DT_S
            body["z"] += rec.v_forward * math.sin(body["heading"]) * DT_S

        pressed_now = any(e["event"] == "press" for e in pre)
        trace.append({
            "tick": t // TICK_MS, "t_ms": t, "phase": phase_of(t),
            "events": pre,
            "settings": {"sensitivity": current.sensitivity,
                         "invert_yaw": current.invert_yaw,
                         "bindings_sha256": bindings_digest(current.bindings)},
            "keys_held": sorted(mapper.held),
            "records": [record_dict(r) for r in emitted],
            "refusals": ([list(x) for x in mapper.last_trace.get("refused", [])]
                         if pressed_now else []),
            "body": dict(body),
        })

    # ── N0 identity (pins enforced at import; lineage re-asserted here) ─────
    C0.require(sha256_file(REFERENCE / "tools/monkey_campaign/product/input_settings.py")
               == SUBJECT_SHA256, "subject drift")
    C0.require(IS.SCHEMA_ID == "chimera.monkey_input.v1", "schema id")
    C0.counts["reference_files"] = len(PINNED_SHA)

    # ── N2 sensitivity law (non-inverted mouse-only boundaries; the cancel
    # window is N4's and the inverted boundaries are N3's signed law) ────────
    by_phase = {}
    for t, rec in records_all:
        counts = mouse_window(t)
        if not counts or in_cancel_window(t):
            continue
        by_phase.setdefault(phase_group(t), []).append((t, rec.yaw_rate))
        if invert_at(t):
            continue
        want = clamp(counts, vector_at(t).sensitivity)
        C2.require(rec.yaw_rate == want,
                   "t=%d yaw %r != recomputed %r" % (t, rec.yaw_rate, want))
    C2.counts["mouse_boundaries"] = sum(len(v) for v in by_phase.values())
    base = by_phase.get("baseline", [])
    s1 = by_phase.get("s1", [])
    if base and s1:
        ratio = s1[0][1] / base[0][1]
        C2.require(abs(ratio - 4.0) <= 1e-12, "4x ratio %r" % ratio)
        C2.counts["ratio_first"] = ratio
    s2 = by_phase.get("s2", [])
    C2.require(bool(s2) and all(y == IM.OMEGA_MAX_RAD_S for _, y in s2),
               "ceiling saturation not exact")
    C2.counts["ceiling_boundaries"] = len(s2)

    # ── N3 inversion (same +5 counts: +OMEGA under S2, -OMEGA under S3/S4) ──
    s3a = by_phase.get("s3a", [])
    C3.require(bool(s2) and bool(s3a), "missing ceiling/inverted boundaries")
    if s2 and s3a:
        C3.require(s2[0][1] == IM.OMEGA_MAX_RAD_S
                   and s3a[0][1] == -IM.OMEGA_MAX_RAD_S,
                   "sign flip not exact: %r vs %r" % (s2[0][1], s3a[0][1]))
    inverted = 0
    for t, rec in records_all:
        counts = mouse_window(t)
        if not counts or in_cancel_window(t) or not invert_at(t):
            continue
        inverted += 1
        want = clamp(counts, -vector_at(t).sensitivity)
        C3.require(rec.yaw_rate == want, "t=%d signed-law mismatch" % t)
    C3.counts["inverted_boundaries"] = inverted

    # ── N4 keys unaffected by inversion ─────────────────────────────────────
    n4 = [row for row in trace if CANCEL_WINDOW[0] <= row["t_ms"] <= CANCEL_WINDOW[1]]
    C4.require(len(n4) == 10, "expected 10 cancel boundaries, got %d" % len(n4))
    for row in n4:
        yaw = row["records"][0]["yaw_rate"] if row["records"] else None
        C4.require(len(row["records"]) == 1 and yaw == 0.0,
                   "t=%d cancel yaw %r" % (row["t_ms"], yaw))
    C4.counts["cancel_boundaries"] = len(n4)

    # ── N5 rebinding ────────────────────────────────────────────────────────
    def yaw_at(lo, hi):
        return [row["records"][0]["yaw_rate"] for row in trace
                if lo <= row["t_ms"] <= hi and row["records"]]
    a_post = yaw_at(12000, 12450)
    d_post = yaw_at(12500, 12950)
    C5.require(len(a_post) == 10 and all(y == -IM.OMEGA_MAX_RAD_S for y in a_post),
               "A(remapped turn_right) must yield -OMEGA exactly")
    C5.require(len(d_post) == 10 and all(y == IM.OMEGA_MAX_RAD_S for y in d_post),
               "D(remapped turn_left) must yield +OMEGA exactly")
    unique_refusals = {tuple(r) for row in trace for r in row["refusals"]}
    C5.require(any(r[0] == "sprint" for r in unique_refusals),
               "E->sprint refusal not named: %r" % (unique_refusals,))
    C5.counts["named_refusals"] = len(unique_refusals)
    bad = IS.InputSettings(bindings={"W": "forward", "S": "backward",
                                     "A": "turn_left", "D": "turn_left"},
                           sensitivity=0.002, invert_yaw=False)
    p = scratch / "coverage_negative.json"
    p.write_bytes(IS.canonical_bytes(bad))
    lr_cov = IS.load_settings(p)
    C5.require(lr_cov.status == "refused"
               and any(r.code == "action_unbound" for r in lr_cov.refusals),
               "coverage refusal codes: %r" % ([r.code for r in lr_cov.refusals],))
    p.unlink()

    # ── N6 persistence ──────────────────────────────────────────────────────
    C6.require(saved_bytes is not None
               and settings_path.read_bytes() == saved_bytes,
               "file bytes != canonical_bytes(S4)")
    IS.save_settings(reload_result.settings, settings_path)
    C6.require(settings_path.read_bytes() == saved_bytes, "resave not byte-identical")
    C6.require(reload_result.status == "loaded" and not reload_result.refusals,
               "reload status %r" % reload_result.status)
    C6.require(reload_result.settings == s4_vector(),
               "reloaded settings != S4 vector")
    C6.counts["settings_bytes"] = len(saved_bytes or b"")
    # the reloaded parent mapper obeys the frozen laws (recomputed replay law)
    want_replay = replay_law_records(reload_result.settings)
    C6.require(len(replay_parent) == len(want_replay),
               "replay %d vs law %d records" % (len(replay_parent), len(want_replay)))
    for got, want in zip(replay_parent, want_replay):
        C6.require(got["yaw_rate"] == want["yaw_rate"]
                   and got["v_forward"] == want["v_forward"]
                   and got["issued_tick"] == want["issued_tick"],
                   "replay t=%s law mismatch" % want.get("t_ms"))
    C6.counts["replay_records"] = len(replay_parent)
    # the CHILD PROCESS (fresh interpreter) reproduces the parent replay exactly
    C6.require(child_ok is True, "child process failed: %r" % (child_payload,))
    if child_ok:
        C6.require(child_payload["status"] == "loaded",
                   "child status %r" % child_payload["status"])
        C6.require(child_payload["settings_document"] == s4_vector().to_document(),
                   "child settings document != S4.to_document()")
        cr = child_payload["records"]
        C6.require(len(cr) == len(replay_parent),
                   "child %d vs parent %d records" % (len(cr), len(replay_parent)))
        mism = sum(0 if records_equal(x, y) else 1
                   for x, y in zip(cr, replay_parent))
        C6.require(mism == 0, "%d field mismatches" % mism)
        C6.counts["child_pid"] = child_payload.get("pid")
        C6.counts["child_records"] = len(cr)
    post = by_phase.get("post", [])
    C6.require(bool(post) and all(y == -IM.OMEGA_MAX_RAD_S for _, y in post),
               "post-reload live boundaries lost the settings")

    # ── N7 refusals (load never writes; named codes) ────────────────────────
    doc = s4_vector().to_document()
    d_hi = copy.deepcopy(doc); d_hi["sensitivity"]["yaw"] = 0.16
    d_zero = copy.deepcopy(doc); d_zero["sensitivity"]["yaw"] = 0
    d_bool = copy.deepcopy(doc); d_bool["sensitivity"]["yaw"] = True
    d_act = copy.deepcopy(doc); d_act["bindings"]["Q"] = "dance"
    poisons = {
        "corrupt.json": b"{not json",
        "schema_unknown.json": b'{"schema":"chimera.monkey_input.v2","bindings":{},'
                               b'"sensitivity":{"yaw":0.002},"invert":{"yaw":false}}',
        "key_unknown.json": b'{"schema":"chimera.monkey_input.v1","bindings":{},'
                            b'"sensitivity":{"yaw":0.002},"invert":{"yaw":false},'
                            b'"interval_ms":50}',
        "too_high.json": json.dumps(d_hi).encode("utf-8"),
        "zero.json": json.dumps(d_zero).encode("utf-8"),
        "bool_sens.json": json.dumps(d_bool).encode("utf-8"),
        "duplicate.json": b'{"schema":"chimera.monkey_input.v1",'
                          b'"bindings":{"W":"forward"},"bindings":{"S":"backward"},'
                          b'"sensitivity":{"yaw":0.002},"invert":{"yaw":false}}',
        "nan.json": b'{"schema":"chimera.monkey_input.v1","bindings":{},'
                    b'"sensitivity":{"yaw":NaN},"invert":{"yaw":false}}',
        "action_unknown.json": json.dumps(d_act).encode("utf-8"),
    }
    want_code = {
        "corrupt.json": "json_corrupt", "schema_unknown.json": "schema_unknown",
        "key_unknown.json": "key_unknown", "too_high.json": "value_out_of_range",
        "zero.json": "value_out_of_range", "bool_sens.json": "sensitivity_type",
        "duplicate.json": "key_duplicate", "nan.json": "not_finite_json",
        "action_unknown.json": "action_unknown",
    }
    listing = sorted(p.name for p in scratch.iterdir())
    for name, blob in poisons.items():
        p = scratch / name
        p.write_bytes(blob)
        lr = IS.load_settings(p)
        codes = [r.code for r in lr.refusals]
        C7.require(lr.status == "refused" and want_code[name] in codes,
                   "%s -> %r" % (name, codes))
        C7.require(lr.settings == IS.default_settings(), "%s partial accept" % name)
        p.unlink()
    C7.require(sorted(p.name for p in scratch.iterdir()) == listing,
               "refused loads changed the scratch listing")
    C7.counts["poisons"] = len(poisons)

    # ── N8 seam protection ──────────────────────────────────────────────────
    C8.require(IM.OMEGA_MAX_RAD_S == seam_before["omega"]
               and IM.V_MAX_IN_BAND_M_S == seam_before["v_max"]
               and IM.INTERVAL_MS == seam_before["interval"]
               and IM.SENS_RAD_PER_COUNT == seam_before["sens"]
               and IM.DEFAULT_BINDINGS == seam_before["bindings"]
               and CR.COMMAND_RECORD_VERSION == seam_before["record_version"],
               "seam constants drifted")
    C8.require(IS.SENS_YAW_MAX_RAD_PER_COUNT
               == IM.OMEGA_MAX_RAD_S * IM.INTERVAL_MS / 1000.0,
               "ceiling not the derived expression")
    for rel in ("tools/monkey_campaign/product/input_mapper.py",
                "tools/science_funnel/typeb_export/command_record.py"):
        C8.require(sha256_file(REFERENCE / rel) == PINNED_SHA[rel],
                   "%s rewritten" % rel)
    C8.counts["apply_calls"] = 4

    # ── N9 trace integrity ──────────────────────────────────────────────────
    for t, rec in records_all:
        if rec.source != IM.SOURCE_ID or rec.record_version != CR.COMMAND_RECORD_VERSION:
            C9.require(False, "t=%d provenance" % t)
        if not (0 <= rec.v_forward <= IM.V_MAX_IN_BAND_M_S):
            C9.require(False, "t=%d v %r out of band" % (t, rec.v_forward))
        if abs(rec.yaw_rate) > IM.OMEGA_MAX_RAD_S:
            C9.require(False, "t=%d yaw beyond bound" % t)
        if rec.issued_tick != (t * PHYSICS_HZ) // 1000:
            C9.require(False, "t=%d issued_tick" % t)
    C9.require(len(records_all) == 368,
               "main records %d != 368" % len(records_all))
    C9.require(not any(row["refusals"] and row["t_ms"] < PRESS_E for row in trace),
               "unexpected refusal before E")
    C9.counts["records"] = len(records_all)
    C9.counts["trace_rows"] = len(trace)
    C9.counts["replay_records_measured"] = len(replay_parent or [])

    return trace, records_all, settings_path, saved_bytes


def phase_group(t):
    if 250 <= t <= 2450: return "baseline"
    if 2500 <= t <= 5450: return "s1"
    if 5500 <= t <= 8450: return "s2"
    if 8500 <= t <= 8950: return "s3a"
    if 9500 <= t <= 11450: return "s3b"
    if 11500 <= t <= 11950: return "s4a"
    if 14000 <= t <= 15950: return "post"
    return "other"


def run_replay(settings, events_log):
    """Drive ONE fresh mapper through the frozen replay sequence on its own
    injected clock (0..500 ms). Returns the list of record dicts."""
    sink = IM.MockSink()
    mapper = IS.configured_mapper(sink, settings)
    records = []
    presses = {0: ["W"], 50: ["A"]}
    releases = {350: ["A"], 400: ["W"]}
    for now in range(0, 501, TICK_MS):
        for name in presses.get(now, []):
            mapper.press(name, now)
            events_log.append({"replay_t": now, "event": "press", "name": name})
        if REPLAY_MOUSE[0] <= now <= REPLAY_MOUSE[1]:
            mapper.mouse(REPLAY_MOUSE[2])
            events_log.append({"replay_t": now, "event": "mouse",
                               "counts": REPLAY_MOUSE[2]})
        for name in releases.get(now, []):
            mapper.release(name, now)
            events_log.append({"replay_t": now, "event": "release", "name": name})
        for rec in mapper.tick(now):
            records.append(record_dict(rec))
    return records


CHECKS = [
    ("N0", "reference pins + lineage identity equal the frozen values"),
    ("N1", "first_run on absent path: defaults, nothing created"),
    ("N2", "mouse yaw bit-exact vs the mapper's own law; 4x ratio; exact ceiling"),
    ("N3", "inversion flips the same counts to exactly -OMEGA; signed law exact"),
    ("N4", "turn key path unaffected by inversion (+OMEGA + -OMEGA == 0.0 exact)"),
    ("N5", "rebound keys flip emitted sign; E->sprint refused by name; coverage refuses"),
    ("N6", "save canonical; reload exact in parent AND a fresh child process; replays field-exact"),
    ("N7", "nine poison classes refuse BY NAME with defaults; load never writes"),
    ("N8", "seam constants, bindings table and pinned module bytes unchanged"),
    ("N9", "368 main records conform to provenance/band/timing laws"),
]


def main() -> int:
    started = time.monotonic()
    checks = [Check(cid, pred) for cid, pred in CHECKS]
    seam = seam_snapshot()
    EVIDENCE.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="mat2-u04-probe-") as tmp:
        child_stats: dict = {}
        trace, records_all, settings_path, saved_bytes = \
            green_run(Path(tmp), checks, seam, [], child_stats)
        if "--selftest" in sys.argv:
            return selftest(Path(tmp))
        trace_path = EVIDENCE / "trace.jsonl"
        trace_path.write_bytes(
            "".join(json.dumps(r, sort_keys=True) + "\n" for r in trace)
            .encode("utf-8"))
        green = all(c.ok for c in checks)
        receipt = {
            "schema": "mat2-u04.input-settings.numerical.v1",
            "task_id": TASK_ID, "card_id": CARD_ID,
            "run_id": RUN_ID, "criteria_sha256": CRITERIA_SHA256,
            "scope_sha256": SCOPE_SHA256, "attempt_id": ATTEMPT_ID,
            "agent_id": AGENT_ID,
            "subject": "tools/monkey_campaign/product/input_settings.py",
            "subject_sha256": SUBJECT_SHA256,
            "pinned_lineage": {"play_head": PLAY_HEAD,
                               "integration_commit": INTEGRATION_COMMIT,
                               "records_leg_pr_head": RECORDS_LEG_HEAD},
            "environment": {"headless": True, "gpu": False,
                            "engine_process": False, "network": False,
                            "platform": sys.platform,
                            "python": sys.version.split()[0],
                            "clock_note": "trace times are INJECTED tick ms"},
            "trace": {"reference":
                      "tools/monkey_campaign/contributions/MAT2-U04/evidence/trace.jsonl",
                      "sha256": sha256_file(trace_path), "rows": len(trace)},
            "settings_file": {"bytes": len(saved_bytes or b""),
                              "sha256": sha256_bytes(saved_bytes or b"")},
            "checks": [c.as_dict() for c in checks],
            "prediction_deviations": [
                {"check": "N9", "prereg": "11 replay records per replay runner "
                 "(boundaries 0..500)", "measured": 10,
                 "reason": "the prereg's arithmetic miscounted: boundary 450 "
                 "emits the tail's exact-zero record and boundary 500 is the "
                 "grid-dissolve tick, which emits nothing; the enforced frozen "
                 "law of the pinned mapper is 10. Disclosed, not silently "
                 "corrected (ONT-U01 prediction_deviations precedent)."},
                {"check": "N6", "prereg": "M2 replay records field-exact == "
                 "original-phase records for the same (settings, input) pairs",
                 "measured": "replay-law conformance + parent/child field-exact",
                 "reason": "no main-trace window pairs 1:1 with the replay "
                 "sequence's key+mouse combination, so the comparison "
                 "implemented is (a) every replay record bit-exact vs the "
                 "mapper's own law recomputed under the RELOADED settings and "
                 "(b) parent M2 vs fresh-child records field-exact. The "
                 "main-trace laws themselves are N2-N5."},
            ],
            "all_green": green,
            "deviations": [c.id for c in checks if not c.ok],
            "wall_clock_probe_seconds": time.monotonic() - started,
        }
        (EVIDENCE / "numerical_receipt.json").write_text(
            json.dumps(receipt, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        runtime = {
            "schema": "mat2-u04.input-settings.runtime.v1",
            "task_id": TASK_ID, "card_id": CARD_ID,
            "run_id": RUN_ID, "attempt_id": ATTEMPT_ID, "agent_id": AGENT_ID,
            "criteria_sha256": CRITERIA_SHA256,
            "subject": "tools/monkey_campaign/product/input_settings.py",
            "subject_sha256": SUBJECT_SHA256,
            "environment": {"headless": True, "cpu_only": True, "gpu": False,
                            "engine_process": False, "network": False,
                            "platform": sys.platform,
                            "python": sys.version.split()[0],
                            "timing": "all trace times are INJECTED tick "
                                      "milliseconds (20 Hz boundary); the only "
                                      "wall clocks are the separately-reported "
                                      "durations here"},
            "child_process": {
                "role": "fresh-interpreter settings RELOAD + frozen replay",
                "command": "python -B child_load_probe.py <settings.json> "
                           "<scratch>/child_records.json",
                "exit_code": 0 if checks[6].ok else 1,
                "pid": child_stats.get("pid"),
                "records": checks[6].counts.get("child_records", 0),
                "wall_clock_ms": child_stats.get("wall_ms"),
            },
            "trace_identity": {"sha256": receipt["trace"]["sha256"],
                               "rows": receipt["trace"]["rows"],
                               "tick_interval": [0, T_END_MS // TICK_MS]},
            "records_emitted": len(records_all),
            "pinned_suite": {
                "runner": "records_leg/ONT-U04/run_falsifiers.py (UNMODIFIED, "
                          "from reviewed PR #182 head " + RECORDS_LEG_HEAD + ")",
                "outcome": "see evidence/records_leg_rerun.json (GREEN 33/0)",
            },
            "wall_clock_probe_seconds": receipt["wall_clock_probe_seconds"],
            "timing_chain": "every record issued_tick == t_ms*300//1000 "
                            "(check N9); release decay lands exactly 0.0 "
                            "within the 100 ms deadline (frozen boundaries "
                            "18500/19000)",
        }
        (EVIDENCE / "runtime_receipt.json").write_text(
            json.dumps(runtime, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        print("VERDICT:", "GREEN" if green else "RED",
              "| checks:", sum(c.ok for c in checks), "/", len(checks),
              "| records:", records_all and len(records_all),
              "| trace sha:", receipt["trace"]["sha256"][:12])
        return 0 if green else 1


# ── failing-first selftest (PREREGISTRATION demos 2-4): mutations MUST fire ──
def selftest(scratch: Path) -> int:
    results = []
    real_apply = IS.apply_settings

    def halving_apply(settings, mapper):
        return real_apply(IS.InputSettings(settings.bindings,
                                           settings.sensitivity / 2.0,
                                           settings.invert_yaw), mapper)
    IS.apply_settings = halving_apply
    results.append(("SENS-LAW-BREAK fires N2",
                    run_checks_once(scratch / "st_sens", {"N2"})))
    IS.apply_settings = real_apply

    def unsigned_apply(settings, mapper):
        return real_apply(IS.InputSettings(settings.bindings,
                                           settings.sensitivity, False), mapper)
    IS.apply_settings = unsigned_apply
    results.append(("INVERT-BREAK fires N3",
                    run_checks_once(scratch / "st_inv", {"N3"})))
    IS.apply_settings = real_apply

    real_child = run_child

    def tampered_child(settings_path, sdir):
        blob = json.loads(settings_path.read_text(encoding="utf-8"))
        blob["sensitivity"]["yaw"] = 0.001
        tampered = settings_path.parent / "tampered.json"
        tampered.write_text(json.dumps(blob), encoding="utf-8")
        return real_child(tampered, sdir)
    globals()["run_child"] = tampered_child
    results.append(("PERSIST-BREAK fires N6",
                    run_checks_once(scratch / "st_pers", {"N6"})))
    globals()["run_child"] = real_child

    green = all(ok for _, ok in results)
    for name, ok in results:
        print("SELFTEST %-28s %s" % (name, "FIRED" if ok else "DID-NOT-FIRE"))
    (EVIDENCE / "selftest_receipt.json").write_text(json.dumps({
        "schema": "mat2-u04.input-settings.selftest.v1", "run_id": RUN_ID,
        "demonstrations": [{"name": n, "fired": ok} for n, ok in results],
        "all_fired": green}, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return 0 if green else 1


def run_checks_once(scratch: Path, expect_ids: set) -> bool:
    """Run the check battery in a scratch dir; True iff one of expect_ids
    FAILED (the mutation fired). A mutation that crashes the run also counts."""
    checks = [Check(cid, pred) for cid, pred in CHECKS]
    try:
        green_run(scratch, checks, seam_snapshot(), [])
    except SystemExit:
        return False
    except Exception:
        return True
    failed = {c.id for c in checks if not c.ok}
    return bool(failed & expect_ids)


if __name__ == "__main__":
    sys.exit(main())
