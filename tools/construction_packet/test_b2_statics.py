"""B2 step 1 gate battery against the live resident runtime.

Checks required by the §13 B2 evidence column for part 1 (gravity/support):
two independent parts admitted as one strict chimera.b2_scene.v1 document
onto the FIRST SHARED RESIDENT runtime state; off-center load gives
correct reactions (each part's ground reaction equals its compiled weight
at rest); loose contact (the parts start separated and stay separated);
refusals name themselves and never clobber the live scene; the numerical
envelope (substep, rest sink, energy drift) is measured, not assumed.

The engine is launched fresh on a dedicated port; the scene is the only
thing loaded -- no membrane body is required (B2 is default-OFF and
independent of the seal).

Run:  python tools/construction_packet/test_b2_statics.py
Requires: .tmp/body-engine/Release/chimera_engine.exe (Release build).
"""
from __future__ import annotations

import copy
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
PORT = 8791
BASE = f"http://127.0.0.1:{PORT}"

_proc: subprocess.Popen | None = None


def _get(path: str) -> dict:
    with urllib.request.urlopen(BASE + path, timeout=5) as r:
        return json.loads(r.read().decode())


def _post(path: str, body: str = "") -> dict:
    req = urllib.request.Request(BASE + path, data=body.encode(), method="POST")
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return json.loads(e.read().decode())


def _rel(a: float, b: float) -> float:
    return abs(a - b) / max(abs(b), 1e-300)


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
        _proc.wait(timeout=10)


class B2Statics(unittest.TestCase):
    def setUp(self):
        _post("/tick_b2_clear")

    def scene(self) -> dict:
        return b2_scene_gen.make_scene()

    # ── the statics bar: reactions equal weight, parts stay loose ─────────
    def test_statics_reactions_and_loose_contact(self):
        scene = self.scene()
        r = _post("/tick_b2_admit", json.dumps(scene))
        self.assertTrue(r.get("ok"), f"admit refused: {r}")
        time.sleep(2.5)                       # settle (zeta 0.7, ~0.2 s)
        st = _get("/tick_b2_state")
        self.assertTrue(st["active"])
        self.assertFalse(st["diverged"])
        self.assertGreater(st["steps"], 0)
        self.assertAlmostEqual(st["dt_substep_s"], 0.00025, places=9)
        self.assertEqual(st["admission_reason"], scene["reason"])
        wtot = sum(p["mass_kg"] for p in scene["parts"]) * b2_scene_gen.G
        self.assertLess(_rel(st["total_weight_n"], wtot), 1e-9)
        self.assertLess(_rel(st["total_reaction_n"], wtot), 1e-3)
        self.assertEqual(len(st["parts"]), 2)
        for sp in st["parts"]:
            self.assertLess(_rel(sp["reaction_n"], sp["weight_n"]), 1e-3,
                            f"{sp['id']}: reaction {sp['reaction_n']} != weight {sp['weight_n']}")
            # wedge bottom face is a triangle: exactly 3 ground sites carry load
            self.assertEqual(sp["contacts_active"], 3, f"{sp['id']}: all sites carry load")
            self.assertLess(sp["speed_m_s"], 1e-3, f"{sp['id']}: still moving at rest")
            # rest sink envelope: s* = 1 cm, zeta 0.7 overshoot < 5 %
            self.assertGreater(sp["pen_run_m"], 0.009, sp["id"])
            self.assertLess(sp["pen_run_m"], 0.012, sp["id"])
        # loose contact: x-extents [0,0.3] and [0.6,0.82] never approach
        xs = [p["com_m"][0] for p in st["parts"]]
        self.assertGreater(abs(xs[1] - xs[0]), 0.4)
        # energy: damping dissipates, bounded by the weight x sink work
        drift = st["energy_drift_j"]
        self.assertLess(drift, 0.0)
        self.assertGreater(drift, -2.0 * wtot * b2_scene_gen.REST_SINK_M)

    def test_steps_advance_while_resident(self):
        self.assertTrue(_post("/tick_b2_admit", json.dumps(self.scene())).get("ok"))
        s1 = _get("/tick_b2_state")["steps"]
        time.sleep(0.4)
        s2 = _get("/tick_b2_state")["steps"]
        self.assertGreater(s2, s1, "the resident tick is not stepping the scene")

    def test_parts_roundtrip(self):
        scene = self.scene()
        _post("/tick_b2_admit", json.dumps(scene))
        got = {p["id"]: p for p in _get("/tick_b2_parts")["parts"]}
        self.assertEqual(set(got), {"part_wedge_a", "part_wedge_b"})
        for want in scene["parts"]:
            g = got[want["id"]]
            self.assertLess(_rel(g["mass_kg"], want["mass_kg"]), 1e-9)
            for a, b in zip(g["inertia_com_local_kg_m2"], want["inertia_com_local_kg_m2"]):
                self.assertLess(_rel(a, b), 1e-6)
            self.assertEqual(g["n_vertices"], 6)
            self.assertEqual(g["n_triangles"], 8)
            # quaternion roundtrip up to sign (q and -q are one rotation)
            dot = sum(a * b for a, b in zip(g["pose_q_wxyz"], want["pose_q_wxyz"]))
            self.assertGreater(abs(dot), 0.9999)

    # ── refusals: every malformed document names itself, scene survives ───
    def test_refusals_name_themselves(self):
        self.assertTrue(_post("/tick_b2_admit", json.dumps(self.scene())).get("ok"))
        before = _get("/tick_b2_state")["admission_reason"]

        def mutate(fn):
            s = copy.deepcopy(self.scene())
            fn(s)
            return s

        cases = [
            ("schema", mutate(lambda s: s.update(schema="chimera.b2_scene.v2")), "schema"),
            ("one part", mutate(lambda s: s["parts"].pop()), "exactly two parts"),
            ("three parts", mutate(lambda s: s["parts"].append(copy.deepcopy(s["parts"][0]))),
             "exactly two parts"),
            ("negative mass", mutate(lambda s: s["parts"][0].update(mass_kg=-1.0)), "mass_kg"),
            ("asymmetric inertia",
             mutate(lambda s: s["parts"][0]["inertia_com_local_kg_m2"].__setitem__(1, 123.0)),
             "symmetric"),
            ("triangle inequality",
             mutate(lambda s: s["parts"][0]["inertia_com_local_kg_m2"].__setitem__(
                 0, s["parts"][0]["inertia_com_local_kg_m2"][2] * 10.0)),
             "triangle inequality"),
            ("bad quaternion", mutate(lambda s: s["parts"][1].update(pose_q_wxyz=[2, 0, 0, 0])),
             "quaternion norm"),
            ("unknown field", mutate(lambda s: s["parts"][0].update(bogus=1)), "unknown field"),
            ("duplicate id", mutate(lambda s: s["parts"][1].update(id=s["parts"][0]["id"])),
             "duplicate part id"),
            ("index out of range",
             mutate(lambda s: s["parts"][0]["boundary_triangles"].__setitem__(0, 99)),
             "index out of range"),
            ("missing ground", mutate(lambda s: s["parts"][0].pop("ground")), "ground"),
            ("zero stiffness",
             mutate(lambda s: s["parts"][1]["ground"].update(k_n_per_m=0.0)), "must be positive"),
            ("negative damping",
             mutate(lambda s: s["parts"][1]["ground"].update(c_n_s_per_m=-1.0)), "must be >= 0"),
        ]
        for name, doc, needle in cases:
            r = _post("/tick_b2_admit", json.dumps(doc))
            self.assertFalse(r.get("ok", True), f"{name}: accepted a malformed scene")
            self.assertIn(needle, r.get("error", ""), f"{name}: error was {r.get('error')}")
        # a raw NaN is not JSON at all -- the strict parser refuses it
        r = _post("/tick_b2_admit", json.dumps(self.scene()).replace(
            '"mass_kg": ' + json.dumps(self.scene()["parts"][0]["mass_kg"]),
            '"mass_kg": NaN', 1))
        self.assertFalse(r.get("ok", True), "NaN accepted")
        # none of the refusals touched the live scene
        st = _get("/tick_b2_state")
        self.assertTrue(st["active"])
        self.assertFalse(st["diverged"])
        self.assertEqual(st["admission_reason"], before)

    def test_clear_disarms(self):
        _post("/tick_b2_admit", json.dumps(self.scene()))
        _post("/tick_b2_clear")
        st = _get("/tick_b2_state")
        self.assertFalse(st["active"])
        self.assertEqual(st["steps"], 0)
        # and the runtime admits again after a clear
        self.assertTrue(_post("/tick_b2_admit", json.dumps(self.scene())).get("ok"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
