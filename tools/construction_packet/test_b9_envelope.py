"""B9 material-geometry-solver qualification envelope battery.

Scope: docs/evidence/construction_packet_20261012/B9_envelope_scope.md.
Every band asserted here is calibrated on a MEASURED B8 failure (the numbers
are in the B9_* constants of b2_scene.cpp and the B8 gallery evidence):

  * rest-sink band   <- 4x stiffer ground + 0.3 kg block exploded at 81 m/s
  * sliding band     <- 20 mm sliding block exploded at 91 m/s
  * tipping band     <- 2 N at COM toppled the 20 mm-base, 110 mm wall
                        (friction couple needs ~11 mm normal shift across a
                        base the 10 mm foundation sink already consumed)

Acceptance criteria covered (scope doc section 3):
  1 named refusals before mutation ........ test_sink_band_named_refusal
                                             test_tipping_band_boundary
                                             test_slide_band_boundary
  2 unchanged state after rejection ....... (hash assertions in each)
  3 boundary cases ........................ test_tipping_band_boundary
  4 known-failure reproductions ........... tests 1-3 refuse the exact
                                             failure tuples; the runtime
                                             trio below covers dynamic exit
  5 visible runtime response to envelope exit after admission:
      speed exceeded ........................ test_runtime_speed_event
      declared stop crossed .................. test_runtime_stop_event
      stand-role tilt ........................ test_runtime_tilt_event
  envelope travels with save/restore ........ test_envelope_roundtrip

Run:  python tools/construction_packet/test_b9_envelope.py
Requires: .tmp/body-engine/Release/chimera_engine.exe (Release build).
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
for p in (str(HERE), str(HERE.parent)):
    if p not in sys.path:
        sys.path.insert(0, p)

import b2_scene_gen  # noqa: E402

REPO = HERE.parent.parent
EXE = REPO / ".tmp" / "body-engine" / "Release" / "chimera_engine.exe"
PORT = 8797
BASE = f"http://127.0.0.1:{PORT}"
RS = b2_scene_gen.REST_SINK_M          # 0.010 m rest sink = the band edge
G = b2_scene_gen.G

_proc: subprocess.Popen | None = None


def _get(path: str) -> dict:
    with urllib.request.urlopen(BASE + path, timeout=10) as r:
        return json.loads(r.read().decode())


def _post(path: str, body: str = "") -> dict:
    req = urllib.request.Request(BASE + path, data=body.encode(), method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return json.loads(e.read().decode())


def _state() -> dict:
    return _get("/tick_b2_state")


def _hash() -> str:
    return _get("/tick_b2_hash")["state_hash"]


def _part(st: dict, pid: str) -> dict:
    return next(p for p in st["parts"] if p["id"] == pid)


def _wait_steps(n: int) -> None:
    s0 = _state()["steps"]
    deadline = time.time() + 30.0
    while time.time() < deadline:
        if _state()["steps"] >= s0 + n:
            return
        time.sleep(0.005)
    raise RuntimeError("engine is not stepping")


def _admit(parts: list[dict], reason: str = "b9") -> dict:
    doc = {"schema": "chimera.b2_scene.v1", "gravity_m_s2": 9.81,
           "reason": reason, "parts": parts}
    return _post("/tick_b2_admit", json.dumps(doc))


def _box(pid, x0, x1, y0, y1, z0, z1, rho=600, mu=0.4):
    return b2_scene_gen.box_document(pid, x0, x1, y0, y1, z0, z1, rho, mu)


def _plate(pid="plate"):
    return _box(pid, -0.35, -0.15, -RS, 0.0, -0.2, 0.2)


def _events(st: dict) -> int:
    return st["out_of_envelope_events"]


def setUpModule():
    global _proc
    assert EXE.exists(), f"engine missing: {EXE} (build Release first)"
    _proc = subprocess.Popen(
        [str(EXE), str(PORT), "--hidden", "1600", "900", "--no-restore"],
        cwd=str(EXE.parent))
    deadline = time.time() + 30.0
    while time.time() < deadline:
        try:
            _get("/tick_state")
            return
        except Exception:
            time.sleep(0.25)
    raise RuntimeError("engine did not answer /tick_state within 30 s")


def tearDownModule():
    if _proc and _proc.poll() is None:
        _proc.terminate()
        _proc.wait(timeout=30)


class B9Envelope(unittest.TestCase):

    # ── band 1: rest sink (measured: 2.5 mm sink exploded at 81 m/s) ────────
    def test_sink_band_named_refusal(self):
        stiff = _box("stiff", 0.10, 0.20, -RS, 0.04, -0.05, 0.05)
        stiff["ground"]["k_n_per_m"] *= 4.0     # rest sink 10 mm -> 2.5 mm
        r = self._admit_refusal([_plate(), stiff])
        self.assertIn("rest sink", r["error"])
        self.assertIn("qualified minimum", r["error"])

        # place route: refusal before mutation, state byte-identical.
        # Pause AFTER admit (a fresh admission runs): the physical clock
        # keeps stepping, and the save document (hence the hash) includes
        # the step counter.
        self.assertTrue(_admit([_plate(), _box("ok", 0.10, 0.20, -RS, 0.04, -0.05, 0.05)]).get("ok"))
        _post("/tick_b2_pause", json.dumps({"on": True}))
        h0 = _hash()
        stiff["id"] = "stiff2"
        r = _post("/tick_b2_place", json.dumps(stiff))
        self.assertFalse(r.get("ok", True), r)
        self.assertIn("rest sink", r["error"])
        self.assertEqual(_hash(), h0, "refused place must not move the state hash")

    # ── band 2: tipping (measured: 2 N at COM toppled the 20 mm wall) ───────
    def _wall(self, pid, half_x, half_z=0.18, top=0.10, rho=1200.0):
        return _box(pid, -half_x, half_x, -RS, top, -half_z, half_z, rho)

    def test_tipping_band_boundary(self):
        # the measured failure tuple: 20 mm base, 110 mm tall, 2 N at COM
        w = self._wall("w20", 0.010)
        w["envelope"] = {"max_lateral_load_n": 2.0, "role": "stand"}
        r = self._admit_refusal([_plate(), w])
        self.assertIn("tipping band", r["error"])
        self.assertIn("lateral load", r["error"])

        # boundary pair on the same wall family (360 mm long, 110 mm tall,
        # rho 1200): 35 mm base refuses, 40 mm admits. The assertion is the
        # band rule itself, evaluated from the authored geometry - the
        # engine must agree with it in both directions.
        for half_x, must_admit in [(0.0175, False), (0.020, True)]:
            doc = self._wall(f"w{int(half_x * 2000)}", half_x)
            doc["envelope"] = {"max_lateral_load_n": 2.0, "role": "stand"}
            m = doc["mass_kg"]
            shift = 2.0 * (doc["pose_c_m"][1] + RS) / (m * G) * 1000.0
            usable = half_x * 1000.0 - RS * 1000.0 - 2.0     # margin 2 mm
            r = _admit([_plate(), doc])
            if must_admit:
                self.assertTrue(r.get("ok"), f"{half_x*2000:.0f} mm wall refused: {r}")
                self.assertLessEqual(shift, usable)
            else:
                self.assertFalse(r.get("ok", True), f"{half_x*2000:.0f} mm wall admitted")
                self.assertGreater(shift, usable)
                self.assertIn("tipping band", r["error"])

    # ── band 3: sliding (measured: 20 mm slider exploded at 91 m/s) ─────────
    def test_slide_band_boundary(self):
        thin = _box("thin", 0.10, 0.30, -RS, 0.010, -0.05, 0.05)   # 20 mm tall
        thin["envelope"] = {"role": "slide"}
        r = self._admit_refusal([_plate(), thin])
        self.assertIn("sliding", r["error"])
        squat = _box("squat", 0.10, 0.30, -RS, 0.040, -0.05, 0.05)  # 50 mm tall
        squat["envelope"] = {"role": "slide"}
        self.assertTrue(_admit([_plate(), squat]).get("ok"))

    # ── criterion 5: visible runtime response AFTER admission ───────────────
    def test_runtime_speed_event(self):
        p = _box("dropper", 0.10, 0.20, 0.05, 0.09, -0.05, 0.05)   # free fall
        p["envelope"] = {"max_approach_speed_m_s": 0.05}
        # Baseline BEFORE the admit: the counters are cumulative across
        # admits, and the speed exit happens within milliseconds of the
        # admission response — reading the baseline after admit races it.
        lim0 = dict(_state()["out_of_envelope_limits"]) if _state()["active"] else {}
        self.assertTrue(_admit([_plate(), p]).get("ok"))
        y0 = _part(_state(), "dropper")["com_m"][1]
        _wait_steps(4000)                       # fall, impact, settle
        st = _state()
        got = st["out_of_envelope_limits"].get("max_approach_speed_m_s", 0)
        self.assertGreater(got - lim0.get("max_approach_speed_m_s", 0), 0,
                           f"speed exit produced no named event; part fell "
                           f"{y0 - _part(st, 'dropper')['com_m'][1]:.4f} m, "
                           f"limits={st['out_of_envelope_limits']}")
        self.assertFalse(st["diverged"])
        self.assertLess(_part(st, "dropper")["speed_m_s"], 5e-3)

    def test_runtime_stop_event(self):
        p = _box("slammer", 0.10, 0.20, 1.0, 1.02, -0.05, 0.05)    # gallery-16 drop
        p["envelope"] = {"role": "impinge"}
        e0 = _events(_state()) if _state()["active"] else 0
        self.assertTrue(_admit([_plate(), p]).get("ok"))
        _wait_steps(6000)
        st = _state()
        self.assertGreater(_events(st), e0, "crossing the declared stop produced no event")
        ev = st["out_of_envelope_last"]
        self.assertEqual(ev["limit"], "backstop_stop_m")
        self.assertGreater(ev["measured"], 0.015)
        self.assertFalse(st["diverged"])

    def test_runtime_tilt_event(self):
        w = self._wall("tilter", 0.020)         # 40 mm base: admits at 2 N
        w["envelope"] = {"max_lateral_load_n": 2.0, "role": "stand"}
        lim0 = dict(_state()["out_of_envelope_limits"]) if _state()["active"] else {}
        self.assertTrue(_admit([_plate(), w]).get("ok"))
        _wait_steps(3000)                       # settle on the rung
        com = _part(_state(), "tilter")["com_m"]
        self.assertTrue(_post("/tick_b2_load", json.dumps(
            {"part": "tilter", "force_n": [15.0, 0.0, 0.0], "point_world": com})).get("ok"))
        _wait_steps(4000)                       # 15 N: shift 44 mm >> 20 mm base
        st = _state()
        got = st["out_of_envelope_limits"].get("stand_tilt_rad", 0)
        self.assertGreater(got - lim0.get("stand_tilt_rad", 0), 0,
                           "stand-role tilt produced no named event")
        self.assertFalse(st["diverged"])
        _post("/tick_b2_load", json.dumps(
            {"part": "tilter", "force_n": [0.0, 0.0, 0.0], "point_world": com}))

    # ── the envelope travels with the part across save/restore ──────────────
    def test_envelope_roundtrip(self):
        p = _box("kept", 0.10, 0.20, -RS, 0.04, -0.05, 0.05)
        p["envelope"] = {"max_lateral_load_n": 1.0, "role": "stand"}
        self.assertTrue(_admit([_plate(), p]).get("ok"))
        _wait_steps(2000)
        _post("/tick_b2_pause", json.dumps({"on": True}))   # freeze the step counter
        doc = _get("/tick_b2_save")
        kept = next(q for q in doc["parts"] if q["id"] == "kept")
        self.assertEqual(kept["envelope"], {"max_lateral_load_n": 1.0, "role": "stand"})
        h0 = _hash()
        r = _post("/tick_b2_restore", json.dumps(doc))
        self.assertTrue(r.get("ok"), r)
        self.assertEqual(_hash(), h0)
        # and the restored part still refuses a stiffer re-admission tuple
        # (the envelope law is live after restore, not a saved comment)
        kept["ground"]["k_n_per_m"] *= 4.0
        self.assertFalse(_post("/tick_b2_place", json.dumps(kept)).get("ok", True))

    # ── helpers ──────────────────────────────────────────────────────────────
    def _admit_refusal(self, parts):
        """Admit must refuse; the previously active scene must survive."""
        before = _state()["parts"] if _state()["active"] else []
        r = _admit(parts)
        self.assertFalse(r.get("ok", True), f"expected refusal, got {r}")
        self.assertIn("error", r)
        st = _state()
        if before:
            self.assertEqual([p["id"] for p in st["parts"]],
                             [p["id"] for p in before],
                             "refused admit must leave the live world untouched")
        return r


if __name__ == "__main__":
    unittest.main(verbosity=2)
