"""B7 cost/state-bound battery: the construction gate "bound cost and
preserve state" (GAME_PLAN_ACTION_RPG.md §13) measured on the resident
runtime against the DECLARED envelope (B7_declared_envelope.json, written
before any measurement).

Gate row, verbatim: "B7 / B2 onward, M4 release gate - bound cost and
preserve state | Resident native working set, independent physical clock,
bounded topology pools, recovery and compatible render LOD | No routine
full-state CPU round trip; declared 4090 memory/frame-time envelope;
repeated construction has stable RAM/VRAM/disk use".

Gate clause -> test map:
  independent physical clock ......... test_independent_physical_clock
  no routine full-state round trip ... test_no_routine_full_state_round_trip
  bounded topology pools ............. test_bounded_topology_pools
  repeated construction plateau ...... test_repeated_construction_plateau
                                       (RAM via psapi, VRAM via nvidia-smi,
                                        disk via Saved/ byte total)
  recovery preserves state ........... test_recovery_preserves_state
  compatible render LOD .............. test_display_lod_compatible
  triangle-order invariance .......... test_triangle_order_invariance
  declared frame-time envelope ....... test_frame_time_envelope

The clock (b2_clock_loop_, membrane_tick.cpp) is a dedicated steady_clock
thread: it advances the scene by real elapsed time whatever the render loop
does, clamps catch-up at 50 ms per wake, and counts every bound applied.
The display LOD (b2_scene.cpp) selects only the render/pick mesh; physics,
the save document and the state hash never see it.

Run:  python tools/construction_packet/test_b7_bounds.py
Requires: .tmp/body-engine/Release/chimera_engine.exe (Release build),
          nvidia-smi on PATH (RTX 4090 host).
"""
from __future__ import annotations

import ctypes
import json
import re
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
ENVELOPE = json.loads((REPO / "docs" / "evidence" / "construction_packet_20261012" /
                       "B7_declared_envelope.json").read_text(encoding="utf-8"))
STDOUT_LOG = REPO / ".tmp" / "b7_engine_stdout.txt"
SAVED_DIR = REPO / "Saved"
PORT = 8798
BASE = f"http://127.0.0.1:{PORT}"

_proc: subprocess.Popen | None = None
_log_handle = None


def _get(path: str) -> dict:
    with urllib.request.urlopen(BASE + path, timeout=10) as r:
        return json.loads(r.read().decode())


def _get_raw(path: str) -> bytes:
    with urllib.request.urlopen(BASE + path, timeout=10) as r:
        return r.read()


def _post(path: str, body: str = "") -> dict:
    req = urllib.request.Request(BASE + path, data=body.encode(), method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return json.loads(e.read().decode())


def _hash() -> str:
    return _get("/tick_b2_hash")["state_hash"]


def _state() -> dict:
    return _get("/tick_b2_state")


def _wait_steps(n: int) -> None:
    """Advance the scene by at least n fixed substeps (1/4000 s each)."""
    s0 = _state()["steps"]
    deadline = time.time() + 30.0
    while time.time() < deadline:
        if _state()["steps"] >= s0 + n:
            return
        time.sleep(0.005)
    raise RuntimeError("engine is not stepping")


def _boxes(n: int, reason: str) -> None:
    doc = {"schema": "chimera.b2_scene.v1", "gravity_m_s2": 9.81, "reason": reason,
           "parts": [b2_scene_gen.box_document(f"p{j}", j * 0.5, j * 0.5 + 0.10,
                                               -b2_scene_gen.REST_SINK_M, 0.10,
                                               -0.05, 0.05, 600, 0.4)
                     for j in range(n)]}
    r = _post("/tick_b2_admit", json.dumps(doc))
    assert r.get("ok"), r


def _chamber(cid: str, q: float, C: float | None = None) -> dict:
    body = {"id": cid, "V0_m3": 0.01, "kappa_Pa": 1e5, "q_m3": q}
    if C is not None:
        body["C_th_J_K"] = C
    return _post("/tick_b2_chamber", json.dumps(body))


def _weld(ai: int, bi: int) -> dict:
    # strut at rest: three anchor pairs at the midpoint between the two
    # boxes (x = j*0.5 .. j*0.5+0.1), identical on both sides, so the weld
    # is born force-free however far apart the parts sit
    xm = (ai * 0.5 + 0.10 + bi * 0.5) / 2.0
    az = [[xm, 0.05, 0.00, xm, 0.05, 0.00],
          [xm, 0.05, 0.05, xm, 0.05, 0.05],
          [xm, 0.08, 0.02, xm, 0.08, 0.02]]
    return _post("/tick_b2_weld", json.dumps(
        {"a": f"p{ai}", "b": f"p{bi}", "k": 1e4, "c_damp": 1.0,
         "anchors_world": az}))


# ── measurement helpers (host facts, not engine facts) ──────────────────────
class _PMC(ctypes.Structure):
    _fields_ = [("cb", ctypes.c_uint32), ("PageFaultCount", ctypes.c_uint32),
                ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]


def _rss_bytes(pid: int) -> int:
    h = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
    assert h, "OpenProcess failed"
    pmc = _PMC()
    pmc.cb = ctypes.sizeof(pmc)
    ok = ctypes.windll.psapi.GetProcessMemoryInfo(h, ctypes.byref(pmc), pmc.cb)
    ctypes.windll.kernel32.CloseHandle(h)
    assert ok, "GetProcessMemoryInfo failed"
    return int(pmc.WorkingSetSize)


def _vram_mib() -> int:
    out = subprocess.run(["nvidia-smi", "--query-gpu=memory.used",
                          "--format=csv,noheader,nounits"],
                         capture_output=True, text=True, timeout=20)
    return int(out.stdout.strip().splitlines()[0])


def _saved_dir_bytes() -> int:
    if not SAVED_DIR.exists():
        return 0
    return sum(f.stat().st_size for f in SAVED_DIR.rglob("*") if f.is_file())


def setUpModule():
    global _proc
    assert EXE.exists(), f"engine missing: {EXE} (build Release first)"
    global _log_handle
    _log_handle = open(STDOUT_LOG, "w")
    _proc = subprocess.Popen(
        [str(EXE), str(PORT), "--hidden", "1600", "900", "--no-restore"],
        cwd=str(EXE.parent), stdout=_log_handle, stderr=subprocess.STDOUT)
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
    if _log_handle:
        _log_handle.close()


class B7Bounds(unittest.TestCase):
    # ── independent physical clock (plan: fixed sim clock independent of
    #   rendering; catch-up bounded; slow frames reported) ────────────────────
    def test_independent_physical_clock(self):
        _boxes(2, "b7-clock")
        c0 = _get("/tick_b2_clock")
        self.assertTrue(c0["ok"] and c0["thread"] and c0["running"])
        self.assertEqual(c0["catchup_bound_s"], ENVELOPE["physical_clock"]["catchup_bound_s"])
        self.assertEqual(c0["wake_budget_ms"], ENVELOPE["physical_clock"]["wake_budget_ms"])
        time.sleep(1.0)
        c1 = _get("/tick_b2_clock")
        d_sim = c1["sim_s"] - c0["sim_s"]
        d_wall = c1["active_wall_s"] - c0["active_wall_s"]
        ratio = d_sim / d_wall
        env = ENVELOPE["physical_clock"]
        self.assertGreaterEqual(ratio, env["sim_over_wall_min"],
                                f"clock lost time: ratio {ratio:.3f}")
        self.assertLessEqual(ratio, env["sim_over_wall_max"],
                             f"clock ran hot: ratio {ratio:.3f}")
        self.assertGreater(c1["ticks"] - c0["ticks"], 100, "clock barely ticks")
        self.assertEqual(c1["catchup_clamps"] - c0["catchup_clamps"], 0,
                         "steady state must not need catch-up bounds")
        # the clock, not the render loop, advances physics: steps grew too
        self.assertGreater(_state()["steps"], 0)
        # reported, never hidden: slow wakes have their own counter
        self.assertIn("slow_ticks", c1)
        self.assertIn("max_gap_ms", c1)

    # ── no routine full-state CPU round trip ─────────────────────────────────
    def test_no_routine_full_state_round_trip(self):
        _boxes(3, "b7-roundtrip")
        self.assertTrue(_chamber("c0", 0.002, C=100.0)["ok"])
        self.assertTrue(_chamber("c1", 0.001, C=100.0)["ok"])
        self.assertTrue(_post("/tick_b2_valve",
                              '{"a":"c0","b":"c1","g_m3_Pa_s":1e-5}').get("ok"))
        self.assertTrue(_post("/tick_b2_heat",
                              '{"a":"c0","b":"c1","k_W_K":0.5}').get("ok"))
        self.assertTrue(_post("/tick_b2_piston",
                              '{"chamber":"c0","part":"p2","axis":[1,0,0],'
                              '"area_m2":0.01,"stroke_m":0.02,"f_max_N":5}').get("ok"))
        rt0 = _state()["round_trips"]
        _wait_steps(2000)                       # 0.5 s of physics
        rt1 = _state()["round_trips"]
        self.assertEqual(rt1["saves"], rt0["saves"],
                         "stepping must not serialise the full state")
        self.assertEqual(rt1["restores"], rt0["restores"])
        self.assertEqual(rt1["hash_reads"], rt0["hash_reads"],
                         "stepping must not hash the full state")
        # declared payload bound on the two routine per-tick reads
        for path in ("/tick_b2_state", "/tick_b2_process"):
            n = len(_get_raw(path))
            self.assertLessEqual(n, ENVELOPE["telemetry_payload_bytes_max"],
                                 f"{path} payload {n} B exceeds declared bound")

    # ── bounded topology pools: caps, self-named refusals, usage telemetry ───
    def test_bounded_topology_pools(self):
        _boxes(6, "b7-pools")
        # parts cap: a 7th part cannot be admitted...
        doc = {"schema": "chimera.b2_scene.v1", "gravity_m_s2": 9.81,
               "reason": "b7-pools-over",
               "parts": [b2_scene_gen.box_document(f"p{j}", j * 0.5, j * 0.5 + 0.10,
                                                   -b2_scene_gen.REST_SINK_M, 0.10,
                                                   -0.05, 0.05, 600, 0.4)
                         for j in range(7)]}
        self.assertFalse(_post("/tick_b2_admit", json.dumps(doc)).get("ok"))
        _boxes(6, "b7-pools")                   # restore the 6-part scene
        _post("/tick_b2_pause", '{"on":true}')
        h_admit = _hash()
        # ...nor placed
        p7 = b2_scene_gen.box_document("p7", 9.0, 9.1, -b2_scene_gen.REST_SINK_M,
                                       0.10, -0.05, 0.05, 600, 0.4)
        self.assertFalse(_post("/tick_b2_place", json.dumps(p7)).get("ok"))
        self.assertEqual(_hash(), h_admit, "a refused place must not move state")
        caps = ENVELOPE["topology_pools"]
        # fill every pool to its cap (accepted edits)
        for j in range(caps["chambers"]):
            self.assertTrue(_chamber(f"c{j}", 0.001, C=100.0)["ok"])
        pairs = [(0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (1, 2),
                 (1, 3), (1, 4), (1, 5), (2, 3), (2, 4), (2, 5)]
        for a, b in pairs:
            r = _post("/tick_b2_valve",
                      f'{{"a":"c{a}","b":"c{b}","g_m3_Pa_s":1e-7}}')
            self.assertTrue(r.get("ok"), r)
        for a, b in pairs:
            r = _post("/tick_b2_heat", f'{{"a":"c{a}","b":"c{b}","k_W_K":0.1}}')
            self.assertTrue(r.get("ok"), r)
        for j in range(caps["pistons"]):
            r = _post("/tick_b2_piston",
                      f'{{"chamber":"c{j}","part":"p{j}","axis":[1,0,0],'
                      '"area_m2":0.01,"stroke_m":0.02,"f_max_N":5}')
            self.assertTrue(r.get("ok"), r)
        # welds: the cap equals C(6,2) - every pair fits, usage sits AT the cap
        allp = [(a, b) for a in range(6) for b in range(a + 1, 6)]
        self.assertEqual(len(allp), caps["welds"])
        for a, b in allp:
            self.assertTrue(_weld(a, b).get("ok"))
        # usage telemetry reports exactly the caps
        pools = _state()["pools"]
        for k in ("parts", "welds", "chambers", "valves", "heat", "pistons"):
            self.assertEqual(pools[k], [caps[k], caps[k]], f"pool {k} usage/cap")
        # now every over-cap control: refused by name, state untouched
        h0 = _hash()
        r = _chamber("c6", 0.001)
        self.assertFalse(r.get("ok"))
        self.assertIn("cap", r["error"])
        r = _post("/tick_b2_valve", '{"a":"c3","b":"c4","g_m3_Pa_s":1e-7}')
        self.assertFalse(r.get("ok"))
        self.assertIn("pool cap", r["error"])
        r = _post("/tick_b2_heat", '{"a":"c3","b":"c4","k_W_K":0.1}')
        self.assertFalse(r.get("ok"))
        self.assertIn("pool cap", r["error"])
        r = _post("/tick_b2_piston",
                  '{"chamber":"c0","part":"p1","axis":[1,0,0],'
                  '"area_m2":0.01,"stroke_m":0.02,"f_max_N":5}')
        self.assertFalse(r.get("ok"))
        self.assertIn("pool cap", r["error"])
        self.assertEqual(_hash(), h0, "refused pool edits must not move state")
        _post("/tick_b2_pause", '{"on":false}')

    # ── repeated construction: RAM / VRAM / disk reach a bounded plateau ────
    def test_repeated_construction_plateau(self):
        env = ENVELOPE
        vram0 = _vram_mib()
        disk0 = _saved_dir_bytes()
        rss = []
        for i in range(25):
            _boxes(3, f"b7-plateau-{i}")
            self.assertTrue(_weld(0, 1).get("ok"))
            self.assertTrue(_weld(1, 2).get("ok"))
            self.assertTrue(_chamber("c0", 0.002, C=100.0)["ok"])
            self.assertTrue(_chamber("c1", 0.001, C=100.0)["ok"])
            self.assertTrue(_post("/tick_b2_valve",
                                  '{"a":"c0","b":"c1","g_m3_Pa_s":1e-5}').get("ok"))
            self.assertTrue(_post("/tick_b2_piston",
                                  '{"chamber":"c0","part":"p2","axis":[1,0,0],'
                                  '"area_m2":0.01,"stroke_m":0.02,"f_max_N":5}').get("ok"))
            _wait_steps(200)                    # 50 ms of physics per cycle
            save = _get("/tick_b2_save")        # explicit full-state round trip
            self.assertIn("parts", save)
            rss.append(_rss_bytes(_proc.pid))
        growth = rss[-1] - rss[4]               # plateau after warm-up cycles
        self.assertLessEqual(
            growth, env["resident_native_working_set"]
            ["engine_rss_growth_over_25_construction_cycles_bytes"],
            f"RSS grew {growth/2**20:.1f} MiB over 25 construction cycles")
        vram1 = _vram_mib()
        self.assertLessEqual(vram1 - vram0, env["vram_growth_over_25_construction_cycles_mib"],
                             f"VRAM grew {vram1 - vram0} MiB over 25 cycles")
        self.assertLessEqual(_saved_dir_bytes(), disk0,
                             "repeated construction must not grow Saved/")

    # ── recovery preserves state (gallery item 11: IDs/inventory survive) ───
    def test_recovery_preserves_state(self):
        _boxes(2, "b7-recovery")
        self.assertTrue(_weld(0, 1).get("ok"))
        self.assertTrue(_chamber("c0", 0.002, C=100.0)["ok"])
        self.assertTrue(_chamber("c1", 0.001, C=100.0)["ok"])
        self.assertTrue(_post("/tick_b2_valve",
                              '{"a":"c0","b":"c1","g_m3_Pa_s":1e-5}').get("ok"))
        _wait_steps(400)
        _post("/tick_b2_pause", '{"on":true}')
        doc = _get("/tick_b2_save")
        h0 = _hash()
        ids0 = [p["id"] for p in _state()["parts"]]
        q0 = {c["id"]: c["q_m3"] for c in _get("/tick_b2_process")["chambers"]}
        _post("/tick_b2_pause", '{"on":false}')
        _wait_steps(800)                        # the state moves on
        _post("/tick_b2_pause", '{"on":true}')
        r = _post("/tick_b2_restore", json.dumps(doc))
        self.assertTrue(r.get("ok"), r)
        self.assertEqual(_hash(), h0, "restore must reproduce the saved state bit-exactly")
        self.assertEqual([p["id"] for p in _state()["parts"]], ids0, "ids survive")
        q1 = {c["id"]: c["q_m3"] for c in _get("/tick_b2_process")["chambers"]}
        for cid, q in q0.items():
            self.assertAlmostEqual(q1[cid], q, delta=1e-12, msg=f"inventory {cid}")
        _post("/tick_b2_pause", '{"on":false}')

    # ── compatible render LOD: display-only, hash-invariant, same picks ─────
    def test_display_lod_compatible(self):
        _boxes(2, "b7-lod")
        _wait_steps(2000)                       # settle onto the ground rung
        _post("/tick_b2_pause", '{"on":true}')
        h0 = _hash()
        s0 = _state()
        phys = s0["display"]["physical_tris"]
        react0 = s0["total_reaction_n"]
        ray = '{"eye":[0.05,1.0,0.0],"dir":[0.0,-1.0,0.0]}'
        pk0 = _post("/tick_b2_pick", ray)
        self.assertTrue(pk0.get("hit"), pk0)
        r = _post("/tick_b2_render_lod", '{"level":1}')
        self.assertTrue(r.get("ok"), r)
        s1 = _state()
        self.assertEqual(s1["display"]["lod"], 1)
        self.assertEqual(s1["display"]["display_tris"], 12 * len(s1["parts"]),
                         "LOD 1 is one world AABB (12 tris) per part")
        self.assertEqual(s1["display"]["physical_tris"], phys,
                         "the physical mesh count never changes with display LOD")
        self.assertEqual(_hash(), h0, "display LOD must not touch the state hash")
        self.assertAlmostEqual(s1["total_reaction_n"], react0, delta=1e-12,
                               msg="attached physics must survive a display LOD change")
        pk1 = _post("/tick_b2_pick", ray)
        self.assertEqual(pk1["id"], pk0["id"], "picks resolve the same ids at LOD 1")
        for a, b in zip(pk1["hit"], pk0["hit"]):
            self.assertAlmostEqual(a, b, delta=1e-6, msg="pick point agrees across LODs")
        r = _post("/tick_b2_render_lod", '{"level":2}')
        self.assertFalse(r.get("ok"))
        self.assertEqual(_hash(), h0, "a refused LOD change must not move state")
        self.assertTrue(_post("/tick_b2_render_lod", '{"level":0}').get("ok"))
        self.assertEqual(_hash(), h0)
        _post("/tick_b2_pause", '{"on":false}')

    # ── gallery item 13: triangle order does not change material strength ───
    def test_triangle_order_invariance(self):
        def settle_and_read(rotate: int) -> dict:
            # the schema needs 2..6 parts; the second box sits far away and
            # never interacts - q0 carries the measurement
            parts = [b2_scene_gen.box_document("q0", 0.0, 0.10, -b2_scene_gen.REST_SINK_M,
                                               0.10, -0.05, 0.05, 600, 0.4),
                     b2_scene_gen.box_document("far", 50.0, 50.10, -b2_scene_gen.REST_SINK_M,
                                               0.10, -0.05, 0.05, 600, 0.4)]
            tris = parts[0]["boundary_triangles"]
            if rotate:
                tris = tris[rotate:] + tris[:rotate]   # same faces, different order
            parts[0]["boundary_triangles"] = tris
            doc = {"schema": "chimera.b2_scene.v1", "gravity_m_s2": 9.81,
                   "reason": "b7-triorder", "parts": parts}
            r = _post("/tick_b2_admit", json.dumps(doc))
            self.assertTrue(r.get("ok"), r)
            _wait_steps(4000)                   # 1 s of physics: fully settled
            s = _state()
            q0 = next(p for p in s["parts"] if p["id"] == "q0")
            return {"reaction": q0["reaction_n"],
                    "sink": q0["com_m"][1],
                    "mass": q0["mass_kg"]}
        a = settle_and_read(0)
        b = settle_and_read(3)                  # rotate the face list by one face
        c = settle_and_read(15)                 # and by five faces
        self.assertAlmostEqual(b["reaction"], a["reaction"], delta=1e-9 * abs(a["reaction"]))
        self.assertAlmostEqual(c["reaction"], a["reaction"], delta=1e-9 * abs(a["reaction"]))
        self.assertAlmostEqual(b["sink"], a["sink"], delta=1e-9)
        self.assertEqual(b["mass"], a["mass"])

    # ── declared frame-time envelope (engine's own 5 s window) ───────────────
    def test_frame_time_envelope(self):
        _boxes(2, "b7-frametime")
        deadline = time.time() + 12.0
        lines: list[str] = []
        while time.time() < deadline:
            lines = STDOUT_LOG.read_text(errors="replace").splitlines()
            if any("ft ms avg" in ln for ln in lines):
                break
            time.sleep(0.5)
        wins = [m for ln in lines
                if (m := re.search(r"ft ms avg ([\d.]+) max ([\d.]+)", ln))]
        self.assertTrue(wins, "engine never reported a frame-time window")
        avg = float(wins[-1].group(1))
        self.assertLessEqual(avg, ENVELOPE["presentation"]["frame_time_avg_ms_max"],
                             f"frame time {avg} ms misses the 60 FPS envelope")


if __name__ == "__main__":
    unittest.main(verbosity=2)
