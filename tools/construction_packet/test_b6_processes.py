"""B6 working-processes battery: each needed channel qualified separately on
the resident runtime (GAME_PLAN_ACTION_RPG.md §13, gate B6).

Gate row, verbatim: "Qualify each needed channel separately: chamber pressure/
flux, a valve, finite actuator, sensor, heat transfer or growth | Paired
exchanges conserve material inventories and close the energy balance including
storage, supplied work, heat and boundary flux; closing or severing a path
removes only its contribution".

Channel -> test map:
  chamber pressure/flux ......... test_chamber_pressure_law_and_energy
  valve (paired transport) ...... test_valve_equalizes_and_conserves
  closing/severing a path ....... test_valve_close_sever_patch_contributions
  heat transfer (paired energy) . test_heat_pair_exact_transfer
  finite actuator ............... test_piston_finite_actuator
  sensor (read-only) ............ test_sensor_readonly
  transaction law on controls ... test_process_transaction_law

The law (b2_scene.hpp): P = kappa*(q - V)/V0, U = kappa*(q-V)^2/(2*V0) — the
membrane's linear compressibility generalised to inventory vs volume. Every
analytic number below is computed from that law by hand; the engine's ledger
residual (max_residual_energy_J) is the implementation-vs-law proof and must
stay at floating-point level.

Run:  python tools/construction_packet/test_b6_processes.py
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
PORT = 8794
BASE = f"http://127.0.0.1:{PORT}"

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


def _proc_telemetry() -> dict:
    return _get("/tick_b2_process")


def _chambers() -> dict:
    return {c["id"]: c for c in _proc_telemetry()["chambers"]}


def _valve(pr: dict, a: str, b: str) -> dict:
    return next(v for v in pr["valves"] if v["a"] == a and v["b"] == b)


def _hash() -> str:
    return _get("/tick_b2_hash")["state_hash"]


def _admit_two_boxes(pid_b: str = "box_b", bx0: float = 3.0) -> None:
    doc = {"schema": "chimera.b2_scene.v1", "gravity_m_s2": 9.81,
           "reason": "b6-processes",
           "parts": [
               b2_scene_gen.box_document("box_a", 0.00, 0.10, -b2_scene_gen.REST_SINK_M,
                                         0.10, -0.05, 0.05, 600, 0.4),
               b2_scene_gen.box_document(pid_b, bx0, bx0 + 0.10, -b2_scene_gen.REST_SINK_M,
                                         0.10, -0.05, 0.05, 600, 0.4)]}
    r = _post("/tick_b2_admit", json.dumps(doc))
    assert r["ok"], r


def _chamber(cid: str, q: float, V0: float = 0.01, kappa: float = 1e5,
             T: float | None = None, C: float | None = None) -> None:
    body = {"id": cid, "V0_m3": V0, "kappa_Pa": kappa, "q_m3": q}
    if T is not None:
        body["T_K"] = T
    if C is not None:
        body["C_th_J_K"] = C
    r = _post("/tick_b2_chamber", json.dumps(body))
    assert r["ok"], r


def _rel(a: float, b: float) -> float:
    return abs(a - b) / max(abs(b), 1e-300)


def _wait_steps(n: int) -> None:
    """Advance the scene by at least n fixed substeps (1/4000 s each).
    Wall-clock sleeps are unreliable here: the render loop's frame pacing
    can stall for tens of ms (measured: steps frozen across a 4 ms sleep),
    so short process windows are measured in SIM time."""
    s0 = _get("/tick_b2_state")["steps"]
    deadline = time.time() + 10.0
    while time.time() < deadline:
        if _get("/tick_b2_state")["steps"] >= s0 + n:
            return
        time.sleep(0.005)
    raise RuntimeError("engine is not stepping")


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


class B6Processes(unittest.TestCase):
    def setUp(self):
        _post("/tick_b2_clear")

    # ── channel 1: chamber pressure + stored energy, exact against the law ──
    def test_chamber_pressure_law_and_energy(self):
        _admit_two_boxes()
        _chamber("c_hi", 0.002)          # X = -0.008 -> P = -80 kPa, U = 320 J
        _chamber("c_pos", 0.011)         # X = +0.001 -> P = +10 kPa,  U = 5 J
        _chamber("c_zero", 0.01)         # X = 0      -> P = 0        , U = 0
        ch = _chambers()
        self.assertAlmostEqual(ch["c_hi"]["p_Pa"], -80000.0, delta=1e-6)
        self.assertAlmostEqual(ch["c_hi"]["u_press_J"], 320.0, delta=1e-6)
        self.assertAlmostEqual(ch["c_pos"]["p_Pa"], 10000.0, delta=1e-6)
        self.assertAlmostEqual(ch["c_pos"]["u_press_J"], 5.0, delta=1e-6)
        self.assertAlmostEqual(ch["c_zero"]["p_Pa"], 0.0, delta=1e-9)
        led = _proc_telemetry()["ledger"]
        self.assertAlmostEqual(led["u_press_total_J"], 325.0, delta=1e-6)
        self.assertAlmostEqual(led["inventory_m3"], 0.023, delta=1e-12)
        self.assertAlmostEqual(led["residual_inventory_m3"], 0.0, delta=1e-12)
        # refusal controls: bad geometry, duplicates, unknown fields (paused,
        # so the only thing that could move the hash is an accepted edit)
        _post("/tick_b2_pause", '{"on":true}')
        h0 = _hash()
        self.assertFalse(_post("/tick_b2_chamber", '{"id":"c_x","V0_m3":0,"kappa_Pa":1}')["ok"])
        self.assertFalse(_post("/tick_b2_chamber", '{"id":"c_hi","V0_m3":0.01,"kappa_Pa":1}')["ok"])
        self.assertFalse(_post("/tick_b2_chamber",
                               '{"id":"c_y","V0_m3":0.01,"kappa_Pa":1,"bogus":2}')["ok"])
        self.assertEqual(_hash(), h0, "refused admissions must not move state")

    # ── channel 2: the valve — paired transport, inventory + energy closure ─
    def test_valve_equalizes_and_conserves(self):
        _admit_two_boxes()
        _chamber("c1", 0.002)
        _chamber("c2", 0.0)
        # analytic: U 820 J -> equalised q=0.001 each, P=-90 kPa, U 810 J,
        # dissipation exactly 10 J (the pair's dU, negative -> heat)
        r = _post("/tick_b2_valve", '{"a":"c1","b":"c2","g_m3_Pa_s":5e-5}')
        self.assertTrue(r["ok"], r)
        _wait_steps(240)                 # 60 ms ~ 60 time constants (tau = 1 ms)
        pr = _proc_telemetry()
        ch = {c["id"]: c for c in pr["chambers"]}
        led = pr["ledger"]
        self.assertLess(_rel(ch["c1"]["q_m3"] + ch["c2"]["q_m3"], 0.002), 1e-9,
                        "paired transport must conserve inventory")
        self.assertAlmostEqual(ch["c1"]["p_Pa"], ch["c2"]["p_Pa"], delta=50.0)
        self.assertAlmostEqual(ch["c1"]["p_Pa"], -90000.0, delta=50.0)
        self.assertLess(_rel(led["diss_total_J"], 10.0), 0.01,
                        "dissipation must match the analytic pair dU")
        self.assertLess(_rel(led["u_press_total_J"], 810.0), 0.01)
        self.assertAlmostEqual(led["residual_inventory_m3"], 0.0, delta=1e-12)
        self.assertLess(led["max_residual_energy_J"], 1e-9,
                        "energy ledger must close to floating point")
        # the valve law itself: flux = g * (Pa - Pb), signed a -> b
        _post("/tick_b2_pause", '{"on":true}')
        pr = _proc_telemetry()
        ch = {c["id"]: c for c in pr["chambers"]}
        v = _valve(pr, "c1", "c2")
        self.assertAlmostEqual(v["flux_m3_s"],
                               v["g_m3_Pa_s"] * (ch["c1"]["p_Pa"] - ch["c2"]["p_Pa"]),
                               delta=1e-9)
        self.assertAlmostEqual(ch["c1"]["flux_in_m3_s"], -v["flux_m3_s"], delta=1e-9)

    # ── gate clause: closing or severing a path removes ONLY its contribution
    def test_valve_close_sever_patch_contributions(self):
        _admit_two_boxes()
        _chamber("c1", 0.002)
        _chamber("c2", 0.0)
        _post("/tick_b2_valve", '{"a":"c1","b":"c2","g_m3_Pa_s":5e-6}')   # tau = 10 ms
        _post("/tick_b2_valve", '{"a":"c2","b":"env","g_m3_Pa_s":5e-6}')  # slow leak
        _wait_steps(16)                  # 4 ms of sim time
        _post("/tick_b2_pause", '{"on":true}')
        pr = _proc_telemetry()
        ch = {c["id"]: c for c in pr["chambers"]}
        v12 = _valve(pr, "c1", "c2")
        dP = ch["c1"]["p_Pa"] - ch["c2"]["p_Pa"]
        self.assertGreater(abs(v12["flux_m3_s"]), 1e-6)
        # flux is the law of the pressure at force time; telemetry p is the
        # post-mutation pressure, so allow one substep of decay (2.5 %)
        self.assertLess(_rel(v12["flux_m3_s"], v12["g_m3_Pa_s"] * dP), 0.03)
        # CLOSE the chamber path: its flux goes to zero, the env leak keeps
        # its own law (only its contribution removed, nothing else changes)
        r = _post("/tick_b2_valve_set", '{"a":"c1","b":"c2","on":false}')
        self.assertTrue(r["ok"], r)
        _post("/tick_b2_pause", '{"on":false}')
        _wait_steps(8)                   # 2 ms of sim time
        _post("/tick_b2_pause", '{"on":true}')
        pr = _proc_telemetry()
        ch = {c["id"]: c for c in pr["chambers"]}
        self.assertEqual(_valve(pr, "c1", "c2")["flux_m3_s"], 0.0,
                         "a closed valve must contribute nothing")
        env = _valve(pr, "c2", "env")
        self.assertLess(_rel(env["flux_m3_s"], env["g_m3_Pa_s"] * ch["c2"]["p_Pa"]), 0.03,
                        "the surviving path must still obey its own law")
        # SEVER it entirely: exchange stops, inventories freeze
        q_before = {c["id"]: c["q_m3"] for c in pr["chambers"]}
        r = _post("/tick_b2_valve_remove", '{"a":"c2","b":"env"}')
        self.assertTrue(r["ok"], r)
        _post("/tick_b2_pause", '{"on":false}')
        _wait_steps(200)                 # 50 ms: a live leak would move q
        ch = _chambers()
        for cid, q in q_before.items():
            self.assertAlmostEqual(ch[cid]["q_m3"], q, delta=1e-12,
                                   msg=f"severed scene must not move inventory ({cid})")
        # PATCH the leak the honest way: it consumes inventory and refuses
        # what the chamber cannot pay; pressure/history survive the debit
        _post("/tick_b2_pause", '{"on":true}')
        _post("/tick_b2_valve", '{"a":"c1","b":"env","g_m3_Pa_s":5e-6}')
        self.assertFalse(_post("/tick_b2_valve_patch",
                               '{"a":"c1","b":"env","cost_m3":10.0}')["ok"],
                         "a patch costing more than the chamber holds must be refused")
        q1 = _chambers()["c1"]["q_m3"]
        r = _post("/tick_b2_valve_patch", '{"a":"c1","b":"env","cost_m3":0.0002}')
        self.assertTrue(r["ok"], r)
        pr = _proc_telemetry()
        ch = {c["id"]: c for c in pr["chambers"]}
        self.assertEqual([v["b"] for v in pr["valves"]], ["c2"],
                         "patch removes only the patched path")
        # delta = the %.9g telemetry print resolution at q ~ 1e-3
        self.assertAlmostEqual(ch["c1"]["q_m3"], q1 - 0.0002, delta=1e-10)
        self.assertAlmostEqual(ch["c1"]["p_Pa"],
                               1e5 * (ch["c1"]["q_m3"] - 0.01) / 0.01, delta=1.0,
                               msg="pressure must be the law of the debited q, not a reset")
        self.assertAlmostEqual(pr["ledger"]["residual_inventory_m3"], 0.0, delta=1e-12)

    # ── channel 3: heat transfer — paired energy, exact conservation ────────
    def test_heat_pair_exact_transfer(self):
        _admit_two_boxes()
        _chamber("h1", 0.01, T=400.0, C=100.0)
        _chamber("h2", 0.01, T=300.0, C=100.0)
        # refusal: a chamber without heat capacity cannot carry a link
        _chamber("h3", 0.01)
        self.assertFalse(_post("/tick_b2_heat", '{"a":"h1","b":"h3","k_W_K":10}')["ok"])
        # refusal: unstable conductance (k*h*(1/Ca+1/Cb) >= 0.5)
        self.assertFalse(_post("/tick_b2_heat", '{"a":"h1","b":"h2","k_W_K":1e6}')["ok"])
        r = _post("/tick_b2_heat", '{"a":"h1","b":"h2","k_W_K":2000}')
        self.assertTrue(r["ok"], r)     # tau = 25 ms
        _wait_steps(1200)                # 0.3 s = 12 time constants
        pr = _proc_telemetry()
        ch = {c["id"]: c for c in pr["chambers"]}
        self.assertAlmostEqual(ch["h1"]["T_K"], 350.0, delta=0.5)
        self.assertAlmostEqual(ch["h2"]["T_K"], 350.0, delta=0.5)
        link = next(l for l in pr["heat"] if l["a"] == "h1")
        self.assertLess(_rel(link["moved_J_run"], 5000.0), 0.01,
                        "moved energy must equal C*dT of the hot side")
        self.assertLess(_rel(pr["ledger"]["u_th_total_J"], 70000.0), 1e-9,
                        "the pair must conserve thermal energy exactly")
        self.assertLess(pr["ledger"]["max_residual_energy_J"], 1e-9)

    # ── channel 4: the finite actuator — work, cap, stroke, relief ──────────
    def test_piston_finite_actuator(self):
        # one 1 kg frictionless box; the chamber pushes it along +x.
        doc = {"schema": "chimera.b2_scene.v1", "gravity_m_s2": 9.81,
               "reason": "b6-piston",
               "parts": [
                   b2_scene_gen.box_document("ram", 0.00, 0.10, -b2_scene_gen.REST_SINK_M,
                                             0.10, -0.05, 0.05, 1000, 0.0),
                   b2_scene_gen.box_document("far", 3.0, 3.10, -b2_scene_gen.REST_SINK_M,
                                             0.10, -0.05, 0.05, 1000, 0.4)]}
        self.assertTrue(_post("/tick_b2_admit", json.dumps(doc))["ok"])
        _chamber("pcyl", 0.011)         # q = V0 + 0.001 -> P0 = +10 kPa
        r = _post("/tick_b2_piston",
                  '{"chamber":"pcyl","part":"ram","axis":[1,0,0],'
                  '"area_m2":0.01,"stroke_m":0.05,"f_max_N":5}')
        self.assertTrue(r["ok"], r)
        # analytic: F_raw = (100 - 1000*x) N clamped to 5 N over the whole
        # 50 mm stroke. The ram box spans y = -REST_SINK..0.10, so its mass
        # is 1000*0.1*(0.1+RS)*0.1 = 1.1 kg -> v = sqrt(2*5*0.05/1.1) at the
        # stop, then the ram coasts (disengaged: no suction, no volume
        # change). W = U(0.001) - U(0.0005) = 5 - 1.25 = 3.75 J; relief = 3.5.
        import math
        m_ram = 1000 * 0.1 * (0.10 + b2_scene_gen.REST_SINK_M) * 0.1
        v_stop = math.sqrt(2 * 5.0 * 0.05 / m_ram)
        _wait_steps(1000)                # 0.25 s sim: engage ~0.15 s, then coast
        pr = _proc_telemetry()
        ps = pr["pistons"][0]
        self.assertLess(_rel(ps["work_J_run"], 3.75), 0.02,
                        "thermodynamic work must equal the chamber's -dU")
        self.assertLess(_rel(ps["relief_J_run"], 3.5), 0.02,
                        "the f_max cap must dissipate the withheld work")
        self.assertLess(_rel(ps["force_N"], 0.0), 1e-12)   # disengaged at read time
        self.assertGreater(ps["x_m"], 0.05, "the ram must have passed the stop")
        st = _get("/tick_b2_state")
        ram = next(p for p in st["parts"] if p["id"] == "ram")
        self.assertLess(_rel(ram["speed_m_s"], v_stop), 0.02,
                        "kinetic energy 0.25 J = applied work (f_max * stroke)")
        ch = {c["id"]: c for c in pr["chambers"]}
        self.assertAlmostEqual(ch["pcyl"]["q_m3"], 0.011, delta=1e-12,
                               msg="a piston moves volume, never inventory")
        self.assertLess(pr["ledger"]["max_residual_energy_J"], 1e-9)
        # coasting past the stop must not pump the chamber dry: volume frozen
        v_now = ch["pcyl"]["V_m3"]
        _wait_steps(400)
        self.assertAlmostEqual(_chambers()["pcyl"]["V_m3"], v_now, delta=1e-9,
                               msg="beyond stroke the volume coupling is disengaged")

    # ── channel 5: the sensor is read-only ──────────────────────────────────
    def test_sensor_readonly(self):
        _admit_two_boxes()
        _chamber("s1", 0.002)
        _chamber("s2", 0.0)
        _post("/tick_b2_valve", '{"a":"s1","b":"s2","g_m3_Pa_s":5e-5}')
        # refusal control: chambers without heat capacity cannot carry a link
        self.assertFalse(_post("/tick_b2_heat", '{"a":"s1","b":"s2","k_W_K":10}')["ok"])
        _wait_steps(200)
        _post("/tick_b2_pause", '{"on":true}')
        h0 = _hash()
        for _ in range(3):
            pr = _proc_telemetry()
        self.assertEqual(_hash(), h0, "reading the sensor must not change the scene")
        # schema completeness (the sensor is an instrument: fixed keys)
        self.assertEqual(pr["schema"], "chimera.b2_process.v1")
        for key in ("inventory_m3", "vented_m3", "u_press_total_J", "u_th_total_J",
                    "diss_total_J", "work_total_J", "boundary_total_J",
                    "residual_inventory_m3", "residual_energy_J",
                    "max_residual_energy_J"):
            self.assertIn(key, pr["ledger"])
        for c in pr["chambers"]:
            for key in ("V0_m3", "kappa_Pa", "q_m3", "V_m3", "p_Pa", "T_K",
                        "C_th_J_K", "u_press_J", "u_th_J", "flux_in_m3_s"):
                self.assertIn(key, c)

    # ── the B4 transaction law, applied to every process control ────────────
    def test_process_transaction_law(self):
        _admit_two_boxes()
        _chamber("t1", 0.002)
        _post("/tick_b2_valve", '{"a":"t1","b":"env","g_m3_Pa_s":5e-5}')
        _post("/tick_b2_pause", '{"on":true}')
        h0 = _hash()
        refusals = [
            ("/tick_b2_valve", '{"a":"t1","b":"nope","g_m3_Pa_s":5e-5}'),      # unknown chamber
            ("/tick_b2_valve", '{"a":"t1","b":"t1","g_m3_Pa_s":5e-5}'),        # self valve
            ("/tick_b2_valve", '{"a":"t1","b":"env","g_m3_Pa_s":-1}'),         # negative g
            ("/tick_b2_valve", '{"a":"t1","b":"env","g_m3_Pa_s":1.0}'),        # unstable g
            ("/tick_b2_valve_set", '{"a":"t1","b":"env","on":"yes"}'),         # not a bool
            ("/tick_b2_valve_remove", '{"a":"t1","b":"cX"}'),                  # no such valve
            ("/tick_b2_valve_patch", '{"a":"t1","b":"env","cost_m3":-1}'),     # negative cost
            ("/tick_b2_piston", '{"chamber":"nope","part":"box_a","axis":[1,0,0],"area_m2":1}'),
            ("/tick_b2_piston", '{"chamber":"t1","part":"nope","axis":[1,0,0],"area_m2":1}'),
            ("/tick_b2_piston", '{"chamber":"t1","part":"box_a","axis":[0,0,0],"area_m2":1}'),
            ("/tick_b2_heat", '{"a":"t1","b":"t1","k_W_K":1}'),
        ]
        for path, body in refusals:
            r = _post(path, body)
            self.assertFalse(r["ok"], f"{path} {body} must be refused")
            self.assertIn("refused:", r["error"])
        self.assertEqual(_hash(), h0, "refused process edits must not move state")


if __name__ == "__main__":
    unittest.main(verbosity=2)
